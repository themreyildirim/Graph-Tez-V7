"""WP11 yeni notebook'u kayıtlı gerçek SHAP tablolarından çalıştırır; fit yok."""
from wp09_close_wp10_notebooks import INIT
from pathlib import Path
import base64,io,json,os


def execute(name,parts):
    """Yalnız bu turdaki yeni WP11 taslağı yenilenebilir; kabul edilmiş dosya yasak."""
    import nbformat as nb
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    root=Path(__file__).resolve().parents[1];target=root/'notebooks'/name
    prior=json.loads((root/'reports/qa/WP11/B1_SHAP_v1/prior_artifacts_sha256.json').read_text())
    if name!='WP11_B1_SHAP.ipynb' or target.relative_to(root).as_posix() in prior:raise RuntimeError('Accepted notebook is read-only')
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            stream=io.BytesIO();plt.figure(i).savefig(stream,format='png',dpi=100,bbox_inches='tight');display(Image(data=stream.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(root);shell=InteractiveShell.instance();cells=[];n=0
    for kind,source in parts:
        cell=nb.v4.new_markdown_cell(source) if kind=='md' else nb.v4.new_code_cell(source)
        if kind=='code':
            compile(source,name,'exec');n+=1
            with capture_output(display=True) as cap:result=shell.run_cell(source,store_history=False)
            if result.error_before_exec or result.error_in_exec:raise RuntimeError(result.error_before_exec or result.error_in_exec)
            cell.execution_count=n;cell.outputs=[]
            for label,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
                if value:cell.outputs.append(nb.v4.new_output('stream',name=label,text=value))
            for output in cap.outputs:
                data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in output.data.items()}
                cell.outputs.append(nb.v4.new_output('display_data',data=data,metadata=output.metadata))
        cells.append(cell)
    notebook=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'},'language_info':{'name':'python'}})
    nb.validate(notebook);nb.write(notebook,target);print(name,n,'executed cells')


def main():
    parts=[('md','''# WP11 · B1 kimya modelini SHAP ile açıklamak

**Aşama 1: kayıtlı model, gerçek test ilaçları, yeniden eğitim yok.** Açıklama “model hangi sayısal girdiyi nasıl kullandı?” sorusuna yanıt verir; “ilaç neden yan etki yapar?” veya bireysel klinik risk sorusuna yanıt vermez. Unknown çiftler doğrulanmış biyolojik negatif değildir.

10 seçilmiş outer PT–B1 modeli açıklanır. Yöntem, background ve alfabetik örnekler açıklama hesabından önce `policy_v1.json` ve hash kaydıyla sabitlendi. Kodlar etiket değeri okumaz; var olan OOF skorları yalnız eşitlik kontrolünde kullanılır.

## 1. Exact linear SHAP: hangi çıktı ve hangi referans?

Altı girdi için `v(S)=mean_train f(x_S,B_notS)` tanımlanır. Kayıtlı doğrusal logitte `φ_i=w_i(x_i−mean_train_i)`, `base=b+w·mean_train` ve `base+Σφ=z` tamdır. Bu **interventional** oyun kimyasal bağımlılıklara koşullamaz. Kelime biyolojik müdahale/nedensellik iddiası değildir. [Resmî LinearExplainer belgesi](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html) bu formülü açıklar. SHAP paketi kurulu olmadığından formül doğrudan uygulanmış, seçilmiş her örnekte 64 koalisyon ile bağımsız doğrulanmıştır.

Katkı birimi **logit**tir. Sigmoid skoruna katkılar doğrudan eklenmez; `expit(base+Σφ)` mevcut observed-record skorunu verir. [Resmî lojistik regresyon örneği](https://shap.readthedocs.io/en/latest/example_notebooks/tabular_examples/linear_models/Sentiment%20Analysis%20with%20Logistic%20Regression.html) ölçek ayrımını gösterir.'''),('code',INIT+r'''
Q=ROOT/'reports/qa/WP11/B1_SHAP_v1'
F=ROOT/'reports/figures/WP11/B1_SHAP_v1';F.mkdir(parents=True,exist_ok=True)
policy=json.loads((Q/'policy_v1.json').read_text(encoding='utf-8'))
summary=json.loads((Q/'analysis_summary.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'yöntem':policy['method'],'ölçek':policy['output_scale'],'background':policy['background'],'ön_kayıt':policy['status']}]).T)
display(pd.DataFrame([summary['max_errors']]).T.rename(columns={0:'en_büyük_mutlak_fark'}))
coverage=pd.read_csv(Q/'coverage_summary.csv');display(coverage)
'''),('md','''**Yorum:** Model ağırlıkları ve scaler'lar değişmedi. Background yalnız uygun train ilaçlarıdır; her modelde 42–45 ilaç vardır. Hesaplanan 27.854 yerel model çıktısı ve 167.124 özellik katkısı yeni performans değerlendirmesi değildir. Toplamsallık farkı yaklaşık 3,6×10⁻¹⁵; kayıtlı OOF skor farkı 3,3×10⁻¹⁶'dır.

## 2. Hangi ilaç/PT için açıklama var?'''),('code',r'''
membership=pd.read_csv(Q/'background_test_membership.csv')
display(membership[membership.role.eq('TEST_ABSTAIN_QC')].assign(protocol=lambda x:x.context.str.split('_').str[0]).groupby('protocol').drug_id.agg(list).rename('açıklanmayan_8_ilaç'))
targets=pd.read_csv(Q/'target_coverage.csv');display(targets[targets.status.ne('explained')])
fig,axs=plt.subplots(1,2,figsize=(12,4.4))
for ax,p in zip(axs,['primary','stress']):
    d=coverage[coverage.protocol.eq(p)]
    ax.bar(d.outer_fold,d.test_explained,label='B1 açıklanabilir',color='#527d91')
    ax.bar(d.outer_fold,d.test_abstain,bottom=d.test_explained,label='Kimya abstention',color='#d0a371')
    ax.set(title=p+' · gerçek test kapsamı',xlabel='Outer fold',ylabel='İlaç sayısı',xticks=range(1,6),ylim=(0,15))
axs[1].legend(fontsize=8);plt.tight_layout();plt.savefig(F/'01_explanation_scope.png',dpi=160);plt.show()
'''),('md','''**Grafik 1 — Ne öğrendik?** 62 ilaç envanterde kalır; her protokolde 54 gerçek test ilacı açıklanır. Sekiz kimya-QC abstention için sıfır katkı veya sahte skor yazılmaz. Primary outer3 ve stress outer5'te birer declared PT için classifier fit edilmemiştir; bunlar NA kalır. PT sayısı foldda değişir, bütün 1.061 kaynak PT açıklanmış değildir.

## 3. Beş kimyasal alan ile availability maskesi

MW molekül ağırlığı, LogP lipofilisite betimi, HBD/HBA hidrojen bağı verici/alıcı sayısı, TPSA polar yüzey alanıdır. WP04'teki mevcut temiz sayılar kullanılır. B1 girdileri train-only standartlaştırılmıştır; SHAP'ın birimi ise logittir. Affine standartlaştırma altında ham birimler ile SHAP eşitliği ayrıca test edilmiştir.'''),('code',r'''
bg=pd.read_csv(Q/'background_summary.csv');display(bg[bg.context.eq('primary_o01_final')])
global_summary=pd.read_csv(Q/'global_common_summary.csv')
common=json.loads((Q/'common_PT_intersections.json').read_text(encoding='utf-8'))
features=policy['features'];labels=['MW','LogP','HBD','HBA','TPSA','Kimya maskesi']
display(global_summary)
fig,axs=plt.subplots(1,2,figsize=(12,4.8))
for ax,p in zip(axs,['primary','stress']):
    d=global_summary[global_summary.protocol.eq(p)].set_index('feature').loc[features]
    ax.barh(labels,d.mean_abs,color=['#527d91']*5+['#ba9470']);ax.invert_yaxis()
    ax.set(title=f'{p}: 54 ilaç × {len(common[p])} ortak PT',xlabel='Ortalama |SHAP| · logit')
    for i,v in enumerate(d.mean_abs):ax.text(v+.002,i,f'{v:.3f}',va='center',fontsize=9)
    ax.set_xlim(0,.36)
plt.tight_layout();plt.savefig(F/'02_global_common_PT_SHAP.png',dpi=160);plt.show()
'''),('md','''**Grafik 2 — Ne öğrendik?** Primary beş-fold PT kesişimi 201, stres kesişimi 186'dır. Primary'de ortalama mutlak katkı HBD için 0,206; stres özetinde LogP için 0,301 logittir. Aynı biyolojik önem sırası elde edildiği iddia edilemez: hedef kesişimleri ve kayıtlı fold modelleri farklıdır. Bu betimsel ortak-kapsam özetidir; ilk/global esas tablo her model–PT için ayrı tutulur.

Maske tüm uygun train/test ilaçlarında 1 olduğu için referanstan farkı ve SHAP değeri sıfırdır. Kayıtlı maskenin katsayısı sıfır olmak zorunda değildir; sabit etkisi base'e dahildir. Bu, eksik kimya durumunun modelce öğrenildiği veya önemsiz olduğu anlamına gelmez.

## 4. Başarıya bakılmadan seçilmiş gerçek local açıklamalar

Her bağlamda alfabetik ilk iki uygun test ID'si ve ilk iki fit edilmiş CUI seçilmiştir. Aşağıdaki 40 örnek, etiket/skor büyüklüğü ya da doğru tahmin ölçütü kullanılmadan önceden donduruldu. Waterfall her protokolün outer1 ilk örneğidir.'''),('code',r'''
examples=pd.read_csv(Q/'examples_frozen_before_explanations.csv')
local=pd.read_csv(Q/'local_shap.csv');pairs=pd.read_csv(Q/'local_pair_outputs.csv')
example_local=pd.read_csv(Q/'example_local_shap.csv')
names=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['id','name']).drop_duplicates().set_index('id')['name'].to_dict()
case_table=examples.merge(pairs,on=['context','protocol','drug_id','class_id'],validate='one_to_one')
case_table.insert(3,'drug_name',case_table.drug_id.map(names));display(case_table[['context','drug_id','drug_name','class_id','base','sum_phi','logit','proxy_score']])
def waterfall(protocol,filename):
    e=examples[examples.context.eq(protocol+'_o01_final')].iloc[0]
    vals=example_local[(example_local.context==e.context)&(example_local.drug_id==e.drug_id)&(example_local.class_id==e.class_id)].set_index('feature').loc[features]
    out=pairs[(pairs.context==e.context)&(pairs.drug_id==e.drug_id)&(pairs.class_id==e.class_id)].iloc[0]
    display(vals[['raw_value','standardized_value','background_mean_standardized','coefficient','SHAP_logit','term']])
    fig,axs=plt.subplots(2,1,figsize=(11,7),gridspec_kw={'height_ratios':[1,3]})
    contributions=vals.SHAP_logit.to_numpy();trajectory=np.r_[out.base,out.base+np.cumsum(contributions)]
    span=max(np.ptp(trajectory),.06);texts=['Base']+labels+['Logit']
    for ai,ax in enumerate(axs):
        position=out.base;ax.bar(0,position,color='#8c99a0')
        for i,value in enumerate(contributions,1):
            ax.bar(i,abs(value),bottom=min(position,position+value),color='#ba6a62' if value>0 else '#527d91')
            ax.plot([i-1,i],[position,position],color='#bfc4c7',linestyle=':',linewidth=1)
            if ai==1:ax.annotate(f'{0. if abs(value)<1e-12 else value:+.4f}',(i,position+value/2),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
            position+=value
        ax.bar(7,out.logit,color='#655784');ax.set_xticks(range(8),texts,rotation=20 if ai else 0,ha='right' if ai else 'center')
        ax.set_ylabel('Proxy logit')
        if ai==0:ax.axhline(0,color='gray',linewidth=.7)
        else:ax.set_ylim(trajectory.min()-.4*span,trajectory.max()+.4*span);ax.set_title('Aynı waterfall · referans çevresinde yakın plan (sıfır bu panelin dışında)',fontsize=10)
    axs[0].set_title(f'{protocol} · {names.get(e.drug_id,e.drug_id)} ({e.drug_id}) → {e.class_id}\n{vals.term.iloc[0]} · sigmoid={out.proxy_score:.4f} (klinik risk değil)',fontsize=11)
    fig.text(.1,.015,f'base {out.base:.6f} + katkılar {out.sum_phi:+.6f} = logit {out.logit:.6f}',fontsize=10)
    plt.tight_layout(rect=(0,.04,1,1));plt.savefig(F/filename,dpi=160);plt.show()
waterfall('primary','03_local_primary_waterfall.png')
'''),('md','''**Grafik 3 — Ne öğrendik?** Doxycycline (DB00254)–C0000731 örneğinde katkılar ilgili train referansına göre okunur. Mavi eksi katkı kimyasal alanın bu kayıtlı modelin logitini aşağı, kırmızı artı katkı yukarı taşıdığını gösterir. Bu mekanizma veya klinik koruyuculuk değildir. Base zaten train kayıt önseli, intercept ve sabit maskenin katkısını içerir. Düşük katkı modelin belirsizliğini ölçmez.'''),('code',r'''
waterfall('stress','04_local_stress_waterfall.png')
'''),('md','''**Grafik 4 — Ne öğrendik?** Stres outer1'in alfabetik ilk örneği ayrı model ve ayrı train referansı ile açıklanır. Buradaki katkı büyüklüklerini primary örneğiyle eşit biyolojik etki ölçeği sayamayız. İki grafik de gerçek kayıtlı test girdileri ve model ağırlıklarından hesaplanmıştır; temsili veri kullanılmamıştır.

## 5. Bir PT'yi foldlar arasında açıklamak'''),('code',r'''
native=pd.read_csv(Q/'global_native_context_PT.csv')
cui=common['primary'][0]
d=native[native.protocol.eq('primary')&native.class_id.eq(cui)].pivot(index='outer_fold',columns='feature',values='mean_abs').loc[range(1,6),features]
display(d)
fig,ax=plt.subplots(figsize=(10,4.4));im=ax.imshow(d,aspect='auto',cmap='Blues',vmin=0)
ax.set_xticks(range(6),labels);ax.set_yticks(range(5),['Fold '+str(i) for i in range(1,6)])
for i in range(5):
    for j in range(6):ax.text(j,i,f'{d.iloc[i,j]:.3f}',ha='center',va='center',fontsize=9)
ax.set_title(f'Primary · ortak ilk CUI {cui} · folda özgü mean |SHAP|')
fig.colorbar(im,ax=ax,label='Logit');plt.tight_layout();plt.savefig(F/'05_native_PT_fold_heatmap.png',dpi=160);plt.show()
'''),('md','''**Grafik 5 — Ne öğrendik?** Tek bir ortak CUI için bile katkılar train popülasyonu ve öğrenilmiş katsayılarla değişir. Her foldun ayrı tablosu korunmuştur. Eksik hedefler bu grafiğe sıfır olarak eklenmemiştir. Grafikteki fold farkı bir güven aralığı değildir.

## 6. Kararlılık: hesap aynı, referansa duyarlılık ayrı'''),('code',r'''
stability=pd.read_csv(Q/'stability_LOO.csv')
s=stability.groupby(['protocol','feature']).agg(max_shift=('max_abs_delta_SHAP','max'),mean_shift=('mean_abs_delta_SHAP','mean'),sign_flips=('nonzero_sign_flip_n','sum'),nonzero_comparisons=('nonzero_sign_comparisons','sum')).reset_index()
s['nonzero_sign_flip_fraction']=s.sign_flips/s.nonzero_comparisons.replace(0,np.nan)
display(s)
fig,axs=plt.subplots(1,2,figsize=(12,4.8))
for ax,p in zip(axs,['primary','stress']):
    d=s[s.protocol.eq(p)].set_index('feature').loc[features]
    ax.barh(labels,d.max_shift,color=['#527d91']*5+['#ba9470']);ax.invert_yaxis()
    ax.set(title=p+' · tüm train LOO referansları',xlabel='En büyük |ΔSHAP| · logit',xlim=(0,.2))
plt.tight_layout();plt.savefig(F/'06_background_LOO_sensitivity.png',dpi=160);plt.show()
display(pd.read_csv(Q/'consistency_checks.csv'))
display(pd.read_csv(Q/'enumeration_checks.csv'))
'''),('md','''**Grafik 6 — Ne öğrendik?** Tek train-background ilacı çıkarıldığında bazı katkılar değişir; en büyük kayma primary'de yaklaşık 0,169, stres'te 0,156 logittir. Bazı küçük katkıların işareti değişir. Model tahmini sabit kalır: base ve SHAP kaymaları birbirini dengeler. Bu exhaustive background duyarlılığıdır; yeniden fit, bootstrap CI veya dış doğrulama değildir. Tekrar hesabı aynıdır, sıra değişimi sayısal yuvarlama düzeyindedir.

40 gerçek örnekte 64 koalisyon hesabı kapalı formu yaklaşık 8,9×10⁻¹⁶ en büyük farkla doğruladı. Ham/standartlaştırılmış alan açıklamaları da uyuştu. MW/TPSA/HBA gibi alanlar ilişkili olabilir; korelasyona koşullayan SHAP başka paylaştırmalar üretebilir. Bu aşamada sonuçlara göre alternatif açıklayıcı seçilmedi.

## 7. Testler, provenans ve koşullu graf yöntemi'''),('code',r'''
print((Q/'tests_v1.txt').read_text(encoding='utf-8'))
display(pd.DataFrame([{'önceki_korunan_dosya':summary['preserved_prior_files'],'model_fit':summary['model_fit'],'protein_PPI_attribution':summary['graph_attribution'],'WP12':summary['WP12'],'test_etiketi_okundu':summary['test_outcomes_read']}]))
print('Graf yöntem önerisi:',ROOT/'docs/plan/WP11_A1P1_GRAPH_EXPLANATION_CONTRACT_v1.md')
'''),('md','''**Son sınır:** 18 test geçti. B0/B1/B2 ve WP09/WP10 ağırlıkları, sonuçları, splitleri ve QC kararları değişmedi. `local_shap.csv` tüm yerel katkıları, `global_native_context_PT.csv` model–PT özetlerini, `global_common_summary.csv` açık kesişim özetini saklar. Sekiz abstention ve fit edilmemiş PT'ler görünür kalır.

Kayıtlı WP10 A1P1 için ayrı yöntem sözleşmesi hazırlanmıştır: önerilen birincil işlem sabit-orijinal-derece mesaj maskesi; fiziksel kenar silme/yeniden normalizasyon ayrı duyarlılıktır. Dört protein rolü ayrı kalır, query readout ile paylaşılan train cache değişimleri ayrılır. **Bu notebook protein/kenar attribution hesaplamaz.** Grafik aşaması için onay beklenir. Yeni eğitim, WP12 veya klinik nedensellik/risk iddiası yoktur.''')]
    execute('WP11_B1_SHAP.ipynb',parts)


if __name__=='__main__':main()
