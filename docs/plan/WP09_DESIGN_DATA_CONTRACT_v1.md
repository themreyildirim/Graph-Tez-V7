# WP09 — Tasarım veri sözleşmesi v1

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
