"""Unified offline demonstration: recorded predictions, explanations and separate PDF reference."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pandas as pd
import streamlit as st
import wp13_final_data_v1 as data
import wp13_explain_v2 as explain
tr=data.tr
st.set_page_config(page_title='Graph-Tez | Final Demo v2',page_icon='◈',layout='wide')
st.markdown('''<style>.block-container{max-width:1500px;padding-top:2rem}h1{font-size:2rem!important;letter-spacing:-.02em}
[data-testid="stSidebar"]{background:#edf3f7}[data-testid="stMetric"]{background:#f0f6f8;padding:1rem;border-radius:10px}</style>''',unsafe_allow_html=True)
st.title('Graph-Tez | İlaç Yan Etki Tahmin ve Açıklanabilirlik Sistemi')
st.caption('Araştırma demosu · Kayıtlı tahmin ≠ prospektüs bildirimi ≠ klinik risk')
with st.sidebar:
    mode=st.radio('Ana işlem',['Kayıtlı ilaç seç','Prospektüs PDF yükle'])
    index=None;doc=None
    if mode=='Kayıtlı ilaç seç':
        sample=st.selectbox('Kayıtlı ilaç',['ERİTRO 500 mg','MONODOKS 100 mg']);index=0 if sample.startswith('ERİTRO') else 1
        use_pdf=st.checkbox('Türkçe prospektüs referansını aç',value=False)
        if use_pdf:doc=tr.load(index)
    else:
        st.caption('Hasta verisi yüklemeyin. PDF dış servise gönderilmez; OCR ve otomatik API yok.')
        uploaded=st.file_uploader('Prospektüs PDF yükle',type=['pdf'])
        if uploaded:
            try:
                result=data.upload(uploaded.getvalue(),uploaded.name);index=result['index'];doc=result['document']
                if index is None:st.info('UNVERIFIED · Yeni belge kimliği ve etkin maddesi kesinleştirilmedi. GNN NOT_SUPPORTED.')
            except Exception:
                st.error('PDF açılamadı: biçim/şifre,20 MB,120 sayfa veya2 milyon karakter sınırını kontrol edin.');doc=None
    st.divider();st.caption('OFFLINE · API kapalı · yeni model/eğitim yok')
    st.caption('Bireysel hastada klinik yan etki olasılığı veya tedavi önerisi değildir.')
bundle=None
if index is not None:
    try:bundle=data.recorded(data.PARENTS[index])
    except Exception:st.error('Kayıtlı tahmin veya kaynak hash kontrolü başarısız.');st.stop()
tabs=st.tabs(['1 · İLAÇ VE BELGE','2 · YAN ETKİ TAHMİNLERİ','3 · MODEL AÇIKLANABİLİRLİĞİ','4 · PROSPEKTÜS KARŞILAŞTIRMASI'])
with tabs[0]:
    if index is not None:
        r=tr.load(index)['record'];st.subheader(r['product']);st.write(r['composition'])
        st.info('Ana etkin madde araştırma bağlantısı: '+r['parent_id']+' · Ticari ürün/tuz/doz eşdeğerliği NOT_ESTABLISHED.')
    if doc is None:st.write('PDF referansı kapalı veya yüklenmedi. Kayıtlı tahminler PDF olmadan da ikinci bölümde görüntülenir.')
    else:
        st.write('**Belge:** '+doc.get('record',{}).get('product',doc.get('display_name','Yüklenen PDF')))
        st.write(f"**Fiziksel sayfa:** {doc['page_count']} · **Metin katmanı:** {sum(p['status']=='TEXT_AVAILABLE' for p in doc['pages'])} sayfa")
        st.warning('Belge güncelliği doğrulanmadı. Kaynak/hash doğrulaması klinik onay değildir. İnsan incelemesi PENDING.')
        with st.expander('Belge teknik ayrıntıları ve sayfa metinleri'):
            st.code(doc['sha256']);n=st.number_input('Fiziksel sayfa',1,doc['page_count'],1)
            p=doc['pages'][n-1];st.caption(p['status']);st.text(p['text'] or 'OCR_NOT_AVAILABLE — Metin katmanı yok.')
            st.download_button('Kaynak izini JSON indir',json.dumps(doc,ensure_ascii=False,indent=2),'yerel_belge_kaydi.json','application/json')
with tabs[1]:
    st.subheader('Ana etkin madde araştırma tahmini')
    st.caption('A1P1 · Kayıtlı primary own-fold outer-test OOF · SIDER observed-record proxy. Skor klinik olasılık yüzdesi değildir; unknown gerçek negatif değildir.')
    if bundle:
        predictions=pd.DataFrame(bundle['predictions']);predictions.insert(0,'Sıra',range(1,len(predictions)+1))
        names={r['class_id']:r['target_name'] for r in bundle['predictions']}
        def target_label(p):return explain.TR_PT.get(p,names[p])+' · '+names[p]+' · '+p
        available=explain.available(bundle['parent'])
        choices=sorted(set(names)&(set(available['shap'])|set(available['graph'])))
        def pick_example():st.session_state['final_pt_'+bundle['parent']]=st.session_state['example_'+bundle['parent']]
        st.selectbox('Açıklanabilir örnekler',choices,format_func=target_label,key='example_'+bundle['parent'],on_change=pick_example)
        pt=st.selectbox('Tahmin hedefi (PT)',list(names),index=list(names).index('C0000731') if 'C0000731' in names else 0,format_func=target_label,key='final_pt_'+bundle['parent'])
        st.caption('İki örnek PT için Türkçe gösterim editoryaldir; onaylı MedDRA çevirisi veya PDF–PT eşlemesi değildir. Diğer özgün hedef adları korunur.')
        shown=predictions.rename(columns={'target_name':'Dondurulmuş PT adı','class_id':'PT CUI','score_observed_record_proxy':'Kayıt sıralama skoru'})
        st.dataframe(shown[['Sıra','Dondurulmuş PT adı','PT CUI','Kayıt sıralama skoru']],hide_index=True,width='stretch',height=390)
        st.bar_chart(predictions.head(10).set_index('target_name')['score_observed_record_proxy'],horizontal=True)
        st.caption('Grafik kayıtlı sıralamanın ilk10 hedefidir. PT adları özgün frozen sözlüktür; Türkçe klinik terminoloji eşlemesi yapılmadı.')
        with st.expander('Tahmin kilidi, fold ve model sürümü'):
            st.json({'ana_etkin_madde':bundle['parent'],'outer_fold':bundle['fold'],'model':bundle['model'],'sürüm':bundle['version'],'hedef_sayısı':len(predictions),'seçili_PT':pt})
            st.json(data.read(data.Q/'data_pins.json'))
    else:pt=None;st.info('NOT_SUPPORTED — Bu belge için doğrulanmış kayıtlı ilaç/OOF bağlantısı yok. PDF yüklemek yeni GNN tahmini üretmez.')
with tabs[2]:
    st.subheader('Model bu skoru hangi bilgilere dayanarak verdi?')
    if bundle and pt:
        row=predictions[predictions.class_id.eq(pt)].iloc[0]
        st.markdown('### '+explain.TR_PT.get(pt,names[pt])+' · '+names[pt])
        c1,c2=st.columns(2);c1.metric('İlaç–PT ilişki skoru (A1P1)',str(row.score_observed_record_proxy));c2.metric('Kayıt sıralamasındaki yeri',str(row['Sıra']))
        st.caption('SIDER observed-record proxy; klinik sıklık veya kalibre edilmiş hasta riski değildir. Unknown çiftler gerçek negatif değildir.')
    with st.expander('1 · Modelin kullandığı girdiler'):
        st.write('A1P1: kimya5, QC maskeli atom44/bağ14 grafı, protein56, dört ayrı rol ve strict insan PPI700. B1: beş kimyasal tanımlayıcı ve ayrı kimya maskesi. Train-only scaler; PDF yan etkileri model girdisi değildir. Bu liste seçili PT için attribution veya biyolojik gerekçe değildir.')
    st.markdown('#### 2 · Bu ilaç–PT için mevcut sayısal açıklama')
    if bundle and pt:
        a=explain.get(bundle['parent'],pt,bundle['fold'])
        if a['absent_paths']:
            with st.expander('NA: kaynakta bulunmayan rol/PPI yolları (sıfır etki değil)'):st.dataframe(pd.DataFrame(a['absent_paths']),hide_index=True)
        if a['graph']:
            g=pd.DataFrame(a['graph']);fixed=g[g['mode']=='fixed'];valid=fixed[fixed.status.eq('OK')].copy()
            st.markdown('**A1P1: tekil mesaj maskesi, orijinal payda sabit**')
            if len(valid):
                valid['Mutlak etki']=valid.delta_z.abs();plot=valid.sort_values('Mutlak etki',ascending=False).head(8).copy()
                plot[['role','protein_id','protein_a','protein_b']]=plot[['role','protein_id','protein_a','protein_b']].fillna('')
                plot['Yol']=plot.apply(lambda r:str(r.get('role',''))+' '+str(r.get('protein_id',''))+' '+str(r.get('protein_a',''))+' '+str(r.get('protein_b','')),axis=1)
                st.bar_chart(plot.set_index('Yol')['delta_z'],horizontal=True)
                st.write(f"Gösterilen {len(plot)} bağlantı en büyük mutlak Δz değerlerine göre seçildi; tüm bağlantılar ayrıntı tablosundadır. Pozitif Δz maskelenince logitin azaldığını, negatif Δz arttığını gösterir. Etkiler toplamsal nedenler değildir.")
                for r in plot.head(3).to_dict('records'):st.write(r['Yol']+': '+explain.delta_sentence(r))
            else:st.info('NA — Uygulanabilir mesaj yolu yok; sıfır etki anlamına gelmez.')
            with st.expander('Gerçek fixed-degree katkıları, kaynak kimlikleri ve NA durumları'):st.dataframe(fixed,hide_index=True,width='stretch')
            with st.expander('Ayrı duyarlılık: physical-delete / yeniden normalizasyon'):
                deletion=g[g['mode']!='fixed'];st.dataframe(deletion,hide_index=True,width='stretch')
                if len(deletion):st.write(explain.delta_sentence(deletion.iloc[0].to_dict()))
        else:st.info('NOT_AVAILABLE — Bu ilaç/PT/fold için uygulanabilir kayıtlı mesaj müdahalesi yok. Genel girdilerden özel PT gerekçesi üretilmedi.')
        if a['shap']:
            s=pd.DataFrame(a['shap']);st.markdown('**B1 kimyasal LR: ayrı modelin SHAP logit açıklaması**')
            st.bar_chart(s.set_index('feature')['SHAP_logit'],horizontal=True)
            st.write(f"Bu grafikteki {len(s)} B1 özelliğinde pozitif katkı eğitim background’una göre logiti artırıcı, negatif katkı azaltıcıdır. A1P1 skorunun açıklaması veya klinik risk yüzdesi değildir.")
            for r in s.to_dict('records'):st.write(explain.shap_sentence(r))
            with st.expander('B1 SHAP sayısal değerler ve kimlikler'):st.dataframe(s,hide_index=True,width='stretch')
        else:st.info('NOT_AVAILABLE — B1’in bu fold/ilaç için fit edilmiş başlığında veya kaydedilmiş açıklamalarında hedef yok; başka PT/fold verisi doldurulmadı.')
    st.markdown('#### 3 · Biyolojik mekanizma')
    st.write('NOT_ESTABLISHED — Bağımsız mekanizma kanıtı yok. Mesaj etkisi veya SHAP, kanıtlanmış advers reaksiyon mekanizması değildir.')
with tabs[3]:
    st.subheader('Prospektüs referansı — tahminden ayrı kol')
    st.caption('Retrospektif, keşifsel kaynak incelemesi; dış klinik doğruluk veya yeni prospektif kör test değildir. Prospektüste geçmeyen PT gerçek negatif veya kesin yanlış tahmin sayılmaz.')
    if doc and index is not None:
        rows=doc['candidates'];byid={c['candidate_id']:c for c in rows}
        cid=st.selectbox('Prospektüs bulgusu (model tahmini değil)',list(byid),format_func=lambda k:tr.candidate_label(byid[k]),key='source_'+doc['sha256'])
        c=byid[cid];v=data.source_view(c)
        st.subheader(c['name_tr']);st.write('**İlgili tam kaynak terimi:** '+v['term'])
        st.caption(f"Fiziksel sayfa {v['page']} · yalnız seçili terim aralığı [{v['start']}, {v['end']})")
        st.write('**Kaynağın sıklık ifadesi:** '+tr.norm(v['frequency']));st.write('**Kapsam:** '+v['scope']+' · PENDING')
        if v['note']:st.info(v['note'])
        for q in c['context_quotes']:
            with st.expander('İlgili uyarı / koşul · sayfa '+str(q['physical_page'])):st.text(q['quote_exact'])
        with st.expander('Prospektüsteki tam bölüm'):st.text(v['full_section'])
        with st.expander('Kaynak teknik ayrıntıları'):st.json(c)
        st.dataframe(pd.DataFrame(data.comparison(doc)),hide_index=True,width='stretch')
        st.info('UNMAPPED — Türkçe terim→PT uzman eşlemesi henüz onaylanmadı. Aynı ad benzerliğiyle otomatik eşleme veya doğruluk hesabı yapılmadı.')
        st.caption('Aşırı doz ve hayvan çalışmaları bu aday listesine katılmaz. Ticari ürün ile ana etkin madde eşdeğerliği kurulmadı. Kayıtlı Türkçe LLM açıklaması NOT_AVAILABLE; yeni API yok.')
    elif doc:
        st.warning('EXPERIMENTAL / UNVERIFIED — Genel doğrulanmış yan etki çıkarıcısı yok; yalnız anahtar sözcük çevresi kaynak pencereleri.')
        for w in result['windows']:
            with st.expander('Aday kaynak penceresi · sayfa '+str(w['physical_page'])):st.text(w['quote'])
        if not result['windows']:st.info('NOT_AVAILABLE / OCR_NOT_AVAILABLE — Destekli metin penceresi bulunamadı; yan etki yokluğu anlamına gelmez.')
    else:st.info('Referans incelemesi için Türkçe prospektüsü açın veya PDF yükleyin. Tahmin kolu bundan bağımsızdır.')
