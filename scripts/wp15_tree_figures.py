"""WP15 agac modeli sonuc sekilleri.

Yalnizca dondurulmus WP15 degerlendirme cikislarini okur; hicbir sey
yeniden hesaplanmaz veya egitilmez.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "reports/qa/WP15/tree_v1"
FIG = ROOT / "reports/figures/WP15"
PRIMARY = "drug_macro_AP"

ADLAR = {
    "T1_RandomForest": "T1 Rastgele orman",
    "T2_HistGradientBoosting": "T2 Gradyan artirma",
    "B1": "B1 Kimya + lojistik",
    "B2": "B2 Kimya + protein",
    "A1P1": "A1P1 Atom + PPI",
    "GiG1a": "GiG-1a bilgi aktarimi",
    "B0_like_B1": "B0 siklik (B1 kapsami)",
    "B0_like_B2": "B0 siklik (B2 kapsami)",
}
VURGU = {"T1_RandomForest": "#1b5e20", "T2_HistGradientBoosting": "#7c3f00"}
# Fark grafiginde kullanilan kisa etiketler; iki B0 referansi ayirt edilir
KISA = {
    "T1_RandomForest": "T1", "T2_HistGradientBoosting": "T2",
    "B1": "B1", "B2": "B2", "A1P1": "A1P1", "GiG1a": "GiG-1a",
    "B0_like_B1": "B0(B1 kapsami)", "B0_like_B2": "B0(B2 kapsami)",
}


def ad(x):
    return ADLAR.get(x, x)


def sekil_ap(metrikler):
    fig, eksenler = plt.subplots(1, 2, figsize=(12.4, 5.0), sharex=True)
    for eksen, protokol, baslik in zip(
            eksenler, ("primary", "stress"),
            ("Birincil protokol (baglanti kilitli gruplar)",
             "Stres protokolu (iskelet / Tanimoto >= 0,8)")):
        s = metrikler[(metrikler.protocol == protokol)
                      & (metrikler.scope == "paired54")
                      & (metrikler.metric == PRIMARY)].sort_values("estimate")
        y = range(len(s))
        renkler = [VURGU.get(m, "#9e9e9e") for m in s.model]
        eksen.barh(list(y), s.estimate, color=renkler, height=0.62)
        eksen.errorbar(s.estimate, list(y),
                       xerr=[s.estimate - s.CI95_low, s.CI95_high - s.estimate],
                       fmt="none", ecolor="#37474f", elinewidth=1.1, capsize=3)
        eksen.set_yticks(list(y))
        eksen.set_yticklabels([ad(m) for m in s.model], fontsize=8.5)
        eksen.set_xlim(0.50, 0.76)
        eksen.set_xlabel("Ilac-makro ortalama kesinlik", fontsize=9)
        eksen.set_title(baslik, fontsize=9.5)
        eksen.grid(axis="x", alpha=0.25, linewidth=0.6)
        for omurga in ("top", "right"):
            eksen.spines[omurga].set_visible(False)
        # Deger etiketleri sabit sutunda durur; hata cubugu uclariyla cakismaz
        for yi, v in zip(y, s.estimate):
            eksen.text(0.734, yi, f"{v:.4f}", va="center", ha="right",
                       fontsize=8.0, color="#263238")
    fig.suptitle("Agac tabanli kollarin dondurulmus referanslarla karsilastirmasi\n"
                 "(cubuklar nokta tahmini, cizgiler kosullu %95 grup bootstrap araligi)",
                 fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    yol = FIG / "01_agac_AP_karsilastirmasi.png"
    fig.savefig(yol, dpi=200)
    plt.close(fig)
    return yol


def sekil_farklar(farklar):
    fig, eksenler = plt.subplots(1, 2, figsize=(12.4, 4.4), sharex=True)
    for eksen, protokol, baslik in zip(
            eksenler, ("primary", "stress"),
            ("Birincil protokol", "Stres protokolu")):
        s = farklar[(farklar.protocol == protokol)
                    & (farklar.scope == "paired54")
                    & (farklar.metric == PRIMARY)].copy()
        s["etiket"] = [f"{KISA.get(a, a)} − {KISA.get(b, b)}"
                       for a, b in zip(s.first, s.reference)]
        s = s.iloc[::-1]
        y = range(len(s))
        ayirt = (s.CI95_low * s.CI95_high) > 0
        renkler = ["#1b5e20" if (a and v > 0) else "#b71c1c" if a else "#9e9e9e"
                   for a, v in zip(ayirt, s.first_minus_reference)]
        eksen.errorbar(s.first_minus_reference, list(y),
                       xerr=[s.first_minus_reference - s.CI95_low,
                             s.CI95_high - s.first_minus_reference],
                       fmt="o", ms=4, ecolor="#546e7a", elinewidth=1.1,
                       capsize=3, linestyle="none", mfc="none", mec="#546e7a")
        for yi, v, c in zip(y, s.first_minus_reference, renkler):
            eksen.plot([v], [yi], "o", ms=5.5, color=c)
        eksen.axvline(0, color="#263238", linewidth=1.0)
        eksen.set_yticks(list(y))
        eksen.set_yticklabels(s.etiket, fontsize=7.8)
        eksen.set_xlabel("Eslestirilmis fark (ilac-makro AP)", fontsize=9)
        eksen.set_title(baslik, fontsize=9.5)
        eksen.grid(axis="x", alpha=0.25, linewidth=0.6)
        for omurga in ("top", "right"):
            eksen.spines[omurga].set_visible(False)
    fig.suptitle("Eslestirilmis farklar: yesil = aralik tumuyle sifirin ustunde, "
                 "kirmizi = tumuyle altinda, gri = sifiri iceriyor", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    yol = FIG / "02_agac_eslestirilmis_farklar.png"
    fig.savefig(yol, dpi=200)
    plt.close(fig)
    return yol


def sekil_iki_yon(metrikler):
    fig, eksen = plt.subplots(figsize=(8.6, 5.0))
    s = metrikler[(metrikler.protocol == "primary")
                  & (metrikler.scope == "paired54")]
    ilac = s[s.metric == PRIMARY].set_index("model").estimate
    sinif = s[s.metric == "class_macro_AP"].set_index("model").estimate
    ortak = [m for m in ilac.index if m in sinif.index]
    # Birbirine cok yakin duran iki siklik referansinin etiketi ayrilir
    kaydir = {"B0_like_B1": (7, 7, "left"), "B0_like_B2": (7, -12, "left"),
              "T1_RandomForest": (-9, 6, "right"),
              "B1": (0, -16, "center"),
              "A1P1": (9, -11, "left"),
              "GiG1a": (0, 11, "center")}
    for m in ortak:
        renk = VURGU.get(m, "#607d8b")
        buyuk = m in VURGU
        eksen.scatter(ilac[m], sinif[m], s=120 if buyuk else 55, color=renk,
                      zorder=3, edgecolor="white", linewidth=1.0)
        dx, dy, hiza = kaydir.get(m, (7, -3, "left"))
        eksen.annotate(ad(m), (ilac[m], sinif[m]), fontsize=8, ha=hiza,
                       xytext=(dx, dy), textcoords="offset points")
    eksen.margins(x=0.10, y=0.10)
    eksen.set_xlabel("Ilac yonu — ilac-makro AP (birincil olcut)", fontsize=9.5)
    eksen.set_ylabel("Terim yonu — sinif-makro AP (betimleyici)", fontsize=9.5)
    eksen.set_title("Iki siralama yonu ayni dondurulmus skorlardan okunur\n"
                    "Terim yonunde bagimsiz guven araligi uretilmemistir",
                    fontsize=10)
    eksen.grid(alpha=0.25, linewidth=0.6)
    for omurga in ("top", "right"):
        eksen.spines[omurga].set_visible(False)
    fig.tight_layout()
    yol = FIG / "03_agac_iki_yon.png"
    fig.savefig(yol, dpi=200)
    plt.close(fig)
    return yol


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    metrikler = pd.read_csv(QA / "metrics_with_group_CI.csv")
    farklar = pd.read_csv(QA / "paired_differences.csv")
    for yol in (sekil_ap(metrikler), sekil_farklar(farklar),
                sekil_iki_yon(metrikler)):
        print("yazildi:", yol.relative_to(ROOT))


if __name__ == "__main__":
    main()
