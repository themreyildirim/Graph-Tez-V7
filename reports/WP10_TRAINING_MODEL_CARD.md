# WP10 dört kollu eğitim model kartı

07.11.2026. Sürüm: WP10-molecular-protein-factorial-observed-record-training-v1.

Görev:SIDER observed-record ilaç–PT sıralaması. Unknown doğrulanmış biyolojik negatif değildir. Sigmoid skorları klinik risk/kalibrasyon/nedensellik veya hasta güvenliği doğrulaması değildir.

152 nested-CV bileşen modeli;tek tüm-kohort deployment fit'i yok. A0P0/A0P1/A1P0/A1P1 aynı150 boyutlu mimari,context init/ID/hedef kapsamı;shuffled deney yok. Atom44/bağ14→hidden16 tek bond-aware residual mean→mean8;protein56→32 tek mean-PPI;kimya5→8;dört rol+maskeler.5512+151K parametre. Strict insan PPI700;K12 koşullu ağ/context80 yok.

Kaynak62 ilaç/1061PT/6416pozitif;54 atom maskesi açık/8QC kapalı;61 kişiselleştirilmiş girdi uygunluğu,Methenamine abstention. Eğitim grafı train-only;query ayrı readout. Frozen scaler/PT/split/seed20261106 korunur. AdamWlr.001/wd.001,proxyBCE,max200,patience20,min_delta.0001;outerepoch ortakinner bestepoch medyanı. B0/B1/B2/WP09 yeniden eğitilmedi.

Ana paired54 AP:A0P0 .642740,A0P1 .643636,A1P0 .645930,A1P1 .646234. Küçük pozitif ana atom kontrastları koşulluCI'da sıfır üzerinde;stres koşullu atom CI'ları sıfırı içerir. PPI veetkileşim katkısı gösterilmedi. B0/B1/WP09'a genel üstünlük yok. B2 farkı yalnız atom/PPI etkisi sayılmaz.

1000 yapısal grup bootstrap CI sabitOOF'ye koşullu;seed/yenidenfit/kaynak/dışkohort belirsizliğini kapsamaz. Önceki sonuçlar görüldüğünden kıyas keşifseldir;çoklu karşılaştırmalar genel istatistiksel üstünlük kanıtı değildir.1685 ana paired54 kaynak pozitif hedef/fit kapsamı dışında;1061PT'nin tamamında performans iddiası yok.

19 gerçek trainer testi geçti.152 fit/8611 optimizer adımı;NPZ restore/reference skor ve tamouter tekrar üretimi,train-onlyPT/heldoutmutasyon/gradient/queryizolasyonu sınandı. Farklı library/CPU sürümlerinde genel bitwise garanti yok. Metadata ve manifestler kaynak/seed/target/fitID/state hash'ini taşır. Bu koleksiyon yalnız araştırma içindir;klinik kullanım doğrulanmadı.

Detaylar:WP10_TRAINING_RESULTS.md ve reports/qa/WP10/training_v1/. WP11 başlatılmadı.
