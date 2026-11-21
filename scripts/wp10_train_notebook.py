"""Gerçek fit/OOF/NPZ dosyalarından WP10 sonuç notebook'u;refit yok."""
from pathlib import Path
import io,base64,os,sys
import nbformat as nb
ROOT=Path(__file__).resolve().parents[1]


def main():
    path=ROOT/'notebooks/WP10_factorial_training.ipynb'
    if path.exists() and '--refresh-working-draft' not in sys.argv:raise RuntimeError('Notebook already exists')
    if (ROOT/'reports/qa/WP10/training_v1/artifact_validation.json').exists():raise RuntimeError('Run finalized')
    cells=[]
    def md(s):cells.append(nb.v4.new_markdown_cell(s))
    def code(s):cells.append(nb.v4.new_code_cell(s))
    md('''# WP10 — Gerçek dört kollu molekül/protein GNN eğitimi

Kullanıcı gerçek eğitimi onayladı. **A0P0/A0P1/A1P0/A1P1**, aynı150 boyutlu mimari, aynı context başlangıçları ve frozen train-only kaynaklarla eğitildi. Shuffled PPI deneyleri eklenmedi. Bu notebook modelleri yeniden eğitmez; gerçek kayıtlı fit/OOF/NPZ dosyalarını okur.

Görev SIDER'da **gözlenen kayıtları sıralamak**. Unknown çiftler doğrulanmış biyolojik negatif değildir. Sigmoidler klinik yan etki olasılığı,kalibrasyon veya nedensellik kanıtı değildir. Önceki baseline/WP09 sonuçları görüldüğünden çalışma keşifseldir.''')
    code(r'''from pathlib import Path
import json,sys,re
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():
    if ROOT.parent==ROOT:raise RuntimeError('Proje kökü bulunamadı')
    ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'scripts'))
from wp10_train import QA,MODEL,NAMES,restore,torch
from wp10_molecular_graph import load_store
torch.set_num_threads(1)
FIG=ROOT/'reports/figures/WP10/training_v1';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',180);pd.set_option('display.max_columns',22)
fit=pd.read_csv(QA/'model_fit_summary.csv');metrics=pd.read_csv(QA/'metrics_with_group_CI.csv')
effects=pd.read_csv(QA/'factorial_contrasts_group_CI.csv');coverage=pd.read_csv(QA/'evaluation_coverage.csv')
run=json.loads((QA/'run_config.json').read_text(encoding='utf-8'));done=json.loads((QA/'training_complete.json').read_text(encoding='utf-8'))
display(pd.DataFrame([done]).drop(columns=['semantics']));display(pd.read_csv(QA/'excluded_inner_jobs.csv'))''')
    md('''**Yorum:**112 inner ve40 outer olmak üzere152 fit kaydedildi. Önceden dışlanan iki inner bağlam dört varyant için de dışarıda:8 iş eğitilmedi. Bu seçim düşük sonuç nedeniyle yapılmadı;eski ortak inner sözleşmesi korunur.62 ilaç envanterde,54 atom maskesi açık ve8 QC kapalıdır. Methenamine için tüm kişiselleştirilmiş girdi eksikliği korunur.

## 1. Gerçek eğitim eğrileri''')
    code(r'''first=fit[fit.context.eq('primary_o01_i01')]
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
for name in NAMES:
    row=first[first.model.eq(name)].iloc[0];history=pd.read_csv(QA/'history'/(row.job_key+'.csv'))
    axs[0].plot(history.epoch,history.train_BCE_pre_update,label=name)
    axs[1].plot(history.epoch,history.validation_drug_AP,label=name)
    best=history[history.epoch.eq(row.best_epoch)].iloc[0];axs[1].scatter([row.best_epoch],[best.validation_drug_AP],s=22)
axs[0].set(title='Gerçek train observed-record BCE',xlabel='Epoch',ylabel='BCE • güncelleme öncesi')
axs[1].set(title='Inner validation drug-macro AP',xlabel='Epoch',ylabel='AP',ylim=(0,1));axs[1].legend()
plt.tight_layout();plt.savefig(FIG/'01_training_curves.png',dpi=160);plt.show()
display(first[['model','epochs_run','best_epoch','best_validation_AP','optimizer_steps']])''')
    md('''**Yorum:**Grafik ilk sıralı inner bağlamı gösterir;152 fitin bütün loss/validation eğrileri history klasöründedir. Yalnız inner validation AP checkpoint seçer,max200/patience20/min_delta0.0001 sabittir. Noktalar seçilmiş epoch'tur. Outer test bu eğrilere girmez;sonuç sonrası süre veya parametre araması yapılmadı.

## 2. Outer epoch ve gerçek öğrenme kanıtı''')
    code(r'''outer=fit[fit.inner_fold.eq(0)];display(outer[['protocol','outer_fold','model','best_epoch','num_targets','optimizer_steps','status']])
proof=fit.groupby('model').agg(fits=('job_key','size'),steps=('optimizer_steps','sum'),minimum_PPI_max_gradient=('maximum_message_gradient_norm','min'),minimum_atom_max_gradient=('maximum_atom_message_gradient_norm','min'),minimum_bond_max_gradient=('maximum_bond_message_gradient_norm','min'),minimum_weight_change=('selected_state_L2_change','min'))
display(proof)
fig,axs=plt.subplots(1,2,figsize=(11,4.4))
axs[0].bar(proof.index,proof.steps,color='#7094a7');axs[0].set(title='Gerçek optimizer adımları',ylabel='Adım')
axs[1].bar(np.arange(4)-.18,proof.minimum_PPI_max_gradient,width=.36,label='PPI message');axs[1].bar(np.arange(4)+.18,proof.minimum_atom_max_gradient,width=.36,label='Atom message')
axs[1].set_xticks(range(4),proof.index);axs[1].set(title='Fit maksimum gradientlerinin minimumu',ylabel='Gradient normu');axs[1].legend()
plt.tight_layout();plt.savefig(FIG/'02_actual_optimizer_gradients.png',dpi=160);plt.show()''')
    md('''**Yorum:**A1 modellerinde atom/bond parametrelerine,A?P1 modellerinde protein komşu mesajına gerçek eğitim gradienti ulaştı. A0 molekül ağırlıkları kullanılmaz ve değişmez;P0 komşu mesajı gerçekten0'dır. P0'da sıfır gradientli ağırlığın AdamW decay ile kayması komşuluk kullanımı kanıtı değildir. Her outer modelin epoch'u aynı ortak inner foldlardaki kendi best-epoch medyanından .5 yukarı seçildi;testle early-stop yoktur.

## 3. Aynı kapsamda dört kol ve sabit referanslar''')
    code(r'''order=['B0_like_B2','B1','B2','WP09_G_noPPI','WP09_G_realPPI']+list(NAMES)
ap=metrics[metrics.scope.eq('paired54')&metrics.metric.eq('drug_macro_AP')]
display(ap[['protocol','model','estimate','CI95_low','CI95_high']])
fig,axs=plt.subplots(1,2,figsize=(15,5),sharey=True)
for ax,protocol in zip(axs,['primary','stress']):
    sub=ap[ap.protocol.eq(protocol)].set_index('model').loc[order]
    ax.errorbar(range(len(order)),sub.estimate,yerr=np.vstack([sub.estimate-sub.CI95_low,sub.CI95_high-sub.estimate]),fmt='o',capsize=3,color='#64879b')
    ax.set_xticks(range(len(order)),[n.replace('WP09_','WP09\n') for n in order],rotation=45,ha='right',fontsize=8)
    ax.set(title=protocol+' • aynı drug/fold/PT kapsamı',ylabel='Drug-macro observed-record AP',ylim=(0,1))
plt.tight_layout();plt.savefig(FIG/'03_shared_AP_references.png',dpi=160);plt.show()''')
    md('''**Yorum:**B0/B1/B2 veWP09 skorları tekrar fit edilmedi;aynı anahtarlarda sabit referans olarak değerlendirildi. Dört yeni kol aynı genişletilmiş mimaridedir. Eski141 boyutluWP09 ile yeni150 boyutluA0 modellerin farkı tek başına atom/PPI etkisi değildir;başlık vebaşlangıç ağırlık şekli de değişir. Doğrudan katkı için aşağıdaki aynı mimarili factorial kontrastlar kullanılır.

## 4. Atom,PPI ve etkileşim''')
    code(r'''primary_effect=effects[effects.scope.eq('paired54')&effects.metric.eq('drug_macro_AP')]
display(primary_effect[['protocol','contrast','estimate','CI95_low','CI95_high','coefficients']])
fig,ax=plt.subplots(figsize=(10,7));y=np.arange(len(primary_effect))
ax.errorbar(primary_effect.estimate,y,xerr=np.vstack([primary_effect.estimate-primary_effect.CI95_low,primary_effect.CI95_high-primary_effect.estimate]),fmt='o',capsize=3,color='#947ba1')
ax.axvline(0,color='gray',ls='--');ax.set_yticks(y,[r.protocol+' / '+r.contrast for r in primary_effect.itertuples()],fontsize=8);ax.invert_yaxis()
ax.set(title='Önceden tanımlanan factorial AP farkları',xlabel='AP farkı • eşleştirilmiş koşullu %95 grup CI')
plt.tight_layout();plt.savefig(FIG/'04_factorial_contrasts.png',dpi=160);plt.show()''')
    md('''**Yorum:**atom_P0=A1P0−A0P0;atom_P1=A1P1−A0P1;PPI_A0=A0P1−A0P0;PPI_A1=A1P1−A1P0. Etkileşim=(A1P1−A0P1)−(A1P0−A0P0). Marjinal etkiler iki koşullu farkın eşit ortalamasıdır,tahmin ensemble'i değildir. Bunlar biyolojik nedensellik ölçüsü değildir.1000 bootstrap aynı frozen yapısal grupları birlikte veaynı çekimlerle örnekler;CI sabitOOF'ye koşulludur,tam tekrar eğitim veya bağımsız dış doğrulama değildir. Sıfırı içerenCI eşdeğerlik kanıtı sayılmaz.

## 5. Kapsam ve tanımsız metrikler''')
    code(r'''sub=coverage[coverage.model.eq('A1P1')];display(sub)
display(pd.read_csv(QA/'prediction_status_all62.csv').groupby(['protocol','model','status']).size().rename('ilaç').reset_index())
secondary=metrics[metrics.model.isin(NAMES)&metrics.scope.eq('paired54')&metrics.metric.isin(['micro_AP','within_fold_class_macro_AUROC','class_macro_AUROC'])]
display(secondary[['protocol','model','metric','estimate','interpretation']])
fig,ax=plt.subplots(figsize=(9,4.5));xx=np.arange(len(sub))
ax.bar(xx,sub.observed_positive_scored,label='SIDER pozitif');ax.bar(xx,sub.unknown_NOT_verified_negative,bottom=sub.observed_positive_scored,label='Unknown • doğrulanmış negatif değil')
ax.set_xticks(xx,[r.protocol+' / '+r.scope for r in sub.itertuples()],fontsize=8);ax.set(title='Ortak skorlanan çiftler ve kaynak kapsamı',ylabel='İlaç–PT çifti');ax.legend(fontsize=8)
plt.tight_layout();plt.savefig(FIG/'05_coverage_positive_unknown.png',dpi=160);plt.show()''')
    md('''**Yorum:**62 envanter korunur;her modelde61 ilaç skorlanır,Methenamine abstention. Ana paired54'te1685 kaynak pozitif hedef/fit kapsamı dışındadır;bu tüm62'nin yanlış-negatif sayısı değildir. Kaynak1061 PT'nin tamamında başarı iddiası yoktur. Tek proxy sınıflar/NA veunknown sıfır başarıya veya biyolojik negatife çevrilmez. Pooled class-AUROC yalnız tanıdır;ikincil fold içi class-AUROC tanımlı fold özetlerinin betimleyici ortalamasıdır,foldlar bağımsız tekrar sayılmaz.

## 6. Gerçek eğitilmiş modelin ağırlıkları ve molekül temsili''')
    code(r'''example=json.loads((QA/'example_drug_inputs.json').read_text(encoding='utf-8'));display(pd.DataFrame([example]).T)
job=example['actual_model_jobs']['A1P1'];metadata=json.loads((MODEL/(job+'.json')).read_text(encoding='utf-8'));trained=restore(metadata);store=load_store()
with torch.no_grad():embedding=trained.molecular(store.make_batch([example['drug_id']]).batch)['molecular_h'][0].numpy()
weights=trained.molecular.projection.weight.detach().numpy();schema=json.loads((ROOT/'reports/qa/WP10/encoder_v1/feature_schema.json').read_text(encoding='utf-8'))
fig,axs=plt.subplots(1,2,figsize=(13,4.6),gridspec_kw={'width_ratios':[2,1]})
im=axs[0].imshow(weights,aspect='auto',cmap='coolwarm',vmin=-abs(weights).max(),vmax=abs(weights).max());plt.colorbar(im,ax=axs[0],shrink=.75)
indices=list(range(0,44,4));axs[0].set_xticks(indices,[schema['atom_columns'][i] for i in indices],rotation=60,ha='right',fontsize=7)
axs[0].set(title='Kaydedilmiş A1P1 atom projection ağırlıkları',ylabel='Hidden16 koordinatı')
axs[1].bar(range(8),embedding,color='#8ba88e');axs[1].set(title=example['name']+' • gerçek molekül temsili',xlabel='Öğrenilmiş koordinat',ylabel='Encoder değeri')
plt.tight_layout();plt.savefig(FIG/'06_actual_trained_model.png',dpi=160);plt.show()
display(pd.DataFrame([{'job':job,'model_NPZ':metadata['parameters_file'],'state_sha256':metadata['selected_state_sha256'],'outer_epochs':metadata['best_epoch'],'input_drug':example['drug_id']}]))''')
    md('''**Yorum:**Bu şekil gerçek outer modelin NPZ ağırlıklarından üretildi;temsili veri değildir. Örnek,sonuçlardan önce alfabetik ilk primary paired54 ID kuralıyla belirlenen Erythromycin'dir. Moleküler koordinatlar ve projection ağırlıkları tek başına önem/SHAP/nedensel açıklama değildir;burada yalnız gerçek eğitim ürününü gösterir. WP11 açıklanabilirlik çalışması yapılmadı.

## 7. Aynı gerçek ilacın dört modelde kayıt sıralaması''')
    code(r'''rank=pd.read_csv(QA/'example_drug_PT_ranking.csv')
display(rank[rank['rank'].le(10)][['model','rank','class_id','PT_name','observed_record_s','score_observed_record_proxy']])
names=rank[rank.model.eq('A1P1')].sort_values('rank').head(12).set_index('class_id')
fig,ax=plt.subplots(figsize=(12,7));yy=np.arange(len(names));width=.18
for j,name in enumerate(NAMES):
    rows=rank[rank.model.eq(name)].set_index('class_id').loc[names.index]
    ax.barh(yy+(j-1.5)*width,rows.score_observed_record_proxy,height=width,label=name)
ax.set_yticks(yy,[r.PT_name+(' [SIDER]' if r.observed_record_s else ' [unknown]') for r in names.itertuples()],fontsize=8)
ax.set(xlabel='Observed-record sigmoid sıralama skoru • klinik olasılık değil',xlim=(0,1),title=example['name']+' • aynı test ilacı ve aynı PT hedefleri');ax.invert_yaxis();ax.legend(fontsize=8)
plt.tight_layout();plt.savefig(FIG/'07_actual_drug_rankings.png',dpi=160);plt.show()''')
    md('''**Yorum:**Çizilen hedefler A1P1'in kaydedilmiş ilk12 PT sırasıdır;tablo her dört modelin kendi ilk10'unu da gösterir. Bütün skorlar aynı frozen test ilacının OOF CSV kaydından gelir. Unknown yüksek skorlar kesin yanlış pozitif veya klinik olay diye adlandırılmaz. Gösterim bir tedavi önerisi,klinik risk hesabı veya vaka doğrulaması değildir.

## 8. Testler,provenans ve durma noktası''')
    code(r'''text=(QA/'tests_actual_trainer.txt').read_text(encoding='utf-8-sig');print(text[-500:])
display(pd.read_csv(QA/'feature_fit_provenance.csv').head(4))
display(pd.DataFrame([json.loads((QA/'evaluation_complete.json').read_text(encoding='utf-8'))]).drop(columns=['semantics']))
display(pd.read_csv(QA/'fold_train_validation_test_scope.csv').head(8))''')
    md('''**Yorum:**Gerçek trainer testleri train-only PT/ID veproxy desteği,heldout label/value mutation,forward/gradient eşitliği,optimizer,girdi izolasyonu,NPZ skor veouter fit tekrar üretimi,ortak anahtarlar vefactorial aritmetiği kapsar. Kontrollü RAM test fitleri üretim modellerini değiştirmez;yeniden ayarlama değildir. Bütün kaynak/encoder/baseline/WP09 çıktıları hash ile korunur.

**WP10 gerçek eğitim ve değerlendirme tamamlandığında durulur. Sonuçlar observed-record proxy ve keşifseldir. Atom/PPI katkısının düşük veya belirsiz olması gizlenmez. WP11'e geçmek için kullanıcı onayı gerekir.**''')
    book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'},'language_info':{'name':'python'}})
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            buffer=io.BytesIO();plt.figure(i).savefig(buffer,format='png',dpi=100,bbox_inches='tight');display(Image(data=buffer.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for i,c in enumerate(cells):
        if c.cell_type=='code':compile(c.source,f'WP10 training cell{i}','exec')
    for c in cells:
        if c.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:r=shell.run_cell(c.source,store_history=False)
        if r.error_before_exec or r.error_in_exec:raise RuntimeError(r.error_before_exec or r.error_in_exec)
        c.execution_count=n;c.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nb.v4.new_output('stream',name=name,text=value))
        for out in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in out.data.items()}
            c.outputs.append(nb.v4.new_output('display_data',data=data,metadata=out.metadata))
    nb.validate(book);nb.write(book,path);print('Executed factorial results notebook:',n,'cells,7 PNG,no refit')


if __name__=='__main__':main()
