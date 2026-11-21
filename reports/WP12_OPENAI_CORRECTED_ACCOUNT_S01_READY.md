# WP12 — Doğru hesap için ayrı S01 yürütücüsü hazır

08.11.2026 — **NOT_RUN / kullanıcı normal PowerShell çıktısı bekleniyor.**

Kullanıcı önceki `credit_balance_exhausted` hatasının yanlış hesaptan oluşturulmuş key nedeniyle olduğunu bildirdi. Bu açıklama yeni ayrı kayıt olarak saklandı; önceki hata/QA/billing-stop/rezervler düzeltilmedi veya silinmedi. Hesap kimliği/bakiyesi bağımsız olarak sorgulanmadı. Proje .env içindeki OPENAI_API_KEY kullanılabilirliği yalnız **VAR** olarak doğrulandı; doğru hesabın kredisi için offline garanti verilmez.

**Aynı kalanlar:** gpt-5.4-mini; aynı V2 kaynak promptu ve API adapter v1 JSON Schema; S01 sorusu/kabul kriteri; DB00199; fiziksel1/6; iki tam537-karakter alıntı; 6000 input/1200 output sınırı, reasoning none;90s timeout; aynı kaynak/hash doğrulamaları; sınırlı dil uyarısı ve zorunlu insan semantik incelemesi. Yeni yöntem veya en iyi çıktı seçimi yoktur. Eski request byte/hash ve semantik bileşenler korunur.

**Açık teknik değişiklik:** Yeni yürütücü yalnız proje .env içindeki OPENAI_API_KEY alanını okur (`environ={}`); süreç ortamında kalmış eski key tercih edilmez. Anahtar değeri, prefix, uzunluk, fingerprint/hash, Authorization header veya gizli dosya hash'i kaydedilmez. Kimlik kaynağı değişikliği ayrı sürümlenmiştir. Eski client/security/adapter ve maliyet konfigürasyonu değiştirilmez.

**Eski blok ve yeni tek-deneme yetkisi:** Kullanıcı hesap düzeltmesi sonrası bir ek denemeyi açıkça yetkilendirdi. V1 billing-stop dosyası ve S01_attempt01 hâlâ salt okunur korunur; V1 yürütücüsü bloklu kalır. Yeni sürüm ayrı corrected-account scope'unda kendi atomik tek-attempt kilidini kullanır. İkinci çalıştırma ağ göndermez. Bu yeni deneme, başarısız v1 kaydının otomatik retry'si veya sıfırlanması değildir; insan tarafından yetkilendirilmiş ayrı altyapı-düzeltme denemesidir.

**Ortak bütçe:** Eski ve yeni ledger'lar her gerçek HTTP öncesi birlikte sayılır. Eski3 HTTP/1 inference rezervi ve$0,023 aynen taşınır. Yeni3 HTTP/1 inference tam giderse toplam6 HTTP/2 inference rezervi ve$0,046 olur. Bu rezerv gerçek ücret değildir; önceki gerçek maliyet UNKNOWN kalır. Aynı10 toplamHTTP/10inference, $0,24 operasyonel tavan ve<$0,25 hedef değişmez. Eski denemeye para iadesi varsayılmaz. İlk dört-vaka planının toplam HTTP kapasitesi artık daha azdır; kalan senaryolara otomatik izin verilmez.

Resmî standart fiyatlar tekrar doğrulandı ve aynı: input$0,75/cached$0,075/output$4,50/milyon. 6000+1200 en kötü token maliyeti$0,0099; %20 payla$0,01188. Eski konfigürasyonun24saat fiyat geçerliliği uzatılmadı; eskirse ağ öncesi durur. [OpenAI Docs model/fiyat](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

**Doğrulama:**18 yeni offline regresyon testi PASS. Eski dosyaların değişmezliği, global iki-scope bütçesi, `.env` tek-kaynak seçimi, AppContainer engeli, bir inference sınırı, ikinci çalıştırma blokajı, timeout/429 gizlemeden saklama, token sınırı ve key yansıtması kontrolleri kapsandı. Fake model yanıtları yalnız TEST_ONLY fixture'dır, gerçek başarı sonucu değildir. PowerShell parser ve policy/client hash pinleri QA'da doğrulanır. Önceki66 kamusal kabul edilmiş artifact/kayıt/control hash'i korunur; gerçek gizli dosyalar bu listeye alınmaz. Önceki35 ve9 test logları değiştirilmez.

**Kullanılacak yeni komut** (.env güncellendikten sonra normal kullanıcı PowerShell'i):

```powershell
& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_OpenAI_CorrectedAccount_S01_v1.ps1" -RunS01
```

Yeni çıktı dizini `reports/qa/WP12/openai_corrected_account_user_runs_v1/` olur. Flag olmadan yalnız key VAR/YOK offline durumudur. Codex gerçek API çağırmadı; AppContainer ağ kısıtını aşma yoktur. Kontroller geçerse yalnız bir kaynaklı üretim isteği gönderilir, otomatik tekrar yoktur. Ham yanıt, request-ID/model-ID, HTTP/completion, quote/prompt/hash, schema, kullanım ve maliyet dosyaları aynı v1 güvenlik yazıcısıyla saklanır; ayrıca global bütçe ve gerçek transport-attempt kayıtları eklenir.

Gerçek cevap henüz olmadığı için yeni Türkçe/kaynak sadakati/ücret sonuçları NOT_RUN; önceki GemmaV1/V2 FAIL ve QwenNOT_RUN aynı kalır. JSON geçişi semantik başarı değildir. İlk gerçek çıktı klasörü geldikten sonra kaynak/PDF, Türkçe, ret/kapsam, yapı, token/cache/reasoning ve maliyet ayrı raporlanacak; insan incelemesi PENDING kalacak.19×3, otomatik yayın, yeni eğitim ve WP13 yoktur.
