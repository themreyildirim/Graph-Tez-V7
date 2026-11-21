# WP13 — Tedizolid / SIVEXTRO dış tahmin hazırlığı v1

**Gerçek dış inference NOT_RUN. Yeni eğitim/SHAP/GNN müdahalesi/prospektüs karşılaştırması yapılmadı.** Çalışma dış adapter sözleşmesi v1 ve aktif ROADMAP WP13 kapsamındadır. Aşağıdaki kimya ve mevcut heldout replay bulguları gerçek dosyalardan hesaplandı; SIDER tedizolid etiketleri veya PT sıklıkları kullanılmadı.

## Önce önemli körlük sınırlaması

SIVEXTRO prospektüsü istenmedi, yüklenmedi veya açılmadı. Ancak kimlik/ön ilaç ilişkisini doğrulamak için yapılan dar web araması, istenmeyen güvenlilik ve prospektüs **arama parçacıkları** döndürdü. Bu belgeler açılmadı; parçacıklar kimya dosyalarına, model/fold/temsil seçimine veya skorlara girdi yapılmadı. Bununla birlikte araştırmacı bilgi körlüğü tam değildir: **STRICT_ANALYST_BLINDNESS_COMPROMISED_BY_SEARCH_SNIPPETS**. Bu olay blindness_audit.json'da açıkça korunur; tam kör prospektif deney iddiası kurulamaz. Kimyasal girişlerin etiketten bağımsızlığı ayrı ve yeniden üretilebilir bir özelliktir; bilgi maruziyetini geri almaz. Katı körlük istenirse yeni bilgiye erişmemiş bağımsız uygulayıcı/değerlendirici gerekir. Bu hazırlığın kabulü gelecekte bu sınırlamanın gizlenmesine izin vermez.

## 1. Kimlik ve eğitim dışında olma

| Kayıt | DrugBank | Yapı / InChIKey |
|---|---|---|
|Tedizolid fosfat|DB09042|C17H16FN6O6P · QCGUSIANLFXSGE-GFCCVEGCSA-N|
|Tedizolid|DB14569|C17H15FN6O3 · XFALPSLJIHVRKE-GFCCVEGCSA-N|

DrugBank XML5.1, exported-on2026-01-04, yerel1.898.100.846bayt dosya **depth2 drug** akış ayrıştırmasıyla okundu. İki kayıt bulunduktan sonra duruldu; dosya belleğe tamamen alınmadı, boyut/mtime değişmedi. Bu ham XML için yeni tam SHA taraması yapılmadı; dosya değişmezliği burada metadata seviyesindedir. Seçilmiş kimlik/kimya çıktısı hash manifestine alınır. Ham güvenlilik/advers reaksiyon alanları dışa aktarılmadı. Kaynak XML'de açıklama cümlesinden prodrug ilişkisi yakalanmadı; bu nedenle ilişkiyi XML doğrulamış gibi sunmuyoruz.

DB09042, Tedizolid phosphate/Torezolid phosphate; DB14569, Tedizolid/Torezolid. Mevcut WP02 primary/secondary/salt tablolarında bu kayıtlar için ikincil veya DBSALT çocuk bağlantısı yok. Bu, her dış veritabanındaki tüm tuz/aliasların çözüldüğü iddiası değildir. Fosfat burada kovalent fosfat esterli, tek bileşenli ayrı yapıdır; basit DBSALT veya temizlenip atılacak karşı iyon değildir. Farmakokinetik birincil araştırma, fosfat ön ilacının fosfatazlarla etkin tedizolide dönüştüğünü bildirir: [Flanagan ve ark., ADME çalışması, PMID24875463](https://pubmed.ncbi.nlm.nih.gov/24875463/). Bu kaynak yalnız kimlik/dönüşüm gerekçesidir, güvenlilik değerlendirme verisi değildir. SIVEXTRO'nun spesifik ticari ürün formu/dozu bu tur belgeyle doğrulanmadı.

62ilaç envanteriyle primary/secondary/salt-ID, yerel alias/ad ve tam InChIKey/bağlantısallık bloğu karşılaştırmalarında **iki kayıt için eşleşme yok**.20 kayıtlı B1/A1P1 primary+stress final modelinin train-ID listelerinde de ikisi yok. Sonuç: **mevcut frozen WP08–WP10 eğitim envanterinin dışında**. Bu, küresel olarak yeni bileşik veya her gelecekteki veri setine bağımsızlık demek değildir. DB14569 eski209 aday listesinde vardı ama yeni62 kohortunda/fit listelerinde değil; aday listesinde bulunmak eğitimde kullanıldığı anlamına gelmez. İlgili kanıt identity_vs_frozen62.json ve frozen_model_training_identity_checks.json.

Morgan radius2/2048bit en yüksek benzerlik DB00601 Linezolid: tedizolid0,37179, fosfat0,33721. Aynı ana madde/bağlantısallık yok; benzerlik yalnız etiket-kör tanısal incelemedir. Yapısal yakınlığı dış başarı kanıtı saymıyoruz; tek fingerprint bütün biyolojik benzerliği ölçmez.

## 2. Kimyasal özellikler ve temsil kararı

İki ham XML SMILES sanitize edildi; RDKit InChIKey XML ile tam eşit. Tek bileşen, formal yük0, metal yok, bir atanmış stereomerkez ve belirsiz stereomerkez0. Fragment silme, nötralizasyon, stereo uydurma veya tedizolid-fosfat dönüşümü yapılmadı. Her iki yapı ve2D çizimleri saklandı.

| Temsil | MW g/mol | RDKit Crippen LogP | HBD | HBA | TPSA Å² |
|---|---:|---:|---:|---:|---:|
|DB14569 tedizolid|370,344|1,3957|1|7|106,26|
|DB09042 fosfat|450,323|1,5127|2|8|152,79|

WP04 ile aynı descriptors() fonksiyonu kullanıldı: MolWt, MolLogP, NumHDonors, NumHAcceptors, CalcTPSA(includeSandP=False). Özellikle fosfat TPSA tanımı eğitimle aynı tutuldu; yeni includeSandP=True varyantına geçilmedi. XML ChemAxon fosfat HBA9 iken RDKit8; logP de hesaplayıcıya göre farklıdır. XML/PubChem sayıları karıştırılmadı; eğitim girdisinin tanımı **RDKit** olduğundan yukarıdaki değerler hazırlandı. XML'deki başka deneysel logP kaydı veya gömülü dış kaynak etiketi yeni girdi yapılmadı. Yeni ChEMBL veri seti/API erişimi yok.

PubChem kimya property URL'sini doğrulama denemesi web aracında erişilemedi; yerel salt özellik isteği ConnectionError verdi. Yeni PubChem yanıtı varmış gibi kullanılmadı; aktif bileşiğin PubChem CID'si bu tur API ile doğrulanmış kimlik sayılmadı. Fosfat CID11476460, DrugBank external-identifier kaydıdır. Mevcut XML yapıları beş eğitim tanımlayıcısını üretmeye yettiği için erişim kısıtı zorlanmadı ve model verisi indirilmedi.

**Sonuçtan bağımsız öneri:** birincil soru ana etkin madde için olduğundan DB14569 tedizolid. WP02 bunu J01XX11 ana kayıt olarak tutuyor; DB09042'nin bu dump'ta ATC'si boş. Bu boşluk fosfatın antibakteriyel olmadığını göstermez. Eğitim protokolü her kaydın tam kaynak SMILES'ini kullanır; bütün ilaçları otomatik aktif metabolite dönüştüren bir kural yoktur. Bu nedenle iki temsil matematiksel olarak aynı girdinin alternatif yazımı değildir. DB14569 birincil araştırma query'si, DB09042 yalnız ayrı önceden onaylı duyarlılık query'si önerisidir; SIVEXTRO ürün tahmini eşdeğerliği iddiası yok. Temsil önerisi JSON'da kayıtlı, dış inference için henüz uygulanmadı.

## 3. İnsan protein/PPI girdileri

Her iki DrugBank kaydında antibakteriyel hedef **23S ribosomal RNA / Enteric bacteria and other eubacteria**, polipeptit yok. İnsan protein/PPI düğümü yapılmaz. Ayrı **enzyme** rolünde Humans P21397(MAOA) ve P27338(MAOB) kayıtları var. Bunları insan terapötik antibakteriyel target veya ön ilacı aktive eden fosfataz diye yeniden adlandırmadık; yalnız DrugBank rolünü koruduk.

WP05'te ikisinin de doğrulanmış standart dizi kaydı ve56 sonlu özellik; WP06'da aynı-taxID9606 kesin STRING eşlemesi mevcut. Yeni protein özelliği/UniProt API üretilmedi. Mevcut induced insan STRING700 ağında ikisinin de derecesi4. Ancak frozen train ağı folda bağlı:

|Primary fold|P21397/P27338 train evreninde|Her protein için PPI700 bağlantısı|
|---|---|---:|
|1,2,4,5|Evet|4|
|3|Hayır|0 / train yolu yok|

3.fold için0, gerçek PPI etkisi sıfır demek değildir; bu train bağlamında uygulanabilir yol yoktur. Query proteinleri mevcut kurala uygun self-only kodlanabilir mi ayrı adapter parity testi gerektirir; train cache'ine yeni düğüm/kenar eklemek yasak. Genel ağa bakıp her fold için dörder kenar varmış gibi davranılamaz. Eksik target/transporter/carrier rolleri uydurulmaz. İlk yeni denetim okuyucusu yanlış `ppi_pairs700` anahtarıyla KeyError verdi; hata kaydı korundu. Gerçek şema `ppi_pairs_700` ve2×E; doğru transpose/hiza ile kapsam tekrar hesaplandı. Eski NPZ değişmedi.

Sonuç: bağımsız insan enzyme girdileri var; **hazır ve onaylı A1P1 dış query adapter'ı var** sonucu çıkarılamaz. K12/MG1655 ve context80 eklenmedi.

## 4. B1 replay/parity — gerçek sonuç

Yeni modül sadece donmuş formülü uygular: (ham5−train mean)/train scale + ayrı kimya maskesi. Kullanılamayan kimyada nötr standart blok ve abstention. Sıra MW/LogP/HBD/HBA/TPSA/mask korunur; yeniden scaler fit yok. Replay, mevcut frozen62 içindeki ilgili heldout ID'lere izin verir; DB14569/DB09042 için dış skor çağrısını açıkça reddeder.

Primary5+stress5 foldta124heldout durum: **108 kullanılabilir replay PASS,16 abstention**.27854 mevcut ilaç/PT skoru yeniden elde edildi. Maksimum dönüşüm farkı0; skor farkı1,11×10⁻¹⁶. Train/test ID kesişimi reddedilir; model metadata/NPZ artifact hash'leri, prepared feature hash ve aynı fit edilmiş class-ID dizisi kontrol edilir. OOF dosyasından yalnız eski skor/anahtar sütunları okundu; observed-label sütunu ve tedizolid SIDER etiketi okunmadı. Bu eski ilaç replay'sidir, yeni dış başarı veya yeni model eğitimi değildir.

**B1 sonucu:** frozen sayısal dönüşüm/katsayı replay'si doğrulandı, kimyasal query girdileri hazırlanabilir. Gerçek dış ilaç kullanımına geçmek için kimlik/temsil ve model politikası onayı + yeni dış query kilidi gerekir. Bu modül halen dış skoru bloke eder; doğru bir vektörün varlığı kendiliğinden inference yetkisi değildir.

## 5. A1P1 teknik engeller ve tamamlanacak testler

Frozen62 ve54/8 QC guard'ı değiştirilmedi. Yeni yapı için dış QC/atom-maskesi sürümü,44atom/14bağ şeması, iki yönlü bağ hizası ve16→8encoder; kimya/protein train scaler'ları ve dört ayrı rol maskesiyle150füzyon query hazırlığı gerekir. Yeni atom grafı/tensor/encoder forward bu tur üretilmedi. Dış proteinlerin self-only/frozen-cache davranışı, özellikle3.fold için açıkça test edilmeli. Eksik ilişki negatif veya sıfır biyolojik özellik sayılmaz.

Önceki adapter sözleşmesindeki ek dış-query kapıları: yanlış birim/sıra/QC/ID/hash reddi; dış SMILES kaynak/sterokimya bağları; amino asit/özellik kaynak eşitliği; query/cache/diğer query izolasyonu; label/reference mutation'a karşı değişmezlik; fold-head hizası ve eksik hedefi NA bırakma; tam prediction_lock ve salt ürün kontrolü. B1 replay geçti; bu ek A1P1 dış adapter testlerinin geçtiği iddia edilmez. Yeni protein ilişkisi veya model/scaler/head genişletilmez.

## 6. Model/fold/ensemble karar kapısı

Beş primary B1 head boyutu220/262/267/270/275, ortak kesişim**201 PT**. Tek foldun klinik/sonuç başarısına göre seçilmesini önermiyoruz. Birincil öneri beş frozen modeli ayrı raporlamak; kullanıcı ayrıca onaylarsa201 ortak PT'de eşit ağırlıklı skor ortalaması ayrı özet olabilir. Eksik PT union'unda sıfır doldurma veya en iyi fold seçimi yok. Stress modeller ilk dış deneye otomatik eklenmez. Bu raporda modeller tedizolid üzerinde çalıştırılmadı.

**Gerçek çıkarım için gerekli kullanıcı kararları:** (1) DB14569 ana etkin madde temsili; fosfat duyarlılığının dahil edilip edilmeyeceği, (2) beş primary B1 ayrı rapor/isteğe bağlı201PT ortalaması politikası, (3) bu oturumun bilgi maruziyeti sınırlamasıyla keşifsel devam mı, yoksa katı körlük için bağımsız uygulayıcı mı. Onay sonrasında yalnız belirlenen dış skor aşaması için yeni sürümlü izin/kilit gerekir. Prospektüs ancak girdiler/yöntem/model ve tahmin hash'leri kilitlendikten sonra referans koluna açılır; bu tur PDF istenmedi.

## QA ve koruma

14 otomatik test: eğitim dışılık,20fit kimliği,SMILES/key/stereo/özellik tanımı,feature-order/maske,dış skora STOP,replay,insan/taxID/fold-PPI,bakteriyelRNA ayrımı,bilgi maruziyeti beyanı ve karar kapısı. Gerçek sonuçlar tests_final.log'da. Çalıştırılmış notebook WP13_Tedizolid_external_preparation_v1.ipynb; iki gerçek molekül çizimi ve kapsam grafikleri reports/figures/WP13/tedizolid_preparation_v1. Ham yapı/kimlik/QC/protein/replay tabloları aynı adlı QA dizininde. Önceki modeller, kaynaklar, API/PENDING/QA kayıtları hash manifestiyle korunur. .env/API anahtarı okunmadı; eski run_status baytları yeni durum altında aynen saklanır. Yeni dış tahmin0, eğitim0, attribution0, SIVEXTRO PDF erişimi0.
