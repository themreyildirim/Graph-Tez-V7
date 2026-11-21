"""Offline Turkish-source demo. No API or model inference. Previous demos unchanged."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import streamlit as st
import pandas as pd
import wp13_tr_sources_v1 as tr
import wp13_presentation_v1_2 as state
st.set_page_config(page_title='Drug Safety Explorer · Türkçe kaynak',page_icon='◈',layout='wide')
st.markdown('''<style>.block-container{padding-top:2rem;padding-bottom:2rem;max-width:1500px}
h1,h2,h3{letter-spacing:-.02em} [data-testid="stMetric"]{background:#f1f6f9;padding:1rem;border-radius:12px}
[data-testid="stSidebar"]{background:#edf3f7} .stCaption{overflow-wrap:anywhere}</style>''',unsafe_allow_html=True)
st.caption('GRAPH–TEZ V7 / WP13_TR_SOURCE_v1 · OFFLINE ARAŞTIRMA DEMOSU')
st.title('Drug Safety Explorer')
st.write('Türkçe prospektüs bulguları ve izlenebilir kaynak kanıtları')
with st.sidebar:
    st.header('Türkçe kaynaklar')
    selected=st.selectbox('Aktif Türkçe belge',['ERİTRO 500 mg · KT','MONODOKS 100 mg · KÜB'])
    index=0 if selected.startswith('ERİTRO') else 1
    st.info('Güncellik doğrulanmadı. Kaynak hash kontrolü klinik onay değildir.')
    st.caption('İngilizce PDF’ler ve eski demolar tarihsel kaynak olarak korunur; bu ekranın aktif kaynağı değildir.')
    st.caption('API KAPALI · OCR yok · yeni tahmin/eğitim yok')
@st.cache_data(show_spinner=False)
def recorded_graph(index):
    old=tr.core.verified_document(['pil.502.pdf','050641Orig1s032lbl.pdf'][index])
    return state.gnn_named(old)
try:
    doc=tr.load(index);tr.validate(doc)
except Exception:
    st.error('SOURCE_INTEGRITY_UNAVAILABLE — Kaynak ya da kayıtlı alıntı bütünlüğü doğrulanamadı.');st.stop()
r=doc['record'];rows=doc['candidates'];summary=tr.statistics(doc)
st.subheader(r['product'])
st.write(r['composition'])
st.warning('UNVERIFIED_CURRENTNESS · Türkçe PDF’nin güncelliği doğrulanmadı. İngilizce ürünle tuz/doz/formülasyon eşdeğerliği kurulmadı.')
cols=st.columns(4)
for col,label,value in zip(cols,['Kaynak aday kaydı','Benzersiz kaynak terimi','Tekrar fazlası','İnsan incelemesi'],[summary['records'],summary['unique_source_terms'],summary['extra_term_records'],'PENDING']):col.metric(label,value)
st.caption('Bu sayılar kaynak tarama birimleridir; klinik olarak doğrulanmış yan etki veya bağımsız kanıt sayısı değildir. KT madde satırları ve KÜB terim listeleri farklı sayım birimleridir.')
with st.expander('Belge kimliği, sürümü ve sayımlar'):
    st.write('Belge türü: '+r['document_type']+' · fiziksel sayfa: '+str(doc['page_count']))
    st.code(doc['sha256'],language=None)
    st.write('Belge içi yenilenme/onay tarihi: boş veya yer tutucu. Dosya adındaki tarih doğrulanmış sürüm değildir.')
    st.json(summary)
    st.caption('Ana etkin madde araştırma bağlantısı '+r['parent_id']+'; ürün eşdeğerliği onayı değildir.')
    st.text(r['identity_evidence']['quote_exact']);st.text(r['version_evidence']['quote_exact'])
namespace='tr_'+doc['sha256'];ids=[c['candidate_id'] for c in rows];byid={c['candidate_id']:c for c in rows}
state.init_selection(st.session_state,namespace,ids)
st.selectbox('Yan etki adayı seçin',ids,format_func=lambda cid:tr.candidate_label(byid[cid]),key=namespace+'_picker',on_change=state.picker_changed,args=(st.session_state,namespace,ids))
c=byid[st.session_state[namespace+'_active']]
def evidence(q):
    st.caption(f"Fiziksel sayfa {q['physical_page']} · {q['quote_id']} · [{q['char_start']}, {q['char_end']}) · {q['statement_kind']} / {q['scope']}")
    st.text(q['quote_exact'])
scope_names={'product_specific':'Bu ürünün yan etki bölümündeki bildirim','class_level':'Tetrasiklin sınıfına ait ifade','drug_direct':'Doğrudan etkin madde ifadesi','unresolved':'Kapsam kısmen belirsiz — insan incelemesi bekliyor'}
tabs=st.tabs(['Türkçe kaynak ve açıklama','Yan etki tablosu','Uyarılar / aşırı doz / hayvan verileri','GNN araştırma kaydı','Bütün PDF sayfaları'])
with tabs[0]:
    st.subheader(c['name_tr'])
    st.caption('Özgün Türkçe kaynak aktarımı · LLM çıktısı değildir · PENDING')
    st.write('**Sıklık:** '+('Sıklığı bilinmiyor; sayısal olasılık değildir.' if c['frequency_state']=='UNKNOWN' else 'Kaynağın seyrek nitelemesi; kendi başlığı/bağlamıyla okunmalıdır.' if c['frequency_state']=='RARE_SOURCE_WORDING' else 'Sıklık belirtilmemiş.'))
    st.write('**Kapsam:** '+scope_names[c['scope']])
    if c['source_note']:st.info(c['source_note'])
    st.markdown('#### Orijinal Türkçe prospektüs kanıtı');evidence(c['source'])
    if c['frequency_quote']:
        with st.expander('Sıklık başlığı / özgün niteleme'):evidence(c['frequency_quote'])
    for context in c['context_quotes']:
        st.markdown('#### Bağlı uyarı / koşul');evidence(context)
    st.caption('Seçili candidate_id: '+c['candidate_id'])
    st.info('Kayıtlı model açıklaması: NOT_AVAILABLE — Bu Türkçe belge ve alıntı kimliğini kaynak gösteren kayıtlı LLM yanıtı yok. İngilizce ürüne ait açıklama iliştirilmedi.')
    st.caption('Biyolojik mekanizma veya model attribution değeri bu kaynak ekranından üretilmez.')
with tabs[1]:
    st.subheader('Türkçe yan etki adayları · PENDING')
    table=pd.DataFrame([{'Özgün Türkçe aday':a['name_tr'],'Sıklık':{'UNKNOWN':'Bilinmiyor','RARE_SOURCE_WORDING':'Seyrek — kaynak ifadesi','NOT_SPECIFIED':'Belirtilmemiş'}[a['frequency_state']],
      'Kapsam':scope_names[a['scope']],'Sayfa':a['source']['physical_page'],'İnceleme':'PENDING'} for a in rows])
    key=namespace+'_table_'+str(st.session_state[namespace+'_epoch'])
    st.dataframe(table,hide_index=True,width='stretch',height=420,key=key,selection_mode='single-row-required',selection_default={'selection':{'rows':[ids.index(c['candidate_id'])]}},on_select=lambda ns=namespace,ordered=ids,k=key:state.table_changed(st.session_state,ns,ordered,k))
    st.write('**Seçili aday:** '+c['name_tr']);st.caption(c['candidate_id']);evidence(c['source'])
with tabs[2]:
    st.subheader('Ayrı kaynak bağlamları')
    st.caption('Aşırı doz ve hayvan bulguları normal kullanım yan etki aday toplamına dahil değildir. Bir uyarıda geçen bulgu otomatik yeni aday yapılmaz.')
    for q in doc['contexts']:
        if q['statement_kind'] in ['warning','overdose','animal_study']:
            with st.expander(f"{q['statement_kind']} · {q['scope']} · fiziksel sayfa {q['physical_page']}"):evidence(q)
with tabs[3]:
    st.warning('predicted_by_GNN ≠ reported_in_PDF. SIDER observed-record proxy sıralaması; klinik bireysel risk değildir. Unknown gerçek negatif değildir.')
    st.write('Türkçe ürün için yeni tahmin: NOT_AVAILABLE. Aşağıdaki seçenek yalnız aynı ana etkin maddenin önceden kaydedilmiş kendi-fold OOF araştırma kaydını gösterir; tuz/doz/ürün eşdeğerliği iddiası değildir.')
    if st.checkbox('Ana etkin maddenin kayıtlı OOF araştırma tablosunu göster',value=False):
        g=recorded_graph(index)
        if g['status']=='NOT_AVAILABLE':st.info('NOT_AVAILABLE')
        else:
            st.caption(f"{g['parent_id']} · A1P1 primary outer{g['fold']} · {g['targets']} PT · {g['model_version']}")
            st.dataframe(pd.DataFrame(g['rows'][:25])[['class_id','target_name','score_observed_record_proxy']],hide_index=True,width='stretch')
    st.caption('PDF adayları/PT eşleştirilmedi; PDF yan etkileri model girdisi yapılmadı.')
with tabs[4]:
    n=st.number_input('Fiziksel sayfa',1,doc['page_count'],1,key='tr_page_'+str(index));p=doc['pages'][n-1]
    st.caption(f"{p['status']} · {p['image_count']} görsel · {len(p['text'])} karakter · OCR yapılmadı")
    st.text(p['text'] or 'NOT_AVAILABLE — Metin katmanı yok.');st.caption(p['text_sha256'])
st.divider();st.caption('Yerel araştırma demosu · Kaynak güncelliği doğrulanmadı · İnsan QA PENDING · Kişisel tedavi önerisi değildir.')
