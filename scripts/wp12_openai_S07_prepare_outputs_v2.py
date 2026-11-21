"""S07/S04 kaynak ve bütçe ön hazırlığı: ölçülmüş yerel veriler, API yok."""
import json
import re
import sys
import subprocess
from pathlib import Path
import wp12_openai_scenarios_v2 as s
import wp12_openai_pilot_budget_v2 as b
import wp12_openai_S07_v2_client as client
from wp12_api_security import public_sha,is_private_path


def save(name,value):s.old.c.save_new(s.QA/name,value)


def main():
    p=b.verify()
    script=s.ROOT/'scripts/WP12_OpenAI_S07_SingleCase_v2.ps1'
    ps=r'''$tokens=$null;$errors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location) 'scripts/WP12_OpenAI_S07_SingleCase_v2.ps1'),[ref]$tokens,[ref]$errors)
[pscustomobject]@{syntax_errors=@($errors).Count;parser_version=$PSVersionTable.PSVersion.ToString();executed=$false}|ConvertTo-Json -Compress
'''
    parsed=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],cwd=s.ROOT,capture_output=True,text=True,encoding='utf-8')
    assert parsed.returncode==0
    check=json.loads(parsed.stdout);check['script_sha256']=public_sha(script)
    check['policy_client_pins_match']=re.findall(r"-cne '([0-9a-f]{64})'",script.read_text(encoding='utf-8'))==[
        public_sha(b.POLICY),public_sha(s.ROOT/'scripts/wp12_openai_S07_v2_client.py')]
    assert check['syntax_errors']==0 and check['policy_client_pins_match'];save('PowerShell_parse_and_hash.json',check)
    tests=s.old.c.read(s.QA/'test_summary.json');assert tests['returncode']==0 and tests['tests']==28
    import pandas as pd
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import networkx as nx
    F=s.ROOT/'reports/figures/WP12/openai_S07_preparation_v2';F.mkdir(parents=True,exist_ok=False)
    rows=[];statuses=[]
    for case in ['S07','S04']:
        ctx,payload,deps,ann=s.context(case)
        for x in payload['sources']:
            rows.append({'scenario':case,'source_key':ann[x['quote_id']]['key'],'quote_id':x['quote_id'],
                'physical_page':x['physical_page'],'char_start':x['char_start'],'char_end':x['char_end'],
                'scope':x['scope'],'kind':x['kind'],'qualifier_exact':x['qualifier'],'quote_exact':x['quote'],
                'required_context_quote_ids':';'.join(x['required_context_quote_ids']),
                'source_characters':len(x['quote'])})
        statuses.append({'scenario':case,'execution_status':'NOT_RUN' if case=='S07' else 'LOCKED_NOT_RUN',
            'source_quotes':3,'source_characters_with_overlap':sum(len(x['quote']) for x in payload['sources']),
            'actual_prompt_tokens':None,'actual_cost_USD':None,'agent_review':'PENDING','human_review':'PENDING',
            'server_Structured_Outputs_acceptance':'PENDING_FIRST_REAL_RESPONSE'})
    pd.DataFrame(rows).to_csv(s.QA/'real_source_dependency_table.csv',index=False,encoding='utf-8-sig')
    save('scenario_statuses_NOT_RUN.json',statuses)
    pd.DataFrame(statuses).to_csv(s.QA/'scenario_statuses_NOT_RUN.csv',index=False,encoding='utf-8-sig')
    save('method_adapter_change_manifest_v2.json',{'version':'WP12-source-scenarios-adapter-v2',
        'frozen_sources_questions_criteria_changed':False,'case_results_seen_before_method':False,
        'S01_response_or_method_files_changed':False,'S01_fixed_sentence_semantic_checks_used':False,
        'changes':['S01-specific instructions replaced by generic system + separate S07/S04 instructions',
            'three primaries and transitive dependency citation coverage; source scopes/purposes unchanged',
            'S07 exception may use two short sentences to retain both original source sentences',
            'refused empty-items branch records refusals; inappropriate refusal is not application success',
            'separate budget-v2 HTTP ceiling30 with prior6 carried, inference10 total and USD0.25 cap'],
        'human_S01_positive_statement_receipt_only':True,'formal_human_QA_unchanged':True,
        'server_schema_runtime_status':'PENDING_REAL_USER_RUN','new_API_requests':0})
    # Gerçek kaynak bağımlılıkları; kesikli oklar mevcut sözleşme/geçişli kapanıştır.
    fig,axs=plt.subplots(1,2,figsize=(14,5))
    for case,ax in zip(['S07','S04'],axs):
        ctx,payload,deps,ann=s.context(case);ids=ctx['scenario']['evidence_ids']
        key={qid:ann[qid]['key'] for qid in ids};G=nx.DiGraph();G.add_nodes_from(key.values())
        original=[];extra=[]
        for qid in ids:
            for context in deps[qid]:
                edge=(key[qid],key[context]);G.add_edge(*edge)
                (original if context in ann[qid]['context_quote_ids'] else extra).append(edge)
        if case=='S07':pos={'D_class_renal':(0,1),'D_class_intro':(-1,0),'D_BUN_exception':(1,0)}
        else:pos={'E_unknown_frequency':(0,1),'E_adverse_p5':(0,.5),'E_adverse_p4':(0,0)}
        nx.draw_networkx_nodes(G,pos,ax=ax,node_size=4300,node_color='#d7e5eb',edgecolors='#56778b')
        nx.draw_networkx_labels(G,pos,ax=ax,font_size=10)
        nx.draw_networkx_edges(G,pos,edgelist=original,ax=ax,arrows=True,node_size=4300,arrowsize=20,width=2,edge_color='#56778b')
        nx.draw_networkx_edges(G,pos,edgelist=extra,ax=ax,arrows=True,node_size=4300,arrowsize=20,width=2,style='dashed',edge_color='#aa7b35')
        ax.set_title(case+' — zorunlu alıntı bağlamı',fontsize=14);ax.set_axis_off();ax.margins(.25)
    fig.text(.02,.015,'Ok: bu alıntı için gereken bağlam. Kesikli: kabul edilmiş renal/BUN ek kuralı. S04 kapanışı unknown → p5 → p4. Semantik doğruluk garantisi değildir.',fontsize=10)
    plt.tight_layout(rect=(0,.06,1,1));plt.savefig(F/'01_real_source_dependencies.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(13,4.5))
    vals=[6,10,30];labels=['Kayıtlı kullanılmış HTTP','Eski v1 HTTP tavanı','Önerilen v2 HTTP tavanı']
    bars=axs[0].barh(labels,vals,color=['#527b91','#abb8bf','#bb9865']);axs[0].bar_label(bars,padding=3);axs[0].set(xlim=(0,35),title='Sayaç6 korunur; teklif30 toplam HTTP')
    vals=[.046,.069,.23];labels=['Korunan gerçek rezerv','S07 tam giderse PLAN','10inference/30HTTP üst PLAN']
    bars=axs[1].barh(labels,vals,color=['#527b91','#86a596','#bb9865']);axs[1].bar_label(bars,labels=[f'${v:.3f}' for v in vals],padding=3)
    axs[1].axvline(.25,color='#555',linestyle='--');axs[1].set(xlim=(0,.285),title='Operasyonel tavan $0,25',xlabel='USD — rezerv/plan, fatura değildir')
    plt.tight_layout();plt.savefig(F/'02_budget_v1_and_proposed_v2.png',dpi=170);plt.close(fig)

    from wp09_close_wp10_notebooks import execute,INIT
    execute('WP12_OpenAI_S07_S04_preparation_v2.ipynb',[
        ('md','''# WP12 — S07 öncelikli tek deneme; S04 kilitli hazırlık

Bu notebook API çağırmaz; kaynak tablolarını, gerçek mevcut sayaçları ve testleri gösterir. S07 ve S04 henüz **NOT_RUN**. Kullanıcının S01 için olumlu insan beyanı ayrı alındıdır; resmî QA **PENDING** aynen kalır. Bütçe genişletme teklifi yeni sürümdür; eski kayıtlar sıfırlanmaz.'''),
        ('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/openai_S07_preparation_v2'
F=ROOT/'reports/figures/WP12/openai_S07_preparation_v2'
table=pd.read_csv(Q/'real_source_dependency_table.csv')
with pd.option_context('display.max_colwidth',None):
    display(table[table.scenario=='S07'][['source_key','physical_page','scope','kind','qualifier_exact','quote_exact','required_context_quote_ids']])
from IPython.display import Image
display(Image(filename=str(F/'01_real_source_dependencies.png')))
'''),('md','''**S07 yorumu:** Renal/BUN bildirimi tetracycline sınıfına aittir. Sınıf girişi ve doxycycline istisnasının iki tam cümlesi çıkarılamaz. Kaynak-ID listesinde üçünün bulunması, modelin istisnayı veya “studies to date indicate” koşulunu doğru Türkçeyle aktaracağını kanıtlamaz. Gerçek çıktı ajan ve insan tarafından ayrıca okunacaktır.

## S04 — farklı kanıt türü, yalnız hazırlık'''),('code',r'''
with pd.option_context('display.max_colwidth',None):
    display(table[table.scenario=='S04'][['source_key','physical_page','scope','qualifier_exact','quote_exact','required_context_quote_ids']])
display(pd.read_csv(Q/'scenario_statuses_NOT_RUN.csv'))
'''),('md','''**S04 yorumu:** Bilinmeyen sıklık alt alıntısı, sayfa5 devamı üzerinden sayfa4 bağlamına bağlıdır. Toplam3803karakter örtüşen alıntıları içerir; sessiz tekilleştirme/kesme yapılmadı. Bilinmeyen sıklık sayısal risk/yaygınlık veya kesin yokluk değildir. S04 şeması hazır olsa da yürütücü S04 bayrağı kabul etmez; S07 sonucu görülmeden çalıştırılamaz.

## Bütçe v2 — teklif ve korunan gerçek sayaç'''),('code',r'''
p=json.loads((ROOT/'configs/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.json').read_text(encoding='utf-8'))
baseline=json.loads((Q/'budget_baseline_real_records.json').read_text(encoding='utf-8'));display(pd.DataFrame([baseline]))
display(pd.DataFrame([{'sınır':'HTTP toplam','v1':10,'v2_teklif':30,'mevcut':6},
 {'sınır':'inference toplam','v1':10,'v2_teklif':10,'mevcut':2},
 {'sınır':'Operasyonel rezerv USD','v1':.24,'v2_teklif':.25,'mevcut':.046}]))
display(Image(filename=str(F/'02_budget_v1_and_proposed_v2.png')))
'''),('md','''**Yorum:**30HTTP, toplam10inference için gereken3'er çağrının üst planıdır; ek10inference değildir. Eski2rezerv sayılınca en fazla8inference rezerv kapasitesi kalır.10×$0,02 +30×$0,001 =$0,23; $0,25 tavan altında. Bu tur yalnız S07'nin bir üretimi yetkilidir. Her HTTP'de finans/hash, her inference öncesi tam sunucu tokenı/maliyet kapısı vardır. Eski kredi-hatalı maliyet UNKNOWN; tam rezerv korunur. Para bakiyesi/fatura sorgulanmadı.

## Teknik/ajan/insan ayrımı'''),('code',r'''
tests=json.loads((Q/'test_summary.json').read_text(encoding='utf-8'));display(pd.DataFrame([tests]))
display(pd.DataFrame([json.loads((Q/'PowerShell_parse_and_hash.json').read_text(encoding='utf-8'))]))
receipt=json.loads((Q/'S01_positive_user_statement_NOT_FORMAL_QA.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'alan':'S01 kullanıcı beyanı','durum':receipt['user_statement_polarity']},
 {'alan':'Formal insan QA','durum':receipt['formal_QA_status']},
 {'alan':'İnceleyici kimliği','durum':receipt['actual_reviewer_identity']},
 {'alan':'S07 yeni API/ajan/insan sonucu','durum':'NOT_RUN / PENDING / PENDING'}]))
'''),('md','''**Yorum:**28offline testte doğru quote-ID'li yanlış-anlam fixture'ları teknik kapıyı geçebilir; semantic_success null ve insanPENDING kalır. Bu test bir model sonucu değildir, otomatik semantik değerlendirme iddiasının sınırını gösterir. S01 sabit iki cümlesi yeni senaryoların doğrulayıcısı olarak kullanılmaz.

İnsan formal kararı için açık proje inceleyici kimliği/rolü, tam run/response hash'i, item ve quote kapsamı, karar, zaman dilimli tarih ve teyit referansı gerekir. Registry/template aktif değildir; doğrulayıcı yalnız kontrol eder, dosya yazmaz. Kullanıcının olumlu beyanı önceki PENDING dosyasını değiştirmez. S07 yetkisi bu turdaki açık kullanıcı isteğidir.

**Durma noktası:** Normal PowerShell'de `-AcceptBudgetV2 -RunS07` bütçe teklifini yalnız bu tek S07 yürütümü için açıkça kabul eder. Bu notebook gerçek istek göndermez. Yeni yanıtın ham gövde/usage/schema/source dosyaları saklanacak, kaynak anlamı ayrıca incelenecektir. S04/19×3/WP13/yayın/eğitim kapalıdır.

[Bütçe ve adaptör sözleşmesi](../docs/plan/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.md); [insan kontrolü](../docs/plan/WP12_HUMAN_DECISION_CONTROL_v1.md).''')])

    report=r'''# WP12 — S07 tek-deneme hazırlığı ve bütçe v2 önerisi

08.11.2026. **S07 NOT_RUN, S04 LOCKED_NOT_RUN; hiçbir yeni API isteği yapılmadı.**

## S01 insan beyanı

Kullanıcı iki S01 cümlesinin kaynakla uyumuna ilişkin olumlu insan beyanı verdi. Bu ifade tam run/raw-response hash'ine bağlı ayrı beyan alındısına yazıldı. Mevcut model `human_review=PENDING`, `human_review_pending.json`, eski QA ve manifestler değiştirilmedi. Kimliği işletim sistemi adından çıkarılmadı. Formal olay için kullanıcı tarafından adlandırılmış proje inceleyici kimliği/rolü, yetki kaydı, inceleme zamanı, açık karar ve iki item/quote kapsamı gerekir. Teknik saf doğrulayıcı yazma/yayınlama yapmaz. Template ve registry henüz aktif değildir; bu tur formal APPROVED olayı yoktur. Süreç `docs/plan/WP12_HUMAN_DECISION_CONTROL_v1.md` içinde açıklanmıştır. S07 hazırlığının yetkisi ayrıca bu turdaki açık kullanıcı isteğidir.

## Kaynak profilleri ve kapsam

| Senaryo | Gerçek kaynak | Alıntı / karakter | Yeni çalışma |
|---|---|---:|---|
| S07 |Doxycycline, fiziksel7 sınıf/renal +fiziksel4 BUN istisnası, DB00254|3 /380|Tek deneme yürütücüsü hazır; NOT_RUN|
| S04 |Erythromycin, fiziksel4/5 ve bilinmeyen sıklık, DB00199|3 /3803|Şema/bağlam hazır; yürütme kilitli|

3803 sayısı örtüşen sayfa5 ve alt-alıntıyı içerir; benzersiz PDF karakteri değildir. Soru, kabul kriteri, quote-ID, sayfa/aralık, kaynak metni, scope/purpose/qualifier aynen korunur. Yeni kaynak veya kanıt eklenmez. Ham iki PDF hash'i ve kabul edilmiş kaynak bundle/anotasyon hash'leri doğrulanır; büyük diğer kaynaklar yeniden taranmaz.

S07 renal item; sınıf girişini ve iki cümlelik D_BUN_exception'ı birlikte cite etmelidir. Tetracycline sınıf anlatımı doğrudan doxycycline olayı olarak sunulmamalı; apparently dose related, may cause, studies to date indicate ve impaired renal function koşulları anlamca korunmalıdır. İstisna evrensel güvenlik veya kesin pozitif/negatif etiketi değildir.

S04 bilinmeyen sıklık; p5 devamı üzerinden p4 bağlamını da taşımalıdır. Not known/frequency cannot be estimated ifadesi risk yüzdesi/yaygınlık veya kesin yoklukla değiştirilemez. Bağlam alıntıları kesilmez; kaynak nitelemeleri özet sırasında sessizce silinmemelidir. `semantic_review_plan.json` dosyaları bu kaynak türlerine özgü gerçek inceleme sorularını içerir; henüz model sonucu değildir.

![Gerçek kaynak bağlamları](figures/WP12/openai_S07_preparation_v2/01_real_source_dependencies.png)

Grafik, seçilmiş gerçek alıntıların kaynak-bağlam bağımlılıklarını gösterir. Kesikli kenar önceki kabul edilmiş renal/BUN bağlam kuralıdır. Bu yapı semantik başarıyı garanti etmez; model ilişkiyi yanlış aktarabilir.

## Model, şema ve yöntem sürümü

gpt-5.4-mini aynı kalır; reasoning none, input6000/output1200,90s timeout, store=false, truncation disabled, tools boş, otomatik retry/Batch yok. Yeni model/LLM indirme/eğitim yoktur. S01'e özgü iki sabit cümle testi kullanılmaz. Yeni genel system ve ayrı S07/S04 yönergeleri, bu senaryoların çıktıları görülmeden sürümlendi. S07 istisna item'ında kaynak iki cümlesini korumak için iki kısa Türkçe cümleye izin verilir; eski S01 prompt veya yanıtı değiştirilmez.

Root object/result nested anyOf, candidate/refused dalları, required alanlar ve additionalProperties=false ile Structured Outputs alt kümesi kullanılır. Candidate tam3item; refused boş items ister. Her birincil kaynağa ait scope/kind, izinli ID ve gereken bağlam uzunluğu şemada sınırlandırılır. Birincil ID sırası, tekrar, üç farklı birincil kapsamı ve geçişli bağımlılıklar ayrıca uygulamada test edilir. Sunucunun bu yeni şemayı kabulü ilk gerçek çağrıya kadar PENDING'dir; offline geçiş API kabulü sayılmaz. [Resmî Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Tam okunur/izinli bağlam varken modelin NO_SOURCE/IMAGE_TEXT_UNAVAILABLE vb. reddi kaydedilir, fakat uygulama başarısı olmaz. Host eksik kaynak/bütçe/context için inference öncesi durur; native API refusal ayrı tutulur. JSON veya doğru ID tek başına semantik başarı değildir. Testlerde doğruID ile bilerek yanlış BUN/olasılık cümlesi teknik kapıyı geçebilir; semantic_success null, ajan/insan PENDING kalır. Bu bir genel semantik classifier değildir. Gerçek yanıt geldikten sonra her iddia kaynakla ayrıca okunacaktır.

## Bütçe v2 — eski sayaçlar taşınır

| Kural | V1 | V2 teklif |
|---|---:|---:|
| Toplam HTTP üst sınırı |10|30|
| Mevcut kullanılmış HTTP |6|6, sıfırlanmaz|
| Toplam inference rezervi/denemesi |en fazla10|en fazla10, ek10 değil|
| Mevcut inference rezervi |2|2, sıfırlanmaz|
| Operasyonel rezerv tavanı |$0,24|$0,25, güncel kullanıcı sınırı|
| Her inference / HTTP rezervi |$0,02 /$0,001|aynı|
| En yüksek sabit plan |$0,21|10×0,02 +30×0,001 =$0,23|

30HTTP, her olası inference için model GET +tam input-count POST +üretim POST olmak üzere3çağrı üzerinden hesaplandı. Önkontrol hataları aynı sınırı tüketir;10tamamlanmış cevap garanti edilmez. Şu an rezerv$0,046'dır. S07 tam3çağrı ilerlerse9HTTP/3inference rezervi=$0,069 olur. Eski bilinmeyen429 maliyeti sıfıra veya iade varsayımına çevrilmez. İlk6HTTP ve eski stop/slotlar değişmez; v2 ayrı ledger kullanır ve bütün ledger'ları birlikte sayar.

![Sayaç ve rezerv teklifi](figures/WP12/openai_S07_preparation_v2/02_budget_v1_and_proposed_v2.png)

Bu görsel gerçek mevcut sayaçları ve açıkça PLAN olarak etiketli sınırları gösterir; yeni deney sonucu veya fatura değildir. Resmî fiyatlar input$0,75/cached$0,075/output$4,50/milyon olarak tekrar kontrol edildi.6000+1200 üst token maliyeti$0,0099; %20 payla$0,01188. Her HTTP öncesi finansal rezerv/hash, her inference öncesi tam sunucu token/maliyet kapısı vardır. Count endpoint'e de aynı seçilmiş üç alıntı iletilir. Sığmayan metin kesilmez, CONTEXT_BUDGET kaydıyla durur. Usage cached/output/reasoning alanları korunur; reasoning çift sayılmaz. Usage bilinmiyorsa stop/UNKNOWN, otomatik tekrar yoktur. Vergi/fatura/bakiye API'si sorgulanmaz. [Resmî model/fiyat](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

V2 ayrı24saat fiyat kaydı kullanır; eski V1 fiyat kaydı veya zamanı güncellenmez. V2 teklifini kabul eden kullanıcı komutu yalnız S07 bir-deneme yetkisini kullanır; kalan8inference kapasitesi otomatik çalışma yetkisi değildir. Ayrıntı `docs/plan/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.md` içindedir.

## QA ve gizlilik

28 yeni offline test PASS. Kaynak metni/scope/closure, iki cümlelik istisna, p4 geçişli bağlam, şema alt kümesi, ret/boş-items ilişkisi, doğruID-yanlış-anlam sınırı, eski6/2 bütçenin taşınması,30/10 sınırları, tek-S07/tekrar blokajı, context/timeout/HTTP hatası, dotenv-only key ve insan kaydının ayrı kalması test edildi. Test fixture'ları TEST_ONLY olarak işaretlidir ve gerçek sonuç CSV'sine konmaz. PowerShell5.1 parse/hash kanıtı QA'dadır. Eski152 kamusal dosya ve33 değişmez giriş hash'i doğrulanır; hamrun/başarısızlık/model/önceki QA dosyaları değiştirilmez. Kaynak prospektüsler,44alıntı ve19senaryo aynı kalır.

Anahtar yalnız kök .env OPENAI_API_KEY alanından okunur; süreçte kalmış eski key kullanılmaz. Kullanılabilirlik yalnız VAR/YOK, değer/prefix/hash/header kaydı yoktur. Gizli dosyalar envanter/hash manifestine alınmaz. HTTP hata gövdeleri key yansıtmasına karşı güvenli kod alanlarıyla kaydedilir; başarılı/beklenmeyen model yanıtları ham olarak korunur.

## Kullanıcının tek S07 komutu

Bu tur yürütücü çalıştırılmadı. Bütçe v2 teklifini yalnız bu tek deneme için kabul ederek normal kullanıcı PowerShell'inde:

```powershell
& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_OpenAI_S07_SingleCase_v2.ps1" -AcceptBudgetV2 -RunS07
```

Yeni çıktı `reports/qa/WP12/openai_S07_user_runs_v2/` altında oluşur. AppContainer'da gerçek çağrı engellenir; kısıt aşma yoktur. Yürütücü S04 bayrağı kabul etmez. İlk S07 yanıtı sonrası status/Evidence_directory kullanıcı tarafından paylaşılınca gerçek PDF sadakati, Türkçe, istisna/qualifier, usage/maliyet ayrı incelenecektir. Şema geçişi semantik başarı veya otomatik yayın olmaz. Bu tur S04,19×3, yeni eğitim veya WP13 başlamaz.
'''
    with (s.ROOT/'reports/WP12_OPENAI_S07_PREPARATION_v2.md').open('x',encoding='utf-8') as f:f.write(report)
    before=(s.QA/'run_status_before.md').read_bytes();assert (s.ROOT/'run_status.md').read_bytes()==before
    header='''# WP12 — S07 tek deneme hazırlığı ve bütçe v2 teklifi ·08.11.2026

- S01 iki cümle için olumlu kullanıcı beyanı ayrıreceipt; formalinsanQA PENDING değişmedi. İsim/rol/yetki/tarih/responsehash/item-quote kapsamlı ayrıolay kontrolü hazır; yazma/yayın işleviyok, registry/templateNOT_ACTIVATED. S07yetkisi bu turdaki açıkistek.
- S07 3alıntı380karakter(DB00254) veS04 3alıntı3803karakter(DB00199) frozen kaynak/soru/kriter/scope/qualifier ile hazır. Renal→sınıfgirişi+BUNikicümle; unknown→p5→p4 closure. S01sabitcümle testi kullanılmaz; teknik/ajan/insan ayrı. İki senaryoNOT_RUN; S04yürütmeLOCKED.
- Bütçev2teklif:eski6HTTP/2inference/.046rezerv aynı;30toplamHTTP/enfazla10toplaminference/$0.25tavan. Enyüksek sabitplan.23USD; S07tamgiderse9HTTP/3rezerv/.069USD. Herçağrı rezerv+hash; üretimönceexactservercount6000/1200token, %20pay. Modelgpt-5.4-mini/timeout90/reasonnone/noRetry aynı. EskiV1sayacı/tarihi/stoplarıdeğişmedi.
-28 ağsıztest PASS; PSparse/hash QA. YeniAPI0. NormalPowerShell scripts/WP12_OpenAI_S07_SingleCase_v2.ps1 -AcceptBudgetV2 -RunS07 bütçeönerisini yalnıztekS07içinkabul eder. SonuçgelmedenS04/kalanpilot/19×3/WP13/yayın/eğitimyok.
- Rapor reports/WP12_OPENAI_S07_PREPARATION_v2.md; sözleşmeler docs/plan/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.md veWP12_HUMAN_DECISION_CONTROL_v1.md; notebook notebooks/WP12_OpenAI_S07_S04_preparation_v2.ipynb; QA reports/qa/WP12/openai_S07_preparation_v2/. Eski152kamusaldosya+33girişkorundu; gizlidosyahash'iyok. Öncekibaşarısızlıklar/QwenNOT_RUN/S01hamyanıtıaynı.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    (s.ROOT/'run_status.md').write_bytes(header.encode('utf-8')+before)
    b.verify(p);assert not list(b.CONTROL.glob('*.json'))
    files=[s.ROOT/path for path in ['scripts/wp12_openai_scenarios_v2.py','scripts/wp12_openai_pilot_budget_v2.py',
        'scripts/wp12_openai_S07_v2_client.py','scripts/wp12_human_review_control_v1.py','scripts/wp12_openai_S07_prepare_outputs_v2.py',
        'tests/test_wp12_openai_S07_v2.py','scripts/WP12_OpenAI_S07_SingleCase_v2.ps1','configs/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.json',
        'docs/prompts/WP12_OPENAI_SOURCE_SYSTEM_v2.txt','docs/prompts/WP12_OPENAI_S07_INSTRUCTIONS_v2.txt',
        'docs/prompts/WP12_OPENAI_S04_INSTRUCTIONS_v2.txt','docs/plan/WP12_HUMAN_DECISION_CONTROL_v1.md',
        'docs/plan/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.md','reports/WP12_OPENAI_S07_PREPARATION_v2.md',
        'notebooks/WP12_OpenAI_S07_S04_preparation_v2.ipynb','run_status.md']]
    files.extend(x for folder in [s.QA,F] for x in folder.iterdir() if not is_private_path(x) and x.is_file())
    key=client.project_key();available=bool(key);leaked=available and any(key.encode('utf-8') in x.read_bytes() for x in files)
    assert not leaked
    save('final_verification.json',{'offline_tests':28,'PowerShell_syntax_errors':0,'source_records_preserved':len(p['prior_public_records_sha256']),
        'immutable_inputs_verified':len(p['immutable_public_inputs_sha256']),'api_key_available':available,
        'secret_value_found':leaked,'secret_files_hashed':False,'global_existing_HTTP':6,'global_existing_inference_reservations':2,
        'new_API_requests':0,'S07':'NOT_RUN','S04':'LOCKED_NOT_RUN','formal_S01_human_QA':'UNCHANGED_PENDING',
        'human_user_statement_separate':'POSITIVE_RECEIPT_ONLY','original_status_bytes_retained':(s.ROOT/'run_status.md').read_bytes().endswith(before)})
    del key
    files.append(s.QA/'final_verification.json')
    save('evidence_manifest.json',{x.relative_to(s.ROOT).as_posix():public_sha(x) for x in files})
    print(json.dumps({'status':'S07_READY_S04_LOCKED_NOT_RUN','tests':28,'prior_public_files':len(p['prior_public_records_sha256']),
        'new_API_requests':0,'formal_S01_human_QA':'PENDING'}))


if __name__=='__main__':main()
