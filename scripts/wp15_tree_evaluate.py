"""WP15 ağaç modellerinin dondurulmuş referanslarla eşleştirilmiş karşılaştırması.

Karşılaştırma anahtarları WP10'un dondurulmuş `comparison_keys.csv`
dosyasından alınır; yeni kapsam tanımlanmaz. Bootstrap ağırlıkları aynı
tohum ve aynı yapısal gruplarla üretilir. Hiçbir model yeniden eğitilmez.
"""
from pathlib import Path
import json
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wp08_baseline_metrics import grouped_bootstrap_weights, percentile_interval
from wp09_train_evaluate import make_panel, bootstrap_primary
from wp10_train import source_labels, PREP, sha
from wp15_tree_models import QA, VERSION, SEMANTICS, write_json, csv

WP10_QA = ROOT / "reports/qa/WP10/training_v1"
WP08 = ROOT / "reports/qa/WP08"
WP14 = ROOT / "reports/qa/WP14/gig1_v1"
ARMS = ["T1_RandomForest", "T2_HistGradientBoosting"]
PRIMARY = "drug_macro_AP"


def main():
    if not (QA / "scoring_complete.json").exists():
        raise RuntimeError("Once dondurulmus skorlama tamamlanmali")
    if (QA / "evaluation_complete.json").exists():
        raise RuntimeError("Degerlendirme zaten dondurulmus")
    started = time.perf_counter()

    new = pd.read_csv(QA / "oof_predictions.csv")
    a1p1 = pd.read_csv(WP10_QA / "oof_predictions.csv")
    old = pd.read_csv(WP08 / "baseline_v1/oof_predictions.csv")
    old = old[old.family.eq("PT")]
    freq = pd.read_csv(WP08 / "B0_frequency_reference_v1/B0_outer_query_scores.csv").rename(
        columns={"pt_cui": "class_id"})
    keys_all = pd.read_csv(WP10_QA / "comparison_keys.csv")
    gig = pd.read_csv(WP14 / "oof_predictions.csv") if (WP14 / "oof_predictions.csv").is_file() else None

    source = source_labels()
    truth = {d: set(f.class_id) for d, f in source.groupby("drug_id")}
    membership = pd.read_csv(PREP / "outer_membership_v1.csv")

    columns = ["outer_fold", "drug_id", "class_id"]
    metrics, deltas, coverage = [], [], []

    for pi, protocol in enumerate(("primary", "stress")):
        members = membership[membership.protocol.eq(protocol)].sort_values("drug_id")
        ids = list(members.drug_id)
        groups = dict(zip(members.drug_id, members.group_id))
        weights = grouped_bootstrap_weights(ids, groups, 1000, 20261106 + 9000 + pi)

        for scope in ("paired54", "own61"):
            keys = keys_all[keys_all.protocol.eq(protocol) & keys_all.scope.eq(scope)][columns].copy()
            ok = True
            for arm in ARMS:
                part = new[new.protocol.eq(protocol) & new.model.eq(arm)
                           & np.isfinite(new.score_observed_record_proxy)]
                covered = keys.merge(part[columns], on=columns, how="left", indicator=True)
                missing = int((covered._merge == "left_only").sum())
                coverage.append({"protocol": protocol, "scope": scope, "arm": arm,
                                 "frozen_keys": len(keys), "missing_keys": missing,
                                 "comparison_valid": missing == 0})
                if missing:
                    ok = False
            if not ok:
                print(f"UYARI {protocol}/{scope}: agac kollari anahtarlari kapsamiyor; atlandi")
                continue

            frames = {arm: (new[new.protocol.eq(protocol) & new.model.eq(arm)],
                            "score_observed_record_proxy") for arm in ARMS}
            frames["A1P1"] = (a1p1[a1p1.protocol.eq(protocol) & a1p1.model.eq("A1P1")],
                              "score_observed_record_proxy")
            frames["B2"] = (old[old.protocol.eq(protocol) & old.model.eq("B2")],
                            "score_observed_record_proxy")
            if scope == "paired54":
                frames["B1"] = (old[old.protocol.eq(protocol) & old.model.eq("B1")],
                                "score_observed_record_proxy")
                frames["B0_like_B1"] = (freq[freq.protocol.eq(protocol)
                                             & freq.reference.eq("B0_like_B1")], "frequency_score")
            frames["B0_like_B2"] = (freq[freq.protocol.eq(protocol)
                                         & freq.reference.eq("B0_like_B2")], "frequency_score")
            if gig is not None:
                sub = gig[gig.protocol.eq(protocol)]
                if len(keys.merge(sub[columns], on=columns, how="inner")) == len(keys):
                    frames["GiG1a"] = (sub, "score_observed_record_proxy")

            panels = {name: make_panel(f, keys, ids, truth, c) for name, (f, c) in frames.items()}
            mask = next(iter(panels.values())).mask
            assert all(np.array_equal(mask, p.mask) for p in panels.values()), "Kapsam maskeleri farkli"

            points, boots = {}, {}
            for name, panel in panels.items():
                points[name] = {k: float(v[0]) for k, v in panel.evaluate().items()}
                boots[name] = bootstrap_primary(panel, weights)
                for metric, value in points[name].items():
                    if metric in boots[name]:
                        lo, hi, n, reason = percentile_interval(boots[name][metric], 800)
                    else:
                        lo = hi = None
                        n, reason = 0, "descriptive class metric;no independent-fold CI"
                    metrics.append({"protocol": protocol, "scope": scope, "model": name,
                                    "metric": metric, "estimate": value, "CI95_low": lo,
                                    "CI95_high": hi, "valid_bootstrap_replicates": n,
                                    "CI_NA_reason": reason, "semantics": SEMANTICS})

            references = [r for r in ("B1", "A1P1", "B0_like_B2", "B0_like_B1", "B2", "GiG1a")
                          if r in points]
            for arm in ARMS:
                for reference in references:
                    for metric in ("drug_macro_AP", "micro_AP", "micro_AUROC"):
                        value = points[arm][metric] - points[reference][metric]
                        samples = boots[arm][metric] - boots[reference][metric]
                        lo, hi, n, reason = percentile_interval(samples, 800)
                        deltas.append({"protocol": protocol, "scope": scope, "first": arm,
                                       "reference": reference, "metric": metric,
                                       "first_minus_reference": value, "CI95_low": lo,
                                       "CI95_high": hi, "valid_bootstrap_replicates": n,
                                       "CI_NA_reason": reason, "semantics": SEMANTICS})

    csv("metrics_with_group_CI.csv", pd.DataFrame(metrics))
    csv("paired_differences.csv", pd.DataFrame(deltas))
    csv("comparison_coverage.csv", pd.DataFrame(coverage))

    frame = pd.DataFrame(deltas)
    verdict = {"criterion": json.loads((QA / "run_config.json").read_text(encoding="utf-8"))["acceptance"],
               "arms": {}}
    for arm in ARMS:
        row = frame[frame.protocol.eq("primary") & frame.scope.eq("paired54")
                    & frame.first.eq(arm) & frame.reference.eq("B1") & frame.metric.eq(PRIMARY)]
        vs_a = frame[frame.protocol.eq("primary") & frame.scope.eq("paired54")
                     & frame.first.eq(arm) & frame.reference.eq("A1P1") & frame.metric.eq(PRIMARY)]
        if len(row) == 1:
            r = row.iloc[0]
            distinguishable = bool(r.CI95_low is not None and float(r.CI95_low) * float(r.CI95_high) > 0)
            verdict["arms"][arm] = {
                "vs_B1_difference": float(r.first_minus_reference),
                "vs_B1_CI95": [float(r.CI95_low), float(r.CI95_high)],
                "vs_B1_distinguishable": distinguishable,
                "vs_A1P1_difference": float(vs_a.iloc[0].first_minus_reference) if len(vs_a) == 1 else None,
            }
    write_json(QA / "acceptance_verdict.json", verdict)
    write_json(QA / "evaluation_complete.json", {
        "version": VERSION, "seconds": time.perf_counter() - started,
        "bootstrap_replicates": 1000, "no_refit": True,
        "comparison_keys_sha256": sha(WP10_QA / "comparison_keys.csv"),
        "metrics_sha256": sha(QA / "metrics_with_group_CI.csv")})

    show = pd.DataFrame(metrics)
    show = show[show.protocol.eq("primary") & show.scope.eq("paired54") & show.metric.eq(PRIMARY)]
    print("\n=== primary / paired54 / drug_macro_AP ===")
    for row in show.sort_values("estimate", ascending=False).itertuples():
        lo = "NA" if row.CI95_low is None else f"{row.CI95_low:.4f}"
        hi = "NA" if row.CI95_high is None else f"{row.CI95_high:.4f}"
        print(f"  {row.model:<24} {row.estimate:.6f}   [{lo}; {hi}]")
    print("\n=== sinif-makro AP (terim yonu) ===")
    cls = pd.DataFrame(metrics)
    cls = cls[cls.protocol.eq("primary") & cls.scope.eq("paired54") & cls.metric.eq("class_macro_AP")]
    for row in cls.sort_values("estimate", ascending=False).itertuples():
        print(f"  {row.model:<24} {row.estimate:.6f}")


if __name__ == "__main__":
    main()
