# WP12 — EXPERIMENTAL_LOW_MEMORY_v1 / gerçek S01-R1 incelemesi

08.11.2026 · **Model yanıt üretti; kaynaklı Türkçe açıklama kabul ölçütlerini karşılamadı. İnsan onayı bekliyor; otomatik yayın yok.**

İncelenen gerçek run: `C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\reports\qa\WP12\experimental_low_memory_user_runs_v1\20261108_065325_050e95866a054763b9ac7d5551e1f8f5`. Üst klasörde en son oluşturulan kayıt olduğu doğrulandı. İnceleme salt okunur;17 ham run dosyası/16 manifest girdisi doğrulandı ve değiştirilmedi. Bu tur yeni inference, API erişimi, tekrar, model indirme, eğitim,19×3 veya WP13 yok. AGENTS/aktif ROADMAP ve v1 kaynak/çıktı sözleşmesi korunur.

## 1. Teknik üretim ile açıklama başarısı farklı

| Kontrol | Sonuç |
|---|---|
|Gerçek yanıt|Var; boş olmayan assistant content|
|HTTP / tamamlama|200 / done=true / done_reason=stop|
|Ollama / kullanıcı ortamı|0.40.6 / PowerShell5.1.26100.9711 / AppContainer=false|
|Giriş / önbellekten giriş / çıktı|919 /0 /188 token|
|Sabit bütçeler|1536input +384output +128safety;2048context|
|Giriş+gerçek çıktı|1107 token; length stop veya truncation kaydı yok|
|Sunucu total / yükleme|8.708088s /5.135394s|
|Sunucu prompt / üretim|1.437998s /2.100574s|
|İstemci bloğu|14.233102s; Python review dahil, salt inference süresi değil|
|Timeout / HTTP exception|Kayıtta yok;60s değiştirilmedi|
|Kaydedilen generation teşebbüsü|1; hash'i eşit runner'da tek PostAsync|
|Yeni indirme|Kayıtta0; runner'da pull yolu yok. Global başka istemci trafiği bu run'dan gözlenemez|
|JSON sözdizimi / vaka ve v1 JSON Schema|Geçti / ikisi de geçti|
|Uygulama sözleşmesi|**BAŞARISIZ: invalid refusal**|
|Codex kaynak sadakati değerlendirmesi|**BAŞARISIZ**; insan onayı değildir|
|İnsan semantik incelemesi|**PENDING**, karar verilmedi; yayımlanabilir değil|

API/source model digest `sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c`; wrapper dosya SHA `sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16` ayrı nesne olarak doğrulandı. Wrapper'ın source-manifest bağlantısı ayrı config ile4 gerçek model/template/license/params katman referansları uygun karşılaştırıldı; wrapper içindeki ek source-manifest referansı bir model katmanı sanılmadı. Kaydedilmiş tags/kimlik ile mevcut yerel manifest, tam model blob, runtime DLL, PDF ve kaynak/kod hash'leri salt okunur doğrulandı. Model yeniden yüklenmedi; tokenizer/context/forward çalıştırılmadı.

Request SHA `cebaf7b94d5a88ead48a58ce1362a4666946a6086bf103310e80a94f3a48591e`; ham response SHA `8ad96fef1e68c9beb826a3ca343d44104bd4069d4002768122f04f127449e3b2`. Frozen request/context ve gerçek token proof eşittir. İki alıntı tam537 karakterle prompt'tadır; kaynak yokluğu veya token kesilmesine kanıt bulunmadı.

## 2. Gerçek model content — AYNEN

Aşağıdaki metin ham HTTP yanıtının `message.content` alanıdır; yazımı, İngilizce cümlesi ve tab/boşlukları korunmuştur. Yeni ya da düzeltilmiş model yanıtı değildir. Ayrı dosya: `reports/qa/WP12/experimental_low_memory_S01_R1_review_v1/model_message_content_exact.txt`.

```json
{
  "schema_version": "WP12-local-llm-candidate-v1",
  "status": "refused",
  "refusal_code": "IMAGE_TEXT_UNAVAILABLE",
  "items": [
    {
      "explanation_tr": "The provided text does not contain any information about the product's form or formulation.",
    	"source_scope": "product_identity",
    "statement_kind": "formulation",
    "evidence_ids": [
      "quote:d6a07837c21263d02077b2e692bb266a46f2ffa230d53d5ebc10988738fe6bbe"
    ]
  }
]
}
```

**Gerçek `explanation_tr` alanı aynen:**

> The provided text does not contain any information about the product's form or formulation.

**Model Türkçe açıklama üretmemiştir.** Aşağıdaki yalnız inceleyenin Türkçe çevirisidir, model çıktısı değildir:

> Sağlanan metin, ürünün şekli veya formülasyonu hakkında herhangi bir bilgi içermiyor.

Türkçe alan adının bulunması, cümlenin Türkçe olduğu veya kaynakla doğru eşleştiği anlamına gelmez.

## 3. Yapısal geçiş ve uygulama sözleşmesi

JSON Schema yalnız geçerli anahtar/enum/tür/boyutları denetledi; mevcut şemada `status=refused` olduğunda `items=[]` şartını kuran koşullu kural yok. Bu nedenle ham aday **JSON Schema'dan geçiyor**, fakat aynı anda refused+IMAGE_TEXT_UNAVAILABLE ve bir açıklama item'ı içerdiği için değişmeyen uygulama validator'ı **invalid refusal** üretiyor. Bu ayrım yeniden üretildi; şema veya kayıt düzeltilmedi.

Ek bağımsız item kontrolü: quote-ID gerçektir ve izinli listede; scope=product_identity doğrudur. Ancak item `statement_kind=formulation` iken atıf **sayfa1 identity** alıntısına yapılmıştır. Sağlanan sayfa6 formulation alıntısı çıktı atfına alınmamıştır. Tek başına doğru quote-ID kaynak uygunluğu sağlamaz. Mevcut validator ilk invalid-refusal hatasında durduğu için ikinci kind/ID hatası bu bağımsız incelemede ayrıca görünür kılındı.

## 4. Özgün PDF ile kaynak karşılaştırması

Kaynak `data/user_pdfs/pil.502.pdf`, ham SHA `1b8182521f1314c595451e14a881caa930ba8a5df3c99d468e50429d0e61533e`. Fiziksel1 ve6'nın bütün sayfaları Poppler ile PNG'ye render edilip görsel olarak kontrol edildi. Mevcut PyMuPDF2.1 bağımlılığı, önceki pilotun text/sort=false/flags195 yolunda yalnız bu iki sayfayı okudu; sayfa metinleri önceki extraction'a ve alıntı aralıklarına birebir eşit. OCR, PDF indirme veya eski extraction çıktısını yeniden yazma yok. Tam sayfa kontrolü için modele yeni içerik eklenmedi.

### Özgün alıntı — fiziksel sayfa1

Quote-ID `quote:d6a07837c21263d02077b2e692bb266a46f2ffa230d53d5ebc10988738fe6bbe`; Unicode yarı açık aralık `[1028,1281)`; alıntı SHA `5c6e3e1df9f794449a55d580da6bab3d08650821159649f109484e27e8c25d8d`.

```text
The name of your medicine is Erythromycin Tablets BP 250 mg (referred to as 
Erythromycin Tablets in this leaflet). Erythromycin Tablets contain the active ingredient 
erythromycin, which belongs to a group of medicines called macrolide antibiotics. 
 
```

### Özgün alıntı — fiziksel sayfa6

Quote-ID `quote:e9288119add1a9a49d1b3353510b966b508729035697e4afe9519f4af95aaeb5`; Unicode yarı açık aralık `[987,1271)`; alıntı SHA `dc8a0bcd503c3c42d0dfff0c825f482d949f7a0b81dd1ad997a564806b13eb32`.

```text
What Erythromycin Tablets look like and the contents of the pack 
Erythromycin Tablets are red coloured, round, biconvex, enteric-coated tablets.  
 
They are available in blister packs containing 28, 56, 84 and 100 tablets or in containers of 
21, 100, 250, 500 and 1000 tablets. 
 
```

| İncelenen konu | Bağımsız kaynak değerlendirmesi | Durum |
|---|---|---|
|ürün|Ürün adı/doz açıklanmamış.|OMITTED|
|etkin_madde|Etkin madde ve ilaç sınıfı aktarılmamış.|OMITTED|
|formülasyon|Formülasyon bilgisi yok iddiası açık kaynakla çelişiyor.|CONTRADICTED|
|ambalaj|Ambalaj bilgileri aktarılmamış.|OMITTED|
|belirsizlik|IMAGE_TEXT_UNAVAILABLE desteklenmiyor; bu sayfalar metin katmanından okunabilir.|UNSUPPORTED_REFUSAL|
|atıf|Gerçek quote-ID seçilmiş ancak formulation amacı identity alıntısına bağlanmış.|MISATTRIBUTED|
|dil|explanation_tr İngilizce; gerçek Türkçe açıklama yok.|WRONG_LANGUAGE|
|eşdeğerlik|Yeni ana ilaç/ürün eşdeğerliği iddiası yok; bu durum yanlış reti başarılı kılmaz.|NO_EQUIVALENCE_CLAIM|
|yasak_çıktı|Bu yanıtta yeni skor/etiket/yan etki üretilmemiş.|NO_FORBIDDEN_GENERATION|

Bu yanıtta yeni bir yan etki/MedDRA etiketi, skor veya klinik risk iddiası üretilmemiştir. Buna karşılık **kaynakta mevcut formülasyon bilgisinin bulunmadığı iddiası desteklenmeyen ve kaynakla çelişen bir ifadedir**; bilgi uydurmanın yalnız yeni pozitif klinik olgu eklemek şeklinde olmadığı görülüyor. IMAGE_TEXT_UNAVAILABLE, gönderilen iki okunabilir metin alıntısına uygun bir ret gerekçesi değildir. Ürün, etkin madde ve formülasyon doğru aktarılmamış; esas olarak atlanmış ve yok sayılmıştır. Kaynakta olmayan bir ürün eşdeğerliği iddiası yoktur; bu tek olumlu sınır, görevin başarısını sağlamaz.

Seçili alıntılarda unknown-frequency/might niteleyicisi yoktur. Modeldeki unavailable ifadesi bu alıntıların belirsizliğini koruma değildir; eklenmiş desteksiz ret gerekçesidir. Erythromycin bilinmeyen sıklık S04 ve Doxycycline sınıf/BUN senaryoları bu tek S01 çalışmasıyla sınanmış sayılamaz. Source/PDF sadakati Codex tarafından olumsuz değerlendirildi; insan inceleme kararı hâlâ bekler.

## 5. Gerçek bellek koşulları

| Ölçüm | Gerçek kayıt |
|---|---:|
|Başlangıç boş RAM|1.751541GiB|
|Gönderim öncesi boş RAM|1.714378GiB|
|Son boş RAM|1.718765GiB|
|Kararlı giriş örnekleri|5 /4.055350s; bütün RAM/commit/OS kapıları geçti|
|Çalışma örnekleri|37|
|Örneklenmiş en düşük boş RAM|**0.997353GiB**|
|Örneklenmiş en düşük commit alanı|9.461472GiB|
|OS düşük bellek sinyali|37 örnekte0 true|
|GPU başlangıç / immediate / son|3935 /3935 /3935MiB boş|
|Gerçek process peak RAM / runtime peak VRAM|**UNKNOWN**; bu sayaçlar örneklenmedi|

Deneysel giriş1,5GiB RAM/1GiB VRAM/3GiB commit koşulları geçti. Çalışma0,75GiB RAM/1GiB commit/OS alarmı tetiklenmedi. Minimum0,997GiB, eski v2'nin1GiB çalışma uyarısının altındadır; eski politika değiştirilmez veya bu deney üzerinden yeniden yazılmaz. Bu run ayrı deneysel sözleşmeyle değerlendirilmiştir. Güvenlik veya başka run'larda çalışabilme garantisi yoktur; örnekler arası minimumlar ve kısa bellek baskısı UNKNOWN kalır.

GPU başlangıç ve sonunda aynı boşluk görülmesi GPU kullanılmadığını veya CPU-only çalıştığını göstermez. keep_alive=0 sonrası dönüş, inference içi peak kullanımını gizleyebilir; kaynak kayıtlarında o peak ölçümü yok. Modelin yanlış açıklamasının nedeni **UNKNOWN**: tek run'dan RAM, model boyutu, dil yeteneği veya seed kaynaklı nedensel teşhis yapılamaz. Gözlenen olgular modelin tam yanıt verdiği ve yanıtın sözleşme/kaynak açısından hatalı olduğudur.

## 6. Testler, korunma ve sonraki adım

**25 bağımsız inceleme testi geçti**:17 ham dosya ve hash'ler, ayrı model kimlikleri,919/188 token, JSON Schema/uygulama ayrımı, invalid refusal, kind-ID uyuşmazlığı, özgün PDF sayfa/aralıkları,37 RAM/commit/OS örneği, exact content, no-network ve kaynak run'ın değişmemesi dahil. Mevcut doğrulayıcı salt fonksiyonlarıyla aynı structural_review sonucu yeniden üretildi; kaynağın içine `review()` çalıştırılıp dosya yazılmadı. İki geliştirme sorunu yeni denetleyicide giderildi: wrapper'ın ek manifest bağlantısını model katmanı gibi karşılaştırma beklentisi ve global Python'da olmayan PyMuPDF yerine mevcut `.deps/pymupdf` konumunun kullanılması. Bunlar **gerçek denemenin hataları değildir**; eski betik veya yöntem değiştirilmedi.

Önceki **3575** dosya,17 gerçek run dosyası dahil salt okunur hash envanteriyle korunur. Eski model/sonuç/QA/şema/senaryo/PDF değişmedi. Yalnız `run_status.md` yeni inceleme bölümü alır; önceki tam baytları QA'da arşivlenir ve status dosyasının devamında korunur. Yeni QA manifesti bu incelemenin çıktılarını izler.

**Geçiş önerisi:19×3 başlatılmamalı.** İlk gerçek vaka teknik olarak tamamlandı ama uygulama ve kaynak başarı kapısını geçmedi. Önce kullanıcı insan incelemesi. Sonra gerekirse, açık yeni kararla ayrı sürümlü bir şema/ret koşulu ve Türkçe kaynak aktarım uyumu önerisi değerlendirilebilir. Bu rapor böyle bir değişikliği uygulamaz, mevcut yanıtı tamir etmez, yeni inference veya otomatik tekrar önerisi çalıştırmaz. Prompt/seed/bellek/timeout/digest/19 vaka değişmez; en iyi çıktı seçimi yok. WP13 başlatılmaz.

Çalıştırılmış notebook: `notebooks/WP12_experimental_low_memory_S01_R1_review.ipynb`. QA: `reports/qa/WP12/experimental_low_memory_S01_R1_review_v1/`. Gerçek PNG'ler: `reports/figures/WP12/experimental_low_memory_S01_R1_review_v1/`. `source_claim_comparison.csv` konu bazlı kaynak incelemesini; `actual_runtime_memory.csv`37 ölçümü; `independent_audit.json` teknik/semantik ayrımı; exact-content dosyası modelin değişmeyen metnini taşır. Yeni manifest yalnız bu turun kanıtıdır; eski run manifesti aynen kalır.

## Ek — Ham HTTP gövdesi AYNEN

Aşağıdaki gövde UTF-8 ham dosyasından okunmuştur; yeniden JSON formatlama yapılmamıştır. Ham dosya hash'i yukarıdadır.

```json
{"model":"gemma3:1b-it-q4_K_M","created_at":"2026-11-08T03:53:46.2128092Z","message":{"role":"assistant","content":"{\n  \"schema_version\": \"WP12-local-llm-candidate-v1\",\n  \"status\": \"refused\",\n  \"refusal_code\": \"IMAGE_TEXT_UNAVAILABLE\",\n  \"items\": [\n    {\n      \"explanation_tr\": \"The provided text does not contain any information about the product's form or formulation.\",\n    \t\"source_scope\": \"product_identity\",\n    \"statement_kind\": \"formulation\",\n    \"evidence_ids\": [\n      \"quote:d6a07837c21263d02077b2e692bb266a46f2ffa230d53d5ebc10988738fe6bbe\"\n    ]\n  }\n]\n}"},"done":true,"done_reason":"stop","total_duration":8708087700,"load_duration":5135394200,"prompt_eval_count":919,"prompt_eval_cached_count":0,"prompt_eval_duration":1437998000,"eval_count":188,"eval_duration":2100574000}
```
