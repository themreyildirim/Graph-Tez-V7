"""Kayıtlı S04 yanıtından rapor/tablolar/görseller; inference veya key okuma yok."""
import json
import textwrap
from decimal import Decimal
import pandas as pd
import wp12_openai_S04_actual_review as r
from wp12_api_security import public_sha, is_private_path
from wp09_close_wp10_notebooks import execute, INIT


def save(name, value):
    r.scenario.old.c.save_new(r.QA/name, value)


def snapshot():
    config=r.read(r.budget.POLICY)
    records=dict(config['protected_prior_public_files_sha256'])
    manifest=r.budget.QA/'evidence_manifest.json'
    for n,h in r.read(manifest).items():
        if n!='run_status.md':records[n]=h
    records[manifest.relative_to(r.ROOT).as_posix()]=public_sha(manifest)
    for f in [*r.RUN.iterdir(),*r.budget.CONTROL.iterdir()]:
        if f.is_file() and not is_private_path(f):records[f.relative_to(r.ROOT).as_posix()]=public_sha(f)
    assert all(not is_private_path(n) and public_sha(r.ROOT/n)==h for n,h in records.items())
    return records


def figures(review, rows):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import networkx as nx
    for row in rows:
        texts=[row['primary_quote_exact'],row['model_explanation_exact'],row['agent_note_tr']]
        wrapped=[textwrap.fill(' '.join(t.split()),54) for t in texts]
        height=max(7.5,max(t.count('\n')+1 for t in wrapped)*.22+2.8)
        fig,axs=plt.subplots(1,3,figsize=(17,height))
        for ax,text,title in zip(axs,wrapped,['Birincil kaynak: birebir metin','Gerçek model açıklaması','Ajan notu; insan PENDING']):
            ax.axis('off');ax.set_title(title,loc='left',fontsize=12,fontweight='bold')
            ax.text(0,.98,text,va='top',fontsize=10.4,linespacing=1.4,transform=ax.transAxes)
        fig.suptitle(f"S04 item {row['item']} · fiziksel sayfa {row['physical_page']} · {len(row['all_cited_ids'])} atıf",fontsize=16,y=.985)
        fig.text(.02,.035,'Görselde satır sonları düzenlendi. Kaynak ve model metni JSON/CSV’de aynen korunur; ajan notu model çıktısı değildir.',fontsize=10)
        fig.text(.02,.015,'Kaynak kimliği: '+row['primary_quote_id'],fontsize=8.3)
        plt.tight_layout(rect=(0,.07,1,.95))
        plt.savefig(r.FIG/f'0{row["item"]}_real_source_and_explanation.png',dpi=155);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    u=review['usage'];b=axs[0].bar(['Giriş','Çıkış'],[u['input_tokens'],u['output_tokens']],color=['#547f96','#8ca186'])
    axs[0].bar_label(b,padding=4);axs[0].set(ylim=(0,3300),ylabel='Gerçek usage tokenı',title='3.604 toplam; cache=0, reasoning=0')
    values=[float(review['input_cost_USD']),float(review['output_cost_USD'])]
    b=axs[1].bar(['Giriş','Çıkış'],values,color=['#547f96','#8ca186'])
    axs[1].bar_label(b,labels=[f'${v:.6f}' for v in values],padding=4)
    axs[1].set(ylim=(0,.0042),ylabel='Usage × standart fiyat (USD)',title='S04 token maliyeti: $0,005613')
    fig.text(.02,.015,'Vergi/fatura düzeltmeleri ve önceki 429 isteğinin bilinmeyen maliyeti dahil değildir.',fontsize=10)
    plt.tight_layout(rect=(0,.05,1,1));plt.savefig(r.FIG/'04_actual_usage_and_cost.png',dpi=160);plt.close(fig)
    G=nx.DiGraph();pos={};labels={}
    sources=r.scenario.context('S04')[1]['sources']
    for i,s in enumerate(sources):
        node=s['quote_id'];G.add_node(node);pos[node]=(1,2-i)
        labels[node]=f"p{s['physical_page']} [{s['char_start']},{s['char_end']})\n{node[6:16]}…"
    for i,row in enumerate(rows):
        node='item'+str(i+1);G.add_node(node);pos[node]=(0,2-i);labels[node]=f'Item {i+1}'
        for q in row['all_cited_ids']:G.add_edge(node,q)
    fig,ax=plt.subplots(figsize=(12,6))
    nx.draw_networkx(G,pos,labels=labels,ax=ax,node_size=5300,node_color='#dce7ed',font_size=10,
                     arrowsize=18,width=1.5,edge_color='#6d8b9b')
    ax.set_title('Gerçek item → kaynak atıfları: 1 + 2 + 3 bağlantı',fontsize=15)
    ax.set_axis_off();ax.margins(.25)
    fig.text(.02,.045,'Bir PDF, iki fiziksel sayfa, üç örtüşebilen alıntı. Altı atıf bağımsız altı kanıt değildir.',fontsize=10)
    fig.text(.02,.02,'Bu ağ biyolojik ilişki veya model attribution ağı değildir; yalnız kaydedilmiş evidence_ids alanıdır.',fontsize=10)
    plt.tight_layout(rect=(0,.08,1,.99));plt.savefig(r.FIG/'05_actual_citation_network.png',dpi=160);plt.close(fig)


def main():
    if (r.QA/'independent_review.json').exists():raise RuntimeError('NO_OVERWRITE_EXISTING_REVIEW')
    protected=snapshot();save('protected_prior_and_real_run_sha256.json',protected)
    previous=(r.ROOT/'run_status.md').read_bytes()
    with (r.QA/'run_status_before.md').open('xb') as f:f.write(previous)
    review=r.inspect();assert all(review['checks'].values());rows=r.agent_annotations(review)
    assert r.read(r.QA/'test_summary.json')['returncode']==0
    save('independent_review.json',review);save('technical_checks.json',review['checks'])
    save('agent_item_reviews.json',rows)
    with (r.QA/'exact_model_message.txt').open('x',encoding='utf-8',newline='') as f:f.write(review['exact_model_message'])
    save('raw_response_reference.json',{'path':str(r.RUN/'inference_response_raw.json'),'sha256':r.RAW_HASH,
        'original_raw_unchanged':True,'model_message_text_sha256':__import__('hashlib').sha256(review['exact_model_message'].encode()).hexdigest()})
    save('human_review_pending.json',{'case_id':'S04','run_id':r.RUN.name,'raw_response_sha256':r.RAW_HASH,
        'status':'PENDING','reviewer_id':None,'role':None,'decision':None,'reviewed_at':None,
        'agent_notes_are_not_human_decision':True,'automatic_release':False,
        'frozen_review_plan_reference':'reports/qa/WP12/openai_S04_preparation_v1/human_review_plan_S04.json',
        'recording_control':'Separate attributed append-only event scoped to run/response/items/quotes; no automatic write or publication.'})
    export=[]
    for row in rows:
        x=dict(row)
        for k in ['all_cited_ids','all_cited_quotes_exact']:x[k]=json.dumps(x[k],ensure_ascii=False)
        export.append(x)
    pd.DataFrame(export).to_csv(r.QA/'source_claim_comparison.csv',index=False,encoding='utf-8-sig')
    back=pd.read_csv(r.QA/'source_claim_comparison.csv')
    assert back.model_explanation_exact.tolist()==[x['model_explanation_exact'] for x in rows]
    assert back.primary_quote_exact.tolist()==[x['primary_quote_exact'] for x in rows]
    assert [json.loads(x) for x in back.all_cited_quotes_exact]==[x['all_cited_quotes_exact'] for x in rows]
    pd.DataFrame(review['stages']).to_csv(r.QA/'HTTP_stages.csv',index=False,encoding='utf-8-sig')
    # New versioned history; old S04 NOT_RUN snapshot remains a true historical record.
    old=r.read(r.ROOT/'reports/qa/WP12/openai_S07_actual_review_v1/all_real_runs_and_locked_S04.json')['rows']
    combined=[x for x in old if x.get('scenario')!='S04']
    combined.append({'scenario':'S04','model_method':review['model'],'experiment_status':'COMPLETED_WITH_AGENT_REVIEW_NOTES',
        'pipeline_terminal_status':'HTTP200 completed / technical PASS','actual_language_agent':review['Turkish_quality_agent'],
        'source_faithfulness_agent':review['source_core_agent'],'formal_human_review':'PENDING','human_review':'PENDING',
        'actual_server_prompt_tokens':2828,'output_tokens':776,'HTTP_latency_seconds':review['latency_seconds'],
        'usage_token_cost_USD':review['usage_token_cost_USD'],'model_message_exact':review['exact_model_message'],
        'raw_response_ref':str(r.RUN/'inference_response_raw.json'),'raw_response_sha256':r.RAW_HASH})
    save('all_real_runs_comparison.json',{'rows':combined,'not_an_equal_task_model_benchmark':True,
        'previous_failed_and_NOT_RUN_rows_preserved':True,'historical_S04_NOT_RUN_snapshot_not_edited':True,
        'formal_human_decisions_unchanged':True,'missing_cost_is_not_zero':True})
    pd.DataFrame(combined).to_csv(r.QA/'all_real_runs_comparison.csv',index=False,encoding='utf-8-sig')
    save('official_price_verification.json',{'source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini',
        'checked_date_Europe_Istanbul':'2026-11-08','official_page_opened':True,
        'standard_USD_per_million':{'input':'0.75','cached_input':'0.075','output':'4.50'},
        'matches_frozen_run_policy':True,'review_makes_no_billable_model_API_call':True})
    figures(review,rows)
    execute('WP12_OpenAI_S04_actual_response_review.ipynb',[
        ('md','# WP12 — Gerçek S04 Erythromycin yanıtı\n\nYalnız kayıtlı yanıt incelenir; yeni API veya model eğitimi yoktur. Teknik PASS, kaynak anlamının eksiksizliği veya insan onayı değildir. Aşağıdaki ajan notları bu tek run/hash içindir, genel semantik sınıflayıcı değildir.'),
        ('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/openai_S04_actual_review_v1'
F=ROOT/'reports/figures/WP12/openai_S04_actual_review_v1'
read=lambda name:json.loads((Q/name).read_text(encoding='utf-8'))
r=read('independent_review.json')
display(pd.DataFrame([{'model':r['model'],'HTTP':r['HTTP_status'],'tamamlama':r['completion_status'],
 'request_ID':r['API_request_id'],'süre_s':r['latency_seconds'],'insan':'PENDING'}]))
print('Gerçek model mesajı, değiştirilmeden:\n'+(Q/'exact_model_message.txt').read_text(encoding='utf-8'))
'''),
        ('md','**Yorum:** Tek S04 inference HTTP200/completed. Metin tekrar üretilmedi veya düzeltilmedi. İngilizce kaynak başlıkları ve bozuk Türkçe ifade dahil tüm yanıt aynen korunur.'),
        ('code',r'''
table=pd.read_csv(Q/'source_claim_comparison.csv')
with pd.option_context('display.max_colwidth',None):
    display(table[['item','physical_page','kind','primary_quote_exact','model_explanation_exact','all_cited_ids','agent_note_tr','human_decision']])
from IPython.display import Image
for name in ['01_real_source_and_explanation.png','02_real_source_and_explanation.png','03_real_source_and_explanation.png']:
    display(Image(filename=str(F/name)))
'''),
        ('md','**Kaynak/dil yorumu:** Bilinmeyen sıklık mevcut verilerden hesaplanamama olarak açıklanmış; nadir/yaygın/yüzde/garantiye çevrilmemiş. Sayfa4 başlangıcı ve sayfa5 devamı mevcut. Kaynakta olmayan “erken” zaman nitelemesi, usually→özellikle aktarımı ve bazı özet eksikleri ayrı nottur. İngilizce başlıklar alıntı olarak kullanılmış ve anlamları Türkçe verilmiştir; tinnitus/vertigo gibi tıbbi terimler ayrıca okunabilirlik incelemesi gerektirir. “belirli bir oranlara” düzeltilmeden saklanan dilbilgisi sorunudur.'),
        ('code',r'''
display(pd.DataFrame(r['page_checks']));display(pd.DataFrame(r['quote_checks']))
display(Image(filename=str(F/'05_actual_citation_network.png')))
'''),
        ('md','**Atıf yorumu:** Birincil quote-ID, scope/kind ve zorunlu bağlam kapanışı doğru. Gerçek atıflar 1+2+3. Bunlar bir PDF ve iki sayfaya bağlı üç örtüşen alıntıdır; bağımsız altı kanıt değildir. Fiziksel4/5 tam metni ve birebir aralıklar kabul edilmiş çıkarıcıyla doğrulandı. Doğru ID, kaynak dışı “erken” nitelemesini otomatik tespit etmez.'),
        ('code',r'''
u=r['usage']
display(pd.DataFrame([{'input':u['input_tokens'],'cached':u['input_tokens_details']['cached_tokens'],
 'output':u['output_tokens'],'reasoning':u['output_tokens_details']['reasoning_tokens'],'total':u['total_tokens'],
 'input_USD':r['input_cost_USD'],'output_USD':r['output_cost_USD'],'S04_USD':r['usage_token_cost_USD']}]))
display(Image(filename=str(F/'04_actual_usage_and_cost.png')))
display(pd.DataFrame([r['aggregate_budget']]))
'''),
        ('md','**Maliyet yorumu:** 2828×0.75/1M +776×4.50/1M =0.005613USD; cache/reasoning0. Bilinen completed S01+S07+S04 alt toplamı0.0112560USD; önceki429 ve fatura UNKNOWN olduğu için kesin pilot faturası değildir. Eski rezervler korunarak global12HTTP/4inference/.092USD oldu; tavan30/10/.25USD. RAM/VRAM telemetrisi toplanmadı, sıfır sayılmaz.'),
        ('code',r'''
history=read('all_real_runs_comparison.json')['rows']
display(pd.DataFrame(history).drop(columns=['model_message_exact'],errors='ignore'))
display(pd.DataFrame([read('test_summary.json')]))
display(pd.DataFrame({'kontrol':list(r['checks']),'sonuç':list(r['checks'].values())}))
display(pd.DataFrame([read('human_review_pending.json')]))
'''),
        ('md','**Karar sınırı:** 18 yeni ağsız teknik test PASS; bunlar semantik doğruluk veya klinik geçerlilik kanıtı değildir. Test-only yanlış-anlam mutasyonu doğruID ile teknik kapıdan geçebildiği halde semantic_success=None ve insanPENDING kalır. Gemma başarısızlıkları, QwenNOT_RUN, ilk429 ve eski S01/S07 değişmedi. S07 kullanıcının tamTürkçe/atıf kalite itirazı ayrı beyanında korunur. Farklı senaryolar ve yöntemler eş görevli model benchmark’ı değildir. Tek yanıtla kararlılık/genelleme çıkarılmaz. reported_in_PDF aday, predicted_by_GNN NOT_REQUESTED/null. Yeni senaryo/tekrar/19×3/yayın/WP13 başlamaz; kullanıcı değerlendirmesi beklenir.'),
    ])
    summaries='\n\n'.join(f"### Item {x['item']} — fiziksel sayfa {x['physical_page']}\n\n> "+
        x['model_explanation_exact']+f"\n\nBirincil kaynak: `{x['primary_quote_id']}`.\n\nAjan notu: {x['agent_note_tr']}" for x in rows)
    report=f'''# WP12 — Gerçek S04: bilinmeyen sıklık ve kaynak/dil incelemesi

08.11.2026 · Europe/Istanbul. Kullanıcının çalıştırdığı tek gerçek S04 kaydı salt okunur incelendi. **Teknik PASS; kaynak/dil notları var; resmî insan kararı PENDING.** Yeni API, otomatik tekrar veya yöntem değişikliği yapılmadı.

| Alan | Doğrulanmış değer |
|---|---|
| Model | {review['model']} |
| Request-ID | {review['API_request_id']} |
| HTTP / tamamlama | 200 / completed; üç HTTP adımı, tek inference |
| JSON Schema / uygulama | PASS / PASS |
| Input / cached / output / reasoning | 2828 / 0 / 776 / 0 |
| Toplam token | 3604 |
| HTTP üretim süresi | 5,203 saniye |
| Usage-token maliyeti | 0,005613 USD |
| Ham yanıt SHA-256 | {r.RAW_HASH} |
| İnsan QA / otomatik yayın | PENDING / kapalı |

## Kaynak ve bağımsız teknik kontrol

Kullanıcı PDF'si `data/user_pdfs/pil.502.pdf`, DB00199 kaynak bağlamında altı fiziksel sayfadır. PDF SHA-256 `{review['source_PDF_sha256']}`. Fiziksel4 ve5 tam sayfaları, kabul edilmiş aynı PyMuPDF sürüm/seçenekleriyle yeniden salt okunur kontrol edildi; tam metinler, üç alıntı aralığı ve hash'ler frozen kayıtlarla aynı. İki sayfanın gerçek render'ı ayrıca görsel incelendi. Kaynak anlamı/belge güncelliği/ürün–ana ilaç eşdeğerliği hash ile onaylanmış olmaz.

Soru, kabul kriteri, prompt, şema, kaynak kimlikleri, nitelemeler ve zorunlu bağlamlar S07 öncesinde hazırlanan S04 isteğiyle aynı. Tam kaynaklar3803karakterdir; örtüşme dahil sayımdır. Unknown alıntısı sayfa5 ve sayfa4 bağlamını korur. Tam PDF değil bu alıntılar gönderilmiş; model araç çağrısı yapmamış. `source_request.json` dosyasındaki serileştirme/satır sonu farkı içerik değişikliği değildir.

Ham HTTP/response dosyalarındaki20 kayıtlı hash, envanter, request/response-ID, tamamlama, raw→JSON, bağımsız schema/application, exact server precount ve usage/maliyet eşleşti. Modelin gerçekten ne döndürdüğü ham kayıttan doğrulandı; yeni inference yok. On sekiz ağsız test PASS. Bunlar kaynak anlamının tam doğru olduğunu kanıtlamaz; yanlış-anlam/doğru-ID test-only mutasyonu semantik kapının insan incelemesi gerektirdiğini gösterir.

## Gerçek açıklamalar — düzeltilmeden

{summaries}

Tam JSON mesajı `exact_model_message.txt` ve çalıştırılmış notebook'ta aynen gösterilir. Her item'ın tam birincil alıntısı, tüm atıfları ve nitelemeleri `source_claim_comparison.csv` / `agent_item_reviews.json` içindedir. Modelin Türkçesi sessizce düzeltilmedi. İngilizce başlıklar burada kaynak alıntısıdır; genel/klinik bir koşulun açıklamasız İngilizce bırakılmasıyla aynı değerlendirilmez.

## Bilimsel değerlendirme

Ana frozen S04 sorusunun bilinmeyen sıklık anlamı ve iki sayfa bağlamı korunuyor. Kaynak ne sıklık oranı veriyor ne de “nadir/yaygın” sınıfı sunuyor; model bunları eklememiş. Bununla birlikte kaynak sadakati bütün cümleler için kusursuz değildir: “erken belirtiler” zamansal nitelemesinin kanıtı yok; “usually associated” açık “genellikle ilişkili” yerine daha serbest aktarılmış. Bu nedenle teknik geçişi tam kaynak/Türkçe kalite onayı yapmıyoruz.

Item2'deki tıbbi terimler ve kısa anlatım hasta dili açısından değerlendirilmelidir. Bazı kaynak ayrıntıları özetlenmemiştir: ishalin şiddet/uzama/kan-mukus koşulları; ayrıca ciddi püstüloz reaksiyonunun kendi bilinmeyen sıklık uyarısı; çocuklar ve raporlama bölümü. Bunların tümünün sorunun gerektirdiği kapsamda zorunlu olup olmadığı insan değerlendirmesine aittir; frozen kriter sonradan genişletilmedi. Kaynakta olmayan yeni bir yan etki adı veya sayısal olasılık bu ajan okumasında gözlenmedi; bu ifade genel bir otomatik halüsinasyon tespit garantisi değildir.

Item atıfları sırasıyla1/2/3tür; birincil alıntı amaçları ve bağımlılıklar doğru. “Tekrar” sözcüğü örtüşen kaynak aralıklarını bağımsız yeni kanıt haline getirmemelidir. Klinik nedensellik, hasta güvenliği veya risk doğrulaması yapılmadı. SIDER unknown çiftleri negatif olarak yeniden etiketlenmedi; hiçbir model girdisi/etiketi/skoru oluşturulmadı.

## Token, maliyet ve bütçe

Sunucu önkontrol2828token ile gerçek usage input2828 eşit. Output776token tüm JSON/kimlik/açıklamayı içerir;1200 sınırının altında. Reasoning0 output'a tekrar eklenmedi. Input maliyeti0.002121USD, output0.003492USD; toplam0.005613USD. Standart input0.75 / cached0.075 / output4.50USD/milyon fiyatları [resmî model sayfasından](https://developers.openai.com/api/docs/models/gpt-5.4-mini) doğrulandı; frozen politikayla aynı. Vergi/fatura düzeltmeleri dahil değildir.

Bilinen completed S01+S07+S04 token maliyeti0.0112560USD. İlk429 usage/fatura bilinmediği için bu kesin toplam fatura değildir. Global sayaç eski9HTTP/3inference'dan12HTTP/4inference'a, operasyonel rezerv0.069'dan0.092USD'ye çıktı. Hiçbir eski rezerv silinmedi. Toplam tavan30HTTP/10inference/0.25USD olarak kaldı. Kalan kapasite yeni senaryo veya yeniden deneme izni değildir.

RAM/VRAM telemetrisi bu bulut isteğinde toplanmadı; NOT_COLLECTED. Süre tek gerçek ölçümdür; farklı senaryolarda model üstünlüğü veya çalışma kararlılığı sonucu çıkarılmaz. API anahtarı ve.env inceleme sırasında okunmadı, hash'lenmedi veya envantere alınmadı; yalnız kayıtlı var/yok beyanı vardır. Authorization başlığı kaydedilmedi.

## Kanıtlar ve durma noktası

Önceki GemmaV1/V2 başarısızlıkları, QwenNOT_RUN, ilk429, S01 ve S07 kayıtları aynen korundu. S07 kullanıcının tamTürkçe/atıf kalite itirazı ayrı beyanında kalır; resmî QA otomatik değiştirilmedi. Tarihsel S04 NOT_RUN hazırlık kayıtları silinmedi; bu yeni sürüm gerçek sonucu ayrıca ekler. Karşılaştırma tablosu farklı görev/yöntemleri içerir; kontrollü eş görevli model benchmark'ı değildir.

Çıktılar: `notebooks/WP12_OpenAI_S04_actual_response_review.ipynb` (çalıştırılmış), `reports/qa/WP12/openai_S04_actual_review_v1/` (ham yanıt referansı, birebir metin, kaynak/iddia CSV/JSON, test ve hash manifesti), `reports/figures/WP12/openai_S04_actual_review_v1/` (üç gerçek kaynak/yanıt karşılaştırması, usage/maliyet, atıf ağı). Şekiller yalnız gerçek dosyalardan üretilmiştir; metin sarma gösterim amaçlıdır.

**Öneri:** İnsan incelemesinde bilinmeyen sıklık anlamını, “erken” ekini, usually aktarımını, özet kapsamını, tam Türkçeyi ve item atıflarını ayrı değerlendir. Karar, inceleyici kimliği/rolü/tarihi ve run–response–item/quote kapsamıyla ayrı olay kaydına bağlanmalıdır. Bu rapor insan adına onay veya ret yazmaz. Tek vaka kalite notu genelleme/klinik doğruluk kanıtı değildir. Kullanıcı değerlendirmesini bekle; tekrar, başka senaryo,19×3, yeni yöntem/eğitim, otomatik yayın veya WP13 uygulaması başlatma.
'''
    with (r.ROOT/'reports/WP12_OPENAI_S04_RESULTS.md').open('x',encoding='utf-8') as f:f.write(report)
    header=f'''# WP12 — Gerçek S04 teknik PASS; kaynak/dil notları, insan PENDING ·08.11.2026

- {r.RUN.name}: GPT-5.4-mini-2026-03-17, HTTP200/completed; tek inference/üçHTTP. İnceleme sırasında yeni API0, key/.env okuma yok.
- Bilinmeyen sıklık ve p4/p5 bağlamı korunmuş. Kaynakta olmayan “erken”, usually aktarımı, özet eksikleri ve dilbilgisi notları ayrı. Teknik PASS tam semantik/Türkçe veya insan onayı değildir; insan PENDING, yayın kapalı.
- 2828input/776output/3604total; cache0/reasoning0;5.203s;0.005613USD token maliyeti. Completed S01+S07+S04 bilinen alt toplam0.0112560USD; ilk429/fatura UNKNOWN. Global12HTTP/4inference/.092USD rezerv; tavan30/10/.25 aynı, eski rezervler korundu.
- 18 yeni ağsız test PASS;20 runhash ve envanter, source/prompt/schema, gerçek PDF fiziksel4/5 tammetin/dilim/hash ve usage/maliyet doğrulandı. Önceki dosyalar korunuyor; S01/S07 insanQA ve GemmaFAIL/QwenNOT_RUN aynı.
- Rapor reports/WP12_OPENAI_S04_RESULTS.md; notebook notebooks/WP12_OpenAI_S04_actual_response_review.ipynb; QA reports/qa/WP12/openai_S04_actual_review_v1/. İnsan değerlendirmesini bekle. Yeni istek/tekrar/19×3/yayın/eğitim/WP13 uygulaması yok; WP13 yalnız kapsam belgesi.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    assert (r.ROOT/'run_status.md').read_bytes()==previous
    (r.ROOT/'run_status.md').write_bytes(header.encode('utf-8')+previous)
    assert all(public_sha(r.ROOT/n)==h for n,h in protected.items())
    save('final_preservation.json',{'protected_public_files':len(protected),'all_match':True,
        'run_status_old_bytes_exact_suffix':(r.ROOT/'run_status.md').read_bytes().endswith(previous),
        'new_API_requests':0,'key_or_dotenv_read':False,'tests_passed':18,'human_review':'PENDING',
        'PDF_pages_visually_inspected':[4,5],'new_scenarios':'NOT_AUTHORIZED','WP13':'IMPLEMENTATION_NOT_STARTED'})
    files=[r.ROOT/n for n in ['scripts/wp12_openai_S04_actual_review.py','scripts/wp12_openai_S04_actual_outputs.py',
        'tests/test_wp12_openai_S04_actual_review.py','reports/WP12_OPENAI_S04_RESULTS.md',
        'notebooks/WP12_OpenAI_S04_actual_response_review.ipynb','run_status.md']]
    files += [p for folder in [r.QA,r.FIG] for p in folder.iterdir() if p.is_file() and not is_private_path(p)]
    save('evidence_manifest.json',{p.relative_to(r.ROOT).as_posix():public_sha(p) for p in files})
    print(json.dumps({'status':review['status'],'protected_public_files':len(protected),'tests_passed':18,'new_API_requests':0}))


if __name__=='__main__':main()
