"""Mevcut WP02 QC sonuçlarından çalıştırılmış öğretici notebook üretir; XML'i tekrar taramaz."""
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]

def main():
    nb=nbf.v4.new_notebook();c=[]
    def md(t):c.append(nbf.v4.new_markdown_cell(t))
    def code(t):c.append(nbf.v4.new_code_cell(t))
    md('''# WP02 DrugBank keşfi ve ilaç kapsamı

**05.11.2026.** DrugBank bu tezde ilaç kimlikleri, ATC kapsamı, tuz–ana ilaç ilişkileri ve kaynakta bildirilen hedef bağlantılarının temelidir. SIDER yan etki etiketleri, PubChem ise kimyasal özellikler için ayrı kaynaklardır. Bir dosyada bulunan her ilaç bu tezin antibakteriyel kohortuna girmez.

Bu notebook **tam XML taramasından hesaplanmış küçük QC tablolarını** okur; her açılışta 1,9 GB dosyayı tekrar taramaz. Tam tarama `python scripts/wp02_drugbank.py` ile salt okunur yapılır. `iterparse`, sadece kökün doğrudan drug çocuklarını işler ve her biten kaydı remove/clear ile bırakır. İnceleme tabloları özellik veya eğitim tensörü değildir. Önceki WP00/WP01 çıktıları yeniden üretilmedi.

Kod hücrelerinin altındaki tablolar/grafikler gerçek yürütme çıktısıdır. Notebook yeniden çalıştırılabilir; internet gerekmez. Drive'dan yalnız izinli eski tablolar bellekte okunmuş, karşılaştırma için üyelik/kimlik özetleri saklanmıştır.''')
    code('''from pathlib import Path
import json,sys
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display,Markdown,FileLink
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'AGENTS.md').exists())
QA=ROOT/'reports/qa/WP02'; FIG=ROOT/'reports/figures/WP02';FIG.mkdir(parents=True,exist_ok=True)
records=json.loads((QA/'drug_registry.json').read_text(encoding='utf-8'))
summary=json.loads((QA/'summary.json').read_text(encoding='utf-8'))
manifest=json.loads((QA/'parse_manifest.json').read_text(encoding='utf-8'))
legacy=pd.read_csv(QA/'legacy_coverage.csv',keep_default_na=False)
mapping=pd.read_csv(QA/'old209_mapping.csv',keep_default_na=False)
registry=pd.DataFrame([{k:v for k,v in r.items() if k not in ['targets','salts']} for r in records])
j01=registry[registry.j01].copy()
conservative=registry[registry.j01_noncombination].copy()
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
def finish(name,title,ylabel='Kayıt sayısı'):
    ax=plt.gca();ax.set_title(title,loc='left',fontweight='bold');ax.set_ylabel(ylabel)
    plt.tight_layout();plt.savefig(FIG/(name+'.png'),dpi=160);plt.show()
display(pd.DataFrame([manifest]).drop(columns=['root_attributes']))
display(pd.DataFrame([manifest['root_attributes']]))''')
    md('''## 1 XML ve iç içe kayıtlar

`drugbank → drug` bir ana kayıttır. `drug → salts → salt` bir tuz varyantı, `drug → drug-interactions → drug` ise başka bir ilaca referanstır. İç içe tüm drug etiketlerini kayıt saymak veya salt ID'sini ana ID'nin üzerine yazmak yanlış sayım oluşturur. Ad, ATC ve kimlikler yalnız uygun **doğrudan çocuk yollarından** alınır.

Birincil kimlik `drug/drugbank-id[@primary="true"]`, ikincil kimlikler aynı düzeyde diğer drugbank-id alanlarıdır. İkincil kimlik yeni etkin madde değildir; eski ID'den güncel ana kayda bağlantıdır. Bir ID birden fazla ebeveyne giderse `ambiguous` tutulur.''')
    code('''display(registry[['record_index','id','primary_count','name','type','secondary_ids','atc']].head(5))
display(pd.DataFrame([{'ana kayıt':summary['records'],'ikincil kimlik görülmesi':summary['secondary_id_occurrences'],
                       'tuz ilişkisi':summary['salt_occurrences'],'geçersiz ana kimlik':summary['invalid_primary_records'],
                       'tekrarlanan ana kimlik':len(summary['duplicate_primary_ids'])}]))
issues=json.loads((QA/'identity_issues.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'çok ebeveynli kimlik':issues['global_ambiguous_id_count'],
                       'eski üyelerde çözülemeyen':len(issues['legacy_members_unresolved']),
                       'eski üyelerde belirsiz':len(issues['legacy_members_ambiguous']),
                       'ATC bulunmayan kaynak kaydı':issues['all_records_missing_atc']}]))
ax=registry.type.value_counts().plot.bar(figsize=(8,4),rot=0,color='#237b8d');ax.bar_label(ax.containers[0],padding=4)
finish('01_record_types','DrugBank · yalnız üst düzey ana kayıt tipleri')''')
    md('''**Ne öğrendik?** Kayıt tipi dağılımı bütün DrugBank kapsamını gösterir. Salt sayıları bu çubuğa yeni ana ilaç olarak eklenmez. Bu kaynak kayıtları, benzersiz kimyasal temel etkin madde olduğu tamamen doğrulanmış moleküllerle bire bir eşit varsayılmaz.''')
    md('''## 2 ATC sınıflandırması ve J01

ATC hiyerarşisi ilacın kullanım sınıflarını kodlar. Örnek J01CA04: J ana grubu, J01 sistemik antibakteriyel sınıfı, sonraki harf/rakamlar daha dar alt grupları belirtir. Bir ilaç birden fazla ATC taşıyabilir. Bu tezde **kaynak-ATC ile doğrulanmış J01 adaylığı**, ana kayda doğrudan bağlı biçimi geçerli `J01[A-Z]{2}[0-9]{2}` kodunun bulunmasıdır. Ruhsat, tek bileşen, tuz/ingredient eşdeğerliği ve SIDER kapsamının tamamının doğrulandığı anlamına gelmez.

J02/D01 antifungal, J04 antimikobakteriyel, D06 topikal antibakteriyel gibi kodlar J01 olmadan ana kohorta eklenmez. ATC'si olmayan kayıt için isim son ekinden sınıf tahmini yapılmaz.''')
    code('''display(j01[['id','name','atc','groups','secondary_ids']].head(12))
display(j01[j01.atc.map(len)>1][['id','name','atc']].head(10))
from collections import Counter
atc_first=Counter(letter for codes in registry.atc for letter in {a[0] for a in codes})
pd.Series(atc_first).sort_values(ascending=False).plot.bar(figsize=(10,4),rot=0,color='#237b8d')
finish('02_atc_classes','ATC ana sınıfları · her sınıfta benzersiz ana kayıt')
display(pd.DataFrame({'durum':['J01 adayı','J01 dışı / ATC yok','J01 içinde birden fazla ATC'],
                     'sayı':[len(j01),len(registry)-len(j01),summary['multi_atc_j01']]}))
pd.Series({'J01 ana kayıt':len(j01),'Hedef kaydı var':summary['j01_with_target_entry'],
           'Protein kimliği var':summary['j01_with_protein'],'XML CID var':summary['j01_with_cid']}).plot.bar(figsize=(10,4),rot=12,color='#237b8d')
finish('03_j01_scope','J01 kapsamı · aynı aday kümesinin farklı bilgi alanları')''')
    md('''**Yorum:** ATC ana sınıf çubuklarının toplamı ilaç sayısını aşabilir; bir kayıt birkaç sınıfta olabilir. J01 kapsam grafiğinde hedef, protein ve CID alt kümeleri birbirini içermek zorunda değildir; çubuklar eğitim sayısı değildir. Eksik ATC, J01 dışı olmanın kanıtı olarak değil bu kaynakta J01 doğrulanamaması olarak yorumlanır.''')
    code('''display(registry[registry.j01_combination_only][['id','name','atc','groups']])
display(pd.DataFrame({'tanım':['Herhangi J01','J01R dışında J01','Yalnız J01R'],
                     'ana kayıt':[summary['j01'],summary['j01_noncombination'],summary['j01_combination_only']]}))
evidence=json.loads((QA/'schema_evidence.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'ID':e['id'],'ATC XML hiyerarşisi':e['atc_hierarchy']} for e in evidence['examples'] if e['id']=='DB00196']))
display(Markdown('**Önemli kapsam ayrımı:** Fluconazole, Nitazoxanide, Nystatin ve Secnidazole yalnız J01R kombinasyon koduyla geniş kümeye giriyor. XML hiyerarşisinde J01R “Combinations of antibacterials” olarak yazıyor. Bu dört kayıt ayrı inceleme listesinde; J01R dışında kod taşıyan **233** kayıt muhafazakâr aday kümesidir. Bu bir klinik kohort sonlandırma kararı değil, açıkça tanımlanmış analiz ayrımıdır.'))''')
    md('''## 3 DBSALT ile ana ilaç ilişkisi ve eski 209 kayıt

DBSALT bir tuz/varyant kaydının kimliğidir. XML'de belirli ana ilacın salts bloğu altında bulunması ebeveyn bağlantısının doğrudan kanıtıdır; tuzun farmakolojik ve kimyasal açıdan ana ilaçla tümüyle eşdeğer olduğunu tek başına kanıtlamaz. Ham tuz kimlikleri korunur, yalnız **tek ebeveynli** ilişkiler sayısal eşlemede kullanılır. Birincil/ikincil/tuz kimliklerinin çakıştığı durumlar otomatik birleştirilmez.''')
    code('''display(mapping.head(12))
display(mapping.groupby(['id_kind','status']).size().rename('satır').reset_index())
display(mapping[mapping.id_kind.eq('DBSALT')][['id','old_name','parent_id','parent_name','parent_j01','parent_atc']].head(12))
pd.Series({'Eski satır':len(mapping),'Tekil ana kayıt':summary['old209_unique_parents'],
           'J01 ana kayıt':summary['old209_unique_j01_parents']}).plot.bar(figsize=(9,4),rot=0,color=['#c08235','#237b8d','#83bd99'])
finish('04_salt_parent','209 satır → ebeveyn kimlikleri → kaynak J01 kapsamı')
display(mapping[(mapping.status!='resolved') | ~mapping.parent_j01.isin([True,'True'])].head(30))''')
    md('''**Yorum:** İlk çubuk satır, ikinci/üçüncü çubuk ana kayıt sayısıdır; paydaları farklıdır. Aynı ebeveyne giden farklı tuzlar yeni bağımsız ilaç olarak eklenmez. Eski ATC ile ebeveynin gerçek ATC'si uyuşmuyorsa kaynak ana kaydın kodu gösterilir; tarihsel etiket düzeltilmiş gibi sessizce değiştirilmez.''')
    code('''display(pd.DataFrame({'ölçüm':['Eski 209 → tekil ebeveyn','Ebeveynler içinde J01R dışı','237 kaynak adayında eski listede olmayan'],
                     'sayı':[summary['old209_unique_parents'],summary['old209_noncombination_parents'],summary['j01']-summary['old209_unique_j01_parents']]}))
display(j01[~j01.in_old209_parent][['id','name','atc']])
display(Markdown('**Verinin düzelttiği beklenti:** Bu özel 209 satır 209 farklı ana kayda gidiyor: 84 primary + 125 farklı ebeveyne giden DBSALT. Tuzları çözmek burada sayıyı azaltmadı. 125 eski tuz kimliğinin tamamı ebeveynin salts listesindeki son tuz ID’siyle eşleşiyor; bu, eski kodun aynı kayıtta ID üzerine yazma riskine uyumlu, fakat eksik 28 ilacın tek nedenini kanıtlamaz.'))''')
    md('''## 4 İlaç–hedef ilişkisi ve amino-acid-sequence

`targets/target` bir hedef kaydıdır; her hedef protein olmayabilir. `polypeptide/@id` ve UniProtKB dış kimliği aynı ise kimlik tutarlı olarak işaretlenir; farklıysa çatışma raporlanır. Polipeptit bulunmayan hedefe protein uydurulmaz. Gen adı protein anahtarı değildir; organizma bilgisi korunur.

WP00 bulgusu: polipeptit dizisi `amino-acid-sequence` alanında FASTA biçiminde olabilir; eski kodun `sequence` alanını araması aynı şey değildir. Burada yalnız alan varlığı/ham uzunluk incelenir. FASTA temizleme, AAC/DC ve protein özellik üretimi WP05'e aittir.''')
    code('''priority=['Erythromycin','Azithromycin','Doxycycline','Vancomycin','Linezolid']
focus=[r for r in records if r['name'] in priority]
target_examples=[{'drug_id':r['id'],'drug':r['name'],**t} for r in focus for t in r['targets']]
display(pd.DataFrame(target_examples))
display(legacy[legacy.name.isin(priority)][['id','name','chemistry','adr','legacy_targets','j01','xml_target_entries','xml_proteins','xml_aa_proteins','chemistry_only_candidate']])
j01.protein_ids.map(len).value_counts().sort_index().plot.bar(figsize=(11,4),rot=0,color='#237b8d')
finish('05_proteins_per_drug','J01 ilaç başına tutarlı XML protein kimliği','İlaç sayısı')
display(pd.DataFrame({'alan':['target kaydı','polipeptit / UniProt','dizi alanı'],
                     'anlam':['hedef ilişkisi var; protein olmayabilir','protein kimliği mevcut; dış doğrulama değil','FASTA/metadata; feature değil']}))''')
    md('''**Yorum:** Eski hedef tablosunda bulunmamak, XML'de hedef bulunmamasıyla aynı değildir. XML'de de protein olmayan hedefler veya eksik kimlikler görülebilir. Histograma sıfır proteinli adaylar da dahildir. XML hedefinin varlığı, o ilacın yan etki etiketli veya GNN eğitimi için hazır olduğu anlamına gelmez.''')
    md('''## 5 PubChem CID ve SID

CID Compound kaydı, SID Substance kaydı kimliğidir; aynı sayı uzayı değildir. XML'deki kaynak etiketi saklanır. SID doğrudan CID sütununa taşınmaz. WP00'daki DrugBank–PubChem köprüsü ayrıca doğrulanır; bu notebook yeni API çağrısı yapmaz.''')
    code('''display(registry[registry.name.isin(priority+['Lepirudin'])][['id','name','pubchem_cid','pubchem_sid']])
display(legacy[legacy.name.isin(priority)][['id','name','cid','sid']])
display(pd.DataFrame([{'kaynak':'XML','CID olan J01':summary['j01_with_cid'],'J01 toplam':len(j01)}]))''')
    md('''**Yorum:** Tablo SID/CID ayrımını gerçek kayıtlarda gösterir. XML CID alanı boş olsa bile köprüde CID bulunabilir. Kimyasal yapı ve tuz eşdeğerliği doğrulanmadan “aynı molekül” sonucu çıkarılmaz.''')
    md('''## 6 Eski 38 ilaç ve yeni kaynak kapsamı

Eski 56 kimyalı, 53 ADR'li, 41 hedef bağlı ve 38 ortak ilaç üyelikleri izinli Drive tablolarından yeniden hesaplandı. XML J01 sınıfı bunlarla karşılaştırılır; yeni SIDER eşlemesi burada yapılmaz. Aşağıdaki tabloda eski ADR alanı yalnız **eski çıktıda kayıt var** demektir; eski tabloda olmayan ilaç için SIDER'da yok sonucu vermez.''')
    code('''display(legacy)
display(legacy[legacy.old38.eq(True) & legacy.j01.isin([False,'False'])][['id','name','atc']])
display(legacy[legacy.old38.eq(True) & legacy.j01_noncombination.eq(True)][['id','name','atc']])
display(legacy[legacy.chemistry_only_candidate.eq(True)][['id','name','j01','xml_target_entries','xml_proteins','chemistry_only_candidate']])
pd.Series({'Eski 38':int(legacy.old38.sum()),'38 içinde XML J01':summary['old38_j01'],
           'Tüm XML J01':summary['j01'],'38 dışında XML J01':summary['j01_outside_old38'],
           '38 dışında J01 + protein':summary['j01_outside_old38_with_protein']}).plot.barh(figsize=(11,5),color='#237b8d')
finish('06_old_new_scope','Eski öğrenme havuzu ile XML aday kapsamı','Küme')
display(Markdown('**Dikkat:** Bu çubuklar iç içe veya farklı kümelerdir; toplanmaz. Yeni adaylar ADR etiketli olarak sayılmamıştır.'))''')
    code('''display(pd.read_csv(QA/'cohort_funnel.csv'))
display(legacy[legacy.j01_noncombination.eq(True) & legacy.adr.eq(True) & (legacy.xml_proteins.astype(int)>0) & ~legacy.old38.eq(True)][['id','name','xml_proteins']])
bridge=json.loads((QA/'bridge_qc.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'köprü satırı':bridge['bridge_total'],'J01 kimliği köprüde eksik':bridge['missing_bridge'],
                      'J01 köprü CID var':bridge['with_bridge_cid'],'dolu CID uyuşmazlığı':len(bridge['conflicting_nonempty_cid'])}]))
display(Markdown('**Sonuç:** Eski 38 içinde 26 muhafazakâr J01 adayı, bir kombinasyon-only Fluconazole ve 11 J01 dışı kayıt var. Eski ADR kaydı taşıyan muhafazakâr adayların 34’ünde XML protein kimliği var; bu 26’ya göre sekiz potansiyel geri kazanım kaydıdır, eğitime hazır oldukları iddiası değildir.'))''')
    md('''## 7 Eksiklik ve belirsizlik

Boş veri, eşleme çatışması ve kaynakta ilişki görülmemesi farklı durumlardır. Aşağıdaki oranlar yalnız kaynak-J01 adaylarına aittir. “Eksik” alanı gerçek negatif olarak kodlanmaz.''')
    code('''missing=pd.DataFrame([{'alan':'XML Compound CID','eksik':int(j01.pubchem_cid.map(len).eq(0).sum())},
                      {'alan':'Hedef kaydı','eksik':int(j01.target_entries.eq(0).sum())},
                      {'alan':'Tutarlı protein ID','eksik':int(j01.protein_ids.map(len).eq(0).sum())}])
missing['payda']=len(j01);missing['eksik_yüzde']=100*missing.eksik/missing.payda
display(missing.round(2))
missing.plot.bar(x='alan',y='eksik_yüzde',legend=False,figsize=(9,4),rot=10,color='#c08235')
finish('07_missingness','J01 kaynak alanlarında eksiklik','Eksik (%)')
missing.to_csv(QA/'missingness_j01.csv',index=False,encoding='utf-8-sig')''')
    md('''**Ne öğrendik?** Protein kaydı olmayan ama kimya ve ADR kaydı bulunan ilaçlar ileride moleküler baseline ile değerlendirilmeye adaydır. Bu, bilinmeyen protein ilişkisi eklemeyi gerektirmez. Yeni XML adaylarının gerçek SIDER PT/UMLS etiket kapsamı, CID/stereo eşlemesi ve tuz kararları WP03'te incelenecek; burada etiket/kohort genişleme garantisi verilmez.''')
    md('''## 8 Tuz bağlantılarını etkileşimli inceleme

Aşağıdaki HTML'de eski listedeki ilk sekiz çözümlü DBSALT ilişkisi ana kayda bağlanır. Tek ebeveyn kanıtı vardır; düğümler yeni ilaç sayımı değildir. Fareyle kimlikleri inceleyin. Plotly HTML kendi JavaScript paketini içerir, internet istemez.''')
    code('''import plotly.graph_objects as go
rows=mapping[mapping.id_kind.eq('DBSALT') & mapping.status.eq('resolved')].head(8)
parents=list(dict.fromkeys(rows.parent_id));salts=list(rows.id);labels=parents+salts
fig=go.Figure(go.Sankey(node=dict(label=labels,pad=25,thickness=18),
    link=dict(source=[parents.index(i) for i in rows.parent_id],target=[len(parents)+i for i in range(len(rows))],
              value=[1]*len(rows),customdata=list(rows.parent_name),hovertemplate='%{customdata}<extra></extra>')))
fig.update_layout(title_text='XML ebeveyn → DBSALT · sekiz gerçek bağlantı (bant = bir kayıt)',height=620)
path=FIG/'salt_parent_interactive.html';fig.write_html(path,include_plotlyjs=True)
display(rows[['parent_id','parent_name','id','old_name']]);display(FileLink(str(path)))''')
    md('''## 9 Doğrulama ve sonraki kapı

Birincil kimlik, iç içe drug/ATC ayrımı, tuz ebeveyni, belirsiz eşleme, dizi etiketi ve duplicate kontrolleri `tests/test_wp02.py` içinde. Kaynak dosyanın boyut/mtime bilgisi tarama öncesi-sonrası kontrol edildi; tam hash alınmadı. Kaynakta bildirilen J01 adaylığı, benzersiz temel ingredient kimliğiyle aynı iddia değildir.''')
    code('''assert summary['invalid_primary_records']==0 and not summary['duplicate_primary_ids']
assert manifest['metadata_unchanged'] and manifest['parse_complete']
assert len(mapping)==209 and legacy.old38.sum()==38
assert len(j01)==summary['j01']
display(pd.DataFrame([summary]).drop(columns=['record_types','old209_mapping_status','duplicate_primary_ids']))
display(Markdown('**WP02 analizi tamamlandı.** WP03 için kullanıcı onayı beklenir.'))''')
    nb.cells=c;nb.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},
                          'execution_method':'IPython InteractiveShell; computed tables and images captured'}
    import os,io,matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    def show(*a,**kw):
        for n in plt.get_fignums():
            buf=io.BytesIO();plt.figure(n).savefig(buf,format='png',dpi=110,bbox_inches='tight');display(Image(data=buf.getvalue()))
        plt.close('all')
    plt.show=show;os.chdir(ROOT);shell=InteractiveShell.instance();n=0
    for cell in c:
        if cell.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:r=shell.run_cell(cell.source,store_history=False)
        if r.error_before_exec or r.error_in_exec:raise RuntimeError(f'Cell {n}: {r.error_before_exec or r.error_in_exec}')
        cell.execution_count=n;cell.outputs=[]
        if cap.stdout:cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=cap.stdout))
        if cap.stderr:cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=cap.stderr))
        for o in cap.outputs:cell.outputs.append(nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata))
        print(f'Executed cell {n}',flush=True)
    path=ROOT/'notebooks/WP02_drugbank_exploration.ipynb';nbf.write(nb,path);print(path)

if __name__=='__main__':main()
