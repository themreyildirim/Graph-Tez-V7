"""WP05 öğretici notebook ve görseller; yalnız küçük kaydedilmiş QA okunur."""
from pathlib import Path
import io,os,base64
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]


def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP05 · Protein dizileri ve biyokimyasal özellikler

06.11.2026 · Öğren → Ham alan → Temizleme → Doğrulama → Görselleştirme.

Protein, amino asitlerin belirli sırayla bağlandığı polimerdir. Bu analiz 20 standart amino asit politikasını kullanır; X/B/Z/J/U/O veya rakamları sessizce silmez. U/O gibi standart 20 dışı kodlar her zaman biyolojik hata değildir; bu hesap politikasında ayrı QC gerektirir. Yeni diziler yalnız seçili 62 ana DrugBank kaydından gelir. Bu notebook XML'i yeniden taramaz, Drive/UniProt sorgulamaz, eğitim veya bölme yapmaz. WP04'ün sekiz inceleme molekülü de 62 ilaç içinde korunur.''')
    code('''from pathlib import Path
import sys,json,pandas as pd,numpy as np
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'AGENTS.md').exists());sys.path.insert(0,str(ROOT/'scripts'))
from wp05_proteins import parse_sequence,features,AA,GROUPS,ProteinAnalysis,Bio
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
from IPython.display import display,FileLink
pd.set_option('display.max_rows',160);pd.set_option('display.max_colwidth',130)
palette={'human':'#4b8dc2','bacteria':'#e28b4d','fungus':'#9f77ad','other_eukaryote':'#888888'}
QA=ROOT/'reports/qa/WP05';FIG=ROOT/'reports/figures/WP05';FIG.mkdir(parents=True,exist_ok=True)
def read(n):return pd.read_csv(QA/n,keep_default_na=False)
summary=json.loads((QA/'coverage_summary.json').read_text(encoding='utf-8'))
registry=read('protein_registry.csv');sequences=read('protein_sequences.csv');f=read('protein_features.csv');e=read('drug_protein_edges.csv');coverage=read('drug_coverage.csv');evidence=read('relation_evidence.csv')
display(pd.DataFrame([{'Biopython':Bio.__version__,'ilaç':len(coverage),'protein':len(registry),'dizisi doğrulanmış':len(f),'UniProt_API':0}]))''')
    md('''## 1. Amino asit, FASTA ve accession

FASTA'da `>` ile başlayan ilk satır başlıktır; izleyen satırlar dizidir. Başlıktaki protein adı amino asit hesabına katılmaz. UniProt accession P/Q/O baş harflerinden oluşan bir kalite puanı değildir. Accession biçimi ve XML `polypeptide/@id`–UniProtKB dış kimliği uyumu kontrol edilir; bağımsız UniProt kaydının güncelliği doğrulandı denmez.

Motilin receptor örneğinde ham başlık, temiz dizi başlangıcı ve uzunluk farkını doğrudan karşılaştıralım. Amino asit frekansı, kalıntı sayısının temiz dizi uzunluğuna oranıdır (0–1).''')
    code('''raw_records=json.loads((QA/'xml_protein_records.json').read_text(encoding='utf-8'))
example=next(r for d in raw_records for r in d['relations'] if r.get('polypeptide_id')=='O43193')
parsed=parse_sequence(example['raw_sequence'])
display(pd.DataFrame([{'accession':example['polypeptide_id'],'protein':example['protein_name'],'organism':example['organism'],'raw_prefix':example['raw_sequence'][:170],'header':parsed['header'],'clean_prefix':parsed['sequence'][:100],'raw_length':parsed['raw_length'],'clean_length':parsed['length'],'QC':parsed['status']}]))
display(read('amino_acid_dictionary.csv'))
display(f[f.accession.eq('O43193')][['accession','length_aa',*['AAC_'+x for x in AA]]])''')
    md('''**Yorum:** Başlık ve satır sonları ayrıldı; doğal harflerden rastgele “dizi” üretmek için regex filtresi kullanılmadı. 478 polipeptit kanıt satırının tamamı tek FASTA başlığı sonrası 20-AA dizisi verdi. Aynı accession'ın birden fazla ilaçta görünmesi diziyi yeni protein diye çoğaltmaz; 141 accession'da dizi/taksonomi çakışması yok. Bu 141 kimlik 140 farklı temiz dizi içeriyor; P0A3M5/P0A3M6 aynı diziye sahip fakat kaynak kimlikleri birleştirilmedi. Aynı dizi kimlik eşitliğini tek başına kanıtlamaz.''')
    md('''## 2. Eski hataları gerçek kayıtlarla görmek

Eski `sequence` alanı bu XML'de polipeptit amino asit dizisi değil; doğru yol `.../polypeptide/amino-acid-sequence`. Eski CSV 70 başlığı satır sonunu kaybederek diziye birleştirmiş. Başlık içindeki standart AA harflerini seçmek başlığı temizlemez; sahte kalıntı ekler. `FASTA başlığı + dizi` satır sınırı kaybolmuşsa başlığı tahmin ederek ayırmıyoruz; yeni XML dizisiyle karşılaştırıyoruz.''')
    code('''oldseq=read('legacy_sequence_audit.csv');oldid=read('legacy_identity_organism_audit.csv')
display(oldseq[['accession','starts_fasta_header','strict_parse_status','new_xml_sequence_available','extra_residues_if_old_regex','prefix_sample']].head(12))
display(pd.DataFrame([{'eski_baslıklı':int(oldseq.starts_fasta_header.sum()),'eski_prefix_skor_formülü_uyumlu':int(oldid.prefix_formula_matches.sum()),'XML_ile_karşılaştırılabilen_eski_dizi':int(oldseq.new_xml_sequence_available.sum()),'XML_eski_sequence_etiketi':summary['old_sequence_tag_present']}]))
display(read('amino_acid_group_audit.csv'))
fig,ax=plt.subplots(figsize=(9,4));values=pd.to_numeric(oldseq.extra_residues_if_old_regex,errors='coerce').dropna();ax.hist(values,bins=12,color='#b87935');ax.set(xlabel='Eski regex ile fazladan sayılan başlık harfi',ylabel='Ortak protein sayısı',title='51 XML ile eşleşen eski dizide başlık kirlenmesi');plt.tight_layout();plt.savefig(FIG/'01_legacy_header_contamination.png',dpi=160);plt.show()''')
    md('''**Yorum:** 51 ortak accession'ın eski metni yeni temiz XML dizisiyle tam olarak bitiyor; başlık harfleri 13–53 ek kalıntı üretebiliyor. Bu örnek doğrudan kaynak karşılaştırmasıdır; eski özelliklerin tamamının hangi kod revizyonuyla üretildiği ispatlanmış değildir. Eski F hem hidrofobik hem aromatik grupta, C/G hiçbir grupta; yeni açık bölümleme bunları düzeltir. Eski P/Q/O skoru 70/70 formülle uyumlu ve yeni özelliklerde yok.''')
    md('''## 3. Hedef, enzim, transporter ve carrier farklı ilişkiler

`target`: kaynakta ilaç hedef ilişkisi; tümü ana antibakteriyel mekanizma değildir. `enzyme`: metabolizma/etkileşim enzimi olabilir; hedefin yerine geçmez. `transporter`: ilaç alımı/atılımıyla ilişkili taşıyıcı; `carrier`: kaynakta taşıma/bağlanma rolü. İsim biyolojik işlevi çağrıştırsa da XML rolü silinmez. Örneğin Vancomycin için kaynakta carrier bölümündeki fare H1 reseptörü ayrıca yorum gerektirir; onu insan antibakteriyel hedefi diye yeniden etiketlemiyoruz.''')
    code('''display(read('role_summary.csv'))
display(evidence[evidence.drug_id.isin(['DB00199','DB00254','DB00512','DB00601'])][['drug_id','role','relation_name','accession','organism','actions','known_action','relation_qc']])
roles=read('role_summary.csv');fig,ax=plt.subplots(figsize=(9,4));ax.bar(roles.role,roles.unique_drug_protein_role_edges,color=['#397e9b','#8666a9','#4c9a7d','#bd8438']);ax.set(ylabel='Benzersiz ilaç–accession–rol üçlüsü',title='İlişki türleri birleştirilmeden korunur');plt.tight_layout();plt.savefig(FIG/'02_relation_roles.png',dpi=160);plt.show()''')
    md('''**Yorum:** 476 benzersiz tipli kenar var. Rol unutulunca 457 ilaç–protein çifti kalır; fark, aynı çiftin birden çok biyolojik rol taşıyabilmesidir. `target` kapsamı 55, tüm roller kapsamı 60; 60 hedefli ilaç demek doğru olmaz. 478 kaynak polipeptit satırı da kenar sayısı değildir; kaynak tekrarları izleriyle korunup kenarlar tekilleştirildi.''')
    md('''## 4. Protein olmayan ve kimliği/dizisi bulunmayan hedefler

rRNA bir protein dizisi değildir; DNA, membran ve peptidoglikan alt yapıları için protein özelliği uydurulmaz. “Peptidoglycan transpeptidase” ise enzim adıdır; polipeptit kaydı yok diye hücre duvarı maddesi sayılmaz. 30S ribosomal protein adında da protein var; belirli accession/dizi bu kayıtta eksik.''')
    code('''display(read('nonprotein_or_unresolved_targets.csv')[['drug_id','drug_name','relation_name','relation_qc','source_path']])
display(read('priority_seven.csv'))''')
    md('''**Yorum:** Doxycycline, Vancomycin, Linezolid, Tinidazole ve Telithromycin'de diğer roller üzerinden doğrulanmış protein dizileri var; antibakteriyel protein hedefi eksikliği böylece giderilmiş sayılmaz. Tobramycin'de RNA/membran hedefleri var; Methenamine'de bu dört bölümde ilişki yok. İkisi de kapsamda kalır; “biyolojik hedef yok” veya “yan etki yok” çıkarımı yapılmaz.''')
    md('''## 5. Protein uzunluğu, molekül ağırlığı ve AAC

Uzunluk temiz amino asit sayısıdır. MW, Biopython 1.88'de ortalama serbest amino asit kütleleri toplamından her peptit bağı için su çıkarılarak hesaplanır; burada tek doğrusal, modifikasyonsuz dizi varsayılır. Birim Da (kDa = Da/1000); deneysel olgun protein kütlesi, multimer veya glikozillenmiş kütle değildir. AAC frekansları yuvarlanmadan hesaplanır, toplamı 1'dir.''')
    code('''display(registry[['accession','protein_name','organism','sequence_validated']].merge(f[['accession','length_aa','molecular_weight_Da']],on='accession').sort_values('length_aa',ascending=False).head(12))
fig,axes=plt.subplots(1,2,figsize=(12,4));axes[0].hist(f.length_aa,bins=20,color='#397e9b');axes[0].set(xlabel='Uzunluk (AA)',ylabel='Benzersiz protein',title='141 protein · uzunluk dağılımı')
axes[1].hist(f.molecular_weight_Da/1000,bins=20,color='#4c9a7d');axes[1].set(xlabel='Hesaplanan MW (kDa)',ylabel='Benzersiz protein',title='Tam dizi üzerinden molekül ağırlığı');plt.tight_layout();plt.savefig(FIG/'03_length_and_mass.png',dpi=160);plt.show()
aac=f[['AAC_'+a for a in AA]];display(pd.DataFrame({'AA':list(AA),'protein_eşit_ağırlıklı_ortalama':aac.mean().values,'kalıntı_ağırlıklı_oran':np.average(aac,axis=0,weights=f.length_aa)}))
fig,ax=plt.subplots(figsize=(10,4));ax.bar(list(AA),aac.mean().values,color='#397e9b');ax.set(xlabel='Standart amino asit',ylabel='Protein başına ortalama frekans',title='AAC · her protein eşit ağırlıklı');plt.tight_layout();plt.savefig(FIG/'04_amino_acid_composition.png',dpi=160);plt.show()''')
    md('''**Yorum:** Uzunluklar 92–4.655 AA. Çok uzun kayıtlar otomatik kesilmedi; 2D/3D yapı üretilmiyor. AAC grafiğinde her protein eşit ağırlıklı; tüm kalıntılar bir havuzda sayılsaydı uzun proteinler daha ağır basardı. Bu iki istatistik aynı değildir. Protein büyüklüğü tek başına ilaç yan etki riski göstermez.''')
    md('''## 6. pI, aromatiklik, GRAVY ve pH'ya bağlı yük

Teorik pI, Bjellqvist pKa tabanlı yük modelinde net yükün yaklaşık sıfır olduğu pH'dır. İki uç ve iyonlaşabilen yan zincirler dikkate alınır; protein katlanması/PTM/ortam ayrıntıları bilinmez. Bisection 0–14 aralığında yürütülür; sonuç deneysel pI değildir. Aromatiklik `(F+W+Y)/L`; GRAVY Kyte–Doolittle kalıntı hidropati puanlarının ortalaması, boyutsuz. Net yük pH 7,0'da temel yük e cinsinden kuramsal toplamdır; pozitif gruptaki histidin sayısını sabit +1 yük saymak doğru değildir.''')
    code('''display(f[['accession','isoelectric_point','aromaticity_fraction','gravy_kyte_doolittle','net_charge_pH7']].head(12))
fig,axes=plt.subplots(1,3,figsize=(13,4))
for ax,col,title in zip(axes,['isoelectric_point','gravy_kyte_doolittle','net_charge_pH7'],['Teorik pI','GRAVY · Kyte–Doolittle','Net yük · pH 7,0']):
    ax.hist(f[col],bins=18,color='#397e9b');ax.set(xlabel=title,ylabel='Protein')
plt.tight_layout();plt.savefig(FIG/'05_biochemical_properties.png',dpi=160);plt.show()
seq=sequences.set_index('accession').loc['O43193','sequence'];analysis=ProteinAnalysis(seq);ph=np.linspace(0,14,100)
fig,ax=plt.subplots(figsize=(9,4));ax.plot(ph,[analysis.charge_at_pH(float(p)) for p in ph]);ax.axhline(0,color='gray',ls='--');ax.set(xlabel='pH',ylabel='Tahmini net yük (e)',title='Motilin receptor O43193 · dizi tabanlı yük eğrisi');plt.tight_layout();plt.savefig(FIG/'06_charge_curve.png',dpi=160);plt.show()''')
    md('''**Yorum:** Aynı proteinin yükü pH ile değişir; pozitif/negatif amino asit oranı gerçek net yükle aynı ölçü değildir. GRAVY bütün dizinin ortalaması olduğundan yerel transmembran parçalarını tek başına kanıtlamaz. Bu değerler ölçülmüş işlev veya klinik risk değildir.''')
    md('''## 7. Yeni, açık amino asit grupları ve grup dipeptitleri

Eski 5 grubun yerine 20 amino asidi tam ve çakışmasız kapsayan açık bir bölümleme tanımlandı: nonpolar/nonaromatik AGILMPV, aromatik FWY, polar yüksüz CNQST, bazik HKR, asidik DE. Bu tezdeki operasyonel bölümlemedir; tek evrensel biyokimyasal sınıflama değildir. Y aromatik gruba önceliklidir; histidinin pH bağımlılığı pI/yük hesabında ayrıca ele alınır.

Grup DC: ardışık, yönlü `i→i+1` grup çiftlerinin sayısı / `(L−1)`. Atlanan kalıntı yok. Tek amino asitli dizide dipeptit tanımsız ve null olur; veri yerine sıfır doldurulmaz. Bu örneklemde bütün diziler en az 92 AA.''')
    code('''display(pd.DataFrame([{'grup':g,'AA':members} for g,members in GROUPS.items()]))
groups=list(GROUPS);row=f.set_index('accession').loc['O43193'];matrix=np.array([[row[f'DC_{a}__{b}'] for b in groups] for a in groups])
fig,ax=plt.subplots(figsize=(9,6));im=ax.imshow(matrix,cmap='Blues');ax.set_xticks(range(5),groups,rotation=20,ha='right');ax.set_yticks(range(5),groups);ax.set(xlabel='Sonraki kalıntı grubu',ylabel='Önceki kalıntı grubu',title='O43193 · grup dipeptit frekansları');fig.colorbar(im,ax=ax,label='Frekans / (L−1)');plt.tight_layout();plt.savefig(FIG/'07_group_dipeptides.png',dpi=160);plt.show()
display(pd.DataFrame([{'AAC_toplam':f[['AAC_'+a for a in AA]].sum(axis=1).min(),'grup_DC_toplam_min':f[[c for c in f if c.startswith('DC_')]].sum(axis=1).min()}]))''')
    md('''**Yorum:** F artık iki kez sayılmıyor, C ve G kapsamda. 25 hücre yönlü komşuluk frekansıdır; `A→B` ile `B→A` aynı hücre değil. Bu dizisel özet 3D protein teması veya PPI kenarı değildir; grup tanımı kaynak/sürümle dondurulmalıdır.''')
    md('''## 8. Organizma: insan ≠ tüm diğerleri bakteri

XML'deki polipeptit organizması ve taksonomi ID'si aynen korunur. İnsan 9606 veya açık Humans/Homo sapiens adı; bakteriler yalnız açık gözden geçirilmiş organizma adlarıyla sınıflandı. Yeast mantar, Mouse ve Plasmodium diğer ökaryot olarak ayrıldı. Kaynak isimlerinin 29 ayrı ad/taksonomi grubu var; bunlar 29 ayrı tür demek değildir. 28 farklı dolu taksonomi ID'si ve bir ID'siz Pseudomonas adı var; tür/strain birleştirmesi yapılmadı.''')
    code('''display(read('organism_summary.csv'))
counts=registry.organism_group.value_counts();fig,ax=plt.subplots(figsize=(9,4));counts.plot.bar(ax=ax,color=[palette[g] for g in counts.index]);ax.set(ylabel='Benzersiz accession',title='Organizma sınıfı · 141 protein');plt.xticks(rotation=15);plt.tight_layout();plt.savefig(FIG/'08_organism_groups.png',dpi=160);plt.show()
rg=e.merge(registry[['accession','organism_group']],on='accession');cross=pd.crosstab(rg.role,rg.organism_group);display(cross)
cross.plot.bar(stacked=True,figsize=(10,4),color=[palette[g] for g in cross.columns]);plt.ylabel('Tipli ilaç–protein kenarı');plt.title('İlişki rolü ve organizma sınıfı');plt.xticks(rotation=0);plt.tight_layout();plt.savefig(FIG/'09_role_organism.png',dpi=160);plt.show()''')
    md('''**Yorum:** 75 bakteri, 63 insan, 1 mantar, 2 diğer ökaryot accession var. Bu yan ilişki kayıtlarının tümünün antibakteriyel mekanizmayı veya insan yan etki mekanizmasını anlattığı iddia edilmez. Bu organizmalar yalnız izinli DrugBank içinde görüldü; yeni türler için STRING veya başka veri indirilmedi.''')
    md('''## 9. 62 ilacın protein modalitesi

Target-only ve tüm rol kapsamını yan yana gösterelim. Eksik modaliteyi bir ilacın biyolojik hedefi veya yan etkisi yokmuş gibi kodlamayız. İleride kimya tabanlı alternatif, bağımsız eksiklik maskesi veya rol bazlı ablation değerlendirilebilir; bugün model kararı/tensör yok.''')
    code('''display(coverage.sort_values('name'))
fig,axes=plt.subplots(1,2,figsize=(12,4));bins=np.arange(0,max(coverage.all_role_proteins)+2)-.5
axes[0].hist(coverage.all_role_proteins,bins=bins,color='#397e9b');axes[0].set(xlabel='Benzersiz protein / ilaç · tüm roller',ylabel='İlaç',title='Sıfırlar dahil 62 ilaç')
axes[1].bar(['Target proteini','Herhangi rol + dizi','Protein modalitesi eksik'],[55,60,2],color=['#397e9b','#4c9a7d','#b87935']);axes[1].set_ylim(0,66);axes[1].tick_params(axis='x',rotation=10);axes[1].set_title('Örtüşen kapsam sayıları; çubuklar toplanmaz');plt.tight_layout();plt.savefig(FIG/'10_drug_coverage.png',dpi=160);plt.show()''')
    md('''**Yorum:** Tüm rol kapsamında eksik iki ilaç Tobramycin ve Methenamine. Protein özelliği olan ilaçları filtreleyip diğerlerini dosyadan silmedik. WP04'te incelemede kalan sekiz molekül de listede duruyor; protein varlığı moleküler QC kararını değiştirmez.''')
    md('''## 10. İki parçalı ilaç–protein grafı ve önemli düğümler

Tam QA grafı 62 ilaç + 141 protein içerir; kenar, tekil kaynak ilaç–accession çiftidir. Çoklu roller kenar açıklamasında korunur. Aşağıdaki küçük alt graf, seçili sekiz ilaç ile yalnız gösterim için en bağlantılı 16 proteini alır; tam ağa göre kapsam/merkezilik kaybı olabilir. İzole ilaçlar çizimde tutulur. Derece merkezilik göstergesidir, risk skoru değildir.''')
    code('''G=nx.Graph()
G.add_nodes_from('D:'+i for i in coverage.id);G.add_nodes_from('P:'+i for i in registry.accession)
for r in e.itertuples():G.add_edge('D:'+r.drug_id,'P:'+r.accession)
metrics=[]
for r in registry.itertuples():metrics.append({'accession':r.accession,'protein':r.protein_name,'organism_group':r.organism_group,'degree_drugs':G.degree('P:'+r.accession),'degree_fraction_62':G.degree('P:'+r.accession)/62})
metrics=pd.DataFrame(metrics).sort_values(['degree_drugs','accession'],ascending=[False,True]);metrics.to_csv(QA/'protein_graph_metrics.csv',index=False,encoding='utf-8-sig');display(metrics.head(12))
chosen=['DB01060','DB00537','DB00199','DB00601','DB00254','DB00512','DB00684','DB06799'];near=e[e.drug_id.isin(chosen)].groupby('accession').drug_id.nunique();picked=sorted(near.index,key=lambda a:(-near[a],a))[:16]
H=G.subgraph(['D:'+i for i in chosen]+['P:'+i for i in picked]).copy()
pos={'D:'+a:(0,-i/(len(chosen)-1)) for i,a in enumerate(chosen)}|{'P:'+a:(1,-i/(len(picked)-1)) for i,a in enumerate(picked)}
names=coverage.set_index('id').name.to_dict();groups=registry.set_index('accession').organism_group.to_dict()
palette={'human':'#4b8dc2','bacteria':'#e28b4d','fungus':'#9f77ad','other_eukaryote':'#888888'}
colors=['#4c9a7d' if n.startswith('D:') else palette.get(groups[n[2:]],'#999999') for n in H]
labels={n:names[n[2:]] if n.startswith('D:') else n[2:] for n in H}
fig,ax=plt.subplots(figsize=(13,10));nx.draw_networkx_edges(H,pos,ax=ax,alpha=.3);nx.draw_networkx_nodes(H,pos,ax=ax,node_color=colors,node_size=420);nx.draw_networkx_labels(H,pos,labels=labels,font_size=9,ax=ax);ax.set_title('Küçük alt graf · ilaç yeşil, insan protein mavi, bakteri turuncu, diğer gri');ax.axis('off');plt.tight_layout();plt.savefig(FIG/'11_bipartite_subgraph.png',dpi=170);plt.show()
graph_summary={'drug_nodes':62,'protein_nodes':141,'untyped_edges':G.number_of_edges(),'components':nx.number_connected_components(G),'isolates':list(nx.isolates(G)),'display_subgraph_nodes':H.number_of_nodes(),'display_subgraph_edges':H.number_of_edges()};(QA/'graph_summary.json').write_text(json.dumps(graph_summary,ensure_ascii=False,indent=2),encoding='utf-8');display(pd.DataFrame([graph_summary]))
traces=[]
for a,b in H.edges:
    traces.append(go.Scatter(x=[pos[a][0],pos[b][0]],y=[pos[a][1],pos[b][1]],mode='lines',line=dict(color='#bbbbbb',width=1),hoverinfo='skip',showlegend=False))
hover=[]
for n in H:
    if n.startswith('D:'):hover.append(n[2:]+' · '+names[n[2:]])
    else:
        row=registry.set_index('accession').loc[n[2:]];hover.append(n[2:]+' · '+row.protein_name+' · '+row.organism)
traces.append(go.Scatter(x=[pos[n][0] for n in H],y=[pos[n][1] for n in H],mode='markers+text',text=[labels[n] for n in H],textposition='middle right',marker=dict(size=13,color=colors),hovertext=hover,hoverinfo='text',showlegend=False))
fig=go.Figure(traces);fig.update_layout(title='WP05 kaynak alt grafı · eğitim grafı değil',height=850,xaxis=dict(visible=False),yaxis=dict(visible=False),margin=dict(l=160,r=180));fig.write_html(FIG/'drug_protein_interactive.html',include_plotlyjs=True,full_html=True);display(FileLink(str(FIG/'drug_protein_interactive.html')))''')
    md('''**Yorum:** Tam graf derecesi birçok ilaca bağlanan paylaşılan proteinleri ortaya çıkarır. En yüksek dereceli düğümler çoğunlukla metabolizma/taşıma/bağlanma rollerinde olabilir; ana antibakteriyel hedef oldukları sonucu çıkmaz. Her düğüm/kenarın kaynak izi ilişki tablosuna gider. 476 tipli kenarı 457 çiftte gösteren bu grafik, rol bilgisini özellik/öğrenme girdisine çevirmedi. HTML çevrimdışı Plotly içerir; canlı tarayıcı etkileşimi test edilmedi.

## Kapanış: desteklenen düğüm/kenarlar ve sınırlar

DrugBank ana ilaç düğümü, yerel accession/dizi protein düğümü, dört farklı ilaç–protein rolü gerçek veriye dayanıyor. rRNA/DNA/membran/hedef yapıları ayrı kaynak hedef varlıkları olarak tutulabilir; bugün protein düğümü/özelliği üretilmedi. Önceki SIDER PT ilişkileri ayrı hedef etiket katmanıdır. PPI, atom grafı, eğitim tensörü, negatif örnek veya ilaç ayrımı bu WP'de oluşturulmadı. Özellik tablosu kimlik dışında yalnız diziden hesaplanan sayıları içerir; organizma/skor/merkezilik/PT sayısı X'e eklenmez.

Kimlik ve diziler yalnız yerel XML içinde doğrulandı. Bağımsız UniProt güncellik/dizi/izoform sorgusu yok; eksik hedefe isim benzerliğiyle accession atanmadı. WP05 sonunda kullanıcı onayı beklenir.

Yöntem belgeleri: [Biopython ProtParam](https://biopython.org/docs/latest/api/Bio.SeqUtils.ProtParam.html), [pI/yük yöntemi](https://biopython.org/docs/latest/api/Bio.SeqUtils.IsoelectricPoint.html), [UniProt accession biçimi](https://www.uniprot.org/help/accession_numbers).''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'IPython in-process; actual computed outputs'})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*a,**kw):
        for n in plt.get_fignums():
            b=io.BytesIO();plt.figure(n).savefig(b,format='png',dpi=100,bbox_inches='tight');display(Image(data=b.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for c in nb.cells:
        if c.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:result=shell.run_cell(c.source,store_history=False)
        if result.error_in_exec or result.error_before_exec:raise RuntimeError(result.error_in_exec or result.error_before_exec)
        c.execution_count=n;c.outputs=[]
        for name,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
            if value:c.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for o in cap.outputs:
            data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in o.data.items()}
            c.outputs.append(nbf.v4.new_output('display_data',data=data,metadata=o.metadata))
    nbf.validate(nb);nbf.write(nb,ROOT/'notebooks/WP05_protein_exploration.ipynb');print('Executed WP05 code cells',n)


if __name__=='__main__':main()
