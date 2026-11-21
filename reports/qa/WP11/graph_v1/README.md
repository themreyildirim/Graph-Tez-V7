# WP11 graf açıklaması QA — v1

Bu dizin kabul edilmiş B1 SHAP dizininden ayrıdır. `policy_commit_before_attribution.json` yöntem/örnek/kapsam hash'lerini; sentetik PASS kapısı gerçek attribution öncesindeki teknik testi bağlar.

`role_contributions.csv.gz` ve `ppi_contributions.csv.gz` tam local açıklama tablolarıdır. Büyük tablolar için örnek okuma: `pd.read_csv(path,chunksize=50000)`. Bunlar model eğitimi girdisi veya yeni etiket değildir. Satır birimi context–ilaç–fit CUI–ilişki–müdahale yöntemidir; farklı satırlar bağımsız biyolojik örnek sayılmaz.

`mode=fixed`: orijinal derece/rol paydası ve availability maskesi sabit tekil mesaj maskesi. `mode=delete`: fiziksel silme, kalan paydanın ve gerekirse rol maskesinin güncellenmesi. `delta_z=original_logit-intervened_logit` kayıt sıralama logitindeki farktır; SHAP veya klinik risk değildir. Yuvarlama nedeniyle CSV'deki fark eşitliği yaklaşık10⁻⁶ hassasiyetindedir.

Eksik yollar `absent_paths_NA.csv` ve `protein_path_coverage.csv` içinde açıklanır. Kaynakta olmayan bağlantılara sıfır katkı yazılmadı. Mevcut uygulanabilir kenarda ölçülen sıfır veya küçük değerler saklandı. Native fold PT başlığı dışına doldurma yapılmadı.

`all_drug_scope_named.csv` bütün62 ilacı iki ayrı protokolde isim/modalite/kapsamla gösterir. `intervention_summary.csv` her müdahalenin kendi fit edilmiş PT'lerindeki özetidir; bunun protokol ortalaması bütün1061 PT'nin ortak global açıklaması değildir.

`attempt_01_technical_failure` ilk hash denetimi API hatasının ve boş kısmi dosyaların arşividir; dondurulmuş yöntem değiştirilmeden teknik hata düzeltildi. `artifact_validation.json` uygulama denetimidir; WP11 nihai kapanış belgesi değildir. WP12 başlamadı.
