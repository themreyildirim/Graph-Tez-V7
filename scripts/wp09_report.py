"""WP09 tasarım/veri sözleşmesi ve açık eğitim kapısı; mevcut QA'dan rapor."""
import json,re
import pandas as pd
from wp09_data import ROOT,QA,preserve,sha


def table(frame):
    def cell(x):
        if isinstance(x,float):return 'NA' if pd.isna(x) else f'{x:.4f}'
        return str(x).replace('|','/')
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join(
        '| '+' | '.join(cell(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None))


def main():
    preserved=preserve();top=pd.read_csv(QA/'fold_ppi_topology.csv');quality=pd.read_csv(QA/'shuffle_quality.csv')
    cov=pd.read_csv(QA/'outer_test_PPI_coverage_all62.csv')
    summary=top.groupby(['protocol','threshold']).agg(human_min=('strict_human_nodes','min'),human_max=('strict_human_nodes','max'),
        message_min=('human_PPI_message_nodes','min'),message_max=('human_PPI_message_nodes','max'),
        isolates_max=('human_isolates','max'),edges_min=('undirected_pairs','min'),edges_max=('undirected_pairs','max')).reset_index()
    null=quality.groupby('threshold').agg(scenarios=('context','count'),accepted=('status',lambda s:int(s.eq('OK_degree_preserving_null').sum())),
        changed_min=('changed_fraction','min'),changed_max=('changed_fraction','max')).reset_index()
    text=(QA/'test_results.txt').read_text(encoding='utf-8');match=re.search(r'Ran (\d+) tests in ([\d.]+)s',text)
    assert match and match.group(1)=='35' and text.rstrip().endswith('OK')
    failures700=quality[quality.threshold.eq(700)&quality.status.ne('OK_degree_preserving_null')]
    proposal=json.loads((ROOT/'configs/WP09_training_PROPOSED_v2.json').read_text(encoding='utf-8'))
    contract='''# WP09 — Tasarım veri sözleşmesi v1

06.11.2026. Durum: **encoder doğrulama girdisi; gerçek eğitim onayı yok**. Kaynaklar mevcut WP04 clean kimya, WP05 56 dizi özelliği ve dört rol, WP06 kesin insan PPI, WP07 input maskeleri, WP08 frozen split/eligibility/train-fit istatistikleridir. Kaynak XML/STRING tekrar ayrıştırılmaz. Feature/scaler üretimi tekrarlanmaz. B0/PT frekansı veya etiket yoğunluğu encoder girdisi değildir.

## Ayrı train ve query dosyaları

`reports/qa/WP09/design_v1/folds/{context}_train.npz` yalnız train drug düğümlerini ve bunlara bağlı dizi-özellikli protein accession'larını taşır. `{context}_query.npz`, validation/test ilaçlarını ayrı tutar. İki dosya NumPy `allow_pickle=False` ile açılır; WP07/WP08 `.pt` yüklenmez. Eğitim grafına query drug, SE/PT düğümü, hedef etiketi, ileri/ters heldout bağlantısı eklenmez.

| Train alanı | Tür/şekil | Anlam |
| --- | --- | --- |
| drug_ids | Unicode[D] | Kanonik primary ID; yalnız join/indeks, sayısal özellik değil |
| protein_ids | Unicode[N] | Yalnız train-linked accession; context yok |
| protein_x | float64[N,56] | WP05 ham özelliğin mevcut train-fitted mean/scale ile dönüşümü |
| chemistry | float64[D,5] | MW/LogP/HBD/HBA/TPSA, aynı mevcut train standardizasyonu |
| masks | bool[D,5] | Kimya,target,enzyme,transporter,carrier kullanılabilirliği |
| eligible | bool[D] | Herhangi girdi dalı var mı; frozen B2 kuralıyla aynı |
| role_target/enzyme/transporter/carrier | int64[2,E_role] | İlk sıra drug indeksi, ikinci protein indeksi; dört ayrı tip |
| ppi_pairs_400/700/900 | int64[2,E] | Kanonik i<j yönsüz çiftler; hepsi aynı-taxID insan, filtre skoru eşik üstü |

PPI forward için her çift iki yönlü edge_index sütununa açılır. Kaynak `combined_score` yalnız filtre/provenans için kullanılır; protein özelliği veya mesaj ağırlığı değildir. Kaynak satır/alias kanıtları WP06 dosyalarında hash ile korunur. İzole insan ve strict-insan dışında kalan doğrulanmış dizi proteinleri self/residual yolunda tutulur.

Query paketi aynı drug/kimya/maske/rol alanlarına ek `split`, `unseen_protein_ids`, `unseen_protein_x` içerir; PPI kenarı taşımaz. Query rol indeksi, train protein cache'i ardından sıralı unseen accession listesine başvurur. Train evreni dışındaki doğrulanmış query proteinleri aynı train-fitted scaler ve shared self encoder ile komşusuz işlenir. Query'den train cache'ine geri mesaj veya query'ler arasında yeniden-fit/batchnorm yoktur. Query ortak kaynak proteinine readout erişimi olması tek başına hedef sızıntısı değildir; heldout ilaç bağlantısı eğitim grafını genişletemez.

Eksik kimya standart nötr blok+maske ile tutulur; bu biyolojik sıfır değildir. Özelliksiz protein/context için sıfır vektör üretilmez. Tüm girdi yoksa `eligible=False`; isteğe bağlı başlık kullanılırsa logits NA, önsel fallback yok. Methenamine böyle korunur. Tobramycin kimya dalıyla kalır; sekiz molekül QC kararı değiştirilmez.

## Ablation ve hedef sözlüğü sınırı

G_noPPI/G_realPPI/G_shuffledPPI aynı projection/self/readout/kimya mimarisidir. Shuffled çağrısı açık null kenarları ister; yoksa hata verir, gerçek kenarları sessizce kullanmaz. Başarısız null için dosyada o eşik anahtarı yoktur ve QA'da NA yazılıdır.

Gerçek veri doğrulamasında PT başlığı kurulmaz. İleride onayla kurulursa K, mevcut her ilgili train B2 sözlüğü ve train-fittable maskesinden gelir; ≥5 pozitif kullanılabilir ilaç/≥2 grup. Train'de tek proxy sonuçlu hedef NA; unknown gerçek negatif değildir. Eski paired54'ün aynı scored drug/fold/PT anahtarları ve B0/B1/B2 sabit skorları korunur. Yeni NA veya kapsam daralması açık gösterilmeden performans kıyası yapılamaz. Kaynak1061 PT sözlüğü başka bir şeydir; graf girdisi değildir.

Sürüm/hash: `input_manifest.json`, `prepared_artifact_manifest.json`, `shuffled_artifact_manifest.json`, önceki çıktı manifestleri ve kapanış doğrulaması. Farklı library sürümlerinde bit düzeyinde genel yeniden üretim garantisi yoktur. İlaç/feature mutation testleri train kaynak sınırını doğrular; bu, henüz yazılmamış trainer'ın uçtan uca doğrulaması yerine geçmez.
'''
    (ROOT/'docs/plan/WP09_DESIGN_DATA_CONTRACT_v1.md').write_text(contract,encoding='utf-8')
    decisions=pd.DataFrame([
        ('PPI primary eşik','700 önerilir; approved=None','400/700 outer erişim51/62; null0/40 vs39/40; performans seçimi yok'),
        ('Duyarlılık eşikleri','400 ve900 ayrı; tüm girdiler hazır','Hiçbiri nihai en iyi eşik diye seçilmedi'),
        ('Protein/query evreni','Train-linked dizi; unseen query self-only','Harici full63/context genişlemesi yok; izoleler korunur'),
        ('Kapasite','56→32 projection, tek residual mean PPI; kimya5→8; dört mean rol','Head hariç3920; temsil141; lineer train PT head142K parametre'),
        ('Loss','BCEWithLogitsLoss; eligible drug ve valid train target üzerinde ortalama','Unknown0 yalnız observed-record proxy; class/pos weight yok; train single outcome NA'),
        ('Optimizer / LR','AdamW; lr=0.001; weight_decay=0.001','Hiç optimizer kurulmadı/adım atılmadı; yeni grid yok'),
        ('Epoch / early stop','Max200; inner validation drug-AP; patience20; min_delta0.0001','En iyi epoch, tie erken; outer epoch geçerli inner epoch yuvarlanmış medyanı'),
        ('Inner NA / seçim','En az2 geçerli inner fold; daha azsa outer NA','Her aday aynı inner hedef kapsamı; outer test karar vermez'),
        ('Seed / init','Base20261106 +10000*protocol_index +100*outer +inner','CPU1thread/deterministik; ablation aynı initial state; seed araması yok'),
        ('Shuffle','10 swap/edge, max200 attempts/edge; değişim≥0.5','Design1null; gelecek3 null önerisi; seed formülü configte; uniform mixing iddiası yok'),
        ('Null başarısızlığı','NA tutulur; değişim kuralı/seed sonradan iyileştirilmez','700 stress_o02_i02 başarısız; tam ablation kapsamı açık karar gerektirir'),
        ('Karşılaştırma','Frozen B0/B1/B2 + aynı mimari no/real/shuffled','Aynı split/proxy/train PT/input/paired54; performans hesaplanmadı'),
        ('Eğitim onayı','training_enabled=False','Bu belge öneri; kullanıcı onayı olmadan trainer/performans başlatılmaz')
    ],columns=['karar','öneri','gerekçe_ve_sınır'])
    csv_write=__import__('wp09_data').csv_write;csv_write(QA/'pretraining_decision_table.csv',decisions)
    gate=f'''# WP09 — Eğitim öncesi karar kapısı

06.11.2026. **Tasarım ve encoder doğrulaması tamamlandı; eğitim/performans onayı bekleniyor.** Kullanıcı bu aşamada yalnız tasarım/girdi/encoder testlerini onayladı. Mevcut eğitilmiş B0/B1/B2 referanslarına dokunulmadı.

{table(decisions)}

## Eşik önerisinin sürüm geçmişi

`configs/WP09_training_PROPOSED_v1.json` null çalıştırılmadan önce yazılan kapsam-öncelikli400 taslağını saklar. Etiketten bağımsız topoloji/null sonuçları incelendikten sonra **ayrı v2** oluşturuldu: öneri700, approved=None. V1 veya ilk analizin kayıtları ezilmedi. Revizyon hiçbir AP/AUROC veya test etiketi görerek yapılmadı; bu aşamada performans hesaplanmadı.

400'de 0/40,700'de39/40,900'de32/40 null kabul edildi. 400 ve700 ana/stres outer testte51/62 ilaç erişimini korur;900 ana44/stres46. İnsan protein mesaj kapsamı700'de400'e göre azalır; aynı ilaç erişimi bütün protein komşuluklarının aynı olduğu anlamına gelmez. **700 en iyi tahmin eşiği değildir; fizibilite dengesi için öneridir.**

700'de yetersiz null:

{table(failures700[['context','edges','successful_swaps','changed_fraction','status']])}

Bu başarısızlık sessizce gerçek kenar, başka seed veya gevşetilmiş değişim kuralıyla doldurulmadı. 49 yetersiz adayın tamamı NA'dır. Degree korunması null'un yeterince farklı veya uniform örneklenmiş olduğunu kanıtlamaz. Gerekli üst sınır hesabı hiçbirinde≥%50 değişimi matematiksel olarak dışlamadı; başarısızlık imkânsızlık kanıtı değildir.

**Eğitimden önce açık karar:** mevcut kural ve eksik-null kapsamını kabul etmek veya etiketten bağımsız yeni bir null politikasını ayrı sürümle incelemek. İkinci seçenek seçilirse önce policy yazılır; iyi performans veren karışım/eşik seçilmez. Yeni null politikasının incelenmesi de bugün otomatik başlatılmadı.

## Onaylanacak somut öneri

Güncel öneri `configs/WP09_training_PROPOSED_v2.json`; protein/query sözleşmesi `docs/plan/WP09_DESIGN_DATA_CONTRACT_v1.md`. Eşik, kapasite/loss/optimizer/LR, epoch/inner NA/outer refit, seed/init, null tekrar/başarısızlık politikası birlikte eğitim onayına sunulur. 35 test yazılım mekaniğini doğruladı; tahmin faydası, klinik güvenlik veya dış doğrulama değildir.

Eğitimden sonra aynı-split kıyas keşifseldir: baseline outer sonuçları daha önce görüldü. Outer test seçime/early-stop'a girmez. Pooled class-AUROC ile fold içi tanı ayrılır; koşullu grup CI bağımsız dış doğrulama sayılmaz. WP08'deki1685 kapsam dışı kaynak pozitif ve tüm1061 PT için iddia sınırı korunur.

**Gerçek GNN eğitimi veya performans karşılaştırması yapılmadı. Kullanıcı eğitim onayı bekleniyor.**
'''
    (ROOT/'reports/WP09_PRETRAINING_DECISION_GATE.md').write_text(gate,encoding='utf-8')
    report=f'''# WP09 — PPI tasarımı, gerçek fold girdileri ve encoder doğrulaması

06.11.2026. **DESIGN_AND_ENCODER_VALIDATION_COMPLETE; AWAITING_SEPARATE_TRAINING_APPROVAL.** Kullanıcı WP08 ilk faz kapanışını kabul etti; bu WP09 aşamasında yalnız tasarım/girdi/encoder doğrulaması yetkilendirildi. GNN fit, optimizer adımı, gerçek PT skoru, AP/AUROC veya ablation performans sonucu üretilmedi.

## 1. Öğrenilen kavram ve kurulan mimari

Protein özelliklerini bağımsız MLP'den geçirmek PPI kullanmak değildir. Yeni modül, önce56 dizi özelliğini32 boyutlu paylaşılan projection'a taşır; ardından **tek residual mean-message katmanı** gerçek PPI edge_index komşularını işler. Dört DrugBank rolü ayrı mean readout alır; maskeli5 kimya özelliği8 boyutlu dalda işlenir. Temsil141 boyut; head hariç3920 parametre, ileride train K PT başlığı142K ek parametre. Gerçek veri probe'unda head yoktur. G_noPPI/G_realPPI/G_shuffledPPI aynı modüllerdir; noPPI gerçekten komşu kenarlarını kaldırır, shuffled açık null kenarları olmadan çağrılamaz.

`z_i=ReLU(Px_i)`, `h_i=z_i+ReLU(Sz_i+M·mean(z_j, j∈N(i)))`. Boş komşulukta mean0; message bias yok. İzole ve insan PPI kapsamı dışındaki dizi proteinleri self/residual yoldadır. Bu encoder, atom grafı/moleküler GNN veya eğitilmiş GiG modeli değildir. Aynı toplam parametre sayısı, noPPI'da kullanılmayan mesaj yolunu aktif hale getirmez; PPI etkisi ileride aynı mimarinin ablation'ıyla sınanacaktır.

![Küçük mimari](figures/WP09/design_v1/07_small_architecture.png)

**Yorum:** Kaynak dizi/protein komşuluğu, dört rol ve kimya dalları farklı bilgi taşır. Az sayıda train ilaçta bu kapasitenin bile overfit riski vardır; projection/katman boyutları başarı garantisi değildir.

## 2. Kaynaklar, koruma ve gerçek fold hazırlığı

AGENTS, aktif ROADMAP, WP05–WP08 raporları, WP08_FINAL_CONCLUSIONS ve önceki WP09 taslağı okundu. Eski raporlardaki bekleyen kararlar tarihsel aşamalardır; son kullanıcı onayı yalnız bugünkü kapsamı açar. DrugBank5.1/export2026-01-04, STRINGv12.0, mevcut PubChem/RDKit QC ve SIDER4.1 kaynak zinciri korunur. Analiz yalnız mevcut küçük proje QA'sını okur; ham büyük kaynak taraması, API/indirme/kurulum yoktur.

**{preserved} önceki dosya** (önceki WP09 taslağı/ön kontrolü dahil) SHA-256 ile korundu. WP08 modelleri/splitleri/C/seed/skorları/QA,62 ID,1061 kaynak PT,6416 kaynak pozitif, sekiz molekül QC ve Tobramycin/Methenamine protein eksiği değiştirilmedi. B0/B1/B2 yeniden fit edilmedi. Kapanış manifestleri bu aşamada koruma ile doğrulandı; eski111 test yeniden çalışmış sayılmıyor.

Ana connectivity ve ayrı scaffold OR≥0,8 stres protokollerinin her birinde5 dış ve3 iç fold vardır: toplam40 fit bağlamı. **80 yeni NPZ** train/query paketi mevcut kaynak tablolardan kuruldu. WP07 inceleme `.pt` veya WP08 `.pt` yüklenmedi/dönüştürülmedi. Ölçekler yeniden fit edilmedi; WP08'in context'e özgü train-only kaynak mean/scale değerleri aynen kullanıldı. Protein evreni yalnız train-linked, dizi özellikli accession'dır; query ilaçları ve PT hedefleri train grafında yoktur.

Tam anahtar/shape/missingness kuralları [tasarım veri sözleşmesinde](../docs/plan/WP09_DESIGN_DATA_CONTRACT_v1.md) tanımlıdır. Her rol,mask/edge uyuşması, finite56/5 alan ve integer indeks sınırı test edilir. ID/taxID yalnız kimlik/provenans, numeric input değildir. PT sayısı,kategori,raporlama sıklığı,kalite_skoru ve STRING skoru protein girdisine girmez.

## 3. Gerçek PPI mesaj kapsamı ve izolasyon

Her eşikte yalnız train evrenindeki aynı-taxID insan düğümleri için induced PPI hesaplandı; diğer dizi proteinleri tutuldu. Aşağıdaki min/max, her protokolün bütün20 inner/outer bağlamları üzerindedir; bağımsız deney veya CI değildir.

{table(summary)}

![Fold mesaj kapsamı](figures/WP09/design_v1/01_fold_message_scope.png)

**Yorum:** Kaynak63 insan proteininden ana bağlamlarda37–59,stres35–61 train evrenine düşer. Mesaj alabilen proteinler400'den900'e azalır; izoleler silinmez. Grafik bağlam medyanını, tablo min/max'ı gösterir. Kaynak full63 topolojisini her fold için varsaymak yanlıştır. Kenar varlığı mesaj-geçişi deneyi için gerekçedir; biyolojik/tahmin faydası kanıtı değildir.

Her protein/bağlam/eşik için `protein_message_scope.csv`, derece0 dahil saklanır. `fold_ppi_topology.csv` insan izolesi yanında bütün dizi proteinlerinin no-PPI sayısını, bileşen/en büyük bileşen/density'yi de taşır. 23 K12/MG1655 koşullu PPI ve80 özelliksiz context hiçbir train/null ağına katılmadı. Koşullu E.coli proteinleri doğrulanmış dizileriyle self yolunda kalabilir; kenarları insan ağına taşınmaz.

## 4. İlaçların PPI erişimi — etiket değerlendirmesi değildir

Her ilaç kendi outer testinde bir kez sayılır. Aynı62 korunur; erişim, bağlı kaynak proteinlerinden en az birinin bu foldta gerçek PPI komşusu olup olmadığıdır.

{table(cov[cov.role.eq('ALL')])}

Ana700 rol ayrımı:

{table(cov[cov.protocol.eq('primary')&cov.threshold.eq(700)])}

![İlaç PPI kapsamı](figures/WP09/design_v1/02_drug_PPI_coverage.png)

**Yorum:** 400/700'de51/62 ilaç rol birleşiminde PPI mesajı alabilir. Ana700 target15,enzyme28,transporter43,carrier19; örtüşen sayılar toplanmaz. İnsan ağının erişimi çoğu ilaçta metabolizma/taşıma rolünden gelir;51 ilacı “doğrulanmış antibakteriyel insan hedefli” diye adlandıramayız. 900 ana44/stres46 erişim bırakır. Bu topoloji erişimi, input-eligible61 veya dizi modalitesi60 ile aynı ölçü değildir. PPI'sız protein/ilaçlar elenmedi; Tahmin performansı hesaplanmadı.

Query yeni accession'ı train protein evreninde değilse train-fitted scaler+paylaşılan self encoder kullanılır, komşu eklenmez. Ana outer testlerin85,stres89 unseen ilişkisi toplamı benzersiz yeni protein sayısı değildir: ALL satırlarında ilaç–accession, rol satırlarında ilaç–rol–accession çiftleri sayılır. Query'ler, cache protein embedding'i veya train grafını değiştirmez. Batchnorm ve query'den proteinlere geri mesaj yoktur.

## 5. Ayırt edici forward ve gradient kanıtı

Gerçek56-girişli modülün ilk iki koordinatında kontrollü sabit ağırlık/özellikler kullanıldı: A—B—C ve izoleD. Önce hA=(5,5),hB=(7.5,5),hC=(7,9),hD=(10,10); B–C kaldırılınca B=(7,4),C=(4,8),A/D aynı kaldı. C_x0'ı+2 değiştirmek bir hop B_h0'ı+1, C self yolunu+4 etkiler; A/D değişmez.

{table(pd.read_csv(QA/'synthetic_forward_proof.csv'))}

![Kenarın forward etkisi](figures/WP09/design_v1/03_edge_forward_proof.png)

{table(pd.read_csv(QA/'synthetic_gradient_proof.csv'))}

![Mesaj gradienti](figures/WP09/design_v1/04_message_gradient.png)

**Yorum:** dB_h0/dC_x0=0,5 ve message ağırlığı gradient normu3,3541'dir. Hook/trace testi message katmanının komşu ortalamalarını gerçekten aldığını doğrular. Eski V6'nın sadece PPI tensoru hazırlayıp forward'da kullanmama hatası bu encoder'da giderildi. Bu, eğitilmiş sistemin üstünlüğü değil kontrollü yazılım kanıtıdır; her rastgele kenarın her ağırlıkta tüm çıktıları değiştirmesi beklenmez. Backward yalnız türev testidir; optimizer adımı yoktur.

## 6. Degree-preserving null: geçerli yapı ve başarısızlık ayrımı

Etiket-kör RNG ile iki kenar yeniden bağlanır; düğüm kümesi, her düğümün derece dizisi ve kenar sayısı tam korunur. Self-loop/duplicate reddedilir; real/shuffled edge hash,seed,deneme/swap sayısı ve değiştirilen çift oranı saklanır. Karıştırma insan fold evreni dışına çıkmaz.

İlk kural null öncesi kaydedildi: kenar başına10 başarılı swap, en fazla200 deneme, orijinal çiftlerden çıkarılan pay≥0,5. 120 adaydan71 kabul,49 NA:

{table(null)}

![Null kalite kontrolü](figures/WP09/design_v1/05_shuffle_quality.png)

**Yorum:** Derece korunmuş olsa bile aday yeterince değişmemiş olabilir. 400'ün tüm40 adayı NA,700'ün1,900'ün8 adayı NA'dır. Başarısızlar için ilgili null NPZ anahtarı yazılmadı; gerçek kenar fallback'i veya daha iyi seed araması yapılmadı. Negatif sonuca/NA'ya başarı denmedi. Algorithm bütçesinin başarısızlığı matematiksel imkânsızlık kanıtı değildir: complement/degree kapasitesinden hesaplanan gerekli üst sınırlar hiçbirinde%50 değişimi dışlamadı. Uniform null örnekleme veya mixing kanıtı da yoktur.

![Gerçek ve geçerli null örneği](figures/WP09/design_v1/06_real_vs_shuffled_topology.png)

**Yorum:** Primary outer1/700 aynı58 insan düğümü/173 yönsüz çift; derece korunurken uç bağlantıları değişir. Diğer train dizi düğümleri çizim dışında fakat veri paketinde durur. Aynı koordinatlar karşılaştırma içindir, biyolojik uzaklık değildir. Bu, PPI/no-PPI ablation performansı değildir. Offline HTML'de accession/degree hover vardır; canlı tarayıcı testi yapılmadı.

## 7. Eşik önerisi ve onaysız eğitim konfigürasyonu

Birincil adayım **700**:400 ile aynı outer51/62 ilaç erişimi, daha fazla kabul edilen null (39/40),900'e göre daha az izolasyon. Bu karar yalnız topoloji/null fizibilitesine dayanır; PT etiketi veya performans analize girmedi. Protein düzeyinde400 daha geniştir, bunun bedeli gizlenmedi. 700'ün en iyi predictive eşik olduğu iddia edilmez ve **approved_primary=None** kalır.

İlk kapsam-öncelikli400 taslağı `WP09_training_PROPOSED_v1.json` korunur. Topoloji/null incelemesi sonrası ayrı v2 önerisi ve v1 hash'i yazıldı; sessizce değiştirilmedi.700'de `stress_o02_i02` null oranı0,4857 ile başarısızdır. Bu nedenle eğitimden önce null eksikliği/fallback politikası ayrıca onay gerektirir;49 NA'yı sonradan kabul etmek için kural gevşetilmedi.

AdamW/lr0,001/weight_decay0,001, proxy BCE (class/pos weight yok),max200 epoch,inner AP early-stop patience20/min_delta0,0001 ve outer train epoch'u için geçerli inner epoch medyanı önerilir. Base seed20261106,CPU1thread/deterministik,aynı ablation initial state; model araması yok. Gelecek3 null tekrar politikası öneridir; bugünkü design yalnız1 aday/bağlam/eşik üretir. Tam kararlar [eğitim kapısında](WP09_PRETRAINING_DECISION_GATE.md) ve v2 JSON'dadır. **Bu konfigürasyonla eğitim yapılmadı.**

## 8. Testler, bilimsel sınırlar ve çıktı rehberi

**35/35 test geçti ({match.group(2)} saniye).** Kaynak hash/frozen split/56-feature transform;40 train-query kapsamı;120 gerçek PPI eşitliği;QC/eligibility;dört rol;heldout feature/relation mutation;PT/ters ilişki/taxID/context enjeksiyon reddi;analitik forward/gradient/trace;node permütasyonu;query cache/state izolasyonu;unseen self-only;abstention;gerçeknull derece/count/change/status ve geçersizclique;versioned gate sınandı. Öğrenilmemiş gerçek encoder120 senaryoda finite ve cache değişmezliği verdi; gerçek PT head yoktur.

Geliştirme logları da korundu: ilk turda query ilişkisini silen mutation fixture'ı query QC kontrolüne takıldı; train-only builder yolu ayrılarak izolasyon doğrudan sınandı. İkinci turda başka query'nin çıktısında2,8e-16 düzeyinde CPU yuvarlama farkı exact-zero testiyle takıldı; tolerans1e-12 olarak açıklandı ve seed sabitlendi. Biyolojik kaynak/split/QC kuralı gevşetilmedi. Nihai35 geçiş gerçek tekrar çalıştırmadır; önceki başarısız loglar silinmedi.

Henüz trainer yoktur; gelecekte inner-only seçim,heldout label mutation,end-to-end training sızıntısı ve tam performans ablation yeniden sınanmalıdır. Mevcut encoder testi tek başına gelecek trainer'ın doğruluğunu garanti etmez. Unknown gerçek negatif değildir; ileri performans yalnız observed-record proxy olacak. Klinik risk,nedensellik veya hasta güvenliği iddiası yok. Önceki baseline sonuçları görülmüş olduğundan gelecek same-split kıyaslar keşifseldir. WP08 pooled/fold AUROC ayrımı ve1685 kapsam dışı pozitif/tüm1061 PT sınırı korunur.

| Çıktı | İşlev |
| --- | --- |
| notebooks/WP09_PPI_encoder_design.ipynb | 9 çalıştırılmış kod hücresi, gerçek tablolar,7 PNG ve Türkçe yorum |
| reports/qa/WP09/design_v1/folds/ | 40 train+40 ayrı query kaynaklı NPZ; hedef yok |
| fold_ppi_topology.csv,protein_message_scope.csv | 120 senaryo topolojisi ve protein mesaj/izole durumu |
| drug_ppi_coverage.csv,fold_drug_coverage_summary.csv,outer_test_PPI_coverage_all62.csv | İlaç/rol/split bazlı gerçek mesaj kapsamı |
| shuffle_quality.csv,shuffle_structural_limits.csv,shuffled/ | Null kanıtı,49 NA ve71 kabul edilmiş kenar kümesi |
| synthetic_forward_proof.csv,synthetic_gradient_proof.csv,synthetic_message_trace.json | Analitik örnek, gradient ve message trace |
| real_encoder_shape_checks.csv | Eğitimsiz120 senaryoda shape/finite/query cache kontrolü |
| input/prepared/shuffled manifestleri,prior_outputs manifestleri | Kimlik/kaynak/dönüşüm ve önceki sonuç bütünlüğü |
| docs/plan/WP09_DESIGN_DATA_CONTRACT_v1.md | Yeni train/query ABI ve güvenlik sınırı |
| reports/WP09_PRETRAINING_DECISION_GATE.md,configs/WP09_training_PROPOSED_v2.json | Eğitimden önce onaylanacak somut öneriler |
| scripts/wp09_data.py,wp09_encoder.py,wp09_shuffle.py | Tekrar kullanılabilir veri/encoder/null modülleri |
| scripts/wp09_analysis.py,wp09_decisions.py,wp09_notebook.py,wp09_report.py | Topoloji/kanıt/sürümlü öneri/yürütülmüş raporlama |
| tests/test_wp09.py,test_results.txt | 35 otomatik test; yeni data/model eğitim testi değil |

Yeni kaynak üretimini yeniden çalıştırmak design-v1 tamamlandıysa ezmeyi reddeder. Normal tekrar kontrolü: `python -m unittest discover -s tests -p test_wp09.py -v`; görüntüleme için kayıtlı notebook/QA yeterlidir. Paket kurulumu gerekmedi; mevcut NumPy/pandas/torch/NetworkX/Matplotlib/Plotly kullanıldı. Önceki kaynaklar salt okunur kaldı.

**WP09 tasarım, gerçek veri hazırlığı ve encoder doğrulaması tamamlandı. Gerçek GNN eğitimi ve performans karşılaştırması için ayrı kullanıcı onayı bekleniyor. Sonraki pakete geçilmedi.**
'''
    (ROOT/'reports/WP09.md').write_text(report,encoding='utf-8')
    print(f'WP09 report/data contract/gate written; {preserved} previous files preserved; training not authorized')


if __name__=='__main__':main()
