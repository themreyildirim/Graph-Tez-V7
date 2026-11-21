"""Kapanış ve WP10 tasarımı için ayrı, çalıştırılmış öğretici notebook'lar."""
import base64
import io
import os
import sys
from pathlib import Path
import nbformat as nb

ROOT=Path(__file__).resolve().parents[1]


def execute(name,parts):
    target=ROOT/'notebooks'/name
    if target.exists() and '--refresh-working-drafts' not in sys.argv:raise RuntimeError('Önceki notebook ezilmez: '+name)
    if target.exists():
        # Yalnız bu görevde yeni oluşturulan iki taslak; kabul edilmiş notebook'lar korunur.
        assert name in ('WP09_final_closure.ipynb','WP10_design_feasibility.ipynb')
    cells=[nb.v4.new_markdown_cell(s) if kind=='md' else nb.v4.new_code_cell(s) for kind,s in parts]
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
        if c.cell_type=='code':compile(c.source,f'{name}:{i}','exec')
    for c in cells:
        if c.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:r=shell.run_cell(c.source,store_history=False)
        if r.error_before_exec or r.error_in_exec:raise RuntimeError(r.error_before_exec or r.error_in_exec)
        c.execution_count=n;c.outputs=[]
        for stream,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nb.v4.new_output('stream',name=stream,text=value))
        for output in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in output.data.items()}
            c.outputs.append(nb.v4.new_output('display_data',data=data,metadata=output.metadata))
    notebook=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'},'language_info':{'name':'python'}})
    nb.validate(notebook);nb.write(notebook,target);print(name,n,'executed cells')


INIT=r'''from pathlib import Path
import json,sys,re
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():
    if ROOT.parent==ROOT:raise RuntimeError('Proje kökü bulunamadı')
    ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'scripts'))
pd.set_option('display.max_rows',70);pd.set_option('display.max_columns',20)
pd.set_option('display.max_colwidth',100)
'''


def main():
    closure=[('md','''# WP09 — Son kapanış denetimi

Kullanıcı gerçek protein-PPI eğitimini araştırma kapsamında kabul etti. Bu notebook yeni kapanış kanıtlarını gösterir; mevcut model/OOF skorlarını değiştirmez. Yeniden çalıştırılan 24 testin kontrollü RAM fitleri deney sonuçlarını ezmez. Aşağıdaki hücreler yalnız kayıtlı QA okur; optimizer veya fit yoktur.

Üç ayrı sonuç: **(1)** PPI gerçekten hesaplanıyor/öğreniliyor: teknik kanıt var. **(2)** Ek birincil tahmin katkısı: bu deneyde gösterilmedi. **(3)** Protein biyolojisi genel olarak yararsızdır: bu çıkarım yapılamaz.'''),('code',INIT+r'''
C=ROOT/'reports/qa/WP09/final_closure_v1';T=ROOT/'reports/qa/WP09/training_v1'
F=ROOT/'reports/figures/WP09/final_closure_v1';F.mkdir(parents=True,exist_ok=True)
checks=json.loads((C/'closure_checks.json').read_text(encoding='utf-8'))
display(pd.DataFrame([checks]).T.rename(columns={0:'doğrulanmış_sonuç'}))
'''),('md','''**Yorum:** 190 NPZ ve190 metadata dosyasının hash'i,190 sayısal state ve2347 önceki dosya doğrulandı. Kaynak62/1061/6416 değişmedi. Test logu ayrı dosyadadır; eski log korunur. Büyük ham dosyalar tekrar taranmadı.

## 1. Kaydedilmiş ağırlıklardan gerçek skor üretimi'''),('code',r'''
display(pd.read_csv(C/'NPZ_score_reconstruction.csv'))
display(pd.read_csv(C/'same_key_checks.csv'))
'''),('md','''**Yorum:** Primary outer1'in no/real/R0/R1/R2 ağırlıkları NPZ'den yüklenip yalnız test query girdileriyle çalıştırıldı. En büyük sayısal fark yaklaşık1,1×10⁻¹⁶;float32 skorların CSV float yazım/okuma yuvarlaması sınırındadır. Bütün modeller ana/stres için aynı drug/fold/PT anahtarlarını taşır. Bu yeni değerlendirme veya model seçimi değildir.

## 2. Eğitilmiş ağırlıklarda edge etkisi ve gradient'''),('code',r'''
proof=pd.read_csv(C/'trained_forward_gradient.csv');display(proof)
fig,axs=plt.subplots(1,2,figsize=(12,4.8))
axs[0].bar(proof.model,proof.same_weights_PPI_removed_protein_L2,color='#618b9f')
axs[1].bar(proof.model,proof.trained_message_weight_gradient_norm,color='#9b7fa5')
axs[0].set(title='Aynı ağırlıklar: PPI kaldırılınca temsil farkı',ylabel='Protein temsil farkı L2')
axs[1].set(title='Kaydedilmiş ağırlıklarda train BCE gradienti',ylabel='message.weight gradient normu')
for ax in axs:ax.tick_params(axis='x',labelrotation=30,labelsize=8)
plt.tight_layout();plt.savefig(F/'01_trained_edge_gradient_check.png',dpi=160);plt.show()
'''),('md','''**Yorum:** Aynı eğitilmiş real ağırlıklarda kenarları kaldırmak protein temsillerini değiştiriyor. Train-only BCE backward mesaj katmanına gradient ulaştırıyor. NoPPI'da komşu etkisi/gradient0. Probe optimizer adımı0 ve state hash'i aynı;bu bir yeniden eğitim değildir. Bu kontrol, önceki gerçek optimizer/gradient kayıtlarıyla birlikte teknik kullanım ve öğrenmeyi destekler;etkinlik üstünlüğünü göstermez.

## 3. Değişmeyen bilimsel sonuç'''),('code',r'''
m=pd.read_csv(T/'metrics_with_group_CI.csv')
order=['G_noPPI','G_realPPI','G_shuffledPPI_mean3_metrics']
a=m[m.protocol.eq('primary')&m.scope.eq('paired54')&m.metric.eq('drug_macro_AP')].set_index('model').loc[order]
display(a[['estimate','CI95_low','CI95_high']])
fig,ax=plt.subplots(figsize=(8,4.4))
ax.errorbar(range(3),a.estimate,yerr=np.vstack([a.estimate-a.CI95_low,a.CI95_high-a.estimate]),fmt='o',capsize=5,color='#67899c')
ax.set_xticks(range(3),['noPPI','realPPI','shuffled: metrik ort.']);ax.set(ylabel='Drug-macro observed-record AP',ylim=(0,1),xlim=(-.4,2.4),title='Kabul edilen paired54 sonucu • koşullu grup CI')
for i,val in enumerate(a.estimate):ax.text(i,val+.065,f'{val:.6f}',ha='center')
plt.tight_layout();plt.savefig(F/'02_frozen_primary_result.png',dpi=160);plt.show()
d=pd.read_csv(T/'paired_differences_group_CI.csv')
display(d[d.protocol.eq('primary')&d.scope.eq('paired54')&d.metric.eq('drug_macro_AP')&d['first'].eq('G_realPPI')][['first','reference','first_minus_reference','CI95_low','CI95_high']])
'''),('md','''**Yorum:** Gerçek PPI'nin noPPI ve karıştırılmış ağlara ek drug-AP katkısı gösterilmedi. B1−GNN farkında kimya/protein girdisi,LR/nonlineer öğrenme,kapasite ve optimizasyon da değişir;tek başına PPI topolojisine atfedilemez. KoşulluCI sıfırı içermesi eşdeğerlik kanıtı değildir. Küçük kohort,rol-mean,insan PPI kapsamı ve SIDER kayıt yanlılığı protein biyolojisinin genel yararsızlığı sonucunu engeller.

## 4. Kapsam ve NA görünür kalır'''),('code',r'''
coverage=pd.read_csv(T/'evaluation_coverage.csv')
display(coverage[coverage.model.eq('G_realPPI')])
status=pd.read_csv(T/'prediction_status_all62.csv');display(status.groupby(['protocol','model','status']).size().rename('ilaç').reset_index())
display(pd.read_csv(T/'excluded_inner_jobs.csv'))
display(pd.DataFrame([{'yeni_log':'trainer_tests_rerun.txt','test':24,'saniye':checks['test_seconds'],'durum':'OK','eski_log_ezildi':False}]))
'''),('md','''**Yorum:** Primary paired54'te1685 kaynak pozitif hedef/fit kapsamı dışında;bu bütün62'nin yanlış-negatif sayısı değildir.61 ilaç skorlanır,Methenamine abstain. Üç null NA,iki shared-excluded inner bağlam/10 iş ve tek-proxy sınıflar görünür kalır. Unknown gerçek biyolojik negatif değildir. Skorlar klinik risk,kalibrasyon,nedensellik veya hasta güvenliği doğrulaması değildir. WP09 kapanır;WP10 yalnız ayrı tasarım/uygulanabilirlik incelemesidir.''')]
    execute('WP09_final_closure.ipynb',closure)

    design=[('md','''# WP10 — Atom–bağ grafı tasarımı ve uygulanabilirlik

Aktif ROADMAP WP10: SMILES→atom/bond graf,RDKit→PyG Data,readout,küçük moleküler GNN ve kademeli karşılaştırma;veri yetersizse deney ertelenir. **Bu aşama yalnız tasarım ve gerçek yapı incelemesidir. Model,PyG eğitim nesnesi veya optimizer oluşturulmadı.**

Kaynaklar WP04'te yerel DrugBank XML'den çıkarılan SMILES ve doğrulanmış CID köprüsüdür. Bunlara canlı PubChem yapısı yeniden doğrulanmış denmez. Yeni molekül,etiket veya veri kaynağı indirilmedi.'''),('code',INIT+r'''
Q=ROOT/'reports/qa/WP10/design_v1';F=ROOT/'reports/figures/WP10/design_v1';F.mkdir(parents=True,exist_ok=True)
summary=json.loads((Q/'feasibility_summary.json').read_text(encoding='utf-8'))
proposal=json.loads((ROOT/'configs/WP10_design_PROPOSED_v1.json').read_text(encoding='utf-8'))
data=pd.read_csv(Q/'molecular_graph_feasibility_all62.csv')
display(pd.DataFrame([summary]).T.rename(columns={0:'sonuç'}));display(data)
display(pd.DataFrame([json.loads((Q/'runtime_readiness.json').read_text(encoding='utf-8'))]))
'''),('md','''**Yorum:**62/62 ayrıştırma,yerel tam anahtar ve atom/bağ sayımı yeniden doğrulandı.2061 atom/2219 bağ;10–125 atom/ilaç. Bunlar gözlenen yapı boyutlarıdır,bağımsız eğitim örneği sayısı62'yi artırmaz. Varsayılan import yolunda PyG görünmese de mevcut `.deps/pyg` paketi ayrıca import edilip doğrulandı;yeni kurulum gerekmedi.

## 1. Teknik uygunluk ile QC onayı'''),('code',r'''
review=pd.read_csv(Q/'QC_review_eight_preserved.csv');display(review[['id','name','review_flags','atoms','bonds','components','proposed_atom_modality_eligible_PENDING_APPROVAL']])
fig,axs=plt.subplots(1,2,figsize=(11,4.6))
axs[0].bar(['Teknik graf mümkün','QC bayraksız','İnceleme bekliyor'],[62,54,8],color=['#7195a8','#87a98c','#c0997d']);axs[0].set(ylabel='İlaç sayısı',title='62 envanterde kalır;QC değişmedi',ylim=(0,70))
for i,v in enumerate([62,54,8]):axs[0].text(i,v+1,str(v),ha='center')
axs[1].scatter(data.atoms,data.bonds,c=np.where(data.strict_QC_pass_unchanged,'#7195a8','#c0997d'))
axs[1].set(xlabel='Atom sayısı',ylabel='Bağ sayısı',title='Gerçek kaynak yapı boyutları')
axs[1].set_xlim(0,145)
offsets={'DB00798':(4,8),'DB04911':(-8,-18),'DB00512':(-66,-20)}
for d in ['DB00798','DB04911','DB00512']:
    r=data[data.id.eq(d)].iloc[0];axs[1].annotate(r['name'],(r.atoms,r.bonds),fontsize=8,xytext=offsets[d],textcoords='offset points',arrowprops={'arrowstyle':'-','color':'gray','lw':.6})
from matplotlib.lines import Line2D
axs[1].legend(handles=[Line2D([0],[0],marker='o',ls='',color='#7195a8',label='QC bayraksız'),Line2D([0],[0],marker='o',ls='',color='#c0997d',label='İnceleme bekliyor')],fontsize=8,loc='upper left')
plt.tight_layout();plt.savefig(F/'01_QC_and_graph_sizes.png',dpi=160);plt.show()
'''),('md','''**Yorum:**Öneri54 atom-dalı uygun maskesi;sekiz ilacın mevcut skaler/protein yolları korunur. Bu öneri henüz nihai girdi kararı değildir. Gentamicin üç bileşenlidir;en büyük fragment seçilmedi,oranlar tahmin edilmedi. Belirtilmemiş stereo tamamlanmadı;Methenamine algoritma-farkı bayrağı gerçek yapı hatası ilan edilmedi. Methenamine için eski abstention değişmez;Tobramycin kimya/atom adayı olarak protein eksiğiyle kalır.

## 2. Gerçek atom–bağ örneği: sadece topoloji'''),('code',r'''
from wp04_chemistry import Chem,parse_smiles
from rdkit.Chem import rdDepictor
import networkx as nx
source=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv').set_index('id')
smiles=source.loc['DB00601','raw_smiles'];mol,status=parse_smiles(smiles);rdDepictor.Compute2DCoords(mol)
g=nx.Graph();g.add_nodes_from(range(mol.GetNumAtoms()))
g.add_edges_from((b.GetBeginAtomIdx(),b.GetEndAtomIdx()) for b in mol.GetBonds())
pos={i:(mol.GetConformer().GetAtomPosition(i).x,mol.GetConformer().GetAtomPosition(i).y) for i in g.nodes}
color={'C':'#cbd5db','N':'#8aafd0','O':'#dba2a2','F':'#9fc99c'}
fig,ax=plt.subplots(figsize=(10,4.8));nx.draw_networkx(g,pos,ax=ax,node_size=370,node_color=[color.get(mol.GetAtomWithIdx(i).GetSymbol(),'#dbc293') for i in g],labels={i:f'{mol.GetAtomWithIdx(i).GetSymbol()}{i}' for i in g},font_size=8,width=1.2)
ax.set_title('Linezolid • kaynak atomları ve kovalent bağ komşuluğu');ax.axis('off')
plt.tight_layout();plt.savefig(F/'02_Linezolid_atom_graph_preview.png',dpi=160);plt.show()
display(pd.DataFrame([{'atom':a.GetIdx(),'element':a.GetSymbol(),'aromatik':a.GetIsAromatic(),'CIP':a.GetProp('_CIPCode') if a.HasProp('_CIPCode') else 'yok/belirtilmemiş','ham_chiral_tag':str(a.GetChiralTag())} for a in mol.GetAtoms()]))
'''),('md','''**Yorum:**Çizgi yalnız komşuluk gösterir;bağ derecesi/aromatiklik/stereo aşağıdaki ayrı edge_attr sözleşmesindedir. Bu görüntü eğitim tensörü veya çalıştırılmış moleküler encoder değildir. Atom indeksleri join/görsel içindir,ezberleme girdisi olmaz.2D koordinatlar çizim içindir;3D konformer veya model girdisi değildir.

## 3. Önerilen özellik ve kapasite sözleşmesi'''),('code',r'''
features=[]
for kind,fields in proposal['features'].items():
    for field,values in fields.items():features.append({'tür':kind,'alan':field,'sabit_kategoriler':str(values),'boyut':len(values)})
display(pd.DataFrame(features));display(pd.DataFrame(list(proposal['PyG_contract'].items()),columns=['alan','önerilen_sözleşme']))
budget=pd.read_csv(Q/'parameter_budget_by_train_PT.csv');display(budget)
fig,ax=plt.subplots(figsize=(9,4.3));ax.plot(budget.train_PT,budget.WP09_total,label='Sabit WP09 mimari sayımı');ax.plot(budget.train_PT,budget.proposed_total,label='Önerilen molekül dalı ile')
ax.set(xlabel='İlgili train sözlüğünde fit edilebilir PT',ylabel='Öğrenilebilir parametre sayısı',title='Cebirsel kapasite hesabı • model kurulmadı');ax.legend()
plt.tight_layout();plt.savefig(F/'03_proposed_parameter_budget.png',dpi=160);plt.show()
'''),('md','''**Yorum:**44 atom/14 bağ alanı sabit kategorilerle önerilir;OTHER desteklenir,testten sözlük öğrenilmez. CIP R/S,belirtilmemiş potansiyel ve stereo-yok ayrıdır. Ham chiralTag/bond direction metadata korunur;komşu sırasına bağlı ham işaretler doğrudan sayısal özellik yapılmaz. İzotop/radikal mevcut kaynakta0;yeni örnekte ayrı QC gerekir.

Öneri bir bond-aware residual mean katmanı hidden16,mean readout→8 ve mevcut141 temsile8+maske ekleyerek150 boyuttur. Yeni dal1592 parametre,PT başlığına9K ek parametre;toplam5512+151K. Mevcut K158–326 için29.370–54.738 parametre,bağımsız örnekler yalnız train ilaçlarıdır. Çok PT daha çok bağımsız ilaç sağlamaz;aşırı öğrenme riski sürer. Edge-conditioned büyük NNConv zorunlu değil;küçük açık mesaj denklemi önerildi. Bir katman yalnız yerel komşuluk taşır;derin kimyasal mekanizma/3D stereo etkileşim çözümü iddia edilmez.

## 4. Ablation ve onay kapısı'''),('code',r'''
display(pd.DataFrame([{'hücre':name,'atom_mesajı':name[1]=='1','insan_PPI_mesajı':name[-1]=='1','durum':'ÖNERİ; uygulanmadı'} for name in proposal['factorial_primary']]))
display(pd.DataFrame({'onay_bekleyen':proposal['remaining_gates']}))
display(pd.DataFrame(json.loads((Q/'method_sources.json').read_text(encoding='utf-8'))['sources']))
'''),('md','''**Yorum:**A0P0/A0P1/A1P0/A1P1 gelecekte aynı genişletilmiş mimari/init/ID/PT kapsamında kıyaslanır. Atom katkısı aynı PPI koşulunda,PPI katkısı aynı atom koşulunda ölçülür. Eski WP09 A0 modeli yeni başlık/kapasiteyi taşımadığından tek başına kontrollü factorial hücre yerine geçmez;sabit tarihsel referans kalır. R0/R1/R2 eklenirse aynı v3 null/NA/ortak-inner politikası ve metrik ortalaması korunur.

Eski split/hash,train-only PT sözlüğü/scaler/uygunluk ve paired54/own61 korunur. Query atom grafı bağımsız okunur;protein train cache'ine/diğer ilaç grafına geri mesaj yoktur. Unknown gerçek negatif değildir. Karşılaştırmalar önceki sonuçlar görülmüş olduğu için keşifseldir;klinik risk iddiası yoktur.

Mevcut yol haritası küçük moleküler GNN'yi izinli konu yapar;bu tasarım tam moleküler Graph-in-Graph tamamlandı anlamına gelmez. İç atom grafı→drug readout ve protein-PPI füzyonu gerçek forward/gradient/permutation/edge-attr/split izolasyon testleriyle uygulanmadan bu iddia kurulamaz. **Tasarım önerisi hazır;uygulama ve özellikle eğitim için kullanıcı onayı beklenir.**

Yöntem kaynakları: [RDKit stereo/aromatiklik](https://www.rdkit.org/docs/RDKit_Book.html),[PyG Data şekilleri](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.data.Data.html),[graph mean readout](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.pool.global_mean_pool.html). Bunlar yöntem belgesidir,yeni biyolojik kaynak değildir.''')]
    execute('WP10_design_feasibility.ipynb',design)


if __name__=='__main__':main()
