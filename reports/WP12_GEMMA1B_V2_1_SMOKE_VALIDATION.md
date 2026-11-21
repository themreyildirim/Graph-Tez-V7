# WP12 — Gerçek Gemma1B v2.1 smoke testinin bağımsız teknik doğrulaması

08.11.2026 · **TECHNICAL_SMOKE_VERIFIED.** Kullanıcının gerçek `20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586` çıktısı salt okunur incelendi. Ham durum SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW olarak değişmeden kaldı; bu yeni inceleme ayrı QA kaydıdır. Codex yeni API/inference/indirme yapmadı.

**Sonuç:** Sonraki kontrollü19×3 kaynaklı açıklama aşamasına geçiş için teknik smoke önkoşulu doğrulandı. Bu tur57 açıklama çalıştırılmadı. Her gerçek istekte mevcut kaynak/bağlam bağımlılıkları, tam prompt token bütçesi ve bellek kapıları uygulanmalı; insan semantik incelemesi ve yayın yasağı devam eder. Bu tek echo testi uzun kaynak bağlamı veya Türkçe özet kalitesini doğrulamaz.

## 1. Model ve dosya kimliği
Gemma tag'i request/response/pre-request tags/record içinde aynı: `gemma3:1b-it-q4_K_M`. API ve kaynak model digest'i **sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c**. Ayrı yerel wrapper SHA'sı **sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16**. Kimlik yardımcısı ve runner hash'leri sabit config ve gerçek record ile eşleşti. Küçük wrapper/kaynak dosyaları bağımsız tekrar hash'lendi; config ve ağırlık/template/lisans/params referansları aynı. GGUF ağırlıkları bu incelemede yeniden hash'lenmedi veya yüklenmedi.

Ollama servis sürümü0.40.6; gerçek kullanıcı PowerShell5.1.26100.9711, is_appcontainer=false. api/ps başlangıç yanıtı boş: test öncesinde yüklü model listesi yok. Bu kullanıcı ortamında başarılı çalışma kanıtıdır; önceki Codex AppContainer erişim reddi model arızasına dönüştürülmez.

## 2. Gerçek istek, şema ve tamamlanma
| Kontrol | Gerçek sonuç |
|---|---|
| HTTP |**200**|
| Tamamlama |**done=true; done_reason=stop**|
| assistant content |`{"probe":"WP12_GEMMA1B_SMOKE_V2"}`|
| Şema |object; required probe; tek enum sabiti; additionalProperties=false — **PASS**|
| prompt/output token |**41 / 19**;1536/384 bütçeleri içinde|
| Context/batch/seed |2048 /32 /20261108|
| Diğer sabit ayarlar |temperature0, think:false, stream:false, keep_alive0|
| İstemci ölçülen süre |6.816sn|
| Sunucu total/load süreleri |6.649 / 6.196sn|

`smoke_request.json` sabit v2 payload'u ile birebir içerik eşleştirmesinden geçti. `smoke_response_raw.json` strict JSON parse ile okundu; tekrar eden JSON anahtarına izin verilmedi. İstek içindeki gerçek JSON Schema, mevcut jsonschema kütüphanesiyle gerçek assistant content'e ayrıca uygulandı. Ham yanıtta ek düşünce/tool çıktısı yok; yalnız probe alanı var. Response created_at UTC zamanı, kayıtlı Europe/Istanbul başlangıç/bitiş aralığına düşüyor. Tam HTTP status ve tamamlanma bu kayıtta doğrudan mevcut; önceki UNKNOWN alanları geriye dönük değiştirilmedi.

Tek şemalı isteğin kabul edilmesi ve uyumlu tamamlanması doğrulandı. Genel şema uyumu, halüsinasyonsuz özet, klinik bilgi veya model risk skoru başarısı sonucu çıkarılmaz. Bu teknik içerik PDF alıntısı/MedDRA etiketi değildir. SHAP/Δz/GNN tahmini üretilmedi.

## 3. Gemma v2 bellek politikasına uygunluk
| Koşul | Gerçek değer | Karar |
|---|---:|---|
| İlk boş host RAM≥2,5GiB |2.794GiB|PASS|
|5 kararlı örnek: her biri≥2,5GiB |en düşük2.720GiB|PASS|
| Örneklerin kapsadığı süre≥4sn |4.053sn|PASS|
| İnference hemen öncesi boş RAM≥2,5GiB |2.737GiB|PASS|
| Başlangıç/hemen önce VRAM≥2048MiB |3935 /3935MiB|PASS|
| Başlangıç/kararlılık/hemen önce commit≥3GiB |tüm kayıtlı değerler uygun|PASS|
| Çalışırken host RAM≥1GiB uyarı sınırı |28 örnekte minimum**1.963GiB**|PASS|
| Son boş host RAM≥1GiB |2.694GiB|PASS|
| Çalışma sırasında minimum commit boşluğu |12.053GiB|Bilgi; başlangıç şartı da geçti|
| Son boş VRAM |3935MiB|Son nokta ölçümü|

**2,5GiB başlangıç kapısıdır; bütün çalışma boyunca uygulanmış alt sınır değildir.** Runtime örnekleri2,5GiB altına inse de kabul edilmiş1GiB uyarı sınırının üstünde kaldı; eşik değiştirilmedi.28 örnek host'un toplam kullanılabilir RAM'ini gösterir; kesin inference tepe RAM'i veya bütünü modele atfedilebilir kullanım değildir. Runtime GPU ölçümü yoktur: **tepe VRAM/CPU-GPU offload durumu UNKNOWN**. Başlangıç/son3935MiB'den “GPU kullanılmadı” veya kesin GPU tepe belleği çıkarılmaz. keep_alive0 bir istek ayarıdır; ayrı son api/ps cevabı olmadan servis residency hakkında ek kanıt üretilmez.

## 4. Tek inference ve yeni indirme denetimi
Kayıtta inference_attempts=1; bir sabit request dosyası ve bir tamamlanmış response var. Aynı hash'li runner tek PostAsync/api-chat çağrı noktası içeriyor; retry döngüsü yok. Önceki üç GET version/tags/ps metadata'dır, inference sayılmaz. Runner'da model pull/indirme endpoint'i/komutu yok; new_downloads/models_pulled0. Gemma, istek öncesi tags listesinde zaten mevcut ve modified_at04:02:20; test04:49'da yapıldı. Bu run ve betik kapsamında **tek inference/yeni indirme0** kanıtı tutarlı.

Bu sonuç sistem çapında paket yakalama veya başka istemcilerin sunucu erişim denetimi değildir. Kullanıcı sağladığı dosyaların hash'leri içerik tutarlılığı sağlar, gerçek process çalışmasını kriptografik olarak tasdik etmez. Bu sınır saklanır; global “hiçbir uygulama indirme yapmadı/başka istek yoktu” iddiası kurulmaz.

## 5. Hash, QA ve koruma
file_hashes.json içindeki7 ham dosya girdisi birebir doğrulandı; manifestin kendisi dahil **8 orijinal dosyanın** yeni SHA envanteri alındı ve inceleme sonunda aynı kaldı. Request SHA: `fa45aec665a391cf25e4a59adbe7175658684e92a0c4febfc3871f816f779cce`; response SHA: `17ca2b76168d95a565b3f3be6166aa0e4af8582285758c7a47ed52df5120783b`. Dondurulmuş19 senaryo ve kaynak sözleşmesi hash'leri config/record/gerçek dosya arasında eşleşti. Önceki3.482 proje dosyası korundu; eski başarısız denemeler başarıya çevrilmedi. run_status eski tam baytları saklanarak öne eklenir.

Mevcut inceleyici ve ikinci bağımsız kontrol aynı teknik sonuca ulaştı.9 gerçek-record regresyon testi ve12 mevcut inceleyici testi =**21 offline test** geçti; mutation testleri yalnız RAM kopyalarında yapıldı. Yeni model çalıştırılmadı. Notebook gerçek echo, kimlik/şema/bellek tabloları ve kayıtlı host RAM grafiğini içerir. Yeni QA: reports/qa/WP12/gemma1b_v2_1_smoke_validation_v1/; teknik sonuç validation_record.json içinde. Semantik PDF incelemesi NOT_TESTED; otomatik yayın yok.19×3, yeni eğitim ve WP13 başlatılmadan burada durulur.
