"""WP10 encoder'ını gerçek verilerle öğreten,PT eğitimi yapmayan notebook."""
from pathlib import Path
import base64,io,os,sys
import nbformat as nb
ROOT=Path(__file__).resolve().parents[1]


def main():
    path=ROOT/'notebooks/WP10_molecular_encoder.ipynb'
    if path.exists() and '--refresh-working-draft' not in sys.argv:raise RuntimeError('Notebook zaten var;ezilmez')
    if (ROOT/'reports/qa/WP10/encoder_v1/artifact_validation.json').exists():raise RuntimeError('Encoder v1 finalized')
    cells=[]
    def md(s):cells.append(nb.v4.new_markdown_cell(s))
    def code(s):cells.append(nb.v4.new_code_cell(s))
    md('''# WP10 — Gerçek moleküler graf,encoder ve entegrasyon

Kullanıcı tasarımv1'i **graf/encoder/teknik test** uygulaması için onayladı. Kaynak WP04 DrugBank XML SMILES,CID köprüsü ve mevcutQC. **62 envanter;54 atom dalı açık,8 inceleme maskesi kapalı.** Yeni kaynak yok.

Bu notebook gerçek PyG2.8.0 Data ve forward/backward gösterir. Bütün ağırlıklar **eğitilmemiş başlangıç/sentetik kanıt ağırlıklarıdır**;optimizer veya gerçekPT loss yoktur. Moleküler temsil bir yan etki skoru değildir. Outer ilaçlar yalnız etiketsiz query temsil izolasyonu için incelendi;PT skorlaması/performans tablosu yapılmadı.''')
    code(r'''from pathlib import Path
import sys,json,re
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display,Image
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():
    if ROOT.parent==ROOT:raise RuntimeError('Proje kökü bulunamadı')
    ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'scripts'))
from wp10_molecular_graph import QA,Chem,torch,Batch,load_store,build_graph,parse_smiles,slices
from wp10_molecular_encoder import initialized_model,BondAwareMolecularEncoder,load_context,VARIANTS
torch.set_num_threads(1)
F=ROOT/'reports/figures/WP10/encoder_v1';F.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',70);pd.set_option('display.max_columns',20);pd.set_option('display.max_colwidth',90)
store=load_store();env=json.loads((QA/'environment.json').read_text(encoding='utf-8'));audit=json.loads((QA/'technical_audit_complete.json').read_text(encoding='utf-8'))
display(pd.DataFrame([env]));display(pd.DataFrame([audit]).T.rename(columns={0:'gerçek_kontrol'}))
display(store.graphs['DB00601'])''')
    md('''**Yorum:** Gerçek Linezolid PyG Data nesnesi x[24,44],edge_index[2,52],edge_attr[52,14] taşır. Kimlik,ad,hamSMILES,QC ve stereo referansları ayrıregistry'dedir;y/PT alanı Data'da yoktur. `.deps/pyg`2.8.0 gerçek çalışma ortamıdır;kurulum yapılmadı. Özellikler sabit şemadan gelir,testten sözlük/scaler öğrenilmedi.

## 1. Tüm62 graf ve54/8 maskesi''')
    code(r'''qa=pd.read_csv(QA/'molecular_graph_QA_all62.csv');display(qa)
display(qa[~qa.atom_eligible][['id','name','atoms','bonds','components','review_flags']])
fig,axs=plt.subplots(1,2,figsize=(11,4.3))
axs[0].bar(['Gerçek PyG Data','Atom dalı açık','QC kapalı'],[len(qa),qa.atom_eligible.sum(),(~qa.atom_eligible).sum()],color=['#7094a7','#86a78c','#c19b80'])
axs[0].set(ylabel='İlaç sayısı',title='62 ilaç korunur;8 maske ile kapalı',ylim=(0,70))
for i,v in enumerate([62,54,8]):axs[0].text(i,v+1,str(v),ha='center')
axs[1].bar(['Atom','Yönsüz bağ','İki yönlü kenar'],[qa.atoms.sum(),qa.bonds.sum(),qa.directed_edges.sum()],color='#7094a7')
axs[1].set(title='Gerçek tüm62 tensör kapsamı',ylabel='Kayıt sayısı')
for i,v in enumerate([qa.atoms.sum(),qa.bonds.sum(),qa.directed_edges.sum()]):axs[1].text(i,v+40,str(v),ha='center')
axs[1].set_ylim(0,5000)
plt.tight_layout();plt.savefig(F/'01_real_PyG_QC_scope.png',dpi=160);plt.show()''')
    md('''**Yorum:**2061 atom/2219 bağ4438 yönlü kenara açılır.54 atom maskesi mevcutQC kararıdır;8 ilaç veri kümesinden silinmez. Gentamicin105 atom/3 bağlantısız bileşen olarak tam korunur;en büyük fragment seçilmez. Methenamine atom dalı kapalı ve mevcut girdisiz abstention politikasında;Tobramycin protein eksiğiyle kimya+uygun atom dalında kalır. Teknik parse/graph uygunluğu biyolojik doğruluğun eksiksiz kanıtı değildir.

## 2.44 atom ve14 bağ özelliği neyi kodluyor?''')
    code(r'''schema=json.loads((QA/'feature_schema.json').read_text(encoding='utf-8'));rows=[]
for kind,fields in schema['fields'].items():
    for field,values in fields.items():rows.append({'tür':kind,'alan':field,'boyut':len(values),'sabit_değerler':str(values)})
display(pd.DataFrame(rows))
atoms=pd.read_csv(QA/'atom_fields_all62.csv');bonds=pd.read_csv(QA/'bond_fields_all62.csv')
display(atoms[atoms.id.eq('DB00601')]);display(bonds[bonds.id.eq('DB00601')])
from rdkit.Chem import Draw
selected=['DB00601','DB00537','DB01060'];mols=[]
for d in selected:
    mol,status=parse_smiles(store.registry[d]['source_SMILES']);mols.append(mol)
options=Draw.MolDrawOptions();options.addAtomIndices=True
picture=Draw.MolsToGridImage(mols,molsPerRow=3,subImgSize=(440,360),legends=[d+' '+store.registry[d]['name'] for d in selected],drawOptions=options)
picture.save(F/'02_real_molecules_indexed.png');display(picture)''')
    md('''**Yorum:**Linezolid,Ciprofloxacin,Amoxicillin kaynak yapıları atom indeksleriyle gösterildi;2D koordinatlar girdi değildir. Formal yük,H sayısı,aromatiklik,bağ tipi veCIP ayrı alanlardır. R/S ile komşu sırasına bağlı ham@/@@ aynı şey değildir. Potansiyel fakat belirtilmemiş atom stereo UNASSIGNED_POTENTIAL;belirtilmemiş potansiyel çiftbağ STEREOANY olarak kodlanır,hamRDKit BondStereo metadatada aynen korunur. Bu sınıflama E/Z veya R/S tahmini değildir.

## 3. İki yönlü kenarlar ve bağ özellik hizası''')
    code(r'''import networkx as nx
from rdkit.Chem import rdDepictor
d='DB00601';mol,_=parse_smiles(store.registry[d]['source_SMILES']);rdDepictor.Compute2DCoords(mol)
g=store.graphs[d];net=nx.DiGraph();net.add_nodes_from(range(g.num_nodes));net.add_edges_from(map(tuple,g.edge_index.T.tolist()))
pos={i:(mol.GetConformer().GetAtomPosition(i).x,mol.GetConformer().GetAtomPosition(i).y) for i in net}
colors={'C':'#cbd5db','N':'#88add0','O':'#dba2a2','F':'#9ac799'}
fig,ax=plt.subplots(figsize=(12,5.3))
nx.draw_networkx_nodes(net,pos,ax=ax,node_size=300,node_color=[colors.get(mol.GetAtomWithIdx(i).GetSymbol(),'#ddc28b') for i in net])
nx.draw_networkx_labels(net,pos,ax=ax,labels={i:mol.GetAtomWithIdx(i).GetSymbol()+str(i) for i in net},font_size=7)
nx.draw_networkx_edges(net,pos,ax=ax,arrows=True,arrowsize=10,node_size=300,connectionstyle='arc3,rad=0.09',edge_color='#65737c',width=.9)
ax.set_title('Linezolid • her kovalent bağ iki mesaj kenarıdır');ax.axis('off')
plt.tight_layout();plt.savefig(F/'03_Linezolid_two_direction_edges.png',dpi=160);plt.show()
alignment=[]
for b in store.registry[d]['raw_stereo_metadata']['bonds'][:7]:
    i,j=b['forward_column'],b['reverse_column'];alignment.append({'RDKit_bond':b['bond_index'],'ileri':str(g.edge_index[:,i].tolist()),'ters':str(g.edge_index[:,j].tolist()),'edge_attr_aynı':bool(torch.equal(g.edge_attr[i],g.edge_attr[j])),'stereo':b['stereo'],'raw_direction':b['raw_bond_direction']})
display(pd.DataFrame(alignment))''')
    md('''**Yorum:**Bu yönler kovalent bağın iki mesaj yönüdür;biyolojik nedensellik yönü değildir. İki yönde bağ-tipi ve E/Z gibi invariant özellikler aynıdır. Raw BondDir/stereo-atom referansları kaynakbegin/end indeksleriyle ayrımetadata'dadır;ters yöne körlemesine rawUP/DOWN özelliği kopyalanmaz. Çizgi türü burada bağ derecesini kodlamaz;bond-order bilgisi14boyutlu edge_attr tablosundadır.

## 4. Kontrollü sentetik forward ve türev''')
    code(r'''m=BondAwareMolecularEncoder().double()
with torch.no_grad():
    for p in m.parameters():p.zero_()
    m.projection.weight[0,0]=1;m.projection.weight[0,2]=2;m.self_update.weight[0,0]=.5
    m.atom_message.weight[0,0]=.75;m.bond_message.weight[0,0]=1;m.bond_message.weight[0,1]=3;m.readout.weight[0,0]=1
mol,_=parse_smiles('CCO');data,raw=build_graph(mol);out=m(Batch.from_data_list([data]));out['molecular_h'].sum().backward()
proof=json.loads((QA/'synthetic_analytic_proof.json').read_text(encoding='utf-8'))
display(pd.DataFrame([proof]).T.rename(columns={0:'kontrollü_kanıt'}))
assert abs(out['molecular_h'][0,0].item()-3.875)<1e-12
assert abs(m.atom_message.weight.grad[0,0].item()-7/6)<1e-12
fig,axs=plt.subplots(1,2,figsize=(10,4.2));i=np.arange(3)
axs[0].bar(i-.17,proof['node_h0_first'],width=.34,label='projection h0');axs[0].bar(i+.17,proof['node_h_first'],width=.34,label='message h1')
axs[0].set_xticks(i,['C0','C1','O2']);axs[0].set(title='CCO • ilk koordinat',ylabel='Kontrollü temsil');axs[0].legend()
axs[1].bar(['Atom mesajı','Bağ mesajı'],[proof['d_output_d_atom_message_00'],proof['d_output_d_bond_message_single_00']],color='#9c81a5');axs[1].set(title='Readout türevi • optimizer yok',ylabel='Analitik gradient')
plt.tight_layout();plt.savefig(F/'04_synthetic_forward_gradient.png',dpi=160);plt.show()''')
    md('''**Yorum:** Tek adımda h0=[1,1,2],h1=[3,25;3,625;4,75] ve mean readout3,875 çıkar. Atom-message türevi7/6,bağ-message türevi1'dir. Bağ kaldırma ve bond-type değişimi testlerde beklenen3,1667 ve4,875 readout'larına gider. Bu elle belirlenmiş ayırt edici kanıt ağırlıklarıdır;optimizer veya yan etki kaybı yoktur.

## 5. Gerçek moleküllerde forward ve gradient''')
    code(r'''real=pd.read_csv(QA/'real_molecular_forward_gradient.csv');display(real)
fig,axs=plt.subplots(1,2,figsize=(11,4.3));i=np.arange(len(real))
axs[0].bar(i-.17,real.edge_removed_output_L2,width=.34,label='Bir bağın iki yönü kaldırıldı');axs[0].bar(i+.17,real.bond_type_perturbed_output_L2,width=.34,label='Bond-type özelliği değişti')
axs[1].bar(i-.17,real.atom_message_gradient_norm,width=.34,label='Atom-message');axs[1].bar(i+.17,real.bond_message_gradient_norm,width=.34,label='Bond-message')
for ax in axs:ax.set_xticks(i,real.name);ax.legend(fontsize=7)
axs[0].set(title='Eğitilmemiş gerçek encoder forward etkisi',ylabel='8-boyutlu çıktı farkı L2');axs[1].set(title='Temsil toplamının gradienti',ylabel='Gradient normu')
plt.tight_layout();plt.savefig(F/'05_real_forward_gradient.png',dpi=160);plt.show()''')
    md('''**Yorum:**Linezolid,Ciprofloxacin,Amoxicillin'de atom ve bağ message parametrelerine gradient ulaştı;kenar veya bond-type özelliği değişince çıktı değişti. Perturbasyonlar yazılım duyarlılık probe'udur;kimyasal olarak geçerli yeni molekül/ilaç,mekanizma veya yan etki açıklaması değildir. Ağırlıklar değişmedi,optimizer adımı0.

## 6. Permütasyon,başlangıç hash'i ve kapasite''')
    code(r'''permutation=pd.read_csv(QA/'permutation_all62.csv');display(permutation)
display(pd.read_csv(QA/'actual_parameter_counts.csv'))
display(pd.DataFrame([json.loads((QA/'UNTRAINED_initial_state.json').read_text(encoding='utf-8'))]).T)
model=initialized_model();model_again=initialized_model()
from wp10_molecular_encoder import model_digest
assert model_digest(model)==model_digest(model_again)
with torch.no_grad():sample=model.molecular(store.make_batch(['DB00601','DB00537','DB01060']).batch)
display(pd.DataFrame([{'tensör':key,'boyut':str(tuple(value.shape))} for key,value in sample.items()]))''')
    md('''**Yorum:**62 gerçek yapının atomları yeniden sıralanıp stereo özellikleri yeniden çıkarıldı. Float64 readout farkı en fazla2,08×10⁻¹⁶,önceden belirlenen tolerans1e-12 altında. Atom indeksi öğrenme özelliği değildir. Dal1592;protein/kimya+atom5512 parametre. Opsiyonel sentetikK başlığı5512+151K olarak sayıldı;gerçek veri forward'unda headNone. NPZ snapshot **UNTRAINED** başlangıç içindir,yan etki modeli değildir. NPZ zip baytları yerine dtype/shape/tensor bayt hash'i sayısal tekrar üretimi tanımlar.

## 7.141→150 füzyon ve dört anahtar''')
    code(r'''checks=pd.read_csv(QA/'integration_forward_40contexts_4variants.csv');display(checks)
first=checks[checks.context.eq('primary_o01_final')].set_index('variant').loc[list(VARIANTS)];display(first)
g,q,tm,qm=load_context('primary_o01_final',store)
model=initialized_model()
with torch.no_grad():
    train=model.encode_train(g,tm,'A1P1');query=model.encode_query(g,q,qm,train['cache'])
display(pd.DataFrame([{'train_repr':str(tuple(train['representation'].shape)),'query_repr':str(tuple(query['representation'].shape)),'gerçek_PT_head':model.head,'train_query_ID_ortak':len(set(tm.ids)&set(qm.ids))}]))
fig,axs=plt.subplots(1,2,figsize=(10,4.2))
axs[0].bar(first.index,first.train_active_atom_mask,color='#85a98d');axs[0].set(title='Primary outer1 • etkin atom dalı',ylabel='Train ilaç sayısı')
axs[1].bar(first.index,first.train_PPI_neighbor_input_norm,color='#7093a5');axs[1].set(title='Protein mesajına giren komşu ortalaması',ylabel='Girdi normu')
plt.tight_layout();plt.savefig(F/'06_four_variant_switches.png',dpi=160);plt.show()''')
    md('''**Yorum:**40 frozen bağlam×4 anahtar160 teknik train/query forward geçti. A0'da molekül8+maske1 bloğu tam0;P0'da protein komşu ortalaması0. Aynı contextte dört anahtar aynı başlangıç/parametre/ID kapsamını taşır. Atom dalı kapalıyken de150 boyut korunur;bu frozenWP09 modelini değiştirmez. Protein cache'inin state/graph bağı doğrulanır;query başkaquery'yi veyacache'i değiştirmez.

Bu40 bağlam teknik şekil/izolasyon denetimidir;WP09 null nedeniyle seçimden çıkarılmış iki inner bağlamı gelecek eğitim planına geri almak değildir. Gelecekteki gerçek trainer ayrıca train-only PT loss/seçim testleri gerektirir;encoder testi henüz yazılmamış trainer'ın doğruluğunu kanıtlamaz.

## 8. Testler ve eğitim kapısı''')
    code(r'''text=(QA/'test_results_context_guard.txt').read_text(encoding='utf-8-sig');test=re.search(r'Ran ([0-9]+) tests in ([0-9.]+)s',text)
display(pd.DataFrame([{'gerçek_test':int(test.group(1)),'saniye':float(test.group(2)),'durum':'PASS' if text.rstrip().endswith('OK') else 'FAIL','optimizer':0,'PT_skoru':False}]))
display(pd.read_csv(QA/'train_query_scope_manifest.csv').head(4))
display(pd.DataFrame([{'alan':'Gerçek dört kollu eğitim','durum':'AYRI KULLANICI ONAYI BEKLİYOR'},
    {'alan':'Outer PT skorlaması / performans','durum':'YAPILMADI'}, {'alan':'R0/R1/R2 ek moleküler ablation','durum':'Gelecek deney kapsamı kararı;ağ/model araması yok'}]))''')
    md('''**Yorum:**28 test sentetik kimya,gerçek62 Data,54/8 maskesi,feature boyut/semantik/direction,permutation,edge/gradient,iki dal kapatma,query/cache izolasyonu,heldout/PT enjeksiyon reddi,tüm40 frozen üyelik,seed/tensor hash veparametre sayısını doğruladı. WP09/B0/B1/B2 sonuçları veQC kaynakları değişmedi;önceki2384 artefaktın hash'i korundu.

Atom-GNN ve protein-PPI artık teknik olarak birleştirilebilir;gerçek yan etki öğrenimi veya performans katkısı henüz ölçülmedi. Bu yüzden tam moleküler GiG araştırması tamamlandı denmez. SIDER unknown gerçek biyolojik negatif değildir;gelecekteki skorlar klinik risk olasılığı değildir. **WP10 encoder teknik doğrulamasında durulur;gerçek dört kollu eğitim için kullanıcı onayı beklenir.**''')
    book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'},'language_info':{'name':'python'}})
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
        if c.cell_type=='code':compile(c.source,f'WP10 encoder cell{i}','exec')
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
    nb.validate(book);nb.write(book,path);print('Executed WP10 encoder notebook',n,'cells;6 PNG;no fit/PT scores')


if __name__=='__main__':main()
