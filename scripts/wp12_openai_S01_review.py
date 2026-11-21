"""Kayıtlı S01 API denemesinin salt okunur bağımsız incelemesi. Ağ/anahtar yok."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import sys
import subprocess
import re
import wp12_openai_adapter as adapter
from wp12_api_security import public_sha,is_private_path

ROOT=adapter.c.ROOT
RUN=ROOT/'reports/qa/WP12/openai_api_user_runs_v1/20261108_162120_31419480b91f4396a7a018152c5c5f7b'
QA=ROOT/'reports/qa/WP12/openai_S01_run_review_v1'
CONTROL=adapter.QA/'control'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def inspect():
    hashes=read(RUN/'file_hashes.json')
    if any(Path(name).name!=name or is_private_path(name) for name in hashes):
        raise ValueError('INVALID_PUBLIC_RUN_MANIFEST')
    verified={name:public_sha(RUN/name)==digest for name,digest in hashes.items()}
    record=read(RUN/'run_record.json');request=read(RUN/'source_request.json')
    stages=[]
    for name,method,path in [('model_access','GET','/models/gpt-5.4-mini'),
        ('input_token_count','POST','/responses/input_tokens'),('inference','POST','/responses')]:
        meta=read(RUN/(name+'_HTTP_metadata.json'))
        stages.append({'stage':name,'method':method,'path':path,**meta})
    error=read(RUN/'inference_error_redacted.json');count=read(RUN/'input_token_count_response_raw.json')
    preflight=read(RUN/'cost_preflight.json');policy=read(adapter.POLICY)
    source=read(RUN/'source_provenance.json');expected=adapter.source_payload()
    components=read(RUN/'prompt_components_sha256.json')
    component_expected={
        'instructions_sha256':hashlib.sha256(request['instructions'].encode('utf-8')).hexdigest(),
        'user_content_sha256':hashlib.sha256(request['input'][0]['content'][0]['text'].encode('utf-8')).hexdigest(),
        'JSON_schema_sha256':hashlib.sha256(adapter.c.dump(request['text']['format']['schema']).encode('utf-8')).hexdigest(),
        'source_quote_sha256':[x['quote_sha256'] for x in expected['sources']]}
    guard=read(CONTROL/'BILLING_OR_LIMIT_STOP.json')
    ledgers={p.name:read(p) for p in CONTROL.glob('*.json') if not is_private_path(p)}
    prepared=read(adapter.QA/'evidence_manifest.json')['public_files']
    prep_verified={p:public_sha(ROOT/p)==digest for p,digest in prepared.items() if p!='run_status.md'}
    public_dependencies={p:public_sha(ROOT/p)==digest for p,digest in policy['immutable_public_inputs_sha256'].items()}
    no_model_output=not any((RUN/name).exists() for name in ['inference_response_raw.json','validated_JSON.json','usage_and_token_cost.json'])
    checks={'run_file_hashes_all_match':all(verified.values()),'run_manifest_matches_file_inventory':
        {p.name for p in RUN.iterdir() if p.is_file()}==set(hashes)|{'file_hashes.json'},
        'run_request_hash_matches_record':public_sha(RUN/'source_request.json')==record['source_request_sha256'],
        'prompt_component_hashes_match':components==component_expected,
        'frozen_source_and_request_equal':source==expected and request==adapter.build_request(),
        'prepared_public_artifacts_unchanged':all(prep_verified.values()),
        'policy_public_dependencies_unchanged':all(public_dependencies.values()),
        'one_recorded_inference_attempt':record['inference_attempts']==1 and len([p for p in ledgers if p.startswith('inference_reservation_')])==1,
        'three_HTTP_attempts':record['http_attempts']==3 and len([p for p in ledgers if p.startswith('http_')])==3,
        'stages_200_200_429':[s['HTTP_status'] for s in stages]==[200,200,429],
        'quota_error_exact':error.get('type')=='insufficient_quota' and error.get('code')=='credit_balance_exhausted',
        'no_generated_explanation_or_usage':no_model_output,
        'preflight_count_and_cost_match':count['input_tokens']==preflight['input_tokens_exact_server_preflight'] and
            adapter.estimate_upper(count['input_tokens'],policy)==preflight,
        'billing_guard_retained':guard['status']=='INFERENCE_COMPLETION_OR_COST_UNKNOWN_NO_RETRY',
        'automatic_retry_off':record['automatic_retry'] is False,
        'no_automatic_release':record['automatic_release'] is False}
    return {'classification':'API_BILLING_BLOCKED_NO_MODEL_OUTPUT','stages':stages,'provider_error':error,
        'model_metadata':read(RUN/'model_access_response_raw.json'),'requested_model':record['model_requested'],
        'generated_model_snapshot':'UNKNOWN_NO_GENERATED_RESPONSE','inference_attempts':1,
        'completed_generations':0,'input_token_preflight_count':count['input_tokens'],
        'generated_output_tokens':None,'actual_billed_input_tokens':None,'actual_cached_input_tokens':None,
        'actual_reasoning_tokens':None,'actual_usage_token_cost_USD':None,
        'actual_billing_status':'UNKNOWN_NO_USAGE_NO_ACCOUNT_BILLING_READ',
        'preflight_cost_NOT_actual_charge':preflight,
        'recorded_reservations_NOT_actual_charge_USD':str(Decimal(policy['reservation_per_inference_USD'])+3*Decimal(policy['reservation_per_HTTP_USD'])),
        'schema_status':'NOT_EVALUABLE_NO_OUTPUT','Turkish_quality':'NOT_EVALUABLE_NO_OUTPUT',
        'source_faithfulness':'NOT_EVALUABLE_NO_OUTPUT','human_review':'PENDING_NO_OUTPUT_TO_REVIEW',
        'actual_account_balance_and_organization':'UNKNOWN_NOT_QUERIED','checks':checks,
        'raw_run_files_verified':len(verified),'prepared_public_artifacts_verified_except_status':len(prep_verified),
        'new_authenticated_API_requests_during_review':0,'retry_or_guard_reset':False,
        'official_error_reference':'https://developers.openai.com/api/docs/guides/error-codes'}


def main():
    QA.mkdir(parents=True,exist_ok=False)
    protected=[*RUN.iterdir(),*CONTROL.glob('*.json')]
    protected=[p for p in protected if not is_private_path(p) and p.is_file()]
    before={p.relative_to(ROOT).as_posix():public_sha(p) for p in protected}
    adapter.c.save_new(QA/'protected_real_run_and_controls_sha256.json',before)
    prior_status=(ROOT/'run_status.md').read_bytes();(QA/'run_status_before.md').write_bytes(prior_status)
    review=inspect();assert all(review['checks'].values())
    adapter.c.save_new(QA/'independent_review.json',review)
    import pandas as pd
    pd.DataFrame(review['stages']).to_csv(QA/'real_HTTP_stages.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame([{'check':k,'pass':v} for k,v in review['checks'].items()]).to_csv(QA/'review_checks.csv',index=False,encoding='utf-8-sig')
    # Sadece yeni bağımsız testler; eski35 test loguna veya tek-deneme slotuna dokunulmaz.
    proc=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests',
        '-p','test_wp12_openai_S01_review.py','-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    (QA/'review_tests.log').write_text(proc.stdout+proc.stderr,encoding='utf-8')
    total=int(re.search(r'Ran (\d+) tests',proc.stderr).group(1))
    adapter.c.save_new(QA/'test_summary.json',{'tests':total,'returncode':proc.returncode,
        'status':'PASS' if proc.returncode==0 else 'FAIL','new_API_requests':0})
    assert proc.returncode==0
    from wp09_close_wp10_notebooks import execute,INIT
    execute('WP12_OpenAI_S01_actual_run_review.ipynb',[
        ('md','''# WP12 — Gerçek S01 API denemesi: bağımsız salt okunur inceleme

Bu notebook yeni API isteği göndermez. Kullanıcının normal PowerShell'de çalıştırdığı kayıt üç HTTP aşaması içerir. Başarısız API üretimi, modelin Türkçe veya kaynak sadakati başarısızlığı olarak etiketlenmez. Önceki Gemma V1/V2 ve Qwen durumları değişmez.'''),
        ('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/openai_S01_run_review_v1'
F=ROOT/'reports/figures/WP12/openai_S01_run_review_v1';F.mkdir(parents=True,exist_ok=True)
r=json.loads((Q/'independent_review.json').read_text(encoding='utf-8'))
stages=pd.read_csv(Q/'real_HTTP_stages.csv');display(stages)
fig,ax=plt.subplots(figsize=(9,4.5))
bars=ax.bar(['Model erişimi','Giriş token sayımı','Üretim isteği'],stages.elapsed_seconds,color=['#4b886f','#4b886f','#b75d55'])
ax.bar_label(bars,labels=[f"HTTP {x}" for x in stages.HTTP_status],padding=4)
ax.set(ylabel='Kaydedilmiş HTTP süresi (s)',ylim=(0,1.65),title='Gerçek S01: erişim ve sayım geçti; üretim kredi hatasıyla reddedildi')
plt.tight_layout();plt.savefig(F/'01_real_HTTP_stages.png',dpi=160);plt.show()
'''),('md','''**Yorum:** Model GET ve tam giriş sayımı200, üretim429'dur. Üretim isteği gerçekten gönderilmiş, fakat kaynaklı açıklama alınamamıştır. Bu üç çağrıyı üç inference olarak saymıyoruz: bir üretim denemesi, sıfır tamamlanmış üretim vardır. Süreler model token üretim gecikmesi değildir.

## Kaynak, token ve bütçe'''),('code',r'''
display(pd.DataFrame([{'alan':'Sayım endpoint giriş tokenı','değer':r['input_token_preflight_count']},
 {'alan':'Tamamlanmış üretim','değer':r['completed_generations']},
 {'alan':'Varsayımsal inference maliyet üstü USD','değer':r['preflight_cost_NOT_actual_charge']['worst_case_no_cache_USD']},
 {'alan':'%20 paylı planlama USD','değer':r['preflight_cost_NOT_actual_charge']['margin_upper_USD']},
 {'alan':'Ayrılmış rezerv; gerçek ücret değil USD','değer':r['recorded_reservations_NOT_actual_charge_USD']},
 {'alan':'Gerçek ücret / usage','değer':'UNKNOWN / kullanım yanıtı yok'}]))
display(pd.DataFrame([r['provider_error']]))
'''),('md','''**Yorum:**1236 token, üretimin faturalandırılmış giriş miktarı değildir; ayrı sayım endpoint'inin önkontrol sonucudur. $0,006327 varsayımsal üst token maliyeti ve$0,0075924 paylı hesap gerçek ücret değildir. Usage, output/cache/reasoning tokenları ve gerçek fatura UNKNOWN tutulur; sıfır ücret varsayılmaz. Tam error.message güvenlik nedeniyle saklanmadığından bilinmiyor; kayıtlı type/code yeterince açıktır.

## Teknik kontrol ve bilimsel sınıflandırma'''),('code',r'''
display(pd.read_csv(Q/'review_checks.csv'))
display(pd.DataFrame([{'boyut':k,'durum':r[k]} for k in ['classification','schema_status','Turkish_quality','source_faithfulness','human_review']]))
display(pd.DataFrame([json.loads((Q/'test_summary.json').read_text(encoding='utf-8'))]))
'''),('md','''**Sonuç:** İki özgün alıntı, S01 sorusu, kaynak kimlikleri, prompt ve şema onaylı istekle aynı; hash kontrolleri başarılı. Şema/Türkçe/kaynak sadakati yanıt olmadığı için değerlendirilemez.Yalnız429 genel koduna bakılarak otomatik retry yapılmadı; özel `credit_balance_exhausted` kodu faturalama engelidir. Modelin kötü açıklama ürettiği sonucu çıkarılamaz.

En küçük sonraki adım: kullanılan API anahtarının bağlı olduğu organizasyonda API Billing bakiyesini kontrol etmek. Kullanıcının gördüğü$5 ile bu isteğin organizasyon/bakiyesi arasındaki ilişki loglardan saptanamaz. Yeni ödeme, anahtar değişimi, slot resetleme veya tekrar bu notebook tarafından yapılmaz. Mevcut billing-stop ve ilk başarısız kayıt korunur. [OpenAI Docs hata açıklaması](https://developers.openai.com/api/docs/guides/error-codes).''')])
    report='''# WP12 — Gerçek OpenAI S01 denemesi: kredi engeli

08.11.2026. Kullanıcı run: `20261108_162120_31419480b91f4396a7a018152c5c5f7b`.

**Kesin teknik bulgu:** üretim isteği HTTP429, `type=insufficient_quota`, `code=credit_balance_exhausted` ile reddedilmiş. Bir gerçek inference isteği gönderilmiş; tamamlanmış model açıklaması yok. Bu bir dil/kaynak sadakati değerlendirme başarısızlığı değildir. Açıklama kalitesi **NOT_EVALUABLE**, insan incelemesi PENDING kalır.

| Aşama | HTTP | Kayıtlı süre | Sonuç |
|---|---:|---:|---|
| Model GET |200|0,953 s|gpt-5.4-mini metadata erişimi başarılı|
| Tam giriş token sayımı |200|1,219 s|1236 giriş tokenı; token/maliyet kapısı geçti|
| Responses üretim POST |429|1,000 s|credit_balance_exhausted; açıklama/usage yok|

OpenAI Docs bu özel kodu, isteğin organizasyonundaki ön ödemeli kredi bakiyesinin tükenmiş olması olarak açıklar. Sıradan istek hızı sınırlamasıyla aynı şey değildir; tekrar denemek kredi engelini çözmez. [Resmî hata sözleşmesi](https://developers.openai.com/api/docs/guides/error-codes).

**Bilinmeyenler:** Kullanıcının hesabında görüntülenen yaklaşık$5'in hangi organizasyon/projeyle ilişkili olduğu; bu anahtarın organizasyon kimliği; güncel fatura bakiyesi; tüketim/aktivasyon ayrıntıları bu kayıtlardan belirlenemez. Hesap/billing API'si sorgulanmadı ve anahtar yüklenmedi. Bakiye hakkında log dışı neden uydurulmadı. Model listesine erişim ücretli üretim kotasını kanıtlamaz; token endpoint'inin kabulü de Structured Outputs üretim doğruluğu kanıtı değildir.

**Maliyet:**1236 önkontrol tokenı, gerçek ücretli inference usage alanı değildir. Dondurulmuş1200 çıkış tavanıyla varsayımsal inference token üstü$0,006327; %20 payla$0,00759240. Kullanım cevabı olmadığından gerçek input/cached/output/reasoning ve ücret UNKNOWN; sıfır maliyet olarak yazılmaz. Muhasebe rezervi$0,02+3×$0,001=$0,023 olup gerçek fatura değildir. Üretim HTTP request-ID: `req_f24e3f2dea264051898f8a35e59d3a39`. Tam model snapshot kimliği üretilmiş cevap olmadığı için UNKNOWN; doğrulanan metadata ID gpt-5.4-mini'dir.

**Bütünlük:** Kayıtlı11 dosya hash'i,12 dosyalık ham klasör envanteri, request/component hash'leri, hazırlığın status dışı33 manifest dosyası ve dondurulmuş kamusal bağımlılık hash'leri kontrol edildi. S01 DB00199, fiziksel1/6, iki tam alıntı537 karakter ve onaylı şema/prompt aynı. Ham kullanıcı klasörü, altı kontrol/rezerv dosyası ve eski35 test logu değiştirilmedi. Billing-stop orijinal genel UNKNOWN adıyla korundu; bu yeni rapor özel429 kredi nedenini ayrıca kaydeder. API hata gövdesi güvenlik politikasıyla redakte edilmiş; tam error.message kaydı yoktur. Gizli .env dosyası/anahtar okunmadı, hash'lenmedi veya manifestlenmedi.

**En küçük gerekli adım:** Kullanıcı API panelinde kullanılan anahtarın bağlı olduğu organizasyonu ve API Billing kullanılabilir kredisini kontrol etmeli. Bakiye varsa aynı organizasyon/proje anahtarının kullanıldığını doğrulamalı. Bu denemede ödeme/anahtar/model/prompt/token bütçesi düzeltmesi veya yükseltmesi yapılmadı. Bir sonraki tek-deneme ancak faturalama durumu açıklığa kavuştuktan sonra, eski slotlar silinmeden ayrı izlenebilir kayıtla hazırlanabilir. Mevcut komut yeniden çalıştırılmamalı; otomatik retry yoktur.

Yeni bağımsız testler ve gerçek üç HTTP aşamasını gösteren görsel/notebook bu inceleme QA dizinindedir. Gemma V1/V2 FAIL ve Qwen NOT_RUN aynı kalır. OpenAI sonucu **API_BILLING_BLOCKED_NO_MODEL_OUTPUT**; başarılı açıklama değildir. Yeni API isteği, eğitim, senaryo değişikliği,19×3, yayın veya WP13 yoktur.
'''
    with (ROOT/'reports/WP12_OPENAI_S01_ACTUAL_RUN_REVIEW.md').open('x',encoding='utf-8') as f:f.write(report)
    prefix=f'''# WP12 — Gerçek S01 API isteği kredi hatasıyla durdu ·08.11.2026

- Kullanıcı run162120_31419480b91f4396a7a018152c5c5f7b: GETmodel200, input-count200/1236token, üretimPOST429 insufficient_quota/credit_balance_exhausted. Bir inference denemesi, sıfır tamamlanmış açıklama. Dil/şema/kaynak NOT_EVALUABLE; model kalitesine başarısızlık atfedilmez.
-11run hash'i/12dosya,33hazırlık manifesti (status hariç), kaynak/prompt/hash ve dondurulmuş S01 doğrulandı. Hamrun/kontrol/rezerv/önceki35testler korundu; billing-stop veya tek-deneme slotu sıfırlanmadı. Yeni inceleme{total}test PASS. Anahtar/.env okunmadı veya hash'lenmedi.
- Gerçek API usage/maliyet UNKNOWN;1236önkontrol ve .006327USD varsayımsal tokenüstü gerçek ücret değildir. .023USDrezerv tüketildi/korundu; fatura bakiyesi okunmadı. Kullanıcının beyan ettiği5USD ile bu anahtarın organizasyonu arasındaki ilişki UNKNOWN. API Billing/organizasyon kullanıcı kontrolü bekleniyor; yeni inference yok.
- Rapor reports/WP12_OPENAI_S01_ACTUAL_RUN_REVIEW.md; notebook notebooks/WP12_OpenAI_S01_actual_run_review.ipynb; QA reports/qa/WP12/openai_S01_run_review_v1/. GemmaV1/V2 FAIL,QwenNOT_RUN aynı.19×3/yayın/eğitim/WP13 yok.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+prior_status)
    assert all(public_sha(ROOT/p)==digest for p,digest in before.items())
    adapter.c.save_new(QA/'final_preservation.json',{'protected_real_run_and_controls':len(before),'all_unchanged':True,
        'prior_status_bytes_retained':(ROOT/'run_status.md').read_bytes().endswith(prior_status),'new_API_requests':0,'tests_passed':total})
    files=[ROOT/'scripts/wp12_openai_S01_review.py',ROOT/'tests/test_wp12_openai_S01_review.py',
        ROOT/'reports/WP12_OPENAI_S01_ACTUAL_RUN_REVIEW.md',ROOT/'notebooks/WP12_OpenAI_S01_actual_run_review.ipynb',
        ROOT/'reports/figures/WP12/openai_S01_run_review_v1/01_real_HTTP_stages.png',ROOT/'run_status.md',*QA.iterdir()]
    manifest={p.relative_to(ROOT).as_posix():public_sha(p) for p in files if not is_private_path(p) and p.is_file()}
    adapter.c.save_new(QA/'evidence_manifest.json',manifest)
    print(json.dumps({'review':review['classification'],'tests':total,'protected_files':len(before),'new_API_requests':0}))


if __name__=='__main__':main()
