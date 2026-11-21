# WP13 — DB14569 gerçek B1 dış tahmini ve prediction lock v1

Durum: **PREDICTIONS_LOCKED_STOP_BEFORE_REFERENCE**. Deney: **EXPLORATORY_EXTERNAL_LABEL_ISOLATED**. Kullanıcı bu politikayı çıkarımdan önce açıkça onayladı. Önceki STRICT_ANALYST_BLINDNESS_COMPROMISED sınırlaması aynen geçerlidir; bu deney tam araştırmacı-kör veya bağımsız klinik validasyon diye sunulmaz.

## Onay ve precommit

Yalnız DB14569 aktif tedizolid. DB09042 fosfat, stress modeller, A1P1 ve yeni GNN müdahalesi NOT_RUN. Beş frozen primary outer PT–B1 modelinin tamamı tek dış query için kullanıldı; performansa göre seçim veya retry yok. Seed20261106 mevcut eğitim seed'idir; inference deterministik, yeni rastgele seçim yok.

Precommit SHA-256: `f1a1b8d2d5dbdab2fdff36fb6dd2e42f025e1a90ba0a940e309111b98c2f1806`

Prediction_lock SHA-256: `301a116e8f7de4c40c3d10fbbd2e4a122689f8319d82f36eb6183f4b8b0de2f1`

precommit_manifest.json, active_input.json ve approved_policy.json girdiyi/yöntemi; her modelin NPZ/JSON hash'ini, scaler mean/scale'ini, exact class-ID sırasını/head hash'ini, ham ve dönüştürülmüş özellikleri, train-ID hash'ini ve split hash'lerini içerir. Precommit gerçek skorlardan önce diske yazıldı; precommit_sha256.json sabitleme kaydıdır. Bütün kaynak hash'leri çıkarımdan hemen önce ve lock öncesi tekrar doğrulandı. Bu SHA kayıtları yerel iç bütünlük ve işlem sırasını belgeler; bağımsız zaman damgası veya dijital imza değildir.

DB14569 frozen62 ve beş model train/scaler fit kimliklerinde yokluğu yeniden kontrol edildi. Önceki kabul edilmiş alias/tam InChIKey/bağlantısallık denetimi hash ile bağlıdır. RDKit ham SMILES yeniden doğrulandı; key XFALPSLJIHVRKE-GFCCVEGCSA-N. Sıra/birim MW370.344g/mol, Crippen LogP1.3957,boyutsuz;HBD1,HBA7,TPSA106.26Å²,mask1. WP04 tanımları, tam yapı ve includeSandP=False korunur. Fosfatın kaynak dosyada ayrı kayıt olarak bulunması onun model girdisi yapılması değildir; active_input yalnız DB14569 değerleridir.

108başarılı heldout replay/16abstention ve27854eski skor kanıtı korunup denetlendi. Eski guard modülü değiştirilmedi; yeni yetkilendirilmiş dış modül ayrıdır. Bu tur eski OOF yeniden yazılmadı veya baseline fit yapılmadı. Ön kapıda16offline test geçti; ardından tek query/beş matris-vektör model çağrısı yapıldı. Model sınıfları zaten fit edilmiş geçerli başlıklardır; eski NA/başlık dışı hedefe yeni skor uydurulmadı.

## Gerçek çıktılar

|Model|Geçerli PT|Ortak201 dışındaki geçerli PT|
|---|---:|---:|
|Primary B1 outer1|220|19|
|Primary B1 outer2|262|61|
|Primary B1 outer3|267|66|
|Primary B1 outer4|270|69|
|Primary B1 outer5|275|74|

Toplam1294bireysel skor kaydı; fold1_scores…fold5_scores CSV/JSON dosyalarında tümü korunur. Her satırda rank,CUI,skor,logit,drug,fold,modeljob/sürüm,model/input/scaler/head/feature hash'i ve proxy semantiği yer alır. CUI dizilişi NPZ head'iyle aynı hedefe bağlanır; çıktı sıralaması skor azalan, tam eşitlikte CUI leksikografik artan olarak önceden belirlenmiştir.

common201_scores.csv/json yalnız beş fit edilmiş başlığın201PT kesişimidir. Her hedefte **5 sigmoid skorunun .2 ağırlıklı aritmetik ortalaması**; logit ortalaması, en iyi fold veya eksik skorun sıfırla doldurulması değil. Beş bileşen skor da aynı satırda saklanır.Ortak dışı bireysel satır toplamı289'dur; benzersiz hedef union'u ile karıştırılmaz. Başarı/duyarlılık/klinik risk paydası yoktur.

İlk ortak skorlar sayısal olarak frozen PT CUI'lerle notebook/tablolarda gösterilir. Bu tur PT adları/tedizolid eşleşmeleri için dış sözlük, prospektüs, SIDER etiketleri veya advers reaksiyon başvuru kaynağı açılmadı. CUI skorlarının büyüklüğü SIDER observed-record eğitim proxy'sinin sıralama çıktısıdır; bireysel yan etki görülme olasılığı, sıklık, kalibrasyon veya nedensellik değildir. Unknown biyolojik negatif değildir. Referans olmadan başarı metriği hesaplanmadı.

## Kilit ve sayısal doğrulama

prediction_lock.json girdi/model/politika ve tüm bireysel/ortak skor CSV/JSON hash'lerini bağlar. prediction_lock_sha256.json ve prediction_lock.sha256 kolay doğrulama kopyalarıdır. inference_started.json tek query başlangıcını; numerical_checks.json finite skor/logit ve sigmoid eşitliğini kaydeder. Tekrar çağrı, model dosyasını açmadan ONE_QUERY_NO_RETRY_NO_OVERWRITE ile reddedilir.

13post-lock test PASS: lock/çıktı/input hash'leri,1query/5model,precommit<başlangıç<lock sırası,exact head üyeliği,finite/bounds ve sigmoid-logit ayrımı,CSV/JSON float roundtrip eşitliği,rank/tie politikası,201aritmetik ortalama ve bileşenler,NOT_RUN kapsamı,tekrar kilidi. Sayısal testler kayıtlı sonuçlar üzerinde çalışır; gerçek modeli ikinci kez çağırmaz. Ön kapı16+son kapı13=29test PASS. Sahte label alanları/yanlış temsil/birim/sıra/nonfinite girdi reddedilir. Reference mutation testi giriş şemasında yasak alan enjeksiyonunu reddetme düzeyindedir; bu bütün gelecekteki kod için evrensel sızıntısızlık iddiası değildir.

## SHAP uygulanabilirliği ve erteleme

docs/plan/WP11_B1_SHAP_CONTRACT_v1.md okundu. Yeni dış query için her modelin exact train_drug_ids listesindeki eşit ağırlıklı frozen standardized feature background'u kullanılabilir; aynı logit kapalı formu phi=w*(x−mean_train),base=b+w*mean_train,z=base+sum(phi). Model/scaler/head fit edilmez. Mevcut feature NPZ, train-ID hizası,6özellik/mask şeması ve kilitli query vektörü gerekir. Bunlar teknik olarak mevcuttur; bu tur yeni SHAP **DEFERRED_NOT_RUN**. Öncelik prediction_lock olduğundan kullanıcıya yeni attribution sonucu sunulmaz. İleride ayrı sürüm aynı WP11 logit/background sözleşmesini doğrulamalıdır.

201PT özeti sigmoid skor ortalamasıdır; tek doğrusal logit modeline eşit değildir. Beş modelin logit-SHAP değerlerini ortalamak bu skor-ortalama ensemble'ının SHAP açıklaması sayılmaz. Ensemble açıklaması istenirse çıktı ölçeği/değer fonksiyonu ayrı sözleşme gerektirir. Klinik risk veya mekanizma çıkarımı yapılamaz.

## Bilimsel durum ve koruma

Geçmiş istenmeyen arama parçacığı maruziyeti silinmedi. Bu tur ağ/arama/API/prospektüs/tedizolid SIDER etiketi erişimi0. Önceki parçacıklar hiçbir girdide/seçimde kullanılmadı; yöntem kullanıcı tarafından sonuçlardan önce sabitlendi. Hazırlık policy'sindeki eski PENDING veNOT_RUN kayıtları tarihsel olarak aynen korundu; bu yeni dizin onaylı dış aşamayı kaydeder.

DB09042/stress/A1P1/SHAP NOT_RUN ve insan QA PENDING durumları korunur. Önceki kabul edilmiş hash'ler final_verification.json kapsamında denetlenir; tüm disk taraması yoktur. Gizli .env/anahtar okunmadı veya hash envanterine alınmadı. Eski run_status baytları yeni giriş altında aynen saklanır. Bu çıktı OOF değildir; WP08–WP10 skorlarının yerine yazılmaz. Grafikler gerçek kilitli skor dosyalarından, notebook çalıştırılmıştır; model yeniden çalıştırmaz.

## Kullanıcıya sonuç ve STOP

Tedizolidin beş B1 modeline ait bireysel sıralamaları ve ortak201hedef sıralaması tamamlanıp kilitlendi. Değerler araştırma kayıt sıralama skorlarıdır; herhangi bir prospektüsle uyum veya klinik doğruluk değerlendirmesi henüz yoktur. Gerçek model skorları artık referans kolundan önce sabittir. **STOP: bu tur kilitten sonra da referans açılmadı.** Kullanıcı PDF'yi ayrı sonraki değerlendirme aşamasında sağlayabilir; o aşama ayrıca kaynak kimliği ve uzman PT crosswalk gerektirir. PDF'de yokluk gerçek negatif veya kesin yanlış tahmin sayılamaz.
