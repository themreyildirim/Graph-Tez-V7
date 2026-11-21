"""WP03 çalıştırılmış öğretici notebook; kaynak etiketleri yeniden analiz modülünden gelir."""
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]

def main():
    nb=nbf.v4.new_notebook();cells=[]
    def md(t):cells.append(nbf.v4.new_markdown_cell(t))
    def code(t):cells.append(nbf.v4.new_code_cell(t))
    md('''# WP03 SIDER keşfi ve yan etki eşlemesi

**05.11.2026.** Bu notebook mevcut DrugBank/SIDER kaynakları arasında kimlik izlenebilirliğini araştırır. Her kod hücresinin altında gerçek hesaplanmış tablo/grafik vardır. Yalnız WP03: model, split, negatif örnek veya etiket temelli girdi yok. **Nihai 30 kategori tanımı değiştirilmedi**; PT-CUI pozitifleri keşif tablosudur, alternatif kategori projeksiyonları denetimdir.

Ana soru: 233 J01R dışı J01 adayının kaçında kaynak kimliği düzeyinde doğrulanabilir PT ilişkisi var? 237 geniş küme ayrıca karşılaştırılır. “Doğrulanabilir”, mevcut kaynakların kimlik ve satır izi anlamındadır; klinik nedensellik veya formülasyon eşdeğerliği anlamında değildir.

Tam analiz `python scripts/wp03_sider.py`; bu notebook mevcut WP03 özetlerini okuyarak görselleri yeniden üretir. SIDER satırları yeni etiketlerin kaynağıdır; eski V5 yalnız referans/kategori denetimidir. WP00–WP02 çıktıları değişmez.''')
    code('''from pathlib import Path
import json,sys
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display,Markdown,FileLink
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'AGENTS.md').exists())
sys.path.insert(0,str(ROOT/'scripts'))
from wp03_sider import decode_stitch,encode_stitch
QA=ROOT/'reports/qa/WP03';FIG=ROOT/'reports/figures/WP03';FIG.mkdir(parents=True,exist_ok=True)
def read(name):return pd.read_csv(QA/name,keep_default_na=False)
def js(name):return json.loads((QA/name).read_text(encoding='utf-8'))
quality=js('sider_quality.json');coverage=js('coverage_summary.json');legacy=js('legacy_comparison.json')
m=read('drug_mapping.csv');u=read('drug_pt_positives.csv');evidence=read('pt_evidence.csv')
pop=m[m.conservative].copy();accepted=pop[pop.has_pt].copy()
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
def finish(name,title,ylabel='Kayıt sayısı'):
    ax=plt.gca();ax.set_title(title,loc='left',fontweight='bold');ax.set_ylabel(ylabel)
    plt.tight_layout();plt.savefig(FIG/(name+'.png'),dpi=160);plt.show()
display(pd.DataFrame([js('source_manifest.json')]).drop(columns=['legacy_source']))''')
    md('''## 1 SIDER ve altı alanı öğrenelim

SIDER ilaç etiketlerinden türetilmiş yan etki ilişkileri içerir. Bu dosyada görülme sıklığı veya hastaya özgü risk alanı yok. Sürüm 4.1 tarihsel kaynak beyanı; başlıksız yerel TSV tek başına sürümü doğrulamaz.

Resmi [SIDER format açıklaması](https://sideeffects.embl.de/media/download/README): ilk iki alan flat/stereo kimliği; sonra kaynak etiket CUI'si, LLT/PT türü, eşlenen terimin UMLS CUI'si ve adıdır. LLT daha ayrıntılı terim düzeyi, PT tercih edilen terim düzeyidir. Kaynakta bir LLT için PT de gösterilebilir; iki satır iki bağımsız klinik gözlem değildir.

**UMLS CUI**, kavram kimliğidir; MedDRA'nın sayısal kodu değildir. PT ile LLT'yi aynı ad veya aynı CUI görünse bile tür alanıyla ayırırız.''')
    code('''display(read('sider_examples.csv'))
display(pd.DataFrame({'alan':['flat_id','stereo_id','label_cui','meddra_type','meddra_cui','term'],
 'anlam':['Birleştirilmiş yapı grubu','Stereo yapının kimliği','Etiketteki kaynak kavram','PT / LLT / diğer','Terimin UMLS CUI kimliği','Terim adı']}))
display(read('label_to_pt_crosswalk.csv').query('label_cui != meddra_cui').head(12))''')
    md('''**Yorum:** İlk gerçek örnekte kaynak C0000729, PT karşılığı C0000737 olabilir. Kaynak kavram ile PT hedefini aynı sütun kabul etmek etiketleri yanlış birleştirir. Ham satırlar kaynak izini korur; pozitif ilişkiler ilaç–PT CUI düzeyinde tekilleştirilir.''')
    md('''## 2 STITCH flat stereo ve PubChem CID/SID

[Resmi STITCH README](https://stitch-db.org/download/README) CID0/CIDs ile stereo, CID1/CIDm ile birleştirilmiş flat biçimi ayırır. Tür işareti çıkarıldıktan sonraki suffix PubChem CID'dir. STITCH tuz biçimlerini de birleştirebildiğinden kimlik eşitliği ayrı ürünlere klinik aktarım izni değildir.

**CID** Compound kimliği, **SID** Substance kimliğidir. SID'yi CID gibi sorgulamıyoruz. Flat suffix, stereo suffix ile aynı olmak zorunda değildir. Örneğin ilk satırdaki flat 85, stereo 10917'dir; 100000085 diye CID üretmek hatalıdır. Ayrıntılı kanıt `identity_semantics.md` içinde.''')
    code('''pairs=read('stitch_pair_map.csv')
display(pairs.head(12))
display(pd.DataFrame([{'girdi':'CID100000085','tür':'flat','doğru suffix CID':decode_stitch('CID100000085','flat'),'yanlış kör CID':'100000085'},
 {'girdi':'CID000010917','tür':'stereo','doğru suffix CID':decode_stitch('CID000010917','stereo'),'yanlış kör CID':'10917 (burada rastlantısal aynı)'}]))
display(pd.DataFrame([{'çok stereo içeren flat grup':quality['flat_with_multiple_stereo'],
                       'çok flat içeren stereo':quality['stereo_with_multiple_flat'],
                       'geçersiz STITCH çifti':len(quality['invalid_stitch_pairs'])}]))
display(pop[['id','name','cid','sid','flat_ids','stereo_ids','status']].head(10))''')
    md('''**Kesin politika:** DrugBank XML Compound CID ↔ köprü CID uyumu, ardından türü kontrol edilmiş tam stereo CID eşitliği. Flat-only, çok sahipli CID veya çelişki “kesin” sayılmaz. Aynı flat gruptaki başka stereo yapıya etiket taşımak ek yapı/kimlik doğrulaması gerektirir. İsim son ekiyle veya SID sayısıyla eşleme yapılmaz.''')
    md('''## 3 SIDER genel kalite tablosu

Satır sayısı, ilaç kimliği sayısı ve tekil ilişki sayısı farklı niceliklerdir. Tam satır tekrarı olmasa bile aynı stereo–PT CUI ilişkisi farklı kaynak kavramlarla yeniden görünebilir. Boş türü PT saymayız.''')
    code('''display(pd.DataFrame([quality]).drop(columns=['missing','type_counts','invalid_stitch_pairs']))
display(pd.DataFrame({'alan':list(quality['missing']),'boş':list(quality['missing'].values()),'payda':quality['rows']}))
types=pd.Series(quality['type_counts']).rename(index={'':'Boş / diğer'})
ax=types.plot.bar(figsize=(8,4),rot=0,color=['#237b8d','#83bd99','#c08235']);ax.bar_label(ax.containers[0])
finish('01_pt_llt','SIDER · PT, LLT ve boş tür satırları')
dup=evidence[evidence.duplicated(['id','meddra_cui'],keep=False)]
display(dup.sort_values(['id','meddra_cui']).head(12))
display(pd.DataFrame({'anahtar':['Tüm satır','stereo + tür + CUI'],
 'tekrar fazlası':[quality['duplicate_full_rows_excess'],quality['duplicate_stereo_type_cui_excess']]}))''')
    md('''**Yorum:** Bu tekrarlar yeni yan etki kanıtı olarak sayılmaz. Kaynak satırı `pt_evidence.csv` içinde korunur; `drug_pt_positives.csv` ilaç–CUI çiftini tekilleştirir. Yerel dosyadaki PT kapsam sayısı yayınlardaki tüm SIDER ADR sayılarıyla aynı tanımda olmayabilir; burada sayılar bu dosyadan hesaplanır.''')
    md('''## 4 DrugBank adaylarında eşleme başarısı ve belirsiz vaka

237 ve 233 listeleri WP02'den okunur. Adaylara yeni CID üretilmez. Tuz/ana ilaç ilişkisi kimlik provenansında tutulur; tuz CID'si veya formülasyon eşdeğerliği mevcut değilse otomatik etiket aktarımı yapılmaz.''')
    code('''display(pd.DataFrame(coverage).T)
display(pop[pop.status.str.startswith('ambiguous')][['id','name','cid','flat_ids','stereo_ids','status']])
display(read('salt_mapping_review.csv').head(10))
counts=pop.status.value_counts();display(counts.rename('ilaç sayısı').reset_index())
counts.plot.barh(figsize=(10,4),color='#237b8d');finish('02_mapping_status','233 aday · kimlik eşleme durumları','Durum')
display(read('unmatched_or_ambiguous.csv')[['id','name','conservative','cid','status']].head(20))''')
    md('''**Telavancin örneği:** DrugBank CID 3081362 için flat CID103081362 görülüyor; kaynak stereo CID045267081, yani CID 45267081. Bu iki CID eşit değil. İlaç adını veya flat grubu gerekçe göstererek kesin kabul etmedik. “CID SIDER'da yok” da “ilaçta yan etki yok” anlamına gelmez; mevcut kimlikle eşleşme bulunmadı demektir.''')
    code('''fig,ax=plt.subplots(figsize=(11,4));ax.axis('off')
values=[('WP02 J01R dışı',coverage['conservative']['candidates']),('Compound CID var',coverage['conservative']['cid_available']),('Kesin stereo + PT',coverage['conservative']['with_pt'])]
for x,(label,n) in zip([.12,.5,.88],values):ax.text(x,.6,f'{label}\\n{n}',ha='center',va='center',bbox=dict(boxstyle='round,pad=.8',fc='#e6f1f3',ec='#237b8d'),transform=ax.transAxes)
for a,b in [(.25,.38),(.63,.76)]:ax.annotate('',xy=(b,.6),xytext=(a,.6),xycoords='axes fraction',arrowprops=dict(arrowstyle='->'))
ax.text(.5,.12,'CID yok: 66 · CID eşleşmedi: 104 · flat-only belirsiz: 1 · SID bu yola girmez',ha='center',transform=ax.transAxes)
finish('03_identity_flow','Kimlik eşleme akışı · sayılar aynı filtre zincirine aittir')''')
    md('''**Akış yorumu:** Kaynak-J01 kapsamı ve etiketlenebilir ilaç kümesi aynı değildir. Doğrudan stereo eşleşmesi dışındaki yollar ayrı inceleme listesinde kalır; sayıyı artırmak için zorlanmaz.''')
    md('''## 5 Gerçek PT kapsamı ve eksik modaliteler

Aşağıdaki “kimya mevcut” bayrağı eski feature tablosunda beş fizikokimyasal özelliğin bulunmasıdır; yeni SMILES/molekül grafı hazır demek değildir. “Protein mevcut” WP02 XML kimlik kontrolüdür; protein özellikleri henüz üretilmedi. Hiçbir bayrak etiketlerden türetilmiş model girdisi değildir; yalnız QA kapsam göstergesidir.''')
    code('''display(accepted[['id','name','pt_count','chemistry_available','protein_available','old38']])
display(read('missing_modalities.csv')[['id','name','chemistry_available','protein_available','pt_count']])
accepted.pt_count.plot.hist(bins=16,figsize=(9,4),color='#237b8d');plt.xlabel('Benzersiz PT CUI / ilaç')
finish('04_pt_per_drug','Kesin 62 ilaçta PT ilişki kapsamı','İlaç sayısı')
display(u[u.conservative].head(12))''')
    md('''**Yorum:** PT sayısı raporlama ve kaynak kapsamını gösterir; yan etki risk skoru veya klinik prevalans değildir. Yeni ilaçların kimyası eksik diye PT pozitifleri atılmaz. SIDER kaydı yokluğu negatif sınıf değildir.''')
    md('''## 6 Üç kaynağın kesişimleri — UpSet görünümü

233 adayın her biri, PT / mevcut kimya / XML protein bayraklarının tek bir kombinasyonuna girer. Çubuklar **ayrık** kesişimlerdir; toplamları 233 eder. PT dışındaki kaynak kapsamı, eksik etiketi gerçek negatif yapmaz.''')
    code('''cols=['has_pt','chemistry_available','protein_available']
intersections=pop.groupby(cols).size().rename('count').reset_index().sort_values('count',ascending=False)
display(intersections);intersections.to_csv(QA/'modality_intersections.csv',index=False,encoding='utf-8-sig')
fig,(ax,mat)=plt.subplots(2,1,figsize=(11,6),gridspec_kw={'height_ratios':[3,1.3]},sharex=True)
x=list(range(len(intersections)));bars=ax.bar(x,intersections['count'],color='#237b8d');ax.bar_label(bars,padding=3);ax.set_ylabel('İlaç sayısı')
for i,(_,r) in enumerate(intersections.iterrows()):
    active=[j for j,k in enumerate(cols) if r[k]]
    mat.plot([i]*3,list(range(3)),'.',color='#d7dbdf',markersize=13)
    if active:mat.plot([i]*len(active),active,'o-',color='#237b8d')
mat.set_yticks(range(3),['PT','Mevcut kimya','XML protein']);mat.set_xticks(x,[str(i+1) for i in x]);mat.set_xlabel('Ayrık kesişim');mat.invert_yaxis()
ax.set_title('233 aday · PT/kimya/protein ayrık kesişimleri',loc='left');plt.tight_layout();plt.savefig(FIG/'05_upset.png',dpi=160);plt.show()
display(pd.DataFrame({'gösterge':['Eski karışık havuz','Eski havuzun J01R dışı kısmı','Yeni kesin PT kapsamı','Eski 30 kategori denetimi'],
 'ilaç':[38,int(accepted.old38.sum()),len(accepted),coverage['conservative']['with_historical_category_audit']]}))''')
    md('''## 7 Eski 38 ile doğru karşılaştırma

Eski 38'in 12'si muhafazakâr J01 kapsamı dışında kaldı (WP02). Yeni 62'nin 26'sı aynı ID'ler, 36'sı eski 38 dışında. Dolayısıyla “36 yeni kimlik” ile “62−38=24 net sayı farkı” farklı karşılaştırmalardır. Ayrıca herhangi PT bulunması ile eski seçilmiş 30 kategoride ilişki bulunması ayrı koşullardır.''')
    code('''display(read('new_drugs_vs_old38.csv')[['id','name','pt_count','chemistry_available','protein_available']])
pd.Series({'Eski 38 (karışık)':38,'Eski aynı kapsam':26,'Yeni kesin PT':62,'Eski 38 dışında yeni ID':36,'Eski 30 kategoride':61}).plot.barh(figsize=(10,4),color='#237b8d')
finish('06_old_new','Eski ve yeni kapsam · tanımları farklı sayılar','Küme')
display(pd.DataFrame([legacy]))''')
    md('''**Yorum:** Sulfanilamide kaynak PT ilişkisi taşır ama tarihsel 30 kategori projeksiyonunda ilişki yoktur. Bu ilaç “yan etkisiz” değildir. Nihai kategori seçimini değiştirmeden, tüm-PT keşif kapsamı ile eski kategori denetimi ayrı tutulur.''')
    md('''## 8 Eski 30 kategori nasıl oluşmuş?

Eski kodun `HEDEF_35_SE` sözlüğü AST ile yalnız veri olarak okundu, çalıştırılmadı: 40 İngilizce ad → 33 Türkçe değer. Gerçek V5 dosyası 30 kategori taşıyor ve kodda olmayan Pseudomembranous colitis terimini içeriyor. Bu bir revizyon farkıdır; eski kodun çıktıyı bire bir ürettiği varsayılmaz.

Eski kategori sözlüğü yalnız denetim amacıyla kaynak PT-CUI'lere yansıtıldı; nihai hedef etiketi onayı değildir. Çok PT'nin aynı kategoriye gitmesi ve etiket-CUI tekrarları ayrı azaltım adımlarıdır.''')
    code('''audit=js('category_audit.json');display(pd.DataFrame(audit))
display(pd.DataFrame([x for x in audit if x['n_cui']>1]))
hist=read('historical_category_projection_audit.csv');h=hist[hist.conservative]
display(h[h.duplicated(['id','category'],keep=False)].sort_values(['id','category']).head(12)[['id','name','meddra_cui','term','category','source_line']])
display(pd.DataFrame({'strateji':['Tüm PT CUI (keşif)','Gerçek V5 30 kategori sözlüğü (denetim)','MASTER kod sözlüğü (denetim)'],
 'ilaç':[62,coverage['conservative']['with_historical_category_audit'],coverage['conservative']['with_code_category_audit']],
 'tekil ilişki':[coverage['conservative']['positive_drug_pt_pairs'],coverage['conservative']['historical_category_pairs_audit'],coverage['conservative']['code_category_pairs_audit']]}))
pd.Series({'Eski 38 PT-CUI':legacy['old38_unique_cui'],'Eski 38 kategori çifti':legacy['old38_unique_pairs']}).plot.bar(figsize=(8,4),rot=0,color=['#237b8d','#c08235'])
finish('07_category_collapse','Eski 38 · kavramdan kategoriye indirgeme')''')
    md('''**Bilimsel yorum:** Loss of consciousness ve Syncope ayrı CUI'lerle aynı “Bilinç kaybı” kategorisine, iki kolit PT'si “C.diff ishal” kategorisine gidiyor. Aynı kategori adı altında farklı kavramlar birleşiyor; bu klinik eşanlamlılığı kanıtlamaz. Genel Colitis → antibiyotikle ilişkili kolit ve kodda Renal impairment → nefrotoksisite gibi çeviriler kapsamı olduğundan özgül gösterebilir. Ayrı “metalik tat/tat değişikliği” veya deri kabarcığı gibi istenen kavramlar otomatik olarak 30 kategoride temsil edilmiş sayılmaz. Harici ontoloji/hiyerarşi eklenmedi; bu yüzden kategori stratejisi yalnız mevcut CUI/adlar düzeyinde denetlendi.''')
    md('''## 9 Küçük etkileşimli ilaç–PT ağı

Görünürlük için kesin kümeden ilk dört ilacın ortak/çok görülen sekiz PT'si seçilir. Bu bir eğitim grafı veya tüm yan etki ağı değildir. Ok, kaynak pozitif ilişkisi anlamındadır; risk olasılığı göstermez.''')
    code('''import plotly.graph_objects as go
ids=accepted.sort_values('id').head(4).id.tolist();small=u[u.id.isin(ids)]
concepts=small.groupby('meddra_cui').id.nunique().sort_values(ascending=False).head(8).index.tolist();small=small[small.meddra_cui.isin(concepts)]
nodes=ids+concepts;positions={n:(x,1-i/max(len(ns)-1,1)) for x,ns in [(0,ids),(1,concepts)] for i,n in enumerate(ns)}
names=dict(zip(accepted.id,accepted.name));names.update(dict(zip(u.meddra_cui,u.term)))
xs=[];ys=[]
for row in small.itertuples():
    a,b=positions[row.id],positions[row.meddra_cui];xs.extend([a[0],b[0],None]);ys.extend([a[1],b[1],None])
fig=go.Figure([go.Scatter(x=xs,y=ys,mode='lines',hoverinfo='skip',line=dict(color='#9aabb5',width=1)),
go.Scatter(x=[positions[n][0] for n in nodes],y=[positions[n][1] for n in nodes],mode='markers+text',text=[names[n] for n in nodes],
 textposition='top center',hovertext=[n+'<br>'+names[n] for n in nodes],hoverinfo='text',marker=dict(size=20,color=['#237b8d']*len(ids)+['#c08235']*len(concepts)))])
fig.update_layout(title='Kesin eşleşmiş dört ilaç → sekiz PT · küçük pozitif ilişki örneği',showlegend=False,height=700,
 xaxis=dict(visible=False,range=[-.4,1.5]),yaxis=dict(visible=False,range=[-.2,1.2]),plot_bgcolor='white',margin=dict(l=100,r=100,t=80,b=60))
html=FIG/'drug_pt_network.html';fig.write_html(html,include_plotlyjs=True);display(small);display(FileLink(str(html)))''')
    md('''## 10 Testler ve durma kapısı

Kimlik türü, flat/stereo karşı örnekleri, SID'nin kullanılmaması, çok sahipli CID, PT tekilliği ve eski 590 çiftin kaynak üzerinden yeniden doğrulanması otomatik testlerle kontrol edilir. Veri yokluğu negatif yapılmaz. Tüm ilişkiler kaynak satır numarasıyla izlenebilir; birden fazla kaynak satırı tek pozitif çifte gidebilir.''')
    code('''assert len(pop)==233 and len(accepted)==62
assert not u.duplicated(['id','meddra_cui']).any()
assert coverage['conservative']['new_vs_old38']+coverage['conservative']['retained_old38']==62
assert legacy['old38_unique_pairs']==590 and legacy['reference_all_legacy_keys_in_raw_sider']==865
assert decode_stitch('CID100000085','flat')!='100000085'
assert js('source_manifest.json')['metadata_unchanged']
display(pd.DataFrame([{'paket':'WP03','durum':'analiz tamamlandı','kesin muhafazakâr PT ilaç':62,'nihai hedef etiketi değişikliği':'yok','sonraki kapı':'kullanıcı onayı'}]))''')
    nb.cells=cells;nb.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'IPython InteractiveShell with captured real outputs'}
    import os,io,matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            b=io.BytesIO();plt.figure(i).savefig(b,format='png',dpi=110,bbox_inches='tight');display(Image(data=b.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for cell in cells:
        if cell.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:r=shell.run_cell(cell.source,store_history=False)
        if r.error_in_exec or r.error_before_exec:raise RuntimeError(f'Cell {n}: {r.error_in_exec or r.error_before_exec}')
        cell.execution_count=n;cell.outputs=[]
        if cap.stdout:cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=cap.stdout))
        if cap.stderr:cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=cap.stderr))
        for o in cap.outputs:cell.outputs.append(nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata))
        print(f'Executed cell {n}',flush=True)
    path=ROOT/'notebooks/WP03_sider_exploration.ipynb';nbf.write(nb,path);print(path)

if __name__=='__main__':main()
