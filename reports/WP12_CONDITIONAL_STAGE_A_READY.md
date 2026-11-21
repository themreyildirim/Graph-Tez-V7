# WP12 — Koşullu LLM planı ve Gemma V2 Aşama A yürütücüsü

08.11.2026 · **Aşama A hazır; gerçek kullanıcı PowerShell çıktı klasörü bekleniyor. V2/Qwen henüz çalıştırılmadı.**

AGENTS/aktif ROADMAP ve kabul edilmiş kaynak/çıktı/V2 sözleşmeleri korunur. Kullanıcı A tek istek ve B koşullu hazırlığını onayladı; küçük hazırlıklar için tekrar izin gerekmiyor. Uygulama yetki/durma kuralları `docs/plan/WP12_CONDITIONAL_EXECUTION_PLAN_v1.md` ve `configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json` içinde kalıcıdır. Bu yeni bir yol haritası değildir.

## 1. Kabul edilmiş yöntemi değiştirmeyen yürütücü

`scripts/WP12_GemmaV2_UserSingleCase_v1.ps1` normal kullanıcı PowerShell'i içindir. Onaylı `gemma3:1b-it-q4_K_M`/`sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c`, kabul edilmiş V2 case schema/system/user request, S01-R1 soru/iki orijinal alıntı/ölçüt birebir aynı. Kaynak537 karakter; önceki gerçek vocabulary-only ölçümü **724 prompt token**; bu yeni gerçek inference sonucu değildir. Her kullanıcı preflight'ında aynı native tokenizer ile tekrar sayılır.1536input/384output/128safety/2048context; context sığmazsa kesmeden durur. Exact v2 runtime grammar ve gerçek server724 teyidi hâlâ NOT_RUN/UNVERIFIED; ilk gerçek istek bunları da sınayacak.

Normal kullanıcıdan yerel version/tags/ps metadata, doğru API digest ile source/wrapper ayrımı ve native/model/PDF/kod/schema/prompt/source-context SHA doğrulaması gerekir. Yüklü başka model varsa otomatik kapatma/unload yerine durur. AppContainer ise API'den bile önce durur. Codex bu yürütücüyü çalıştırmadı; API0/inference0.

Yeni Python yardımcı modülü `scripts/wp12_gemma_v2_user_run.py` yalnız ağsız preflight ve reply incelemesidir. Status/schema/application/obvious-language/task coverage ayrılır. Türkçe veya kaynak sadakati otomatik PASS olmaz; source/human PENDING kalır. Yanlış JSON/ret/kind/İngilizce/eksik görev kaydedilir. HTTP/model yükleme/timeout/token sayısı uyumsuzluğu teknik hatadır; kaynak becerisi veya klinik doğruluk sonucu değildir. Gerçek yanıtı aldıktan sonra bağımsız kaynak ve insan incelemesi ayrıca yapılır.

## 2. Tek gerçek istek sınırı ve kayıtlar

Proje genelindeki sabit slot **reports/qa/WP12/conditional_local_llm_v1/control/stage_A_generation_claim.json**. Bütün kaynak/token/bellek ön koşullarından sonra, PostAsync öncesi atomik FileMode.CreateNew/FileShare.None ile tüketilir. İkinci kullanıcı çağrısı önce slotu görüp durur; iki eşzamanlı süreçte yalnız biri CreateNew alabilir. API veya süreç hatası sonrası da otomatik silme/reset/retry yoktur; başladığı belirsiz istek ikinci kez yollanmaz. Bu mekanizma aynı projenin kayıt dosyası korunurken geçerlidir; kullanıcı tarafından elle silinmiş/kopyalanmış kayıt için global sunucu garantisi iddia edilmez. Betikte force/reset seçeneği veya dosya silme yolu yoktur.

Her deneme benzersiz `reports/qa/WP12/gemma_v2_user_runs_v1/<zaman_GUID>/` klasörü açar. Tam wire request, raw HTTP yanıt (hata gövdesi dahil), schema/system/token/context/dependency hashleri, generation-claim kopyası, metadata/digest, Python stdout/stderr, süre/HTTP/bellek/OS/GPU, structural_review, boş insan inceleme formu ve file_hashes saklanır. Yanıtın kendisi otomatik çevrilmez/düzeltilmez/yayımlanmaz. Global slot tüketimi istemci isteği teşebbüsünü sınırlar; sunucunun tamamladığına ancak raw response kanıtı destek verir.

## 3. Donanım politikası aynı

EXPERIMENTAL_LOW_MEMORY_v1'in yalnız donanım/timeout/OS alanları devralındı: başlangıç RAM≥1,5GiB/GPU≥1GiB/commit≥3GiB, OS düşük bellekfalse;5 kararlı RAM/commit/OS ölçümü ve hemen önce RAM/GPU kontrolü. Runtime RAM<0,75GiB veya commit<1GiB veya OS basıncında kayıt/istemci iptali, no-retry. Eksik ölçümde durur. HTTP60s; sunucunun anında durduğu varsayılmaz. Gemma eski2,5GiB politikası ve bütün eski kararlar değişmez. Qwen için bu düşük eşikleri kullanma izni yoktur.

Hazırlık snapshot'ı `2026-11-08T07:39:43.6146225+03:00`: boş RAM **1.734GiB**, GPU **3935MiB**, commit **11.184GiB**, OSfalse. Bu bir başlangıç/peak garantisi değildir. Gerçek komut öncesinde bütün koşullar yeniden ölçülür; eşik sağlanmazsa istek yoktur.

## 4. Koşullu Qwen ve bilimsel karşılaştırma

Mevcut karar **WAIT_USER_STAGE_A_RUN**; B henüz açılmadı. Gerçek, teknik tamamlanmış V2 yanıtında schema/application/language/source/task FAIL olduğunda koşullu kullanıcı izniyle Qwen hazırlığı yapılabilecek. Yeni indirme, yeni keyfi soru/ölçüt veya en iyi tekrar seçimi yok. Qwen cache/digest/template/tokenizer ve kendi bellek uygunluğu açıkça denetlenecek; RAM/VRAM/commit/OS eşiği geçmezse durulacak, otomatik riskli düşürme yapılmayacak. Teknik engeller kalite FAIL gibi yazılmayacak. Normal kullanıcı PowerShell'i gerekirse açık komut verilecek; tekrar küçük hazırlık onayı istenmeyecek.

Şimdiki `comparison_current_NOT_FINAL.json/csv` yalnız gerçek V1 sonuçlarını ve açık NOT_RUN V2/Qwen satırlarını taşır. V1 HTTP200/stop/919input/188output; JSON SchemaPASS, application/Türkçe/kaynak/primary-IDFAIL, sampled RAM minimum0,997GiB. V1'in ilk insan formu PENDING kalır; kullanıcının başarısızlığı kabul ettiği ayrı alandadır. V2 için724 offline tokenı server ölçümü gibi göstermedik. Qwen için güncel digest/bellek değerlendirmesi henüz yapılmış gibi gösterilmedi. Gerçek raw message JSON/CSV round-trip ile aynı tutuldu. Kaynak karşılaştırma CSV'si dokuz bağımsız üretim değil, tek gerçek cümlenin konu bazlı incelemesidir.

Gerçek yeni sonuç gelince ayrı sürümlü rapor/notebook/claim-tablosu/figürler/manifestler tamamlanacak. İlk başarısız V1 silinmez veya başarılıya çevrilmez. Aynı S01'i görerek yöntem düzeltmek, bağımsız genelleme veya klinik doğruluk kanıtı değildir. İnsan semantik incelemesi ve observed-source açıklama sınırı sürer. Tek vaka geçse bile19×3 için kullanıcı sonuç değerlendirmesi beklenir.

## 5. QA ve korunma

**30 yeni yürütücü/koşul testi +36 kabul edilmiş yöntem testi geçti.** Atomik slot .NET testi ayrı TEST_ONLY dosyasında ilk açma başarılı/ikinci açma engelli; gerçek slot tüketilmedi. PS5.1(5.1.26100.9711) parse0hata, AST1PostAsync, betik çalıştırılmadı. Runner SHA **f3f639c8c0f425a0e00b615d19fef010aaf8aae9f91135e5fb07df18553f45f1**. Python duplicate-key/NaN, token/model/stop/bütçe ve uygulama/dil/görev kontrolleri; AppContainer erken kapısı, claim öncesi bellek/hash kontrolü, no-download/no-force/no-reset/no-retry ve koşullu B/D sınırları test edildi.

Önceki **3630** kabul edilmiş dosyanın SHA envanteri korundu. Yalnız güncel status yeni bölümle güncellenecek; önceki baytları QA arşivi ve tarihsel devamda aynen korunur. Eski modeller/GNN/SHAP/PPI, PDF/44 alıntı/19 senaryo/ölçüt, V1 ve V2 öneri dosyaları değiştirilmez. PROPOSED adındaki kabul edilmiş yöntem dosyaları tarihsel isimleriyle kullanılır; yeni yürütücü config'i onayı ayrı kaydeder.

## 6. Kullanıcı komutu ve beklenen çıktı

Normal kullanıcı PowerShell'inde **yalnız bir kez**:

```powershell
& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_GemmaV2_UserSingleCase_v1.ps1" -RunFirstCase
```

Yazdırılan **Evidence directory** yolunu paylaşın. Mevcut koşullu yetkiye göre gerçek yanıtın teknik ve kaynak/dil incelemesini yapacağız; gerekirse B hazırlığını ayrıca küçük izin istemeden tamamlayacağız. Ön koşullar geçmezse hatayı/ölçümleri saklayarak durur; otomatik tekrar yoktur. Kullanıcı uygulamalarını veya Ollama servisini kapatma, güvenlik ayarı/yetki değiştirme talimatı verilmez. Bu turda yeni inference/model indirme/eğitim/otomatik yayın/WP13 yapılmadı;19×3 başlatılmadı.

Notebook `notebooks/WP12_conditional_local_llm_stage_A_ready.ipynb`; QA `reports/qa/WP12/conditional_local_llm_v1/`; gerçek/NOT_RUN durum PNG'si `reports/figures/WP12/conditional_local_llm_v1/`. Aktif sonraki adım yalnız gerçek kullanıcı çıktı klasörünü beklemek.
