"""Public offline final-demo evidence, notebook and status. No inference or network."""
import json
from pathlib import Path
import pandas as pd
import wp13_final_data_v1 as m
from wp12_api_security import public_sha
from wp09_close_wp10_notebooks import execute,INIT
ROOT=m.ROOT;Q=m.Q;F=ROOT/'reports/figures/WP13/final_demo_v1'
def write(p,obj):
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def main():
 bundles=[m.recorded(p) for p in m.PARENTS]
 scope=[{'parent':b['parent'],'outer_fold':b['fold'],'PT_scores':len(b['predictions']),'graph_example_PTs':len({r['class_id'] for r in b['graph']}),'B1_SHAP_example_PTs':len({r['class_id'] for r in b['shap']}),'new_inference':False} for b in bundles]
 pd.DataFrame(scope).to_csv(Q/'coverage.csv',index=False,encoding='utf-8-sig')
 report='''# WP13 FINAL DEMO v1 — Bütünleşik offline araştırma arayüzü

Kullanıcının ekli A–G talimatıyla hazırlanan ayrı sürüm. Ekli dosya G bölümündeki “Ö” ile biter; eksik metne yeni gereksinim atfedilmedi. AGENTS/aktif ROADMAP/WP13_TR_SOURCE_v1/WP13_v1_2/BLIND_EXTERNAL_VALIDATION_FEASIBILITY_v1 esas alındı. Önceki kod, kaynak, model, QA ve insan PENDING kayıtları değiştirilmedi.

## Tek ana akış ve çalışan işlevler

Kayıtlı ilaç seç veya Prospektüs PDF yükle. Dört bölüm: İLAÇ VE BELGE, YAN ETKİ TAHMİNLERİ, MODEL AÇIKLANABİLİRLİĞİ, PROSPEKTÜS KARŞILAŞTIRMASI. Light tema açıkça sabit. Teknik hash/job/quote ayrıntıları ve uzun pasajlar kapalı açılır alanlarda. Türkçe kaynaklar varsayılan; İngilizce dosyalar frozen geçmişte korunur.

**Kaynak terimi:** Nefes darlığı tek terim, fiziksel6/[1319,1332) olarak gösterilir. Altı maddelik pasaj varsayılan kapalı “Prospektüsteki tam bölüm”dedir. Sıklık/uyarı ayrıca; kaynak adayları model tahmini diye sunulmaz. Türkçe örneklerin25 ve48 satır sayısı klinik veya GNN doğruluğu değildir. MONODOKS BUN/birikim ayrımı ve hayvan/aşırı doz kaynak sözleşmesi korunur. Kaynak LLM cevabı yoksa NOT_AVAILABLE; mekanizma NOT_ESTABLISHED.

**Tahmin:** PDF referansı kapalıyken bile ana etkin madde araştırma tahmini gösterilir. DB00199 primary own-fold outer3/318PT, DB00254 outer1/240PT A1P1 kayıtlı OOF. Sıralama tablosu ve ilk10 skor grafiği gerçek dosyadan; yeni model çalıştırılmadı. Frozen PT adları özgün İngilizcedir; onaysız Türkçe tıbbi eşleme/çeviri yapılmadı. Skor yüzde klinik risk değildir, unknown gerçek negatif değildir. Ticari ürün/tuz/doz eşdeğerliği kurulmaz. B1 ile yeni performans karşılaştırması yapılmadı; B1 yalnız ayrı SHAP panelindedir.

**Açıklama:** WP11 final_artifact_manifest ve model input_manifest hash'leriyle seçilmiş gerçek katkı dosyaları doğrulandı. İlgili ilaç/fold/PT ile eşleşen C0000731 ve C0000737 frozen örnekleri için A1P1 tekil mesaj maskelemesi ve B1 SHAP ayrı sunulur. A1P1 orijinal logit sigmoid'i kayıtlı OOF ile1e-6 içinde; Δz=orijinal−müdahale1e-6 içinde; B1 SHAP base+toplam=logit1e-8 içinde kontrol edildi. Yeni attribution veya inference yok. Sabit derece/rol paydalı müdahale birincil, fiziksel silme/yeniden normalizasyon ayrı açılır tabloda. Rol/protein/PPI kimlikleri ve NA değerleri korunur; müdahale grafiği mevcut satırların ilk12 bağlantısını gösterir, eksik yol sıfıra doldurulmaz. Açıklama olmayan PT için başka hedefin açıklaması bağlanmaz. Kimya özellikleri ve maske SHAP'ta ayrı satırlardır. Girdi şeması attribution/klinik neden değildir.

**Yükleme:** st.file_uploader,20MB,120 fiziksel sayfa ve2milyon karakter limiti; şifreli/bozuk PDF reddi. PDF RAM'de işlenir; ham dosya için geçici disk dosyası oluşturulmaz. Hash, görünen ad, bütün fiziksel sayfalar/text hash/status session belleğinde; kullanıcı kaynak JSON'unu indirebilir. Hasta verisi uyarısı var. Tam Türkçe hash eşleşmesi kayıtlı kaynağı açar. Diğer PDF kimliği UNVERIFIED, GNN NOT_SUPPORTED; yalnız gerçek metindeki anahtar sözcük çevresi pencereleri EXPERIMENTAL. KT/KÜB/İngilizce başlık tanıma adapter'da var; bu klinik kimlik veya ADR çıkarımı değildir. Sözlük dışı/boş sayfa yan etki yokluğu değildir; OCR_NOT_AVAILABLE. Yeni PDF'ye iki örneğin anchor listesi uygulanmaz. Otomatik API/anahtar okuma yok.

## Sızıntısız kol ayrımı ve açık kalan sınır

data_pins.json mevcut model/OOF/katkı snapshot hash'lerini kilitler; prior_pins önceki split/model/QA kaynaklarını korur. Tahmin adapter'ı PDF okumadan kayıtlı çıktıyı sunar; bunu test doğrular. PDF referansı model/scaler/fit/PT sözlüğünü değiştiremez. Mevcut iki ilaç zaten incelendiği için bu prospektif bağımsız dış doğrulama değildir.

Türkçe terim→PT için henüz onaylı uzman eşlemesi yoktur. Tüm73 referans kaydı UNMAPPED/PENDING; model skoru bunlara otomatik iliştirilmedi. Dolayısıyla eşlenmiş yan yana sıralama veya klinik doğruluk metriği uydurulmadı. Mevcut kaynak tablosu ve ayrı PT sıralaması incelenebilir; gerçek crosswalk onaylanınca sürümlü ek gerekir. Prospektüste yokluk gerçek negatif/kesin yanlış tahmin değildir. Genel yeni antibiyotik inference desteklenmez; yükleme yeni tahmin anlamına gelmez. Bu bilimsel kısıt final arayüzde görünür.

## Test ve gerçek ekranlar

16 offline test PASS:318/240 own-fold anahtarları, PDF olmadan tahmin, kapsam dışı ilaç, tek kaynak terimi/aralık, iki gerçek dosya hash'iyle upload, bilinmeyen okunabilir ve boş PDF, boyut/biçim/sayfa/karakter limitleri, UNMAPPED/PENDING, tam attribution ID eşliği, eksik hedef, Δz/NA ve SHAP toplamı, ağ/eğitim çağrısı yokluğu. İlk14 ve final16 logu ayrı saklandı.

Gerçek tarayıcıda PDF kapalı OOF tablosu, seçili C0000731 gerçek A1P1 müdahalesi/B1 SHAP, tek Nefes darlığı ve kapalı tam pasaj, gerçek MONODOKS PDF upload→hash eşleşmiş Türkçe kaynak görüldü. File chooser işlemi yavaştı; başarısız veya sessiz atlanmış sayılmadı, gerçek sonuç browser_real_upload.txt'de. Bilinmeyen/boş dosya UI upload'u ayrıca browser'da denenmedi; bunlar backend testleridir. Ekranlar gerçeklocalhost8508, mockup değil. UI sonucu WP12 semantik başarı oranı değildir.

Kaynak güncelliği UNVERIFIED, insan QA PENDING kalır. Eski modeller yeniden eğitilmedi; API/OCR/yeni attribution/model inference0. Seçilmiş önceki dosya/hash koruma kapsamı final_verification.json'dadır; bütün disk taraması değildir. .env/anahtar okunmadı veya hashlenmedi. run_status eski baytları altında aynen korunur.

## Çalıştırma

`& "C:\\Users\\emrey\\Downloads\\Graph-Tez-V7_SADELESTIRILMIS_CODEX\\Graph-Tez-V7\\scripts\\WP13_Start_FINAL_DEMO_v1.ps1"`

Varsayılan localhost8501. Port doluysa kullanıcı boş bir port seçebilir (`-Port 8509`); eski sunucular kapatılmaz. Hazır QA sürümü http://127.0.0.1:8508. Sunum: PDF kapalı tahmin→PT C0000731→açıklanabilirlik→Türkçe PDF referansı→tek kaynak terimi. Dosya yüklemesini ayrı ana işlemden gösterin. Çalıştırılmış notebook WP13_FINAL_DEMO_v1.ipynb, QA/figures WP13/final_demo_v1. İnsan değerlendirmesi beklenir; API veya yeni dış ilaç denemesi başlatılmaz.
'''
 (ROOT/'reports/WP13_FINAL_DEMO_v1.md').write_text(report,encoding='utf-8')
 execute('WP13_FINAL_DEMO_v1.ipynb',[
 ('md','# WP13 FINAL DEMO v1\n\nGerçek kayıtlar, ayrı tahmin/açıklama/PDF kolları. Yeni model/API/attribution yok. İnsan PENDING; kaynak güncelliği doğrulanmadı.'),
 ('code',INIT+"\nQ=ROOT/'reports/qa/WP13/final_demo_v1';F=ROOT/'reports/figures/WP13/final_demo_v1'\ndisplay(pd.read_csv(Q/'coverage.csv'))\n"),
 ('md','**Yorum:** Kendi-fold tahminleri PDF olmadan kullanılabilir. Açıklama kapsamı tüm PT uzayından daha dardır; olmayan açıklama doldurulmaz.'),
 ('code',"b=json.loads((Q/'DB00199.json').read_text(encoding='utf-8'))\np=pd.DataFrame(b['predictions']);display(p.head(10))\nfig,ax=plt.subplots(figsize=(10,5));p.head(10).plot.barh(x='target_name',y='score_observed_record_proxy',ax=ax,legend=False);ax.set_xlabel('Observed-record proxy skor; klinik risk değil');plt.tight_layout();plt.savefig(F/'05_actual_recorded_ranking.png',dpi=160);plt.show()"),
 ('md','**Yorum:** İlk10 frozen sıralama görselidir; yeni tahmin veya doğruluk değerlendirmesi değildir.'),
 ('code',"g=pd.DataFrame(b['graph']);s=pd.DataFrame(b['shap']);display(g[g.class_id.eq('C0000731')].head(12));display(s[s.class_id.eq('C0000731')]);display(pd.read_csv(Q/'DB00199_reference_UNMAPPED.csv').head(8))"),
 ('md','**Yorum:** Δz A1P1 mesaj müdahalesidir; SHAP B1 logit açıklamasıdır. Kaynak terimleri UNMAPPED; otomatik PT eşlemesi veya negatif üretimi yok.'),
 ('code',"from IPython.display import Image\nfor f in ['01_real_OOF_without_PDF.jpg','02_real_A1P1_intervention.jpg','03_selected_term_not_six_predictions.jpg','04_real_PDF_upload.jpg']:display(Image(filename=str(F/f),width=1000))"),
 ('md','**Yorum:** Ekranlar gerçeklocalhost8508 arayüzündendir. Gerçek MONODOKS dosyası yüklendi; metin çıktısı değil ham PDF kullanıldı. Sunum başarısı klinik/semantik onay değildir.')])
 prior=m.read(Q/'prior_pins.json')
 for p,h in prior.items():assert public_sha(ROOT/p)==h,p
 assert (Q/'tests_final.log').read_text(encoding='utf-8-sig').rstrip().endswith('OK')
 before=(Q/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==before
 prefix='''# WP13 FINAL DEMO v1 ·09.11.2026

Bütünleşik dört bölüm: ilaç/belge, gerçek own-fold A1P1 OOF tahmini, tam ilaç/PT/fold eşleşmeli WP11 A1P1 müdahale+B1 SHAP, ayrı PDF referansı. PDF olmadan318/240PT tahmin; yeni inference/eğitim/API/attribution0. Tek kaynak terimi ve aralığı önde, tam bölüm kapalı. Gerçek MONODOKS browser upload doğrulandı; bilinmeyen PDF UNVERIFIED/NOT_SUPPORTED, OCR yok. Türkçe73kaynak UNMAPPED/PENDING; klinik doğruluk metriği üretilmedi.16offline test PASS; önceki hash'ler aynı. Launcher scripts/WP13_Start_FINAL_DEMO_v1.ps1; QA localhost8508. Rapor reports/WP13_FINAL_DEMO_v1.md; notebook notebooks/WP13_FINAL_DEMO_v1.ipynb. Kaynak güncelliği doğrulanmadı, insanPENDING aynı. Kullanıcı değerlendirmesi bekleniyor.

---
Önceki durum (tam baytları korunmuş):

'''
 (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
 write(Q/'final_verification.json',{'previous_hashes_verified':len(prior),'new_tests_PASS':16,'new_inference':0,'API':0,'new_training':0,'new_attribution':0,'human_QA':'PENDING_UNCHANGED','PT_reference_mapping':'UNMAPPED','actual_browser_upload':'MONODOKS_PASS','run_status_exact_history_suffix':(ROOT/'run_status.md').read_bytes().endswith(before)})
 files=['scripts/wp13_final_data_v1.py','scripts/wp13_final_deliverables_v1.py','scripts/WP13_Start_FINAL_DEMO_v1.ps1','apps/drug_safety_explorer_FINAL_v1.py','tests/test_wp13_final_v1.py','reports/WP13_FINAL_DEMO_v1.md','notebooks/WP13_FINAL_DEMO_v1.ipynb','run_status.md']
 files.extend(p.relative_to(ROOT).as_posix() for folder in [Q,F] for p in folder.iterdir() if p.is_file())
 write(Q/'evidence_manifest.json',{p:public_sha(ROOT/p) for p in sorted(set(files))})
 print('Final public evidence and previous hashes verified:',len(prior))
if __name__=='__main__':main()
