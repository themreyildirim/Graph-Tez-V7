# WP12 — Kullanıcı PowerShell smoke testi ve ayrı doğrulama kaydı

**AWAITING_USER_POWERSHELL_OUTPUT** · 2026-11-08T03:42:44.085060+03:00. Bu tur kullanıcı ortamında gerçek çıktı henüz alınmadı. Codex inference başlatmadı;19×3 senaryo yok. 3GiB RAM eşiği değiştirilmedi.

## Yeni gerçek ölçüm
| Kontrol | Sonuç |
|---|---|
| Boş/toplam host RAM | **0.89 / 7.42GiB**; kullanım%88.1 |
| Boş/toplam VRAM | **1633 / 4096MiB** |
| Değişmeyen kapı | Host en az3GiB; VRAM en az2560MiB (2,5GiB) |
| Çağıran süreç | TokenIsAppContainer=true |
| Yerel GET /api/version | {'error_type': 'URLError', 'error': '<urlopen error [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions>'} |

Hem RAM hem mevcut VRAM koşulu geçilmedi. Önceki3935MiB boş VRAM ölçümü tarihsel olarak korunur; yeni1633MiB ölçümünden hangi uygulama/modelin belleği kullandığı çıkarılamaz. İzin sınırı nedeniyle Ollama'nın gerçek servis/model durumu bu ortamdan doğrulanamadı.10013, bu ağ erişimi denemesindeki izin reddidir; model arızası sonucu değildir. Önceki teşhis raporunda AppContainer izolasyonu olası neden olarak ayrılmıştır; belirli kural kanıtı yoktur. Bu iki engelden herhangi biri yeterli olduğundan Codex içinde inference yapılmadı.

## Kullanıcı kendi PowerShell ortamında nasıl çalıştıracak?
Normal kullanıcı PowerShell penceresinde, Codex'in komut yürütücüsünden bağımsız çalıştırın. Yönetici yetkisi veya ExecutionPolicy değişikliği gerekçesi üretilmedi. Betik güvenlik politikanız tarafından engellenirse ayarı değiştirmeden hata çıktısını paylaşın.

Yalnız bağımsız metadata/bellek kontrolü (varsayılan, inference yok):

```powershell
& 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_UserPowerShellSmoke_v1.ps1'
```

Koşullar uygunsa tek teknik smoke testine izin veren komut:

```powershell
& 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_UserPowerShellSmoke_v1.ps1' -RunSmoke
```

Betik kendi yeniden ölçümünde de3GiB RAM/2,5GiB VRAM tabanını ve non-AppContainer ortamını zorunlu tutar. Bu bir bellek garantisi değildir; koşul sağlanmazsa inference olmadan kayıt üretip durur. Model bellekte zaten yüklüyse otomatik unload etmez; başka oturumu etkilemeden durur. Ollama kapalıysa betik servis başlatmaz. Yalnız127.0.0.1:11434'e gider; proxy kapalı, HTTP redirect kapalı; başka URL/indirme/pull yolu yoktur.

Seçilmiş tam tag/digest eşleşmelidir: qwen3:4b-instruct-2507-q4_K_M / sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0. Eksik/farklı modelde otomatik indirme veya alternatif yoktur. /api/version, /api/tags ve /api/ps yalnız metadata kontrolüdür. RAM/VRAM çağrıdan hemen önce yeniden ölçülür.

## Smoke testin sınırı ve sabit ayarları
Bu test **PDF açıklaması değildir**: tek, klinik içeriksiz teknik echo talebiyle yerel JSON Schema taşımasını sınar. Sahte prospektüs, yan etki, MedDRA, SHAP, Δz veya model skoru üretmez. Teknik istekte probe sabiti WP12_LOCAL_SMOKE_V1 istenir; bu bir doğrulama işaretidir, gerçek sonuç değildir. Gerçek yanıt henüz yoktur.

Değişmeyen ayarlar: num_ctx2048, num_predict384, temperature0, seed20261108, think:false, stream:false, keep_alive0. En çok bir /api/chat isteği;60sn HTTP timeout; retry/fallback yok. İstek baytları/SHA ve model digest'i yanıt görülmeden kaydedilir. Bu echo için ayrı teknik şema kullanılması, PDF açıklaması v1 sözleşmesini veya19 senaryo kilidini değiştirmez. Kaynaklı19 senaryo uygulanacaksa gerçek tokenizer/prompt bütçesi ve insan semantik inceleme kapıları ayrıca aynen korunacaktır.

Host RAM saniyelik örneklenir; GPU başlangıç/hemen önce/sonra alınır. Bu kayıtlar kesin tepe inference RAM/VRAM ölçümü değildir.60sn istemci timeout'u sunucunun kesin durduğu anlamına gelmez; böyle durumda UNKNOWN kaydı tutulur, tekrar gönderilmez ve süreç sonlandırılmaz. Başka kullanıcı/uygulamaların eşzamanlı bellek veya servis kullanımının kontrol edildiği iddia edilmez.

Başarılı echo, tek şemalı isteğin kabulü ve onunla uyumlu yanıt için teknik kanıttır; genel JSON Schema uyumu, Türkçe özet kalitesi veya kaynak sadakati kanıtı değildir. `reported_in_PDF` ve `predicted_by_GNN` sözleşmesi değişmez. Açıklama otomatik yayınlanmaz.

## Gerçek çıktı nasıl teslim ve doğrulanacak?
Betik sonunda yeni klasörün tam yolunu yazar: reports/qa/WP12/user_smoke_runs/tarih_GUID/. Var olan kaydı ezmez. Aynı klasörde run_record.json, file_hashes.json ve yalnız gerçekten gerçekleşen aşamaların ham metadata/istek/yanıt/bellek dosyaları bulunur. Çalıştırdıktan sonra bu klasör yolunu paylaşın. Henüz çıktı gelmediği için bu turdaki ayrı external_output_review_record.json **AWAITING_USER_POWERSHELL_OUTPUT**, sonuçnull'dır.

Gelecek inceleme komutu (LLM/ağ çalıştırmaz):

```powershell
python 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\wp12_user_smoke_review.py' '<betiğin yazdığı gerçek çıktı klasörü>'
```

Doğrulayıcı her gerçek teslim için ayrı user_smoke_reviews/UUID/review.json oluşturur; ham çıktıyı veya eski QA'yı değiştirmez. Dosya manifesti/SHA, script/senaryo/sözleşme kilidi, tam model digest, bağımsız host token, iki bellek kapısı, tek istek, ayarların aynılığı, echo/done/token sayıları ve metadata bağlantıları kontrol edilir. Eksik/timeout/düşük sonuç başarıya çevrilmez. Hash tutarlılığı, kullanıcının sağladığı kaydın gerçek çalışmasını kriptografik olarak tasdik etmez; bu sınır inceleme kaydında yazılır.

Kullanıcı host testi başarılı, aynı zamandaki Codex erişimi10013 ise ortamlar arası fark için kanıt güçlenir; belirli firewall kuralı yine kendiliğinden kanıtlanmış olmaz. Host'ta da hata varsa hata aynen korunur; model bozukluğu teşhisi otomatik konmaz.

## Bu turdaki gerçek doğrulama ve koruma
PowerShell betiği **yalnız AST/sözdizimi ayrıştırmasından geçti; çalıştırılmadı**. Bağımsız host çalışma başarısı henüz NOT_RUN.12 yeni offline doğrulayıcı testi +6 bellek kapısı +24 kaynak sözleşmesi testi geçti. Yeni testlerde yalnız geçici, açıkça teknik echo fixture'ları kullanıldı; bunlar kullanıcı çıktısı veya gerçek model sonucu değildir.

Önceki3.343 dosya başlangıç SHA kaydıyla korundu; önceki3.328 kümesi, kaynak alıntıları, PDF'ler, deneyler ve sözleşmeler dahildir. run_status güncel kayıtla öne eklenir; önceki tam baytlar QA arşivinde ve dosyanın sonunda tutulur.19 senaryo değişmedi. Süreç sonlandırma, firewall/yetki değişikliği, indirme, eğitim veya WP13 yoktur.

Teknik başvuru: [Ollama Chat API](https://docs.ollama.com/api/chat) şema formatı, çalışma seçenekleri ve yanıt alanlarını; [Ollama model listesi API](https://docs.ollama.com/api/tags) yerel model/digest metadata yapısını açıklar. Bu belgelerin incelenmesi yerel API desteğinin çalıştırılarak doğrulanması değildir.
