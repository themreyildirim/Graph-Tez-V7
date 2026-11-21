"""S07 gerçek metin/kanıt görselleri ve raporu; yeni API veya düzeltme isteği yok."""
import json
import textwrap
from pathlib import Path
import wp12_openai_S07_actual_review as r
from wp12_api_security import public_sha,is_private_path


def save(name,value):r.scenario.old.c.save_new(r.QA/name,value)


def snapshot():
    p=r.read(r.budget.POLICY);records={**p['prior_public_records_sha256'],**p['immutable_public_inputs_sha256']}
    prior_manifest=r.scenario.QA/'evidence_manifest.json'
    for name,digest in r.read(prior_manifest).items():
        if name!='run_status.md':records[name]=digest
    records[prior_manifest.relative_to(r.ROOT).as_posix()]=public_sha(prior_manifest)
    for f in [*r.RUN.iterdir(),*r.budget.CONTROL.glob('*.json')]:
        if not is_private_path(f) and f.is_file():records[f.relative_to(r.ROOT).as_posix()]=public_sha(f)
    for name,digest in records.items():
        assert not is_private_path(name) and public_sha(r.ROOT/name)==digest
    return records


def figures(review,rows):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import networkx as nx
    ctx,payload,_,ann=r.scenario.context('S07')
    fig,axs=plt.subplots(3,3,figsize=(17,13),gridspec_kw={'width_ratios':[1,1.1,1.1]})
    for row,axes in zip(rows,axs):
        for ax in axes:ax.axis('off')
        axes[0].set_title(f"Birincil kaynak — fiziksel {row['physical_page']}",loc='left',fontsize=12,fontweight='bold')
        axes[0].text(0,.94,textwrap.fill(' '.join(row['primary_quote_exact'].split()),53),va='top',fontsize=11.2,linespacing=1.4)
        axes[0].text(0,.08,f"Item {row['item']}; toplam atıf: {len(row['all_cited_ids'])}\nTam kimlikler/aralıklar QA tablosunda",fontsize=10,color='#555')
        axes[1].set_title('Modelin değiştirilmemiş cümleleri',loc='left',fontsize=12,fontweight='bold')
        axes[1].text(0,.94,textwrap.fill(row['model_explanation_exact'],58),va='top',fontsize=11.5,linespacing=1.45)
        axes[2].set_title('Ajan inceleme notu — insan PENDING',loc='left',fontsize=12,fontweight='bold')
        axes[2].text(0,.94,textwrap.fill(row['agent_note_tr'],58),va='top',fontsize=10.7,linespacing=1.4,
            color='#9c4c35' if row['item']==3 else '#625831')
        axes[2].text(0,.08,'Teknik PASS ≠ tam Türkçe/semantik onay',fontsize=10,color='#946326')
    fig.suptitle('Gerçek S07: istisna bağlamı korunurken dil ve atıf notları ayrı kalır',fontsize=17,y=.99)
    fig.text(.02,.014,'Kaynak satır sonları yalnız gösterimde düzenlendi; model metni düzeltilmedi. Tam kanonik kaynaklar ve tüm atıflar JSON/CSV’de.',fontsize=10)
    plt.tight_layout(rect=(0,.04,1,.96));plt.savefig(r.FIG/'01_real_quotes_claims_and_flags.png',dpi=160);plt.close(fig)
    G=nx.DiGraph();pos={};labels={}
    for i,row in enumerate(rows):G.add_node('item'+str(i));pos['item'+str(i)]=(0,2-i);labels['item'+str(i)]=f"Item {i+1}"
    for i,source in enumerate(payload['sources']):
        q=source['quote_id'];G.add_node(q);pos[q]=(1,2-i);labels[q]=ann[q]['key']
    for i,row in enumerate(rows):
        for q in row['all_cited_ids']:G.add_edge('item'+str(i),q)
    fig,ax=plt.subplots(figsize=(12,5.2))
    colors=['#e8cfaa' if n=='item2' else '#d8e6ec' for n in G.nodes]
    nx.draw_networkx(G,pos,labels=labels,ax=ax,node_size=4100,node_color=colors,font_size=11,arrowsize=20,
        edge_color='#5b7c8d',width=1.7)
    ax.set_title('Yanıtın gerçek item → alıntı bağlantıları (3 + 1 + 1 atıf)',fontsize=15)
    ax.set_axis_off();ax.margins(.22)
    fig.text(.02,.02,'Item2 yalnız sınıf girişini cite eder; renal/doxycycline yorumu için atıf ayrıntısı ajan notudur. Kimlik bağlantısı semantik doğruluk garantisi değildir.',fontsize=9.5)
    plt.tight_layout(rect=(0,.06,1,.98));plt.savefig(r.FIG/'02_real_citation_network.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    u=review['usage'];bars=axs[0].bar(['Giriş','Çıkış'],[u['input_tokens'],u['output_tokens']],color=['#547f96','#8da68f'])
    axs[0].bar_label(bars,padding=4);axs[0].set(ylim=(0,2300),ylabel='Raw usage tokenı',title='2.466 toplam; cached=0, reasoning=0')
    vals=[float(review['input_cost_USD']),float(review['output_cost_USD'])]
    bars=axs[1].bar(['Giriş','Çıkış'],vals,color=['#547f96','#8da68f'])
    axs[1].bar_label(bars,labels=[f'${v:.7f}' for v in vals],padding=4)
    axs[1].set(ylim=(0,.0028),ylabel='Usage × resmî fiyat (USD)',title=f"S07 token maliyeti: ${review['usage_token_cost_USD']}")
    fig.text(.02,.015,'Vergi/fatura düzeltmeleri ve önceki kredi-hatalı isteğin bilinmeyen maliyeti dahil değildir.',fontsize=10)
    plt.tight_layout(rect=(0,.05,1,1));plt.savefig(r.FIG/'03_actual_usage_and_cost.png',dpi=160);plt.close(fig)


def main():
    if (r.QA/'independent_review.json').exists():raise RuntimeError('Review already exists; no overwrite')
    protected=snapshot();save('protected_prior_and_real_run_sha256.json',protected)
    prior=(r.ROOT/'run_status.md').read_bytes();(r.QA/'run_status_before.md').write_bytes(prior)
    review=r.inspect();assert all(review['checks'].values());rows,span=r.agent_annotations(review)
    save('independent_review.json',review);save('agent_item_reviews.json',rows)
    save('untranslated_span_agent_note.json',span)
    (r.QA/'exact_model_message.txt').write_bytes(review['exact_model_message'].encode('utf-8'))
    save('raw_response_reference.json',{'path':str(r.RUN/'inference_response_raw.json'),
        'raw_SHA256':public_sha(r.RUN/'inference_response_raw.json'),'model_message_unchanged':True})
    save('human_review_pending.json',{'case_id':'S07','run_id':r.RUN.name,'raw_response_sha256':public_sha(r.RUN/'inference_response_raw.json'),
        'status':'PENDING','reviewer_id':None,'decision':None,'reviewed_at':None,'items':rows,
        'agent_notes_are_not_human_approval':True,'automatic_release':False})
    save('technical_checks.json',review['checks'])
    import pandas as pd
    export=[]
    for x in rows:
        d=dict(x);d['all_cited_ids']=json.dumps(d['all_cited_ids'],ensure_ascii=False)
        d['all_cited_quotes_exact']=json.dumps(d['all_cited_quotes_exact'],ensure_ascii=False);export.append(d)
    pd.DataFrame(export).to_csv(r.QA/'source_claim_comparison.csv',index=False,encoding='utf-8-sig')
    rt=pd.read_csv(r.QA/'source_claim_comparison.csv')
    assert rt.model_explanation_exact.tolist()==[x['model_explanation_exact'] for x in rows]
    assert rt.primary_quote_exact.tolist()==[x['primary_quote_exact'] for x in rows]
    assert [json.loads(x) for x in rt.all_cited_ids]==[x['all_cited_ids'] for x in rows]
    pd.DataFrame(review['stages']).to_csv(r.QA/'HTTP_stages.csv',index=False,encoding='utf-8-sig')
    comparisons=r.read(r.ROOT/'reports/qa/WP12/openai_S01_success_review_v1/all_real_runs_comparison.json')['rows']
    combined=[{**x,'scenario':'S01','formal_human_review':'PENDING',
        'user_positive_statement':'SEPARATE_RECEIPT_FOR_TWO_ITEMS' if 'corrected account' in x['model_method'] else None} for x in comparisons]
    combined.append({'scenario':'S07','model_method':review['model'],'experiment_status':'COMPLETED_WITH_AGENT_QUALITY_FLAGS',
        'pipeline_terminal_status':'HTTP200 completed / technical PASS','actual_language_agent':review['Turkish_quality_agent'],
        'source_faithfulness_agent':review['source_core_agent'],'citation_note':review['citation_granularity_agent'],
        'human_review':'PENDING','formal_human_review':'PENDING','actual_server_prompt_tokens':1962,'output_tokens':504,
        'HTTP_latency_seconds':review['latency_HTTP_seconds'],'usage_token_cost_USD':review['usage_token_cost_USD'],
        'model_message_exact':review['exact_model_message'],'raw_response_ref':str(r.RUN/'inference_response_raw.json'),
        'raw_response_sha256':public_sha(r.RUN/'inference_response_raw.json')})
    combined.append({'scenario':'S04','model_method':'gpt-5.4-mini / planned','experiment_status':'LOCKED_NOT_RUN',
        'actual_language_agent':'NOT_RUN','source_faithfulness_agent':'NOT_RUN','human_review':'PENDING',
        'actual_server_prompt_tokens':None,'output_tokens':None,'usage_token_cost_USD':None})
    save('all_real_runs_and_locked_S04.json',{'rows':combined,'not_an_equal_task_model_benchmark':True,
        'missing_or_NOT_RUN_cost_not_zero':True,'S01_positive_statement_not_formal_QA_update':True})
    pd.DataFrame(combined).to_csv(r.QA/'all_real_runs_and_locked_S04.csv',index=False,encoding='utf-8-sig')
    figures(review,rows)
    from wp09_close_wp10_notebooks import execute,INIT
    execute('WP12_OpenAI_S07_actual_response_review.ipynb',[
        ('md','''# WP12 — Gerçek S07: teknik geçiş ve kaynak/dil incelemesi

Bu notebook yalnız kayıtlı cevabı inceler. Yeni API, model/optimizer veya otomatik tekrar yoktur. **HTTP200/şema PASS, tam Türkçe/semantik onay değildir.** S07 kalite notları ayrı, insan kararı PENDING; S04 kilitli kalır.'''),
        ('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/openai_S07_actual_review_v1'
F=ROOT/'reports/figures/WP12/openai_S07_actual_review_v1'
r=json.loads((Q/'independent_review.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'model':r['model'],'HTTP':r['HTTP_status'],'completion':r['completion_status'],
    'request_ID':r['API_request_id'],'süre_s':r['latency_HTTP_seconds'],'insan':'PENDING'}]))
print('Modelin birebir JSON mesajı:\n'+(Q/'exact_model_message.txt').read_text(encoding='utf-8'))
'''),('md','''**Yorum:** Tamamlanmış tek S07 yanıtı üç item içerir. Düzeltme yapılmadan gösterilir; bu metin üzerinde ikinci inference veya en iyi yanıt seçimi yoktur. Aşağıdaki notlar bu run'a bağlı **ajan okumasıdır**, genel semantik classifier veya kullanıcı insan kararı değildir.

## 1. Kaynaklar ve gerçek cümleler'''),('code',r'''
table=pd.read_csv(Q/'source_claim_comparison.csv')
with pd.option_context('display.max_colwidth',None):
    display(table[['item','physical_page','scope','kind','primary_quote_exact','model_explanation_exact','all_cited_ids','agent_note_tr','human_decision']])
from IPython.display import Image
display(Image(filename=str(F/'01_real_quotes_claims_and_flags.png')))
'''),('md','''**Kaynak yorumu:** BUN bildirimi sınıf kapsamında tutulmuş; “dozla ilişkili olabileceği” belirsizliği ve doxycycline için bağımsız doğrudan kanıt olmadığı açıklanmış. İstisna item'ında “yol açabilir” ile “Mevcut çalışmalara göre” ve renal koşul mevcut. Koşulsuz güvenlik veya yeni klinik negatif etiketi gözlenmedi.

**Dil kalite notu:** “impaired renal function” aynen İngilizce bırakılmış; kullanıcıya tam Türkçe açıklama gereksinimi tam karşılanmıyor. “tetracyclines” sınıf sözcüğü de İngilizce. “böbrek işlevi bozulmuş” yalnız ajan açıklama notudur; modelin metnine yazılmamıştır. Kaynak koşulunun var olması Türkçe anlatım kalitesini otomatik PASS yapmaz.

## 2. Gerçek atıf kapsamı'''),('code',r'''
display(Image(filename=str(F/'02_real_citation_network.png')))
display(pd.DataFrame([json.loads((Q/'untranslated_span_agent_note.json').read_text(encoding='utf-8'))]))
'''),('md','''**Atıf yorumu:** Item2'deki sınıf gözlemi doğrudan sınıf girişinden desteklenir. “Renal alt başlık” ve doxycycline karşılaştırması tüm girdi bağlamında açıklanabilir; ancak yalnız cite edilen sınıf-giriş cümlesi bu sözcükleri içermez. Item düzeyinde atıf ayrıntısı inceleme notudur. Mevcut şema/başarı ölçütü sonradan değiştirilmedi; teknik PASS geriye dönük FAIL yapılmadı. Doğru kimlik ile iddianın kaynak kapsamı ayrı değerlendirilir.

## 3. Gerçek token/maliyet ve korunan sayaçlar'''),('code',r'''
u=r['usage']
display(pd.DataFrame([{'input':u['input_tokens'],'cached':u['input_tokens_details']['cached_tokens'],
 'output':u['output_tokens'],'reasoning_in_output':u['output_tokens_details']['reasoning_tokens'],'total':u['total_tokens'],
 'input_USD':r['input_cost_USD'],'output_USD':r['output_cost_USD'],'S07_USD':r['usage_token_cost_USD']}]))
display(Image(filename=str(F/'03_actual_usage_and_cost.png')))
display(pd.DataFrame([r['aggregate_budget']]))
'''),('md','''**Yorum:**1962×$0,75/1M +504×$4,50/1M =$0,0037395. Gerçek cached ve reasoning alanları0; çıkış tokenına ikinci ücret eklenmedi. Ücret vergi/fatura düzeltmeleri hariç usage-token hesabıdır. S01+S07 bilinen completed token maliyeti$0,0056430; ilk429 usage'ı ve toplam fatura UNKNOWN kalır.9HTTP/3inference rezervi$0,069; eski kayıtlar sıfırlanmadı.4,813s HTTP süresi ağ/servis toplamıdır; tek örnekten hız/kararlılık/genelleme iddiası yoktur.

## 4. QA, geçmiş koşular ve insan kararı'''),('code',r'''
display(pd.DataFrame([{'kontrol':k,'sonuç':v} for k,v in r['checks'].items()]))
display(pd.DataFrame([json.loads((Q/'test_summary.json').read_text(encoding='utf-8'))]))
c=pd.read_csv(Q/'all_real_runs_and_locked_S04.csv')
display(c[['scenario','model_method','experiment_status','actual_language_agent','source_faithfulness_agent','human_review']])
display(pd.DataFrame([{'alan':k,'durum':r[k]} for k in ['schema_status','application_status','source_core_agent','Turkish_quality_agent','citation_granularity_agent','human_review']]))
'''),('md','''**Durma kararı:** Teknik kontroller geçti; dilde somut eksik ve atıf ayrıntısı notu nedeniyle koşulsuz kalite PASS verilmedi. İnsan karar formu PENDING. S01 olumlu kullanıcı beyanı ayrı kalır; S01/S07 resmî insan QA kaydı otomatik değiştirilmez. Kaynak PDF/senaryo/şema/prompt/istemci dondurulmuş; başarısız eski kayıtlar ve Qwen NOT_RUN korunmuştur. S04 hâlâ LOCKED_NOT_RUN. Yeni yöntem/yeniden deneme,19×3, yayın, eğitim ve WP13 yoktur. Sonuç kullanıcı incelemesine sunulur.

[Resmî model/fiyat](https://developers.openai.com/api/docs/models/gpt-5.4-mini); kullanıcı PDF'si050641Orig1s032lbl.pdf fiziksel4/7. Tam kaynak sayfaları bu raporun figür klasöründe görsel olarak incelenmiştir.''')])
    texts='\n\n'.join('> '+x['model_explanation_exact'] for x in rows)
    report=f'''# WP12 — Gerçek S07 Doxycycline/BUN açıklaması: bağımsız inceleme

08.11.2026 · Run `{r.RUN.name}`.

**Sonuç:** HTTP200/completed, JSON Schema ve kaynak-uygulama kontrolleri PASS. Sınıf bağlamı ve istisnanın iki cümlesinin çekirdek anlamı ajan okumasında korunmuş. Ancak **tam Türkçe kalite geçişi verilmedi**: kritik renal koşul “impaired renal function” İngilizce bırakılmış. İkinci item için atıf ayrıntısı notu var. İnsan kararı PENDING; otomatik yayın veya S04 yürütümü yoktur. Teknik PASS geri yazılmadı, kalite notları ayrı kayıttır.

## Modelin gerçek cümleleri — değiştirilmeden

{texts}

Tam model mesajı:

```json
{review['exact_model_message']}
```

Özgün HTTP cevabı `inference_response_raw.json` dosyasında kalır. Yeni `exact_model_message.txt` birebir mesaj metnidir. CSV round-trip ile cümle/alıntı/atıf eşliği kontrol edildi. İngilizce terim düzeltilip modelin başarısı gibi gösterilmedi.

## Teknik sonuç ve kaynak kimliği

| Alan | Gerçek değer |
|---|---|
| Model |{review['model']}|
| HTTP / completion |200 / completed; error ve incomplete_details null|
| Request-ID |{review['API_request_id']}|
| Response-ID |{review['response_id']}|
| JSON / uygulama |PASS /PASS; birincil sıra, scope/kind,3ayrı kaynak ve bağımlılık kapanışı doğru|
| Kaynak |Kullanıcı PDF'si050641Orig1s032lbl.pdf, DB00254;3frozen alıntı/380karakter|
| PDF SHA-256 |{review['source_PDF_sha256']}|
| PDF sayfa sayısı |{review['source_PDF_page_count']}|
| İnsan kararı |PENDING|

PyMuPDF'nin kabul edilmiş çıkarıcı tanımıyla fiziksel4/7tam sayfa metinleri yeniden salt okunur kontrol edildi. Tam sayfa metni, üç karakter dilimi ve alıntı hash'leri frozen bundle ile aynı. Sayfa PNG'leri görsel incelendi. Yeni alıntı oluşturulmadı ve girdi genişletilmedi. Belgenin kendi “latest approved” uyarısı/güncellik sınırı korunur; hash eşliği düzenleyici veya klinik doğruluk onayı değildir.

## Ajan kaynak/dil incelemesi

| Item | Kaynak okuması | Kalite/atıf notu |
|---|---|---|
|1 renal/BUN|Sınıf kapsamı ve dozla ilişkili olabileceği nitelemesi korunmuş. Doğrudan doxycycline kanıtı olarak alınmaması belirtilmiş.|tetracyclines sözcüğü İngilizce; üç kaynağa atıf var.|
|2 sınıf girişi|İlk gözlem cümlesi sınıf girişinden desteklenir; devam eden yorum tüm girdi bağlamıyla uyumlu okunabilir.|Yalnız sınıf girişine atıf var; literal alıntı renal/doxycycline sözcüklerini içermez. Bu item düzeyinde atıf ayrıntısı notudur.|
|3 istisna|May cause → yol açabilir; studies to date indicate → Mevcut çalışmalara göre; doxycycline ve renal işlev koşulu mevcut. İki kaynak cümlesi birlikte aktarılmış.|“impaired renal function” çevrilmemiş. Ajanın Türkçe açıklama notu “böbrek işlevi bozulmuş”tur; bu not LLM metnine eklenmemiştir.|

İstisnanın kapsamı var diye Türkçe gereksinimi otomatik geçmiş sayılmaz. “Mevcut çalışmalara göre” ifadesi sınırlı çalışma bağlamını koruyor; tüm insanlar/gelecek koşullar için evrensel güvenlik veya yeni bir klinik negatif etiketi gözlenmedi. Bunun insan semantik incelemesiyle değerlendirilmesi gerekir. BUN'a yeni açılım veya yeni yan etki/skor/MedDRA hedefi eklenmemiştir.

Atıf notu, kaynak seti genelinde desteklenebilen yorumla item'ın literal atfının ayrımını gösterir. Bu gözlem yeni bir zorunlu-kenar veya şema kuralı olarak geriye dönük eklenmedi; frozen kriter ve teknik PASS değiştirilmedi. Yeni çalışma ancak bu bulgular ayrı değerlendirilerek tasarlanabilir; bu tur yöntem düzeltmesi veya tekrar yoktur. Eski basit dil tarayıcısı da sonuç sonrası terim listesiyle değiştirilmedi.

![Gerçek kaynaklar, cümleler ve ajan notları](figures/WP12/openai_S07_actual_review_v1/01_real_quotes_claims_and_flags.png)

![Gerçek atıf bağlantıları](figures/WP12/openai_S07_actual_review_v1/02_real_citation_network.png)

Şekildeki5kenar yalnız gerçek response evidence_ids alanıdır:3+1+1. Biyolojik etkileşim, öğrenilmiş önem veya nedensellik değildir. Kaynak kimlikleri doğru olsa bile cümle anlamı ve okunabilirlik ayrıca değerlendirilir. Ajan notları bu tek run/raw hash'ine bağlıdır; S01 sabit cümle testi veya genel otomatik semantik classifier kullanılmadı.

## Usage, maliyet ve bütçe

| Alan | Değer |
|---|---:|
| Tam sunucu önkontrol / gerçek input |1962 /1962|
| Cached input |0|
| Output toplam |504|
| Output içindeki reasoning |0|
| Toplam token |2466|
| HTTP üretim süresi |4,813 s|
| Input token maliyeti |${review['input_cost_USD']}|
| Output token maliyeti |${review['output_cost_USD']}|
| S07 usage-token maliyeti |**${review['usage_token_cost_USD']}**|
| S01+S07 bilinen completed token maliyeti |${review['known_completed_S01_plus_S07_token_cost_USD']}|
| Global rezerv |9HTTP/3inference; $0,069|

Bağımsız Decimal hesabı:1962×$0,75/1M +504×$4,50/1M =$0,0037395. Cached ve reasoning0 raw alanlarda mevcuttur; çift sayılmadı.504token bütün JSON/ID/cümle çıktısını kapsar. [Resmî standart fiyatlar](https://developers.openai.com/api/docs/models/gpt-5.4-mini). Vergiler/fatura düzeltmeleri ve ilk429 isteğinin UNKNOWN usage maliyeti hariçtir; pilotun kesin toplam faturasını bilinen completed alt toplamla eşitlemiyoruz. Bakiye veya hesap API'si okunmadı.

![Gerçek usage ve token maliyeti](figures/WP12/openai_S07_actual_review_v1/03_actual_usage_and_cost.png)

Bütçe v2 komut kabulü kayıtta mevcut; eski6HTTP/2rezerv silinmeden3HTTP/1inference eklenmiş.30HTTP/10inference ve$0,25 operasyonel sınır korunur. Eski stop/rezervler ve yeniS07tek-attempt kilidi durur. Kalan kapasite yeni çalışma yetkisi değildir. RAM/VRAM telemetrisi toplanmadı; hız/kararlılık için tek ölçümden genelleme yapılmadı.

## QA, geçmiş kayıtlar ve durma noktası

{review['raw_run_files_verified']} kayıtlı run hash'i, dosya envanteri, raw→JSON, exact prompt/source/schema hash'leri, frozen source-ID/bağımlılıklar, PDF sayfaları, bağımsız usage/maliyet, sayaç/tek-deneme ve insan kapıları doğrulandı.14 yeni ağsız gerçek-kayıt testi PASS. Önceki28 hazırlık testi/QA dosyaları ezilmedi. Özgün model yanıtı, GemmaV1/V2 başarısızlıkları, QwenNOT_RUN, ilkHTTP429, S01 başarı kaydı ve S01 olumlu kullanıcı beyanı aynen korundu. Resmî S01 insanPENDING değiştirilmedi.

JSON/CSV karşılaştırma S01 ile S07'nin farklı senaryolar olduğunu gösterir; eş görevde model üstünlüğü veya klinik güvenlilik benchmark'ı değildir. Başarısız/NOT_RUN alanlar sıfır başarı/ücretle doldurulmadı. `reported_in_PDF` aday olarak kalır, `predicted_by_GNN` NOT_REQUESTED/null; model eğitimi veya veri etiketine yazım yapılmadı.

**Öneri:** S07'nin tam Türkçelik ve item2 atıf notları için kullanıcı/insan kararını bekle. Mevcut yanıtı sessizce düzeltme veya bu vakayı tekrar çalıştırma. S04 hâlâ LOCKED_NOT_RUN; otomatik ilerleme,19×3, yayın, model araması/eğitimi ve WP13 kapalıdır. Anahtar/.env okunmadı veya hash'lenmedi; bu incelemede yeni API isteği0.
'''
    with (r.ROOT/'reports/WP12_OPENAI_S07_RESULTS.md').open('x',encoding='utf-8') as f:f.write(report)
    assert r.read(r.QA/'test_summary.json')['returncode']==0
    header=f'''# WP12 — Gerçek S07 teknikPASS; dil/atıf notlarıyla insanPENDING ·08.11.2026

- Run173049_106b5d49c4f64383ad0b59cd7fd50e0e: gpt-5.4-mini-2026-03-17, HTTP200/completed;3HTTP/1inference. Request-ID {review['API_request_id']}. Yeni incelemeAPI0.
- Sınıf kapsamı, may cause/Mevcut çalışmalara göre ve istisnanın iki cümlesi mevcut. Kritik impaired renal function çevrilmemiş; tamTürkçe kalitePASS verilmedi. Item2 renal/doxy yorumunun yalnız sınıfgirişi atfı ajaninceleme notu. Teknikşema/başarıölçütüsonradandeğişmedi; çıktıdüzeltilmedi. İnsanPENDING,yayınkapalı.
-1962input/cached0/504output/reasoning0/2466total;4.813sHTTP. Bağımsıztokenücreti.0037395USD; S01+S07bilinensubtotal.0056430USD, tümfatura/ilk429UNKNOWN. Global9HTTP/3inference rezervi.069USD; eski6/2taşındı, reset/iadevarsayımıyok.
-14yeni ağsız test PASS; runhash/envanter/source/prompt/schema/PDF4-7tammetin/slice/hash doğrulandı. S01formalQA PENDINGveolumlubeyanayrı/öncekibaşarısızlıklar/QwenNOT_RUNaynı. S07resmîinsanPENDING, S04LOCKED_NOT_RUN. Anahtar/.envokunmadı/hash'lenmedi.
- Rapor reports/WP12_OPENAI_S07_RESULTS.md; notebook notebooks/WP12_OpenAI_S07_actual_response_review.ipynb; QA reports/qa/WP12/openai_S07_actual_review_v1/. KullanıcıS07notlarınıdeğerlendirene kadardur; tekrar/S04/19×3/yeniyöntem/yayın/eğitim/WP13yok.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    assert (r.ROOT/'run_status.md').read_bytes()==prior
    (r.ROOT/'run_status.md').write_bytes(header.encode('utf-8')+prior)
    assert all(public_sha(r.ROOT/p)==h for p,h in protected.items())
    save('final_preservation.json',{'protected_public_files_unchanged':len(protected),'all_match':True,
        'prior_status_bytes_retained':(r.ROOT/'run_status.md').read_bytes().endswith(prior),
        'new_API_requests':0,'api_key_or_dotenv_read':False,'tests_passed':14,'human_review':'PENDING',
        'S04':'LOCKED_NOT_RUN','source_PDF_pages_visually_inspected':[4,7]})
    files=[r.ROOT/p for p in ['scripts/wp12_openai_S07_actual_review.py','scripts/wp12_openai_S07_actual_outputs.py',
        'tests/test_wp12_openai_S07_actual_review.py','reports/WP12_OPENAI_S07_RESULTS.md',
        'notebooks/WP12_OpenAI_S07_actual_response_review.ipynb','run_status.md']]
    files.extend(f for folder in [r.QA,r.FIG] for f in folder.iterdir() if not is_private_path(f) and f.is_file())
    save('evidence_manifest.json',{f.relative_to(r.ROOT).as_posix():public_sha(f) for f in files})
    print(json.dumps({'status':review['status'],'tests_passed':14,'protected_public_files':len(protected),'new_API_requests':0,'S04':'LOCKED_NOT_RUN'}))


if __name__=='__main__':main()
