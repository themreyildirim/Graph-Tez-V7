# WP12 — Kullanıcı PDF'leri için belge ve alıntı veri sözleşmesi v1

08.11.2026. AGENTS, aktif ROADMAP WP12 ve `reports/WP12_PREPARATION_DECISION.md` esas alınmıştır. Kullanıcı kaynak kararını verdi: **prospektüs PDF'lerini kullanıcı sağlayacak.** Otomatik arama/indirme yoktur. Bu sürüm yalnız veri sözleşmesi ve uygulama ön hazırlığıdır. Gerçek PDF sağlanmadı; çıkarım yapılmadı. Durum **AWAITING_USER_PDFS**.

Makine şeması: `docs/schemas/WP12_document_bundle_v1.schema.json`. Saf doğrulayıcı: `scripts/wp12_document_contract.py`. Politika: `configs/WP12_preparation_v1.json`. Şemadaki `$schema` adresi standardın kimliğidir; doğrulayıcı onu internetten indirmez. Yeni bağımlılık kurulmadı.

JSON Schema yapısal alanları tanımlar. Kimlik türetme, foreign-key bağlantıları, birebir metin dilimi, sayfa bütünlüğü ve teknik test kaydının üretime alınmaması ayrıca `validate_bundle` tarafından denetlenir. Yalnız yapısal şemadan geçmek gerçek PDF'nin veya kaynağın doğrulandığı anlamına gelmez.

## 1. Kabul edilen kaynak ve kapsam

Yalnız açık kullanıcı eki veya kullanıcının açıkça belirttiği PDF dosyası kabul edilebilir. Her biri bir `receipt` kaydına bağlanır. URL'den veri çekme, kaynak klasörlerini otomatik tarama, prospektüs arama, örnek belge üretme veya kaynak PDF'yi değiştirme yoktur. İleride kullanıcı dosyayı sağladığında erişim salt okunur olacak; gereksiz kopya oluşturulmayacak.

Bu hazırlıkta yalnız metadata/JSON sözleşmesi doğrulanır. `.pdf` uzantısı ve `application/pdf` beyanı gerçek dosyanın PDF olduğunun kanıtı değildir. Ham dosyanın hash'i, boyutu, PDF biçimi, şifre/bozulma durumu ve fiziksel sayfa sayısı ancak kullanıcı dosyası gerçekten sağlandığında kontrol edilebilir. Şu an bu kontroller **NOT_RUN_NO_USER_PDF** durumundadır. Kullanıcı sağlamadığını, bir metadata satırıyla gerçek kaynak haline getirmek yasaktır.

## 2. Kayıt türleri ve kimlik zinciri

| Kayıt | Alanlar ve anlam |
| --- | --- |
| Bundle | `schema_version=WP12-document-bundle-v1`; `data_status`; ayrı `documents`, `extraction_runs`, `pages`, `quotes` dizileri |
| Receipt | `receipt_id`, `source_kind=user_provided_pdf`, `receipt_kind=user_attachment/explicit_user_file`, `reference`, `original_filename`, zaman dilimli `supplied_at`. Kaynak verilme olayıdır; ilaç kimliği değildir |
| Document | `document_id`, `raw_sha256`, `raw_size_bytes`, `mime_type`, `declared_version`, `page_count`, bir veya daha çok receipt. Sürüm bilinmiyorsa `null`; dosya tarihinden sürüm uydurulmaz |
| Extraction run | `extraction_run_id`, `document_id`, `extractor_name/version/options`, zaman dilimli `created_at`, `status=partial/complete`. Hangi metin çıkarma tanımının kullanıldığını bağlar |
| Page | `page_id`, belge/run bağlantıları, `page_index`, `page_number`, ayrı `printed_page_label`, tam `text`, `text_sha256`, `text_length_codepoints`, `text_status` |
| Quote | `quote_id`, belge/run/page bağlantıları, fiziksel `page_number`, `char_start`, `char_end`, birebir `quote`, `quote_sha256`, `claim_kind=verbatim_source_quote` |

`document_id = "sha256:" + SHA256(ham PDF'nin tam baytları)`. İsim değişince kimlik değişmez. Aynı içerik birden çok kez verilirse tek belge kimliği ve farklı receipt/isim kayıtları tutulur; eski teslim provenansı kaybolmaz. Baytlar değişirse yeni belge kimliğidir; eski kaynak üzerine yazılmaz. Hash, kimlik/tutarlılık kontrolüdür; yayıncı veya klinik doğruluk doğrulaması değildir.

Run kimliği; belge ID, extractor adı/sürümü ve seçeneklerin sıralanmış anahtarlı canonical JSON gösteriminden hesaplanır. Tarih bu kimliğe girmez. Aynı çıkarım tanımı aynı kimliği verir; tekrar çalışma olayları ayrıca loglanabilir. Parser sürümü/seçeneği değişirse run kimliği değişir. Çalışma zamanı, motor veya okuma sırası seçimi henüz yapılmış sayılmaz; gerçek parametreler kullanıldığında kaydedilecektir.

Page kimliği belge/run/physical index/metin hash'ine; quote kimliği page ID/aralık/alıntı hash'ine bağlıdır. Sadece basename, ilaç adı veya sayfa numarası tek başına benzersiz kimlik değildir. Bir bundle'da aynı belge, run, page veya quote ID'si tekrarlanamaz. Aynı run içindeki fiziksel sayfa indeksi de tekildir.

## 3. Sayfa numarası ve birebir metin

- `page_index`: fiziksel PDF sırasındaki **0 tabanlı** indeks.
- `page_number`: aynı fiziksel sayfanın insan tarafından okunur **1 tabanlı** sayısı; kesinlikle `page_index+1`.
- `printed_page_label`: belgenin basılı sayfa etiketi varsa ayrı saklanır; fiziksel numara yerine kullanılmaz. Bilinmiyorsa `null`.
- `page_count`: gerçek dosya incelenmeden `null` olabilir; extraction run/page kaydı oluşturmak için fiziksel sayı doğrulanmış olmalıdır. Sayfa indeksi bu sınırı aşamaz.
- `text`: ilgili extractor/run'ın verdiği tam Unicode sayfa dizgesi. Trim, satır sonu dönüşümü, tire birleştirme, boşluk düzenleme veya Unicode normalizasyonu **kaynak metne sessizce uygulanmaz**.
- `text_sha256=SHA256(text.encode('utf-8'))`; `text_length_codepoints=len(text)`.

Kaynak metin üzerindeki sıra, PDF'nin ham bayt sırası veya mutlak görsel yerleşimi değildir; extractor'ın o sürüm/seçenekle verdiği okuma sırasıdır. Gerçek PDF görülmeden bu sıranın, sütunların veya tabloların doğruluğu test edilmiş sayılmaz. İleride okuma sırası değişirse yeni run/metin kimliğiyle izlenir.

Metin katmanı olmayan sayfa için `text=""`, uzunluk0, boş dizgenin hash'i ve `text_status=no_text` tutulur; sayfa atlanmaz, alıntı uydurulmaz. OCR bu hazırlıkta uygulanmaz. Bir run ancak fiziksel sayfaların **tamamı**, boş/metinsiz sayfalar dahil, kayıtlıysa `complete` olabilir; diğer durumlar `partial` kalır. Tamamlanmış çıktılar yayımlandıktan sonra farklı içerikle aynı kimlik üzerine yazılmaz; tekrar üretim uyuşmazlığı açık QC sorunudur.

## 4. Metin aralığı ve kaynak alıntısı

`[char_start,char_end)` yarı açık aralıktır: başlangıç dahil, son hariç. İndeksler **saklanan aynı sayfa dizgesindeki Python Unicode kod noktalarını** sayar. UTF-8 bayt sayısı veya JavaScript UTF-16 birimi değildir. Türkçe karakter, emoji veya birleşen karakterlerde dönüştürme hatasıyla başka bir aralığa işaret edilmez.

Zorunlu eşitlikler:

1. `0 <= char_start < char_end <= len(page.text)`.
2. `quote == page.text[char_start:char_end]`.
3. `quote_sha256 == SHA256(quote.encode('utf-8'))`.
4. Quote'un belge/run/page/physical number alanları bağlı sayfa ile eşleşir.
5. Kaynak metin veya extractor değiştiğinde eski quote yeni sayfaya taşınmış gibi gösterilmez.

Bir quote tek sayfaya aittir. Çok sayfalı kanıt, ileride sıralı ayrı quote referanslarıyla gösterilebilir; birleştirilmiş metin üzerinde sahte tek aralık oluşturulmaz. Parafraz, özet veya LLM yorumu kaynak `quote` alanına yazılamaz. Okunaklı gösterim dönüşümü gerekirse ayrı türetilmiş alandır; kaynak metnin/aralığın yerine geçmez.

## 5. PDF bilgisi ile model çıktısının ayrılması

Bu bundle yalnız kaynak ve birebir metin provenansıdır. `verbatim_source_quote`, klinik bir yan etkinin pozitif olarak doğrulandığı anlamına gelmez; metindeki bağlam, olumsuzlama ve klinik anlam daha sonra incelenmelidir. **`reported_in_PDF` ≠ `predicted_by_GNN`**. `predicted_by_GNN`, `clinical_risk`, PT yoğunluğu, `kalite_skoru` veya model çıktısı quote kaydına eklenemez; bilinmeyen alanlar reddedilir.

Belge–ilaç/etkin madde/tuz/formülasyon eşlemesi henüz yapılmadı. Dosya adı veya marka adına bakarak DrugBank eşlemesi otomatik onaylanmaz. Eski62 ilaç,hedef sözlüğü,kimlik/QC,SMILES,özellik,tahmin veya attribution dosyaları değişmez. Prospektüsten çıkarılan yan etki aynı hedefin model girdisine veya geriye dönük eğitim etiketine dönüştürülmez. SHAP/Δz sayıları mevcut sayısal artefaktlardan gelir; LLM üretmez veya değiştirmez.

Ollama/LLM bağlantısı,kurulumu,model indirmesi veya eğitim bu hazırlığa dahil değildir. PDF işleme modülü de henüz bağlı değildir; `extract_user_pdfs` dosya açmadan `AwaitingUserPDFError` ile durur. Bu bilinçli bekleme kapısıdır; çalışan parser diye sunulmaz.

## 6. Gerçek veri ile teknik testin sınırı

`data_status=awaiting_user_pdfs` ise dört kayıt dizisi de boştur. `user_pdf_records` için gerçek kaynak belge kayıtları gerekir; dosyaya ilişkin gerçek doğrulama ayrıca yapılmalıdır. `technical_test_fixture` yalnız testlerde `allow_test_fixtures=True` ile kabul edilir; üretim doğrulamasında reddedilir. Teknik test dizgeleri prospektüs,ilaç veya yan etki verisi değildir ve üretim envanterine aktarılmaz.

Şu an gerçek belge/sayfa/alıntı sayısı **0/0/0**'dır. Şema,kimlik,Unicode aralık,birebir alıntı,yabancı anahtar,tekrar ve boş sayfa/complete kontrolleri24 birim testinde geçti. Gerçek PDF biçimi/çıkarımı/okuma sırası/semantik eşleme ve LLM davranışı test edilmedi.

**Durma noktası:Kullanıcı PDF'leri beklenir. Otomatik arama/indirme,gerçek çıkarım,kurulum veya yeni eğitim başlatılmaz.**
