# -*- coding: utf-8 -*-
"""EMT2 nihai raporu v6 — resmi EMT sablonu uzerine sifirdan kurulur.

Girdi : docs/EMT_Sablon_v2025_v3.docx  (degistirilmez)
Cikti : EMT2_Akademik_v6/EMT2_FINAL_REPORT.docx

Onceki rapor surumleri (v3, v4, v5) oldugu gibi durur. Bu surum onlarin
uzerine yama degildir; sablonun kendi stil ve bolum iskeleti korunarak
icerik yeniden kurulur.

Icindekiler, cizelge listesi ve sekil listesi Word ALAN KODU olarak
yazilir; sayfa numaralari `disa_aktar.ps1` calistirildiginda Word
tarafindan doldurulur.
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sablon import RaporKurucu            # noqa: E402
from bolum_1_3 import bolum1, bolum2, bolum3   # noqa: E402
from bolum_4_5 import bolum4, bolum5           # noqa: E402
from bolum_6 import bolum6                     # noqa: E402
from bolum_7_8 import bolum7, bolum8, arka_bolumler  # noqa: E402

CIKTI = HERE.parent / "EMT2_FINAL_REPORT.docx"

BASLIK = ("ANTİBAKTERİYEL İLAÇLARDA YAN ETKİ TERİMLERİNİN "
          "HETEROJEN GRAF MODELLERİYLE SIRALANMASI")

KAPAK = {
    "BAŞLIK BURAYA GELİR": "ANTİBAKTERİYEL İLAÇLARDA YAN ETKİ",
    "GEREKLİ İSE İKİNCİ SATIR": "TERİMLERİNİN HETEROJEN GRAF",
    "GEREKLİ İSE ÜÇÜNCÜ SATIR, ÜÇ SATIRA SIĞDIRINIZ": "MODELLERİYLE SIRALANMASI",
    "ENDÜSTRİ MÜHENDİSLİĞİ TASARIMI I (veya II)": "ENDÜSTRİ MÜHENDİSLİĞİ TASARIMI II",
    "Öğrenci Adı SOYADI": "Emre YILDIRIM        Mehmet NORTCU",
    "Danışman: Dr. Ad SOYAD": "Danışman: Dr. Kenan MENGÜÇ",
    "TESLİM EDİLDİĞİ AY YIL": "KASIM 2026",
    "Aileme,": "",
}

ONSOZ = (
    "Bu rapor, antibakteriyel ilaçların yan etki kayıtlarının moleküler yapı ve "
    "protein etkileşim bilgisinden yararlanılarak sıralanmasını konu alan bir "
    "tasarım çalışmasını sunar. Çalışmanın çıkış sorusu şudur: bir molekülün "
    "yapısını ve ilişkili olduğu proteinleri bilmek, daha önce incelenmemiş bir "
    "antibiyotik için hangi yan etki terimlerinin öncelikle gözden geçirilmesi "
    "gerektiğini gösterebilir mi? Bu soruya yanıt ararken önce kaynakların hangi "
    "karşılaştırmalara elverdiği belirlenmiş, ardından kimyasal ve biyolojik "
    "bilginin katkısı aynı ilaçlar üzerinde ölçülmüştür. Çalışma boyunca, "
    "beklentiyi desteklemeyen sonuçların da raporlanması temel ilke sayılmıştır."
)
ONSOZ2 = (
    "Çalışma, İstanbul Teknik Üniversitesi İşletme Fakültesi Endüstri "
    "Mühendisliği Bölümünde Dr. Kenan Mengüç danışmanlığında yürütülmüştür. "
    "Katkıları ve yönlendirmesi için kendisine teşekkür ederiz."
)

OZET = (
    "Bir antibakteriyel için hangi yan etki terimlerinin önce inceleneceğini "
    "belirlemek, eksik kayıtlar altında bir sıralama problemidir. Çalışmada "
    "sistemik antibakteriyellerin DrugBank kimlikleri, SIDER 4.1’deki tercih "
    "edilen terimlerle eşleştirilmiş; 62 ilaç için 1.061 terime yayılan 6.416 "
    "benzersiz gözlenen kayıt elde edilmiştir. Kimyasal tanımlayıcılar, rolü "
    "bilinen ilaç–protein ilişkileri, atom grafı ve insan protein etkileşimleri, "
    "öğrenmede görülmemiş ilaçlar üzerinde ilaç düzeyinde ayrık bir protokolle "
    "karşılaştırılmıştır. Ortak 54 ilaçta kimyasal lojistik modelin ilaç başına "
    "ortalama kesinliği 0,6556, atom ve protein dallarını birlikte kullanan "
    "modelinki 0,6462’dir; aradaki fark koşullu %95 aralıkta sıfırı "
    "içermektedir. Kimya modelinin eğitim sıklığına dayalı referansa göre farkı "
    "+0,0119 olup bu aralık da sıfırı içerir. Proteinler arası mesaj aktarımının "
    "hesaba girdiği doğrulanmış, ancak ek sıralama katkısı gösterilememiştir. "
    "Protein temsillerine ilaç bağlamından bilgi aktaran mimari genişletme ve "
    "doğrusal olmayan ağaç tabanlı kollar, önceden kilitlenen kabul ölçütlerini "
    "karşılamamıştır. Buna karşılık aynı skorlar terim yönünde okunduğunda "
    "öğrenme içeren bütün modeller sıklık referansını belirgin biçimde aşmakta; "
    "bu da ilaca özgü sinyalin ölçülebilir olduğunu, ancak ilaç yönünde kayıt "
    "yaygınlığını aşamadığını göstermektedir. Son aşamada model açıklaması ile "
    "ürün belgesindeki ifadeler ayrı ayrı incelenmiş, eğitim dışı tedizolid için "
    "ilk on sıra ürün belgesi açılmadan sabitlenmiştir. Sonuçlar bir "
    "araştırmacının inceleme sırasını gerekçelendirmeye elverişlidir; hasta "
    "düzeyinde olay sıklığı bu tasarımda ölçülmemiştir."
)
ANAHTAR = ("Anahtar kelimeler: antibakteriyel, heterojen graf, bilinmeyen etiket, "
           "ortalama kesinlik, açıklanabilirlik.")

SUMMARY = (
    "Selecting which adverse-effect terms to review for an antibacterial is a "
    "ranking problem under incomplete observation. DrugBank identities of "
    "systemic antibacterials were linked to SIDER 4.1 preferred terms, yielding "
    "6,416 distinct observed pairs across 62 drugs and 1,061 terms. Chemical "
    "descriptors, role-typed drug–protein relations, molecular graphs and human "
    "protein interactions were compared under a drug-disjoint protocol using "
    "drugs held out from training. In the paired set of 54 drugs, drug-macro "
    "average precision was 0.6556 for chemical logistic regression and 0.6462 "
    "for the model combining atom and protein message passing; the conditional "
    "95% interval of their difference spans zero. The chemical model exceeded "
    "its matched frequency baseline by 0.0119, again with an interval spanning "
    "zero. Protein message passing was verified to enter the computation, but no "
    "additional ranking benefit was established. An architectural extension "
    "passing drug-context information into protein embeddings, and non-linear "
    "tree-based arms, both failed pre-registered acceptance criteria. Read in "
    "the term direction, however, every learned model clearly exceeds the "
    "frequency baseline, showing that drug-specific signal is measurable but "
    "does not overcome record prevalence in the drug direction. Model "
    "explanations and documentary evidence were assessed separately, and for "
    "external tedizolid the top ten terms were locked before the product "
    "document was opened. Expert terminology review remains pending. The scores "
    "order source-record candidates and do not estimate patient-level incidence."
)
KEYWORDS = ("Keywords: antibacterial, heterogeneous graph, unknown label, "
            "average precision, explainability.")

KISALTMALAR = [
    ("AP", "Ortalama kesinlik (Average Precision)"),
    ("ATC", "Anatomik Terapötik Kimyasal sınıflama sistemi"),
    ("AUROC", "Alıcı işletim eğrisi altında kalan alan"),
    ("CID", "PubChem bileşik kimliği (Compound Identifier)"),
    ("CUI", "UMLS kavram kimliği (Concept Unique Identifier)"),
    ("GNN", "Graf sinir ağı (Graph Neural Network)"),
    ("GRAVY", "Ortalama hidropati değeri"),
    ("HBA", "Hidrojen bağı alıcı sayısı"),
    ("HBD", "Hidrojen bağı verici sayısı"),
    ("KÜB", "Kısa Ürün Bilgisi"),
    ("LogP", "Oktanol–su dağılım katsayısının logaritması"),
    ("MedDRA", "Düzenleyici Faaliyetler için Tıbbi Sözlük"),
    ("MW", "Molekül ağırlığı"),
    ("OOF", "Dış bölme tahmini (Out-of-Fold)"),
    ("PPI", "Protein–protein etkileşimi"),
    ("PT", "Tercih edilen terim (Preferred Term)"),
    ("SHAP", "Shapley toplamsal açıklama değerleri"),
    ("SID", "PubChem madde kimliği (Substance Identifier)"),
    ("TPSA", "Topolojik polar yüzey alanı"),
    ("UMLS", "Birleşik Tıbbi Dil Sistemi"),
]

SEMBOLLER = [
    ("G=(V,E,τ,ρ)", "Düğüm, kenar, düğüm tipi ve kenar rolüyle tanımlı heterojen graf"),
    ("D", "Yönsüz ağın yoğunluğu, D=2m/[n(n−1)]"),
    ("n, m", "Düğüm sayısı ve benzersiz yönsüz kenar sayısı"),
    ("x′", "Eğitim bölmesinde öğrenilen ölçekle standartlaştırılmış girdi"),
    ("μₜ, σₜ", "Eğitim bölmesinden hesaplanan ortalama ve standart sapma"),
    ("z, s", "Doğrusal logit ve sigmoid uygulanmış skor"),
    ("ϕⱼ", "j girdisinin logite katkısı"),
    ("Δz", "Mesaj müdahalesi öncesi ve sonrası logit farkı"),
    ("P, R", "Kesinlik ve duyarlılık"),
    ("K", "Eğitim bağlamındaki tahmin başlığı sayısı"),
]

TOC = r'TOC \o "1-4" \h \z \u'
TOF = (r'TOC \h \z \t "'
       "Sekil_FBE_Sablon_BolumI,1,Sekil_FBE_Sablon_BolumII,1,"
       "Sekil_FBE_Sablon_BolumIII,1,Sekil_FBE_Sablon_BolumIV,1,"
       "Sekil_FBE_Sablon_BolumV,1,Sekil_FBE_Sablon_BolumVI,1,"
       'Sekil_FBE_Sablon_EKLER,1"')
TOT = (r'TOC \h \z \t "'
       "Cizelge_FBE_Sablon_BolumI,1,Cizelge_FBE_Sablon_BolumII,1,"
       "Cizelge_FBE_Sablon_BolumIII,1,Cizelge_FBE_Sablon_BolumIV,1,"
       "Cizelge_FBE_Sablon_BolumV,1,Cizelge_FBE_Sablon_BolumVI,1,"
       'Cizelge_FBE_Sablon_BolumEKLER,1"')



def on_bolumler(k):
    k.on_baslik("ÖNSÖZ")
    k.govde_metni(ONSOZ)
    k.govde_metni(ONSOZ2)
    k.govde_metni("")
    k.govde_metni("Kasım 2026\t\t\t\tEmre YILDIRIM")
    k.govde_metni("\t\t\t\tMehmet NORTCU")
    k.bolum_sonu("roman")

    k.on_baslik("İÇİNDEKİLER")
    k.alan_listesi(TOC)
    k.bolum_sonu("roman")

    k.on_baslik("KISALTMALAR")
    for kisa, acik in KISALTMALAR:
        k.govde_metni(f"**{kisa}**\t: {acik}")
    k.bolum_sonu("roman")

    k.on_baslik("SEMBOLLER")
    for sembol, acik in SEMBOLLER:
        k.govde_metni(f"**{sembol}**\t: {acik}")
    k.bolum_sonu("roman")

    k.on_baslik("ÇİZELGE LİSTESİ")
    k.alan_listesi(TOT)
    k.bolum_sonu("roman")

    k.on_baslik("ŞEKİL LİSTESİ")
    k.alan_listesi(TOF)
    k.bolum_sonu("roman")

    k.govde_metni(BASLIK)
    k.on_baslik("ÖZET")
    k.govde_metni(OZET)
    k.govde_metni(ANAHTAR)
    k.bolum_sonu("roman")

    k.govde_metni("RANKING ADVERSE-EFFECT TERMS FOR ANTIBACTERIAL DRUGS "
                  "WITH HETEROGENEOUS GRAPH MODELS")
    k.on_baslik("SUMMARY")
    k.govde_metni(SUMMARY)
    k.govde_metni(KEYWORDS)
    k.bolum_sonu("roman")


def main():
    k = RaporKurucu(CIKTI)
    bulunan = k.kapak_doldur(KAPAK)

    on_bolumler(k)
    bolum1(k)
    bolum2(k)
    bolum3(k)
    bolum4(k)
    bolum5(k)
    bolum6(k)
    bolum7(k)
    bolum8(k)
    arka_bolumler(k, ozgecmis_var=False)
    k.kaydet()

    ozet = {
        "cikti": str(CIKTI.relative_to(HERE.parents[1])),
        "sablon": "docs/EMT_Sablon_v2025_v3.docx (degistirilmedi)",
        "kapak_yer_tutucu": len(bulunan),
        "sekil": len(k.sekiller),
        "cizelge": len(k.cizelgeler),
        "sekil_listesi": [f"{e} : {a}" for e, a in k.sekiller],
        "cizelge_listesi": [f"{e} : {a}" for e, a in k.cizelgeler],
        "not": ("Icindekiler / sekil / cizelge listeleri Word alan kodudur; "
                "sayfa numaralari disa_aktar.ps1 ile doldurulur."),
    }
    (HERE / "uretim_ozeti.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Yazildi: {CIKTI}")
    print(f"  sekil: {len(k.sekiller)}  cizelge: {len(k.cizelgeler)}")
    for etiket, ad in k.sekiller:
        print(f"    {etiket} : {ad[:60]}")
    for etiket, ad in k.cizelgeler:
        print(f"    {etiket} : {ad[:60]}")


if __name__ == "__main__":
    main()
