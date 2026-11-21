# Graph-in-Graph ve A1P1 — Mimari Çözümleme, Fizibilite ve Karar

> 14.11.2026 · Yalnız çözümleme ve karar. **Hiçbir model eğitilmedi, hiçbir
> dondurulmuş çıktı değiştirilmedi.** Bu raporda geçen her sayı ya kaynak
> kodundan ya da `reports/qa/` altındaki kayıtlı çıktılardan alınmıştır.

---

## 1. Kapsam ve incelenen kaynaklar

| Kaynak | Kullanım |
|---|---|
| `EMT1_FİNAL_RAPOR_SON.pdf` §4.3 (s.29–31) | GiG biçimselleştirmesi, Denklem (4.1)–(4.14) |
| `legacy/MASTER_KOD.py`, `legacy/Kod_Aciklama_Raporu.docx` | V6'da fiilen çalıştırılan kod |
| `scripts/wp09_encoder.py` | `ResidualMeanProtein`, `RoleMaskedPPI` |
| `scripts/wp10_molecular_encoder.py` | `BondAwareMolecularEncoder`, `MolecularProteinFusion` |
| `scripts/wp10_train.py` | Kayıp, optimizer, epoch politikası |
| `reports/qa/WP10/training_v1/fold_train_validation_test_scope.csv` | Kat başına kapsam ve sızıntı bayrakları |
| `reports/qa/WP10/training_v1/model_fit_summary.csv` | 152 fit, hedef sayıları, optimizer adımları |
| `reports/WP08_FINAL_CONCLUSIONS.md`, `WP09_FINAL_CLOSURE.md`, `WP10_FINAL_CLOSURE.md` | Kabul edilmiş AP sonuçları |

**Bir düzeltme:** Görevde `GRAPH_TEZ_V7_TEKNIK_HAKIMIYET_SAVUNMA_REHBERI.docx`
adlı bir belge isteniyor. Bu adda dosya yoktur. Projedeki karşılığı
`EMT2_Teslim_v1/GRAPH_TEZ_V7_THEORY_AND_DEFENSE_GUIDE.docx` (12 sayfa) olup
bu çözümlemede kullanılmıştır.

---

## 2. EMT1'in Graph-in-Graph'ı gerçekte nedir?

### 2.1 Biçimselleştirme (EMT1 §4.3.2, Denklem 4.8–4.13)

| Adım | Denklem | Anlamı |
|---|---|---|
| 1 | `h_p = MLP_P(x_p) = W₂·ReLU(W₁·x_p + b₁) + b₂` | Protein gömmesi |
| 2 | `h_d⁽⁰⁾ = MLP_D(x_d)` | İlaç temel gömmesi |
| 3 | `μ_d = (1/\|N(d)\|)·Σ_{p∈N(d)} h_p` | Hedef proteinlerin ortalaması |
| 4 | `h_d = ReLU(W_agg·[h_d⁽⁰⁾ ∥ μ_d] + b_agg)` | Birleştirme + doğrusal olmayan karıştırma |
| 5 | `h_s = MLP_S(x_s)` | Yan etki gömmesi (x_s = 30 boyutlu one-hot) |
| 6 | `ŷ_ds = σ(MLP_pred([h_d ∥ h_s]))` | Ortak tahmin başlığı |

### 2.2 Belirleyici bulgu: `E_PP` denklemlerde yok

EMT1 §4.3.1'de protein–protein kenar kümesi açıkça tanımlanır:

> "protein–protein etkileşim kenarları (E_PP, |E_PP| = 70)"

Ancak **Denklem (4.8)–(4.13) dizisinin hiçbir adımında `E_PP` geçmez.**
`h_p` yalnızca `x_p`'nin bir MLP dönüşümüdür; komşu proteinlerden mesaj
almaz. İç ağ üzerinde tanımlı bir yayılım denklemi yoktur.

Bunun iki sonucu vardır:

1. **V6 kodu EMT1 tasarımından sapmamıştır.** `MASTER_KOD.py` içindeki
   `forward(self, x_drug, x_prot, x_se, dp_ei, pred_drug_idx, pred_se_idx)`
   imzasında PPI parametresi bulunmaması bir uygulama hatası değil, EMT1
   biçimselleştirmesinin birebir karşılığıdır.
2. **EMT1'in "Graph-in-Graph" adlandırması, gerçek bir iç içe graf öğrenme
   mimarisini değil, kavramsal bir heterojen graf şemasını tanımlar.**
   "İç ağ", üzerinde mesaj geçirilmeyen bir düğüm kümesidir; `E_PP`
   yalnızca graf şemasında yer alır.

Bu, bu raporun en önemli teknik tespitidir ve aşağıdaki bütün
değerlendirmeyi belirler.

### 2.3 EMT1'in gerçek öğrenme mekanizması

Tasarımdan mesaj geçişi çıkarıldığında geriye şu kalır:

```
ilaç özellikleri ──MLP──┐
                        ├─ concat ─ ReLU(W_agg·) ─┐
hedef proteinlerin      │                        ├─ MLP_pred ─ σ ─ ŷ
ortalama MLP gömmesi ───┘                        │
yan etki kimliği ──embedding──────────────────────┘
```

Yani: **ilaç özellikleri + hedef proteinlerin ortalama gömmesi + yan etki
kimliği üzerinden bir bağlantı tahmini.** Bu, literatürdeki adıyla bir
"drug–target mean aggregation + link predictor" modelidir.

---

## 3. A1P1 gerçekte nedir?

### 3.1 Uçtan uca akış (kod düzeyinde)

| Aşama | Kod | İşlem | Boyut |
|---|---|---|---|
| Protein kodlayıcı | `ResidualMeanProtein.forward` | `z = ReLU(P·x)`, sonra `z + ReLU(S·z + M·mean_komşu(z))` | 56 → 32 |
| **PPI mesaj geçişi** | aynı fonksiyon, `index_add` | Yönsüz çiftler iki yöne açılır, komşu ortalaması alınır; `G_noPPI`'de kenar tensörü `edges[:,:0]` ile boşaltılır | 346 yönlü sütun (dış kat) |
| Rol okuması | `RoleMaskedPPI.readout` | `target`, `enzyme`, `transporter`, `carrier` için **ayrı** maskeli ortalamalar | 4 × 32 = 128 |
| Kimya | `self.chemistry` | `ReLU(Linear(5,8)) × maske` | 8 |
| Maskeler | — | 5 boolean alan temsile eklenir | 5 |
| **Taban temsil** | `torch.cat` | — | **141** |
| Molekül kodlayıcı | `BondAwareMolecularEncoder` | `h = h₀ + ReLU(S·h₀ + mean_j ReLU(U·h₀ⱼ + V·e_ji))`, sonra `global_mean_pool` → `ReLU(Linear(16,8))` | atom 44 / bağ 14 → 8 |
| Atom maskesi | `_fuse` | QC54 açık / 8 kapalı | 1 |
| **Füzyon** | `torch.cat` | — | **150** |
| Başlık | `nn.Linear(150, K)` | PT başına **bağımsız** doğrusal okuma | 150 → K |
| Abstention | `masked_fill(~eligible)` | Hiç girdisi olmayan ilaçta logit `NaN` | — |

### 3.2 On soruya yanıt

1. **Moleküler GNN:** Tek katmanlı, bağ-duyarlı artık ortalama geçişi;
   atom 44 boyut, bağ 14 boyut, gizli 16, okuma 8. GIN veya GCN değildir;
   PyG'den yalnız `global_mean_pool` kullanılır.
2. **Protein ve PPI:** 56 sayısal protein alanı 32 boyuta indirgenir;
   STRING v12 insan (taxid 9606) eşik-700 alt grafında **gerçek** komşu
   ortalaması alınır. Kanıt: ağırlıklardan kenar çıkarıldığında protein L2
   farkı **13,162168**; mesaj ağırlığı gradyan normu **0,0040160404**;
   `G_noPPI`'de her ikisi de **0** (`WP09_FINAL_CLOSURE.md`).
3. **Dört rol:** Ayrı ayrı toplanır, her biri kendi maskesiyle çarpılır;
   rol maskesi ile tipli kenarlar çelişirse hata yükseltilir.
4. **Birleştirme:** İlaç ve protein bilgisi **okuma (readout) aşamasında**
   birleşir — rol ortalamaları ilaç satırına `index_add` ile taşınır.
5. **Tahmin başlığı:** `Linear(150, K)`. Her PT için bağımsız bir 150
   boyutlu ağırlık vektörü.
6. **SIDER etiketleri:** Yalnız kayıp fonksiyonunda. `fold_train_validation_test_scope.csv`
   içindeki `side_effect_edges` sütunu **152 işin tamamında `False`**.
7. **Maskeler ve abstention:** Eksik modalite nötr sıfır blok + ayrı
   bulunabilirlik maskesi; hiçbir girdisi olmayan ilaç (Methenamine)
   `NaN` döndürür, önsel ile doldurulmaz.
8. **İndüktif geçerlilik:** `query_readout` görülmemiş proteinleri
   **kenarsız** (self-only) işler ve train önbelleğine geri mesaj
   göndermez; önbellek graf ve model özetine bağlanmıştır.
9. **Parametre sayısı (ölçüldü):**

   | Bileşen | Parametre |
   |---|---:|
   | `RoleMaskedPPI` tabanı | 3.920 |
   | Moleküler kodlayıcı | 1.592 |
   | **Omurga toplamı** | **5.512** |
   | Başlık (K = 240) | 36.240 |
   | **A1P1 toplamı (K = 240)** | **41.752** |

   **Parametrelerin %86,8'i tahmin başlığındadır.** Graf öğrenmesini
   yapan omurga yalnızca %13,2'dir.
10. **PPI katkısının gösterilememesi:** Kayıtlı sonuç
    `real − noPPI = −0,000142`, koşullu %95 GA `[−0,003611; +0,003248]`.
    Olası nedenler (hiçbiri ayrıştırılmış değildir): 63 düğümlü, 184
    kenarlı, 12 izole düğümlü seyrek alt graf; rol-ortalaması sonrası
    topolojik bilginin erimesi; 48 ilaçlık eğitim kümesinde yüksek
    varyans; ve SIDER kayıt mekanizmasının protein biyolojisinden çok
    raporlanma sıklığını yansıtması.

### 3.3 A1P1 tam heterojen mesajlaşmalı bir GiG midir?

**Kısmen — ve EMT1'in tanımından daha fazlasıdır.**

- **Gerçek iç ağ mesajlaşması vardır** (protein–protein). EMT1'de yoktur.
- **Tipli (rol ayrımlı) dış ağ toplaması vardır.** EMT1'de tek, tipsiz
  ortalama vardır.
- **Atom düzeyinde üçüncü bir iç graf vardır.** EMT1'de yoktur.
- **Yan etki düğümü bir graf düğümü değildir**; başlıktaki bir satırdır.
  Bu, EMT1'e göre eksik olan tek yapısal öğedir.

Dolayısıyla A1P1, EMT1 GiG'inin **gerçek bir üst kümesidir** — tek
istisnası yan etki düğümü temsilidir.

---

## 4. Karşılaştırma tablosu

| Kriter | A1P1 (uygulanmış) | EMT1 GiG (tasarım) | Değerlendirme |
|---|---|---|---|
| Mimari yapı | Üç kodlayıcı: atom grafı, PPI grafı, rol toplaması; doğrusal başlık | İki MLP + tek ortalama + ortak MLP başlığı | A1P1 kesin üst küme; tek fark başlık |
| Düğüm türleri | İlaç, protein (atom ayrıca) | İlaç, protein, yan etki | Yan etki düğümü yalnız EMT1'de |
| Kenar türleri | `target/enzyme/transporter/carrier`, PPI, atom–bağ | `targets`, `interacts`, `causes` | `interacts` EMT1'de tanımlı ama **kullanılmıyor** |
| Atom-bağ bilgisi | Var (44/14, tek katman) | Yok | A1P1 lehine |
| Protein-PPI kullanımı | **Gerçek mesaj geçişi**, kanıtlı | **Yalnız şemada**; denklemlerde yok | A1P1 lehine |
| Yan etki düğümünün rolü | Başlık satırı (örtük gömme) | Açık `h_s` gömmesi + ortak başlık | EMT1 lehine olabilecek **tek** öğe |
| Mesajlaşma mekanizması | Artık ortalama, maskeli, tipli | Tipsiz tek ortalama | A1P1 lehine |
| Heterojen ilişkilerin korunması | Dört rol ayrı tutulur | Roller birleştirilir | A1P1 lehine |
| İndüktif tahmin | Önbellek izolasyonu + self-only query ile kanıtlı | Tasarımda mümkün, kanıt yok | A1P1 lehine |
| Etiket sızıntısı riski | `side_effect_edges=False`, 152/152 | `E_DS` yalnız hedef; mesajlaşmada yok → **risk yok** | İkisi de güvenli |
| Eksik veri yönetimi | Nötr blok + maske + abstention | Tanımsız | A1P1 lehine |
| Hesaplama maliyeti | 41.752 parametre (K=240); 37–92 optimizer adımı/iş | Benzer mertebe, başlık daha küçük | Bkz. §6.7 |
| Açıklanabilirlik | WP11 mesaj maskeleme (Δz) + B1 SHAP | Tanımsız | A1P1 lehine; ortak başlık Δz'yi karmaşıklaştırır |
| Küçük veri kümesine uygunluk | **Zayıf**: 48 ilaçtan 240 bağımsız 150-boyutlu vektör | **Daha iyi**: ortak başlık, düşük ranklı çarpanlama | **EMT1 lehine** |
| Beklenen avantaj / sınır | Zengin temsil; başlıkta aşırı parametrelenme | Zayıf temsil; istatistiksel güç paylaşımı | Melez tasarım mantıklı |

---

## 5. Etiket sızıntısı çözümlemesi

### 5.1 EMT1 GiG'i uygulamak sızıntı yaratır mı? — Hayır

EMT1'in denklemlerinde `x_s` **30 boyutlu one-hot**tur; yani yan etki
düğümü yalnızca *kimliğini* taşır, hiçbir veri türevi bilgi taşımaz.
`E_DS` kenarları hiçbir ileri yayılım denkleminde geçmez; yalnız Denklem
(4.14)'teki denetim hedefidir.

Dolayısıyla **EMT1 tasarımının sadık uygulanması etiket sızıntısı
içermez.** Görev tanımındaki §6 kaygısı, EMT1'in belirttiği mimariye
değil, yan etki kenarlarının encoder'a verildiği *genişletilmiş* bir
varyanta aittir.

### 5.2 Yan etki düğümleri mesajlaşmaya katılsaydı

`E_DS` kenarları encoder'a verilseydi, bir yan etki düğümünün gömmesi
kendisine bağlı ilaçlardan bilgi toplardı. Test ilacının o kenarları
çıkarılsa bile **diğer** ilaçların etiketleri sınıf gömmesini biçimlendirir;
bu, çok etiketli kurulumda meşru bir tümevarımdır ancak test ilacının
kendi kenarı asla girmemelidir.

Matematiksel koşul: eğitim grafında kullanılan kenar kümesi
`E_DS^enc ⊆ {(d,s) : d ∈ D_train}` olmalı ve değerlendirme anında test
ilacı için `N_S(d_test) = ∅` kabul edilmelidir.

Mevcut kod bu koşulu zaten **daha güçlü** biçimde sağlar: hiçbir `E_DS`
kenarı encoder'a girmez (`side_effect_edges=False`). Önerilen tasarım da
bu güçlü koşulu koruyacaktır — yani yan etki düğümü **yalnız kimlik
gömmesi** olarak kalacak, komşuluk toplamayacaktır.

### 5.3 Korunacak güvenceler

- Test ilacına ait hiçbir PT etiketi encoder'a, ölçekleyiciye, hedef
  sözlüğüne veya model seçimine girmez.
- Hedef sözlüğü yalnız ilgili train bölmesinden kurulur (≥5 pozitif
  uygun ilaç, ≥2 bağımsız grup).
- SIDER'da kayıt bulunmaması **doğrulanmış negatif değildir**; `unknown`
  semantiği korunur.
- Dondurulmuş 5 dış / 3 iç kat ve ilaç kimlikleri değişmez.

---

## 6. On fizibilite sorusu

**6.1 Teknik olarak mümkün mü?** Evet. Gerekli olan tek şey yeni bir
başlık modülüdür; graf kurulumu, veri yükleyici, bölme ve değerlendirme
boru hattı aynen kullanılabilir. Omurga (`RoleMaskedPPI`,
`BondAwareMolecularEncoder`) değiştirilmeden yeniden kullanılır.

**6.2 Beklenen bilgi kazanımı nedir?** EMT1'in asıl mimari katkısının
—yan etki düğümü gömmesi ve ortak tahmin başlığı— ölçülebilir bir
etkisi olup olmadığı. Bu, tezde "EMT1'in tasarımını denedik mi?"
sorusuna kanıtla yanıt verir.

**6.3 A1P1'in çözemediği hangi problemi çözebilir?** A1P1'in başlığı 48
eğitim ilacından **240 bağımsız 150-boyutlu ağırlık vektörü** öğrenir
(vektör başına ~0,2 ilaç). Ortak başlık bunu düşük ranklı bir
çarpanlamaya indirger ve PT'ler arasında istatistiksel güç paylaşır.
Bu, A1P1'in sıklık referansını (B0 ≈ 0,6466) aşamamasının olası bir
nedenini doğrudan hedefler.

**6.4 Yan etki düğümleri gerçekten avantaj sağlar mı?** Mesajlaşmaya
katılırlarsa belirsiz ve riskli. **Kimlik gömmesi olarak** ise
savunulabilir bir düzenlileştirme sağlar — ölçülen parametre azalması:

| Yapılandırma | K=171 | K=240 | K=326 |
|---|---:|---:|---:|
| A1P1 başlığı `Linear(150,K)` | 25.821 | 36.240 | 49.226 |
| Ortak başlık (e=16, H=32) | 8.113 | 9.217 | 10.593 |
| Ortak başlık (e=32, H=64) | 17.249 | 19.457 | 22.209 |

**6.5 Sızıntısız test edilebilir mi?** Evet — §5'teki güçlü koşul
korunarak. Yan etki gömmesi veriden değil, kimlikten türetilir.

**6.6 Örneklem yeterli mi?** **Hayır, bol değil.** Birincil
karşılaştırma 54 ilaç üzerindedir; dış kat eğitimi 48–50 ilaç, iç kat 32
ilaçtır. Bağımsız gözlem birimi ilaçtır, çift değil. Bu, mevcut
mimarilerden **daha karmaşık** bir model için yeterli değildir; ancak
**daha az parametreli** bir başlık için uygun bir ortamdır. Deneyin
yönü bu nedenle "büyütmek" değil, "küçültmek" olmalıdır.

**6.7 Aşırı öğrenme riski nasıl değişir?** Toplam parametre K=240 için
41.752'den ≈14.700'e (e=16, H=32) iner — **%65 azalma**. Risk artmaz,
azalır. Ancak ortak başlık PT'ler arası benzerlik varsayımı getirir; bu
varsayım yanlışsa başarım düşebilir. Bu da bilgi değeri olan bir sonuçtur.

**6.8 Hesaplama maliyeti nedir?** Kayıtlı WP10 çalışması 152 fit, toplam
8.611 optimizer adımı, iş başına 37–92 adımdır. Önerilen deney aynı
protokolde **tek bir ek model kolu** ekler: 152 fit daha. Omurga
değişmediğinden adım maliyeti benzerdir; CPU üzerinde mevcut WP10 ile
aynı mertebede (saatler değil, dakikalar–onlarca dakika) beklenir.

**6.9 PPI katkısının gösterilememesi beklentiyi nasıl etkiler?** Önemli
ölçüde **düşürür**. Gerçek PPI mesaj geçişi (`real − noPPI = −0,000142`),
gerçek atom grafı (`marjinal atom = +0,002894`, stres alt sınırı
`+0,000006`) ve 234 alanlı protein özeti (B2 = 0,6262 < B1 = 0,6556) —
üçü de bu veri kümesinde kayda değer kazanç üretmedi. Temsili
zenginleştirmenin getirisi bu kohortta sistematik olarak düşüktür.
Dolayısıyla **ortak başlıktan da büyük bir kazanç beklenmemelidir**;
beklenti, küçük bir iyileşme veya bilgilendirici bir sıfır sonuçtur.

**6.10 Tezin bilimsel katkısını artırır mı?** Evet, ancak sonucu ne
olursa olsun. Şu an tezde "EMT1'in önerdiği mimari denenmedi" boşluğu
vardır. Bu deney, ya EMT1 tasarımının bir öğesinin işe yaradığını ya da
yaramadığını **aynı dondurulmuş protokolde** kanıtlar. Sıfır sonuç da
yayınlanabilir bir bulgudur ve §6.9'daki örüntüyü güçlendirir.

---

## 7. Karar

> ## **IMPLEMENT_CONDITIONALLY**

### Gerekçe

**Lehine:**
- Teknik olarak düşük riskli: omurga değişmez, yalnız başlık değişir.
- Sızıntı riski yok: yan etki düğümü kimlik gömmesidir, komşuluk toplamaz.
- Parametre sayısını %65 azaltır — küçük kohort için doğru yön.
- A1P1'in gözlenen zayıflığını (başlıkta aşırı parametrelenme) doğrudan
  hedefler.
- Tezdeki "EMT1 mimarisi denenmedi" boşluğunu kapatır.

**Aleyhine:**
- Bu kohortta temsil/mimari değişikliklerinin getirisi sistematik olarak
  düşük çıkmıştır (§6.9).
- 54 ilaçlık karşılaştırmada ±0,04 mertebesindeki güven aralıkları, küçük
  farkları ayırt etmeye yetmeyebilir.
- Ortak başlık, WP11'in PT-özgü mesaj maskeleme açıklamalarını
  karmaşıklaştırır (artık PT'ler ağırlık paylaşır).

### Koşullar (hepsi sağlanmadan eğitim başlatılmaz)

1. **Adlandırma dürüstlüğü.** Model `A1P1+SEHead` veya `GiG-Head` olarak
   adlandırılır. **"Graph-in-Graph" adı kullanılmaz**, çünkü EMT1'in
   kendi denklemlerinde iç ağ mesajlaşması yoktur (§2.2) ve yan etki
   düğümü mesaj almaz. Rapor bunu açıkça belirtir.
2. **Protokol sonuçlardan önce kilitlenir** (§8), hash ile dondurulur.
3. **Yan etki düğümü yalnız kimlik gömmesidir**; `E_DS` encoder'a girmez.
4. **Hiperparametreler iç katlarda seçilir**, dış test sonuçlarına
   bakılmaz. `e` ve `H` için en fazla iki aday denenir.
5. **A1P1, B1, B2, B0 yeniden eğitilmez**; mevcut OOF skorları aynen
   karşılaştırma referansı olur.
6. **Sentetik kapı önce geçilir:** mesajlaşma, gradyan ve izolasyon
   testleri gerçek veriden önce küçük yapay graflarda doğrulanır.

---

## 8. Önerilen deney protokolü (onay sonrası kilitlenecek)

### 8.1 Model

```
h_rep  = A1P1 omurgası (değişmez, 150 boyut)          # dondurulmuş mimari
e_s    = Embedding(K, e)                              # yan etki kimlik gömmesi
z_ds   = ReLU(W₁ · [h_rep ∥ e_s] + b₁)                # ortak karıştırma (EMT1 4.11/4.13)
ŷ_ds   = W₂ · z_ds + b₂                               # tek skaler logit
```

EMT1 Denklem (4.11)'deki `W_agg + ReLU` karıştırması ve (4.13)'teki ortak
`MLP_pred` böylece birlikte uygulanır. A1P1'in `Linear(150,K)` başlığı
yerine geçer; omurga bit düzeyinde aynıdır.

### 8.2 Sabit tutulacaklar

| Öğe | Değer |
|---|---|
| Kohort | 62 ilaç; birincil karşılaştırma ortak 54 |
| Bölme | Dondurulmuş 5 dış / 3 iç, ilaç-ayrık + ayrı stres protokolü |
| Hedef sözlüğü | Train-only, ≥5 pozitif / ≥2 grup |
| Ölçekleyici | Train-only, mevcut dondurulmuş hali |
| Kayıp | `BCEWithLogitsLoss`, gözlenen-kayıt vekili, ağırlıksız |
| Optimizer | AdamW, lr 1e-3, wd 1e-3 |
| Epoch | max 200, patience 20, min_delta 1e-4 |
| Seed | 20261106 tabanlı mevcut formül |
| PPI eşiği | 700, katı insan |

### 8.3 Aranacak hiperparametreler (yalnız iç katlarda)

`(e, H) ∈ {(16, 32), (32, 64)}` — iki aday, iç kat drug-macro AP ile seçim.

### 8.4 Birincil ölçüt ve kabul kriteri

- **Birincil:** ortak 54 ilaç, drug-macro observed-record AP.
- **Kabul:** `GiG-Head − A1P1` farkının koşullu %95 grup bootstrap GA'sı
  **tamamen sıfırın üzerinde** olmalı **ve** stres protokolünde nokta
  tahmini negatif olmamalı.
- Bu sağlanmazsa sonuç **"ek katkı gösterilemedi"** olarak raporlanır ve
  A1P1 ana araştırma mimarisi olarak korunur.
- B1 (0,6556) her durumda referans olarak raporlanır. **"Ana graf
  araştırma mimarisi" ile "en yüksek AP'li model" tezde ayrı kavramlar
  olarak sunulmaya devam eder.**

### 8.5 Ek ölçütler

Micro AP · PT bazında AP · fold başına AP · kapsam ve abstention ·
parametre sayısı · optimizer adımı ve süre · stres protokol sonuçları ·
tanımsız durumlar `NA`.

### 8.6 Doğrulama kapıları (gerçek eğitimden önce)

1. Sentetik graf: mesajlaşma ve gradyan akışı.
2. `side_effect_edges=False` iddiasının yeni kolda da testi.
3. Heldout etiket mutasyon testi: test etiketleri değiştirildiğinde
   eğitim ağırlıkları değişmemeli.
4. Omurga eşitliği: yeni modelin omurga ağırlıkları A1P1 ile aynı
   başlangıç durumundan türemeli.
5. Önbellek izolasyonu: query → train geri mesajı olmamalı.

### 8.7 Dokunulmayacaklar

`models/`, `reports/qa/WP08-WP11`, dondurulmuş OOF skorları, mevcut
manifestler, A1P1/B0/B1/B2 ağırlıkları. Yeni çıktılar ayrı bir
`WP14/` ad alanına yazılır.

---

## 9. Diyagramlar

| Dosya | İçerik |
|---|---|
| `reports/figures/WP14/01_mimari_karsilastirma.png` (+ `.svg`) | EMT1 GiG tasarımı ile A1P1 uygulamasının yan yana karşılaştırması; `E_PP`'nin denklemlerde bulunmadığı işaretli |
| `reports/figures/WP14/02_veri_akisi.png` (+ `.svg`) | Kaynaktan yan etki skoruna veri akışı ve sızıntı sınırı |

Üretici: `scripts/wp14_diagrams.py` (yalnız çizim; veri veya model okumaz).

---

## 10. Sonraki adım

Bu rapor **karar aşamasında durur.** Eğitim, kullanıcı onayı ve §8'deki
protokolün hash ile kilitlenmesinden sonra başlatılacaktır.

Onay verilirse sıra: sentetik kapı → protokol kilidi → iç kat seçimi →
dış kat eğitimi → karşılaştırma raporu → ana model kararı için ayrıca
onay.
