# WP12 — Gerçek Gemma V2 incelemesi ve koşullu Qwen ön hazırlığı

08.11.2026 · **Gemma V2 gerçek yanıt verdi; token kapısı FAIL ve Türkçe açıklama FAIL. Qwen ön hazırlığı yapıldı, inference RAM kapısında NOT_RUN.**

Run `C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\reports\qa\WP12\gemma_v2_user_runs_v1\20261108_074723_6a9844b7f6d249c08bb38033d1ce218e` salt okunur incelendi.21 ham dosya/20 manifest girdisi, doğru Gemma9755… digest, aynı V2 request/schema/iki tam alıntı, globalclaim ve frozen kaynak/kod hash'leri doğrulandı. Bu tur model inference/API isteği/tekrar/indirme/eğitim yoktur. AGENTS/ROADMAP/WP12 kaynak sözleşmeleri ve koşullu plan uygulanır;19×3/otomatik yayın/WP13 yok.

## 1. Teknik sonuç ve değişmeyen token hatası

HTTP200/done=true/stop. Gerçek server prompt **729**, kayıtlı offline beklenti **724**; fark+5. Gerçek output312<384, toplam1041<context2048; context bütçe aşımı veya length stop yoktur. Sunucu total **8,157021s**, yükleme3,452087s, prompt1,223231s, output3,461736s; istemci blok12,527538s Python review dahil. Tek generation slotu tüketildi ve korunuyor; ikinci Gemma isteği/retry/reset yapılmaz.

Saved `structural_review.json` aynen **TOKEN_COUNT_ALIGNMENT_FAILED / technicalFAIL / schemaNOT_EVALUABLE / applicationNOT_EVALUABLE** kalır. Token kapısı JSON kontrolünden önce durdu. Yeni ayrı `Gemma_V2_independent_review.json` içindeki ham-content kontrolü orijinal pipeline'ı PASS'e çevirmez; sahte729 proof ile yeniden validation yapılmadı.

## 2. Token farkı: benim ön kontrol varsayımım ve doğrulama sınırı

Ön kontrolü hazırlarken GGUF iç Jinja şablonunu kayıtlı Ollama servis şablonuyla aynı varsaydım. Tek-user41 ve919 hizalaması, yeni system+user yolunu kanıtlamıyordu. Yerel kayıtlı template SHA **e0a42594d802e5d31cdc786deb4823edb8adff66094d49de8fffe976d753e348** ile GGUF şablonu farklıdır: GGUF system içeriğini ilk user prefix'ine birleştirirken, kayıtlı Go template system mesajını ayrı bir user turu olarak basar. Test edilmiş saf yeniden kurulumda **Go2 user turu / GGUF1 user turu** görülüyor. Bu teknik ön-kontrol kusuru modelin biyolojik bilgisi veya Türkçe yeteneğiyle karıştırılmaz.

[Ollama0.40.6 template işleyicisi](https://github.com/ollama/ollama/blob/v0.40.6/template/template.go) system içeriğini ayrıca toplarken mesajları da korur; modelin seçtiği template buna göre farklı metin üretir. [Prompt yolu](https://github.com/ollama/ollama/blob/v0.40.6/server/prompt.go) ve [llama-server köprüsü](https://github.com/ollama/ollama/blob/v0.40.6/llm/llama_server.go) farklı renderer/Go-template/native-chat yolları içerir. Bu nedenle yalnız GGUF şablonunun token sayısı servis için evrensel sayı değildir.

**Sınır:** Sunucunun gerçekten render ettiği prompt baytları bu run'da saklı değildir. Sözlük-only tekrarın1,5GiB ayrı RAM kapısı geçilmediği için **729'un native sayısal yeniden üretimi bu tur UNKNOWN/BLOCKED**; kesin729 reproduksiyon yapılmış gibi sunulmaz. Kayıtlı template farkı+5 ile tutarlıdır;5'in bütün nedenleri kesin doğrulandı iddiası yok. Eski724 dosyası, test kanıtları veya runner güncellenip geçmişte doğruymuş gibi gösterilmedi. Sınırlı yeni Go-template alt-küme renderer'ı yalnız hash-pinned iki modelin plain system/user/no-tools yolunu inceler; Go kurulum/derleme veya yeni model indirme yoktur. Bilinmeyen syntax reddedilir.

## 3. Gerçek model yanıtı aynen

```json
{
"schema_version": "WP12-local-llm-candidate-v2",
"status": "candidate",
"refusal_code": null,
"items": [
  {
    "explanation_tr": "Erythromycin Tablets are a pharmaceutical product containing the active ingredient erythromycin. Erythromycin is a macrolide antibiotic.",
    "source_scope": "product_identity",
    "statement_kind": "identity",
    "evidence_ids": ["quote:d6a07837c21263d02077b2e692bb266a46f2ffa230d53d5ebc10988738fe6bbe"]
  },
  {
    "explanation_tr": "The Erythromycin Tablets are red coloured, round, biconvex, enteric-coated tablets.",
    "source_scope": "product_identity",
    "statement_kind": "formulation",
    "evidence_ids": ["quote:e9288119add1a9a49d1b3353510b966b508729035697e4afe9519f4af95aaeb5"]
  }
],
"language": "tr"
}
```

**Item0 model metni aynen:**

> Erythromycin Tablets are a pharmaceutical product containing the active ingredient erythromycin. Erythromycin is a macrolide antibiotic.

**İnceleyenin Türkçe çevirisi; model çıktısı değildir:**

> Erythromycin Tablets, etkin madde erythromycin içeren farmasötik bir üründür. Erythromycin bir makrolid antibiyotiktir.

İngilizce. Etkin madde ve sınıf kaynakta var. BP250mg ürün tanımı atlanmış; yeni klinik olgu yok.

**Item1 model metni aynen:**

> The Erythromycin Tablets are red coloured, round, biconvex, enteric-coated tablets.

**İnceleyenin Türkçe çevirisi; model çıktısı değildir:**

> Erythromycin Tablets kırmızı renkli, yuvarlak, bikonveks, enterik kaplı tabletlerdir.

İngilizce. Renk/şekil/enterik kaplama alıntıyla uyumlu. Ambalaj sayıları atlanmış; birincil quote-ID ve kind doğru.

## 4. İçerik/şema/kaynak/dil birbirinden ayrı

Ham JSON'a salt ayrı post-hoc bakıldığında V2 schema ve primary quote-ID/kind bağları **PASS**. İki farklı purpose bulundu. Yanlış image-only ret yok, candidate/null-code doğru. Buna rağmen açıklamalar **İngilizce**; language=tr gerçek cümle diliyle uyuşmuyor. İlk item iki cümle içeriyor; tek kısa cümle yönergesine de tam uymuyor. Dolayısıyla tam yönerge/Türkçe görevi **FAIL**; automatic checker'ın no-error/PENDING sonucu semantik başarı değildir.

Sınırlı İngilizce-marker yöntemi bu yeni iki İngilizce cümleyi **yakalamadı**; language_checks PENDING döndü. Bu gözlenen false-negative açıkça korunuyor; marker listesi sonuç görüldükten sonra değiştirilmedi. Önceden zorunlu tutulan bağımsız dil/kaynak ve insan incelemesi gerekliliği gerçek örnekte görülmüş oldu. İnsan formu PENDING; bu rapordaki ajan değerlendirmesi insan onayı değildir.

Kaynak açısından: sayfa1 etkin madde erythromycin ve macrolide sınıfını; sayfa6 kırmızı/yuvarlak/bikonveks/enterik tablet biçimini destekler. BP250mg ürün ayrıntısı ve ambalaj sayıları atlanmış; yeni bir klinik olgu/ADR/skor/SHAP/Δz/MedDRA üretilmemiş. İki primary-ID ve purpose doğru. Bu çekirdek kaynak aktarımı V1'in “formülasyon yok” ifadesinden daha uyumludur, fakat başarılı Türkçe açıklama sayılmaz. Kaynakta olmayan eşdeğerlik veya klinik risk iddiası yoktur. Seçili alıntıda unknown/might qualifier yok; S04/Doxycycline/BUN vakaları ayrıca sınanmış sayılmaz.

**Koşullu B gerekçesi** token hatası değildir: HTTP200/stop ile elde edilmiş, bağımsız incelenebilen gerçek yanıtın Türkçe zorunluluğunu açıkça ihlal etmesidir. Bu, kullanıcının önceden verdiği dil/görev başarısızlığında Qwen hazırlığı yetkisine uyar. Token teknik hatası ayrı FAIL olarak aynen kalır. Yalnız API/model yükleme engeli olup gerçek metin olmasaydı kaynak açıklama kalitesi FAIL yazılmazdı.

## 5. Gerçek bellek ve V1/V2 karşılaştırması

V2 giriş RAM1,559GiB, istekten hemen önce1,537GiB;34 örnekte minimum **0.869167GiB**, commit minimum **9.361252GiB**, OS düşük bellek0true. Deneysel0,75GiB uyarısı aşılmadı. GPU giriş/son3935MiB; gerçek runtime peak VRAM/processRAM ve ara örneklerdeki minimumlar UNKNOWN. Bu tek run genel güvenlik kanıtı değildir.

| Boyut | Gemma V1 gerçek | Gemma V2 gerçek | Qwen3 4B |
|---|---|---|---|
|Üretim|HTTP200/stop|HTTP200/stop|NOT_RUN|
|Pipeline son durumu|invalid refusal|TOKEN_COUNT_ALIGNMENT_FAILED|NOT_RUN / RAMBLOCKED|
|Token beklenti / gerçek|919/919|724/729|UNKNOWN / NOT_RUN|
|Gerçek output token|188|312|NOT_RUN|
|Ham içeriğin ayrı schema denetimi|PASS|PASS, post-hoc|NOT_RUN|
|Tam açıklama yönergesi|FAIL|FAIL, İngilizce|NOT_RUN|
|Kaynak ajan incelemesi|FAIL:bilgi-yok çelişkisi|çekirdek destekli; ürün ayrıntıları eksik|NOT_RUN|
|Primary kind-ID|FAIL|PASS|NOT_RUN|
|İnsan per-item incelemesi|PENDING|PENDING|PENDING|

JSON/CSV tam rawHTTP/model-message alanları aynı bayt/metin hashleriyle izlenir; CSV round-trip doğrulandı. Hiçbir önceki dosya yeniden yazılmaz. Aynı S01 üzerinde görülen hata sonrası V2 geliştirme vardır; bağımsız genelleme veya klinik doğruluk, genel model üstünlüğü ve saf parametre-boyutu etkisi iddiası yok. Zorunlu model chat-template farkı da karşılaştırmanın teknik bağlamıdır.

## 6. Koşullu Qwen hazırlığı: gerçek yerel kimlik ve boyut

Mevcut model **qwen3:4b-instruct-2507-q4_K_M**; yerel kayıtlı manifest digest **sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0**, eski frozen Qwen kaydıyla aynı. Config ve model/template/license/params blob SHA'ları doğrulandı; model yeniden indirilmedi. API'nin güncel tags digest'ini normal kullanıcı ortamında doğrulama **PENDING**; Codex AppContainer'dan API erişimi zorlanmadı.

Model dosyası **2.497.280.480bayt (2.326GiB)**. Gerçek GGUF metadata:36katman,2560embedding,32attentionhead/8KVhead,key128/value128,add_bos=false.2048context tam FP16 KV varsayımı `36×2048×8×(128+128)×2`=**288MiB**. Bu hesap runtime/offload/activation/sürücü peak'i değildir.

Qwen kayıtlı template SHA **eade0a07cac7712787bbce23d12f9306adb4781d873d1df6e16f7840fa37afec**. Saf string kurulumunda system ve user ayrı gerçek system/user turlarındadır; Gemma kayıtlı template'i system'i user diye basıyordu. S01 kaynak/soru/kriter/schema/options/system içerikleri korunmuş `Qwen_S01_v2_request_NOT_SENT.json` dosyasında **yalnız model adı değişir**. Template/tokenizer farkı zorunlu teknik uyarlamadır. Tam Qwen prompt token sayısı RAM nedeniyle **UNKNOWN/BLOCKED**; tahmini karakter oranı veya GGUF şablonuyla kesin sayıyı ikame etmedim. API/token count eşitliği ileride ayrı doğrulanmadan Qwen inference açılmaz.

## 7. Qwen ayrı bellek politikası ve gerçek engel

`configs/WP12_QWEN4B_CONDITIONAL_MEMORY_v1.json`: **RAM≥3GiB / GPU≥3584MiB(3,5GiB) / commit≥4GiB / OS düşük bellekfalse**. Eski Qwen3GiB host tabanı korunur. GPU3,5GiB, model2,326GiB+teorik KV0,281GiB+varsayımsal0,75GiB runtime marjının yukarı0,25GiB yuvarlanmasıdır. Bu marj ölçülmüş peak veya garanti değildir. Commit4GiB ayrı plan marjıdır, fiziksel RAM rezervi değildir. Runtimehost1GiB/commit1GiB/OSalarm koşulları, no-retry/no-download/no-automatic-threshold-lowering ve gerçek ölçüm zorunluluğu korunur. Gemma'nın1,5GiB/1GiB düşük eşikleri Qwen'e kopyalanmadı.

Gerçek son salt okunur ölçüm **2026-11-08T07:56:49.1624073+03:00**: boş hostRAM **1.275GiB**, boşGPU **3935MiB**, commit **10.917GiB**, OSfalse. RAM3GiB şartı **FAIL**; commit/GPU yeterli olması fiziksel RAM eksikliğini çözmez. Ayrıca vocab-only1,5GiB ön kontrolü de geçmedi. Bu nedenle **Qwen inference NOT_RUN**, güncel API kimliği ve tam tokenizer sayı UNKNOWN/PENDING. Model yükleme/kalite testi yapılmadı; Qwen için açıklama başarısızlığı veya başarısı iddia edilemez.

Bu koşullarda yeni Qwen inference komutu/yürütücüsü açılmadı. Kullanıcı uygulamaları/servisi kapatılmadı, güvenlik/yetki değiştirilmedi ve daha riskli eşiklere inilmedi. Gerekli kaynak koşulları gerçekten sağlandığında mevcut koşullu yetkiyle normal-user API kimliği + registered-template/native-tokenizer sayımı + SHA/bellek kapıları tamamlanıp en fazla1 Qwen denemesi hazırlanabilir. Bunun için yeni küçük hazırlık izni gerekmez; engel dış bellek koşuludur, izin eksikliği değil.

## 8. QA, korunma ve durma

**32 yeni test geçti**:21 ham V2 dosyası/hash,729/724 ayrımı,312output, orijinalgate sonucu, bağımsız dil/source/schema kontrolleri, marker false-negative, primary-ID, tüketilmiş claim,34 bellek örneği, güvenli şablon alt-kümesi/whitespace/range/system ayrımı, Qwen katman kimliği/KV/ayrı eşikler/gerçek RAM engeli, frozen request yalnızmodel farkı ve V1 başarısızlığı. Yeni template renderer'ının ilk geliştirme denemesinde `$msg.Role` alan erişimi desteği eksikti; yalnız bu yeni modülde düzeltildi ve test edildi. Bu run'ı değiştiren bir yöntem düzeltmesi değildir.

Önceki3679 dosyanın SHA envanteri korunur; GemmaV1/V2 hamları ve globalclaim aynı hash'tedir. Eski724token proof, dosya/script/QA/model/split/senaryo/44alıntı/ölçüt değiştirilmez. Yalnız status yeni bölümle güncellenir; önceki tam baytları QA ve tarihsel devamda saklanır. Yeni manifest rapor/notebook/test/görsel/JSON/CSV/cache-metadata kanıtlarını hash'ler. Bu turda yeni inference0, yeni OllamaAPI0, model indirme0, yeni eğitim0, otomatikyayın0;19×3/WP13 yok.

Notebook `notebooks/WP12_Gemma_V2_review_Qwen_preparation.ipynb`; QA `reports/qa/WP12/gemma_v2_review_qwen_preparation_v1/`; şekiller `reports/figures/WP12/gemma_v2_review_qwen_preparation_v1/`. Aktif durum: **Gemma A tek denemesi tüketildi; B hazırlığı yapıldı ama RAM/token/API kapılarında bloke; gerçek Qwen sonucu yok.** Kaynak/bellek koşulu değişmeden model isteği başlatılmaz.

## Ek — V2 ham HTTP body AYNEN

```json
{"model":"gemma3:1b-it-q4_K_M","created_at":"2026-11-08T04:47:43.287959Z","message":{"role":"assistant","content":"{\n\"schema_version\": \"WP12-local-llm-candidate-v2\",\n\"status\": \"candidate\",\n\"refusal_code\": null,\n\"items\": [\n  {\n    \"explanation_tr\": \"Erythromycin Tablets are a pharmaceutical product containing the active ingredient erythromycin. Erythromycin is a macrolide antibiotic.\",\n    \"source_scope\": \"product_identity\",\n    \"statement_kind\": \"identity\",\n    \"evidence_ids\": [\"quote:d6a07837c21263d02077b2e692bb266a46f2ffa230d53d5ebc10988738fe6bbe\"]\n  },\n  {\n    \"explanation_tr\": \"The Erythromycin Tablets are red coloured, round, biconvex, enteric-coated tablets.\",\n    \"source_scope\": \"product_identity\",\n    \"statement_kind\": \"formulation\",\n    \"evidence_ids\": [\"quote:e9288119add1a9a49d1b3353510b966b508729035697e4afe9519f4af95aaeb5\"]\n  }\n],\n\"language\": \"tr\"\n}"},"done":true,"done_reason":"stop","total_duration":8157021100,"load_duration":3452086700,"prompt_eval_count":729,"prompt_eval_cached_count":0,"prompt_eval_duration":1223231000,"eval_count":312,"eval_duration":3461736000}
```
