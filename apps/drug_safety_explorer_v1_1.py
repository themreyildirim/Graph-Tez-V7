from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import streamlit as st
import pandas as pd
import wp13_core as core
import wp13_candidates_v1_1 as method

st.set_page_config(page_title='Drug Safety Explorer · v1.1',page_icon='◈',layout='wide')
st.markdown('''<style>
.stApp{background:#f5f7fb;color:#182e43}.block-container{padding-top:1.7rem;max-width:1440px}
[data-testid="stSidebar"]{background:#eaf0f5;color:#182e43}
[data-testid="stMetric"]{background:white;border:1px solid #dce5ed;border-radius:12px;padding:14px}
.hero{background:linear-gradient(110deg,#102b43,#15576a);padding:25px 30px;border-radius:16px;color:white;margin-bottom:20px}
.hero h1{color:white;margin:4px 0;font-size:2.4rem}.hero p{color:#d6ebf0;margin:4px 0}
.eyebrow{color:#91d9d1;letter-spacing:.15em;font-size:.72rem;font-weight:700}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">GRAPH–TEZ V7 / LOCAL RESEARCH DEMO v1.1</div><h1>Drug Safety Explorer</h1><p>Yan etki adayından orijinal prospektüs kanıtına.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.markdown('### ◈ Kaynak çalışma alanı')
    mode=st.radio('Çalışma modu',['VERIFIED_DEMO','EXPERIMENTAL_UPLOAD'])
    selection=st.selectbox('Kayıtlı prospektüs',['Erythromycin · 250 mg tablet','Doxycycline · monohydrate kapsül'])
    filename='pil.502.pdf' if selection.startswith('Erythromycin') else '050641Orig1s032lbl.pdf'
    upload=st.file_uploader('Prospektüs PDF yükle',type=['pdf'],help='Hasta verisi yüklemeyin. Yalnız yerel bellek; OCR yok.')
    st.divider();st.caption('VERIFIED yalnız kaynak/hash eşleşmesidir. Yan etki adayları ve kayıtlı LLM metinleri insan incelemesi bekler.')
    st.caption('API KAPALI · eğitim yok · otomatik inference yok')

@st.cache_data(show_spinner=False)
def known(filename):return core.verified_document(filename)

@st.cache_data(show_spinner=False,max_entries=2)
def graph(doc):return method.gnn_named(doc)

try:
    if mode=='VERIFIED_DEMO':
        if upload is not None:
            found=core.match_upload(upload.getvalue())
            if not found or found['filename']!=filename:
                st.error('IDENTITY_MISMATCH — Yüklenen PDF seçili kaynakla aynı hash’e sahip değil. Yeni PDF’yi EXPERIMENTAL_UPLOAD modunda inceleyin.');st.stop()
        doc=known(filename);candidates=method.known(doc);title=doc['record']['existing_parent_name']
    else:
        if upload is None:
            st.info('PDF bekleniyor. EXPERIMENTAL_UPLOAD, sayfa metinlerini ve sınırlı yerel sözlüğün bulabildiği yan etki adaylarını gösterir; kimlik veya klinik doğruluk onayı vermez.');st.stop()
        doc=core.extract_pdf(upload.getvalue());candidates=method.experimental(doc);title='Yeni PDF · ilaç kimliği doğrulanmadı'
except Exception:
    st.error('Kaynak açılamadı veya bütünlük doğrulanamadı. PDF biçimini/boyutunu kontrol edin. OCR ve kaynak tamamlama yapılmadı.');st.stop()

st.subheader(title)
cols=st.columns(4)
for col,label,value in zip(cols,['Fiziksel sayfa','Yan etki adayı','İnceleme durumu','Çalışma'],[doc['page_count'],len(candidates),'PENDING','OFFLINE']):col.metric(label,value)
st.caption('SHA-256: '+doc['sha256'])
if mode=='VERIFIED_DEMO':
    st.info(f"VERIFIED kaynak · {doc['record']['DrugBank_parent_id']} ana etkin madde bağlantısı. Ürün/tuz/doz eşdeğerliği veya VERIFIED_CLINICAL onayı değildir.")
else:st.warning('EXPERIMENTAL · ilaç kimliği, sıklık ve kapsam doğrulanmış değildir. Çıkarım sözlüğü sınırlıdır; bulunmaması yan etki yokluğu anlamına gelmez.')
st.caption('WP13 yöntem v1.1 · aday çıkarımı WP12 frozen deney sonucu değildir. Örtüşen alıntılar bağımsız klinik kanıt sayılmaz; tüm adaylar MedDRA UNMAPPED.')

if candidates:
    selected=st.selectbox('Yan etki seçin',range(len(candidates)),format_func=lambda i:f"{candidates[i]['name_tr']} · {candidates[i]['scope']} · sayfa {candidates[i]['physical_page']}",key='candidate_'+doc['sha256']+'_'+mode)
    candidate=candidates[selected]
else:candidate=None
tabs=st.tabs(['Yan etkiler','Türkçe açıklama ve kaynak','GNN araştırma sonuçları','PDF sayfaları ve kaynak izi'])

def source_view(c):
    st.markdown('#### '+c['name_tr'])
    st.caption(f"Sıklık: {c['frequency']} · Kapsam: {c['scope']} · {c['status']}")
    st.caption(f"Fiziksel sayfa {c['physical_page']} · {c['quote_id']} · alıntı [{c['quote_start']}, {c['quote_end']}) · terim [{c['term_start']}, {c['term_end']})")
    st.code(c['quote_exact'],language=None,wrap_lines=True)
    if c['frequency_source']:st.text('Sıklık kanıtı: '+c['frequency_source'])
    st.text('Kaynak kapsam/koşul notu: '+c['qualifier'])
    for q in c['context_quotes']:
        st.caption(f"Zorunlu bağlam / istisna · fiziksel sayfa {q['page_number']} · {q['quote_id']} · [{q['char_start']}, {q['char_end']})")
        st.code(q['quote'],language=None,wrap_lines=True)

with tabs[0]:
    st.markdown('### Prospektüsten çıkarılan yan etki adayları')
    st.caption('reported_in_PDF · kaynak destekli aday terimler; klinik olarak onaylanmış olay veya MedDRA/PT eşlemesi değildir.')
    if candidates:
        data=[]
        for c in candidates:
            data.append({'Yan etki adı':c['name_tr'],'Kaynak terim':c['source_term'],'Sıklık':c['frequency'],'Atıf kapsamı':c['scope'],
                'Uyarı / istisna / koşul':c['qualifier']+(' | Ek kaynak/istisna aşağıda.' if c['context_quotes'] else ''),
                'PDF sayfası':c['physical_page'],'quote-ID':c['quote_id'],'Karakter aralığı':f"[{c['quote_start']}, {c['quote_end']})",'İnceleme':c['status']})
        event=st.dataframe(pd.DataFrame(data),hide_index=True,width='stretch',height=340,on_select='rerun',selection_mode='single-row',key='table_'+doc['sha256']+'_'+mode+'_'+str(selected))
        indices=event.selection.rows
        detail=candidates[indices[0]] if indices else candidate
        st.caption('Bir satıra tıklayın; ilgili orijinal pasaj aşağıda açılır. Diğer sekmeler için üstteki “Yan etki seçin” alanını kullanın.')
        candidate=detail
        source_view(detail)
    else:
        st.warning('Ayrıştırılabilir yan etki adayı bulunamadı. Metin katmanı yoksa/görsel ağırlıklıysa çıkarım durur. Sözlük dışı pasajlar zorla listeye eklenmez; PDF sayfaları sekmesinde gerçek metni inceleyin.')
with tabs[1]:
    st.markdown('### Seçili yan etki: kaynak ve kayıtlı açıklama')
    if candidate:
        source_view(candidate)
        results=method.explanation(candidate,filename) if mode=='VERIFIED_DEMO' else []
        if results:
            for row in results:
                with st.container(border=True):
                    st.caption(f"Kayıtlı WP12 {row['scenario']} item {int(row['item'])} · PENDING · yeni API çağrısı değil")
                    st.text(row['model_explanation_exact']);st.warning('Önceki ajan kalite notu: '+row['agent_note_tr'])
                    st.caption('Bu metin seçili terimi içerir fakat daha geniş bir kaynak pasajını da özetleyebilir. Önceki kusurlar aynen korunur.')
        else:st.info('NOT_AVAILABLE — Bu seçili aday için kaynak-ID ve terim kapsamı doğrulanan kayıtlı bir açıklama yok. Başka senaryonun yanıtı iliştirilmedi. Orijinal kanıt yukarıda gösterilir; yeni açıklama uydurulmaz.')
    else:st.info('Önce destekli bir aday seçin. Ayrıştırılamayan kaynak için açıklama üretilmez.')
    st.caption('Bu v1.1 tamamen offline çalışır. API düğmesi yoktur; eski bütçe ve tek-deneme kilitleri korunur.')
with tabs[2]:
    st.markdown('### Kayıtlı GNN araştırma sonuçları')
    st.warning('predicted_by_GNN · SIDER observed-record proxy sıralaması. Klinik bireysel yan etki olasılığı değildir. Unknown çiftler gerçek negatif değildir.')
    result=graph(doc)
    if result['status']=='NOT_AVAILABLE':st.info('NOT_AVAILABLE — '+result['reason']+' VERIFIED_DEMO modunda mevcut Erythromycin/Doxycycline kaynaklarını seçerek kayıtlı araştırma kapsamını görebilirsiniz.')
    else:
        st.caption(f"{result['parent_id']} · A1P1 · primary outer fold {result['fold']} · {result['targets']} PT · {result['model_version']}")
        st.caption('Yalnız kayıtlı outer-test OOF skorları; ürün için yeni tahmin yok. Aday yan etki ile PT otomatik eşleştirilmez; adayın MedDRA durumu UNMAPPED kalır.')
        st.dataframe(pd.DataFrame(result['rows'][:25])[['class_id','target_name','score_observed_record_proxy','model_job_key']].rename(columns={'class_id':'PT CUI','target_name':'Dondurulmuş hedef adı','score_observed_record_proxy':'Kayıt sıralama skoru'}),hide_index=True,width='stretch')
with tabs[3]:
    st.markdown('### Fiziksel PDF sayfası ve kaynak izi')
    number=st.number_input('Fiziksel sayfa',1,doc['page_count'],1)
    p=doc['pages'][number-1];st.caption(f"{p['status']} · {p['image_count']} görsel nesne · {len(p['text'])} karakter")
    if p['status']!='TEXT_AVAILABLE':st.warning('OCR/görsel okuma yapılmadı. Footer veya boş metin, görsel içeriğinin yerine geçmez.')
    st.code(p['text'] or '[Metin katmanı yok]',language=None,wrap_lines=True);st.caption('Metin SHA-256: '+p['text_sha256'])
st.divider();st.caption('Araştırma demosu · VERIFIED kaynak ≠ VERIFIED_CLINICAL · İnsan QA PENDING · Kişisel tedavi önerisi değildir.')
