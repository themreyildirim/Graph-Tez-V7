# WP12 — RAM/VRAM ve yerel Ollama erişiminin tekrar kontrolü

**STOPPED_RAM_OR_LOCAL_API_GATE** · 2026-11-08T03:36:11.462507+03:00. Kaynaklar ve dondurulmuş19 senaryo korundu. Hiçbir LLM modeli yüklenmedi, smoke test veya19×3 senaryo çalıştırılmadı. WP13 başlamadı.

## Gerçek ölçüm ve karar
| Kontrol | Sonuç |
|---|---|
| Toplam kullanılabilir RAM | 7.42GiB |
| Anlık boş RAM | **0.53GiB**; kullanım%92.8 |
| GPU toplam/boş VRAM | 4096/3935MiB |
| Eski planlama tabanı | 3GiB boş RAM /2,5GiB boş VRAM; sığma garantisi değil |
| Bellek koşulu | FAIL |
| TCP127.0.0.1:11434 | {"status": "FAILED", "errno": 13, "winerror": 10013, "error": "[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions"} |
| Yerel API | {"error_type": "URLError", "error": "<urlopen error [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions>"} |

Önceki0,36 ve0,93GiB ölçümleri tarihsel olarak korundu; yeniden ölçüm bunların yerine yazılmadı. Sistem RAM'ini azalttığımız/uygulama kapattığımız iddia edilmiyor. Bu tur yalnız güncel durumu okuduk. RAM koşulu sağlanmadı; API erişimi de doğrulanamadı. Bunlar bağımsız iki engeldir; RAM eksikliği10013'ün kanıtlanmış nedeni değildir.

## WinError10013: kanıt ve neden ayrımı
1. **Doğrulandı:** Çağrıyı yapan Python sürecinin TokenIsAppContainer değeri true. Yalnız TOKEN_QUERY erişimi kullanıldı; token veya ayrıcalık değiştirilmedi.
2. **Doğrulandı:** Doğrudan TCP soketi ve proxy kapalı HTTP GET /api/version aynı erişim reddini veriyor. Sayısal loopback adresi kullanıldığı için DNS çözümleme bu denemenin parçası değil. HTTP proxy ayarı bu sonucun açıklaması olarak desteklenmiyor.
3. **Sınırlı görünürlük:** TCP dinleyici tablosu sorgusu GetExtendedTcpTable hatası verdi. Sınırlı süreç listesinde Ollama görülmedi; bu, ana bilgisayarda servis bulunmadığı/çalışmadığı kanıtı değildir. Servis/listener ve sürümü **UNVERIFIED** kaldı.
4. **Salt okunur izin sınırı:** CheckNetIsolation LoopbackExempt -s sorgusu erişim reddi verdi. Komutun yönetici çalıştırma metni bir hata mesajıdır; uygulanmadı, yetki yükseltme veya muafiyet ekleme yapılmadı.

Microsoft,10013'ü WSAEACCES/erişim reddi olarak tanımlar; hata tek başına belirli bir güvenlik kuralını teşhis etmez. [Microsoft Winsock hata kodları](https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2).

Microsoft'un AppContainer/UWP ağ yalıtımı açıklaması, loopback ve yetenek kısıtlarının bağlantıları engelleyebildiğini belirtir. Bu genel mekanizma ile gerçek token/socket bulguları birlikte değerlendirildiğinde **çalışma ortamının AppContainer ağ izolasyonu güçlü bir olası açıklamadır**. Ancak WFP drop kaydı, muafiyet listesi veya belirli engelleyen kural elde edilmedi; kesin kök neden/kural adı doğrulanmış değildir. [Microsoft ağ yalıtımı teşhisi](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall).

10013'ü model bozukluğu, port çakışması, Ollama kesin kapalı veya firewall kesin hatalı diye yorumlamıyoruz. Model dosyaları önceki turda tam hash ile doğrulanmıştı; bu tur büyük ağırlıklar gereksiz yeniden taranmadı. İlk ad-hoc token sorgusunda ctypes64-bit handle imzası hatası oluştu; doğru argtypes ile sorgu tekrarlandı ve true elde edildi. Bu uygulama hatası düzeltilirken işletim sistemi ayarı değiştirilmedi.

## Yapılmayanlar ve koruma
- Model yükleme/çıkarım0; smoke test NOT_RUN_PRECONDITIONS_FAILED.
-19×3 senaryo NOT_RUN_SMOKE_NOT_PASSED; dondurulmuş liste ve SHA değişmedi. Başarı veya başarısız LLM yanıtı uydurulmadı.
- Kaynak doğrulama24 ve bellek kapısı6 offline test geçti; bunlar JSON Schema API veya gerçek LLM kalite testi değildir.
- Süreç sonlandırma, RAM temizleme aracı, servis başlatma, firewall/muafiyet değişimi, yetki yükseltme, yeni model/PDF indirme veya eğitim yok.
- İnsan semantik incelemesi NOT_PERFORMED_NO_OUTPUT; açıklama otomatik yayınlanmadı. reported_in_PDF /predicted_by_GNN ayrımı ve kaynak sözleşmesi değişmedi.
- Önceki3.328 dosya başlangıç SHA kaydıyla korunur. run_status güncel kayıtla öne eklenir; eski tam baytlar yeni QA arşivinde ve dosyanın sonunda saklanır.

## Çıktılar ve durma noktası
QA: reports/qa/WP12/local_llm_recheck_v1/. recheck.json gerçek ölçüm ve hataları, diagnostic_interpretation.json kanıt/çıkarım sınırını, frozen_inputs_check.json19 senaryo kilidini, iki yeni log30 offline testi gösterir. Notebook yalnız kayıtları okuyup gerçek tablo/grafik üretir; model çağrısı içermez.

Bu aşamada duruldu. Devam için hem boş RAM koşulu hem erişilebilir yerel API yeniden doğrulanmalıdır. Güvenlik ayarını değiştirmeden veya yetki yükseltmeden bu oturumdan kesin servis/listener doğrulaması yapılamadı. Bir sonraki izinli işlem koşullar sağlanınca yalnız sınırlı, önceden kilitlenmiş smoke test olacaktır;19×3 çalışma bu turun kapsamına alınmadı.
