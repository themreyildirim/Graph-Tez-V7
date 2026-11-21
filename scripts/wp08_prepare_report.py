"""Deney öncesi hazırlık raporu/kapanış; WP08'i kapatmaz, eğitimi başlatmaz."""
from pathlib import Path
import json,hashlib,re
import pandas as pd
import nbformat

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP08/experimental_preparation'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(f):
    def fmt(v):return str(v).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','|'+'|'.join(['---']*len(f.columns))+'|']+
                     ['| '+' | '.join(fmt(v) for v in r)+' |' for r in f.itertuples(index=False,name=None)])


def validate():
    out={}
    for name in ('prior_outputs_hashes.json','input_manifest.json','frozen_split_manifest.json'):
        m=json.loads((QA/name).read_text(encoding='utf-8'));base=QA if name=='frozen_split_manifest.json' else ROOT
        changed=[p for p,h in m.items() if sha(base/p)!=h];assert not changed,changed
        out[name]={'checked':len(m),'changed':changed}
    nb=nbformat.read(ROOT/'notebooks/WP08_experimental_preparation.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs]
    assert [c.execution_count for c in code]==list(range(1,8))
    assert not any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs)
    assert sum('image/png' in o.get('data',{}) for o in outputs)==5
    fig=ROOT/'reports/figures/WP08/experimental_preparation'
    assert len(list(fig.glob('*.png')))==5
    html=(fig/'frozen_fold_membership_interactive.html').read_text(encoding='utf-8')
    assert not re.search(r'<script[^>]+src\s*=',html,re.I)
    log=(QA/'test_results.txt').read_text(encoding='utf-8');match=re.search(r'Ran (\d+) tests in ([\d.]+)s',log)
    assert match and match.group(1)=='28' and log.rstrip().endswith('OK')
    out['tests']={'passed':28,'seconds':float(match.group(2)),'dependency_deprecation_warning':'torch.jit.script' in log}
    out['notebook']={'executed_cells':7,'embedded_png':5,'errors':0}
    out['figures']={'PNG_visual_review':5,'offline_HTML':1,'live_browser_tested':False}
    out['scope']={'actual_splits_created':True,'train_only_preprocessing_fitted':True,'model_training':False,
                   'predictions_computed':False,'performance_computed':False,'negative_sampling':False,
                   'WP08_closed':False,'WP09_started':False}
    (QA/'artifact_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


def main():
    v=validate();read=lambda n:pd.read_csv(QA/n,keep_default_na=False)
    s=json.loads((QA/'preparation_summary.json').read_text(encoding='utf-8'))
    lock=json.loads((QA/'split_lock_v1.json').read_text(encoding='utf-8'))
    ctx=read('context_summary.csv');outer=ctx[ctx.protocol.eq('primary')&ctx.inner_fold.eq(0)]
    vc=read('vocabulary_counts.csv');vc=vc[vc.protocol.eq('primary')&vc.inner_fold.eq(0)]
    targets=vc.pivot(index='outer_fold',columns='scope',values='PT_classes').reset_index()[['outer_fold','cohort','B1','B2','paired']]
    eligible=read('prediction_eligibility.csv');coverage=eligible.groupby('model').agg(cohort=('drug_id','nunique'),eligible=('eligible','sum')).reset_index();coverage['abstention']=coverage.cohort-coverage.eligible
    short=pd.DataFrame([
        ['Seed / split','20261106; connectivity 5×3; ayrı scaffold OR ≥0,8 stres','v1 kilitli; eğitim için son kabul'],
        ['PT kuralı','≥5 kullanılabilir train ilacı + ≥2 train grup; paired hedefler train kesişimi','Kural ve destek paydası'],
        ['Metrik varsayımı','Observed-record proxy; drug-macro AP birincil, micro/class-macro AP ve AUROC ikincil','Unknown gerçek negatif değil'],
        ['Maskeler / abstention','Nötr standart blok+maske; B1 kimya yoksa, B2 iki dal yoksa abstain','Methenamine tahminsiz kalır'],
        ['Learner / seçim','B1/B2 L2-LR adayı; C=0,1/1/10; inner mean drug-AP; eşitlikte küçük C','LR ve ayarlar henüz öneri'],
        ['NA / fallback','Train tek proxy sonucu veya metrik desteği yoksa NA; olasılık fallback yok','Ortak drug/target kıyası + kapsam'],
        ['ATC / ek deney','ATC ayrı; 53 complete-case duyarlılık; PPI/context yok','Ek eğitimler ayrı onay'],
    ],columns=['Detay','Hazırlanan / önerilen v1','Son onay konusu'])
    gate=f'''# WP08 — Eğitim öncesi son karar kapısı

06.11.2026. **Model eğitimi henüz başlamadı.** Aşağıdaki v1 hazırlığı, kullanıcının yeni yönlendirmesiyle somutlaştırıldı. Split kimlikleri ve seed, hedef dosyaları bu hazırlıkta işlenmeden önce kilitlendi; seçimler performansa göre denenmedi.

{table(short)}

Bu tablo eğitim onayı değildir. 5/2 kuralı düşük destek ve tek yapısal gruba bağımlılığı sınırlayan **önceden belirlenmiş operasyonel adaydır**; güç/klinik geçerlilik garantisi değildir. Kullanılabilir-train paydası, gerçekten inputu olmayan örneklerin bir modelin destek sayısını yapay artırmasını önler; kohort sözlüğü ayrıca korunur. Ortak karşılaştırma yalnız train'den seçilen hedef ve ortak input kapsamıyla yapılır.

Seed **20261106** yalnız sabit tarih kodudur; “en iyi seed” değildir. Dış test etiketleri daha önce keşfedildiğinden sonuçlar yine iç doğrulama sayılacaktır. Bu hazırlıkta başarım, tahmin, CI veya negatif örnek yoktur. Gerçek train-only **ön işleme fit'i** yapılmıştır; sınıflandırıcı fit edilmemiştir.

Kilitli split tanım SHA-256: `{lock['specification_sha256']}`. Ayrıntılı parametreler ve `class_weight=None` önerisi [QA karar tablosunda](qa/WP08/experimental_preparation/final_pretraining_decisions.csv), kaynak/fit/graf kapsamı [hazırlık raporundadır](WP08_EXPERIMENTAL_PREPARATION.md). WP08 açık kalır; WP09 yetkilendirilmedi.
'''
    (ROOT/'reports/WP08_FINAL_PRETRAINING_GATE.md').write_text(gate,encoding='utf-8')
    evals=read('metric_evaluability_NO_scores.csv');ev=evals[evals.context.isin(outer.context)&evals.split.eq('test')]
    text=f'''# WP08 — Deneysel kısma hazırlık v1

06.11.2026 — **Hazırlık tamamlandı, model eğitimi ve kalan yöntem ayrıntıları için son onay bekleniyor. WP08 kapanmadı. WP09 başlamadı.** Önceki protokol incelemesi kullanıcı tarafından kabul edildi; yol haritasındaki baseline ve performans deneyleri hâlâ yapılmadı.

## Hazırlananlar ve amaç

Araştırma sorusu, mevcut SIDER'da gözlenen ilaç–yan etki ilişkilerinin yeni ilaçlara genellenerek sıralanmasıdır. Klinik bireysel yan etki olasılığı iddiası yoktur. Gerçek connectivity kilitli **5 dış/3 iç nested split**, önceden tanımlı ayrı scaffold OR ≥0,8 stres split'i, her bağlamın train PT sözlüğü, train-only standardizasyonu, maskeli B1/B2 tasarım matrisleri ve **40 yeni train-only HeteroData** hazırlandı. Sınıflandırıcı, tahmin, AP/AUROC/CI ve negatif örnek üretimi yoktur.

Son eğitim öncesi onaylar, tekrarlanmayan **[tek kısa karar tablosunda](WP08_FINAL_PRETRAINING_GATE.md)** bulunur. Kullanıcının 5/2 PT kuralı “aday” niteliğini korur; gerçek destek çıktıları görülse de bu v1'de kural/seed/fold değiştirilmeyecek. Yeni yöntem kararı gerekirse gerekçeli v2, eski v1'i ezmeden oluşturulmalıdır.

## Önceki çıktıların korunması

Başlangıçta WP00–WP07 koruma manifesti doğrulandı. Önceki WP08 protokol raporu/notebook/kod/testleri de korunarak toplam **{s['prior_files_preserved']} proje dosyası** başlangıç ve kapanış hash'iyle aynı bulundu. Sekiz kaynak girdi hash'i ayrıca kaydedildi. `run_status.md` istenen güncel durum kaydı olduğu için bu korumanın dışındadır. Eski raporlar veya QC kararları revize edilmedi; bu çalışma ayrı eklerdir.

Ham XML/SIDER/STRING içeriği yeniden açılmadı; yeni veri/API/paket indirilmedi. Küçük kaynak QA'lar ve mevcut NumPy/pandas/PyG kullanıldı. Kaynak sürüm/provenansları korunur: DrugBank XML 5.1 / 2026-01-04 export, SIDER 4.1 ve önceki STRING v12.0 denetimleri. Bu hazırlık PPI verisi kullanmaz. Önceki WP07 inceleme `.pt` dosyaları yüklenmedi.

## Gerçek split ve seed kilidi

Seed **20261106** proje tarihinden alınan sabit sayıdır; başarım için optimize edilmedi. Gruplar büyükten küçüğe, eşitlikte SHA256(seed|group_id) sırasıyla en az ilaç içeren folda atanır. Inner seed `20261106 + 100*outer_fold`. Python'un değişken hash sırası veya hedef stratifikasyonu kullanılmaz. Bu algoritma sklearn GroupKFold'ın bire bir uygulaması olarak sunulmuyor; açık sürümlü, etiket körü grup dengeleme algoritmasıdır.

Kilit önceliği: önce source group hash + seed/5×3/support/girdi kapsamı SPEC → `split_lock_v1.json`; sonra gerçek CSV üyelikleri ve `frozen_split_manifest.json`; **sonra** PT kaynak dosyası açılıp destek hesaplanır. Kod, farklı v1 tanımı/üyeliğiyle mevcut kilidi ezmeyi reddeder. Daha önce tüm 62 etiket dağılımı keşfedildiği için bu kayıt “hiç görülmemiş dış test” iddiası sağlamaz; iç doğrulama sınırı korunur.

Ana connectivity kapsamı 61 bağımsız grup; Levofloxacin ve Ofloxacin aynı grupta. Her ilaç dış testte tam bir kez yer alır; her outer train ilacı üç iç validation'da toplam bir kez bulunur. Outer test, o outer'a ait bütün inner train/validation kümelerinin dışındadır. Ayrı stres protokolü 40 scaffold/benzerlik grubuyla aynı 5×3 düzeninde hazırlanmıştır; daha iyi sonuç verene göre ana protokolle yer değiştirilmeyecek.

{table(outer[['context','train_drugs','validation_drugs','test_drugs','train_graph_proteins','train_graph_edges']])}

Outer-final validation=0 beklenir: iç seçimden sonra son modelin fit edileceği outer train kapsamıdır, henüz model yoktur. Ana outer test büyüklükleri **13/13/12/12/12**; outer train **49/49/50/50/50**. Inner train 32–34, inner validation 16–17 ilaçtır. Tam 62 kimlik ve grup/split alanları notebook'ta ve CSV'lerde gösterilir.

![Kilitli dış foldlar](figures/WP08/experimental_preparation/01_frozen_outer_membership.png)

**Yorum:** Her satır bir gerçek ilaçtır; ana ve stres foldları ayrı panellerdir. Bu bir tahmin veya başarı grafiği değildir. Connectivity kilidi aynı bağlantı yapısının stereo varyantlarını ayırmaz; kimyasal/klinik eşdeğerlik sonucuna dönüşmez.

## PT sözlükleri ve destek kuralının gerekçesi

Kural **≥5 pozitif train ilacı + ≥2 bağımsız train grup**, düşük destekli/tek gruba bağımlı hedefleri operasyonel olarak sınırlamak için performans hesaplanmadan seçilmiş adaydır. İstatistiksel güç veya negatif doğruluk garantisi sağlamaz. Ne 3/10 destek denemesi ne seed araması yapıldı.

Üç kapsam saklandı: (a) bütün kohort train'inde 5/2 sözlüğü, (b) her baseline'ın gerçekten input kullanabildiği train ilaçlarıyla 5/2 sözlüğü, (c) B1/B2 train sözlüklerinin eşleştirilmiş kesişimi. Bu kullanılabilir-train paydası son onay tablosunda açıkça sunulmuştur; sınıfı yapay çoğaltmaz. Her inner train kendi kuralını yeniden uygular, outer train sözlüğü inner validation bilgisiyle taşınmaz. Validation/test desteği sözlük seçiminde kullanılmaz.

{table(targets)}

![Train PT sözlükleri](figures/WP08/experimental_preparation/02_train_vocabularies.png)

**Yorum:** Ana outer train'de kohort/B2 sözlüğü 240–326, B1/paired sözlüğü 220–275 PT içerir. Bu sayılar 1061 kaynak PT'nin “yanlış” olduğu veya seçilmeyenlerin negatif olduğu anlamına gelmez. Testte sözlük dışı pozitifler korunur; `out_of_vocab_observed_positive_pairs` ile açık kapsam kaybı raporlanır. B1 ve B2 farklı sözlük/kapsamlarda ölçülüp doğrudan eşdeğer başarılar gibi kıyaslanmayacak.

5/2 sözlüğüyle ikili proxy sınıflandırıcısının fit edilebilirliği ayrıdır. Train'de tüm kullanılabilir ilaçlarda pozitif kayıt taşıyan bir PT, iki proxy sonucu içermediğinden LR fit'ine uygun değildir. `proxy_trainability_NO_model_fit.csv` ve train-only fittable sözlük bu durumu ayrı işaretler. Olasılık/önsel fallback üretilmedi; NA politikası son onaydadır. Bu ayrım test etiketine göre yapılmaz.

Tarihsel 30 kategori sabit bir ikincil referans olarak saklanır; anlam daralma/birleşme uyarıları değişmedi. Her bağlam/model için train desteği ve test/validation hesaplanabilirliği ayrı tablolardadır. Yeni klinik alt küme veya merge/drop yapılmadı.

## B1/B2 girdileri, abstention ve karşılaştırma kapsamı

{table(coverage)}

B1 yalnız 5 clean kimya + kimya maskesi (**6 alan**); B2 5 kimya + ayrı target/enzyme/transporter/carrier rolleri için 4×56 dizi özeti + 5 presence maskesi (**234 alan**). Kimlik, CID, accession, taxID, PT/kategori/sıklık veya kalite_skoru sayısal girdiye alınmadı. Kaynak kimlikleri yalnız metadata/join/provenanstır.

![Girdi ve abstention kapsamı](figures/WP08/experimental_preparation/03_abstention_coverage.png)

**Yorum:** B1 için 54/62, B2 için 61/62 ilaçta input vardır; bunlar üretilmiş tahmin sayısı değildir. B1 sekiz kimya incelemesinde abstain; B2 yalnız **Methenamine** için iki dal da yokken abstain. Methenamine envanterde kalır; ona ortak önsel veya uydurma kişisel özellikten skor verilmez. Tobramycin kimya dalıyla iki baseline'da da kalır. Kaynak sekiz QC bayrağı ve iki eksik protein modalitesi değişmedi.

Model inputu olmayan satır `ABSTAIN`, diğer satırlar `PREDICTION_NOT_RUN` olarak işaretlidir. `baseline_row_plan.csv` gelecekteki classifier fit satırlarını yalnız inputu kullanılabilir train ilaçları olarak listeler; Methenamine bu satırlara hiçbir bağlamda giremez. Her baseline'ın kendi kapsamı yanında **ortak inputlu 54 ilaç** ve ortak train hedeflerindeki eşleştirilmiş kıyas ayrıca hazırlanmıştır. **53 complete-case**, ortak input kapsamıyla aynı şey değildir: protein bulunmayan fakat kimyası olan Tobramycin nedeniyle 54≠53. Complete-case ayrı envanter ve aynı ana split içinde yalnız duyarlılık kapsamıdır; yeni split seçilmedi ve bu alt kümede model eğitilmedi.

## Gerçek train-only ön işleme

Bu aşamada **sayısal ön işleme fit'i gerçekten yapılmıştır**, sınıflandırıcı eğitimi yapılmamıştır. Her 40 bağlamın kimya ortalama/std'si yalnız QC-onaylı train ilaçlarında; protein ortalama/std'si yalnız train ilaçlarının ilişkili benzersiz accession kümesinde hesaplanır. std ddof=0, sabit sütunda scale=1; öğeler kayıtta açıkça bulunur. Heldout'a yalnız aynı dönüşüm uygulanır.

Proteinler train ölçeğinde standardize edilir, sonra her ilacın her rolündeki benzersiz proteinler ayrı ayrı ortalanır. Test ilacının yalnız kendisine bağlı yeni bir proteini fit kaynağı olmaz; kaynakta bulunuyorsa o dizi değerine train dönüşümü uygulanarak query özeti hazırlanabilir. Query ilişkileri train grafını genişletmez. Paylaşılan bir accession train ilaçlarında da varsa train fit kaynağı olarak yer alması meşrudur.

Eksik dalda kaynak NaN/eksikliği korunur; **yalnız sayısal tasarım matrisinde maskeyle birlikte standardize nötr 0** kullanılır. Bu gerçek protein/MW/AAC sıfırı, yeni dizi, kimya doğrulaması veya context dolgusu değildir. İki dalı olmayan Methenamine'in yer tutucu satırı scoring/fit için eligibility planıyla engellenir. Bu maskeli kodlamanın son yöntem onayı istenir. Ham/clean kaynaklar değiştirilmedi.

![Fit kaynakları](figures/WP08/experimental_preparation/04_transform_fit_scope.png)

**Yorum:** Ana outer kimya fit sayıları 43/43/43/44/43; benzersiz protein sayıları 125/121/133/119/123'tür. Bunlar ayrı biyolojik birimlerdir. Inner fit kaynakları da ayrı kaydedilir. Test-only değerleri büyük sayılarla değiştiren test, kaydedilen train fit istatistiklerinin değişmediğini doğruladı. B2'nin 234 alanı 32–50 train ilacına göre yüksek boyuttur; düzenlileştirilmiş küçük baseline önerisi bu yüzden açık onay tablosundadır.

ATC başlangıç matrisine eklenmedi. İstenirse WP02 kaynak ATC'sinden, eski hatalı one-hot kopyalanmadan, train vocabulary veya önceden sabit hiyerarşiyle ayrı varyant hazırlanmalıdır. Bu ek varyant/eğitim onayı verilmiş sayılmaz. LR/RF/MLP yol haritası deneyleri henüz çalıştırılmadı; ilk eşleştirilmiş B1/B2 L2-LR ve sınırlı iç C seçimi yalnız öneridir.

## Yeni train-only graf ve korunan WP09 sınırı

**40 yeni HeteroData** dosyası birleşik bundle'da saklanır. Her biri yalnız kendi train drug düğümleri, onların target/enzyme/transporter/carrier kenarları ve bu ilişkilerdeki proteinleri içerir. Validation/test drug düğümleri ve ileri/ters ilişkileri yoktur. SE hedef düğümü/kenarı, PPI ve 80 context düğümü yoktur; x/y bu graf nesnelerine yazılmadı. Girdiler ayrı baseline matrislerindedir. WP07 `.pt` verisi kullanılmadı.

63 aynı-taxID insan ile 23 K12/MG1655 kapsam-inceleme proteini PPI bakımından ayrı statülerini korur. Burada PPI kullanılmadığından bu proteinler, train DrugBank ilişkileri varsa normal dizi modalitesinde bulunabilir; K12 ana PPI ağına kabul edilmiş değildir. PPI'siz proteinler elenmez; train graph evreni yalnız train ilişkilerinden türetilir. Query'nin etiketsiz ilişkileri gelecekte ayrı inferans akışında kullanılmalı, heldout ilaçlardan train'e geri mesaj verilmemelidir.

WP09 için gerçek forward komşuluk etkisi testi ve eşleştirilmiş PPI/no-PPI/karıştırılmış-PPI ablation gereksinimi korunur. Skor 700 seçilmedi, PPI encoder/message passing veya WP09 işlemi başlamadı.

## Kayıt sıralaması, proxy metrik ve NA kapsamı

Unknown çiftler doğrulanmış biyolojik negatif değildir. Negatif örnekleme ve hedef 0 matrisi üretilmedi. Gelecekte onaylanırsa observed-label proxy AP/AUROC yalnız **kaynak kayıt sıralamasını** ölçer; klinik negatif doğrulaması, bireysel risk veya gerçek biyolojik kalibrasyon iddiası taşımaz. Bütün sonuç tablolarında bu semantik bulunmalıdır. İkili proxy loss dahi bu son onaya bağlıdır.

Aşağıdaki tabloda değerler destek ve kapsam sayılarıdır, **AP/AUROC sonucu değildir**:

{table(ev[['context','model','eligible_drugs','abstained_drugs','train_selected_PT_classes','classes_no_observed_positive','classes_all_observed_positive','train_and_split_proxy_AUROC_possible_classes','out_of_vocab_observed_positive_pairs']])}

![Metrik destek kapsamı](figures/WP08/experimental_preparation/05_metric_support_not_scores.png)

**Yorum:** Testte hiç gözlenen pozitif veya hiç unknown olmayan PT'lerde ayırt edici class proxy metriği NA kalmalıdır. Train'de tek proxy sonucu olup model fit edilemeyen sınıf da ayrı NA'dır; sayılan 5/2 sözlüğünden ayrı raporlanır. `train_and_split_proxy_AUROC_possible_classes` her iki gerekli koşulu kontrol eder, yine de model/scoringsiz başarı söylemez. AP araçtan all-positive durumda sayı döndürebilse bile ayırt edici değerlendirme gibi sunulmaz.

Önerilen ana metric drug-macro AP, her yeni ilacın train'den seçilmiş PT adayları arasındaki kayıt sıralamasını ortalar. Micro/class-macro AP ve AUROC ikincildir. AP trapez PR-AUC ile aynı hesap değildir. Drug/class başına pozitif ve unknown desteği, abstention, sözlük dışı hedefler ve ortak kıyas kapsamı birlikte gösterilir. Her foldun sözlüğü farklı olabildiği için sabit görev varmış gibi tüm OOF çiftlerini kayıtsız havuzlamak uygun değildir. Inner seçim aynı foldun sabit candidate kapsamını kullanmalı; hedef eşiği daha iyi skor için geriye dönük değişmemelidir.

## Doğrulama ve dosyalar

**{v['tests']['passed']}/{v['tests']['passed']} test geçti; {str(v['tests']['seconds']).replace('.',',')} saniye.** Test logunda mevcut torch/PyG importu için deprecation uyarısı var, test hatası yok. Önceki testler değiştirilmedi. Kontroller: kaynak/frozen hash; deterministik etiket körü atama; bütün train/validation/test kimlik/grup ayrıklığı; Levo/Oflox kilidi; nested containment; her train'den bağımsız 5/2 sözlüğü; heldout label/feature mutasyonuna dayanıklılık; fit drug/accession kapsamı ve mean/std'nin bağımsız hesabı; sayısal şema/maske/rol özeti; 40 grafın kaynak kenar ve düğümleri; abstention/classifier row planı; tarihsel 30; NA/paired kapsam; açık WP08/kapalı WP09 ve notebook görselleri.

[Notebook](../notebooks/WP08_experimental_preparation.ipynb), **7 yürütülmüş kod hücresi, 5 gömülü PNG**, tam ID tabloları ve Türkçe yorumlar içerir. PNG'ler görsel olarak incelendi. [İnteraktif fold HTML](figures/WP08/experimental_preparation/frozen_fold_membership_interactive.html) çevrimdışı ve kimlik/ad/grup hover'lıdır; canlı tarayıcı etkileşim testi yapılmadı.

| Dosya / konum | İşlev |
|---|---|
| split_lock_v1.json, frozen_split_manifest.json | Önceden sabit seed/yöntem/hash ve overwrite engeli |
| outer_membership_v1.csv, nested_partitions_v1.csv | Bütün gerçek drug/group/train/validation/test listeleri |
| train_PT_support.csv, train_vocabularies.json, vocabulary_counts.csv | Train-only kohort/model/paired 5/2 hedef kapsamı |
| proxy_trainability_NO_model_fit.csv, train_fittable_vocabularies_NO_model_fit.json | Tek proxy sonucu nedeniyle fit edilemeyen sınıflar, NA planı |
| transform_fit_sources_and_statistics.json | Her bağlamın fit drug/accession kimliği ve sayısal dönüşümü |
| features/*.npz, feature_schema_v1.json | Folda özgü 62 satır B1/B2 tasarım matrisi ve açık maskeli şema |
| train_only_graphs_v1.pt, context_summary.csv, graph_edge_counts.csv | Yeni 40 train-only graf ve tam sayımları |
| prediction_eligibility.csv, baseline_row_plan.csv | Abstention ve gelecekteki classifier fit satırlarını engelleme planı |
| metric_evaluability_NO_scores.csv, paired_evaluation_scope_NO_scores.csv | Pozitif/unknown/sözlük dışı/NA ve ortak kıyas kapsamı; skor yok |
| historical30_reference.json, secondary30_*.csv | Tarihsel 30'un semantik uyarılı train/evaluation desteği |
| complete_case_53_inventory_ONLY.csv | Aynı ana splitte değerlendirilecek duyarlılık alt grubu |
| final_pretraining_decisions.csv, training_gate.json | Son yöntem onayı ve kapalı eğitim/performans kapısı |
| input_manifest.json, prior_outputs_hashes.json, artifact_validation.json | Korunma/tekrar üretim/doğrulama izi |

QA dosyaları `reports/qa/WP08/experimental_preparation/`, PNG/HTML `reports/figures/WP08/experimental_preparation/` altındadır. Kod: `scripts/wp08_prepare.py`, `wp08_prepare_summary.py`, `wp08_prepare_notebook.py`, `wp08_prepare_report.py`; test `tests/test_wp08_prepare.py`.

Tekrar üretim sırası: prepare → prepare_summary → prepare_notebook → test_wp08_prepare (çıktıyı QA test_results.txt'ye kaydet) → prepare_report. Büyük kaynak yeniden taranmaz. Aynı v1 kilidi korunur; değişen seed/üyelik için üretici hata verir. Onaydan sonra classifier, tahmin ve metrik kodu ayrıca açık kapsamla geliştirilecektir; mevcut hazırlık kendi kendine eğitim başlatmaz.

**Sonraki adım yalnız [kısa karar tablosunun](WP08_FINAL_PRETRAINING_GATE.md) kullanıcı tarafından değerlendirilmesidir. WP08 açık, baseline/performance görevleri yapılmamış, WP09 kapalıdır.**
'''
    (ROOT/'reports/WP08_EXPERIMENTAL_PREPARATION.md').write_text(text,encoding='utf-8')
    code_paths=[*sorted((ROOT/'scripts').glob('wp08_prepare*.py')),ROOT/'tests/test_wp08_prepare.py']
    (QA/'generator_code_manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in code_paths},indent=2),encoding='utf-8')
    print('Validated preparation; wrote report and final pretraining gate. WP08 remains open.')


if __name__=='__main__':main()
