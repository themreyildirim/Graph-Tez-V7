"""V2 yöntem ÖNERİSİ: değişiklik manifesti, çalıştırılmış notebook ve rapor."""
import copy
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import wp12_source_case as c
import wp12_method_v2 as v
import wp12_low_memory_run_review as a
from wp09_close_wp10_notebooks import execute
from jsonschema import Draft202012Validator


def text_new(path,value):
    with Path(path).open('x',encoding='utf-8') as f:f.write(value)


def main():
    log=(v.QA/'test_method_v2_release.log').read_text(encoding='utf-8-sig')
    oldlog=(v.QA/'test_historical_run_review.log').read_text(encoding='utf-8-sig')
    assert 'Ran 36 tests' in log and log.rstrip().endswith('OK')
    assert 'Ran 25 tests' in oldlog and oldlog.rstrip().endswith('OK')
    proof=c.read(v.QA/'v2_actual_token_proof.json');assert proof['input_token_count']==724
    ctx=v.verified_S01_context();req=v.request_for_S01();plan=c.read(c.ROOT/'configs/WP12_METHOD_CORRECTION_v2_PROPOSED.json')
    oldschema=c.ROOT/'docs/schemas/WP12_local_llm_candidate_v1.schema.json'
    changes=[
        {'id':'C01','change':'Tam object oneOf: refused=>items boş ve tanımlı ret kodu; candidate=>en az1 item ve refusal_code null.',
         'before':str(oldschema.relative_to(c.ROOT)),'before_sha256':c.sha(oldschema),'after':v.SCHEMA.relative_to(c.ROOT).as_posix(),'after_sha256':c.sha(v.SCHEMA)},
        {'id':'C02','change':'language=tr açık beyanı; system rolünde Türkçe cümle zorunluluğu; sınırlı İngilizce kontrolü+zorunlu insan dil incelemesi.',
         'before':'V1 tek user mesajında Türkçe talebi; dil alanı yok.','after':v.SYSTEM.relative_to(c.ROOT).as_posix(),'after_sha256':c.sha(v.SYSTEM)},
        {'id':'C03','change':'S01 okunabilir kaynak profiline göre geçersiz retler kapalı; context/bellek/API/token retleri önce host kapısıdır.',
         'before':'Global ret enumları S01 grammar alanında da açıktı.','after':'S01_refusal_eligibility.json; yalnız S01 case candidate grammar; genel şema meşru retleri destekler.'},
        {'id':'C04','change':'S01 item oneOf, statement_kind+source_scope+birincil quote-ID bağını şemaya da taşır.',
         'before':'Enumlar bağımsız; v1 uygulama sonradan kind kontrolü yapar.','after':'S01_case_schema_v2_PROPOSED.json; v1 kaynak doğrulayıcısı ayrıca korunur.'},
        {'id':'C05','change':'Ayrı system+user; biçimsel şema yalnız API format alanında, tam şema prompt içine tekrar yazılmaz. Kaynaklar tamdır.',
         'before_wire_request_sha256':c.sha(a.RUN/'source_request.json'),
         'after_proposed_file_sha256':c.sha(v.QA/'S01_request_v2_PROPOSED_NOT_SENT.json'),
         'after_canonical_wire_request_sha256':__import__('hashlib').sha256(c.dump(req).encode()).hexdigest(),
         'before_tokens':919,'after_tokens':724,'input_limit':1536},
        {'id':'C06','change':'V2 için ayrı en fazla1 S01-R1 doğrulama planı; yürütücü/inference yok; v1 başarısızlığı ve tüm19 vaka korunur.',
         'before':'V1 gerçek run başarısız.','after':'WP12-method-v2-S01-R1-validation-01; izin bekleyen yöntem-geliştirme denemesi, bağımsız doğrulama değil.'}]
    manifest={'method':'WP12-source-method-v2-PROPOSED','approval_status':'PENDING_USER_METHOD_APPROVAL',
        'trigger_observed_failed_run':a.RUN.relative_to(c.ROOT).as_posix(),
        'trigger_raw_response_sha256':c.sha(a.RUN/'source_response_raw.json'),
        'historical_run_remains_failed':True,'frozen_scenarios_sha256':c.sha(c.ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'),
        'source_bundle_sha256':c.sha(c.ROOT/'reports/qa/WP12/pilot_v1/source_evidence_bundle.json'),
        'hardware_policy_reference':plan['hardware_policy_reference'],'hardware_policy_sha256':plan['hardware_policy_sha256'],
        'native_tokenizer_unchanged':True,'chat_template_unchanged':True,'render_adapter_changed_to_system_user':True,
        'software_changed_without_model_retraining':True,'actual_new_inference':0,'changes':changes,
        'model_and_options_unchanged_from_v1':True,'future_API_grammar_compatibility':'UNVERIFIED_NO_API_CALL',
        'human_semantic_review_required':True,'automatic_release':False}
    c.save_new(v.QA/'change_manifest_v2.json',manifest)
    # İşlev testleri, yeni model yanıtı değildir. Doğru kaynak kimliği semantik kanıt olmaz.
    fixture={'schema_version':v.VERSION,'language':'tr','status':'candidate','refusal_code':None,
        'items':[{'explanation_tr':'Bu yalnız bir teknik test cümlesidir; model çıktısı değildir.',
            'source_scope':s['scope'],'statement_kind':s['kind'],'evidence_ids':[s['quote_id']]}
            for s in ctx['sources']]}
    cases=[]
    def row(name,x):
        generic=Draft202012Validator(v.generic_schema()).is_valid(x)
        check=v.inspect_candidate(x)
        cases.append({'fixture':'TEST_ONLY_NOT_LLM_OUTPUT','case':name,'generic_schema_valid':generic,
            'S01_case_schema_valid':check['schema_valid'],'application_errors':check['errors'],
            'semantic_success':check['semantic_success'],'automatic_release':False})
    row('İki item içeren teknik candidate',copy.deepcopy(fixture))
    x=copy.deepcopy(fixture);x['items']=[];row('Boş candidate',x)
    x=copy.deepcopy(fixture);x.update(status='refused',refusal_code='IMAGE_TEXT_UNAVAILABLE');row('Dolu items ile refused',x)
    x['items']=[];row('Boş refused: genel şema geçer, okunabilir S01 profili reddeder',x)
    x=copy.deepcopy(fixture);x['items'][0]['statement_kind']='formulation';row('Kind-primary ID uyuşmazlığı',x)
    x=copy.deepcopy(fixture);x['items'][0]['explanation_tr']='The provided text does not contain information about this product.';row('Doğru şema, İngilizce açıklama',x)
    x=copy.deepcopy(fixture);x['items'][0]['explanation_tr']='Bu kaynakta olmayan bir iddiadır.';row('Doğru ID ile uydurma cümle: insan incelemesi zorunlu',x)
    c.save_new(v.QA/'schema_prompt_regression_matrix_TEST_ONLY.json',cases)
    checks={'status':'PROPOSED_METHOD_TESTED_OFFLINE_NOT_RUN','new_method_tests_passed':36,
        'historical_run_review_tests_passed':25,'native_tokenizer_test':'PASS_VOCAB_ONLY_NO_TENSORS',
        'prompt_tokens':724,'input_limit':1536,'all19_scenarios_unchanged':True,'source_chars_unchanged':537,
        'real_new_LLM_responses':0,'inference_or_API_requests':0,'future_max_attempts':1,
        'runtime_grammar_support_for_v2_schema':'UNVERIFIED','automatic_publication':False}
    c.save_new(v.QA/'preparation_checks.json',checks)
    F=c.ROOT/'reports/figures/WP12/method_correction_v2';F.mkdir(parents=True,exist_ok=True)
    init=r'''from pathlib import Path
import json,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists(): ROOT=ROOT.parent
Q=ROOT/'reports/qa/WP12/method_correction_v2'
F=ROOT/'reports/figures/WP12/method_correction_v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
pd.set_option('display.max_colwidth',500)
'''
    execute('WP12_method_correction_v2_proposal.ipynb',[
        ('md','''# WP12 — V2 yöntem düzeltme ÖNERİSİ

Kullanıcı ilk S01-R1'in teknik olarak tamamlandığını fakat kaynak/sözleşme bakımından başarısız olduğunu kabul etti. Bu notebook yalnız öneri ve ağsız testleri gösterir. **Yeni model yanıtı yoktur.** V2, görülen hatadan sonra geliştirildiği için gelecekteki aynı-vaka kontrolü bağımsız başarı deneyi sayılmaz. V1 başarısızlığı,19 frozen vaka,537 karakterlik S01 kaynakları, Gemma/digest ve donanım politikası değişmez.'''),
        ('code',init+r'''
change=read(Q/'change_manifest_v2.json')
display(pd.DataFrame(change['changes'])[['id','change']])
print((ROOT/'docs/prompts/WP12_SOURCE_EXPLANATION_SYSTEM_v2_PROPOSED.txt').read_text(encoding='utf-8'))
'''),
        ('md','''**Yorum:** V2 genel şema refused için boş items ve geçerli kod; candidate için en az1 item ve null kod ister. language=tr bir beyandır, dil doğruluğu kanıtı değildir. S01 için salt kaynak profili okunabilirdir; IMAGE_TEXT_UNAVAILABLE gibi gerekçeler engellenir. Bu dar S01 case grammar'ı candidate dalını kullanır; diğer18 vaka uygulanmış sayılmaz. Girdiler yetersizse host model çağrısından önce durur. Geçersiz aday başarıya zorlanmaz; hata saklanır.

## Şema, prompt ve kaynak regresyonları — teknik fixture'lar'''),
        ('code',r'''
matrix=read(Q/'schema_prompt_regression_matrix_TEST_ONLY.json');display(pd.DataFrame(matrix))
ctx=read(ROOT/'reports/qa/WP12/source_single_case_v1/package/context.json')
display(pd.DataFrame(ctx['sources'])[['physical_page','kind','quote_id','quote']])
'''),
        ('md','''**Yorum:** Yukarıdaki fixture'lar model çıktısı değildir. Kind/quote-ID eşlemesi artık S01 şemasında bağlıdır; v1 kaynak validator'ı da korunur. Doğru ID yanında uydurma Türkçe cümle hâlâ teknik kontrolleri geçebilir; insan onayı zorunludur. Sınırlı İngilizce kontrolü gözlenen hatayı yakalar ama her dili tanıyan bir model değildir. ASCII Türkçe için aksan zorunluluğu yoktur. “Pink capsules exist.” gibi bir İngilizce cümle otomatik belirlenemese bile insan dil incelemesinde bekler; otomatik başarı/yayın olmaz.

## Gerçek tokenizer: system+user şablonu'''),
        ('code',r'''
proof=read(Q/'v2_actual_token_proof.json');native=read(Q/'tokenizer_tests.json')
display(pd.DataFrame([{k:v for k,v in proof.items() if k!='rendered_prompt'}]).T.rename(columns={0:'ölçüm'}))
display(pd.DataFrame([native]))
fig,ax=plt.subplots(figsize=(9,4))
ax.bar(['V1 tam prompt','V2 önerilen tam prompt'],[919,proof['input_token_count']],color=['#8f9fa8','#4d8197'])
ax.axhline(1536,color='#a96868',ls='--',label='Giriş sınırı1536')
ax.set(ylabel='Gerçek token sayısı',title='Kaynaklar aynı; prompt/şema sunumu ayrı sürüm')
for x,y in enumerate([919,proof['input_token_count']]):ax.text(x,y+20,str(y),ha='center')
ax.legend();plt.tight_layout();plt.savefig(F/'actual_v1_v2_prompt_token_counts.png',dpi=160);plt.show()
'''),
        ('md','''**Yorum:** V2 tam prompt724, giriş sınırı1536;384output+128safety ile toplam ayrılmış alan1236, context2048. İki tam kaynak ve kabul ölçütü kesilmedi. Tam biçimsel şema API format alanında; prompt içinde ikinci kez yazılmıyor. Sayı azalması açıklama kalitesi artışı değildir. Aynı yerel GGUF/native sözlük eski41 ve919 sayımlarını üretti; system+user şablon eşdeğerliği ve tekrar token hash'i doğrulandı. Büyük test eki15723 token oldu ve kesilmeden CONTEXT_BUDGET verdi. Sadece vocab_only, tensor/context/decode/inference yok. Gerçek Ollama'nın bu exact v2 şeması ve system mesajını işlemesi henüz API ile sınanmadı; gelecekte tek denemede sunucu prompt sayısı da724'e eşit olmalı.

## Testler ve izin bekleyen tek deneme'''),
        ('code',r'''
display(pd.DataFrame([read(Q/'preparation_checks.json')]).T.rename(columns={0:'durum'}))
plan=read(ROOT/'configs/WP12_METHOD_CORRECTION_v2_PROPOSED.json')
display(pd.DataFrame([{k:plan[k] for k in ['future_trial_id','max_future_generation_attempts','actual_new_generation_attempts','RAM_floor_bytes','GPU_floor_MiB','commit_floor_bytes','runtime_RAM_floor_bytes','runtime_commit_floor_bytes','HTTP_timeout_seconds','user_approval_required_before_execution','all19x3_enabled','automatic_publication']}]).T)
'''),
        ('md','''**Yorum:**36 yeni yöntem +25 tarihsel run inceleme testi geçti. Gelecek plan en fazla1 ayrı S01-R1 validation-01; otomatik retry/57 deneme yok. EXPERIMENTAL_LOW_MEMORY_v1'in yalnız bellek/timeout/OS alanları devralınır; eski v1 prompt veya runner v2 için yürütücü değildir. Yeni yürütücü verilmedi. Türkçe sistem yönergesi, şema, request, native şablon/token, kaynak ve model digest hash'leri ayrı sürümle kayıtlıdır. Gelecek bir başarılı yanıt v1'i geriye dönük başarılı yapmaz; tek görülen vaka genel dil/kaynak performansını kanıtlamaz. Kullanıcı yöntem onayı beklenir;19×3, model indirme/eğitim, otomatik yayın veya WP13 yoktur.''')])
    change_lines='\n'.join(f"|{x['id']}|{x['change']}|" for x in changes)
    system=v.SYSTEM.read_text(encoding='utf-8')
    report=f'''# WP12 — Gözlenen S01-R1 başarısızlığı için yöntem düzeltme v2 ÖNERİSİ

08.11.2026 · **Yöntem önerisi ve ağsız testler tamamlandı. Yeni LLM denemesi yapılmadı.**

AGENTS, aktif ROADMAP WP12, kabul edilmiş PDF/çıktı kaynak sözleşmesi esas alınır. İlk gerçek Gemma S01-R1 run'ı HTTP200/stop/919input/188output ile teknik olarak tamamlandı; İngilizce ve kaynağa aykırı bilgi-yok ifadesi, refused+nonempty items ve formulation/identity ID uyuşmazlığı nedeniyle başarısızdır. Bu değerlendirme değişmez. V2 bu görülen hata sonrası geliştirme önerisidir; gelecekte aynı vaka üstündeki doğrulama bağımsız performans kanıtı veya önceden kör değerlendirme sayılmaz.

## 1. Değişiklik tablosu ve sürüm sınırı

| ID | Açık değişiklik |
|---|---|
{change_lines}

`change_manifest_v2.json`, her değişikliğin gerekçesini/before-after dosya hash'lerini, gerçek başarısız run/response hash'ini ve aynı frozen kaynak/model/donanım bağlarını kaydeder. Eski şema, prompt, doğrulayıcı, kaynak, model veya run dosyası düzenlenmez. Bu yeni bir yol haritası değildir; WP12 içindeki dar S01 yöntem düzeltmesidir.

## 2. Yeni genel şema ve S01 alt şeması

Önerilen genel dosya: `docs/schemas/WP12_local_llm_candidate_v2_PROPOSED.schema.json`.

- Ayrı tam-object **oneOf** dalları kullanılır. `candidate`: en az1 item, en çok4, refusal_code=null. `refused`: items boş, refusal_code tanımlı6 ret enumundan biri ve null olamaz.
- Yeni schema_version=`{v.VERSION}`; language=`tr`. Zorunlu anahtarlar/fazla anahtar yasağı ve v1 scope/kind sözlüğü korunur. language=tr yalnız beyan; Türkçe cümle kanıtı değildir.
- S01 case şeması iki item türünü ayrı oneOf object'lerle source_scope+statement_kind+birincil quote-ID'ye bağlar. S01'de context bağımlılığı yoktur; bir item bir gerçek primary-ID taşır. identity amaçlı sayfa1 kimliği formulation diye kullanılamaz. Bu yalnız S01 için daraltmadır; BUN gibi çoklu bağlam gerektiren diğer vakaları tek ID'ye daraltan bir genel karar değildir.
- Genel candidate≥1 kuralı S01'de de geçerlidir; kimlik ve formülasyonun ikisi aktarılmadıysa ayrı görev kapsam kontrolü TASK_COVERAGE_INCOMPLETE der. Bu kaynak kaydını veya frozen ölçütü değiştirmez; mevcut sorunun iki konusunun eksik bırakıldığını görünür kılar.
- S01 case şemasında kaynak profiline uygun model ret kodu yoktur; bu profile ait üretim grammar'ı candidate dalıdır. Model düşük kaliteli/uydurma aday verirse başarısız kaydedilir, otomatik doğru kabul edilmez. Modelin şemaya zorlanması kaynak doğruluğu garantisi değildir.

Şemalar Python Draft202012Validator ile doğrulandı. Ollama0.40.6'nın **bu exact v2 oneOf/const şemasını** runtime grammar olarak derlediği henüz test edilmedi. Önceki basit JSON Schema smoke geçişi bu yeni şema için yeterli kanıt değildir. API uyumsuzluğu olursa gelecekteki tek deneme başarısız kaydedilecek; sessiz fallback/şema sadeleştirme/retry yok.

## 3. Türkçe sistem yönergesi ve denetlenebilirlik

Dosya `docs/prompts/WP12_SOURCE_EXPLANATION_SYSTEM_v2_PROPOSED.txt`; request'te gerçek `system` rolü, ardından tek `user` rolü vardır. Yerel Gemma3 GGUF şablonu ilk system içeriğini ilk user turuna prefix olarak birleştiriyor; bu özgün şablon ve bağımsız fold eşdeğerliği test edildi. Şablon veya tokenizer değiştirilmedi; yeni render adaptörü yalnız iki rolü destekler.

```text
{system}```

Doğru Türkçe üretimi salt JSON Schema ile güvenilir şekilde belirlenemez. Denetim üç parçalıdır: (1) açık sistem zorunluluğu ve tr beyanı; (2) açıklama cümleleri üstünde sınırlı, deterministik İngilizce göstergesi; (3) **her aday için zorunlu insan dil/kaynak incelemesi**. Marker listeleri v2 modülünde sabittir; observed English cümlesi engellenir. Aksan/özel Türkçe harf zorunluluğu yoktur; geçerli ASCII Türkçe reddedilmez. Marker kontrolünün yanlış negatifleri mümkündür; “Pink capsules exist.” testi bunu gösterir, sonuç dil başarısı yerine PENDING_HUMAN_LANGUAGE_REVIEW'dir. Dil tespiti garantisi veya yeni dil modeli yoktur.

`human_review_required_v2_PROPOSED.json` henüz yanıt/inceleyen/karar içermeyen zorunlu insan inceleme formudur; gerçek veya onaylanmış açıklama değildir.

İnsan formunda her açıklama için şu kararlar gereklidir: cümle Türkçe mi, atıf birincil amacı doğru mu, iddia kaynakta var mı, belirsizlik/istisna korunmuş mu, ürün/etkin madde/formülasyon eşdeğerliği uydurulmuş mu, yeni olgu/skor/etiket var mı? JSON/dil işareti geçişi otomatik semantik başarı değildir. `reported_in_PDF` trusted kaynak cümlesi/sayfa/aralık ile ayrı kalır; `predicted_by_GNN` NOT_REQUESTED/null. İçerik validator'ı v1'in kaynak işlevlerini yalnız RAM kopyasında uyarlayarak kullanır; eski modeller, dosyalar veya sonuçlar uyarlanmaz.

## 4. Ret gerekçeleri: yalnız kaynak olgularına göre

S01'in iki tam metin alıntısı, sayfa1 identity ve sayfa6 formulation, aynı537 karakterle mevcuttur. Kaynak/dependency/ham PDF hash'leri ve eski doğrulama kanıtları korunur. IMAGE_TEXT_UNAVAILABLE okunabilir metin için uygun değildir; NO_SOURCE ve MISSING_CONTEXT de bu profilde olgusal olarak yanlıştır. Kaynak belirsizliği/çatışması saptanmamışken modelin salt özgüven düşüklüğü UNCERTAIN_EVIDENCE kanıtı sayılmaz. S01 yasak skor/etiket görevi değildir.

Kaynak/dependency bozulursa, bellek/API koşulu eksikse veya tam prompt sığmazsa **host model çağrısından önce durur**; kaynak metnini kesmez. CONTEXT_BUDGET bir preflight sonucudur. S01'in bu hazır kaynak profilinde sahte ret yerine, başarısız aday veya runtime hatası varsa ham olarak kaydetmek esastır. Bu kurallar diğer18 senaryonun ret uygunluğunu uygulanmış saymaz; örneğin görsel-kutu S15 ve gerçek NO_SOURCE S16 frozen vakaları aynen durur. V2 genel şeması meşru retleri destekler; diğer case profilleri sonraki ayrı kapsam kararıdır.

## 5. Prompt, tokenizer ve kaynak bağlamı testleri

Tam user görevi frozen soru/kabul ölçütü+iki tam kaynak/ID/sayfa/scope/kind/qualifier'dır. Örnek doğru yanıt veya test fixture'ı prompt'a konmadı. Biçimsel şema request'in format alanına taşınır; v1 gibi prompt'ta ayrıca tekrar edilmez. Bu açık C05 yöntem değişikliğidir, token azaltımını gizleyen bir kesme değildir. Kaynak cümleleri ve zorunlu bağlam değiştirilmez; uzun kaynaklar için kesme yolu yoktur.

| Gerçek offline sayım | Sonuç |
|---|---:|
|Geçmiş gerçek technical smoke hizası|41|
|V1 gerçek S01 tam prompt|919|
|V2 önerilen tam system+user prompt|**724**|
|Giriş üst sınırı|1536|
|Çıktı/güvenlik/context|384 /128 /2048|
|V2 giriş+rezervler|1236; context içinde812 boşluk|
|Test amaçlı büyük ek ile tam prompt|15723; **CONTEXT_BUDGET**, ek ve kaynak kesilmedi|

Sayaç mevcut onaylı GGUF ve kurulu libllama/ggml SHA'larıyla vocabulary-only kipindedir. Native log `vocab only - skipping tensors` kaydeder; tensor/context/decode/sampler/model inference yok. Aynı v2 prompt tekrarında token hash'i aynı; system+user render ile bağımsız tek-user prefix render eşit. Token sayısı tahmini karakter oranı değildir. API grammar metni modele gizli prompt gibi eklenmedi; format alanının tamamı ayrıca dosya/wire hash ile izlenir. Gerçek sunucu yeni v2 isteğinde724 prompt sayısını doğrulamalıdır; bu henüz gerçekleşmedi. Çelişki varsa otomatik düzeltme yoktur.

`schema_prompt_regression_matrix_TEST_ONLY.json` teknik fixture matrisidir, yeni model çıktısı değildir. Refused+items, boş candidate, yanlış primary-kind ve Türkçe beyanlı İngilizce adaylar sınandı. Doğru ID ile uydurma Türkçe cümlenin insan incelemesine hâlâ ihtiyaç duyduğu da gösterildi; yanlış güven hissi yaratılmadı.

## 6. Test sonucu ve kaynak korunması

**36 yeni yöntem testi +25 gerçek tarihsel run inceleme testi geçti.** Native tokenizer ölçümü ayrıca mevcut sözlükle çalıştırıldı. İlk başarısız model yanıtı ve17 ham run dosyası aynı hash'te; uygulama sonucu hâlâ invalid refusal, kaynak sadakati başarısızdır. V1 cevap sadece teknik regresyon için RAM'de v2 metadata'sına uyarlansa bile refused+nonempty-items nedeniyle v2 genel şemadan geçmez; bu RAM fixture'ı ham model kaydının yerine yazılmadı.

Önceki3598 dosya snapshot'ı QA'dadır. AGENTS/ROADMAP, eski şema/prompt/kod/QA,19 senaryo/ölçüt,44 alıntı, Gemma/digest, GNN/SHAP/PPI ve donanım politikası korunur. Yalnız güncel run_status yeni öneri bölümü alır; eski tam baytları arşiv ve tarihsel devamda korunur. Yeni manifest değişiklik ve kanıt dosyalarını hash'ler. Kurulum, indirme, Ollama API erişimi veya yeni eğitim yapılmadı.

## 7. En fazla bir gelecek doğrulama denemesi — ŞİMDİ ÇALIŞTIRILMAZ

Plan dosyası `configs/WP12_METHOD_CORRECTION_v2_PROPOSED.json`. Ayrı kimlik **{plan['future_trial_id']}**; en fazla1 generation teşebbüsü, sıfır otomatik tekrar. Eski S01-R1 run silinmez veya bu sonuçla değiştirilmez. Önce kullanıcı yöntem onayı; sonra gerekirse normal kullanıcı PowerShell'i için bu hash'leri koruyan ayrı yürütücü hazırlanır. Bu tur yeni yürütücü veya inference komutu verilmez.

Gemma `{plan['model']}` ve digest `{plan['API_model_digest']}` aynı.2048context/384output/batch32/temperature0/seed20261108/thinkfalse/streamfalse/keep_alive0 ve60s timeout değişmez. EXPERIMENTAL_LOW_MEMORY_v1'in **yalnız bellek/timeout/OS alanları** devralınır: giriş1,5GiB RAM/1GiB GPU/3GiB commit,5 kararlı RAM/commit/OS örneği, OS basıncıfalse; runtime RAM<0,75GiB veya commit<1GiB veya OS basıncı/missing ölçümünde durma/kayıt/istemci iptali, server completion UNKNOWN olabilir. Eski v1 prompt referansı veya runner, v2 yürütücüsü gibi sunulmaz. Güvenlik/çalışabilirlik garantisi yoktur; koşullar tek gelecek istek öncesinde yeniden ölçülür.

Uygulama sırası önerisi: kullanıcı yöntem kararı → kaynak/kod/digest/bellek/API ve tam token kapıları → en fazla1 ayrı S01-R1 v2 isteği → bütün ham yanıt/ret/hata/HTTP/token/bellek/duration/hash → değişmeyen kabul ölçütleriyle schema/primary-ID/dil kontrolü → insan kaynak/semantik incelemesi → dur. Yeni yanıt düşük kaliteli veya başarısızsa aynen saklanır; v1/v2 arasında en iyi cevabı seçip genel başarı ilan edilmez. Aynı görülen vakada olası düzelme ancak yöntem geliştirme kanıtıdır, genel Türkçe/PDF doğruluğu değildir.

**Onay kapısı:** yalnız önerilen v2 yöntem ve test sonuçları kullanıcıya sunulur.19×3, yeni model, model eğitimi, otomatik açıklama yayını ve WP13 kapalıdır.

Çıktılar: v2 genel şema; ayrı Türkçe system yönergesi; S01 case şeması/request/ret profili; modüler ağsız doğrulayıcı; değişiklik ve kanıt manifestleri; test logları/token proof; `notebooks/WP12_method_correction_v2_proposal.ipynb` çalıştırılmış Türkçe notebook; `reports/figures/WP12/method_correction_v2/` gerçek token sayım grafiği; güncel run_status.
'''
    text_new(c.ROOT/'reports/WP12_METHOD_CORRECTION_v2_PROPOSAL.md',report)
    text_new(c.ROOT/'docs/plan/WP12_METHOD_CORRECTION_v2_DECISION_GATE.md',f'''# WP12 v2 yöntem karar kapısı — ÖNERİ

08.11.2026. Gerçek ilk S01-R1 başarısızlığı korunur.36 yeni+25 tarihsel test geçti; yeni prompt724 gerçek token; inference0.

| Karar | Öneri | Sınır |
|---|---|---|
|Schema|Ayrı candidate/refused oneOf, v2/tr beyanı|Schema semantik veya dil kanıtı değil|
|S01 kaynak|Tam iki alıntı ve kind-primary-ID bağı|Diğer18 vaka uygulanmış değil|
|S01 ret|Okunabilir metinde IMAGE_TEXT_UNAVAILABLE yok; kaynak profiline göre uygunsuz retler kapalı|Düşük kaliteli candidate başarıya çevrilmez|
|Dil|Açık system Türkçe, sınırlı İngilizce uyarısı, her aday için insan incelemesi|Otomatik dil/semantik başarı yok|
|Prompt|System+user, format alanında şema;724token|Gerçek server count/grammar desteği henüz sınanmadı|
|Donanım/model|EXPERIMENTAL_LOW_MEMORY_v1 yalnız hardware alanları; mevcut Gemma/digest/ayarlar|Kapılar yeniden ölçülür; garanti yok|
|Gelecek deneme|{plan['future_trial_id']};en fazla1, no retry|Henüz yürütücü/çıkarım yok; kullanıcı yöntem onayı beklenir|

Ayrıntı reports/WP12_METHOD_CORRECTION_v2_PROPOSAL.md ve QA change_manifest_v2.json. Başarılı olursa bile aynı gözlenen vaka üzerinde yöntem geliştirme kontrolüdür; bağımsız genelleme deneyi sayılmaz.19×3/model indirme/eğitim/otomatik yayın/WP13 yok.
''')
    before=(v.QA/'run_status_before.md').read_bytes();assert (c.ROOT/'run_status.md').read_bytes()==before
    prefix=f'''# WP12 — V2 yöntem düzeltme önerisi test edildi; yöntem onayı bekleniyor ·08.11.2026

- İlk gerçek S01-R1 başarısızlığı ve17 ham dosya korundu. Yeni v2 şema candidate≥1/null code, refused boşitems/tanımlıcode; S01 primary-kind-ID bağlı, uygunsuz retler kaynak profiline göre kapalı. Yeni system Türkçe zorunlu; dil beyanı/marker kontrolü semantik başarı değil, insan incelemesi zorunlu.
-36 yeni yöntem +25 tarihsel run inceleme testi geçti. Gerçek vocab-only token:eski41/919 hizası aynı, v2 tam prompt724/1536. İki tam kaynak537karakter; büyük test15723token kesilmeden CONTEXT_BUDGET. Tensor/context/decode/inference/API0.
-Gemma/digest/generationayarları ve EXPERIMENTAL_LOW_MEMORY_v1 hardware/timeout/OS alanları değişmedi. Ayrı en fazla1 {plan['future_trial_id']} planlandı; yeni yürütücü yok, yöntem onayı olmadan deneme yok. Yeni exact şemanın Ollama runtime uyumu ve server724token teyidi henüz UNKNOWN.
-Önceki3598 dosya doğrulandı; eski status tam arşivlendi.19 senaryo/ölçüt/44 alıntı ve bütün önceki sonuçlar aynı. Rapor reports/WP12_METHOD_CORRECTION_v2_PROPOSAL.md; karar kapısı docs/plan/WP12_METHOD_CORRECTION_v2_DECISION_GATE.md; notebook notebooks/WP12_method_correction_v2_proposal.ipynb; QA reports/qa/WP12/method_correction_v2/.
-19×3, model indirme/eğitim, otomatik yayın ve WP13 kapalı. Sonraki işlem kullanıcı yöntem değerlendirmesini beklemek.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''.encode('utf-8')
    (c.ROOT/'run_status.md').write_bytes(prefix+before)
    previous=c.read(v.QA/'previous_files_sha256.json')
    changed=[p for p,h in previous.items() if c.sha(c.ROOT/p)!=h];assert changed==['run_status.md'],changed
    assert c.sha(v.QA/'run_status_before.md')==previous['run_status.md']
    c.save_new(v.QA/'previous_artifacts_preservation.json',{'previous_files':len(previous),
        'unchanged_at_original_path':len(previous)-1,'only_updated_path':'run_status.md',
        'old_status_archived_exactly':True,'old_status_retained_as_exact_suffix':(c.ROOT/'run_status.md').read_bytes().endswith(before),
        'original_failed_run_unchanged':a.source_checks()['all_raw_hashes_valid'],'old_outcomes_reclassified':False,
        'actual_new_inference':0})
    print('Proposed v2 method, executed notebook and decision gate complete; no inference.')


if __name__=='__main__':main()
