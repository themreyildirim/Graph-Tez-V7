"""WP08 protokol keşfi notebook'u; gerçek çıktı, model sonucu yok."""
import os,io,base64
from pathlib import Path
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP08 — Tahmin ve değerlendirme protokolü: karar öncesi inceleme

**Bu çalışmada eğitim veya performans sonucu yoktur.** ROADMAP WP08 split/baseline eğitimlerini içerir; son kullanıcı talimatı metodolojiyi önce gerekçelendirmeyi ve onay beklemeyi gerektirir. Burada 62 ilaç için seçenekler somutlaştırılır; D01–D07 onaylanmış sayılmaz.

Deney birimi ilaçtır; satır veya ilaç–PT çifti değildir. Aynı ilaçtan çok sayıda etiket olması bağımsız örneklem büyüklüğünü artırmaz. Önceki WPlarda tüm 62 ilaç etiketleri keşfedildiği için gelecekteki sonuçlar iç doğrulamadır; hiç görülmemiş prospektif test iddiası kurulamaz.''')
    code('''from pathlib import Path
import json,sys
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP08';FIG=ROOT/'reports/figures/WP08';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',125);pd.set_option('display.max_columns',25);pd.set_option('display.max_colwidth',100)
def read(n):return pd.read_csv(QA/n,keep_default_na=False)
summary=json.loads((QA/'structure_audit_summary.json').read_text(encoding='utf-8'))
display(pd.DataFrame([summary]).drop(columns=['fingerprint','empty_scaffold_policy']))
display(pd.DataFrame([{'cohort':62,'test_bagimsiz_yeni_veri':False,'model_egitimi':False,'gercek_split':False,'nihai_yontem_onayi':False}]))''')
    md('''## 1. D01 — PT, tarihsel kategori ve klinik alt küme

Sıklık, “kaç ilaçta kaynakta pozitif kayıt var?” sorusunun yanıtıdır; hasta olay oranı değildir. Klinik alt küme uzman onaylı kavram listesi olmadan tanımlanamaz. Sayı daha yoğun görünsün diye PT veya kategori seçilmez.''')
    code('''options=read('label_options.csv');freq=read('class_frequencies_QA.csv');display(options)
pt=freq[freq.strategy.eq('PT_CUI')];cat=freq[freq.strategy.eq('historical_30')].sort_values('positive_drugs_QA')
display(pt.sort_values('positive_drugs_QA',ascending=False).head(12));display(cat)
fig,axs=plt.subplots(1,2,figsize=(15,8));axs[0].hist(pt.positive_drugs_QA,bins=np.arange(.5,62.5,1),color='#598aaf');axs[0].set(xlabel='Pozitif ilaç / PT',ylabel='Sınıf sayısı',title='1061 PT: seyrek kuyruk')
axs[1].barh(cat.class_id,cat.positive_drugs_QA,color='#ba9467');axs[1].set(xlabel='Pozitif ilaç / 62',title='Tarihsel 30: semantik onay değildir');plt.tight_layout();plt.savefig(FIG/'01_label_options.png',dpi=160);plt.show()
display(read('clinical_subset_review_queue.csv')[['kategori','kaynak_PT','CUI','pozitif_ilac_62','inceleme','clinical_expert_approved']])''')
    md('''**Yorum:** 1061 PT/6416 çift ile tarihsel 30/1011 çift farklı kavram uzaylarıdır. PT'de 406 sınıf tek ilaçta, 710 sınıf beşten az ilaçta görülür. Klinik alt küme sayısı **henüz tanımsızdır**; 30 kategorinin daha yoğun olması klinik doğruluğunu sağlamaz.

**Sızıntısız seçim yöntemi önerisi:** Etiket körü yapısal gruplar ve dış fold önce sabitlenir. Her dış train içinde PT destek eşiği ve grup desteği hesaplanır; iç validation yöntem ayarı içindir. Dış testin PT sıklığına bakılarak sınıf eklenmez/çıkarılmaz. 3/5/10 ilaç ve en az iki grup eşikleri yalnız onay bekleyen adaylardır; burada bu eşiklerle gerçek öğrenme sözlüğü üretilmedi. Uzman sabit klinik liste seçerse performansa bakılmadan gerekçesi kaydedilir. Testte train sözlüğü dışında pozitifler ayrı kapsanmayan hedef kapsamı olarak raporlanır.

## 2. D05 — Aynı yapı, stereo varyantı ve yakın yapı

Mevcut kaynak SMILES'lerden Morgan radius=2, 2048 bit ve stereo dışı Tanimoto benzerliği yalnız gruplama QA'sı için hesaplandı; yeni model özelliği değildir. Tam InChIKey ile bağlantı bloğu aynı şeyi anlatmaz. Murcko scaffold, kaynaktaki molekülün yerini almayan türetilmiş bir karşılaştırma temsilidir.''')
    code('''structures=read('structure_grouping_evidence.csv');pairs=read('pairwise_structure_similarity.csv');shared=read('shared_structure_pairs.csv')
names=structures.set_index('drug_id').name.to_dict();ordered=list(structures.drug_id)
top=pairs.nlargest(12,'morgan2_2048_no_stereo_tanimoto').copy();top['name1']=top.drug_id1.map(names);top['name2']=top.drug_id2.map(names);display(top)
display(shared[shared.matching_representations.str.contains('connectivity')])
sim=pd.DataFrame(np.eye(len(ordered)),index=ordered,columns=ordered)
for r in pairs.itertuples():sim.loc[r.drug_id1,r.drug_id2]=sim.loc[r.drug_id2,r.drug_id1]=r.morgan2_2048_no_stereo_tanimoto
fig,ax=plt.subplots(figsize=(10,8));im=ax.imshow(sim,vmin=0,vmax=1,cmap='viridis');ax.set_xticks(range(0,62,4),ordered[::4],rotation=90,fontsize=8);ax.set_yticks(range(0,62,4),ordered[::4],fontsize=8);fig.colorbar(im,ax=ax,label='Morgan Tanimoto • stereo dışı');ax.set_title('62 ilaç / 1891 farklı çift • QC bayrakları korunur');plt.tight_layout();plt.savefig(FIG/'02_structure_similarity.png',dpi=160);plt.show()
display(structures[['drug_id','name','components','WP04_review','WP04_review_flags']])''')
    md('''**Yorum:** Levofloxacin–Ofloxacin bağlantı bloğu ve nonisomeric yapı eşit; stereo dışı benzerlik 1'dir. Ayrı train/test ID'leri olarak bırakmak zor bir yeni-kimya testi sağlamaz. Bu kimyasal/klinik eşdeğerlik iddiası değildir. Tam yapı anahtarı veya CID tekrarı yok. 99 tuz–ebeveyn ve 63 ikincil–ebeveyn kaydı kaynak WP02'den korundu; tuzlar ayrı ilaç eklemedi. Bütün molekül ve QC bayrakları korundu, nötralizasyon/ana fragment seçimi/stereo tamamlama yapılmadı. Sekiz inceleme molekülünün gruplaması da bu nedenle geçicidir.

## 3. Gruplama seçenekleri ve yalnız büyüklük fizibilitesi''')
    code('''groups=read('group_summary.csv');sizes=read('split_size_feasibility.csv');display(groups);display(sizes)
fig,axs=plt.subplots(1,2,figsize=(14,5));axs[0].barh(groups.method,groups.groups,color='#6b98b8');axs[0].set(xlabel='Bağımsız aday grup sayısı',title='Hiçbiri nihai split kararı değil');axs[1].barh(groups.method,groups.largest_group,color='#bf9b6c');axs[1].set(xlabel='En büyük gruptaki ilaç',title='Transitif benzerlik kısıtlarının etkisi');plt.tight_layout();plt.savefig(FIG/'03_grouping_candidates.png',dpi=160);plt.show()
display(shared.head(12))''')
    md('''**Yorum:** Primary ID düzeyinde 62 grup; bağlantı kilidinde 61; scaffold kısıtında 41; scaffold veya benzerlik≥0,8 kısıtının birleşiminde 40 grup vardır. Sonuncunun en büyük grubu beş ilaçtır. 0,7/0,8/0,9 eşikleri biyolojik eşdeğerlik veya en iyi eşik değildir. Bağlı bileşenle gruplama transitiftir: uç üyeler doğrudan eşiğin altında olabilir. Aynı scaffold bazen yalnız basit fenil halkasıdır; Sulfanilamide/Chloramphenicol aynı scaffold görünürken genel kimyasal benzerlikleri düşük olabilir. Bu nedenle scaffold tek başına antibiyotik aile sınıflaması değildir.

Üç ve beş fold için tabloda görülen 21/21/20 ve 13/13/12/12/12 **yalnız grup büyüklüğü yerleştirme fizibilitesidir**. Gerçek ilaç–fold ataması, stratifikasyon veya test seçimi yapılmadı. Nested CV'de her dış train içinde iç grup ayrımı gerekir. 3 dış fold daha büyük test (~20–21) ama daha küçük train (~41–42); 5 dış fold daha büyük train (~49–50) ve daha küçük test (~12–13) verir. Bunlar fold sayısı önerisini somutlaştırır, onay yerine geçmez.

## 4. Seyrek sınıflar ilaç değil grup düzeyinde de sınır koyar''')
    code('''support=read('support_feasibility_QA.csv');display(support)
selected=support[support.strategy.eq('PT_CUI')]
fig,ax=plt.subplots(figsize=(12,5));x=np.arange(len(selected));ax.bar(x-.18,selected.positive_in_one_group,width=.36,label='Yalnız 1 pozitif grup');ax.bar(x+.18,selected.at_least_5_positive_groups,width=.36,label='En az 5 pozitif grup');ax.set_xticks(x,selected.method,rotation=25,ha='right');ax.set(ylabel='PT sınıfı / 1061',title='Grup desteği • gerekli koşul, fold desteği garantisi değil');ax.legend();plt.tight_layout();plt.savefig(FIG/'04_group_support_limits.png',dpi=160);plt.show()''')
    md('''**Yorum:** Connectivity kilidiyle 411, scaffold+0,8 varyantıyla 416 PT yalnız tek pozitif grupta kalır. Bu sınıflara hem eğitim hem bağımsız grup testinde pozitif garanti edilemez. Beş pozitif grup olması bile beş foldun her birine pozitif düşmesini garanti etmez. Bu global QA sayımları sınıf eşiği veya test seçmekte kullanılmamalıdır. Hesaplanamayan sınıf metriği NA ve gerekçesiyle gösterilmeli; başarım sıfırı gibi yazılmamalıdır.

## 5. D02 — 62 ilaçta modalite maskesi birincil aday''')
    code('''m=read('drug_modality_QA_preserved.csv');display(m)
patterns=m.groupby(['chemistry_qc_available','protein_modality_available']).size().rename('drugs').reset_index();display(patterns)
fig,ax=plt.subplots(figsize=(11,5));labels=['Kimya '+('var' if r.chemistry_qc_available else 'incelemede')+' / protein '+('var' if r.protein_modality_available else 'yok') for r in patterns.itertuples()];bars=ax.barh(labels,patterns.drugs,color=['#b5806c','#ceab68','#75a2b9','#63997e']);ax.bar_label(bars);ax.set(xlabel='62 ilaç; complete-case ana kohort değildir',xlim=(0,62),title='53 / 7 / 1 / 1 modalite kapsamı');plt.tight_layout();plt.savefig(FIG/'05_modality_retention.png',dpi=160);plt.show()
display(m[m.molecule_review | ~m.protein_modality_available][['drug_id','name','molecule_review','review_flags','protein_modality_available']])''')
    md('''**Yorum:** 53 complete-case ilaç, 62'nin yerine geçirilmez. Maskeli dal yaklaşımı 62'yi korumaya adaydır. Tobramycin kimya dalıyla, protein modalitesi eksik olarak kalabilir. Methenamine'de hem temkinli kimya hem protein dalı kullanılamadığı için **etiketten bağımsız kişisel girdi bilgisi kalmayan bir durum** vardır: ayrı abstention veya yalnız train'den öğrenilen ortak önsel açıkça onaylanmalıdır. “62'yi koruduk” ifadesi 62'sine de kişiselleştirilmiş güvenilir tahmin verebildik demek değildir. Protein dizisi veya kimya uydurulmaz; ham değerle QC bypass edilmez.

## 6. D03–D04 — Context olmadan başlangıç ve ayrı PPI senaryosu''')
    code('''context=read('context_topology_cost_QA.csv');display(context)
human=context[context.network_taxid.astype(str).eq('9606')]
fig,axs=plt.subplots(1,2,figsize=(11,4.8));axs[0].bar(human.graph_type,human.edges,color=['#5c8cac','#d0a56c']);axs[0].set(ylabel='Yönsüz çift',title='İnsan 700 • aynı kaynak örnek eşiği');axs[1].bar(human.graph_type,human.isolates,color=['#5c8cac','#d0a56c']);axs[1].set(ylabel='İzole düğüm',title='Düğüm paydaları farklı: 63 ve 103');plt.tight_layout();plt.savefig(FIG/'06_context_topology_cost.png',dpi=160);plt.show()''')
    md('''**Yorum:** 80 context'in başlangıçtan çıkarılması doğrulanmış özellik gereksinimini korur; bazı yolları ve komşuları kaybettirir. İnsan 700 örneği 184 seed çifti/12 izole ile 372 geniş ağ çifti/7 izoleyi gösterir; bu bir model faydası ölçümü değildir ve 700'ü seçtirmez. WP08 B1/B2 PPI'sız adaylardır. Katı 63 insan proteiniyle PPI katkısı yalnız WP09'da gerçek encoder ve ablation ile sınanacaktır; 23 K12 inceleme proteini ana PPI ağına karışmaz. PPI'siz proteinler dizi modalitesinde kalır.

## 7. D06–D07 — Girdi, eğitim sınırı ve ölçüm anlamı''')
    code(r'''display(read('input_fields_v0_1_DRAFT.csv'));display(read('metric_interpretation.csv'));display(read('decision_proposals.csv'))
fig,ax=plt.subplots(figsize=(14,7));ax.set(xlim=(0,14),ylim=(0,7));ax.axis('off')
def box(x,y,w,h,text,color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',facecolor=color,edgecolor='#555'));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
box(.3,4.4,3.9,1.8,'Etiket körü yapı grupları\nParent / stereo / scaffold denetimi\nDış fold önce dondurulur','#dce9f4')
box(5,4.4,4,1.8,'Yalnız dış TRAIN\nİç CV: vocab / scaler / ağırlık\nTrain ilaç ilişkileriyle yeni graf','#e0eddf')
box(9.8,4.4,3.9,1.8,'Dış TEST\nSabit sözlük + fit edilmiş dönüşüm\nAyara geri besleme yok','#f1dfdd')
box(.3,.8,6,1.9,'Pozitif–etiketsiz semantik\ns: kaynakta kayıt varlığı ≠ y: biyolojik gerçek\nAP/AUROC proxy yorumu ayrıca onaylanır','#eee2f3')
box(7.1,.8,6.6,1.9,'Graf güvenlik sınırı\nTrain grafında yalnız train ilaç düğümleri/rol kenarları\nWP07 inceleme grafı train nesnesi değildir','#f3e6d3')
for a,b in [((4.2,5.3),(5,5.3)),((9,5.3),(9.8,5.3))]:ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=2))
ax.text(7,3.35,'Henüz gerçek split / fit / model / tahmin sonucu yok',ha='center',fontsize=13,color='#a53b36')
plt.tight_layout();plt.savefig(FIG/'07_protocol_boundary.png',dpi=160);plt.show()''')
    md('''**Yorum:** Taslakta 5 kimya + 56 dizi alanı vardır; dört rol ayrı tutulur, kaynak ID'ler yalnız metadata/join içindir. Protein scaler'ının yalnız train-linked benzersiz accession'larda fit edilmesi, test ilacı bağlantılarının dolaylı dağılım etkisini önler. 141 proteinlik registry zaten kohort kaynaklıdır; onu sabit harici evren gibi kullanmak saf indüktif değerlendirme sayılmamalıdır. Yeni graph üreticisi bu iki kapsamı açık parametreyle ayırır, varsayılan karar vermez.

SIDER için `s=1` kaydı gözlenir; gizli biyolojik `y` ve etiketlenme eğilimi bilinmez. Unknown=0 ile AP/AUROC ancak kayıt sıralama proxy'sidir. Gerçek negatif, klinik kalibrasyon veya nedensellik iddiası olmaz. PU düzeltmesi için sınıf önseli ve SCAR/SAR gibi varsayımlar gerekir; burada doğrulanmadılar. Ortalama precision (AP), trapez PR eğrisi alanıyla aynı hesap değildir; ileride metrik adı/yöntemi açık yazılmalı. Belirsizlik ilaç/yapısal grup düzeyinde ele alınmalı, çiftler bağımsız sayılmamalıdır.

## 8. İnteraktif yapı benzerliği ve karar kapısı''')
    code('''import plotly.graph_objects as go
hover=np.array([[a+' '+names[a]+' ↔ '+b+' '+names[b] for b in ordered] for a in ordered])
fig=go.Figure(go.Heatmap(z=sim.to_numpy(),x=ordered,y=ordered,text=hover,hovertemplate='%{text}<br>Morgan stereo dışı Tanimoto: %{z:.3f}<extra></extra>',zmin=0,zmax=1,colorscale='Viridis'))
fig.update_layout(title='62 kaynak molekül • yalnız gruplama QA; yapı/QC eşdeğerliği iddiası yok',width=1100,height=1000)
fig.write_html(FIG/'structure_similarity_interactive.html',include_plotlyjs=True,full_html=True)
display(pd.DataFrame([{'kod_hucresi':9,'PNG':7,'interaktif_HTML':1,'canli_tarayici_testi':False,'metodoloji_onayi':'BEKLENİYOR','egitim':'YOK'}]))''')
    md('''**Kapanış:** D01–D07 önerileri [WP08 karar kapısında](../reports/WP08_PROTOCOL_DECISION_GATE.md), gerçek sayımlar/testler [WP08 raporundadır](../reports/WP08.md). Başlangıç eğitimine onay verilmeden LR/RF/MLP veya PU modeli eğitilmez. WP09 çalışması başlamadı; forward komşuluk testi ve PPI/no-PPI/karıştırılmış PPI ablation gereksinimi korunur.

Yöntem kaynakları: [RDKit Morgan generator](https://www.rdkit.org/docs/source/rdkit.Chem.rdFingerprintGenerator.html), [Murcko scaffold](https://rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html), [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html), [sızıntı sınırları](https://scikit-learn.org/stable/common_pitfalls), [PU ölçüm düzeltme çalışması](https://arxiv.org/abs/1702.00518). Bunlar yöntem belgesidir; yeni biyolojik kaynak eklenmedi.''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'Actual IPython execution; no training'})
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
        if c.cell_type=='code':compile(c.source,f'WP08 cell {i}','exec')
    for c in nb.cells:
        if c.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:result=shell.run_cell(c.source,store_history=False)
        if result.error_in_exec or result.error_before_exec:raise RuntimeError(result.error_in_exec or result.error_before_exec)
        c.execution_count=n;c.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for out in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in out.data.items()}
            c.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=out.metadata))
    nbf.validate(nb);nbf.write(nb,ROOT/'notebooks/WP08_prediction_protocol.ipynb');print('Executed WP08 code cells',n)


if __name__=='__main__':main()
