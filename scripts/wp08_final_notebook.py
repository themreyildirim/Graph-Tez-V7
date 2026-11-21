"""Yalnız kayıtlı sonuçları gösteren, çalıştırılmış WP08 kapanış notebook'u."""
from pathlib import Path
import base64
import io
import os
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(text):cells.append(nbf.v4.new_markdown_cell(text))
    def code(text):cells.append(nbf.v4.new_code_cell(text))
    md('''# WP08 — B0/B1/B2 ilk deney fazının kapanışı

Kullanıcı B0/B1/B2 sonuçlarını ve ilk fazın bu modellerle kapanmasını kabul etti. ATC, Random Forest, kimya MLP ve protein-mean MLP **yapılmadı; ilk faz dışında ertelendi**. ROADMAP ve eski deneyler korunur. Bu notebook yalnız mevcut sonuçları okur; model fit, yeni tahmin, hiperparametre araması veya WP09 encoder içermez.

**Görev SIDER'da gözlenen kayıtları yeni ilaçlar için sıralamak. Unknown gerçek negatif değildir; klinik yan etki olasılığı, nedensellik veya hasta güvenliği doğrulaması yapılmadı.** B0 ilk B1/B2 sonuçları görüldükten sonra eklenen keşifsel referanstır. Sonuç kaynakları, QA dizinleri ve hash'ler aşağıda açıkça gösterilir.''')
    code('''from pathlib import Path
import json,numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').is_file():
    if ROOT.parent == ROOT: raise RuntimeError('Proje kökü bulunamadı')
    ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP08/final_closure_v1'
B0=ROOT/'reports/qa/WP08/B0_frequency_reference_v1'
FIG=ROOT/'reports/figures/WP08/final_closure_v1';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_columns',18);pd.set_option('display.max_colwidth',100)
metrics=pd.read_csv(QA/'accepted_paired_metrics.csv')
delta=pd.read_csv(QA/'accepted_paired_differences.csv')
audit=json.loads((QA/'integrity_audit.json').read_text(encoding='utf-8'))
contract=json.loads((QA/'WP09_comparison_contract_draft.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'ilk_faz':'KAPANDI: B0/B1/B2','baseline_sürümü':audit['old_models']['version'],
                      'B0_sürümü':audit['B0']['version'],'seed':audit['seed'],
                      'ilaç':audit['source_PT']['drugs'],'kaynak_PT':audit['source_PT']['PT_CUI'],
                      'kaynak_pozitif_çift':audit['source_PT']['positive_pairs'],
                      'WP09_eğitim_onayı':contract['WP09_training_authorized']}]))
display(pd.read_csv(QA/'scope_disposition.csv'))''')
    md('''**Yorum:** B1/B2 için model sürümü değişmedi. Kapanış kapsam kararı, yapılmamış roadmap varyantlarını tamamlanmış yapmaz. B0'ın girdisiz nüfus referansı verebilmesi Methenamine'in B1/B2 abstention'ını kaldırmaz.

## 1. Aynı 54 ilaç ve aynı PT anahtarlarında karşılaştırma''')
    code('''ap=metrics[metrics.metric.eq('drug_macro_AP')]
display(ap[['protocol','model','estimate','CI95_low','CI95_high','valid_bootstrap_replicates']])
selected=delta[delta.metric.eq('drug_macro_AP') & ((delta['first'].eq('B1') & delta.reference.eq('B0_like_B1')) | (delta['first'].eq('B2') & delta.reference.isin(['B0_like_B2','B1'])))]
display(selected[['protocol','first','reference','first_minus_reference','CI95_low','CI95_high']])
order=['B0_like_B1','B1','B0_like_B2','B2'];colors=['#8a9b72','#537e9e','#8a9b72','#b28560']
fig,axs=plt.subplots(1,2,figsize=(12,4.8),sharey=True)
for ax,protocol,title in zip(axs,['primary','stress'],['Ana connectivity','Ayrı yapı stresi']):
    sub=ap[ap.protocol.eq(protocol)].set_index('model').loc[order]
    for i,(model,row) in enumerate(sub.iterrows()):
        ax.errorbar(i,row.estimate,yerr=[[row.estimate-row.CI95_low],[row.CI95_high-row.estimate]],fmt='o',color=colors[i],capsize=5)
        ax.annotate(f'{row.estimate:.4f}',(i,row.estimate),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9)
    ax.set_xticks(range(4),order,rotation=20,ha='right');ax.set(title=title,ylim=(0,1),ylabel='Drug-macro observed-record AP')
fig.suptitle('Ortak54 • aynı ilaç/PT kapsamı • koşullu grup CI',fontsize=12)
plt.tight_layout();plt.savefig(FIG/'01_accepted_paired_AP.png',dpi=160);plt.show()''')
    md('''**Yorum:** Ana B1=0,6556 ile eşleşen B0=0,6438 arasındaki +0,0119 farkın CI'ı sıfırı içerir; ek başarı henüz belirgin değildir. B2=0,6262, kendi B0=0,6466 referansını geçmedi; stres farkı da düşük kaldı. Bu koşullu CI'lar bağımsız dış doğrulama değildir.

B2'nin 61 ilaçta input bulması kapsam kazancıdır; ortak54'te performans artışı değildir. Küçük örneklemde 234 giriş alanı, rol ortalamasının bilgi kaybı ve farklı biyolojik/kayıt mekanizmaları **olası açıklamalar**dır; bunları neden diye kanıtlayan yeni deney yapılmadı. B0/B1 AP oranı açıklanan nedensel yüzde olarak hesaplanmaz.

## 2. Aynı PT'de ilaçları sıralamak ile aynı ilaçta PT'leri sıralamak''')
    code('''diag=pd.read_csv(B0/'within_fold_AUROC_descriptive_mean.csv')
pooled=metrics[metrics.protocol.eq('primary')&metrics.metric.eq('class_macro_AUROC')][['model','estimate']]
comparison=pooled.merge(diag[diag.protocol.eq('primary')][['model','descriptive_mean_of_5_fold_class_AUROC']],on='model')
display(comparison);display(diag[['protocol','model','descriptive_mean_of_5_fold_class_AUROC','CI_status']])
order=['B0_like_B1','B0_like_B2','B1','B2'];p=comparison.set_index('model').loc[order]
fig,ax=plt.subplots(figsize=(9,4.8));x=np.arange(4)
ax.bar(x-.18,p.estimate,.36,label='Pooled OOF class-AUROC',color='#7295ac')
ax.bar(x+.18,p.descriptive_mean_of_5_fold_class_AUROC,.36,label='Fold içi ortalama: betimleyici',color='#b99c76')
ax.axhline(.5,color='gray',ls='--',lw=1);ax.set_xticks(x,order);ax.set(ylim=(0,1),ylabel='Observed-record class-AUROC',title='Ana protokol • farklı özetlerin yorum sınırı');ax.legend(fontsize=9)
plt.tight_layout();plt.savefig(FIG/'02_AUROC_interpretation.png',dpi=160);plt.show()''')
    md('''**Yorum:** Drug-AP ilaç içinde PT sıralaması; class-AUROC aynı PT için ilaç sıralamasıdır. B2'nin pooled class-AUROC artışı birincil drug-AP kaybını telafi eden genel üstünlük değildir. B0 fold/PT içinde sabit skor verdiğinden tanımlı AUROC=0,5'tir. Pooled sonuçtaki yaklaşık0,32, farklı fold train frekanslarının/skor ölçeklerinin ve değişen sözlüklerin birleşmesinden etkilenir. B0 ters biyolojik tahmin yapıyor sonucu çıkarılmaz. Foldlar bağımsız tekrar değildir; betimleyici ortalamaya t-CI veya yeni seçim uygulanmadı.

## 3. Kaynak PT uzayı, unknown ve kapsam dışı pozitifler''')
    code('''coverage=pd.read_csv(QA/'accepted_primary_coverage.csv')
display(coverage[coverage.model.eq('B0_all_train')].drop(columns=['semantics']))
c=coverage[coverage.scope.eq('paired54') & coverage.model.eq('B0_all_train')].iloc[0]
display(pd.DataFrame([{'ortak_ilaç':c.scored_drugs,'skorlanan_çift':c.scored_pairs,
    'pozitif':c.observed_positive_scored,'unknown_gerçek_negatif_değil':c.unknown_scored_NOT_verified_negative,
    'bu_ilaçlarda_kaynak_pozitif':c.source_positive_for_scored_drugs,
    'skor_sözlüğü_dışında_pozitif':c.out_of_scored_vocab_positive,'tüm62_kaynak_PT':1061}]))
fig,axs=plt.subplots(1,2,figsize=(11,4.8))
axs[0].bar(['Gözlenen pozitif','Unknown'],[c.observed_positive_scored,c.unknown_scored_NOT_verified_negative],color=['#739d8c','#b1bbce'])
axs[0].set(title='13.964 skorlanan çift',ylabel='Çift sayısı')
axs[1].bar(['Skor kapsamı','Sözlük/fit dışı'],[c.observed_positive_scored,c.out_of_scored_vocab_positive],color=['#739d8c','#bf9177'])
axs[1].set(title='Aynı54 ilaçta 5.505 kaynak pozitif',ylabel='Pozitif çift sayısı')
for ax in axs:
    for bar in ax.patches:ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+80,str(int(bar.get_height())),ha='center')
    ax.margins(y=.18)
plt.tight_layout();plt.savefig(FIG/'03_target_coverage_limits.png',dpi=160);plt.show()''')
    md('''**Yorum:** 1.685 kapsam dışı kaynak pozitif, ortak54'ün folda özgü skorlanmayan pozitifleridir; bütün62 için eksik/yanlış-negatif sayısı değildir. Skorlanmayan PT'ler ve NA sınıflar sıfır başarıya çevrilmedi. Kaynak evren 1.061 PT iken pooled ortak kapsam306 CUI, class metriği tanımlı256/NA50'dir. Tüm1.061 PT uzayında performans iddiası kurulamaz. Unknown, kesin negatif veya biyolojik yokluk değildir. İki grafiğin paydaları farklıdır ve açık gösterilmiştir.

## 4. WP09 için plan: onay kapısı''')
    code('''topology=pd.read_csv(QA/'WP09_train_only_topology_preflight.csv')
summary=topology.groupby(['protocol','threshold']).agg(train_human_min=('strict_human_train_nodes','min'),train_human_max=('strict_human_train_nodes','max'),pairs_min=('undirected_PPI_pairs','min'),pairs_max=('undirected_PPI_pairs','max'),isolates_max=('isolated_human_nodes','max')).reset_index()
display(summary)
display(pd.DataFrame([{'sözleşme_sürümü':contract['version'],'WP09_uygulama_onayı':contract['WP09_implementation_authorized'],
    'WP09_eğitim_onayı':contract['WP09_training_authorized'],'eşik':contract['graph']['threshold'],
    'K12_kenarı_insan_ağında':contract['graph']['K12_MG1655_23_conditional_edges_in_human_graph'],
    'context80':contract['graph']['context80'],'sonuç_sonrası_keşifsel':contract['exploratory_after_seen_baselines']}]))
display(pd.DataFrame({'zorunlu_ablation':contract['ablations']}))
display(pd.DataFrame({'uygulama_öncesi_onay_konuları':contract['open_approval_items']}))''')
    md('''**Yorum:** Bu tablo mevcut küçük WP06 kaynak tablosundan yalnız train protein evreninin topolojik ön kontrolüdür; eğitim grafı oluşturulmadı. 63 kesin insan düğümünün tamamı her foldta bulunmaz; eşik400/700/900 henüz seçilmedi. İzole/PPI'sız proteinler silinmez; 23 koşullu K12/MG1655 kenarı insan ağına eklenmez; özellik eksik80 context yoktur.

Plan, aynı mimaride noPPI/realPPI/shuffledPPI, ayırt edici forward ve gradient testleri, aynı frozen split/PT/input kapsamı gerektirir. Bunlar **henüz uygulanmış testler değildir**. Model kapasitesi/optimizer/early-stop/null politikası ve uygulama onayı açık kalır. Daha önce görülen outer sonuçlar WP09'da seçim için kullanılamaz; aynı veride gelecekteki kıyas keşifseldir.

## 5. Kapanış denetimi''')
    code('''tests=pd.read_csv(QA/'existing_test_suite_results.csv')
display(tests[['suite','tests','unittest_seconds','passed','persistent_model_or_score_writes']])
display(pd.DataFrame([{'mevcut_test_sayısı':int(tests.tests.sum()),'tümü_geçti':bool(tests.passed.all()),
    'korunan_dosya':audit['accepted_artifacts']['files_checked'],'değişen_dosya':len(audit['accepted_artifacts']['changed']),
    'ham_içerik_tekrar_taraması':audit['raw_content_rescan_or_hash'],
    'WP09_eğitim_onayı':audit['WP09_training_authorized']}]))
display(pd.DataFrame(audit['raw_metadata_only']))
display(pd.DataFrame([{'split_file':k,'SHA256':v} for k,v in audit['frozen_split_manifest'].items()]))''')
    md('''**Yorum:** Mevcut103 test yeniden geçti; eski test logları, modeller, skorlar ve QC kararları korunur. Baseline unit testleri yalnız RAM'de küçük fit/mutasyon/tekrar üretim kontrolleri yapar; yeni deney modeli yazmaz. Ham büyük kaynaklarda sadece boyut/mtime kontrolü yapıldı, tam içerik hash doğrulaması tekrarlanmadı.

Sonuçlar kaynak kayıt sıralamasına özgüdür. Koşullu grup CI, bütün yeniden eğitim belirsizliği veya bağımsız dış doğrulama değildir. Klinik olasılık, nedensellik ve hasta güvenliği sonucu çıkarılmaz.

[Kapanış raporu](../reports/WP08_FINAL_CONCLUSIONS.md) ve [WP09 taslak sözleşmesi](../docs/plan/WP09_COMPARISON_CONTRACT_DRAFT.md) ayrıntıları içerir. **WP08 ilk faz kapandı; WP09 uygulaması kullanıcı onayını bekliyor.**''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},
        'language_info':{'name':'python'}})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for number in plt.get_fignums():
            buffer=io.BytesIO();plt.figure(number).savefig(buffer,format='png',dpi=100,bbox_inches='tight')
            display(Image(data=buffer.getvalue()))
        plt.close('all')
    plt.show=show
    shell=InteractiveShell.instance();os.chdir(ROOT);count=0
    for i,cell in enumerate(cells):
        if cell.cell_type=='code':compile(cell.source,f'WP08 closure cell {i}','exec')
    for cell in cells:
        if cell.cell_type!='code':continue
        count+=1
        with capture_output(display=True) as captured:result=shell.run_cell(cell.source,store_history=False)
        if result.error_in_exec or result.error_before_exec:raise RuntimeError(result.error_in_exec or result.error_before_exec)
        cell.execution_count=count;cell.outputs=[]
        for name,value in [('stdout',captured.stdout),('stderr',captured.stderr)]:
            if value:cell.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for output in captured.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in output.data.items()}
            cell.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=output.metadata))
    nb.cells=cells;nbf.validate(nb)
    nbf.write(nb,ROOT/'notebooks/WP08_final_conclusions.ipynb')
    print(f'Executed closure notebook: {count} code cells, 3 scientific PNG figures; no model training')


if __name__=='__main__':main()
