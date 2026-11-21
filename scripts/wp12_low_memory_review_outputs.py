"""Gerçek S01-R1 kayıtlarından rapor/çalıştırılmış notebook; yeni inference yok."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import wp12_source_case as c
import wp12_source_low_memory as low
import wp12_low_memory_run_review as a
from wp09_close_wp10_notebooks import execute


def new_text(path,value):
    with Path(path).open('x',encoding='utf-8',newline='') as f:f.write(value)


def new_csv_or_same(path,frame):
    text=frame.to_csv(index=False)
    if path.exists():
        assert path.read_bytes()==text.encode('utf-8-sig'),'working draft CSV differs'
        return
    with path.open('x',encoding='utf-8-sig',newline='') as f:f.write(text)


def main():
    import pandas as pd
    r=c.read(a.QA/'independent_audit.json');t=r['technical'];m=r['memory'];s=r['structural'];v=r['semantic']
    raw=(a.RUN/'source_response_raw.json').read_bytes().decode('utf-8')
    content=c.read(a.RUN/'source_response_raw.json')['message']['content']
    exact=v['exact_explanation_field'];translation=v['reviewer_Turkish_translation_NOT_MODEL_OUTPUT']
    quotes=c.read(a.QA/'original_PDF_source_checks.json')
    log=(a.QA/'test_actual_run_review.log').read_text(encoding='utf-8-sig')
    assert 'Ran 25 tests' in log and log.rstrip().endswith('OK')
    compare=pd.DataFrame(v['findings'])
    new_csv_or_same(a.QA/'source_claim_comparison.csv',compare)
    memory=pd.DataFrame(c.read(a.RUN/'memory_samples.json'))
    memory['RAM_GiB']=memory.available_bytes/2**30;memory['commit_GiB']=memory.commit_available_bytes/2**30
    new_csv_or_same(a.QA/'actual_runtime_memory.csv',memory)
    old=c.read(a.QA/'previous_files_sha256.json')
    assert all(c.sha(c.ROOT/name)==h for name,h in old.items())
    F=c.ROOT/'reports/figures/WP12/experimental_low_memory_S01_R1_review_v1'
    init=r'''from pathlib import Path
import sys,json,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display,Image
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():ROOT=ROOT.parent
Q=ROOT/'reports/qa/WP12/experimental_low_memory_S01_R1_review_v1'
RUN=ROOT/'reports/qa/WP12/experimental_low_memory_user_runs_v1/20261108_065325_050e95866a054763b9ac7d5551e1f8f5'
F=ROOT/'reports/figures/WP12/experimental_low_memory_S01_R1_review_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
r=read(Q/'independent_audit.json')
pd.set_option('display.max_colwidth',600);pd.set_option('display.max_rows',50)
'''
    execute('WP12_experimental_low_memory_S01_R1_review.ipynb',[
        ('md','''# WP12 — Gerçek S01-R1 denemesinin bağımsız incelemesi

**Sonuç: teknik üretim tamamlandı; kaynaklı Türkçe açıklama kabul edilemedi.** HTTP200/stop ve geçerli JSON Schema, kaynak sadakati veya uygulama sözleşmesi başarısı değildir. Aşağıdaki çıktılar gerçek kullanıcı run'ından gelir. Bu notebook yalnız okur; ağ/LLM/optimizer/tekrar yoktur. İnsan onayı hâlâ bekliyor; otomatik yayın/19×3/WP13 yok.'''),
        ('code',init+'''
display(pd.DataFrame([r['technical']]).T.rename(columns={0:'doğrulanmış_kayıt'}))
display(pd.DataFrame([r['source']]).T.rename(columns={0:'kaynak_bütünlüğü'}))
'''),
        ('md','''**Yorum:** Onaylı API9755… ve yerel wrapper313f… farklı kimlik nesneleridir; ayrı hash ve doğru manifest bağlantısıyla doğrulandı.17 ham dosya/16 manifest girdisi korundu.919 prompt,0 cached prompt ve188 output token; truncation/length stop/timeout kaydı yok.8,708s sunucu total;14,233s istemci bloğu Python incelemesini de içerir. Bunlar aynı süre tanımı değildir.

## Gerçek yanıt — aynen'''),
        ('code',r'''
response=read(RUN/'source_response_raw.json')
print(response['message']['content'])
print('\nexplanation_tr alanı AYNEN:')
candidate=json.loads(response['message']['content']);print(candidate['items'][0]['explanation_tr'])
print('\nİNCELEYENİN TÜRKÇE ÇEVİRİSİ; MODEL ÇIKTISI DEĞİLDİR:')
print(r['semantic']['reviewer_Turkish_translation_NOT_MODEL_OUTPUT'])
'''),
        ('md','''**Yorum:** Model Türkçe açıklama üretmedi; `explanation_tr` İngilizcedir. Rapordaki Türkçe çeviri inceleyenin çevirisidir ve yeni LLM çıktısı gibi sunulmaz. “Formülasyon bilgisi yok” iddiası kaynakla çelişir. IMAGE_TEXT_UNAVAILABLE gerekçesi bu iki metin alıntısı için desteklenmez.

## JSON Schema, uygulama sözleşmesi ve kaynak anlamı'''),
        ('code',r'''
display(pd.DataFrame([{'kontrol':'JSON sözdizimi','sonuç':r['structural']['JSON_syntax_valid']},
 {'kontrol':'V1 JSON Schema','sonuç':r['structural']['v1_JSON_Schema_valid']},
 {'kontrol':'Vaka JSON Schema','sonuç':r['structural']['case_JSON_Schema_valid']},
 {'kontrol':'Uygulama sözleşmesi','sonuç':r['structural']['application_contract_valid']},
 {'kontrol':'Kaynak sadakati (Codex incelemesi)','sonuç':r['semantic']['agent_assessment']},
 {'kontrol':'İnsan onayı','sonuç':r['semantic']['human_semantic_review']}]))
display(pd.DataFrame(r['structural']['item_checks']))
display(pd.read_csv(Q/'source_claim_comparison.csv'))
'''),
        ('md','''**Yorum:** Mevcut şema `refused` ise boş items koşulunu JSON Schema içinde şartlı tanımlamıyor; dolayısıyla Schema geçiyor. Değişmeyen uygulama doğrulayıcısı `invalid refusal` ile durduruyor. Bağımsız item kontrolü ayrıca formulation amacının identity alıntısına bağlandığını gösterdi; source_scope doğru, ID gerçek olsa bile bu amaç uyumu doğru değildir. Eski şema/validator/yanıt düzeltilmedi.

## Özgün fiziksel sayfalar ve birebir alıntılar'''),
        ('code',r'''
sources=read(Q/'original_PDF_source_checks.json')
display(pd.DataFrame(sources)[['page','char_start','char_end','quote_id','quote','source_span_matches_original_PDF']])
display(Image(filename=str(F/'original_physical_page_1.png'),width=650))
display(Image(filename=str(F/'original_physical_page_6.png'),width=650))
'''),
        ('md','''**Yorum:** İki tam fiziksel sayfa Poppler ile render edilip görsel olarak kontrol edildi. Mevcut PyMuPDF text yolu ile sayfa metinleri kabul edilmiş extraction'a, `[start,end)` aralıkları alıntılara ve SHA'ları ham PDF'ye eşit bulundu. Sayfa1 ürün/etkin maddeyi; sayfa6 kırmızı, yuvarlak, bikonveks, enterik kaplı tablet ve ambalajı açıkça veriyor. Tam sayfa render'ındaki diğer içerikler modele verilmiş gibi değerlendirilmez: prompt yalnız dondurulmuş iki alıntıyı içeriyordu. Model bunları aktarmadı; doğrudan çelişen bilgi-yok iddiası verdi. Seçilen alıntılarda unknown-frequency/might gibi qualifier yok; S04 belirsizlik vakası bu run ile sınanmış sayılmaz.

## Gerçek bellek örnekleri ve sınırlar'''),
        ('code',r'''
display(pd.DataFrame([r['memory']]).T.rename(columns={0:'gerçek_ölçüm'}))
memory=pd.read_csv(Q/'actual_runtime_memory.csv')
times=pd.to_datetime(memory['at'],utc=True);seconds=(times-times.iloc[0]).dt.total_seconds()
fig,axes=plt.subplots(1,2,figsize=(12,4))
axes[0].scatter(seconds,memory.RAM_GiB,s=18,color='#467d98',label='Ölçülen boş RAM')
axes[0].axhline(.75,color='#b35c5c',ls='--',label='Deneysel çalışma sınırı0,75')
axes[0].axhline(1,color='gray',ls=':',label='Eski v2 çalışma sınırı1,0')
axes[0].set(xlabel='İlk bellek örneğinden geçen saniye',ylabel='GiB',title='37 gerçek örnek; ara minimum garanti değil');axes[0].legend(fontsize=8)
axes[1].scatter(seconds,memory.commit_GiB,s=18,color='#558572',label='Ölçülen boş commit')
axes[1].axhline(1,color='#b35c5c',ls='--',label='Deneysel kritik sınır1GiB')
axes[1].set(xlabel='İlk bellek örneğinden geçen saniye',ylabel='GiB',title='Commit: fiziksel RAM rezervi değildir');axes[1].legend(fontsize=8)
plt.tight_layout();plt.savefig(F/'actual_runtime_memory.png',dpi=160);plt.show()
'''),
        ('md','''**Yorum:** Giriş1,752GiB; istekten hemen önce1,714GiB.37 örnekte minimum0,997GiB, commit minimum9,461GiB ve OS düşük bellek0. Deneysel0,75 sınırı aşılmadı; eski1GiB uyarısı farklı politika olarak korunur ve burada geriye dönük yeniden uygulanmaz. GPU başlangıç/son3935MiB; inference sırasındaki peakUNKNOWN. Sistem baskısının örnekler arasında olmadığı veya process tepe RAM'inin ne olduğu söylenemez. Böylece tek çalışmanın teknik uygulanabilirliği gözlendi; genel güvenlik/uygulanabilirlik kanıtlanmadı. Yanlış yanıtın nedenini RAM/model boyutu/dil yeteneğine bağlamak için veri yok; UNKNOWN.

## Karar ve durma noktası'''),
        ('code',r'''
print((Q/'test_actual_run_review.log').read_text(encoding='utf-8-sig').split('----------------------------------------------------------------------')[-1])
display(pd.DataFrame([{'teknik_üretim':'TAMAMLANDI','uygulama_sözleşmesi':'BAŞARISIZ',
 'Codex_kaynak_incelemesi':'BAŞARISIZ','insan_onayı':'BEKLİYOR','yayımlanabilir':False,
 'yeni_inference':0,'otomatik_tekrar':False,'19×3':'BAŞLATILMADI','WP13':'BAŞLATILMADI'}]))
'''),
        ('md','''**Sonraki aşama önerisi:** Bu yanıt ilk-vaka başarı kapısını geçmedi;19×3 açılmamalı. Önce kullanıcı insan incelemesi. Gerekirse daha sonraki açık kararla ayrı sürümlü şema/prompt uyumu önerisi hazırlanabilir; bu tur hiçbir yöntem/ayar/seed/timeout/eşik/ham çıktı değiştirilmedi ve yeni inference yapılmadı. Mevcut tek başarısız yanıt saklı kalır; otomatik tamir veya en iyi tekrar seçimi yoktur. B0/B1/B2, GNN, SHAP ve PPI sonuçları aynı kalır.''')])
    findings='\n'.join(f"|{x['topic']}|{x['assessment_tr']}|{x['status']}|" for x in v['findings'])
    quote_sections='\n\n'.join(f'''### Özgün alıntı — fiziksel sayfa{q['page']}

Quote-ID `{q['quote_id']}`; Unicode yarı açık aralık `[{q['char_start']},{q['char_end']})`; alıntı SHA `{q['quote_sha256']}`.

```text
{q['quote']}```''' for q in quotes)
    report=f'''# WP12 — EXPERIMENTAL_LOW_MEMORY_v1 / gerçek S01-R1 incelemesi

08.11.2026 · **Model yanıt üretti; kaynaklı Türkçe açıklama kabul ölçütlerini karşılamadı. İnsan onayı bekliyor; otomatik yayın yok.**

İncelenen gerçek run: `{a.RUN}`. Üst klasörde en son oluşturulan kayıt olduğu doğrulandı. İnceleme salt okunur;17 ham run dosyası/16 manifest girdisi doğrulandı ve değiştirilmedi. Bu tur yeni inference, API erişimi, tekrar, model indirme, eğitim,19×3 veya WP13 yok. AGENTS/aktif ROADMAP ve v1 kaynak/çıktı sözleşmesi korunur.

## 1. Teknik üretim ile açıklama başarısı farklı

| Kontrol | Sonuç |
|---|---|
|Gerçek yanıt|Var; boş olmayan assistant content|
|HTTP / tamamlama|200 / done=true / done_reason=stop|
|Ollama / kullanıcı ortamı|0.40.6 / PowerShell5.1.26100.9711 / AppContainer=false|
|Giriş / önbellekten giriş / çıktı|919 /0 /188 token|
|Sabit bütçeler|1536input +384output +128safety;2048context|
|Giriş+gerçek çıktı|1107 token; length stop veya truncation kaydı yok|
|Sunucu total / yükleme|{t['server_total_seconds']:.6f}s /{t['server_load_seconds']:.6f}s|
|Sunucu prompt / üretim|{t['server_prompt_eval_seconds']:.6f}s /{t['server_output_eval_seconds']:.6f}s|
|İstemci bloğu|{t['client_generation_plus_review_block_seconds']:.6f}s; Python review dahil, salt inference süresi değil|
|Timeout / HTTP exception|Kayıtta yok;60s değiştirilmedi|
|Kaydedilen generation teşebbüsü|1; hash'i eşit runner'da tek PostAsync|
|Yeni indirme|Kayıtta0; runner'da pull yolu yok. Global başka istemci trafiği bu run'dan gözlenemez|
|JSON sözdizimi / vaka ve v1 JSON Schema|Geçti / ikisi de geçti|
|Uygulama sözleşmesi|**BAŞARISIZ: invalid refusal**|
|Codex kaynak sadakati değerlendirmesi|**BAŞARISIZ**; insan onayı değildir|
|İnsan semantik incelemesi|**PENDING**, karar verilmedi; yayımlanabilir değil|

API/source model digest `{r['source']['API_digest']}`; wrapper dosya SHA `sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16` ayrı nesne olarak doğrulandı. Wrapper'ın source-manifest bağlantısı ayrı config ile4 gerçek model/template/license/params katman referansları uygun karşılaştırıldı; wrapper içindeki ek source-manifest referansı bir model katmanı sanılmadı. Kaydedilmiş tags/kimlik ile mevcut yerel manifest, tam model blob, runtime DLL, PDF ve kaynak/kod hash'leri salt okunur doğrulandı. Model yeniden yüklenmedi; tokenizer/context/forward çalıştırılmadı.

Request SHA `{c.sha(a.RUN/'source_request.json')}`; ham response SHA `{c.sha(a.RUN/'source_response_raw.json')}`. Frozen request/context ve gerçek token proof eşittir. İki alıntı tam537 karakterle prompt'tadır; kaynak yokluğu veya token kesilmesine kanıt bulunmadı.

## 2. Gerçek model content — AYNEN

Aşağıdaki metin ham HTTP yanıtının `message.content` alanıdır; yazımı, İngilizce cümlesi ve tab/boşlukları korunmuştur. Yeni ya da düzeltilmiş model yanıtı değildir. Ayrı dosya: `reports/qa/WP12/experimental_low_memory_S01_R1_review_v1/model_message_content_exact.txt`.

```json
{content}
```

**Gerçek `explanation_tr` alanı aynen:**

> {exact}

**Model Türkçe açıklama üretmemiştir.** Aşağıdaki yalnız inceleyenin Türkçe çevirisidir, model çıktısı değildir:

> {translation}

Türkçe alan adının bulunması, cümlenin Türkçe olduğu veya kaynakla doğru eşleştiği anlamına gelmez.

## 3. Yapısal geçiş ve uygulama sözleşmesi

JSON Schema yalnız geçerli anahtar/enum/tür/boyutları denetledi; mevcut şemada `status=refused` olduğunda `items=[]` şartını kuran koşullu kural yok. Bu nedenle ham aday **JSON Schema'dan geçiyor**, fakat aynı anda refused+IMAGE_TEXT_UNAVAILABLE ve bir açıklama item'ı içerdiği için değişmeyen uygulama validator'ı **invalid refusal** üretiyor. Bu ayrım yeniden üretildi; şema veya kayıt düzeltilmedi.

Ek bağımsız item kontrolü: quote-ID gerçektir ve izinli listede; scope=product_identity doğrudur. Ancak item `statement_kind=formulation` iken atıf **sayfa1 identity** alıntısına yapılmıştır. Sağlanan sayfa6 formulation alıntısı çıktı atfına alınmamıştır. Tek başına doğru quote-ID kaynak uygunluğu sağlamaz. Mevcut validator ilk invalid-refusal hatasında durduğu için ikinci kind/ID hatası bu bağımsız incelemede ayrıca görünür kılındı.

## 4. Özgün PDF ile kaynak karşılaştırması

Kaynak `data/user_pdfs/pil.502.pdf`, ham SHA `{quotes[0]['raw_sha256']}`. Fiziksel1 ve6'nın bütün sayfaları Poppler ile PNG'ye render edilip görsel olarak kontrol edildi. Mevcut PyMuPDF2.1 bağımlılığı, önceki pilotun text/sort=false/flags195 yolunda yalnız bu iki sayfayı okudu; sayfa metinleri önceki extraction'a ve alıntı aralıklarına birebir eşit. OCR, PDF indirme veya eski extraction çıktısını yeniden yazma yok. Tam sayfa kontrolü için modele yeni içerik eklenmedi.

{quote_sections}

| İncelenen konu | Bağımsız kaynak değerlendirmesi | Durum |
|---|---|---|
{findings}

Bu yanıtta yeni bir yan etki/MedDRA etiketi, skor veya klinik risk iddiası üretilmemiştir. Buna karşılık **kaynakta mevcut formülasyon bilgisinin bulunmadığı iddiası desteklenmeyen ve kaynakla çelişen bir ifadedir**; bilgi uydurmanın yalnız yeni pozitif klinik olgu eklemek şeklinde olmadığı görülüyor. IMAGE_TEXT_UNAVAILABLE, gönderilen iki okunabilir metin alıntısına uygun bir ret gerekçesi değildir. Ürün, etkin madde ve formülasyon doğru aktarılmamış; esas olarak atlanmış ve yok sayılmıştır. Kaynakta olmayan bir ürün eşdeğerliği iddiası yoktur; bu tek olumlu sınır, görevin başarısını sağlamaz.

Seçili alıntılarda unknown-frequency/might niteleyicisi yoktur. Modeldeki unavailable ifadesi bu alıntıların belirsizliğini koruma değildir; eklenmiş desteksiz ret gerekçesidir. Erythromycin bilinmeyen sıklık S04 ve Doxycycline sınıf/BUN senaryoları bu tek S01 çalışmasıyla sınanmış sayılamaz. Source/PDF sadakati Codex tarafından olumsuz değerlendirildi; insan inceleme kararı hâlâ bekler.

## 5. Gerçek bellek koşulları

| Ölçüm | Gerçek kayıt |
|---|---:|
|Başlangıç boş RAM|{m['entry_RAM_GiB']:.6f}GiB|
|Gönderim öncesi boş RAM|{m['immediate_RAM_GiB']:.6f}GiB|
|Son boş RAM|{m['after_RAM_GiB']:.6f}GiB|
|Kararlı giriş örnekleri|5 /{m['stable_span_seconds']:.6f}s; bütün RAM/commit/OS kapıları geçti|
|Çalışma örnekleri|37|
|Örneklenmiş en düşük boş RAM|**{m['sampled_RAM_min_GiB']:.6f}GiB**|
|Örneklenmiş en düşük commit alanı|{m['sampled_commit_min_GiB']:.6f}GiB|
|OS düşük bellek sinyali|37 örnekte0 true|
|GPU başlangıç / immediate / son|3935 /3935 /3935MiB boş|
|Gerçek process peak RAM / runtime peak VRAM|**UNKNOWN**; bu sayaçlar örneklenmedi|

Deneysel giriş1,5GiB RAM/1GiB VRAM/3GiB commit koşulları geçti. Çalışma0,75GiB RAM/1GiB commit/OS alarmı tetiklenmedi. Minimum0,997GiB, eski v2'nin1GiB çalışma uyarısının altındadır; eski politika değiştirilmez veya bu deney üzerinden yeniden yazılmaz. Bu run ayrı deneysel sözleşmeyle değerlendirilmiştir. Güvenlik veya başka run'larda çalışabilme garantisi yoktur; örnekler arası minimumlar ve kısa bellek baskısı UNKNOWN kalır.

GPU başlangıç ve sonunda aynı boşluk görülmesi GPU kullanılmadığını veya CPU-only çalıştığını göstermez. keep_alive=0 sonrası dönüş, inference içi peak kullanımını gizleyebilir; kaynak kayıtlarında o peak ölçümü yok. Modelin yanlış açıklamasının nedeni **UNKNOWN**: tek run'dan RAM, model boyutu, dil yeteneği veya seed kaynaklı nedensel teşhis yapılamaz. Gözlenen olgular modelin tam yanıt verdiği ve yanıtın sözleşme/kaynak açısından hatalı olduğudur.

## 6. Testler, korunma ve sonraki adım

**25 bağımsız inceleme testi geçti**:17 ham dosya ve hash'ler, ayrı model kimlikleri,919/188 token, JSON Schema/uygulama ayrımı, invalid refusal, kind-ID uyuşmazlığı, özgün PDF sayfa/aralıkları,37 RAM/commit/OS örneği, exact content, no-network ve kaynak run'ın değişmemesi dahil. Mevcut doğrulayıcı salt fonksiyonlarıyla aynı structural_review sonucu yeniden üretildi; kaynağın içine `review()` çalıştırılıp dosya yazılmadı. İki geliştirme sorunu yeni denetleyicide giderildi: wrapper'ın ek manifest bağlantısını model katmanı gibi karşılaştırma beklentisi ve global Python'da olmayan PyMuPDF yerine mevcut `.deps/pymupdf` konumunun kullanılması. Bunlar **gerçek denemenin hataları değildir**; eski betik veya yöntem değiştirilmedi.

Önceki **{len(old)}** dosya,17 gerçek run dosyası dahil salt okunur hash envanteriyle korunur. Eski model/sonuç/QA/şema/senaryo/PDF değişmedi. Yalnız `run_status.md` yeni inceleme bölümü alır; önceki tam baytları QA'da arşivlenir ve status dosyasının devamında korunur. Yeni QA manifesti bu incelemenin çıktılarını izler.

**Geçiş önerisi:19×3 başlatılmamalı.** İlk gerçek vaka teknik olarak tamamlandı ama uygulama ve kaynak başarı kapısını geçmedi. Önce kullanıcı insan incelemesi. Sonra gerekirse, açık yeni kararla ayrı sürümlü bir şema/ret koşulu ve Türkçe kaynak aktarım uyumu önerisi değerlendirilebilir. Bu rapor böyle bir değişikliği uygulamaz, mevcut yanıtı tamir etmez, yeni inference veya otomatik tekrar önerisi çalıştırmaz. Prompt/seed/bellek/timeout/digest/19 vaka değişmez; en iyi çıktı seçimi yok. WP13 başlatılmaz.

Çalıştırılmış notebook: `notebooks/WP12_experimental_low_memory_S01_R1_review.ipynb`. QA: `reports/qa/WP12/experimental_low_memory_S01_R1_review_v1/`. Gerçek PNG'ler: `reports/figures/WP12/experimental_low_memory_S01_R1_review_v1/`. `source_claim_comparison.csv` konu bazlı kaynak incelemesini; `actual_runtime_memory.csv`37 ölçümü; `independent_audit.json` teknik/semantik ayrımı; exact-content dosyası modelin değişmeyen metnini taşır. Yeni manifest yalnız bu turun kanıtıdır; eski run manifesti aynen kalır.

## Ek — Ham HTTP gövdesi AYNEN

Aşağıdaki gövde UTF-8 ham dosyasından okunmuştur; yeniden JSON formatlama yapılmamıştır. Ham dosya hash'i yukarıdadır.

```json
{raw}
```
'''
    new_text(c.ROOT/'reports/WP12_EXPERIMENTAL_LOW_MEMORY_S01_R1_REVIEW.md',report)
    before=(a.QA/'run_status_before.md').read_bytes();assert (c.ROOT/'run_status.md').read_bytes()==before
    prefix=f'''# WP12 — Gerçek S01-R1 incelemesi: üretim var, kaynaklı açıklama başarısız ·08.11.2026

- Kullanıcı run20261108_065325_050e95866a054763b9ac7d5551e1f8f5:HTTP200/done true/stop,919input/188output,tek kayıtlı inference. Model9755… ve wrapper313f… ayrı doğrulandı;17 ham dosya aynı hash'te.
- JSON sözdizimi/v1-vaka JSON Schema geçti; uygulama sözleşmesi invalid refusal ile başarısız:refused+nonempty items. Ek kind-ID denetimi formulation'ın identity alıntısına atandığını gösterdi. Model Türkçe yerine İngilizce “formülasyon bilgisi yok” dedi; özgün PDFp6 tam tersini açıkça içeriyor. Codex kaynak incelemesi başarısız; insan onayı PENDING, otomatik yayınfalse.
- Giriş RAM{m['entry_RAM_GiB']:.3f}GiB;37 çalışma örneğinde minimum{m['sampled_RAM_min_GiB']:.3f}GiB,commit minimum{m['sampled_commit_min_GiB']:.3f}GiB,OSlow0. Deneysel0,75 alarmı tetiklenmedi; peak VRAM/processRAM ve hatanın nedeni UNKNOWN. Genel güvenlik veya başarı garantisi yok.
-25 bağımsız test geçti; özgün PDFp1/p6 sayfa/aralık/hash ve görseller kontrol edildi. Önceki{len(old)} dosya korundu, eski status tam arşivlendi. Bu tur yeni API/inference/tekrar/indirme/eğitim0;19×3 ve WP13 başlatılmadı.
- Rapor reports/WP12_EXPERIMENTAL_LOW_MEMORY_S01_R1_REVIEW.md; notebook notebooks/WP12_experimental_low_memory_S01_R1_review.ipynb; QA reports/qa/WP12/experimental_low_memory_S01_R1_review_v1/. Öneri:ilk-vaka kabul kapısı geçmedi; insan incelemesinden önce toplu deneye geçme.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''.encode('utf-8')
    (c.ROOT/'run_status.md').write_bytes(prefix+before)
    changed=[name for name,h in old.items() if c.sha(c.ROOT/name)!=h];assert changed==['run_status.md'],changed
    assert c.sha(a.QA/'run_status_before.md')==old['run_status.md']
    c.save_new(a.QA/'previous_artifacts_preservation.json',{'previous_files':len(old),
        'unchanged_at_original_path':len(old)-1,'only_updated_path':'run_status.md',
        'old_status_archived_exactly':True,'old_status_as_exact_suffix':(c.ROOT/'run_status.md').read_bytes().endswith(before),
        'raw_run_files_unchanged':a.source_checks()['raw_files'],'new_inference_or_API_calls':0})
    print('Real response/source/memory review complete; first case failed, human approval pending.')


if __name__=='__main__':main()
