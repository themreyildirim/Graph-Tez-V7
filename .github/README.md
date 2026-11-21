<h1 align="center">Antibiyotik Yan Etkilerinin Heterojen Ağ Modelleriyle Öngörülmesi</h1>

<p align="center">
  <em>Graph-Tez V7 — antibakteriyel ilaç ↔ yan etki ilişkilerinin graf sinir ağlarıyla modellenmesi<br>
  ve açıklanabilir bir araştırma karar destek arayüzü</em>
</p>

<p align="center">
  <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11.3-3776AB?logo=python&logoColor=white">
  <img alt="PyTorch Geometric" src="https://img.shields.io/badge/PyTorch%20Geometric-GNN-EE4C2C?logo=pytorch&logoColor=white">
  <img alt="Testler" src="https://img.shields.io/badge/testler-1212%20toplanan-success">
  <img alt="Veri" src="https://img.shields.io/badge/veri-depoda%20yok-important">
  <img alt="Kapsam" src="https://img.shields.io/badge/kapsam-ara%C5%9Ft%C4%B1rma%20prototipi-blue">
</p>

> [!IMPORTANT]
> Bu bir **araştırma karar destek prototipidir**. Tedavi önerisi, klinik güvenlilik garantisi
> veya bireysel hastaya özgü risk üretmez. Birim, *ilaç–MedDRA PT çifti*dir; hasta, reçete,
> doz-cevap ve tedavi seçimi kapsam dışıdır.

---

## Problem

Bir antibiyotiğin hangi yan etkilerle ilişkili olduğu, klinik kayıtlarda ancak kısmen
belgelenmiştir. SIDER'da bir ilaç–yan etki çiftinin **bulunmaması**, o yan etkinin
olmadığı anlamına gelmez — yalnızca kayıt olmadığı anlamına gelir. Bu proje, bu belirsizliği
koruyarak (`positive` / `unknown` ayrımı) ilaç–yan etki ilişkilerini üç bilgi kaynağından
öğrenmeyi dener:

```
    kimyasal yapı            hedef proteinler            protein-protein ağı
  (SMILES, MW, LogP,   ─▶   (DrugBank hedef/enzim   ─▶   (STRING: insan + E. coli)
   TPSA, HBD, HBA)            ilişkileri, AAC/DC)              message passing
          │                          │                            │
          └──────────────────────────┴────────────────────────────┘
                                     ▼
                    heterojen graf  ·  ilaç / protein / yan etki
                                     ▼
                        ilaç → yan etki skoru  +  açıklama
```

## Yaklaşım

Modeller **kademeli** kurulur; her katmanın gerçekten katkı sağlayıp sağlamadığı ablation
ile ölçülür. Basit ve güçlü bir modeli dürüstçe raporlamak, katkısı kanıtlanmamış karmaşık
bir modeli savunmaktan değerli kabul edilir.

| Aşama | Model | Soru |
|---|---|---|
| **B0** | Etiket sıklığı referansı | Veriden öğrenmeden ne kadar ileri gidilir? |
| **B1** | Kimyasal özellik → MLP | Molekül tek başına ne söylüyor? |
| **B2** | İlaç–protein ortalama toplama | Hedef bilgisi katkı sağlıyor mu? |
| **WP09** | PPI encoder + drug aggregator | Protein ağında mesaj geçirmek işe yarıyor mu? |
| **WP10** | Atom grafı × PPI faktöriyel | Moleküler graf ile ağ birlikte ne yapar? |
| **WP14** | GiG-1a | Graf-içinde-graf mimarisi |
| **WP15** | Ağaç tabanlı modeller | Güçlü klasik taban çizgisi |

Değerlendirme **ilaç-ayrık** (drug-disjoint) bölmelerle yapılır: test ilaçları eğitimde hiç
görünmez. Ölçekleme ve özellik seçimi yalnız eğitim bölmesinde fit edilir.

## Açıklanabilirlik

Skor ve açıklama ayrı katmanlardır ve birbirinin yerine geçmez:

- **SHAP** — kimyasal taban modeli için yerel/küresel katkılar (`WP11`)
- **Graf maskeleme** — hangi protein/kenarın skora etki ettiği (`A1P1` mesaj maskeleme)
- **Belge karşılaştırması** — prospektüsten okunan yan etkiler (`reported_in_PDF`),
  modelin tahmininden (`predicted_by_GNN`) **ayrı** tabloda tutulur

> SHAP bir **nedensellik** açıklaması değildir; yolak üzerindeki en kısa yol topolojik bir
> ipucudur. Prospektüsten çıkarılan yan etki metni hiçbir zaman aynı ilişkinin tahmini için
> modele girdi olmaz.

## Veri politikası

> [!WARNING]
> Bu depo **hiçbir ham veri seti, hasta kaydı veya lisanslı veri dosyası içermez.**

DrugBank, SIDER, STRING ve UniProt kaynaklarına erişim akademik çalışma amacıyla alınan
izinlerle sağlanmıştır; lisans koşulları gereği dosyalar yeniden dağıtılamaz. Kullanılan
veri setleri yalnız **isim, sürüm ve lisans** olarak [`DATA_INVENTORY.md`](../DATA_INVENTORY.md)
içinde belgelenmiştir — orada veriyi yerine koyma (reproduksiyon) sırası da yazılıdır.

Depo dışında tutulanlar:

| İçerik | Neden |
|---|---|
| Ham veri (`data/`) | Lisanslı / sağlık verisi |
| Türetilmiş QA tabloları (`reports/qa/**` CSV·JSON) | DrugBank/SIDER'den türetilmiş |
| Model ağırlıkları (`models/`) | Yeniden üretilebilir |
| Plotly etkileşimli HTML grafikler | Tüm veri noktalarını gömülü taşır |
| `.env` | API anahtarı — şablon: [`env.example`](../env.example) |

Depoda kalan kanıt izi: **138 Türkçe iş paketi raporu**, statik PNG görseller,
notebook'lar, kod ve testler.

## Hızlı başlangıç

```powershell
git clone https://github.com/themreyildirim/Graph-Tez-V7.git
cd Graph-Tez-V7
```

```powershell
python -m venv .venv_wp13; .venv_wp13\Scripts\python.exe -m pip install -r requirements.txt
```

Ham veri kökünü tanıt (veri setlerini kendi lisansınızla edinmeniz gerekir):

```powershell
$env:GRAPH_TEZ_DATA_ROOT = "D:\Tez\Dataset"
```

Testleri çalıştır:

```powershell
.venv_wp13\Scripts\python.exe -m pytest -q
```

Arayüzü başlat (güncel sürüm v5, port 8530):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/WP13_Start_v5.ps1
```

## Depo yapısı

| Yol | İçerik |
|---|---|
| `scripts/` | İş paketi hattı — veri çıkarımı, eğitim, değerlendirme, XAI (259 dosya) |
| `apps/` | Streamlit karar destek arayüzü. **Güncel:** `arayuz_v5.py` + `tedizolid_v5.py`; diğerleri tarihsel, çalışır durumda tutulur |
| `notebooks/` | Her iş paketinin çalıştırılmış, açıklamalı Jupyter defteri (62) |
| `reports/` | Türkçe iş paketi raporları (`WP00`–`WP15`) ve statik görseller |
| `docs/plan/` | Yol haritası, veri kontratları, karar kapıları |
| `tests/` | Birim, bütünlük ve **sızıntı** testleri (1212 test) |
| `configs/` | Deney politikaları ve dondurulmuş protokol kayıtları |
| `EMT2_Akademik_v6/` | Tez raporu — final sürüm (53 sayfa, resmî şablon) |
| `EMT2_Teslim_v1/` | Teslim paketi: rapor, sunum, jüri soruları, ekran görüntüleri |
| `legacy/` | Önceki V6 sisteminin tarihsel belgeleri (talimat değildir) |

Güncel işleyiş ve iş paketi durumu: [`GUNCEL_DURUM.md`](../GUNCEL_DURUM.md) ·
Durum günlüğü (ters kronolojik): [`run_status.md`](../run_status.md)

## Bütünlük kilitleri

Bu projede sonuç zinciri **hash ile dondurulmuştur**: `reports/qa/**` ve `configs/**`
altındaki bütünlük manifestoları, aralarında `README.md`, `AGENTS.md`, `run_status.md` ve
`apps/*.py`'nin de bulunduğu dosyaların SHA-256 değerlerini kaydeder. Bu yüzden:

- Kök `README.md` ve `AGENTS.md` **değiştirilmez** — bu açılış sayfası ayrı bir dosyadır
  (`.github/README.md`; GitHub bunu kök README'den önce gösterir).
- `.gitattributes` içindeki `* -text`, Git'in satır sonu dönüşümünü kapatır; böylece klon
  baytı baytına diskteki hâliyle aynı olur ve hash doğrulaması her işletim sisteminde çalışır.
- Yayın dışlama kuralları, kök `.gitignore` kilitli olduğu için alt klasörlerdeki
  `.gitignore` dosyalarına dağıtılmıştır (`data/`, `models/`, `reports/qa/`,
  `reports/figures/`, `legacy/`, `configs/`).

## Bilinen sınırlar

- Eski V6'nın `AUROC 0.9004 / AUPR 0.8545` değerleri **`historical, unverified`** etiketlidir;
  V7 için karşılaştırma ölçütü sayılmaz.
- `WP12` (PDF/LLM) ve `WP13` (dış referans) **resmî kapanış almadı**; uzman terim eşlemesi
  ve insan değerlendirmesi beklemede.
- Kohort sistemik antibakteriyeller (ATC **J01**) ile sınırlıdır; antifungal/topikal ajanlar
  ayrı raporlanır. İlaç adı son ekleriyle (`-azole`, `-mycin`) sınıflama yapılmaz.
- Antibiyotik direnç tahmini ayrı outcome etiketleri olmadığı için yan etki modelinden
  türetilmez.
