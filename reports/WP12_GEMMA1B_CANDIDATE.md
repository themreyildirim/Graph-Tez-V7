# WP12 — Gemma3 1B ayrı aday ve koşullu çalışma v1

**LOCAL_CACHE_VERIFIED — AWAITING_USER_HOST_METADATA_AND_TECHNICAL_SMOKE.** Kullanıcı yeni adayı seçti: `gemma3:1b-it-q4_K_M`. Codex indirme, Ollama API çağrısı veya inference yapmadı. Qwen3 4B modeli/kayıtları ve WP00–WP12 sonuçları silinmedi/değiştirilmedi.19 dondurulmuş senaryo, AGENTS, ROADMAP ve PDF sözleşmeleri korundu.

## 1. Gerçek model kimliği ve digest ayrımı
Yerel tam tag önbelleği zaten mevcut bulundu. Bu gözlem, indirmeyi Codex'in yaptığı anlamına gelmez; kullanıcı teslim olayı veya API doğrulaması uydurulmadı. Bloblar1MiB parçalarla hash'lendi, model inference için yüklenmedi. Config dahil6 dosyanın boyut ve tam SHA-256 kontrolleri geçti.

| Alan | Gerçek kayıt |
|---|---|
| Yeni aday ID | WP12-gemma3-1b-it-q4_K_M-candidate-v1 |
| Seçilen tag | gemma3:1b-it-q4_K_M |
| Yerel manifest tam digest | sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16 |
| İçerilen üst kaynak manifesti | sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c |
| Model katmanı digest | sha256:2f8c3d137f2496dcb4019e17a50f2974b89c1be1a742db3c80cc86f91cafeeef |
| Ağırlık katmanı | 806.058.400bayt ≈0,751GiB; Q4_K_M |
| Yerel config | gemma3;999.89M;GGUF; requires0.30.0 |
| Kullanıcı API'sinin bildirdiği digest | **PENDING**; Codex yerel servise bağlanmadı |

Yerel manifestin digest'i313f… ile içindeki üst manifestin9755… digest'i farklı kayıt nesnelerinin hash'leridir; birbirinin yerine yazılmaz. Yerel manifest üst manifesti ayrı bir layer olarak içerir. Üst manifestte aynı ağırlık/template/license/params bağlantıları ve runner=llamacpp bulunur. Bütün ilgili dosyaların hash'leri doğrulandı. [Resmi tam tag sayfası](https://ollama.com/library/gemma3:1b-it-q4_K_M)806MB/Q4_K_M ve97558784bdc9 kısa kaydını gösteriyor. Yerel tam kimlik ayrı saklandı; dosya tutarlılığı yayıncı özgünlüğü/klinik doğruluk onayı değildir.

Koşullu smoke betiği API'de **yerel tam digest'in** aynısını arar. API farklı bir digest döndürürse önce metadata kaydı incelenir; sessizce9755… veya başka bir tag'e geçilmez, inference yapılmaz. Yerel config'in requires0.30.0 şartı da kontrol edilir. Önceki kullanıcı Qwen kaydındaki servis0.40.6 tarihsel bilgidir; yeni Gemma çalışmasında sürüm tekrar alınacaktır. Resmi aile sayfasındaki genel0.6+ bilgisi bu gerçek artefaktın0.30.0 config şartının yerine geçirilmez.

## 2. RAM/VRAM yeniden değerlendirmesi
Güncel salt okunur ölçüm: **2026-11-08T04:05:00.340385+03:00**; toplam RAM7.42GiB, boş RAM**1.02GiB**, kullanım%86.3. GPUNVIDIA GeForce GTX 1650 Ti, toplam4096MiB, boş**3935MiB**. Bu tur yerel API bağlantısı denenmedi.

Gemma ağırlık katmanı≈0,751GiB; mevcut Qwen4B'nin önceden doğrulanmış2.497.280.480bayt katmanı≈2,326GiB. Ağırlık farkı≈1,575GiB'dir; bu değer **ölçülmüş RAM/VRAM tasarrufu değildir**. KV cache,2048context, motor çalışma alanı, host/GPU kopyaları ve diğer süreçler ek bellek gerektirir. Dosya boyutundan kesin çalışma belleği hesaplanmadı. Daha küçük model için Türkçe kaynak sadakati/negasyon başarısı garanti edilmez.

**3GiB boş host RAM ve2560MiB (2,5GiB) boş VRAM tabanı aynen korunmuştur.** Daha düşük eşik önerilmedi; bu sürüm eşik gevşetmesi değildir. Sebep: bu makinede gerçek Gemma tepe belleği henüz ölçülmedi, son RAM ölçümü tabanın altında ve yalnız ağırlık boyutuna bakarak güvenlik payını küçültmek için kanıt yok. İleride alt eşik gerekirse yeni, açık karar sürümü gerekir; mevcut betikte bypass/override parametresi yoktur. Tabanın sağlanması da sığma garantisi değildir. [Ollama context belgesi](https://docs.ollama.com/context-length) büyüyen bağlamın bellek maliyetini açıklar; ilk smoke context2048 kalır.

## 3. Bağımsız kullanıcı PowerShell akışı
Gemma cache'i mevcut olduğu için yeniden indirme talep etmiyoruz. Kullanıcı kendi PowerShell'inde gerekirse yalnız seçilmiş tag'i indirir (`ollama pull gemma3:1b-it-q4_K_M`); bu komut **Codex tarafından çalıştırılmadı**, betik de pull/install içermez. Qwen için remove/rm komutu yoktur.

Önce yalnız metadata ve bellek kontrolü:

```powershell
& 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_Gemma1B_UserPowerShellSmoke_v1.ps1'
```

Koşullar sağlanınca yalnız tek teknik JSON Schema smoke testi:

```powershell
& 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_Gemma1B_UserPowerShellSmoke_v1.ps1' -RunSmoke
```

Yeni betik Qwen betiğinden ayrı, sürümlü bir dosyadır; eski dosya ezilmedi. Model/tag/digest, teknik probe, kayıt dizini ve minimum artefakt sürümü farklıdır; eşikler, context2048, çıktı384, seed20261108, sıcaklık0, stream:false, think:false ve keep_alive0 korunur. Modellerde thinking desteği aynı varsayılmaz: API bu alanı reddederse hata aynen kaydedilir; alanı kaldırıp sessiz fallback yoktur. Yeni örnek arama/hiperparametre optimizasyonu yapılmaz.

Normal kullanıcı PowerShell'i/non-AppContainer; yalnız127.0.0.1; proxy/redirect kapalı; servis başlatma/guvenlik değişikliği yok. API version/tags/ps metadata alınır; farklı digest veya yüklü model varsa otomatik değişiklik yapılmadan durulur. RAM/VRAM inference'tan hemen önce tekrar ölçülür. En çok bir istek,60sn istemci timeout'u; timeout sunucu tamamlanmasını kanıtlamaz ve otomatik retry yapılmaz. Host RAM örnekleri ve başlangıç/son GPU ölçümleri kaydedilir; kesin tepe bellek veya genel kalite iddiası yapılmaz.

Bu, klinik içeriksiz **WP12_GEMMA1B_SMOKE_V1** echo testidir; gerçek PDF açıklaması değildir. Şema kontrollü tek yanıtın tutarlılığını sınar. Başarı,19×3 için otomatik izin veya kaynak anlam sadakati kanıtı olmayacaktır. `reported_in_PDF`/`predicted_by_GNN` ayrımı,44 alıntı ve insan semantik inceleme şartı değişmez. Sahte prospektüs, yeni MedDRA/yan etki, model skoru, SHAP veyaΔz üretilmez.

## 4. Ayrı gerçek çıktı ve inceleme kaydı
Betik her denemeyi reports/qa/WP12/gemma1b_user_smoke_runs/tarih_GUID altında yeni kayda yazar. Ham metadata, sabit istek SHA, gerçek yanıt varsa ham yanıt ve bellek örnekleri korunur. Henüz Gemma gerçek API/çıkarım sonucu yoktur; conditional_run_record.json sonuçnull ile bekler.

Kullanıcı oluşan tam klasör yolunu paylaştığında ağsız doğrulayıcı kullanılabilir:

```powershell
python 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\wp12_gemma_smoke_review.py' '<gerçek Gemma çıktı klasörü>'
```

Doğrulayıcı yalnız Gemma dizinini/modelini/digest'ini kabul eder; Qwen çıktısını Gemma gibi sunmaz. Yeni inceleme kaydı gemma1b_user_smoke_reviews/UUID altına yazılır; eski ham kayıtlar değişmez. Dosya hash'i tutarlılık sağlar, gerçek çalışmanın kriptografik tasdiki değildir. İnsan semantik onayı veya otomatik yayın yoktur.

## 5. Önceki kullanıcı Qwen kayıtlarının verdiği ek kanıt
Önceden normal PowerShell'de oluşturulmuş **2 gerçek Qwen kayıt** bulundu ve dosya manifestleri doğrulandı. İkisinde de **is_appcontainer=false**, servis0.40.6, exact Qwen digest ve STOP_MEMORY_GATE/inference0 görülüyor. Bu nedenle eski bekleme kaydı tarihsel haliyle korunurken yeni ek kayıtta kullanıcı API erişiminin çalışmış olduğu belirtilir. Bu, Codex10013 ile kullanıcı ortamını ayıran kanıttır; belirli firewall kuralı veya Gemma inference başarısı kanıtı değildir. Eski kayıtların/modelin hiçbirini silmedik/değiştirmedik.

## 6. QA ve durma noktası
Gemma betiği yalnız PowerShell AST ayrıştırmasından geçer; burada çalıştırılmaz.12 Gemma doğrulayıcı testi +12 Qwen doğrulayıcı +6 bellek +24 kaynak sözleşmesi =54 offline test; teknik fixture'lar gerçek LLM çıktısı değildir. Yeni Gemma kodu sürümlü fork olarak kayıtlı; kabul edilmiş eski kodların refaktörü/üzerine yazılması yoktur.

Önceki3.372 proje dosyası (gerçek kullanıcı Qwen çıktıları dahil),19 senaryo ve bütün sözleşmeler başlangıç SHA ile korunur. Qwen cache manifesti0edc… aynı kalır; büyük Qwen ağırlıkları gereksiz yeniden taranmadı. run_status önceki tam baytlarını arşivleyerek güncellenir. Bu noktada kullanıcı Gemma metadata/smoke çıktısı beklenir; Codex indirme/servis erişimi/inference,19×3, yeni eğitim veya WP13 yoktur.
