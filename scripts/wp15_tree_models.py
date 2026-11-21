"""WP15 — Ağaç tabanlı karşılaştırma modelleri (T1: RandomForest, T2: HistGradientBoosting).

Araştırma sorusu: Kimyasal tanımlayıcılar ile gözlenen yan etki kaydı
arasındaki ilişki, doğrusal bir modelin yakalayamayacağı eksen hizalı
etkileşimler içeriyor mu?

B1 ile **birebir aynı** girdi, bölme, hedef sözlüğü, uygunluk kuralı ve
etiket tanımı kullanılır; yalnız kestirici değişir. Böylece gözlenen fark
yalnız model sınıfına atfedilebilir.

Protokol sonuçlardan ÖNCE kilitlenir. Izgara dar ve sabittir; seçim
yalnız iç katlarda yapılır; dış test skoruna bakarak ayar yapılmaz.

Kullanım:
    python scripts/wp15_tree_models.py lock
    python scripts/wp15_tree_models.py train
    python scripts/wp15_tree_models.py score
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import platform
import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wp08_baseline_metrics import RankingCache

PREP = ROOT / "reports/qa/WP08/experimental_preparation"
QA = ROOT / "reports/qa/WP15/tree_v1"
MODEL = ROOT / "models/WP15_tree_v1"
VERSION = "WP15-tree-chemistry-baselines-v1"
SEMANTICS = (
    "Observed SIDER record ranking proxy; unknown NOT verified biological negative; "
    "NOT clinical risk; tabular comparison models on the frozen B1 feature set"
)
SEED = 20261106

# --- Önceden sabitlenmiş dar ızgara (sonuçlardan önce kilitlenir) ---
GRID = {
    "T1_RandomForest": [
        {"max_depth": 3, "min_samples_leaf": 1},
        {"max_depth": 3, "min_samples_leaf": 3},
        {"max_depth": None, "min_samples_leaf": 1},
        {"max_depth": None, "min_samples_leaf": 3},
    ],
    "T2_HistGradientBoosting": [
        {"max_depth": 2},
        {"max_depth": 3},
    ],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


# ------------------------------------------------------------------ veri
def load_inputs():
    parts = pd.read_csv(PREP / "nested_partitions_v1.csv")
    elig = pd.read_csv(PREP / "prediction_eligibility.csv")
    vocab = json.loads((PREP / "train_vocabularies.json").read_text(encoding="utf-8"))
    labels = pd.read_csv(ROOT / "reports/qa/WP03/drug_pt_positives.csv")
    labels = labels[labels.conservative][["id", "meddra_cui"]].rename(
        columns={"id": "drug_id", "meddra_cui": "class_id"})
    if labels.duplicated(["drug_id", "class_id"]).any():
        raise ValueError("Duplicate observed record")
    lookup = {c: set(f.drug_id) for c, f in labels.groupby("class_id")}
    eligible = set(elig[elig.model.eq("B1") & elig.eligible].drug_id)
    return parts, vocab, lookup, eligible


def features(context):
    with np.load(PREP / "features" / (context + ".npz"), allow_pickle=False) as a:
        return a["B1"].copy(), list(a["drug_ids"])


def proxy_matrix(ids, classes, lookup):
    # 0 = kaynakta kayıt yok; doğrulanmış negatif DEĞİL.
    return np.asarray([[int(d in lookup.get(c, set())) for c in classes] for d in ids], dtype=np.int8)


def drug_ap(y, scores):
    values = []
    for yy, ss in zip(y, scores):
        values.append(RankingCache(yy, ss, np.zeros(len(yy), dtype=int)).evaluate(np.ones(1))[0][0])
    values = np.asarray(values)
    return float(values[np.isfinite(values)].mean()) if np.isfinite(values).any() else float("nan")


def make_estimator(arm, params):
    """Kestirici kurulumu.

    HistGradientBoosting'de `early_stopping` KAPALIDIR. Dahili erken
    durdurma, eğitim kümesinden tabakalı bir doğrulama payı ayırır; 29-50
    ilaçlık eğitim kümelerinde seyrek hedeflerde bir sınıfın tek üyesi
    kaldığı için bu bölme başarısız olur. Düzenlileştirme bunun yerine
    `max_depth` (iç katta seçilir) ve sabit `max_iter` ile sağlanır.

    RandomForest'ta `n_jobs=1` kullanılır. Hız için `n_jobs=-1` denendi
    ancak determinizm kapısı BAŞARISIZ oldu: aynı `random_state` ile
    n_jobs=1 ve n_jobs=-1 birebir aynı olasılıkları vermedi. Tekrar
    üretilebilirlik hızdan önce geldiği için tek iş parçacığı seçildi.
    """
    if arm == "T1_RandomForest":
        return RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=1,
                                      bootstrap=True, **params)
    return HistGradientBoostingClassifier(learning_rate=0.1, max_iter=100,
                                          early_stopping=False,
                                          random_state=SEED, **params)


def fit_and_score(arm, params, X_train, y_train, X_query, targets):
    """PT başına bağımsız ikili sınıflandırıcı (B1 ile aynı kurulum)."""
    scores = np.full((len(X_query), len(targets)), np.nan)
    skipped = []
    for j, target in enumerate(targets):
        column = y_train[:, j]
        if column.min() == column.max():
            skipped.append(target)  # tek sonuç; B1'de de fit edilmez
            continue
        model = make_estimator(arm, params)
        model.fit(X_train, column)
        positive = list(model.classes_).index(1)
        scores[:, j] = model.predict_proba(X_query)[:, positive]
    return scores, skipped


# ------------------------------------------------------------------ kilit
def lock():
    if (QA / "run_config.json").exists():
        raise RuntimeError("Protokol zaten kilitli")
    config = {
        "version": VERSION,
        "semantics": SEMANTICS,
        "plan": "reports/EMT2_FINAL_REPORT_REWRITE_MASTER_PLAN.md",
        "user_authorized_training": True,
        "research_question": (
            "Kimyasal tanimlayicilar ile gozlenen kayit arasindaki iliski, dogrusal bir "
            "modelin yakalayamayacagi eksen hizali etkilesimler iceriyor mu?"
        ),
        "arms": list(GRID),
        "feature_set": "B1 ile birebir ayni: chem__MW, chem__LogP, chem__HBD, chem__HBA, chem__TPSA, mask__chemistry",
        "feature_source": "reports/qa/WP08/experimental_preparation/features/{context}.npz :: B1",
        "eligibility": "prediction_eligibility.csv :: model=B1 (54 ilac)",
        "targets": "train_vocabularies.json :: {context}.B1 (train-only)",
        "split": "frozen nested_partitions_v1.csv; 5 outer x 3 inner; drug-disjoint",
        "labels": "WP03 drug_pt_positives.csv (conservative)",
        "multilabel": "PT basina bagimsiz ikili siniflandirici",
        "grid": GRID,
        "grid_frozen_before_results": True,
        "fixed_estimator_settings": {
            "T1_RandomForest": {"n_estimators": 300, "bootstrap": True, "n_jobs": 1},
            "T2_HistGradientBoosting": {"learning_rate": 0.1, "max_iter": 100,
                                        "early_stopping": False},
        },
        "protocol_amendment_before_any_training": (
            "Ilk kilitte HistGradientBoosting early_stopping=True idi. Duman testinde, "
            "seyrek hedeflerde dahili tabakali dogrulama bolmesi tek uyeli sinif nedeniyle "
            "hata verdi. Hicbir egitim calistirilmadan once early_stopping=False ve "
            "max_iter=100 olarak degistirildi; duzenlilestirme max_depth ile ic katta "
            "secilir."
        ),
        "determinism_gate": (
            "RandomForest icin n_jobs=-1 hiz amaciyla denendi; ayni random_state ile "
            "n_jobs=1 ve n_jobs=-1 birebir ayni olasiliklari vermedigi icin kapi "
            "BASARISIZ oldu ve n_jobs=1 secildi. Tekrar uretilebilirlik hizdan oncedir."
        ),
        "selection": "yalniz ic kat drug_macro_AP ortalamasi",
        "seed": SEED,
        "primary_metric": "drug-macro observed-record AP on common 54 drugs",
        "secondary_metrics": ["micro_AP", "micro_AUROC", "class_macro_AP"],
        "acceptance": (
            "Yeni model otomatik olarak ana model olmaz. Ayirt edilebilirlik icin "
            "farkin kosullu %95 grup bootstrap araliginin sifiri icermemesi aranir."
        ),
        "frozen_models_retrained": False,
        "test_labels_in_training": False,
        "environment": {"python": platform.python_version(),
                        "sklearn": __import__("sklearn").__version__},
        "script_sha256": sha(ROOT / "scripts/wp15_tree_models.py"),
    }
    write_json(QA / "run_config.json", config)
    print(f"Protokol kilitlendi: {QA/'run_config.json'}")
    for arm, grid in GRID.items():
        print(f"  {arm}: {len(grid)} aday")


# ----------------------------------------------------------------- egitim
def training():
    run = json.loads((QA / "run_config.json").read_text(encoding="utf-8"))
    if not run["user_authorized_training"]:
        raise RuntimeError("Training not authorized")
    if (QA / "training_complete.json").exists():
        raise RuntimeError("WP15 v1 tamamlandi; sonuc gudumlu yeniden fit yok")
    parts, vocab, lookup, eligible = load_inputs()
    inner_rows, selections = [], []
    started = time.perf_counter()
    with threadpool_limits(limits=1):
        for protocol in ("primary", "stress"):
            for ofold in range(1, 6):
                for arm, grid in GRID.items():
                    per_candidate = {i: [] for i in range(len(grid))}
                    for ifold in range(1, 4):
                        context = f"{protocol}_o{ofold:02}_i{ifold:02}"
                        sub = parts[parts.context.eq(context)]
                        train_ids = sorted(set(sub[sub.split.eq("train")].drug_id) & eligible)
                        val_ids = sorted(set(sub[sub.split.eq("validation")].drug_id) & eligible)
                        targets = vocab[context]["B1"]
                        X, ids = features(context)
                        index = {d: i for i, d in enumerate(ids)}
                        Xtr = X[[index[d] for d in train_ids]]
                        Xva = X[[index[d] for d in val_ids]]
                        ytr = proxy_matrix(train_ids, targets, lookup)
                        yva = proxy_matrix(val_ids, targets, lookup)
                        for ci, params in enumerate(grid):
                            scores, skipped = fit_and_score(arm, params, Xtr, ytr, Xva, targets)
                            keep = ~np.isnan(scores).any(0)
                            ap = drug_ap(yva[:, keep], scores[:, keep]) if keep.any() else float("nan")
                            per_candidate[ci].append(ap)
                            inner_rows.append({"protocol": protocol, "outer_fold": ofold,
                                               "inner_fold": ifold, "context": context, "arm": arm,
                                               "candidate": ci, "params": json.dumps(params),
                                               "drug_macro_AP": ap, "targets": len(targets),
                                               "skipped_single_outcome": len(skipped)})
                    means = {ci: float(np.nanmean(v)) if np.isfinite(v).any() else float("nan")
                             for ci, v in per_candidate.items()}
                    best = max((ci for ci in means if math.isfinite(means[ci])),
                               key=lambda ci: means[ci], default=None)
                    selections.append({"protocol": protocol, "outer_fold": ofold, "arm": arm,
                                       "selected_candidate": best,
                                       "selected_params": json.dumps(grid[best]) if best is not None else "",
                                       "inner_means": json.dumps({str(k): v for k, v in means.items()}),
                                       "status": "selected_inner_only" if best is not None else "NA",
                                       "outer_test_used": False, "semantics": SEMANTICS})
                print(f"WP15 ic secim tamam: {protocol} outer {ofold}/5", flush=True)
    csv("inner_selection_metrics.csv", pd.DataFrame(inner_rows))
    csv("selected_candidates.csv", pd.DataFrame(selections))
    write_json(QA / "selection_complete_before_test_scoring.json", {
        "selected_candidates_sha256": sha(QA / "selected_candidates.csv"),
        "outer_test_scoring_performed": False})
    write_json(QA / "training_complete.json", {
        "version": VERSION, "inner_fits": len(inner_rows),
        "seconds": time.perf_counter() - started})
    print(f"\nIc secim tamam: {len(inner_rows)} aday-kat degerlendirmesi, "
          f"{time.perf_counter()-started:.0f} s")


# --------------------------------------------------------------- skorlama
def scoring():
    if not (QA / "training_complete.json").exists():
        raise RuntimeError("Once ic secim tamamlanmali")
    if (QA / "scoring_complete.json").exists():
        raise RuntimeError("Dis skorlar zaten dondurulmus")
    committed = json.loads((QA / "selection_complete_before_test_scoring.json").read_text(encoding="utf-8"))
    assert sha(QA / "selected_candidates.csv") == committed["selected_candidates_sha256"], "Secim degismis"
    parts, vocab, lookup, eligible = load_inputs()
    selections = pd.read_csv(QA / "selected_candidates.csv", keep_default_na=False)
    MODEL.mkdir(parents=True, exist_ok=True)
    pred, status = [], []
    with threadpool_limits(limits=1):
        for row in selections.itertuples():
            if row.status != "selected_inner_only":
                continue
            context = f"{row.protocol}_o{row.outer_fold:02}_final"
            sub = parts[parts.context.eq(context)]
            train_ids = sorted(set(sub[sub.split.eq("train")].drug_id) & eligible)
            test_all = sorted(set(sub[sub.split.eq("test")].drug_id))
            test_ids = [d for d in test_all if d in eligible]
            targets = vocab[context]["B1"]
            X, ids = features(context)
            index = {d: i for i, d in enumerate(ids)}
            Xtr = X[[index[d] for d in train_ids]]
            Xte = X[[index[d] for d in test_ids]]
            ytr = proxy_matrix(train_ids, targets, lookup)
            params = json.loads(row.selected_params)
            scores, skipped = fit_and_score(row.arm, params, Xtr, ytr, Xte, targets)
            write_json(MODEL / f"{context}_{row.arm}.json", {
                "context": context, "arm": row.arm, "params": params, "seed": SEED,
                "train_drug_ids": train_ids, "targets": targets,
                "skipped_single_outcome": skipped, "model_version": VERSION,
                "semantics": SEMANTICS})
            for d in test_all:
                s = "SCORED" if d in eligible else "ABSTAIN_no_chemistry"
                status.append({"protocol": row.protocol, "outer_fold": row.outer_fold,
                               "model": row.arm, "drug_id": d, "status": s})
            for i, d in enumerate(test_ids):
                for j, c in enumerate(targets):
                    if not np.isfinite(scores[i, j]):
                        continue
                    pred.append({"protocol": row.protocol, "outer_fold": int(row.outer_fold),
                                 "model": row.arm, "drug_id": d, "class_id": c,
                                 "observed_record_s": int(d in lookup.get(c, set())),
                                 "score_observed_record_proxy": float(scores[i, j]),
                                 "model_version": VERSION, "semantics": SEMANTICS})
    csv("oof_predictions.csv", pd.DataFrame(pred))
    csv("prediction_status.csv", pd.DataFrame(status))
    write_json(QA / "scoring_complete.json", {
        "predictions": len(pred),
        "predictions_sha256": sha(QA / "oof_predictions.csv"),
        "model_refit_during_scoring": False})
    print(f"Dondurulmus dis skorlama tamam: {len(pred)} cift")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["lock", "train", "score"])
    {"lock": lock, "train": training, "score": scoring}[parser.parse_args().action]()
