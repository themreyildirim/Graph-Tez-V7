"""Yalnız offline QA ve öğretici notebook; gerçek API yürütücüsünü çağırmaz."""
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime,timezone
import wp12_openai_adapter as a
from wp12_api_security import public_sha,git_privacy_state,key_available
from wp09_close_wp10_notebooks import execute,INIT

ROOT=a.c.ROOT


def save(path,value):
    # Yalnız bu henüz kabul edilmemiş hazırlığın çalışma kanıtları yenilenebilir.
    assert path.parent==a.QA and path.name in {'offline_tests_summary.json','PowerShell_parse_and_hash.json',
        'public_documentation_verification.json','adapter_change_manifest.json','comparison_unchanged_local_and_cloud_NOT_RUN.json'}
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    command=[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p','test_wp12_openai_pilot.py','-v']
    done=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    log=a.QA/'offline_tests.log'
    if log.exists() and not (a.QA/'offline_tests_initial33.log').exists():
        (a.QA/'offline_tests_initial33.log').write_bytes(log.read_bytes())
    with log.open('w',encoding='utf-8') as f:f.write(done.stdout+done.stderr)
    total=int(re.search(r'Ran (\d+) tests',done.stderr).group(1))
    save(a.QA/'offline_tests_summary.json',{'tests':total,'returncode':done.returncode,
        'status':'PASS' if done.returncode==0 else 'FAIL','authenticated_API_calls':0,
        'transport_tests':'TEST_ONLY fake fixtures, socket creation forbidden',
        'command_without_credentials':command})
    if done.returncode:raise RuntimeError('OFFLINE_TEST_FAILURE')

    ps=r'''$tokens=$null;$errors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location) 'scripts/WP12_OpenAI_UserSingleCase_v1.ps1'),[ref]$tokens,[ref]$errors)
[pscustomobject]@{syntax_error_count=@($errors).Count;parser_version=$PSVersionTable.PSVersion.ToString();script_executed=$false}|ConvertTo-Json -Compress
'''
    parsed=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
        cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    if parsed.returncode:raise RuntimeError('POWERSHELL_PARSE_FAILURE')
    state=json.loads(parsed.stdout);state['script_sha256']=public_sha(ROOT/'scripts/WP12_OpenAI_UserSingleCase_v1.ps1')
    wrapper=(ROOT/'scripts/WP12_OpenAI_UserSingleCase_v1.ps1').read_text(encoding='utf-8')
    state['policy_and_client_pins_match']=re.findall(r"-cne '([0-9a-f]{64})'",wrapper)==[
        public_sha(a.POLICY),public_sha(ROOT/'scripts/wp12_openai_client.py')]
    assert state['syntax_error_count']==0 and state['policy_and_client_pins_match']
    save(a.QA/'PowerShell_parse_and_hash.json',state)
    save(a.QA/'public_documentation_verification.json',{
        'checked_UTC':datetime.now(timezone.utc).isoformat(),'account_model_access':'PENDING_NO_AUTHENTICATED_REQUEST',
        'Structured_Outputs_public_support':'VERIFIED_OFFICIAL_DOCS','adapter_server_acceptance':'PENDING_FIRST_USER_RUN',
        'sources':[{'topic':'model/pricing/snapshot/reasoning','url':'https://developers.openai.com/api/docs/models/gpt-5.4-mini'},
            {'topic':'supported JSON Schema subset','url':'https://developers.openai.com/api/docs/guides/structured-outputs'},
            {'topic':'exact input token count','url':'https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count'},
            {'topic':'max_output_tokens/usage','url':'https://developers.openai.com/api/reference/resources/responses/methods/create'}]})
    save(a.QA/'adapter_change_manifest.json',{
        'version':'WP12-OpenAI-Responses-adapter-v1','prior_outputs_modified':False,
        'changes':['provider/model changed from local Gemma to gpt-5.4-mini',
            'HTTP Responses instructions/input vs local chat template; no local tokenizer assumed',
            'server exact input token count before inference; max input6000/output1200 incl reasoning',
            'root result wrapper, nested oneOf->anyOf, const->typed enum, omit $schema/uniqueItems',
            'additional Turkish reminder; original V2 system prompt/source/question/criteria untouched',
            'no seed/temperature copied from Ollama; reasoning none; source ID/kind checks preserved'],
        'prior_scenario_method_development_disclosed':True,'human_review_required':True,
        'original_system_sha256':public_sha(a.v.SYSTEM),'request_sha256':public_sha(a.QA/'S01_Responses_request_NOT_SENT.json'),
        'schema_sha256':public_sha(a.QA/'S01_Structured_Outputs_schema_adapter_v1.json'),
        'Git_privacy':git_privacy_state(ROOT),'api_key_available':key_available(ROOT),
        'secret_file_contents_or_hashes_in_manifest':False,'first_authenticated_API_call':'NOT_RUN'})

    old=a.c.read(ROOT/'reports/qa/WP12/gemma_v2_review_qwen_preparation_v1/real_comparison_v1_v2_Qwen_NOT_RUN.json')
    rows=[]
    for row in old['rows']:
        rows.append({k:row.get(k) for k in ['model_method','experiment_status','pipeline_terminal_status',
            'actual_language_agent','source_faithfulness_agent','human_review','actual_server_prompt_tokens','output_tokens']})
    rows.append({'model_method':'OpenAI gpt-5.4-mini / adapter v1','experiment_status':'NOT_RUN',
        'pipeline_terminal_status':'WAIT_USER_APPROVAL','actual_language_agent':'NOT_RUN',
        'source_faithfulness_agent':'NOT_RUN','human_review':'PENDING','actual_server_prompt_tokens':None,'output_tokens':None})
    save(a.QA/'comparison_unchanged_local_and_cloud_NOT_RUN.json',{'rows':rows,
        'only_actual_local_results_are_results':True,'cloud_result_not_imputed':True})
    import pandas as pd
    pd.DataFrame(rows).to_csv(a.QA/'comparison_unchanged_local_and_cloud_NOT_RUN.csv',index=False,encoding='utf-8-sig')

    parts=[('md','''# WP12 — OpenAI API küçük pilotu: çevrimdışı hazırlık

Bu notebook **API çağırmaz**. Kaynak örnekleri, gerçek çevrimdışı test sonuçları ve maliyet planını gösterir. OpenAI yanıtı henüz NOT_RUN; birim testlerdeki sentetik yanıtlar deney sonucu değildir. Gemma V1/V2 FAIL ve Qwen NOT_RUN durumları korunur. İlk S01 API isteği ayrıca kullanıcı onayı bekler.'''),
    ('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/openai_api_pilot_v1'
F=ROOT/'reports/figures/WP12/openai_api_pilot_v1';F.mkdir(parents=True,exist_ok=True)
policy=json.loads((ROOT/'configs/WP12_OPENAI_API_PILOT_v1.json').read_text(encoding='utf-8'))
outbound=json.loads((Q/'outbound_disclosure_S01.json').read_text(encoding='utf-8'))
sources=outbound['exact_source_payload']['sources']
with pd.option_context('display.max_colwidth',None):
    display(pd.DataFrame(sources)[['physical_page','kind','quote_id','char_start','char_end','quote']])
print('Tam kaynak karakteri:',sum(len(s['quote']) for s in sources),'— API gönderimi: NOT_RUN')
'''),('md','''**Kaynak yorumu:** Erythromycin DB00199 ana ilaç kaydıyla ilişkilendirilen fiziksel1 ve6 sayfa alıntıları eksiksizdir. Tablet/etkin madde anlatımı dışına çıkılmaz; ana ilaç kaydı ürüne, tuza veya doza eşdeğerlik iddiası değildir. API yalnız bu537 karakteri ve gerekli soru/kimlik/şema/yönergeyi alacak; tam PDF/proje dosyaları gönderilmeyecektir.

## 1. Ölçülmüş çevrimdışı testler ve korunan deney durumu'''),('code',r'''
tests=json.loads((Q/'offline_tests_summary.json').read_text(encoding='utf-8'))
parse=json.loads((Q/'PowerShell_parse_and_hash.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'kontrol':'Offline testler','sonuç':tests['status'],'sayı':tests['tests']},
    {'kontrol':'PowerShell sözdizimi hatası','sonuç':parse['syntax_error_count'],'sayı':None},
    {'kontrol':'Policy/client hash eşliği','sonuç':parse['policy_and_client_pins_match'],'sayı':None},
    {'kontrol':'Kimlik doğrulamalı API çağrısı','sonuç':'YAPILMADI','sayı':0}]))
display(pd.read_csv(Q/'comparison_unchanged_local_and_cloud_NOT_RUN.csv'))
'''),('md','''**Yorum:** Testler gerçek kaynak kimliklerini doğrular; ağ açılması testte yasaktır. Timeout/HTTP hatası sonrası ikinci inference yoktur. Anahtar/yetkilendirme başlıkları kanıtlara yazılamaz. Önceki yerel başarısızlıklar başarılıya çevrilmemiştir. OpenAI erişimi, gerçek Türkçe kalitesi ve kaynak sadakati henüz ölçülmemiştir; NOT_RUN satırına sonuç skoru verilmez.

## 2. Fiyat ve bütçe: planlanan üst sınırlar'''),('code',r'''
from decimal import Decimal
rates=policy['prices_per_million_USD']
display(pd.DataFrame([{'token_türü':k,'USD_milyon_token':v} for k,v in rates.items()]))
base=(Decimal(6000)*Decimal(rates['input'])+Decimal(1200)*Decimal(rates['output']))/1000000
budget=pd.DataFrame({'plan':['Tek inference / token üst sınırı','Tek inference / %20 pay','4 vaka / token üst sınırı','4 vaka / sabit rezerv+9 HTTP','Tüm pilot / mutlak rezerv','Kullanıcının maliyet hedefi'],
    'USD':[float(base),float(base*Decimal('1.20')),float(base*4),.089,.21,.25]})
display(budget)
fig,ax=plt.subplots(figsize=(11,4.8))
bars=ax.barh(budget.plan,budget.USD,color=['#4a7d9d']*5+['#b68a4d'])
ax.bar_label(bars,labels=[f'${x:.5f}' for x in budget.USD],padding=4)
ax.set(xlim=(0,.29),xlabel='USD — PLANLAMA, gerçek API faturası değildir',title='WP12 düşük maliyet kapısı; şu ana kadar inference yok')
plt.tight_layout();plt.savefig(F/'01_cost_reservation_plan.png',dpi=160);plt.show()
'''),('md','''**Bilimsel/işletim yorumu:** Resmî standart model fiyatıyla6000 giriş +1200 toplam çıkış en kötü token hesabı$0,0099'dur; cache indirimi önceden varsayılmaz. Muhakeme varsa output toplamına dahildir ve iki kez ücretlendirilmez. Sabit rezervler fiyat garantisi değildir; gerçek API usage ve vergi/fatura farkları ayrıca değerlendirilir. Fiyat kaydı24 saat sonra eskirse yürütücü durur. Bakiye kullanıcı beyanıdır; bu notebook hesap erişimi yapmaz.

## 3. Önceden seçilen küçük aday plan ve insan incelemesi'''),('code',r'''
plan=json.loads((Q/'small_evaluation_plan_NOT_AUTHORIZED.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'senaryo':s['scenario_id'],'soru':s['question_tr'],
    'kabul_kriteri':s['acceptance_criteria_tr'],'kaynak_sayısı':len(s['evidence_ids']),
    'durum':'İlk istek öncesi onay bekliyor' if s['scenario_id']=='S01' else 'İlk sonuç değerlendirilmeden YETKİSİZ'}
    for s in plan['frozen_scenarios_unchanged']]))
display(pd.DataFrame([{'boyut':s,'şimdiki_durum':'NOT_RUN / PENDING insan incelemesi'} for s in
    ['JSON Schema','uygulama sözleşmesi','Türkçe anlatım','PDF kaynak sadakati','quote-ID/sayfa','yanlış ret/kapsam','gerçek token/latency/maliyet']]))
'''),('md','''**Karar:** API adaptöründeki kök result nesnesi ve nested anyOf yalnız teknik uyumluluk içindir; asıl V2 kaynak doğrulayıcısı da çalışır. Schema PASS, Türkçe veya olgusal doğruluk garantisi değildir. `reported_in_PDF` ile `predicted_by_GNN` ayrıdır; yeni GNN/MedDRA bilgisi üretilmez. İlk gerçek S01 sonucu incelenmeden başka vaka çalıştırılmaz;19×3/WP13/eğitim/yayın yoktur.

Resmî kaynaklar: [model/fiyat](https://developers.openai.com/api/docs/models/gpt-5.4-mini), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [tam token sayımı](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count), [Responses usage ve output sınırı](https://developers.openai.com/api/reference/resources/responses/methods/create).''')]
    # Sadece yeni WP12 API taslağının çalıştırılmış çıktısı atomik güncellenir.
    temporary_name='WP12_OpenAI_API_working_execution.ipynb'
    execute(temporary_name,parts)
    source=ROOT/'notebooks'/temporary_name
    target=ROOT/'notebooks/WP12_OpenAI_API_offline_preparation.ipynb'
    assert source.parent.resolve()==target.parent.resolve()==(ROOT/'notebooks').resolve()
    source.replace(target)
    print('Offline evidence/notebook complete; authenticated API calls=0.')


if __name__=='__main__':main()
