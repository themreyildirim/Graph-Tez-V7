# WP09 — Eğitilmiş model kartı

Sürüm **WP09-protein-PPI-observed-record-v3-training-v1**,06.11.2026. Bu tek deployment modeli değil,nested CV'nin190 bileşen model koleksiyonudur.190 NPZ/JSON çifti `models/WP09_PPI_v3_training_v1/` altında;manifest model hash'lerini korur.

**Görev:** yeni ilaçlar için SIDER observed-record sıralaması. Unknown doğrulanmış biyolojik negatif değildir. Sigmoid skoru klinik olasılık/kalibrasyon veya hasta güvenliği doğrulaması değildir. Klinik tedavi önerisi veya nedensel mekanizma iddiası yoktur.

**Mimari:** protein56→32 paylaşılan projection,tek residual mean PPI,dört ayrı role mean+maske,skaler kimya5→8 ve train PT lineer başlığı. Atom–bağ GNN yok;tam moleküler GiG değildir. NoPPI/real700/shuffledR0,R1,R2 aynı init/context-ID/PT kapsamındadır. Nonhuman/PPI'sız sequence self yolunda;K12 PPI/context80 yoktur. Feature kaynakları frozen WP04/05/08;PT/kategori/sıklık/kalite_skoru/STRINGscore düğüm özelliği değildir.

**Fit:** fullbatch proxy BCE;AdamW lr0,001/weight_decay0,001;CPU1thread,float32;max200,inner patience20/min_delta0,0001;outer epoch ortak inner best-epoch medyanından .5yukarı. Base20261106 sabit seed;inner/outer başlıkları kendi fittable PT listesidir. Train-only scaler/target/graph;test ilaçları ve ters/SE ilişkileri eğitim grafında yoktur. Query train-state'i değiştirmez;unseen protein self-only. Kişiselleştirilmiş girdi yoksa abstention.

**Sonuç:** ana paired54 drugAP noPPI0,6430/real0,6429/shuffled3mean0,6433. Real−noPPI/real−shuffled koşulluCI sıfırı içerir;ekPPI faydası gösterilemedi. B1/B2/B0 sabit ve yeniden fit edilmedi. Stres B2 kazancı noPPI'da da vardır;PPI'ye atfedilemez. Üç null için metrik ortalaması alınır,tahmin ensemble'i veya en iyi tekrar yoktur.

**Kapsam:**62 envanter/61 skor/Methenamine abstention;paired54 primary. Kaynak1061 PT,6416 pozitif;primarypaired54'te1685 pozitif skor sözlüğü dışında. Tüm PT evreninde başarı iddiası yok. Class-metric NA ve unknown korunur. Bütün modellerde aynı karşılaştırma anahtarları kullanılır.

**Sınırlar:** önceki baseline sonuçları görülmüş olduğundan keşifsel iç doğrulama;1000 grup bootstrap CI sabit OOF/3null'a koşullu,full-retraining veya bağımsız dış doğrulama değildir. Tek init seed politikası;küçük kohort/seyrek etiket/source-reporting yanlılığı vardır. Lower/similar sonuçlar raporlandı;sonuç sonrası tuning yok.

**Doğrulama:**24 gerçektrainer testi;190 fit/10867 optimizer adımı;gerçekPPImessage gradient/forward/query izolasyonu,heldout mutasyon,checkpoint/epoch ve independentAP testleri. Model NPZ'leri yalnız sayısal state_dict'tir;kimlik/target/split/null/source metadata JSON yanındadır. Kütüphane sürümleri/environment ve hash manifestiyle kullanılır;cross-version bitwise garanti yoktur.

Detaylar:[eğitim raporu](WP09_TRAINING_RESULTS.md),`reports/qa/WP09/training_v1/`. WP10 veya moleküler encoder eğitimi yapılmadı.
