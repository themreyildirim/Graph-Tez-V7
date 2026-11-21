# WP12 — Kullanıcı PDF'leriyle gerçek belge pilotu

08.11.2026. **PDF çıkarımı ve kaynak doğrulaması tamamlandı;kullanıcı incelemesi bekleniyor. Ollama/LLM kurulumu,model indirme/çalıştırma veya eğitim yapılmadı.**

## 1. Kaynakların gerçekten mevcut olması ve kullanıcı provenansı

Kullanıcı şu iki dosyayı `data/user_pdfs` altında tam adıyla seçti. İkisi degerçek yerel dosya olarak bulundu;herhangi biri bulunmasaydı durulacaktı. Kaynak verilmiş olmasının kanıtı mevcut kullanıcı talimatındaki açık seçimdir;dosya sahibi/yayıncı özgünlüğü veya dijital imza kriptografik doğrulaması iddia edilmez. İnternetten alternatif prospektüs aranmadı veya indirilmedi. PDF içindeki bağlantılar takip edilmedi.

Ham dosyalar salt okunur açıldı;SHA-256 önce/sonra aynı kaldı. PDF header,PyMuPDF PDF biçimi/şifre durumu vefiziksel sayfa sayısı kontrol edildi. Poppler `pdfinfo` sayımları bağımsız olarak6 ve11 sayfayla eşleşti. Kaynaklar kopyalanıp değiştirilmedi.

| filename | bytes | pages | raw_SHA256 | content_revision | type |
| --- | --- | --- | --- | --- | --- |
| pil.502.pdf | 136759 | 6 | 1b8182521f1314c595451e14a881caa930ba8a5df3c99d468e50429d0e61533e | December 2025 | patient_information_leaflet |
| 050641Orig1s032lbl.pdf | 550960 | 11 | 237080fbda2eb353f322921302401bcc98d6a8e54dece1f8e9d11c886dfddcd5 | 02/2022 | prescribing_information_label_with_package_image_and_signature |

`user_source_receipts.json` açık kullanıcı dosyası,gerçek yol/hash/boyut vealımın gözlendiği UTC zamanını kaydeder. Bu zaman dosyanın yayımlanma veya ilk yüklenme tarihi değildir. Ham PDF kimliği dosyanın tam baytlarına bağlıdır;dosya adı tek başına kimlik değildir.

## 2. Sözleşmeye uygun bütün fiziksel sayfaların çıkarımı

Önceden kabul edilmiş `WP12_DOCUMENT_DATA_CONTRACT_v1.md` vemakine şeması değişmedi. Hazırlık v1'in boş envanteri/kilitli kapısı tarihsel olarak korundu;gerçek pilot yeni `wp12_pilot.py` girişinde veayrı `reports/qa/WP12/pilot_v1/` dizininde uygulanır.

PyMuPDF2.1,`Page.get_text('text',sort=False,flags=195)` ile bütün17 fiziksel sayfada çalıştı. OCR,layout-model çıkarımı veya sessiz satır/Unicode normalizasyonu yoktur. Parametreler/version ilk çıkarımdan önce kaydedildi. API'nin text-page yolu için [resmî Page.get_text belgesi](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text) kullanıldı;yerel kurulu fonksiyon da incelendi.

Her sayfanın tam metni,UTF-8 hash'i,Unicode kod noktası uzunluğu vephysical index0/page number1 bağlantısı saklandı. `page_text/` dosyaları bayt olarak yazılarak Windows satır sonu dönüşümü önlendi. Alıntıların tamamı bu saklanan aynı dizgenin `[char_start,char_end)` dilimidir;PDF ham bayt konumu veya ekrandaki piksel koordinatı değildir.

17/17 sayfa metin katmanı içerir;boş metin sayfası0 veUnicode replacement-character sayısı0'dır. Bu,bütün görsel içeriğin metne dönüştürüldüğü anlamına gelmez. Doxycycline fiziksel10,ambalaj etiket görseli içerir ve yalnız154 kod noktalık uyarı/footer metni çıkarılmıştır. Sayfa atlanmadı;görseli saklandı,OCR yapılmadı,görselde görülen içerik metin katmanı alıntısı diye uydurulmadı. Fiziksel1'deki yapı görseli de raster kanıt olarak korunur;ondan yeni SMILES/özellik çıkarılmadı.

## 3. Sayfa numarası,sürüm vebelge türü

- Erythromycin:6 fiziksel sayfa,`Package leaflet: Information for the user` başlığıyla hasta kullanma talimatıdır. Fiziksel6'da revizyon **December2025** olarak doğrulandı. PDF metadata CreationDate/ModDate Mart2026'ya aittir;bu tarihler klinik belge revizyonuyla aynı şey değildir.
- Doxycycline:11 fiziksel sayfa;ilk9 sayfanın görünür etiketi `Page1 of9`–`Page9 of9` biçimindedir. Fiziksel10 ambalaj görseli,fiziksel11 elektronik imza temsilidir;11'deki `Signature Page1 of1`,physical page number11'in yerine kullanılmaz.
- Doxycycline revizyonu fiziksel9'da **Rev:02/2022**;PDF CreationDate Mart2022,ModDate Haziran2024'tür. Belgenin footer'ında **en güncel FDA onaylı etiket olmayabileceği** yazmaktadır. Bu pilot,tarihsel kullanıcı dosyasını inceler;güncel etiket veya klinik öneri doğrulaması yapmaz.

Sürüm/ürün/üretici görüşleri,belgedeki gerçek quote ID'lerine bağlanan `document_metadata_content_review.json` içindedir. PDF metadata veya dosya adına bakarak sürüm belirlenmedi. Elektronik imza temsilinin korunması,imzanın kriptografik olarak doğrulandığı anlamına gelmez.

## 4. Ana ilaç,tuz/hidrat,formülasyon vemarka

| filename | DrugBank_parent_id | existing_parent_name | existing_CID | PDF_formulation | PDF_named_salt_or_hydrate | existing_salt_link_id |
| --- | --- | --- | --- | --- | --- | --- |
| pil.502.pdf | DB00199 | Erythromycin | 12560 | 250 mg enteric-coated tablet | no specific salt/ester named beyond erythromycin | nan |
| 050641Orig1s032lbl.pdf | DB00254 | Doxycycline | 54671203 | oral capsules 50/75/100/150 mg parent-equivalent;doxycycline monohydrate | doxycycline monohydrate | DBSALT001956 |

Erythromycin'in etkin maddesi/adı/250mg gücü fiziksel1/6 ile;enterik kaplı tablet niteliği6 ile desteklenir. Belge erythromycin dışında belirli bir tuz/ester adlandırmaz. Sekiz eski DrugBank tuzundan biri tahmin edilerek seçilmedi. Sovereign Medical/Waymade bilgisi pazarlama ruhsatı sahibi/üretici olarak kaydedildi;ayrı bir tescilli ilaç marka kimliği uydurulmadı.

Doxycycline'de monohydrate kapsüller,parent doxycycline'e eşdeğer50/75/100/150mg olarak fiziksel1/8'de tanımlanır. Mevcut WP02 kaynağında **DBSALT001956 Doxycycline monohydrate → DB00254** ilişkisi vardır. Hyclate,hydrochloride vecalcium diğer kayıtlar olarak ayrı kalır. Chartwell Pharmaceuticals/Chartwell RX üretici/pazarlayan şirket metniyle kaydedilir;generic ürün adının yerine yeni bir ilaç markası sayılmaz.

Mevcut WP02 primary ID,PubChem CID veWP04 structure/CID kayıtları birbiriyle kontrol edildi:DB00199/CID12560;DB00254/CID54671203. Bu **etkin madde/ana ilaç düzeyinde** desteklenen eşlemedir;ürün,doz,formülasyon veya klinik eşdeğerlik kanıtı değildir. PDF'nin monohydrate formülü `C22H24N2O8 • H2O` iken mevcut parent yapı `C22H24N2O8` kaydıdır. PDF'nin monohydrate molekül ağırlığı mevcut parent kimya özelliği yerine geçirilmedi;RDKit/kimyasal özellikler yeniden üretilmedi.

## 5. Birebir yan etki bölümleri vebağlam ayrımı

Toplam **44 kaynak alıntısı** vardır. Ana yan etki metni Erythromycin physical4–5 veDoxycycline physical7'den bütünüyle sayfa dilimleri olarak saklandı. Ayrıca kimlik,sürüm,formülasyon veilgili uyarı bağlamları için alıntılar bulunur. Üst bölüm/alt paragraf dilimleri örtüşebilir;44 sayısı benzersiz yan etki,kategori veya hasta sayısı değildir.

Erythromycin4'te bölüm4 başlangıcı,5'te devamı korunur. `Not known` sıklık başlığı ilgili alt bölümle birlikte saklanır;sayısal risk üretilmez. Aynı fiziksel4'teki boya maddesi alerjisi `excipient_specific`,doz aşımı cümlesi `overdose_context` olarak ayrı kaynak bağlamıdır;normal kullanımda etkin madde yan etkisi gibi karıştırılmaz.

Doxycycline7'de açılışın ilk cümlesi doğrudan doxycycline'den söz eder ve`infrequent` niteliğini taşır. Sonraki **The following adverse reactions have been observed in patients receiving tetracyclines** ifadesi sınıf bağlamını kurar. GI,skin,renal,hypersensitivity,blood,other veprolonged thyroid paragrafları bu bağlam quote ID'sine bağlanmıştır;başlıkta Doxycycline yazdığı için otomatik direct-doxycycline listesine çevrilmez.

Seçilmiş kaynaklı ayrım örnekleri (hiçbiri model etiketi değildir):

| selection_key | physical_page | span | scope | quote | qualifier |
| --- | --- | --- | --- | --- | --- |
| D_direct_intro | 7 | [74,210) | drug_direct | Due to oral doxycycline’s virtually complete absorption, side effects to the lower bowel, particularly diarrhea, have been  infrequent.  | Retain infrequent qualifier;no numerical frequency |
| D_class_intro | 7 | [210,299) | class_level | The following adverse reactions have been observed in patients receiving tetracyclines.   | Governs following ADR subsections;not drug-specific proof |
| D_class_renal | 7 | [1145,1239) | class_level | Renal Toxicity: Rise in BUN has been reported and is apparently dose related (see WARNINGS).   | Inherited tetracycline-class scope;not independent direct-doxycycline evidence |
| D_BUN_exception | 4 | [3826,4023) | class_statement_with_doxycycline_exception | The antianabolic action of the tetracyclines may cause an increase in BUN. Studies to date indicate that this does not occur  with the use of doxycycline in patients with impaired renal function.   | Retain BOTH sentences;doxycycline exception in renal-impairment context;not positive doxycycline-BUN label |
| D_direct_candidiasis | 5 | [1541,1624) | drug_direct | –that the use of doxycycline might increase the incidence of vaginal candidiasis.   | Might qualifier retained |
| D_tetracycline_methoxyflurane | 6 | [53,161) | other_named_drug_tetracycline | The concurrent use of tetracycline and methoxyflurane has been reported to result in fatal renal toxicity.   | Named tetracycline;not silently relabeled doxycycline |
| D_related_animals | 6 | [445,949) | related_drug_animal_invitro_context | Long-term studies in animals to evaluate the carcinogenic potential of doxycycline have not been conducted. However, there  has been evidence of oncogenic activity in rats in studies with related antibacterial, oxytetracycline (adrenal and pituitary  tumors) and minocycline (thyroid tumors). Likewise, although mutagenicity studies of doxycycline have not been conducted,  positive results in in vitro mammalian cell assays have been reported for related antibacterial (tetracycline, oxytetracycline).   | Doxycycline studies not conducted;related oxytetracycline/minocycline evidence not direct human-doxycycline ADR |

Özellikle **BUN** için fiziksel4'teki iki cümle aynı alıntıda tutulur:ilk cümle tetracycline sınıfının antianabolik etkisini,izleyen cümle renal bozukluk bağlamında doxycycline için gözlenmediği istisnasını bildirir. Bu ne doxycycline'e pozitif BUN etiketi ne degenel/bugüne ait “kesin negatif” kanıtıdır. Fiziksel7 renal listesi sınıf kapsamında kalır.

Tooth-development veIH uyarıları `class_including_doxycycline`;CDAD daha geniş antibacterial sınıfı içinde explicitly doxycycline kapsüllerini içerir. Vaginal candidiasis cümlesi doğrudan doxycycline'i anarken`might` niteliği korunur. Methoxyflurane etkileşim cümlesi ad olarak **tetracycline** der;doxycycline diye yeniden adlandırılmaz. Hayvan/in-vitro veilişkili ilaç bulguları insan doxycycline ADR'si sayılmaz. Bu ayrımlar kaynak-okuma temelli pilot anotasyonlardır;klinik uzman gold-standard adjudication veyaLLM sınıflaması değildir,kullanıcı incelemesi bekler.

## 6. Doğrulama,test vegörsel kanıt

18 gerçek pilot testi geçti. İki kaynak dosyanın önce/sonra hash'i;PDF/sayfa sayısı;tüm17 sayfanın ağ vealt süreç erişimi engellenmiş tekrar çıkarımında birebir metin/hash eşitliği;44 alıntının page/span/hash yabancı anahtarları;physical/printed numara ayrımı;görsel10'un korunması;sürüm metni;sınıf/direct bağlamı;BUN istisnası;monohydrate mapping;eski dosya bütünlüğü vebozulmuş alıntıların reddi kontrol edildi. Gerçek JSON,önceden kabul edilmiş `validate_bundle` ile geçerlidir.

Tüm17 sayfa Poppler ile PNG'ye dönüştürüldü veiki contact-sheet üzerinde incelendi;öncelikli Erythromycin4/5,Doxycycline4/7/10 sayfaları ayrıca tam boyutta kontrol edildi. Poppler bir Symbol font uyarısı verdi;çıktı sayfaları oluştu vebu sayfalardaki metin/yerleşim görsel olarak incelendi. Kaynakta değişiklik veya sessiz metin onarımı yapılmadı. OCR yoktur;görsel alanlar metin çıkarımının sınırı olarak açık tutulur.

PyMuPDF mevcut iki Python ortamında yoktu;yalnız proje içi `.deps/pymupdf` konumuna PyMuPDF2.1 vepip bağımlılıkları kuruldu. İlk sandbox denemesi DNS nedeniyle başarısız oldu;yetkili bağımlılık kurulumu tamamlandı. PyMuPDF2.1 paketi onnxruntime/layout/pymupdf4llm yardımcı bağımlılıkları da getirdi;bu pilot yalnız native text katmanını kullanır. **Ollama/LLM modeli indirilmedi veya çalıştırılmadı.** Kurulan PyMuPDF paketi kendi OCR/layout ONNX kaynaklarını da içerir;bu yazılım paketine bağlı kaynaklar pasif olarak kuruldu,hiçbiri çalıştırılmadı. Ayrı OCR-model indirme komutu yoktur;ağ kapalı tekrar testinde onnxruntime modülü yüklenmedi. Tam bağımlılık listesi `runtime_provenance.json` içindedir. Global Python paketleri/önceki modeller değiştirilmedi.

## 7. Çıktılar vekorunan sınırlar

- `reports/qa/WP12/pilot_v1/source_evidence_bundle.json`:2 belge,2 run,17 fiziksel sayfanın tam metni ve44 birebir kaynak alıntısı;mevcut şemaya uygundur.
- `source_quotes.csv`, `source_context_annotations.json`, `doxycycline_scope_contrast.csv`:sayfa/aralık/hash,ana bölüm vecontext quote ID'leri;manual pilot kapsam/qualifier anotasyonu. SIDER/PT/MedDRA eşlemesi veya eğitim etiketi yoktur.
- `document_inventory.csv`, `user_source_receipts.json`, `source_document_metadata.json`, `document_metadata_content_review.json`:ham hash,boyut,sayfa,sürüm/kaynak vePDF metadata ayrımı.
- `drug_identity_review.json`, `existing_parent_salt_links_review.csv`, `identity_input_manifest.json`:mevcut kaynaklarla ingredient-level DrugBank/CID/tuz incelemesi.
- `page_text/`, `page_inventory.csv`, `page_text_coverage_review.csv`, `visual_content_notes.json`:her fiziksel sayfanın kayıpsız metni vegörsel/metin kapsam sınırları.
- `reports/figures/WP12/pilot_v1/pages/`:tüm17 gerçek sayfa PNG'si;iki contact sheet ve`01_physical_page_text_coverage.png` gerçek metin miktarını gösterir.
- `notebooks/WP12_user_pdf_pilot.ipynb`:çalıştırılmış Türkçe notebook;gerçek tablolar,birebir alıntılar,kapsam grafiği veilgili kaynak sayfa görselleri.
- `pilot_tests_v1.txt`, `artifact_validation.json`, `evidence_manifest.json`:test veprovenans kanıtı;hiçbir eski QA dosyası ezilmedi.

Görev başındaki **3208 dosya** (önceki kabul edilmiş artefaktlar veiki seçilmiş ham PDF dahil) hash ile korundu. WP00–WP11 model,split,özellik,sonuç,SHAP/graf attribution veQA verileri değişmedi. Hazırlık v1 sözleşmesi veboş envanteri dekorundu. `run_status.md` yalnız ilerleme kaydıyla güncellendi;önceki tam baytları yeni QA arşivinde vedosyanın devamında saklanır.

`reported_in_PDF` ile `predicted_by_GNN` ayrı kalır. PDF bilgisi SIDER etiketine,model girdisine veyayeni eğitim verisine dönüştürülmedi. Bilinmeyen çiftlerden negatif üretilmedi;klinik risk,tedavi önerisi,nedensellik veyamodel başarısı iddiası yoktur. **Pilot burada durur. Kullanıcı kaynak/alıntı/kimlik incelemesini değerlendirmeden LLM veya sonraki uygulamaya geçilmez.**
