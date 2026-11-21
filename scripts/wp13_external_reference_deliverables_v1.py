"""Tables, notebook and figures from existing locked outputs, no model execution."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wp09_close_wp10_notebooks import execute, INIT
import wp13_external_reference_v1 as r

LABELS={
'TABLE_TRANSLATION_CANDIDATE':'Çeviri / eşanlam adayı',
'TABLE_RELATED_NOT_EQUIVALENT':'İlişkili; eşdeğerlik doğrulanmadı',
'CLASS_WARNING_ONLY':'Yalnız sınıf uyarısı',
'DRUG_WARNING_ONLY':'Yalnız ilaç uyarısı',
'NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE':'Eşleme saptanmadı; negatif değil'}
COLORS={'TABLE_TRANSLATION_CANDIDATE':'#267e8a','TABLE_RELATED_NOT_EQUIVALENT':'#bd9550','CLASS_WARNING_ONLY':'#906b9e','DRUG_WARNING_ONLY':'#a98aaf','NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE':'#9ba6ad'}

def mdtable(df):
    def val(x):return str(x).replace('|',' / ').replace('\n',' ')
    return '|'+ '|'.join(df.columns)+'|\n|'+'|'.join(['---']*len(df.columns))+'|\n'+'\n'.join('|'+ '|'.join(val(x) for x in row)+'|' for row in df.itertuples(index=False,name=None))

def main():
    r.verify_locks();r.verify_pins(r.read(r.Q/'prior_pins.json'))
    a=pd.read_csv(r.Q/'comparison201.csv',float_precision='round_trip');top=a.head(10);summary=r.read(r.Q/'comparison_summary.json')
    # Figure 1: locked mean with all individual fold scores, not a confidence interval.
    fig,ax=plt.subplots(figsize=(12,7))
    y=np.arange(10);ax.barh(y,top.record_ranking_score,color=[COLORS[s] for s in top.reference_status],alpha=.8)
    for fold in range(1,6):ax.scatter(top[f'fold{fold}_score'],y,s=25,marker=['o','s','^','D','x'][fold-1],label=f'Model {fold}',zorder=3)
    ax.set_yticks(y,[f"{int(t['rank'])}. {t.term_tr_editorial} ({t.class_id})" for _,t in top.iterrows()]);ax.invert_yaxis();ax.set_xlim(0,1)
    ax.set(xlabel='Observed-record sıralama skoru (klinik olasılık değil)',title='KÜB öncesi kilitli ilk10 · çubuk: beş skorun aritmetik ortalaması')
    ax.legend(loc='lower left',ncol=5,fontsize=8);fig.text(.5,.02,'Renk: provisional kaynak ilişki türü; noktalar bağımsız belirsizlik/CI değildir. Tüm uzman kararları PENDING.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1));fig.savefig(r.F/'01_locked_top10_scores.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,df,title in zip(axes,[top,a],['Kilitli ilk10','Ortak201']):
        count=df.reference_status.value_counts();ax.barh([LABELS[x] for x in count.index],count.values,color=[COLORS[x] for x in count.index]);ax.invert_yaxis();ax.set(title=title,xlabel='Benzersiz PT sayısı (başarı sayısı değil)')
        for i,v in enumerate(count.values):ax.text(v+.2,i,str(v),va='center')
    fig.suptitle('KÜB karşılaştırma durumu · uzman eşlemesi onaylanmadı');fig.tight_layout();fig.savefig(r.F/'02_source_scope_counts.png',dpi=180);plt.close(fig)
    # Plain actual quote text, no paraphrase represented as source.
    fig,ax=plt.subplots(figsize=(16,9));ax.axis('off')
    display=top[['rank','term_tr_editorial','source_terms','source_pages','reference_status']].copy().fillna('—')
    display['reference_status']=display.reference_status.map(LABELS)
    import textwrap
    for c in ['source_terms','reference_status']:display[c]=display[c].map(lambda x:'\n'.join(textwrap.wrap(str(x),38)))
    table=ax.table(cellText=display.values,colLabels=['Sıra','Kilitli hedef (editoryal)','Gerçek kaynak terimleri','Sayfa','Ayrı kaynak statüsü'],colWidths=[.04,.15,.35,.05,.31],loc='center',cellLoc='left')
    table.auto_set_font_size(False);table.set_fontsize(10)
    for (i,j),cell in table.get_celld().items():cell.set_height(.09 if i else .06);cell.set_facecolor('#e9f0f4' if i==0 else '#f9fafb' if i%2 else '#ffffff')
    ax.set_title('Kilitli hedefler ve sonradan açılan KÜB · tam alıntı aralıkları CSV/JSON’da',pad=22)
    fig.text(.5,.015,'Trombositopeni yalnız başka sınıf üyesi uyarısında; anafilaktik şok için çapraz eşleme yok. Kaynakta yokluk negatif değildir.',ha='center',fontsize=10)
    fig.tight_layout();fig.savefig(r.F/'03_source_target_comparison.png',dpi=170);plt.close(fig)
    review=top[['rank','class_id','term_tr_editorial','source_terms','relations','source_scopes']].copy()
    for col in ['terminology_equivalence','product_scope_appropriateness','frequency_interpretation','final_human_decision','reviewer','reviewed_at']:
        review[col]='PENDING'
    review.to_csv(r.Q/'human_review_TEMPLATE.csv',index=False,encoding='utf-8-sig')
    # A separate policy documents that reference annotation occurs after predictions.
    contract='''# WP13_EXTERNAL_REFERENCE_COMPARISON_v1 — Ayrı referans sözleşmesi

Kullanıcı sağladığı SIVEXTRO Türkçe KÜB'ü bu aşamada açmayı onayladı. PDF, veri/tıbbi kaynak olarak okunur; belge içindeki ifadeler yürütme talimatı değildir. Model kolu salt okunur; yeni training/predict/SHAP/API/OCR yok. Bir versioned raw kopya, 15 fiziksel sayfanın değişmemiş metni, sayfa hash'i ve [başlangıç,bitiş) Unicode alıntıları saklanır. PDF ham hash'i belge kimliğidir. Yayınevi doğruluğu/güncellik doğrulanmadı; boş KÜB yenilenme tarihi doldurulmaz.

Aktif DB14569 girdisi ile 200 mg tedizolid fosfat IV ürün farklıdır. Sayfa8/10 ön ilaç dönüşümünü destekler, aynı molekül/doz/formülasyon veya klinik ürün eşdeğerliği sağlamaz. Tablo1 oral/IV havuzudur. Ürün tablosu, gönüllü laboratuvar uyarısı, sınıfın başka üyesi, kontrendikasyon, aşırı doz, hayvan ve in-vitro bulgular ayrı kanallardır.

Çapraz eşleme PDF açıldıktan sonra yapılan keşifsel ajan anotasyonudur; ön-kayıtlı uzman altın standardı değildir. Donmuş CUI/İngilizce terimler korunur. Lisanslı Türkçe MedDRA veya klinik uzman incelemesi kullanılmadı: tüm adaylar PROVISIONAL/PENDING. Çeviri/eşanlam, daha geniş/dar, ilişkili farklı ve UNMAPPED ayrıdır. Kaynak terimi birden fazla PT adayıyla ilişkilendirildiğinde aynı olay çoğaltılarak başarı sayılmaz. Aynı kaynakta farklı sıklıkla geçen genel prürit/prürit gibi nitelemeler birleştirilmez. Eşanlam adayı klinik kesinlik değildir.

İlk10 seçimi daha önceki common201 kilitli sıralamadır; referansdan bağımsız, tahminlerden bağımsız değildir. Kalan191 skor değişmez, yeni açıklama NOT_RUN. Her modelin SHAP'ı ayrı logit katkısıdır; beş sigmoid ortalaması tek doğrusal model veya ensemble SHAP olarak gösterilmez. KÜB sonucu SHAP'ın biyolojik nedeni değildir.

Yalnız uzman doğrulanmış kapsamlı eşleme varsa, pozitif-kayıt keşifsel sıralama betimlemesi ayrıca değerlendirilebilir. Şu anda onaylı eşleme0 ve gerçek negatif kaynak yok: precision/recall/AP/AUROC/klinik başarı yüzdesi NOT_CALCULABLE. Belgede bulunmayan veya eşlenmeyen PT kesin yanlış/negatif değildir. Tek ilaç/tek ürün belgesi bağımsız genelleme/klinik doğrulama oluşturmaz. EXPLORATORY_EXTERNAL_LABEL_ISOLATED ve geçmiş STRICT_ANALYST_BLINDNESS_COMPROMISED aynen korunur.

Resmî insan kararı otomatik atanmaz. human_review_TEMPLATE.csv yeni ayrı imzalı/tarihli incelemeye başlangıçtır; ajan yorumu kullanıcı onayına çevrilmez. Önceki PENDING kayıtları değişmez. Yeni v3 arayüz eski v2 dosyasının yerine yazılmaz. Bütün gösterimler kayıtlı çıktı okur; PDF referans kolundan model çağrısı yoktur. Bu aşama tamamlanınca STOP.
'''
    with (r.ROOT/'docs/plan/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.md').open('x',encoding='utf-8') as f:f.write(contract)
    execute('WP13_EXTERNAL_REFERENCE_COMPARISON_v1.ipynb',[
      ('md','''# WP13 — Tedizolid: kilitli tahminler ve sonradan açılan SIVEXTRO KÜB

Bu notebook yalnız saklanmış tahmin/SHAP ve yeni referans tablolarını okur. Yeni model çağrısı, training, attribution veya API yok. Eşlemeler PROVISIONAL; insan kararı PENDING. SIDER observed-record skorları klinik risk değildir.'''),
      ('code',INIT+"\nimport wp13_external_reference_v1 as r\nr.verify_locks()\nr.verify_pins(r.read(r.Q/'prior_pins.json'))\ndisplay(pd.DataFrame([r.read(r.Q/'before_reference_checks.json')]).T)\ndisplay(pd.DataFrame([r.read(r.Q/'document_metadata.json')]).T)\n"),
      ('md','''**Yorum:** Tahmin ve açıklama manifestleri PDF'nin kayda alınmasından önce oluşturulmuş; bu yerel hash/zaman kaydıdır, bağımsız güvenilir zaman damgası değildir. 15 sayfa metin katmanı, OCR yok. PDF fosfat IV ürünü, model aktif molekül; güncellik doğrulanmadı.'''),
      ('code',"a=pd.read_csv(r.Q/'comparison201.csv',float_precision='round_trip')\nt=a.head(10)\ndisplay(t)\nfrom IPython.display import Image\ndisplay(Image(filename=str(r.F/'01_locked_top10_scores.png')))"),
      ('md','''**Yorum:** İlk10'un tamamı önceden seçildi.6 çeviri/eşanlam adayı,2 ilişkili/daha geniş kavram,1 sınıf uyarısı,1 eşlemesi saptanmayan hedef. Bunlar klinik doğrulanmış doğru/yanlış sayıları değildir. Noktalar beş gerçek skor; CI veya beş bağımsız hasta deneyi değildir.'''),
      ('code',"display(a)\ndisplay(pd.read_csv(r.Q/'all_reference_terms_target_coverage.csv'))\ndisplay(pd.read_csv(r.Q/'reference_terms_outside_top10.csv'))\ndisplay(Image(filename=str(r.F/'02_source_scope_counts.png')))\ndisplay(Image(filename=str(r.F/'03_source_target_comparison.png')))"),
      ('md','''**Yorum:** 76 özgün tablo hücresi:7 yaygın/69 yaygın olmayan.67 kaynak teriminin ilk10 içinde anotasyon adayı yoktur; bunlar yanlış negatif değildir.38 ortak PT'de çeviri/eşanlam adayı,21'de yalnız ilişkili terim,3'te sınıf uyarısı,3'te ilaç uyarısı,136'da anotasyon saptanmadı. Terim ilişkileri çoktan çoğa olabilir; aynı olay bağımsız kanıt gibi sayılmaz. Bulantı gibi kaynak olayları ortak201'in kapsamı dışında kalabilir.'''),
      ('code',"local=pd.read_csv(r.S/'local_feature_SHAP.csv',float_precision='round_trip')\npairs=pd.read_csv(r.S/'pair_additivity.csv',float_precision='round_trip')\ndisplay(pairs)\ndisplay(local)\nfor n in r.read(r.S/'selected_PT_names.json'):\n    print(n['rank'],n['term_tr_editorial'],n['class_id'])\n    display(Image(filename=str(r.ROOT/f\"reports/figures/WP13/tedizolid_B1_SHAP_v1/PT{n['rank']:02d}_{n['class_id']}_five_models.png\")))\n    display(pd.DataFrame([v for v in r.read(r.S/'Turkish_verbal_explanations.json') if v['class_id']==n['class_id']]))"),
      ('md','''**Yorum:** Mevcut50 ayrı model/PT açıklaması ve300katkı kullanıldı; yeni SHAP yok. Pozitif/negatif katkı yalnız ilgili B1 logitinin train-background'a göre değişimidir. Maske ayrı tutulur. Ortak sigmoid ortalaması tek doğrusal model gibi açıklanmaz; biyolojik mekanizma veya KÜB bulgusunun nedeni çıkarılmaz.'''),
      ('code',"display(pd.DataFrame([r.read(r.Q/'product_identity_and_limitations.json')]).T)\ndisplay(pd.read_csv(r.Q/'human_review_TEMPLATE.csv'))\nprint((r.Q/'reference_tests.log').read_text(encoding='utf-16') if (r.Q/'reference_tests.log').read_bytes().startswith(b'\\xff\\xfe') else (r.Q/'reference_tests.log').read_text(encoding='utf-8-sig'))"),
      ('md','''**Sonuç:** Kaynak ve sıralama izlenebilir şekilde karşılaştırıldı. Uzman eşleme alt kümesi henüz yok; AP/AUROC/klinik doğruluk yüzdesi hesaplanmadı. Tek molekül ve farklı fosfat ürün belgesi, tam kör veya dış klinik validasyon değildir. İnsan incelemesi beklenir. STOP.''')
    ])
    # Human-readable complete top10 report and links to full machine-readable records.
    tab=top[['rank','class_id','term_tr_editorial','record_ranking_score','source_terms','reference_status']].copy().fillna('—')
    tab.record_ranking_score=tab.record_ranking_score.map(lambda v:f'{v:.6f}');tab.reference_status=tab.reference_status.map(LABELS)
    report=f'''# WP13_EXTERNAL_REFERENCE_COMPARISON_v1 — Tedizolid / SIVEXTRO KÜB

## Sonuç ve kapsam

Kilitli ilk10'un tamamı, ortak201'in tüm skorları,50 bireysel model/PT açıklaması ve300gerçek SHAP katkısı korunarak karşılaştırıldı. İlk10'da **6 çeviri/eşanlam adayı,2 ilişkili fakat eşdeğer olmayan kavram,1 yalnız sınıf uyarısı,1 eşleme saptanmayan PT** var. Hepsi uzman onayı açısından PENDING; klinik doğruluk/başarı yüzdesi üretilmedi. “Destek” burada ancak kaynakta açık terim bulunması/anotasyon adayı anlamındadır; onaylı klinik eşdeğerlik değildir.

EXPLORATORY_EXTERNAL_LABEL_ISOLATED korunur. Hazırlık aramasında istenmeyen güvenlilik parçacıklarına maruziyet nedeniyle STRICT_ANALYST_BLINDNESS_COMPROMISED silinmedi. Bu çalışma tam araştırmacı-kör veya genel dış validasyon değildir.

## Kilit, kronoloji ve koruma

Prediction SHA-256: `{r.PRED_HASH}`

Explanation SHA-256: `{r.SHAP_HASH}`

Precommit ve pre-explanation dosyaları,5 model/metadata/scaler/head/girdi kaynakları,1294bireysel skor ve201ortak skor,10hedef,50açıklama,300katkı yeniden hash doğrulandı.1.069önceki dosya koruma kapsamındadır; tüm disk için iddia yok. Tahmin2026-11-08T23:22:47Z ve daha sonraki açıklama kaydı, bu referansın alınmasından önce gelir. Tam saatler before_reference_checks.json'dadır. Yerel manifest/hash kronolojisi bağımsız zaman damgası veya geçmiş analist bilgisinin yokluğuna kanıt değildir. İlk kod yürütmesinde gizli dosya koruyucusu herkese açık .gitignore'u da reddetti; PDF açılmadan yalnız bu allowlist hatası düzeltildi. Gerçek hash uyuşmazlığı olmadı. Hücre terimi Prürit/Prüritik alt-dize çakışması tam satır ankrajıyla engellendi; eski veriler değiştirilmedi.

## Gerçek belge

Kullanıcı sağladığı PDF367.220bayt/15fiziksel sayfa. Ham SHA-256 `{r.read(r.Q/'document_metadata.json')['raw_sha256']}`. Ham kopya reference/ klasöründe; asıl Downloads dosyası değişmedi. Bütün15sayfa PyMuPDF2.1 text/flags195/sort=False ile çıkarıldı; OCR uygulanmadı, boş sayfa atlanmadı. Sayfa6–8 görsel olarak sütunlarıyla kontrol edildi. Her hücre fiziksel sayfa, quote-ID, SHA ve değişmemiş metnin Python Unicode [start,end) aralığına bağlıdır; byte/görsel koordinat indeksi değildir.

Ürün: SIVEXTRO200mg/flakon **tedizolid fosfat**, IV infüzyonluk liyofilize toz; sulandırılınca50mg/mL. Tahmin **DB14569aktif tedizolid** üzerinden kilitlenmişti; DB09042fosfat NOT_RUN. Sayfa8/10ön ilaç→aktif dönüşümü bildirir, birebir molekül/formülasyon/doz eşitliği kurmaz.4.8güvenlilik tabanı oral ve/veya IV havuzudur; yalnız IV advers reaksiyon sıklığı diye sunulmaz. İlk ruhsat27.03.2019; KÜB yenilenme tarihi boş. PDF metadata2019tarihleri güncellik kanıtı değildir; currentness/publisher authenticity NOT_VERIFIED. Kaynağın m.2 ve m.6.1yardımcı madde ayrıntıları farklı kapsamlarla listelenir; bu çalışmada yeni yardımcı madde eşdeğerliği çıkarılmadı.

## Kilitli ilk10

{mdtable(tab)}

İshal↔Diyare, kusma, döküntü, karın ağrısı, prürit ve ürtiker çeviri/eşanlam adaylarıdır. Aşırı duyarlılık hedefi, **ilaca** aşırı duyarlılıktan daha geniştir; gastrointestinal ağrı, karın ağrısıyla birleştirilmedi. Anafilaktik şok, aşırı duyarlılık veya belgedeki septik şok ifadesinden türetilmedi. Trombositopeni sayfa3'te oksazolidinon sınıfının başka üyesine ait uyarıda; sayfa2'deki platelet düşüşü ayrı laboratuvar değişimidir. Doğrudan4.8ürün trombositopeni kaydı ilan edilmedi.

## Tüm201, kaynak kapsamı ve ilk10 dışında kalanlar

comparison201.csv/json, beş model skorunu, eski ortalamayı/sırayı ve ayrı kaynak durumunu içerir.1294eski bireysel skor dosyasının hiçbiri değişmedi.201'de38çeviri/eşanlam adayı,21yalnız ilişkili geniş/dar/farklı terim,3yalnız sınıf,3yalnız ilaç uyarısı,136eşleme saptanmayan hedef var. Bunlar tamamlanmış tıbbi terminoloji taraması değildir; açık70anotasyon satırının sonuçlarıdır. Kaynakta tam onaylı birebir klinik eşleşme ilan edilen kayıt0. relation alanları translation/synonym/target broader/narrower/source narrower/related distinct biçiminde ayrıdır.

76özgün4.8tablo hücresi (7yaygın,69yaygın olmayan) klinik76bağımsız yan etki sayısı değildir. Özet paragrafın tekrarı yeni kayıt sayılmadı. Genel prürit ve nitelemesiz prürit farklı hücre/sıklıkla korunur. Ortak201'e/ilk10'a eşlenemeyen hücreler all_reference_terms_target_coverage.csv'de; ilk10adayı bulunmayan67hücre reference_terms_outside_top10.csv'de. Örneğin bulantı kaynakta en sık bildirimlerdendir ama ortak201başlığında yoktur; hedef sonradan eklenmedi. Aynı karın ağrısı hücresinin hem abdominal pain hem daha geniş GI pain adayı olması iki bağımsız ürün kanıtı sayılmaz. Alt terimler, genel kavramlar, laboratuvar ve tanı, injection/infusion bölgesi, üst/alt anatomik kapsam otomatik eşitlenmez.

Çapraz eşleme bu referans görüldükten sonra açık gerekçelerle oluşturulan **ajan inceleme adayıdır**. Yeni web/yan etki veri tabanı/lisanslı MedDRA çeviri kaynağı kullanılmadı. İnsan/uzman human_review_TEMPLATE.csv'de adayın anlam, ürün/sınıf ve sıklık kapsamını ayrıca kaydetmelidir. Ajan yorumu resmî insan onayına dönüştürülmedi.

## Sıralama değerlendirmesi neden hesaplanmadı?

Uzman doğrulanmış eşleme alt kümesi0, tek aktif molekül ve farklı fosfat ürün/karma uygulama kaynağı var. KÜB'de yokluk gerçek negatif değildir. Bu koşullarda precision@10, recall, AP, AUROC, duyarlılık/özgüllük veya klinik başarı oranı için geçerli altın standart yok: **NOT_CALCULABLE**. Yalnız gözlemsel terim örtüşmesi ve sıralar betimlenir.38aday/201ve6aday/10 oranları semantik doğruluk ya da model başarı yüzdesi olarak sunulmaz. Bağımsız klinik genelleme kanıtı yoktur.

## Gerçek SHAP ve kullanıcı sunumu

İlk10hedefin tamamının mevcut50model/PT ve300katkısı gösterilir. Her modelin base+SHAP toplamı önceki kilitli logitle uyumlu kalır; yeni SHAP, tahmin tekrarı veya model seçimi yok. Pozitif/negatif katkı yalnız ilgili LR logitinin kendi train-only background'una göre yönüdür. Maske kimyadan ayrıdır; beşsigmoid ortalaması tekLRlogiti/ensembleSHAP değildir. Kaynakta olay geçmesi SHAP'ın kimyasal/biyolojik nedeni olarak açıklanmadı. Tam50Türkçe deterministik paragraf önceki immutable Turkish_verbal_explanations.json'dan okunur.

Eski FINALv2uygulama dosyası korunur; yeni FINALv3'te “Tedizolid dış tahmin deneyi” modu vardır. İki sütunda kayıtlı B1skoru/SHAP ile sonradan açılan KÜB alıntısı ayrı görünür. Seçim CUI/fold ile eşleşir; kaynak sayfası/quote-ID/aralık görünür. Grafikler yeni model sonucu değil, gerçek kilitli çıktının sunumudur. Lokal sunucu QAport8512; kullanıcı launcher varsayılan8501. Ekran kanıtları ayrı browser_QA kaydında, gerçek localhost'tan alınır; temsili UI üretilmez.

## Çıktılar, test ve durma

29kaynak/kilit/scope/skor-ayrımı testi reference_tests.log'da. UI akışı ayrıca gerçek Streamlit ve tarayıcı üzerinden denetlenir. Çalıştırılmış notebook: WP13_EXTERNAL_REFERENCE_COMPARISON_v1.ipynb.3karşılaştırma görseli ve7orijinal sayfa renderı, kaynak/iddia CSV/JSON, insan inceleme şablonu, ayrı referans sözleşmesi ve finalmanifest üretilir. Önceki WP00–WP13, QA, modeller, PDF'ler ve insan durumları değişmez. run_statuseski baytları aynen arşivlenir.

**STOP:** yeni training/prediction forward/SHAP/API, dış model veya başka referans incelemesi yapılmadı. Kaynak eşlemesi/ürün kapsamı için insan incelemesi bekleniyor. Klinik doğruluk veya mekanizma sonucu çıkarılmadı.
'''
    with (r.ROOT/'reports/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.md').open('x',encoding='utf-8') as f:f.write(report)
    print('3 figures, executed notebook, report and contract created.')

if __name__=='__main__':main()
