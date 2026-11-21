"""Gerçek PDF pilotunun kaynaklı Türkçe raporu,çalıştırılmış notebook'u ve QA."""
import json,re,subprocess
import pandas as pd
from wp12_pilot import ROOT,QA,SOURCE,FILES,read,preserve
from wp12_prepare import save,sha
from wp09_close_wp10_notebooks import execute,INIT


def table(df):
    def value(v):return str(v).replace('|','/').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']+['| '+' | '.join(value(v) for v in row)+' |' for row in df.itertuples(index=False,name=None)])


def main():
    report=ROOT/'reports/WP12_PDF_PILOT.md'
    if report.exists():raise RuntimeError('PDF pilot report already exists')
    preserve();bundle=read(QA/'source_evidence_bundle.json');annotations=read(QA/'source_context_annotations.json');identity=read(QA/'drug_identity_review.json');meta=read(QA/'document_metadata_content_review.json');rows=[];independent=[]
    for d in bundle['documents']:
        name=d['receipts'][0]['original_filename'];m=next(m for m in meta if m['filename']==name)
        rows.append({'filename':name,'bytes':d['raw_size_bytes'],'pages':d['page_count'],'raw_SHA256':d['raw_sha256'],'content_revision':m['content_revision'],'type':m['document_type_content_verified']})
        result=subprocess.run(['pdfinfo',str(SOURCE/name)],capture_output=True,text=True,encoding='utf-8',errors='replace',check=True);(QA/(name+'.pdfinfo.txt')).write_text(result.stdout+result.stderr,encoding='utf-8');n=int(re.search(r'^Pages:\s+(\d+)',result.stdout,re.M).group(1));assert n==d['page_count'];independent.append({'filename':name,'PyMuPDF_pages':d['page_count'],'Poppler_pdfinfo_pages':n,'status':'PASS'})
    pd.DataFrame(rows).to_csv(QA/'document_inventory.csv',index=False,encoding='utf-8-sig');pd.DataFrame(independent).to_csv(QA/'pdfinfo_page_count_crosscheck.csv',index=False,encoding='utf-8-sig')
    qs={q['quote_id']:q for q in bundle['quotes']};keys={a['key']:a for a in annotations}
    annotated=[]
    for key in ['D_direct_intro','D_class_intro','D_class_renal','D_BUN_exception','D_direct_candidiasis','D_tetracycline_methoxyflurane','D_related_animals']:
        a=keys[key];q=qs[a['quote_id']];annotated.append({'selection_key':key,'physical_page':q['page_number'],'span':f"[{q['char_start']},{q['char_end']})",'scope':a['attribution_scope'],'quote':q['quote'],'qualifier':a['qualifier']})
    pd.DataFrame(annotated).to_csv(QA/'doxycycline_scope_contrast.csv',index=False,encoding='utf-8-sig')
    text='''# WP12 — Kullanıcı PDF'leriyle gerçek belge pilotu

08.11.2026. **PDF çıkarımı ve kaynak doğrulaması tamamlandı;kullanıcı incelemesi bekleniyor. Ollama/LLM kurulumu,model indirme/çalıştırma veya eğitim yapılmadı.**

## 1. Kaynakların gerçekten mevcut olması ve kullanıcı provenansı

Kullanıcı şu iki dosyayı `data/user_pdfs` altında tam adıyla seçti. İkisi degerçek yerel dosya olarak bulundu;herhangi biri bulunmasaydı durulacaktı. Kaynak verilmiş olmasının kanıtı mevcut kullanıcı talimatındaki açık seçimdir;dosya sahibi/yayıncı özgünlüğü veya dijital imza kriptografik doğrulaması iddia edilmez. İnternetten alternatif prospektüs aranmadı veya indirilmedi. PDF içindeki bağlantılar takip edilmedi.

Ham dosyalar salt okunur açıldı;SHA-256 önce/sonra aynı kaldı. PDF header,PyMuPDF PDF biçimi/şifre durumu vefiziksel sayfa sayısı kontrol edildi. Poppler `pdfinfo` sayımları bağımsız olarak6 ve11 sayfayla eşleşti. Kaynaklar kopyalanıp değiştirilmedi.

'''+table(pd.DataFrame(rows))+'''

`user_source_receipts.json` açık kullanıcı dosyası,gerçek yol/hash/boyut vealımın gözlendiği UTC zamanını kaydeder. Bu zaman dosyanın yayımlanma veya ilk yüklenme tarihi değildir. Ham PDF kimliği dosyanın tam baytlarına bağlıdır;dosya adı tek başına kimlik değildir.

## 2. Sözleşmeye uygun bütün fiziksel sayfaların çıkarımı

Önceden kabul edilmiş `WP12_DOCUMENT_DATA_CONTRACT_v1.md` vemakine şeması değişmedi. Hazırlık v1'in boş envanteri/kilitli kapısı tarihsel olarak korundu;gerçek pilot yeni `wp12_pilot.py` girişinde veayrı `reports/qa/WP12/pilot_v1/` dizininde uygulanır.

PyMuPDF2.1,`Page.get_text('text',sort=False,flags=195)` ile bütün17 fiziksel sayfada çalıştı. OCR,layout-model çıkarımı veya sessiz satır/Unicode normalizasyonu yoktur. Parametreler/version ilk çıkarımdan önce kaydedildi. API'nin text-page yolu için [resmî Page.get_text belgesi](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text) kullanıldı;yerel kurulu fonksiyon da incelendi.

Her sayfanın tam metni,UTF-8 hash'i,Unicode kod noktası uzunluğu vephysical index0/page number1 bağlantısı saklandı. `page_text/` dosyaları bayt olarak yazılarak Windows satır sonu dönüşümü önlendi. Alıntıların tamamı bu saklanan aynı dizgenin `[char_start,char_end)` dilimidir;PDF ham bayt konumu veya ekrandaki piksel koordinatı değildir.

17/17 sayfa metin katmanı içerir;boş metin sayfası0 veUnicode replacement-character sayısı0'dır. Bu,bütün görsel içeriğin metne dönüştürüldüğü anlamına gelmez. Doxycycline fiziksel10,ambalaj etiket görseli içerir ve yalnız154 kod noktalık uyarı/footer metni çıkarılmıştır. Sayfa atlanmadı;görseli saklandı,OCR yapılmadı,görselde görülen içerik metin katmanı alıntısı diye uydurulmadı. Fiziksel1'deki yapı görseli de raster kanıt olarak korunur;ondan yeni SMILES/özellik çıkarılmadı.

## 3. Sayfa numarası,sürüm vebelge türü

- Erythromycin:6 fiziksel sayfa,`Package leaflet: Information for the user` başlığıyla hasta kullanma talimatıdır. Fiziksel6'da revizyon **December2025** olarak doğrulandı. PDF metadata CreationDate/ModDate Mart2026'ya aittir;bu tarihler klinik belge revizyonuyla aynı şey değildir.
- Doxycycline:11 fiziksel sayfa;ilk9 sayfanın görünür etiketi `Page1 of9`–`Page9 of9` biçimindedir. Fiziksel10 ambalaj görseli,fiziksel11 elektronik imza temsilidir;11'deki `Signature Page1 of1`,physical page number11'in yerine kullanılmaz.
- Doxycycline revizyonu fiziksel9'da **Rev:02/2022**;PDF CreationDate Mart2022,ModDate Haziran2024'tür. Belgenin footer'ında **en güncel FDA onaylı etiket olmayabileceği** yazmaktadır. Bu pilot,tarihsel kullanıcı dosyasını inceler;güncel etiket veya klinik öneri doğrulaması yapmaz.

Sürüm/ürün/üretici görüşleri,belgedeki gerçek quote ID'lerine bağlanan `document_metadata_content_review.json` içindedir. PDF metadata veya dosya adına bakarak sürüm belirlenmedi. Elektronik imza temsilinin korunması,imzanın kriptografik olarak doğrulandığı anlamına gelmez.

## 4. Ana ilaç,tuz/hidrat,formülasyon vemarka

'''+table(pd.DataFrame(identity)[['filename','DrugBank_parent_id','existing_parent_name','existing_CID','PDF_formulation','PDF_named_salt_or_hydrate','existing_salt_link_id']])+'''

Erythromycin'in etkin maddesi/adı/250mg gücü fiziksel1/6 ile;enterik kaplı tablet niteliği6 ile desteklenir. Belge erythromycin dışında belirli bir tuz/ester adlandırmaz. Sekiz eski DrugBank tuzundan biri tahmin edilerek seçilmedi. Sovereign Medical/Waymade bilgisi pazarlama ruhsatı sahibi/üretici olarak kaydedildi;ayrı bir tescilli ilaç marka kimliği uydurulmadı.

Doxycycline'de monohydrate kapsüller,parent doxycycline'e eşdeğer50/75/100/150mg olarak fiziksel1/8'de tanımlanır. Mevcut WP02 kaynağında **DBSALT001956 Doxycycline monohydrate → DB00254** ilişkisi vardır. Hyclate,hydrochloride vecalcium diğer kayıtlar olarak ayrı kalır. Chartwell Pharmaceuticals/Chartwell RX üretici/pazarlayan şirket metniyle kaydedilir;generic ürün adının yerine yeni bir ilaç markası sayılmaz.

Mevcut WP02 primary ID,PubChem CID veWP04 structure/CID kayıtları birbiriyle kontrol edildi:DB00199/CID12560;DB00254/CID54671203. Bu **etkin madde/ana ilaç düzeyinde** desteklenen eşlemedir;ürün,doz,formülasyon veya klinik eşdeğerlik kanıtı değildir. PDF'nin monohydrate formülü `C22H24N2O8 • H2O` iken mevcut parent yapı `C22H24N2O8` kaydıdır. PDF'nin monohydrate molekül ağırlığı mevcut parent kimya özelliği yerine geçirilmedi;RDKit/kimyasal özellikler yeniden üretilmedi.

## 5. Birebir yan etki bölümleri vebağlam ayrımı

Toplam **44 kaynak alıntısı** vardır. Ana yan etki metni Erythromycin physical4–5 veDoxycycline physical7'den bütünüyle sayfa dilimleri olarak saklandı. Ayrıca kimlik,sürüm,formülasyon veilgili uyarı bağlamları için alıntılar bulunur. Üst bölüm/alt paragraf dilimleri örtüşebilir;44 sayısı benzersiz yan etki,kategori veya hasta sayısı değildir.

Erythromycin4'te bölüm4 başlangıcı,5'te devamı korunur. `Not known` sıklık başlığı ilgili alt bölümle birlikte saklanır;sayısal risk üretilmez. Aynı fiziksel4'teki boya maddesi alerjisi `excipient_specific`,doz aşımı cümlesi `overdose_context` olarak ayrı kaynak bağlamıdır;normal kullanımda etkin madde yan etkisi gibi karıştırılmaz.

Doxycycline7'de açılışın ilk cümlesi doğrudan doxycycline'den söz eder ve`infrequent` niteliğini taşır. Sonraki **The following adverse reactions have been observed in patients receiving tetracyclines** ifadesi sınıf bağlamını kurar. GI,skin,renal,hypersensitivity,blood,other veprolonged thyroid paragrafları bu bağlam quote ID'sine bağlanmıştır;başlıkta Doxycycline yazdığı için otomatik direct-doxycycline listesine çevrilmez.

Seçilmiş kaynaklı ayrım örnekleri (hiçbiri model etiketi değildir):

'''+table(pd.DataFrame(annotated))+'''

Özellikle **BUN** için fiziksel4'teki iki cümle aynı alıntıda tutulur:ilk cümle tetracycline sınıfının antianabolik etkisini,izleyen cümle renal bozukluk bağlamında doxycycline için gözlenmediği istisnasını bildirir. Bu ne doxycycline'e pozitif BUN etiketi ne degenel/bugüne ait “kesin negatif” kanıtıdır. Fiziksel7 renal listesi sınıf kapsamında kalır.

Tooth-development veIH uyarıları `class_including_doxycycline`;CDAD daha geniş antibacterial sınıfı içinde explicitly doxycycline kapsüllerini içerir. Vaginal candidiasis cümlesi doğrudan doxycycline'i anarken`might` niteliği korunur. Methoxyflurane etkileşim cümlesi ad olarak **tetracycline** der;doxycycline diye yeniden adlandırılmaz. Hayvan/in-vitro veilişkili ilaç bulguları insan doxycycline ADR'si sayılmaz. Bu ayrımlar kaynak-okuma temelli pilot anotasyonlardır;klinik uzman gold-standard adjudication veyaLLM sınıflaması değildir,kullanıcı incelemesi bekler.

## 6. Doğrulama,test vegörsel kanıt

18 gerçek pilot testi geçti. İki kaynak dosyanın önce/sonra hash'i;PDF/sayfa sayısı;tüm17 sayfanın ağ vealt süreç erişimi engellenmiş tekrar çıkarımında birebir metin/hash eşitliği;44 alıntının page/span/hash yabancı anahtarları;physical/printed numara ayrımı;görsel10'un korunması;sürüm metni;sınıf/direct bağlamı;BUN istisnası;monohydrate mapping;eski dosya bütünlüğü vebozulmuş alıntıların reddi kontrol edildi. Gerçek JSON,önceden kabul edilmiş `validate_bundle` ile geçerlidir.

Tüm17 sayfa Poppler ile PNG'ye dönüştürüldü veiki contact-sheet üzerinde incelendi;öncelikli Erythromycin4/5,Doxycycline4/7/10 sayfaları ayrıca tam boyutta kontrol edildi. Poppler bir Symbol font uyarısı verdi;çıktı sayfaları oluştu vebu sayfalardaki metin/yerleşim görsel olarak incelendi. Kaynakta değişiklik veya sessiz metin onarımı yapılmadı. OCR yoktur;görsel alanlar metin çıkarımının sınırı olarak açık tutulur.

PyMuPDF mevcut iki Python ortamında yoktu;yalnız proje içi `.deps/pymupdf` konumuna PyMuPDF2.1 vepip bağımlılıkları kuruldu. İlk sandbox denemesi DNS nedeniyle başarısız oldu;yetkili bağımlılık kurulumu tamamlandı. PyMuPDF2.1 paketi onnxruntime/layout/pymupdf4llm yardımcı bağımlılıkları da getirdi;bu pilot yalnız native text katmanını kullanır. **Ollama/LLM modeli indirilmedi veya çalıştırılmadı.** Kurulan PyMuPDF paketi kendi OCR/layout ONNX kaynaklarını da içerir;bu yazılım paketine bağlı kaynaklar pasif olarak kuruldu,hiçbiri çalıştırılmadı. Ayrı OCR-model indirme komutu yoktur;ağ kapalı tekrar testinde onnxruntime modülü yüklenmedi. Tam bağımlılık listesi `runtime_provenance.json` içindedir. Global Python paketleri/önceki modeller değiştirilmedi.

## 7. Çıktılar vekorunan sınırlar

- `reports/qa/WP12/pilot_v1/source_evidence_bundle.json`:2 belge,2 run,17 fiziksel sayfanın tam metni ve44 birebir kaynak alıntısı;mevcut şemaya uygundur.
- `source_quotes.csv`, `source_context_annotations.json`, `doxycycline_scope_contrast.csv`:sayfa/aralık/hash,ana bölüm vecontext quote ID'leri;manual pilot kapsam/qualifier anotasyonu. SIDER/PT/MedDRA eşlemesi veya eğitim etiketi yoktur.
- `document_inventory.csv`, `user_source_receipts.json`, `source_document_metadata.json`, `document_metadata_content_review.json`:ham hash,boyut,sayfa,sürüm/kaynak vePDF metadata ayrımı.
- `drug_identity_review.json`, `existing_parent_salt_links_review.csv`, `identity_input_manifest.json`:mevcut kaynaklarla ingredient-level DrugBank/CID/tuz incelemesi.
- `page_text/`, `page_inventory.csv`, `page_text_coverage_review.csv`, `visual_content_notes.json`:her fiziksel sayfanın kayıpsız metni vegörsel/metin kapsam sınırları.
- `reports/figures/WP12/pilot_v1/pages/`:tüm17 gerçek sayfa PNG'si;iki contact sheet ve`01_physical_page_text_coverage.png` gerçek metin miktarını gösterir.
- `notebooks/WP12_user_pdf_pilot.ipynb`:çalıştırılmış Türkçe notebook;gerçek tablolar,birebir alıntılar,kapsam grafiği veilgili kaynak sayfa görselleri.
- `pilot_tests_v1.txt`, `artifact_validation.json`, `evidence_manifest.json`:test veprovenans kanıtı;hiçbir eski QA dosyası ezilmedi.

Görev başındaki **3208 dosya** (önceki kabul edilmiş artefaktlar veiki seçilmiş ham PDF dahil) hash ile korundu. WP00–WP11 model,split,özellik,sonuç,SHAP/graf attribution veQA verileri değişmedi. Hazırlık v1 sözleşmesi veboş envanteri dekorundu. `run_status.md` yalnız ilerleme kaydıyla güncellendi;önceki tam baytları yeni QA arşivinde vedosyanın devamında saklanır.

`reported_in_PDF` ile `predicted_by_GNN` ayrı kalır. PDF bilgisi SIDER etiketine,model girdisine veyayeni eğitim verisine dönüştürülmedi. Bilinmeyen çiftlerden negatif üretilmedi;klinik risk,tedavi önerisi,nedensellik veyamodel başarısı iddiası yoktur. **Pilot burada durur. Kullanıcı kaynak/alıntı/kimlik incelemesini değerlendirmeden LLM veya sonraki uygulamaya geçilmez.**
'''
    report.write_text(text,encoding='utf-8')
    parts=[('md','''# WP12 · Gerçek iki kullanıcı PDF'siyle kaynak doğrulama pilotu

Kaynaklar kullanıcı tarafından tam dosya adı/yoluyla seçildi. Bu notebook gerçek PDF metinlerini gösterir;örnek/sahte prospektüs içermez. Bütün fiziksel sayfalar PyMuPDF ile çıkarıldı;OCR veyaOllama/LLM/model eğitimi yoktur. **Kaynak alıntısı model etiketi/tahmini değildir.**'''),('code',INIT+r'''
import html
from IPython.display import HTML,Image
Q=ROOT/'reports/qa/WP12/pilot_v1';F=ROOT/'reports/figures/WP12/pilot_v1'
bundle=json.loads((Q/'source_evidence_bundle.json').read_text(encoding='utf-8'))
annotations=json.loads((Q/'source_context_annotations.json').read_text(encoding='utf-8'))
from wp12_document_contract import validate_bundle
display(pd.DataFrame([validate_bundle(bundle)]));display(pd.read_csv(Q/'document_inventory.csv'))
display(pd.read_csv(Q/'pdfinfo_page_count_crosscheck.csv'))
'''),('md','''**Yorum:**2 gerçek belge/17 fiziksel sayfa vardır. HamSHA dosya kimliğidir;dosyanın yayımlayıcısını veya klinik doğruluğunu kanıtlamaz. Kullanıcı provenansı mevcut açık seçim talimatına bağlanır;internetten alternatif dosya alınmadı.

## 1. Fiziksel sayfalar veçıkarım kapsamı'''),('code',r'''
pages=pd.read_csv(Q/'page_text_coverage_review.csv');display(pages)
fig,axs=plt.subplots(1,2,figsize=(12,4.8))
for ax,name,label in zip(axs,['pil.502.pdf','050641Orig1s032lbl.pdf'],['Erythromycin','Doxycycline']):
    d=pages[pages.filename.eq(name)];ax.bar(d.physical_page_number,d.chars,color=['#b98758' if s=='SPARSE_TEXT_SUBSTANTIVE_IMAGE_NO_OCR' else '#527d91' for s in d.text_coverage_status])
    ax.set(title=label+' · tüm fiziksel sayfalar',xlabel='Fiziksel sayfa (1 tabanlı)',ylabel='Metin katmanı Unicode kod noktası',xticks=d.physical_page_number)
axs[1].annotate('10:ambalaj görseli\n154 karakter,OCR yok',xy=(10,154),xytext=(7.8,1400),arrowprops={'arrowstyle':'->'},fontsize=8)
plt.tight_layout();plt.savefig(F/'01_physical_page_text_coverage.png',dpi=160);plt.show()
display(Image(filename=str(F/'erythromycin_all_pages_contact.png')))
display(Image(filename=str(F/'doxycycline_all_pages_contact.png')))
'''),('md','''**Grafik yorumu:**Boş metin sayfası0 olması,görsel içeriğin tamamen metne dönüştürüldüğü anlamına gelmez. Doxycycline fiziksel10'da yalnızfooter metni çıkar;ambalaj görseli saklanır veOCR yapılmaz. Fiziksel11 imza temsilidir. Ana metindeki “Page7 of9”,17 toplam sayfanın sayılmasıyla karıştırılmaz;belge kendi içinde11 fiziksel sayfadır.

## 2. Belge türü,sürüm veana ilaç/formülasyon'''),('code',r'''
display(pd.DataFrame(json.loads((Q/'document_metadata_content_review.json').read_text(encoding='utf-8'))))
identity=json.loads((Q/'drug_identity_review.json').read_text(encoding='utf-8'));display(pd.DataFrame(identity)[['filename','DrugBank_parent_id','existing_parent_name','existing_CID','PDF_formulation','PDF_named_salt_or_hydrate','existing_salt_link_id','mapping_level','product_or_dose_equivalence']])
display(pd.read_csv(Q/'existing_parent_salt_links_review.csv'))
'''),('md','''**Yorum:**Erythromycin6'daDecember2025;Doxycycline9'daRev:02/2022 yazıyor. PDF metadata tarihleri bu revizyonların yerine geçirilmez. FDA belgesi kendisinin güncel olmayabileceğini söylüyor;pilot güncel etiket aramadı.

DB00199 veDB00254 etkin madde/parent düzeyinde mevcut DrugBank/CID kaydıyla desteklenir. Monohydrate→DBSALT001956→DB00254 mevcut ilişkidir;hyclate/hydrochloride ile otomatik ürün eşdeğerliği kurulmaz. Erythromycin250mg enterik tablettir;belgede belirli bir salt/ester adı yoktur. Şirket adı ayrı ilaç markası diye uydurulmaz. Hiçbir PDF kimyası eski model girdisinin yerini almadı.

## 3. Birebir kaynak alıntıları nasıl okunur?'''),('code',r'''
quotes={q['quote_id']:q for q in bundle['quotes']};bykey={a['key']:a for a in annotations}
def show_quote(key):
    a=bykey[key];q=quotes[a['quote_id']]
    display(pd.DataFrame([{'kaynak':a['filename'],'fiziksel_sayfa':q['page_number'],'aralık':f"[{q['char_start']},{q['char_end']})",'scope':a['attribution_scope'],'qualifier':a['qualifier'],'quote_id':q['quote_id']}]))
    display(HTML('<pre style="white-space:pre-wrap">'+html.escape(q['quote'])+'</pre>'))
show_quote('E_adverse_p4');show_quote('E_adverse_p5')
'''),('md','''**Alıntı yorumu:**Bu iki dilim Erythromycin bölüm4'ün physical4–5 devamıdır. `Not known` başlığı vequalifier'lar tutulur. Aynı sayfadaki ayrı excipient/overdose paragrafları bölüm4'e karıştırılmadı. Alıntı metni kaynak extractor çıktısının birebir dilimidir;özetlenmedi veya düzeltilmedi.

## 4. Doxycycline doğrudan ifade ile tetracycline sınıfını ayırmak'''),('code',r'''
show_quote('D_adverse_all')
display(pd.read_csv(Q/'doxycycline_scope_contrast.csv'))
for key in ['D_direct_intro','D_class_intro','D_class_renal','D_BUN_exception','D_direct_candidiasis','D_tetracycline_methoxyflurane']:show_quote(key)
'''),('md','''**Bağlam yorumu:**Doxycycline7'nin ilk cümlesi doğrudan ilaca ait`infrequent` ifadesidir. Ardındaki tetracycline-class cümlesi GI/skin/renal vb.listeyi kapsar;bu başlıklar ayrı direct-doxycycline pozitifleri yapılmadı. BUN'un physical4'teki doxycycline istisnası aynı alıntıda tutulur. `Might`,popülasyon,sınıf,hayvan/ilişkili ilaç veadvice bağlamları görünür kalır. Bunlar pilot kaynak incelemesidir;klinik uzman gold-standard etiketi değildir.

## 5. Gerçek kaynak sayfalarını görerek doğrulamak'''),('code',r'''
for rel in ['pages/erythromycin/page-4.png','pages/erythromycin/page-5.png','pages/doxycycline/page-04.png','pages/doxycycline/page-07.png','pages/doxycycline/page-10.png']:
    print(rel);display(Image(filename=str(F/rel)))
'''),('md','''**Görsel yorumu:**Erythromycin'in kullanıcı istediği4–5'i ileDoxycycline'nin7'si veuyarı4'ü tam sayfa gösterilir. Ambalaj10'un görüntüsü metin katmanıyla aynı şey değildir;bu görseldeki yazılar OCR yapılmış alıntı diye JSON'a eklenmedi. OrijinalPDF'ler değiştirilmedi.

## 6. Testler,provenans vedurma noktası'''),('code',r'''
print((Q/'pilot_tests_v1.txt').read_text(encoding='utf-8'))
display(pd.DataFrame([json.loads((Q/'evidence_complete.json').read_text(encoding='utf-8'))]).T)
from wp12_pilot import preserve
print('Hash ile değişmediği doğrulanan eski dosya/seçiliPDF:',preserve())
'''),('md','''**Sonuç:**18 gerçek test geçti;tüm17 sayfa ağ/alt süreç erişimi engellenmiş tekrar çıkarımında aynı kaldı.44 quote'un aralık/hash/page bağlantısı geçerlidir.44 sayısı ADR sınıfı/olay sayısı değildir;üst/alt dilimler örtüşür. Eski şema,hazırlık kaydı,kohort,model/sonuç/QA dosyaları değişmedi. Yeni SIDER etiketi,model girdisi,eğitim veyaLLM çalışması yoktur. **Kaynak doğrulama pilotu burada durur;kullanıcı incelemesi beklenir.**''')]
    execute('WP12_user_pdf_pilot.ipynb',parts)
    print('Pilot report + executed notebook complete')


if __name__=='__main__':main()
