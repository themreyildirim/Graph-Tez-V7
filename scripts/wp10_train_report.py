"""Gerçek WP10 kayıtlarından sonuç raporu ve model kartı;refit yapmaz."""
import json,re
import pandas as pd
from wp10_train import ROOT,QA,MODEL,NAMES


def table(frame,digits=6):
    def fmt(value):
        if pd.isna(value):return 'NA'
        if isinstance(value,float):return f'{value:.{digits}f}'
        return str(value).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def main():
    if (QA/'artifact_validation.json').exists():raise RuntimeError('Finalized run;reports immutable')
    done=json.loads((QA/'training_complete.json').read_text(encoding='utf-8'))
    fit=pd.read_csv(QA/'model_fit_summary.csv');metrics=pd.read_csv(QA/'metrics_with_group_CI.csv')
    effects=pd.read_csv(QA/'factorial_contrasts_group_CI.csv');refs=pd.read_csv(QA/'paired_reference_differences.csv')
    cov=pd.read_csv(QA/'evaluation_coverage.csv');example=json.loads((QA/'example_drug_inputs.json').read_text(encoding='utf-8'))
    tests=(QA/'tests_actual_trainer.txt').read_text(encoding='utf-8-sig');test=re.search(r'Ran ([0-9]+) tests in ([0-9.]+)s',tests)
    assert test and tests.rstrip().endswith('OK')
    ap=metrics[metrics.scope.eq('paired54')&metrics.metric.eq('drug_macro_AP')]
    own=metrics[metrics.scope.eq('own61')&metrics.metric.eq('drug_macro_AP')&metrics.model.isin(NAMES)]
    effect=effects[effects.scope.eq('paired54')&effects.metric.eq('drug_macro_AP')]
    proof=fit.groupby('model').agg(fits=('job_key','size'),optimizer_steps=('optimizer_steps','sum'),min_weight_change=('selected_state_L2_change','min'),
        min_max_PPI_gradient=('maximum_message_gradient_norm','min'),min_max_atom_gradient=('maximum_atom_message_gradient_norm','min'),min_max_bond_gradient=('maximum_bond_message_gradient_norm','min')).reset_index()
    outer=fit[fit.inner_fold.eq(0)]
    epoch=outer.pivot(index=['protocol','outer_fold'],columns='model',values='best_epoch').reset_index()
    report=f'''# WP10 — Gerçek dört kollu eğitim ve değerlendirme

07.11.2026. **Eğitim ve değerlendirme tamamlandı; kullanıcı sonuç incelemesi bekleniyor. WP11 başlatılmadı.** Kullanıcının açık onayıyla kabul edilmiş WP10 encoder'ı gerçek PT kayıtları üzerinde eğitildi. Birincil deney yalnız A0P0/A0P1/A1P0/A1P1 içerir; shuffled PPI deneyleri eklenmedi.

## 1. Bilimsel sonuç

Ana paired54 drug-macro observed-record AP: **A0P0=0.642740, A0P1=0.643636, A1P0=0.645930, A1P1=0.646234**. Aynı mimaride atom dalı küçük pozitif farklar verdi: PPI kapalıyken+0.003189 (koşullu%95CI[+0.000398;+0.006675]), PPI açıkken+0.002598 ([+0.000717;+0.004763]). Ana marjinal atom farkı+0.002894 ([+0.000773;+0.005470]).

**Bu küçük, sabit OOF'ye koşullu keşifsel bir kazanımdır; genel üstünlük veya dış doğrulama değildir.** Stres protokolünde koşullu atom farklarının CI'ları sıfırı içerir. Stres marjinal atom farkının alt sınırı yaklaşık+0.000006 olup sıfıra çok yakındır; güçlü bir sağlamlık kanıtı olarak sunulmaz.

Ana marjinal PPI farkı+0.000600 (CI[−0.001133;+0.002316]); etkileşim−0.000591 ([−0.003102;+0.001541]). **Ek PPI katkısı veya atom–PPI sinerjisi gösterilmedi.** Negatif etkileşim nokta tahmini de antagonizma kanıtı değildir. Atom ve PPI'nin forward/gradient içinde gerçekten kullanılması teknik olarak doğrulandı; tahmin katkısı ayrı ölçüldü.

A1P1−B0_like_B2=−0.000370 (CI[−0.011528;+0.010018]); A1P1−B1=−0.009408 ([−0.025901;+0.005600]); A1P1−WP09_realPPI=+0.003355 ([−0.002902;+0.010505]). Bu referanslara karşı belirgin ek üstünlük gösterilmedi. B2 karşısındaki ana+0.019995 farkının CI'ı pozitiftir; ancak mimari, nonlineer öğrenme ve kapasite de değiştiğinden bu toplam fark yalnız atom veya PPI topolojisine atfedilemez.

## 2. Onay, koruma ve değişmeyen kaynaklar

AGENTS, aktif ROADMAP, WP10 teknik raporu, veri sözleşmesi ve eğitim kapısı esas alındı. Yeni yol haritası oluşturulmadı. Tarihsel öneri/uygulama config'leri değişmedi; yeni eğitim onayı ve sonuç öncesi kararlar `training_v1/run_config.json` içine yazıldı. `code_contract_before_fit.json` kodu, job üyeliklerini ve sözleşmeyi üretim fitlerinden önce dondurdu.

**{done['prior_files_verified']} önceki dosya** içerik hash'iyle korundu: B0/B1/B2 veWP09 modelleri/skorları, eski notebook/rapor/testler, splitler, hedef sözlükleri, seed veQC kararları değişmedi. Yeni biyolojik kaynak, API, paket kurulumu veya büyük ham dosya taraması yoktur. Yerel DrugBank XML kaynaklı WP04 SMILES/CID köprüsü, RDKit2026.09.1/PyG2.8.0, temiz56 protein özelliği, dört rol ve strict insan STRING700 kullanıldı. K12/MG1655 koşullu ağ ve80 özelliksiz context eklenmedi.

Envanter **62 ilaç/1061 kaynak PT/6416 pozitif ilişki** olarak korundu. Atom dalı54 QC uygun yapıda açık, sekiz inceleme kaydında maskeli kapalıdır. Gentamicin fragmentleri ve belirtilmemiş stereokimya korunur. Methenamine girdisiz abstention; Tobramycin protein eksiğiyle mevcut kimya/atom yollarında kalır. ID/PT sıklığı/kalite_skoru veya hedeflerden türetilmiş skorlar girdi değildir.

## 3. Gerçek eğitim ve optimizer kanıtı

**152/152 fit OK:112 inner+40 outer model, toplam{done['optimizer_steps']} gerçek optimizer adımı.**152 sayısal NPZ ve152 metadata JSON ayrı sürümde saklandı; bütün62 üzerinde ayrıca deployment fit'i yapılmadı. Dört kol aynı contextte aynı başlangıç ağırlıkları, hedefler, uygun ilaçlar ve150 boyutlu mimariyi kullanır.

Protein56→32 tek residual mean-PPI; kimya5→8; dört ayrı rol readout; atom44/bağ14, hidden16 tek bond-aware residual mean, molekül mean→8 ve atom maskesi. Başlıksız5512, K PT ile5512+151K parametre. A0 atom bloğu/maskesi0; P0 protein komşu mesajı0. A0 molekül parametreleri gradient almaz ve değişmez. P0'da kullanılmayan sıfır-gradientli mesaj ağırlığının AdamW decay ile kayması komşuluk kullanımı kanıtı sayılmaz.

{table(proof,8)}

![Gerçek optimizer ve gradient](figures/WP10/training_v1/02_actual_optimizer_gradients.png)

**Yorum:**Aktif dallara gerçek eğitimde gradient ulaştı, seçilmiş ağırlıklar değişti. Bu teknik öğrenme kanıtıdır; biyolojik nedensellik veya performans üstünlüğü değildir.

Full-batch observed-record proxy BCEWithLogitsLoss, class/pos weight yok; AdamW lr0.001/weight_decay0.001; CPU1 thread, float32 ve deterministik algoritmalar kullanıldı. Sabit girdiler bir kez doğrulanarak aynı kabul edilmiş katman hesabı yürütüldü; bu yol dört kolda referans encoder ile **çıktı ve gradient bakımından bire bir eşit** olarak test edildi. Encoder veya hiperparametre değiştirilmedi.

## 4. Nested CV ve test sınırı

Ana connectivity dış5/iç3 ve ayrı scaffold/≥0.8 stres üyelik/hash'leri aynı kaldı. Eski ortak inner politikası korundu: primary outer2 inner2/3; stress outer2 inner1/3; diğer outerlarda üç inner. Önceden dışlanan iki bağlam dört model için8 iş olarak ayrı tabloda durur. Bu turda yeni null denenmedi veya başarılı fold araması yapılmadı.

Inner max200/patience20/min_delta0.0001; ilk finite AP checkpoint'i ve daha sonra>min_delta iyileşme seçildi, eşitlikte erken epoch korundu. Her kolun outer epoch'u aynı ortak inner kümesindeki kendi best-epoch medyanından .5 yukarı belirlendi. Outer son eğitimleri{int(outer.best_epoch.min())}–{int(outer.best_epoch.max())} epoch'tur.

{table(epoch)}

![Gerçek eğitim eğrileri](figures/WP10/training_v1/01_training_curves.png)

**Yorum:**Grafik ilk sıralı inner bağlamın dört gerçek eğrisidir; bütün152 history dosyası saklıdır. Train loss güncelleme öncesi, validation ölçüleri güncelleme sonrası kaydedilir. Outer test hiçbir seçim veya early-stop kararında kullanılmadı.

Mevcut B2 train-only sözlük/fittable maskeleri aynen kullanıldı; en az5 pozitif kullanılabilir ilaç ve2 bağımsız grup desteği test edildi. Train'de tek proxy sonucu olan25 context/PT olayı başlık dışında/NA kaldı; fallback yoktur. Bu25 benzersiz PT sayısı değildir. Dönüşümler eski train-only istatistiklerdir; yeni scaler fit edilmedi.

Gerçek fit API'si yalnız exact train/validation etiket sözlüklerini kabul eder. Validation girdisi outer test ilaçları ve test-only unseen proteinlerden arındırılır; moleküller de yalnız istenen train/validation ID'lerinden alınır. Kaynak label tablosunun bellekte okunması heldout etiketlerin trainer'a geçmesi anlamına gelmez; gerçek mutasyon testinde outer etiket/kimya/molekül değerleri değiştirildiğinde checkpoint ve parametreler aynı kaldı.

Tüm inner seçimleri ve outer ağırlıklar hash ile kaydedildikten sonra ayrı score aşaması143896 OOF çift skoru üretti. Query train protein cache'ini veya model durumunu değiştiremez. WP07 inceleme grafı yüklenmedi. Fit/validation başarısızlığı olsaydı ortak finite/evaluable kesişim/min2 ve bütün outer dört-kol NA politikası uygulanacaktı; **bu çalışmada ek teknik fit başarısızlığı olmadı**. Düşük skorlar elenmedi.

## 5. Aynı kapsamda birincil sonuçlar

{table(ap[['protocol','model','estimate','CI95_low','CI95_high']])}

![Ortak kapsam ve referanslar](figures/WP10/training_v1/03_shared_AP_references.png)

**Yorum:**B0/B1/B2 veWP09 sabit skorları aynı anahtarlarda yeniden değerlendirilir; hiçbir referans yeniden fit edilmedi. Eski141 boyutlu WP09, yeni150 boyutlu A0 kontrol hücresinin yerine geçirilmedi. Aynı mimarili dört kol katkı sorusunu ayırır; modellerin test sonuçlarına göre yeni ayarı yapılmadı.

## 6. Önceden tanımlı factorial kontrastlar

{table(effect[['protocol','contrast','estimate','CI95_low','CI95_high']])}

![Atom,PPI,etkileşim](figures/WP10/training_v1/04_factorial_contrasts.png)

**Yorum:**atom_P0=A1P0−A0P0; atom_P1=A1P1−A0P1; PPI_A0=A0P1−A0P0; PPI_A1=A1P1−A1P0. Etkileşim bu atom farklarının farkıdır. Marjinal atom/PPI farkları iki koşullu farkın eşit ortalamasıdır, skor ensemble'i değildir. Ana atom farkları küçüktür ve bu koşullu analizde pozitiftir; stresin koşullu atom aralıkları sıfırı içerir. PPI ve etkileşim için tutarlı ek katkı gösterilmedi. Bu kontrastlar biyolojik nedensel etkiler değildir.

1000 eşleştirilmiş yapısal grup bootstrap tekrarı bütün modeller için aynı çekimleri kullanır; Levofloxacin/Ofloxacin aynı grupta örneklenir. Seed20261106+9000+protocol_index korundu. CI sabit OOF modellerine ve tek init seed politikasına koşulludur; yeniden eğitim, seed/örneklem varyansı, kaynak kayıt yanlılığı veya dış kohort belirsizliğini kapsamaz. Çoklu keşifsel karşılaştırmalar genel istatistiksel üstünlük veya bağımsız dış doğrulama olarak sunulmaz. Sıfırı içeren aralık eşdeğerlik kanıtı değildir.

## 7. Own61, bilinmeyenler ve kapsam sınırı

{table(own[['protocol','scope','model','estimate','CI95_low','CI95_high']])}

{table(cov[cov.model.eq('A1P1')][['protocol','scope','scored_drugs','scored_pairs','observed_positive_scored','unknown_NOT_verified_negative','out_of_scored_vocab_positive','class_AUROC_NA']])}

![Pozitif ve unknown kapsamı](figures/WP10/training_v1/05_coverage_positive_unknown.png)

**Yorum:**Her model61 ilaç skorlar;62 envanter korunur ve Methenamine abstain kalır. Ana paired54'te13964 çift=3820 kaynak pozitif+10144 unknown. Aynı ilaçlardaki5505 kaynak pozitifin **1685**'i hedef/fit kapsamı dışındadır;bu bütün62'nin yanlış-negatif sayısı değildir. Tüm1061 PT uzayında başarı iddiası yoktur.50 pooled class-AUROC NA ayrıca raporlanır. Complete-case53 yeni eğitim kohortu olarak kullanılmadı.

Micro AP ve fold içi class-AUROC ayrı tablolarda yer alır. AP average precision'dır, trapez PR-AUC değildir. Pooled class-AUROC yalnız diagnostic olarak işaretlendi; fold içi sınıf-AUROC tanımlı fold özetlerinin betimleyici ortalamasıdır ve bağımsız-fold CI üretilmedi. Unknown çiftler gerçek biyolojik negatif değildir; kalibrasyon/özgüllük/klinik risk iddiası yoktur.

## 8. Gerçek model ve örnek ilaç çıktısı

Örnek sonuçlardan önce belirlenen alfabetik ilk primary paired54 ID'dir: **{example['drug_id']} {example['name']}**, primary outer3 test query. Dört modelin aynı PT sözlüğündeki gerçek OOF skorları `example_drug_PT_ranking.csv` içinde saklıdır. Kaynak kimya MW733.937,LogP1.7856,HBD5,HBA14,TPSA193.91; target2/enzyme3/transporter6/carrier0 ve QC açık molekül girdisi kullanıldı.

![Gerçek eğitilmiş ağırlık ve temsil](figures/WP10/training_v1/06_actual_trained_model.png)

**Yorum:**Projection matrisi ve8 boyutlu molekül temsili primary_o03_final_A1P1 NPZ'sinden gelir; temsili veri değildir. Bu koordinatlar önem/SHAP/nedensel açıklama değildir. WP11 yapılmadı.

![Gerçek OOF sıralamaları](figures/WP10/training_v1/07_actual_drug_rankings.png)

**Yorum:**Hedefler A1P1'in gerçek ilk12 PT sırasından seçilerek aynı PT'lerde dört modelin kaydedilmiş skorları gösterilir. Notebook her modelin kendi ilk10'unu da verir. Unknown yüksek skor gerçek yanlış pozitif veya klinik yan etki ilan edilmez. Bu tedavi önerisi, hasta riski hesabı veya klinik doğrulama değildir.

## 9. Doğrulama ve dosyalar

**{test.group(1)}/{test.group(1)} trainer testi geçti;{test.group(2)} saniye.** Bunlar13 üretim fit/OOF/factorial testi ve6 preflight testidir. Gerçek optimizer/gradient/ağırlık güncellemesi, train-only PT ve grup desteği, heldout label/value mutation, encoder eşitliği, aynı init/ID, epoch commit, kayıtlı NPZ'den referans encoder ile skor üretimi, aynı outer fit'in tam tekrar üretimi, query/cache izolasyonu, bağımsız sklearn AP, aynı karşılaştırma anahtarları ve factorial aritmetiği doğrulandı. Kontrollü RAM test fitleri üretim modeline yazmaz veya hiperparametre aramaz.

| Çıktı | İşlev |
| --- | --- |
| models/WP10_factorial_training_v1/ |152 eğitilmiş NPZ+152 metadata;seed/PT/ID/epoch/hash ve kaynak izi |
| reports/qa/WP10/training_v1/run_config.json | Açık eğitim onayı ve sonuç öncesi yöntem/kontrast/CI kararları |
| training_jobs_frozen.csv,code_contract_before_fit.json |152 iş ve kaynak/kod sözleşmesinin sonuç öncesi hash'i |
| model_fit_summary.csv,history/,selections/ | Her fitin epoch/loss/AP/gradient/optimizer ve seçim izi |
| outer_training_and_evaluation.csv | Fold bazlı epoch/loss/test metrikleri ve kapsam |
| oof_predictions.csv,prediction_status_all62.csv | Gerçek skorlar,61 kapsam ve62-ID abstention/NA durumu |
| metrics_with_group_CI.csv,factorial_contrasts_group_CI.csv,paired_reference_differences.csv | Aynı kapsamda metrikler,atom/PPI/etkileşim ve sabit referans farkları |
| comparison_keys.csv,evaluation_coverage.csv,per_class_metrics.csv | Exact anahtarlar,unknown/kapsam dışı/sınıf NA ve destekler |
| feature_fit_provenance.csv,fold_train_validation_test_scope.csv | Train-only dönüşüm,hedef ve graf/molekül ID kaynağı |
| example_drug_inputs.json,example_drug_PT_ranking.csv | Gerçek test query girdisi ve dört model sıralaması |
| notebooks/WP10_factorial_training.ipynb |9 çalıştırılmış kod hücresi,7 gerçek PNG ve Türkçe bilimsel yorum |
| tests_actual_trainer.txt,artifact_validation.json,manifestler | Testler,hash/kaynak/model/notebook kapanış kanıtı |

## 10. Kapanış sınırı

Bu, **molekül atom–bağ encoder'ı ve protein-PPI/rol dalını geç füzyonla birleştiren GNN** deneyidir. Bütün tez veya tüm olası Graph-in-Graph mimarileri tamamlandı denmez. Atom dalının küçük koşullu kazanımı daha güçlü frekans/kimya referanslarına genel üstünlük sağlamadı; ek PPI veya sinerji gösterilmedi. Kaynak kayıtları sıralandı; klinik yan etki olasılığı,nedensellik veya hasta güvenliği doğrulaması yapılmadı.

**WP10 eğitim ve değerlendirmesi tamamlandı;sonuçlar kullanıcı incelemesine sunulur. WP11'e geçilmedi.**
'''
    card='''# WP10 dört kollu eğitim model kartı

07.11.2026. Sürüm: WP10-molecular-protein-factorial-observed-record-training-v1.

Görev:S​​IDER observed-record ilaç–PT sıralaması. Unknown doğrulanmış biyolojik negatif değildir. Sigmoid skorları klinik risk/kalibrasyon/nedensellik veya hasta güvenliği doğrulaması değildir.

152 nested-CV bileşen modeli;tek tüm-kohort deployment fit'i yok. A0P0/A0P1/A1P0/A1P1 aynı150 boyutlu mimari,context init/ID/hedef kapsamı;shuffled deney yok. Atom44/bağ14→hidden16 tek bond-aware residual mean→mean8;protein56→32 tek mean-PPI;kimya5→8;dört rol+maskeler.5512+151K parametre. Strict insan PPI700;K12 koşullu ağ/context80 yok.

Kaynak62 ilaç/1061PT/6416pozitif;54 atom maskesi açık/8QC kapalı;61 kişiselleştirilmiş girdi uygunluğu,Methenamine abstention. Eğitim grafı train-only;query ayrı readout. Frozen scaler/PT/split/seed20261106 korunur. AdamWlr.001/wd.001,proxyBCE,max200,patience20,min_delta.0001;outerepoch ortakinner bestepoch medyanı. B0/B1/B2/WP09 yeniden eğitilmedi.

Ana paired54 AP:A0P0 .642740,A0P1 .643636,A1P0 .645930,A1P1 .646234. Küçük pozitif ana atom kontrastları koşulluCI'da sıfır üzerinde;stres koşullu atom CI'ları sıfırı içerir. PPI veetkileşim katkısı gösterilmedi. B0/B1/WP09'a genel üstünlük yok. B2 farkı yalnız atom/PPI etkisi sayılmaz.

1000 yapısal grup bootstrap CI sabitOOF'ye koşullu;seed/yenidenfit/kaynak/dışkohort belirsizliğini kapsamaz. Önceki sonuçlar görüldüğünden kıyas keşifseldir;çoklu karşılaştırmalar genel istatistiksel üstünlük kanıtı değildir.1685 ana paired54 kaynak pozitif hedef/fit kapsamı dışında;1061PT'nin tamamında performans iddiası yok.

19 gerçek trainer testi geçti.152 fit/8611 optimizer adımı;NPZ restore/reference skor ve tamouter tekrar üretimi,train-onlyPT/heldoutmutasyon/gradient/queryizolasyonu sınandı. Farklı library/CPU sürümlerinde genel bitwise garanti yok. Metadata ve manifestler kaynak/seed/target/fitID/state hash'ini taşır. Bu koleksiyon yalnız araştırma içindir;klinik kullanım doğrulanmadı.

Detaylar:WP10_TRAINING_RESULTS.md ve reports/qa/WP10/training_v1/. WP11 başlatılmadı.
'''.replace('S​​IDER','SIDER')
    for name,text in [('WP10_TRAINING_RESULTS.md',report),('WP10_TRAINING_MODEL_CARD.md',card)]:
        path=ROOT/'reports'/name
        if path.exists() and '--refresh-working-draft' not in __import__('sys').argv:raise RuntimeError('Report exists')
        path.write_text(text,encoding='utf-8')
    print('WP10 real training report and model card written')


if __name__=='__main__':main()
