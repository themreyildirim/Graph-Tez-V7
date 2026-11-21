# WP08 — İlk baseline model kartı

06.11.2026 — Sürüm **WP08-observed-record-L2LR-v1**. Kullanıcı ilk eğitimi açıkça onayladı. Model dosyaları `models/WP08_baseline_v1/`, sonuç QA'sı `reports/qa/WP08/baseline_v1/` altındadır. Bu kart tek tüm-kohort deployment modeli değil, nested CV bileşen model koleksiyonunu açıklar.

## Görev ve doğru çıktı anlamı

Yeni ilaçlarda **SIDER'da gözlenen ilaç–yan etki kayıt ilişkilerinin sıralanması**. `s=1` kayıt var, `s=0` kaynakta kayıt yok. **Unknown doğrulanmış biyolojik negatif değildir.** Sigmoid(w·x+b) yalnız observed-record proxy sıralama skorudur; bireysel klinik yan etki olasılığı, özgüllük veya kalibrasyon iddiası yoktur. Kaynak kayıt olasılığı olarak da kalibrasyon değerlendirmesi yapılmadı. Hasta/olay/payda verisi kullanılmadı.

## Veri ve protokol

- 62 DrugBank ana ilacı envanterde korunur. Kaynak PT ilişkileri 6416 çift / 1061 CUI; nihai fold sözlüğü 1061'in tamamı değildir. Her ilgili train'de en az 5 pozitif kullanılabilir ilaç ve 2 bağımsız grup; historical30 ayrı semantik uyarılı referans.
- Connectivity kilitli 5 dış/3 iç nested CV; Levofloxacin/Ofloxacin aynı grupta. Seed 20261106. Ayrı scaffold OR Tanimoto>=0,8 stres protokolü. Split ve hazırlık SHA-256 değişmedi.
- B1: 5 QC-onaylı kimya+1 input maskesi (6 alan). B2: 5 kimya+4 ayrı rol×56 protein özeti+5 maske (234 alan). Ölçekler yalnız train ilaçları / benzersiz train-linked accession'lardan hazırlanmış kayıtlı dönüşümlerdir.
- Kimlikler yalnız join/provenans; PT/kategori/raporlama skoru/kalite_skoru/combined_score girdisi yok. Eksik blok standart nötr 0+maske, gerçek kimyasal/AA sıfır değil. Sekiz QC kararı korunur; context80/PPI yok. K12 PPI ana ağa alınmadı.

## Öğrenme ve seçim

PT/kategori başına L2 lojistik regresyon, liblinear, `l1_ratio=0`, `class_weight=None`, tol=1e-8, max_iter=10000, intercept açık ve liblinear sentetik intercept scaling=1. sklearn **1.9.0**, NumPy **2.4.6**, SciPy **1.17.1**, Python **3.11.3**. CPU threadpool=1.

C grid {0.1,1,10}; her outer için yalnız üç inner validation drug-macro observed-label AP'nin eşit fold ağırlıklı ortalaması. Aynı fold içinde bütün C adaylarında aynı ilaç/hedef kapsamı; NA'lar sıfır sayılmaz. Eşitlikte küçük C, tolerans 1e-12. Bütün seçimler outer test scoring'den önce hash'le commit edildi. Tek proxy sonuçlu train sınıfı fit edilmez, fallback olasılık yok. Sonuçlara göre ek fit/özellik/sözlük/seed araması yapılmadı.

400 bundle: 360 inner aday, 40 outer son model koleksiyonu. Toplam 46744 başarılı tek-hedef classifier fit'i, 287 tek proxy sonuç nedeniyle yapılmayan fit (279 inner, 8 outer). Yakınsama/fit hatası yok. Bütün 62 üzerinde ek deployment fit'i yapılmadı.

## Kapsam ve sonuç sınırı

B1 54 ilacı, B2 61 ilacı skorlar. Methenamine her ikisinde abstention; B1 diğer yedi kimya inceleme kaydında da skor vermez. 54 ortak ilaç/ortak train hedefinde ana PT drug-AP B1 **0,6556**, B2 **0,6262**. Complete-case53 aynı modellerin değerlendirme alt kümesidir, yeni eğitilmiş modeller değildir.

Bu ilk deneyde B2 ana drug-AP'yi yükseltmedi; bazı sınıf bazlı ikincil ölçüler farklı yöndedir. Bu, protein biyolojisinin değersizliği veya klinik üstünlük sonucu değildir. Yoğun/sık yan etki etiketlerini sıralamak yüksek drug-AP sağlayabilir; sınıf bazında yeni ilaç ayırt etme ayrı ölçüdür. B0/sıklık önseli bu onay kapsamına eklenmedi; skorlar onun aşıldığını kanıtlamaz.

## Belirsizlik ve kullanım sınırı

1000 yapısal grup bootstrap çekimi; grup üyeleri birlikte, paired B1/B2 aynı çekimlerle. Aralıklar **sabit OOF tahminlerine koşulludur**; tekrar eğitim, hiperparametre seçimi ve dış doğrulama belirsizliğinin tamamını kapsamaz. 62 ilaç daha önce keşfedildi; bu iç doğrulamadır. Foldlar ve ilaç–PT çiftleri bağımsız birimler sayılmadı. Seyrek/ragged sınıflarda hesaplanamayan ölçüler NA ve gerekçesiyle raporlandı. AP trapez PR-AUC değildir.

Klinik karar, tedavi seçimi, kişisel risk, nedensellik veya güvenlik sertifikasyonu için kullanılmaz. Onaylanan amaç tezde kayıt ilişkisi sıralama deneyidir. PPI/gerçek GiG kullanılmadı; WP09 başlamadı.

## İzlenebilirlik

Her bundle `.npz` parametreleri ve `.json` sürüm/kaynak/split hash/C/seed/train ID/özellik-target sözlüğü/dönüşüm fit kimliklerini içerir; pickle gerekmez. `model_artifact_manifest.json` 800 dosyanın hash'ini verir. Test ilacının yalnız etiketsiz hazırlanmış inputu query olarak kullanılır; train-only graf ve fit kaynaklarına eklenmez. [Tam deney raporu](WP08_BASELINE_RESULTS.md).
