"""B0 keşifsel eki: gerçek sonuç tabloları ve öğretici grafikler; refit yok."""
from pathlib import Path
import os,io,base64
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP08 — B0_frequency_reference_v1 keşifsel referans kontrolü

**Bu karşılaştırma B1/B2 sonuçları görüldükten sonra kararlaştırıldı; keşifseldir.** Kabul edilen B1=0,6556 ve B2=0,6262 ana ortak drug-AP değerleri korunur. Eski model, skor, split, C, seed ve hedef sözlüğü değiştirilmedi.

B0 yalnız train ilaçlarında gözlenen PT kayıt sayısı / tanımlı train ilaç sayısıdır. Kimya, protein, PPI, ATC veya test sıklığı kullanmaz. Skor klinik yan etki olasılığı değildir. Unknown doğrulanmış biyolojik negatif değildir. Tek formül, smoothing/dönüşüm/tuning yok; B0 sonuçları hesaplanmadan bu ekin politikası kaydedildi. Bu, B1/B2 görülmeden yapılmış confirmatory preregistration anlamına gelmez.''')
    code('''from pathlib import Path
import json,numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP08/B0_frequency_reference_v1';FIG=ROOT/'reports/figures/WP08/B0_frequency_reference_v1';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',180);pd.set_option('display.max_columns',22);pd.set_option('display.max_colwidth',100)
def read(n):return pd.read_csv(QA/n,keep_default_na=False)
policy=json.loads((QA/'policy_before_B0_results.json').read_text(encoding='utf-8'))
display(pd.DataFrame([policy]).drop(columns=['train_populations','main_comparisons','scope']))
pop=read('train_population_sizes.csv');display(pop[pop.inner_fold.eq(0)])
fig,ax=plt.subplots(figsize=(10,5));p=pop[pop.protocol.eq('primary')&pop.inner_fold.eq(0)].pivot(index='outer_fold',columns='reference',values='train_drugs');p.plot.bar(ax=ax);ax.set(ylabel='Frekans paydası: train ilaç sayısı',title='B0 popülasyonları önceden tanımlı • test sıklığı kullanılmaz');plt.tight_layout();plt.savefig(FIG/'01_train_population_denominators.png',dpi=160);plt.show()''')
    md('''**Yorum:** B0_all_train bütün train ilaçlarını, B0_like_B1/B0_like_B2 ilgili modelin input-uygun train ilaçlarını kullanır. İkinci ve üçüncü popülasyon yalnız eşleştirilmiş referans tasarımı için frozen ID/eligibility bilgisine dayanır; sayısal biyolojik değer okunmaz. Böylece farklı train paydaları gizlenmez ve iyi sonuç veren payda sonradan seçilmez.

## 1. Gerçek train sıklığı ve girdisiz ilaç politikası''')
    code('''frequency=read('train_frequency_estimates.csv');example=frequency[frequency.context.eq('primary_o01_final')&frequency.reference.eq('B0_like_B1')].sort_values('frequency_score',ascending=False)
display(example.head(15).drop(columns=['semantics']))
display(read('train_population_ids.csv').query("context == 'primary_o01_final'").head(15).drop(columns=['semantics']))
status=read('B0_status_all62.csv');display(status[status.drug_id.eq('DB06799')].drop(columns=['semantics']))
coverage=read('coverage_and_positive_unknown.csv');display(coverage[coverage.scope.eq('B0_all62_reference_ONLY')].drop(columns=['semantics']))''')
    md('''**Yorum:** B0 aynı outer fold içinde aynı PT için bütün test ilaçlarına aynı popülasyon skorunu verir; bireye özgü ayrım yapmaz. Biyolojik input gerektirmediği için Methenamine dahil 62 ilaçta bu referans hesaplanabilir. Bu durum B1/B2'nin Methenamine abstention'ını iptal etmez. Paired kıyasta B0 tam olarak aynı eski model ilaç/target anahtarlarına kısıtlanır; 62'lik referans ayrı ve doğrudan kıyaslanmayan kapsamdır. 0/1 sıklıklar yalnız train kayıt oranıdır, gerçek yokluk veya klinik olasılık değildir.

## 2. B1/B2, kayıt sıklığını geçiyor mu?''')
    code('''metrics=read('metrics_with_group_CI.csv');delta=read('paired_differences_group_CI.csv')
paired=metrics[metrics.scope.eq('paired54')];display(paired[paired.metric.isin(['drug_macro_AP','class_macro_AUROC'])].drop(columns=['semantics','CI_scope']))
order=['B0_all_train','B0_like_B1','B0_like_B2','B1','B2']
fig,axs=plt.subplots(1,2,figsize=(14,5),sharey=True)
for ax,protocol in zip(axs,['primary','stress']):
    f=paired[paired.protocol.eq(protocol)&paired.metric.eq('drug_macro_AP')].set_index('model').loc[order]
    xx=np.arange(len(f));ax.errorbar(xx,f.estimate,yerr=np.vstack([f.estimate-f.CI95_low,f.CI95_high-f.estimate]).astype(float),fmt='o',capsize=4,color='#607f9a');ax.set_xticks(xx,order,rotation=30,ha='right');ax.set(ylim=(0,1),ylabel='Observed-record drug-macro AP',title=protocol+' • aynı 54 ilaç / aynı hedefler')
plt.tight_layout();plt.savefig(FIG/'02_matched_drug_AP.png',dpi=160);plt.show()''')
    md('''**Yorum:** Ana ortak kapsamda B1 0,6556, B0_like_B1 0,6438; B2 0,6262, B0_like_B2 0,6466. B1'in küçük nokta avantajı tek başına üstünlük kanıtı değildir. B0 sonuçlarının B1'e yakın olması, yalnız sıklık sıralamasının güçlü bir referans olduğunu gösterir. “Başarının yüzde kaçı frekanstan kaynaklandı?” şeklinde nedensel veya açıklanan-varyans yüzdesi bu AP değerlerinden hesaplanamaz; doğru nicelik eşleştirilmiş ek AP farkıdır.

## 3. Aynı grup çekimleriyle model − B0 farkları''')
    code('''d=delta[delta.scope.eq('paired54')&delta.metric.eq('drug_macro_AP')&delta.reference.str.startswith('B0')];display(d.drop(columns=['semantics','CI_scope']))
fig,ax=plt.subplots(figsize=(12,5));f=d[((d['first']=='B1')&(d.reference=='B0_like_B1'))|((d['first']=='B2')&(d.reference=='B0_like_B2'))].copy();xx=np.arange(len(f))
ax.errorbar(xx,f.first_minus_reference,yerr=np.vstack([f.first_minus_reference-f.CI95_low,f.CI95_high-f.first_minus_reference]).astype(float),fmt='o',capsize=5,color='#87689b');ax.axhline(0,ls='--',color='#777');ax.set_xticks(xx,f.protocol+' / '+f['first']+' − '+f.reference,rotation=20,ha='right');ax.set(ylabel='Eşleştirilmiş observed-record AP farkı',title='Keşifsel • sabit skor/frekanslara koşullu %95 grup CI');plt.tight_layout();plt.savefig(FIG/'03_model_minus_frequency_group_CI.png',dpi=160);plt.show()''')
    md('''**Yorum:** Ana B1−B0_like_B1 ≈+0,0119; %95 koşullu CI yaklaşık [−0,0021,+0,0274]. Ana B2−B0_like_B2 ≈−0,0204; CI yaklaşık [−0,0438,+0,0032]. İkisi de sıfırı içerir. Stres protokolünde B2'nin farkı daha düşüktür ve koşullu aralık sıfırın altındadır; bu da keşifsel, sabit OOF koşullu sonuçtur. Çoklu keşifsel kıyasları confirmatory test gibi sunmuyoruz. B1/B2'ye yeniden C araması veya eğitim yapılmadı.

Bootstrap 1000 kez kilitli yapısal grupları birlikte örnekler; aynı çekimler bütün karşılaştırılan skor panellerinde kullanılır. Pair/fold bağımsızlığı varsayılmaz. Bu CI tüm tekrar eğitim belirsizliği veya bağımsız dış doğrulama değildir.

## 4. Drug-AP ve class-AUROC neden farklı yönlere gidebilir?''')
    code('''within=read('within_fold_class_AUROC_diagnostic.csv');mean=read('within_fold_AUROC_descriptive_mean.csv');display(within[within.protocol.eq('primary')].drop(columns=['semantics']));display(mean.drop(columns=['semantics']))
pooled=paired[paired.protocol.eq('primary')&paired.metric.eq('class_macro_AUROC')].set_index('model').loc[order]
local=mean[mean.protocol.eq('primary')].set_index('model').loc[order]
fig,axs=plt.subplots(1,2,figsize=(14,5),sharey=True)
axs[0].bar(order,pooled.estimate,color=['#a6b38d']*3+['#5987ae','#b68c63']);axs[0].set_title('Pooled ragged OOF class-AUROC')
axs[1].bar(order,local.descriptive_mean_of_5_fold_class_AUROC,color=['#a6b38d']*3+['#5987ae','#b68c63']);axs[1].set_title('Fold içi class-AUROC ortalaması • betimleyici')
for ax in axs:ax.axhline(.5,color='#777',ls='--');ax.tick_params(axis='x',rotation=30);ax.set(ylim=(0,1),ylabel='Observed-record class-AUROC; unknown gerçek negatif değil')
plt.tight_layout();plt.savefig(FIG/'04_pooled_vs_within_fold_class_AUROC.png',dpi=160);plt.show()''')
    md('''**Yorum:** Drug-AP, bir ilacın PT'lerini birbirine göre sıralar; class-AUROC aynı PT'de farklı ilaçları ayırt etmeyi sorar. Sık PT'ler herkeste üstte olduğunda kişiselleştirme olmadan drug-AP yüksek olabilir. B2 bazı sınıf içi ayrımları geliştirirken PT'ler arası sıralamayı zayıflatabilir; tek bir “daha iyi” ölçü gibi yorumlanmaz.

**B0 için kritik kontrol:** Fold içinde bir PT'nin skoru sabittir; iki outcome varsa AUROC tam 0,5 olmalıdır ve doğrulandı. Pooled OOF'ta skorlar foldların train sıklığıyla değişir; testte kaydı daha yoğun olan bir foldun tamamlayıcı train sıklığı daha düşük olabilir. Bu nedenle pooled B0 class-AUROC≈0,32 iken fold içi değer 0,5'tir. Bunu B0'ın “ters klinik tahmini” veya bütün B1/B2 sınıf ayrımının kazanımı gibi yorumlamamak gerekir. Yeni fold-içi tablo açıklayıcı diagnostiktir; eski pooled değerler değiştirilmedi, beş fold bağımsız CI birimi yapılmadı.

## 5. Kapsam, unknown ve 1685 dışarıda kalan pozitif''')
    code('''common=coverage[coverage.protocol.eq('primary')&coverage.scope.eq('paired54')];display(common.drop(columns=['semantics']))
fig,axs=plt.subplots(1,2,figsize=(14,5));c=common.set_index('model').loc[order]
pd.DataFrame({'Gözlenen pozitif':c.observed_positive_scored,'Unknown (gerçek negatif değil)':c.unknown_scored_NOT_verified_negative}).plot.bar(stacked=True,ax=axs[0],color=['#6e9d86','#b5bfd0']);axs[0].set(ylabel='Skorlanan drug–PT çifti',title='Tam eşleştirilmiş 13964 çift')
axs[1].bar(['Skor kapsamında','Sözlük/fit kapsamı dışında'],[3820,1685],color=['#6e9d86','#c4947b']);axs[1].set(ylabel='Kaynakta gözlenen pozitif çift',title='Aynı 54 ilaçta toplam 5505 kaynak pozitifi')
axs[0].tick_params(axis='x',rotation=30);plt.tight_layout();plt.savefig(FIG/'05_positive_unknown_and_uncovered.png',dpi=160);plt.show()''')
    md('''**Yorum:** Ortak kapsamda her yöntem 54 ilaç/13964 çift üzerinde karşılaştırıldı: 3820 gözlenen pozitif, 10144 unknown. Aynı ilaçlarda 1685 ek kaynak pozitifi folda özgü seçilmiş/fit edilmiş hedeflerin dışındadır. Bu 1685, bütün 62 kohorttaki toplam eksik etiket sayısı değildir. Değerlendirilen uzay dışındaki pozitiflere başarısızlık/negatif etiketi uydurulmadı; kapsam raporlandı. Dolayısıyla 0,65 civarı AP, tüm 1061 PT ve 62 ilaçta tam hedef uzayı performansı iddiası taşımaz. B0'nın tüm-62 referansı da yine sabit cohort-train hedef sözlüğüne koşulludur.

## 6. Koruma, bilimsel sonuç ve açık ROADMAP görevleri''')
    code('''display(read('ROADMAP_WP08_remaining_tasks.csv'))
done=json.loads((QA/'evaluation_complete.json').read_text(encoding='utf-8'));display(pd.DataFrame([done]))
import plotly.graph_objects as go
f=read('per_drug_model_minus_matched_frequency.csv');f=f[f.protocol.eq('primary')]
fig=go.Figure()
for model in ['B1','B2']:
    a=f[f.model.eq(model)];fig.add_trace(go.Scatter(x=a.drug_id,y=a.AP_difference,mode='markers',name=model,hovertemplate='%{x}<br>Model − eşleştirilmiş B0 AP=%{y:.3f}<extra>'+model+'</extra>'))
fig.add_hline(y=0,line_dash='dash');fig.update_layout(title='Keşifsel drug-AP farkları • klinik risk değil',height=650,width=1200,xaxis_title='DrugBank ID',yaxis_title='Observed-record AP farkı')
fig.write_html(FIG/'per_drug_frequency_reference_interactive.html',include_plotlyjs=True,full_html=True)''')
    md('''**Kapanış:** B1/B2 v1 ve tüm eski QA korunur. B0 frekansları test etiketi/değeriyle ayarlanmadı; sonuç görüldükten sonra smoothing/model/split/seed seçilmedi. Bu ek, B1/B2'den sonra kararlaştırılan keşifsel referanstır. ATC, RF/MLP, protein-mean MLP gibi yol haritasındaki yapılmamış varyantlar tabloda açık bırakıldı; gerçek PPI encoder ve ablation WP09'dur, bu ekte başlanmaz.

[Bilimsel B0 raporu](../reports/WP08_B0_FREQUENCY_REFERENCE.md). WP08 kapanmadı; sonuç ve sonraki kapsam için kullanıcı onayı beklenir. Bütün ölçüler observed-record proxy'dir; unknown gerçek negatif değildir.''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'Actual IPython; exploratory B0 read-only results'})
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
        if c.cell_type=='code':compile(c.source,f'WP08 B0 cell {i}','exec')
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
    nbf.validate(nb);nbf.write(nb,ROOT/'notebooks/WP08_B0_frequency_reference_v1.ipynb');print('Executed B0 notebook code cells',n)


if __name__=='__main__':main()
