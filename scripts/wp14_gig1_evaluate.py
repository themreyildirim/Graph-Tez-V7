"""GiG-1a'nın dondurulmuş A1P1/B1/B2/B0 skorlarıyla eşleştirilmiş karşılaştırması.

Karşılaştırma anahtarları WP10'un dondurulmuş `comparison_keys.csv`
dosyasından alınır; yeni bir kapsam tanımlanmaz. Bootstrap ağırlıkları
aynı tohum ve aynı yapısal gruplarla üretilir. Hiçbir model yeniden
eğitilmez; yalnız kayıtlı skorlar okunur.
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
from wp14_gig1_train import QA, VERSION, SEMANTICS, write_json, csv

WP10_QA = ROOT / "reports/qa/WP10/training_v1"
WP08 = ROOT / "reports/qa/WP08"
WP09 = ROOT / "reports/qa/WP09/training_v1"
PRIMARY = "drug_macro_AP"


def main():
    if not (QA / "scoring_complete.json").exists():
        raise RuntimeError("Önce dondurulmuş skorlama tamamlanmalı")
    if (QA / "evaluation_complete.json").exists():
        raise RuntimeError("Değerlendirme zaten dondurulmuş")
    started = time.perf_counter()

    new = pd.read_csv(QA / "oof_predictions.csv")
    a1p1 = pd.read_csv(WP10_QA / "oof_predictions.csv")
    old = pd.read_csv(WP08 / "baseline_v1/oof_predictions.csv")
    old = old[old.family.eq("PT")]
    freq = pd.read_csv(WP08 / "B0_frequency_reference_v1/B0_outer_query_scores.csv").rename(
        columns={"pt_cui": "class_id"}
    )
    wp09 = pd.read_csv(WP09 / "oof_predictions.csv")
    keys_all = pd.read_csv(WP10_QA / "comparison_keys.csv")

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
            part = new[new.protocol.eq(protocol) & np.isfinite(new.score_observed_record_proxy)]
            covered = keys.merge(part[columns], on=columns, how="left", indicator=True)
            missing = int((covered._merge == "left_only").sum())
            coverage.append({"protocol": protocol, "scope": scope, "frozen_keys": len(keys),
                             "gig1a_missing_keys": missing,
                             "comparison_valid": missing == 0,
                             "note": "dondurulmuş WP10 anahtarları; yeni kapsam tanımlanmadı"})
            if missing:
                print(f"UYARI {protocol}/{scope}: GiG1a {missing} anahtarı kapsamıyor; bu kapsam atlandı")
                continue

            frames = {
                "GiG1a": (part, "score_observed_record_proxy"),
                "A1P1": (a1p1[a1p1.protocol.eq(protocol) & a1p1.model.eq("A1P1")], "score_observed_record_proxy"),
                "A0P0": (a1p1[a1p1.protocol.eq(protocol) & a1p1.model.eq("A0P0")], "score_observed_record_proxy"),
                "B2": (old[old.protocol.eq(protocol) & old.model.eq("B2")], "score_observed_record_proxy"),
            }
            if scope == "paired54":
                frames["B1"] = (old[old.protocol.eq(protocol) & old.model.eq("B1")], "score_observed_record_proxy")
                frames["B0_like_B1"] = (freq[freq.protocol.eq(protocol) & freq.reference.eq("B0_like_B1")], "frequency_score")
            frames["B0_like_B2"] = (freq[freq.protocol.eq(protocol) & freq.reference.eq("B0_like_B2")], "frequency_score")
            frames["WP09_G_realPPI"] = (wp09[wp09.protocol.eq(protocol) & wp09.model.eq("G_realPPI")], "score_observed_record_proxy")

            panels = {name: make_panel(f, keys, ids, truth, c) for name, (f, c) in frames.items()}
            mask = next(iter(panels.values())).mask
            assert all(np.array_equal(mask, p.mask) for p in panels.values()), "Kapsam maskeleri farklı"

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
                                    "CI_NA_reason": reason, "semantics": SEMANTICS,
                                    "CI_scope": "paired structural groups;fixed OOF conditional"})

            references = ["A1P1", "A0P0", "B2", "B0_like_B2", "WP09_G_realPPI"]
            if scope == "paired54":
                references += ["B1", "B0_like_B1"]
            for reference in references:
                for metric in ("drug_macro_AP", "micro_AP", "micro_AUROC"):
                    value = points["GiG1a"][metric] - points[reference][metric]
                    samples = boots["GiG1a"][metric] - boots[reference][metric]
                    lo, hi, n, reason = percentile_interval(samples, 800)
                    deltas.append({"protocol": protocol, "scope": scope,
                                   "first": "GiG1a", "reference": reference, "metric": metric,
                                   "first_minus_reference": value, "CI95_low": lo, "CI95_high": hi,
                                   "valid_bootstrap_replicates": n, "CI_NA_reason": reason,
                                   "semantics": SEMANTICS,
                                   "interpretation": "difference of observed-record metrics;not biological causality"})

    csv("metrics_with_group_CI.csv", pd.DataFrame(metrics))
    csv("paired_differences.csv", pd.DataFrame(deltas))
    csv("comparison_coverage.csv", pd.DataFrame(coverage))

    # --- önceden kilitlenmiş kabul kriteri ---
    frame = pd.DataFrame(deltas)
    primary = frame[frame.protocol.eq("primary") & frame.scope.eq("paired54")
                    & frame.reference.eq("A1P1") & frame.metric.eq(PRIMARY)]
    stress = frame[frame.protocol.eq("stress") & frame.scope.eq("paired54")
                   & frame.reference.eq("A1P1") & frame.metric.eq(PRIMARY)]
    verdict = {"criterion": json.loads((QA / "run_config.json").read_text(encoding="utf-8"))["acceptance_criterion"]}
    if len(primary) == 1 and len(stress) == 1:
        p = primary.iloc[0]
        s = stress.iloc[0]
        ci_above_zero = p.CI95_low is not None and float(p.CI95_low) > 0
        stress_not_negative = float(s.first_minus_reference) >= 0
        verdict.update({
            "primary_difference": float(p.first_minus_reference),
            "primary_CI95": [None if p.CI95_low is None else float(p.CI95_low),
                             None if p.CI95_high is None else float(p.CI95_high)],
            "stress_difference": float(s.first_minus_reference),
            "primary_CI_strictly_above_zero": bool(ci_above_zero),
            "stress_point_estimate_not_negative": bool(stress_not_negative),
            "accepted": bool(ci_above_zero and stress_not_negative),
        })
        verdict["conclusion"] = ("GiG1a kabul kriterini KARŞILADI" if verdict["accepted"]
                                 else "Ek katkı gösterilemedi; A1P1 ana araştırma mimarisi olarak korunur")
    else:
        verdict["accepted"] = False
        verdict["conclusion"] = "Birincil karşılaştırma üretilemedi"
    write_json(QA / "acceptance_verdict.json", verdict)

    write_json(QA / "evaluation_complete.json", {
        "version": VERSION, "seconds": time.perf_counter() - started,
        "bootstrap_replicates": 1000, "no_refit": True,
        "comparison_keys_source": "reports/qa/WP10/training_v1/comparison_keys.csv",
        "comparison_keys_sha256": sha(WP10_QA / "comparison_keys.csv"),
        "metrics_sha256": sha(QA / "metrics_with_group_CI.csv"),
        "differences_sha256": sha(QA / "paired_differences.csv")})

    print("\n=== Birincil sonuç (primary / paired54 / drug_macro_AP) ===")
    show = pd.DataFrame(metrics)
    show = show[show.protocol.eq("primary") & show.scope.eq("paired54") & show.metric.eq(PRIMARY)]
    for row in show.sort_values("estimate", ascending=False).itertuples():
        lo = "NA" if row.CI95_low is None else f"{row.CI95_low:.4f}"
        hi = "NA" if row.CI95_high is None else f"{row.CI95_high:.4f}"
        print(f"  {row.model:<16} {row.estimate:.6f}   [{lo}; {hi}]")
    print("\n=== GiG1a - referans farklari ===")
    for row in primary.itertuples():
        print(f"  vs A1P1: {row.first_minus_reference:+.6f}  [{row.CI95_low:+.6f}; {row.CI95_high:+.6f}]")
    print(f"\nKARAR: {verdict['conclusion']}")


if __name__ == "__main__":
    main()
