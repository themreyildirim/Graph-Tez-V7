"""B0 ekinin sonuçlardan türetilen Türkçe raporu ve son artefakt doğrulaması."""
import json
import re
import pandas as pd
import nbformat
from wp08_b0_frequency import ROOT, QA, PREP, sha, check_preservation, write_json


def table(frame):
    def cell(x):
        if isinstance(x, float):
            return 'NA' if pd.isna(x) else f'{x:.4f}'
        return str(x).replace('|', '/')
    return '| ' + ' | '.join(frame.columns) + ' |\n| ' + ' | '.join(['---'] * len(frame.columns)) + ' |\n' + '\n'.join(
        '| ' + ' | '.join(cell(x) for x in row) + ' |' for row in frame.itertuples(index=False, name=None))


def main():
    preserved = check_preservation()
    inputs = json.loads((QA/'input_manifest.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p) == h for p,h in inputs.items())
    done = json.loads((QA/'evaluation_complete.json').read_text(encoding='utf-8'))
    assert sha(QA/'policy_before_B0_results.json') == done['policy_sha256']
    assert sha(QA/'train_frequency_estimates.csv') == done['frequency_sha256_unchanged']
    assert sha(QA/'B0_outer_query_scores.csv') == done['query_scores_sha256_unchanged']
    tests = (QA/'test_results.txt').read_text(encoding='utf-8')
    assert 'Ran 19 tests' in tests and tests.rstrip().endswith('OK')
    test_seconds = re.search(r'Ran 19 tests in ([\d.]+)s', tests).group(1)
    notebook = ROOT/'notebooks/WP08_B0_frequency_reference_v1.ipynb'
    nb = nbformat.read(notebook, as_version=4)
    nbformat.validate(nb)
    codes = [c for c in nb.cells if c.cell_type == 'code']
    assert len(codes) == 7 and all(c.execution_count for c in codes)
    assert not any(o.output_type == 'error' for c in codes for o in c.outputs)
    figures = ROOT/'reports/figures/WP08/B0_frequency_reference_v1'
    pngs = sorted(figures.glob('*.png'))
    assert len(pngs) == 5
    html = figures/'per_drug_frequency_reference_interactive.html'
    assert html.exists() and not re.search(r'<script[^>]+src=["\']https?://', html.read_text(encoding='utf-8'))
    validation = {
        'prior_files_verified_unchanged':preserved, 'input_hashes_verified':len(inputs),
        'tests_passed':19, 'test_seconds':float(test_seconds), 'executed_code_cells':len(codes),
        'static_PNG_count':len(pngs), 'PNG_visual_review':'All five viewed; labels/data legible',
        'HTML':'Plotly embedded, no external script dependency; no live browser interaction test',
        'no_B1_B2_refit_or_retuning':True, 'WP08_closed':False, 'WP09_started':False,
        'new_code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('wp08_b0_*.py'))},
        'test_code_sha256':sha(ROOT/'tests/test_wp08_b0.py'), 'notebook_sha256':sha(notebook)}
    write_json(QA/'artifact_validation.json', validation)
    metrics = pd.read_csv(QA/'metrics_with_group_CI.csv')
    differences = pd.read_csv(QA/'paired_differences_group_CI.csv')
    paired = metrics[metrics.scope.eq('paired54')]
    ap = paired[paired.metric.eq('drug_macro_AP')][['protocol','model','estimate','CI95_low','CI95_high']]
    delta = differences[differences.scope.eq('paired54') & differences.metric.eq('drug_macro_AP')]
    delta = delta[['protocol','first','reference','first_minus_reference','CI95_low','CI95_high']]
    secondary = paired[paired.protocol.eq('primary')].pivot(index='model',columns='metric',values='estimate').reset_index()
    secondary = secondary[['model','drug_macro_AP','micro_AP','class_macro_AP','micro_AUROC','class_macro_AUROC']]
    diagnostic = pd.read_csv(QA/'within_fold_AUROC_descriptive_mean.csv')
    diagnostic = diagnostic[['protocol','model','descriptive_mean_of_5_fold_class_AUROC']]
    populations = pd.read_csv(QA/'train_population_sizes.csv')
    populations = populations[populations.protocol.eq('primary') & populations.inner_fold.eq(0)]
    populations = populations.pivot(index='outer_fold',columns='reference',values='train_drugs').reset_index()
    coverage = pd.read_csv(QA/'coverage_and_positive_unknown.csv')
    coverage = coverage[coverage.protocol.eq('primary') & coverage.model.eq('B0_all_train')]
    coverage = coverage[['scope','scored_drugs','drug_AP_evaluable','observed_positive_scored',
                         'unknown_scored_NOT_verified_negative','out_of_scored_vocab_positive']]
    roadmap = pd.read_csv(QA/'ROADMAP_WP08_remaining_tasks.csv')
    split = json.loads((PREP/'frozen_split_manifest.json').read_text(encoding='utf-8'))
    text = f'''# WP08 — B0_frequency_reference_v1 keşifsel referans eki

Tarih: 06.11.2026. Durum: **B0 eki tamamlandı, kullanıcı incelemesi bekleniyor; WP08 açık, WP09 başlamadı.**

## Bulguların anlamı

Kullanıcının kabul ettiği ilk L2-LR sonuçları korundu: ana ortak kapsamda B1 drug-macro AP **0,6556**, B2 **0,6262**. Protein rol özetleri bu deneyin birincil metriğini artırmadı. B0, bu sonuçlar görüldükten sonra kullanıcı isteğiyle eklendi; **keşifsel, sonuç sonrası bir karşılaştırmadır**. İlk deneyin önceden belirlenmiş referansı olarak sunulamaz.

B1'in aynı train popülasyonundan türetilen B0 drug-AP'si **0,6438**; B1−B0 farkı **+0,0119**, %95 koşullu grup CI **−0,0021–+0,0274**. B1'in frekans referansını belirgin biçimde geçtiği gösterilemiyor. B2'nin eşleşen B0'ı **0,6466**; B2−B0 **−0,0204**, CI **−0,0438–+0,0032**. Ana protokolde B2 için de bir artış yok. Stres protokolünde B2'nin B0'a göre farkı **−0,0469**, CI **−0,0769–−0,0176**; düşük sonuç gizlenmedi. Bunlar çoklu keşifsel karşılaştırmalardır; doğrulayıcı üstünlük/başarısızlık testi veya klinik doğruluk iddiası değildir.

## 1. Dondurulan yöntem ve train popülasyonu

Skor, her PT için **ilgili train'de bu kaydı olan benzersiz ilaç sayısı / tanımlı train ilaç sayısı**. Düzeltme, smoothing, logit veya sonuçla ayarlanan dönüşüm yok. Kimya, protein, PPI, ATC değerleri kullanılmadı. Eligibility dosyasından yalnız ID/model/uygunluk sütunları okundu; bunlar paydanın kimliklerini tanımlar. Etiket frekansları B1/B2 girdilerine eklenmedi.

| Referans | Train paydası | Kullanım |
| --- | --- | --- |
| B0_all_train | Splitteki bütün train ilaçları | Biyolojik girdiden bağımsız nüfus referansı |
| B0_like_B1 | Train ∩ sabit B1 input-eligible kimlikleri | B1 ile aynı kullanılabilir-train popülasyonu |
| B0_like_B2 | Train ∩ sabit B2 input-eligible kimlikleri | B2 ile aynı kullanılabilir-train popülasyonu |

Ana outer-final paydaları:

{table(populations)}

Her iki protokolün toplam **40** inner/outer train bağlamında **120** popülasyon için sıklık ve kaynak train ID'leri saklandı. B0'ın ayarlanacak C değeri yok; inner sonuçlarıyla seçim yapılmadı. Inner sıklıklar yalnız kendi train'inden hesaplandı. B1/B2'nin seçilmiş C değerleri veya modelleri tekrar fit edilmedi.

B0 için biyolojik input gerekmediğinden **62/62** ilaca nüfus sıklığı sıralaması verilebilir. Bu, kişiselleştirilmiş girdi veya klinik olasılık değildir. Methenamine'e de bu açık statüyle referans verildi; B1/B2'nin Methenamine abstention kararı korundu. Eşleştirilmiş analizde eski B1/B2'nin skorladığı ilaç/PT anahtarları aynen kullanıldı; B0 ile LR abstention boşlukları doldurulmadı.

Hedefler mevcut kohort-train PT sözlüğünden alındı; yeni sınıf seçilmedi. Eşleştirilmiş analizde mevcut B1/B2 skor anahtarlarına bire bir join yapıldı. Böylece aynı ilaçlar, aynı outer fold ve aynı PT kapsamı kullanıldı. `own_B1`, `own_B2`, `paired54`, `complete_case53` ayrı saklandı. Complete-case53 aynı fit modellerin değerlendirme alt kümesidir; yeni eğitim değildir. B0_all62 ayrı, eşleştirilmemiş referanstır.

## 2. Birincil drug-macro observed-record AP

Ortak 54 ilaç, aynı hedefler ve aynı değerlendirilebilirlik maskesi:

{table(ap)}

Eşleştirilmiş farklar, aynı grup bootstrap ağırlıkları:

{table(delta)}

Sıklık referansının B1'e yakın AP'ye ulaşması, sık gözlenen PT kayıtlarının güçlü bir sıralama başlangıcı oluşturduğunu gösteriyor. **B1 AP'sinin yüzde kaçının frekans tarafından açıklandığı hesaplanamaz**: AP doğrusal bir açıklanan varyans ölçüsü değildir; B0/B1 oranı nedensel katkı yüzdesi vermez. Gözlenebilen ek değer, aynı örneklerdeki +0,0119 AP farkıdır ve belirsizlik aralığı sıfırı içerir. B0 başarısı da raporlama sıklığı/etiket yoğunluğu dahil kaynak kayıt mekanizmasını yansıtabilir.

AP, sıralama eşiklerinde hesaplanan average precision'dır; trapez PR-AUC ile değiştirilmedi. Unknown çiftler doğrulanmış negatif değildir. Buradaki binary proxy, gözlenen kaynak kaydını etiketsiz kaynak çiftlerinden ayıran sıralamayı ölçer. Klinik risk, kalibrasyon, özgüllük veya gerçek biyolojik negatif tanıma başarısı iddiası yoktur.

## 3. İkincil metrikler ve B2'nin AUROC yorumu

Ana ortak kapsam, eski B1/B2 değerleri değiştirilmeden:

{table(secondary)}

Drug-AP aynı ilaç içinde PT'leri sıralar; class-AUROC aynı PT için ilaçları sıralar. Dolayısıyla B2'nin drug-AP'si azalırken pooled class-AUROC'unun 0,4814'ten 0,5431'e yükselmesi farklı bir sıralama yönünü ifade eder; genel veya klinik üstünlük değildir.

**OOF birleştirme sınırı:** B0 aynı fold/PT için bütün test ilaçlarına aynı skoru verir. Pozitif ve unknown birlikte bulunan fold/PT'de AUROC tam **0,5** olur. Farklı foldların frekans skorlarını tek sütunda birleştirince B0 pooled class-AUROC'u yaklaşık 0,32 çıkabilir. Sabit PT için train frekansı `(toplam pozitif − ilgili test pozitif)/(toplam ilaç − ilgili test ilaç)` ilişkisine sahiptir; tamamlayıcı train/test frekansları, folda göre değişen hedef kapsamı ve skor ölçekleri birleşik metriği etkiler. Bu test etiketini skora katmak değildir; yalnız pooled yorumun sınırıdır. B0'ın biyolojik olarak ters tahmin yaptığı sonucuna gidilmez. Eski LR pooled AUROC değerleri de doğrudan tek bir ortak skor ölçeğindeki ayrım gücü olarak aşırı yorumlanmamalıdır.

Bu nedenle ek, **yalnız betimleyici** fold içi class-AUROC ortalamasını da gösterir:

{table(diagnostic)}

Ana protokolde B1 0,5513, B2 0,5716 iken stres protokolünde sıralama tersine döner. Beş fold bağımsız tekrar sayılmadı; bu ortalamalara t-CI veya üstünlük testi uygulanmadı. Sonuç sonrası tanısal ek, kilitli birincil metrik/hiperparametre seçimini değiştirmiyor.

## 4. Kapsam, değişen sözlükler ve 1.685 pozitif

{table(coverage)}

Ana ortak54 için **13964** skorlanan çift: **3820** gözlenen pozitif, **10144** unknown. Aynı ilaçlardaki **5505** kaynak pozitifin **1685** tanesi folda özgü skorlanan sözlük/fit kapsamı dışında. Bunlar otomatik yanlış negatif veya negatif etiket değildir. 1685 bütün 62 ilaçtaki eksik kayıt sayısı olarak sunulamaz. B0_all62 referansının farklı kapsamındaki dış pozitif sayısı da ayrı tabloda verilir.

Train desteği nedeniyle fold sözlükleri farklıdır; pooled union ortak54'te 306 CUI, class metriği hesaplanabilen 256, NA olan 50 CUI vardır. Başka foldda hedef olması ilgili test foldunda hedef olduğu anlamına gelmez. Pozitif veya unknown desteği bulunmayan ilaç/sınıf metrikleri NA kaldı; başarı sıfırı veya fallback olasılığı yapılmadı. Fold bazlı kapsam ve her sınıfın destek/NA durumları CSV'lerde tutuldu. Bu seçilmiş, değişken hedef uzayındaki AP/AUROC değerleri bütün kaynak PT uzayında performans iddiasını desteklemez. Tarihsel 30 kategori deneyi eski semantik uyarılarıyla ayrı tutuldu; B0 hedefi olarak yeniden tanımlanmadı ve PT ile tek skora birleştirilmedi.

## 5. Belirsizlik ve sızıntı kontrolleri

Ana protokolde 61 connectivity, streste 40 yapı grubu biriminden **1000** bootstrap çekimi kullanıldı; aynı çekimdeki grup üyeleri ve modeller birlikte ağırlıklandırıldı. Levofloxacin/Ofloxacin ayrılmadı. Foldlar veya ilaç–PT çiftleri bağımsız gözlem sayılmadı. Aralıklar sabit OOF modellerine ve sabit train frekanslarına **koşulludur**; bütün nested CV yeniden eğitimi, kaynak yanlılığı ve dış kohort belirsizliğini kapsamaz. Aggregate CI'larda 1000 geçerli çekim var; tekil NA kapsamı ayrı dosyalardadır. Train grupları tekrar örneklenerek frekanslar yeniden tahmin edilmedi; bu yüzden koşulsuz eğitim belirsizliği iddiası yoktur.

**19/19 test geçti ({test_seconds} saniye).** Testler 120 train popülasyonunu ve frekans pay/paydasını bağımsız hesaplar; heldout etiket mutasyonu ve heldout tekrarlarının skoru değiştirmediğini doğrular. Kimyasal/protein sütunları estimator tarafından reddedilir. Dondurulan hedefler, eski skor anahtarları, B1/B2 metrikleri, eşit-skor AUROC=0,5, bootstrap tekrarlanabilirliği, Methenamine statüsü ve notebook çıktıları sınanır. B1/B2 kodu fit amacıyla çalıştırılmadı; WP07 grafı veya yeni eğitim grafı üretilmedi. B0 sonuçları model girdisine dönüştürülmedi.

Koruma kontrolü **{preserved} önceki dosya** için SHA-256 eşitliğini doğruladı. Dokuz B0 girdi dosyasının hash'i ayrıca kayıtlı; modeller, seçilmiş C, split, hedefler ve QA değişmedi. Seed **20261106**; bootstrap seed politikası ilk deneydekiyle aynı. B0 policy hash: `{done['policy_sha256']}`.

| Kilit | SHA-256 |
| --- | --- |
| split_lock_v1.json | `{split['split_lock_v1.json']}` |
| outer_membership_v1.csv | `{split['outer_membership_v1.csv']}` |
| nested_partitions_v1.csv | `{split['nested_partitions_v1.csv']}` |
| B1/B2 OOF skor dosyası | `{done['B1_B2_score_file_sha256_unchanged']}` |
| B1/B2 selected_C.csv | `{done['selected_C_sha256_unchanged']}` |

## 6. Öğretici çıktılar ve yeniden üretim

- [Çalıştırılmış notebook](../notebooks/WP08_B0_frequency_reference_v1.ipynb): yedi kod hücresinin altında gerçek tablolar/grafikler ve Türkçe yorumlar.
- `reports/qa/WP08/B0_frequency_reference_v1/`: policy, girdi/koruma hash'leri, train ID/payda listeleri, sıklıklar, aynı anahtarlarla skorlar, fold/sınıf/ilaç metrikleri, CI farkları, destek ve test logu. `artifact_validation.json` son doğrulamayı saklar.
- `reports/figures/WP08/B0_frequency_reference_v1/01_…png`: train paydalarının farklılığını açıklar.
- `02_…png`: aynı 54 ilaçta ana/stres AP ve koşullu CI; frekansın güçlü referans olduğunu gösterir.
- `03_…png`: eşleştirilmiş AP farkı; bağımsız iki CI'ı gözle karşılaştırmak yerine aynı grup çekimleri kullanılır.
- `04_…png`: pooled ve fold içi class-AUROC ayrımı; tezde AUROC yorumunun kapsamını öğretir.
- `05_…png`: gözlenen pozitif/unknown ve kapsam dışı pozitifler; bütün PT uzayına genelleme sınırını gösterir.
- `per_drug_frequency_reference_interactive.html`: ilaç bazında B1/B2−eşleşen B0 AP farkını kaynak ID'leriyle inceler. Plotly betiği gömülüdür. Beş PNG görsel olarak incelendi; HTML için canlı tarayıcı etkileşim testi yapılmadı.

Kodlar ayrı `scripts/wp08_b0_frequency.py`, `wp08_b0_evaluate.py`, `wp08_b0_summary.py`, `wp08_b0_notebook.py`, `wp08_b0_report.py`; test `tests/test_wp08_b0.py`. Kaynak sayısal girdileri okumadan mevcut küçük QA tablolarıyla çalışır. Ham XML/STRING tekrar taranmadı, API/indirme/kurulum yapılmadı.

Temiz yeni bir çıktı ortamında sıra: frequency → evaluate → summary → notebook → `python -m unittest discover -s tests -p test_wp08_b0.py -v` → report. Mevcut v1 frequency komutu tamamlanma işareti varsa ezmeyi reddeder; sonuç sonrası yeniden tahmin etmeye izin vermez. Notebook yalnız kayıtlı sonuçları okur, eğitim çalıştırmaz. Kod/girdi/hash sınırları saklanır; farklı kütüphane sürümlerinde bit düzeyinde genel yeniden üretim garantisi verilmez.

## 7. Açık kalan WP08 ROADMAP görevleri

{table(roadmap)}

ATC/RF/MLP seçeneklerinin uygulanması veya gerekçeyle ertelenmesi için kullanıcı kapsam kararı gerekir. B0 eklendi diye B1/B2 yeniden ayarlanmadı. Bu ek WP08'i tamamen kapatmaz. **Kullanıcı onayı bekleniyor; WP09, PPI eğitimi veya sonraki modele geçilmedi.**
'''
    (ROOT/'reports/WP08_B0_FREQUENCY_REFERENCE.md').write_text(text,encoding='utf-8')
    print(f'B0 report written; {preserved} prior files unchanged; 19 tests passed; WP08 remains open')


if __name__ == '__main__':
    main()
