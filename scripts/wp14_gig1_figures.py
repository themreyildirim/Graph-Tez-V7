"""GiG-1a sonuç görselleri: AP karşılaştırması ve eşleştirilmiş farklar.

Yalnız kayıtlı metrik dosyalarını okur; model çalıştırmaz.
"""
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "reports/qa/WP14/gig1_v1"
OUT = ROOT / "reports/figures/WP14"

ACCENT = "#0f6e7d"
WARN = "#b4553f"
GREY = "#5b7682"
LIGHT = "#c3dae0"


def ap_figure():
    m = pd.read_csv(QA / "metrics_with_group_CI.csv")
    m = m[m.protocol.eq("primary") & m.scope.eq("paired54") & m.metric.eq("drug_macro_AP")]
    m = m.sort_values("estimate")
    labels = {"B0_like_B1": "B0 (sıklık, B1 paydası)", "B0_like_B2": "B0 (sıklık, B2 paydası)",
              "WP09_G_realPPI": "WP09 G_realPPI"}
    names = [labels.get(x, x) for x in m.model]
    colors = [WARN if x == "GiG1a" else (ACCENT if x == "A1P1" else GREY) for x in m.model]

    fig, ax = plt.subplots(figsize=(9.2, 4.6), dpi=150)
    y = range(len(m))
    ax.barh(list(y), m.estimate, color=colors, height=0.62, zorder=3)
    ax.errorbar(m.estimate, list(y), xerr=[m.estimate - m.CI95_low, m.CI95_high - m.estimate],
                fmt="none", ecolor="#2b4a52", elinewidth=1.3, capsize=4, zorder=4)
    for i, (v, name) in enumerate(zip(m.estimate, m.model)):
        ax.text(v + 0.004, i, f"{v:.4f}", va="center", fontsize=9,
                color=WARN if name == "GiG1a" else "#20383C",
                fontweight="bold" if name in ("GiG1a", "A1P1") else "normal")
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlim(0.50, 0.76)
    ax.set_xlabel("İlaç-makro gözlenen-kayıt AP (birincil protokol, ortak 54 ilaç)", fontsize=10)
    ax.set_title("GiG-1a ile dondurulmuş referansların karşılaştırması",
                 fontsize=12.5, fontweight="bold", color="#10303a", pad=12)
    ax.grid(axis="x", color=LIGHT, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LIGHT)
    fig.text(0.012, 0.02,
             "Hata çubukları koşullu %95 grup bootstrap aralığıdır (1.000 tekrar, sabit OOF). "
             "Skorlar SIDER kayıt sıralama vekilidir; klinik risk değildir.",
             fontsize=7.8, color=GREY)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    path = OUT / "04_gig1a_AP_karsilastirmasi.png"
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def difference_figure():
    d = pd.read_csv(QA / "paired_differences.csv")
    d = d[d.metric.eq("drug_macro_AP") & d.scope.eq("paired54")]
    order = ["A1P1", "A0P0", "WP09_G_realPPI", "B0_like_B1", "B0_like_B2", "B1", "B2"]
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.3), dpi=150, sharey=True)
    for ax, protocol in zip(axes, ("primary", "stress")):
        sub = d[d.protocol.eq(protocol)].set_index("reference").reindex(order).dropna(how="all")
        y = range(len(sub))
        for i, row in enumerate(sub.itertuples()):
            above = row.CI95_low > 0
            below = row.CI95_high < 0
            color = ACCENT if above else (WARN if below else GREY)
            ax.plot([row.CI95_low, row.CI95_high], [i, i], color=color, linewidth=2.2, zorder=3)
            ax.plot([row.first_minus_reference], [i], "o", color=color, markersize=6.5, zorder=4)
        ax.axvline(0, color="#2b4a52", linewidth=1.1, linestyle="--", zorder=2)
        ax.set_yticks(list(y))
        ax.set_yticklabels(sub.index, fontsize=9.5)
        ax.set_title("Birincil protokol" if protocol == "primary" else "Yapısal stres protokolü",
                     fontsize=11, fontweight="bold", color="#10303a")
        ax.set_xlabel("GiG-1a − referans (ilaç-makro AP)", fontsize=9.5)
        ax.grid(axis="x", color=LIGHT, linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(LIGHT)
    fig.suptitle("Eşleştirilmiş farklar — kırmızı: GiG-1a daha kötü, teal: daha iyi",
                 fontsize=12.5, fontweight="bold", color="#10303a", y=0.99)
    fig.text(0.012, 0.015,
             "Aralıklar koşullu %95 grup bootstrap; sıfırı içeren aralık eşdeğerlik kanıtı değildir.",
             fontsize=7.8, color=GREY)
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    path = OUT / "05_gig1a_farklar.png"
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for p in (ap_figure(), difference_figure()):
        print(f"  {p.relative_to(ROOT).as_posix()}  ({p.stat().st_size//1024} KB)")
