# WP12 — Gerçek S04: bilinmeyen sıklık ve kaynak/dil incelemesi

08.11.2026 · Europe/Istanbul. Kullanıcının çalıştırdığı tek gerçek S04 kaydı salt okunur incelendi. **Teknik PASS; kaynak/dil notları var; resmî insan kararı PENDING.** Yeni API, otomatik tekrar veya yöntem değişikliği yapılmadı.

| Alan | Doğrulanmış değer |
|---|---|
| Model | gpt-5.4-mini-2026-03-17 |
| Request-ID | req_c3a245f121c845278f2d0b2791aaf1b7 |
| HTTP / tamamlama | 200 / completed; üç HTTP adımı, tek inference |
| JSON Schema / uygulama | PASS / PASS |
| Input / cached / output / reasoning | 2828 / 0 / 776 / 0 |
| Toplam token | 3604 |
| HTTP üretim süresi | 5,203 saniye |
| Usage-token maliyeti | 0,005613 USD |
| Ham yanıt SHA-256 | acbafb53ffb8c937d5d1589a979d165b35ae654f94263b424653443b9edc6138 |
| İnsan QA / otomatik yayın | PENDING / kapalı |

## Kaynak ve bağımsız teknik kontrol

Kullanıcı PDF'si `data/user_pdfs/pil.502.pdf`, DB00199 kaynak bağlamında altı fiziksel sayfadır. PDF SHA-256 `1b8182521f1314c595451e14a881caa930ba8a5df3c99d468e50429d0e61533e`. Fiziksel4 ve5 tam sayfaları, kabul edilmiş aynı PyMuPDF sürüm/seçenekleriyle yeniden salt okunur kontrol edildi; tam metinler, üç alıntı aralığı ve hash'ler frozen kayıtlarla aynı. İki sayfanın gerçek render'ı ayrıca görsel incelendi. Kaynak anlamı/belge güncelliği/ürün–ana ilaç eşdeğerliği hash ile onaylanmış olmaz.

Soru, kabul kriteri, prompt, şema, kaynak kimlikleri, nitelemeler ve zorunlu bağlamlar S07 öncesinde hazırlanan S04 isteğiyle aynı. Tam kaynaklar3803karakterdir; örtüşme dahil sayımdır. Unknown alıntısı sayfa5 ve sayfa4 bağlamını korur. Tam PDF değil bu alıntılar gönderilmiş; model araç çağrısı yapmamış. `source_request.json` dosyasındaki serileştirme/satır sonu farkı içerik değişikliği değildir.

Ham HTTP/response dosyalarındaki20 kayıtlı hash, envanter, request/response-ID, tamamlama, raw→JSON, bağımsız schema/application, exact server precount ve usage/maliyet eşleşti. Modelin gerçekten ne döndürdüğü ham kayıttan doğrulandı; yeni inference yok. On sekiz ağsız test PASS. Bunlar kaynak anlamının tam doğru olduğunu kanıtlamaz; yanlış-anlam/doğru-ID test-only mutasyonu semantik kapının insan incelemesi gerektirdiğini gösterir.

## Gerçek açıklamalar — düzeltilmeden

### Item 1 — fiziksel sayfa 4

> 4. bölümde, tüm ilaçlar gibi bu ilacın da yan etki yapabileceği ve herkesin bunu yaşamayabileceği belirtiliyor. Acil tıbbi yardım gerektirebilecek erken belirtiler arasında nefes almada zorluk, bayılma, yüz/dudak/boğaz şişmesi, deri döküntüleri, büyük sıvı dolu kabarcıklar, yaralar/ülserler ve ağız ile boğazda ülserler sayılıyor; bunlar alerjik reaksiyon işaretleri olabilir.

Birincil kaynak: `quote:b4d0701dab56bb08e603b3cdf898cae091d46cd7810efd715287f39103996468`.

Ajan notu: Yan etki olasılığı, herkesin yaşamayabileceği ve acil doktor iletişimi bağlamı korunuyor. Ancak “erken belirtiler” kaynakta yok: zamanlamaya ilişkin ek niteleme. Bu gözlem yeni yan etki saptaması değildir; kaynak sadakati notudur.

### Item 2 — fiziksel sayfa 5

> 5. sayfada bölümün devamında daha ağır cilt reaksiyonları, ishal, karaciğer/safra kesesi sorunları ve torsades de pointes gibi ciddi durumlar da listeleniyor. Aynı devam bölümünde, 'Not known (frequency cannot be estimated from the available data)' ifadesiyle bazı yan etkilerin sıklığının mevcut verilerden hesaplanamadığı açıkça söyleniyor; bunun yanında bulantı/kusma, eozinofili, tinnitus, geri dönüşlü işitme kaybı, göğüs ağrısı, ateş, anormal kalp ritimleri, konfüzyon, anoreksi, nöbet, vertigo, halüsinasyon, kırgınlık, interstisyel nefrit, düşük tansiyon ve bulanık görme gibi etkiler örnekleniyor. Ayrıca işitme kaybının özellikle yüksek dozlarda veya böbrek problemi olan hastalarda görülebildiği not ediliyor.

Birincil kaynak: `quote:a27cf43f6de611a56aa38fad6f0fa93bcde99a4a82718f975a5d6cbfcd3dff85`.

Ajan notu: Yan etki örnekleri ve bilinmeyen sıklık aynı p5 kaynağında. İşitme kaybı geri dönüşlü; yüksek doz/böbrek koşulu ve olabilirlik mevcut. “usually associated” → “özellikle ... görülebildiği” birebir değil: usually/genellikle açık aktarılmamış. İshalin şiddet/uzama/kan-mukus nitelemeleri, ayrı püstüloz uyarısı, çocuklar ve raporlama özette yok; bunlar kapsam eksiklikleridir. “daha ağır” karşılaştırmasının referansı kaynakta açık değil. Tinnitus/vertigo gibi terimler hasta dili bakımından ayrıca değerlendirilmeli.

### Item 3 — fiziksel sayfa 5

> Aynı 5. sayfa devamında 'Other side effects of Erythromycin Tablets include' başlığı altında 'Not known (frequency cannot be estimated from the available data)' ifadesi tekrar veriliyor. Bu, ilgili yan etkiler için sayısal bir olasılık ya da yaygınlık oranı verilemediği anlamına gelir; metin sıklığı bilinmeyen etkileri listeler, ancak bunları yüzdeye, belirli bir oranlara ya da kesin yokluk ifadesine dönüştürmez.

Birincil kaynak: `quote:a606c2c9f5d1862695ef31567790df3a34d34aae6ccdd088097c63f2bb6865d8`.

Ajan notu: Mevcut verilerden sıklığın hesaplanamaması Türkçe açıklanmış; nadir/yaygın/yüzde veya kesin yokluk yapılmamış. İngilizce başlık/niteleme birebir alıntı olarak verilmiş, anlamı Türkçe açıklanıyor. “belirli bir oranlara” dilbilgisi sorunu. “tekrar” sözcüğü, aynı p5 metninin örtüşen alıntılarda bulunması nedeniyle bağımsız ikinci kanıt gibi okunmamalı.

Tam JSON mesajı `exact_model_message.txt` ve çalıştırılmış notebook'ta aynen gösterilir. Her item'ın tam birincil alıntısı, tüm atıfları ve nitelemeleri `source_claim_comparison.csv` / `agent_item_reviews.json` içindedir. Modelin Türkçesi sessizce düzeltilmedi. İngilizce başlıklar burada kaynak alıntısıdır; genel/klinik bir koşulun açıklamasız İngilizce bırakılmasıyla aynı değerlendirilmez.

## Bilimsel değerlendirme

Ana frozen S04 sorusunun bilinmeyen sıklık anlamı ve iki sayfa bağlamı korunuyor. Kaynak ne sıklık oranı veriyor ne de “nadir/yaygın” sınıfı sunuyor; model bunları eklememiş. Bununla birlikte kaynak sadakati bütün cümleler için kusursuz değildir: “erken belirtiler” zamansal nitelemesinin kanıtı yok; “usually associated” açık “genellikle ilişkili” yerine daha serbest aktarılmış. Bu nedenle teknik geçişi tam kaynak/Türkçe kalite onayı yapmıyoruz.

Item2'deki tıbbi terimler ve kısa anlatım hasta dili açısından değerlendirilmelidir. Bazı kaynak ayrıntıları özetlenmemiştir: ishalin şiddet/uzama/kan-mukus koşulları; ayrıca ciddi püstüloz reaksiyonunun kendi bilinmeyen sıklık uyarısı; çocuklar ve raporlama bölümü. Bunların tümünün sorunun gerektirdiği kapsamda zorunlu olup olmadığı insan değerlendirmesine aittir; frozen kriter sonradan genişletilmedi. Kaynakta olmayan yeni bir yan etki adı veya sayısal olasılık bu ajan okumasında gözlenmedi; bu ifade genel bir otomatik halüsinasyon tespit garantisi değildir.

Item atıfları sırasıyla1/2/3tür; birincil alıntı amaçları ve bağımlılıklar doğru. “Tekrar” sözcüğü örtüşen kaynak aralıklarını bağımsız yeni kanıt haline getirmemelidir. Klinik nedensellik, hasta güvenliği veya risk doğrulaması yapılmadı. SIDER unknown çiftleri negatif olarak yeniden etiketlenmedi; hiçbir model girdisi/etiketi/skoru oluşturulmadı.

## Token, maliyet ve bütçe

Sunucu önkontrol2828token ile gerçek usage input2828 eşit. Output776token tüm JSON/kimlik/açıklamayı içerir;1200 sınırının altında. Reasoning0 output'a tekrar eklenmedi. Input maliyeti0.002121USD, output0.003492USD; toplam0.005613USD. Standart input0.75 / cached0.075 / output4.50USD/milyon fiyatları [resmî model sayfasından](https://developers.openai.com/api/docs/models/gpt-5.4-mini) doğrulandı; frozen politikayla aynı. Vergi/fatura düzeltmeleri dahil değildir.

Bilinen completed S01+S07+S04 token maliyeti0.0112560USD. İlk429 usage/fatura bilinmediği için bu kesin toplam fatura değildir. Global sayaç eski9HTTP/3inference'dan12HTTP/4inference'a, operasyonel rezerv0.069'dan0.092USD'ye çıktı. Hiçbir eski rezerv silinmedi. Toplam tavan30HTTP/10inference/0.25USD olarak kaldı. Kalan kapasite yeni senaryo veya yeniden deneme izni değildir.

RAM/VRAM telemetrisi bu bulut isteğinde toplanmadı; NOT_COLLECTED. Süre tek gerçek ölçümdür; farklı senaryolarda model üstünlüğü veya çalışma kararlılığı sonucu çıkarılmaz. API anahtarı ve.env inceleme sırasında okunmadı, hash'lenmedi veya envantere alınmadı; yalnız kayıtlı var/yok beyanı vardır. Authorization başlığı kaydedilmedi.

## Kanıtlar ve durma noktası

Önceki GemmaV1/V2 başarısızlıkları, QwenNOT_RUN, ilk429, S01 ve S07 kayıtları aynen korundu. S07 kullanıcının tamTürkçe/atıf kalite itirazı ayrı beyanında kalır; resmî QA otomatik değiştirilmedi. Tarihsel S04 NOT_RUN hazırlık kayıtları silinmedi; bu yeni sürüm gerçek sonucu ayrıca ekler. Karşılaştırma tablosu farklı görev/yöntemleri içerir; kontrollü eş görevli model benchmark'ı değildir.

Çıktılar: `notebooks/WP12_OpenAI_S04_actual_response_review.ipynb` (çalıştırılmış), `reports/qa/WP12/openai_S04_actual_review_v1/` (ham yanıt referansı, birebir metin, kaynak/iddia CSV/JSON, test ve hash manifesti), `reports/figures/WP12/openai_S04_actual_review_v1/` (üç gerçek kaynak/yanıt karşılaştırması, usage/maliyet, atıf ağı). Şekiller yalnız gerçek dosyalardan üretilmiştir; metin sarma gösterim amaçlıdır.

**Öneri:** İnsan incelemesinde bilinmeyen sıklık anlamını, “erken” ekini, usually aktarımını, özet kapsamını, tam Türkçeyi ve item atıflarını ayrı değerlendir. Karar, inceleyici kimliği/rolü/tarihi ve run–response–item/quote kapsamıyla ayrı olay kaydına bağlanmalıdır. Bu rapor insan adına onay veya ret yazmaz. Tek vaka kalite notu genelleme/klinik doğruluk kanıtı değildir. Kullanıcı değerlendirmesini bekle; tekrar, başka senaryo,19×3, yeni yöntem/eğitim, otomatik yayın veya WP13 uygulaması başlatma.
