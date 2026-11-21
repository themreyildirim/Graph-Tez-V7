# DATA_INVENTORY.md — Veri setleri yalnız **isim** olarak

> **Bu depoda hiçbir ham veri seti, hasta kaydı veya lisanslı veri dosyası bulunmaz.**
> Aşağıdaki kaynaklara erişim, **akademik çalışma amacıyla** ilgili kurumlardan/portallardan
> alınan izinlerle sağlanmıştır. Lisans koşulları gereği dosyaların kendisi yeniden
> dağıtılamaz; bu dosya sadece **hangi veri setinin kullanıldığını** belgeler.
>
> Depoyu klonlayan kişi, aynı kaynaklara **kendi lisansı/izniyle** erişmek ve dosyaları
> aşağıda belirtilen yollara kendisi yerleştirmek zorundadır.

---

## 1. Yerel veri kökü (depo dışında)

Kod, ham veriyi yapılandırılabilir bir kökten **salt okunur** olarak okur:

```
<DATA_ROOT>/
  DrugBank/
  SIDER/
  string-db/
  UniProt Dataset/
```

Geliştirme makinesindeki karşılığı: `C:\Users\<kullanici>\OneDrive\...\Tez Dosyalar\Dataset`
Hiçbir modülde bu yol sabit kodlanmaz; `configs/` üzerinden verilir.

---

## 2. Aktif kapsam (allowlist) — modelin fiilen kullandığı kaynaklar

| # | Veri seti | Dosya adı (içerik depoda yok) | Yaklaşık boyut | Kaynak / sürüm | Lisans ve erişim |
|---|---|---|---|---|---|
| 1 | **DrugBank** tam veritabanı | `drugbank_all_full_database.xml` (`.xml.zip`) | ~1.9 GB (zip ~174 MB) | DrugBank 5.x tam döküm | Akademik/araştırma lisansı, hesap bazlı. **Yeniden dağıtım yasak.** |
| 2 | DrugBank hedef polipeptit kimlikleri | `drugbank_all_target_polypeptide_ids.csv.zip` | ~0.6 MB | DrugBank 5.x | Aynı lisans |
| 3 | DrugBank enzim / taşıyıcı / carrier kimlikleri | `drugbank_all_enzyme_polypeptide_ids.csv.zip`, `drugbank_all_transporter_polypeptide_ids.csv.zip`, `drugbank_all_carrier_polypeptide_ids.csv.zip` | <1 MB | DrugBank 5.x | Aynı lisans |
| 4 | DrugBank ↔ PubChem eşlemesi | `drug links.csv` | ~ MB | DrugBank external links | Aynı lisans |
| 5 | **SIDER 4.1** yan etki etiketleri | `meddra_all_se.tsv` (`.tsv.gz`) | ~2.3 MB (gz) | SIDER 4.1 | Araştırma kullanımı; MedDRA terimleri MedDRA MSSO lisansına tabidir. |
| 6 | **PubChem PUG REST** | (dosya yok, API) | — | PubChem Compound | Kamuya açık, NCBI kullanım koşulları |
| 7 | **STRING** PPI — insan | `9606.protein.links.v12.0.txt`, `9606.protein.aliases.v12.0.txt` | ~600 MB / ~ MB | STRING v12.0 | CC BY 4.0 (atıf zorunlu) |
| 8 | **STRING** PPI — *E. coli* K-12 | `511145.protein.links.v12.0.txt`, `511145.protein.aliases.v12.0.txt` | ~ MB | STRING v12.0 | CC BY 4.0 |
| 9 | **UniProtKB** kimlik eşlemeleri (opsiyonel) | `idmapping_2026_03_09_all_target.xlsx` ve eşleri | <1 MB | UniProt ID mapping dökümü | CC BY 4.0 |

> Not: Protein dizileri ve UniProtKB kimlikleri birincil olarak DrugBank XML içinden
> çıkarılır; bağımsız UniProt indirmesi zorunlu değildir.

---

## 3. Kapsam dışı — bu depoda **okunmayan** veri setleri

Veri kökünde bulunsa bile aşağıdaki dizinler proje kapsamına **dahil değildir**;
kod bunlara erişmez, hash almaz, kopyalamaz:

| Dizin / kaynak | Neden kapsam dışı |
|---|---|
| `MIMIC-IV/` (PhysioNet) | **Hasta düzeyinde klinik veri.** Bu çalışmanın girdisi değil. PhysioNet DUA'sı gereği hiçbir koşulda yayımlanmaz. |
| `CARD/` (ARO, direnç genleri) | Antibiyotik direnç tahmini bu tezin outcome etiketleri arasında yok (opsiyonel V8). |
| FAERS, OnSIDES, DisGeNET, ChEMBL, DailyMed / openFDA toplu dökümleri | Aktif allowlist'te değil; ek yan etki kaynağı otomatik entegre edilmez. |
| STRING — *S. aureus*, *P. aeruginosa*, *K. pneumoniae* | Kohort insan + *E. coli* ile sınırlı. |
| Tarihsel birleşik tablolar (`all.csv`, `ANTIBIYOTIK_MASTER_NETWORK*`, `nihai_antibiyotik_agi_*`) | Önceki denemelere ait, denetlenmemiş çıktılar. |

Bu isimler eski `legacy/` belgelerinde geçebilir; bu, kapsama geri alma talimatı değildir.

---

## 4. Depo içinde **yer almayan** türetilmiş çıktılar

Aşağıdakiler `.gitignore` ile dışarıda bırakılmıştır (lisanslı kaynaklardan türetildikleri
ve/veya çok büyük oldukları için). Hepsi kod çalıştırılarak yeniden üretilebilir:

| Yol | İçerik | Neden dışarıda |
|---|---|---|
| `data/raw/`, `data/staging/`, `data/processed/`, `data/external/` | Ham ve ara veri | Lisanslı / sağlık verisi |
| `data/user_pdfs/` | Kullanıcı prospektüs PDF'leri: `050641Orig1s032lbl.pdf`, `eritro-500-mg-film-tablet-8ccc-kt.pdf`, `monodoks-100-mg-kapsul-kub-07-11-2018.pdf`, `pil.502.pdf` | Üçüncü taraf ürün dokümanları |
| `models/` | WP08–WP15 model ağırlıkları, `.npz` / `.pt` checkpoint'leri (~132 MB) | Boyut; yeniden üretilebilir |
| `reports/qa/**` (`.md` hariç) | İlaç kayıt tabloları, protein dizileri, yan etki etiketleri, OOF tahminleri, SHAP katkı tabloları (~417 MB) | **DrugBank/SIDER'den türetilmiş** — yeniden dağıtım kapsamına girer |
| `**/*.html` | Plotly etkileşimli grafikler | Tüm veri noktalarını gömülü taşır |
| `.venv_wp13/`, `.deps/` | Sanal ortam ve indirilmiş wheel'ler | Boyut |
| `.env` | `OPENAI_API_KEY` | **Sır** — bkz. `.env.example` |

Depoda **kalan** kanıt izi: `reports/**/*.md` (Türkçe iş paketi raporları),
`reports/figures/**/*.png` (statik görseller), `notebooks/*.ipynb`, `scripts/`, `tests/`,
`configs/`, `docs/plan/`.

---

## 5. Veriyi yerine koyma (reproduksiyon) sırası

1. DrugBank akademik lisansı al → `drugbank_all_full_database.xml` ve `drug links.csv` indir.
2. SIDER 4.1 → `meddra_all_se.tsv` indir.
3. (Gerekirse) STRING v12.0 → `9606.*` ve `511145.*` links/aliases indir.
4. Dosyaları `<DATA_ROOT>` altındaki ilgili klasörlere koy; `configs/data.yaml` içinde kökü göster.
5. `pytest -q` ile şema/sızıntı testlerini çalıştır, sonra WP sırasını izle.

---

## 6. Etik ve kullanım sınırı

Bu depo bir **araştırma karar destek prototipidir**. Tedavi önerisi, klinik güvenlilik
garantisi veya bireysel hastaya özgü risk üretmez. SIDER'da kayıt bulunmaması
"yan etki yok" anlamına gelmez (`positive` / `unknown` ayrımı korunur).
