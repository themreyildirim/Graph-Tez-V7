"""Gerçek eğitimin kayıtlı sonuçlarını öğreten notebook; hiçbir fit yeniden çalışmaz."""
from pathlib import Path
import os,io,base64
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP09 — Gerçek protein-PPI eğitimi ve kontrollü ablation

Kullanıcının açık onayıyla frozen v3 protokolünde eğitim yapıldı. **190 fit,10.867 gerçek optimizer adımı,140 inner/50 outer son model.** Protein56→32 tek residual mean PPI;kimya5→8;dört rol ve maskeler. Atom–bağ GNN yoktur;tam moleküler Graph-in-Graph tamamlandı denmez.

**Bilimsel görev:** SIDER'da gözlenen kayıtları yeni ilaçlar için sıralamak. Unknown biyolojik negatif değildir;sigmoid skoru klinik olasılık değildir. Aynı-split sonuçlar önceki baseline'lar görüldüğü için keşifseldir. Bu notebook yalnız kayıtlı çıktıları okur;modeli yeniden fit etmez.''')
    code(r'''from pathlib import Path
import json,re,numpy as np,pandas as pd,matplotlib.pyplot as plt,networkx as nx
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').is_file():
    if ROOT.parent==ROOT:raise RuntimeError('Proje kökü bulunamadı')
    ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP09/training_v1';MODEL=ROOT/'models/WP09_PPI_v3_training_v1'
FIG=ROOT/'reports/figures/WP09/training_v1';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',150);pd.set_option('display.max_columns',22);pd.set_option('display.max_colwidth',100)
fit=pd.read_csv(QA/'model_fit_summary.csv');metrics=pd.read_csv(QA/'metrics_with_group_CI.csv');delta=pd.read_csv(QA/'paired_differences_group_CI.csv')
done=json.loads((QA/'training_complete.json').read_text(encoding='utf-8'));run=json.loads((QA/'run_config.json').read_text(encoding='utf-8'))
display(pd.DataFrame([done]).drop(columns=['semantics']))
display(pd.DataFrame([{'model_sürümü':run['version'],'threshold':run['approved_primary_threshold'],'dtype':'float32','CPU_thread':1,
    'atom_bağ_GNN':False,'WP10':False,'B0_B1_B2_refit':False}]))
display(pd.read_csv(QA/'excluded_inner_jobs.csv'))''')
    md('''**Yorum:** Yapısal null politikası nedeniyle primary_o02_i01 ve stress_o02_i02 bütün varyantlarda seçimden dışarıdadır:10 inner fit çalıştırılmadı. Üç başarısız null eski NA statüsünde kalır. Kalan190 fit teknik hata vermedi;teknik başarı tahmin üstünlüğü veya klinik doğrulama değildir. Dtype float32,CPU1thread ve bütün runtime/CI kararları sonuçlardan önce ayrı onaylı run_config'te kaydedildi;eski proposed v3 dosyası ezilmedi.

## 1. Gerçek loss ve inner doğrulama eğrileri''')
    code(r'''context='primary_o01_i01';labels=['G_noPPI','G_realPPI','G_shuffledPPI_R0','G_shuffledPPI_R1','G_shuffledPPI_R2']
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
for name in labels:
    row=fit[(fit.context==context)&(fit.model==name)].iloc[0]
    history=pd.read_csv(QA/'history'/(row.job_key+'.csv'))
    axs[0].plot(history.epoch,history.train_BCE_pre_update,label=name,lw=1.3)
    axs[1].plot(history.epoch,history.validation_drug_AP,label=name,lw=1.3)
    selected=history[history.epoch==row.best_epoch].iloc[0]
    axs[1].scatter([row.best_epoch],[selected.validation_drug_AP],s=22)
axs[0].set(title='Train observed-record BCE (güncelleme öncesi)',xlabel='Epoch',ylabel='BCE loss')
axs[1].set(title='Inner validation drug-macro AP',xlabel='Epoch',ylabel='Observed-record AP',ylim=(0,1));axs[1].legend(fontsize=7)
plt.tight_layout();plt.savefig(FIG/'01_real_training_curves.png',dpi=160);plt.show()
display(fit[fit.context.eq(context)][['model','epochs_run','best_epoch','best_validation_AP','optimizer_steps','selected_state_L2_change']])''')
    md('''**Yorum:** Train loss optimizer adımlarıyla değişiyor;inner AP seçilmiş checkpoint'i belirliyor. Patience20/min_delta0,0001 kuralı sabittir;en iyi görülen yeni parametre araması yapılmadı. Noktalar kaydedilmiş best epoch'lardır;son optimizer adımıyla aynı olmak zorunda değildir. Outer test bu eğrilere girmez. Başka fitleri gizlemek için bu örnek seçilmedi:ilk sıralı inner context gösterilir,190 fitin tam eğrileri QA history klasöründedir.

## 2. Outer epoch sayıları nasıl belirlendi?''')
    code(r'''outer=fit[fit.inner_fold.eq(0)]
display(outer[['protocol','outer_fold','model','best_epoch','optimizer_steps','num_targets','status']])
decisions=json.loads((QA/'outer_fit_and_selection.json').read_text(encoding='utf-8'));display(pd.DataFrame(decisions).drop(columns=['outer_epoch_by_model']))
fig,axs=plt.subplots(1,2,figsize=(12,4.4))
for ax,protocol in zip(axs,['primary','stress']):
    heat=outer[outer.protocol.eq(protocol)].pivot(index='model',columns='outer_fold',values='best_epoch').loc[labels]
    ax.imshow(heat,aspect='auto',vmin=25,vmax=65,cmap='Blues');ax.set_xticks(range(5),heat.columns);ax.set_yticks(range(5),heat.index,fontsize=8)
    for i in range(5):
        for j in range(5):ax.text(j,i,str(int(heat.iloc[i,j])),ha='center',va='center',fontsize=9)
    ax.set(title=protocol+' • outer son eğitim epoch',xlabel='Outer fold')
plt.tight_layout();plt.savefig(FIG/'02_outer_epoch_selection.png',dpi=160);plt.show()''')
    md('''**Yorum:** Outer son eğitimleri34–55 epoch sürer. Her variant/null için aynı ortak inner foldlardaki best epoch medyanı .5 yukarı yuvarlanır. Primary outer2 inner2/3,stress outer2 inner1/3 kullanır;diğerleri3 fold. Seçimler önce JSON/hash olarak kaydedildi,bütün outer ağırlıklar tamamlandı,sonra test skorlaması ayrı komutla açıldı. İç sözlükler folda özgüdür;aynı contextte bütün5 fit aynı train ID/head/PT/init hash'ine sahiptir.

## 3. Aynı ortak54 kapsamda B0/B1/B2 ve GNN''')
    code(r'''order=['B0_like_B2','B1','B2','G_noPPI','G_realPPI','G_shuffledPPI_mean3_metrics']
ap=metrics[(metrics.scope=='paired54')&(metrics.metric=='drug_macro_AP')]
display(ap[['protocol','model','estimate','CI95_low','CI95_high','valid_bootstrap_replicates']])
fig,axs=plt.subplots(1,2,figsize=(13,5),sharey=True)
for ax,protocol in zip(axs,['primary','stress']):
    sub=ap[ap.protocol.eq(protocol)].set_index('model').loc[order]
    for i,(name,row) in enumerate(sub.iterrows()):
        ax.errorbar(i,row.estimate,yerr=[[row.estimate-row.CI95_low],[row.CI95_high-row.estimate]],fmt='o',capsize=4,color='#63879e')
        ax.annotate(f'{row.estimate:.4f}',(i,row.estimate),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
    ax.set_xticks(range(len(order)),order,rotation=35,ha='right',fontsize=8);ax.set(title=protocol+' • aynı ilaç/fold/PT keys',ylabel='Drug-macro observed-record AP',ylim=(0,1))
plt.tight_layout();plt.savefig(FIG/'03_paired_baseline_comparison.png',dpi=160);plt.show()''')
    md('''**Yorum:** Ana ortak54'te G_noPPI0,6430,G_realPPI0,6429,shuffled3 metrik ortalaması0,6433. B1 0,6556,B2 0,6262 ve eşleşen B0_like_B2 0,6466 değişmedi. Gerçek PPI ek drug-AP üstünlüğü göstermedi. Shuffled her R0/R1/R2 ayrı modeldir;tabloda her biri bulunur,primary özet üç metriğin eşit ortalamasıdır. Tahmin skorları ensemble yapılmadı ve en iyi replica seçilmedi. Stres sonuçları B2'ye göre daha iyi görünse de PPI'sız model de aynı kazancı gösterir;PPI katkısı diye sunulamaz.

## 4. PPI katkısı için eşleştirilmiş fark''')
    code(r'''chosen=delta[(delta.scope=='paired54')&(delta.metric=='drug_macro_AP')&(delta['first']=='G_realPPI')&delta.reference.isin(['G_noPPI','G_shuffledPPI_mean3_metrics','B2','B0_like_B2'])]
display(chosen[['protocol','first','reference','first_minus_reference','CI95_low','CI95_high']])
fig,ax=plt.subplots(figsize=(10,5.2));yy=np.arange(len(chosen))
ax.errorbar(chosen.first_minus_reference,yy,xerr=np.vstack([chosen.first_minus_reference-chosen.CI95_low,chosen.CI95_high-chosen.first_minus_reference]),fmt='o',capsize=4,color='#8a759c')
ax.axvline(0,ls='--',color='gray');ax.set_yticks(yy,[f'{r.protocol}: real − {r.reference}' for r in chosen.itertuples()],fontsize=8)
ax.set(xlabel='Drug-AP farkı • sabit OOF koşullu %95 grup CI',title='Aynı örnek/grup çekimleriyle karşılaştırma');ax.invert_yaxis()
plt.tight_layout();plt.savefig(FIG/'04_PPI_paired_differences.png',dpi=160);plt.show()''')
    md('''**Yorum:** Ana real−noPPI −0,000142 (CI−0,003611–+0,003248);real−shuffled_mean −0,000379 (−0,002039–+0,001310). Stres farkları da sıfırı içeren CI verir. PPI'nin kullanıldığını kanıtlamak,bu kaynak ve görevde faydalı olduğunu kanıtlamaz. Real−B2 stres farkı+0,0469 olsa da noPPI−B2+0,0479'dur;kapasite/nonlineer encoder/öğrenme farkı ile topoloji katkısı ayrılmalıdır. Bunlar keşifsel,çoklu karşılaştırmalar;bağımsız dış doğrulama/genel üstünlük kanıtı değildir.

## 5. Micro AP ve fold içi class-AUROC''')
    code(r'''secondary=metrics[(metrics.scope=='paired54')&metrics.metric.isin(['micro_AP','within_fold_class_macro_AUROC','class_macro_AUROC'])&metrics.model.isin(order)]
display(secondary[['protocol','model','metric','estimate','interpretation']])
fig,axs=plt.subplots(2,2,figsize=(12,8),sharey=True)
for i,protocol in enumerate(['primary','stress']):
    for j,(metric,title) in enumerate([('micro_AP','Micro observed-record AP'),('within_fold_class_macro_AUROC','Fold içi class-AUROC • betimleyici')]):
        f=secondary[(secondary.protocol==protocol)&(secondary.metric==metric)].set_index('model').loc[order]
        axs[i,j].bar(range(len(order)),f.estimate,color=['#a0ad8d','#7895a5','#b99b7b','#6f96a6','#547e93','#a18db1'])
        axs[i,j].set_xticks(range(len(order)),order,rotation=35,ha='right',fontsize=7);axs[i,j].set(title=protocol+' / '+title,ylim=(0,1))
plt.tight_layout();plt.savefig(FIG/'05_secondary_metrics.png',dpi=160);plt.show()''')
    md('''**Yorum:** Drug-AP her ilaçta PT sıralaması,micro AP bütün skorlanan çiftlerin pooled sıralaması,class-AUROC aynı PT'de ilaç sıralamasıdır. Fold içi class-AUROC eşit fold ortalaması yalnız betimleyicidir;foldlar bağımsız tekrar sayılmadı. Pooled class-AUROC ayrıca tabloda tanısal tutulur;fold skor ölçekleri/sözlükleri farklı olduğundan klinik ayrım veya tek genel üstünlük diye yorumlanmaz. B0 aynı fold/PT'de sabit skor verdiği için fold içi AUROC0,5'tir. Primary gerçekG microAP0,5678 ve fold içi classAUROC0,5270;stres0,5903/0,5468. Daha iyi görünen özet seçilip primary ölçüt değiştirilmedi.

## 6. Paired54 / own61,unknown,NA ve kapsam dışı pozitifler''')
    code(r'''coverage=pd.read_csv(QA/'evaluation_coverage.csv');c=coverage[coverage.model=='G_realPPI']
display(c.drop(columns=['semantics']))
display(pd.read_csv(QA/'prediction_status_all62.csv').groupby(['protocol','model','status']).size().rename('ilaç').reset_index())
target=pd.read_csv(QA/'target_trainability_audit.csv');display(target.groupby('status').size().rename('context_PT_kaydı').reset_index())
fig,axs=plt.subplots(1,2,figsize=(12,4.5));x=np.arange(len(c));names=[f'{r.protocol}/{r.scope}' for r in c.itertuples()]
axs[0].bar(x,c.observed_positive_scored,label='Gözlenen pozitif',color='#78a18e');axs[0].bar(x,c.unknown_NOT_verified_negative,bottom=c.observed_positive_scored,label='Unknown:gerçek negatif değil',color='#b2bed0')
axs[1].bar(x,c.observed_positive_scored,label='Skorlanan pozitif',color='#78a18e');axs[1].bar(x,c.out_of_scored_vocab_positive,bottom=c.observed_positive_scored,label='Kaynak pozitif:skor sözlüğü dışı',color='#be947c')
for ax,title in zip(axs,['Skorlanan çift kapsamı','Aynı ilaçlardaki kaynak pozitifler']):
    ax.set_xticks(x,names,rotation=25,ha='right',fontsize=8);ax.set(title=title,ylabel='Çift sayısı');ax.legend(fontsize=7)
plt.tight_layout();plt.savefig(FIG/'06_coverage_unknown_NA.png',dpi=160);plt.show()''')
    md('''**Yorum:** Her model61/62 ilaçta skor,Methenamine'de abstention verir. Own61 vepaired54 farklı paydadır;B1 own61 tablosuna eksik skorla eklenmez. Kaynak1061 PT ve6416 pozitif korunur;primary paired54'te13964 çift=3820 pozitif+10144 unknown veaynı ilaçlarda1685 kaynak pozitif skor kapsamı dışındadır. Bunlar otomatik negatif/yanlış negatif değildir.306 pooled CUI'nin256'sında class metriği tanımlı,50'sinde NA'dır. Tüm1061 PT'de performans iddiası kurulamaz. Trainability tablosundaki25 single-proxy kaydı40 contextteki PT-sözlük oluşumlarıdır,25 benzersiz ilaç veya25 başarısız model değildir;başlıkta bu hedefler yoktur.

## 7. Önceden seçilmiş gerçek query örneği:Erythromycin''')
    code(r'''example=json.loads((QA/'example_drug_inputs.json').read_text(encoding='utf-8'));ranking=pd.read_csv(QA/'example_drug_PT_ranking.csv')
display(pd.DataFrame([{'drug_id':example['drug_id'],'name':example['name'],**example['chemistry_source_values'],
    'chem_QC_mask':example['chemistry_QC_mask'],'protein_available':example['protein_available'],'actual_model_job':example['actual_model_job']}]))
display(pd.DataFrame([{'rol':r,'accessionlar':a,'sayı':len(a)} for r,a in example['protein_role_accessions'].items()]))
display(ranking[['rank','class_id','PT_name','score_observed_record_proxy','observed_record_s']].head(20))
top=ranking.head(15).iloc[::-1]
fig,axs=plt.subplots(1,2,figsize=(13,6),gridspec_kw={'width_ratios':[1,2]})
roles=list(example['protein_role_accessions']);axs[0].barh(roles,[len(example['protein_role_accessions'][r]) for r in roles],color='#7a98a7')
axs[0].set(title='Gerçek girdiler / dört ayrı rol',xlabel='Doğrulanmış accession sayısı')
chem='; '.join(f'{k}={v:.3g}' for k,v in example['chemistry_source_values'].items());axs[0].text(0,-.2,chem,transform=axs[0].transAxes,fontsize=8,wrap=True)
axs[1].barh(range(len(top)),top.score_observed_record_proxy,color=np.where(top.observed_record_s.eq(1),'#7d9f8e','#bb947c'))
axs[1].set_yticks(range(len(top)),[f'{r.PT_name} [{r.class_id}]' for r in top.itertuples()],fontsize=8)
axs[1].set(xlim=(0,1),xlabel='Observed-record sıralama skoru • klinik olasılık değil',title='Erythromycin / primary outer3 / gerçek PPI')
from matplotlib.patches import Patch
axs[1].legend(handles=[Patch(color='#7d9f8e',label='SIDER kaydı var'),Patch(color='#bb947c',label='SIDER unknown;negatif değil')],fontsize=7,loc='lower right')
plt.tight_layout();plt.savefig(FIG/'07_real_drug_ranking_example.png',dpi=160);plt.show()''')
    md('''**Yorum:** Örnek ID sonuçlara bakılmadan alfabetik ilk primary paired54 ID'si olarakrun_config'te belirlendi:DB00199 Erythromycin. MW733,937;LogP1,7856;HBD5;HBA14;TPSA193,91 kaynak clean girdileridir. Protein target2/enzyme3/transporter6/carrier0 ayrı tutulur. Bu ilaç primary outer3 test query'sidir;train'e girmemiştir. Renkler değerlendirme sırasında açılan kaynak kayıt durumudur,girdi değildir. Skoru yüksekunknown kavramı gerçek yanlış pozitif veya kesin klinik yan etki değildir. Bu,gerçek girdilerin ve sıralamanın öğretici örneğidir;SHAP/nedensel açıklama değildir. Kaynakta olmayan “risk olasılığı” veya hasta güvenliği önerisi üretilmez.

## 8. Gerçek optimizer/gradient kanıtı''')
    code(r'''proof=fit.groupby('model').agg(fit=('job_key','count'),optimizer_steps=('optimizer_steps','sum'),
    min_weight_change=('selected_state_L2_change','min'),min_max_message_gradient=('maximum_message_gradient_norm','min'),
    max_message_gradient=('maximum_message_gradient_norm','max'),max_message_input=('maximum_train_message_input_norm','max')).reindex(labels)
display(proof)
fig,axs=plt.subplots(1,2,figsize=(12,4.5));axs[0].bar(range(5),proof.optimizer_steps,color='#6f92a4');axs[0].set(title='Gerçek optimizer adımı toplamı',ylabel='Adım')
axs[1].bar(range(5),proof.min_max_message_gradient,color='#a68ba7');axs[1].set(title='Her modeldeki maksimum gradientlerin minimumu',ylabel='PPI message.weight gradient normu')
for ax in axs:ax.set_xticks(range(5),labels,rotation=25,ha='right',fontsize=8)
plt.tight_layout();plt.savefig(FIG/'08_optimizer_gradient_evidence.png',dpi=160);plt.show()
import plotly.graph_objects as go
drug=pd.read_csv(QA/'per_drug_metrics.csv');sub=drug[(drug.protocol=='primary')&(drug.scope=='paired54')&drug.model.isin(['G_noPPI','G_realPPI'])]
pivot=sub.pivot(index='drug_id',columns='model',values='drug_AP')
interactive=go.Figure([go.Scatter(x=pivot.G_noPPI,y=pivot.G_realPPI,mode='markers',text=pivot.index,hovertemplate='%{text}<br>noPPI AP=%{x:.4f}<br>realPPI AP=%{y:.4f}<extra></extra>'),go.Scatter(x=[0,1],y=[0,1],mode='lines',line=dict(dash='dash',color='gray'),hoverinfo='skip')])
interactive.update_layout(title='Primary paired54 • ilaç bazlı observed-record AP;klinik risk değil',xaxis_title='G_noPPI drug AP',yaxis_title='G_realPPI drug AP',showlegend=False)
interactive.write_html(FIG/'per_drug_ablation_interactive.html',include_plotlyjs=True,full_html=True)''')
    md('''**Yorum:** Tüm190 fitte ağırlıklar değişti. Real/shuffled mesaj gradienti her fitte sıfırdan farklı;noPPI mesaj girdisi/gradienti0. NoPPI'da kullanılmayan message ağırlığınınAdamW weight decay ile sayısal kayması komşuluk kullanımı sayılmaz;kanıt gerçek gradient/input/forward testidir. ÖncekiV6'nın“PPI var ama forward yok” hatası giderilmiştir,fakat performans ablation'ı bu görevde ek fayda göstermemiştir. Etkileşimli HTML ilaç bazlı AP kıyasını incelemek içindir;offlinePlotly içerir,canlı tarayıcı testi yapılmadı.

## 9. Testler,tekrar üretim ve durma noktası''')
    code(r'''text=(QA/'test_results.txt').read_text(encoding='utf-8');test=re.search(r'Ran ([0-9]+) tests in ([0-9.]+)s',text)
display(pd.DataFrame([{'gerçek_trainer_testi':int(test.group(1)),'saniye':float(test.group(2)),'tümü_geçti':text.rstrip().endswith('OK'),
    'korunan_önceki_dosya':done['prior_files_verified'],'base_seed':20261106,'WP10':False}]))
display(pd.read_csv(QA/'feature_fit_provenance.csv').head(5))
display(pd.DataFrame([json.loads((QA/'evaluation_complete.json').read_text(encoding='utf-8'))]).drop(columns=['semantics']))''')
    md('''**Yorum:**24 test gerçek optimizer,init/epoch/ID/PT kaynağı,kayıtlı parametreden skor,aynıouter fit tekrar üretimi,gerçektrainer'da outer label/value mutation,train-state/query izolasyonu,trained PPI/noPPI forward,kusurda NA,bağımsızsklearn AP ve kapsam testlerini içerir. Testlerin küçük kontrollü yeniden fit'leri model dosyalarını değiştirmez,protokol veya parametre araması değildir.

CI1000 paired structural-group bootstrap'tır;ana61/stres40 grup birlikte örneklenir ve modeller aynı çekimleri kullanır. SabitOOF ve üç sabit null'a koşulludur;tam tekrar-eğitim/initialization/null dağılımı/dış kohort belirsizliğini kapsamaz. Null'lar bağımsız hasta/ilaç örneği değildir.

[Eğitim raporu](../reports/WP09_TRAINING_RESULTS.md) ve [model kartı](../reports/WP09_TRAINING_MODEL_CARD.md) nihai bulgu/sınırları açıklar. **WP09 eğitim/değerlendirmesi bittiğinde durulur;WP10'a geçmek için kullanıcı onayı gerekir.**''')
    notebook=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'},'language_info':{'name':'python'}})
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            b=io.BytesIO();plt.figure(i).savefig(b,format='png',dpi=100,bbox_inches='tight');display(Image(data=b.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for i,c in enumerate(cells):
        if c.cell_type=='code':compile(c.source,f'WP09 training cell{i}','exec')
    for c in cells:
        if c.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:r=shell.run_cell(c.source,store_history=False)
        if r.error_in_exec or r.error_before_exec:raise RuntimeError(r.error_in_exec or r.error_before_exec)
        c.execution_count=n;c.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for output in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in output.data.items()}
            c.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=output.metadata))
    notebook.cells=cells;nbf.validate(notebook);nbf.write(notebook,ROOT/'notebooks/WP09_training_results.ipynb')
    print(f'Executed WP09 training results notebook: {n} cells /8 PNG /offline HTML; no refit')


if __name__=='__main__':main()
