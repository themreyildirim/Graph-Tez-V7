"""Son null kapısını öğreten, yalnız kayıtlı topoloji/plan QA'sını okuyan notebook."""
from pathlib import Path
import os,io,base64
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP09 — Null politikası ve son eğitim kapısı v3

**Bu notebook model kurmaz/fit etmez, optimizer çalıştırmaz ve gerçek PT skoru üretmez.** Kabul edilen encoder ve bütün önceki sonuçlar korunur.700 önerisi topoloji/null fizibilitesidir; tahmin performansından seçilmedi. İncelenen soru: başarısız degree-preserving null nasıl açıklanır ve bütün modellerin karşılaştırılabilirliği nasıl korunur?

Tek v3 önerisi: aynı generator ve10E/max200E/%50 kuralı;önceden tanımlı3 null;ortak geçerli inner kesişimi;minimum2;başarısızlık NA. Üretim bütçesi/seed değiştirilmez. v3 training_enabled=False;ayrı onay beklenir.''')
    code(r'''from pathlib import Path
import json,re,numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').is_file():
    if ROOT.parent==ROOT:raise RuntimeError('Proje kökü bulunamadı')
    ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP09/null_gate_v3';FIG=ROOT/'reports/figures/WP09/null_gate_v3';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',140);pd.set_option('display.max_columns',20);pd.set_option('display.max_colwidth',120)
d=json.loads((QA/'failure_diagnosis.json').read_text(encoding='utf-8'))
c=json.loads((ROOT/'configs/WP09_training_PROPOSED_v3.json').read_text(encoding='utf-8'))
done=json.loads((QA/'null_preflight_complete.json').read_text(encoding='utf-8'))
rows=pd.read_csv(QA/'null_preflight_700_three_replicates.csv',keep_default_na=False)
scope=pd.read_csv(QA/'common_inner_outer_preflight.csv',keep_default_na=False)
display(pd.DataFrame([{'primary_eşik_önerisi':700,'onaylı_eşik':c['threshold']['approved_primary'],
    'null_adayı':len(rows),'tekrar':3,'korunan_dosya':done['prior_files_verified'],
    'eski40_r0_aynı':done['old_replicate_zero_40_exactly_reproduced'],'eğitim':c['training_enabled']}]))
display(pd.DataFrame([d]).T.rename(columns={0:'kanıt'}))''')
    md('''**Yorum:** Eski40 R0 seed/status/endpoint hash'i aynıdır.84 proteinli bağlamın PPI kenarlarına29 düğüm katılır;105 kenarda%50 için en az53 kenar değişmelidir. Eski51/105 endpoint NA kalır. Protein sayısı veya seed değiştirilmedi. Derece korunması endpoint farkının monoton artacağı anlamına gelmez.

## 1. Swap sayısı, farklı kalan eski kenar sayısı değildir''')
    code(r'''trace=pd.read_csv(QA/'failure_full_swap_trace.csv');first=trace[trace.accepted_swaps<=1050]
endpoints=pd.read_csv(QA/'failure_fixed_horizon_diagnostics.csv')
display(endpoints[['swaps_per_edge','attempts','accepted_swaps','shared_endpoint_rejections','existing_pair_rejections','removed_original_edges','changed_fraction','passes_change_rule']])
fig,ax=plt.subplots(figsize=(10,4.5));ax.plot(first.accepted_swaps,first.removed_original_edges,color='#64879d',lw=1)
ax.axhline(53,color='#a37d62',ls='--',label='Kabul için en az53 değişmiş eski kenar')
ax.scatter([1050],[51],color='#b25f50',zorder=4);ax.annotate('Önceden sabit endpoint:51 → NA',(1050,51),xytext=(-200,-25),textcoords='offset points',arrowprops=dict(arrowstyle='->'),fontsize=9)
ax.set(xlabel='Başarılı çift-kenar swap sayısı',ylabel='Orijinalden çıkarılmış farklı kenar',title='stress_o02_i02 • aynı seed • ilk1050 swap');ax.legend(fontsize=9)
plt.tight_layout();plt.savefig(FIG/'01_endpoint_trace.png',dpi=160);plt.show()''')
    md('''**Yorum:** 1050 swap3801 denemede tamamlandı;max21000 bütçe tükenmedi.637 ortak uç,2114 mevcut/duplicate yeni çift reddi var. Kümülatif822 orijinal çıkarma−771 geri ekleme=51 net değişim. Ara noktada63 değişmiş kenara ulaşılıp finalde51'e dönülmesi fiziksel/algoritmik “imkânsızlık” açıklamasını dışlar.50E/100E endpointleri bu yürüyüşte geçse de sadece tanısaldır;eski null'u değiştirmediler. İlk başarılı ara noktayı seçen yeni stop kuralı geriye dönük uygulanmadı. Daha uzun yürüyüş uniform mixing veya her zaman daha yüksek değişim garantisi değildir.

## 2. Aynı generator, üç önceden tanımlı tekrar''')
    code(r'''summary=rows.groupby('replicate').agg(aday=('context','count'),kabul=('status',lambda s:int(s.eq('OK_degree_preserving_null').sum())),
    minimum_değişim=('changed_fraction','min'),maksimum_değişim=('changed_fraction','max')).reset_index()
display(summary);display(rows[rows.status.ne('OK_degree_preserving_null')][['context','replicate','seed','changed_fraction','status','artifact_file']])
display(rows.pivot(index='context',columns='replicate',values='status'))
fig,ax=plt.subplots(figsize=(8,4.7))
for rep in range(3):
    sub=rows[rows.replicate.eq(rep)];offset=np.linspace(-.14,.14,len(sub))
    ax.scatter(rep+offset,sub.changed_fraction,c=np.where(sub.status.eq('OK_degree_preserving_null'),'#7095aa','#ba7c66'),s=28,alpha=.8)
    for failed in sub[sub.status.ne('OK_degree_preserving_null')].itertuples():
        ax.annotate(failed.context,(rep,failed.changed_fraction),xytext=(8,-20 if rep==1 else 12),textcoords='offset points',fontsize=7)
ax.axhline(.5,color='gray',ls='--');ax.set_xticks([0,1,2],['R0:eski seed','R1:+1.000.000','R2:+2.000.000'])
ax.set(ylim=(.4,.8),ylabel='Değişmiş orijinal çift payı',title='700 • sabit120 aday:117 geçerli /3 NA')
plt.tight_layout();plt.savefig(FIG/'02_three_null_replicates.png',dpi=160);plt.show()''')
    md('''**Yorum:** Tekrarlar en iyi seed'i seçmek için kullanılmaz. R0 her yerde eski adaydır;R1/R2 v2'de zaten yazılan seed formülünden gelir. Her tekrar gerçek grafla yeniden başlar. Aynı-degree/simple/aynı-node kısıtları,loop/duplicate reddi ve≥%50 endpoint testi tümünde aynıdır.3 NA iki inner contexttedir;geçerli diğer tekrarlar bunların yerine konmaz. Başarılı117 adaydan,eksik contextlerdeki3 başarılı aday da primary ortak kapsamdan çıkarılır:114 null kullanımlık plan,3 açık ek kapsam kaybı vardır.

## 3. Bütün modellerde ortak inner kapsam''')
    code(r'''display(pd.read_csv(QA/'failure_policy_options.csv'))
display(scope)
matrix=[];labels=[]
for row in scope.itertuples():
    valid={int(x) for x in row.common_valid_inner_folds.split(',') if x}
    matrix.append([int(i in valid) for i in (1,2,3)]+[int(row.outer_all_three_nulls_valid)])
    labels.append(f'{row.protocol} / outer{row.outer_fold}')
from matplotlib.colors import ListedColormap
fig,ax=plt.subplots(figsize=(8,5));ax.imshow(matrix,aspect='auto',vmin=0,vmax=1,cmap=ListedColormap(['#c88f79','#8ca999']))
ax.set_xticks(range(4),['Inner1','Inner2','Inner3','Outer-final']);ax.set_yticks(range(10),labels)
for i,row in enumerate(matrix):
    for j,value in enumerate(row):ax.text(j,i,'ORTAK' if value else 'NA / dışarıda',ha='center',va='center',fontsize=8)
ax.set_title('Yapısal preflight • bütün varyantlarda aynı kapsam\nModel/metrik uygunluğu henüz ölçülmedi')
plt.tight_layout();plt.savefig(FIG/'03_common_scope.png',dpi=160);plt.show()''')
    md('''**Yorum:** Primary outer2:inner2/3;stress outer2:inner1/3;diğer8 outer:inner1/2/3. Minimum2 ile10/10 outer topolojik olarak hazırdır. Bu durum model/metrik başarısı değildir. Minimum3 seçilse iki outer primary kıyas NA olacaktı. Model başına farklı foldlarla seçim yapmak karşılaştırılabilirliği bozar. Herhangi fit/metrik NA'sında yine bütün5 fit için ortak tanımlı kesişim alınır;düşük AP dışlama nedeni değildir. Kesişim<2 olursa bütün outer primary NA;outer-final null eksikse yine bütün triad NA. Mevcut frozen split/ID/sözlük değişmez;final fit yine aynı outer train'i kullanır.

## 4. Tek konfigürasyon ve doğru mimari adı''')
    code(r'''display(pd.read_csv(QA/'final_configuration_table.csv'))
fig,ax=plt.subplots(figsize=(11,4));ax.axis('off')
from matplotlib.patches import FancyBboxPatch
boxes=[(.02,.60,.29,.25,'BUGÜN:protein56 → PPI mesajı\n+4 rol readout'),(.02,.20,.29,.22,'BUGÜN:skaler kimya5\n+modalite maskeleri'),
    (.42,.43,.23,.25,'BUGÜN:ilaç temsili\nprotein-PPI model adayı'),(.74,.17,.24,.58,'EKLENMEDİ:molekül grafı\natom+bağ+stereo özellikleri\ngerçek molecular message passing\nilaç graph readout\nhiyerarşik füzyon/testler')]
for x,y,w,h,label in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.01',facecolor='#e4ecee' if x<.7 else '#f4eee7',edgecolor='#7d8c92',linestyle='--' if x>.7 else '-'))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=9)
for start,end in [((.31,.71),(.42,.59)),((.31,.31),(.42,.50))]:ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color='#657f8c',lw=1.8))
ax.set_title('Mevcut modelde ilaç atom–bağ GNN yok;tam moleküler GiG iddiası yok')
plt.tight_layout();plt.savefig(FIG/'04_architecture_scope.png',dpi=160);plt.show()''')
    md('''**Yorum:** Güncel model protein-PPI mesaj geçişli,rol readout ve skaler kimya dallıdır. Tam moleküler GiG için QC-doğrulanmış ilaç atom/bağ grafları,moleküler encoder/readout ve protein katmanıyla hiyerarşik füzyon gerekir;ilgili forward/gradient/ablation ve split kontrolleri ayrı uygulanır. Bunlar WP10 ve sonraki onaylı işlere aittir;bugün yapılmadı. Tablo gelecekteki AdamW/BCE/epoch ayarlarını önerir,hiçbiri çalıştırılmaz. Null generator/bütçe aynıdır;v3 yalnız tekrar,karşılaştırılabilirlik ve NA politikasını tamamlar.

## 5. Uygulanacak eğitim sırası — yalnız önizleme''')
    code(r'''schedule=pd.read_csv(QA/'training_sequence_PREVIEW_ONLY.csv')
display(schedule.groupby(['phase','variant']).size().rename('gelecekteki_koşullu_fit_sayısı').reset_index())
display(schedule.head(10))
sources=json.loads((QA/'training_preview_sources.json').read_text(encoding='utf-8'))
context='primary_o01_i01';src=sources[context]
display(pd.DataFrame([{'context':context,'graph_train_ids':src['graph_train_ids'],'fit_eligible_train_ids':src['fit_eligible_train_ids'],
    'validation_query_ids':src['validation_query_ids'],'test_query_ids':src['test_query_ids'],
    'declared_train_PT':len(src['declared_train_B2_PT']),'fittable_train_PT':len(src['fittable_train_B2_PT'])}]))''')
    md('''**Yorum:** 190 koşullu plan işi:140 inner,50 outer-final. Çalıştırılan fit sayısı0'dır. Her contextte real/noPPI ve3 shuffled aynı ID/hedef/hash/init ile planlanır. Önce kullanıcı onayı+hash doğrulama,sonra ortak inner fit/early-stop;en az2 geçerli inner epoch medyanıyla outer refit;en son aynı query kapsamı/paired karşılaştırma. PT hedef listeleri burada yalnız önceki kilitli train metadata'sıdır;null tanısına etiket matrisi veya performans girmez. Shuffled3 metriğinin eşit ortalaması özetlenir;PT skorları ensemble yapılmaz ve en iyi replica seçilmez. Gerçek sonuçlar alındıktan sonra yeni hyperparameter araması yoktur.

## 6. Test ve koruma''')
    code(r'''text=(QA/'test_results.txt').read_text(encoding='utf-8');test=re.search(r'Ran ([0-9]+) tests in ([0-9.]+)s',text)
display(pd.DataFrame([{'null_kapısı_testi':int(test.group(1)),'saniye':float(test.group(2)),'tümü_geçti':text.rstrip().endswith('OK'),
    'korunan_önceki_dosya':done['prior_files_verified'],'gerçek_model_fit':False,'optimizer':False,'PT_skoru':False,
    'eski_B0_B1_B2_değişti':False,'eğitim_onayı':c['training_enabled']}]))
display(pd.DataFrame([{'gelecek_eğitim_araştırma_sorusu':'SIDER observed-record sıralaması','unknown':'gerçek negatif değil',
    'klinik_risk_iddiası':False,'gelecek_kıyas':'WP08 sonuçları görülmüş olduğundan keşifsel'}]))''')
    md('''**Yorum:**18 test eski40 R0 endpoint'ini,seed/hash ve null derece/count basitgraf kısıtlarını,3 NA'nın dosya eksikliğini,ortak-fold/minimum2/outer-NA kusur enjeksiyonlarını ve aynı ID/PT/init planını doğrular. Önceki35 encoder testi korunur;bu ek yeniden encoder doğrulaması yapmış sayılmaz.62 ilaç,1061 PT ve6416 kaynak pozitif ilişkisi hash'le korundu;etiketler yeniden analiz edilmedi.

Kaynaklar yalnız yöntem içindir: [NetworkX double-edge-swap](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.swap.double_edge_swap.html),[Fosdick ve ark.](https://arxiv.org/abs/1608.00607),[Dutta ve ark.](https://arxiv.org/abs/2105.12120). Derece korumak uniform mixing kanıtı değildir;sonlu null tekrarı bağımsız dış doğrulama değildir.

[Tek nihai eğitim kapısı](../reports/WP09_FINAL_TRAINING_GATE.md) gerekçeyi ve sıralamayı içerir. **Model fit edilmedi;ayrı kullanıcı eğitim onayı bekleniyor.**''')
    notebook=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'},'language_info':{'name':'python'}})
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            buffer=io.BytesIO();plt.figure(i).savefig(buffer,format='png',dpi=100,bbox_inches='tight');display(Image(data=buffer.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();count=0
    for i,cell in enumerate(cells):
        if cell.cell_type=='code':compile(cell.source,f'Null gate cell{i}','exec')
    for cell in cells:
        if cell.cell_type!='code':continue
        count+=1
        with capture_output(display=True) as cap:result=shell.run_cell(cell.source,store_history=False)
        if result.error_in_exec or result.error_before_exec:raise RuntimeError(result.error_in_exec or result.error_before_exec)
        cell.execution_count=count;cell.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:cell.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for output in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in output.data.items()}
            cell.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=output.metadata))
    notebook.cells=cells;nbf.validate(notebook);nbf.write(notebook,ROOT/'notebooks/WP09_null_policy_review.ipynb')
    print(f'Executed null-policy notebook: {count} code cells /4 PNG; no model or optimizer')


if __name__=='__main__':main()
