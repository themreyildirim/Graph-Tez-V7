# WP12 — Küçük yerel LLM tasarım ve uygulanabilirlik

08.11.2026 · **DESIGN_ONLY — kullanıcı onayı bekleniyor.** LLM kurulmadı, indirilmedi, çağrılmadı; eğitim yoktur. Önceki PDF pilotu kullanıcı tarafından kabul edilmiştir. Bu rapor eski `reports/WP12.md` veya pilot raporunu ezmeyen ayrı ektir.

## 1. Karar ve kapsam
Küçük bir modelin görevini yalnız mevcut PDF alıntılarını Türkçe açıklamak/özetlemekle sınırlamak uygundur. **Mevcut RAM basıncıyla çalıştırma önerilmez.** Bellek serbestliği ve ayrıca kullanıcı onayı sağlanırsa küçük, quantize metin modeliyle kontrollü pilot denenebilir. Bu bir performans/kalite garantisi değildir. LLM açıklaması yan etki tahmini, biyolojik nedensellik veya klinik risk doğrulaması olmayacaktır.

AGENTS, aktif ROADMAP WP12, belge sözleşmesi v1, kabul edilmiş pilot raporu, 44 alıntı ve bağlam anotasyonları incelendi. WP13 kapsamına geçilmedi; yeni yol haritası oluşturulmadı. WP00–WP11 modelleri ve sonuçları kullanılmadı/değiştirilmedi. PDF'den türetilen bilgi etiket, girdi, SIDER kaydı veya yeni MedDRA hedefi olmayacak.

## 2. Salt okunur ortam ölçümü
Ölçüm zamanı: **2026-11-08T03:07:15.686921+03:00**. Ham ölçüm/provenans `reports/qa/WP12/llm_design_v1/hardware_snapshot.json` içindedir.

| Kaynak | Gerçek gözlem | Yorum |
|---|---|---|
| CPU | Ryzen5 4600H; 6 fiziksel/12 mantıksal çekirdek | CPU inference süresi ölçülmedi |
| RAM | 7.42 GiB kullanılabilir toplam; 0.77 GiB anlık boş; kullanım%89.6 | İlk sınırlayıcı mevcut host bellek basıncı |
| GPU | NVIDIA GeForce GTX 1650 Ti; toplam 4096MiB, anlık boş 3935MiB | 4GiB VRAM; KV cache/çalışma alanı ayrıca gerekir |
| Sürücü | 555.97 | Resmi GTX1650Ti compute7.5/550+ koşuluyla uyumlu görünür; fiili runtime testi yok |
| Disk C | 44.33 GiB boş | İlk sınırlayıcı disk değil |
| Python | 3.11.3 | Mevcut pandas/matplotlib/nbformat/nbclient ve standart kütüphane kullanıldı |
| Ollama | Çalıştırılabilir dosya mevcut | Sürüm/API yeteneği doğrulanmadı; binary veya endpoint çağrılmadı |

Windows CIM sorgusu erişim hatası verdi; bu, donanım yok anlamına gelmez. CPU adı registry, çekirdek/RAM psutil ve native ölçüm, GPU nvidia-smi salt okunur sorgusuyla doğrulandı. Süreç kontrolünde çalışan Ollama süreci görülmedi; bu gözlem daha sonra servis başlamayacağını veya portun boşluğunu kanıtlamaz. Seçilmiş OLLAMA çevre anahtarları tanımlı görünmüyor. Sandbox LOCALAPPDATA farklı bir dizine yönlendiğinden gerçek kullanıcı binary yolu açıkça kontrol edildi; yeniden kurulum gerekçesi üretilmedi.

Resmi [Ollama GPU desteği](https://docs.ollama.com/gpu) GTX1650Ti'yi listeler. Driver şartının sağlanması, kurulu sürümün JSON schema/think kontrollerini desteklediği veya modelin tamamen GPU'ya sığdığı anlamına gelmez. [Context belgesi](https://docs.ollama.com/context-length) daha büyük context'in bellek maliyetini açıklar. Dosya boyutu, VRAM/RAM gereksinimi değildir; KV cache, runtime ve diğer süreçler ek yük getirir.

## 3. Model adayları — kalite ölçümü değil
| Aday | Resmi kayıt boyutu/quantization | Yerel durum ve öneri |
|---|---|---|
| [qwen3:1.7b](https://ollama.com/library/qwen3:1.7b) | 1.4GB, Q4_K_M | Daha düşük ağırlık boyutlu birincil aday; henüz indirilmedi. Etiket1.7b, kayıt ayrıntısı2.03B gösterdiği için isimden kesin parametre hesabı yapılmadı |
| [gemma3:1b-it-q4_K_M](https://ollama.com/library/gemma3:1b-it-q4_K_M) | 806MB, Q4_K_M | Metin-only düşük boyut alternatifi; Ollama>=0.6 gerekir; Gemma kullanım şartları ayrıca incelenmeli |
| [qwen3:4b-instruct-2507-q4_K_M](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M) | 2.5GB, Q4_K_M | Zaten önbellekte; 4GiB kartta bellek payı daha dar; ikincil koşullu seçenek |
| [qwen3:4b](https://ollama.com/library/qwen3:4b) | 2.5GB, Q4_K_M | Mevcut instruct2507 ile farklı tag/digest; ek4B indirme önerilmedi |

Boyutlar ondalık GB/MB resmi registry verisidir; GiB donanım ölçümleriyle özdeş değildir. Qwen kayıtları Apache2.0; Gemma kendi kullanım koşullarıyla sunulur. Lisans/tam digest onay sonrası nihai çalışma kaydına alınır. Model ailesinin çok dil desteği Türkçe tıbbi sadakat kanıtı değildir. 7/8B veya görüntü modeli bu kısa metin görevinin ilk pilotuna önerilmez; hız ve özet kalitesi henüz **NA/NOT_MEASURED**.

Önemli yerel bulgu: `qwen3/4b-instruct-2507-q4_K_M` manifesti zaten var. Model katmanı **2,497,280,480 bayt**, digest `85e4a5b7b8ef0e48af0e8658f5aaab9c2324c76c1641493f4d1e25fce54b18b9`. Manifestin işaret ettiği tüm dosyaların varlığı/boyutları uyumlu; ağırlık içerik hash'i alınmadı, yükleme/çalıştırma veya tam model doğrulaması yapılmadı. Registry manifest prefix'i ile model katmanı digest'i farklı şeylerdir. Bu tur hiçbir modeli bizim indirdiğimiz varsayılmaz.

Önerilen ileriki seçenek: Qwen küçük aday için açık2048 context,384 çıktı token, sıcaklık0, seed20261108, tek istek, iş bitiminde keep_alive0. [Thinking kontrolü](https://docs.ollama.com/capabilities/thinking) model/sürüm bağımlıdır; destek doğrulanırsa think:false, yoksa sessiz fallback yerine durma. [Yapısal çıktı](https://docs.ollama.com/capabilities/structured-outputs) için JSON Schema formatı önerilir. Bunlar **PROPOSED**, henüz çalıştırılmış ayarlar değildir.

Yerel planlama kapısı: küçük aday için en az3GiB boş host RAM ve2.5GiB boş VRAM önerilir. Bu eşikler üretici minimumu veya ölçülmüş sığma garantisi değildir; ihtiyatlı başlangıç kuralıdır. Anlık boş RAM bu kuralı karşılamıyor. Uygulamalar kapatılmadı, sürücü güncellenmedi, servis başlatılmadı. Onaydan sonra bellek tekrar ölçülmeli; 4B seçilirse daha fazla pay ve gerçek tepe bellek kontrolü gerekecek. Kullanıcı mevcut önbellekli modeli tercih edebilir; bizim ilk önerimiz daha küçük adaydır, otomatik indirme yoktur.

## 4. Kaynaklı çıktı ve doğrulama sınırı
`docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md` ayrıntılı sözleşmedir. Aday sadece kanıt kimlikleriyle Türkçe taslak döndürür. Trusted wrapper gerçek sayfa, metin aralığı, SHA ve birebir kaynak cümle/alıntı aralığını ekler. Kimlik, sayfa veya kaynak cümle yoksa açıklama reddedilir. `reported_in_PDF` ile `predicted_by_GNN` ayrı; ikincisi bu modülde sabit NOT_REQUESTED/null'dır. Model skoru, SHAP, Δz, yeni yan etki veya MedDRA etiketi alanları kabul edilmez.

Kaynak kapsamı/amaçları eski anotasyondan korunur: doğrudan ürün, ilaç, sınıf, sınıf içinde doxycycline, uyarı, etkileşim, hayvan/ilişkili ilaç, yardımcı madde, aşırı doz ve belirsizlik birleştirilmez. Renal sınıf cümlesi, sınıf girişi ve doxycycline istisnasıyla birlikte taşınır. Bu bağımlılık yeni tasarım katmanıdır; eski dosyalar değişmez. Parent/tuz/formülasyon ve PDF sürüm farkları korunur.

**Kaynak kimliği doğru olmak anlam doğruluğu demek değildir.** Doğru alıntıya bağlı uydurma bir özet yapısal kontrolden geçebilir. Bu sınırı özel bir teknik test açıkça gösterir. Bu yüzden hiçbir aday otomatik yayınlanmaz: hepsi insan semantik incelemesinde bekler. İnsan incelemesi her iddianın alıntıda bulunmasını, kapsam/negasyon/istisna ve belirsizliği kontrol eder. Eksik kanıt için ret; düşük kalite için onarım adı altında yeni bilgi ekleme yoktur.

## 5. Gerçek kaynaklı sabit senaryolar ve kabul
19 senaryo seçildi; model sonuçları okunarak örnek seçilmedi. Tam kaynak kimliği/page/offset/hash, soru ve kabul kriterleri `frozen_scenarios.json` içindedir. Her vaka **NOT_RUN_NO_LLM**; semantik sonuç null, başarı0 değildir. Kaynakların içeriği senaryo tanımıdır, LLM çıktısı değildir.

Kapsam: ürün/formülasyon; yardımcı madde; aşırı doz; Erythromycin p4–5 devamı ve bilinmeyen sıklık; Doxycycline p7 doğrudan giriş ve sınıf ayrımı; renal istisna; sınıf-dahil uyarılar; might; adı tetracycline olan bileşik etkileşimi; hayvan/ilişkili ilaç; emzirme bilinmeyeni; monohydrate/parent; belge sürümü; görsel sayfa10 metin yokluğu; kaynaksız ve yasak tahmin isteği; PDF içi URL/talimatı izlememe; uzun context'in kesilmeden reddi.

Kabul için atıfların%100 çözülmesi ve birebir dilim uyumu zorunludur. Tüm ekstra alanlar/kaynaksız iddialar reddedilir. Anlam için her cümlede insan onayı gerekir; tek kapsam/negasyon/uydurma ihlalinde aday reddedilir. Gerçek LLM'de bütün senaryolar ve aynı ayarla üç tekrar gelecekte kaydedilecek; en iyi cevap seçilmeyecek. Tekrarların byte eşitliği ile kaynak/semantik tutarlılığı ayrı raporlanacaktır.

Karakter uzunlukları hesaplandı; tokenizer yok, kesin token sayısı ölçülmedi. Bütün44 alıntı tek context'e verilmez. Gelecekte prompt+şema+bağımlı kaynaklar gerçek tokenizer ile1536 token sınırını aşarsa istisna kesilmez; ret veya bağlamı koruyan bölümleme gerekir. Kısa modelin İngilizce→Türkçe aktarımı, uzun bağlam ve negasyon kabiliyeti bu turda sınanmadı.

## 6. Teknik QA, notebook ve koruma
Yeni `tests/test_wp12_llm_contract.py`: **24 teknik test**. Gerçek44 alıntının17 sayfadaki dilimleri, uydurma/seçilmemiş kaynak, sınıf yükseltme, eksik bağlam, renal istisna, yasak görev/alanlar, tam kaynak zarfı, refusal, kaynak mutasyonu, tekrarlanabilirlik ve ağ/proses gerektirmeme sınanır. Test adayları yalnız TEKNİK TEST metnidir; sahte prospektüs veya LLM sonucu değildir. `infer` çağrısı kasıtlı hata verir. Test kaydı yalnız bu yeni QA dizinine yazılır; eski testler/çıktılar yeniden üretilmez.

Çalıştırılmış notebook `notebooks/WP12_local_llm_design.ipynb`: donanım, model adayları, gerçek alıntı kapsamları, renal istisna örneği,19 senaryo ve teknik test kanıtını kod altında gösterir. Üç PNG, RAM anlık durumu, kayıt boyutları ve gerçek alıntı kapsamını açıklar. Bunlar model başarısı grafikleri değildir.

Önceki **3.282 dosya** başlangıç SHA kaydıyla korunur; iki ham PDF ve44 alıntı paketi dahildir. Büyük DrugBank/STRING kaynakları yeniden taranmadı. Son koruma sonucu ve eski pilot manifest kontrolü yeni `artifact_validation.json` içinde; değişebilir run_status eski tam baytları yeni QA arşivinde ve güncel dosyanın sonunda korunur. Yeni kanıt manifesti kendi dışındaki üretilen dosyaları ve kabul edilmiş pilot kaynak referanslarını kapsar.

## 7. Sonraki onay kapısı
Onay gerektirenler: küçük model seçimi (yeni indirme gerekiyorsa açık izin), mevcut Ollama sürüm/yetenek kontrolü, bellek boşluğu, tam digest/prompt kilidi ve kontrollü senaryo çalıştırması. Donanım için koşullu uygulanabilirlik var; **şu an RAM kapısı geçilmedi**. LLM kalite ve kaynak sadakati için henüz deneysel kanıt yoktur. Bu noktada durulur; gerçek yerel LLM uygulaması ve WP13 başlatılmaz.

## Yürütme kaydı ve son kontrol
Notebook'un7 kod hücresi gerçek IPython yürütmesiyle çalıştırıldı;3 PNG gömüldü ve görsel olarak incelendi. İlk nbclient harici kernel denemesi çıktı üretmeden beklediği için durduruldu; başarılı kernel çalışması iddia edilmedi. Projede önceki paketlerde kullanılan sıralı IPython yürütücüsüyle hücreler gerçekten çalıştırılıp tablo/grafik çıktıları yakalandı. Bu teknik yürütme farkı kaynak/metot kararını veya LLM iznini değiştirmedi. İki ayrı teknik test logu korundu; ikisinde de24 test geçti.

Son bütünlük denetimi:3.282 önceki dosya ve eski pilot manifestindeki74 girdi doğrulandı; run_status tarihsel baytları arşivden kontrol edildi.19 senaryonun kaynak ve bağlam bağlantıları geçerli; gerçek LLM yanıtı/başarı ölçümü yoktur.
