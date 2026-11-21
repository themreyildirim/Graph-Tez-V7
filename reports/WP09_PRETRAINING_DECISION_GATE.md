# WP09 — Eğitim öncesi karar kapısı

06.11.2026. **Tasarım ve encoder doğrulaması tamamlandı; eğitim/performans onayı bekleniyor.** Kullanıcı bu aşamada yalnız tasarım/girdi/encoder testlerini onayladı. Mevcut eğitilmiş B0/B1/B2 referanslarına dokunulmadı.

| karar | öneri | gerekçe_ve_sınır |
| --- | --- | --- |
| PPI primary eşik | 700 önerilir; approved=None | 400/700 outer erişim51/62; null0/40 vs39/40; performans seçimi yok |
| Duyarlılık eşikleri | 400 ve900 ayrı; tüm girdiler hazır | Hiçbiri nihai en iyi eşik diye seçilmedi |
| Protein/query evreni | Train-linked dizi; unseen query self-only | Harici full63/context genişlemesi yok; izoleler korunur |
| Kapasite | 56→32 projection, tek residual mean PPI; kimya5→8; dört mean rol | Head hariç3920; temsil141; lineer train PT head142K parametre |
| Loss | BCEWithLogitsLoss; eligible drug ve valid train target üzerinde ortalama | Unknown0 yalnız observed-record proxy; class/pos weight yok; train single outcome NA |
| Optimizer / LR | AdamW; lr=0.001; weight_decay=0.001 | Hiç optimizer kurulmadı/adım atılmadı; yeni grid yok |
| Epoch / early stop | Max200; inner validation drug-AP; patience20; min_delta0.0001 | En iyi epoch, tie erken; outer epoch geçerli inner epoch yuvarlanmış medyanı |
| Inner NA / seçim | En az2 geçerli inner fold; daha azsa outer NA | Her aday aynı inner hedef kapsamı; outer test karar vermez |
| Seed / init | Base20261106 +10000*protocol_index +100*outer +inner | CPU1thread/deterministik; ablation aynı initial state; seed araması yok |
| Shuffle | 10 swap/edge, max200 attempts/edge; değişim≥0.5 | Design1null; gelecek3 null önerisi; seed formülü configte; uniform mixing iddiası yok |
| Null başarısızlığı | NA tutulur; değişim kuralı/seed sonradan iyileştirilmez | 700 stress_o02_i02 başarısız; tam ablation kapsamı açık karar gerektirir |
| Karşılaştırma | Frozen B0/B1/B2 + aynı mimari no/real/shuffled | Aynı split/proxy/train PT/input/paired54; performans hesaplanmadı |
| Eğitim onayı | training_enabled=False | Bu belge öneri; kullanıcı onayı olmadan trainer/performans başlatılmaz |

## Eşik önerisinin sürüm geçmişi

`configs/WP09_training_PROPOSED_v1.json` null çalıştırılmadan önce yazılan kapsam-öncelikli400 taslağını saklar. Etiketten bağımsız topoloji/null sonuçları incelendikten sonra **ayrı v2** oluşturuldu: öneri700, approved=None. V1 veya ilk analizin kayıtları ezilmedi. Revizyon hiçbir AP/AUROC veya test etiketi görerek yapılmadı; bu aşamada performans hesaplanmadı.

400'de 0/40,700'de39/40,900'de32/40 null kabul edildi. 400 ve700 ana/stres outer testte51/62 ilaç erişimini korur;900 ana44/stres46. İnsan protein mesaj kapsamı700'de400'e göre azalır; aynı ilaç erişimi bütün protein komşuluklarının aynı olduğu anlamına gelmez. **700 en iyi tahmin eşiği değildir; fizibilite dengesi için öneridir.**

700'de yetersiz null:

| context | edges | successful_swaps | changed_fraction | status |
| --- | --- | --- | --- | --- |
| stress_o02_i02 | 105 | 1050 | 0.4857 | NA_shuffle_insufficient |

Bu başarısızlık sessizce gerçek kenar, başka seed veya gevşetilmiş değişim kuralıyla doldurulmadı. 49 yetersiz adayın tamamı NA'dır. Degree korunması null'un yeterince farklı veya uniform örneklenmiş olduğunu kanıtlamaz. Gerekli üst sınır hesabı hiçbirinde≥%50 değişimi matematiksel olarak dışlamadı; başarısızlık imkânsızlık kanıtı değildir.

**Eğitimden önce açık karar:** mevcut kural ve eksik-null kapsamını kabul etmek veya etiketten bağımsız yeni bir null politikasını ayrı sürümle incelemek. İkinci seçenek seçilirse önce policy yazılır; iyi performans veren karışım/eşik seçilmez. Yeni null politikasının incelenmesi de bugün otomatik başlatılmadı.

## Onaylanacak somut öneri

Güncel öneri `configs/WP09_training_PROPOSED_v2.json`; protein/query sözleşmesi `docs/plan/WP09_DESIGN_DATA_CONTRACT_v1.md`. Eşik, kapasite/loss/optimizer/LR, epoch/inner NA/outer refit, seed/init, null tekrar/başarısızlık politikası birlikte eğitim onayına sunulur. 35 test yazılım mekaniğini doğruladı; tahmin faydası, klinik güvenlik veya dış doğrulama değildir.

Eğitimden sonra aynı-split kıyas keşifseldir: baseline outer sonuçları daha önce görüldü. Outer test seçime/early-stop'a girmez. Pooled class-AUROC ile fold içi tanı ayrılır; koşullu grup CI bağımsız dış doğrulama sayılmaz. WP08'deki1685 kapsam dışı kaynak pozitif ve tüm1061 PT için iddia sınırı korunur.

**Gerçek GNN eğitimi veya performans karşılaştırması yapılmadı. Kullanıcı eğitim onayı bekleniyor.**
