"""WP08 hazırlık eki: yürütülmüş gerçek split/fit/graf kapsamı; başarım yok."""
from pathlib import Path
import os,io,base64
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP08 — Gerçek nested split ve deney öncesi hazırlık v1

WP08 kapanmadı. Bu ek, onaylanan protokol incelemesini değiştirmeden gerçek ID/fold listeleri, train sözlükleri, train-only sayısal dönüşümler ve yeni graf nesneleri üretir. **Sınıflandırıcı, tahmin skoru, AP/AUROC veya CI hesaplanmadı.**

Görev, yeni ilaçlarda gözlenen SIDER ilişkilerini sıralamaktır; klinik bireysel risk değildir. Önceki keşifte tüm 62 etiket dağılımı görüldü; değerlendirme ileride iç doğrulama olarak adlandırılmalıdır. Split ve seed, hedef dosyasını bu hazırlıkta açmadan önce kilitlendi.''')
    code('''from pathlib import Path
import json,sys,numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP08/experimental_preparation';FIG=ROOT/'reports/figures/WP08/experimental_preparation';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',130);pd.set_option('display.max_columns',22);pd.set_option('display.max_colwidth',100)
def read(n):return pd.read_csv(QA/n,keep_default_na=False)
summary=json.loads((QA/'preparation_summary.json').read_text(encoding='utf-8'));lock=json.loads((QA/'split_lock_v1.json').read_text(encoding='utf-8'))
display(pd.DataFrame([summary]).drop(columns=['protocols','feature_dimensions']))
display(pd.DataFrame([{'seed':lock['specification']['seed'],'outer':5,'inner':3,'kilit_SHA256':lock['specification_sha256'],'onay':'EĞİTİM BEKLİYOR'}]))''')
    md('''## 1. Connectivity kilitli dış 5-fold ve iç 3-fold

Atama grup büyüklüğüne göre dengelenir; eşit büyüklüklerde SHA256(seed|group_id) sırası kullanılır. Seed **20261106**, yalnız sabit tarih kodu seçimidir. İkinci seed denemesi veya hedef desteğine göre fold arama yapılmadı. Inner seed=20261106+100×outer_fold. Stress gruplaması, mevcut scaffold OR >=0,8 benzerlik bileşenidir; ana sonuç yerine daha iyi görünürse seçilmeyecek.''')
    code('''outer=read('outer_membership_v1.csv');parts=read('nested_partitions_v1.csv');contexts=read('context_summary.csv')
display(outer[outer.protocol.eq('primary')]);display(contexts)
names=pd.read_csv(ROOT/'reports/qa/WP07/drug_modality_QA.csv').set_index('drug_id').name.to_dict()
fig,axs=plt.subplots(1,2,figsize=(13,13))
for ax,protocol in zip(axs,['primary','stress']):
    f=outer[outer.protocol.eq(protocol)].sort_values(['outer_test_fold','group_id','drug_id'])
    grid=np.array([[1 if fold==r.outer_test_fold else 0 for fold in range(1,6)] for r in f.itertuples()])
    ax.imshow(grid,aspect='auto',cmap='Blues',vmin=0,vmax=1);ax.set_xticks(range(5),range(1,6));ax.set_yticks(range(62),f.drug_id,fontsize=6);ax.set(xlabel='Dış test fold',title=protocol+' • her ilaç bir kez test')
plt.tight_layout();plt.savefig(FIG/'01_frozen_outer_membership.png',dpi=160);plt.show()
display(parts[parts.context.eq('primary_o01_i01')])''')
    md('''**Yorum:** Gerçek outer test büyüklükleri 13/13/12/12/12; outer train 49/49/50/50/50. Inner train/validation/test ID'leri eksiksiz dosyadadır. Levofloxacin–Ofloxacin her outer ve inner bağlamda aynı tarafta kalır. Outer-final satırlarında validation boş olması beklenir; iç seçim daha sonra tamamlanınca son outer train fit'i yapılacaktır. 40 bağlam, iki protokol × (5 son outer fit + 15 inner fit) demektir; 40 eğitim çalıştırıldığı anlamına gelmez.

## 2. PT destek kuralı: train ilaç ve grup desteği''')
    code('''vocab=read('vocabulary_counts.csv');supports=read('train_PT_support.csv')
final=vocab[vocab.protocol.eq('primary') & vocab.inner_fold.eq(0)];display(final)
display(supports[supports.context.eq('primary_o01_final')].head(16))
pivot=final.pivot(index='outer_fold',columns='scope',values='PT_classes')[['cohort','B1','B2','paired']]
fig,ax=plt.subplots(figsize=(10,5));pivot.plot.bar(ax=ax);ax.set(ylabel='Train seçilmiş PT CUI',title='>=5 pozitif train ilacı ve >=2 train grup • başarım değil');plt.tight_layout();plt.savefig(FIG/'02_train_vocabularies.png',dpi=160);plt.show()
inner=vocab[vocab.protocol.eq('primary') & vocab.inner_fold.gt(0) & vocab.scope.eq('paired')].pivot(index='outer_fold',columns='inner_fold',values='PT_classes');display(inner)''')
    md('''**Yorum:** 5/2 kuralı sonuç başarımına bakılmadan düşük destek ve tek grup bağımlılığını sınırlayan operasyonel adaydır; istatistiksel güç veya klinik geçerlilik garantisi değildir. Kohort train sözlüğü ayrıca saklanır. B1/B2 için kullanılabilir inputu olan train ilaçlarında destek yeniden sayılır; eşleştirilmiş hedefler iki model sözlüğünün train-only kesişimidir. Bu payda ayrıntısı son onay tablosunda açıkça belirtilir. Outer train sözlüğü inner validation desteğine kopyalanmaz; her inner train yeniden kendi sözlüğünü belirler.

Test etiketleri sözlüğü genişletemez. Seçili sözlük dışındaki test pozitiflerinin kapsamı ileride ayrıca raporlanmalı; sınıf elemesini metrik yükseltme yöntemi gibi yorumlamamalıyız. Tarihsel 30 değişmeyen, semantik uyarılı ayrı karşılaştırmadır.

## 3. Model bazlı girdi kapsamı ve abstention''')
    code('''eligible=read('prediction_eligibility.csv');display(eligible)
coverage=eligible.groupby('model').agg(kohort=('drug_id','nunique'),tahmine_girdi_uygun=('eligible','sum'));coverage['abstention']=coverage.kohort-coverage.tahmine_girdi_uygun;display(coverage)
fig,ax=plt.subplots(figsize=(9,5));coverage[['tahmine_girdi_uygun','abstention']].plot.bar(stacked=True,ax=ax,color=['#5f9c83','#c28a76']);ax.set(ylabel='İlaç / sabit 62',title='Girdi uygunluğu • tahmin başarımı veya üretilmiş skor değil');plt.tight_layout();plt.savefig(FIG/'03_abstention_coverage.png',dpi=160);plt.show()
display(eligible[eligible.drug_id.isin(['DB06799','DB00684'])])''')
    md('''**Yorum:** B1 kimya-only için 54 ilaçta girdi var, sekiz inceleme molekülünde abstention var. B2 rol bazlı protein+kimya için 61 ilaçta en az bir dal var; **Methenamine için iki modelde de abstention** uygulanır. Tobramycin B2'de kimya dalıyla kalır. “Uygun” henüz skor üretildiği anlamına gelmez. 62 ID envanterde korunur; 53 complete-case yalnız duyarlılık alt grubudur. Maskeler kaynak girdisinden gelir, yan etki etiketinden türetilmez.

## 4. Train-only dönüşüm ve 4 ayrı protein rolü''')
    code('''fits=json.loads((QA/'transform_fit_sources_and_statistics.json').read_text(encoding='utf-8'));schema=json.loads((QA/'feature_schema_v1.json').read_text(encoding='utf-8'))
display(contexts[['context','chemistry_fit_drugs','protein_fit_accessions']]);display(pd.DataFrame([{'model':m,'alan_sayisi':len(cols),'ID_ve_PT_girdisi':False} for m,cols in schema['features'].items()]))
example='primary_o01_i01';fit=fits[example]
display(pd.DataFrame({'kimya_fit_drug_id':fit['chemistry_fit_drug_ids']}));display(pd.DataFrame({'protein_fit_accession':fit['protein_fit_accessions']}))
display(pd.DataFrame({'mean':fit['chemistry']['mean'],'scale':fit['chemistry']['scale']}))
arr=np.load(QA/'features'/(example+'.npz'),allow_pickle=False)
display(pd.DataFrame(arr['B2'][:5,:5],index=arr['drug_ids'][:5],columns=schema['features']['B2'][:5]))
fig,ax=plt.subplots(figsize=(11,4.8));c=contexts[(contexts.protocol.eq('primary')) & contexts.inner_fold.eq(0)];ax.plot(c.outer_fold,c.chemistry_fit_drugs,'o-',label='Kimya fit ilacı');ax.plot(c.outer_fold,c.protein_fit_accessions,'s-',label='Benzersiz train-linked protein');ax.set(xlabel='Dış fold',ylabel='Fit kaynak kaydı',title='Yalnız train kaynağı • farklı biyolojik birimler');ax.legend();plt.tight_layout();plt.savefig(FIG/'04_transform_fit_scope.png',dpi=160);plt.show()''')
    md('''**Yorum:** Gerçek dönüşüm istatistikleri fit edildi, sınıflandırıcı eğitilmedi. Kimya yalnız QC-onaylı train ilaçları, protein yalnız train ilacı ilişkilerindeki benzersiz accession'lar üzerinden standardize edilir. Test ilacının yalnız kendisinde bulunan proteini fit kaynağı olamaz; aynı protein train ilacında da varsa train kaynak olarak bulunması meşrudur.

B1: 5 kimya+1 maske=6 alan. B2: 5 kimya+4×56 ayrı rol özeti+5 availability maskesi=234 alan. Eksik dalda standardize edilmiş **nötr yer tutucu 0 ve açık maske** kullanılır; bu gerçek MW/AAC sıfırı veya eksik dizi doldurma değildir. Ham/clean kaynak eksikleri korunur; 80 context hiç eklenmez. Her rol önce train ölçeğine göre dönüştürülür, sonra o ilacın ilişkili proteinleri ortalanır. Kimlikler metadata'dadır. Bu yüksek boyut küçük örneklemde düzenlileştirme gerektirir; LR/MLP/RF seçimi eğitim onayında kalır.

## 5. Yeni train-only graflar ve metrik hesaplanabilirliği''')
    code('''display(contexts[['context','train_drugs','validation_drugs','test_drugs','train_graph_drugs','train_graph_proteins','train_graph_edges']])
display(read('graph_edge_counts.csv').head(12))
evaluation=read('metric_evaluability_NO_scores.csv');ev=evaluation[evaluation.context.isin(final.context) & evaluation.split.eq('test')];display(ev)
fig,ax=plt.subplots(figsize=(10,5));ev.pivot(index='context',columns='model',values='train_and_split_proxy_AUROC_possible_classes').plot.bar(ax=ax);ax.set(ylabel='Train ve test desteği uygun PT sınıfı',title='Skor veya AUROC sonucu değil • pozitif/unknown kayıt desteği');plt.xticks(rotation=30,ha='right');plt.tight_layout();plt.savefig(FIG/'05_metric_support_not_scores.png',dpi=160);plt.show()
display(read('proxy_trainability_NO_model_fit.csv').groupby(['context','model']).proxy_classifier_fittable_if_approved.agg(['size','sum']).head(10))
display(read('secondary30_evaluability_NO_scores.csv').head(10))''')
    md('''**Yorum:** 40 yeni graf, her bağlamın train ilaçlarını ve yalnız onların dört tip DrugBank ilişkisini içerir. WP07 `.pt` dosyaları kullanılmaz; validation/test drug düğümleri veya ileri/ters bağlantıları, PPI ve SE hedef kenarları yoktur. Train-linked protein evreni kullanılır; 141 proteinlik bütün-kohort registry veya 80 context'e otomatik genişleme yoktur. İleride query inferansı ayrı yapılmalıdır.

“Hesaplanabilir” sütunu sınıfta hem gözlenen pozitif hem unknown bulunduğunu söyler; unknown gerçek negatif değildir. Train'de yalnız tek proxy sonucu bulunan sınıfta LR fit'i de yapılamaz; bu sınıflar için önsel olasılık uydurulmadan NA planlandı. Seçilen 5/2 sözlüğü ile ikili proxy modelinin fit edilebilirliği ayrı dosyalardır. Sıfır pozitif veya bütün ilaçlarda pozitif olan test sınıfları ayırt edici proxy metriği için NA kalır. **Burada AP/AUROC değeri hesaplanmadı.** Gelecekte onaylanırsa AP/AUROC yalnız gözlenen kaynak kayıtlarını sıralayan proxy ölçüm olacak; klinik bireysel risk, gerçek negatif özgüllüğü veya biyolojik kalibrasyon olmayacaktır. Folda göre değişen sözlük kapsamları gizlenmeden raporlanmalıdır.

## 6. Model eğitimi öncesi tek kısa karar tablosu''')
    code('''display(read('final_pretraining_decisions.csv'))
gate=json.loads((QA/'training_gate.json').read_text(encoding='utf-8'));display(pd.DataFrame([gate]))
import plotly.graph_objects as go
f=outer[outer.protocol.eq('primary')].sort_values('drug_id')
heat=np.array([[int(r.outer_test_fold==i) for i in range(1,6)] for r in f.itertuples()]);hover=np.array([[r.drug_id+' '+names[r.drug_id]+' | '+r.group_id for i in range(5)] for r in f.itertuples()])
fig=go.Figure(go.Heatmap(z=heat,x=list(range(1,6)),y=f.drug_id,text=hover,hovertemplate='%{text}<br>Outer fold %{x}; test üyeliği=%{z}<extra></extra>',colorscale='Blues',showscale=False))
fig.update_layout(title='Kilitli connectivity outer fold kimlikleri • model sonucu değil',height=1400,width=1000)
fig.write_html(FIG/'frozen_fold_membership_interactive.html',include_plotlyjs=True,full_html=True)''')
    md('''**Kapanış:** Bu hazırlıkta gerçek split, train kaynaklı sözlük/standardizasyon ve train-only graf dosyaları üretildi. Negatif örnekleme, classifier fit, tahmin ve performans yoktur. Son karar tablosu [hazırlık raporunda](../reports/WP08_EXPERIMENTAL_PREPARATION.md) da bulunur. Kullanıcı model eğitimi ve kalan yöntem ayrıntılarını onaylamadan deney başlatılmaz. WP08 açık kalır, WP09'a geçilmez.

[Train-only dönüşüm için resmi açıklama](https://scikit-learn.org/stable/common_pitfalls.html), [AP tanımı](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [AUROC tanımı](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html).''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'Actual IPython; no model training'})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            buf=io.BytesIO();plt.figure(i).savefig(buf,format='png',dpi=100,bbox_inches='tight');display(Image(data=buf.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for i,c in enumerate(nb.cells):
        if c.cell_type=='code':compile(c.source,f'WP08 preparation cell {i}','exec')
    for c in nb.cells:
        if c.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:result=shell.run_cell(c.source,store_history=False)
        if result.error_in_exec or result.error_before_exec:raise RuntimeError(result.error_in_exec or result.error_before_exec)
        c.execution_count=n;c.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for o in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in o.data.items()}
            c.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=o.metadata))
    nbf.validate(nb);nbf.write(nb,ROOT/'notebooks/WP08_experimental_preparation.ipynb');print('Executed preparation code cells',n)


if __name__=='__main__':main()
