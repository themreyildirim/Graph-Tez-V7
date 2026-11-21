"""Türkçe ilk deney raporu/model kartı; sonuç okur, yeniden eğitim yapmaz."""
from pathlib import Path
import json,hashlib,re
import pandas as pd
import numpy as np
import nbformat

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP08/baseline_v1'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(frame):
    def fmt(x):
        if x is None or isinstance(x,float) and np.isnan(x) or x=='':return 'NA'
        if isinstance(x,(float,np.floating)):return f'{x:.4f}'
        return str(x).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(frame.columns)+' |','|'+'|'.join(['---']*len(frame.columns))+'|']+
                     ['| '+' | '.join(fmt(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)])


def validate():
    checks={}
    for name in ('prior_outputs_hashes.json','preparation_input_manifest.json','model_artifact_manifest.json'):
        m=json.loads((QA/name).read_text(encoding='utf-8'));bad=[p for p,h in m.items() if sha(ROOT/p)!=h]
        assert not bad,bad;checks[name]={'count':len(m),'changed':bad}
    log=(QA/'test_results.txt').read_text(encoding='utf-8');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',log)
    assert m and m.group(1)=='28' and log.rstrip().endswith('OK')
    checks['tests']={'passed':28,'seconds':float(m.group(2))}
    nb=nbformat.read(ROOT/'notebooks/WP08_baseline_results.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs]
    assert [c.execution_count for c in code]==list(range(1,9))
    assert not any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs)
    assert sum('image/png' in o.get('data',{}) for o in outputs)==6
    fig=ROOT/'reports/figures/WP08/baseline_v1';assert len(list(fig.glob('*.png')))==6
    html=(fig/'per_drug_proxy_AP_interactive.html').read_text(encoding='utf-8');assert not re.search(r'<script[^>]+src\s*=',html,re.I)
    checks['notebook']={'executed_cells':8,'embedded_png':6,'errors':0}
    checks['figures']={'PNG_visually_reviewed':6,'offline_HTML':1,'live_browser_tested':False}
    checks['scope']={'first_LR_baseline_complete':True,'input_files_modified':False,'test_driven_refit':False,'WP09_started':False}
    (QA/'artifact_validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    return checks


def main():
    v=validate();read=lambda n:pd.read_csv(QA/n)
    training=json.loads((QA/'training_complete.json').read_text(encoding='utf-8'))
    env=json.loads((QA/'environment.json').read_text(encoding='utf-8'))
    metrics=read('oof_metrics_with_group_CI.csv');coverage=read('evaluation_coverage.csv');delta=read('paired_B2_minus_B1_group_CI.csv')
    selection=read('selected_C.csv');trace=read('class_fit_trace.csv')
    main_metrics=metrics[metrics.protocol.eq('primary')&metrics.family.eq('PT')&metrics.scope.eq('paired54')]
    ap=metrics[metrics.family.eq('PT')&metrics.metric.eq('drug_macro_AP')]
    hist=metrics[metrics.family.eq('historical30')&metrics.scope.eq('paired54')&metrics.metric.eq('drug_macro_AP')]
    ptcoverage=coverage[coverage.protocol.eq('primary')&coverage.family.eq('PT')]
    card=f'''# WP08 — İlk baseline model kartı

06.11.2026 — Sürüm **WP08-observed-record-L2LR-v1**. Kullanıcı ilk eğitimi açıkça onayladı. Model dosyaları `models/WP08_baseline_v1/`, sonuç QA'sı `reports/qa/WP08/baseline_v1/` altındadır. Bu kart tek tüm-kohort deployment modeli değil, nested CV bileşen model koleksiyonunu açıklar.

## Görev ve doğru çıktı anlamı

Yeni ilaçlarda **SIDER'da gözlenen ilaç–yan etki kayıt ilişkilerinin sıralanması**. `s=1` kayıt var, `s=0` kaynakta kayıt yok. **Unknown doğrulanmış biyolojik negatif değildir.** Sigmoid(w·x+b) yalnız observed-record proxy sıralama skorudur; bireysel klinik yan etki olasılığı, özgüllük veya kalibrasyon iddiası yoktur. Kaynak kayıt olasılığı olarak da kalibrasyon değerlendirmesi yapılmadı. Hasta/olay/payda verisi kullanılmadı.

## Veri ve protokol

- 62 DrugBank ana ilacı envanterde korunur. Kaynak PT ilişkileri 6416 çift / 1061 CUI; nihai fold sözlüğü 1061'in tamamı değildir. Her ilgili train'de en az 5 pozitif kullanılabilir ilaç ve 2 bağımsız grup; historical30 ayrı semantik uyarılı referans.
- Connectivity kilitli 5 dış/3 iç nested CV; Levofloxacin/Ofloxacin aynı grupta. Seed 20261106. Ayrı scaffold OR Tanimoto>=0,8 stres protokolü. Split ve hazırlık SHA-256 değişmedi.
- B1: 5 QC-onaylı kimya+1 input maskesi (6 alan). B2: 5 kimya+4 ayrı rol×56 protein özeti+5 maske (234 alan). Ölçekler yalnız train ilaçları / benzersiz train-linked accession'lardan hazırlanmış kayıtlı dönüşümlerdir.
- Kimlikler yalnız join/provenans; PT/kategori/raporlama skoru/kalite_skoru/combined_score girdisi yok. Eksik blok standart nötr 0+maske, gerçek kimyasal/AA sıfır değil. Sekiz QC kararı korunur; context80/PPI yok. K12 PPI ana ağa alınmadı.

## Öğrenme ve seçim

PT/kategori başına L2 lojistik regresyon, liblinear, `l1_ratio=0`, `class_weight=None`, tol=1e-8, max_iter=10000, intercept açık ve liblinear sentetik intercept scaling=1. sklearn **{env['sklearn']}**, NumPy **{env['numpy']}**, SciPy **{env['scipy']}**, Python **{env['python']}**. CPU threadpool=1.

C grid {{0.1,1,10}}; her outer için yalnız üç inner validation drug-macro observed-label AP'nin eşit fold ağırlıklı ortalaması. Aynı fold içinde bütün C adaylarında aynı ilaç/hedef kapsamı; NA'lar sıfır sayılmaz. Eşitlikte küçük C, tolerans 1e-12. Bütün seçimler outer test scoring'den önce hash'le commit edildi. Tek proxy sonuçlu train sınıfı fit edilmez, fallback olasılık yok. Sonuçlara göre ek fit/özellik/sözlük/seed araması yapılmadı.

400 bundle: 360 inner aday, 40 outer son model koleksiyonu. Toplam 46744 başarılı tek-hedef classifier fit'i, 287 tek proxy sonuç nedeniyle yapılmayan fit (279 inner, 8 outer). Yakınsama/fit hatası yok. Bütün 62 üzerinde ek deployment fit'i yapılmadı.

## Kapsam ve sonuç sınırı

B1 54 ilacı, B2 61 ilacı skorlar. Methenamine her ikisinde abstention; B1 diğer yedi kimya inceleme kaydında da skor vermez. 54 ortak ilaç/ortak train hedefinde ana PT drug-AP B1 **0,6556**, B2 **0,6262**. Complete-case53 aynı modellerin değerlendirme alt kümesidir, yeni eğitilmiş modeller değildir.

Bu ilk deneyde B2 ana drug-AP'yi yükseltmedi; bazı sınıf bazlı ikincil ölçüler farklı yöndedir. Bu, protein biyolojisinin değersizliği veya klinik üstünlük sonucu değildir. Yoğun/sık yan etki etiketlerini sıralamak yüksek drug-AP sağlayabilir; sınıf bazında yeni ilaç ayırt etme ayrı ölçüdür. B0/sıklık önseli bu onay kapsamına eklenmedi; skorlar onun aşıldığını kanıtlamaz.

## Belirsizlik ve kullanım sınırı

1000 yapısal grup bootstrap çekimi; grup üyeleri birlikte, paired B1/B2 aynı çekimlerle. Aralıklar **sabit OOF tahminlerine koşulludur**; tekrar eğitim, hiperparametre seçimi ve dış doğrulama belirsizliğinin tamamını kapsamaz. 62 ilaç daha önce keşfedildi; bu iç doğrulamadır. Foldlar ve ilaç–PT çiftleri bağımsız birimler sayılmadı. Seyrek/ragged sınıflarda hesaplanamayan ölçüler NA ve gerekçesiyle raporlandı. AP trapez PR-AUC değildir.

Klinik karar, tedavi seçimi, kişisel risk, nedensellik veya güvenlik sertifikasyonu için kullanılmaz. Onaylanan amaç tezde kayıt ilişkisi sıralama deneyidir. PPI/gerçek GiG kullanılmadı; WP09 başlamadı.

## İzlenebilirlik

Her bundle `.npz` parametreleri ve `.json` sürüm/kaynak/split hash/C/seed/train ID/özellik-target sözlüğü/dönüşüm fit kimliklerini içerir; pickle gerekmez. `model_artifact_manifest.json` 800 dosyanın hash'ini verir. Test ilacının yalnız etiketsiz hazırlanmış inputu query olarak kullanılır; train-only graf ve fit kaynaklarına eklenmez. [Tam deney raporu](WP08_BASELINE_RESULTS.md).
'''
    (ROOT/'reports/WP08_BASELINE_MODEL_CARD.md').write_text(card,encoding='utf-8')
    text=f'''# WP08 — İlk baseline eğitim ve değerlendirme sonuçları

06.11.2026 — **Onaylı ilk B1/B2 L2-LR deneyleri tamamlandı; kullanıcı sonuç onayı bekleniyor. WP09'a geçilmedi.** Bu ek, protokol/hazırlık raporlarını değiştirmez. Yol haritasındaki tüm ek varyantların tamamlandığı iddia edilmez; ATC, RF/MLP, PPI ve context bu ilk eğitime eklenmedi.

## Ana bulgu

Connectivity kilitli dış 5 / iç 3 nested CV'de ortak **54 ilaç ve ortak train hedefleri** üzerinde PT drug-macro **observed-label AP**: B1 **0,6556** (%95 koşullu grup CI 0,6131–0,6920), B2 **0,6262** (0,5792–0,6701). Paired B2−B1 **−0,0294** (−0,0511–−0,0093). Bu ilk protokolde protein rol özetleri ana sıralama ölçüsünü artırmadı. Sonuca göre C/sözlük/seed/özellikler değiştirilmedi.

**Bunlar klinik bireysel yan etki riskleri değildir.** `s=1` kaynakta gözlenen ilişki, `s=0` kayıt yokluğudur. Unknown doğrulanmış biyolojik negatif sayılmaz. Binary observed-record proxy eğitimi kullanıcı tarafından bu anlamıyla onaylandı; gerçek negatif, klinik özgüllük veya kalibrasyon doğrulaması yapılmadı.

## Sabit girdiler ve önceki çıktıların bütünlüğü

Önceki **{v['prior_outputs_hashes.json']['count']} proje dosyası** ve hazırlık dosyalarının tümü hash ile aynı kaldı. Eski WP00–WP07, önceki WP08 rapor/notebook/testleri, v1 split/eligibility/dönüşüm/sözlük/feature/graf dosyaları korunmuştur. Hazırlık dosyasındaki geçmiş `training_authorized=False` kaydı ezilmedi; yeni kullanıcı onayı ayrı `user_authorization.json` ile belgelendi. `run_status.md` güncel kayıt olarak manifest dışındadır.

Kilitli v1 split tanımı SHA-256: `9872adf0168ad3ab377994fc346dc3eb553338e68109b9b1cf27ec966ef4bd65`. Üyelik CSV/hash'leri değişmedi. Seed **20261106**, tek ana ve tek önceden tanımlı stres protokolü. Gerçek train/validation/test ve yapısal grup listeleri hazırlıktaki dosyalardır; kopyası yeniden seçilmedi.

Ham XML/SIDER/STRING yeniden taranmadı; yeni veri/API/paket kurulumu yok. Kaynak sürümleri önceki provenanstan gelir: DrugBank XML 5.1 / 2026-01-04 export, SIDER 4.1. Bu eğitimde STRING/PPI kullanılmadı. Eğitim yalnız kayıtlı prepared input ve kaynak pozitif tablolarıyla yapıldı. WP07 `.pt` veya eski V6 model kodu kullanılmadı.

## Öğrenme görevi, modeller ve fit sınırı

B1 6 alan (5 clean kimya+maske), B2 234 alan (5 kimya+4 rol×56 dizi özeti+5 maske). Target/enzyme/transporter/carrier ayrı; ID/PT/kategori/sıklık/kalite_skoru/STRING skoru model girdisi değil. Maskeli nötr blok, eksik kaynak değeri gerçek sıfır olmuş gibi yorumlanmaz. Kaynak sekiz QC ve protein eksikliği korunur; 62 ilaç envanterde kalır.

PT başına onaylı L2 lojistik regresyon: liblinear, l1_ratio=0, class_weight=None, tol=1e-8, max_iter=10000, seed=20261106; intercept scaling=1. Liblinear'ın sentetik intercept parametresi de düzenlileştirmeye tabidir. Sabit seçenekler eğitimden önce run_config'e kaydedildi. Sklearn {env['sklearn']}, NumPy {env['numpy']}, SciPy {env['scipy']}; CPU threadpool 1. Gerçek learned preprocessing yeniden fit edilmedi; her context'in v1 dönüşümü aynen kullanıldı.

Her model yalnız kendi train ID'leri∩input eligibility satırlarına fit edildi. Protein dönüşümü yalnız train-linked benzersiz accession, kimya dönüşümü yalnız QC-onaylı train ilaçlarıyla daha önce hazırlanmıştı. Test ilacı query olarak yalnız etiketsiz inputunu verir; train grafı/dönüşüm kaynaklarına girmez. Train-only graf bundle'ı hash ile doğrulandı; LR baselineları onun PPI/mesaj geçişini kullandığını iddia etmez, rol özetleri hazırlanmış kaynaktan gelir.

## İç seçim: değişen PT kapsamı nasıl karşılaştırıldı?

Her inner train'de kendi 5 pozitif kullanılabilir ilaç / 2 bağımsız grup sözlüğü kullanılır. Üç inner foldun sözlükleri değişebilir; dış test sözlük/parametre seçiminde görülmez. **Aynı inner fold içindeki bütün C adayları aynı validation ilaçları ve C'den bağımsız hedef kapsamıyla** skorlanır; başarılı fit sınıflarının C'ler arası kesişimi kullanılır. Fit başarısızlığı olsaydı bu dışlamalar kayıtlı olacaktı; gözlenen hata/yakınsama sorunu yoktur. Tek proxy sonucu nedeniyle fit edilemeyen sınıflarda olasılık fallback'i yoktur.

C={{0.1,1,10}}, aynı inner fold kapsamı bütün adaylara ortaktır. NA fold-drug AP sıfır yapılmaz; bütün C'lerde geçerli ortak foldların **eşit fold ağırlıklı ortalaması** alınır. Bu, üç foldun aynı sabit hedef görevini ölçtüğü iddiası değildir; train destek kuralına koşullu folda özgü sıralama görevlerinin önceden tanımlı seçim özetidir. Coverage signature her C satırında saklandı. Eşitlik toleransı 1e-12; küçük C. Bütün seçimlerde üç inner fold da geçerliydi.

{table(selection[selection.protocol.eq('primary')][['outer_fold','family','model','selected_C','valid_inner_folds']])}

![Inner C seçimleri](figures/WP08/baseline_v1/01_inner_selected_C.png)

**Yorum:** B2 ana PT'de beş foldun tamamında C=0,1; B1 0,1/0,1/1/1/0,1 seçti. C aralığı sonuçtan sonra genişletilmedi. Stres protokolünün seçimleri ayrı tablodadır; daha iyi protokol seçmek için outer sonuçlar kullanılmadı. `selection_complete_before_outer_scoring.json`, C seçim dosyasının outer scoring öncesi hash'ini saklar; değerlendirme sonrasında da aynıdır.

## Outer modeller ve başarısız/uygulanamayan fitler

360 inner aday + 40 outer son model koleksiyonu = **400 parametre bundle'ı**. Fit izi **47031 aday tek-hedef fit durumu** içerir: **40611 inner + 6133 outer = 46744** başarılı classifier; **279 inner + 8 outer** tek proxy sonuç nedeniyle eğitilmedi. Bunlar benzersiz ilaç/etiket sayıları değildir; aynı hedef farklı fold/C/modelde tekrar yer alır. Yakınsama veya fit hatası gözlenmedi. Tam 62 üzerinde ayrıca deployment modeli eğitilmedi.

{table(trace[trace.phase.eq('outer')&trace.status.ne('fitted')][['context','family','model','class_id','observed_train_positive','train_unknown_NOT_verified_negative','status']])}

Örnek: C0027497 / tarihsel Mide bulantısı bazı outer train'lerde bütün kullanılabilir ilaçlarda kayıtlıdır; unknown örneği yoktur. Bu hedeflerde classifier fit edilmedi; “herkeste risk 1” veya train önselinden tahmin üretilmedi. Hedefin NA durumu saklandı.

![Outer fold PT](figures/WP08/baseline_v1/02_outer_fold_PT_AP.png)

**Yorum:** Ortak kapsamda fold farkları gerçek test ilaçları, label yoğunluğu ve train'den türeyen hedef kapsamlarını yansıtır. İyi foldlar seçilip kötüleri atılmadı. Foldlar birbirinden bağımsız beş tekrar gibi t-test/CI için kullanılmadı; training setleri örtüşür.

## Ana protokol, ortak kapsam: bütün ölçümler

{table(main_metrics[['model','metric','estimate','CI95_low','CI95_high','valid_bootstrap_replicates']])}

AP burada **average precision**: her skor eşiğindeki precision, recall artışıyla ağırlıklandırılır; trapez PR-AUC değildir. Drug-macro AP her ilaçta bilinen kayıtların PT adaylarına göre sıralamasını, micro AP bütün skorlanan OOF çiftlerini, class-macro AP/AUROC her hedefin skorlanabildiği ilaçlardaki kaydı ayırt etmeyi özetler. Unknown yalnız onaylı proxy referansıdır, gerçek negatif değil.

**Metrikler aynı bilimsel soruyu vurgulamıyor:** Ortak kapsamda B1 class-macro AUROC **0,4814** (CI 0,4283–0,5330), B2 **0,5431** (0,4999–0,5897). B2'nin sınıf bazlı bazı ikincil değerleri daha yüksekken birincil drug-macro AP'si daha düşüktür. Yüksek drug-AP, her PT için yeni ilaç ayırt etme gücü veya klinik güvenilirlik kanıtı değildir; sık etiketlerin sıralanması katkıda bulunabilir. Bu onaylı ilk deneyde B0/sıklık önseli baseline eklenmedi; dolayısıyla onun aşıldığı da iddia edilmez.

## Kendi kapsamı, paired54 ve complete-case53

{table(ap[['protocol','scope','model','estimate','CI95_low','CI95_high']])}

![PT kapsam ve koşullu CI](figures/WP08/baseline_v1/03_PT_AP_group_CI.png)

**Yorum:** Kendi kapsamlarında B1 54, B2 61 ilaç skorlar; own değerler doğrudan eşleştirilmiş karşılaştırma değildir. `paired54` aynı 54 input-uygun ilaç ve aynı outer-train'de gerçekten fit edilmiş ortak hedeflere göre maske uygular; yalnız testteki outcome'a göre hedef seçmez. Bir modelde fit edilemeyen sınıf paired kapsamdan iki tarafta birlikte çıkar. `complete_case53`, aynı eğitilmiş modellerin aynı ana splitlerdeki test alt kümesi duyarlılığıdır; 53 üzerinde yeniden eğitilmiş complete-case deneyi olarak sunulmaz.

{table(ptcoverage[['scope','model','scored_drugs','drug_AP_evaluable','scored_pairs','observed_positive_scored','unknown_scored_NOT_verified_negative','out_of_scored_vocab_positive','class_AP_AUROC_evaluable','class_metric_NA']])}

Ana paired54'te **13964** skorlanmış OOF çiftinin **3820**'si gözlenen pozitif, **10144**'ü unknown'dır. Bu ilaçların kaynak PT pozitifleri 5505; **1685** pozitif bu folda özgü skorlanan hedef kapsamının dışında kalmıştır. Bunlar negatifleştirilmedi veya yok sayılan başarılar gibi sayılmadı; coverage raporlandı. Pooled ortak union 306 CUI'de skor var; 256 sınıfta iki proxy outcome ile class metriği hesaplanabilir, 50'si NA.

Farklı outer foldlarda farklı train sözlükleri olduğundan pooled micro/class özetleri **ragged OOF kapsamına koşulludur**. Seçilmemiş/fit edilememiş drug–PT çifti tabloya 0 skor/negatif olarak eklenmez. Bu özet sabit 1061 PT'nin tümünde başarım iddiası değildir; fold kapsamı ve positive/unknown sayıları ayrı sunulur.

## Tarihsel 30: ayrı, semantik uyarılı karşılaştırma

{table(hist[['protocol','model','estimate','CI95_low','CI95_high']])}

![Tarihsel 30 sonucu](figures/WP08/baseline_v1/04_historical30_separate.png)

**Yorum:** Ana ortak kapsam drug-AP B1 0,8892, B2 0,8627; bu yoğun/seçilmiş farklı etiket uzayıdır. PT'ye göre yüksek sayı daha iyi yöntem veya klinik kategori geçerliliği kanıtı değildir. Renal impairment→Nefrotoksisite daraltması, Loss of consciousness/Syncope birleşmesi ve diğer önceki uyarılar korunur. Yeni kategori merge/drop yapılmadı.

Sulfanilamide tarihsel 30 içinde pozitif taşımadığı için skoru olsa da drug-AP NA'dır. Ana own kapsamda tarihsel drug-AP hesaplanabilir ilaç sayısı B1 53, B2 60; paired54'te 53, complete-case53'te 52'dir. AP'nin destek yokken üretilen yapay sıfırı kullanılmadı. Bütün class/drug NA nedenleri CSV'dedir.

## Abstention ve değişmeyen modaliteler

![Skor kapsamı](figures/WP08/baseline_v1/05_prediction_coverage.png)

**Yorum:** 62 ID korunur. Methenamine iki modelde de `ABSTAIN_no_input` ve hiç skor satırı yoktur. B1 sekiz kimya inceleme molekülünde skor vermez; B2 protein dalıyla yedi ek ilaçta skor verebilir. Tobramycin kimya dalıyla kalır. Ortak 54 ile complete-case 53 farklıdır: Tobramycin protein olmadan iki modelin input kapsamına dahildir. Bu input kapsam artışı, B2'nin aynı kapsamdaki performans artışı değildir. Önceki sekiz QC ve iki protein eksiği değiştirilmedi.

## Grup düzeyinde belirsizlik ve eşleştirilmiş fark

1000 percentile bootstrap; seed=20261106+9000+protokol_indeksi. Ana protokolde **61 connectivity grubu**, streste **40 yapı grubu** birlikte örneklenir; Levofloxacin/Ofloxacin aynı çoğaltma ağırlığını taşır. Paired farklar B1/B2 için aynı grup çekimleriyle hesaplanır. İlaç–PT çiftleri veya beş fold bağımsız birim gibi bootstrap edilmedi. Valid replika eşiği 800 olarak eğitimden önce kaydedildi; bu çalışmadaki aggregate aralıkların hepsi 1000 geçerli replika üretti.

{table(delta[delta.family.eq('PT')&delta.metric.eq('drug_macro_AP')][['protocol','scope','B2_minus_B1','CI95_low','CI95_high','valid_bootstrap_replicates']])}

![Paired AP farkı](figures/WP08/baseline_v1/06_paired_difference_group_CI.png)

**Yorum:** Ana ve stres PT paired drug-AP farkları bu sabit deneyde B2 aleyhinedir. Aralıklar **sabit OOF tahminlerine koşullu örnekleme belirsizliğidir**; bütün model/inner seçim sürecini bootstrap içinde yeniden eğitmedik. Training setlerinin örtüşmesinden ve önceki keşiften gelen tüm belirsizliği kapsamaz; bağımsız dış doğrulama veya genel nedensel üstünlük çıkarımı değildir. Class-macro bootstrap'ta destek kaybolan sınıflar o replikada NA kalır; sınıf kapsamı değişebildiğinden aralıkların yorumu ayrıca sınırlıdır.

Seyrek per-class veya tek outer-fold düzeyinde ayrı CI üretilmedi; `CI_status`/`CI_NA_reason` bunun nedenini yazar. Aggregate metriklerde CI NA oluşmadı; metrik değerinin hesaplanamadığı drug/class'larda destek nedeni saklandı. Tam tekrar eğitim belirsizliği bu ilk çalışmanın raporlanmış sınırıdır.

## Model uyumu, test ve tekrar üretim

**{v['tests']['passed']}/{v['tests']['passed']} test geçti; {str(v['tests']['seconds']).replace('.',',')} saniye.** Testler: önceki/hazırlık/model SHA'ları; gerçek frozen split; inner-only C'nin bağımsız tekrar hesabı ve tie/NA kuralı; 400 bundle'da exact train fit IDs/dönüşüm kaynağı; heldout query/label/value mutasyonunda model ve C değişmezliği; gerçek tek-hedef tekrar fit'inin aynı parametreyi vermesi; kayıtlı parametrelerden skor yeniden üretimi; abstention/62 ID; kaynağa tam proxy label eşitliği; ağırlıklı ve bağlı skor AP/AUROC'nin sklearn ile karşılaştırması; structural group bootstrap; paired scope eşitliği; coverage/NA/sürüm/no-extra-variant ve notebook figürleri. Testlerde sadece küçük kontrollü yeniden fit'ler yapıldı; ana eğitimin seçimini değiştirmedi ve model artefaktlarını ezmedi.

[Notebook](../notebooks/WP08_baseline_results.ipynb) **8 çalıştırılmış kod hücresi, 6 gömülü PNG** ve gerçek sonuç tabloları içerir; stderr/hata yok. Altı PNG görsel olarak incelendi. [İnteraktif ilaç-AP HTML](figures/WP08/baseline_v1/per_drug_proxy_AP_interactive.html) çevrimdışıdır; canlı tarayıcı etkileşimi test edilmedi.

Her bundle'da seed/C/sürüm, sklearn sürümü, fit drug IDs, train preprocessing accession/drug kaynakları, özellik sırası, declared/fitted target sözlüğü, gerçek split hash'i ve parametre hash'i bulunur. 800 parametre+metadata dosyası manifestle korunur (yaklaşık 69,5 MB). Parametreler NumPy NPZ/JSON'dur; eski pickle/PyG model kopyası değil. [Model kartı](WP08_BASELINE_MODEL_CARD.md) bilimsel kullanım sınırını açıklar.

| Çıktı | İşlev |
|---|---|
| models/WP08_baseline_v1/*.npz, *.json | Inner aday ve outer final katsayı/intercept, tam fit/seçim/provenans izi |
| selected_C.csv, inner_selection_metrics.csv | Inner-only seçim, her C'nin aynı kapsam hash'i, NA/valid fold sayısı |
| selection_complete_before_outer_scoring.json | Dış test scoring öncesi seçim commit/hash'i |
| oof_predictions.csv, prediction_status_all62.csv | Gerçek OOF proxy skorları/record s ve 62 ilaç için abstention durumu |
| outer_fold_metrics.csv, oof_metrics_with_group_CI.csv | Fold ve koşullu OOF beş metrik/CI |
| paired_B2_minus_B1_group_CI.csv | Aynı drug/target ve grup çekimleriyle paired fark |
| evaluation_coverage.csv, per_drug_metrics.csv, per_class_metrics.csv | Pozitif/unknown/sözlük dışı/NA ve kapsam paydaları |
| class_fit_trace.csv, fit_status_summary.csv | Başarılı/uygulanamayan bütün aday fit'ler |
| model_fit_provenance.csv, fold_train_validation_test_scope.csv | Fit drug/protein kaynak ve train/validation/test kapsamı |
| bootstrap_design.csv, run_config.json | Önceden sabit yöntem, seed/rep/unit/CI sınırı |
| user_authorization.json, environment.json | Yeni kullanıcı onayı ve sürüm/ortam kaydı |
| preparation_input_manifest.json, prior_outputs_hashes.json, model_artifact_manifest.json | Hazırlığın ve eski çıktıların korunması, modellerin hash'i |
| test_results.txt, artifact_validation.json | 28 test ve yürütülmüş notebook/görsel kontrolü |

QA `reports/qa/WP08/baseline_v1/`, görseller `reports/figures/WP08/baseline_v1/` altındadır. Kod modülleri `wp08_baseline_train.py`, `wp08_baseline_metrics.py`, `wp08_baseline_evaluate.py`, `wp08_baseline_audit.py`, `wp08_baseline_notebook.py`, `wp08_baseline_report.py`; test `tests/test_wp08_baseline.py`.

Ana training producer `training_complete.json` varsa yeniden fit'i reddeder; sonuç görüldükten sonra aynı sürümü yeniden ayarlamaya karşı korumadır. Sadece sonuç görüntülemek için notebook üreticisi yeterlidir. Değerlendirme yeniden hesaplanabilir, hiçbir model refit etmez. Tekrar doğrulamada `python -m unittest discover -s tests -p test_wp08_baseline.py -v` çıktısı QA'ya kaydedilip rapor yenilenir. Yeni deney ancak gerekçeli/onaylı ayrı sürümle yapılmalıdır.

## Resmi yöntem kaynakları

[Sklearn LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) ve [AUROC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html) API tanımları doğrulandı. Ağırlıklı bootstrap hesaplarının bağlı skor davranışı da mevcut sklearn ile test edildi. Harici biyolojik kaynak eklenmedi.

**İlk WP08 baseline sonuçları tamamlandı. Onaysız varyantlara veya WP09'a geçilmedi; sonuç onayı bekleniyor.**
'''
    (ROOT/'reports/WP08_BASELINE_RESULTS.md').write_text(text,encoding='utf-8')
    paths=[*sorted((ROOT/'scripts').glob('wp08_baseline*.py')),ROOT/'tests/test_wp08_baseline.py']
    (QA/'generator_code_manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in paths},indent=2),encoding='utf-8')
    print('Validated baseline results and wrote Turkish experiment report/model card')


if __name__=='__main__':main()
