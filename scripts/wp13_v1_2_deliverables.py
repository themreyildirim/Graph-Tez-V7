"""Offline tables, teaching notebook and preservation evidence for WP13 v1.2."""
import json, hashlib, sys
from pathlib import Path
import pandas as pd
import wp13_presentation_v1_2 as m
ROOT=Path(__file__).resolve().parents[1]
Q=ROOT/'reports/qa/WP13/v1_2'
F=ROOT/'reports/figures/WP13/v1_2'

def write_json(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)

def tables():
    counts=[];alloc=[];repeats=[];editorials=[]
    for filename in ['pil.502.pdf','050641Orig1s032lbl.pdf']:
        doc=m.core.verified_document(filename);rows=m.known(doc);s=m.counts(rows)
        counts.append({'drug':doc['record']['existing_parent_name'],'filename':filename,
            **{k:v for k,v in s.items() if k not in ['scope_counts','source_key_counts','repeated_terms']},
            **{scope:s['scope_counts'].get(scope,0) for scope in ['product_specific','drug_direct','class_level']}})
        alloc.extend({'filename':filename,'source_key':k,'records':n} for k,n in s['source_key_counts'].items())
        repeats.extend({'filename':filename,**r} for r in s['repeated_terms'])
        editorials.extend({'filename':filename,**m.editorial(c),'physical_page':c['physical_page'],
            'source_term':c['source_term'],'scope':c['scope'],'source_exact':c['quote_exact'],
            'context_quotes':c['context_quotes']} for c in rows)
    for name,rows in [('candidate_count_summary',counts),('source_key_allocation',alloc),('repeated_terms',repeats),('editorial_translations',editorials)]:
        write_json(Q/(name+'.json'),rows);pd.DataFrame(rows).to_csv(Q/(name+'.csv'),index=False,encoding='utf-8-sig')
    a=json.loads((Q/'blind_audit.json').read_text(encoding='utf-8'))
    df=pd.DataFrame(a['fold_checks'])
    summary=df.groupby(['package','protocol','model'],as_index=False).agg(outer_models=('job_key','size'),OOF_drugs=('OOF_drugs','sum'),OOF_rows=('OOF_rows','sum'),min_fold_targets=('OOF_targets','min'),max_fold_targets=('OOF_targets','max'))
    summary.to_csv(Q/'OOF_scope_summary.csv',index=False,encoding='utf-8-sig')
    features=[
      ['DrugBank kimliği / tuz / formülasyon','Kaynak kayıt + açık kimlik kontrolü','Evet; eşdeğerlik ayrıca doğrulanır','Birleştirme/salt varsayımı yok','Metadata; sayısal ezberleme girdisi değil'],
      ['MW, LogP, HBD, HBA, TPSA + maske','WP04 QC / doğrulanmış yapı','Evet; yan etki etiketinden bağımsız','İlgili outer train scaler; yeni ilaçta refit yok','B1/B2/WP09/WP10'],
      ['Atom44 / bağ14 / stereo','WP04 SMILES + sabit WP10 şema','Evet; yapı kaynağı/QC gerekir','Sabit şema; QC54 açık/8 kapalı korunur','WP10; mevcut builder frozen62 dışında reddeder'],
      ['56 protein özelliği','WP05 temiz standart amino asit dizileri','Dizi ve kimlik doğrulanmışsa','Outer train protein fit evreni ve scaler','kalite_skoru yasak'],
      ['Target/enzyme/transporter/carrier','DrugBank kaynak ilişkileri','Kaynakta varsa; bilinmeyen uydurulmaz','Train grafına heldout ilaç/ters ilişki eklenmez','B2 rol özeti; WP09/WP10 dört ayrı readout'],
      ['İnsan PPI700','WP06 strict aynı-taxID STRING','Etiketten bağımsız dış bağlam','Sabit train protein cache; query grafı değiştirmez','23 E.coli ve80 özelliksiz context hariç'],
      ['PT hedef sözlüğü','Kilitli ilgili outer-train seçimi','Çıkış uzayı; girdi değil','>=5 kullanılabilir pozitif ilaç / >=2 grup train-only','Dış ilaç için yeni head/PT eklenmez'],
      ['Prospektüs yan etkileri / SIDER test etiketleri','PDF / değerlendirme referansı','GİRDİ OLARAK YASAK','Tahmin ve yöntem hash kilidinden sonra karşılaştırma','Yokluğu gerçek negatif değil'],
      ['PT/kategori sayısı, rapor sıklığı, SHAP/Δz, hedef skorları','Hedeften türetilen bilgi','GİRDİ OLARAK YASAK','Baseline referans B0 değişmez; özellik yapılmaz','Sızıntı önleme']]
    pd.DataFrame(features,columns=['alan','kaynak','tahmin_aninda_bilinebilirlik','fit_ve_izolasyon','sinir']).to_csv(Q/'prediction_input_leakage_matrix.csv',index=False,encoding='utf-8-sig')
    write_json(Q/'browser_checks.json',{'app':'drug_safety_explorer_v1_2.py','url':'http://127.0.0.1:8504','actual_browser':True,
      'picker_changes_candidate_and_source':'PASS','table_Glossit_updates_picker_and_detail':'PASS',
      'same_Glossit_ID_in_explanation_tab':'PASS','BUN_Turkish_exception':'PASS','class_scope_visible':'PASS',
      'unknown_frequency_hearing_usually':'PASS','uncovered_Glossit_NO_saved_LLM':'PASS',
      'original_English_expander':'PASS','new_upload_browser_test':'NOT_RUN_THIS_REVISION',
      'human_editorial_review':'PENDING','new_API_requests':0})
    print(summary.to_string(index=False))

def notebook():
    from wp09_close_wp10_notebooks import execute,INIT
    execute('WP13_demo_v1_2.ipynb',[
      ('md','''# WP13 v1.2 — Kaynaklı Türkçe sunum ve kör tahmin fizibilitesi

Bu notebook yalnız mevcut gerçek kayıtları okur. Eğitim, API veya yeni tahmin yoktur. Türkçe özetler **source-bound editorial translation**, kayıtlı LLM yanıtı değildir. İnsan incelemesi **PENDING** kalır.

## Neden iki ilaçta da 34 satır?
Sınırlı v1.1 sözlük, seçilmiş gerçek kaynak pasajlarında terim arar. 34, klinik olarak doğrulanmış yan etki sayısı veya eksiksiz prospektüs taraması değildir.'''),
      ('code',INIT+r'''
Q=ROOT/'reports/qa/WP13/v1_2';F=ROOT/'reports/figures/WP13/v1_2'
counts=pd.read_csv(Q/'candidate_count_summary.csv');display(counts)
display(pd.read_csv(Q/'source_key_allocation.csv'));display(pd.read_csv(Q/'repeated_terms.csv'))
fig,ax=plt.subplots(figsize=(9,4))
counts.set_index('drug')[['records','unique_source_terms','unique_Turkish_names']].plot.bar(ax=ax,color=['#247c91','#69a7ac','#d6ad62'],rot=0)
ax.set(title='Gerçek kaynak kayıtları: satır ≠ bağımsız klinik kanıt',ylabel='Sınırlı sözlük eşleşme sayısı');plt.tight_layout()
plt.savefig(F/'07_actual_candidate_counts.png',dpi=160);plt.show()
'''),
      ('md','''**Yorum:** Erythromycin34 terim/34 Türkçe ad; Doxycycline34 satır/33 terim/33 ad. Doxycycline'de ishal hem doğrudan ilaç hem sınıf kapsamında geçer. Bu iki satır bağımsız doğrudan ilaç kanıtı değildir; kaynağı silmeden kapsam ayrı tutulur.'''),
      ('code',r'''
editorial=pd.read_json(Q/'editorial_translations.json')
display(editorial[editorial.source_term.str.contains('BUN|reversible loss of hearing|glossitis',case=False)][['name','scope','frequency_tr','condition_tr','physical_page','source_quote_id','source_exact','review']])
display(pd.read_json(Q/'browser_checks.json',typ='series').to_frame('gerçek_tarayıcı_kontrolü'))
'''),
      ('md','''**Yorum:** BUN istisnası böbrek işlevi bozulmuş hastalara ilişkin cümleyi korur. Sıklığı bilinmeyen kayıt nadir/yaygın yapılmaz. İngilizce asıl kanıt açılır bölümde; editoryal metin ve eski PENDING LLM yanıtı ayrıdır. Glossit için başka adayın LLM metni iliştirilmez.

## OOF tahmin gerçekten eğitim dışında mı?'''),
      ('code',r'''
display(pd.read_csv(Q/'OOF_scope_summary.csv'))
checks=pd.read_csv(Q/'OOF_fold_isolation_checks.csv')
display(checks.groupby('package')[['drug_disjoint','group_disjoint','transform_train_only','target_train_only']].all())
display(pd.read_csv(Q/'OOF_demo_drug_checks.csv').query("package == 'WP10' and model == 'A1P1' and protocol == 'primary'"))
display(pd.read_csv(Q/'prediction_input_leakage_matrix.csv'))
'''),
      ('md','''**Yorum:** 110 final outer model/fold bağlamı ve ilgili hash/split/fit kayıtları denetlendi. Her ilaç yalnız kendi test fold'unun modeli için eğitim dışıdır; diğer fold modellerinde eğitimde olabilir. Train/query NPZ ayrımı ve scaler fit kimlikleri kontrol edildi. Bu salt okunur kayıt denetimi yeni performans veya evrensel sızıntısızlık kanıtı değildir.

62 ilaç dışı uçtan uca inference adapter'ı henüz yoktur. WP10 builder frozen62 dışındaki kimliği reddeder. B1 sayısal fonksiyonu uygun bir vektörü hesaplayabilir; bu, yeni ilaç kimliği/özellik/QC/preprocessing doğrulamasını sağlamaz. Şimdilik yalnız geçmiş OOF için sınırlı, retrospektif kör kaynak karşılaştırması tasarlanabilir; gerçek dış validasyon değildir.

## Gerçek çalışan arayüzden kanıt'''),
      ('code',r'''
from IPython.display import Image
for name in ['01_erythromycin_Turkish_summary.jpg','05_BUN_editorial_and_saved_LLM.jpg','06_Glossit_no_saved_explanation.jpg']:
    display(Image(filename=str(F/name),width=520))
'''),
      ('md','''**Yorum:** Görseller çalışan localhost8504 tarayıcısından alınmıştır; temsili UI veya sentetik skor yoktur. Dar tarayıcı görünümü nedeniyle bazı ekranlar kaydırılmış ayrıntı görünümleridir. Teknik UI başarısı WP12 semantik başarı oranı değildir. Yeni dış antibiyotik denemesi başlatılmadı; insan değerlendirmesi bekleniyor.''')])

if __name__=='__main__':
    if '--tables' in sys.argv:tables()
    if '--notebook' in sys.argv:notebook()
