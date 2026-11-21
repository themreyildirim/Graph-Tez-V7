"""EMT2 teknik dogrulama arsivi dizinini uretir.

Ana rapordan cikarilan teknik icerik (kanit dizinleri, hash listeleri,
dosya yollari, test sayilari, is paketi kodlari) silinmez; bu betik
bunlara isaret eden tek bir dizin belgesi ve kaynak-bolum eslestirme
cizelgesi uretir.

Yalnizca OKUR ve yeni bir dizine YAZAR. Hicbir mevcut dosya
degistirilmez; butunluk manifestleri etkilenmez.
"""
from pathlib import Path
import csv
import json
import hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "EMT2_Teknik_Dogrulama_Arsivi"

# Is paketi -> (yontem adi, yeni rapordaki bolum)
PACKAGES = [
    ("WP00", "Kaynak envanteri ve erisim denetimi", "4.1"),  # KK kayitlari reports/qa kokunde
    ("WP01", "Graf temsili on calismasi", "3.2"),
    ("WP02", "DrugBank kayitlarinin ayristirilmasi ve ATC kohortu", "4.1, 4.2"),
    ("WP03", "SIDER yan etki etiketlerinin eslenmesi", "4.2"),
    ("WP04", "Kimyasal yapi cikarimi ve kalite kontrolu", "4.3, 4.4"),
    ("WP05", "Protein dizileri ve sayisal protein ozellikleri", "4.5"),
    ("WP06", "Ilac-protein rolleri ve kimlik eslemesi", "4.5"),
    ("WP07", "Heterojen grafin kurulmasi ve PPI alt grafi", "4.6, 4.7"),
    ("WP08", "Referans modeller ve bolme protokolu", "4.10, 5.1, 6.2"),
    ("WP09", "Protein-PPI mesaj gecisi ve PPI topoloji deneyleri", "5.2, 6.3"),
    ("WP10", "Atom-bag kodlayici ve faktoriyel tasarim", "5.3, 6.4"),
    ("WP11", "Aciklanabilirlik: lineer SHAP ve mesaj maskeleme", "5.6, 6.8"),
    ("WP12", "Yerel ve uzak dil modeli denemeleri", "6.9"),
    ("WP13", "Arastirma prototipi ve dis ilac ornegi", "6.9, 6.10"),
    ("WP14", "Graph-in-Graph bilgi aktarimi deneyi", "5.4, 6.5, 6.6"),
    ("WP15", "Agac tabanli karsilastirma modelleri", "5.5, 6.7"),
]

# Ana rapordan cikarilan icerik -> arsivdeki karsiligi
MOVED = [
    ("Ek A - bolum-kanit dizini (tam cizelge)",
     "EMT2_Teslim_v1/EMT2_EVIDENCE_INVENTORY.csv",
     "Ana metinde yalnizca yontem anlatimi kalir; dosya duzeyi izlenebilirlik burada"),
    ("Ek B - yeniden inceleme gunlugu",
     "EMT2_Teslim_v1/YENIDEN_INCELEME.md",
     "Surec gunlugu akademik akisi keser"),
    ("Ek C - C.1-C.5 ham deney kayitlari",
     "reports/qa/WP08, WP09, WP10, WP14",
     "Yalnizca faktoriyel farklarin ozeti ana rapor bolum 6.4'e tasinir"),
    ("SHA-256 ve manifest listeleri",
     "EMT2_Teslim_v1/PROJE_KANIT_HASHLERI.csv",
     "Butunluk kaniti; govde metninde okunabilirligi dusurur"),
    ("Dosya yolu listeleri",
     "EMT2_Teslim_v1/TESLIM_MANIFESTI.csv, reports/qa/*",
     "Ana rapor kaynaklarina bolum duzeyinde atif yapar"),
    ("Test sayilari ve kosu kayitlari",
     "EMT2_Teslim_v1/REGRESYON_TESTLERI.log, reports/qa/*/test*",
     "Ana rapor bolum 4.9'da tek cumlelik ozet"),
    ("Is paketi kodlari (WP03, WP09 ...)",
     "EMT2_Teknik_Dogrulama_Arsivi/IS_PAKETI_BOLUM_ESLESTIRME.csv",
     "Ana raporda yontem adiyla anilir; kod karsiligi bu arsivin 1. cizelgesinde"),
    ("Notebook adlari ve hucre sayilari",
     "EMT2_Teslim_v1/NOTEBOOK_DENETIMI.csv",
     "Arac duzeyi ayrinti"),
    ("Durum ve kapanis kayitlari",
     "run_status.md, GUNCEL_DURUM.md",
     "Proje gunlugu"),
]


def sayim(path: Path):
    if not path.is_dir():
        return 0, 0
    files = [p for p in path.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def sha(path: Path):
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def mb(size):
    return f"{size / 1_048_576:.1f}"


def main():
    OUT.mkdir(exist_ok=True)

    envanter = []
    for code, isim, bolum in PACKAGES:
        qa = ROOT / "reports/qa" / code
        fig = ROOT / "reports/figures" / code
        qn, qs = sayim(qa)
        fn, fs = sayim(fig)
        etiket = f"reports/qa/{code}" if qn else ""
        if code == "WP00":
            # Kaynak envanteri kayitlari alt dizin degil, reports/qa kokunde durur
            kok = [p for p in (ROOT / "reports/qa").glob("*") if p.is_file()]
            qn, qs = len(kok), sum(p.stat().st_size for p in kok)
            etiket = "reports/qa (kok dizindeki envanter dosyalari)"
        envanter.append({
            "is_paketi": code, "yontem_adi": isim, "yeni_rapor_bolumu": bolum,
            "qa_dizini": etiket,
            "qa_dosya_sayisi": qn, "qa_boyut_MB": mb(qs),
            "sekil_dizini": f"reports/figures/{code}" if fn else "",
            "sekil_dosya_sayisi": fn, "sekil_boyut_MB": mb(fs),
        })

    kanit = []
    for icerik, yol, gerekce in MOVED:
        ilk = yol.split(",")[0].strip()
        hedef = ROOT / ilk
        kanit.append({
            "ana_rapordan_cikarilan": icerik, "arsiv_konumu": yol,
            "var_mi": hedef.exists(), "gerekce": gerekce,
        })

    def yaz_csv(name, rows):
        path = OUT / name
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return path

    yaz_csv("IS_PAKETI_BOLUM_ESLESTIRME.csv", envanter)
    yaz_csv("ANA_RAPORDAN_CIKARILAN_ICERIK.csv", kanit)

    toplam_qa = sum(r["qa_dosya_sayisi"] for r in envanter)
    toplam_fig = sum(r["sekil_dosya_sayisi"] for r in envanter)
    test_sayisi = len(list((ROOT / "tests").glob("test_*.py")))
    betik_sayisi = len(list((ROOT / "scripts").glob("*.py")))

    satirlar = [
        "# EMT2 Teknik Doğrulama Arşivi — Dizin Belgesi",
        "",
        "Bu dizin **yeni kanıt üretmez.** Ana rapordan çıkarılan teknik",
        "içeriğin (kanıt dizinleri, hash listeleri, dosya yolları, test",
        "sayıları, iş paketi kodları) depodaki gerçek konumlarını",
        "gösterir. Hiçbir dosya taşınmamış veya silinmemiştir.",
        "",
        f"- Kalite kontrol kaydı: **{toplam_qa}** dosya, 16 iş paketi",
        f"- Üretilmiş şekil: **{toplam_fig}** dosya",
        f"- Test modülü: **{test_sayisi}** · analiz betiği: **{betik_sayisi}**",
        "",
        "> Ana rapor bu dizine atıf yapar; bu dizin ana raporun parçası",
        "> **değildir** ve teslim edilen akademik metne eklenmez.",
        "",
        "---",
        "",
        "## 1. İş paketi kodu ↔ yöntem adı ↔ rapor bölümü",
        "",
        "Ana raporda iş paketi kodları (WP03, WP09 …) kullanılmaz; her",
        "paket yöntem adıyla anılır. Karşılıkları:",
        "",
        "| Kod | Yöntem adı | Rapor bölümü | KK dosyası | Şekil |",
        "|---|---|---|---:|---:|",
    ]
    for r in envanter:
        satirlar.append(
            f"| {r['is_paketi']} | {r['yontem_adi']} | §{r['yeni_rapor_bolumu']} | "
            f"{r['qa_dosya_sayisi']} | {r['sekil_dosya_sayisi']} |")

    satirlar += [
        "",
        "Makine okunur biçimi: `IS_PAKETI_BOLUM_ESLESTIRME.csv`",
        "",
        "---",
        "",
        "## 2. Ana rapordan çıkarılan içerik ve yeni konumu",
        "",
        "| Çıkarılan içerik | Depodaki konum | Gerekçe |",
        "|---|---|---|",
    ]
    for r in kanit:
        isaret = "" if r["var_mi"] else " ⚠️ bulunamadı"
        satirlar.append(f"| {r['ana_rapordan_cikarilan']} | `{r['arsiv_konumu']}`{isaret} "
                        f"| {r['gerekce']} |")

    satirlar += [
        "",
        "Makine okunur biçimi: `ANA_RAPORDAN_CIKARILAN_ICERIK.csv`",
        "",
        "---",
        "",
        "## 3. Bütünlük zinciri",
        "",
        "Eğitim ve değerlendirme betikleri dosya listesi manifestleriyle",
        "kilitlidir. Manifestte adı geçen bir dosya değiştirilirse ilgili",
        "kapı testi başarısız olur. Bu nedenle bu çalışmada **yalnızca",
        "dosya eklenmiş**, hiçbir kilitli dosya düzenlenmemiştir.",
        "",
        "| Kapı | Beklenen değer |",
        "|---|---:|",
        "| Protein-PPI boş model kapısı | 1567 |",
        "| Protein-PPI eğitim kapısı | 1711 |",
        "| Atom-bağ eğitim kapısı | ≥ 2487 |",
        "",
        "Hash listesi: `EMT2_Teslim_v1/PROJE_KANIT_HASHLERI.csv`",
        "",
        "---",
        "",
        "## 4. Bilimsel kısıtların kaydı",
        "",
        "Arşivdeki her skor dosyası aynı anlam etiketini taşır:",
        "",
        "- Skorlar **gözlenen SIDER kaydı sıralama vekilidir**; klinik",
        "  risk tahmini değildir.",
        "- Kayıt bulunmaması **doğrulanmış biyolojik negatif değildir**;",
        "  bilinmeyen çiftler negatif olarak etiketlenmemiştir.",
        "- Hiçbir çıktı tedavi önerisi veya hastaya özgü risk içermez.",
    ]

    (OUT / "ARSIV_DIZINI.md").write_text("\n".join(satirlar) + "\n", encoding="utf-8")

    ozet = {
        "uretim_betigi": "scripts/wp16_teknik_arsiv.py",
        "is_paketi_sayisi": len(envanter),
        "kalite_kontrol_dosyasi": toplam_qa,
        "sekil_dosyasi": toplam_fig,
        "test_modulu": test_sayisi,
        "analiz_betigi": betik_sayisi,
        "eksik_kanit": [r["ana_rapordan_cikarilan"] for r in kanit if not r["var_mi"]],
        "mevcut_dosya_degisikligi": "yok; yalnizca yeni dizin yazildi",
        "dizin_sha256": sha(OUT / "ARSIV_DIZINI.md"),
    }
    (OUT / "ARSIV_OZETI.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Arsiv yazildi: {OUT}")
    for k, v in ozet.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
