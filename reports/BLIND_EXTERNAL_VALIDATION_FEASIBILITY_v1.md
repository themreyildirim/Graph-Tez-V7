# Kör / dış doğrulama fizibilitesi v1 — WP13

Durum: **RETROSPECTIVE_OOF_COMPARISON_DESIGN_ONLY**; yeni dış ilaç için **BLOCKED_NO_APPROVED_EXTERNAL_INPUT_ADAPTER**. Bu çalışmada yeni tahmin, fit, API, etiket eşleme veya performans metriği üretilmedi. Kullanıcının iki hedefi ayrı tutulur: PDF'den kaynaklı açıklama ve PDF yan etkilerini girdi olarak almamış kayıtlı ilaç–PT tahmini.

## 1. Gerçek dosyalarla eğitim dışı kapsam denetimi

Kilitli WP08 outer_membership/nested_partitions/split_lock üçlüsü frozen_split_manifest SHA-256 ile doğrulandı. WP08 final PT B1/B2 için20, WP09 no/real/shuffledR0/R1/R2 için50, WP10 dört kol için40: **110 model/outer-fold bağlamı**, primary ve stress ayrı denetlendi. Büyük XML/STRING tekrar taranmadı.

Her bağlamda kayıtlı OOF drug/fold anahtarı dış test üyeliğiyle; model fit ID'leri train ile; kimya scaler fit ID'leri train ile; PT sözlüğü mevcut train-only sözlükle karşılaştırıldı. Train/test ilaç ve yapısal grup kesişimi yok. Model JSON/NPZ hash'leri kendi artifact manifestleriyle doğrulandı. WP09/WP10 train ve query NPZ hash'leri metadata ile aynı; train grafı ilaçları train'e, query ilaçları test'e eşit; train grafında hedef/y/PT etiketi dizisi yok. Protein evreni train fit accessions ile eşit. Protein düğümleri ilaçlar arasında ortak olabilir; bu, heldout ilacın train grafında bulunması demek değildir.

| Kayıtlı aile | Her protokolde skor bulunan benzersiz ilaç | Primary fold başına PT aralığı | Anlam |
|---|---:|---:|---|
| B1 |54|220–275|Kimya uygunluğu;6 boyut (5 özellik + maske)|
| B2 |61|240–326|Kimya + dört ayrı protein rolü/maskeleri|
| WP09 her varyant |61|240–326|Protein mesaj geçişli model|
| WP10 her kol |61|240–326|150 boyutlu genişletilmiş füzyon|

62 envanter kaydı korunur. Skoru olmayan/abstain ilaçlar negatif veya başarısızlık sıfırı yapılmaz; Methenamine kullanılabilir kişiselleştirilmiş girdisi yokken abstain, Tobramycin protein modalitesi eksik. Atom dalı54 QC uygun yapı için açık,8 yapı için kapalı kalır. Tam61 kapsamın tamamında atom dalı varmış gibi yorumlanmaz. Ortak B1/GNN karşılaştırması54 kapsam gerektirir. Stress hedef aralıkları ayrı OOF_scope_summary.csv'dedir; farklı foldlarda bulunmayan PT'ler birleştirilip doldurulmaz.

Gerçek demo A1P1 primary: **Erythromycin DB00199 outer3/318 PT**, **Doxycycline DB00254 outer1/240 PT**. İlgili kendi-fold modelinde bu iki ilaç train fit, scaler fit veya train grafında yoktur. Bir ilaç diğer outer fold modellerinin eğitiminde bulunabilir: herhangi bir kayıtlı modeli seçmek kör tahmin sağlamaz. Yalnız kendi heldout model-job/OOF satırı kullanılmalıdır.

Kanıtlar: reports/qa/WP13/v1_2/OOF_fold_isolation_checks.csv, OOF_demo_drug_checks.csv, OOF_scope_summary.csv, blind_audit.json, blind_source_pins.json. Denetim scripts/wp13_blind_audit_v1.py ile salt okunur,20.000 satırlık OOF parçalarıyla yapılır. İlk çalışmadaki Windows manifest yol ayıracı okuma problemi ayrı audit_initial_path_issue.json'da korunur; okuyucu anahtarları normalize edildi, eski manifest değiştirilmedi. Denetim mevcut kayıt provenansını doğrular; tüm olası gelecek kod için evrensel sızıntısızlık kanıtı değildir. Burada modeller yeniden çalıştırılarak skor hesaplanmadı.

## 2. Gerçek girişler ve tahmin anında bilinebilirlik

| Model / bileşen | Gerekli bağımsız giriş | Dönüşüm ve kapsam |
|---|---|---|
| B1 |Doğrulanmış moleküler yapıdan MW, LogP, HBD, HBA, TPSA + kimya maskesi|İlgili outer-train scaler ve sabit özellik sırası; LR parametreleri/head aynı|
| B2 |B1 +56 özellikli proteinlerden target/enzyme/transporter/carrier ayrı özetleri ve maskeleri|Train-only protein/kimya dönüşümleri; yokluk maskeli, ilişki uydurulmaz|
| WP09 |Kimya5→8, protein56→32, tek residual mean-message, dört rol readout|Strict insan STRING700 train protein bağlamı; query train/cache'i değiştirmez; atom grafı yok|
| WP10 |Atom44, bağ14; kovalent bağ iki yönlü; stereokimya/aromatiklik/formal yük/H; atom16→mean8; atom maskesi|Mevcut141 boyut kimya/protein +8 atom +1 maske=150; A0/A1 ve P0/P1 anahtarları; train scaler/target sabit|

DrugBank ilişkileri, kaynak doğrulanmış SMILES/PubChem özellikleri, temiz protein dizileri ve mevcut izinli STRING, yan etki etiketinden bağımsız olarak tahmin zamanında bulunabiliyorsa kullanılabilir. Bulunamayan/modalitesi olmayan kayıt tahminle doldurulmaz.80 özelliksiz context ve23 koşullu E.coli protein insan ağına eklenmez. PPI skoru düğüm özelliği değildir; kalite_skoru yasaktır. İlaç ID metadata'dır, sayısal ezberleme özelliği değildir.

**Yasak girişler:** prospektüs yan etki listesi, SIDER/test etiketi, kategori/PT yoğunluğu, raporlama sıklığı, hedefe dayalı skorlar, SHAP veyaΔz. Bunlar daha sonra değerlendirme/açıklama için kullanılabilir; yeni ilacın input vektörünü veya kimlik kararını etiket sonuçlarına göre ayarlayamaz. B0 sabit etiket sıklığı referansı olarak kalır; bu sıklık B1/GNN özelliği yapılmaz. Ayrıntılı girdi matrisi prediction_input_leakage_matrix.csv'dedir.

## 3. 62 ilaç dışında doğrudan inference mümkün mü?

**Mevcut uçtan uca proje hattında desteklenmiyor.** WP10 MolecularProteinFusion._check_molecules frozen62 ID ve54/8 QC maskesini doğrular, kapsam dışı ID'yi reddeder. WP09 hazırlayıcıları ve WP08 eligibility/transform kaynakları mevcut kanonik kayıtlarla sınırlıdır. Bunları yeni ilaç ekleyerek sessizce genişletmek mevcut sözleşmeyi ihlal eder.

B1'in predict_parameters fonksiyonu doğru sırada/ölçekte bir sayısal vektörü matematiksel olarak değerlendirebilir. Bu, yeni antibiyotik için kimlik, tuz, stereokimya, QC, özellik tanımı ve preprocessing'in doğrulandığı anlamına gelmez. Yeni inference adaptörü ve teknik testleri ayrıca onaylanmalıdır. Yeni proteinlerin frozen train protein cache'iyle nasıl ele alınacağı da açık karardır; query ile train cache'ini değiştirmek kabul edilmez. Sabit model head'ine yeni PT eklenemez.

Kaynak kod denetimi: scripts/wp08_baseline_train.py, wp09_data.py, wp10_train.py, wp10_training_forward.py, wp10_molecular_encoder.py. Eski dosyalar salt okunur; kaynak hash'leri yeni kanıt manifestine alınır. Bu rapor yeni adapter uygulamaz.

## 4. Mevcut OOF ile yapılabilecek kör karşılaştırma önerisi

1. Kendi outer-test OOF ilaç/fold/PT/job, seed/split, model/metadata, hedef sözlüğü ve önceden belirlenen karşılaştırma politikasını hash'le kilitle. Bu çalışmanın blind_source_pins kaydı bu provenansı sağlar; geçmişe dönük prospektif körlük yaratmaz.
2. Etiket/tahmin sıralarını görmeyen bir kaynak eşleme incelemesi planla. Ürün etkin madde, formülasyon/tuz ve ana DrugBank kimliği eşdeğerliği açıkça karar gerektirir. Erythromycin tablet BP250 mg ve doxycycline monohydrate kapsül ana ilaç ile otomatik tüm ürünler eşdeğer değildir.
3. PDF'yi yalnız tahmin kilidinden sonra değerlendirme kaynağı olarak aç. Kaynak terimi→donmuş PT CUI eşlemesini sözlük/uzman incelemesiyle kayıtla; mevcut Türkçe aday adlarını otomatik PT sanma. Eşlenmeyen, doğrudan ilaç, ürün, class-level ve belirsiz ifadeleri ayrı tut. Eşleme ve rank değerlendirme eşikleri önceden belirlenir.
4. Yalnız eşlenebilir hedeflerde kaynakta bildirilen olayların sıralamadaki yerini ve kapsamını raporla. Kaynakta geçmeyeni gerçek negatif yapma. Gerçek negatif yokken klinik özgüllük, kalibrasyon veya tam hedef uzayı başarısı iddia etme. Fold sözlüğü dışında kalan pozitifler ayrı kayıt;1061 PT'nin hepsinde skor varmış gibi davranma. Önceki1685 sözlük dışı kaynak pozitifini yok sayma.
5. Mevcut iki PDF ve model sonuçları zaten incelendiğinden çalışma **retrospektif, keşifsel kaynak karşılaştırması** olur; prospektif bağımsız kör deney değildir. SIDER ile prospektüs kaynaklarının tarihsel örtüşmesi/aynı etiket kökeni bağımsızlığı sınırlayabilir. Bu kaynaklar klinik hasta sonucu değildir. WP08–WP12 başarı metrikleriyle birleştirilmez; yeniden model seçimi yapılmaz.

## 5. Gerçek yeni antibiyotik için dış validasyon karar kapısı

Önce adayın bütün62 ilaçla, tuz/ana etkin madde, bağlantısallık/scaffold/yüksek benzerlik düzeyinde bağımsızlığı incelenmelidir. Aynı ilacın yeni prospektüsü dış ilaç validasyonu değildir. Yeni ana ilaç için etiketlerden bağımsız ham girişler, kaynak provenansı, yapı/stereo QC, mevcut scaler/head kullanımı, eksik modalite ve olası yeni protein/cache politikası sürümlü bir adaptörde test edilmelidir. Birden fazla fold modeli varsa hangisi/ensemble kuralı kullanılacağı PDF yan etkilerine bakılmadan ayrıca kararlaştırılmalıdır; bu tur seçim yapılmadı.

Başlangıç tahmin dosyası ve yöntem hash kilidi tamamlanmadan prospektüs ADR karşılaştırması başlamaz. Bağımsız referans kaynağının erişim/lisans/tarih/etiket kökeni uygunluğu belgelenmelidir. Yeni dış veri indirme bu turda yetkili değildir. Kaynak kimliği, girdi veya kapsam engeli varsa **STOP/NA**. Bu şartlar sağlanmadan dış başarı, genel genelleme, nedensellik veya klinik risk iddiası kurulamaz.

**Sonuç:** mevcut OOF'nin drug-disjoint kapsamı doğrulandı; sınırlı retrospektif kaynak karşılaştırması tasarlanabilir. Yeni dış antibiyotik çıkarımı ve değerlendirmesi başlatılmadı. Kullanıcı değerlendirmesi bekleniyor.
