"""Gerçek S01 kaynak/usage karşılaştırma çıktıları; API/anahtar kullanmaz."""
import json
from pathlib import Path
from datetime import datetime,timezone
import textwrap
import wp12_openai_S01_success_review as r
from wp12_api_security import public_sha,is_private_path


def save(name,obj):r.a.c.save_new(r.QA/name,obj)


def protected_snapshot():
    previous=r.read(r.attempt.POLICY)['protected_prior_public_files_sha256']
    files={r.ROOT/p:d for p,d in previous.items()}
    for manifest in [r.attempt.QA/'evidence_manifest.json']:
        for p,d in r.read(manifest).items():
            if p!='run_status.md':files[r.ROOT/p]=d
        files[manifest]=public_sha(manifest)
    for p,d in r.read(r.a.POLICY)['immutable_public_inputs_sha256'].items():files[r.ROOT/p]=d
    for p in [*r.RUN.iterdir(),*r.attempt.CONTROL.glob('*.json'),r.PDF]:
        if not is_private_path(p) and p.is_file():files[p]=public_sha(p)
    old=r.read(r.ROOT/'reports/qa/WP12/gemma_v2_review_qwen_preparation_v1/real_comparison_v1_v2_Qwen_NOT_RUN.json')
    for row in old['rows']:
        if row.get('raw_response_ref'):
            p=Path(row['raw_response_ref']);files[p]=row['raw_response_sha256']
    result={}
    for p,d in files.items():
        if is_private_path(p):raise ValueError('PRIVATE_PATH_EXCLUDED')
        assert public_sha(p)==d
        result[p.relative_to(r.ROOT).as_posix()]=d
    return result


def figures(review,rows,comparison):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch,Patch
    # Kanonik metin aynı kalır; görselde yalnız satır/boşluk düzenlemesi yapılır.
    fig,axs=plt.subplots(2,2,figsize=(15,8))
    for row,axes in zip(rows,axs):
        for ax in axes:ax.axis('off')
        left,right=axes
        left.set_title(f"PDF fiziksel sayfa {row['physical_page']} — {row['statement_kind']}",loc='left',fontsize=13,fontweight='bold')
        left.text(0,.92,textwrap.fill(' '.join(row['source_quote_exact'].split()),75),va='top',fontsize=11.5,linespacing=1.5)
        left.text(0,.06,'quote-ID: '+row['quote_id'][6:26]+'… (tam kimlik CSV/JSON’da)',fontsize=9,color='#555555')
        right.set_title('Modelin gerçek Türkçe açıklaması',loc='left',fontsize=13,fontweight='bold')
        right.text(0,.92,textwrap.fill(row['model_explanation_exact'],70),va='top',fontsize=13,linespacing=1.6)
        right.text(0,.49,textwrap.fill(row['agent_note_tr'],78),va='top',fontsize=10.5,linespacing=1.4,color='#2b5e48')
        right.text(0,.15,'Ajan: kaynakla uyumlu\nİnsan semantik incelemesi: PENDING',fontsize=11,color='#8b650e')
    fig.suptitle('Gerçek S01: PDF kanıtı ve değiştirilmemiş model cümleleri',fontsize=17,y=.99)
    fig.text(.02,.012,'Gösterimde kaynak satır sonları düzenlendi; birebir kanonik metin/aralıklar CSV ve JSON’da korunur. Otomatik yayın yok.',fontsize=10)
    plt.tight_layout(rect=(0,.045,1,.95));plt.savefig(r.FIG/'01_PDF_vs_real_claims.png',dpi=170);plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    u=review['usage'];bars=axs[0].bar(['Giriş','Çıkış'],[u['input_tokens'],u['output_tokens']],color=['#4b7892','#7f9e82'])
    axs[0].bar_label(bars,padding=4);axs[0].set(ylim=(0,1450),ylabel='Gerçek usage tokenı',title='1.453 toplam; cached=0, reasoning=0')
    vals=[float(review['input_cost_USD']),float(review['output_cost_USD'])]
    bars=axs[1].bar(['Giriş','Çıkış'],vals,color=['#4b7892','#7f9e82'])
    axs[1].bar_label(bars,labels=[f'${x:.7f}' for x in vals],padding=4)
    axs[1].set(ylim=(0,.0012),ylabel='Usage × resmî fiyat (USD)',title=f"Bu tamamlanmış çağrı: ${review['usage_token_cost_USD']}")
    axs[1].ticklabel_format(axis='y',style='plain');fig.text(.02,.01,'Vergi/fatura düzeltmeleri ve önceki kredi-hatalı denemenin bilinmeyen maliyeti dahil değildir.',fontsize=9)
    plt.tight_layout(rect=(0,.04,1,1));plt.savefig(r.FIG/'02_actual_usage_and_token_cost.png',dpi=170);plt.close(fig)

    # Nitel durum tablosu: sayısal başarı oranına çevrilmez.
    fig,ax=plt.subplots(figsize=(14,5.3));ax.axis('off')
    headers=['Gerçek kayıt','Teknik/şema','Dil (ajan)','Kaynak (ajan)','İnsan']
    cells=[['Gemma V1','Şema PASS; sözleşme FAIL','FAIL','FAIL','PENDING'],
           ['Gemma V2','Post-hoc şema PASS; token FAIL','FAIL','Çekirdek uyum; eksik','PENDING'],
           ['Qwen3 4B','NOT_RUN','NOT_RUN','NOT_RUN','PENDING'],
           ['OpenAI / ilk hesap','HTTP429; NA','NA','NA','Çıktı yok'],
           ['OpenAI / düzeltilmiş hesap','HTTP200; şema PASS','Ajan: uyumlu','Ajan: uyumlu + kapsam notu','PENDING']]
    table=ax.table(cellText=cells,colLabels=headers,loc='center',cellLoc='left',colWidths=[.23,.28,.14,.23,.12])
    table.auto_set_font_size(False);table.set_fontsize(10.5);table.scale(1,2.7)
    for (i,j),cell in table.get_celld().items():
        if i==0:cell.set_facecolor('#314b5b');cell.set_text_props(color='white',weight='bold')
        else:cell.set_facecolor('#f1f4f6' if i%2 else '#e5ebee')
        if i==5 and j in [2,3,4]:cell.set_facecolor('#f5eacb')
    ax.set_title('Aynı S01 geliştirme vakası: başarısızlıklar ve PENDING ayrı tutulur',fontsize=15,pad=22)
    fig.text(.02,.025,'Tek vaka, farklı yöntem/çalışma ortamları. Genelleme, klinik doğruluk veya eş koşullarda hız üstünlüğü sonucu değildir.',fontsize=10)
    plt.tight_layout(rect=(0,.04,1,.96));plt.savefig(r.FIG/'03_real_comparison_statuses.png',dpi=160);plt.close(fig)


def main():
    if (r.QA/'independent_review.json').exists():raise RuntimeError('Accepted/new review not overwritten')
    protected=protected_snapshot();save('protected_prior_and_real_run_files_sha256.json',protected)
    before=(r.ROOT/'run_status.md').read_bytes();(r.QA/'run_status_before.md').write_bytes(before)
    review=r.inspect();assert all(review['checks'].values());rows=r.item_reviews(review)
    save('independent_review.json',review);save('agent_item_source_review.json',rows)
    (r.QA/'exact_model_message.txt').write_bytes(review['exact_model_message'].encode('utf-8'))
    save('raw_response_reference.json',{'path':str(r.RUN/'inference_response_raw.json'),
        'raw_response_sha256':public_sha(r.RUN/'inference_response_raw.json'),
        'raw_model_message_utf8_sha256':__import__('hashlib').sha256(review['exact_model_message'].encode()).hexdigest(),
        'HTTP_raw_file_unchanged':True})
    save('human_review_pending.json',{'status':'PENDING','reviewer':None,'reviewed_at':None,'decision':None,
        'source_claim_rows':rows,'agent_assessment_is_not_human_approval':True,'automatic_release':False})
    save('review_checks.json',review['checks'])
    import pandas as pd
    pd.DataFrame(rows).to_csv(r.QA/'source_claim_comparison.csv',index=False,encoding='utf-8-sig')
    roundtrip=pd.read_csv(r.QA/'source_claim_comparison.csv')
    assert list(roundtrip.model_explanation_exact)==[x['model_explanation_exact'] for x in rows]
    assert list(roundtrip.source_quote_exact)==[x['source_quote_exact'] for x in rows]
    pd.DataFrame(review['stages']).to_csv(r.QA/'HTTP_stages.csv',index=False,encoding='utf-8-sig')
    comparison=r.read(r.ROOT/'reports/qa/WP12/gemma_v2_review_qwen_preparation_v1/real_comparison_v1_v2_Qwen_NOT_RUN.json')['rows']
    slim=[]
    for x in comparison:
        slim.append({k:x.get(k) for k in ['model_method','experiment_status','pipeline_terminal_status','independent_content_schema_status',
            'actual_language_agent','source_faithfulness_agent','human_review','actual_server_prompt_tokens','output_tokens',
            'server_total_seconds','model_message_exact','raw_response_ref','raw_response_sha256']})
    slim.append({'model_method':'OpenAI / first account','experiment_status':'API_BILLING_BLOCKED_NO_MODEL_OUTPUT',
        'pipeline_terminal_status':'HTTP429 credit_balance_exhausted','independent_content_schema_status':'NOT_EVALUABLE',
        'actual_language_agent':'NOT_EVALUABLE','source_faithfulness_agent':'NOT_EVALUABLE','human_review':'PENDING_NO_OUTPUT',
        'actual_server_prompt_tokens':None,'preflight_count_only':1236,'output_tokens':None,'usage_token_cost_USD':None})
    slim.append({'model_method':review['model']+' / corrected account','experiment_status':'COMPLETED_PENDING_HUMAN',
        'pipeline_terminal_status':'HTTP200 completed','independent_content_schema_status':'PASS',
        'actual_language_agent':review['Turkish_quality_agent'],'source_faithfulness_agent':review['source_faithfulness_agent'],
        'human_review':'PENDING','actual_server_prompt_tokens':1236,'output_tokens':217,
        'HTTP_latency_seconds':review['latency_HTTP_seconds'],'server_total_seconds':None,
        'latency_definition':'HTTP client wall duration; local Gemma server-duration is a different measure',
        'usage_token_cost_USD':review['usage_token_cost_USD'],'model_message_exact':review['exact_model_message'],
        'raw_response_ref':str(r.RUN/'inference_response_raw.json'),'raw_response_sha256':public_sha(r.RUN/'inference_response_raw.json')})
    save('all_real_runs_comparison.json',{'rows':slim,'independent_generalization_claim':False,
        'NA_NOT_RUN_and_failure_kept_separate':True,'missing_cost_not_zero':True})
    pd.DataFrame(slim).to_csv(r.QA/'all_real_runs_comparison.csv',index=False,encoding='utf-8-sig')
    figures(review,rows,slim)

    from wp09_close_wp10_notebooks import execute,INIT
    execute('WP12_OpenAI_S01_real_response_review.ipynb',[
        ('md','''# WP12 — İlk gerçek kaynaklı OpenAI yanıtı

Bu notebook kaydedilmiş HTTP200 yanıtını inceler; yeni API isteği/model çalıştırmaz. **Teknik PASS ≠ insan semantik onayı.** Aynı S01 daha önce Gemma yöntem geliştirmesinde kullanılmıştır. Yerel başarısızlıklar, Qwen NOT_RUN ve ilk API hesabının kredi hatası korunur.'''),
        ('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/openai_S01_success_review_v1'
F=ROOT/'reports/figures/WP12/openai_S01_success_review_v1'
r=json.loads((Q/'independent_review.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'model':r['model'],'HTTP':r['HTTP_status'],'completion':r['completion_status'],
    'request_id':r['API_request_id'],'HTTP_süre_s':r['latency_HTTP_seconds'],'insan':'PENDING'}]))
display(pd.read_csv(Q/'HTTP_stages.csv'))
print('Modelin özgün JSON mesajı (değiştirilmeden):\n'+(Q/'exact_model_message.txt').read_text(encoding='utf-8'))
'''),('md','''**Yorum:** gpt-5.4-mini-2026-03-17 gerçekten completed yanıtı vermiştir. Üç HTTP çağrısının yalnız biri üretimdir; otomatik retry yoktur. 3,953s HTTP süresi ağ/servis toplamıdır; yerel Gemma server-duration ölçüsüyle eş koşullu hız kıyası yapılamaz.

## 1. Gerçek PDF ve iddia karşılaştırması'''),('code',r'''
table=pd.read_csv(Q/'source_claim_comparison.csv')
with pd.option_context('display.max_colwidth',None):
    display(table[['physical_page','statement_kind','quote_id','source_quote_exact','model_explanation_exact','agent_note_tr','human_decision']])
from IPython.display import Image
display(Image(filename=str(F/'01_PDF_vs_real_claims.png')))
'''),('md','''**Ajan incelemesi:** Tam ürün adı ve etkin madde birinci alıntıdan; kırmızı/yuvarlak/bikonveks/enterik kaplı tablet ifadesi altıncı sayfadaki ikinci alıntıdan desteklenir. Gerçek Türkçe kullanılmış, ürün adı korunmuştur. Yanlış ret veya ek risk/etiket/eşdeğerlik iddiası gözlenmedi. Makrolid sınıfı ve ambalaj adetleri aktarılmamıştır: kısa özetin kapsam notlarıdır; bütün alıntının eksiksiz çevirisi olduğu iddia edilmez. Bu okuma **Codex ajan değerlendirmesidir**, bağımsız insan/klinik doğrulama değildir.

## 2. Bağımsız kullanım ve fiyat hesabı'''),('code',r'''
u=r['usage']
display(pd.DataFrame([{'input':u['input_tokens'],'cached_input':u['input_tokens_details']['cached_tokens'],
 'output_total':u['output_tokens'],'reasoning_included':u['output_tokens_details']['reasoning_tokens'],
 'total':u['total_tokens'],'input_USD':r['input_cost_USD'],'output_USD':r['output_cost_USD'],'token_cost_USD':r['usage_token_cost_USD']}]))
display(Image(filename=str(F/'02_actual_usage_and_token_cost.png')))
display(pd.DataFrame([r['aggregate_reservations']]))
'''),('md','''**Yorum:**1236×$0,75/1M +217×$4,50/1M =$0,0019035. Cached ve muhakeme alanları gerçekten0; muhakeme output'a ikinci kez eklenmez.217 token, kaynak-ID'leri dahil tüm çıktı JSON'unu kapsar. Bu tutar vergi/fatura düzeltmeleri hariç kullanım-token hesabıdır. Önceki kredi-hatalı isteğin gerçek maliyeti UNKNOWN olduğundan tüm pilotun kesin ücretini bu tutara eşitlemiyoruz. İki hesabın toplam6HTTP/2inference rezervi$0,046 olarak kalır. RAM/VRAM telemetrisi API koşusunda toplanmamıştır; sıfır gibi yazılmaz.

## 3. Bütün gerçek koşular; başarısız ve çalıştırılmayanlar'''),('code',r'''
c=pd.read_csv(Q/'all_real_runs_comparison.csv')
display(c[['model_method','experiment_status','pipeline_terminal_status','independent_content_schema_status','actual_language_agent','source_faithfulness_agent','human_review']])
display(Image(filename=str(F/'03_real_comparison_statuses.png')))
'''),('md','''**Yorum:** Bu tablo nitel, tek-vaka geliştirme karşılaştırmasıdır; başarı yüzdesi veya bağımsız benchmark değildir. Gemma V2'nin orijinal token hatası post-hoc şema PASS ile silinmez. İlk OpenAI kredi hatası modelin açıklama kalitesi olarak FAIL sayılmaz. Qwen çalıştırılmadığı için NOT_RUN kalır. Yeni iki Türkçe item ajan okumasında uyumlu; insan onayı PENDING.

## 4. Kaynak ve teknik kontrol kanıtları'''),('code',r'''
display(pd.DataFrame([{'kontrol':k,'sonuç':v} for k,v in r['checks'].items()]))
display(pd.DataFrame(r['source_page_checks']))
display(pd.DataFrame([json.loads((Q/'test_summary.json').read_text(encoding='utf-8'))]))
print('İnsan kararı: PENDING; tekrar kararlılığı: tek tamamlanmış yanıtla değerlendirilemez.')
'''),('md','''**Durma noktası:** Fiziksel1/6 tam sayfa metinleri yeniden salt okunur doğrulanıp görsel incelendi; kaynak PDF ve eski artefaktlar değiştirilmedi. İnsan formu ayrı QA kaydıdır; kaynak/model dosyası üzerinde karar değişikliği yapılmaz. Doxycycline sınıf/BUN istisnası, bilinmeyen sıklık ve kaynak dışı görev senaryoları bu S01 sonucuyla doğrulanmış sayılmaz. Kalan pilot için kullanıcı sonuç değerlendirmesi gerekir; 10 toplamHTTP tavanında yalnız4 HTTP kapasitesi kalmıştır. Bu tur başka senaryo,19×3, eğitim, yayın veya WP13 yoktur.

[Resmî model/fiyat](https://developers.openai.com/api/docs/models/gpt-5.4-mini); kanonik kaynak: kullanıcı tarafından sağlanmış pil.502.pdf, fiziksel1 ve6.''')])

    text_items='\n\n'.join('> '+x['model_explanation_exact'] for x in rows)
    report=f'''# WP12 — Gerçek S01 OpenAI yanıtının bağımsız incelemesi

08.11.2026. Run: `20261108_164416_6fd67845f94e4074818e71b22470cf22`.

**Sonuç:** Teknik olarak completed; iki Türkçe açıklama Codex ajanının kaynak okumasında destekleniyor. **İnsan semantik onayı PENDING, otomatik yayın kapalıdır.** Eski model, prompt, kaynak, kabul kriteri veya şema değiştirilmedi; yeni inference yapılmadı.

## Gerçek model yanıtı

Aşağıdaki iki cümle çıktının `explanation_tr` değerleriyle aynıdır; yazım/ürün adı/Unicode apostrofu düzeltilmedi:

{text_items}

Tam model JSON mesajı:

```json
{review['exact_model_message']}
```

Tam HTTP cevabı özgün run klasöründeki `inference_response_raw.json` içinde kalır. Yeni `exact_model_message.txt` yalnız bu gövdeden birebir alınan çıktı mesajıdır; raw referans/hash dosyası kaynak dosyasını gösterir. CSV/JSON kopyalarıyla metin round-trip eşliği ayrıca kontrol edildi.

## Teknik, uygulama ve semantik sonuçların ayrılması

| Boyut | Sonuç |
|---|---|
| Model | `{review['model']}` |
| HTTP / completion |200 / completed; error=null; incomplete_details=null|
| Request-ID |`{review['API_request_id']}`|
| Response-ID |`{review['response_id']}`|
| JSON Schema |API adapter v1 ve özgün S01 V2 denetiminde PASS|
| Uygulama/source-ID |PASS; iki ayrı identity/formulation item, doğru birincil quote-ID|
| Türkçe |Ajan: gerçek Türkçe; ürün adı kaynak yazımıyla korunmuş|
| Kaynak sadakati |Ajan: dönen iki item kaynakça destekleniyor; kapsam notları aşağıda|
| Ret / yeni olgu |Ret yok; dönen iki item'da desteklenmeyen yeni iddia gözlenmedi|
| İnsan kararı |PENDING; ajan değerlendirmesi insan/klinik doğrulama yerine geçmez|
| Tekrar kararlılığı |Değerlendirilemez: yalnız bir completed API yanıtı var|
| RAM/VRAM |Bu API koşusunda toplanmadı; NOT_COLLECTED|

## PDF kaynak sadakati

Kullanıcı PDF'si `data/user_pdfs/pil.502.pdf`, SHA-256 `{review['PDF_sha256']}`, {review['PDF_page_count']} fiziksel sayfa. Kaydedilmiş çıkarıcıyla aynı PyMuPDF sürümü `{review['extractor_version']}` ve aynı sort/flags tanımıyla yalnız ilgili1/6sayfalar salt okunur kontrol edildi. Tam sayfa metni, aralık ve alıntı hash'leri eşleşiyor. Tam iki sayfanın PNG'leri görsel olarak incelendi; PDF değiştirilmedi. Hash ve kullanıcı provenansı yayıncı doğruluğu/güncel klinik etiket garantisi değildir.

| Item | Birincil kaynak | Ajan okuması ve sınır |
|---|---|---|
| Ürün adı / etkin madde |Fiziksel1; [1028,1281)|Erythromycin Tablets BP250mg ürün adı ve eritromisin etkin maddesi açıkça mevcut.250mg ürün adı bağlamında aktarılmış; tedavi dozu önerilmemiş. Makrolid sınıfı özetlenmemiş.|
| Formülasyon/görünüm |Fiziksel6; [987,1271)|Red coloured/round/biconvex/enteric-coated tablet özellikleri doğru aktarılmış. Ambalaj adetleri özetlenmemiş.|

Bu iki eksiltme kaynakla çelişen bir iddia değildir; dondurulmuş kısa S01 ölçütü bütün alıntının tam çevirisini zorunlu kılmıyor. Ancak çıktı bütün prospektüsün veya kaynak paragrafının eksiksiz özeti olarak sunulamaz. Seçilen iki alıntının qualifier alanı boş; sıklık, risk, istisna veya ana DrugBank DB00199 ile ürün/tuz/formülasyon eşdeğerliği eklenmemiş. Doğru bir kaynak-ID tek başına semantik destek kanıtı sayılmadı; iki cümle ayrıca okunup kaynakla karşılaştırıldı.

Tam kanonik alıntılar, quote-ID'ler, sayfa/aralıklar ve özgün model cümleleri `source_claim_comparison.csv` ve `agent_item_source_review.json` içinde yan yanadır. Görsel yalnız gösterim için kaynak satır sonlarını düzenler; kanonik metni değiştirmez.

![Gerçek PDF alıntıları ve model cümleleri](figures/WP12/openai_S01_success_review_v1/01_PDF_vs_real_claims.png)

`reported_in_PDF` trusted wrapper'da kaynaklı aday olarak kalır. `predicted_by_GNN={{status: NOT_REQUESTED_IN_WP12, artifact_ref: null}}`; model skoru, SHAP, Δz, yeni MedDRA/yan etki etiketi üretilmedi. Bu işlem SIDER/model girdisi veya eğitim etiketi oluşturmaz.

## Gerçek usage, süre ve maliyet

| Alan | Değer |
|---|---:|
| Önkontrol / gerçek giriş tokenı |1236 /1236|
| Cached input |0|
| Toplam output |217|
| Output içindeki reasoning |0|
| Toplam usage |1453|
| Üretim HTTP süresi |3,953 s|
| Giriş token maliyeti |${review['input_cost_USD']}|
| Çıkış token maliyeti |${review['output_cost_USD']}|
| Bu completed çağrı token maliyeti |**${review['usage_token_cost_USD']}**|

Hesap raw usage'tan bağımsız Decimal aritmetiğiyle yeniden yapıldı:1236×$0,75/1M +0×$0,075/1M +217×$4,50/1M =$0,0019035. Cached ve reasoning0 gerçekten response alanlarında; bilinmeyenleri0'a doldurma yoktur. Muhakeme output toplamına ikinci kez eklenmedi.217 çıktı tokenı yalnız Türkçe cümleleri değil tüm JSON/source-ID metnini kapsar. İstenen ve dönen service_tier default, tools boş. [Resmî fiyat/model kaynağı](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

Bu rakam vergi/diğer fatura düzeltmeleri hariç token fiyat hesabıdır; fatura/bakiye API'si sorgulanmadı. İlk kredi-hatalı isteğin usage'ı yok, maliyeti UNKNOWN kalır; tüm pilotun gerçek ücretini$0,0019035 diye sunamayız. Eski/yeni toplam6HTTP ve2inference rezervi$0,046; eski$0,023 rezerv silinmedi.10toplamHTTP/10inference, $0,24 operasyonel tavan ve<$0,25 hedef korunuyor. Rezerv ücret değildir.

![Gerçek token ve token maliyeti](figures/WP12/openai_S01_success_review_v1/02_actual_usage_and_token_cost.png)

HTTP3,953s ağ/servis toplamıdır. Gemma'nın server_total_duration ölçümü farklıdır; bu iki değer üzerinden donanım/model hız üstünlüğü iddia edilmez. Tek yanıtla gecikme dağılımı veya kararlılık ölçülmedi.

## Bütün gerçek deneylerin karşılaştırılması

GemmaV1:orijinal FAIL; şema teknik PASS olsa da yanlış ret/İngilizce/ID-amaç hatası. GemmaV2:orijinal TOKEN_COUNT_ALIGNMENT_FAILED; ayrı post-hoc şema/ID PASS, iki İngilizce cümle ve yönerge eksiklikleri aynı. Qwen3 4B:NOT_RUN. İlk OpenAI hesabı:HTTP429 kredi engeli, model kalitesi değerlendirilemez. Yeni OpenAI hesabı:HTTP200, şema/uygulama PASS, iki Türkçe cümle ajan okumasında destekli, insanPENDING.

![Tek-vaka nitel karşılaştırma](figures/WP12/openai_S01_success_review_v1/03_real_comparison_statuses.png)

Bu karşılaştırma aynı S01'in önceki yöntem geliştirmesinden sonra yapılmıştır. Aynı senaryoda bir başarı, bağımsız genelleme, klinik doğruluk veya üstünlük kanıtı değildir. JSON+CSV bütün başarısız/NOT_RUN satırlarını ve özgün mesajları korur; eksik ücret veya çıktı0'a çevrilmez. Doxycycline sınıf/BUN istisnası, Erythromycin bilinmeyen sıklık ve yasak kaynak-dışı görevler bu çıktıyla test edilmiş sayılmaz.

## QA ve durma kararı

20 run dosyasının kayıtlı hash'i/21dosyalık envanter doğrulandı; önceki hesapla request bayt hash'i de aynı. İki sayfada yeni okuma/slice/hash kontrolleri; kaynak-ID/scope/purpose; raw→JSON; train/model/PDF katmanı ayrımı; usage/Decimal/caps; tek üretim/3HTTP; iki-scope bütçesi ve insan kapısı olmak üzere12 yeni test PASS. Eski çalışma kayıtları, başarısızlıklar, manifestler ve kaynak PDF korunur. Ayrı kanıt manifesti ve status tarihçesi yazılır; anahtar/.env okunmadı veya hash'lenmedi. Herhangi bir inference, eğitim veya yöntem araması yapılmadı.

**Öneri:** İlk S01 için ajan teknik/kaynak incelemesi olumlu; iki gerçek cümleyi kullanıcının semantik olarak değerlendirmesine sun. İnsan onayı olmadan yayın veya diğer senaryolara geçiş yoktur. Mevcut10toplamHTTP kuralında yalnız4HTTP kapasitesi kaldığından önceki dört-vaka planının tamamı artık aynı şekilde çalıştırılamaz. Sonraki değerlendirmede S07 sınıf/BUN ve S04 bilinmeyen sıklık kritik farklı kanıtlardır; yeni yürütme/ek istek politikası ancak kullanıcı onayıyla hazırlanır. Bu tur19×3 veya WP13'e geçilmedi.
'''
    with (r.ROOT/'reports/WP12_OPENAI_S01_RESULTS.md').open('x',encoding='utf-8') as f:f.write(report)
    tests=r.read(r.QA/'test_summary.json');assert tests['returncode']==0
    prefix=f'''# WP12 — Gerçek S01 completed; ajan kaynak okuması uyumlu, insanPENDING ·08.11.2026

- Düzeltilmişhesaprun164416_6fd67845f94e4074818e71b22470cf22: gpt-5.4-mini-2026-03-17, HTTP200/completed,1üretim/3HTTP. request-ID {review['API_request_id']}. Yeni inference0.
- Aynı S01/prompt/şema/DB00199/537karakter; önceki hesap request bayt hash'i eşit. Fiziksel1/6PDF tam sayfa metni/aralık/hash ve görsel kontrol uyumlu. İki gerçekTürkçeitem kaynakça destekli (ajan); makrolid/ambalajdetayıeksik kapsamnotu. Otomatiksemantikbaşarı veya yayın yok; insanPENDING.
-1236input/cached0/217output/reasoning0/1453total. HTTPsüre3.953s. Rawusage×resmîfiyat .0019035USD tokenmaliyeti; vergi/fatura/bakiyeUNKNOWN. Önceki429gerçekmaliyetUNKNOWN; toplamrezerv6HTTP/2inference .046USD korunur. Kalan4HTTP kapasitesi başka senaryoya otomatikyetki değildir.
-12 yeni ağsız gerçek-kayıt testi PASS.20runhash'i/21dosya; iki-scopekontrolleri/eskiQA/manifest/kaynaklar korundu. GemmaV1/V2 FAIL,QwenNOT_RUN,ilkOpenAIkredi-hatasıaynı. RAM/VRAMNOT_COLLECTED,tekrarkararlılığıtekçıktıylaNOT_EVALUABLE. Anahtar/.env okunmadı/hash'lenmedi.
- Rapor reports/WP12_OPENAI_S01_RESULTS.md; notebook notebooks/WP12_OpenAI_S01_real_response_review.ipynb; QA reports/qa/WP12/openai_S01_success_review_v1/. Kullanıcı gerçek iki cümleyi değerlendirene kadar dur. Diğerpilot/19×3/yayın/eğitim/WP13 yok.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    assert (r.ROOT/'run_status.md').read_bytes()==before
    (r.ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
    assert all(public_sha(r.ROOT/p)==d for p,d in protected.items())
    save('final_preservation.json',{'prior_public_files_verified_unchanged':len(protected),'all_match':True,
        'status_prior_bytes_retained':(r.ROOT/'run_status.md').read_bytes().endswith(before),
        'new_API_requests':0,'api_key_or_dotenv_read_during_review':False,'tests_passed':12,
        'human_decision':'PENDING','automatic_release':False,'PDF_source_pages_visually_inspected':[1,6]})
    files=[r.ROOT/p for p in ['scripts/wp12_openai_S01_success_review.py','scripts/wp12_openai_S01_success_outputs.py',
        'tests/test_wp12_openai_S01_success_review.py','reports/WP12_OPENAI_S01_RESULTS.md',
        'notebooks/WP12_OpenAI_S01_real_response_review.ipynb','run_status.md']]
    files.extend(p for folder in [r.QA,r.FIG] for p in folder.iterdir() if not is_private_path(p) and p.is_file())
    save('evidence_manifest.json',{p.relative_to(r.ROOT).as_posix():public_sha(p) for p in files})
    print(json.dumps({'status':review['status'],'tests_passed':12,'protected_public_files':len(protected),'new_API_requests':0}))


if __name__=='__main__':main()
