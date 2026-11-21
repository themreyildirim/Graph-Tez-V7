# WP08 — Eğitim öncesi son karar kapısı

06.11.2026. **Model eğitimi henüz başlamadı.** Aşağıdaki v1 hazırlığı, kullanıcının yeni yönlendirmesiyle somutlaştırıldı. Split kimlikleri ve seed, hedef dosyaları bu hazırlıkta işlenmeden önce kilitlendi; seçimler performansa göre denenmedi.

| Detay | Hazırlanan / önerilen v1 | Son onay konusu |
|---|---|---|
| Seed / split | 20261106; connectivity 5×3; ayrı scaffold OR ≥0,8 stres | v1 kilitli; eğitim için son kabul |
| PT kuralı | ≥5 kullanılabilir train ilacı + ≥2 train grup; paired hedefler train kesişimi | Kural ve destek paydası |
| Metrik varsayımı | Observed-record proxy; drug-macro AP birincil, micro/class-macro AP ve AUROC ikincil | Unknown gerçek negatif değil |
| Maskeler / abstention | Nötr standart blok+maske; B1 kimya yoksa, B2 iki dal yoksa abstain | Methenamine tahminsiz kalır |
| Learner / seçim | B1/B2 L2-LR adayı; C=0,1/1/10; inner mean drug-AP; eşitlikte küçük C | LR ve ayarlar henüz öneri |
| NA / fallback | Train tek proxy sonucu veya metrik desteği yoksa NA; olasılık fallback yok | Ortak drug/target kıyası + kapsam |
| ATC / ek deney | ATC ayrı; 53 complete-case duyarlılık; PPI/context yok | Ek eğitimler ayrı onay |

Bu tablo eğitim onayı değildir. 5/2 kuralı düşük destek ve tek yapısal gruba bağımlılığı sınırlayan **önceden belirlenmiş operasyonel adaydır**; güç/klinik geçerlilik garantisi değildir. Kullanılabilir-train paydası, gerçekten inputu olmayan örneklerin bir modelin destek sayısını yapay artırmasını önler; kohort sözlüğü ayrıca korunur. Ortak karşılaştırma yalnız train'den seçilen hedef ve ortak input kapsamıyla yapılır.

Seed **20261106** yalnız sabit tarih kodudur; “en iyi seed” değildir. Dış test etiketleri daha önce keşfedildiğinden sonuçlar yine iç doğrulama sayılacaktır. Bu hazırlıkta başarım, tahmin, CI veya negatif örnek yoktur. Gerçek train-only **ön işleme fit'i** yapılmıştır; sınıflandırıcı fit edilmemiştir.

Kilitli split tanım SHA-256: `9872adf0168ad3ab377994fc346dc3eb553338e68109b9b1cf27ec966ef4bd65`. Ayrıntılı parametreler ve `class_weight=None` önerisi [QA karar tablosunda](qa/WP08/experimental_preparation/final_pretraining_decisions.csv), kaynak/fit/graf kapsamı [hazırlık raporundadır](WP08_EXPERIMENTAL_PREPARATION.md). WP08 açık kalır; WP09 yetkilendirilmedi.
