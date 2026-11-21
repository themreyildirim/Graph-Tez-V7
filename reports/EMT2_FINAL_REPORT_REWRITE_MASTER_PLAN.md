# EMT2 Final Raporu — Modelleme Değerlendirmesi ve Yeniden Yazım Ana Planı

> 14.11.2026 · **Plan aşaması.** Hiçbir model eğitilmedi, final raporu
> yazılmadı. Resmî şablon alındı ve çözümlendi.
> Bütünlük manifestleri sabit: 1567 / 1711 / 2487.

---

# ÇIKTI 1 — Mevcut modellerin bilimsel değerlendirmesi

## 1.1 Önermenin düzeltilmesi: "B1, A1P1'den daha başarılı"

Görev tanımında B1'in daha yüksek başarı elde ettiği belirtilmiştir.
Nokta tahminleri bunu destekler; **belirsizlik aralığı desteklemez.**

`reports/qa/WP10/training_v1/paired_reference_differences.csv`
(primary · paired54 · drug_macro_AP):

| Fark | Değer | %95 GA | Ayırt edilebilir mi? |
|---|---:|---|---|
| **A1P1 − B1** | **−0,009408** | **[−0,025901; +0,005600]** | **Hayır** |
| A1P0 − B1 | −0,009712 | [−0,025997; +0,004416] | Hayır |
| A0P1 − B1 | −0,012006 | [−0,028977; +0,003411] | Hayır |
| A0P0 − B1 | −0,012902 | [−0,029833; +0,002459] | Hayır |
| A1P1 − B0_like_B2 | −0,000370 | [−0,011528; +0,010018] | Hayır |
| **A1P1 − B2** | **+0,019995** | **[+0,003321; +0,036445]** | **Evet** |

**Sonuç:** B1 ile A1P1 arasındaki fark bu veri ve bu ölçüt altında
istatistiksel olarak ayırt edilemez. Raporda "lojistik regresyon grafik
sinir ağını geçti" **denmemelidir.** Doğru ifade: *grafik tabanlı
mimariler kimyasal doğrusal modele göre ölçülebilir bir üstünlük
gösterememiş, fark belirsizlik aralığı içinde kalmıştır.* Ayırt
edilebilen tek fark, bütün grafik kollarının **B2'den** daha iyi
olmasıdır.

## 1.2 Asıl soru: neden hiçbir model sıklığı geçemedi?

Öğrenme içermeyen sıklık referansı B0 = 0,6466; A1P1 = 0,6462;
B1 = 0,6556. Yani soru "GNN neden LR'yi geçemedi" değil, **"neden hiçbir
model yaygınlık referansını geçemedi"** olmalıdır.

## 1.3 Doğrulanmış açıklama: iki sıralama yönü

`reports/WP14_GIG1A_RESULTS.md` §5b (primary · paired54):

| Model | Terim yönü (sınıf-makro AP) | İlaç yönü (ilaç-makro AP) |
|---|---:|---:|
| B2 | **0,3489** | 0,6262 |
| GiG-1a | 0,3205 | 0,6427 |
| A1P1 | 0,3173 | 0,6462 |
| B1 | 0,3152 | 0,6556 |
| **B0 (sıklık)** | **0,2382** | 0,6466 |

- **Terim yönünde** (sabit PT için ilaçları sırala): öğrenme içeren bütün
  modeller sıklığı yaklaşık %33 bağıl farkla aşar.
- **İlaç yönünde** (sabit ilaç için PT'leri sırala — **birincil ölçüt**):
  hiçbiri aşamaz.

Sınıf başına pozitif yoğunluğunun bütün bantlarında A1P1 sıklığı aşar;
tek pozitifli 59 sınıfta bile (0,0751 / 0,0310) ve 306 sınıfın 278'inde.

> **Darboğaz, bir ilacın terim sıralamasında kayıt yaygınlığının baskın
> olmasıdır** — kodlayıcı zenginliği veya başlık kapasitesi değil.

## 1.4 On olası açıklamanın kanıt düzeyine göre ayrımı

| # | Açıklama | Durum | Dayanak |
|---|---|---|---|
| 1 | İlaç sayısının sınırlılığı (62 kohort / 48 fit) | **Desteklenen** | Bütün farkların GA'sı geniş; ±0,03 mertebesi |
| 2 | Karmaşıklığa göre örnek yetersizliği | **Desteklenen** | Parametrelerin %86,8'i başlıkta (K=240 için 36.240 / 41.752) |
| 3 | Aşırı öğrenme | **Desteklenmiyor** | Sınıf yönünde seyrek sınıflarda bile sıklığı aşıyor (§1.3) |
| 4 | Etiket seyrekliği ve bilinmeyen belirsizliği | **Desteklenen** | 13.964 çiftin 10.144'ü bilinmeyen |
| 5 | Moleküler graf sinyalinin sınırlılığı | **Kısmen** | Atom marjinali +0,002894, stres alt sınırı +0,000006 |
| 6 | PPI'nin ek bilgi vermemesi | **Desteklenen** | real−noPPI = −0,000142; real−shuffled = −0,000379 |
| 7 | Kimyasal tanımlayıcıların yeterliliği | **Desteklenen** | Altı alanlı B1, 234 alanlı B2'yi geçiyor |
| 8 | Rol özetleri / füzyonda bilgi kaybı | **Hipotez** | GiG-1a ile sınandı; ek katkı yok (−0,003536) |
| 9 | Hedef/düzenlileştirme/hiperparametre | **Hipotez** | C ızgarası {0,1; 1; 10}; ablation yok |
| 10 | **Değerlendirme protokolü ve ölçüt yönü** | **Doğrulandı** | §1.3 — en güçlü açıklama |

**Kaçınılacak varsayım:** Daha fazla parametreli modelin daha başarılı
olması gerekmez. Bu çalışmada tersi gözlenmiştir (B2 > parametre, < AP).

---

# ÇIKTI 2 — Ağaç tabanlı modeller ve ANN fizibilitesi

## 2.1 Bağlam

WP08 kapanışında şunlar `DEFERRED_OUTSIDE_PHASE1` olarak kayıtlıdır:
**ATC varyantı, Random Forest, kimya MLP, protein-mean MLP.** Boşluk
projenin kendi kaydında açıktır.

Ortam uygun: scikit-learn 1.9.0 (RF, ExtraTrees, HistGradientBoosting),
ayrıca xgboost ve lightgbm **kurulu** — yeni indirme gerekmez.

Ölçek: bağlam başına ~240 hedef × 48 eğitim ilacı; B1 özellik uzayı
5 kimyasal tanımlayıcı + 1 maske.

## 2.2 Karşılaştırma

| Yöntem | Giriş | Veriye uygunluk | Aşırı öğrenme riski | Beklenen katkı | Maliyet | Açıklanabilirlik |
|---|---|---|---|---|---|---|
| **Random Forest** | B1 (6 alan) | 48×6, out-of-bag ile dengeli | **Düşük** (torbalama) | Doğrusal olmayan etkileşim — **hiç sınanmadı** | Düşük | Özellik önemi; SHAP ağaç açıklayıcısı |
| **HistGradientBoosting** | B1 (6 alan) | Küçük örnekte erken durdurma gerekli | Orta | RF ile farklı önyargı | Düşük | Aynı |
| ExtraTrees | B1 | RF'ye çok yakın | Düşük | **Yeni bilgi az** | Düşük | Aynı |
| XGBoost / LightGBM | B1 | 48 örnekte ayar hassas | **Yüksek** (ızgara büyür) | HGB ile örtüşür | Orta | Aynı |
| Küçük MLP (kimya) | B1 | 48 örnek için sınırda | Yüksek | **A1P1 zaten doğrusal olmayan kimya kolu içeriyor** | Düşük | Zayıf |
| MLP (kimya+protein) | B2 (234 alan) | 48 örnekte 234 alan — elverişsiz | **Çok yüksek** | B2 zaten en düşük AP | Orta | Zayıf |

## 2.3 Değerlendirme

**Ağaç modelleri gerçekten yeni bir hipotez sınıfı sınar.** Şu ana kadar
denenen her şey ya doğrusaldır (B0/B1/B2) ya da graf tabanlı doğrusal
olmayan temsildir (WP09/WP10/WP14). **Eksen hizalı bölmelerle kurulan
özellik etkileşimleri hiç sınanmamıştır.** RF bu boşluğu doğrudan
kapatır ve küçük örneklemde düşük varyanslıdır.

**ANN önerilmemektedir.** A1P1 zaten doğrusal olmayan, yüksek kapasiteli
koldur; 48 ilaçta ayrı bir MLP'nin marjinal bilgi değeri düşük,
aşırı öğrenme riski yüksektir.

**Bu modeller A1P1'in yerine geçmez;** güçlü tabular karşılaştırma
modelleri olarak konumlandırılmalıdır.

**Sonuç odaklı model aramasına dönüşme riski gerçektir.** Bu nedenle
ızgara önceden ve dar tutulmalı, seçim yalnız iç katlarda yapılmalıdır.

## 2.4 Beklenti

§1.3 gereği birincil ölçüt yaygınlıkla doygundur; **ağaç modellerinin
ilaç-makro AP'yi anlamlı biçimde değiştirmesi beklenmemektedir.** Asıl
bilgi değeri terim yönünde ve "doğrusal olmayanlık da denendi"
ifadesinin kanıtlanmasındadır.

---

# ÇIKTI 3 — Ek deney önerisi

> ## **B — Sınırlı ek deney öneriliyor**

**İki kol:** `T1 = RandomForest` ve `T2 = HistGradientBoosting`,
**yalnız B1 özellik setinde**, dondurulmuş protokolde.

**Gerekçe:**
1. WP08'de belgelenmiş `DEFERRED` boşluğunu kapatır.
2. Hiç sınanmamış bir hipotez sınıfını (eksen hizalı etkileşim) sınar.
3. Ek bağımlılık ve ek veri gerektirmez; maliyet düşüktür.
4. Sonucu ne olursa olsun tezde savunulabilir bir cümle üretir.

**Gerekçelendirilmeyen:** ANN kolları, B2 tabanlı ağaçlar, XGBoost/
LightGBM (HGB ile örtüşür), geniş hiperparametre araması.

## 3.1 Önceden kaydedilecek protokol

| Öğe | Karar |
|---|---|
| Kohort | Dondurulmuş 62; birincil karşılaştırma ortak 54 |
| Bölme | Mevcut 5 dış × 3 iç, ilaç-ayrık + stres protokolü |
| Özellikler | B1 ile **birebir aynı**: 5 kimyasal tanımlayıcı + kimya maskesi |
| Hedef sözlüğü | Train-only, mevcut `fittable_train_B2_PT` |
| Dönüşüm | Train-only; B1'in dondurulmuş ölçekleyicisi |
| Çok etiketli kurulum | PT başına bağımsız sınıflandırıcı (B1 ile aynı) |
| **Izgara (dar, önceden sabit)** | RF: `n_estimators=300`, `max_depth ∈ {3, None}`, `min_samples_leaf ∈ {1, 3}` → **4 aday**. HGB: `max_depth ∈ {2, 3}`, `learning_rate=0.1`, `max_iter=200`, `early_stopping=True` → **2 aday** |
| Seçim | **Yalnız iç kat** drug-macro AP |
| Seed | 20261106 formülü |
| Birincil ölçüt | Ortak 54, drug-macro observed-record AP |
| İkincil | Micro AP, micro AUROC, **sınıf-makro AP** (iki yön için) |
| Belirsizlik | 1.000 tekrar grup bootstrap, aynı tohum |
| Durdurma | Izgara dışına çıkılmaz; dış test skoruna bakarak ayar yapılmaz |
| Kabul | Yeni model **otomatik olarak** ana model olmaz; §1.1'deki ayırt edilebilirlik ölçütü uygulanır |

Çıktı ad alanı: `reports/qa/WP15/tree_v1/`, `models/WP15_tree_v1/`.
Mevcut hiçbir model yeniden eğitilmez.

---

# ÇIKTI 4 — Yeni raporun ana planı

## 4.1 Mevcut rapordaki yapısal problemler

| Problem | Açıklama |
|---|---|
| Ek yükü | Ek A (bölüm–kanıt dizini), Ek B (yeniden inceleme), Ek C (deney kayıtları) ana metnin ~%20'si |
| Kanıt dizinleri gövdede | Dosya yolları, hash/manifest adları akademik akışı kesiyor |
| İş paketi adlandırması | WP03/WP08/WP09/WP10 kodları gövdede geçiyor; okuyucu için anlamsız |
| Şablon uyumsuzluğu | Zorunlu dört etki başlığı (çevresel/toplumsal/ekonomik/etik) ayrı alt başlık değil |
| Numaralandırma | Şekil/çizelge sürekli numaralı; şablon **bölüm bazlı** ister (Şekil 2.1) |

## 4.2 EMT1'den örnek alınacak yönler

Bölüm akışı ve denge; sistem analizi başlıklarının ayrı ayrı işlenmesi;
kuramsal temelin uygulamadan önce kurulması; ÖZET/SUMMARY ikilisi;
numaralı `[n]` atıf düzeni; çizelge adlarının bölüm bazlı numaralanması.

## 4.3 Resmî şablonun zorunlu kıldıkları

`EMT-Sablon_v2025_v3 (4).docx` çözümlemesi:

**Stiller:** `BASLIK1`–`BASLIK5`, gövde `GOVDE`, şekil/çizelge
açıklamaları bölüm bazlı stiller (`Sekil_FBE_Sablon_BolumIII`,
`Cizelge_FBE_Sablon_BolumV` …).

**Zorunlu ön bölümler:** ÖNSÖZ · İÇİNDEKİLER · ÇİZELGE LİSTESİ ·
ŞEKİL LİSTESİ · ÖZET · SUMMARY

**Tasarım projesinde zorunlu başlıklar:** Sistem Tanımı · Sistemin
Paydaşları · Sistem Gereksinimleri · Tasarıma Yön Veren Kısıtlar ·
Tasarımın İlişkili Olduğu Mesleki Standartlar

**SONUÇ VE ÖNERİLER altında zorunlu dört alt başlık:** Çözüm Önerisinin
Çevresel / Toplumsal / Ekonomik Etkilerinin İncelenmesi · Çözüm
Önerisinin Etik Boyutunun İncelenmesi

**Zorunlu arka bölümler:** KAYNAKLAR · EKLER · ÖZGEÇMİŞ

**Biçim kuralları:** Şekil/çizelge bölüm bazlı numaralanır (Şekil 2.1);
eklerde harfle (Çizelge A.1); çizelge adı **nokta ile biter**; şekil ve
çizelgeler ilk anıldıkları yerden hemen sonra, ortalı; atıf ya numaralı
`[1]`, `[1-3]`, `[1,3]` ya da yazar-soyadı düzeni — **biri seçilir**.
Mevcut rapor numaralı düzeni kullanıyor; korunacak.

## 4.4 Önerilen başlık düzeni

| # | Başlık (BASLIK1) | Alt başlıklar (BASLIK2) |
|---|---|---|
| — | ÖNSÖZ / İÇİNDEKİLER / ÇİZELGE LİSTESİ / ŞEKİL LİSTESİ / ÖZET / SUMMARY | — |
| 1 | **GİRİŞ** | 1.1 Problem ve motivasyon · 1.2 Gözlem birimi ve karar birimi · 1.3 Araştırma soruları ve katkı |
| 2 | **SİSTEM ANALİZİ** | 2.1 **Sistem Tanımı** · 2.2 **Sistemin Paydaşları** · 2.3 **Sistem Gereksinimleri** · 2.4 **Tasarıma Yön Veren Kısıtlar** · 2.5 **Tasarımın İlişkili Olduğu Mesleki Standartlar** |
| 3 | **KURAMSAL TEMEL VE LİTERATÜR** | 3.1 Gözlenen kayıt ile advers olay ayrımı · 3.2 Heterojen graf temsilleri · 3.3 Graph-in-Graph ve iç içe graf yaklaşımları · 3.4 Moleküler graf öğrenme · 3.5 Açıklanabilirlik · 3.6 Değerlendirme ölçütleri ve indüktif genelleme |
| 4 | **VERİ VE YÖNTEM** | 4.1 Veri kaynakları ve sürümler · 4.2 Kimlik eşleme ve etiket tanımı · 4.3 Kimyasal yapı kalite kontrolü · 4.4 Moleküler atom-bağ grafı · 4.5 Protein özellikleri ve ilaç–protein rolleri · 4.6 İnsan PPI ağı · 4.7 Heterojen grafın kurulması · 4.8 Eksik veri, maskeleme ve çekimserlik · 4.9 Sızıntıya karşı önlemler · 4.10 Eğitim ve değerlendirme protokolü |
| 5 | **KARŞILAŞTIRILAN MİMARİLER** | 5.1 Referans modeller (B0, B1, B2) · 5.2 Protein-PPI mesaj geçişi · 5.3 Atom ve PPI dallarının faktöriyel tasarımı · 5.4 **Graph-in-Graph mimarisi ve bilgi aktarımı** · 5.5 Ağaç tabanlı karşılaştırma modelleri *(onaylanırsa)* · 5.6 Model karmaşıklığı ve hesaplama maliyeti |
| 6 | **DENEYSEL BULGULAR** | 6.1 Kohort ve kapsam · 6.2 Referans modellerin başarımı · 6.3 PPI topolojisinin katkısı · 6.4 Atom ve PPI faktöriyel sonuçları · 6.5 **Graph-in-Graph sonuçları** · 6.6 **İki sıralama yönü** · 6.7 Ağaç modelleri *(onaylanırsa)* · 6.8 Açıklanabilirlik bulguları · 6.9 Belge temelli açıklama ve dış ilaç örneği · 6.10 Araştırma prototipi |
| 7 | **TARTIŞMA** | 7.1 Bulguların bilimsel yorumu · 7.2 Mimari karmaşıklık ve veri ölçeği · 7.3 Ölçüt yönünün sonuçlara etkisi · 7.4 Kısıtlar · 7.5 Gelecek çalışmalar |
| 8 | **SONUÇ VE ÖNERİLER** | 8.1 Tasarım kararı · 8.2 **Çevresel Etkiler** · 8.3 **Toplumsal Etkiler** · 8.4 **Ekonomik Etkiler** · 8.5 **Etik Boyut** |
| — | KAYNAKLAR · EKLER · ÖZGEÇMİŞ | — |

## 4.5 Graph-in-Graph içeriğinin yerleştirilmesi

**Olgusal düzeltme:** Görevde GiG çalışmasının "Ek C'de" olduğu
belirtilmiştir; **bu doğru değildir.** Mevcut v5 raporunda GiG **§5.14'te,
ana metindedir**; Ek C ise C.1–C.5 (deney büyüklükleri, protokol
toplulaştırma, faktöriyel farklar, model seçimi ve tarihsel etiket
duyarlılığı) içerir. Dolayısıyla "Ek C'den taşıma" gerekmez.

| Mevcut içerik | Yeni konum |
|---|---|
| GiG mimarisinin yapısı, düğüm/kenar türleri, mesajlaşma | **§5.4** |
| A1P1 ile yapısal fark (geç füzyon ↔ bilgi aktarımı) | **§5.4** + §7.2 |
| Eğitim protokolü, hiperparametre, maskeleme | **§4.10** ve §5.4 |
| Sentetik kapı ve izolasyon kanıtı | **§4.9** (kısa) + teknik arşiv (ayrıntı) |
| Sonuç tablosu ve eşleştirilmiş farklar | **§6.5** |
| Dejenerasyon ölçümü (mesaj genliği/yayılımı) | **§6.5** + §7.2 |
| İki yön tablosu (Çizelge 9) | **§6.6** |
| GiG-2'nin neden uygulanmadığı | **§5.4** sonu (tasarım/uygulama ayrımı) |

**Üç durumun ayrımı rapor boyunca korunacak:** (a) uygulanmış ve
doğrulanmış (GiG-1a), (b) değerlendirilmiş fakat uygulanmamış (GiG-2),
(c) yalnız tasarlanmış, eğitilmiş kaydı olmayan (literatürdeki tam GiG
biçimselleştirmesi). Keşifsel deney, önceden planlanmış gibi
gösterilmeyecek.

**Ayrı bir Ek C oluşturulmayacak;** ham kayıtlar teknik arşivde kalacak.

## 4.6 Her başlığın bilimsel içeriği — yazım ilkesi

Kod dosyası anlatımı yerine gerekçe anlatımı. Örnek: "44 atom ve 14 bağ
özelliği kullanılmıştır" yerine bu özelliklerin hangi kimyasal bilgiyi
kodladığı, neden bu ayrımın seçildiği ve mesajlaşmada nasıl işlendiği.
Sonuçlar tabloyla bırakılmayacak; her tablo için ölçülen nicelik,
referansla karşılaştırma, belirsizlik ve bilimsel anlam yazılacak.

---

# ÇIKTI 5 — Ana rapora taşınmayacak teknik içerikler

| İçerik | Nereye |
|---|---|
| Ek A — bölüm–kanıt dizini (tam tablo) | **Teknik arşiv** |
| Ek B — yeniden inceleme günlüğü | **Teknik arşiv** |
| Ek C — C.1–C.5 ham deney kayıtları | **Teknik arşiv**; yalnız C.4 faktöriyel farkları §6.4'e özetlenir |
| SHA-256 / manifest / hash listeleri | **Teknik arşiv** |
| Dosya yolu listeleri (`reports/qa/...`, `EMT2_Teslim_v1/...`) | **Teknik arşiv** |
| Test sayıları ve log adları (ör. "19/19 test, 17.812 s") | **Teknik arşiv**; §4.9'da tek cümlelik özet |
| İş paketi kodları (WP03, WP09 …) gövdede | Kaldırılır; yöntem adıyla anılır |
| Notebook adları ve hücre sayıları | **Teknik arşiv** |
| Durum/kapanış kayıtları (`run_status.md` alıntıları) | **Teknik arşiv** |

**Hiçbiri silinmez.** Teknik arşiv önerisi:
`EMT2_Teknik_Dogrulama_Arsivi/` — mevcut `reports/qa/` ve
`EMT2_Teslim_v1/` içeriğine işaret eden tek bir dizin belgesi + kaynak–
bölüm eşleştirme çizelgesi (ana rapora **konmayacak**).

Şablonun zorunlu tuttuğu **EKLER** bölümü korunacak; içine yalnız
akademik değeri olan ek(ler) konacak (ör. model hiperparametre özeti).

---

# ÇIKTI 6 — Gerekli dosyalar ve eksik materyaller

| Materyal | Durum |
|---|---|
| Resmî şablon | ✅ **Alındı** ve çözümlendi |
| Web arayüzü v5 ekranları | ✅ `reports/figures/WP13/arayuz_v5/` — 7 PNG, 1640×1060 |
| WP14 sonuç şekilleri | ✅ `reports/figures/WP14/04, 05` |
| Mimari ve veri akışı diyagramları | ✅ `reports/figures/WP14/01, 02` (SVG + PNG) |
| **EMT1 final raporu künyesi** | ❌ **Kullanıcıdan isteniyor** — kaynakçaya eklenecekse yayın türü/erişim bilgisi gerekir; uydurulmayacak |
| **Özgeçmiş metinleri** | ❌ Şablon zorunlu kılıyor; güncel metin gerekli |
| **Proje bilgi formu güncelliği** | ⚠️ `EMT2_Teslim_v1/EMT2_PROJE_BILGI_FORMU.docx` var; teyit gerekli |
| Ağaç modeli sonuç şekilleri | ⏳ Deney onaylanırsa üretilecek |
| Kurum logosu / kapak bilgileri | ⚠️ Şablondan devralınacak; ad-soyad ve tarih teyidi gerekir |

---

# Yazım sırası ve kalite kontrolü

**Sıra:** (1) onay → (2) ağaç deneyi *(onaylanırsa)* → (3) teknik arşiv
dizini → (4) Bölüm 4–6 (veri, mimariler, bulgular) → (5) Bölüm 3 ve 7
(literatür, tartışma) → (6) Bölüm 1–2 ve 8 → (7) ön/arka bölümler →
(8) kalite kontrolü.

**Teslim denetimi:** şablon stilleri (`BASLIK1-5`, `GOVDE`) · bölüm
bazlı şekil/çizelge numaraları · çizelge adlarının nokta ile bitmesi ·
her şekil/çizelgeye metin içi atıf · `[n]` atıf tutarlılığı ·
zorunlu dört etki başlığının varlığı · sayısal değerlerin kayıtlı QA
çıktılarıyla birebir eşleşmesi · B1'in konumunun gizlenmemiş olması ·
"gözlenen kayıt ≠ klinik risk" ve "bilinmeyen ≠ doğrulanmış negatif"
ifadelerinin korunması.

---

## Onay beklenen karar

Modelleme değerlendirmesini ve EMT2 final raporunu sıfırdan hazırlama
planını tamamladım. **Önerilen ek deneyleri (T1 RandomForest, T2
HistGradientBoosting) ve ardından yeni raporun yazımını başlatmamı
onaylıyor musunuz?**
