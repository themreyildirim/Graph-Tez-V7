"""Orijinal WP03 notebook'una dokunmadan kapanış eki oluşturur."""
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]
def main():
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# WP03 son kontrol eki

Bu ek, orijinal WP03 notebook'unu değiştirmeden 62/36 ilaç tablolarını ve etiket stratejisi ölçümlerini gösterir. Büyük kaynaklar okunmaz. Tablolar `wp03_final_review.py` tarafından mevcut QA dosyalarından bağımsız hesaplanmıştır. Nihai 30 kategori, model girdisi ve öğrenme ayrımı oluşturulmaz.''')
    code('''from pathlib import Path
import json,pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
pd.set_option('display.max_rows',100)
pd.set_option('display.max_colwidth',180)
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'AGENTS.md').exists())
QA=ROOT/'reports/qa/WP03/final_review';FIG=ROOT/'reports/figures/WP03/final_review';FIG.mkdir(parents=True,exist_ok=True)
def read(n):return pd.read_csv(QA/n,keep_default_na=False)
checks=json.loads((QA/'consistency_checks.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'kontrol':x['check'],'sonuç':'GEÇTİ' if x['passed'] else 'KALDI'} for x in checks]))
assert all(x['passed'] for x in checks)''')
    md('''## Kesin eşleşen 62 ilaç

PT sayısı benzersiz CUI sayısıdır. Mevcut kimya, eski beş özellik kaydının bulunmasıdır; yeni molekül grafı hazır demek değildir. Protein bayrağı WP02 XML kimlik kontrolünden gelir. V6 üyeliği eski 38 ID listesiyle karşılaştırılmıştır. Bu sütunlar QA içindir; model girdisi olarak dışa aktarılmaz.''')
    code("display(read('accepted_62.csv'))")
    md('''## Eski 38 dışında kalan 36 ilaç

“Yeni” kimlik kazanımı 36'dır. Önceki 38'in yalnız 26'sı aynı muhafazakâr kapsamda kaldığı için 26+36=62; ham 38→62 farkı ile yeni ID sayısı birbirinden ayrılır.''')
    code("display(read('new_36.csv'))")
    md('''## Kategori anlamları

Daralma/genişleme/birleştirme notları terminoloji inceleme bayrağıdır; dış ontolojiyle klinik eşdeğerlik doğrulaması yapılmadı. Genel böbrek işlevi terimine toksik neden yüklemek, Colitis'e antibiyotik bağlamı eklemek ve ayrı CUI'leri birleştirmek ayrıca karar gerektirir.''')
    code("display(read('category_semantic_review.csv'))")
    md('''## Seyreklik ve sınıf sıklığı

Payda hep aynı 62 ilaçtır. Sınıf sıklığı pozitif kaydı olan ilaç sayısıdır; hasta prevalansı değildir. Tüm kohorttan elde edilen bu keşif sayıları gelecekte test verisine göre sınıf seçmek, ağırlık hesaplamak veya girdi üretmek için kullanılamaz.''')
    code('''metrics=read('label_strategy_metrics.csv');display(metrics)
pt=read('class_frequency_PT_CUI.csv');cat=read('class_frequency_historical_30.csv')
display(pt.head(15));display(cat)
fig,axes=plt.subplots(1,2,figsize=(12,4));plt.rcParams['font.family']='DejaVu Sans'
axes[0].hist(pt.positive_drugs,bins=range(1,64),color='#237b8d');axes[0].set_title('PT sınıfları · uzun seyrek kuyruk');axes[0].set_xlabel('Pozitif ilaç / sınıf');axes[0].set_ylabel('Sınıf sayısı')
axes[1].barh(cat.class_id,cat.positive_drugs,color='#c08235');axes[1].set_title('Tarihsel 30 kategori');axes[1].set_xlabel('Pozitif ilaç / sınıf')
fig.set_size_inches(15,10);plt.tight_layout();plt.savefig(FIG/'class_support.png',dpi=160);plt.show()''')
    md('''**Yorum:** 1.061 gözlenen PT sınıfının 406'sı tek ilaçta görülüyor. 30 kategoride destek 7–61 arasında; daha yoğun olması kavramsal doğruluğu kanıtlamaz. Seyrek PT'leri sırf sayısal artış için birleştirmek ve eksik kayıtları negatif kabul etmek uygun değildir.''')
    code('''counts=read('per_drug_positive_counts.csv');display(counts)
fig,axes=plt.subplots(1,2,figsize=(12,4))
axes[0].hist(counts.PT_CUI,bins=16,color='#237b8d');axes[0].set_title('İlaç başına PT pozitifleri');axes[0].set_xlabel('PT sayısı');axes[0].set_ylabel('İlaç sayısı')
axes[1].hist(counts.historical_30,bins=15,color='#c08235');axes[1].set_title('İlaç başına tarihsel kategori pozitifleri');axes[1].set_xlabel('Kategori sayısı')
plt.tight_layout();plt.savefig(FIG/'per_drug_support.png',dpi=160);plt.show()''')
    md('''**Yorum:** PT sayısındaki farklılık, risk veya etki büyüklüğü olarak yorumlanamaz. Sulfanilamide tarihsel kategorilerde sıfır pozitif taşıyor; bu ilaç için 30 gerçek negatif olduğu anlamına gelmez. Gözlenmeyen çiftler unknown kalır.

## Kapanış kararı

13 eski test geçti; 17 bağımsız tablo tutarlılık kontrolü geçti. Nihai kategori seti değişmedi. Etiket stratejisi kararı ve merkezi ham yol konfigürasyonu önerisi raporda; mevcut çalışan kod yeniden yazılmadı. Statik sızıntı incelemesi gelecekteki eğitim hattı için garanti değildir. WP04 başlamaz; kullanıcı onayı beklenir.''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'execution_method':'IPython InteractiveShell; computed outputs'})
    import os,io,matplotlib
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
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        n+=1
        with capture_output(display=True) as cap:r=shell.run_cell(cell.source,store_history=False)
        if r.error_in_exec or r.error_before_exec:raise RuntimeError(r.error_in_exec or r.error_before_exec)
        cell.execution_count=n;cell.outputs=[]
        if cap.stdout:cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=cap.stdout))
        if cap.stderr:cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=cap.stderr))
        for o in cap.outputs:cell.outputs.append(nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata))
    nbf.write(nb,ROOT/'notebooks/WP03_final_review.ipynb');print('Executed WP03 closure notebook',n)
if __name__=='__main__':main()
