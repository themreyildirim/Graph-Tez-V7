"""Belge olmadan sözleşme/readiness raporu ve çalıştırılmış notebook üretir."""
import csv,json
from wp12_prepare import ROOT,QA,save,preserve
from wp12_document_contract import schema,empty_bundle,validate_bundle
from wp09_close_wp10_notebooks import execute,INIT


def main():
    if (ROOT/'reports/WP12.md').exists():raise RuntimeError('Preparation report already exists')
    previous=preserve();status=validate_bundle(json.loads((QA/'empty_document_bundle.json').read_text(encoding='utf-8')))
    assert all(status[k]==0 for k in ['documents','extraction_runs','pages','quotes'])
    checks=[
      {'control':'Belge/run/page/quote şeması','status':'PASS_CONTRACT_TEST_ONLY','scope':'JSON yapısı ve yabancı anahtarlar'},
      {'control':'SHA ve deterministik kimlik','status':'PASS_CONTRACT_TEST_ONLY','scope':'RAM teknik bayt/dizgeleri;gerçek PDF değil'},
      {'control':'Unicode aralık ve birebir alıntı','status':'PASS_CONTRACT_TEST_ONLY','scope':'Türkçe/emoji/satır sonu teknik dizgeleri'},
      {'control':'Tekrar ve eksik/boş sayfa','status':'PASS_CONTRACT_TEST_ONLY','scope':'Tamamlandı statüsü tüm fiziksel sayfaları gerektirir'},
      {'control':'Gerçek PDF kimliği/biçimi','status':'NOT_RUN_NO_USER_PDF','scope':'Kullanıcı dosyası bekleniyor'},
      {'control':'PyMuPDF metin çıkarımı/okuma sırası','status':'NOT_IMPLEMENTED','scope':'Parser bağlı değil'},
      {'control':'Tarama/OCR ihtiyacı','status':'NOT_ASSESSED','scope':'Gerçek belge görülmedi'},
      {'control':'İlaç/tuz/formülasyon semantik eşleme','status':'NOT_IMPLEMENTED','scope':'Dosya adından otomatik onay yok'},
      {'control':'Ollama/LLM','status':'DISABLED','scope':'Kurulum,indirme veya servis yok'},
      {'control':'Yeni model eğitimi','status':'DISABLED','scope':'Önceki sonuçlar sabit'},
      {'control':'Önceki kabul edilmiş dosyalar','status':'PASS_HASH','scope':str(previous)+' dosya değişmedi'}]
    with (QA/'verification_scope.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['control','status','scope']);w.writeheader();w.writerows(checks)
    fields=[]
    for entity,definition in schema()['$defs'].items():
        for name,rule in definition['properties'].items():fields.append({'entity':entity,'field':name,'required':name in definition['required'],'shape':json.dumps(rule,ensure_ascii=False)})
    with (QA/'contract_field_dictionary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['entity','field','required','shape']);w.writeheader();w.writerows(fields)
    (ROOT/'reports/WP12.md').write_text('''# WP12 — Kullanıcı PDF'leri için veri sözleşmesi ve ön hazırlık

08.11.2026. **Durum:AWAITING_USER_PDFS. Yalnız hazırlık tamamlandı;gerçek WP12 belge çıkarımı başlamadı.**

Kullanıcı kaynak kararını verdi:prospektüs PDF'lerini kullanıcı sağlayacak. AGENTS,aktif ROADMAP WP12 ve değişmeden korunan `WP12_PREPARATION_DECISION.md` esas alındı. Otomatik prospektüs arama/indirme,PDF açma,belge üretme,Ollama/LLM kurulumu,model indirme veya yeni eğitim yapılmadı. Kullanıcı bu istekte PDF sağlamadığı için kayıtlı belge/run/sayfa/alıntı sayısı **0/0/0/0**'dır. Bu sayı bilgisayardaki bütün PDF'lerin taranmasıyla bulunmuş bir sayı değildir;bu aşamaya sağlanan gerçek girdinin durumudur.

## Sözleşme neyi sağlar?

`docs/plan/WP12_DOCUMENT_DATA_CONTRACT_v1.md`,belge teslim olayını ham dosya kimliğine;extractor sürüm/seçeneklerini run'a;fiziksel sayfayı tam metin/hash'e;alıntıyı tek sayfadaki yarı açık `[start,end)` aralığına bağlar. Kimlik zinciri document→run→page→quote'tur. Makine şeması `docs/schemas/WP12_document_bundle_v1.schema.json`,çalıştırılabilir saf doğrulayıcı `scripts/wp12_document_contract.py`dir. PDF/ağ/dosya erişimi bu doğrulayıcıda yoktur;yalnız verilen JSON/dizgeler üzerinde çalışır.

BelgeID `sha256:`+ham dosyanın SHA-256 değeridir. Aynı baytlar farklı adlarla verilirse aynı kimlik veayrı receipt kayıtları kullanılır;değişen baytlar yeni belge kimliğidir. Gerçek intake aşamasında hash salt okunur dosya akışından hesaplanacaktır;bu hazırlıkta PDF hash'lenmedi. Kaynağın gerçek kullanıcı teslimi vePDF biçimi metadata'nın kendisinden kanıtlanamaz;bu kontroller dosyalar geldikten sonra yapılacaktır.

Fiziksel `page_index`0 tabanlı,`page_number`1 tabanlıdır;basılı sayfa etiketi ayrı/nullable alandır. Metin satır sonu,Unicode veya boşluk normalizasyonu yapılmadan korunur. Aralıklar saklanan tam sayfa dizgesindeki **Python Unicode kod noktalarıdır**,UTF-8 bayt veyaUTF-16 birimi değildir. Alıntı bu dilimin birebir eşitidir;parafraz değildir. Sayfa/metin/run değişince eski kaynak aralığı taşınmış gibi gösterilmez. Çok sayfalı kanıt tek sahte aralığa birleştirilmez.

Metinsiz sayfa atlanmaz;boş metin/hash ve`no_text` ile kalır. `complete` statüsü tüm fiziksel sayfaları gerektirir;eksik çıktıda`partial` kalır. OCR veya okuma sırası başarısı şu an test edilmiş değildir. Parser parametreleri veçalışma stratejisi gerçek PDF incelendiğinde,provenansı korunarak belirlenecektir.

## Gerçek veri ve teknik test ayrımı

24 birim testi geçti. Testler yalnız RAM'de `technical_test_fixture` olarak işaretlenmiş,hiçbir prospektüs/ilaç/yan etki bilgisi içermeyen teknik bayt veUnicode dizgeleridir. Gerçek veya sahtePDF oluşturulmadı. Teknik kayıtlar üretim doğrulamasında varsayılan olarak reddedilir;boş gerçek envantere aktarılmadı. Kaynak türü/URL reddi,kimlik/hash,sürüm/değişmiş seçenek,duplicate/foreign-key,sayfa numarası,sınır,metin/alıntı değişikliği veUnicode kontrolleri test edildi. `extract_user_pdfs` hazırlık kapısı dosya açmadan durur.

Bu testler **gerçek PDF çıkarım başarısı değildir**. Dosya biçimi/şifre/bozulma,sayfa okuma sırası,tablo/sütun,OCR ihtiyacı,ilaç kimliği veklinik metin anlamı henüz doğrulanmadı. QA `verification_scope.csv` hangi sonucun teknik test,hangi işin bekleyen/uygulanmamış olduğunu açıkça ayırır.

## Kaynak bilgisi modele dönüşmez

`claim_kind=verbatim_source_quote` yalnız birebir kaynak metni gösterir;klinik pozitif yan etki etiketi değildir. `reported_in_PDF` ile `predicted_by_GNN` ayrı tutulur. Model skoru/SHAP/Δz veya `kalite_skoru` quote kaydına eklenemez. LLM yorum/özet alanı bu hazırlıkta uygulanmadı;LLM yan etki tahmini veya sayısal attribution üretmez. Kaynak metin aynı hedefin model girdisine/geriye dönük eğitim etiketine sokulmaz. Belge–DrugBank/CID,tuz/formülasyon eşlemesi daha yapılmadı;dosya adı veya marka otomatik doğrulama değildir.

## Çıktılar ve korunma

- İnsan için veri sözleşmesi ve JSON Schema:kimlik,sayfa,metin aralığı vealıntı bağını tanımlar.
- `configs/WP12_preparation_v1.json`:user-only kaynak kararı veAWAITING_USER_PDFS kapısı;arama/indirme/parser/LLM/eğitim kapalı.
- `reports/qa/WP12/preparation_v1/document_inventory.csv`:yalnız başlıklı,gerçek kayıt içermeyen envanter. `empty_document_bundle.json` dört boş dizi içerir;örnek prospektüs değildir.
- `readiness.json`, `verification_scope.csv`, `contract_field_dictionary.csv`, `contract_tests_v1.txt`:gerçek sıfır girdi durumu,şema alanları ve24 testin kayıtları.
- `notebooks/WP12_document_contract_preparation.ipynb`:çalıştırılmış Türkçe açıklamalı hazırlık notebook'u;gerçek boş envanteri veşema tablolarını gösterir.
- `reports/figures/WP12/preparation_v1/01_document_provenance_contract.png`:yalnız sözleşmenin kavramsal kaynak zinciri/bekleme kapısıdır;gerçek çıkarım sonucu değildir.
- Yeni doğrulama kodu/testleri standart Python kütüphanesiyle çalışır;yeni bağımlılık kurulmadı. Notebook/görsel mevcut ortamı kullanır.

Görev başındaki **3183 önceki kabul edilmiş dosya** hash ile korunur. WP11 kapanışının43 kanıt manifest girdisi doğru status arşiviyle doğrulandı;hiçbir eski manifest/QA değiştirilmedi. `run_status.md` yalnız ilerleme kaydı için yeni başlıkla güncellenir;önceki tam baytları bu QA altında ve dosyanın devamında aynen korunur. WP00–WP11 kaynak,model,split,sonuç veQC kararları değişmez.

**Belge bekleme noktasında duruldu. Kullanıcı PDF'leri sağladıktan sonra gerçek belge doğrulama veçıkarım çalışmasına geçilecek;şu an çıkarım veya kurulum başlatılmadı.**
''',encoding='utf-8')
    parts=[('md','''# WP12 · Kullanıcı PDF'leri için veri sözleşmesi hazırlığı

**Gerçek PDF sağlanmadı.** Bu notebook gerçek belge çıkarımı değildir;boş envanter veuygulama ön hazırlığını gösterir. Kullanıcı prospektüs PDF'lerini kendisi sağlayacak. Otomatik arama/indirme,PDF açma,Ollama/LLM kurulumu veya eğitim yoktur.'''),('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/preparation_v1'
F=ROOT/'reports/figures/WP12/preparation_v1';F.mkdir(parents=True,exist_ok=True)
readiness=json.loads((Q/'readiness.json').read_text(encoding='utf-8'))
display(pd.DataFrame([readiness]).T.rename(columns={0:'gerçek_durum'}))
inventory=pd.read_csv(Q/'document_inventory.csv');display(inventory)
print('Gerçek belge envanteri satırı:',len(inventory))
'''),('md','''**Yorum:**0 satır “bilgisayarda PDF yok” anlamına gelmez;bu çalışmaya kullanıcı PDF'si verilmediğini gösterir. Sahte prospektüs veya örnek tıbbi içerik gerçek veri gibi eklenmedi. Sayfa vealıntı sayısı da0'dır.

## 1. Belge kimliği ile alıntı arasındaki bağ'''),('code',r'''
fields=pd.read_csv(Q/'contract_field_dictionary.csv');display(fields)
from wp12_document_contract import validate_bundle
bundle=json.loads((Q/'empty_document_bundle.json').read_text(encoding='utf-8'))
display(pd.DataFrame([validate_bundle(bundle)]))
'''),('md','''**Yorum:**BelgeID ham baytlardan,runID belge+motor+sürüm+seçeneklerden,pageID sayfa/metin kimliğinden,quoteID tek sayfa aralığı vealıntı hash'inden oluşur. Gerçek dosya yokken herhangi bir PDF hash'i hesaplanmadı. Aynı dosyanın isim değişikliği yeni belge üretmez;farklı receipt ile izlenir.

## 2. Kavramsal akış;çalıştırılmış çıkarım değil'''),('code',r'''
from matplotlib.patches import FancyBboxPatch
fig,ax=plt.subplots(figsize=(15,4.6));ax.set(xlim=(0,15),ylim=(0,4));ax.axis('off')
boxes=[('Kullanıcı PDF\nHenüz sağlanmadı','#d4b18a'),('Document\nham SHA-256','#86a8b8'),('Run\nmotor / sürüm / ayar','#86a8b8'),('Page\nindeks / tam metin / hash','#86a8b8'),('Quote\n[start,end) / alıntı / hash','#86a8b8')]
for i,(label,color) in enumerate(boxes):
    x=.25+i*3
    ax.add_patch(FancyBboxPatch((x,1.8),2.4,1.15,boxstyle='round,pad=.08',facecolor=color,edgecolor='#526875'))
    ax.text(x+1.2,2.375,label,ha='center',va='center',fontsize=10)
    if i<4:ax.annotate('',xy=(x+2.94,2.375),xytext=(x+2.5,2.375),arrowprops={'arrowstyle':'->','color':'#7a8890'})
ax.text(7.5,3.55,'WP12 veri sözleşmesi · kavramsal kimlik/kaynak zinciri',ha='center',fontsize=15)
ax.text(7.5,1,'DUR:AWAITING_USER_PDFS · Gerçek çıkarım,LLM ve eğitim kapalı',ha='center',fontsize=12,color='#9b4d43')
ax.text(7.5,.35,'Gerçek envanter:belge0 / run0 / sayfa0 / alıntı0. Kutular mevcut veri değil,alan ilişkileridir.',ha='center',fontsize=10)
plt.tight_layout();plt.savefig(F/'01_document_provenance_contract.png',dpi=160);plt.show()
'''),('md','''**Şema görselinin yorumu:**Bu beş kutu gerçek kayıt veya sonuç değildir. İleride kullanıcının dosyası ile sayfa/alıntı arasındaki provenans ilişkisini gösterir. Fiziksel sayfa indeksi0,insan numarası1 tabanlıdır;basılı etiket ayrı saklanır. Metin aralıkları Python Unicode kod noktalarında yarı açıktır;alıntı tam sayfa dizgesinin birebir dilimidir. Türkçe/emoji/satır sonu normalizasyonu sessizce yapılmaz.

## 3. Test edilen sözleşme ile henüz test edilmemiş belge işlemi'''),('code',r'''
display(pd.read_csv(Q/'verification_scope.csv'))
print((Q/'contract_tests_v1.txt').read_text(encoding='utf-8'))
'''),('md','''**Yorum:**24 test yalnız RAM teknik fikstürlerini kullanır;prospektüs içeriği veya PDF dosyası değildir. `technical_test_fixture` üretim doğrulamasında reddedilir. Şema/ID/aralık/yabancı anahtar testleri geçti;gerçek PDF biçimi,sayfa okuma sırası,OCR,semantik eşleme veLLM davranışı doğrulanmış değildir. Çıkarım girişindeki hazırlık kapısı dosya açmadan durur.

## 4. Kaynak metin ile tahmini karıştırmamak'''),('code',r'''
from wp12_prepare import preserve
print('Hash ile korunan önceki dosya:',preserve())
display(pd.DataFrame([{'kaynak':"verbatim_source_quote / reported_in_PDF",'model':"predicted_by_GNN / SHAP / Δz ayrı artefaktta",'anlam':"Kaynak alıntı klinik pozitif etiket veya bireysel risk değildir",'durum':"Kullanıcı PDF'leri bekleniyor"}]).T)
'''),('md','''**Durma noktası:**Gerçek PDF sağlanınca salt okunur dosya/kimlik/biçim veçıkarım kontrolleri yapılacak. Şimdilik otomatik arama/indirme,gerçek çıkarım,LLM kurulumu/model indirmesi veya eğitim yoktur. Önceki WP00–WP11 dosyaları değişmedi. Sözleşme hazır;belge bekleniyor.''')]
    execute('WP12_document_contract_preparation.ipynb',parts)
    print('Preparation report/notebook created;zero document extraction')


if __name__=='__main__':main()
