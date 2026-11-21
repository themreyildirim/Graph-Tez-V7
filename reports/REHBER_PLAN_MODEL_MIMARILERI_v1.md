# Plan — "Graph-Tez V7 — Model Mimarileri, Veri Yapıları ve GNN Teknik Öğrenme Rehberi"

> **DURUM: UYGULANDI (15.11.2026).** Rehber
> `reports/REHBER_MODEL_MIMARILERI_v1.md` (+ `.docx`, `.pdf`) olarak üretildi.
> Bu dosya tarihsel plan kaydıdır.
>
> **Planda yapılan bir düzeltme:** Aşağıdaki §2 örnek bölümünde B1'in
> kapsadığı ilaç sayısı **61** yazılmıştı. Kod doğrulaması bunun **54**
> olduğunu gösterdi (`prediction_eligibility.csv :: model=B1 & eligible`);
> B1 ineligible 8, B2 ineligible yalnız 1 (Methenamine). Nihai rehberde
> doğru sayı kullanılmıştır (bkz. rehber §4.3).

> **Bu dosya rehberin kendisi değil, onay için sunulan içindekiler planı + bir örnek bölüm taslağıdır.**
> Mevcut final rapor (`EMT2_Teslim_v1/EMT2_FINAL_REPORT.*`), eğitimler, deney
> sonuçları ve QA dosyaları **değiştirilmeyecek**. Rehber yeni ve bağımsız bir
> dosya olacak.

---

## 0. Kod incelemesinden çıkan envanter (planın dayanağı)

Rehberde anlatılacak modellerin tamamı `scripts/` içindeki gerçek Python
dosyalarından doğrulandı. Aşağıdaki tablo rehberin iskeletini belirler.

| Model | Gerçek kod dosyası | Model sınıfı / yöntem | Gerçekten eğitildi mi? |
|---|---|---|---|
| **B0** (3 varyant) | `wp08_b0_frequency.py` | Öğrenilebilir parametre **yok**; `count(train ilaç) / N` | Eğitim yok, **tahmin üretildi** (40 bağlam / 120 popülasyon) |
| **B1** | `wp08_baseline_train.py` | `sklearn.LogisticRegression`, L2, liblinear | **Evet** |
| **B2** | `wp08_baseline_train.py` | Aynı sınıf, geniş özellik vektörü | **Evet** |
| **WP09 GNN** | `wp09_encoder.py` + `wp09_train.py` | `RoleMaskedPPI` (PyTorch), tek residual-mean PPI katmanı | **Evet** — 190/190 fit, 10.867 AdamW adımı |
| **A0P0 / A0P1 / A1P0 / A1P1** | `wp10_molecular_encoder.py`, `wp10_molecular_graph.py`, `wp10_train.py` | `MolecularProteinFusion` = `RoleMaskedPPI` + `BondAwareMolecularEncoder` | **Evet** — 152/152 fit, 8.611 adım |
| **GiG-1a** | `wp14_gig1_encoder.py` + `wp14_gig1_train.py` | `GiG1Encoder` = A1P1 omurgası + ilaç→protein mesajı | **Evet** — 38/38 fit, 2.032 adım |
| (Ek) **WP15 ağaç modelleri** | `wp15_tree_models.py` | — | Ek bölüm olarak **sadece ekte**, kullanıcı isterse |

**Rehberde özellikle düzeltilecek yaygın yanlış anlamalar** (hepsi kodla
doğrulandı):

1. Projede **GCNConv, GATConv, GraphSAGE, CNN veya Transformer katmanı yok.**
   PyTorch Geometric yalnız üç şey için kullanılıyor: `Data` kabı, `Batch`
   birleştirmesi ve `global_mean_pool`. Mesajlaşma **elle**, `index_add` ile
   yazılmış (`wp09_encoder.py:36-39`, `wp10_molecular_encoder.py:42-45`).
2. **Her iki GNN kolunda da tek mesajlaşma katmanı var.** Yani bir atom veya
   protein yalnız **1 bağlantı uzaklığındaki** komşusunu görebilir. Rehberde
   "ikinci katmanda daha uzak komşular" diye genel bir GNN dersi anlatılmayacak;
   bizim modelimizin 1-hop sınırı açıkça çizilecek.
3. **STRING `combined_score` modelde sayısal kenar ağırlığı veya kenar özelliği
   DEĞİL.** Yalnız 700 eşiğiyle "bu kenar grafa girsin mi?" kararında
   kullanılıyor. Grafa giren kenarın ağırlığı yoktur; komşu ortalaması
   ağırlıksızdır (`wp09_encoder.py:36-39`).
4. **A1/P1 isimleri bir model dalını açıp kapatır**; tek bir ilacın `atom_mask`
   değerinin 0/1 olmasıyla aynı şey değildir. A1P1'de dahi 8 ilacın atom
   maskesi kapalıdır (54 QC-geçer / 8 maskeli).
5. **GiG-1a bir GNN'dir** ve A1P1'in kontrollü genişletmesidir; `W_dp = 0`
   olduğunda A1P1 ile **bit düzeyinde aynı** protein gömmesi üretir (sentetik
   kapı 05). Eski EMT1 "iç/dış graf" tasarımı ile karıştırılmayacak.
6. **Yan etki düğümü hiçbir encoder'da mesajlaşmaya katılmıyor.** Yan etki,
   son `nn.Linear(150, K)` başlığının **çıkış boyutu**dur; graf düğümü değildir.
   Rehberin GiG bölümünde bu nokta ayrıca vurgulanacak, çünkü "heterojen graf"
   beklentisi burada karşılanmıyor.

---

## 1. Rehberin içindekiler planı

### Kısım I — Temeller (öğrenme zemini)

| § | Başlık | İçerik |
|---|---|---|
| 1 | Bu rehber ne, ne değil | Final rapordan ayrı; öğrenme amaçlı; klinik iddia yok |
| 2 | Okuma haritası | Hangi bölüm hangi soruyu cevaplıyor; savunma öncesi 2 saatlik okuma yolu |
| 3 | Sözlük (örnekli) | düğüm, kenar, özellik vektörü, `edge_index`, mesajlaşma, pooling, embedding, maskeleme, füzyon, logit, sigmoid, AP — her terim **projenin kendi sayılarıyla** |
| 4 | Veri zinciri tek sayfada | DrugBank XML → SIDER → PubChem → STRING → 62 ilaç / 1061 PT / 6416 pozitif → fold'lar; her oku bir dosya adıyla |
| 5 | Ortak değerlendirme iskeleti | 5×3 nested CV, primary/stress protokolü, paired54 / own61 kapsamı, drug-macro AP, 1000 grup bootstrap |
| 6 | Sızıntı kuralları | drug-disjoint split, train-only scaler, test kenarının grafta olmaması, `selection_complete_before_test_scoring.json` |

### Kısım II — Modeller (her biri A–G şablonuyla)

Her model bölümü **aynı yedi alt başlık**: A amaç · B giriş verileri ·
C gerçek Python temsili · D mimari · E tek ilaç üzerinden çalışma örneği ·
F çıktı yapısı · G metrikler.

| § | Model | Tahmini uzunluk |
|---|---|---|
| 7 | **B0 — sıklık referansı** (3 popülasyon varyantı) | kısa; "parametresiz model" kavramını öğretir |
| 8 | **B1 — 6 boyutlu kimyasal lojistik regresyon** | orta; A–G şablonunun tam örneği (**bu plandaki örnek bölüm**) |
| 9 | **B2 — 234 boyutlu kimya + protein LR** | orta; "daha çok özellik ≠ daha iyi" bulgusu |
| 10 | **WP09 GNN — protein/PPI mesajlaşması** | uzun; ilk gerçek GNN, 141 boyut |
| 11 | **WP10 faktöriyel — A0P0 / A0P1 / A1P0 / A1P1** | **çok uzun**; 150 boyutlu füzyon, 2×2 ablation |
| 12 | **GiG-1a — Graph-in-Graph** | **çok uzun**; ilaç→protein mesajı, dejenerasyon tanısı |
| 13 | (Ek) WP15 ağaç modelleri | yalnız istenirse |

### Kısım III — Grafların anatomisi (rehberin kalbi)

| § | Başlık | İçerik |
|---|---|---|
| 14 | **Atom–bağ moleküler grafı** | 44 atom özelliğinin şema tablosu (element one-hot, derece, yük, H sayısı, hibridizasyon, aromatiklik, halka, CIP, izotop); 14 bağ özelliği (bağ türü, stereo, konjügasyon, halka); SMILES → RDKit `Mol` → `Data` zinciri; `edge_index` ↔ `edge_attr` ayrımı; **çift bağ = tek bağ, `bond_type` one-hot'ta farklı pozisyon**, iki kenar ise **iki yöndür**; değişken atom sayısının `Batch` ile nasıl işlendiği; QC'den geçmeyen 8 molekülde `atom_mask` |
| 15 | **Protein ve PPI grafı** | 56 protein özelliğinin dökümü (6 global + 20 AAC + 5 grup + 25 dipeptit grubu); 125 dizi proteininden yalnız ~48'inin insan STRING-700 mesaj düğümü olması; 4 DrugBank rolü; 700 eşiğinin anlamı (173 yönsüz çift → 346 yönlü kolon, 12 bileşen, 10 izole); `kalite_skoru`'nun **neden dışlandığı** |
| 16 | **Mesajlaşmanın adım adım anatomisi** | Tek düğüm üzerinden: ham özellik → `projection` → ReLU → komşu ortalaması → `self_update` + `message` → residual toplama; iki ayrı görsel (adım 0 ve adım 1); denklemlerin her sembolünün tek tek açıklaması; **neden ikinci adım yok** |
| 17 | **Kenar özelliğinin mesaja girişi** | Moleküler kolda `bond_message(edge_attr)`'ın mesajın içine nasıl eklendiği; protein kolunda kenar özelliği olmadığının açıkça söylenmesi |
| 18 | **Pooling ve füzyon** | `global_mean_pool` ile atom→molekül; rol bazlı maskeli ortalama ile protein→ilaç; 141 + 8 + 1 = 150 birleşimi |
| 19 | **Başlık, logit ve sigmoid** | `Linear(150, K)` → logit → sigmoid; NaN maskeleme; "skor klinik yüzde değildir" |

### Kısım IV — Karşılaştırma ve sonuç okuma

| § | Başlık |
|---|---|
| 20 | Tek büyük karşılaştırma tablosu (B0/B1/B2/WP09/A0P0/A0P1/A1P0/A1P1/GiG-1a; 13 alan) |
| 21 | Metriklerin öğretici anlatımı: AP'nin ne ölçtüğü, 5 PT'lik elle hesaplanmış örnek; drug-macro ↔ class-macro yön farkı (WP14 §5b bulgusu); micro AP; AUROC; bootstrap GA'nın neyi kapsamadığı |
| 22 | Üç tutarlı negatif bulgu: PPI −0,000142 · atom +0,002894 · GiG −0,003536 → "temsil zenginleştirmenin getirisi ~0" örüntüsü |
| 23 | Kapsam dürüstlüğü: 62 envanter / 61 skorlanan / 54 eşleşen; 1685 kapsam-dışı pozitif; unknown ≠ negatif |
| 24 | Sınırlamalar ve bir sonraki adımlar |

### Ekler

- **Ek A** — Dosya haritası: hangi tablo/tensör hangi dosyadan geliyor (`reports/qa/...` yolları)
- **Ek B** — JSON/NPZ biçimleri: metadata ile sayısal girdinin ayrımı
- **Ek C** — "Kendim kodlasam" kontrol listesi: A1P1'i sıfırdan yazmak için 12 adım
- **Ek D** — Danışman sorularına hazır cevap kartları (20 soru)

### Görsel listesi (planlanan)

| No | Görsel | Tür |
|---|---|---|
| G1 | Veri zinciri akış şeması | temsili şema |
| G2 | B1 → B2 → WP09 → A1P1 → GiG mimari evrimi | temsili şema |
| G3 | Bir molekülün atom–bağ grafı (gerçek bir ilaç, RDKit) | **gerçek veri** |
| G4 | Atom özellik vektörünün 44 kutulu şeması | temsili şema |
| G5 | Fold içi insan PPI alt grafı (700 eşiği) | **gerçek veri** |
| G6–G7 | Mesajlaşma adım 0 / adım 1 | temsili şema |
| G8 | A1P1 tam mimari + boyut etiketleri | temsili şema |
| G9 | 150 boyutlu füzyon vektörünün blok haritası | temsili şema |
| G10 | GiG-1a'nın A1P1'den farkı (tek ok) | temsili şema |
| G11 | Model AP karşılaştırması | **gerçek veri** (mevcut WP10/WP14 figürleri) |

Gerçek veriden üretilen her görselin altında kaynak dosya adı yazacak;
temsili şemalar "öğretim amaçlı" etiketiyle işaretlenecek.

### Teslim biçimleri

1. `reports/REHBER_MODEL_MIMARILERI_v1.md` — ana kaynak (Markdown, tablolar + gömülü görseller)
2. `.docx` — mevcut `EMT2_Akademik_v6/calisma/` üretim desenine benzer bir betikle
3. `.pdf` — Word'den dışa aktarma
4. `reports/figures/REHBER/` — yeni görseller (PNG/SVG)

---

## 2. Örnek bölüm taslağı — "§8 B1 modeli"

> Aşağıdaki metin, rehberdeki **her model bölümünün** izleyeceği A–G
> şablonunun tam bir örneğidir. Grafik modellerinde (§10–12) aynı şablon
> korunacak, fakat D ve E alt başlıkları 4–6 kat daha uzun olacak ve
> Kısım III'teki graf anatomisine bağlanacak.

---

### 8. B1 — Beş fizikokimyasal özellikle lojistik regresyon

#### A. Modelin amacı

B1 şu tek soruyu sorar: **"Bir antibakteriyelin sadece beş temel kimyasal
özelliğini bilsem, o ilacın yan etki kayıtlarını rastgeleden daha iyi
sıralayabilir miyim?"**

Bilimsel gerekçe: proje grafik mimarilerine geçmeden önce bir **taban çizgisi**
gerekiyordu. Eğer karmaşık GNN'ler bu beş sayıyı geçemiyorsa, karmaşıklığın
bedeli boşa gitmiş olur. B1 kasıtlı olarak mümkün olan en basit **öğrenen**
modeldir. B0'dan farkı: B0 hiçbir şey öğrenmez, yalnız eğitim sıklığını
tekrarlar. B1 ilacın kendi özelliklerini kullanır, yani ilaca özgüdür.

Sonucu baştan söylemek gerekir, çünkü rehberin geri kalanını anlamlandırır:
**B1, bu kohortta birincil ölçütte tüm GNN'lerden daha yüksek AP aldı
(0,655642).** Bu bir başarı hikâyesi değil, bir **kohort küçüklüğü**
teşhisidir; §22'de ayrıntılandırılacak.

#### B. Kullanılan giriş verileri

| Alan | Değer |
|---|---|
| Kaynak veri seti | PubChem PUG REST (WP04), DrugBank köprüsü üzerinden |
| Özellik sayısı | **6** (`reports/qa/WP08/experimental_preparation/feature_schema_v1.json`) |
| Kullanılan ilaç sayısı | 62 envanterden **61** uygun; Methenamine `ABSTAIN_no_input` |
| Eksik veri politikası | Kimya yoksa blok **nötr 0** + `mask__chemistry = 0`; biyolojik sıfır değildir |
| Standardizasyon | Yalnız **eğitim bölmesinde** fit edilen dönüşüm; `transform_fit_sources_and_statistics.json` |
| Hedef | O fold'un train sözlüğündeki PT'ler (`train_vocabularies.json`) |

Özellik listesi, `feature_schema_v1.json` içinden birebir:

```
chem__MW, chem__LogP, chem__HBD, chem__HBA, chem__TPSA, mask__chemistry
```

**Örnek giriş tablosu** (değerler `example_drug_inputs.json`'dan
DB00199 Erythromycin; diğer satırlar biçim göstermek için temsilîdir):

| drug_id | chem__MW | chem__LogP | chem__HBD | chem__HBA | chem__TPSA | mask__chemistry |
|---|---:|---:|---:|---:|---:|---:|
| DB00199 (Erythromycin) | 733,937 | 1,7856 | 5 | 14 | 193,91 | 1 |
| DB0xxxx (temsilî) | 349,406 | 0,57 | 3 | 7 | 112,30 | 1 |
| Methenamine | 0 | 0 | 0 | 0 | 0 | 0 → **skorlanmaz** |

Son satır önemli: maske 0 olduğunda model bir sayı üretmez, **çekimser
kalır**. "0 tahmin etti" ile "tahmin etmedi" aynı şey değildir.

#### C. Giriş verilerinin gerçek Python temsili

B1'de **tensör, graf, `edge_index` yok.** Gerçek kodda üç biçim var:

**1. İnsan tarafından okunabilir tablo** — yukarıdaki tablo; diske
`reports/qa/WP08/experimental_preparation/features/<context>.npz` olarak değil,
CSV olarak değil, **NPZ** olarak yazılır.

**2. NumPy dizisi** — `wp08_baseline_train.py:185`:

```python
with np.load(PREP/'features'/(context+'.npz'), allow_pickle=False) as arr:
    params, traces, metrics, common = tune_fold(arr[model], arr['drug_ids'], ...)
```

Yani her fold bağlamı için tek bir NPZ dosyası var ve içinde:

| NPZ anahtarı | Şekil | Anlamı |
|---|---|---|
| `drug_ids` | `(N,)` string | Satır sırası = ilaç kimliği |
| `B1` | `(N, 6)` float | B1'in özellik matrisi |
| `B2` | `(N, 234)` float | B2'nin özellik matrisi (aynı dosyada) |

Dikkat: **kimlikler ayrı bir dizide tutulur, özellik matrisinin içinde
değildir.** Bu kasıtlıdır — ID'nin modele özellik olarak sızmasını engeller.

**3. Matematiksel boyut gösterimi**

$$X^{\text{B1}} \in \mathbb{R}^{N \times 6},\qquad N = \text{o fold'daki ilaç sayısı}$$

Örnek: `primary_o03_final` bağlamında train 49 ilaç → `X.shape == (49, 6)`.

#### D. Model mimarisi

| Özellik | Değer (koddan) |
|---|---|
| Model türü | L2 düzenlileştirilmiş **ikili lojistik regresyon**, her PT için ayrı |
| Kütüphane | `scikit-learn` (`LogisticRegression`), `scipy.special.expit` |
| Katman | Tek doğrusal katman + sigmoid; gizli katman **yok** |
| Giriş → çıkış | 6 → 1 (her PT için ayrı model) |
| Öğrenilebilir parametre | PT başına 6 ağırlık + 1 kesme = **7** |
| Çözücü | `liblinear`, `tol=1e-8`, `max_iter=10000` |
| C ızgarası | `(0.1, 1.0, 10.0)` — yalnız iç katlarda seçilir |
| Sınıf ağırlığı | **Yok** (`class_weight=None`) |
| Kayıp | L2 cezalı lojistik kayıp (sklearn'in kendi amacı) |

Gerçek koddan çekirdek (`wp08_baseline_train.py:84-92`):

```python
model = LogisticRegression(C=C, solver='liblinear', class_weight=None,
                           tol=1e-8, max_iter=10000, random_state=SEED)
model.fit(X, s)                      # s = o PT için 0/1 gözlenen kayıt
...
fitted[target] = (model.coef_[0].copy(), float(model.intercept_[0]))
```

Tahmin ise ağırlıkları elle uygulayarak yapılır (`:100-105`):

```python
out[:, j] = expit(X @ coef + intercept)
```

**Tablo karşılığı** — `X @ coef + intercept` işleminin tek satır için anlamı:

| Terim | Değer (temsilî) | Katkı |
|---|---:|---:|
| MW × w₁ | 733,937 × 0,0004 | +0,294 |
| LogP × w₂ | 1,7856 × (−0,21) | −0,375 |
| ... | ... | ... |
| kesme (b) | — | −0,88 |
| **logit toplamı** | | **−0,42** |
| **sigmoid(−0,42)** | | **0,3965** |

Kritik mimari detay: **PT başına bağımsız bir model var.** Yani 306 PT için
306 ayrı ağırlık vektörü. PT'ler arası bilgi paylaşımı **yoktur**. GNN'lerde
bu değişir: orada 150 boyutlu tek temsil, `Linear(150, K)` ile **bütün** PT'lere
aynı anda bakar. Rehberin §11'i bu farkı ayrıca işler.

Bir PT'de eğitim bölmesinde ya hep 0 ya hep 1 varsa model kurulmaz:
`status='NA_single_proxy_outcome'`. Yedek/varsayılan değer **atanmaz**.

#### E. Modelin çalışma örneği (DB00199 Erythromycin, tek ilaç)

| Adım | Ne oluyor | Boyut |
|---|---|---|
| 1 | WP04 PubChem değerleri okunur | 5 sayı |
| 2 | Train-only dönüşüm uygulanır (`transform`, **fit değil**) | `(1, 6)` |
| 3 | Maske kontrol edilir: `mask__chemistry = 1` → skorlanabilir | — |
| 4 | O fold'un her PT'si için `X @ coef_j + b_j` | 306 logit |
| 5 | `expit` (sigmoid) her logiti (0, 1) aralığına taşır | 306 skor |
| 6 | Skorlar **bu ilaç için** büyükten küçüğe sıralanır | sıralı liste |

Erythromycin bu fold'da `primary` outer 3 **test** sorgusudur — yani bu ilaç
hiçbir aşamada eğitime girmedi. Gerçek sıralamaları
`reports/qa/WP10/training_v1/example_drug_PT_ranking.csv` dosyasında saklı.

#### F. Model çıktıları

Çıktı tek bir uzun tablodur (`oof_predictions.csv`), satır başına **bir
ilaç–PT çifti**:

| protocol | outer_fold | model | drug_id | class_id | observed_record_s | score_observed_record_proxy |
|---|---|---|---|---|---|---|
| primary | 3 | B1 | DB00199 | C0011991 | 1 | 0,78 |
| primary | 3 | B1 | DB00199 | C0027497 | 1 | 0,71 |
| primary | 3 | B1 | DB00199 | C0019080 | 0 | 0,33 |

Yukarıdaki skorlar **biçim göstermek için temsilîdir**; gerçek sayılar
adı geçen CSV'de. İnsan okuması için aynı veri geniş biçime çevrilebilir:

| İlaç | Yan etki A | Yan etki B | Yan etki C |
|---|---:|---:|---:|
| İlaç 1 | 0,82 | 0,43 | 0,71 |
| İlaç 2 | 0,21 | 0,65 | 0,34 |

**Bu sayılar klinik yan etki görülme yüzdesi değildir.** `observed_record_s = 1`
"SIDER'da kayıt var", `0` ise "**kayıt yok**" demektir — "yan etki yok"
demek değildir. Modelin işi bu kayıtları doğru **sıralamaktır**.

#### G. Başarı metrikleri

| Metrik | primary / paired54 | %95 GA |
|---|---:|---|
| **drug-macro AP** (birincil) | **0,655642** | [0,613111; 0,692041] |
| class_macro_AP | 0,3152 | GA yok (pooled, diagnostic) |
| B0_like_B1 referansı | 0,643787 | [0,602130; 0,681983] |
| B1 − B0_like_B1 | ~+0,0119 | GA sıfırı içerir |

Kaynak: `reports/WP10_TRAINING_RESULTS.md` §5 ve `reports/WP14_GIG1A_RESULTS.md` §3/§5b.

**Metrikler ne anlatıyor?** — AP (Average Precision), *tek bir ilaç için*
PT'leri skora göre sıraladığımızda gerçek kayıtların ne kadar üste geldiğini
ölçer. Beş PT'lik öğretici bir örnek:

| Sıra | PT | Skor | Gerçek kayıt var mı? | O noktadaki precision |
|---|---|---:|---|---:|
| 1 | PT-a | 0,91 | **Evet** | 1/1 = 1,00 |
| 2 | PT-b | 0,77 | Hayır | — |
| 3 | PT-c | 0,66 | **Evet** | 2/3 = 0,67 |
| 4 | PT-d | 0,40 | Hayır | — |
| 5 | PT-e | 0,12 | **Evet** | 3/5 = 0,60 |

AP = (1,00 + 0,67 + 0,60) / 3 = **0,757**. Yani AP yalnız doğru/yanlış
saymaz, **doğruların ne kadar yukarıda olduğunu** ödüllendirir.

**Neden bu metrik seçildi?** Çünkü pozitifler seyrek (13.964 çiftin 3.820'si
pozitif) ve karar eşiği yok; sorduğumuz soru "bu ilaç için hangi yan etkilere
önce bakılmalı?" sorusudur. Doğruluk (accuracy) burada yanıltıcı olurdu.

**drug-macro** = her ilaç için AP hesaplanır, sonra ilaçlar üzerinde ortalanır.
Böylece çok kayıtlı bir ilaç toplamı domine etmez.

**Hesaplamanın kapsamı** (uydurma yok, hesaplanmamış metrik yazılmaz):

| Alan | Değer |
|---|---|
| Veri bölmesi | Nested CV'nin **outer test** katları, OOF |
| Kapsam | `paired54` — dört modelin ortak skorladığı 54 ilaç |
| Çift sayısı | 13.964 (3.820 pozitif + 10.144 unknown) |
| GA yöntemi | 1000 eşleştirilmiş yapısal grup bootstrap, seed 20261106+9000+protokol |
| GA'nın **kapsamadığı** | Yeniden eğitim varyansı, seed varyansı, kaynak kayıt yanlılığı, dış kohort |
| Precision/Recall | Eşik tanımlanmadığı için **hesaplanmadı** → rehberde "hesaplanmadı" yazacak |
| Abstention | 62'den 1 ilaç (Methenamine), kapsam 61 |

---

## 3. Onay istenen noktalar

| # | Karar | Önerim |
|---|---|---|
| 1 | İçindekiler planı (Kısım I–IV + 4 ek) uygun mu? | Onay |
| 2 | A–G şablonu ve yukarıdaki B1 örneğinin **detay seviyesi** yeterli mi, yoksa daha derin/daha yüzeysel mi olsun? | Bu seviye |
| 3 | WP15 ağaç modelleri ek olarak girsin mi? | Kısa ek olarak girsin |
| 4 | Teslim biçimi: Markdown + DOCX + PDF üçlüsü mü, yoksa yalnız Markdown + PDF mi? | Üçü |
| 5 | Yeni görseller üretilsin mi (G3–G10), yoksa yalnız mevcut WP10/WP14 figürleri kullanılsın mı? | Üretilsin |
| 6 | Tek dosya mı, yoksa Kısım başına ayrı dosya mı? | Tek dosya + ayrı figür klasörü |

**Hiçbir mevcut dosya değiştirilmedi.** Bu plan dosyası dışında yazılan bir
şey yok.
