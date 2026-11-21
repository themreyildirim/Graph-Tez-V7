"""İlk baseline sonuçları: gerçek tablolar, gözlenen-kayıt proxy yorumları."""
from pathlib import Path
import os,io,base64
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP08 — İlk B1/B2 L2-lojistik regresyon baseline sonuçları

**Görev:** Yeni ilaçlarda SIDER'da gözlenen ilaç–yan etki kayıt ilişkilerini sıralamak. Binary proxy `s=1` kaynakta gözlenen kayıt; `s=0` kaydı olmayan çifttir. **Unknown doğrulanmış biyolojik negatif değildir. Klinik risk, özgüllük veya kalibrasyon iddiası yoktur.**

Bu notebook eğitim üreticisini yeniden çalıştırmaz. Kilitli connectivity 5×3 nested CV, seed 20261106, train-only 5 ilaç/2 grup PT sözlüğü, hazırlanmış dönüşüm ve eligibility dosyaları korunarak tamamlanan deneyin sonuçlarını okur. Ana protokol ve scaffold OR >=0,8 stres sonucu ayrı kalır. ATC/RF/MLP/PPI/context eklenmedi. Önceden keşfedilmiş 62 ilaçta iç doğrulamadır.''')
    code('''from pathlib import Path
import json,numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP08/baseline_v1';FIG=ROOT/'reports/figures/WP08/baseline_v1';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',170);pd.set_option('display.max_columns',22);pd.set_option('display.max_colwidth',100)
def read(n):return pd.read_csv(QA/n,keep_default_na=False)
run=json.loads((QA/'run_config.json').read_text(encoding='utf-8'));training=json.loads((QA/'training_complete.json').read_text(encoding='utf-8'))
display(pd.DataFrame([training]));display(read('environment.json') if False else pd.DataFrame([json.loads((QA/'environment.json').read_text(encoding='utf-8'))]))
display(read('fold_train_validation_test_scope.csv'))''')
    md('''## 1. C yalnız iç doğrulamayla seçildi

Her inner fold içinde aynı C adayları aynı kullanılabilir ilaçlar ve C'den bağımsız hedef kümesiyle karşılaştırılır. Farklı inner foldlarda sözlükler değişebilir; bu nedenle skorların görevi folda özgü train destek kuralına koşulludur. Üç geçerli foldun drug-macro AP ortalaması seçim ölçütüdür; NA sıfır sayılmaz. Eşitlikte küçük C. Tüm inner seçimler tamamlanıp hash'le kaydedilmeden outer test skorlanmadı.''')
    code('''selection=read('selected_C.csv');inner=read('inner_selection_metrics.csv');display(selection.drop(columns=['semantics']));display(inner.head(12).drop(columns=['semantics']))
grid=selection.assign(row=selection.protocol+'_outer_'+selection.outer_fold.astype(str),col=selection.family+'_'+selection.model).pivot(index='row',columns='col',values='selected_C')
fig,ax=plt.subplots(figsize=(10,7));im=ax.imshow(np.log10(grid.to_numpy(dtype=float)),cmap='viridis',vmin=-1,vmax=1,aspect='auto');ax.set_xticks(range(len(grid.columns)),grid.columns,rotation=20,ha='right');ax.set_yticks(range(len(grid)),grid.index)
for i in range(len(grid)):
    for j in range(len(grid.columns)):ax.text(j,i,f'{grid.iloc[i,j]:g}',ha='center',va='center',color='white' if grid.iloc[i,j]<1 else 'black')
ax.set_title('Yalnız inner observed-record drug-AP ile seçilen C');plt.tight_layout();plt.savefig(FIG/'01_inner_selected_C.png',dpi=160);plt.show()''')
    md('''**Yorum:** B2 her ana outer fold için C=0,1 seçti; B1'de seçim folda göre 0,1 veya 1. Bu sonuçtan sonra C aralığı genişletilmedi. 40.611 inner ve 6.133 outer tek-PT/kategori sınıflandırıcısı fit edildi; bunlar ilaç veya bağımsız deney sayısı değildir. 279 inner aday sınıf fit'i ve sekiz outer sınıf fit'i tek proxy sonucu nedeniyle yapılmadı. Yakınsama/fit hatası gözlenmedi. 400 parametre bundle'ı seçim iziyle saklandı.

## 2. Ana PT görevi: outer test fold sonuçları''')
    code('''folds=read('outer_fold_metrics.csv');display(folds[(folds.protocol=='primary') & (folds.family=='PT') & (folds.metric=='drug_macro_AP')].drop(columns=['semantics','CI95_low','CI95_high']))
fig,ax=plt.subplots(figsize=(10,5))
f=folds[(folds.protocol=='primary') & (folds.family=='PT') & (folds.scope=='paired54') & (folds.metric=='drug_macro_AP')]
for model,color in [('B1','#4d88b1'),('B2','#bb885d')]:
    a=f[f.model.eq(model)].sort_values('outer_fold');ax.plot(a.outer_fold,a.estimate,'o-',label=model,color=color)
ax.set(ylim=(0,1),xlabel='Kilitli outer test fold',ylabel='Observed-record drug-macro AP',title='Ortak ilaç ve train hedefleri • unknown biyolojik negatif değil');ax.legend();plt.tight_layout();plt.savefig(FIG/'02_outer_fold_PT_AP.png',dpi=160);plt.show()
display(read('outer_model_coverage.csv').drop(columns=['semantics']))''')
    md('''**Yorum:** Fold farkları küçük örneklem, input kapsamı ve train'den öğrenilen hedef sözlüğü farklarını birlikte yansıtır. Foldları bağımsız beş tekrar gibi test etmek doğru değildir; eğitim kümeleri örtüşür. Tek bir iyi/kötü fold seçilmedi. Bu grafiğe ayrı fold CI verilmedi; CI gerekçesi tabloda ve grup-resampled OOF özette belirtilir.

## 3. PT: kendi kapsamı, ortak 54 ve complete-case 53''')
    code('''metrics=read('oof_metrics_with_group_CI.csv');coverage=read('evaluation_coverage.csv')
display(metrics[(metrics.family=='PT')].drop(columns=['semantics','CI_interpretation']))
fig,axs=plt.subplots(1,2,figsize=(13,5),sharey=True)
for ax,protocol in zip(axs,['primary','stress']):
    f=metrics[(metrics.protocol==protocol)&(metrics.family=='PT')&(metrics.metric=='drug_macro_AP')]
    for model,offset,color in [('B1',-.1,'#4d88b1'),('B2',.1,'#bb885d')]:
        a=f[f.model.eq(model)].set_index('scope').loc[['own','paired54','complete_case53']];xx=np.arange(3)+offset
        ax.errorbar(xx,a.estimate,yerr=np.vstack([a.estimate-a.CI95_low,a.CI95_high-a.estimate]).astype(float),fmt='o',capsize=4,label=model,color=color)
    ax.set_xticks(range(3),['Kendi kapsamı','Ortak 54','Complete-case 53'],rotation=15);ax.set(title=protocol+' • sabit OOF koşullu grup CI',ylim=(0,1),ylabel='Observed-record drug-macro AP');ax.legend()
plt.tight_layout();plt.savefig(FIG/'03_PT_AP_group_CI.png',dpi=160);plt.show()
display(coverage[coverage.family.eq('PT')].drop(columns=['semantics']))''')
    md('''**Yorum:** Ana protokol ortak 54 ilaç/ortak train hedeflerinde B1 AP≈0,656, B2≈0,626. Kendi kapsamlarında B1 54, B2 61 ilaç skorlar; iki farklı kapsamın ham metrik farkı eşleştirilmiş kıyas değildir. Complete-case 53, aynı fit edilmiş modellerin test alt kümesi duyarlılığıdır; 53 ilaçla yeniden eğitilmiş ayrı model yoktur.

CI, 1000 kez kilitli yapısal grup örneklemesiyle sabit OOF tahminlerine koşulludur. İlaç–PT çiftleri veya foldlar bağımsız örneklenmedi. Bu aralık bütün tekrar eğitim/hiperparametre belirsizliğini veya yeni dış veri belirsizliğini kapsamaz. Farklı foldlarda farklı hedef sözlükleri olduğundan pooled micro/class ölçümler ragged kapsamlı, train-destek kuralına koşullu özetlerdir; sabit 1061-hedef başarımı gibi yorumlanmaz.

## 4. Tarihsel 30 ayrı karşılaştırmadır''')
    code('''hist=metrics[(metrics.family=='historical30') & (metrics.scope=='paired54')];display(hist.drop(columns=['semantics','CI_interpretation']))
fig,ax=plt.subplots(figsize=(10,5))
f=folds[(folds.protocol=='primary')&(folds.family=='historical30')&(folds.scope=='paired54')&(folds.metric=='drug_macro_AP')]
for model,color in [('B1','#4d88b1'),('B2','#bb885d')]:
    a=f[f.model.eq(model)].sort_values('outer_fold');ax.plot(a.outer_fold,a.estimate,'o-',label=model,color=color)
ax.set(ylim=(0,1),xlabel='Outer fold',ylabel='Observed-record drug-macro AP',title='Tarihsel 30 • semantik uyarılar korunur, klinik onay değil');ax.legend();plt.tight_layout();plt.savefig(FIG/'04_historical30_separate.png',dpi=160);plt.show()
display(coverage[coverage.family.eq('historical30')].drop(columns=['semantics']))''')
    md('''**Yorum:** Tarihsel 30 daha yoğun ve seçilmiş farklı bir etiket uzayıdır; PT ile sayısal AP farkı doğrudan daha iyi yöntem veya daha doğru klinik kategori anlamına gelmez. Renal impairment→Nefrotoksisite, birden fazla kavramın birleştirilmesi gibi önceki semantik uyarılar geçerlidir. Sulfanilamide'nin kategori pozitifinin olmaması gerçek negatiflik değildir; drug-AP desteği yoksa NA kalır.

## 5. Abstention, bilinmeyenler ve hesaplanamayan sınıflar''')
    code('''status=read('prediction_status_all62.csv');display(status[status.protocol.eq('primary')&status.family.eq('PT')].drop(columns=['semantics']))
display(read('fit_status_summary.csv').drop(columns=['semantics']))
cls=read('per_class_metrics.csv');display(cls[cls.protocol.eq('primary')&cls.family.eq('PT')&cls.AUROC.eq('')].head(12).drop(columns=['semantics']))
drug=read('per_drug_metrics.csv');display(drug[drug.protocol.eq('primary')&drug.family.eq('historical30')&drug.NA_reason.ne('')].head(12).drop(columns=['semantics']))
fig,ax=plt.subplots(figsize=(9,5));c=coverage[coverage.protocol.eq('primary')&coverage.family.eq('PT')&coverage.scope.eq('own')].set_index('model')
counts=pd.DataFrame({'Skorlanan':c.scored_drugs,'Skor yok / abstention':62-c.scored_drugs});counts.plot.bar(stacked=True,ax=ax,color=['#659e85','#c18d77']);ax.set(ylabel='İlaç / sabit 62',title='Tahmin kapsamı • Methenamine envanterde, skor yok');plt.tight_layout();plt.savefig(FIG/'05_prediction_coverage.png',dpi=160);plt.show()''')
    md('''**Yorum:** Methenamine için iki modelde de abstention; B1 sekiz kimya inceleme kaydında skor vermez. B2 protein dalıyla yedi ek ilaçta kayıt-sıralama skoru verebilir; bu ilave input kapsamı başarı artışı iddiası değildir. Kaynak 62 ID ve QC kararları değişmedi. Train tek proxy sınıfı, test sıfır gözlenen pozitif veya sıfır unknown gibi durumlarda fallback olasılık/başarım sıfırı üretilmedi. Sözlük dışı kaynak pozitif sayıları kapsam tablosunda ayrıca vardır.

## 6. Eşleştirilmiş fark ve koşullu belirsizlik''')
    code('''delta=read('paired_B2_minus_B1_group_CI.csv');display(delta[delta.family.eq('PT')].drop(columns=['semantics','CI_interpretation']))
display(read('bootstrap_design.csv').drop(columns=['semantics']))
fig,ax=plt.subplots(figsize=(11,5));f=delta[delta.family.eq('PT')&delta.metric.eq('drug_macro_AP')].copy();xx=np.arange(len(f));ax.errorbar(xx,f.B2_minus_B1,yerr=np.vstack([f.B2_minus_B1-f.CI95_low,f.CI95_high-f.B2_minus_B1]).astype(float),fmt='o',capsize=5,color='#805f9b');ax.axhline(0,color='#777',ls='--');ax.set_xticks(xx,f.protocol+' / '+f.scope,rotation=15);ax.set(ylabel='B2 − B1 observed-record drug-AP',title='Aynı grup bootstrap çekimleri • yalnız sabit OOF tahminlerine koşullu');plt.tight_layout();plt.savefig(FIG/'06_paired_difference_group_CI.png',dpi=160);plt.show()''')
    md('''**Yorum:** Ana PT ortak kapsam farkı yaklaşık −0,029; koşullu %95 grup-bootstrap aralığı yaklaşık [−0,051, −0,009]. Bu ilk sabit protokolde B2'nin üstünlüğü görülmedi. Proteinlerin biyolojik olarak faydasız olduğu veya başka modelin de başarısız olacağı sonucu çıkarılmaz; küçük örneklem, özellik boyutu, kaynak ve hedef kapsamı sınırlıdır. CI'nın sıfırı dışlaması bütün eğitim sürecinin belirsizliğiyle kanıtlanmış genel üstünlük iddiasına çevrilmez. Sonuca göre C/split/PT/seed değiştirilmedi.

## 7. Model uyumu ve yeniden üretim izi''')
    code('''provenance=read('model_fit_provenance.csv');display(provenance.head(10).drop(columns=['semantics']))
example=ROOT/'models/WP08_baseline_v1/primary_o01_final_PT_B1_selected.json';md=json.loads(example.read_text(encoding='utf-8'))
display(pd.DataFrame([{'model_version':md['model_version'],'C':md['C'],'seed':md['seed'],'sklearn':md['sklearn_version'],'feature_dimension':md['feature_dimension'],'train_drugs':len(md['train_drug_ids']),'fitted_classes':len(md['fitted_classes']),'parameter_sha256':md['parameters_sha256']}]))
display(pd.DataFrame({'train_fit_drug_id':md['train_drug_ids']}))
import plotly.graph_objects as go
f=drug[drug.protocol.eq('primary')&drug.family.eq('PT')&drug.scope.eq('paired54')].copy()
f['drug_AP_num']=pd.to_numeric(f.drug_AP,errors='coerce');pivot=f.pivot(index='drug_id',columns='model',values='drug_AP_num')
fig=go.Figure()
for model in ['B1','B2']:fig.add_trace(go.Scatter(x=pivot.index,y=pivot[model],mode='markers',name=model,hovertemplate='%{x}<br>Observed-record drug AP=%{y:.3f}<extra>'+model+'</extra>'))
fig.update_layout(title='Ortak kapsamda ilaç başına observed-record AP • klinik risk değil',xaxis_title='DrugBank ID',yaxis_title='Drug AP',height=650,width=1200)
fig.write_html(FIG/'per_drug_proxy_AP_interactive.html',include_plotlyjs=True,full_html=True)''')
    md('''**Kapanış:** Bu ilk baseline eğitimi kullanıcı onayıyla çalıştırıldı; onay öncesi hazırlık dosyaları değiştirilmedi. Her parametre bundle'ında gerçek split hash'i, C, train ID'leri, dönüşüm fit kaynakları, özellik/target sözlüğü, seed ve sürüm bulunur. Model sonuçları test doğrulamasından sonra Türkçe deney raporu ve model kartında açıklanır. WP09'a geçilmez; PPI/ATC/RF/MLP/context kendiliğinden eklenmez.

[Deney raporu](../reports/WP08_BASELINE_RESULTS.md), [model kartı](../reports/WP08_BASELINE_MODEL_CARD.md). Yöntem referansları: [lojistik regresyon](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [AP](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [AUROC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html).''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'Actual IPython results only; no refit'})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            b=io.BytesIO();plt.figure(i).savefig(b,format='png',dpi=100,bbox_inches='tight');display(Image(data=b.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for i,c in enumerate(nb.cells):
        if c.cell_type=='code':compile(c.source,f'WP08 baseline cell {i}','exec')
    for c in nb.cells:
        if c.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:r=shell.run_cell(c.source,store_history=False)
        if r.error_in_exec or r.error_before_exec:raise RuntimeError(r.error_in_exec or r.error_before_exec)
        c.execution_count=n;c.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for o in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in o.data.items()}
            c.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=o.metadata))
    nbf.validate(nb);nbf.write(nb,ROOT/'notebooks/WP08_baseline_results.ipynb');print('Executed baseline notebook cells',n)


if __name__=='__main__':main()
