"""Koşullu WP12 çalışma kaydı/raporu/notebook; gerçek V2 inference YOK."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
import wp12_source_case as c
import wp12_method_v2 as v
import wp12_gemma_v2_user_run as run
import wp12_low_memory_run_review as oldreview
from wp09_close_wp10_notebooks import execute


def text_new(path,value):
    with Path(path).open('x',encoding='utf-8') as f:f.write(value)


def main():
    import pandas as pd
    cfg,policy,_=run.verify()
    syntax=c.read(run.QA/'powershell_5_1_syntax.json')
    assert syntax['error_count']==0 and syntax['generation_call_AST_count']==1
    assert syntax['runner_sha256']==cfg['runner_sha256']
    for name,count in [('test_conditional_runner.log',30),('test_accepted_v2_method.log',36)]:
        log=(run.QA/name).read_text(encoding='utf-8-sig')
        assert f'Ran {count} tests' in log and log.rstrip().endswith('OK')
    atomic=c.read(run.QA/'atomic_slot_test_result.json');assert atomic['second_claim_blocked'] and not atomic['real_stage_A_slot_exists']
    old=oldreview.audit();raw=c.read(oldreview.RUN/'source_response_raw.json')
    rows=[{'model':'Gemma3 1B','method':'V1','experiment_status':'FAIL','technical_status':'PASS','schema':'PASS',
        'application':'FAIL','Turkish_quality':'FAIL','source_faithfulness':'FAIL','primary_page_quote_alignment':'FAIL',
        'human_review':'PENDING_FORMAL_ITEM_REVIEW','user_acknowledged_failure':True,
        'source_question':'S01-R1','server_prompt_tokens':919,'server_output_tokens':188,
        'server_total_seconds':old['technical']['server_total_seconds'],'sampled_free_RAM_min_GiB':old['memory']['sampled_RAM_min_GiB'],
        'raw_response_ref':oldreview.RUN.relative_to(c.ROOT).as_posix()+'/source_response_raw.json',
        'raw_response_sha256':c.sha(oldreview.RUN/'source_response_raw.json'),
        'model_message_content_exact':raw['message']['content'],
        'errors':'invalid refusal; English; unsupported image-only reason; formulation/identity ID mismatch; unsupported absence claim',
        'reason':'Real user run; accepted as failure; structured human per-item review remains unfilled.'}]
    for model,method,reason in [('Gemma3 1B','V2','WAIT_USER_STAGE_A_RUN'),
                                ('Qwen3 4B','V2 with model-specific template only if required','CONDITION_NOT_TRIGGERED')]:
        rows.append({'model':model,'method':method,'experiment_status':'NOT_RUN','technical_status':'NOT_RUN',
            'schema':'NOT_RUN','application':'NOT_RUN','Turkish_quality':'NOT_RUN','source_faithfulness':'NOT_RUN',
            'primary_page_quote_alignment':'NOT_RUN','human_review':'PENDING','user_acknowledged_failure':None,
            'source_question':'S01-R1','server_prompt_tokens':None,'server_output_tokens':None,'server_total_seconds':None,
            'sampled_free_RAM_min_GiB':None,'raw_response_ref':None,'raw_response_sha256':None,
            'model_message_content_exact':None,'errors':None,'reason':reason})
    c.save_new(run.QA/'comparison_current_NOT_FINAL.json',{'status':'PARTIAL_V1_ONLY','rows':rows,
        'offline_Gemma_V2_prompt_tokens':724,'offline_token_count_is_not_a_model_run':True,
        'same_case_method_development_not_independent_validation':True})
    with (run.QA/'comparison_current_NOT_FINAL.csv').open('x',encoding='utf-8-sig',newline='') as f:pd.DataFrame(rows).to_csv(f,index=False)
    back=pd.read_csv(run.QA/'comparison_current_NOT_FINAL.csv',keep_default_na=False)
    assert back.iloc[0]['model_message_content_exact']==raw['message']['content']
    claim_rows=[{'model':'Gemma3 1B','method':'V1','model_statement_exact':old['semantic']['exact_explanation_field'],
        'assessment_level':'One actual sentence reviewed by topic, not nine independent model claims',**x}
        for x in old['semantic']['findings']]
    with (run.QA/'source_vs_claim_current_V1_ONLY.csv').open('x',encoding='utf-8-sig',newline='') as f:pd.DataFrame(claim_rows).to_csv(f,index=False)
    checks={'stage_A':'NOT_RUN_WAIT_USER_POWERSHELL','stage_B':'NOT_RUN_CONDITION_NOT_TRIGGERED',
        'stage_C':'PARTIAL_REAL_V1_ONLY','stage_D':'NO_AUTOSTART_USER_REVIEW_REQUIRED',
        'new_tests_passed':30,'accepted_method_tests_passed':36,'PowerShell_5_1_syntax_errors':0,
        'single_generation_AST_sites':1,'atomic_second_open_blocked':True,'real_stage_A_slot_consumed':False,
        'approved_method_prompt_tokens_offline':724,'actual_stage_A_server_tokens':'NOT_RUN',
        'new_inference':0,'API_calls_this_preparation':0,'new_model_downloads':0,'automatic_publication':False,
        'next_action':run.next_action(),'runner_sha256':cfg['runner_sha256']}
    c.save_new(run.QA/'preparation_checks.json',checks)
    F=c.ROOT/'reports/figures/WP12/conditional_local_llm_v1';F.mkdir(parents=True,exist_ok=True)
    init=r'''from pathlib import Path
import json,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display,Image
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():ROOT=ROOT.parent
Q=ROOT/'reports/qa/WP12/conditional_local_llm_v1'
F=ROOT/'reports/figures/WP12/conditional_local_llm_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
pd.set_option('display.max_colwidth',500);pd.set_option('display.max_columns',15)
'''
    execute('WP12_conditional_local_llm_stage_A_ready.ipynb',[
        ('md','''# WP12 — Koşullu yerel LLM planı; Aşama A hazır

Kullanıcı V2 yöntemi ve koşullu A→B hazırlığını onayladı. Bu notebook gerçek yeni inference yapmaz. GemmaV1 gerçek ve başarısız; GemmaV2/Qwen NOT_RUN. Yeni normal PowerShell komutu yalnız GemmaV2 S01-R1 için proje genelinde tek üretim slotu kullanabilir.19×3 ve WP13 otomatik açılmaz. Aynı görülen vakada yöntem geliştirme vardır; bağımsız genelleme/klinik doğruluk iddiası yoktur.'''),
        ('code',init+r'''
plan=read(ROOT/'configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json')
display(pd.DataFrame([{'aşama':k,'kapsam':value} for k,value in plan.items() if k.startswith('stage_')]))
display(pd.DataFrame([read(Q/'preparation_checks.json')]).T.rename(columns={0:'gerçek_hazırlık_durumu'}))
'''),
        ('md','''**Yorum:** Koşullu izin diskte kaydedildi; küçük hazırlıklar için tekrar izin istenmeyecek. Kullanıcı PowerShell çıktısı gerekli olduğunda yalnız komut ve gerçek klasör beklenir. GemmaV2 gerçek yanıtında uygulama/dil/görev/kaynak FAIL varsa Qwen hazırlığı açılabilir. Model/API/ölçüm engeli ayrı teknik durumdur; kaynak kalitesi NOT_EVALUABLE kalır. Qwen için mevcut cache/digest, kendi template/tokenizer ve ayrı RAM/VRAM/commit/OS değerlendirmesi gerekir; Gemma'nın düşük eşikleri kopyalanmaz, otomatik düşürülmez.

## Yalnız gerçek kayıtlı sonuç ve NOT_RUN satırları'''),
        ('code',r'''
comparison=read(Q/'comparison_current_NOT_FINAL.json')
table=pd.DataFrame(comparison['rows'])
display(table[['model','method','experiment_status','technical_status','schema','application','Turkish_quality','source_faithfulness','primary_page_quote_alignment','human_review','server_prompt_tokens','server_output_tokens','server_total_seconds']])
fig,ax=plt.subplots(figsize=(13,3.4));ax.axis('off')
small=table[['model','experiment_status','schema','application','Turkish_quality','source_faithfulness','human_review']].copy()
small['model']=['Gemma V1','Gemma V2','Qwen3 4B'];small['human_review']='PENDING'
t=ax.table(cellText=small.values,colLabels=['Model','Deney','Schema','Uygulama','Türkçe','Kaynak','İnsan'],loc='center',cellLoc='center')
t.auto_set_font_size(False);t.set_fontsize(10);t.scale(1,2)
for (i,j),cell in t.get_celld().items():
 if i==0:cell.set_facecolor('#dce8ee')
 elif small.iloc[i-1,j]=='FAIL':cell.set_facecolor('#f0d3cf')
 elif small.iloc[i-1,j]=='NOT_RUN':cell.set_facecolor('#eeeeee')
ax.set_title('Mevcut gerçek kayıt: V1; V2 ve Qwen henüz çalıştırılmadı',pad=25)
plt.tight_layout();plt.savefig(F/'current_real_and_NOT_RUN_statuses.png',dpi=160,bbox_inches='tight');plt.show()
'''),
        ('md','''**Yorum:** NOT_RUN hücreleri sıfır performans değildir. V1'in önceki insan formu PENDING kalır; kullanıcının başarısızlığı kabul etmesi ayrı user_acknowledged_failure alanındadır. V2 için724 offline token kanıtı vardır fakat henüz server prompt token/yanıt yoktur;724 tabloya gerçek run sonucu olarak yazılmaz. Qwen digest/memory/tokenizer bu aşamada ölçülmüş gibi gösterilmez. JSON ve CSV'de ilk ham model content alanının aynılığı round-trip test edildi.

## Kaynak/id iddiaları — gerçek V1 yanıtı'''),
        ('code',r'''
display(pd.read_csv(Q/'source_vs_claim_current_V1_ONLY.csv')[['topic','source_fact','model_statement_exact','assessment_tr','status']])
print('GERÇEK V1 MODEL CONTENT — AYNEN:')
print(comparison['rows'][0]['model_message_content_exact'])
'''),
        ('md','''**Yorum:** Kaynak karşılaştırması tek gerçek V1 cümlesinin ayrı konular açısından değerlendirmesidir; dokuz bağımsız model iddiası üretilmiş gibi sayılmaz. V1 hatası değişmez. Yeni V2 yanıt geldiğinde ham/model kaynakları ayrı QA sürümüne yazılacak, önceki yanıt düzeltilmeyecek. Şema/uygulama geçişi Türkçe kaynak sadakati ya da insan onayı değildir.

## Çalıştırıcı ve ölçüm sınırları'''),
        ('code',r'''
display(pd.DataFrame([read(Q/'atomic_slot_test_result.json')]))
display(pd.DataFrame([read(Q/'powershell_5_1_syntax.json')]))
display(pd.DataFrame([read(Q/'preparation_memory_snapshot.json')]))
'''),
        ('md','''**Yorum:** Gerçek generation slotu tüketilmedi; ayrı TEST_ONLY dosyasında ilk CreateNew başarılı/ikinci engelli. PowerShell5.1 parse0hata, bir PostAsync.30 yeni yürütücü/koşul +36 kabul edilmiş yöntem testi geçti. AppContainer'da API'den önce durulur. Başlangıç1,5GiB RAM/1GiB GPU/3GiB commit, OSfalse; runtime0,75GiB RAM/1GiB commit/OS alarmı ve60s timeout aynı. Snapshot bir çalışma garantisi değildir; gerçek kullanıcı preflight'ında tekrar ölçülür. Bellek/kimlik/kaynak/token/şema kapılarından sonra atomik tek-slot claim alınır; timeout veya kalite hatasında claim otomatik sıfırlanmaz. Slot alındıktan sonra başarısızlık bile tekrar hakkı yaratmaz. Bu dosyaya reset/force/kopyalama yönergesi yoktur.

**Durdurma noktası:** Normal kullanıcı PowerShell'inde yalnız Aşama A komutu. Çıktı klasörü bekleniyor. Qwen hazırlığı koşula bağlı; 19×3 sonuç incelemesi olmadan başlamaz; yeni eğitim/yayın/WP13 yok.''')])
    memory=c.read(run.QA/'preparation_memory_snapshot.json')
    mem=memory['memory'];gpu=memory['GPU']
    command=f'& "{c.ROOT / cfg["runner"]}" -RunFirstCase'
    document=f'''# WP12 — Kullanıcı onaylı koşullu yerel LLM çalışma planı v1

08.11.2026. Bu belge aktif ROADMAP WP12 kapsamındaki A/B/C/D yetki ve durma sınırlarını kaydeder; yeni yol haritası değildir. Kullanıcı V2 yöntemini, Aşama A tek isteğini ve koşullu Qwen hazırlığını açıkça onayladı. Kabul edilen V2 dosyalarının adında PROPOSED olması tarihsel addır; mevcut onayı geçersiz kılmaz ve dosyalar yeniden yazılmaz.

## A — Şimdi açık

Gemma3 1B aynı onaylı digest, kabul edilmiş aynı V2 schema/system/user prompt ve S01'in aynı iki tam Erythromycin alıntısı. Normal kullanıcı PowerShell'inde **en fazla bir** gerçek generation isteği. Tek-slot atomik CreateNew kaydı `reports/qa/WP12/conditional_local_llm_v1/control/stage_A_generation_claim.json` ile farklı/tekrar kullanıcı çağrılarında korunur. Kayıt tüketilirse reset/force/otomatik retry yoktur. Preflight'ta durulup slot alınmadıysa actual generation0 olarak kaydedilir. Codex AppContainer erişim engeli aşılmaz.

## B — Koşullu, henüz tetiklenmedi

Tamamlanmış gerçek GemmaV2 yanıtında JSON/application/Türkçe/kaynak/görev FAIL varsa tekrar küçük hazırlık izni istemeden mevcut Qwen3 4B için hazırlığa geçilir. Kaynak/dil incelemesi henüz PENDING ise PASS uydurulmaz. Yanıt üretilemeyen API/model yükleme/bellek engeli kaynak kalitesi FAIL sayılmaz; teknik blok ve NOT_EVALUABLE raporlanır. B'nin başlangıç durumu NOT_RUN_CONDITION_NOT_TRIGGERED.

Qwen indirilmeyecek. Yerel manifest/model digest'i ve normal kullanıcı API kimliği doğrulanacak. S01 soru/alıntı/kriter ve V2 mantığı aynı kalır; yalnız modelin zorunlu chat-template/tokenizer uyarlaması ayrı hash/manifestle yapılır. Tam prompt aynı context bütçesi içinde gerçekten sayılır; kesme yok. Qwen model dosya boyutu, mimari/KV context, runtime/offload ve fiziksel RAM/VRAM/commit/OS koşulları ayrı değerlendirilir. Gemma1,5GiB/1GiB eşikleri Qwen'e kopyalanmaz; daha riskli eşiklere otomatik düşülmez. Yerel eski Qwen politikası varsa tarihsel olarak korunur; güncel ayrı uygunluk değerlendirmesi olmadan Qwen yürütücüsü/inference açılmaz. Uygunsa normal kullanıcı PowerShell komutuyla tek gerçek deneme; uygun değilse ölçüm/engel raporlanır. Süreç kapatma, güvenlik değişimi, yetki yükseltme veya indirme yok.

## C — Gerçek sonuçlardan, ayrı durumlar

Schema, uygulama, Türkçe, PDF sadakati, sayfa/primaryquote, yanlış ret/eksik/uydurma, gerçek tokens/süre/bellek, insan incelemesi ayrı tutulur. JSON/CSV ham yanıtlar, gerçek kaynak-iddia tablosu, gerçek gözlemlerin PNG'leri, Türkçe rapor ve çalıştırılmış notebook, test/QA/hashler/güncel status üretilir. Çalıştırılmayan alan NOT_RUN; gerçek başarısız alan FAIL; insan incelemesi olmayan alan PENDING. Teknik ölçüm yoksa UNKNOWN/NOT_EVALUABLE; varsayılan0 değildir. İlk V1 başarısızlığı korunur. Aynı görülen vaka üstünde yöntem geliştirmesi, bağımsız genelleme/klinik doğruluk kanıtı değildir.

## D — Otomatik kapalı

Tek-vaka iyi olsa dahi19×3 başlamaz. Sonuçlar kullanıcıya sunulur; ayrı sonuç değerlendirme/onayı beklenir. Yeni eğitim, model indirme, otomatik yayın veya WP13 yoktur.

Bu koşullu izin disk dosyası `configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json` içinde de kayıtlıdır. Karar kuralları sabit kalır; gelecekteki durum/sonuçlar yeni QA sürümlerine yazılır. Model içeriği bu yetki kurallarını değiştiremez. Kullanıcı müdahalesi gerekmeyen test/rapor/hazırlıklar tamamlanır; AppContainer nedeniyle kullanıcı PowerShell çalıştırması gerekli olduğunda yalnız açık komut ve gerçek çıktı klasörü beklenir.
'''
    text_new(c.ROOT/'docs/plan/WP12_CONDITIONAL_EXECUTION_PLAN_v1.md',document)
    report=f'''# WP12 — Koşullu LLM planı ve Gemma V2 Aşama A yürütücüsü

08.11.2026 · **Aşama A hazır; gerçek kullanıcı PowerShell çıktı klasörü bekleniyor. V2/Qwen henüz çalıştırılmadı.**

AGENTS/aktif ROADMAP ve kabul edilmiş kaynak/çıktı/V2 sözleşmeleri korunur. Kullanıcı A tek istek ve B koşullu hazırlığını onayladı; küçük hazırlıklar için tekrar izin gerekmiyor. Uygulama yetki/durma kuralları `docs/plan/WP12_CONDITIONAL_EXECUTION_PLAN_v1.md` ve `configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json` içinde kalıcıdır. Bu yeni bir yol haritası değildir.

## 1. Kabul edilmiş yöntemi değiştirmeyen yürütücü

`scripts/WP12_GemmaV2_UserSingleCase_v1.ps1` normal kullanıcı PowerShell'i içindir. Onaylı `{cfg['model']}`/`{cfg['model_digest']}`, kabul edilmiş V2 case schema/system/user request, S01-R1 soru/iki orijinal alıntı/ölçüt birebir aynı. Kaynak537 karakter; önceki gerçek vocabulary-only ölçümü **724 prompt token**; bu yeni gerçek inference sonucu değildir. Her kullanıcı preflight'ında aynı native tokenizer ile tekrar sayılır.1536input/384output/128safety/2048context; context sığmazsa kesmeden durur. Exact v2 runtime grammar ve gerçek server724 teyidi hâlâ NOT_RUN/UNVERIFIED; ilk gerçek istek bunları da sınayacak.

Normal kullanıcıdan yerel version/tags/ps metadata, doğru API digest ile source/wrapper ayrımı ve native/model/PDF/kod/schema/prompt/source-context SHA doğrulaması gerekir. Yüklü başka model varsa otomatik kapatma/unload yerine durur. AppContainer ise API'den bile önce durur. Codex bu yürütücüyü çalıştırmadı; API0/inference0.

Yeni Python yardımcı modülü `scripts/wp12_gemma_v2_user_run.py` yalnız ağsız preflight ve reply incelemesidir. Status/schema/application/obvious-language/task coverage ayrılır. Türkçe veya kaynak sadakati otomatik PASS olmaz; source/human PENDING kalır. Yanlış JSON/ret/kind/İngilizce/eksik görev kaydedilir. HTTP/model yükleme/timeout/token sayısı uyumsuzluğu teknik hatadır; kaynak becerisi veya klinik doğruluk sonucu değildir. Gerçek yanıtı aldıktan sonra bağımsız kaynak ve insan incelemesi ayrıca yapılır.

## 2. Tek gerçek istek sınırı ve kayıtlar

Proje genelindeki sabit slot **{cfg['generation_slot']}**. Bütün kaynak/token/bellek ön koşullarından sonra, PostAsync öncesi atomik FileMode.CreateNew/FileShare.None ile tüketilir. İkinci kullanıcı çağrısı önce slotu görüp durur; iki eşzamanlı süreçte yalnız biri CreateNew alabilir. API veya süreç hatası sonrası da otomatik silme/reset/retry yoktur; başladığı belirsiz istek ikinci kez yollanmaz. Bu mekanizma aynı projenin kayıt dosyası korunurken geçerlidir; kullanıcı tarafından elle silinmiş/kopyalanmış kayıt için global sunucu garantisi iddia edilmez. Betikte force/reset seçeneği veya dosya silme yolu yoktur.

Her deneme benzersiz `reports/qa/WP12/gemma_v2_user_runs_v1/<zaman_GUID>/` klasörü açar. Tam wire request, raw HTTP yanıt (hata gövdesi dahil), schema/system/token/context/dependency hashleri, generation-claim kopyası, metadata/digest, Python stdout/stderr, süre/HTTP/bellek/OS/GPU, structural_review, boş insan inceleme formu ve file_hashes saklanır. Yanıtın kendisi otomatik çevrilmez/düzeltilmez/yayımlanmaz. Global slot tüketimi istemci isteği teşebbüsünü sınırlar; sunucunun tamamladığına ancak raw response kanıtı destek verir.

## 3. Donanım politikası aynı

EXPERIMENTAL_LOW_MEMORY_v1'in yalnız donanım/timeout/OS alanları devralındı: başlangıç RAM≥1,5GiB/GPU≥1GiB/commit≥3GiB, OS düşük bellekfalse;5 kararlı RAM/commit/OS ölçümü ve hemen önce RAM/GPU kontrolü. Runtime RAM<0,75GiB veya commit<1GiB veya OS basıncında kayıt/istemci iptali, no-retry. Eksik ölçümde durur. HTTP60s; sunucunun anında durduğu varsayılmaz. Gemma eski2,5GiB politikası ve bütün eski kararlar değişmez. Qwen için bu düşük eşikleri kullanma izni yoktur.

Hazırlık snapshot'ı `{mem['at']}`: boş RAM **{mem['available_bytes']/2**30:.3f}GiB**, GPU **{gpu['free_MiB']}MiB**, commit **{mem['commit_available_bytes']/2**30:.3f}GiB**, OSfalse. Bu bir başlangıç/peak garantisi değildir. Gerçek komut öncesinde bütün koşullar yeniden ölçülür; eşik sağlanmazsa istek yoktur.

## 4. Koşullu Qwen ve bilimsel karşılaştırma

Mevcut karar **{run.next_action()}**; B henüz açılmadı. Gerçek, teknik tamamlanmış V2 yanıtında schema/application/language/source/task FAIL olduğunda koşullu kullanıcı izniyle Qwen hazırlığı yapılabilecek. Yeni indirme, yeni keyfi soru/ölçüt veya en iyi tekrar seçimi yok. Qwen cache/digest/template/tokenizer ve kendi bellek uygunluğu açıkça denetlenecek; RAM/VRAM/commit/OS eşiği geçmezse durulacak, otomatik riskli düşürme yapılmayacak. Teknik engeller kalite FAIL gibi yazılmayacak. Normal kullanıcı PowerShell'i gerekirse açık komut verilecek; tekrar küçük hazırlık onayı istenmeyecek.

Şimdiki `comparison_current_NOT_FINAL.json/csv` yalnız gerçek V1 sonuçlarını ve açık NOT_RUN V2/Qwen satırlarını taşır. V1 HTTP200/stop/919input/188output; JSON SchemaPASS, application/Türkçe/kaynak/primary-IDFAIL, sampled RAM minimum0,997GiB. V1'in ilk insan formu PENDING kalır; kullanıcının başarısızlığı kabul ettiği ayrı alandadır. V2 için724 offline tokenı server ölçümü gibi göstermedik. Qwen için güncel digest/bellek değerlendirmesi henüz yapılmış gibi gösterilmedi. Gerçek raw message JSON/CSV round-trip ile aynı tutuldu. Kaynak karşılaştırma CSV'si dokuz bağımsız üretim değil, tek gerçek cümlenin konu bazlı incelemesidir.

Gerçek yeni sonuç gelince ayrı sürümlü rapor/notebook/claim-tablosu/figürler/manifestler tamamlanacak. İlk başarısız V1 silinmez veya başarılıya çevrilmez. Aynı S01'i görerek yöntem düzeltmek, bağımsız genelleme veya klinik doğruluk kanıtı değildir. İnsan semantik incelemesi ve observed-source açıklama sınırı sürer. Tek vaka geçse bile19×3 için kullanıcı sonuç değerlendirmesi beklenir.

## 5. QA ve korunma

**30 yeni yürütücü/koşul testi +36 kabul edilmiş yöntem testi geçti.** Atomik slot .NET testi ayrı TEST_ONLY dosyasında ilk açma başarılı/ikinci açma engelli; gerçek slot tüketilmedi. PS5.1({syntax['parser']}) parse0hata, AST1PostAsync, betik çalıştırılmadı. Runner SHA **{cfg['runner_sha256']}**. Python duplicate-key/NaN, token/model/stop/bütçe ve uygulama/dil/görev kontrolleri; AppContainer erken kapısı, claim öncesi bellek/hash kontrolü, no-download/no-force/no-reset/no-retry ve koşullu B/D sınırları test edildi.

Önceki **3630** kabul edilmiş dosyanın SHA envanteri korundu. Yalnız güncel status yeni bölümle güncellenecek; önceki baytları QA arşivi ve tarihsel devamda aynen korunur. Eski modeller/GNN/SHAP/PPI, PDF/44 alıntı/19 senaryo/ölçüt, V1 ve V2 öneri dosyaları değiştirilmez. PROPOSED adındaki kabul edilmiş yöntem dosyaları tarihsel isimleriyle kullanılır; yeni yürütücü config'i onayı ayrı kaydeder.

## 6. Kullanıcı komutu ve beklenen çıktı

Normal kullanıcı PowerShell'inde **yalnız bir kez**:

```powershell
{command}
```

Yazdırılan **Evidence directory** yolunu paylaşın. Mevcut koşullu yetkiye göre gerçek yanıtın teknik ve kaynak/dil incelemesini yapacağız; gerekirse B hazırlığını ayrıca küçük izin istemeden tamamlayacağız. Ön koşullar geçmezse hatayı/ölçümleri saklayarak durur; otomatik tekrar yoktur. Kullanıcı uygulamalarını veya Ollama servisini kapatma, güvenlik ayarı/yetki değiştirme talimatı verilmez. Bu turda yeni inference/model indirme/eğitim/otomatik yayın/WP13 yapılmadı;19×3 başlatılmadı.

Notebook `notebooks/WP12_conditional_local_llm_stage_A_ready.ipynb`; QA `reports/qa/WP12/conditional_local_llm_v1/`; gerçek/NOT_RUN durum PNG'si `reports/figures/WP12/conditional_local_llm_v1/`. Aktif sonraki adım yalnız gerçek kullanıcı çıktı klasörünü beklemek.
'''
    text_new(c.ROOT/'reports/WP12_CONDITIONAL_STAGE_A_READY.md',report)
    previous=c.read(run.QA/'previous_files_sha256.json')
    before=(run.QA/'run_status_before.md').read_bytes();assert (c.ROOT/'run_status.md').read_bytes()==before
    prefix=f'''# WP12 — Koşullu plan onaylı; Gemma V2 tek-istek yürütücüsü hazır ·08.11.2026

- Kullanıcı A/B/C/D koşullu akışı onayladı. A:aynı Gemma/digest/kabul edilen V2/iki tam alıntı/S01-R1, normal kullanıcı PowerShell'inde proje-geneli atomik tek-slot. scripts/WP12_GemmaV2_UserSingleCase_v1.ps1 -RunFirstCase. Gerçek klasör bekleniyor; API/inference0, slot tüketilmedi.
-30 yürütücü/koşul +36 yöntem testi geçti. PS5.1 parse0hata,1PostAsync; atomik ikinci-açma TEST_ONLY'da engelli. Önceki724-token prompt/donanım/timeout/OS politikası aynı; gerçek kullanıcı preflight'ında tüm kapılar yeniden ölçülür. SHA{cfg['runner_sha256']}.
-B:tamamlanmış gerçek V2 yanıtında sözleşme/dil/görev/kaynakFAIL ise mevcut Qwen için ayrı kimlik/template/tokenizer/bellek hazırlığı yetkili. Teknik yükleme/API engeli semantikFAIL değil. Yeni indirme veya Gemma düşük eşiklerini Qwen'e kopyalama/otomatik düşürme yok. B henüz NOT_RUN.
-C:yalnız gerçek V1 sonucu ve NOT_RUN V2/Qwen satırları; ham JSON/CSV aynı. İnsan incelemesi PENDING; kullanıcı başarısızlık kabulü ayrı kayıttır. Aynı-vaka yöntem geliştirmesi bağımsız/klinik doğrulama değildir. D:19×3 kullanıcı sonuç incelemesinden önce başlamaz; WP13/eğitim/yayın yok.
-Önceki3630 dosya ve tüm sonuçlar korundu; eski status baytları arşivlendi. Plan docs/plan/WP12_CONDITIONAL_EXECUTION_PLAN_v1.md; rapor reports/WP12_CONDITIONAL_STAGE_A_READY.md; notebook notebooks/WP12_conditional_local_llm_stage_A_ready.ipynb; QA reports/qa/WP12/conditional_local_llm_v1/.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''.encode('utf-8')
    (c.ROOT/'run_status.md').write_bytes(prefix+before)
    changed=[p for p,h in previous.items() if c.sha(c.ROOT/p)!=h];assert changed==['run_status.md'],changed
    assert c.sha(run.QA/'run_status_before.md')==previous['run_status.md']
    c.save_new(run.QA/'previous_artifacts_preservation.json',{'previous_files':len(previous),
        'unchanged_at_original_path':len(previous)-1,'only_updated_path':'run_status.md','old_status_archived_exactly':True,
        'old_status_retained_as_exact_suffix':(c.ROOT/'run_status.md').read_bytes().endswith(before),
        'v1_raw_run_unchanged':oldreview.source_checks()['all_raw_hashes_valid'],'actual_new_inference':0})
    print('A runner/report/executed notebook ready. B conditional; waiting for actual user output directory.')


if __name__=='__main__':main()
