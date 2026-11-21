"""Gerçek V2 + korunmuş V1 karşılaştırması ve bellek kapısında duran Qwen hazırlığı."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
import wp12_source_case as c
import wp12_method_v2 as method
import wp12_gemma_v2_real_review as a
import wp12_low_memory_run_review as v1
from wp09_close_wp10_notebooks import execute


def text_new(path,value):
    with Path(path).open('x',encoding='utf-8',newline='') as f:f.write(value)


def main():
    import pandas as pd
    r=c.read(a.QA/'Gemma_V2_independent_review.json');old=v1.audit()
    resources=c.read(a.QA/'Qwen_cache_and_resource_assessment.json');state=c.read(a.QA/'conditional_state_after_GemmaV2.json')
    mem=c.read(a.QA/'Qwen_current_memory_snapshot.json');policy=c.read(c.ROOT/'configs/WP12_QWEN4B_CONDITIONAL_MEMORY_v1.json')
    raw=c.read(a.RUN/'source_response_raw.json');oldraw=c.read(v1.RUN/'source_response_raw.json')
    log=(a.QA/'test_review_and_qwen_preparation.log').read_text(encoding='utf-8-sig')
    assert 'Ran 32 tests' in log and log.rstrip().endswith('OK')
    rows=[]
    for tag,rr,rawdata,path in [('Gemma V1',old,oldraw,v1.RUN),('Gemma V2',r,raw,a.RUN)]:
        v2=tag=='Gemma V2'
        rows.append({'model_method':tag,'experiment_status':'FAIL','generation_completed':True,
            'pipeline_terminal_status':r['original_pipeline_status_preserved']['status'] if v2 else old['structural']['status'],
            'pipeline_schema_status':'NOT_EVALUABLE_TOKEN_GATE' if v2 else 'PASS',
            'independent_content_schema_status':'PASS','independent_source_contract_technical':'PASS' if v2 else 'FAIL',
            'actual_language_agent':'FAIL_ENGLISH','full_instruction_compliance_agent':'FAIL',
            'source_faithfulness_agent':'CORE_SUPPORTED_OMISSIONS' if v2 else 'FAIL_CONTRADICTED',
            'primary_quote_kind_alignment':'PASS' if v2 else 'FAIL','human_review':'PENDING',
            'planned_offline_prompt_tokens':724 if v2 else 919,'actual_server_prompt_tokens':rawdata['prompt_eval_count'],
            'output_tokens':rawdata['eval_count'],'server_total_seconds':rawdata['total_duration']/1e9,
            'sampled_min_free_RAM_GiB':r['memory']['sampled_min_RAM_GiB'] if v2 else old['memory']['sampled_RAM_min_GiB'],
            'peak_VRAM':'UNKNOWN','raw_response_ref':str(path/'source_response_raw.json'),
            'raw_response_sha256':c.sha(path/'source_response_raw.json'),
            'model_message_exact':rawdata['message']['content'],
            'raw_HTTP_body_exact':(path/'source_response_raw.json').read_bytes().decode('utf-8')})
    rows.append({'model_method':'Qwen3 4B','experiment_status':'NOT_RUN','generation_completed':False,
        'pipeline_terminal_status':'BLOCKED_HOST_RAM_AND_TOKEN_API_PREREQUISITES',
        'pipeline_schema_status':'NOT_RUN','independent_content_schema_status':'NOT_RUN',
        'independent_source_contract_technical':'NOT_RUN','actual_language_agent':'NOT_RUN',
        'full_instruction_compliance_agent':'NOT_RUN','source_faithfulness_agent':'NOT_RUN',
        'primary_quote_kind_alignment':'NOT_RUN','human_review':'PENDING',
        'planned_offline_prompt_tokens':None,'actual_server_prompt_tokens':None,'output_tokens':None,
        'server_total_seconds':None,'sampled_min_free_RAM_GiB':None,'peak_VRAM':'NOT_RUN',
        'raw_response_ref':None,'raw_response_sha256':None,'model_message_exact':None,'raw_HTTP_body_exact':None})
    c.save_new(a.QA/'real_comparison_v1_v2_Qwen_NOT_RUN.json',{'rows':rows,
        'independent_content_diagnostic_not_original_pipeline_override':True,'same_case_posthoc_method_development':True})
    with (a.QA/'real_comparison_v1_v2_Qwen_NOT_RUN.csv').open('x',encoding='utf-8-sig',newline='') as f:pd.DataFrame(rows).to_csv(f,index=False)
    back=pd.read_csv(a.QA/'real_comparison_v1_v2_Qwen_NOT_RUN.csv',keep_default_na=False)
    assert back.iloc[0]['model_message_exact']==oldraw['message']['content']
    assert back.iloc[1]['model_message_exact']==raw['message']['content']
    assert back.iloc[1]['raw_HTTP_body_exact']==(a.RUN/'source_response_raw.json').read_bytes().decode('utf-8')
    claim_rows=[];ctx=method.verified_S01_context()
    for finding,src in zip(r['semantic_agent_review']['findings'],ctx['sources']):
        claim_rows.append({**finding,'physical_page':src['physical_page'],'quote_id':src['quote_id'],
            'source_quote_exact':src['quote'],'reviewer_translation_is_model_output':False})
    with (a.QA/'V2_source_vs_claim.csv').open('x',encoding='utf-8-sig',newline='') as f:pd.DataFrame(claim_rows).to_csv(f,index=False)
    checks={'new_tests_passed':32,'V2_real_response':'HTTP200_STOP_729_INPUT_312_OUTPUT',
        'original_pipeline_status':'TOKEN_COUNT_ALIGNMENT_FAILED','original_planned_prompt_tokens':724,
        'posthoc_content_schema':'PASS','primary_kind_ID':'PASS','actual_language':'FAIL_ENGLISH',
        'human_review':'PENDING','registered_vs_GGUF_template_difference_verified':True,
        'exact_729_native_reproduction':'BLOCKED_VOCAB_ONLY_RAM_GUARD_UNKNOWN',
        'Qwen_local_identity_and_layer_hashes':'VERIFIED','Qwen_API_identity':'PENDING',
        'Qwen_actual_tokens':'UNKNOWN_BLOCKED','Qwen_inference':'NOT_RUN_HOST_RAM_BELOW3GiB',
        'Gemma_extra_requests':0,'new_Ollama_API_requests':0,'automatic_threshold_reduction':False,
        '19x3':'NOT_STARTED','WP13':'NOT_STARTED','new_training_or_downloads':0,'automatic_release':False}
    c.save_new(a.QA/'review_checks.json',checks)
    F=c.ROOT/'reports/figures/WP12/gemma_v2_review_qwen_preparation_v1';F.mkdir(parents=True,exist_ok=True)
    init=r'''from pathlib import Path
import json,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():ROOT=ROOT.parent
Q=ROOT/'reports/qa/WP12/gemma_v2_review_qwen_preparation_v1'
F=ROOT/'reports/figures/WP12/gemma_v2_review_qwen_preparation_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
pd.set_option('display.max_colwidth',600);pd.set_option('display.max_columns',16)
'''
    execute('WP12_Gemma_V2_review_Qwen_preparation.ipynb',[
        ('md','''# WP12 — Gerçek Gemma V2 ve koşullu Qwen hazırlığı

**V2 gerçekten yanıt verdi; token sayımı kapısı başarısız ve açıklamalar yine İngilizce.** Özgün TOKEN_COUNT_ALIGNMENT_FAILED kaydı değiştirilmez. Ayrı post-hoc içerik kontrolü, sayım doğrulanmış gibi yapılmış yeni bir pipeline değerlendirmesi değildir. Kullanıcının koşullu izniyle Qwen hazırlığı açıldı; Qwen belleği yetersiz, inference NOT_RUN. Yeni istek/tekrar/model indirme/eğitim/WP13 yok.'''),
        ('code',init+r'''
audit=read(Q/'Gemma_V2_independent_review.json')
display(pd.DataFrame([audit['transport_generation']]).T.rename(columns={0:'gerçek_kayıt'}))
display(pd.DataFrame([audit['original_pipeline_status_preserved']]).T.rename(columns={0:'değişmeyen_sonuç'}))
print('GERÇEK MODEL CONTENT — AYNEN:')
print(read(Q/'real_comparison_v1_v2_Qwen_NOT_RUN.json')['rows'][1]['model_message_exact'])
'''),
        ('md','''**Yorum:** HTTP200/done=true/stop,729input/312output; eski offline724.729+312=1041, context2048 ve output384 sınırları içinde. Bu hata token budget aşımı/timeout değildir. Sayım kapısı JSON incelemesinden önce durdu; saved schema/application NOT_EVALUABLE kalır. Aynı ham JSON'un ayrı salt içerik kontrolü yapılabilir ama bu kayıt geriye dönük pipeline PASS'e çevrilemez.

## Kaynak, dil ve uygulama sınırları'''),
        ('code',r'''
display(pd.read_csv(Q/'V2_source_vs_claim.csv')[['item','physical_page','quote_id','source_quote_exact','model_text','assessment','translation_reviewer_NOT_MODEL']])
display(pd.DataFrame(audit['independent_posthoc_content_check']['language_checks']))
display(pd.DataFrame([audit['semantic_agent_review']]).T.rename(columns={0:'ajan_incelemesi_insan_onayı_değil'}))
'''),
        ('md','''**Yorum:** İki primary-ID ve kind artık doğru; ana etkin madde/sınıf ve kırmızı/yuvarlak/bikonveks/enterik tablet ifadeleri kaynakta var. BP250mg ürün ayrıntısı ve ambalaj sayıları atlanmış. İlk item iki cümle; tek kısa cümle yönergesine de tam uyulmuyor. Her iki açıklama İngilizce; language=tr yanlış beyan. Sınırlı marker kontrolü bu İngilizce cümleleri yakalamadı; zorunlu insan/ajan incelemesi bu yüzden vazgeçilmezdir. Türkçe çeviri sütunu inceleyenin çevirisi, model çıktısı değildir. İnsan onayı PENDING; yeni skor/etiket/klinik risk yok.

## Token farkı: kayıtlı servis şablonu ve GGUF varsayımı'''),
        ('code',r'''
render=read(Q/'pure_template_reconstruction.json')
display(pd.DataFrame([{k:v for k,v in render.items() if not k.endswith('_prompt')}]))
display(pd.DataFrame([read(Q/'registered_template_token_diagnostics.json')]))
print('KAYITLI OLLAMA GEMMA BAŞLANGICI:',repr(render['Gemma_Go_prompt'][:90]))
print('GGUF BAŞLANGICI:',repr(render['Gemma_GGUF_prompt'][:90]))
'''),
        ('md','''**Yorum:** Ön kontrol GGUF Jinja'daki system+user→tek user birleştirmesini servisle aynı varsaydı. Kayıtlı Ollama Go şablonu system ve user'ı ayrı user turları yapıyor (2 yerine1 farklı). Sınırlı renderer yalnız bu iki hash-pinned template'in güvenli alt kümesi için test edildi; genel Go yorumlayıcısı değildir. Sunucunun gerçek render baytları kayıtta yok. Native729 tekrarı ve Qwen token sayımı, sözlük-only1,5GiB RAM kapısında durdu; sayısal teyit UNKNOWN, tahmin yapılmadı. 5-token farkı şablon farkıyla tutarlıdır ama tam sayısal neden kesin kanıtlanmış gibi sunulmaz. Eski724 proof veya script düzeltilmedi; slot reset/retry yok.

## Gerçek V1/V2, Qwen NOT_RUN karşılaştırması'''),
        ('code',r'''
rows=pd.DataFrame(read(Q/'real_comparison_v1_v2_Qwen_NOT_RUN.json')['rows'])
display(rows[['model_method','experiment_status','pipeline_terminal_status','pipeline_schema_status','independent_content_schema_status','actual_language_agent','source_faithfulness_agent','primary_quote_kind_alignment','human_review','actual_server_prompt_tokens','output_tokens','server_total_seconds']])
fig,axes=plt.subplots(1,2,figsize=(12,4))
real=rows.iloc[:2]
axes[0].bar(real.model_method,real.server_total_seconds,color=['#9b9191','#6b8f9d'])
axes[0].set(ylabel='Sunucu total süresi (s)',title='İki gerçek run; tek-vaka, CI veya üstünlük kanıtı yok')
axes[1].bar(real.model_method,real.sampled_min_free_RAM_GiB,color=['#9b9191','#6b8f9d'])
axes[1].axhline(.75,color='#b06060',ls='--',label='Gemma deneysel uyarı0,75GiB')
axes[1].set(ylabel='Örneklenmiş minimum boş RAM (GiB)',title='Sürekli minimum/peak modelRAM değildir');axes[1].legend(fontsize=8)
plt.tight_layout();plt.savefig(F/'real_V1_V2_latency_and_sampled_memory.png',dpi=160);plt.show()
'''),
        ('md','''**Yorum:** V2 kaynak çekirdeğinde V1'e göre daha iyi görünüyor fakat Türkçe görevi başarısız; token protokolü de FAIL. Bu aynı görülmüş vaka üstünde geliştirme karşılaştırmasıdır; bağımsız genelleme/klinik doğruluk veya genel model üstünlüğü değildir. Ham response/message JSON ve CSV'de aynen korunur. Qwen için sayı/puan çizilmez: NOT_RUN.

## Qwen kimliği, modele özel bellek planı ve durma'''),
        ('code',r'''
res=read(Q/'Qwen_cache_and_resource_assessment.json')
policy=read(ROOT/'configs/WP12_QWEN4B_CONDITIONAL_MEMORY_v1.json')
display(pd.DataFrame([{'model':res['model'],'yerel_digest':res['local_registered_digest'],
 'model_bytes':res['model_bytes'],'full_FP16_KV_MiB':res['full_FP16_KV_bytes_at_2048']/2**20,
 'API_identity':res['API_digest_current']}]))
display(pd.DataFrame(res['layer_hashes']))
display(pd.DataFrame([policy]).T.rename(columns={0:'Qwen_ayrı_plan'}))
m=read(Q/'Qwen_current_memory_snapshot.json')
fig,ax=plt.subplots(figsize=(9,4))
ax.bar(['Ölçülen host RAM','Qwen giriş RAM'],[m['memory']['available_bytes']/2**30,3],color=['#ad7777','#628897'])
ax.set(ylabel='GiB',title='Qwen için fiziksel RAM kapısı geçmiyor')
plt.tight_layout();plt.savefig(F/'Qwen_host_RAM_gate_BLOCKED.png',dpi=160);plt.show()
'''),
        ('md','''**Yorum:** Yerel Qwen digest0edc… tarihsel kayıtla aynı;2.497.280.480bayt model ve config/template/license/params hash'leri doğrulandı.36katman/8KVhead/key128/value128 için2048context tam FP16 KV288MiB teorik hesap; gerçek runtime peak değildir. Qwen ayrı giriş:RAM3GiB,VRAM3,5GiB,commit4GiB, OSfalse. VRAM tabanı model+KV+0,75GiB varsayımsal çalışma marjının yukarı0,25GiB yuvarlanmasıdır; ölçülmüş peak veya güvenlik garantisi değil. Eski Qwen3GiB host tabanı korunur; Gemma düşük eşikleri kopyalanmaz.

Son RAM1,275GiB<3; VRAM3935MiB ve commit ölçümleri yeterli olsa bile host kapısı FAIL. API digest ve tam Qwen tokenizer sayısı PENDING/UNKNOWN; AppContainer'dan API zorlanmadı. Qwen inference NOT_RUN ve yürütücü/istek komutu açılmadı. Uygun gerçek kaynak koşulları sonradan oluşursa mevcut koşullu yetkiyle API/template/token/bellek kapıları tamamlanıp en fazla bir Qwen denemesi hazırlanabilir; otomatik riskli eşik düşürülmez.32 test geçti.19×3 ve WP13 kapalı; yeni inference/indirme/eğitim/yayın yok.''')])
    body=(a.RUN/'source_response_raw.json').read_bytes().decode('utf-8')
    content=raw['message']['content']
    translations='\n\n'.join(f"**Item{x['item']} model metni aynen:**\n\n> {x['model_text']}\n\n**İnceleyenin Türkçe çevirisi; model çıktısı değildir:**\n\n> {x['translation_reviewer_NOT_MODEL']}\n\n{x['assessment']}" for x in r['semantic_agent_review']['findings'])
    policy_text=f"RAM≥3GiB / GPU≥{policy['GPU_floor_MiB']}MiB(3,5GiB) / commit≥4GiB / OS düşük bellekfalse"
    report=f'''# WP12 — Gerçek Gemma V2 incelemesi ve koşullu Qwen ön hazırlığı

08.11.2026 · **Gemma V2 gerçek yanıt verdi; token kapısı FAIL ve Türkçe açıklama FAIL. Qwen ön hazırlığı yapıldı, inference RAM kapısında NOT_RUN.**

Run `{a.RUN}` salt okunur incelendi.21 ham dosya/20 manifest girdisi, doğru Gemma9755… digest, aynı V2 request/schema/iki tam alıntı, globalclaim ve frozen kaynak/kod hash'leri doğrulandı. Bu tur model inference/API isteği/tekrar/indirme/eğitim yoktur. AGENTS/ROADMAP/WP12 kaynak sözleşmeleri ve koşullu plan uygulanır;19×3/otomatik yayın/WP13 yok.

## 1. Teknik sonuç ve değişmeyen token hatası

HTTP200/done=true/stop. Gerçek server prompt **729**, kayıtlı offline beklenti **724**; fark+5. Gerçek output312<384, toplam1041<context2048; context bütçe aşımı veya length stop yoktur. Sunucu total **8,157021s**, yükleme3,452087s, prompt1,223231s, output3,461736s; istemci blok12,527538s Python review dahil. Tek generation slotu tüketildi ve korunuyor; ikinci Gemma isteği/retry/reset yapılmaz.

Saved `structural_review.json` aynen **TOKEN_COUNT_ALIGNMENT_FAILED / technicalFAIL / schemaNOT_EVALUABLE / applicationNOT_EVALUABLE** kalır. Token kapısı JSON kontrolünden önce durdu. Yeni ayrı `Gemma_V2_independent_review.json` içindeki ham-content kontrolü orijinal pipeline'ı PASS'e çevirmez; sahte729 proof ile yeniden validation yapılmadı.

## 2. Token farkı: benim ön kontrol varsayımım ve doğrulama sınırı

Ön kontrolü hazırlarken GGUF iç Jinja şablonunu kayıtlı Ollama servis şablonuyla aynı varsaydım. Tek-user41 ve919 hizalaması, yeni system+user yolunu kanıtlamıyordu. Yerel kayıtlı template SHA **{a.GEMMA_TEMPLATE}** ile GGUF şablonu farklıdır: GGUF system içeriğini ilk user prefix'ine birleştirirken, kayıtlı Go template system mesajını ayrı bir user turu olarak basar. Test edilmiş saf yeniden kurulumda **Go2 user turu / GGUF1 user turu** görülüyor. Bu teknik ön-kontrol kusuru modelin biyolojik bilgisi veya Türkçe yeteneğiyle karıştırılmaz.

[Ollama0.40.6 template işleyicisi](https://github.com/ollama/ollama/blob/v0.40.6/template/template.go) system içeriğini ayrıca toplarken mesajları da korur; modelin seçtiği template buna göre farklı metin üretir. [Prompt yolu](https://github.com/ollama/ollama/blob/v0.40.6/server/prompt.go) ve [llama-server köprüsü](https://github.com/ollama/ollama/blob/v0.40.6/llm/llama_server.go) farklı renderer/Go-template/native-chat yolları içerir. Bu nedenle yalnız GGUF şablonunun token sayısı servis için evrensel sayı değildir.

**Sınır:** Sunucunun gerçekten render ettiği prompt baytları bu run'da saklı değildir. Sözlük-only tekrarın1,5GiB ayrı RAM kapısı geçilmediği için **729'un native sayısal yeniden üretimi bu tur UNKNOWN/BLOCKED**; kesin729 reproduksiyon yapılmış gibi sunulmaz. Kayıtlı template farkı+5 ile tutarlıdır;5'in bütün nedenleri kesin doğrulandı iddiası yok. Eski724 dosyası, test kanıtları veya runner güncellenip geçmişte doğruymuş gibi gösterilmedi. Sınırlı yeni Go-template alt-küme renderer'ı yalnız hash-pinned iki modelin plain system/user/no-tools yolunu inceler; Go kurulum/derleme veya yeni model indirme yoktur. Bilinmeyen syntax reddedilir.

## 3. Gerçek model yanıtı aynen

```json
{content}
```

{translations}

## 4. İçerik/şema/kaynak/dil birbirinden ayrı

Ham JSON'a salt ayrı post-hoc bakıldığında V2 schema ve primary quote-ID/kind bağları **PASS**. İki farklı purpose bulundu. Yanlış image-only ret yok, candidate/null-code doğru. Buna rağmen açıklamalar **İngilizce**; language=tr gerçek cümle diliyle uyuşmuyor. İlk item iki cümle içeriyor; tek kısa cümle yönergesine de tam uymuyor. Dolayısıyla tam yönerge/Türkçe görevi **FAIL**; automatic checker'ın no-error/PENDING sonucu semantik başarı değildir.

Sınırlı İngilizce-marker yöntemi bu yeni iki İngilizce cümleyi **yakalamadı**; language_checks PENDING döndü. Bu gözlenen false-negative açıkça korunuyor; marker listesi sonuç görüldükten sonra değiştirilmedi. Önceden zorunlu tutulan bağımsız dil/kaynak ve insan incelemesi gerekliliği gerçek örnekte görülmüş oldu. İnsan formu PENDING; bu rapordaki ajan değerlendirmesi insan onayı değildir.

Kaynak açısından: sayfa1 etkin madde erythromycin ve macrolide sınıfını; sayfa6 kırmızı/yuvarlak/bikonveks/enterik tablet biçimini destekler. BP250mg ürün ayrıntısı ve ambalaj sayıları atlanmış; yeni bir klinik olgu/ADR/skor/SHAP/Δz/MedDRA üretilmemiş. İki primary-ID ve purpose doğru. Bu çekirdek kaynak aktarımı V1'in “formülasyon yok” ifadesinden daha uyumludur, fakat başarılı Türkçe açıklama sayılmaz. Kaynakta olmayan eşdeğerlik veya klinik risk iddiası yoktur. Seçili alıntıda unknown/might qualifier yok; S04/Doxycycline/BUN vakaları ayrıca sınanmış sayılmaz.

**Koşullu B gerekçesi** token hatası değildir: HTTP200/stop ile elde edilmiş, bağımsız incelenebilen gerçek yanıtın Türkçe zorunluluğunu açıkça ihlal etmesidir. Bu, kullanıcının önceden verdiği dil/görev başarısızlığında Qwen hazırlığı yetkisine uyar. Token teknik hatası ayrı FAIL olarak aynen kalır. Yalnız API/model yükleme engeli olup gerçek metin olmasaydı kaynak açıklama kalitesi FAIL yazılmazdı.

## 5. Gerçek bellek ve V1/V2 karşılaştırması

V2 giriş RAM1,559GiB, istekten hemen önce1,537GiB;34 örnekte minimum **{r['memory']['sampled_min_RAM_GiB']:.6f}GiB**, commit minimum **{r['memory']['sampled_min_commit_GiB']:.6f}GiB**, OS düşük bellek0true. Deneysel0,75GiB uyarısı aşılmadı. GPU giriş/son3935MiB; gerçek runtime peak VRAM/processRAM ve ara örneklerdeki minimumlar UNKNOWN. Bu tek run genel güvenlik kanıtı değildir.

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

Mevcut model **{resources['model']}**; yerel kayıtlı manifest digest **{resources['local_registered_digest']}**, eski frozen Qwen kaydıyla aynı. Config ve model/template/license/params blob SHA'ları doğrulandı; model yeniden indirilmedi. API'nin güncel tags digest'ini normal kullanıcı ortamında doğrulama **PENDING**; Codex AppContainer'dan API erişimi zorlanmadı.

Model dosyası **2.497.280.480bayt ({resources['model_bytes']/2**30:.3f}GiB)**. Gerçek GGUF metadata:36katman,2560embedding,32attentionhead/8KVhead,key128/value128,add_bos=false.2048context tam FP16 KV varsayımı `36×2048×8×(128+128)×2`=**288MiB**. Bu hesap runtime/offload/activation/sürücü peak'i değildir.

Qwen kayıtlı template SHA **{a.QWEN_TEMPLATE}**. Saf string kurulumunda system ve user ayrı gerçek system/user turlarındadır; Gemma kayıtlı template'i system'i user diye basıyordu. S01 kaynak/soru/kriter/schema/options/system içerikleri korunmuş `Qwen_S01_v2_request_NOT_SENT.json` dosyasında **yalnız model adı değişir**. Template/tokenizer farkı zorunlu teknik uyarlamadır. Tam Qwen prompt token sayısı RAM nedeniyle **UNKNOWN/BLOCKED**; tahmini karakter oranı veya GGUF şablonuyla kesin sayıyı ikame etmedim. API/token count eşitliği ileride ayrı doğrulanmadan Qwen inference açılmaz.

## 7. Qwen ayrı bellek politikası ve gerçek engel

`configs/WP12_QWEN4B_CONDITIONAL_MEMORY_v1.json`: **{policy_text}**. Eski Qwen3GiB host tabanı korunur. GPU3,5GiB, model2,326GiB+teorik KV0,281GiB+varsayımsal0,75GiB runtime marjının yukarı0,25GiB yuvarlanmasıdır. Bu marj ölçülmüş peak veya garanti değildir. Commit4GiB ayrı plan marjıdır, fiziksel RAM rezervi değildir. Runtimehost1GiB/commit1GiB/OSalarm koşulları, no-retry/no-download/no-automatic-threshold-lowering ve gerçek ölçüm zorunluluğu korunur. Gemma'nın1,5GiB/1GiB düşük eşikleri Qwen'e kopyalanmadı.

Gerçek son salt okunur ölçüm **{mem['memory']['at']}**: boş hostRAM **{mem['memory']['available_bytes']/2**30:.3f}GiB**, boşGPU **{mem['GPU']['free_MiB']}MiB**, commit **{mem['memory']['commit_available_bytes']/2**30:.3f}GiB**, OSfalse. RAM3GiB şartı **FAIL**; commit/GPU yeterli olması fiziksel RAM eksikliğini çözmez. Ayrıca vocab-only1,5GiB ön kontrolü de geçmedi. Bu nedenle **Qwen inference NOT_RUN**, güncel API kimliği ve tam tokenizer sayı UNKNOWN/PENDING. Model yükleme/kalite testi yapılmadı; Qwen için açıklama başarısızlığı veya başarısı iddia edilemez.

Bu koşullarda yeni Qwen inference komutu/yürütücüsü açılmadı. Kullanıcı uygulamaları/servisi kapatılmadı, güvenlik/yetki değiştirilmedi ve daha riskli eşiklere inilmedi. Gerekli kaynak koşulları gerçekten sağlandığında mevcut koşullu yetkiyle normal-user API kimliği + registered-template/native-tokenizer sayımı + SHA/bellek kapıları tamamlanıp en fazla1 Qwen denemesi hazırlanabilir. Bunun için yeni küçük hazırlık izni gerekmez; engel dış bellek koşuludur, izin eksikliği değil.

## 8. QA, korunma ve durma

**32 yeni test geçti**:21 ham V2 dosyası/hash,729/724 ayrımı,312output, orijinalgate sonucu, bağımsız dil/source/schema kontrolleri, marker false-negative, primary-ID, tüketilmiş claim,34 bellek örneği, güvenli şablon alt-kümesi/whitespace/range/system ayrımı, Qwen katman kimliği/KV/ayrı eşikler/gerçek RAM engeli, frozen request yalnızmodel farkı ve V1 başarısızlığı. Yeni template renderer'ının ilk geliştirme denemesinde `$msg.Role` alan erişimi desteği eksikti; yalnız bu yeni modülde düzeltildi ve test edildi. Bu run'ı değiştiren bir yöntem düzeltmesi değildir.

Önceki3679 dosyanın SHA envanteri korunur; GemmaV1/V2 hamları ve globalclaim aynı hash'tedir. Eski724token proof, dosya/script/QA/model/split/senaryo/44alıntı/ölçüt değiştirilmez. Yalnız status yeni bölümle güncellenir; önceki tam baytları QA ve tarihsel devamda saklanır. Yeni manifest rapor/notebook/test/görsel/JSON/CSV/cache-metadata kanıtlarını hash'ler. Bu turda yeni inference0, yeni OllamaAPI0, model indirme0, yeni eğitim0, otomatikyayın0;19×3/WP13 yok.

Notebook `notebooks/WP12_Gemma_V2_review_Qwen_preparation.ipynb`; QA `reports/qa/WP12/gemma_v2_review_qwen_preparation_v1/`; şekiller `reports/figures/WP12/gemma_v2_review_qwen_preparation_v1/`. Aktif durum: **Gemma A tek denemesi tüketildi; B hazırlığı yapıldı ama RAM/token/API kapılarında bloke; gerçek Qwen sonucu yok.** Kaynak/bellek koşulu değişmeden model isteği başlatılmaz.

## Ek — V2 ham HTTP body AYNEN

```json
{body}
```
'''
    text_new(c.ROOT/'reports/WP12_GEMMA_V2_REVIEW_QWEN_PREPARATION.md',report)
    text_new(c.ROOT/'docs/plan/WP12_POST_GEMMA_V2_RESOURCE_GATE_v1.md',f'''# WP12 — Gemma V2 sonrası koşullu durum

Kullanıcının koşullu yetkisi geçerli. A'nın tek isteği tüketildi; reset/retry yok. Orijinal TOKEN_COUNT_ALIGNMENT_FAILED korunur. Ayrı gerçek içerik incelemesi iki İngilizce cümle gösterdi; bu dilFAIL, Qwen hazırlığının yetkili gerekçesidir. Şablon farklılığı ve sayım UNKNOWN sınırları raporda açık.

Qwen yerel digest {resources['local_registered_digest']} ve tüm blob hash'leri doğrulandı. Ayrı {policy_text} planı; ölçülen hostRAM{mem['memory']['available_bytes']/2**30:.3f}GiB<3. Qwen NOT_RUN; API kimliği PENDING, tam tokenizer sayısı RAM kapısında UNKNOWN. Eşik düşürme/indirme/servis kapatma/API kısıtı aşma yok.

Sonraki izinli sıra, dış kaynak koşulları uygun olduğunda: aynı koşullu onayla bellek yeniden ölçümü→normal-user API identity→kayıtlı servis şablonu/tokenizer/proof→en fazla1 ayrı Qwen S01 isteği→tüm ham sonuç/semantik insan incelemesi→dur.19×3 kullanıcı sonuç değerlendirmesinden önce başlamaz. WP13/yeni eğitim/otomatik yayın yok. İzin eksikliği yok; mevcut engel fiziksel RAM ve doğrulanmamış token/API ön koşullarıdır.
''')
    before=(a.QA/'run_status_before.md').read_bytes();assert (c.ROOT/'run_status.md').read_bytes()==before
    prefix=f'''# WP12 — Gerçek Gemma V2 incelemesi; Qwen ayrı bellek kapısında durdu ·08.11.2026

- V2 run074723_6a9844b7f6d249c08bb38033d1ce218e HTTP200/stop,729serverinput/724offline/312output. Original TOKEN_COUNT_ALIGNMENT_FAILED aynen korundu, Aclaim tüketildi; tekrar/reset yok.21 ham dosya doğrulandı.
- Ayrı post-hoc içerik schema/primary-ID doğru; iki cümle İngilizce, language=tr yanlış. İlkitem2cümle; BP250mg/ambalajayrıntıları eksik. Çekirdek aktifmadde/sınıf/formülasyon kaynakla uyumlu; Türkçe/yönergeFAIL, insanPENDING. Marker yöntemi bu İngilizceyi kaçırdı; değiştirilmedi.
- Kayıtlı Ollama Go template2user turu, önceki GGUFJinja1user. Önkontrol varsayımı hatalıydı; ancak native729tekrarı sözlük-only1,5GiB RAM kapısında durdu, kesin5token nedeni sayısal olarak UNKNOWN. Eski724kanıtı düzeltilmedi. Sunucu renderbaytları yok; teknik sınır açık.
- Koşullu B, token hatası değil gerçek dilFAIL nedeniyle açıldı. Mevcut Qwen0edc…/blobhash doğrulandı;2.497GBmodel,36katman/8KVhead/288MiBteorikKV. Ayrı RAM3GiB/GPU3,5GiB/commit4GiB/OSfalse planı. Gerçek RAM{mem['memory']['available_bytes']/2**30:.3f}GiB<3; QwenNOT_RUN,API/tokenPENDING/UNKNOWN. Yeni istek/yürütücü açılmadı; riskli eşik düşürme yok.
-32 test geçti. Önceki3679 dosya ve eski status baytları korundu. Rapor reports/WP12_GEMMA_V2_REVIEW_QWEN_PREPARATION.md; notebook notebooks/WP12_Gemma_V2_review_Qwen_preparation.ipynb; QA reports/qa/WP12/gemma_v2_review_qwen_preparation_v1/. Yeni inference/API/indirme/eğitim0,19×3/WP13/yayın yok. Dış bellek koşulu değişmeden yeni model isteği başlatma.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''.encode('utf-8')
    (c.ROOT/'run_status.md').write_bytes(prefix+before)
    previous=c.read(a.QA/'previous_files_sha256.json')
    changed=[p for p,h in previous.items() if c.sha(c.ROOT/p)!=h];assert changed==['run_status.md'],changed
    assert c.sha(a.QA/'run_status_before.md')==previous['run_status.md']
    c.save_new(a.QA/'previous_artifacts_preservation.json',{'previous_files':len(previous),
        'unchanged_at_original_path':len(previous)-1,'only_updated_path':'run_status.md',
        'old_status_archived_exactly':True,'old_status_retained_as_suffix':(c.ROOT/'run_status.md').read_bytes().endswith(before),
        'Gemma_V1_and_V2_raw_runs_unchanged':True,'Gemma_claim_preserved':True,'new_inference_or_Ollama_API':0})
    print('V2 real review + Qwen resource block report complete; no inference or retry.')


if __name__=='__main__':main()
