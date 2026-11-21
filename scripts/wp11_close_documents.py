"""08.11.2026 kapanış raporu/notebook'u; kabul edilmiş sonuçlara yazmaz."""
import json
import pandas as pd
from wp11_close_audit import ROOT,C,G,B,read,csv,preserve
from wp11_linear_shap import sha
from wp09_close_wp10_notebooks import execute,INIT


def table(df):
    def text(v):return (f'{v:.7g}' if isinstance(v,float) else str(v)).replace('|','/').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']+['| '+' | '.join(text(v) for v in row)+' |' for row in df.itertuples(index=False,name=None)])


def main():
    target=ROOT/'reports/WP11_FINAL_CLOSURE.md'
    if target.exists():raise RuntimeError('WP11 final closure report already exists')
    preserve();r=read(C/'replay_complete.json');assert r['status']=='PASS';assert read(C/'table_audit_complete.json')['status']=='PASS'
    perf=[]
    for wp,names in [('WP09',['G_noPPI','G_realPPI','G_shuffledPPI_mean3_metrics']),('WP10',['A0P0','A0P1','A1P0','A1P1'])]:
        p=ROOT/f'reports/qa/{wp}/training_v1/metrics_with_group_CI.csv';df=pd.read_csv(p);df=df[df.protocol.eq('primary')&df.scope.eq('paired54')&df.metric.eq('drug_macro_AP')&df.model.isin(names)]
        for row in df.itertuples():perf.append({'WP':wp,'model':row.model,'accepted_drug_macro_AP':row.estimate,'source_CSV':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),'recomputed':False})
    csv('accepted_performance_unchanged.csv',perf)
    m=pd.read_csv(C/'model_integrity_all742.csv');models=m.groupby('model_group').size().rename('NPZ_metadata_çifti').reset_index()
    streams=pd.read_csv(C/'contribution_stream_checks.csv');network=pd.read_csv(C/'network_data_consistency.csv');tests=pd.read_csv(C/'tests_rerun_summary.csv');images=pd.read_csv(C/'image_data_checks.csv');keys=pd.read_csv(C/'all_intervention_key_checks.csv');na=pd.read_csv(C/'NA_source_consistency.csv')
    content='''# WP11 — Nihai kapanış denetimi

**Tarih:08.11.2026. Durum:PASS — kullanıcı tarafından araştırma kapsamında kabul edilen WP11 kapatıldı. WP12 yalnız hazırlık notudur;uygulama başlamadı.**

Esas belgeler AGENTS,aktif ROADMAP,SOURCE_USAGE_AUDIT,`reports/WP11.md`, `reports/WP11_GRAPH_EXPLANATIONS.md` ve kabul edilmiş yöntem sözleşmeleridir. Önceki raporlar ve çıktılar değiştirilmedi. İlk aşama raporundaki “graf yalnız öneri”,sonraki graf raporundaki “nihai kapanış yapılmadı” ifadeleri kendi tarihsel aşamalarını anlatır; bugünkü kapanış ayrı belgelenir. Yeni model eğitimi,optimizer,backward,yeni attribution yöntemi,hiperparametre araması veya başarıya göre sonuç/örnek seçimi yoktur.

## 1. Kayıtlı model,kaynak ve QA bütünlüğü

Görev başlangıcındaki **3.139 kabul edilmiş dosyanın SHA-256 değeri** değişmeden doğrulandı. Buna B1 SHAP,graf attribution,önceki model/metadata,split/feature/QC,rapor/notebook/görsel ve önceki QA manifestleri dahildir. B1 ve graf aşamasının input,policy commit,prior-artifact ve final-artifact olmak üzere8 manifesti kontrol edildi. Mutable `run_status.md` için aşamaya ait arşiv doğru kaynak olarak kullanıldı;uyuşmazlık gizlemek için eski manifest değiştirilmedi.

Model ağırlık dosyasının hash'i kendi metadata kaydıyla eşleştirildi;numeric array'ların sonluluğu denetlendi. WP09/WP10'da kaydedilmiş numeric state digest'i de tekrar hesaplandı. Toplam742 NPZ ve742 metadata dosyası:

'''+table(models)+'''

İşlenmiş/modelde kullanılan kaynaklar,NPZ train/query bundle'ları,kimlik köprüleri,özellikler,kilitli sözlükler ve kaynak manifestleri kontrol edildi. Büyük ham DrugBank XML/STRING dosyaları bu kapanışta tekrar okunmadı veya yeniden hash'lenmedi;ham kaynak baytlarının bugün yeniden tarandığı iddia edilmez. Önceki provenans kayıtları korunur. Kapsam dışı klinik veri dizinleri açılmadı.

## 2. İki açıklama yöntemi ayrı kalır

| Yöntem | Açıklanan çıktı ve referans | Kapsam/toplamsallık sınırı |
| --- | --- | --- |
| B1 exact interventional linear SHAP | Kayıtlı LR logiti;yalnız o modelin uygun train ilaçları background. Beş kimya alanı ve availability maskesi ayrı | Seçilen interventional oyunda base+Σφ=logit. Korelasyona koşullayan veya nedensel açıklama değildir.54 uygun ilaç/protokol;8 abstention için sahte katkı yok |
| A1P1 tekil mesaj maskesi | Δz=orijinal−müdahale logiti. Orijinal degree/rol paydası ve maskeler sabit;PPI çiftinin iki yönü birlikte | SHAP/Shapley değildir. Source protein/rol vePPI yolları ayrı;tekil katkılar ortak biyolojik etki diye toplanmaz |
| A1P1 fiziksel silme duyarlılığı | Aynı Δz ölçeği;ilişki/kenar çıkarılır,kalan payda ve gerekirse rol availability maskesi güncellenir | Sabit-payda maskesiyle aynı müdahale değildir;sonuçlara bakarak “daha iyi yöntem” seçilmedi |

Bütün açıklamalar kendi fold modelinin fit edilmiş PT başlığına bağlıdır. Bulunmayan PT birleştirilmedi veya doldurulmadı. B1'de ek global özet yalnız önceden belirlenen beş-fold ortak PT kesişimidir;graf özetleri native context/PT kapsamındadır. SIDER unknown doğrulanmış biyolojik negatif değildir. İki yöntemin sayıları model davranışını betimler;klinik bireysel yan etki riski,kalibrasyon,nedensellik veya hasta güvenliği kanıtı değildir.

## 3. Test kayıtları ve model çıktısına geri bağlantı

Önceki10 sentetik+16 gerçek-model graf testinin logları/hash'leri korundu. Kapanışta aynı26 test yeni log dosyalarında yeniden geçti. B1'in18 testi de tekrar geçti;toplam44/44. Fit/optimizer/backward için çalışan engeller altında yeniden doğrulama yapıldı;yasak çağrı0. Eski test logları ezilmedi.

'''+table(tests[['module','passed','seconds','old_log_overwritten']])+'''

On kayıtlı A1P1 dış modeli yüklenerek bütün **35.974 orijinal ilaç–PT logiti** `original_outputs.csv` ile karşılaştırıldı;en büyük fark8,882×10⁻¹⁶. Bu yeni performans hesabı veya model seçimi değildir. Önceki testler OOF sigmoid skorlarını da dondurulmuş toleransta doğruladı.

Katkı değerlerini görmeden,kimlik sırasına göre her bağlamda her rolün ilk mevcut ilişkisi veilk mevcut query–PPI çifti seçildi;aynı50 anahtar iki yöntemde kontrol edildi. **100 mevcut müdahalenin29.560 PT kaydı** kayıtlı modelden yeniden hesaplandı. Kaydedilmiş müdahale logiti/Δz ile en büyük fark1,649×10⁻⁷;önceden kabul edilmiş10⁻⁵ logit toleransının altındadır. Model,orijinal graph/query/cache digest'leri değişmedi. Bütün2.440.976 müdahale çıktısının forward'ı yeniden çalıştırılmış gibi sunulmaz;tam dosya taraması aşağıdaki kaynak/cebir/tekillik denetimidir.

## 4. Tam katkı CSV denetimi ve kaynak kimlikleri

Sıkıştırılmış CSV'ler50.000 satırlık parçalarla okundu. Her kaydın orijinal logiti kayıtlı referans tabloya bağlandı;`orijinal−müdahale=Δz` kimliği kontrol edildi. Her source drug–protein–rol WP05 kaynak tablosuyla;her PPI endpoint/çift WP06 strict aynı-taxID insan STRING700 kaynağıyla eşleşti. Her query–PPI çiftinin tek katmanda readout'a ulaşan gerçek bir hesap yolu olduğu doğrulandı. K12/MG1655/context80 eklenmedi.

Her bir **8.358 context–ilaç–ilişki–yöntem anahtarında** native fit-CUI sözlüğü tam ve tekildir;duplicate veya eksik/fold dışı CUI yoktur. Her müdahalenin signed/mutlak ortalama,maksimum ve sıfıra yakın sayısı tam CSV'den tekrar türetilip mevcut `intervention_summary.csv` ile karşılaştırıldı;en büyük özet farkı1,980×10⁻⁷'dir. Kaydedilmiş özetler yeniden yazılmadı.

'''+table(streams)+'''

CSV round-trip farkları float32/decimal yazım sınırındadır:orijinal logit karşılaştırmasında2,331×10⁻⁷,Δz cebirinde4,700×10⁻⁷. Bunlar veri/kimlik değişikliği değildir ve önceden kabul edilmiş toleransın içindedir.

## 5. NA ile gerçek sıfır katkı korunur

Her protokolde62 envanter/61 skor/60 protein rolü/51 query-PPI yolu aynen kalır. Methenamine abstention,Tobramycin protein eksikliği,54/8 yapıQC;62/1061/6416 kaynak kapsamı değişmez. Fit edilmeyen C0027497 başlığı primary outer3 ve stres outer5 için NA kalır. Ana paired54'te1.685 kapsam dışı kaynak pozitif sınırlaması devam eder.

Eksik rol,PPI yolu olmayan protein veya unseen/self-only protein için NA kayıtları doğrudan kaynak NPZ kimliklerinden yeniden türetildi;önceki NA tablolarıyla tam eşleşti:

'''+table(na)+'''

Ölçülmüş sonlu katkı tablolarında NA satırı0 olması eksik yol olmadığı anlamına gelmez:eksik yollar ayrı NA dosyalarında tutulur. Mevcut,uygulanabilir PPI kenarlarında **48 tam sıfır** ve bunlar dahil **56 adet |Δz|≤10⁻⁷** kaydı aynen korundu. Bunlara eksik yol eklenmedi. Erythromycin'de olmayan carrier veya incident PPI yolu,sıfır katkı diye uydurulmadı.

## 6. Notebook,gerçek ağ vealtı görsel aynı veriye bağlı

İki kabul edilmiş notebook şeması,çalıştırılmış hücreleri ve hata çıktısı yokluğu kontrol edildi:B1'de8,graf notebook'unda9 kod hücresi;graf notebook'unda6 gömülü PNG vardır. Gerçek ağ JSON'undaki her düğüm/typed rol/PPI kimliği,source bundle ve tam katkı CSV'siyle karşılaştırıldı;örnek CSV'nin aynı değerleri taşıdığı doğrulandı:

'''+table(network)+'''

Doxycycline çizimi4 rol/35 PPI,Erythromycin çizimi11 rol/85 PPI kenarı taşır;ikisi de33 protein düğümü içerir. Bu sayılar keyfi en büyük katkı seçimi değil,önceden belirlenmiş ilaçların gerçek hesap yollarıdır.

Kabul edilmiş graf notebook'unun mevcut veri/çizim kodu,bütün dosya yazımları yeni kapanış QA alanına yönlendirilerek tekrar çalıştırıldı. **Altı PNG'nin tamamı ve notebook'un altı gömülü görüntüsü piksel düzeyinde aynıdır**;yeniden çizilen PNG SHA-256 değerleri de orijinalleriyle eşleşir. Orijinal notebook veya şekiller yazılmadı. Böylece yalnız görsel dosyasının varlığı değil,saklanan gerçek verilerden aynı görüntünün üretildiği gösterildi.

'''+table(images[['figure','differing_pixels','embedded_differing_pixels']])+'''

## 7. Kabul edilmiş performans sonuçları değişmedi

Bu değerler mevcut metric CSV'lerinden okunan sabit referanslardır;yeniden eğitim,evaluation,CI veya sonuç seçimi yapılmadı:

'''+table(pd.DataFrame(perf)[['WP','model','accepted_drug_macro_AP']])+'''

PPI gerçekten hesaplanıyor/öğreniliyor teknik sonucu korunur;ek birincil performans katkısı gösterildiği söylenmez. Protein biyolojisinin genel yararsızlığı çıkarılamaz. WP10 atom dalının küçük koşullu katkısı,PPI üstünlüğünün veB0/B1 üstünlüğünün gösterilememesi değişmedi. B1–GNN farkı tek başına PPI topolojisine bağlanamaz. Açıklama sayılarının varlığı veya büyüklüğü bu sonuçları tersine çevirmez. KoşulluCI'lar dış doğrulama/genel üstünlük kanıtı değildir.

## 8. Kanıtlar,teknik geçmiş ve durma koşulu

Yeni kanıt dizini `reports/qa/WP11/final_closure_v1/`dir. `prior_artifacts_sha256.json`,manifest/model denetim CSV'leri,tam müdahale-anahtar denetimi,source NA kontrolü,yeni test logları,replay kayıtları,network/image tutarlılığı ve yönlendirilmiş görsel kopyaları bulunur. `closure_checks.json` nihai denetim sonucunu;`evidence_manifest.json` kapanış kanıtlarının hash'lerini saklar. `notebooks/WP11_final_closure.ipynb` çalıştırılmış Türkçe kapanış incelemesidir.

Önceki graf çalışmasında attribution üretmeden duran hash-yardımcısı tür hatasının traceback'i ve boş kısmi dosyaları eski `attempt_01_technical_failure/` arşivinde aynen korundu. Bu kapanışta başarısız deney kaldırılmadı veya eski protokol yeniden ayarlanmadı. Ham XML/STRING bugün yeniden hash'lenmedi;tam müdahale forward'ı yalnız dondurulmuş100 eski kayıt için tekrarlandı. Bu sınırlar doğrulanmış kapsamın parçasıdır.

`run_status.md` kapanış ilerlemesi için güncellendi;önceki tam baytları QA'da arşivlendi ve güncel dosyanın devamında aynen tutuldu. Diğer kabul edilmiş dosyalar değişmedi. Aktif ROADMAP/AGENTS düzenlenmedi.

WP12'nin yalnız aktif yol haritasındaki kapsamı `reports/WP12_PREPARATION_DECISION.md` içinde incelendi:yalnız kullanıcı seçimi prospektüs PDF'leri,sayfa kaynaklı bilgi çıkarımı,küçük yerel LLM;`reported_in_PDF` ile model tahmin/açıklamasının ayrılması. PDF açılmadı/indirilmedi,parser kurulmadı,Ollama/model indirilmedi veya başlatılmadı. Yeni klinik veri kaynağı eklenmedi.

**Son durum:WP11 kabul edilmiş iki açıklama aşamasıyla nihai olarak kapandı. WP12 uygulamasına geçilmedi. Hazırlık kararları ve kullanıcı onayı beklenerek duruldu.**
'''
    target.write_text(content,encoding='utf-8')
    parts=[('md','''# WP11 · Nihai kapanış denetimi

08.11.2026. Kullanıcı B1 SHAP ve protein/PPI açıklamasını araştırma kapsamında kabul etti. Bu notebook mevcut sonuçları değiştirmeden yapılan kapanış kanıtlarını gösterir. Yeni eğitim veya açıklama yöntemi yoktur. WP12 yalnız hazırlık notudur.

**Yöntemler ayrı:** B1 exact linear SHAP,train background'ına göre logit paylaştırır;A1P1 tekil mesaj maskesi/silme ise Δz duyarlılığıdır. İkisi klinik risk/nedensellik kanıtı değildir. Unknown gerçek biyolojik negatif değildir.'''),('code',INIT+r'''
C=ROOT/'reports/qa/WP11/final_closure_v1'
display(pd.read_csv(C/'manifest_checks.csv'))
models=pd.read_csv(C/'model_integrity_all742.csv');display(models.groupby('model_group').size().rename('ağırlık_metadata_çifti').reset_index())
'''),('md','''**Yorum:**8 manifest ve742 kayıtlı ağırlık–metadata çifti doğrulandı.3139 önceki kabul edilmiş dosyanın hash'i değişmedi. Eski mutable run_status için doğru arşiv kullanılır;diğer dosyalar güncel halleriyle karşılaştırılır. Büyük ham XML/STRING tekrar taranmadı.'''),('code',r'''
display(pd.read_csv(C/'tests_rerun_summary.csv'))
display(pd.read_csv(C/'original_model_output_replay.csv'))
display(pd.DataFrame([json.loads((C/'replay_complete.json').read_text(encoding='utf-8'))]).T)
'''),('md','''**Yorum:**26 graf testi ve18 B1 testi yeni loglarda geçti.35974 orijinal logit kaydı veönceden kimlikle seçilmiş100 mevcut müdahalenin29560 PT kaydı kayıtlı modelden doğrulandı. Bu yeni model/performans veya bütün2440976 müdahaleyi forward ile yeniden üretme iddiası değildir. Fit/optimizer/backward çağrısı0.'''),('code',r'''
display(pd.read_csv(C/'contribution_stream_checks.csv'))
keys=pd.read_csv(C/'all_intervention_key_checks.csv');display(keys.groupby(['kind','mode']).agg(müdahale=('PT_count','size'),PT_satırı=('PT_count','sum'),max_özet_farkı=('summary_max_error','max')).reset_index())
display(pd.read_csv(C/'NA_source_consistency.csv'))
display(pd.read_csv(C/'network_data_consistency.csv'))
'''),('md','''**Yorum:**Tam CSV taramasında her ilaç–PT–source ilişki anahtarı,orijinal logit veΔz cebiri doğrulandı.8358 müdahale her native PT'yi tam bir kez içerir;eksik/fold dışı CUI doldurulmaz.48 gerçek sıfır PPI katkısı korunur;eksik yollar ayrı NA tablosunda kalır. Gerçek ağ JSON'u hem tam hem örnek CSV ile uyumludur.'''),('code',r'''
display(pd.read_csv(C/'image_data_checks.csv')[['figure','differing_pixels','embedded_differing_pixels']])
from IPython.display import Image
for filename in pd.read_csv(C/'image_data_checks.csv').figure:
    print(filename)
    display(Image(filename=str(ROOT/'reports/figures/WP11/graph_v1'/filename)))
'''),('md','''**Görsel yorumu:**İlk grafik mevcut/eksik yolu ayırır. İki gerçek ağ,Doxycycline veErythromycin'in önceden seçilmiş fold/CUI kayıtlarını gösterir;yerleşim biyolojik mesafe değildir. Dağılım grafiği düşük katkıları saklamaz;maske–silme grafiği farklı normalizasyon sorularını ayırır;sayısal kararlılık grafiği klinik kararlılık veyaCI değildir. Altı orijinal PNG ve kabul edilmiş notebook'un gömülü görüntüleri yeniden çizimle piksel eşleşir;öncekilere yazılmadı.'''),('code',r'''
display(pd.read_csv(C/'accepted_performance_unchanged.csv')[['WP','model','accepted_drug_macro_AP','recomputed']])
'''),('md','''**Yorum:**Bunlar değişmeyen mevcut observed-record proxy AP değerleridir. PPI'nin hesaplandığı teknik olarak gösterildi;ek birincil başarı gösterilmedi. Protein biyolojisinin yararsızlığı çıkarılamaz. WP10 atom katkısı küçük/koşulludur;B0/B1 üstünlüğü gösterilmedi. Bu kapanış yeniAP/CI hesaplamadı.'''),('code',r'''
display(pd.DataFrame([{'WP11':'Kullanıcı kabulüyle nihai kapandı','WP12':'Yalnız aktif ROADMAP kapsam/karar notu','PDF işleme':'Başlamadı','Ollama/LLM kurulumu':'Yapılmadı','yeni eğitim':'Yok'}]).T)
print('Kapanış raporu:',ROOT/'reports/WP11_FINAL_CLOSURE.md')
print('WP12 hazırlık:',ROOT/'reports/WP12_PREPARATION_DECISION.md')
'''),('md','''**Durma koşulu:**WP12 için kullanıcı seçimi PDF'ler,belge–ilaç kimliği,sayfa/alıntı şeması ve küçük yerelLLM koşulları açık karar olarak kalır. PDF'de bildirilen yan etki model girdisine dönüştürülmez;LLM sayısal katkı/yan etki tahmini üretmez. WP12 uygulanmadı;burada duruldu.''')]
    execute('WP11_final_closure.ipynb',parts)
    print('Closure report + executed notebook created;accepted reports untouched')


if __name__=='__main__':main()
