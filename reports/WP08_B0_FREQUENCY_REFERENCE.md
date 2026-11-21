# WP08 — B0_frequency_reference_v1 keşifsel referans eki

Tarih: 06.11.2026. Durum: **B0 eki tamamlandı, kullanıcı incelemesi bekleniyor; WP08 açık, WP09 başlamadı.**

## Bulguların anlamı

Kullanıcının kabul ettiği ilk L2-LR sonuçları korundu: ana ortak kapsamda B1 drug-macro AP **0,6556**, B2 **0,6262**. Protein rol özetleri bu deneyin birincil metriğini artırmadı. B0, bu sonuçlar görüldükten sonra kullanıcı isteğiyle eklendi; **keşifsel, sonuç sonrası bir karşılaştırmadır**. İlk deneyin önceden belirlenmiş referansı olarak sunulamaz.

B1'in aynı train popülasyonundan türetilen B0 drug-AP'si **0,6438**; B1−B0 farkı **+0,0119**, %95 koşullu grup CI **−0,0021–+0,0274**. B1'in frekans referansını belirgin biçimde geçtiği gösterilemiyor. B2'nin eşleşen B0'ı **0,6466**; B2−B0 **−0,0204**, CI **−0,0438–+0,0032**. Ana protokolde B2 için de bir artış yok. Stres protokolünde B2'nin B0'a göre farkı **−0,0469**, CI **−0,0769–−0,0176**; düşük sonuç gizlenmedi. Bunlar çoklu keşifsel karşılaştırmalardır; doğrulayıcı üstünlük/başarısızlık testi veya klinik doğruluk iddiası değildir.

## 1. Dondurulan yöntem ve train popülasyonu

Skor, her PT için **ilgili train'de bu kaydı olan benzersiz ilaç sayısı / tanımlı train ilaç sayısı**. Düzeltme, smoothing, logit veya sonuçla ayarlanan dönüşüm yok. Kimya, protein, PPI, ATC değerleri kullanılmadı. Eligibility dosyasından yalnız ID/model/uygunluk sütunları okundu; bunlar paydanın kimliklerini tanımlar. Etiket frekansları B1/B2 girdilerine eklenmedi.

| Referans | Train paydası | Kullanım |
| --- | --- | --- |
| B0_all_train | Splitteki bütün train ilaçları | Biyolojik girdiden bağımsız nüfus referansı |
| B0_like_B1 | Train ∩ sabit B1 input-eligible kimlikleri | B1 ile aynı kullanılabilir-train popülasyonu |
| B0_like_B2 | Train ∩ sabit B2 input-eligible kimlikleri | B2 ile aynı kullanılabilir-train popülasyonu |

Ana outer-final paydaları:

| outer_fold | B0_all_train | B0_like_B1 | B0_like_B2 |
| --- | --- | --- | --- |
| 1 | 49 | 43 | 48 |
| 2 | 49 | 43 | 48 |
| 3 | 50 | 43 | 50 |
| 4 | 50 | 44 | 49 |
| 5 | 50 | 43 | 49 |

Her iki protokolün toplam **40** inner/outer train bağlamında **120** popülasyon için sıklık ve kaynak train ID'leri saklandı. B0'ın ayarlanacak C değeri yok; inner sonuçlarıyla seçim yapılmadı. Inner sıklıklar yalnız kendi train'inden hesaplandı. B1/B2'nin seçilmiş C değerleri veya modelleri tekrar fit edilmedi.

B0 için biyolojik input gerekmediğinden **62/62** ilaca nüfus sıklığı sıralaması verilebilir. Bu, kişiselleştirilmiş girdi veya klinik olasılık değildir. Methenamine'e de bu açık statüyle referans verildi; B1/B2'nin Methenamine abstention kararı korundu. Eşleştirilmiş analizde eski B1/B2'nin skorladığı ilaç/PT anahtarları aynen kullanıldı; B0 ile LR abstention boşlukları doldurulmadı.

Hedefler mevcut kohort-train PT sözlüğünden alındı; yeni sınıf seçilmedi. Eşleştirilmiş analizde mevcut B1/B2 skor anahtarlarına bire bir join yapıldı. Böylece aynı ilaçlar, aynı outer fold ve aynı PT kapsamı kullanıldı. `own_B1`, `own_B2`, `paired54`, `complete_case53` ayrı saklandı. Complete-case53 aynı fit modellerin değerlendirme alt kümesidir; yeni eğitim değildir. B0_all62 ayrı, eşleştirilmemiş referanstır.

## 2. Birincil drug-macro observed-record AP

Ortak 54 ilaç, aynı hedefler ve aynı değerlendirilebilirlik maskesi:

| protocol | model | estimate | CI95_low | CI95_high |
| --- | --- | --- | --- | --- |
| primary | B1 | 0.6556 | 0.6131 | 0.6920 |
| primary | B2 | 0.6262 | 0.5792 | 0.6701 |
| primary | B0_all_train | 0.6465 | 0.6040 | 0.6852 |
| primary | B0_like_B1 | 0.6438 | 0.6021 | 0.6820 |
| primary | B0_like_B2 | 0.6466 | 0.6044 | 0.6853 |
| stress | B1 | 0.6319 | 0.5700 | 0.6863 |
| stress | B2 | 0.5997 | 0.5341 | 0.6577 |
| stress | B0_all_train | 0.6472 | 0.6050 | 0.6874 |
| stress | B0_like_B1 | 0.6440 | 0.6029 | 0.6844 |
| stress | B0_like_B2 | 0.6466 | 0.6045 | 0.6871 |

Eşleştirilmiş farklar, aynı grup bootstrap ağırlıkları:

| protocol | first | reference | first_minus_reference | CI95_low | CI95_high |
| --- | --- | --- | --- | --- | --- |
| primary | B1 | B0_like_B1 | 0.0119 | -0.0021 | 0.0274 |
| primary | B1 | B0_all_train | 0.0091 | -0.0059 | 0.0255 |
| primary | B2 | B0_like_B2 | -0.0204 | -0.0438 | 0.0032 |
| primary | B2 | B0_all_train | -0.0203 | -0.0444 | 0.0032 |
| primary | B2 | B1 | -0.0294 | -0.0511 | -0.0093 |
| stress | B1 | B0_like_B1 | -0.0121 | -0.0412 | 0.0111 |
| stress | B1 | B0_all_train | -0.0153 | -0.0456 | 0.0094 |
| stress | B2 | B0_like_B2 | -0.0469 | -0.0769 | -0.0176 |
| stress | B2 | B0_all_train | -0.0475 | -0.0781 | -0.0176 |
| stress | B2 | B1 | -0.0322 | -0.0569 | -0.0096 |

Sıklık referansının B1'e yakın AP'ye ulaşması, sık gözlenen PT kayıtlarının güçlü bir sıralama başlangıcı oluşturduğunu gösteriyor. **B1 AP'sinin yüzde kaçının frekans tarafından açıklandığı hesaplanamaz**: AP doğrusal bir açıklanan varyans ölçüsü değildir; B0/B1 oranı nedensel katkı yüzdesi vermez. Gözlenebilen ek değer, aynı örneklerdeki +0,0119 AP farkıdır ve belirsizlik aralığı sıfırı içerir. B0 başarısı da raporlama sıklığı/etiket yoğunluğu dahil kaynak kayıt mekanizmasını yansıtabilir.

AP, sıralama eşiklerinde hesaplanan average precision'dır; trapez PR-AUC ile değiştirilmedi. Unknown çiftler doğrulanmış negatif değildir. Buradaki binary proxy, gözlenen kaynak kaydını etiketsiz kaynak çiftlerinden ayıran sıralamayı ölçer. Klinik risk, kalibrasyon, özgüllük veya gerçek biyolojik negatif tanıma başarısı iddiası yoktur.

## 3. İkincil metrikler ve B2'nin AUROC yorumu

Ana ortak kapsam, eski B1/B2 değerleri değiştirilmeden:

| model | drug_macro_AP | micro_AP | class_macro_AP | micro_AUROC | class_macro_AUROC |
| --- | --- | --- | --- | --- | --- |
| B0_all_train | 0.6465 | 0.5856 | 0.2400 | 0.7501 | 0.3289 |
| B0_like_B1 | 0.6438 | 0.5804 | 0.2389 | 0.7482 | 0.3188 |
| B0_like_B2 | 0.6466 | 0.5867 | 0.2382 | 0.7502 | 0.3281 |
| B1 | 0.6556 | 0.5422 | 0.3152 | 0.7269 | 0.4814 |
| B2 | 0.6262 | 0.5323 | 0.3489 | 0.7145 | 0.5431 |

Drug-AP aynı ilaç içinde PT'leri sıralar; class-AUROC aynı PT için ilaçları sıralar. Dolayısıyla B2'nin drug-AP'si azalırken pooled class-AUROC'unun 0,4814'ten 0,5431'e yükselmesi farklı bir sıralama yönünü ifade eder; genel veya klinik üstünlük değildir.

**OOF birleştirme sınırı:** B0 aynı fold/PT için bütün test ilaçlarına aynı skoru verir. Pozitif ve unknown birlikte bulunan fold/PT'de AUROC tam **0,5** olur. Farklı foldların frekans skorlarını tek sütunda birleştirince B0 pooled class-AUROC'u yaklaşık 0,32 çıkabilir. Sabit PT için train frekansı `(toplam pozitif − ilgili test pozitif)/(toplam ilaç − ilgili test ilaç)` ilişkisine sahiptir; tamamlayıcı train/test frekansları, folda göre değişen hedef kapsamı ve skor ölçekleri birleşik metriği etkiler. Bu test etiketini skora katmak değildir; yalnız pooled yorumun sınırıdır. B0'ın biyolojik olarak ters tahmin yaptığı sonucuna gidilmez. Eski LR pooled AUROC değerleri de doğrudan tek bir ortak skor ölçeğindeki ayrım gücü olarak aşırı yorumlanmamalıdır.

Bu nedenle ek, **yalnız betimleyici** fold içi class-AUROC ortalamasını da gösterir:

| protocol | model | descriptive_mean_of_5_fold_class_AUROC |
| --- | --- | --- |
| primary | B0_all_train | 0.5000 |
| primary | B0_like_B1 | 0.5000 |
| primary | B0_like_B2 | 0.5000 |
| primary | B1 | 0.5513 |
| primary | B2 | 0.5716 |
| stress | B0_all_train | 0.5000 |
| stress | B0_like_B1 | 0.5000 |
| stress | B0_like_B2 | 0.5000 |
| stress | B1 | 0.5722 |
| stress | B2 | 0.5625 |

Ana protokolde B1 0,5513, B2 0,5716 iken stres protokolünde sıralama tersine döner. Beş fold bağımsız tekrar sayılmadı; bu ortalamalara t-CI veya üstünlük testi uygulanmadı. Sonuç sonrası tanısal ek, kilitli birincil metrik/hiperparametre seçimini değiştirmiyor.

## 4. Kapsam, değişen sözlükler ve 1.685 pozitif

| scope | scored_drugs | drug_AP_evaluable | observed_positive_scored | unknown_scored_NOT_verified_negative | out_of_scored_vocab_positive |
| --- | --- | --- | --- | --- | --- |
| own_B1 | 54 | 54 | 3820 | 10144 | 1685 |
| own_B2 | 61 | 61 | 4576 | 13428 | 1829 |
| paired54 | 54 | 54 | 3820 | 10144 | 1685 |
| complete_case53 | 53 | 53 | 3730 | 9964 | 1617 |
| B0_all62_reference_ONLY | 62 | 62 | 4596 | 13738 | 1820 |

Ana ortak54 için **13964** skorlanan çift: **3820** gözlenen pozitif, **10144** unknown. Aynı ilaçlardaki **5505** kaynak pozitifin **1685** tanesi folda özgü skorlanan sözlük/fit kapsamı dışında. Bunlar otomatik yanlış negatif veya negatif etiket değildir. 1685 bütün 62 ilaçtaki eksik kayıt sayısı olarak sunulamaz. B0_all62 referansının farklı kapsamındaki dış pozitif sayısı da ayrı tabloda verilir.

Train desteği nedeniyle fold sözlükleri farklıdır; pooled union ortak54'te 306 CUI, class metriği hesaplanabilen 256, NA olan 50 CUI vardır. Başka foldda hedef olması ilgili test foldunda hedef olduğu anlamına gelmez. Pozitif veya unknown desteği bulunmayan ilaç/sınıf metrikleri NA kaldı; başarı sıfırı veya fallback olasılığı yapılmadı. Fold bazlı kapsam ve her sınıfın destek/NA durumları CSV'lerde tutuldu. Bu seçilmiş, değişken hedef uzayındaki AP/AUROC değerleri bütün kaynak PT uzayında performans iddiasını desteklemez. Tarihsel 30 kategori deneyi eski semantik uyarılarıyla ayrı tutuldu; B0 hedefi olarak yeniden tanımlanmadı ve PT ile tek skora birleştirilmedi.

## 5. Belirsizlik ve sızıntı kontrolleri

Ana protokolde 61 connectivity, streste 40 yapı grubu biriminden **1000** bootstrap çekimi kullanıldı; aynı çekimdeki grup üyeleri ve modeller birlikte ağırlıklandırıldı. Levofloxacin/Ofloxacin ayrılmadı. Foldlar veya ilaç–PT çiftleri bağımsız gözlem sayılmadı. Aralıklar sabit OOF modellerine ve sabit train frekanslarına **koşulludur**; bütün nested CV yeniden eğitimi, kaynak yanlılığı ve dış kohort belirsizliğini kapsamaz. Aggregate CI'larda 1000 geçerli çekim var; tekil NA kapsamı ayrı dosyalardadır. Train grupları tekrar örneklenerek frekanslar yeniden tahmin edilmedi; bu yüzden koşulsuz eğitim belirsizliği iddiası yoktur.

**19/19 test geçti (7.268 saniye).** Testler 120 train popülasyonunu ve frekans pay/paydasını bağımsız hesaplar; heldout etiket mutasyonu ve heldout tekrarlarının skoru değiştirmediğini doğrular. Kimyasal/protein sütunları estimator tarafından reddedilir. Dondurulan hedefler, eski skor anahtarları, B1/B2 metrikleri, eşit-skor AUROC=0,5, bootstrap tekrarlanabilirliği, Methenamine statüsü ve notebook çıktıları sınanır. B1/B2 kodu fit amacıyla çalıştırılmadı; WP07 grafı veya yeni eğitim grafı üretilmedi. B0 sonuçları model girdisine dönüştürülmedi.

Koruma kontrolü **1331 önceki dosya** için SHA-256 eşitliğini doğruladı. Dokuz B0 girdi dosyasının hash'i ayrıca kayıtlı; modeller, seçilmiş C, split, hedefler ve QA değişmedi. Seed **20261106**; bootstrap seed politikası ilk deneydekiyle aynı. B0 policy hash: `3a3b9139f2175b53e54aa818eeb5fcd8f315499c3eb6f83fd51956046dbd06ab`.

| Kilit | SHA-256 |
| --- | --- |
| split_lock_v1.json | `cda71983763b8e1cbbca055400f6cb4ed4692cbbec016abf36a101337335faea` |
| outer_membership_v1.csv | `079557dc2b9e27ecd1064cf78a130de6f988865f0964d548709ab299cdd51e89` |
| nested_partitions_v1.csv | `33528de50c4420be89713a8e648debb06177d3ddafe897955075df8a41a234e5` |
| B1/B2 OOF skor dosyası | `e4b8be02329ce0f6b5cb78083a6426cde12336fe7979718951f293a12cff77aa` |
| B1/B2 selected_C.csv | `5e20e8df3aa05d2a74cf67eb3abae565fe13fd6ad339eefebe6800ac431ff2c6` |

## 6. Öğretici çıktılar ve yeniden üretim

- [Çalıştırılmış notebook](../notebooks/WP08_B0_frequency_reference_v1.ipynb): yedi kod hücresinin altında gerçek tablolar/grafikler ve Türkçe yorumlar.
- `reports/qa/WP08/B0_frequency_reference_v1/`: policy, girdi/koruma hash'leri, train ID/payda listeleri, sıklıklar, aynı anahtarlarla skorlar, fold/sınıf/ilaç metrikleri, CI farkları, destek ve test logu. `artifact_validation.json` son doğrulamayı saklar.
- `reports/figures/WP08/B0_frequency_reference_v1/01_…png`: train paydalarının farklılığını açıklar.
- `02_…png`: aynı 54 ilaçta ana/stres AP ve koşullu CI; frekansın güçlü referans olduğunu gösterir.
- `03_…png`: eşleştirilmiş AP farkı; bağımsız iki CI'ı gözle karşılaştırmak yerine aynı grup çekimleri kullanılır.
- `04_…png`: pooled ve fold içi class-AUROC ayrımı; tezde AUROC yorumunun kapsamını öğretir.
- `05_…png`: gözlenen pozitif/unknown ve kapsam dışı pozitifler; bütün PT uzayına genelleme sınırını gösterir.
- `per_drug_frequency_reference_interactive.html`: ilaç bazında B1/B2−eşleşen B0 AP farkını kaynak ID'leriyle inceler. Plotly betiği gömülüdür. Beş PNG görsel olarak incelendi; HTML için canlı tarayıcı etkileşim testi yapılmadı.

Kodlar ayrı `scripts/wp08_b0_frequency.py`, `wp08_b0_evaluate.py`, `wp08_b0_summary.py`, `wp08_b0_notebook.py`, `wp08_b0_report.py`; test `tests/test_wp08_b0.py`. Kaynak sayısal girdileri okumadan mevcut küçük QA tablolarıyla çalışır. Ham XML/STRING tekrar taranmadı, API/indirme/kurulum yapılmadı.

Temiz yeni bir çıktı ortamında sıra: frequency → evaluate → summary → notebook → `python -m unittest discover -s tests -p test_wp08_b0.py -v` → report. Mevcut v1 frequency komutu tamamlanma işareti varsa ezmeyi reddeder; sonuç sonrası yeniden tahmin etmeye izin vermez. Notebook yalnız kayıtlı sonuçları okur, eğitim çalıştırmaz. Kod/girdi/hash sınırları saklanır; farklı kütüphane sürümlerinde bit düzeyinde genel yeniden üretim garantisi verilmez.

## 7. Açık kalan WP08 ROADMAP görevleri

| task | status | scope_note |
| --- | --- | --- |
| Drug-disjoint / nested split / train-only scaler | Tamamlandı, v1 kilitli | Bu ekte değişmedi; B0 farklı seed veya split aramadı |
| Observed-record LR ve koşullu grup CI / leakage test | İlk B1/B2 ve keşifsel B0 tamamlandı | Sabit OOF CI tüm tekrar-eğitim belirsizliği değil |
| 5 kimya + ATC baseline varyantı | Yapılmadı; kullanıcı onayı bekler | WP02 kaynak kodları, train-only/sabit hiyerarşi kararı; eski one-hot kullanılmaz |
| RF ve kimya MLP baseline | Yapılmadı; ilk eğitim onayı bunları dışladı | Kapasite/arama planı sonuç görmeden ayrı sürümlenmeli; bu ekte başlatılmadı |
| Protein-mean MLP baseline | Yapılmadı | Mevcut B2 rol özetli LR, MLP veya PPI/GiG değildir |
| Gerçek PU loss / class-prior varsayım deneyi | Ayrı yöntem seçilmedi; mevcut hedef observed-record proxy | WP08 karşılaştırmalı PU öğretimi var; ek PU modeli zorunluymuş gibi otomatik eklenmez |
| Tarihsel V6 metriklerinin bağımsız doğrulanması | Doğrulandı iddiası yok | Bu 62/PT/clean giriş deneyleri eski 38/30/sızıntılı sistemi yeniden doğrulamaz |
| WP08 nihai kapsam/kapanış kararı | Açık; kullanıcı onayı bekleniyor | Yapılmayan roadmap varyantları için yap/ertele/kapsam daralt kararı gerekir |
| PPI encoder gerçek forward ve ablation | WP09 görevi, başlamadı | WP08 eksiğini kapatmak için kendiliğinden WP09a geçilmez |

ATC/RF/MLP seçeneklerinin uygulanması veya gerekçeyle ertelenmesi için kullanıcı kapsam kararı gerekir. B0 eklendi diye B1/B2 yeniden ayarlanmadı. Bu ek WP08'i tamamen kapatmaz. **Kullanıcı onayı bekleniyor; WP09, PPI eğitimi veya sonraki modele geçilmedi.**
