# WP12 — İki gerçek Gemma1B v2 denemesinin hata incelemesi

08.11.2026 · **READ_ONLY_DIAGNOSIS_COMPLETE — NO_RETRY.** İki deneme de aynı digest kontrolünde durdu. Gerçek neden kayıtlarda açık: `System.Management.Automation.RuntimeException: MODEL_DIGEST_MISMATCH: do not silently switch model`. Timeout veya model inference başarısızlığı teşhisi yoktur.

Önceki betikte API model digest'ini yerel sarmalayıcı manifest dosyasının hash'iyle eşleştirmiştim. Bu iki farklı kimliği aynı kontrol alanında kullanmam yanlıştı. Önceki v2 betiği ve deney kayıtları bu incelemede değiştirilmedi; gereken düzeltme aşağıda yalnız öneri olarak kaydedildi.

## 1. Her denemenin ayrı sonucu
| Kontrol | Deneme1 —04:28:56 | Deneme2 —04:29:06 |
|---|---|---|
| Tam run ID |20261108_042856_aa8562b748f84e2e997f898e2001b6e7|20261108_042906_1ffecdc7c9e64cc1bee7dee3c5263a30|
| Betik başlangıç/bitiş |2026-11-08T04:28:56.1616157+03:00 / 2026-11-08T04:28:57.4762293+03:00|2026-11-08T04:29:06.0194432+03:00 / 2026-11-08T04:29:06.6815212+03:00|
| Toplam duvar saati süresi |1.315sn|0.662sn|
| Kaydedilen genel durum |FAILED_OR_TIMED_OUT_NO_RETRY|FAILED_OR_TIMED_OUT_NO_RETRY|
| Gerçek exception |MODEL_DIGEST_MISMATCH|MODEL_DIGEST_MISMATCH|
| Hata aşaması |Digest kontrolü; API ps/bellek kapısı/chat öncesi|Aynı aşama|
| Non-AppContainer kullanıcı ortamı |is_appcontainer=false|is_appcontainer=false|
| Ollama servis erişimi |GET version ve tags yanıtları mevcut; servis0.40.6|GET version ve tags yanıtları mevcut; servis0.40.6|
| Metadata HTTP tam status |**UNKNOWN — kaydedilmemiş**|**UNKNOWN — kaydedilmemiş**|
| Smoke HTTP status |N/A — istek gönderilmedi|N/A — istek gönderilmedi|
| Timeout aşaması |Ulaşılmadı; açık guard exception'ı|Ulaşılmadı; açık guard exception'ı|
| Kaydedilen inference_attempts |0|0|
| Bu betikten model yükleme isteği |Gönderilmedi|Gönderilmedi|
| Sunucuda önceden yüklü model durumu |**UNKNOWN**; api/ps cevabı yok|**UNKNOWN**; api/ps cevabı yok|
| İlk boş RAM |2.404907GiB; açık 97.375MiB|2.395996GiB; açık 106.500MiB|
| İlk boş VRAM |3935MiB;2GiB koşulu uygun|3935MiB;2GiB koşulu uygun|
| İlk commit boşluğu |13.750GiB;3GiB koşulu uygun|13.753GiB;3GiB koşulu uygun|
| Betiğin bellek kapısı çalıştı mı? |**Hayır**, önce digest guard attı|**Hayır**, önce digest guard attı|
| İlk ölçümden bağımsız yeniden hesap |RAM koşulu **FAIL**|RAM koşulu **FAIL**|
|5 kararlı örnek/hemen önce ölçüm |Alınmadı|Alınmadı|

Her klasörde yalnız file_hashes.json, metadata_1_version.json, metadata_2_tags.json, run_record.json var. Manifest başına3 içerik girdisi; iki klasörde toplam8 gerçek dosyanın bayt/hash'leri korundu. metadata_3_ps, smoke_request, smoke_response ve memory_samples dosyaları yok. Bu yokluk tek başına değil, run_record inference0/exception ve **aynı SHA'lı betiğin kontrol akışıyla birlikte** gönderilmemiş chat isteğini doğruluyor.

`FAILED_OR_TIMED_OUT_NO_RETRY` genel catch etiketidir; içinde “TIMED_OUT” bulunması timeout kanıtı değildir. Yaklaşık1,315sn/0,662sn toplam süre HTTP gecikmesi veya model yükleme süresi değildir. Burada açıkça digest guard atılmış;60sn timeout'a dayalı hata yoktur. Genel `server_completion_if_request_started=UNKNOWN_ON_CLIENT_ERROR` metni koşullu boilerplate'tir; bu kayıtlarda istek başlamamıştır.

GetStringAsync başarılı gövde dönüşünde2xx başarı sınıfını sağlar, fakat betik tam HTTP status kodunu saklamamış. Bu nedenle200 diye doldurmadık. [Microsoft GetStringAsync açıklaması](https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpclient.getstringasync). Servis erişiminin çalışması, Gemma modelinin yüklendiği veya JSON Schema inference desteğinin sınandığı anlamına gelmez.

## 2. Digest uyuşmazlığının kesin açıklaması
| Kimlik | Değer |
|---|---|
| Betiğin beklediği yerel sarmalayıcı dosya SHA |sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16|
| Her iki gerçek API tags cevabının model digest'i |sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c|
| Yerel sarmalayıcının içerdiği üst manifestin doğrulanmış SHA'sı |sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c|

İki gerçek API yanıtı tam aynı Gemma tag'ini, family=gemma3,999.89M,Q4_K_M ve9755… digest'ini döndürüyor. [Ollama tags API](https://docs.ollama.com/api/tags) bu alanı model metadata'sının parçası olarak sunar. Yerel313f… dosyasının içindeki9755… manifesti küçük metadata dosyasından yeniden hash'lendi; config ve ağırlık/template/license/params layer listelerinin birebir aynı olduğu doğrulandı. Model ağırlıkları yeniden yüklenmedi veya inference yapılmadı.

Dolayısıyla bu kayıtlarda **farklı hash nesnelerinin karşılaştırıldığı** kanıtlıdır. Bundan bütün Ollama sürümlerinin her zaman aynı digest normalizasyonunu yaptığı genellemesi çıkarılmaz. Modelin bozuk olduğu, değiştirilmesi/yeniden indirilmesi gerektiği veya AppContainer10013 hatası bu iki denemenin nedeni olduğu iddia edilmez. Kaydedilmiş hata yerel kullanıcı ortamında digest guard'dır.

## 3. En küçük gerekli düzeltme — uygulanmadı
Kimlik kontrolünü kaldırmadan iki alanı ayrı tutmak gerekir:

```text
local_wrapper_manifest_file_sha256 = sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16
expected_API_model_digest         = sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c
```

Gelecekte yalnız kimlik bağlama düzeltmesi olarak runner/config/inceleyicinin API digest alanı9755… ile eşleştirilir;313f… yerel dosya bütünlüğü alanında korunur. Sarmalayıcı→kaynak manifest→aynı layer zinciri ayrıca denetlenir. Rastgele digest kabulü, kontrolü kaldırma veya model değiştirme yoktur. Ayrı öneri `minimal_correction_PROPOSED_ONLY.json` içindedir. Bu tur aktif betiğe/config'e/inceleyiciye düzeltme uygulanmadı, yeniden çalıştırma komutu verilmedi.

**Bu düzeltme tek başına smoke testini başlatmaya yetmez.** İlk ölçümler2,404907GiB ve2,395996GiB; v2 RAM tabanı2,5GiB'nin sırasıyla97,375 ve106,500MiB altındadır. Aynı başlangıç değerleriyle digest düzeltmesinden sonra bellek kapısı da durdururdu. Bu, kaydedilmiş ölçümlere dayalı koşullu hesap; ilerideki boş RAM tahmini değildir. Eşiklerin veya timeout'un değiştirilmesi için bu hatalar gerekçe oluşturmaz. Modelin gerçekten çalışıp çalışmayacağı ve tepe belleği **UNKNOWN/NOT_TESTED** kalır.

## 4. QA, koruma ve durma
8 offline test: iki gerçek manifest, aynı betik SHA'sı, doğru hata aşaması, timeout ayrımı, gönderilmemiş inference, bilinmeyen sunucu residency'si, yeniden hesaplanan bellek, uydurulmayan HTTP status ve farklı hata/sürümde otomatik teşhis reddi. Önerilen kaynak digest eşleşmesi yalnız offline sınandı; hiçbir HTTP isteği gönderilmedi.

Notebook iki gerçek kaydı, bellek farklarını, digest zincirini ve test çıktısını kod altında gösterir. Önceki3.432 proje dosyası başlangıç hash kaydıyla korunur; iki ham deneme klasörü değiştirilmedi. run_status eski tam baytlarını saklayarak güncellenir. Yeni model/PDF indirme, servis/süreç müdahalesi, timeout/eşik değişimi, inference,19×3, yeni eğitim veya WP13 yoktur. İnceleme burada biter.
