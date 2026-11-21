"""WP01 notebook'unu kurar ve tüm hücrelerini sırayla çalıştırır."""
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT=Path(__file__).resolve().parents[1]

def main():
    nb=nbf.v4.new_notebook(); cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP01 Graf kavramları ve küçük ilaç–protein ağı

**05.11.2026 · Çalıştırılmış öğretici notebook.** Hücrelerin altındaki tablolar ve grafikler gerçek yürütme çıktılarıdır. Sıra: kavram → oyuncak örnek → gerçek legacy alt graf → test → yorum.

Bu paket veri temizleme veya J01 kohortu oluşturma paketi değildir. Gerçek örnek eski izinli `ilac_protein_eslesmesi_v6.csv` ilişkilerinin sınırlı bir gösterimidir. Kaynak kayıtları yeniden biyolojik doğrulamadan geçirilmiş sayılmaz. Yeni veri, model eğitimi, `kalite_skoru` veya yan etki hedef kenarı kullanılmaz.

**Çalıştırma:** Proje içinden Jupyter ile açıp “Restart Kernel and Run All” seçin. Notebook proje kökünü kendisi bulur; internet gerekmez. Kaynak CSV'nin tamamı yerelde saklanmadı; yalnız görseldeki 10 ilişkinin kaynak satırı belirtilmiş eğitim örneği JSON olarak tutuldu.''')
    code('''from pathlib import Path
import sys, json, platform
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown, FileLink
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'AGENTS.md').exists())
sys.path.insert(0, str(ROOT/'scripts'))
from wp01_graphs import toy_graph, real_graph, metrics, summary, draw, real_positions, interactive
OUT = ROOT/'reports/qa/WP01'; OUT.mkdir(parents=True, exist_ok=True)
display(pd.DataFrame({'bileşen':['Python','NetworkX','pandas'], 'sürüm':[platform.python_version(),nx.__version__,pd.__version__]}))''')
    md('''## 1 Düğüm ve kenar

Graf $G=(V,E)$ bir düğüm kümesi ve bu düğümler arasındaki kenarlardan oluşur. Düğüm bir varlığı, kenar tanımlanmış bir ilişkiyi temsil eder. Aşağıdaki **sentetik** grafın A–B–C üçgeni, C–D uzantısı ve bağlantısız E düğümü var. A ile B arasındaki çizgi bir kayıt, geometrik uzunluğu ise çizim tercihidir.

Tezde düğüm ilaç veya protein; kenar kaynakta bildirilen ilaç→hedef ilişkisi olabilir. İlaç ve protein kimliklerini farklı öneklerle saklamak aynı metnin yanlışlıkla aynı düğüm olmasını engeller.''')
    code('''G = toy_graph()
display(pd.DataFrame({'düğüm':list(G), 'komşular':[sorted(G.neighbors(n)) for n in G]}))
display(pd.DataFrame(G.edges(), columns=['uç 1','uç 2']))
pos = {'A':(0,1),'B':(0,0),'C':(1,.5),'D':(2,.5),'E':(2,1.4)}
draw(G,'01_nodes_edges','Sentetik örnek · 5 düğüm, 4 kenar, 2 bileşen',pos=pos)
display(summary(G))''')
    md('''**Okuma:** E'nin listede olup kenarı olmaması onu izole düğüm yapar. Veride ilişki bulunmaması biyolojik ilişkinin imkânsız olduğu anlamına gelmez. Kaynakta hiç kaydı olmayan ilaçlar yalnız kenar tablosundan kurulan grafın içine kendiliğinden girmez.''')
    md('''## 2 Yönlü ve yönsüz graf

`nx.Graph` ilişkiyi simetrik işler: A–B varsa B'nin komşusu A'dır. `nx.DiGraph` için A→B, B→A'yı yaratmaz. **Ardıl** dışarı giden, **öncül** içeri gelen komşudur. Buradaki ok yönü ilişki şemasıdır; biyolojik nedensellik veya fiziksel sinyal akışı kanıtı değildir.''')
    code('''D = nx.DiGraph([('A','B'),('B','C')])
display(pd.DataFrame([{'düğüm':n,'öncüller':list(D.predecessors(n)),'ardıllar':list(D.successors(n)),
                      'giriş derecesi':D.in_degree(n),'çıkış derecesi':D.out_degree(n)} for n in D]))
draw(D,'02_direction','Sentetik yönlü graf · A → B → C',pos={n:pos[n] for n in D})
display(pd.DataFrame({'sorgu':['A→C yolu','C→A yolu','yönsüz C–A yolu'],
                     'var mı':[nx.has_path(D,'A','C'),nx.has_path(D,'C','A'),nx.has_path(D.to_undirected(),'C','A')]}))''')
    md('''**Tez açısından:** İlaç→protein şemasında protein ardılı yok diye protein bağlantısız değildir; giriş kenarları vardır. Merkezilik hesaplarken yönlü ilişkiyi mi yoksa yönsüz bağlantı izdüşümünü mü kullandığımızı açıkça seçmeliyiz.''')
    md('''## 3 Komşuluk derece ve 1-hop 2-hop

Bir düğümün komşuları doğrudan bağlı olduğu düğümlerdir. Derece bunların sayısıdır (burada basit, kendine kenarsız graf). Yönsüz grafın dereceler toplamı $2|E|$ olur. “Tam 2-hop” uzaklığı iki olanları; `ego_graph(radius=2)` ise merkez dahil uzaklığı **en çok** iki olanları verir.''')
    code('''distance = nx.single_source_shortest_path_length(G,'A',cutoff=2)
display(pd.DataFrame([{'düğüm':n,'A’ya uzaklık':distance.get(n,'erişilemiyor'),'derece':G.degree(n)} for n in G]))
display(pd.DataFrame({'küme':['tam 1-hop','tam 2-hop','en çok 2-hop'],
                     'düğümler':[[n for n,d in distance.items() if d==1],[n for n,d in distance.items() if d==2],list(nx.ego_graph(G,'A',radius=2))]}))
draw(G,'03_hops','Sentetik komşuluk · sarı merkez A; D iki adım uzakta',pos=pos,highlight=['A'])
assert sum(dict(G.degree()).values()) == 2*G.number_of_edges()''')
    md('''## 4 Ağırlık güç ve uzaklık

Ağırlığın anlamı açıkça tanımlanmalıdır. Aşağıdaki sentetik ağırlık **mesafe/maliyet**: A–B=1, B–C=1, A–C=5. Ağırlıksız en kısa yol tek kenarlı A–C; mesafe toplamını en aza indiren yol A–B–C'dir. Daha büyük güven/etkileşim skoru daha uzun mesafe anlamına gelmez; böyle bir dönüşüm gerekçesiz yapılamaz. Gerçek alt grafımızda doğrulanmış kenar ağırlığı bulunmadığı için ağırlık kullanılmaz.''')
    code('''W = nx.Graph()
W.add_weighted_edges_from([('A','B',1),('B','C',1),('A','C',5)],weight='distance')
display(pd.DataFrame([{'başlangıç':a,'bitiş':b,**v} for a,b,v in W.edges(data=True)]))
display(pd.DataFrame({'yöntem':['kenar sayısı','mesafe toplamı'],
                     'A–C yolu':[nx.shortest_path(W,'A','C'),nx.shortest_path(W,'A','C',weight='distance')],
                     'uzunluk':[nx.shortest_path_length(W,'A','C'),nx.shortest_path_length(W,'A','C',weight='distance')]}))
draw(W,'04_weights','Sentetik mesafe ağırlıkları · 1 + 1 < 5',pos={n:pos[n] for n in W},edge_labels=nx.get_edge_attributes(W,'distance'))''')
    md('''## 5 Merkezilik

**Derece merkeziliği** $k/(N-1)$ doğrudan bağlantıyı ölçer. **Aradalık** (betweenness), en kısa yolların ne kadarının düğümden geçtiğini gösterir; uç düğümler sayılmaz ve eşit yollar paylaştırılır. **Yakınlık** (closeness), erişilen düğümlere uzaklıkla ilişkilidir. Burada NetworkX'in kopuk bileşenleri erişilebilir oranla düzelten `wf_improved=True` seçeneği kullanılır.

Bu üç soru farklıdır: “Kaç bağlantısı var?”, “Kaç en kısa yol üzerinde?”, “Diğerlerine ne kadar yakın?”. Yüksek değer biyolojik önem veya yan etki riski ölçümü değildir; kaynak kapsamından ve düğüm seçiminden etkilenir.''')
    code('''toy_metrics = metrics(G)
display(toy_metrics.round(4))
ax=toy_metrics.set_index('label')[['degree_centrality','betweenness','closeness_WF']].plot.bar(figsize=(10,4),rot=0)
ax.set_title('Sentetik graf · farklı merkezilik tanımları'); ax.set_ylabel('Normalize değer')
plt.tight_layout(); plt.savefig(ROOT/'reports/figures/WP01/05_centrality.png',dpi=160); plt.show()''')
    md('''**Okuma:** C, üçgeni D'ye bağladığı için aradalığı yükselir; E sıfır değer alır. İlaç–protein gibi iki parçalı graflarda ilaç ve protein rollerini ayrı karşılaştırmak gerekir. Buradaki derece normalizasyonu tüm N−1 düğüme göredir; karşı parçanın büyüklüğüne göre normalize edilmiş özel bipartit merkezilik değildir.''')
    md('''## 6 Alt graf ve bağlı bileşen

Seçilen düğümler arasındaki tüm mevcut kenarları korursak **indüklenmiş alt graf** elde ederiz. Kenar alt grafı yalnız seçilen kenarları içerir. Bir bağlı bileşende her iki düğüm arasında yol vardır; bileşenler arasında yol yoktur. Merkezilik alt graf içinde yeniden hesaplanınca değişebilir.''')
    code('''H = G.subgraph(['A','B','C']).copy()
display(pd.DataFrame({'bileşen':range(1,nx.number_connected_components(G)+1),
                     'düğümler':[sorted(c) for c in nx.connected_components(G)]}))
display(pd.DataFrame({'ölçüm':['C tüm grafta derece','C üçgen alt grafta derece','tüm graf yoğunluk','üçgen yoğunluk'],
                     'değer':[G.degree('C'),H.degree('C'),nx.density(G),nx.density(H)]}))
draw(H,'06_subgraph','İndüklenmiş alt graf · A, B, C üçgeni',pos={n:pos[n] for n in H})''')
    md('''## 7 İzinli gerçek veriden küçük ilaç–protein alt grafı

Kaynak: `ilac_protein_eslesmesi_v6.csv` (Drive, 153×5). Dört ilaç **öğretici amaçla** seçildi: Ciprofloxacin, Norfloxacin, Levofloxacin, Amoxicillin. Yalnız Humans, tabloda açık yazılı H. influenzae KW20/Rd ve Helicobacter pylori organizma metinlerindeki ilişkiler gösterildi. Seçim; ortak hedefler, tek ilaca bağlı hedef ve ayrı bileşen görülmesi içindir. Bir J01 kohortu veya tüm hedef ağı değildir.

Örnek JSON sadece seçilen 10 ilişkinin kaynak satırlarını ve provenansı saklar. CSV'nin tamamı indirilip dosya olarak kaydedilmedi. Organizma adı içeren protein ilişkilerini göstermek yeni organizma STRING veri seti kullanmak anlamına gelmez; burada PPI yoktur.''')
    code('''sample = json.loads((ROOT/'reports/qa/wp01_graph_sample.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'kaynak':sample['source_url'],'son değişiklik':sample['source_modified_time'],
                       'kaynak satır':sample['source_rows'],'seçili ilişki':len(sample['relations'])}]))
relations = pd.DataFrame(sample['relations'])
display(relations)
display(pd.DataFrame({'alan':relations.columns,'boş hücre':[(relations[c].isna() | relations[c].astype(str).str.strip().eq('')).sum() for c in relations],
                      'kayıt sayısı':len(relations)}))
R = real_graph(sample); U = R.to_undirected()
display(summary(R).round(4))
display(pd.DataFrame([{'ilaç':R.nodes[n]['label'],'giriş':R.in_degree(n),'çıkış':R.out_degree(n)} for n in R if R.nodes[n]['kind']=='drug']))''')
    md('''**Şema:** `drug:DB…` ve `protein:UniProt…` farklı düğüm tipleri, `targets_legacy` tek kenar tipidir. Düğüm etiketleri okunabilirlik içindir; birleştirme anahtarı gen adı değildir. Aynı gen adı farklı organizmalarda aynı protein anlamına gelmez. Eski kaynak kaydı, doğrulanmış bağlanma gücü veya klinik etki olarak yorumlanmaz.''')
    code('''rp = real_positions(R)
labels = {n:R.nodes[n]['label']+'\\n'+R.nodes[n]['identifier'] for n in R}
draw(R,'07_real_graph','Gerçek legacy alt graf · mavi ilaç → yeşil protein',pos=rp,labels=labels)
component_table = pd.DataFrame([{'bileşen':i,'düğüm':len(c),'kenar':U.subgraph(c).number_of_edges(),
                                 'etiketler':', '.join(R.nodes[n]['label'] for n in sorted(c))}
                                for i,c in enumerate(sorted(nx.connected_components(U),key=len,reverse=True),1)])
display(component_table)''')
    md('''**Grafiğin anlamı:** Ortak proteinler birden çok ilaca bağlanır. Amoxicillin bu seçimde yalnız PBP1 (Q8L103) ilişkisiyle ayrı bileşendedir. Bu görünüm ilacın gerçekte yalnız bir hedefi olduğunu kanıtlamaz; filtre ve eski tablo kapsamının sonucudur. Grafın iki parçalı yapısı nedeniyle üçgen/clustering=0 beklenir; bu değer “biyoloji seyrek” sonucunu tek başına vermez.

Özet tablosundaki yoğunluk yönlü graf için $10/(9·8)=0,1389$ değeridir. Yönsüz izdüşümde $10/36=0,2778$; yalnız izin verilen ilaç–protein çiftlerini payda alırsak $10/(4·5)=0,5$ olur. Paydaları farklı bu ölçümler birbirinin yerine kullanılamaz.''')
    code('''real_metrics = metrics(R)
display(real_metrics.round(4))
display(pd.DataFrame([{'düğüm':R.nodes[n]['label'],'tür':R.nodes[n]['kind'],
                       'öncüller':list(R.predecessors(n)),'ardıllar':list(R.successors(n))} for n in R]))
ax=real_metrics.set_index('label')[['degree_centrality','betweenness','closeness_WF']].plot.barh(figsize=(11,6))
ax.set_title('Gerçek alt graf · yönsüz izdüşümde merkezilik');ax.set_xlabel('Normalize değer')
plt.tight_layout();plt.savefig(ROOT/'reports/figures/WP01/08_real_metrics.png',dpi=160);plt.show()
real_metrics.to_csv(OUT/'node_metrics.csv',index=False,encoding='utf-8-sig')
component_table.to_csv(OUT/'components.csv',index=False,encoding='utf-8-sig')''')
    md('''**Tez açısından:** Derece ve aradalığı yüksek düğümler bu alt grafın bağlantı düzenini özetler. Graf küçültülünce sıralama değişebilir. Bu değerleri kalite skoru yerine kullanıp model girdisi yapmıyoruz. İlaç ve proteinleri farklı biyolojik rolleriyle okumak gerekir; gözlenen derece farmakolojik etki büyüklüğü değildir.''')
    md('''## 8 Gerçek veride 1-hop ve 2-hop

Yönlü ilaç→protein grafında bir ilacın ardılları hedefleridir. Proteinlerden dışarı giden kenar olmadığı için yönlü iki adımla başka ilaca ulaşılmaz. **Yönsüz izdüşümde** ilaç–protein–ilaç yolu ortak hedef paylaşımını gösterebilir. Bu, PPI veya ilaç–ilaç etkileşim kanıtı değildir.''')
    code('''center='drug:DB00537'
ds=nx.single_source_shortest_path_length(U,center,cutoff=2)
display(pd.DataFrame([{'ID':n,'etiket':R.nodes[n]['label'],'tür':R.nodes[n]['kind'],'hop':d} for n,d in ds.items()]))
display(pd.DataFrame({'sorgu':['yönlü en çok 2-hop','yönsüz en çok 2-hop'],
                     'düğüm sayısı':[len(nx.ego_graph(R,center,radius=2)),len(nx.ego_graph(U,center,radius=2))]}))
ego=U.subgraph(ds).copy()
draw(ego,'09_real_ego','Ciprofloxacin · yönsüz en çok 2-hop alt grafı',pos={n:rp[n] for n in ego},
     labels={n:labels[n] for n in ego},highlight=[center])''')
    md('''## 9 NetworkX ve HeteroData fikri

NetworkX'te türleri düğüm/kenar metadata'sında tutuyoruz. İleride `HeteroData` aynı fikri ayrı tür depoları ve tamsayı indeksleriyle temsil eder: `drug`, `protein`, `(drug, targets, protein)`. Aşağıdaki indeks tablosu yalnız temsil örneğidir; PyG grafı veya model oluşturulmaz. İleride yan etki ilişkileri hedef olacağı için test hedeflerinin eğitim grafına eklenmemesi ayrıca sınanmalıdır.''')
    code('''drug_nodes=sorted(n for n in R if R.nodes[n]['kind']=='drug')
protein_nodes=sorted(n for n in R if R.nodes[n]['kind']=='protein')
di={n:i for i,n in enumerate(drug_nodes)};pi={n:i for i,n in enumerate(protein_nodes)}
display(pd.DataFrame([{'kaynak indeksi':di[a],'hedef indeksi':pi[b],'ilişki':'drug → targets → protein',
                       'ilaç':a,'protein':b} for a,b in R.edges]))
html_path=ROOT/'reports/figures/WP01/real_graph_interactive.html'
interactive(R,rp,html_path)
display(Markdown('**İnteraktif çıktı:** Fareyle düğüm kimliği ve organizmasını inceleyin; yakınlaştırma, kaydırma ve PNG dışa aktarma araçları var. HTML kendi Plotly paketini içerir, internet istemez.'))
display(FileLink(str(html_path)))''')
    md('''## 10 Doğrulama ve öğrenme özeti

Kontroller aşağıda çalışır. Kaynak kapsamı: 153 satırlık tarihsel tablodan 10 seçilmiş ilişki; dört ilaç ve beş protein. Merkezilik yönsüz ve ağırlıksız izdüşümde hesaplandı. Gerçek kenarlara rastgele ağırlık atanmadı.

Kendinizi sınayın: C neden aradalıkta yükseldi? Ağırlık güven skoru olsaydı en kısa yol hesabına doğrudan verilebilir miydi? İki ilaç ortak hedefe sahipse bu bir PPI kenarı mıdır? Bu notebook'un ilgili hücreleri cevapları tablolarla gösterir.''')
    code('''assert len(R)==9 and R.number_of_edges()==10
assert nx.is_bipartite(U) and nx.number_connected_components(U)==2
assert all(R.nodes[a]['kind']=='drug' and R.nodes[b]['kind']=='protein' for a,b in R.edges)
assert all('weight' not in attrs and 'kalite_skoru' not in attrs for _,_,attrs in R.edges(data=True))
assert sum(dict(U.degree()).values())==2*U.number_of_edges()
assert len(nx.ego_graph(R,center,radius=2))==5
assert len(nx.ego_graph(U,center,radius=2))==7
assert not nx.has_path(U,center,'drug:DB01060')
assert metrics(G).set_index('node').loc['C','betweenness'] > 0
result={'nodes':len(R),'edges':R.number_of_edges(),'components':nx.number_connected_components(U),
        'drug_nodes':len(drug_nodes),'protein_nodes':len(protein_nodes),'source_id':sample['source_id'],
        'networkx':nx.__version__,'checks':'passed','scope':'WP01 only'}
(OUT/'graph_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
display(pd.DataFrame([result]))
display(Markdown('**WP01 tamamlandı.** Kaynaklar değiştirilmedi; kullanıcı onayı olmadan WP02 başlatılmaz.'))''')
    nb.cells=cells
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}}
    path=ROOT/'notebooks/WP01_graf_temelleri.ipynb';path.parent.mkdir(exist_ok=True)
    # Aynı süreçte IPython yürütme: ayrı kernel/socket bağımlılığı olmadan gerçek
    # display çıktıları ve PNG'ler hücrelere yazılır. Notebook normal Jupyter'da da çalışır.
    import os, io, matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.display import display, Image
    def capture_figures(*args, **kwargs):
        for number in plt.get_fignums():
            fig=plt.figure(number); buf=io.BytesIO()
            fig.savefig(buf,format='png',dpi=120,bbox_inches='tight')
            display(Image(data=buf.getvalue()))
        plt.close('all')
    plt.show=capture_figures
    os.chdir(ROOT)
    shell=InteractiveShell.instance(); count=0
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        count+=1
        with capture_output(display=True) as cap:
            result=shell.run_cell(cell.source,store_history=False)
        if result.error_before_exec or result.error_in_exec:
            raise RuntimeError(f'Cell {count}: {result.error_before_exec or result.error_in_exec}')
        cell.execution_count=count; cell.outputs=[]
        if cap.stdout:cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=cap.stdout))
        if cap.stderr:cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=cap.stderr))
        for output in cap.outputs:
            cell.outputs.append(nbf.v4.new_output('display_data',data=output.data,metadata=output.metadata))
        print(f'Executed cell {count}',flush=True)
    nb.metadata['execution_method']='IPython InteractiveShell; real display outputs captured in process'
    nbf.write(nb,path)
    print(f'Executed notebook: {path}; {len(cells)} cells')

if __name__=='__main__':main()
