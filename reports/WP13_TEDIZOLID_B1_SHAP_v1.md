# WP13 — DB14569 ilk10 kilitli hedef için gerçek B1 SHAP v1

**SHAP_LOCKED_STOP_BEFORE_REFERENCE.** Yeni sürümde50bireysel B1model/PT açıklaması ve300özellik katkısı tamamlandı. Yeni model/fold seçimi, eğitim, tahmin tekrarı veya referans incelemesi yok. EXPLORATORY_EXTERNAL_LABEL_ISOLATED ve geçmiş STRICT_ANALYST_BLINDNESS_COMPROMISED korunur.

## Kilitler ve kaynaklar

Tahmin kilidi Python bağımsız chunked SHA-256 ve PowerShell Get-FileHash ile yeniden hesaplandı: `301a116e8f7de4c40c3d10fbbd2e4a122689f8319d82f36eb6183f4b8b0de2f1`. Beş NPZ/metadata, tüm bireysel ve ortak201 skor CSV/JSON dosyaları, orijinal precommit/input/policy/scaler/head/feature hash'leri doğrulandı. Tahmin kilidi ve skorlar işlem boyunca değişmedi.

Pre-explanation SHA-256: `10561e51dc048db1e5838ad3a026aec21744df110c11edd90456715de3d95343`

Explanation lock SHA-256: `db756d0a8a34de7be962e2dacde7be399b6b10bb868cb35798ab4be76ec8a0c1`

pre_explanation_manifest, açıklama değerleri hesaplanmadan önce seçili hedefleri/rankları, beş model/background üyeliğini, özellik dosyası, scaler, kaynak ve yöntem hash'lerini sabitledi. Kaynak WP11_B1_SHAP_CONTRACT_v1 ve frozen policy_v1. Seçim **kilitli tahmin sıralamasına bağlı**, fakat prospektüs/gerçek etiketten bağımsızdır. Tahminlerden bağımsız örnek seçimi veya tarafsız genel açıklama örneklemi diye sunulmaz. Bu kullanıcı tarafından önceden belirlenmiş ilk10 koşullu incelemedir.

## Sabit10 hedef

|Kilitli sıra|PT CUI|Türkçe editoryal ad|Donmuş terim adı|
|---|---|---|---|
|1|C0011991|İshal|Diarrhoea|
|2|C0015230|Döküntü|Rash|
|3|C0002792|Anafilaktik şok|Anaphylactic shock|
|4|C0042963|Kusma|Vomiting|
|5|C0000737|Karın ağrısı|Abdominal pain|
|6|C0687713|Gastrointestinal ağrı|Gastrointestinal pain|
|7|C0020517|Aşırı duyarlılık|Hypersensitivity|
|8|C0033774|Kaşıntı|Pruritus|
|9|C0040034|Trombositopeni|Thrombocytopenia|
|10|C0042109|Ürtiker|Urticaria|

Ad kaynağı yalnız mevcut pt_concept_dictionary.csv, iki sütun CUI/term. Bu dosya ilaç–yan etki ilişkisi veya PT sıklığı içermez. Yeni web/güvenlilik referansı/SIVEXTRO etiketi açılmadı. Türkçe adlar editoryaldir; onaylı MedDRA çevirisi, klinik doğrulama veya PDF–PT çapraz eşlemesi değildir. Yakın anlamlı CUI'ler ayrı tutulur. Adlar bu olayların tedizolidde gerçekten gözlendiğini göstermez.

## Exact interventional linear SHAP

Her model için6özellik: MW,LogP,HBD,HBA,TPSA ve ayrı kimya bulunabilirlik maskesi. Query x, kilitli model-specific standardized vektördür. Background, yalnız o modelin **tam train_drug_ids** listesinin saved B1 feature NPZ satırları; eşit ağırlıklı, örnekleme/yeniden fit yok. Test kimlikleri ve DB14569 background dışında. WP11 frozen_contexts ile üyelik, metadata ile özellik hash'i ve scaler/head sırası karşılaştırıldı.

φ_i=w_i(x_i−mean_train_i), base=b+w·mean_train; base+Σφ kilitli logitle karşılaştırılır. Bu kullanıcı isteğiyle yeni attribution'dır; orijinal WP11 artefaktlarını değiştirmez. Kod yeni bir gerçek query `predict/forward` çağrısı yapmaz; yalnız katsayı/background ile katkı/base hesabı ve kilitli çıktı rekonstrüksiyonu yapar. expit(rekonstrüksiyon) kontrolü yeni tahmin dosyası üretmez; eski kilitli skorla eşitliği denetler.

50çiftte maksimum logit toplamsallık farkı **4.4408920985006262e-16** (tolerans1e-10); maksimum sigmoid/locked-score farkı **0** (tolerans1e-12).300satırın tümünde katsayı, ham/standardize değer, background ortalaması, özellik türü ve gerçek işaret korunur. Maskede50yerel katkı0 çünkü query ve background maskeleri1; bu maskenin başka eksik-modalite durumlarında önemsizliğini kanıtlamaz.

## Sözlü yorum

Pozitif φ yalnız bu modelde train-background'a göre logiti artırıcı; negatif φ azaltıcı,0sıfır katkıdır. Özelliğin ham değerinin yüksek/düşük olması tek başına yönü belirlemez; katsayı ve background farkı birlikte etkilidir. Biyolojik mekanizma, nedensellik, klinik sıklık/kalibrasyon veya yüzde risk üretilmez. Yüksek proxy skor, bütün kimyasal katkıların pozitif olduğunu göstermez; model base'i de vardır.

Örnek: model1/İshal için base1.2028393651467484 ve kimyasal+maske katkı toplamı0.15495992764950872, kilitli logit1.357799292796257 ile eşittir. HBD katkısı+0.09622034541489968, HBA−0.005849215876346629, maske0. Bu klinik ishal olasılığının açıklaması değil, ayrı B1 logitinin açıklamasıdır.

Her hedefin beş modeline ait tam Türkçe paragraf reports/WP13_TEDIZOLID_B1_SHAP_VERBAL_v1.md; feature düzeyi300cümle local_feature_SHAP.csv/json;50model/PT paragrafı Turkish_verbal_explanations.csv/json. Tablolarda exact ham değerler; grafik yazılarında okunabilirlik için yuvarlama var. Her hedef için beş ayrı panel ve Türkçe yorum notebook'ta gösterilir. Tekil model katkıları toplanıp/ortalanıp201sigmoid-ortalama ensemble'ının SHAP'ı olarak sunulmaz. Ensemble attribution bu tur NOT_RUN.

## Kapsam, test ve koruma

Ortak201'de191diğer hedef NOT_RUN; bireysel fit başlıklarında toplam1244model/PTçifti NOT_RUN. Bunun anlamı etki yok/SHAP0 değildir. Model head'i dışındaki hedefler için açıklama veya skor genişletilmedi. coverage.csv/json her modelin başlığını ve durumunu açıkça saklar.

10önkapı test PASS: lock/precommit/top10/background/işaret/maske/hassasiyet/formül/64koalisyon bağımsız **sentetik** kontrol/ölçek/schema.14sonkapı PASS: explanation/source hash'leri,50/300anahtar,lockedlogit+skor,herözellikformülü,background,NOT_RUN,NA/sıfır yokluğu,anlatım işaretleri,noensemble/predict,kronoloji,tekrar engeli. Sentetik64koalisyon testi gerçek tedizolid model tahminini tekrar çalıştırmaz. Gerçek sayısal kontroller SHAP rekonstrüksiyonunu kilitli çıktıyla karşılaştırır; performans metriği değildir.

Çalıştırılmış notebook notebooks/WP13_Tedizolid_B1_SHAP_v1.ipynb.10gerçek katkı görseli reports/figures/WP13/tedizolid_B1_SHAP_v1. QA/CSV/JSON/manifest aynı adlı QA dizininde. Önceki dosyalar hash koruma kapsamında değişmez; final_verification kapsamı tüm disk iddiası değildir. Gizli dosya/anahtar okunmaz. Eski run_status baytları yeni girişin altında aynen tutulur. Prediction_lock içindeki eski SHAP DEFERRED_NOT_RUN tarihi değiştirilmedi; yeni attribution'ın durumu yalnız yeni explanation_lock'tadır.

SIVEXTRO KÜB/KT, tedizolid SIDER ilişkisi, advers reaksiyon kaynağı, web/API erişimi yok. A1P1, fosfat duyarlılığı, yeni eğitim kapalı kaldı. Geçmiş bilgi maruziyeti sınırlaması silinmedi. Unknown gerçek negatif değildir. **STOP:** açıklamalar sürümlü kilitle tamam; SIVEXTRO KÜB referansı bundan sonraki ayrı kaynak/değerlendirme aşamasında kullanıcı tarafından yüklenebilir. Bu tur karşılaştırma/başarı metriği üretilmedi.
