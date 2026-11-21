"""Offline presentation of locked data only; no model/SHAP/API execution."""
import json
import re
from pathlib import Path
import pandas as pd
import streamlit as st
import wp13_external_reference_v1 as r

LABELS={
 'TABLE_TRANSLATION_CANDIDATE':'Tabloda çeviri/eşanlam adayı · PROVISIONAL',
 'TABLE_RELATED_NOT_EQUIVALENT':'Tabloda ilişkili terim · eşdeğerlik kurulmadı',
 'CLASS_WARNING_ONLY':'Yalnız sınıf uyarısı · ürün yan etkisi olarak doğrulanmadı',
 'DRUG_WARNING_ONLY':'İlaca ait uyarı · 4.8 tablo kaydı değil',
 'NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE':'Çapraz eşleme saptanmadı · negatif değil'}

def load():
    r.verify_locks()
    r.verify_pins(r.read(r.Q/'presentation_pins.json'))
    return pd.read_csv(r.Q/'comparison201.csv',float_precision='round_trip'),r.read(r.Q/'reference_terms.json'),r.read(r.Q/'context_quotes.json')

def render():
    try: frame,terms,ctx=load()
    except Exception:
        st.error('HASH_CHECK_FAILED — Kayıtlı kilit veya karşılaştırma kaynağı doğrulanamadı.'); st.stop()
    st.header('Tedizolid dış tahmin deneyi')
    st.caption('DB14569 aktif tedizolid · Beş frozen primary B1 kimya modeli · Sonradan açılan SIVEXTRO KÜB referansı')
    st.info('Tahmin kolu: DrugBank SMILES → 5 kimyasal özellik + ayrı maske → frozen train-only scaler/LR → kilitli skorlar ve SHAP. PDF bu kola girdi değildir.')
    st.warning('Keşifsel, etiketlerden izole tek dış ilaç. Önceki arama parçacığı maruziyeti nedeniyle tam araştırmacı körlüğü korunmadı. Skorlar klinik yan etki olasılığı değildir.')
    c=st.columns(4)
    for col,label,value in zip(c,['Kilitli ortak PT','Önceden seçilen PT','Ayrı model/PT açıklaması','KÜB tablo terimi'],[201,10,50,len(terms)]):col.metric(label,value)
    st.caption('76 tablo terimi klinik olarak doğrulanmış 76 bağımsız olay demek değildir. İnsan/uzman eşleme kararı PENDING; başarı yüzdesi hesaplanmadı.')
    top=frame.head(10).copy();top['Kaynak durumu']=top.reference_status.map(LABELS)
    st.subheader('Kilitli ilk 10 hedef — seçim KÜB görülmeden yapıldı')
    labels={'rank':'Sıra','term_tr_editorial':'Model hedefi (PT)','record_ranking_score':'İlişki skoru','source_terms':'KÜB terimi','frequencies':'Sıklık','source_scopes':'Kaynak kapsamı','Kaynak durumu':'Eşleme durumu','source_pages':'Sayfa','human_review':'İnsan incelemesi'}
    display=top[list(labels)].rename(columns=labels).copy()
    absent=top.reference_status.eq('NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE')
    display.loc[absent,'KÜB terimi']='Bu belgede doğrulanmış eşleme bulunamadı'
    display['İlişki skoru']=display['İlişki skoru'].map(lambda x:f'{x:.3f}')
    display['İnsan incelemesi']='Bekliyor'
    display['Kaynak kapsamı']=display['Kaynak kapsamı'].fillna('—').str.replace('PRODUCT_POOLED_ORAL_IV','Ürün · oral/IV havuzu',regex=False).str.replace('CLASS','Sınıf',regex=False)
    st.dataframe(display.fillna('—'),hide_index=True,width='stretch',height=392)
    byid=top.set_index('class_id')
    pt=st.selectbox('İncelenecek kilitli PT',list(top.class_id),format_func=lambda x:byid.loc[x,'term_tr_editorial']+' · '+x,key='tedizolid_reference_PT')
    row=byid.loc[pt]; left,right=st.columns([1,1],gap='large')
    with left:
        st.subheader('Kayıtlı B1 tahmini ve açıklaması')
        st.markdown('### Tedizolid · '+row.term_tr_editorial)
        st.caption(f'Kilitli sıralama: {int(row["rank"])} / 201')
        st.metric('Beş sigmoid skorunun eşit ağırlıklı ortalaması',f'{row.record_ranking_score:.3f}')
        st.caption('Klinik risk yüzdesi, görülme sıklığı veya kalibre edilmiş olasılık değildir.')
        st.dataframe(pd.DataFrame({'Frozen primary model':range(1,6),'Kayıt sıralama skoru':[round(row[f'fold{i}_score'],4) for i in range(1,6)]}),hide_index=True,width='stretch')
        values=pd.read_csv(r.S/'local_feature_SHAP.csv',float_precision='round_trip')
        verbal=r.read(r.S/'Turkish_verbal_explanations.json');pairs=pd.read_csv(r.S/'pair_additivity.csv',float_precision='round_trip')
        fold=st.selectbox('SHAP açıklaması için bireysel model',[1,2,3,4,5],key='tedizolid_shap_fold')
        sub=values[values.class_id.eq(pt)&values.fold.eq(fold)]
        st.bar_chart(sub.set_index('feature_name_tr')['SHAP_logit'],horizontal=True,color='#247c8d')
        original_verbal=next(v['explanation_tr'] for v in verbal if v['class_id']==pt and v['fold']==fold)
        st.markdown("**SHAP’ın açıkladığı şey**")
        for sign,label in [(1,'artıran'),(-1,'azaltan')]:
            z=sub[sub.SHAP_logit*sign>0].sort_values('SHAP_logit',ascending=sign<0)
            if len(z):
                v=z.iloc[0];st.write(f"Model {fold} için logiti en çok {label} özellik: {v.feature_name_tr} ({v.SHAP_logit:+.4f}).")
            else:st.write(f"Bu kayıtta logiti {label} katkı yok.")
        with st.expander('Tam hassasiyette özgün model yorumu'):st.write(original_verbal)
        st.caption('Pozitif/negatif katkı bu B1 modelinin logitini train background’una göre artırır/azaltır. Kimya maskesi ayrı değişkendir; biyolojik mekanizma kanıtı değildir. Ortak skor ortalamasının ensemble SHAP’ı değildir.')
        with st.expander('Beş modelin mevcut SHAP grafiği ve değerleri'):
            st.image(str(r.ROOT/f'reports/figures/WP13/tedizolid_B1_SHAP_v1/PT{int(row["rank"]):02d}_{pt}_five_models.png'))
            st.dataframe(values[values.class_id.eq(pt)],hide_index=True)
            st.dataframe(pairs[pairs.class_id.eq(pt)],hide_index=True)
    with right:
        st.subheader('Tahmin kilidinden sonra açılan KÜB')
        st.write('**Ürün:** SIVEXTRO 200 mg/flakon tedizolid fosfat; intravenöz infüzyonluk liyofilize toz.')
        st.caption('Aktif tedizolid ile fosfat ön ilacı aynı moleküler girdi değildir. 4.8 güvenlilik verileri oral ve/veya IV havuzudur; yalnız IV insidansı değildir. Güncellik doğrulanmadı.')
        st.info(LABELS[row.reference_status]+' · İnsan incelemesi PENDING')
        matches=[m for m in r.read(r.Q/'crosswalk_candidates.json') if m['class_id']==pt]
        qlookup={t['quote']['quote_id']:t['quote'] for t in terms};qlookup.update({q['quote_id']:q for q in ctx})
        if not matches:
            st.write('Bu belgede doğrulanmış eşleme bulunamadı. Bu durum gerçek negatif veya kesin yanlış tahmin değildir. Aşırı duyarlılık, anafilaktik şok yerine geçirilmedi.')
        for match in matches:
            q=qlookup[match['quote_id']]
            st.markdown('**Kaynak terimi:** '+match['source_term'])
            st.write('**Sıklık:** '+match['frequency']+' · **Kapsam:** '+match['scope'])
            st.write(match['rationale_tr'])
            if match['source_channel']=='4.4_CLASS_WARNING':
                bridge=r.read(r.Q/'class_scope_bridge.json')
                st.caption('Sınıf kapsamı cümlesi önceki fiziksel sayfadan devam eder: '+bridge['quote_id'])
                st.text(bridge['quote_exact'])
            st.caption(f"Fiziksel sayfa {q['physical_page']} · {q['quote_id']} · [{q['char_start']}, {q['char_end']})")
            st.text(q['quote_exact'])
        with st.expander('Tam 4.8 bağlamı, sıklık başlıkları ve ürün farkı'):
            for q in r.read(r.Q/'complete_4_8_pages.json'):
                st.markdown('**Fiziksel sayfa '+str(q['physical_page'])+'**');st.text(q['quote_exact'])
        st.warning('PROVISIONAL çapraz eşleme, uzman onaylı MedDRA çevirisi değildir. Daha geniş/dar kavramlar, sınıf uyarıları ve laboratuvar düşüşleri doğrudan ürün yan etkisiyle birleştirilmez.')
    with st.expander('Tüm 201 PT, beş model skoru ve kaynak eşleme adayları'):
        st.dataframe(frame,hide_index=True,width='stretch');st.download_button('201 PT karşılaştırmasını CSV indir',(r.Q/'comparison201.csv').read_bytes(),'tedizolid_common201_reference.csv','text/csv')
    with st.expander('KÜB’deki tüm 76 tablo terimi — ilk10 dışında kalanlar dahil'):
        st.dataframe(pd.read_csv(r.Q/'all_reference_terms_target_coverage.csv'),hide_index=True,width='stretch')
        st.caption('Terim tekrarları ve alt türler bağımsız olay/başarı sayılmaz. Bulantı ve başka terimler ortak201’de eşlenemeyebilir; hedef kapsamı genişletilmedi.')
    with st.expander('Kilitler, kaynak kimliği ve yöntem sınırları'):
        st.code('Prediction SHA-256: '+r.PRED_HASH+'\nExplanation SHA-256: '+r.SHAP_HASH)
        st.json(r.read(r.Q/'product_identity_and_limitations.json'))
    st.caption('OFFLINE · Yeni eğitim, prediction forward, SHAP hesabı, API, OCR veya otomatik insan onayı yok.')
