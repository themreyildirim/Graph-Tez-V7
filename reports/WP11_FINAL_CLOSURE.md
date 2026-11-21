# WP11 — Nihai kapanış denetimi

**Tarih:08.11.2026. Durum:PASS — kullanıcı tarafından araştırma kapsamında kabul edilen WP11 kapatıldı. WP12 yalnız hazırlık notudur;uygulama başlamadı.**

Esas belgeler AGENTS,aktif ROADMAP,SOURCE_USAGE_AUDIT,`reports/WP11.md`, `reports/WP11_GRAPH_EXPLANATIONS.md` ve kabul edilmiş yöntem sözleşmeleridir. Önceki raporlar ve çıktılar değiştirilmedi. İlk aşama raporundaki “graf yalnız öneri”,sonraki graf raporundaki “nihai kapanış yapılmadı” ifadeleri kendi tarihsel aşamalarını anlatır; bugünkü kapanış ayrı belgelenir. Yeni model eğitimi,optimizer,backward,yeni attribution yöntemi,hiperparametre araması veya başarıya göre sonuç/örnek seçimi yoktur.

## 1. Kayıtlı model,kaynak ve QA bütünlüğü

Görev başlangıcındaki **3.139 kabul edilmiş dosyanın SHA-256 değeri** değişmeden doğrulandı. Buna B1 SHAP,graf attribution,önceki model/metadata,split/feature/QC,rapor/notebook/görsel ve önceki QA manifestleri dahildir. B1 ve graf aşamasının input,policy commit,prior-artifact ve final-artifact olmak üzere8 manifesti kontrol edildi. Mutable `run_status.md` için aşamaya ait arşiv doğru kaynak olarak kullanıldı;uyuşmazlık gizlemek için eski manifest değiştirilmedi.

Model ağırlık dosyasının hash'i kendi metadata kaydıyla eşleştirildi;numeric array'ların sonluluğu denetlendi. WP09/WP10'da kaydedilmiş numeric state digest'i de tekrar hesaplandı. Toplam742 NPZ ve742 metadata dosyası:

| model_group | NPZ_metadata_çifti |
| --- | --- |
| WP08_baseline_v1 | 400 |
| WP09_PPI_v3_training_v1 | 190 |
| WP10_factorial_training_v1 | 152 |

İşlenmiş/modelde kullanılan kaynaklar,NPZ train/query bundle'ları,kimlik köprüleri,özellikler,kilitli sözlükler ve kaynak manifestleri kontrol edildi. Büyük ham DrugBank XML/STRING dosyaları bu kapanışta tekrar okunmadı veya yeniden hash'lenmedi;ham kaynak baytlarının bugün yeniden tarandığı iddia edilmez. Önceki provenans kayıtları korunur. Kapsam dışı klinik veri dizinleri açılmadı.

## 2. İki açıklama yöntemi ayrı kalır

| Yöntem | Açıklanan çıktı ve referans | Kapsam/toplamsallık sınırı |
| --- | --- | --- |
| B1 exact interventional linear SHAP | Kayıtlı LR logiti;yalnız o modelin uygun train ilaçları background. Beş kimya alanı ve availability maskesi ayrı | Seçilen interventional oyunda base+Σφ=logit. Korelasyona koşullayan veya nedensel açıklama değildir.54 uygun ilaç/protokol;8 abstention için sahte katkı yok |
| A1P1 tekil mesaj maskesi | Δz=orijinal−müdahale logiti. Orijinal degree/rol paydası ve maskeler sabit;PPI çiftinin iki yönü birlikte | SHAP/Shapley değildir. Source protein/rol vePPI yolları ayrı;tekil katkılar ortak biyolojik etki diye toplanmaz |
| A1P1 fiziksel silme duyarlılığı | Aynı Δz ölçeği;ilişki/kenar çıkarılır,kalan payda ve gerekirse rol availability maskesi güncellenir | Sabit-payda maskesiyle aynı müdahale değildir;sonuçlara bakarak “daha iyi yöntem” seçilmedi |

Bütün açıklamalar kendi fold modelinin fit edilmiş PT başlığına bağlıdır. Bulunmayan PT birleştirilmedi veya doldurulmadı. B1'de ek global özet yalnız önceden belirlenen beş-fold ortak PT kesişimidir;graf özetleri native context/PT kapsamındadır. SIDER unknown doğrulanmış biyolojik negatif değildir. İki yöntemin sayıları model davranışını betimler;klinik bireysel yan etki riski,kalibrasyon,nedensellik veya hasta güvenliği kanıtı değildir.

## 3. Test kayıtları ve model çıktısına geri bağlantı

Önceki10 sentetik+16 gerçek-model graf testinin logları/hash'leri korundu. Kapanışta aynı26 test yeni log dosyalarında yeniden geçti. B1'in18 testi de tekrar geçti;toplam44/44. Fit/optimizer/backward için çalışan engeller altında yeniden doğrulama yapıldı;yasak çağrı0. Eski test logları ezilmedi.

| module | passed | seconds | old_log_overwritten |
| --- | --- | --- | --- |
| test_wp11_graph_synthetic | 10 | 0.3124674 | False |
| test_wp11_graph_real | 16 | 12.09088 | False |
| test_wp11_shap | 18 | 10.16646 | False |

On kayıtlı A1P1 dış modeli yüklenerek bütün **35.974 orijinal ilaç–PT logiti** `original_outputs.csv` ile karşılaştırıldı;en büyük fark8,882×10⁻¹⁶. Bu yeni performans hesabı veya model seçimi değildir. Önceki testler OOF sigmoid skorlarını da dondurulmuş toleransta doğruladı.

Katkı değerlerini görmeden,kimlik sırasına göre her bağlamda her rolün ilk mevcut ilişkisi veilk mevcut query–PPI çifti seçildi;aynı50 anahtar iki yöntemde kontrol edildi. **100 mevcut müdahalenin29.560 PT kaydı** kayıtlı modelden yeniden hesaplandı. Kaydedilmiş müdahale logiti/Δz ile en büyük fark1,649×10⁻⁷;önceden kabul edilmiş10⁻⁵ logit toleransının altındadır. Model,orijinal graph/query/cache digest'leri değişmedi. Bütün2.440.976 müdahale çıktısının forward'ı yeniden çalıştırılmış gibi sunulmaz;tam dosya taraması aşağıdaki kaynak/cebir/tekillik denetimidir.

## 4. Tam katkı CSV denetimi ve kaynak kimlikleri

Sıkıştırılmış CSV'ler50.000 satırlık parçalarla okundu. Her kaydın orijinal logiti kayıtlı referans tabloya bağlandı;`orijinal−müdahale=Δz` kimliği kontrol edildi. Her source drug–protein–rol WP05 kaynak tablosuyla;her PPI endpoint/çift WP06 strict aynı-taxID insan STRING700 kaynağıyla eşleşti. Her query–PPI çiftinin tek katmanda readout'a ulaşan gerçek bir hesap yolu olduğu doğrulandı. K12/MG1655/context80 eklenmedi.

Her bir **8.358 context–ilaç–ilişki–yöntem anahtarında** native fit-CUI sözlüğü tam ve tekildir;duplicate veya eksik/fold dışı CUI yoktur. Her müdahalenin signed/mutlak ortalama,maksimum ve sıfıra yakın sayısı tam CSV'den tekrar türetilip mevcut `intervention_summary.csv` ile karşılaştırıldı;en büyük özet farkı1,980×10⁻⁷'dir. Kaydedilmiş özetler yeniden yazılmadı.

| kind | rows | original_logit_CSV_consistency_max_error | delta_identity_max_error | exact_zero | near_zero_including_exact | NA_measurement_rows | all_source_keys_valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| role | 557574 | 2.330933e-07 | 4.69e-07 | 0 | 0 | 0 | True |
| ppi | 1883402 | 2.330933e-07 | 4.7e-07 | 48 | 56 | 0 | True |

CSV round-trip farkları float32/decimal yazım sınırındadır:orijinal logit karşılaştırmasında2,331×10⁻⁷,Δz cebirinde4,700×10⁻⁷. Bunlar veri/kimlik değişikliği değildir ve önceden kabul edilmiş toleransın içindedir.

## 5. NA ile gerçek sıfır katkı korunur

Her protokolde62 envanter/61 skor/60 protein rolü/51 query-PPI yolu aynen kalır. Methenamine abstention,Tobramycin protein eksikliği,54/8 yapıQC;62/1061/6416 kaynak kapsamı değişmez. Fit edilmeyen C0027497 başlığı primary outer3 ve stres outer5 için NA kalır. Ana paired54'te1.685 kapsam dışı kaynak pozitif sınırlaması devam eder.

Eksik rol,PPI yolu olmayan protein veya unseen/self-only protein için NA kayıtları doğrudan kaynak NPZ kimliklerinden yeniden türetildi;önceki NA tablolarıyla tam eşleşti:

| absent_role_PPI_rows | protein_path_rows | source_ID_and_path_consistency | no_zero_filling |
| --- | --- | --- | --- |
| 208 | 952 | PASS | True |

Ölçülmüş sonlu katkı tablolarında NA satırı0 olması eksik yol olmadığı anlamına gelmez:eksik yollar ayrı NA dosyalarında tutulur. Mevcut,uygulanabilir PPI kenarlarında **48 tam sıfır** ve bunlar dahil **56 adet |Δz|≤10⁻⁷** kaydı aynen korundu. Bunlara eksik yol eklenmedi. Erythromycin'de olmayan carrier veya incident PPI yolu,sıfır katkı diye uydurulmadı.

## 6. Notebook,gerçek ağ vealtı görsel aynı veriye bağlı

İki kabul edilmiş notebook şeması,çalıştırılmış hücreleri ve hata çıktısı yokluğu kontrol edildi:B1'de8,graf notebook'unda9 kod hücresi;graf notebook'unda6 gömülü PNG vardır. Gerçek ağ JSON'undaki her düğüm/typed rol/PPI kimliği,source bundle ve tam katkı CSV'siyle karşılaştırıldı;örnek CSV'nin aynı değerleri taşıdığı doğrulandı:

| context | drug_id | class_id | protein_nodes | role_edges | PPI_edges | JSON_full_CSV_example_CSV_max_error | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary_o01_final | DB00254 | C0000731 | 33 | 4 | 35 | 1.552124e-08 | PASS |
| primary_o03_final | DB00199 | C0000731 | 33 | 11 | 85 | 1.252899e-08 | PASS |

Doxycycline çizimi4 rol/35 PPI,Erythromycin çizimi11 rol/85 PPI kenarı taşır;ikisi de33 protein düğümü içerir. Bu sayılar keyfi en büyük katkı seçimi değil,önceden belirlenmiş ilaçların gerçek hesap yollarıdır.

Kabul edilmiş graf notebook'unun mevcut veri/çizim kodu,bütün dosya yazımları yeni kapanış QA alanına yönlendirilerek tekrar çalıştırıldı. **Altı PNG'nin tamamı ve notebook'un altı gömülü görüntüsü piksel düzeyinde aynıdır**;yeniden çizilen PNG SHA-256 değerleri de orijinalleriyle eşleşir. Orijinal notebook veya şekiller yazılmadı. Böylece yalnız görsel dosyasının varlığı değil,saklanan gerçek verilerden aynı görüntünün üretildiği gösterildi.

| figure | differing_pixels | embedded_differing_pixels |
| --- | --- | --- |
| 01_real_path_coverage.png | 0 | 0 |
| 02_Doxycycline_real_network.png | 0 | 0 |
| 03_Erythromycin_real_network.png | 0 | 0 |
| 04_real_delta_distributions.png | 0 | 0 |
| 05_mask_vs_deletion.png | 0 | 0 |
| 06_numeric_stability.png | 0 | 0 |

## 7. Kabul edilmiş performans sonuçları değişmedi

Bu değerler mevcut metric CSV'lerinden okunan sabit referanslardır;yeniden eğitim,evaluation,CI veya sonuç seçimi yapılmadı:

| WP | model | accepted_drug_macro_AP |
| --- | --- | --- |
| WP09 | G_noPPI | 0.6430212 |
| WP09 | G_realPPI | 0.6428796 |
| WP09 | G_shuffledPPI_mean3_metrics | 0.643259 |
| WP10 | A0P0 | 0.6427402 |
| WP10 | A0P1 | 0.6436359 |
| WP10 | A1P0 | 0.6459295 |
| WP10 | A1P1 | 0.6462343 |

PPI gerçekten hesaplanıyor/öğreniliyor teknik sonucu korunur;ek birincil performans katkısı gösterildiği söylenmez. Protein biyolojisinin genel yararsızlığı çıkarılamaz. WP10 atom dalının küçük koşullu katkısı,PPI üstünlüğünün veB0/B1 üstünlüğünün gösterilememesi değişmedi. B1–GNN farkı tek başına PPI topolojisine bağlanamaz. Açıklama sayılarının varlığı veya büyüklüğü bu sonuçları tersine çevirmez. KoşulluCI'lar dış doğrulama/genel üstünlük kanıtı değildir.

## 8. Kanıtlar,teknik geçmiş ve durma koşulu

Yeni kanıt dizini `reports/qa/WP11/final_closure_v1/`dir. `prior_artifacts_sha256.json`,manifest/model denetim CSV'leri,tam müdahale-anahtar denetimi,source NA kontrolü,yeni test logları,replay kayıtları,network/image tutarlılığı ve yönlendirilmiş görsel kopyaları bulunur. `closure_checks.json` nihai denetim sonucunu;`evidence_manifest.json` kapanış kanıtlarının hash'lerini saklar. `notebooks/WP11_final_closure.ipynb` çalıştırılmış Türkçe kapanış incelemesidir.

Önceki graf çalışmasında attribution üretmeden duran hash-yardımcısı tür hatasının traceback'i ve boş kısmi dosyaları eski `attempt_01_technical_failure/` arşivinde aynen korundu. Bu kapanışta başarısız deney kaldırılmadı veya eski protokol yeniden ayarlanmadı. Ham XML/STRING bugün yeniden hash'lenmedi;tam müdahale forward'ı yalnız dondurulmuş100 eski kayıt için tekrarlandı. Bu sınırlar doğrulanmış kapsamın parçasıdır.

`run_status.md` kapanış ilerlemesi için güncellendi;önceki tam baytları QA'da arşivlendi ve güncel dosyanın devamında aynen tutuldu. Diğer kabul edilmiş dosyalar değişmedi. Aktif ROADMAP/AGENTS düzenlenmedi.

WP12'nin yalnız aktif yol haritasındaki kapsamı `reports/WP12_PREPARATION_DECISION.md` içinde incelendi:yalnız kullanıcı seçimi prospektüs PDF'leri,sayfa kaynaklı bilgi çıkarımı,küçük yerel LLM;`reported_in_PDF` ile model tahmin/açıklamasının ayrılması. PDF açılmadı/indirilmedi,parser kurulmadı,Ollama/model indirilmedi veya başlatılmadı. Yeni klinik veri kaynağı eklenmedi.

**Son durum:WP11 kabul edilmiş iki açıklama aşamasıyla nihai olarak kapandı. WP12 uygulamasına geçilmedi. Hazırlık kararları ve kullanıcı onayı beklenerek duruldu.**
