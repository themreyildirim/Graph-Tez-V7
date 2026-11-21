"""Gerçek QA tablolarından yürütülmüş WP07 notebook ve öğretici figürler."""
import base64
import io
import os
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def main():
    cells = []
    def md(text): cells.append(nbf.v4.new_markdown_cell(text))
    def code(text): cells.append(nbf.v4.new_code_cell(text))
    md('''# WP07 — Veri entegrasyonu, heterojen graf ve karar kapısı

**Öğren → Gerçek tablo → Görsel → Sızıntı denetimi → Doğrulama → Karar.**

WP00–WP06 onaylandı. Bu notebook yeni ham kaynak açmaz; kayıtlı ve hash doğrulamalı küçük QA çıktılarından çalışır. Nihai etiket, eksik modalite stratejisi ve model giriş şeması seçilmez. İnceleme HeteroData nesneleri `training_ready=False` taşır; x/y, split, negatif örnek veya model yoktur.

Kanonik kimlik kaynak ID'dir; node_index ise yalnız yeniden üretilebilir depolama sırasıdır. Source/target kenarın uç tiplerini, target rolü ise DrugBank'ın biyolojik ilişki rolünü anlatır; bu iki “target” anlamı karıştırılmaz.''')
    code('''from pathlib import Path
import sys,json
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists(): ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'.deps/pyg'))
import pandas as pd,numpy as np,matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from IPython.display import display
import torch
from torch_geometric.data import HeteroData
QA=ROOT/'reports/qa/WP07';FIG=ROOT/'reports/figures/WP07';FIG.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',150);pd.set_option('display.max_columns',30);pd.set_option('display.max_colwidth',90)
def read(name): return pd.read_csv(QA/name,keep_default_na=False)
summary=json.loads((QA/'integration_summary.json').read_text(encoding='utf-8'))
display(pd.DataFrame([summary]).drop(columns=['role_edges','scenarios']))
drugs=read('drug_nodes.csv');proteins=read('protein_nodes.csv');pt=read('pt_audit_nodes.csv')
display(drugs.head(5));display(proteins.head(5));display(pt.head(5))''')
    md('''**Yorum:** 62 ilaç ve 141 protein korunur. 1061 PT CUI, tüm kohortta gözlenmiş kaynak sözlüğüdür; nihai öğrenme sözlüğü değildir. Aynı ana ilacın tuzu bağımsız drug düğümü yapılmadı. Proteinler PPI eşleşmesi yok diye elenmez.

## 1. Heterojen graf ve hedef deposu

Farklı düğüm ve kenar tipleri heterojen grafı oluşturur. İlaç–protein ilişkileri yönlü ve role özgüdür. STRING ilişkileri kaynakta yönsüzdür; PyG iki yönü iki indeks sütunu olarak saklar. SIDER pozitifleri ayrı hedef deposundadır; inceleme grafındaki SE düğümlerine hedef veya ters hedef kenarı bağlanmaz.''')
    code(r'''fig,ax=plt.subplots(figsize=(14,7));ax.set(xlim=(0,14),ylim=(0,7));ax.axis('off')
def box(x,y,w,h,text,color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',facecolor=color,edgecolor='#555'))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
box(.4,4.5,3.4,1.7,'62 drug\n3 girdi QC maskesi\nx / y yok','#dce9f4')
box(6,4.5,3.7,1.7,'141 protein\n4 ayrı DrugBank rolü\nPPI yok diye eleme yok','#e0eddc')
box(10.5,4.5,3.1,1.7,'Ayrı PPI senaryoları\n63 insan / 23 K12 review\nBirbirine karışmaz','#f4e4d4')
box(.4,.8,4.6,1.7,'1061 se_pt_audit düğümü\nKenar yok, x yok\nKaynak sözlüğü; nihai hedef seçimi değil','#e9e0f1')
box(6,.8,7.6,1.7,'Harici SIDER hedef deposu\n6416 observed_positive; gözlenmeyen unknown\nEncoder komşuluğuna / model X’ine aktarılmaz','#f1dfdf')
ax.annotate('',xy=(6,5.4),xytext=(3.8,5.4),arrowprops=dict(arrowstyle='->',lw=2));ax.text(4.9,5.65,'4 rol / 476',ha='center')
ax.annotate('',xy=(9.7,5.4),xytext=(10.5,5.4),arrowprops=dict(arrowstyle='<->',lw=2));ax.text(10.1,4.05,'Yalnız protein PPI',ha='center',fontsize=9)
ax.text(7,3.2,'Hedeflerden encoder’a ok yok • eğitim hazır değil',ha='center',fontsize=13,color='#9d3333')
ax.set_title('WP07 yapısal inceleme sözleşmesi • nihai model mimarisi değil');plt.tight_layout();plt.savefig(FIG/'01_review_schema.png',dpi=160);plt.show()
graphs=torch.load(QA/'heterodata_review_scenarios.pt',weights_only=False,map_location='cpu') # yalnız bu projede yeni üretilmiş güvenilir dosya
display(pd.DataFrame([{'senaryo':k,'drug':g['drug'].num_nodes,'protein':g['protein'].num_nodes,'SE_QA':g['se_pt_audit'].num_nodes,'tipli_kenar':len(g.edge_types),'training_ready':g.training_ready} for k,g in graphs.items()]))
display(graphs['human_700'])''')
    md('''**Yorum:** Grafik bir veri sözleşmesi çizimidir; mesaj geçişi uygulanmadı. HeteroData nesnelerinin tümünde aynı 62/141/1061 düğüm paydası bulunur. PyG'nin SE düğümlerinin ilişki kenarı olmadığına dair uyarısı beklenen bilinçli ayrımdır, eksik hedef kenarı ekleme talimatı değildir. PT düğümlerinin sayılması, PT sayısını ilaç özelliği yapmak anlamına gelmez. Dosya yalnız güvenilir yerel üretimden yüklenir; eski `.pt` yüklenmez.

## 2. Eksik modalite ve QC maskeleri

Eksik bir özellik biyolojik sıfır değildir. İnceleme bayrağı da molekülün kesin yanlış olduğu anlamına gelmez. Kimya QC ve protein bulunurluğu kaynak girdisinden gelir; `has_pt` veya kategori yoğunluğu bunları belirlemez.''')
    code('''m=read('drug_modality_QA.csv');patterns=read('modality_patterns.csv')
display(m);display(patterns)
fig,ax=plt.subplots(figsize=(10,5));names=['Kimya '+('var' if r.chemistry_qc_available else 'bekliyor')+' / protein '+('var' if r.protein_modality_available else 'yok') for r in patterns.itertuples()]
bars=ax.barh(names,patterns.drugs,color=['#c68974','#dfb66c','#77a9bd','#5d9c7f'][:len(patterns)])
ax.bar_label(bars);ax.set(xlabel='İlaç sayısı / sabit 62',title='Girdi modalite örüntüleri • nihai kohort elemesi yok');ax.set_xlim(0,62);plt.tight_layout();plt.savefig(FIG/'02_modality_patterns.png',dpi=160);plt.show()
display(m[m.molecule_review | ~m.protein_modality_available][['drug_id','name','molecule_review','review_flags','protein_modality_available']])''')
    md('''**Yorum:** WP04'ün sekiz inceleme bayrağı korunur. Tobramycin ve Methenamine eksik protein modalitesiyle kalır; Methenamine aynı zamanda moleküler incelemededir. Complete-case yalnız bir duyarlılık seçeneğidir; ana kohortu otomatik daraltmak değildir. Maskeli ayrı dallar, train-only imputasyon ve complete-case kıyası karar dosyasında karşılaştırılır.

## 3. Biyolojik roller ayrı kenar tipleridir''')
    code('''typed=read('typed_drug_protein_edges.csv');roles=typed.groupby('role').agg(kenar=('accession','size'),ilac=('drug_id','nunique'),protein=('accession','nunique')).reindex(['target','enzyme','transporter','carrier'])
display(roles);display(typed.head(12));display(read('edge_counts.csv'))
fig,ax=plt.subplots(figsize=(9,5));bars=ax.bar(roles.index,roles.kenar,color=['#4f8fba','#8bb078','#cf9d63','#a287bd']);ax.bar_label(bars);ax.set(ylabel='Benzersiz (drug, role, protein)',title='476 tipli kenar; rollerin biyolojik anlamları korunur');ax.set_ylim(0,280);plt.tight_layout();plt.savefig(FIG/'03_role_edges.png',dpi=160);plt.show()''')
    md('''**Yorum:** Target bağları tek başına 241; enzyme, transporter ve carrier eklenince 476 tipli kenar var. Aynı ilaç–protein çifti farklı rollerde bulunabilir; rol silinerek tekilleştirmek farklı bir graf üretir. Ters ilişki eklemek sonraki mesaj geçişi tasarımına bağlıdır; burada otomatik ters kenar eklenmez.

## 4. PPI kapsamını ve yönsüz sayımı koruma''')
    code('''mapping=pd.read_csv(ROOT/'reports/qa/WP06/protein_string_mapping.csv',keep_default_na=False)
scope=mapping.status.value_counts();display(scope.rename('accession').to_frame())
ppi=read('ppi_scenarios.csv');display(ppi)
fig,axs=plt.subplots(1,2,figsize=(13,5))
counts=[63,23,6,49];labs=['İnsan aynı-taxID','K12 alt suş inceleme','E. coli alias yok','Diğer organizma']
bars=axs[0].barh(labs,counts,color=['#4f8fba','#df9c61','#aaa','#888']);axs[0].bar_label(bars);axs[0].set(xlabel='141 WP05 protein',title='PPI yok diye protein kaybı yok')
human=ppi[ppi.scenario.str.startswith('human')];axs[1].plot(human.threshold,human.unique_undirected_pairs,'o-',label='Tekil yönsüz çift');axs[1].plot(human.threshold,human.directed_index_columns,'s--',label='PyG indeks sütunu');axs[1].legend();axs[1].set(xlabel='İnsan skor eşiği',ylabel='Sayı',title='Depolama yönleri biyolojik kenarı ikiye katlamaz')
plt.tight_layout();plt.savefig(FIG/'04_ppi_scope_and_counts.png',dpi=160);plt.show()
context=read('context_inventory_no_features.csv');display(context[['string_id','network_taxid','protein_name','sequence_feature_available']].head(10));display(context.groupby('network_taxid').size().rename('Özelliksiz context').to_frame())''')
    md('''**Yorum:** 63 aynı-taxID insan ile 23 K12/MG1655 inceleme kaydı aynı kesinlikte değildir. K12 700 senaryosu ayrı tutulur. İnsan 700'de 184 kaynak çifti 368 indeks sütunu eder; model PPI kullandı demek değildir. 80 context proteininin amino asit özellikleri yoktur; inceleme grafına alınmadılar ve sıfırla doldurulmadılar. Sıfır+maske, öğrenilen tip tokenı, ayrı topolojik temsil veya context kullanmama seçenekleri biyolojik anlamlarıyla karar dosyasındadır.

## 5. Hedef stratejileri ve unknown semantiği''')
    code('''strategies=read('label_strategy_comparison.csv');display(strategies)
labels=read('observed_pt_positives_external.csv');display(labels.head(8))
freq=labels.groupby('pt_cui').drug_id.nunique();perdrug=labels.groupby('drug_id').pt_cui.nunique().reindex(drugs.drug_id,fill_value=0)
fig,axs=plt.subplots(1,2,figsize=(12,4.8));axs[0].hist(freq,bins=np.arange(.5,62.5,1),color='#658eb1');axs[0].set(xlabel='Pozitif kaydı olan ilaç / PT sınıfı',ylabel='PT sınıfı sayısı',title='Kaynak PT destek dağılımı • QA')
axs[1].hist(perdrug,bins=16,color='#b98c60');axs[1].set(xlabel='Gözlenen pozitif PT / ilaç',ylabel='İlaç sayısı',title='Etiket yoğunluğu • girdi özelliği değil');plt.tight_layout();plt.savefig(FIG/'05_label_strategy_QA.png',dpi=160);plt.show()''')
    md('''**Yorum:** 6416 kayıt 1061 PT sınıfında kayıpsız tutulur. 406 singleton ve küçük kohort, sınıf bazında bağımsız değerlendirmeyi sınırlar. Tarihsel 30 projeksiyonunda 61 ilaç/1011 çift vardır; Sulfanilamide'nin kategori pozitifinin olmaması kesin negatif değildir. PT sözlüğünde 59366 gözlenmeyen çift unknown olarak düşünülür; böyle bir yoğun negatif matris üretilmedi. Nihai etiket seti veya destek eşiği seçilmedi.

## 6. Sızıntı sınırı ve inceleme kararları''')
    code(r'''audit=read('leakage_audit.csv');decisions=read('decision_options.csv');display(audit);display(decisions)
fig,ax=plt.subplots(figsize=(13,6));ax.set(xlim=(0,13),ylim=(0,6));ax.axis('off')
box(.4,3.5,3.7,1.5,'Girdi kaynakları\nKimya / dizi / DrugBank / PPI\nAçık alan allowlist','#dce9f4')
box(4.8,3.5,3.6,1.5,'Yapısal inceleme\nKimlik / rol / aralık / maske\nEğitim kapısı kapalı','#e2eddd')
box(9.1,3.5,3.5,1.5,'Gelecekte WP08\nTrain-only fit\nDrug-disjoint protokol','#e9e0f1')
box(.4,.7,5.5,1.5,'Hedef deposu + QA\nPT / kategori / yoğunluk / has_pt\nGirdi akışına erişemez','#f1dddd')
box(6.6,.7,6,1.5,'WP09 zorunlu kanıt\nGerçek PPI forward etkisi testi\nPPI / no-PPI / karıştırılmış PPI ablation','#f3e5d2')
for a,b in [((4.1,4.25),(4.8,4.25)),((8.4,4.25),(9.1,4.25))]:ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=2))
ax.text(6.5,5.6,'Val/test hedefleri ve test ilaçları eğitim grafına giremez',ha='center',fontsize=12)
plt.tight_layout();plt.savefig(FIG/'06_leakage_boundary.png',dpi=160);plt.show()''')
    md('''**Yorum:** Bu ayrım gelecekteki eğitim hattını otomatik güvenli yapmaz. İnceleme grafı tüm kohortu içerir; bu yüzden doğrudan train grafı olarak kullanılamaz. WP08'de test ilaç düğümleri ve ileri/ters ilişkileri eğitimden çıkarılmalı, scaler/özellik seçimi yalnız train'de fit edilmeli. Paylaşılan protein/PPI bağlamının sınırı açık protokol kararıdır. PPI encoder ancak forward'da komşuluğu gerçekten kullanınca ve kontrollü ablation ile sınanınca iddia edilebilir.

## 7. Etkileşimli modalite envanteri ve kapanış''')
    code('''import plotly.graph_objects as go
columns=['chemistry_qc_available','protein_modality_available','molecule_review']
z=m[columns].astype(int).to_numpy();hover=np.repeat((m.drug_id+' | '+m.name+' | QC: '+m.review_flags).to_numpy()[:,None],3,axis=1)
fig=go.Figure(go.Heatmap(z=z,x=['Kimya QC var','Protein var','Molekül incelemede'],y=m.drug_id,text=hover,hovertemplate='%{text}<br>%{x}: %{z}<extra></extra>',zmin=0,zmax=1,colorscale=[[0,'#eee'],[1,'#4f8fba']],showscale=False))
fig.update_layout(title='62 ilaç: input modalite ve QC envanteri • 1/0 bayrak, biyolojik özellik değil',height=1450,width=1050)
fig.write_html(FIG/'drug_modality_interactive.html',include_plotlyjs=True,full_html=True)
display(pd.DataFrame([{'HTML':'reports/figures/WP07/drug_modality_interactive.html','PNG':6,'canlı_tarayıcı_testi':False}]))
display(pd.DataFrame([{'D01':'Nihai etiket','D02':'Eksik ilaç modalitesi','D03':'Context temsil','D04':'PPI kapsam/eşik','D05':'Drug-disjoint protokol','D06':'Giriş şeması','D07':'Unknown/PU varsayımı'}]).T.rename(columns={0:'Onay bekleyen karar'}))''')
    md('''**Yorum:** HTML 62 ilacın kimliği, adı ve kaynak QC bayraklarını gösterir. 0 burada yalnız boole bayrak değeridir; eksik molekül veya dizi için sıfır özellik vektörü üretilmez. HTML çevrimdışı Plotly içerir; canlı tarayıcı etkileşim testi yapılmadı.

Altı PNG'nin her biri açıklamasıyla kaydedildi. 62 ilaç, sekiz molekül incelemesi, iki eksik protein modalitesi, 63/23 ayrımı ve 80 özelliksiz context korunmuştur. D01–D07 seçenekleri [karar dosyasında](../reports/WP07_DECISION_GATE.md) bekler. Otomatik test sonuçları ve hash kontrolleri [WP07 raporundadır](../reports/WP07.md).

WP07 sonunda durulur. WP08, eğitim, negatif örnekleme, metrik sonucu, ölçekleme veya PPI mesaj geçişi başlatılmaz.

[PyG resmi HeteroData API](https://pytorch-geometric.readthedocs.io/en/stable/generated/torch_geometric.data.HeteroData.html): yapısal `validate`, düğüm sayıları ve yönsüz kenarların indeks sayımı için yöntem referansı.''')
    nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec': {'name':'python3','display_name':'Python 3','language':'python'}, 'language_info': {'name':'python'}, 'execution_method':'Actual IPython execution in process'})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display, Image
    def show(*args, **kwargs):
        for i in plt.get_fignums():
            buf=io.BytesIO();plt.figure(i).savefig(buf,format='png',dpi=100,bbox_inches='tight');display(Image(data=buf.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for i,c in enumerate(nb.cells):
        if c.cell_type=='code': compile(c.source,f'WP07 cell {i}','exec')
    for c in nb.cells:
        if c.cell_type!='code': continue
        n+=1
        with capture_output(display=True) as cap: result=shell.run_cell(c.source,store_history=False)
        if result.error_in_exec or result.error_before_exec: raise RuntimeError(result.error_in_exec or result.error_before_exec)
        c.execution_count=n;c.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for out in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in out.data.items()}
            c.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=out.metadata))
    nbf.validate(nb);nbf.write(nb,ROOT/'notebooks/WP07_data_integration.ipynb');print('Executed code cells',n)


if __name__=='__main__': main()
