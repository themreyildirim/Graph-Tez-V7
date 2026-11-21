# WP12 — Ayrı OpenAI API kaynaklı açıklama adaptörü v1

Durum: **OFFLINE_PREPARED / gerçek API NOT_RUN / ilk istek öncesi kullanıcı onayı bekleniyor.** Bu belge mevcut aktif yol haritasındaki WP12 açıklama katmanının sağlayıcı adaptörüdür. Yeni yol haritası, eğitim veya WP13 değildir. Yerel Gemma V1/V2 başarısızlıkları ve Qwen NOT_RUN kaydı değişmez.

## 1. Önceden belirlenen kapsam

İlk vaka yalnız S01: “Ürün ve formülasyon kaynakta nasıl tanımlanıyor?” Aynı dondurulmuş soru, kabul kriteri, Erythromycin DB00199 ana ilaç kimliği, fiziksel sayfa 1 ve6, iki quote-ID ve537 karakterlik tam alıntı korunur. Ana ilaç kimliği ürün/tuz/doz/formülasyon eşdeğerliğini kanıtlamaz. Yeni etiket, MedDRA kavramı, GNN skoru, SHAP, Δz veya tedavi önerisi üretilemez.

Bulut pilotu, aynı S01 üzerinde yerel yöntem geliştirme sonuçları görüldükten sonra açılmıştır. Tek vaka başarısı bağımsız genelleme, klinik doğruluk veya nedensellik kanıtı olmayacaktır. Yanıtlar otomatik yayımlanmaz.

İlk vaka değerlendirilmeden diğer vakalar yetkili değildir. Sonuç öncesi hazırlanan küçük aday plan S01, S04 (bilinmeyen sıklık), S07 (tetracycline sınıfı/BUN istisnası) ve S17 (yasak skor/etiket görevi) içerir. Dondurulmuş19 senaryo aynen korunur; dört vaka bu listenin alt kümesidir. İleride de en fazla10 inference; bu sürüm daha tutucu olarak metadata ve token sayımı dahil toplam10 HTTP çağrısını sınırlar. Dört vakalık olası plan1 model GET +4 sayım +4 inference =9 HTTP'dir. Diğer üç vaka için yürütme döngüsü bu sürümde yoktur.

## 2. Model ve şema

İstenen model `gpt-5.4-mini`; kabul edilen yanıt kimlikleri bu alias ve resmî `gpt-5.4-mini-2026-03-17` snapshot'ıdır. Belgelerde Responses/Structured Outputs ve reasoning `none` desteği doğrulandı. Hesaba özgü erişim henüz **PENDING**: normal kullanıcı yürütücüsü önce model GET, sonra tam istek için token sayımı yapar. Başka modele otomatik geçilmez. [Resmî model belgesi](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

API adaptörü kökte `{"result": ...}` nesnesi kullanır. Onaylı S01 V2 aday nesnesi `result` altına taşınır; `oneOf` → iç içe `anyOf`, `const` → tipli tek-değer `enum`; `$schema` ve `uniqueItems` API şemasından çıkarılır. Bütün object alanları required, `additionalProperties=false` olur. Dallar farklı statement_kind/quote-ID sabitleriyle ayrık olduğundan S01 anlamı korunur; dönen iç nesne ayrıca özgün V2 doğrulayıcıdan geçirilir. Kök union ve desteklenmeyen koşullu anahtarlar yoktur. Bu bir API-adapter değişikliğidir; eski V2 şema/prompt dosyaları değiştirilmez. [Structured Outputs kapsamı](https://developers.openai.com/api/docs/guides/structured-outputs).

Özgün V2'nin bu hazır/okunabilir S01 bağlamına özel sözleşmesi yalnız candidate kabul eder: boş item veya gerekçesiz uygulama reddi geçmez. Genel V2 ret mantığı değiştirilmez. API'nin kendi güvenlik refusal çıktısı ayrı **API_NATIVE_REFUSAL** olarak saklanır; JSON şemasından geçmiş veya semantik başarılı sayılmaz. Kimlik/formülasyon birincil alıntı eşleşmeleri ve iki amacın kapsanması ayrıca doğrulanır.

Sistem yönergesi gerçek Türkçe cümle ister. `language=tr` beyanı dil başarısı değildir. Mevcut sınırlı dil uyarısı İngilizceyi kaçırabilir; insan dil/kaynak incelemesi zorunlu kalır. `reported_in_PDF` yalnız doğrulanmış kaynak zarfıdır; `predicted_by_GNN` NOT_REQUESTED/null kalır. LLM'ye GNN girdisi, PT sözlüğü veya model çıktıları gönderilmez.

## 3. Anahtar, gönderim ve gizlilik

Anahtar yalnız süreç `OPENAI_API_KEY` ortam değişkeninden, yoksa kök `.env` içindeki aynı değişkenden `python-dotenv` ile alınır. İnterpolasyon ve diğer dotenv alanlarını ortama yükleme yoktur. Kullanılabilirlik yalnız boolean'dır. Gerçek değer; argv, terminal, notebook, rapor, JSON, CSV, hata mesajı ve hash manifestine girmez. Authorization başlığı bellekte HTTP için oluşturulur; başlıklar kaydedilmez. Anahtarın kendisi hash'lenmez.

`.env`, `.env.*`, `.env*` ve yaygın özel anahtar dosyaları `.gitignore` kapsamındadır. Kök mevcut durumda Git deposu değildir; ignore davranışı ayrı geçici Git deposunda test edilir. Çalıştırma öncesi Git deposu varsa izlenen özel dosya denetimi yapılır. Hiçbir gerçek gizli dosya içerik envanterine/hash taramasına dahil edilmez. Kimlik doğrulama hatası anahtarı geri yansıtabileceğinden HTTP hata gövdesi/metni saklanmaz; yalnız güvenli error-code/type/param, durum ve request-ID tutulur. Başarılı ham yanıtlar aynen saklanır; beklenmedik anahtar yansıtması algılanırsa yazım/hash durur.

Gönderilecek tam kaynak metni ve kimlikleri `outbound_disclosure_S01.json` içindedir. Tam PDF, proje klasörü, model dosyası veya yerel dosya yolu gönderilmez. Seçilmiş aynı iki alıntı hem token-sayım endpoint'ine hem inference endpoint'ine iletilir; bu iki dış aktarım açıkça kaydedilir. `store=false` kullanılır; bu alan sağlayıcının bütün saklama politikaları için ayrıca sıfır-saklama garantisi değildir.

## 4. Dondurulmuş maliyet kapısı

| Alan | Sınır/karar |
|---|---|
| Resmî standart fiyat /1M token | input $0,75; cached input $0,075; output $4,50 |
| Giriş sınırı | Sunucu tam sayımında en çok6000 token; sessiz kesme yok |
| Çıkış | `max_output_tokens=1200`; muhakeme dahil toplam çıkış sınırı |
| Muhakeme | `effort=none`; varsa usage muhakeme sayısı ayrı kaydedilir |
| En kötü inference token maliyeti | 6000×0,75/1M +1200×4,50/1M =$0,0099 |
| %20 planlama payıyla | $0,01188; ön hesapta cache indirimi varsayılmaz |
| Kalıcı inference rezervi | Deneme başına $0,02; başarısızlıkta iade edilmez |
| İlave HTTP rezervi | Her HTTP için $0,001; metadata/sayımın gerçek faturası olarak sunulmaz |
| En fazla rezerv | 10×0,02 +10×0,001 =$0,21; operasyonel tavan $0,24; hedef <$0,25 |
| Bu sürüm | Yalnız1 inference; S01 proje-geneli tek-attempt slotu |
| Fiyat geçerliliği | Doğrulama anından24 saat; eskiyse ağ başlamadan dur |

Fiyat kaynağı [resmî model sayfasıdır](https://developers.openai.com/api/docs/models/gpt-5.4-mini). Çıkış sınırı görünür metinle birlikte muhakeme/invisible tokenları kapsar; reasoning sayısı output toplamına ikinci kez eklenmez. [Responses create sözleşmesi](https://developers.openai.com/api/reference/resources/responses/methods/create).

İlk inference öncesi tam model/instructions/input/schema ile `/v1/responses/input_tokens` sayımı yapılır. Özel çevrimiçi tokenizer indirimi veya yerel yaklaşık token sayısıyla kapı açma yoktur. Sayım başarısızsa, üst sınır aşılırsa veya kaynak hash'i değişirse inference yoktur. [Resmî token sayım endpoint'i](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count).

Usage tabanlı token maliyeti: `((input−cached)×0,75 +cached×0,075 +output_total×4,50)/1M`. Cached-token alanı yoksa sıfır varsayılmaz; maliyet UNKNOWN ve yeni istek kapalıdır. Başlatılmış inference timeout'unda maliyet bilinmiyorsa kalıcı billing-stop oluşur. Vergi/fatura düzeltmeleri bu token tahmininin dışındadır; $5 bakiye kullanıcı beyanıdır, hesap bakiyesi sorgulanmadı. Rezervler küçük pilotun token bütçe kontrolüdür; sağlayıcı faturası için garanti değildir.

## 5. Yürütme ve kanıt

Transport yalnız sabit `https://api.openai.com/v1` ve üç izinli endpoint'i kabul eder; standart TLS, redirect/proxy kapalı, tek deneme,90s timeout. Yeni paket/SDK kurulmaz. Web/file search, Batch, ek model, ücretli araç veya otomatik retry yoktur. AppContainer tespit edilirse ağ çağrısı yapılmadan durur. Normal kullanıcı PowerShell'i mevcut ağ kısıtını aşan bir Codex işlemi değildir; kullanıcı kendi oturumunda çalıştırır.

Her başarılı yanıtta tam dönen model kimliği, request/response-ID, HTTP ve completion durumu, ham gövde, doğrulanan JSON, prompt bileşen/source hash'leri, sunucu token sayımı, gerçek usage, cache/muhakeme ayrımı, tahmini token maliyeti ve süre saklanır. Schema, uygulama, dil, kaynak sadakati, yanlış ret/kapsam ve insan onayı ayrı alanlardır. Yapısal geçişten sonra kaynak sadakati ve insan incelemesi **PENDING** kalır.

**Durma noktası:** Kullanıcı ilk gerçek isteği onaylamadan `-RunFirstCase` çalıştırılmaz. Onay sonrası tek S01 denemesi biter; otomatik ikinci vaka/tekrar yoktur. Oluşan klasör `reports/qa/WP12/openai_api_user_runs_v1/` altında kullanıcı tarafından paylaşılır. Hata durumunda slotlar elle silinerek yeniden deneme yapılmaz; önce gerçek kanıt incelenir.
