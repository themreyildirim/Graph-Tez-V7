"""Salt okunur gerçek QA'dan ayrıntılı Türkçe uygulama raporu."""
import json
import pandas as pd
from wp11_graph_policy import ROOT,QA,ROLES,preserve
import wp10_train as old


def table(df):
    def value(v):
        if isinstance(v,float):return f'{v:.6g}'
        return str(v).replace('|','/').replace('\n',' ')
    lines=['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']
    return '\n'.join(lines+['| '+' | '.join(value(v) for v in row)+' |' for row in df.itertuples(index=False,name=None)])


def main():
    target=ROOT/'reports/WP11_GRAPH_EXPLANATIONS.md'
    if target.exists():raise RuntimeError('WP11 graph report already exists')
    preserve();coverage=pd.read_csv(QA/'drug_coverage.csv');desc=pd.read_csv(QA/'descriptive_summary.csv');checks=pd.read_csv(QA/'consistency_checks.csv');stability=pd.read_csv(QA/'stability_checks.csv');local=pd.read_csv(QA/'example_contributions.csv')
    contexts=json.loads((QA/'frozen_contexts.json').read_text());reg=json.loads((ROOT/'reports/qa/WP10/encoder_v1/molecule_registry.json').read_text())
    names=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['id','name']).drop_duplicates().set_index('id')['name'].to_dict()
    rows=[];folds=[]
    for c in contexts:
        g=old.load_bundle(c['context'],'train');q=old.load_bundle(c['context'],'query');d=coverage[coverage.context.eq(c['context'])]
        folds.append({'context':c['context'],'train_protein':len(g['protein_ids']),'insan700_bağ':g['ppi_pairs_700'].shape[1],'test_uygun':len(c['eligible_ids']),'rol_yolu_ilaç':int(d.role_relations.gt(0).sum()),'PPI_yolu_ilaç':int(d.applicable_PPI_pairs.gt(0).sum()),'fit_PT':len(c['fitted_targets'])})
        for i,drug in enumerate(q['drug_ids']):
            a=d[d.drug_id.eq(drug)].iloc[0].to_dict();a.update({'name':names[drug],'chemistry_available':bool(q['masks'][i,0]),'atom_QC_available':reg[drug]['atom_eligible'],'fit_PT':len(c['fitted_targets'])})
            for r in ROLES:a[r+'_links']=int((q['role_'+r][0]==i).sum())
            rows.append(a)
    named=pd.DataFrame(rows);named.to_csv(QA/'all_drug_scope_named.csv',index=False,encoding='utf-8-sig')
    roles=pd.read_csv(QA/'intervention_summary.csv');role_summary=roles[roles.kind.eq('role')&roles['mode'].eq('fixed')].groupby(['protocol','role']).agg(n=('status','size'),mean_native_PT_abs_delta=('mean_abs_delta','mean')).reset_index()
    ery=local[local.drug_id.eq('DB00199')&local.protocol.eq('primary')&local.class_id.eq('C0000731')]
    erythro=ery[ery.kind.eq('role')].pivot(index=['role','protein_id'],columns='mode',values='delta_z').reset_index()
    eryppi=ery[ery.kind.eq('ppi')].sort_values(['protein_a','protein_b','mode']).head(6)[['protein_a','protein_b','mode','delta_z']]
    summarycols=['protocol','kind','mode','interventions','mean_of_native_PT_mean_abs_delta','median_of_native_PT_mean_abs_delta','max_abs_delta_any_PT']
    text='''# WP11 — Protein/PPI graf açıklaması uygulama raporu

07.11.2026. **Graf açıklaması uygulaması tamamlandı; WP11 nihai olarak kapatılmadı. Kullanıcı değerlendirmesi beklenir. WP12 başlamadı.** Bu rapor, kabul edilmiş B1 SHAP raporuna ayrı ektir; `reports/WP11.md` ve bütün B1 SHAP çıktıları aynen korunmuştur.

## Kapsam ve değişmeyen kaynaklar

AGENTS, aktif ROADMAP ve `docs/plan/WP11_A1P1_GRAPH_EXPLANATION_CONTRACT_v1.md` esas alındı. Kayıtlı WP10 A1P1'in connectivity ve ayrı stres protokolündeki beşer dış modeli kullanıldı. Ağırlık, split, train-only dönüşüm, seed, hedef sözlüğü, öğrenme yöntemi veya eğitim sonucu değiştirilmedi. Yeni model eğitimi/optimizer/hiperparametre araması yapılmadı. Ham büyük kaynaklar yeniden taranmadı; yeni biyolojik kaynak veya paket indirilmedi.

Görev başındaki 3.079 kabul edilmiş dosya hash ile korundu; bunlar B1 SHAP tablolarını/notebook'unu ve 1.484 önceki model/metadata dosyasını da kapsar. 62 ilaç,1.061 kaynak PT,6.416 pozitif,54/8 atom QC ayrımı; Methenamine abstention ve Tobramycin protein eksikliği değişmedi. Context80 eklenmedi; K12/MG1655 kenarları insan ağına katılmadı. Protein envanterinde başka organizmaların DrugBank proteinleri kalabilir; PPI kenarları yalnız strict aynı-taxID insan STRING700 kapsamındadır. Her gerçek PPI endpoint/çift kaynağı WP06 izinli eşleme tablosuyla yeniden kontrol edildi.

## Hesaplamadan önce dondurulan yöntem

`reports/qa/WP11/graph_v1/policy_v1.json`, `frozen_contexts.json`, `examples_frozen.csv`, üyelik/kapsam tabloları ve input manifesti **gerçek attribution değerleri görülmeden** kaydedildi. `policy_commit_before_attribution.json` bunların SHA-256 değerlerini bağlar. Önce analitik test kapısı, ardından gerçek model hesabı çalıştırıldı; zaman/hash bağlantısı QA'da saklandı. Yerel kayıt sırası dışarıdan noterlenmiş zaman damgası iddiası değildir.

Her modelin kendi fit edilmiş PT başlıklarının tamamı, yalnız kendi test ilaçları için kullanıldı. Primary/stres ayrı tutuldu; bulunmayan PT birleştirilmedi veya doldurulmadı. Örnekler her bağlamın alfabetik ilk iki uygun test ilacı ve heldout olduğunda Erythromycin DB00199, alfabetik ilk iki fit edilmiş CUI olarak donduruldu:40 örnek. Etiket, AP, doğru/yanlış tahmin veya attribution büyüklüğü seçime girmedi.

Ölçü **Δz = orijinal logit − müdahale sonrası logit**tir. Pozitif/negatif işaret yalnız bu kayıtlı modelin observed-record logitinin sayısal yönünü gösterir. Bu tekil graf mesajı duyarlılığıdır; **SHAP, Shapley değeri, nedensel etki veya klinik risk farkı değildir.** Çoklu yolların, rol maskelerinin ve ReLU'nun etkileri nedeniyle tekil katkılar toplanıp genel biyolojik katkı olarak sunulmaz.

### Birincil: sabit orijinal payda

Protein projection `z_i=ReLU(Px_i)` ve residual güncelleme `h_i=z_i+ReLU(Sz_i+M m_i)` korunur. PPI için `m_i=Σ_j g_ji z_j/max(d_i_original,1)`. Bir kanonik yönsüz çiftin **iki yönlü mesajı birlikte** sıfırlanır; self/residual yol ve düğüm özellikleri değişmez. PPI score düğüm özelliği veya açıklama ağırlığı olarak eklenmez.

Rol için `r_drug,role=Σ_p g_drug,p h_p/n_original` kullanılır. Yalnız bir query–protein–rol terimi sıfırlanır; orijinal role availability maskesi sabit kalır. Target,enzyme,transporter,carrier ayrı tutulur. Bir protein birden çok role bağlıysa ayrı typed ilişki olarak değerlendirilir; protein düğümü veya amino asit özelliği silinmez.

### Ayrı duyarlılık: silme ve yeniden normalizasyon

PPI çiftinin iki yönü yerel edge tensorundan çıkarılır, degree kalan kenarlardan yeniden hesaplanır. Rol ilişkisi kaldırılır ve kalan rol sayısına bölünür; son ilişki kaldırılırsa rol maskesi de kapanır. Kullanılabilir hiçbir modalite kalmazsa müdahale çıktısı NA olur; fallback üretilmez. Bu olasılık analitik testte doğrulandı; gerçek tekil silmelerde yeni abstention oluşmadı.

Maskeler arasında kimya ve moleküler atom dalı sabittir; 150 boyutlu füzyon/head ağırlıkları değişmez. Bir PPI katmanı bulunduğundan, bir kenar yalnız endpoint'lerinden biri query rol readout'unda kullanılıyorsa bu query'ye hesap yolu taşır. Ulaşmayan kenarlar ölçülmüş sıfır katkı sayılmaz; kapsam dışı/yol yok olarak ayrılır.

### Kaynak graph ve cache güvenliği

Orijinal model,train/query bundle ve train protein cache salt okunur tutuldu. Rol maskesi yalnız ilgili query readout'unda uygulandı; diğer query logitleri değişmedi. PPI maskesi/silmesi yeni yerel kenar/mesaj tensörleriyle **fresh açıklama cache'i** üretti. Ayrı `ExplanationCache`, kaynak graph/model digest'i ve müdahale kimliğini taşır; eski `ProteinCache` digest denetimi atlatılmadı. Kaynak graph dosyasına veya orijinal cache'e yazılmadı.

Train'de bulunmayan query proteinleri mevcut self-only encoder yoluyla kalır; bunlara yeni PPI eklenmedi. Yan etki ilişkileri/etiketleri graph girdisine girmedi. Gerçek test etiketi okunmadı; eski OOF dosyasından yalnız kimlikler ve sayısal skorlar eşitlik kontrolü için kullanıldı. Açıklama hesabı `eval`, `no_grad`, CPU float32, tek thread/deterministik modda yapıldı. Fit, optimizer oluşturma ve backward çağrılarına çalışan engeller konuldu; ihlal sayısı0.

## Analitik kapı ve teknik hata kaydı

Gerçek attribution öncesi **10 sentetik/analitik test** geçti. A–B–C zincirinde B orijinal derecesi2 iken A–B maskesi sonrası kalan C mesajı C/2, fiziksel silmede C/1 olur; elle kurulan örnekte B temsili [7,4] ve [8,6]'dır. Sıfır müdahale,iki yönlü maske,rol sayısı/son ilişki maskesi,ID hizası,indeks permütasyonu,query/cache izolasyonu,tekrar ve noPPI'da etkisiz yol kontrolleri uygulandı. Bu sentetik sayılar gerçek ilaç sonucu değildir.

İlk gerçek deneme attribution satırı üretmeden durdu: `numeric_digest` sözlük beklerken cache tensörü doğrudan verilmişti. Düzeltme tensörü isimli bir sözlük alanında hash'lemek oldu; yöntem,tolerans,örnek,model veya kapsam değiştirilmedi. Hata traceback'i,başlangıç kaydı ve iki boş gzip dosyası `attempt_01_technical_failure/` altında korundu. Bu ilk teknik başarısızlık gizlenmedi. Düzeltmeden sonraki gerçek çalışma ve16 gerçek-model testi başarılıdır.

## Gerçek fold kapsamı

'''+table(pd.DataFrame(folds))+'''

Her protokolde 62 test envanteri vardır; 61 ilaç skorlanır,60 ilaçta en az bir protein rolü,51 ilaçta query'ye ulaşan PPI yolu vardır. Primary ve stres aynı ilaçları farklı bağlamlarda değerlendirir; toplam124 satır124 bağımsız ilaç değildir. Methenamine skorsuz; Tobramycin protein rolü olmadan diğer girdileriyle korunur. Her protokolde476 typed query–protein ilişkisi vardır. İnsan700 PPI için primary1.623 ve stres1.604 uygulanabilir query–kenar çifti bulunur; aynı kaynak kenarı birden çok query tarafından kullanılabilir.

Her protokolde11 ilacın PPI yolu yoktur; bu klinik “PPI etkisi sıfır” demek değildir. Eksik roller `absent_paths_NA.csv` içinde; protein düzeyindeki train-izolasyon/self-only boşlukları `protein_path_coverage.csv` içindedir. Primary'de182 rol bağlantısı train'de bulunup incident PPI kenarı taşımaz,85'i unseen/self-only'dir;stres sayıları178 ve89'dur. Her iki protokolde209 rol bağlantısı en az bir gerçek train PPI kenarına erişir.

Primary outer3 ve stres outer5 için C0027497 fit edilmemiş başlıktır ve NA kalır. Toplam **35.974 orijinal ilaç–PT logiti** açıklama referansı olarak üretildi. Bütün1.061 kaynak PT'nin kapsandığı iddia edilmez. Ana paired54 değerlendirmedeki1.685 kapsam dışı kaynak pozitif sınırı önceki raporlarla aynen korunur; bu çalışma o ilişkileri geri kazanmaz.

## Gerçek katkı tabloları ve betimsel sonuç

İki yöntem için toplam557.574 rol satırı ve1.883.402 PPI satırı, toplam2.440.976 ölçüm satırı vardır. Bunlar farklı fold/PT/ilaç/ilişki tekrarlarıdır; bağımsız biyolojik örnek sayısı değildir. Tam tablolar gzip CSV'dir; 50.000 satırlık parçalarla doğrulandı. Her katkı orijinal logit,müdahale logiti,Δz,kaynak drug/protein/rol/CUI,context ve yöntemle bağlanır. NA yollar ayrı tutulur; boş hedefe veya bağlantıya sıfır yazılmaz.

Aşağıdaki özet önce **her müdahalenin kendi native fit-PT sözlüğündeki mean |Δz|** değerini,sonra bu skalerlerin ortalama/medyanını verir. Farklı fold PT'leri ortak bir union vektörüne doldurulmaz. Paydalar müdahale sayılarıdır; bu bir bütün hedef evreni global SHAP veya aynı özellik birimiyle biyolojik önem kıyası değildir.

'''+table(desc[summarycols])+'''

Birincil maskede PPI yerel logit duyarlılığı rol ilişkisinden daha küçüktür. Ancak farklı sayıdaki mesajları farklı paydalarla müdahale etmek doğrudan biyolojik önem kıyası değildir. Küçük Δz,sıfır biyolojik etki veya protein bilgisinin yararsızlığı sonucu vermez. Büyük Δz de tahmin doğruluğu/ek AP başarısı kanıtı değildir. Bu çalışma yeni performans tablosu üretmedi; WP09/WP10'daki “PPI ek birincil başarı gösterilmedi” sonucu değişmedi.

Dört rolün birincil sabit-payda kapsamı:

'''+table(role_summary)+'''

Carrier ortalaması bazı diğer rollerden büyük görünse de yalnız22 farklı ilişki/protokol içerir; rol kapsamı,ölçek ve öğrenilmiş head katsayıları farklıdır. Bu bir biyolojik rol sıralaması veya klinik sonuç değildir. Signed değerler tam tabloda bulunur; mutlak özet yön bilgisini taşımaz.

PPI tablosunda iki yöntem/protokol toplamında **48 tam sıfır Δz** ve bunlar dahil **56 adet |Δz|≤10⁻⁷** kaydı korunmuştur. Ham küçük değerler eşiklenip silinmedi;10⁻⁷ yalnız önceden belirlenen raporlama sınıflamasıdır. Rol tablosunda bu eşikte sıfır yoktur. Eksik bağlantı NA'ları bu sayılara dahil değildir. Her uygulanabilir tekil silme gerçek veride sonlu çıktı verdi; başarısız silme sonucu uydurulmadı.

## Erythromycin: önceden belirlenen gerçek local örnek

Erythromycin DB00199,primary outer3'te heldout test ilacıdır. İlk fit CUI C0000731 için orijinal logit−1,768257'dir. Bu örnekte11 rol ilişkisi ve85 incident train PPI kenarı gösterilir. Carrier ilişkisi bulunmadığı için o rolün katkısı NA'dır; sıfır carrier etkisi denmez. Rol değerleri:

'''+table(erythro)+'''

Örneğin Q12809 target ilişkisinde sabit-maskenin−0,304226 değeri ile silmenin+0,147869 değeri farklı soruları yanıtlar: birincisi eski target sayısına bölerek terimi bastırır; ikincisi diğer target'ı yeni paydada yeniden ağırlıklandırır. İşaret farkı gizlenmedi. Bu, proteinin biyolojik koruyuculuğu veya ilaç yan etki mekanizması değildir.

Aynı ilacın alfabetik ilk üç gerçek PPI çiftinin iki yöntem sonucu (büyük katkı seçimi yapılmadı):

'''+table(eryppi)+'''

O43193 için rol açıklaması geçerlidir; mevcut bağlamda incident PPI yolu yoktur. Bu protein için kaynakta bulunmayan PPI kenarı üretilmedi. Doxycycline DB00254 ayrı primary outer1 örneğidir; iki ağ da gerçek girdi ve kaydedilmiş ağırlıklardan gelen sayısal katkılarla çizildi.

## Kararlılık ve gerçek model testleri

Sıfır müdahalede açıklama forward'ı kabul edilmiş encoder logitiyle **tam eşleşti**; yeniden üretilen cache farkı0. Eski kaydedilmiş OOF sigmoid skoruyla en büyük fark5,960×10⁻⁸'dir. Bu, float32 kabul edilmiş tam encoder/önceden kullanılan hızlı forward işlem sırası hassasiyeti sınırında ve önceden dondurulan10⁻⁷ toleransının altındadır; eski skor değiştirilmedi.

Bütün tekil müdahaleler tekrar hesaplandı; tekrar farkı0. Rol maskesi diğer query'lerde fark yaratmadı (en büyük fark0); kaynak model/graph/query/cache digest'leri on bağlamda da aynı kaldı. On bağlamın önceden belirlenen ilk ilişki/ilk PPI kenarı için ilave kararlılık denetimi:

'''+table(stability.groupby('check').max_abs_logit_error.max().reset_index())+'''

En büyük fark1,192×10⁻⁶ logittir;10⁻⁵ toleransının altındadır. Bu testler sabit ağırlıklarda sayısal/kimlik hizası kararlılığını gösterir. Yeniden eğitim,örnekleme belirsizliği,bağımsız dış doğrulama veya klinik kararlılık test edilmedi. Fiziksel silme–maskeleme farkı öncelikle müdahale tanımı farkıdır; aynı açıklama yönteminin tekrar hatası olarak sunulmaz.

Ek30 QA kontrolü, on bağlamda ilk gerçek ilişki/kenarı kullanarak doğrudan Δz'nin de kararlılığını doğruladı (`additional_delta_stability.csv`). Yalnız kenar sırası değişiminde PPI ve rol Δz farkı en çok9,537×10⁻⁷; query tek başına hesaplandığında rol Δz farkı en çok1,550×10⁻⁶'dır. Bu da önceden dondurulmuş10⁻⁵ toleransının altındadır. Bu kontrol seed,model veya maske politikası seçmez.

Δz float32 hesaplanmıştır; CSV yazma/okuma sonrasında `orijinal−müdahale−Δz` kimliği en çok yaklaşık4,7×10⁻⁷ yuvarlama farkı taşır. Açıklama tablolarının decimal gösterimi sonsuz hassasiyet iddiası değildir; ham model ağırlıkları değişmemiştir.

Önce10 sentetik,sonra16 gerçek-model testi: **26/26 geçti**. Gerçek testler train/test ve hedef izolasyonu,kayıtlı OOF eşitliği,rol katkısının lineer head üzerinden bağımsız analitik doğrulaması,orijinal cache korunumu,iki yönlü maske,ID çözümü,62/61 kapsam,NA ayrımı,frozen topoloji kapsamı,dört rol tekilliği,PT doldurmama,tekrar/permutation/tek-query,fitting/optimizer/backward engeli ve teknik hata/sıfır değerlerin korunmasını kapsar.

## Çıktıların işlevi ve yeniden üretim

- `notebooks/WP11_A1P1_graph_explanations.ipynb`:9 çalıştırılmış kod hücresi,gerçek tablolar,analitik örnek ve6 gömülü grafik;her görsel altında Türkçe bilimsel yorum.
- `reports/figures/WP11/graph_v1/01_real_path_coverage.png`:envanter,input,protein vePPI kapsamını ayırır;eksik yolu gizlemeyi önler.
- `02_Doxycycline_real_network.png`, `03_Erythromycin_real_network.png`:gerçek typed ilaç–protein veincident train PPI kenarları;renk signed Δz'dir. İki panelin renk aralıkları ayrıdır;çembersel konumlar yalnız çizimdir,mesafe biyolojik bilgi değildir. İzole düğüm turuncu çerçeveyle NA gösterilir. Hiçbir kenar büyük katkısına göre seçilmedi.
- `04_real_delta_distributions.png`:bütün uygulanabilir birincil maskelerin native-PT ortalama mutlak katkısını gösterir;düşük değerler ve kuyruklar kesilmez.
- `05_mask_vs_deletion.png`:aynı query/ilişki anahtarlarında farklı normalizasyonların etkisini gösterir;“daha iyi açıklayıcı” seçimi yapılmaz.
- `06_numeric_stability.png`:gerçek model tekrar/kimlik/sıra hassasiyeti ve önceden belirlenen sayısal tolerans.
- `role_contributions.csv.gz`, `ppi_contributions.csv.gz`:tam signed local değerler;yaklaşık10,28 ve36,41 MiB. pandas ile `chunksize` kullanılarak açılabilir;dosyanın bütünü belleğe alınmak zorunda değildir.
- `example_contributions.csv`, `real_networks.json`:önceden dondurulmuş gerçek örneklerin tabloları ve çizim kenar/değer provenansı.
- `all_drug_scope_named.csv`, `drug_coverage.csv`, `protein_path_coverage.csv`, `absent_paths_NA.csv`, `target_scope.csv`, `train_PPI_scope.csv`:ilaç isimleri,QC/modalite,kapsam,eksik/uygulanamaz yollar ve kesininsan kenar kaynakları.
- `intervention_summary.csv`, `global_native_context_PT.csv`, `descriptive_summary.csv`, `mask_vs_deletion_sensitivity.csv`:paydaları açık yerel/native-PT özetler. Farklı foldlarda bulunmayan hedefler eklenmez.
- `consistency_checks.csv`, `stability_checks.csv`, `compressed_table_stream_checks.csv`:OOF,cache/kimlik ve tam sıkıştırılmış tablo denetimleri. İki test logu,başlangıç/başarı kapıları veilk hata arşivi kanıt olarak saklanır.

Yeni modüller `wp11_graph_policy.py`, `wp11_graph_forward.py`, `wp11_graph_run.py`, `wp11_graph_summaries.py`, `wp11_graph_stability.py`, `wp11_graph_notebook.py`, `wp11_graph_report.py`, `wp11_graph_validate.py`dir. Önceki encoder/trainer dosyaları değiştirilmedi. Sürümlü gerçek üreticiler var olan sonuçları ezmeyi reddeder. Salt okunur testler `python -m unittest discover -s tests -p test_wp11_graph_synthetic.py -v` ve `python -m unittest discover -s tests -p test_wp11_graph_real.py -v` ile çalıştırılabilir;eski eğitim üreticileri çağrılmaz.

## Bilimsel sınır ve kullanıcı değerlendirmesi

SHAP ile bu tekil graf müdahalesi aynı yöntem değildir. Buradaki referans fiziksel olarak doğrulanmış moleküler/protein müdahalesi değil,model hesabında mesajın bastırılmasıdır. Aynı protein diğer roller veya başka PPI yollarıyla ilişkilidir;modelin ve kaynak evrenin sınırları açıklamada da geçerlidir. Topolojik olmayan kimya/atom girdileri sabit tutulduğundan bu çalışma yeni bir PPI/noPPI performans ablation'ı değildir. Gerçek PPI'nin hesaplandığı/öğrenildiği teknik kanıt ile ek genelleme başarısı ayrıdır;WP09/WP10 referans sonuçları aynen kalır.

Unknown çiftler doğrulanmış biyolojik negatif değildir. SIDER kayıt sıralama logiti,klinik bireysel yan etki olasılığı,nedensellik,kalibrasyon veya hasta güvenliği doğrulaması sayılmaz. Daha büyük veya kararlı attribution bu sınırları kaldırmaz.

`run_status.md` yalnız bu uygulamanın ilerleme durumu için güncellendi; önceki tam baytları hem QA arşivinde hem güncel dosyanın devamında korunur. **Graf açıklaması uygulaması tamamlandı. WP11 nihai olarak kapatılmadı;sonuçların kullanıcı tarafından değerlendirilmesi bekleniyor. WP12'ye geçilmedi.**
'''
    target.write_text(text,encoding='utf-8');print('Report created;accepted B1 report untouched')


if __name__=='__main__':main()
