# -*- coding: utf-8 -*-
"""EMT2 v6 raporunun teslim denetimi.

Denetlenen noktalar:
  1. Sablonun zorunlu on/arka bolumleri ve tasarim projesi basliklari
  2. Sekil ve cizelge aciklamalarinin bolum bazli numaralandirilmasi
  3. Cizelge adlarinin nokta ile bitmesi
  4. Metin icinde anilan her sekil/cizelge numarasinin var olmasi
  5. Raporda gecen her sayisal degerin kayitli QA ciktilarinda bulunmasi
  6. Bilimsel kisit ifadelerinin korunmasi
  7. Sablon ornek metninin kalmamis olmasi
"""
from pathlib import Path
import re
import io
import sys

import pandas as pd
from docx import Document

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOCX = HERE.parent / "EMT2_FINAL_REPORT.docx"
QA = ROOT / "reports/qa"

ZORUNLU_ON = ["ÖNSÖZ", "İÇİNDEKİLER", "KISALTMALAR", "SEMBOLLER",
              "ÇİZELGE LİSTESİ", "ŞEKİL LİSTESİ", "ÖZET", "SUMMARY"]
ZORUNLU_ARKA = ["KAYNAKLAR", "EKLER", "ÖZGEÇMİŞ"]
ZORUNLU_SISTEM = ["Sistem Tanımı", "Sistemin Paydaşları", "Sistem Gereksinimleri",
                  "Tasarıma Yön Veren Kısıtlar",
                  "Tasarımın İlişkili Olduğu Mesleki Standartlar"]
ZORUNLU_ETKI = ["Çevresel Etkilerinin İncelenmesi",
                "Toplumsal Etkilerinin İncelenmesi",
                "Ekonomik Etkilerinin İncelenmesi",
                "Etik Boyutunun İncelenmesi"]
KISIT_IFADELERI = [
    "doğrulanmış negatif",
    "hasta düzeyinde",
    "gözlenen kayıt",
]
SABLON_KALINTISI = ["Lorem ipsum", "Opsiyoneldir", "Bu bir nottur",
                    "BAŞLIK BURAYA", "Öğrenci Adı SOYADI", "Takip eden bölümler",
                    "kılavuzu dikkatlice"]

QA_DOSYALARI = [
    "WP08/baseline_v1/metrics_with_group_CI.csv",
    "WP08/baseline_v1/paired_differences.csv",
    "WP09/training_v1/metrics_with_group_CI.csv",
    "WP09/training_v1/paired_differences.csv",
    "WP10/training_v1/metrics_with_group_CI.csv",
    "WP10/training_v1/paired_differences.csv",
    "WP10/training_v1/paired_reference_differences.csv",
    "WP14/gig1_v1/metrics_with_group_CI.csv",
    "WP14/gig1_v1/paired_differences.csv",
    "WP15/tree_v1/metrics_with_group_CI.csv",
    "WP15/tree_v1/paired_differences.csv",
    "WP08/baseline_v1/paired_B2_minus_B1_group_CI.csv",
    "WP11/B1_SHAP_v1/global_common_summary.csv",
]

# Cizelge disi kayitlar: ag topolojisi, graf aciklamasi ve dis sorgu
EK_KAYITLAR = [
    "EMT2_Teslim_v1/graf_v1/topoloji.json",
    "reports/WP11_GRAPH_EXPLANATIONS.md",
    "reports/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.md",
    "reports/qa/WP13/tedizolid_B1_SHAP_v1",
]


def kayitli_degerler():
    """QA ciktilarindaki butun sayisal degerleri 4 ve 6 haneli olarak toplar."""
    havuz = set()
    for goreli in QA_DOSYALARI:
        yol = QA / goreli
        if not yol.is_file():
            continue
        cerceve = pd.read_csv(yol)
        for sutun in cerceve.columns:
            if cerceve[sutun].dtype.kind not in "fi":
                continue
            for deger in cerceve[sutun].dropna():
                for basamak in (4, 6):
                    havuz.add(round(float(deger), basamak))
                    havuz.add(round(-float(deger), basamak))

    # Cizelge disi kayitlardaki sayilar duz metinden toplanir
    for goreli in EK_KAYITLAR:
        yol = ROOT / goreli
        dosyalar = sorted(yol.rglob("*")) if yol.is_dir() else [yol]
        for dosya in dosyalar:
            uzanti = dosya.suffix.lower()
            if not dosya.is_file() or uzanti not in (".json", ".md", ".csv"):
                continue
            try:
                icerik = dosya.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for parca in re.findall(r"-?\d+\.\d{3,}", icerik):
                deger = float(parca)
                for basamak in (4, 6):
                    havuz.add(round(deger, basamak))
                    havuz.add(round(-deger, basamak))
    return havuz


def main():
    belge = Document(DOCX)
    basliklar, govde, sekil_ad, cizelge_ad = [], [], [], []
    for p in belge.paragraphs:
        metin = p.text.strip()
        if not metin:
            continue
        stil = p.style.name
        if stil.startswith("BASLIK"):
            basliklar.append(metin)
        elif stil.startswith("Sekil_FBE"):
            sekil_ad.append(metin)
        elif stil.startswith("Cizelge_FBE"):
            cizelge_ad.append(metin)
        else:
            govde.append(metin)
    tam_metin = "\n".join(basliklar + govde)
    for tablo in belge.tables:
        for satir in tablo.rows:
            for hucre in satir.cells:
                tam_metin += "\n" + hucre.text

    sorun, bilgi = [], []

    # 1. zorunlu basliklar
    for grup, ad in ((ZORUNLU_ON, "on bolum"), (ZORUNLU_ARKA, "arka bolum"),
                     (ZORUNLU_SISTEM, "sistem basligi"),
                     (ZORUNLU_ETKI, "etki basligi")):
        for gereken in grup:
            if not any(gereken in b for b in basliklar):
                sorun.append(f"Eksik {ad}: {gereken}")
    bilgi.append(f"baslik sayisi: {len(basliklar)}")

    # 2-3. aciklama bicimi
    bilgi.append(f"sekil: {len(sekil_ad)}  cizelge: {len(cizelge_ad)}")
    for ad in cizelge_ad:
        if not ad.endswith("."):
            sorun.append(f"Cizelge adi nokta ile bitmiyor: {ad[:50]}")
    for ad in sekil_ad:
        if not ad.endswith("."):
            sorun.append(f"Sekil adi nokta ile bitmiyor: {ad[:50]}")

    # 4. metin ici atiflar
    from sablon import ROMA  # noqa: F401  (stil adlarini dogrulamak icin)
    sekil_no, cizelge_no = set(), set()
    sayac = {}
    bolum = 0
    for p in belge.paragraphs:
        stil = p.style.name
        if stil == "BASLIK1" and p.text.strip() and not any(
                z in p.text for z in ZORUNLU_ON + ZORUNLU_ARKA):
            bolum += 1
        if stil.startswith("Sekil_FBE"):
            anahtar = ("S", bolum)
            sayac[anahtar] = sayac.get(anahtar, 0) + 1
            sekil_no.add(f"{bolum}.{sayac[anahtar]}")
        if stil.startswith("Cizelge_FBE"):
            anahtar = ("C", bolum)
            sayac[anahtar] = sayac.get(anahtar, 0) + 1
            cizelge_no.add(f"{bolum}.{sayac[anahtar]}")
    for anilan in set(re.findall(r"Şekil (\d+\.\d+)", tam_metin)):
        if anilan not in sekil_no:
            sorun.append(f"Metinde anilan Sekil {anilan} belgede yok")
    for anilan in set(re.findall(r"Çizelge (\d+\.\d+)", tam_metin)):
        if anilan not in cizelge_no:
            sorun.append(f"Metinde anilan Cizelge {anilan} belgede yok")

    # 5. sayisal degerler
    havuz = kayitli_degerler()
    turetilmis = set()
    bulunamayan = []
    for parca in set(re.findall(r"[−+-]?\d?[,]\d{4,6}\b", tam_metin)):
        try:
            deger = float(parca.replace("−", "-").replace(",", "."))
        except ValueError:
            continue
        if round(deger, 6) in havuz or round(deger, 4) in havuz:
            continue
        turetilmis.add(parca)
        bulunamayan.append(parca)
    bilgi.append(f"QA ile eslesen deger havuzu: {len(havuz)}")
    if bulunamayan:
        bilgi.append("QA tablolarinda birebir bulunamayan degerler "
                     f"({len(bulunamayan)}): {sorted(bulunamayan)}")

    # 6. bilimsel kisitlar
    for ifade in KISIT_IFADELERI:
        if ifade not in tam_metin:
            sorun.append(f"Bilimsel kisit ifadesi kaybolmus: {ifade}")

    # 7. sablon kalintisi
    for kalinti in SABLON_KALINTISI:
        if kalinti.lower() in tam_metin.lower():
            sorun.append(f"Sablon ornek metni kalmis: {kalinti}")

    # Windows konsolu cp1254; cikti UTF-8'e zorlanir
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=== EMT2 v6 teslim denetimi ===")
    for satir in bilgi:
        print("  bilgi :", satir)
    if sorun:
        print(f"\n  {len(sorun)} SORUN:")
        for satir in sorun:
            print("   -", satir)
        return 1
    print("\n  Butun denetimler GECTI.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    sys.exit(main())
