"""Eğitim/ablation sonuçları ve model kartı; yalnız dondurulmuş QA okur."""
import json,re
import pandas as pd
from wp09_train import ROOT,QA,MODEL,PREP,VERSION,SEMANTICS,sha,write_json,csv,preserve


def table(frame):
    def cell(v):
        if isinstance(v,float):return 'NA' if pd.isna(v) else f'{v:.4f}'
        return str(v).replace('|','/')
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join(
        '| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def main():
    preserved=preserve();done=json.loads((QA/'training_complete.json').read_text(encoding='utf-8'))
    run=json.loads((QA/'run_config.json').read_text(encoding='utf-8'))
    fit=pd.read_csv(QA/'model_fit_summary.csv');metrics=pd.read_csv(QA/'metrics_with_group_CI.csv')
    delta=pd.read_csv(QA/'paired_differences_group_CI.csv');coverage=pd.read_csv(QA/'evaluation_coverage.csv')
    ap=metrics[metrics.scope.eq('paired54')&metrics.metric.eq('drug_macro_AP')]
    own=metrics[metrics.scope.eq('own61')&metrics.metric.eq('drug_macro_AP')]
    keydelta=delta[delta.scope.eq('paired54')&delta.metric.eq('drug_macro_AP')]
    select_names=['B1','B2','B0_like_B2','G_noPPI','G_realPPI','G_shuffledPPI_mean3_metrics']
    secondary=metrics[metrics.scope.eq('paired54')&metrics.model.isin(select_names)&metrics.metric.isin(['micro_AP','within_fold_class_macro_AUROC'])]
    proof=fit.groupby('model').agg(fits=('job_key','count'),optimizer_steps=('optimizer_steps','sum'),
        minimum_selected_weight_L2_change=('selected_state_L2_change','min'),
        minimum_max_message_gradient=('maximum_message_gradient_norm','min'),maximum_message_gradient=('maximum_message_gradient_norm','max')).reset_index()
    epochs=fit[fit.inner_fold.eq(0)].pivot(index=['protocol','outer_fold'],columns='model',values='best_epoch').reset_index()
    targets=pd.read_csv(QA/'target_trainability_audit.csv')
    testlog=(QA/'test_results.txt').read_text(encoding='utf-8');match=re.search(r'Ran ([0-9]+) tests in ([0-9.]+)s',testlog)
    assert match and match.group(1)=='24' and testlog.rstrip().endswith('OK')
    example=json.loads((QA/'example_drug_inputs.json').read_text(encoding='utf-8'))
    rank=pd.read_csv(QA/'example_drug_PT_ranking.csv')
    c=coverage[coverage.model.eq('G_realPPI')][['protocol','scope','scored_drugs','scored_pairs','observed_positive_scored',
        'unknown_NOT_verified_negative','source_positive_for_scored_drugs','out_of_scored_vocab_positive','scored_class_union','class_AUROC_evaluable','class_AUROC_NA']]
    report=f'''# WP09 — Gerçek protein-PPI eğitimi ve ablation sonuçları

06.11.2026. **WP09_TRAINING_AND_EVALUATION_COMPLETE; AWAITING_USER_RESULTS_REVIEW.** Kullanıcı frozen v3 kapsamında eğitimi açıkça onayladı. WP10 başlamadı. Sürüm: **{VERSION}**. Bu modelde atom–bağ GNN yoktur;tam moleküler Graph-in-Graph tamamlandı iddiası yoktur.

## 1. Ana sonuç

**Gerçek PPI mesaj geçişi çalıştı ve öğrenildi;bu deneyde birincil drug-macro observed-record AP'ye ek katkı gösterilmedi.** Ana paired54'te G_noPPI **0,6430**,G_realPPI **0,6429**,üç shuffled metriğinin eşit ortalaması **0,6433**. Real−noPPI **−0,000142**,koşullu%95 CI **−0,003611–+0,003248**;real−shuffled_mean **−0,000379** (−0,002039–+0,001310). Stres farkları da sıfırı içerir.

B1 **0,6556**,B2 **0,6262**,B0_like_B2 **0,6466** ana ortak AP değerleri değişmedi. G_realPPI−B1 **−0,012762** (−0,031658–+0,004782),G_realPPI−B0_like_B2 **−0,003724** (−0,016303–+0,007884);bu kaynak/ölçüde bu referanslara karşı belirgin ek başarı gösterilemiyor. Eşdeğerlik veya bütün protein biyolojisinin yararsızlığı kanıtlanmış değildir.

Streste real−B2 **+0,046908** (0,025161–0,070822) iken noPPI−B2 **+0,047929** (0,026299–0,070056). Nonlineer encoder/öğrenme yapısı B2 LR'den farklıdır;bu fark **PPI topolojisinin etkisi diye sunulamaz**. Streste gerçekPPI ile B0_like_B2 neredeyse aynı AP verir. Düşük,benzer veya karşılaştırma aleyhine sonuçlar gizlenmedi;sonuçtan sonra model/eşik/null/seed/hyperparametre değişmedi.

## 2. Onay,protokol ve korunan kaynaklar

AGENTS,aktif ROADMAP,WP09 tasarım/karar raporları ve v3 sözleşmesi esas alındı. Kullanıcının yeni eğitim onayı ayrı `run_config.json` içine kaydedildi. Eski `WP09_training_PROPOSED_v3.json` training_enabled=False taşıyan tarihsel öneri olarak aynen korunur;yeni wrapper açık kullanıcı onayını ve700 eşiğini kaydeder. Teknik onay engeli varmış gibi yeniden izin istenmedi.

**{preserved} önceki dosya** içerik SHA-256 ile aynı kaldı:WP00–WP08 ve WP09 tasarım/null verileri,kod/test/notebook/QA,seed20261106,split üyelikleri,target sözlükleri,62 ilaç,1061 kaynakPT,6416 kaynak pozitif veQC kararları. B0/B1/B2 ağırlıkları/skorları/C değerleri yeniden fit edilmedi. Ham büyük XML/STRING/SIDER tekrar taranmadı;PUG API/yeni biyolojik kaynak/paket kurulumu yok.

Kaynak zinciri mevcut küçük QA'dır:DrugBank5.1/export2026-01-04→WP05 accession/56özellik/4rol;STRINGv12.0→aynı-taxID insan induced PPI;WP04 clean5kimya/QC;SIDER4.1→WP03 kesin62 kaynakPT kayıtları;WP08→train-only scaler/target/eligibility/frozen nested split. Kaynak ID'leri sadece join/provenanstır,öğrenme özelliği değildir. `kalite_skoru`,PT sayıları,kategoriler,raporlama sıklığı veya STRING skoru düğüm girdisi yapılmadı.

## 3. Gerçek eğitim ve model ağırlıkları

**190/190 fit OK**:140 inner model+50 outer-final model. Toplam **{done['optimizer_steps']} gerçek AdamW adımı**;190 NPZ state_dict+190 JSON metadata ayrı model dizininde. NumPy state arşivi `allow_pickle=False` ile okunur;tek tüm62 üzerinde deployment fit'i yapılmadı. Her dosya model sürümü,seed,init/selected state hash'i,PT vefit-ID listeleri,graph/null hash'i,epoch/gradient/proxy desteği ve kaynağı korur.

56→32 paylaşılan protein projection,tek residual mean PPI,5→8kimya,dört ayrı masked mean rol,5maskeden141 boyut ve train-fittable PT lineer başlığı kullanıldı. Head hariç3920 parametre;K hedefte142×K başlık parametresi. G_noPPI gerçekten boş komşu mesajı kullanır;G_realPPI gerçek700 insan kenarlarını,G_shuffledPPI ayrıR0/R1/R2 kenarlarını işler. Bütün5 fit aynıcontextte aynı başlangıç ağırlığı/ID/target/girdi kapsamına sahiptir.

Full-batch observed-record proxy **BCEWithLogitsLoss**,class/pos weight yok;AdamW lr0,001/weight_decay0,001;float32/CPU1thread/deterministik algoritmalar. Eksik dal standart nötr+maskedir,biyolojik sıfır değildir;özelliksiz80 context eklenmedi. 23 K12/MG1655 koşullu PPI insan ağına alınmadı;PPI'sız doğrulanmış diziler self/residual yolunda kaldı. Kimya QC sekiz ilaç ve Tobramycin/Methenamine protein eksiği değişmedi.

{table(proof)}

![Optimizer ve mesaj gradienti](figures/WP09/training_v1/08_optimizer_gradient_evidence.png)

**Yorum:** Her gerçek/shuffled fitte PPI message.weight'e sıfır olmayan gradient ulaştı. NoPPI mesaj girdisi/gradienti0'dır. NoPPI'da kullanılmayan message ağırlığının weight-decay ile kayması komşuluk kullanımı kanıtı değildir. Ağırlık güncellemesi,gerçekgradient ve trained-forward edge kaldırma testleri birlikte raporlandı. Böylece eskiV6'nın“PPI tensoru var ama forward'da kullanılmıyor” hatası giderildi;performans faydası ayrıca ablation'la sorgulandı ve gösterilemedi.

## 4. Nested CV,epoch seçimi ve açık kalan NA'lar

Ana connectivity dış5/iç3 ve ayrı scaffold OR≥0,8 stres üyelikleri aynı kaldı. Üç nullun tümü geçersiz olmayan ortak inner bağlamlar kullanıldı:primary outer2 inner2/3,stress outer2 inner1/3,diğer8 outer inner1/2/3. Null nedeni ile dışlanan iki contextte **10 inner fit çalıştırılmadı**;`excluded_inner_jobs.csv` bütün varyantları açıkça gösterir. Üç başarısız null NA kaldı,bütçe/seed/%50 kuralı değişmedi veya başka kenarla doldurulmadı.

Inner max200 epoch,patience20,min_delta0,0001. İlk finite AP checkpoint'i ve daha sonra>min_delta iyileşme seçildi;tie erken epoch. Eğitim sonunda selected checkpoint restore edildi. Her variant/replica için ortak geçerli inner best epoch medyanı .5 yukarı yuvarlanarak outer-final epoch sayısı belirlendi;outer test early stopping'e girmedi.

{table(epochs)}

![Gerçek loss ve validation eğrileri](figures/WP09/training_v1/01_real_training_curves.png)

**Yorum:** İlk sıralı inner contextin beş eğrisi gösterilir;tam190 history dosyası saklıdır. Train BCE güncelleme öncesi,validation AP/loss güncelleme sonrası ölçülür. AP'ye göre seçilen epoch son optimizer epoch'u olmak zorunda değildir. Tüm outer epochları34–55 aralığındadır;sonuçtan sonra uzatılmadı.

![Outer epoch seçimi](figures/WP09/training_v1/02_outer_epoch_selection.png)

**Yorum:** Aynı kapsam,aynı epoch sayısı zorunluluğu değildir;her modelin kendi inner early-stop bilgisi,aynı ortak foldlar üzerinden önceden onaylanan medyan kuralına girer. Bütün10 outer bağlamda beş final fit OK'dir;ek numeric-fit veya validation-metric NA oluşmadı. Gelecek hatalarda ortak-fold≥2/outer-triad NA kuralı gerçek trainer'da sürer;kusur enjeksiyon testleri bunu sınırlar.

## 5. Hedefler ve sızıntı sınırı

Her fit mevcut train B2 sözlüğü ve train-fittable maskesini kullandı. ≥5 pozitif kullanılabilir ilaç/≥2 grup ilkesi önceden kilitli kaldı;hiçbir hedef global test sıklığıyla seçilmedi.40 context sözlük oluşumunda **{int((~targets.fittable).sum())}** single-proxy kayıt vardır;başlık dışında tutuldu,fallback olasılığı yoktur. Bu sayı benzersiz PT/ilaç veya başarısız GNN sayısı değildir. Aktif38contextte her beş modelin başlığı aynıdır. Kaynak1061 PT'nin tamamı her foldda hedef değildir.

Train grafında yalnız train ilaçları ve train-linked sequence proteinler vardır;heldout ilaç/ileri-ters ilişkisi,SE/PT hedef kenarı veya WP07 inceleme grafı yoktur. Dönüşüm mean/scale ve fit-ID kaynakları WP08'den aynen kullanıldı;yeniden scaler fit edilmedi. Query readout train protein cache'ini/model state'ini değiştiremez. Train evreni dışındaki query accession'ı aynı train-scaler/shared self encoder ile PPI'sız işlenir;query'den train'e geri mesaj/batchnorm yoktur.

Küçük kaynak etiket deposu okunur,ancak gerçek fit API'si yalnız exact train vevalidation ID sözlüklerini kabul eder. Inner çağrıdan outer test query'leri ve test-only unseen feature satırları çıkarılır. Bütün seçimler ve outer ağırlıklar tamamlanıp hash'le commit edildikten sonra `score` ayrı aşamada outer outcome'larını değerlendirmede kullanır. Outer label/value mutation testinde gerçek trainer'ın checkpoint/validation AP ve parametreleri değişmedi.

## 6. Eşleştirilmiş birincil sonuçlar

Aşağıdaki paired54 aynı **drug/fold/PT** anahtarlarıdır;iki protokolde de eski frozen karşılaştırma anahtarlarının hiçbiri kaybolmadı. Shuffled mean satırı üç metriğin eşit ortalamasıdır;OOF'ta ensemble score satırı yoktur.

{table(ap[['protocol','model','estimate','CI95_low','CI95_high']])}

![Aynı kapsamda B0/B1/B2 ve ağ modelleri](figures/WP09/training_v1/03_paired_baseline_comparison.png)

**Yorum:** Ana B1 point değeri daha yüksek;real−B1 CI sıfırı içerdiğinden bu deneyden genel istatistiksel üstünlük/başarısızlık çıkarılmaz. Frekans referansı güçlü kalır. Ağların kendi aralarındaki çok küçük farklar ek PPI faydasını desteklemiyor. Düşük/benzer sonuçları daha iyi göstermek için etiket,örnek,epoch/seed veya eşik yeniden seçilmedi.

{table(keydelta[['protocol','first','reference','first_minus_reference','CI95_low','CI95_high']])}

![Eşleştirilmiş PPI farkları](figures/WP09/training_v1/04_PPI_paired_differences.png)

**Yorum:** Real−noPPI ve real−shuffled_mean doğrudan topoloji katkısını sorgular;real−B2 kapasite/öğrenme/temsil farklarını da taşır. Stres B2 kazancını PPI kazancı diye sunmamak için noPPI ve shuffled karşılaştırmaları aynı tabloda tutulur. Bu farklılıklar biyolojik mekanizmanın nedensel ölçüsü değildir.

## 7. Own61 ve ikincil metrikler

{table(own[['protocol','model','estimate','CI95_low','CI95_high']])}

Own61 B2-eligible kaynak kapsamıdır;B1 kendi54 input kapsamıyla burada eksik skorları yok sayılarak yarıştırılmaz. Ana birincil kıyas paired54'tür. 53 complete-case bu aşamada yeni eğitilmiş kohort yapılmadı;62 envanterden ilaç silinmedi.

{table(secondary[['protocol','model','metric','estimate']])}

![Micro AP ve fold içi class-AUROC](figures/WP09/training_v1/05_secondary_metrics.png)

**Yorum:** Primary real microAP0,5678/fold içi classAUROC0,5270;stres0,5903/0,5468. Drug-AP ilaç içi PT sıralaması,microAP pooled çift sıralaması,classAUROC aynı PT'de ilaç sıralamasıdır. Fold içi classAUROC yalnız tanımlı fold-macro değerlerin eşit ortalaması,betimleyici secondary metriktir;foldlar bağımsız tekrar gibi CI'a sokulmadı. Pooled classAUROC `metrics_with_group_CI.csv` içinde **diagnostic only** olarak saklıdır;skor ölçeği/folda özgü sözlük ve B0 frekans etkisi nedeniyle klinik ayrım gücü veya primary başarı diye yorumlanmaz. B0 fold içinde sınıf skoru sabit olduğundan tanımlı AUROC0,5'tir.

## 8. Pozitif/unknown,sınıf kapsamı ve abstention

{table(c)}

![Değerlendirme kapsamı](figures/WP09/training_v1/06_coverage_unknown_NA.png)

**Yorum:** Her model61/62 ilaçta skorlar,Methenamine için ABSTAIN_no_input bırakır. Primary paired54:13964 çift=3820 gözlenen pozitif+10144 unknown. Aynı ilaçlardaki5505 kaynak pozitifin **1685**'i skor sözlüğü/fit kapsamı dışındadır;bu bütün62 için eksik/yanlış-negatif sayısı değildir.306 CUI pooled union'da skorlanır;class metriği256'da tanımlı,50'de NA. Source1061 PT uzayının tamamında performans iddiası kurulamaz. Kaynakta görünmeyen çift gerçek biyolojik negatif değildir;NA/sözlük dışı/abstention sıfır başarıya çevrilmedi.

## 9. Gerçek girdi ve yan etki kayıt sıralaması örneği

Örnek sonuçlardan önce run_config'te alfabetik ilk primary paired54 ID olarak sabitlendi:**{example['drug_id']} {example['name']}**. Gerçek model işi **{example['actual_model_job']}**;ilaç primary outer3 test query'sidir,train'e girmedi. Kaynak temiz kimya:MW733,937/LogP1,7856/HBD5/HBA14/TPSA193,91;target2/enzyme3/transporter6/carrier0 doğrulanmış accession. Bunlar girdidir,importance/SHAP sonucu değildir.

{table(rank[['rank','class_id','PT_name','observed_record_s','score_observed_record_proxy']].head(12))}

![Erythromycin gerçek girdi ve query sıralaması](figures/WP09/training_v1/07_real_drug_ranking_example.png)

**Yorum:** Yeşil kaynak kaydı var,kahverengiunknown;değerlendirme rengi encoder girdisi değildir. Örneğin yüksek skorluunknown PT gerçek yanlış pozitif veya kesin klinik yan etki diye etiketlenemez. Sigmoid bu modelde **uncalibrated observed-record ranking score**'dur,hasta yan etki olasılığı değildir. Örnek bir ilaç önerisi,prospektüs doğrulaması,nedensel açıklama veya hasta güvenliği sonucu içermez. SHAP/Ollama/atom grafı başlatılmadı.

## 10. Belirsizlik,model başarısının sınırı ve yapılmayanlar

1000 percentile **eşleştirilmiş yapısal grup bootstrap**;ana61 connectivity/stres40 grup,bütün üyeler birlikte ve bütün modeller aynı çekimlerle. Seed20261106+9000+protocol_index eski baseline ile aynı. AP average precision'dır,trapez PR-AUC değildir. Drug-AP/microAP/microAUROC CI üretilir;sınıf metrikleri destek/NA ve betimleyici fold özetiyle ayrıca verilir. Üç null modeli için her aynı çekimde üç metriğin eşit ortalaması alınır;replicalar bağımsız hasta/ilaç örneği sayılmaz.

CI **sabit OOF modellerine ve üç sabit null'a koşulludur**;nested CV yeniden fit'i,initialization varyansı,global null örnekleme dağılımı,veri kaynağı yanlılığı veya dış kohort belirsizliğini kapsamaz. Tek önceden sabit model-init seed politikası kullanıldı. Birlikte raporlanan birçok karşılaştırma keşifseldir;genel istatistiksel üstünlük veya bağımsız dış doğrulama kanıtı değildir.

PPI faydasının gösterilememesinin olası nedenleri küçük örneklem,az/seyrek PT desteği,insan PPI erişiminin çoğunlukla taşıma/metabolizma rolleri olması,query unseen proteinlerin self yolu,rol-mean bilgi kaybı ve SIDER kayıt sürecinin etiket mekanizması olabilir. Bunlar ayrıştırılmış nedenler değildir;veriye bakarak yeni “daha iyi” hiperparametre/eşik deneyi yapılmadı. Protein/PPI biyolojisinin genel yararsızlığı sonucuna gidilmez.

Bu bir **protein-PPI GNN + skaler kimya + rol readout** modelidir. Molekül iç atom/bağ GNN,Graph-in-Graph'in moleküler alt graf bileşeni veya tam moleküler GiG uygulanmadı. Gerçek biyolojik negatif/olay-payda/hasta verisi yoktur;klinik risk,kalibrasyon,özgüllük,nedensellik veya hasta güvenliği doğrulaması yapılamaz. WP10/SHAP/LLM veya yeni veri kaynağı başlatılmadı.

## 11. Testler,tekrar üretim ve artefakt rehberi

**24/24 gerçek trainer testi geçti ({match.group(2)} saniye).** Gerçek optimizer/gradient/weight update,aynı init/ID/PT,inner-only epoch seçimi,frozen target/proxy,NPZ'den skor,aynı outer fit'in tekrar üretimi,gerçektrainer'da outer label/value mutation,query train-state izolasyonu,trained PPI/noPPI forward,null sabitliği/NA,kusurlu fitte NA/tek-outcome reddi,bağımsız sklearn AP,mikro/grup bootstrap,kapsam ve frozen B0/B1/B2 değerleri test edildi. Testler küçük kontrollü RAM yeniden fit'leri yapar;model dosyalarını/protokolü değiştirmez. Bütün ana190 fit teknik olarak tamamlandı;teknik başarısızlık veya düşük sonuç nedeniyle tekrar araması yapılmadı.

Tam tekrar üretim aynı çevrede toleranslı olarak sınandı;farklı kütüphane/CPU sürümlerinde bit düzeyi garanti yoktur. Gerçek model ve seçilmiş checkpoint hash'leri korunur;ana producer `training_complete.json`/scoring tamamlandıysa yeni fit/score üstüne yazmayı reddeder. Aynı sürümle sonuç sonrası yeniden ayarlama yapılmaz.

| Çıktı | İşlev |
| --- | --- |
| models/WP09_PPI_v3_training_v1/ | 190 eğitilmiş NPZ +190 sürümlü metadata;inner/outer/null ayrımı |
| reports/qa/WP09/training_v1/run_config.json | Açık kullanıcı eğitim onayı ve sonuç öncesi runtime/evaluation sözleşmesi |
| model_fit_summary.csv,history/ | Tüm epoch/loss/validationAP/gradient/optimizer izi |
| selections/,selection_complete_before_test_scoring.json | Inner-only epoch kararları ve test scoring öncesi commit |
| outer_training_and_evaluation.csv | Fold epoch/trainloss/testAP ve kapsamı birleştiren kayıt |
| oof_predictions.csv,prediction_status_all62.csv | Gerçek61 ilaç OOF skorları ve62-ID abstention/NA durumları |
| metrics_with_group_CI.csv,paired_differences_group_CI.csv | Paired54/own61 gerçek/net-frekans kıyasları ve koşullu CI |
| per_drug_metrics.csv,per_class_metrics.csv,outer_fold_metrics.csv | İlaç/sınıf/fold destek ve NA durumları |
| target_trainability_audit.csv,feature_fit_provenance.csv | Train-only PT ve dönüşüm fit-ID kaynak izi |
| comparison_keys.csv,excluded_comparison_keys.csv,evaluation_coverage.csv | Aynı drug/fold/PT anahtarları ve kapsam/unknown/sözlük dışı pozitifler |
| excluded_inner_jobs.csv | Başarısıznull nedeniyle bütün varyantlarda çalıştırılmayan10 inner fit |
| example_drug_inputs.json,example_drug_PT_ranking.csv | Önceden seçilmiş Erythromycin girdileri ve gerçekOOF sıralaması |
| model/input/prior manifestleri,test_results.txt,artifact_validation.json | Hash/provenans,test ve notebook/görsel kapanış kanıtı |
| notebooks/WP09_training_results.ipynb | 10 yürütülmüş kod hücresi,8PNG ve Türkçe bilimsel yorum |
| reports/figures/WP09/training_v1/ | Loss/epoch/baseline/ablation/coverage/gradient/örnek PNG ve offline interaktif ilaçAP HTML |
| scripts/wp09_train.py,wp09_train_evaluate.py,wp09_train_summary.py | Modüler gerçektrainer,ayrı scoring,değerlendirme/provenans |
| tests/test_wp09_training.py | Gerçek trainer sınırları ve bağımsız metrik doğrulamaları |

Notebook yalnız kayıtlı QA okur;fit çalıştırmaz. Normal yeniden kontrol:`python -m unittest discover -s tests -p test_wp09_training.py -v`;çıktıyı önceki logu ezmeden yeni doğrulama kaydına yaz. Ağırlıkları değerlendirmek için source/graph/config hash'leriyle restore API'si kullanılır;eski producer'ları çalıştırmak gerekmez.

**WP09 gerçek eğitim ve karşılaştırmalı değerlendirme tamamlandı. PPI kullanımı teknik olarak doğrulandı;bu deneyde ek primary drug-AP faydası gösterilmedi. Sonuç incelemesi için kullanıcı onayı bekleniyor;WP10'a geçilmedi.**
'''
    (ROOT/'reports/WP09_TRAINING_RESULTS.md').write_text(report,encoding='utf-8')
    card=f'''# WP09 — Eğitilmiş model kartı

Sürüm **{VERSION}**,06.11.2026. Bu tek deployment modeli değil,nested CV'nin190 bileşen model koleksiyonudur.190 NPZ/JSON çifti `models/WP09_PPI_v3_training_v1/` altında;manifest model hash'lerini korur.

**Görev:** yeni ilaçlar için SIDER observed-record sıralaması. Unknown doğrulanmış biyolojik negatif değildir. Sigmoid skoru klinik olasılık/kalibrasyon veya hasta güvenliği doğrulaması değildir. Klinik tedavi önerisi veya nedensel mekanizma iddiası yoktur.

**Mimari:** protein56→32 paylaşılan projection,tek residual mean PPI,dört ayrı role mean+maske,skaler kimya5→8 ve train PT lineer başlığı. Atom–bağ GNN yok;tam moleküler GiG değildir. NoPPI/real700/shuffledR0,R1,R2 aynı init/context-ID/PT kapsamındadır. Nonhuman/PPI'sız sequence self yolunda;K12 PPI/context80 yoktur. Feature kaynakları frozen WP04/05/08;PT/kategori/sıklık/kalite_skoru/STRINGscore düğüm özelliği değildir.

**Fit:** fullbatch proxy BCE;AdamW lr0,001/weight_decay0,001;CPU1thread,float32;max200,inner patience20/min_delta0,0001;outer epoch ortak inner best-epoch medyanından .5yukarı. Base20261106 sabit seed;inner/outer başlıkları kendi fittable PT listesidir. Train-only scaler/target/graph;test ilaçları ve ters/SE ilişkileri eğitim grafında yoktur. Query train-state'i değiştirmez;unseen protein self-only. Kişiselleştirilmiş girdi yoksa abstention.

**Sonuç:** ana paired54 drugAP noPPI0,6430/real0,6429/shuffled3mean0,6433. Real−noPPI/real−shuffled koşulluCI sıfırı içerir;ekPPI faydası gösterilemedi. B1/B2/B0 sabit ve yeniden fit edilmedi. Stres B2 kazancı noPPI'da da vardır;PPI'ye atfedilemez. Üç null için metrik ortalaması alınır,tahmin ensemble'i veya en iyi tekrar yoktur.

**Kapsam:**62 envanter/61 skor/Methenamine abstention;paired54 primary. Kaynak1061 PT,6416 pozitif;primarypaired54'te1685 pozitif skor sözlüğü dışında. Tüm PT evreninde başarı iddiası yok. Class-metric NA ve unknown korunur. Bütün modellerde aynı karşılaştırma anahtarları kullanılır.

**Sınırlar:** önceki baseline sonuçları görülmüş olduğundan keşifsel iç doğrulama;1000 grup bootstrap CI sabit OOF/3null'a koşullu,full-retraining veya bağımsız dış doğrulama değildir. Tek init seed politikası;küçük kohort/seyrek etiket/source-reporting yanlılığı vardır. Lower/similar sonuçlar raporlandı;sonuç sonrası tuning yok.

**Doğrulama:**24 gerçektrainer testi;190 fit/10867 optimizer adımı;gerçekPPImessage gradient/forward/query izolasyonu,heldout mutasyon,checkpoint/epoch ve independentAP testleri. Model NPZ'leri yalnız sayısal state_dict'tir;kimlik/target/split/null/source metadata JSON yanındadır. Kütüphane sürümleri/environment ve hash manifestiyle kullanılır;cross-version bitwise garanti yoktur.

Detaylar:[eğitim raporu](WP09_TRAINING_RESULTS.md),`reports/qa/WP09/training_v1/`. WP10 veya moleküler encoder eğitimi yapılmadı.
'''
    (ROOT/'reports/WP09_TRAINING_MODEL_CARD.md').write_text(card,encoding='utf-8')
    print(f'WP09 Turkish training report/model card written; {preserved} previous files unchanged')


if __name__=='__main__':main()
