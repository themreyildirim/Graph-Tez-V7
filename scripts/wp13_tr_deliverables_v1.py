"""Executed teaching notebook from real Turkish-source QA; no API, training or predictions."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from wp09_close_wp10_notebooks import execute,INIT
from wp13_tr_sources_v1 import load,statistics,validate
Q=ROOT/'reports/qa/WP13/tr_source_v1'

def main():
    docs=[load(i) for i in range(2)]
    import pandas as pd
    registry=[];pages=[];quotes={}
    for d in docs:
        validate(d);r=d['record']
        registry.append({k:v for k,v in r.items() if k not in ['identity_evidence','version_evidence','PDF_metadata']}|{'document_id':d['document_id'],'sha256':d['sha256'],'pages':d['page_count'],'parser':d['parser']})
        for p in d['pages']:pages.append({'filename':r['filename'],**{k:v for k,v in p.items() if k!='text'},'characters':len(p['text']),'replacement_characters':p['text'].count('\ufffd')})
        for c in d['candidates']:
            for q in [c['source']]+c['context_quotes']+([c['frequency_quote']] if c['frequency_quote'] else []):quotes[q['quote_id']]=q
        for q in d['contexts']:quotes[q['quote_id']]=q
    for name,value in [('document_registry.json',registry),('all_quotes.json',list(quotes.values()))]:
        with (Q/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    pd.DataFrame(pages).to_csv(Q/'page_quality.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(quotes.values()).to_csv(Q/'all_quotes.csv',index=False,encoding='utf-8-sig')
    execute('WP13_Turkish_source_pilot_v1.ipynb',[
      ('md','''# WP13 — İki gerçek Türkçe prospektüs / TR_SOURCE_v1

İngilizce kaynaklardan bağımsız belge kimlikleri. Yeni API, OCR, eğitim veya model inference yoktur. Özgün Türkçe terimler yalnız gerçek kaynak sayfa/aralıklarından gösterilir. **Güncellik doğrulanmadı; insan QA PENDING**. Kaynak/hash doğrulaması klinik doğruluk değildir.

## 1. Ürün, tuz, belge ve tarih'''),
      ('code',INIT+r'''
import wp13_tr_sources_v1 as tr
Q=ROOT/'reports/qa/WP13/tr_source_v1';F=ROOT/'reports/figures/WP13/tr_source_v1'
docs=[tr.load(i) for i in range(2)]
display(pd.DataFrame([{k:d['record'][k] for k in ['product','document_type','composition','currentness','document_revision_date','filename_date_hint','English_product_equivalence']} for d in docs]))
display(pd.read_csv(Q/'page_quality.csv'))
'''),
      ('md','''**Yorum:** ERİTRO8, MONODOKS13 fiziksel sayfadır;21 sayfa metin katmanından çıkarıldı, boş/görsel sayfa atlanmadı. Tuz ve dozlar ürün sayfa1 kanıtıyla saklanır. KT onay/KÜB yenilenme alanı boş/yer tutucudur;2018 dosya adı güncellik onayı değildir. İngilizce ürünlerle eşdeğerlik varsayılmaz.

## 2. Gerçek aday sayıları ve sıklık'''),
      ('code',r'''
counts=pd.read_csv(Q/'count_summary.csv').fillna(0);display(counts)
fig,ax=plt.subplots(figsize=(10,4.5))
counts.set_index('product')[['records','unique_source_terms']].plot.bar(rot=0,ax=ax,color=['#207f92','#d2a453'])
ax.set(title='Türkçe kaynak tarama kayıtları — klinik etki sayısı değil',ylabel='Sayı');plt.tight_layout();plt.savefig(F/'07_actual_TR_counts.png',dpi=160);plt.show()
display(pd.DataFrame([{'ürün':d['record']['product'],'aday':c['name_tr'],'sayfa':c['source']['physical_page'],'sıklık':c['frequency_state'],'kapsam':c['scope'],'inceleme':c['status']} for d in docs for c in d['candidates']]))
'''),
      ('md','''**Yorum:** ERİTRO25 madde satırı:6 oldukça seyrek,19 bilinmiyor. MONODOKS48 kayıt/47 terim:glossit iki bölümde. KÜB terimleri ve KT madde satırları farklı birimlerdir; bu sayılar biyolojik kapsam üstünlüğü değildir. MONODOKS37 ürün,6 açık sınıf,5 kısmen belirsiz kapsam; belirsiz5 kayıtta yerel Seyrek başlığının/parantez sonrası kapsamın uzanımı insan incelemesi bekler. Bilinmiyor, seyrek ve sıklık belirtilmemiş birbirine doldurulmaz. Hiçbir aday klinik olarak onaylanmadı.

## 3. BUN / birikim ve ayrı kaynak bağlamları'''),
      ('code',r'''
bun=next(c for c in docs[1]['candidates'] if c['name_tr']=='BUN artışı')
display(pd.DataFrame([bun['source']]+bun['context_quotes'])[['physical_page','statement_kind','scope','quote_exact','quote_id','char_start','char_end']])
display(pd.DataFrame([q for d in docs for q in d['contexts'] if q['statement_kind'] in ['overdose','animal_study']])[['physical_page','statement_kind','scope','quote_exact','quote_id']])
assert all(tr.validate(d) for d in docs)
'''),
      ('md','''**Yorum:** 4.8 BUN artışı sıklığı bilinmeyen kayıt olarak kalır.4.2'de tetrasiklin sınıf BUN uyarısı ve MONODOKS birikim yokluğu ayrı kaynak cümleleridir. Birikim yokluğu BUN yokluğu değildir. Aşırı doz ve hayvan bulguları normal kullanım aday tablosuna eklenmedi. Tiroid renk değişimi ile fonksiyon bozukluğunun bilinmediği cümle aynı kanıtta korunur.

## 4. Gerçek localhost ekranları'''),
      ('code',r'''
from IPython.display import Image
for f in ['10_final_ERITRO_table.jpg','08_final_MONODOKS_BUN.jpg','09_final_MONODOKS_table.jpg']:
    display(Image(filename=str(F/f),width=1000))
'''),
      ('md','''**Yorum:** Görseller gerçek çalışan127.0.0.1:8506 arayüzünden alındı. Yeni Türkçe kaynaklara atıf yapan kayıtlı LLM yanıtı yok:NOT_AVAILABLE. Geçmiş İngilizce açıklamalar Türkçe ürünlerin açıklaması olarak taşınmadı. GNN yalnız ayrı ana etkin madde OOF panelidir; ürün tahmini veya klinik risk değildir. Kaynak PENDING kararları kullanıcı adına değiştirilmedi.''')])
if __name__=='__main__':main()
