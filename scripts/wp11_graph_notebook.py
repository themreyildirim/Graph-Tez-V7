"""Yalnız gerçek graph-v1 QA tablolarından Türkçe notebook ve bilimsel PNG."""
from pathlib import Path
import base64,io,json,os
from wp09_close_wp10_notebooks import INIT


def execute(parts):
    import nbformat as nb
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    root=Path(__file__).resolve().parents[1];name='WP11_A1P1_graph_explanations.ipynb';target=root/'notebooks'/name
    prior=json.loads((root/'reports/qa/WP11/graph_v1/prior_artifacts_sha256.json').read_text())
    if target.relative_to(root).as_posix() in prior:raise RuntimeError('Accepted file is read-only')
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            stream=io.BytesIO();plt.figure(i).savefig(stream,format='png',dpi=100,bbox_inches='tight');display(Image(data=stream.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(root);shell=InteractiveShell.instance();cells=[];n=0
    for kind,source in parts:
        cell=nb.v4.new_markdown_cell(source) if kind=='md' else nb.v4.new_code_cell(source)
        if kind=='code':
            compile(source,name,'exec');n+=1
            with capture_output(display=True) as cap:r=shell.run_cell(source,store_history=False)
            if r.error_before_exec or r.error_in_exec:raise RuntimeError(r.error_before_exec or r.error_in_exec)
            cell.execution_count=n;cell.outputs=[]
            for label,value in [('stdout',cap.stdout),('stderr',cap.stderr)]:
                if value:cell.outputs.append(nb.v4.new_output('stream',name=label,text=value))
            for output in cap.outputs:
                data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in output.data.items()}
                cell.outputs.append(nb.v4.new_output('display_data',data=data,metadata=output.metadata))
        cells.append(cell)
    result=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'},'language_info':{'name':'python'}})
    nb.validate(result);nb.write(result,target);print(name,n,'executed code cells')


def main():
    parts=[('md','''# WP11 · Kayıtlı A1P1 protein/PPI graf açıklaması

**Uygulama aşaması; WP11 nihai kapanışı değildir.** Kayıtlı WP10 dış modelleri sabittir. Yeni eğitim, optimizer veya sonuçlara göre yöntem araması yoktur. B1 SHAP dosyaları korunmuştur. Buradaki tekil mesaj maskeleme duyarlılığı **SHAP değildir**; katkıların toplamı bütün protein/PPI etkisini vermek zorunda değildir.

Araştırılan büyüklük `Δz=z_orijinal−z_müdahale`dır. Pozitif değer ilgili mesajın kaldırılmasıyla modelin observed-record logitinin düştüğünü; negatif değer arttığını gösterir. Bu klinik risk değişimi veya biyolojik nedensellik değildir. SIDER unknown çiftleri doğrulanmış negatif değildir.

## 1. Sonuç öncesi sözleşme ve sentetik kapı

Birincil işlem orijinal degree/rol sayısı ve availability maskesini sabit tutar. PPI çiftinin iki yönlü mesajı birlikte maskelenir. Ayrı duyarlılıkta gerçek edge/rol ilişkisi silinir, kalan degree/rol sayısı yeniden hesaplanır; son rol ilişkisi silinirse rol maskesi de kapanır. Kimya/atom dalları sabittir. Mevcut olmayan yol NA'dır.'''),('code',INIT+r'''
Q=ROOT/'reports/qa/WP11/graph_v1';F=ROOT/'reports/figures/WP11/graph_v1';F.mkdir(parents=True,exist_ok=True)
policy=json.loads((Q/'policy_v1.json').read_text(encoding='utf-8'))
complete=json.loads((Q/'analysis_complete.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{k:policy[k] for k in ['status','primary','sensitivity','output','examples']}]).T)
print((Q/'synthetic_tests_before_real.txt').read_text(encoding='utf-8'))
'''),('md','''**Yorum:** Gerçek attribution başlamadan 10 analitik test geçti. İlgili zaman/hash kapısı saklandı. Sözleşme test veya katkı sonucuna göre değiştirilmedi. İlk gerçek deneme hash yardımcısına yanlış nesne türü verildiği için katkı üretmeden durdu; hata ve boş dosyalar arşivlendi. Düzeltme yalnız bu teknik denetim çağrısıydı.

### Mean aggregation neden iki farklı sonuç verir?'''),('code',r'''
from wp09_encoder import distinguishing_fixture
from wp11_graph_forward import protein_messages,torch
m,x,pairs=distinguishing_fixture()
with torch.no_grad():
    proof=[]
    for label,ei,mode in [('Orijinal',None,'fixed'),('A–B sabit derece maskesi',0,'fixed'),('A–B silme / yeni derece',0,'delete')]:
        out=protein_messages(m,x,pairs,ei,mode)
        proof.append({'analitik_sentetik_durum':label,'B_degree':float(out['degree'][1]),'B_neighbor_mean':out['mean'][1].tolist(),'B_temsili':out['h'][1].tolist()})
display(pd.DataFrame(proof))
'''),('md','''**Analitik örnek:** A–B–C zincirinde B'ye gelen C mesajı sabit paydada C/2, silme sonrası C/1'dir. B temsilleri sırasıyla [7,4] ve [8,6] olur. Bu elle belirlenmiş küçük test gerçek ilaç sonucu olarak sunulmaz. Gerçek tablolar aşağıdadır.

## 2. Gerçek kapsam: envanter, input ve hesap yolu'''),('code',r'''
coverage=pd.read_csv(Q/'drug_coverage.csv');paths=pd.read_csv(Q/'protein_path_coverage.csv');absent=pd.read_csv(Q/'absent_paths_NA.csv')
scope=coverage.groupby('protocol').agg(envanter=('drug_id','size'),skor=('eligible','sum'),protein_rolü=('role_relations',lambda v:(v>0).sum()),PPI_yolu=('applicable_PPI_pairs',lambda v:(v>0).sum()))
display(scope)
named_scope=pd.read_csv(Q/'all_drug_scope_named.csv')
display(named_scope[named_scope.applicable_PPI_pairs.eq(0)][['context','drug_id','name','eligible','chemistry_available','atom_QC_available','role_relations','PPI_status']])
display(paths.groupby(['protocol','PPI_path_status']).size().rename('rol_bağlantısı').reset_index())
fig,ax=plt.subplots(figsize=(10,4.4));scope.T.plot.bar(ax=ax,color=['#527d91','#ba9470'],rot=0)
ax.set(ylabel='Farklı ilaç sayısı',title='Gerçek kapsam · olmayan yol sıfır etki değildir',ylim=(0,70))
for container in ax.containers:ax.bar_label(container,padding=2)
plt.tight_layout();plt.savefig(F/'01_real_path_coverage.png',dpi=160);plt.show()
display(pd.read_csv(Q/'consistency_checks.csv'))
display(pd.read_csv(Q/'target_scope.csv').query("status=='NA_not_fitted'"))
'''),('md','''**Grafik 1 — Ne öğrendik?** Her protokolde 62 envanter / 61 skor / 60 protein rolü / 51 PPI-yollu ilaç var. Methenamine abstain; Tobramycin protein rolü olmadan mevcut diğer girdileriyle korunur. Train dışında kalan query proteinleri self-only'dir; bunlar için yeni PPI komşuluğu eklenmedi. İnsan PPI kenarları strict aynı-taxID STRING700'dür; diğer organizmaların proteinleri envanterde bulunabilse de E.coli K12 ağı veya context80 eklenmedi.

35.974 orijinal ilaç–PT logiti yeniden üretildi. Yeni açıklama forward'ı kabul edilmiş encoder ile sıfır müdahalede tam eşleşti; önceki OOF sigmoid skorundan en büyük fark yaklaşık 5,96×10⁻⁸ (float32 işlem yolu sınırı). Modeller ve önceki OOF dosyaları değiştirilmedi.

## 3. Local gerçek örnekler: Doxycycline ve Erythromycin

Örnekler alfabetik ilk test kimlikleri ve önceden belirtilen Erythromycin'dir; ilk iki fit edilmiş CUI kullanılır. Ağlar primary outer1 ilk örneği ile Erythromycin'in gerçek heldout folduna aittir. Başarılı tahmin veya büyük attribution seçimi yapılmamıştır.'''),('code',r'''
import networkx as nx
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
examples=pd.read_csv(Q/'examples_frozen.csv');local=pd.read_csv(Q/'example_contributions.csv')
networks=json.loads((Q/'real_networks.json').read_text(encoding='utf-8'))
display(examples)
def real_network(net,filename):
    fig,axs=plt.subplots(1,2,figsize=(15,7.5))
    role_edges=[e for e in net['edges'] if e['kind']=='role'];ppi_edges=[e for e in net['edges'] if e['kind']=='ppi']
    role_nodes=sorted({e['target'] for e in role_edges});styles={'target':'solid','enzyme':'dashed','transporter':'dotted','carrier':'dashdot'}
    # Role panel shows exactly the observed typed drug–protein relations.
    drug=net['drug_id'];G=nx.MultiDiGraph();G.add_node(drug)
    for e in role_edges:G.add_edge(drug,e['target'],key=e['role'])
    pos={drug:np.array([0.,0.])}
    for i,n in enumerate(role_nodes):pos[n]=np.array([np.cos(2*np.pi*i/len(role_nodes)),np.sin(2*np.pi*i/len(role_nodes))])
    vmax=max([abs(e['delta_z']) for e in role_edges]+[1e-7]);norm=Normalize(-vmax,vmax);cmap=plt.get_cmap('RdBu_r')
    nx.draw_networkx_nodes(G,pos,nodelist=role_nodes,node_color='#90b9c7',node_size=850,ax=axs[0])
    nx.draw_networkx_nodes(G,pos,nodelist=[drug],node_color='#d3b38d',node_shape='s',node_size=1800,ax=axs[0])
    for i,e in enumerate(role_edges):nx.draw_networkx_edges(G,pos,edgelist=[(drug,e['target'],e['role'])],edge_color=[cmap(norm(e['delta_z']))],style=styles[e['role']],width=2.5,connectionstyle=f'arc3,rad={.05*(i%3-1)}',arrows=True,arrowsize=14,node_size=1000,ax=axs[0])
    nx.draw_networkx_labels(G,pos,font_size=8,ax=axs[0]);axs[0].set_title('Gerçek dört tip rol ilişkisi · tek ilişki maskesi')
    fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=axs[0],shrink=.45,label='Rol Δz (logit)')
    axs[0].legend(handles=[Line2D([0],[0],color='#555555',linestyle=style,label=r) for r,style in styles.items()],loc='lower left',fontsize=8)
    # PPI panel includes all incident train edges,NOT a highest-effect subgraph.
    H=nx.Graph();H.add_nodes_from(n['id'] for n in net['nodes'])
    H.add_edges_from((e['source'],e['target']) for e in ppi_edges)
    # Deterministic circular display avoids isolated nodes compressing the component.
    # All nodes/edges retained;positions have no biological meaning.
    pos2=nx.circular_layout(sorted(H))
    colors=['#90b9c7' if n in role_nodes else '#d9dde0' for n in H]
    nx.draw_networkx_nodes(H,pos2,node_size=560,node_color=colors,edgecolors=['#c47a3b' if H.degree(n)==0 else '#84949c' for n in H],linewidths=1.3,ax=axs[1])
    v=max([abs(e['delta_z']) for e in ppi_edges]+[1e-7]);norm2=Normalize(-v,v)
    nx.draw_networkx_edges(H,pos2,edgelist=[(e['source'],e['target']) for e in ppi_edges],edge_color=[cmap(norm2(e['delta_z'])) for e in ppi_edges],width=1.6,ax=axs[1])
    nx.draw_networkx_labels(H,pos2,font_size=7.2,ax=axs[1]);axs[1].set_title('İlgili strict insan700 train PPI · iki yön birlikte')
    fig.colorbar(plt.cm.ScalarMappable(norm=norm2,cmap=cmap),ax=axs[1],shrink=.45,label='PPI Δz (logit; ayrı renk aralığı)')
    for ax in axs:ax.set_axis_off();ax.margins(.15)
    fig.suptitle(f"{net['drug_name']} ({drug}) · {net['context']} · {net['class_id']}\nSabit payda;renk Δz; biyolojik nedensellik/klinik risk değildir",fontsize=13)
    fig.text(.03,.015,'Mavi: query rol proteini; gri: train PPI komşusu; turuncu çerçeve: PPI yolu NA. Çembersel konumlar yalnız çizimdir. Panellerin renk aralığı farklıdır.',fontsize=9)
    plt.tight_layout(rect=(0,.04,1,.91));plt.savefig(F/filename,dpi=160);plt.show()
    display(local[(local.context==net['context'])&(local.drug_id==drug)&(local.class_id==net['class_id'])&local.kind.eq('role')][['role','protein_id','mode','original_logit','intervened_logit','delta_z','status']])
real_network(networks[0],'02_Doxycycline_real_network.png')
'''),('md','''**Grafik 2 — Ne öğrendik?** Doxycycline'in gerçek kaynak rol ilişkileri ve yalnız bu query'ye tek PPI katmanında ulaşabilen insan train kenarları gösterilir. Renk kaynak PT logitindeki değişimdir. Sağ panelin renk aralığı daha küçük olabilir; iki panelin renk doygunluğundan biyolojik büyüklük kıyası yapılmaz. İzole/bağlantısız rol proteini sıfır etkili PPI kenarı diye çizilmez.'''),('code',r'''
real_network(networks[1],'03_Erythromycin_real_network.png')
'''),('md','''**Grafik 3 — Ne öğrendik?** Erythromycin kendi primary outer3 modelinde heldout query'dir. 11 rol ilişkisi ayrı türleriyle korunur; bu örnekte çizilen 85 PPI bağı gerçek train kapsamından gelir. Tekil kenarın Δz değeri tüm rolün/proteinin ortak nedensel etkisi değildir. Paylaşılan protein/PPI yolları ve ReLU nedeniyle kenar katkıları toplamı bütün model farkı sayılmaz.

## 4. Düşük katkılar, gerçek sıfırlar ve dört ayrı rol'''),('code',r'''
desc=pd.read_csv(Q/'descriptive_summary.csv');interventions=pd.read_csv(Q/'intervention_summary.csv')
display(desc);display(pd.read_csv(Q/'compressed_table_stream_checks.csv'))
role_stats=interventions[interventions.kind.eq('role')&interventions['mode'].eq('fixed')].groupby(['protocol','role']).agg(ilişki=('status','size'),ortalama_native_PT_mutlak_delta=('mean_abs_delta','mean'),medyan_native_PT_mutlak_delta=('mean_abs_delta','median')).reset_index();display(role_stats)
fig,axs=plt.subplots(1,2,figsize=(12,4.6))
for ax,kind in zip(axs,['role','ppi']):
    for p,color in [('primary','#527d91'),('stress','#ba9470')]:
        d=interventions[interventions.kind.eq(kind)&interventions.protocol.eq(p)&interventions['mode'].eq('fixed')]
        ax.hist(d.mean_abs_delta,bins=35,alpha=.65,label=p,color=color)
    ax.set(title=kind+' · bütün uygulanabilir tekil maskeler',xlabel='O müdahalenin native PT ortalama |Δz|',ylabel='Müdahale sayısı');ax.legend()
plt.tight_layout();plt.savefig(F/'04_real_delta_distributions.png',dpi=160);plt.show()
'''),('md','''**Grafik 4 — Ne öğrendik?** Primary sabit-maskede müdahale başına native-PT mean |Δz| ortalaması rol ilişkilerinde 0,173636, PPI'da 0,006473 logittir; stres değerleri 0,186299 ve 0,007744'tür. Bu, farklı PT sözlüklerini ve farklı müdahale nesnelerini içeren betimsel özettir; ortak global SHAP, klinik etki veya performans ölçüsü değildir.

İki yöntem/protokol birlikte PPI tablolarında 48 tam sıfır ve |Δz|≤10⁻⁷ olan 56 satır korunmuştur. Bunlar **mevcut, uygulanabilir** kenarlardır. NA yollar tabloda ayrı saklanır; bu sıfırlara katılmaz. Tekrar edilen çiftler bağımsız biyolojik gözlem değildir.

## 5. Fiziksel silme neden ayrı bir duyarlılıktır?'''),('code',r'''
paired=pd.read_csv(Q/'mask_vs_deletion_sensitivity.csv');display(paired[['kind','context','drug_id','role','protein_id','protein_a','protein_b','mean_abs_delta_fixed','mean_abs_delta_delete','mean_abs_delta_delete_minus_fixed']].head(20))
fig,axs=plt.subplots(1,2,figsize=(11,4.8))
for ax,kind in zip(axs,['role','ppi']):
    d=paired[paired.kind.eq(kind)];ax.scatter(d.mean_abs_delta_fixed,d.mean_abs_delta_delete,s=10,alpha=.35,color='#527d91')
    high=max(d.mean_abs_delta_fixed.max(),d.mean_abs_delta_delete.max());ax.plot([0,high],[0,high],color='gray',linestyle='--')
    ax.set(title=kind+' · aynı ilaç/ilişki anahtarları',xlabel='Sabit payda · native PT mean |Δz|',ylabel='Silme / yeniden normalizasyon')
plt.tight_layout();plt.savefig(F/'05_mask_vs_deletion.png',dpi=160);plt.show()
'''),('md','''**Grafik 5 — Ne öğrendik?** Aynı ilişki için maske ve fiziksel silme aynı soru değildir. Sabit payda toplam mesajı azaltır; silme kalan komşuların ağırlığını yeniden düzenler. Son rol ilişkisinin silinmesinde availability maskesi de değişir. Gerçek veride müdahale sonrası yeni abstention oluşmadı; bu olasılık analitik testte doğrulandı. İki yöntemin farklılaşması tek başına hesap hatası veya istikrarsız model kanıtı değildir.

## 6. Sayısal kararlılık ve query/cache izolasyonu'''),('code',r'''
stability=pd.read_csv(Q/'stability_checks.csv');display(stability)
display(pd.read_csv(Q/'additional_delta_stability.csv'))
consistency=pd.read_csv(Q/'consistency_checks.csv');display(consistency)
d=stability.groupby('check').max_abs_logit_error.max()
fig,ax=plt.subplots(figsize=(11,4.8));ax.barh(['Protein indeks permütasyonu','PPI maskesi + ters ID sırası','Query tek başına','Query sıra değişimi'],d.reindex(['protein_index_permutation_no_mask','protein_permutation_PPI_mask_reverse_endpoint_ID','query_alone_role_mask','query_order_role_mask']),color='#527d91')
ax.axvline(1e-5,color='#ba9470',linestyle='--',label='Önceden sabitlenen tolerans 10⁻⁵');ax.set(xlabel='En büyük |logit farkı|',title='Gerçek model kararlılığı · sayısal hassasiyet kontrolü');ax.legend(fontsize=8)
plt.tight_layout();plt.savefig(F/'06_numeric_stability.png',dpi=160);plt.show()
'''),('md','''**Grafik 6 — Ne öğrendik?** Bütün tekil müdahaleler tekrar hesaplandı; fark sıfırdı. On bağlamın ilk gerçek ilişki/kenarında query sırası, query tek başına, protein indeks permütasyonu ve ters endpoint ID kontrolleri yapıldı. Grafikteki en büyük fark 1,192×10⁻⁶ logittir. Ek30 kontrolde yalnız kenar sırasını değiştirme ve query'yi tek başına kullanma için doğrudan Δz farkı da ölçüldü; en büyük fark 1,550×10⁻⁶ oldu. Her ikisi dondurulmuş float32 toleransının altındadır. Bu, bootstrap CI veya biyolojik stabilite değildir; yalnız sabit modelde uygulama/sayısal kararlılıktır.

Rol maskesi diğer query skorlarını değiştirmedi. PPI müdahalesi kopya bir cache üretti; orijinal train cache, kaynak graph/query ve model digest'leri değişmedi. Kaynakta olmayan self-only query proteinlerine PPI eklenmedi.

## 7. Testler, veri güvenliği ve durma noktası'''),('code',r'''
print((Q/'real_tests_v1.txt').read_text(encoding='utf-8'))
display(pd.DataFrame([complete]).T.rename(columns={0:'sonuç'}))
print('Ayrıntılı rapor:',ROOT/'reports/WP11_GRAPH_EXPLANATIONS.md')
print('İlk teknik hata arşivi:',Q/'attempt_01_technical_failure')
'''),('md','''**Sınır:** Önce 10 sentetik, ardından 16 gerçek-model testi geçti. 557.574 rol ve 1.883.402 PPI satırı iki yöntemi/protokolü ve kendi fit edilmiş PT başlıklarını içerir. Büyük tablolar gzip CSV olarak akışla yazılıp kontrol edildi. Eksik PT hedefi birleştirilmedi veya doldurulmadı; protein/kenar açıklaması B1 SHAP ile eşdeğer sayılmadı.

Bu gözlemler WP09/WP10'da gösterilememiş PPI performans üstünlüğünü değiştirmez. Protein biyolojisinin genel olarak yararsızlığı da çıkarılamaz. 62/1061/6416,54/8 QC,Methenamine/Tobramycin ve 1.685 kapsam dışı kaynak pozitif sınırı korunur. Yeni eğitim, optimizer veya model araması yapılmadı. **Graf açıklaması uygulaması tamamlandı; WP11 nihai kapanışı yapılmadı. Kullanıcı değerlendirmesi bekleniyor; WP12 başlamadı.**''')]
    execute(parts)


if __name__=='__main__':main()
