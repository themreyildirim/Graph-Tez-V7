# WP11 — B1 SHAP yöntem sözleşmesi v1

07.11.2026. Bu kararlar açıklama değerleri hesaplanmadan `reports/qa/WP11/B1_SHAP_v1/policy_v1.json` içinde donduruldu. `policy_commit_before_explanations.json`, yöntem, örnek kimlikleri, background/test üyelikleri ve kaynak manifestinin SHA-256 değerlerini saklar. Sonuçlara göre yöntem seçimi yapılmaz.

Yalnız kayıtlı, seçilmiş 10 outer PT–B1 modeli açıklanır: connectivity ve stres protokollerinin beşer dış katlaması. Inner modeller veya tarihsel 30 kategori bu açıklama evrenine katılmaz. Model, scaler, PT sözlüğü veya seed yeniden fit edilmez.

## Yöntem, ölçek ve referans

**Exact interventional linear SHAP**, kaydedilmiş doğrusal logit `f(x)=b+w·x` üzerinde uygulanır. Her model için background, yalnız kendi `train_drug_ids` listesindeki uygun ilaçların tamamıdır; eşit ağırlıklıdır. Kaydedilmiş train-only standartlaştırılmış özellikler kullanılır. Test ilaçları, etiketleri, sıklıkları veya sonuç başarısı referans seçiminde kullanılmaz.

`v(S)=mean_B f(x_S,B_notS)` oyunu için `φ_i=w_i(x_i−mean_B B_i)` ve `base=b+w·mean_B B`; dolayısıyla `base+Σφ=f(x)`. Bu, bağımsız/interventional doğrusal SHAP'ın tam çözümüdür. Özellik bağımlılığına koşullayan farklı bir SHAP oyunu hesaplanmaz. Resmî [LinearExplainer yöntemi](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html) bu kapalı formu belgeler. Ortamda SHAP paketi bulunmadığından yeni bağımlılık kurulmadan formül uygulanır; dondurulmuş 40 örnekte 64 koalisyonun tamamı üzerinden bağımsız Shapley hesabıyla kontrol edilir.

Ölçek **logit**tir. `expit(base+Σφ)` yalnız mevcut observed-record OOF skorunu doğrular; katkılar sigmoid skoruna doğrudan toplanmaz. Bu ayrım [resmî lojistik regresyon SHAP örneğiyle](https://shap.readthedocs.io/en/latest/example_notebooks/tabular_examples/linear_models/Sentiment%20Analysis%20with%20Logistic%20Regression.html) uyumludur. Sigmoid çıktısı klinik olasılık olarak yorumlanmaz.

Beş kimya özelliği MW, LogP, HBD, HBA, TPSA ayrı raporlanır. Altıncı sütun `mask__chemistry` ayrıca gösterilir. B1 uygun train/test popülasyonunda maske 1'dir; eksik kimyalı abstention kayıtları için sahte açıklama üretilmez. Maske katkısının sıfır olması eksik kimyanın önemsizliğini kanıtlamaz.

## Kapsam, örnek ve kararlılık

- Birincil global tablo her modelin kendi geçerli PT başlığı ve test ilaçları için `mean(abs(φ))` ve `mean(φ)` verir. Yerel açıklama ilaç–CUI–model üçlüsüne bağlıdır.
- Protokol özeti yalnız beş outer modelin **kesişimindeki** PT'leri kullanır. Mevcut gerçek açıklamalar betimsel olarak ortalanır; farklı modellerin ortak PT kapsamı açık gösterilir. Sözlük dışında olan hedefe sıfır veya tahmin atanmaz.
- Her bağlamda alfabetik ilk iki uygun test ilaç ID'si × alfabetik ilk iki fit edilmiş CUI örnektir. İki waterfall grafiği her protokolün ilk outer modelindeki ilk örnektir. Başarı, etiket veya skor büyüklüğü seçime girmez.
- Tam tekrar ve sıra/eksen değişmezliği kontrol edilir. Bütün train ilaçları tek tek background'dan çıkarılarak referans duyarlılığı hesaplanır. Ağırlıklar sabittir; bu aralık güven aralığı veya dış doğrulama değildir. Referans değişirken logit sabit kalmalı, base ve katkılar birbirini dengelemelidir.
- Toplamsallık ve koalisyon toleransı `1e-10`; kayıtlı skor ve tekrar toleransı `1e-12`.

Kimyasal alanlar ilişkili olabilir; interventional değiştirmeler her zaman fiziksel moleküle karşılık gelmez. “Interventional” sözcüğü burada değer fonksiyonunu tanımlar; biyolojik müdahale veya nedensellik iddiası değildir. Unknown çiftler doğrulanmış negatif değildir. Protein/PPI attribution bu aşamada yalnız yöntem önerisidir; eğitim ve WP12 kapsam dışıdır.
