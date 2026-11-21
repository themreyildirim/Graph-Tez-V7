"""Ağ/XML taraması yapmadan WP04 tablolarını ve molekül çizimlerini çalıştırır."""
from pathlib import Path
import io
import os
import base64
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP04 · Moleküler veri keşfi ve RDKit

**Öğren → Gerçek yapı → Tablo → Görsel → QC.** Onaylı 62 DrugBank ana ID incelenir. SIDER yalnız önceki kohort tanımıdır; PT, kategori ve etiket sayıları kimyasal hesaplara girmez. Bu notebook kayıtlı WP04 yapı alanlarını okur; XML'i yeniden taramaz, internet/API veya eğitim başlatmaz.

SMILES bir molekülün atomlarını, bağlarını, dallarını ve halka kapanışlarını metinle anlatır. `C/N/O` atom simgeleri, `=` çift bağ, küçük `c/n` aromatik atom, nokta `.` bağlantısız bileşen, `@/@@` yerel tetrahedral stereokimya, `/` ve `\\` bağ geometrisi için işaretlerdir. `@` tek başına R, `@@` tek başına S demek değildir; yazımdaki komşu sırası önemlidir. Sayılar atom sayısı değil halka kapatma etiketleridir.''')
    code('''from pathlib import Path
import sys,json,pandas as pd,numpy as np
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'AGENTS.md').exists())
sys.path.insert(0,str(ROOT/'scripts'))
from wp04_chemistry import parse_smiles,identity,descriptors,atom_bond_tables,Chem,rdBase
from rdkit.Chem import Draw,rdDepictor
import matplotlib.pyplot as plt
import networkx as nx
from IPython.display import display,Image
pd.set_option('display.max_rows',100);pd.set_option('display.max_colwidth',130)
QA=ROOT/'reports/qa/WP04';FIG=ROOT/'reports/figures/WP04';FIG.mkdir(parents=True,exist_ok=True)
def read(n):return pd.read_csv(QA/n,keep_default_na=False)
sources=read('structure_sources.csv');qc=read('structure_validation.csv')
raw=pd.read_csv(QA/'chemical_features_raw.csv');clean=pd.read_csv(QA/'chemical_features_clean.csv')
recovery=read('coverage_and_recovery.csv');summary=json.loads((QA/'coverage_summary.json').read_text(encoding='utf-8'))
mols={r.id:parse_smiles(r.raw_smiles)[0] for r in sources.itertuples()}
display(pd.DataFrame([{'Python':sys.version.split()[0],'RDKit':rdBase.rdkitVersion,'ilaç':len(sources),'ağ çağrısı':summary['pubchem_requests_this_analysis']}]))''')
    md('''## 1. Önce mevcut kaynak ve gerçek XML alanları

DrugBank XML `drug/calculated-properties/property` altında `kind/value/source` üçlüleri vardır. Molekül ağırlığı ve H-bağı alanları da yereldedir; eski kodda “XML'den çekilemedi” denmesi bu alanların hiç bulunmadığı anlamına gelmiyordu. **CID köprüsü yapı dosyası değildir:** önceki gerçek `drug links.csv` şeması CID/SID içerir, SMILES/InChI içermez. WP02 köprü anlık görüntüsüyle kimlik bağı korunur. Tuz listesi ana ilacın alternatif tuz kayıtlarına bağlanır; SMILES'in mutlaka tuz içerdiğini göstermez.''')
    code('''fields=read('xml_field_coverage.csv');display(fields[fields.kind.isin(['SMILES','InChI','InChIKey','Molecular Formula','Molecular Weight','H Bond Donor Count','H Bond Acceptor Count','logP','Polar Surface Area (PSA)'])])
manifest=json.loads((QA/'xml_extract_manifest.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{k:manifest[k] for k in ['records_scanned','selected_found','bytes_read','elapsed_seconds','sampled_rss_max_mib','os_peak_wset_mib','metadata_unchanged']}]))
evidence=read('xml_property_evidence.csv')
display(evidence[evidence.id.eq('DB00601') & evidence.kind.isin(['SMILES','InChI','InChIKey','logP','Molecular Weight'])][['section','kind','value','source']])''')
    md('''**Yorum:** 62/62 kayıtta üç yapı alanı var. Son seçili ana kayıtta duruldu; dosyanın tümü belleğe alınmadı. Aynı `logP` adı altında farklı hesaplayıcılar/deneysel değerler bulunabilir; bu satırlar ortalanmadı veya son satırla ezilmedi. XML dışa aktarımında kök sürüm `5.1`, tarih `2026-01-04`; daha ayrıntılı DrugBank sürümü çıkarılamaz.''')
    md('''## 2. Canonical/isomeric SMILES ve InChI kimliği

Canonical SMILES belirli bir yazılım ve sürümün atom sıralama kuralına göre üretilir; evrensel tek dize değildir. “Canonical” olması stereo taşımadığı anlamına gelmez. RDKit `canonical=True, isomericSmiles=True` ikisini birlikte kullanabilir. Buradaki nonisomeric çıktı stereo/isotop ayrıntısını dışarıda bırakır; kaynak yapı yerine kullanılmaz.

InChI katmanlı bir yapı tanımıdır; InChIKey bunun özetidir ve tek başına molekülü geri kurmaya yetmez. Tam anahtar uyumu yerel kaynak içi tutarlılıktır; bağımsız klinik/formülasyon eşdeğerliği veya güncel PubChem yapısı doğrulaması değildir. İlk InChIKey bloğunun aynı olması stereo/protonasyon/diğer katmanların tümünün aynı olduğu anlamına gelmez.''')
    code('''ids=['DB00601','DB01137','DB01165']
display(sources[sources.id.isin(ids)][['id','name','cid','raw_smiles','raw_inchi','raw_inchikey']])
display(qc[qc.id.isin(ids)][['id','name','rdkit_isomeric_smiles','rdkit_nonisomeric_smiles','chiral_assigned','chiral_unassigned','smiles_key_relation']])
levo=qc.set_index('id').loc['DB01137'];oflo=qc.set_index('id').loc['DB01165']
display(pd.DataFrame([{'gerçek örnek':'Levofloxacin / Ofloxacin','nonisomeric_yazım_eşit':levo.rdkit_nonisomeric_smiles==oflo.rdkit_nonisomeric_smiles,'tam_InChIKey_eşit':levo.rdkit_inchikey==oflo.rdkit_inchikey}]))''')
    md('''**Yorum:** Aynı bağlantı yapısına sahip yazımlar stereo ayrıntısında ayrışabilir. Ofloxacin kaydında stereo işareti yokluğunu rastgele bir enantiyomer seçerek tamamlamıyoruz. Kaynak anahtarının eşleşmesi, belirtilmemiş stereonun otomatik tamamlandığı anlamına gelmez.''')
    md('''## 3. Tüm 62 ilaç için yapı kapsamı

Yapılar doğrudan yerel XML ana ID kaydından gelir; CID hem XML hem mevcut köprüyle eşleşir. `strict_qc_pass` bu WP'deki temkinli inceleme politikasıdır, nihai model kohortu değildir. Bir bayrak SMILES'in ayrıştırılamadığı anlamına gelmez. Kaynak InChI'den hesaplanan anahtar da ayrı kontrol edildi.''')
    code('''table=qc[['id','name','cid','parse_status','identity_verified_local','strict_qc_pass','review_flags']].merge(recovery[['id','old_chemistry_available']],on='id',validate='one_to_one')
display(table)
fig,ax=plt.subplots(figsize=(10,4));labels=['XML SMILES','RDKit ayrıştırma','Yerel kimlik uyumu','Bayraksız temkinli QC'];vals=[summary[k] for k in ['xml_structures','valid_smiles','local_identity_verified','strict_qc_pass']]
ax.bar(labels,vals,color=['#327d9b','#327d9b','#327d9b','#b9782c']);ax.set_ylim(0,68);ax.set_ylabel('İlaç / 62')
for i,v in enumerate(vals):ax.text(i,v+1,str(v),ha='center')
ax.set_title('Yapı varlığı, doğrulama ve inceleme politikası ayrı ölçülerdir');plt.tight_layout();plt.savefig(FIG/'01_structure_coverage.png',dpi=160);plt.show()''')
    md('''**Yorum:** Üç ilk basamak 62; bayraksız temkinli QC 54. Bu 8 kaydı biyolojik olarak yanlış veya kullanılamaz ilan etmiyoruz. Özellikle stereokimya belirsizliği ile çok bileşenlilik farklı inceleme nedenleridir. Yeni yapı sorgusu yapılmadan 62 yapı üzerinde hesap yapılabiliyor.''')
    md('''## 4. Başarısız ayrıştırma, tuz, karışım, metal ve stereo kontrolü

Kaynakta ayrıştırma hatası, yerel tam InChIKey uyuşmazlığı ve metal atomu bulunmadı; sıfır gözlenmesi bu problemlerin genel olarak imkânsız olduğu anlamına gelmez. Tuz bağlantısı olan ana kayıt ve noktayla ayrılmış SMILES bileşenleri farklı şeylerdir. Gentamicin kaydındaki üç bileşeni tek bir “en büyük fragment” seçerek değiştirmiyoruz.''')
    code('''flagged=qc[qc.review_flags.ne('')];display(flagged[['id','name','components','metal_atoms','chiral_unassigned','legacy_chiral_unassigned','double_stereo_unassigned','review_flags']])
display(sources[sources.declared_salt_links.astype(int)>0][['id','name','declared_salt_links']])
display(pd.DataFrame([{'ayrıştırma_hatası':int(qc.parse_status.ne('valid').sum()),'yerel_anahtar_uyuşmazlığı':int(qc.smiles_key_relation.ne('full_inchikey_match').sum()),'metal_içeren':int(qc.metal_atoms.ne('').sum()),'çok_bileşenli':int(qc.components.astype(int).gt(1).sum())}]))
gm=Chem.Mol(mols['DB00798']);before=(gm.GetNumAtoms(),gm.GetNumBonds())
img=Draw.MolToImage(gm,size=(1600,950),legend='DB00798 - Gentamicin - 3 components');img.save(FIG/'02_gentamicin_components.png');display(img)
assert before==(gm.GetNumAtoms(),gm.GetNumBonds())''')
    md('''**Yorum:** Gentamicin kaydı C60H123N15O21 formülüyle üç ayrı organik bileşen taşıyor. Ham özellikler bu tam kayıt için hesaplanır; tek bir gentamicin bileşeninin ya da ticari bir karışımın derişim ağırlıklı özelliği değildir. “Nokta varsa tuzdur” denemez. Methenamine'de yeni RDKit stereo algılayıcısı 4 potansiyel N merkezi işaretliyor, eski algılayıcı 0; bu algoritma farkı gerçek stereo hatası diye sunulmuyor. Cefprozil'de bir çift bağ geometrisi belirtilmemiş. Sekiz kayıt temiz tabloda bekletiliyor; kaynak değerleri korunuyor.''')
    md('''## 5. Beş tanımlayıcı nasıl hesaplanıyor?

| Alan | WP04 tanımı | Birim / sınır |
|---|---|---|
| MW | RDKit `Descriptors.MolWt` | g/mol, ortalama molekül ağırlığı; monoisotopik/ExactMolWt değil |
| LogP | Wildman–Crippen `Crippen.MolLogP` | boyutsuz hesap; eski PubChem XLogP ile aynı yöntem değil, deneysel logD değil |
| HBD | `Lipinski.NumHDonors` | donor merkez sayısı; H atomlarının toplamı değil |
| HBA | `Lipinski.NumHAcceptors` | acceptor merkez sayısı; tüm N+O atom sayısı değil |
| TPSA | `CalcTPSA(includeSandP=False)` | Å², N/O katkıları; S/P duyarlılık hesabı ayrı |

Kaynak molekülün tamamı kullanılır. Nötralizasyon, tautomer değiştirme, fragment seçme, atom/bağ silme yok. Sayısal sıfır geçerli bir sonuç olabilir; eksik değer `NaN/null` ile korunur. Hiçbir PT/kategori alanı fonksiyon parametresi değildir.''')
    code('''computed=pd.DataFrame([{'id':i,**descriptors(mols[i])} for i in ['DB01060','DB00537','DB00207']]);display(computed)
display(read('missingness.csv'));display(raw.head(8));display(clean[clean.MW.isna()])
assert list(raw.columns)==['id','MW','LogP','HBD','HBA','TPSA']
assert list(clean.columns)==list(raw.columns)''')
    md('''**Yorum:** Ham hesap tablosunda 62 ilaçta beş değer var; temiz tabloda sekiz inceleme kaydının beş değeri de bilerek boş. Bu, hesaplanamayan molekül ile hesaplanıp incelemede tutulan molekülü ayırır. Temiz tablo eğitim tensörü değildir; veri ölçeklenmedi, doldurulmadı.''')
    md('''## 6. Eski V5 ile fark ve hesap yöntemi

Eski kod kaynakta PubChem MolecularWeight/XLogP/HBondDonorCount/HBondAcceptorCount/TPSA istiyordu. İzinli Drive tablosundan yalnız ham beş alan, ID, ad ve CID karşılaştırma için alındı; eski normalizasyonlar kullanılmadı. 41 ortak kaydın CID'si mevcut kohort CID'siyle uyumlu. LogP yöntem farkı doğrudan hesap hatası değildir.''')
    code('''diff=pd.read_csv(QA/'legacy_feature_comparison.csv');display(read('legacy_difference_summary.csv'))
display(diff[diff.old_value.notna()].assign(abs_delta=lambda d:d.delta_rdkit_minus_old.abs()).sort_values('abs_delta',ascending=False).head(15))
fig,axes=plt.subplots(2,3,figsize=(12,7))
for ax,k in zip(axes.flat,['MW','LogP','HBD','HBA','TPSA']):
    d=diff[diff.feature.eq(k)&diff.old_value.notna()];ax.scatter(d.old_value,d.rdkit_value,s=20,alpha=.7)
    lo=min(d.old_value.min(),d.rdkit_value.min());hi=max(d.old_value.max(),d.rdkit_value.max());ax.plot([lo,hi],[lo,hi],'--',color='gray')
    ax.set(title=k,xlabel='Eski V5 / PubChem',ylabel='RDKit')
axes.flat[-1].axis('off');fig.suptitle('41 ortak ilaç · yöntem ve yuvarlama farkları');plt.tight_layout();plt.savefig(FIG/'03_legacy_comparison.png',dpi=160);plt.show()''')
    md('''**Yorum:** MW farkları küçük (en çok yaklaşık 0,071 g/mol); yuvarlama/atomik ağırlık tanımı katkısı olabilir, tek neden kanıtlanmış değil. HBD 41/41 aynı. HBA, LogP ve TPSA farklı yöntemlerle hesaplandığı için aynı sütun adı aynı değer garantisi vermez. Farklar silinmedi veya eski değerle değiştirilmedi.''')
    code('''sp=read('tpsa_definition_sensitivity.csv');display(sp[sp.delta_S_P.astype(float)>0][['id','name','TPSA_N_O','TPSA_with_S_P','delta_S_P']])
fig,ax=plt.subplots(figsize=(9,4));ax.hist(sp.delta_S_P.astype(float),bins=15,color='#327d9b');ax.set(xlabel='TPSA(S/P dahil) − TPSA(N/O), Å²',ylabel='İlaç sayısı',title='Aynı yapı, farklı TPSA tanımı');plt.tight_layout();plt.savefig(FIG/'04_tpsa_definition.png',dpi=160);plt.show()''')
    md('''**Yorum:** Örneğin Ampicillin N/O-only TPSA yaklaşık 112,73; S/P katkısıyla yaklaşık 138,03 Å². Eski 138,0 değeriyle bu ikinci tanım daha yakın. Bu gözlem tüm eski farkların yalnız S/P kaynaklı olduğunu kanıtlamaz. Yeni varsayılanı sonuçlara bakarak ilaç bazında değiştirmiyoruz; her iki tanımı kaynaklı ayrı tabloda koruyoruz.''')
    md('''## 7. Üç gerçek antibakteriyelin tam 2D yapısı

2D çizimde çizgi uçları/köşeleri çoğunlukla karbon, karbonlara bağlı H'ler örtük gösterilir. Bu çizim kuralı atomları molekülden silmek değildir. Kama/kesik kama stereo yönelimini anlatır; 2D koordinatlar 3D konformasyon veya bağ enerjisi hesabı değildir.''')
    code('''examples=['DB01060','DB00537','DB00207']
for identifier in examples:
    name=sources.set_index('id').loc[identifier,'name'];mol=Chem.Mol(mols[identifier]);before=(mol.GetNumAtoms(),mol.GetNumBonds())
    image=Draw.MolToImage(mol,size=(1200,650),legend=f'{identifier} - {name}')
    image.save(FIG/(identifier+'_2D.png'));display(image)
    assert before==(mol.GetNumAtoms(),mol.GetNumBonds())
display(qc[qc.id.isin(examples)][['id','name','formula','atom_count','bond_count','aromatic_atoms','chiral_assigned']].merge(raw,on='id'))''')
    md('''**Yorum:** Amoxicillin'in beta-laktam halkası ve S içeren iskeleti, Ciprofloxacin'in aromatik/heterosiklik ve F içeren yapısı, Azithromycin'in büyük makrolid halkası ve şeker benzeri halkaları farklı atom/bağ düzenleri gösterir. Azithromycin daha büyük ve daha çok atom taşır; bu tek başına etkinlik ya da yan etki riski sıralaması değildir. Karşılaştırma moleküler temsil çeşitliliğini öğretir.

Karmaşık Vancomycin de aşağıda tam olarak çizilir. Daha küçük görünmesi için halka, şeker veya yan zincir çıkarılmadı.''')
    code('''vm=Chem.Mol(mols['DB00512']);counts=(vm.GetNumAtoms(),vm.GetNumBonds());im=Draw.MolToImage(vm,size=(1800,1300),legend='DB00512 - Vancomycin');im.save(FIG/'05_vancomycin_full.png');display(im)
assert counts==(vm.GetNumAtoms(),vm.GetNumBonds())''')
    md('''**Yorum:** Vancomycin'in tam kaynak yapısındaki halkalar, şekerler ve yan zincirler korunur. Karmaşıklık, çizim boyutunu artırmayı gerektirir; atom/bağ silerek daha basit bir molekül oluşturulmaz. Çizimden hedef protein veya yan etki ilişkisi çıkarılmaz.''')
    md('''## 8. Atom ve bağ tablolarından öğretici molekül grafı

Linezolid örneğinde düğüm atom, kenar kovalent bağdır. Aromatiklik hem atom hem bağ özelliğidir; RDKit aromatik bağları `AROMATIC`/1,5 olarak temsil edebilir, bu ölçülmüş kesirli bağ mertebesi değildir. Atom `chiral_tag`'i yerel sıra kuralı, CIP etiketi R/S atamasıdır; birbirine doğrudan eşitlenmez. Eğitim tensörü, fingerprint veya embedding oluşturulmaz.''')
    code('''lm=Chem.Mol(mols['DB00601']);atoms,bonds=atom_bond_tables(lm)
display(pd.DataFrame(atoms));display(pd.DataFrame(bonds))
options=Draw.MolDrawOptions();options.addAtomIndices=True
indexed=Draw.MolToImage(lm,size=(1200,650),options=options,legend='DB00601 - Linezolid - atom indices')
indexed.save(FIG/'DB00601_indexed.png');display(indexed)
rdDepictor.Compute2DCoords(lm);conf=lm.GetConformer();graph=nx.Graph()
graph.add_nodes_from(range(lm.GetNumAtoms()));graph.add_edges_from((b.GetBeginAtomIdx(),b.GetEndAtomIdx()) for b in lm.GetBonds())
pos={i:(conf.GetAtomPosition(i).x,conf.GetAtomPosition(i).y) for i in graph}
colors={'C':'#c7d4dc','N':'#4b82c2','O':'#e47b73','F':'#80bd75'}
fig,ax=plt.subplots(figsize=(12,7));nx.draw_networkx_edges(graph,pos,ax=ax,edge_color=['#b9782c' if lm.GetBondBetweenAtoms(a,b).GetIsAromatic() else '#777777' for a,b in graph.edges])
nx.draw_networkx_nodes(graph,pos,ax=ax,node_size=420,node_color=[colors.get(lm.GetAtomWithIdx(i).GetSymbol(),'#bca4d5') for i in graph])
nx.draw_networkx_labels(graph,pos,ax=ax,labels={i:f'{lm.GetAtomWithIdx(i).GetSymbol()}{i}' for i in graph},font_size=9)
ax.set_title('Linezolid · atom indeksleri; turuncu kenarlar aromatik');ax.axis('off');plt.tight_layout();plt.savefig(FIG/'06_linezolid_teaching_graph.png',dpi=170);plt.show()
assert graph.number_of_nodes()==lm.GetNumAtoms() and graph.number_of_edges()==lm.GetNumBonds()''')
    md('''**Yorum:** Her atom/bağ tabloda ve grafikte aynı indeksle izlenebilir. Grafın 2D yerleşimi yalnız gösterimdir. Bağ tipi ve stereo ayrıntısı tablolarda bulunur; çizgi rengine indirgenmez. Hidrojenler kaynak SMILES/RDKit temsilindeki örtük/açık biçimleriyle korunur; bu bir drug–protein veya öğrenme grafı değildir.''')
    md('''## 9. Eksik kimya kayıtlarının geri kazanımı ve dağılımlar

Önceki 41 kimya kaydı ile eksik 21 kayıt aynı 62 kimlik üzerinden karşılaştırılır. “Ham hesap tamam” ve “temkinli QC'de bayraksız” ayrı sayılır; etiket varlığı/sıklığı kimya hesabına girmez.''')
    code('''display(recovery[~recovery.old_chemistry_available.astype(bool)])
fig,axes=plt.subplots(1,2,figsize=(12,4))
axes[0].bar(['Eski kimya','Ham RDKit','Temkinli QC'],[41,62,54],color=['#777777','#327d9b','#b9782c']);axes[0].set_ylim(0,68);axes[0].set_ylabel('İlaç / 62');axes[0].set_title('Kimya kapsamı · aynı kohort')
axes[1].bar(['Eski eksik','Ham hesapla tamam','Temkinli QC geri kazanım'],[21,21,18],color=['#777777','#327d9b','#b9782c']);axes[1].tick_params(axis='x',labelrotation=12);axes[1].set_title('Önceki 21 eksik kaydın durumu')
plt.tight_layout();plt.savefig(FIG/'07_recovery.png',dpi=160);plt.show()
fig,axes=plt.subplots(2,3,figsize=(12,7))
for ax,k in zip(axes.flat,['MW','LogP','HBD','HBA','TPSA']):
    bins=np.histogram_bin_edges(raw[k],bins=14)
    ax.hist(raw[k],bins=bins,color='#327d9b',alpha=.7,label='Ham, 62');ax.hist(clean[k].dropna(),bins=bins,histtype='step',linewidth=2,color='#b9782c',label='Temkinli, 54');ax.set(title=k,ylabel='İlaç sayısı');ax.legend(fontsize=8)
axes.flat[-1].axis('off');plt.tight_layout();plt.savefig(FIG/'08_descriptor_distributions.png',dpi=160);plt.show()''')
    md('''**Yorum:** Önceki 21 eksik kaydın hepsinde yerel yapı üzerinden ham beş değer hesaplandı; 18'i temkinli incelemede bayraksız. Gentamicin, Cefprozil ve Methenamine incelemede kaldı. Dağılım farkında Gentamicin'in çok bileşenli toplam yapısı gibi kayıt tanımı etkileri vardır; uç değerler otomatik silinmedi. Temkinli QC 54, eski 41'e ekleme hesabı değildir: eski 41'in beşi de inceleme bayrağı taşıyor (36 eski + 18 geri kazanım = 54).

## 10. PubChem, sınırlar ve tekrar üretim

Üretim analiz istemcisiyle **0 PUG REST çağrısı** yapıldı; 62 yerel kayıt yeterliydi. API formatı incelenirken web aracıyla CID 12560 için tek keşif isteği denendi, araç erişilebilir veri döndürmedi; sonuçlar özellik hesabına girmedi. Bu başarısız deneme `pubchem_query_audit.json` içinde kayıtlı. Dokümanların bazı doğrudan sayfaları CAPTCHA döndürdü; resmi indeks açıklamaları ve erişilebilir RDKit dokümanları kullanıldı. Güncel PubChem yapı yanıtı doğrulandı iddiası yok.

`wp04_pubchem.py` gerektiğinde yalnız onaylı CID, en fazla 8 CID/istek, varsayılan ağ kapalı, toplam 3 istek bütçesi, en fazla 1 istek/saniye, CID yanıt kontrolü ve hash'li önbellek uygular. Canlı sorgu yapılmadan sentetik yanıtlarla test edilir. Eksik stereo veya karışım sorununu adla arayıp tek yapı seçerek gizlemez.

Önceki raporlar korunur. Nihai 30 kategori değişmez; negatif, split, ölçekleme, protein özelliği, GNN/tensör veya eğitim yok. WP04 sonunda kullanıcı onayı beklenir.

Kaynaklar: [RDKit başlangıç](https://rdkit.org/docs/GettingStartedInPython.html), [Crippen tanımı](https://rdkit.org/docs/source/rdkit.Chem.Crippen.html), [TPSA/stereo ayrıntısı](https://www.rdkit.org/docs/RDKit_Book.html), [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest).''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'IPython in-process; real computed display outputs'})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for n in plt.get_fignums():
            buf=io.BytesIO();plt.figure(n).savefig(buf,format='png',dpi=100,bbox_inches='tight');display(Image(data=buf.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();count=0
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        count+=1
        with capture_output(display=True) as cap:r=shell.run_cell(cell.source,store_history=False)
        if r.error_in_exec or r.error_before_exec:raise RuntimeError(r.error_in_exec or r.error_before_exec)
        cell.execution_count=count;cell.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:cell.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for out in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in out.data.items()}
            cell.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=out.metadata))
    nbf.validate(nb);nbf.write(nb,ROOT/'notebooks/WP04_molecular_exploration.ipynb')
    print('Executed WP04 notebook cells:',count)


if __name__=='__main__':main()
