from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import streamlit as st
import pandas as pd
import wp13_core as core

st.set_page_config(page_title='Drug Safety Explorer · Graph-Tez',page_icon='◈',layout='wide')
st.markdown('''<style>
.stApp{background:#f4f7fb;color:#182e43} .block-container{padding-top:2rem;max-width:1450px}
h1,h2,h3{letter-spacing:-.03em} [data-testid="stSidebar"]{background:#eaf0f5}
[data-testid="stMetric"]{background:white;border:1px solid #dce5ed;border-radius:14px;padding:16px}
.hero{background:linear-gradient(110deg,#102b43,#15576a);padding:30px 34px;border-radius:18px;color:white;margin-bottom:22px}
.hero h1{color:white;margin:3px 0;font-size:2.5rem}.eyebrow{color:#91d9d1;letter-spacing:.16em;font-size:.72rem;font-weight:700}
.hero p{color:#d8e9ef;margin:7px 0}.pill{display:inline-block;background:#e4f2ee;color:#21695c;padding:5px 12px;border-radius:20px;font-size:.75rem;font-weight:700}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">GRAPH–TEZ V7 / RESEARCH DEMO</div><h1>Drug Safety Explorer</h1><p>Prospektüs kanıtını keşfedin. Model sıralamasını ayrı inceleyin.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.markdown('### ◈ Araştırma çalışma alanı')
    st.caption('Localhost · v1 · eğitim veya otomatik API yok')
    mode=st.radio('Çalışma modu',['VERIFIED_DEMO','EXPERIMENTAL_UPLOAD'])
    selected=st.selectbox('Kayıtlı prospektüs',['Erythromycin · 250 mg tablet','Doxycycline · monohydrate kapsül'])
    filename='pil.502.pdf' if selected.startswith('Erythromycin') else '050641Orig1s032lbl.pdf'
    upload=st.file_uploader('PDF yükle',type=['pdf'],help='Yalnız prospektüs. Hasta verisi yüklemeyin. Yerel bellekte işlenir; OCR yok.')
    st.divider();st.caption('VERIFIED: yalnız kaynak/hash eşleşmesi. Klinik bilgi veya LLM insan onayı anlamına gelmez.')
    st.caption('PENDING: insan incelemesi bekliyor. NOT_AVAILABLE: destekli kayıt yok.')

@st.cache_data(show_spinner=False)
def known(name):return core.verified_document(name)

@st.cache_data(show_spinner=False,max_entries=2,ttl=300)
def graph(doc):return core.gnn(doc)

try:
    if mode=='VERIFIED_DEMO':
        if upload is not None:
            found=core.match_upload(upload.getvalue())
            if not found or found['filename']!=filename:
                st.error('IDENTITY_MISMATCH — Yüklenen PDF seçili kaynakla hash düzeyinde eşleşmiyor. EXPERIMENTAL_UPLOAD kullanın.');st.stop()
        doc=known(filename);rows=[q for q in doc['quotes'] if q['purpose'] in ['adverse_section','adverse_context','warning','warning_section','interaction','scope_anchor']]
        title=doc['record']['existing_parent_name']
    else:
        if upload is None:
            st.info('EXPERIMENTAL — Sayfa metinlerini incelemek için gerçek bir PDF yükleyin. Kimlik otomatik atanmaz.');st.stop()
        doc=core.extract_pdf(upload.getvalue());rows=core.candidates(doc);title='Yeni PDF · kimlik doğrulanmadı'
except Exception:
    st.error('NOT_AVAILABLE — PDF okunamadı, limit aşıldı veya kaynak bütünlüğü doğrulanamadı. OCR ve otomatik tamamlama yapılmadı.');st.stop()

st.markdown(f'## {title}')
st.caption('VERIFIED kaynak · açıklamalar PENDING' if mode=='VERIFIED_DEMO' else 'EXPERIMENTAL · sözcük bağlamı adayları, klinik doğrulama yok')
cols=st.columns(4)
for col,label,value in zip(cols,['Fiziksel sayfa','Kaynak pasajı','İnsan açıklama QA','İşleme'],[doc['page_count'],len(rows),'PENDING','OCR YOK']):col.metric(label,value)
st.caption('Belge SHA-256: '+doc['sha256'])
if mode=='VERIFIED_DEMO':
    rec=doc['record'];st.info(f"Ana etkin madde bağlantısı: {rec['DrugBank_parent_id']} · ürün/tuz/doz eşdeğerliği kurulmuş değildir. Kaynak sürümü mevcut kayıtla sınırlıdır.")
else:st.warning('İlaç kimliği UNVERIFIED. Dosya adı ve metin içindeki ilaç adı, DrugBank eşdeğerliği kanıtı değildir.')
tabs=st.tabs(['Kaynak bulguları','Türkçe açıklamalar','GNN kayıtları','Sayfa & provenans'])
with tabs[0]:
    st.subheader('Prospektüste bildirilenler')
    st.caption('reported_in_PDF · birebir kaynak pasajları; SIDER etiketi veya GNN girdisi değildir.')
    if not rows:st.warning('NOT_AVAILABLE — Kullanılabilir aday pasaj yok. Bu, yan etki olmadığı anlamına gelmez. Görsel metni için OCR uygulanmadı.')
    else:
        table=[]
        for q in rows:
            table.append({'Sayfa':q.get('page_number',q.get('physical_page')),'Amaç':q.get('purpose','Anahtar sözcük bağlamı'),
                'Kapsam':q.get('scope','EXPERIMENTAL'),'Kaynak ifadesi':q['quote'],'Niteleme':q.get('qualifier','İnsan incelemesi gerekli')})
        st.dataframe(pd.DataFrame(table),hide_index=True,width='stretch',height=330)
        index=st.selectbox('Tam alıntı ve kaynak aralığı',range(len(rows)),format_func=lambda i:f"{i+1}. pasaj · fiziksel sayfa {rows[i].get('page_number',rows[i].get('physical_page'))}")
        q=rows[index];st.code(q['quote'],language=None,wrap_lines=True)
        st.caption(f"{q['quote_id']} · Unicode [{q['char_start']}, {q['char_end']})")
        st.caption('Sıklık/uyarılar yalnız metinde yazdığı biçimde gösterilir. Bilinmeyen sıklık nadir/yaygın/yüzdeye çevrilmez; sınıf ifadeleri doğrudan ilaç kanıtı yapılmaz.')
with tabs[1]:
    st.subheader('Kaynaklı Türkçe açıklama adayları')
    if mode=='VERIFIED_DEMO':
        for item in core.saved_explanations(filename):
            with st.container(border=True):
                st.caption(f"{item['scenario']} · item {item['item']} · fiziksel sayfa {item['physical_page']} · PENDING")
                st.write(item['model_explanation_exact']);st.warning('Ajan inceleme notu: '+item['agent_note_tr'])
                with st.expander('Birebir kaynak ve atıf'):st.code(item['source_quote_exact'],language=None,wrap_lines=True)
        st.divider();st.markdown('#### İsteğe bağlı yeni API adayı')
        st.caption('GPT-5.4-mini · yalnız mevcut frozen S04/S07 alıntıları. WP13 toplam tek deneme; otomatik tekrar yok. Kaynak metni dış servise iletilecektir. Klinik risk/skor üretilmez.')
        with st.expander('Gönderilecek tam metni ve maliyet kapısını incele'):
            import wp12_openai_scenarios_v2 as scenario
            case='S04' if filename=='pil.502.pdf' else 'S07'
            st.json(scenario.context(case)[1],expanded=False)
            st.caption('6000 input /1200 output sınırı; %20 payla üst plan $0.01188, rezerv $0.023. WP12 global tavan 30HTTP/10inference/$0.25 korunur. Fiyat snapshot süresi dolmuşsa çağrı yapılmaz.')
        consent=st.checkbox('Yalnız gösterilen alıntıların API’ye gönderilmesini ve en fazla $0.023 rezervi kabul ediyorum.')
        if st.button('Tek kaynaklı açıklama isteğini başlat',disabled=not consent,type='primary'):
            try:
                import wp13_api
                result=wp13_api.run_from_ui(filename,consent=consent)
                st.session_state['api_result']=result
            except Exception:st.session_state['api_result']={'status':'SAFE_STOP_NO_RETRY','review':'PENDING'}
        if 'api_result' in st.session_state:st.json(st.session_state['api_result'])
    else:st.info('NOT_AVAILABLE — Yeni PDF için API açıklaması bu v1’de açık değildir. Genel kaynak adaptörü/insan incelemesi gerekir. Metin ve aday alıntılar yerelde incelenebilir.')
with tabs[2]:
    st.subheader('GNN kaynak-kayıt sıralaması')
    st.caption('predicted_by_GNN · kayıtlı WP10 A1P1, primary outer-test OOF. Yeni inference veya eğitim yapılmaz.')
    st.warning('Skor, SIDER observed-record proxy sıralamasıdır; bireysel hastada klinik yan etki olasılığı değildir. Unknown çiftler doğrulanmış negatif değildir.')
    result=graph(doc)
    if result['status']=='NOT_AVAILABLE':st.info('NOT_AVAILABLE — '+result['reason'])
    else:
        st.caption(f"{result['parent_id']} · outer fold {result['fold']} · {result['targets']} destekli PT · {result['model_version']}")
        st.caption('Bu, yüklenen ürün için yeni tahmin değildir; ana ilaç için önceden kaydedilmiş araştırma çıktısıdır. Fold hedef sözlüğü dışında skor yoktur.')
        st.dataframe(pd.DataFrame(result['rows'][:20]).rename(columns={'class_id':'Kaynak PT CUI','score_observed_record_proxy':'Kayıt sıralama skoru'}),hide_index=True,width='stretch')
        st.bar_chart(pd.DataFrame(result['rows'][:10]).set_index('class_id')['score_observed_record_proxy'],horizontal=True)
with tabs[3]:
    st.subheader('Sayfa metni & kaynak izi')
    number=st.number_input('Fiziksel sayfa',1,doc['page_count'],1)
    p=doc['pages'][number-1];st.caption(f"{p['status']} · {p['image_count']} görsel nesne · {len(p['text'])} Unicode karakter")
    if p['status']=='IMAGE_TEXT_UNAVAILABLE':st.warning('IMAGE_TEXT_UNAVAILABLE — Kısa metin/footer görsel kutusunun yerine kullanılamaz. OCR/görsel okuma yapılmadı.')
    st.code(p['text'] or '[Metin katmanı yok]',language=None,wrap_lines=True)
    st.caption('Sayfa metni SHA-256: '+p['text_sha256'])
st.divider();st.caption('Araştırma demosu · Kaynak doğrulaması ≠ insan semantik onayı · Klinik karar desteği veya kişisel tedavi önerisi değildir.')
