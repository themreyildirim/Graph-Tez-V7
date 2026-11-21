# WP13 — Dış antibiyotik kör inference adapter sözleşmesi v1

Durum **DESIGN_ONLY / NOT_SUPPORTED_UNTIL_APPROVED**. Bu tur dış ilaç, yeni özellik/attribution, forward/fit veya PDF karşılaştırması çalıştırılmaz. Önceki split, scaler, modeller, PT head ve QC kararları değişmez.

## Kapı0: gerçekten yeni ana etkin madde

Bağımsız özellik kaynaklarından kimlik dosyası: primary/secondary DrugBank ID, tüm bilinen alias ve DBSALT→ana madde bağları, CID/SID ayrımı, InChIKey tam ve bağlantısallık bloğu, stereokimyası korunmuş SMILES, formülasyon/tuz/doz kanıtı. Önce mevcut WP02 köprüleri ve tüm62 envanter/outer-train birleşimiyle karşılaştır; tek foldun testinde bulunmak dış ilaç olmak değildir. Aynı ana ilacın yeni tuzu, markası, dozu veya PDF'si dış ilaç değildir. Bağlantısallık/scaffold/benzerlik yakınlığı ayrıca raporlanır; yakınlık olmaması kimlik çözümünün yerine geçmez. Kimlik eşleme çözümsüzse STOP. Bu kanıt dosyası mevcut ham allowlist/kullanıcı sağladığı kaynaklardan hazırlanmalı; yeni kaynak indirme yetkisi bu sözleşmeden doğmaz.

## Kapı1: B1 dış kimya adapter'ı — önce bu

Sabit sıra **chem__MW, chem__LogP, chem__HBD, chem__HBA, chem__TPSA, mask__chemistry**. Birimler MW=g/mol, LogP=boyutsuz tanım/sürüm kayıtlı, HBD/HBA=sayı, TPSA=Å². SMILES ayrıştırma, tuz/çok bileşen, stereokimya, metal, ana yapı/ölçülen yapı farkı insan QC gerektirir; fragment/atom keyfi silinmez. Özellik hesaplama tanımı mevcut WP04 ile aynı olmalı; aksi fark kaydı ve onay gerekir. Yeni ilacın ham ve QC değerleri ayrı, kaynak hash/sürümü/sorgu zamanı kayıtlı. Prospektüs ADR veya SIDER etiketi bu dosyada bulunamaz.

Her sabit outer model için yalnız kendi mevcut train-only fit kaynakları/kimya scaler parametreleri kullanılır. Dış ilaçta scaler fit edilmez; feature order değişmez. Kimya yoksa B1 abstain; sıfır ham vektör gerçek kimya gibi verilmez. Maskeli nötr **standartlaştırılmış** blok, mevcut eğitim dönüşümünün formülü ve maske tanımıyla doğrulanmalıdır; önceki kodun çalışma çıktısıyla parity testi olmadan implementation onayı yok. LR katsayı/intercept ve fitted_classes dizilişi NPZ/JSON'dan sabitlenir. Sayısal predict_parameters fonksiyonu vektör hesaplayabilir; bu kimlik/QC/preprocessing adapter'ının hazır olduğunu göstermez.

## Kapı2: A1P1 dış query adapter'ı

Atom44/bağ14, iki yönlü bağ hizası, H/formal yük/aromatiklik/stereo,16 hidden→8 readout; kimya5, protein56, dört ayrı rol readout ve maskeler; mevcut150 füzyon ve protein projection32 korunur. WP10 frozen62/54-8 ID guard'ını devre dışı bırakmak kabul edilmez. Dış yapı QC ve atom-maskesi politikası için ayrı sürümlü query adapter ve onay gerekir; eksik yapı keyfi mask1 yapılmaz. Özellik yokluğu eğitim protokolündeki gibi maskelenebiliyorsa parity ile belgelenir; bütün kişiselleştirilmiş modaliteler yoksa abstain.

Protein kimliği/dizisi/56 özellik/roller mevcut kaynaklarla doğrulanmalı. Rol yokluğu bilinmeyendir; ilişki uydurulmaz. Strict insan STRING700 train protein/cache aynen kalır; query kendi proteinleriyle train grafını veya scaler'ı değiştiremez. Train-cache dışında kalan proteinler için mevcut self-only davranışın dış query'ye aktarılabilirliği ayrı test/onay gerektirir. Yeni PPI komşuluğu oluşturulmaz. E.coli23/context80 eklenmez. Query ilişkileri train/ters ilişkiler arasına karışamaz. Uygun adapter yoksa STOP/NOT_SUPPORTED.

## Kapı3: model ve hedef politikası — seçim önceden

Öneri: ilk teknik pilot B1 ile, beş frozen primary outer modeli **ayrı ayrı**; hiçbiri PDF sonucuna göre seçilmez. Birincil tek model veya ensemble henüz **PENDING_USER_DECISION**. Ensemble istenirse beş modelin ortak fit edilmiş PT kesişiminde eşit ağırlık gibi bir kural, kaynak/prospektüs sonucuna bakmadan ayrıca onaylanır; union'daki eksik hedef sıfıra doldurulmaz. Her model kendi scaler/head'ini kullanır. Önceki model başarımı bilindiğinden gelecek karşılaştırma keşifseldir. En iyi fold veya en yüksek skor seçimi yasaktır. Yeni ilaç için bu öneri onaylanmadan skor üretilmez.

## Kapı4: kilit ve referans ayrımı

Kimlik/QC/ham özellik+maskeler, descriptor/parser sürümü, model/scaler/split/head hash'leri, seed/determinism, model/ensemble yöntemi ve tüm çıktı skorları tek prediction_lock manifestinde saklanır. Kilitten sonra referans PDF ADR incelemesi açılır. Referans işlevi inference'a callable/girdi olarak verilemez; API PDF içeriği model girdisi değildir. Test etiketi, PT sıklığı, kategori/PT sayısı, kalite_skoru ve SHAP/Δz türetilmiş alanları yasaktır. Türkçe/İngilizce terim→PT eşlemesi uzman/denetlenebilir sözlük ile ayrı sürüm; yoksa UNMAPPED. Ürün/sınıf/doğrudan/uyarı ve tuz/doz farkları saklanır. PDF'de yokluk negatif değildir; klinik doğruluk, kalibrasyon ve özgüllük iddiası yok.

## Uygulama öncesi zorunlu test planı

1. Eğitim envanterindeki primary/secondary/salt/alias/bağlantısallık eşleşmesinde dış ilaç kapısı reddeder; eksik kimlik STOP.
2. Yanlış sıra/birim/boyut, sonsuz/NaN veya hatalı maske reddi; descriptor sürüm/QC guard'ı.
3. Mevcut heldout ilaçla, sayısal B1 dış-query adayının frozen dönüşüm+OOF replay parity'si (bu bir dış başarı testi değildir).
4. Ham eksikliği sıfır gerçek özellik sanmama; maskeli nötr blok ve abstention parity.
5. Wrong PT/fold/model/scaler/hash reddi; model ağırlığı ve train fit kimlikleri değişmez.
6. PDF/SIDER/heldout label mutation, reference nesnesi enjeksiyonu ve PT sıklığı ekleme girişimlerinde tahmin/değer/fit state değişmez veya istek reddedilir.
7. A1P1 atom permutation/bond alignment/edge effect, train/query/cache izolasyonu, başka query eklenince eski skor değişmez; protein/PPI/QC kapsam dışı STOP.
8. Fold hedefleri eksikse NA; ensemble'da eksik hedef/sıfır doldurma reddi; sonradan model seçimi reddi.
9. Prediction_lock tamlığı ve referans açılma sırası; geçmiş frozen artefakt hash'lerinin değişmezliği.

Bu testler **tasarım gereksinimidir, dış adapter uygulanıp geçmiş gibi gösterilmez**. Bu turdaki testler yalnız mevcut açıklama sunumu ve önceki read-only demo içindir. Uygulama/gerçek dış deney için ayrıca kullanıcı onayı beklenir.
