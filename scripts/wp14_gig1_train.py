"""GiG-1a gerçek eğitimi ve dondurulmuş dış skorlaması.

Protokol `reports/qa/WP14/gig1_v1/run_config.json` içinde sonuçlardan ÖNCE
kilitlenir. Bölmeler, hedef sözlüğü, ölçekleyici, kayıp, optimizer, epoch
politikası ve karşılaştırma anahtarları WP10 ile birebir aynıdır; tek fark
modeldir.

Kullanım:
    python scripts/wp14_gig1_train.py lock     # protokolü kilitle
    python scripts/wp14_gig1_train.py train    # iç seçim + dış fit
    python scripts/wp14_gig1_train.py score    # dondurulmuş dış skorlama
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math
import platform
import sys
import time
import traceback

import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wp08_baseline_metrics import RankingCache
from wp09_data import validate_bundle
from wp10_molecular_graph import load_store
from wp10_train import (
    load_bundle,
    source_labels,
    restrict_labels,
    proxy_matrix,
    select_query,
    sha,
    state_hash,
)
from wp14_gig1_encoder import (
    VARIANT,
    initialized_gig1,
    prepare,
    input_digest,
    train_forward,
    query_forward,
)

QA = ROOT / "reports/qa/WP14/gig1_v1"
MODEL = ROOT / "models/WP14_gig1_v1"
WP10_QA = ROOT / "reports/qa/WP10/training_v1"
NULL = ROOT / "reports/qa/WP09/null_gate_v3"
VERSION = "WP14-GiG1a-drug-to-protein-message-v1"
SEMANTICS = (
    "Observed SIDER record ranking proxy; unknown NOT verified biological negative; "
    "NOT clinical risk; exploratory architecture comparison against frozen A1P1"
)


def write_json(path, obj):
    def clean(v):
        if isinstance(v, dict):
            return {str(k): clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        if isinstance(v, np.generic):
            return clean(v.item())
        if isinstance(v, float) and not math.isfinite(v):
            return None
        return v

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(obj), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def csv(name, frame):
    (QA / name).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(QA / name, index=False, encoding="utf-8-sig", lineterminator="\n")


def configure_runtime():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def drug_ap(y, scores):
    values = []
    for yy, ss in zip(y, scores):
        values.append(RankingCache(yy, ss, np.zeros(len(yy), dtype=int)).evaluate(np.ones(1))[0][0])
    values = np.asarray(values)
    return float(values[np.isfinite(values)].mean()) if np.isfinite(values).any() else float("nan")


def jobs_frame():
    """WP10'un dondurulmuş iş listesinden A1P1 bağlamları alınır."""
    jobs = pd.read_csv(WP10_QA / "training_jobs_frozen.csv", keep_default_na=False)
    arm = jobs[jobs.variant.eq("A1P1")].copy()
    if arm.empty:
        raise RuntimeError("A1P1 bağlamları bulunamadı")
    return arm.reset_index(drop=True)


# --------------------------------------------------------------- kilit
def lock():
    if (QA / "run_config.json").exists():
        raise RuntimeError("Protokol zaten kilitli")
    gate = ROOT / "reports/qa/WP14/gig1_gate_v1/synthetic_gate.json"
    if not gate.is_file():
        raise RuntimeError("Önce sentetik kapı çalıştırılmalı")
    gate_result = json.loads(gate.read_text(encoding="utf-8"))
    if gate_result["failed"]:
        raise RuntimeError("Sentetik kapı geçilmeden kilit yok")
    arm = jobs_frame()
    config = {
        "version": VERSION,
        "semantics": SEMANTICS,
        "decision_report": "reports/GIG1_GIG2_FEASIBILITY_AND_DECISION_v2.md",
        "user_authorized_training": True,
        "arm": VARIANT,
        "model": "A1P1 omurgası + ilaç→protein mesajı (tipsiz, tekilleştirilmiş çiftler)",
        "frozen_from": "reports/qa/WP10/training_v1/training_jobs_frozen.csv (variant=A1P1)",
        "contexts": int(len(arm)),
        "inner_contexts": int((arm.inner_fold > 0).sum()),
        "outer_contexts": int((arm.inner_fold == 0).sum()),
        "split": "frozen 5 outer / 3 inner, drug-disjoint; identical to WP08/WP09/WP10",
        "targets_source": "reports/qa/WP09/null_gate_v3/training_preview_sources.json :: fittable_train_B2_PT",
        "loss": "mean BCEWithLogitsLoss observed-record proxy, no weights",
        "optimizer": {"name": "AdamW", "lr": 0.001, "weight_decay": 0.001},
        "epochs": {"max": 200, "patience": 20, "min_delta": 0.0001,
                   "outer": "floor(median(common inner best epochs)+0.5)"},
        "ppi_threshold": 700,
        "primary_metric": "drug-macro observed-record AP on common 54 drugs",
        "acceptance_criterion": (
            "GiG1a - A1P1 conditional 95% group bootstrap CI strictly above zero "
            "AND stress protocol point estimate not negative"
        ),
        "side_effect_edges_in_encoder": False,
        "test_labels_in_encoder": False,
        "frozen_models_retrained": False,
        "synthetic_gate_sha256": sha(gate),
        "encoder_sha256": sha(ROOT / "scripts/wp14_gig1_encoder.py"),
        "gate_script_sha256": sha(ROOT / "scripts/wp14_gig1_gate.py"),
        "environment": {"python": platform.python_version(), "torch": torch.__version__},
    }
    write_json(QA / "run_config.json", config)
    print(f"Protokol kilitlendi: {QA/'run_config.json'}")
    print(f"  bağlam: {config['contexts']} ({config['inner_contexts']} iç + {config['outer_contexts']} dış)")
    print(f"  encoder sha256: {config['encoder_sha256'][:16]}…")


# --------------------------------------------------------------- eğitim
def fit_model(graph, train_labels, targets, seed, validation=None, validation_labels=None,
              fixed_epochs=None, store=None):
    configure_runtime()
    ids = list(graph["drug_ids"])
    eligible = np.asarray(graph["eligible"], bool)
    fit_ids = list(np.asarray(ids)[eligible])
    if not targets or not fit_ids:
        raise ValueError("NA_no_trainable_targets_or_drugs")
    y = proxy_matrix(train_labels, fit_ids, targets)
    if not ((y.sum(0) > 0) & (y.sum(0) < len(y))).all():
        raise ValueError("Single train proxy outcome; no fallback")
    if validation is not None:
        validate_bundle(graph, validation)
        if not np.all(validation["split"] == "validation"):
            raise ValueError("Only validation queries may select epochs")
        ve = validation["eligible"]
        val_ids = list(validation["drug_ids"][ve])
        yv = proxy_matrix(validation_labels, val_ids, targets)
    elif fixed_epochs is None:
        raise ValueError("Outer fit requires committed fixed epochs")
    else:
        validate_bundle(graph)

    store = load_store() if store is None else store
    model = initialized_gig1(int(seed), num_targets=len(targets))
    initial = copy.deepcopy(model.state_dict())
    initial_hash = state_hash(initial)
    train_input = prepare(model, graph, store.make_batch(ids))
    val_input = prepare(model, validation, store.make_batch(validation["drug_ids"])) if validation is not None else None
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.001)

    history, best_state, best_ap, best_epoch, bad, steps = [], None, -math.inf, None, 0, 0
    status, error = "OK", ""
    limit = int(fixed_epochs if fixed_epochs is not None else 200)
    try:
        for epoch in range(1, limit + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            output = train_forward(model, train_input)
            logits = output["logits"][eligible]
            if not torch.isfinite(logits).all():
                raise FloatingPointError("Nonfinite train logits")
            loss = nn.functional.binary_cross_entropy_with_logits(
                logits, torch.from_numpy(y), reduction="none"
            ).mean(1).mean()
            if not torch.isfinite(loss):
                raise FloatingPointError("Nonfinite proxy loss")
            loss.backward()

            def gnorm(p):
                return float(p.grad.norm()) if p.grad is not None else 0.0

            dm = gnorm(model.drug_message.weight)
            dp = gnorm(model.drug_projection.weight)
            pm = gnorm(model.base.protein.message.weight)
            am = gnorm(model.molecular.atom_message.weight)
            if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):
                raise FloatingPointError("Nonfinite gradient")
            optimizer.step()
            steps += 1
            if any(not torch.isfinite(p).all() for p in model.parameters()):
                raise FloatingPointError("Nonfinite updated parameters")

            ap = vl = float("nan")
            nval = 0
            if validation is not None:
                model.eval()
                with torch.no_grad():
                    cache = train_forward(model, train_input)["protein_h"]
                    pred = query_forward(model, val_input, cache)["logits"][ve]
                    if not torch.isfinite(pred).all():
                        raise FloatingPointError("Nonfinite validation logits")
                    ap = drug_ap(yv, torch.sigmoid(pred).numpy())
                    vl = float(nn.functional.binary_cross_entropy_with_logits(pred, torch.from_numpy(yv)))
                    nval = int(((yv.sum(1) > 0) & (yv.sum(1) < yv.shape[1])).sum())
                if math.isfinite(ap) and (best_epoch is None or ap > best_ap + 0.0001):
                    best_ap, best_epoch, bad = ap, epoch, 0
                    best_state = copy.deepcopy(model.state_dict())
                else:
                    bad += 1
            history.append({"epoch": epoch, "train_BCE_pre_update": float(loss.detach()),
                            "validation_BCE_post_update": vl, "validation_drug_AP": ap,
                            "validation_AP_evaluable_drugs": nval,
                            "drug_message_gradient_norm": dm, "drug_projection_gradient_norm": dp,
                            "ppi_message_gradient_norm": pm, "atom_message_gradient_norm": am,
                            "optimizer_steps_cumulative": steps})
            if validation is not None and bad >= 20:
                break
        terminal_hash = state_hash(model.state_dict())
        if validation is not None:
            if best_state is None:
                status = "NA_validation_not_evaluable"
            else:
                model.load_state_dict(best_state)
        else:
            best_epoch, best_ap = limit, float("nan")
    except Exception:
        status, error = "NA_fit_exception", traceback.format_exc()
        terminal_hash = state_hash(model.state_dict())

    assert input_digest(train_input.graph, train_input.molecules) == train_input.digest
    if val_input is not None:
        assert input_digest(val_input.graph, val_input.molecules) == val_input.digest
    state = model.state_dict()

    def delta(prefix=""):
        return math.sqrt(sum(float(((state[k] - initial[k]).double() ** 2).sum())
                             for k in state if k.startswith(prefix)))

    info = {
        "status": status, "error": error, "initial_state_sha256": initial_hash,
        "selected_state_sha256": state_hash(state), "terminal_state_sha256": terminal_hash,
        "best_epoch": best_epoch, "best_validation_AP": best_ap, "epochs_run": len(history),
        "optimizer_steps": steps, "selected_state_L2_change": delta(),
        "drug_message_L2_change": delta("drug_message"),
        "drug_projection_L2_change": delta("drug_projection"),
        "maximum_drug_message_gradient_norm": max((r["drug_message_gradient_norm"] for r in history), default=0.0),
        "maximum_ppi_message_gradient_norm": max((r["ppi_message_gradient_norm"] for r in history), default=0.0),
        "maximum_atom_message_gradient_norm": max((r["atom_message_gradient_norm"] for r in history), default=0.0),
        "train_fit_drug_ids": fit_ids, "num_targets": len(targets),
        "train_observed_positive": int(y.sum()),
        "train_unknown_proxy_NOT_negative": int(y.size - y.sum()),
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "prepared_train_input_sha256": train_input.digest,
        "dtype": "float32", "semantics": SEMANTICS,
    }
    return model, pd.DataFrame(history), info


_STORE = None


def get_store():
    global _STORE
    if _STORE is None:
        _STORE = load_store()
    return _STORE


def context_arguments(job, source):
    graph = load_bundle(job["context"], "train")
    query = load_bundle(job["context"], "query")
    validate_bundle(graph, query)
    sources = json.loads((NULL / "training_preview_sources.json").read_text(encoding="utf-8"))[job["context"]]
    targets = sources["fittable_train_B2_PT"]
    fit_ids = sources["fit_eligible_train_ids"]
    val = val_labels = None
    if int(job["inner_fold"]) > 0:
        validation_ids = list(query["drug_ids"][query["split"] == "validation"])
        val = select_query(query, validation_ids, len(graph["protein_ids"]))
        val_labels = restrict_labels(source, list(val["drug_ids"][val["eligible"]]))
    return graph, query, targets, val, restrict_labels(source, fit_ids), val_labels, sources


def job_key(job):
    return f'{job["context"]}_{VARIANT}'


def run_job(job, source, fixed_epochs=None):
    key = job_key(job)
    path = MODEL / (key + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    base = {"job_key": key, "context": job["context"], "protocol": job["protocol"],
            "outer_fold": int(job["outer_fold"]), "inner_fold": int(job["inner_fold"]),
            "model": VARIANT, "seed": int(job["init_seed"]), "model_version": VERSION,
            "semantics": SEMANTICS, "threshold": 700, "fixed_outer_epochs": fixed_epochs,
            "approved_run_config_sha256": sha(QA / "run_config.json")}
    started = time.perf_counter()
    try:
        graph, query, targets, val, train_labels, val_labels, sources = context_arguments(job, source)
        model, history, info = fit_model(graph, train_labels, targets, int(job["init_seed"]),
                                         val, val_labels, fixed_epochs, store=get_store())
        MODEL.mkdir(parents=True, exist_ok=True)
        param_path = MODEL / (key + ".npz")
        np.savez_compressed(param_path, **{k: v.detach().cpu().numpy() for k, v in model.state_dict().items()})
        csv("history/" + key + ".csv", history)
        md = {**base, **info, "fitted_targets": targets,
              "parameters_file": param_path.relative_to(ROOT).as_posix(),
              "parameters_sha256": sha(param_path),
              "protein_ids": list(graph["protein_ids"]),
              "elapsed_seconds": time.perf_counter() - started}
    except Exception:
        md = {**base, "status": "NA_job_exception", "error": traceback.format_exc(),
              "elapsed_seconds": time.perf_counter() - started}
    write_json(path, md)
    return md


def training():
    run = json.loads((QA / "run_config.json").read_text(encoding="utf-8"))
    if not run["user_authorized_training"]:
        raise RuntimeError("Training not authorized")
    if (QA / "training_complete.json").exists():
        raise RuntimeError("GiG-1a v1 tamamlandı; sonuç güdümlü yeniden fit yok")
    (QA / "history").mkdir(parents=True, exist_ok=True)
    configure_runtime()
    arm = jobs_frame()
    source = source_labels()
    trace, decisions = [], []
    for protocol in ("primary", "stress"):
        for fold in range(1, 6):
            local = arm[arm.protocol.eq(protocol) & arm.outer_fold.eq(fold)]
            inner = []
            for job in local[local.inner_fold.gt(0)].to_dict("records"):
                md = run_job(job, source)
                inner.append(md)
                trace.append(md)
            common = [int(m["inner_fold"]) for m in inner
                      if m["status"] == "OK" and m.get("best_validation_AP") is not None
                      and math.isfinite(m["best_validation_AP"])]
            decision = {"protocol": protocol, "outer_fold": fold,
                        "actual_common_inner_folds": sorted(common),
                        "common_inner_count": len(common),
                        "status": "SELECTION_COMPLETE" if len(common) >= 2 else "NA_selection_insufficient",
                        "outer_epochs": None, "outer_test_labels_or_scores_used": False}
            if len(common) >= 2:
                epochs = [m["best_epoch"] for m in inner if m["inner_fold"] in common]
                decision["outer_epochs"] = int(math.floor(float(np.median(epochs)) + 0.5))
            write_json(QA / f"selections/{protocol}_o{fold:02}.json", decision)
            if decision["outer_epochs"] is not None:
                outer = [run_job(job, source, decision["outer_epochs"])
                         for job in local[local.inner_fold.eq(0)].to_dict("records")]
                trace.extend(outer)
                decision["outer_fit_OK"] = all(m["status"] == "OK" for m in outer) and len(outer) == 1
            else:
                decision["outer_fit_OK"] = False
            decisions.append(decision)
            print(f'GiG1a {protocol} outer{fold}: common inner={sorted(common)}; '
                  f'outer epochs={decision["outer_epochs"]}; outer OK={decision["outer_fit_OK"]}', flush=True)
    keep = ("job_key", "context", "protocol", "outer_fold", "inner_fold", "model", "seed", "status",
            "best_epoch", "best_validation_AP", "epochs_run", "optimizer_steps",
            "selected_state_L2_change", "drug_message_L2_change", "drug_projection_L2_change",
            "maximum_drug_message_gradient_norm", "maximum_ppi_message_gradient_norm",
            "maximum_atom_message_gradient_norm", "num_targets", "parameter_count", "elapsed_seconds")
    summary = pd.DataFrame([{k: m.get(k) for k in keep} for m in trace])
    csv("model_fit_summary.csv", summary)
    write_json(QA / "outer_fit_and_selection.json", decisions)
    write_json(QA / "selection_complete_before_test_scoring.json", {
        "selections": {p.relative_to(ROOT).as_posix(): sha(p) for p in (QA / "selections").glob("*.json")},
        "outer_test_scoring_performed": False})
    write_json(QA / "model_artifact_manifest.json",
               {p.relative_to(ROOT).as_posix(): sha(p) for p in MODEL.glob("*") if p.is_file()})
    write_json(QA / "training_complete.json", {
        "version": VERSION, "jobs_recorded": len(trace),
        "optimizer_steps": int(summary.optimizer_steps.fillna(0).sum()),
        "fit_status_counts": summary.status.value_counts().to_dict(),
        "outer_complete_count": sum(d["outer_fit_OK"] for d in decisions)})
    print(f"\nEğitim tamam: {len(trace)} iş, {int(summary.optimizer_steps.fillna(0).sum())} optimizer adımı")


# ------------------------------------------------------------ skorlama
def score_queries(md, graph, query):
    model = initialized_gig1(int(md["seed"]), num_targets=len(md["fitted_targets"]))
    with np.load(ROOT / md["parameters_file"], allow_pickle=False) as archive:
        model.load_state_dict({k: torch.from_numpy(archive[k].copy()) for k in archive.files})
    model.eval()
    store = get_store()
    train_input = prepare(model, graph, store.make_batch(graph["drug_ids"]))
    query_input = prepare(model, query, store.make_batch(query["drug_ids"]))
    with torch.no_grad():
        cache = train_forward(model, train_input)["protein_h"]
        logits = query_forward(model, query_input, cache)["logits"]
        return torch.sigmoid(logits).numpy()


def scoring():
    if not (QA / "training_complete.json").exists():
        raise RuntimeError("Önce eğitim tamamlanmalı")
    if (QA / "scoring_complete.json").exists():
        raise RuntimeError("Dış skorlar zaten dondurulmuş")
    committed = json.loads((QA / "selection_complete_before_test_scoring.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / p) == h for p, h in committed["selections"].items()), "Seçim dosyaları değişmiş"
    decisions = json.loads((QA / "outer_fit_and_selection.json").read_text(encoding="utf-8"))
    arm = jobs_frame()
    source = source_labels()
    configure_runtime()
    pred, status = [], []
    for decision in decisions:
        local = arm[arm.protocol.eq(decision["protocol"]) & arm.outer_fold.eq(decision["outer_fold"])
                    & arm.inner_fold.eq(0)]
        for job in local.to_dict("records"):
            graph = load_bundle(job["context"], "train")
            query = load_bundle(job["context"], "query")
            query = select_query(query, list(query["drug_ids"][query["split"] == "test"]),
                                 len(graph["protein_ids"]))
            md_path = MODEL / (job_key(job) + ".json")
            md = json.loads(md_path.read_text(encoding="utf-8")) if md_path.exists() else None
            scores = score_queries(md, graph, query) if decision["outer_fit_OK"] else None
            labels = restrict_labels(source, list(query["drug_ids"]))
            for i, drug in enumerate(query["drug_ids"]):
                s = ("ABSTAIN_no_input" if not query["eligible"][i]
                     else "SCORED" if scores is not None else "NA_outer_fit_or_selection")
                status.append({"protocol": job["protocol"], "outer_fold": int(job["outer_fold"]),
                               "model": VARIANT, "drug_id": drug, "status": s, "semantics": SEMANTICS})
                if s != "SCORED":
                    continue
                if not np.isfinite(scores[i]).all():
                    raise FloatingPointError("Outer scores nonfinite for eligible query")
                for c, value in zip(md["fitted_targets"], scores[i]):
                    pred.append({"protocol": job["protocol"], "outer_fold": int(job["outer_fold"]),
                                 "model": VARIANT, "drug_id": drug, "class_id": c,
                                 "observed_record_s": int(c in labels[drug]),
                                 "score_observed_record_proxy": float(value),
                                 "model_job_key": job_key(job), "outer_epochs": md["best_epoch"],
                                 "model_version": VERSION, "semantics": SEMANTICS})
    csv("oof_predictions.csv", pd.DataFrame(pred))
    csv("prediction_status.csv", pd.DataFrame(status))
    write_json(QA / "scoring_complete.json", {
        "predictions": len(pred),
        "selection_commit_sha256": sha(QA / "selection_complete_before_test_scoring.json"),
        "predictions_sha256": sha(QA / "oof_predictions.csv"),
        "model_refit_during_scoring": False})
    print(f"Dondurulmuş dış skorlama tamam: {len(pred)} çift")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["lock", "train", "score"])
    action = parser.parse_args().action
    {"lock": lock, "train": training, "score": scoring}[action]()
