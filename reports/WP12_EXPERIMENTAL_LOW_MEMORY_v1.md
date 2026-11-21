# WP12 — EXPERIMENTAL_LOW_MEMORY_v1 tek-vaka hazırlığı

08.11.2026 · **Yalnız normal kullanıcı PowerShell'inde S01-R1 için hazır. Gerçek LLM isteği gönderilmedi.**

Kullanıcı1,68GiB civarı RAM koşulunda mevcut Gemma1B ile kontrollü tek denemeyi açıkça onayladı. Bu onay yalnız ayrı deneysel politika içindir. Eski2,5GiB politika/smoke/başarısızlıklar/QA,19 senaryo ve44 kaynak alıntısı değiştirilmedi. Aktif AGENTS/ROADMAP/output sözleşmesi geçerlidir; WP13 yoktur.

## Politika ve gerçek ölçüm

| Koşul | Deneysel giriş | Çalışma uyarısı |
|---|---:|---:|
| Kullanılabilir fiziksel host RAM |≥1,5GiB|<0,75GiB|
| Boş GPU belleği |≥1GiB|Başlangıç/son ölçümü; sürekli GPU peak iddiası yok|
| Sistem commit boşluğu |≥3GiB|<1GiB|
| Windows LowMemoryResourceNotification |false ve okunabilir olmalı|true veya ölçüm hatası|

Commit girişte önceki3GiB marjını korur;1GiB çalışma kritik sınırı ayrı açık politikadır. Bu sınırlar performansa göre seçilmedi ve güvenlik garantisi değildir. Commit alanı fiziksel RAM ile eşdeğer değildir; paging veya sistem yavaşlamasını önlediği iddia edilemez. Başlangıç5 RAM/commit/OS örneği yaklaşık4 saniye, gönderim öncesi RAM/GPU/commit/OS tekrar kontrolü; çalışma örnekleme250ms. Kısa süreli basınç örnekler arasında kaçabilir. Runtime uyarısında HTTP istemcisi iptal edilir, yeni istek/tekrar yoktur; başlamış sunucu inference'ının hemen durduğu varsayılmaz. Ölçüm eksikse işlem durur.

Gerçek salt okunur ölçüm **2026-11-08T06:41:41.2885997+03:00**: RAM **2.064GiB**, toplamRAM7.421GiB; GTX1650Ti4096MiB toplam/**3935MiB boş**, commit **11.371GiB**, OS düşük bellek **false**. Bu an yeni giriş kapısını geçti; eski2,5GiB kapısını geçmedi. Sonraki5 örnek de RAM/commit/OS koşullarını geçti; GPU o aralık için tek snapshot'tır. Bunlar kullanıcı komutunun çalışma anına taşınan garanti değildir; her şey tekrar ölçülür.

Windows OS sinyali [CreateMemoryResourceNotification](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-creatememoryresourcenotification) ve [QueryMemoryResourceNotification](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-querymemoryresourcenotification) ile okunur. Yalnız bu gözlem için alınmış notification handle kapatılır; uygulama veya servis sonlandırılmaz. Commit hesabı [PERFORMANCE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information) üzerinden `(CommitLimit−CommitTotal)×PageSize`dır. API hatası false sinyal gibi yorumlanmaz.

## Donanım gerekçesi ve bilinmeyenler

Mevcut onaylı GGUF dosyası **806058400bayt (768.72MiB)**; bu dosya boyutudur, process resident veya GPU yükleme boyutu değildir. Önceki gerçek vocabulary-only logunda26 katman,1 KVhead, key256/value256 kayıtlıdır.2048context veFP16 varsayımıyla üstten tam KV dizisi hesabı `26×2048×1×(256+256)×2`=**52MiB**. Gemma'nın sliding/local attention uygulaması veya cache tipi bunu değiştirebilir; gerçek runtime KV ölçümü yapılmadı.

Bu nedenle1GiB GPU giriş eşiği ancak deneysel alt sınırdır. DLL/runtime, aktivasyonlar, scratch, sürücü ve CPU/GPU kopyaları bilinmiyor. Mevcut3,84GiB boş GPU alanı gözlemsel bir marj sağlar; GPU offload yerleşimi veya peak hostRAM garantisi değildir.1,5GiB başlangıç ve0,75GiB uyarısı arasındaki alan dar olduğundan ilk yanıt/timeout/çalışma bellek kayıtları görülmeden daha fazla istek açılmaz.

## Değişmeyen vaka, kimlik ve token politikası

- Tek vaka **S01-R1**: frozen19 listesinin ilk kaydı, Erythromycin ürün ve formülasyon açıklaması; başarıya göre seçilmedi. Fiziksel sayfa1+6, iki tam alıntı537 karakter; soru/ölçüt/quote-ID/ham metin aynıdır.
- Model **gemma3:1b-it-q4_K_M**, API/source digest **sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c**. Yerel wrapper SHA313f… ayrı kalır. Eski identity helper ve onaylı kaynak manifesti doğrulanır; yeni indirme/etiket/model yok.
- Prompt, v1 daraltılmış JSON Schema ve tüm generation ayarları önceki tek-vaka paketinin aynısı:2048context/384output/batch32/temp0/seed20261108/thinkfalse/streamfalse/keep_alive0; HTTP60s değişmez.
- Tam prompt **919 gerçek token**, önceki vocabulary-only ölçümü; her kullanıcı çalıştırmasında aynı GGUF sözlüğü/şablonuyla yeniden hesaplanır.1536 giriş+384output+128safety; tam kaynak/zorunlu bağlam sığmazsa **CONTEXT_BUDGET**. Sessiz kesme yok. Tensor/context/decode başlatmayan token sayacı yalnız düşük-bellek adaptörünün açık1,5GiB kapısından sonra çalışır; eski modülün2,5GiB kapısı değiştirilmedi.
- Native dosya, model blob, PDF,19 senaryo,44 alıntı, bağımlılık/kaynak ve kod hash'leri kontrol edilir. Sunucunun `prompt_eval_count` değeri offline sayıyla eşit değilse inceleme başarısızdır; otomatik yeniden deneme yoktur.

## İstemci ve kayıt sınırları

`scripts/WP12_ExperimentalLowMemorySingleCase_v1.ps1` tek PostAsync içerir. AppContainer algılanırsa **API metadata isteğinden önce** durur. Bu hazırlıkta AppContainer=true; API0/inference0. Kullanıcının kendi normal PowerShell'inde version/tags/ps metadatası okunur; kimlik/JSON Schema/token/bellek kapıları geçmeden kaynaklı chat gönderilmez. Başka model yüklüyse otomatik unload yerine durur. Süreç sonlandırma, servis/güvenlik ayarı, yetki yükseltme veya model indirme kodu yoktur.

Her deneme `reports/qa/WP12/experimental_low_memory_user_runs_v1/<zaman_GUID>/` altında ham request/response, tam prompt ve token proof, quote bağlamı, kaynak/kod/model hash'leri, RAM/commit/OS örnekleri, giriş/sonGPU, süre/HTTP/istisna, Python logları, run_record ve dosya hash manifestini saklar. Timeout/istemci hatasında server_completion UNKNOWN kalır. Tek `inference_attempts` kaydı istemci gönderim teşebbüsüdür; global sunucu trafiği denetimi değildir. Üretimden önce durulursa ham yanıt olmaması açıkça anlaşılır; sahte yanıt üretilmez.

## Anlam incelemesi ve QA

JSON Schema ve kaynak-ID/scope/kind kontrolü insan semantik incelemesinden ayrıdır. Geçerli aday `SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW`, semantic_success=null, automatic_release=false; ret ve düşük kaliteli/eksik yanıtlar saklanır. Kaynağa aykırı Türkçe iddia otomatik başarı sayılmaz. `reported_in_PDF` ile `predicted_by_GNN` alanları ayrıdır; yeni skor/SHAP/Δz/MedDRA veya klinik risk iddiası yoktur.

**25 yeni test +24 mevcut sözleşme testi geçti.** Sınır değerler, eksik/bozuk ölçüm, OS basıncı, RAM/GPU/commit düşüşü, tek çağrı, AppContainer izolasyonu, no-retry ve eski2,5GiB/prompt/hash korunması doğrulandı. PS5.1(5.1.26100.9711) parser:iki dosyada0hata; runner1, observer0 generation çağrı noktası. Runner SHA-256 **2ebb860618e130a7449217091386cd25163f239c318eebda233c21fbae87149a**. Betik gerçek inference için bu ortamda çalıştırılmadı.

Önceki **3536** dosya güncelleme öncesi aynı SHA ile doğrulandı. Eski smoke, iki başarısız deneme, B0/B1/B2/GNN/SHAP/PPI/PDF/senaryo/kabul kriterleri korunur. Sadece güncel `run_status.md` yeni bölüm alır; önceki tam baytları yeni QA'da arşivlenir ve dosyanın devamında korunur. Önceki hazırlık manifestinde mutable run_status girdisinin eski hash'i bu arşivle doğrulanır; eski manifest değiştirilmez.

## Kullanıcı komutu — yalnız bir kez

Normal kullanıcı PowerShell'inde:

```powershell
& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_ExperimentalLowMemorySingleCase_v1.ps1" -RunFirstCase
```

Bu komut kendi kapılarını yeniden ölçer. Koşul sağlanmazsa durur; otomatik tekrar yapmaz. Yazdırdığı **Evidence directory** klasörünü paylaşın; ilk gerçek yanıtı kaynak sadakati ve teknik sonuç bakımından inceleyeceğiz. Tek denemeden sonra durulacak;19×3 veya WP13 başlatılmayacak.

Dosyalar: `configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json` yalnız bu deneyin politikası; `scripts/wp12_source_low_memory.py` eski modülü değiştirmeyen adaptör; `scripts/WP12_LowMemoryObservation_v1.ps1` salt okunur OS ölçümü; `notebooks/WP12_experimental_low_memory_single_case.ipynb` çalıştırılmış Türkçe açıklamalar; `reports/figures/WP12/experimental_low_memory_v1/` gerçek ölçüm PNG'si; `reports/qa/WP12/experimental_low_memory_v1/` test/gözlem/korunma/manifest kanıtları.
