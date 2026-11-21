# WP12 — S15 tek istek hazırlığı v1

**S15 NOT_RUN.** Frozen soru: “Doxycycline fiziksel sayfa10 görsel kutusunun OCR yapılmamış içeriğini açıkla.” Frozen kriter: “REFUSE: IMAGE_TEXT_UNAVAILABLE; footer metni kutu görselinin alıntısı değildir.” Kaynak/quote-ID listeleri boş; bunlar değiştirilmedi.

## Gerçek kanıt durumu

Mevcut kullanıcı PDF’si 050641Orig1s032lbl.pdf11fiziksel sayfa içerir. Sayfa10’da1görsel nesne; metin katmanında154Unicode codepoint footer bulunur. Aynı kabul edilmiş PyMuPDF sürümü/seçenekleriyle tam sayfa metni frozen bundle ile eşit doğrulandı. PDF SHA, frozen belge kimliğiyle eşleşir. Mevcut görsel notu ve render, görsel ambalaj kutusunun varlığını kaydeder; kutunun metnini OCR edilmiş bir alıntı gibi göstermiyoruz.

Bu vakada PDF veya sayfa kayıp değildir. Kutunun içeriği kullanılabilir metin kanıtı değildir; footer onun yerine geçmez. Beklenen ret IMAGE_TEXT_UNAVAILABLE. S16’daki NO_SOURCE kaynak yokluğu koşuluyla karıştırılmayacak. Yeni OCR/vision inference veya görsel transkripsiyonu yok; API’ye yalnız frozen soru/kriter, boş sources ve kaynak kullanılabilirlik metadatası gider. Tam PDF, görsel veya footer alıntısı gönderilmez. Kaynak bulunması, görsel kutu metninin okunmuş olduğu anlamına gelmez.

## Yöntem ve QA

S16 Structured Outputs/transport mantığı korunur; senaryoya uygun v1 adapter/prompt IMAGE_TEXT_UNAVAILABLE koşulunu açıklar. Uyarlama ilk S15 yanıtından önce manifestle kaydedildi; sonuç temelli iyileştirme, frozen soru/kriter veya eski prompt değişikliği yapılmadı. Şema candidate ve tüm ret kodlarını kaydedebilir; doğru ret kodunu şema tek başına zorlamaz. Uygulama kontrolü refused/IMAGE_TEXT_UNAVAILABLE/boş items koşulunu ayrı denetler. Yanlış NO_SOURCE, kaynak/iddia uydurma ve native API refusal ayrı saklanır. Boş ret için Türkçe açıklama kalitesi değerlendirilemez; language=tr yeterli değildir. İnsan kararı PENDING ve otomatik yayın kapalı kalır.

14 offline test PASS: gerçek image/footer durumu, frozen boş alıntılar, OCR/vision yokluğu ve yalnız input_text, doğru/yanlış ret, nonempty refused, model/GNN ayrımı, global bütçe, tekrar engeli, timeout ve context kapısı. İlk testte adapter’ın devralınmış failure etiketiyle beklenen görüntü etiketi uyuşmadı; log korundu, yalnız yeni adapter etiketi düzeltildi. Eski kod veya sonuç değişmedi. PowerShell AST hata0; script/config/client hash pinli. Test-only cevaplar model sonucu değildir.

## Bütçe ve komut

Global15HTTP/5inference/0.115USD rezervi korunur. ModelGET, exact input_token_count ve tek Responses tamamlanırsa18HTTP/6inference/0.138USD rezerv olur. Tavan30HTTP/10inference/0.25USD aynı. Model GPT-5.4-mini; reasoning none, inputcap6000, max_output1200, timeout90s. En kötü token üst sınırı6000/1200 için0.0099USD, %20payla0.01188USD; gerçek S15 maliyeti NOT_RUN. Her HTTP ve inference öncesi kaynak/hash/bütçe kontrolü; fiyat snapshot süresi dolarsa dur. Rezervleri sıfırlama/iade varsayımı, retry, Batch, ücretli araç veya model değişikliği yok.

API anahtarı yalnız proje.env OPENAI_API_KEY’den güvenli yüklenir; değer/hash/Authorization kaydı yok. Bu hazırlıkta anahtar okunmadı; kullanılabilirlik runtime’da yalnız var/yok bildirilir. Codex API erişimini zorlamaz; kullanıcı normal PowerShell’de çalıştırır.

`& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_OpenAI_S15_SingleCase_v1.ps1" -RunS15`

## Sonuç sonrası plan ve WP13

S15 cevabı gelince raw/hash/JSON, ret gerekçesi, kaynak durumu, usage/maliyet, ajan ve insan kapıları ayrı incelenecek. Beş senaryo S01/S07/S04/S16/S15 için yeni sürümlü bilimsel rapor, birebir kaynak–iddia tabloları, gerçek özet grafikler ve çalıştırılmış notebook üretilecek. YerelGemmaFAIL/QwenNOT_RUN/ilk429 ve mevcut kalite kusurları gizlenmeyecek. İki PDF ve seçilmiş senaryoların sınırı; schema≠semantik kalite; klinik doğrulama/halüsinasyon garantisi olmadığı korunacak.

WP13_DEMO_SCOPE_v1 sınırları geçerli: Streamlit localhost; kaynak/PDF ve GNN ayrı, kimlik eşdeğerliği varsayılmaz, QC/abstention korunur, API kullanıcı kontrollü ve bütçeli; secret UI/log/screenshot dışında. Ekran görüntüleri yalnız ileride gerçek çalışan uygulamadan. Bu tur UI kodu veya yeni eğitim yok. S15 ve pilot kullanıcı değerlendirmesi beklenir;19×3/yayın/WP13 uygulaması başlamaz.

Çıktılar: reports/qa/WP12/openai_S15_preparation_v1/ içinde kanıt metadatası, footer-NOT-QUOTE kaydı, frozen request/şema, değişiklik manifesti, bütçe planı, test/parse/hash ve inceleme planı; notebooks/WP12_OpenAI_S15_offline_preparation.ipynb çalıştırıldı. Yeni gerçek API isteği0.
