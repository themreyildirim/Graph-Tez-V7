# WP13 FINAL DEMO v2 — Deterministik sözlü açıklama

AGENTS/aktif ROADMAP, WP11 fixed-degree açıklama sözleşmesi ve uygulanmış policy_v1, WP13 FINAL v1 ve kör fizibilite v1 esas alındı. Yeni kod ayrı v2; geçmiş dosya/model/QA ve insan PENDING değişmez.

## Gerçek kapsam denetimi

Tam local_shap.csv ve role/ppi_contributions.csv.gz akışla50.000satırlık parçalarla tarandı, her dosya WP11 artifact manifestiyle hash doğrulandı. Toplam2.608.100 satır: B1 SHAP167124, rol557574, PPI1883402. Primary/stress ve model/context/ilaç bazında satır kapsamı full_WP11_coverage_by_drug_fold.csv; native PT sayıları full_native_PT_coverage.csv. Bunlar mevcut10outer model/family kapsamıdır, fold hedef union'u doldurulmadı. İki demo ilacının tam önceden hesaplanmış kayıtları yeni salt okunur indekslere alındı; yeni attribution yapılmadı.

DB00199 primary outer3: A1P1 müdahalesi318PT, B1 SHAP267PT. DB00254 primary outer1: A1P1 müdahalesi240PT, B1 SHAP220PT. B1 ve GNN head/kapsamı farklıdır; biri diğerinin açıklaması değildir. Önceki v1 yalnız iki seçilmiş örneği gösteriyordu; bu bir hesaplama eksikliği değil, sunum kapsamı kısıtıydı. C0000731/C0000737 her iki ilaçta kaynak hash ve model/fold/PT hizasıyla test edildi. B1 toplam/base/logit ve sigmoid/proxy ayrımı; A1P1 Δz=orijinal−müdahale değerleri korunur. Yanlış PT/fold/model/ilaç açık ValueError ile reddedilir.

## Anlaşılır açıklama ve sınırlar

Üç düzey ayrı:1girdi şeması,2seçili ilaç/PT için gerçek katkı,3biyolojik mekanizma NOT_ESTABLISHED. Seçili A1P1 ilişki skoru/sırası üstte. Açıklanabilir örnekler seçicisi mevcut kayıtlı hedeflere bağlı. İki örnek PT'nin Türkçe editoryal gösterimi orijinal adla birlikte ve onaysız terminoloji uyarısıyla sunulur; bu PDF→PT eşlemesi değildir. Diğer adlar frozen sözlükteki haliyle kalır.

SHAP>0 logiti artırıcı,SHAP<0 azaltıcı,0sıfır katkı; raw sayı repr ile korunur. Kimya5 ve modalite maskesi ayrı adlandırılır. B1 açıklaması A1P1 skoruna gerekçe yapılmaz. Δz>0 maskelenince logit azalır;Δz<0 artar. Fixed-degree ana görsel, physical-delete/renormalization ayrı kapalı alan. Kaynakta olmayan yol NA, gerçek sıfır0; absent_paths_NA kaydı ayrı gösterilir. Grafik altındaki yorum gerçek gösterilen satır/katsayı işaretlerinden deterministik üretilir; klinik oran, sıklık, kalibrasyon veya nedensellik iddiası yoktur. En büyük|Δz|8bağlantı görselde, ilk3ü sözlü; tüm bağlantılar kapalı ayrıntıdadır. İlk tarayıcı görüntüsündeki boş protein alanlarının nan etiketi son sürümde yalnız gösterim için boş bırakıldı; ham veriler değişmedi, erken ekran kanıtı tutuldu.

Bu açıklamalar modelin seçili girdilere yerel sayısal duyarlılığını anlatır; bütün sıralamanın nedenini eksiksiz açıklama, protein biyolojisi veya klinik mekanizma kanıtı değildir. Atom/kimya attribution'u A1P1 için burada yok; genel girdi listesi yerine özel gerekçe uydurulmaz. Prospektüs karşılaştırması v1'deki gibi ayrı, UNMAPPED/PENDING. PDF yüklemek yeni GNN tahmini değildir.

## Dış inference ve yeni attribution kapısı

Ayrı reports/WP13_EXTERNAL_INFERENCE_FEASIBILITY_v2.md ve docs/plan/WP13_EXTERNAL_INFERENCE_ADAPTER_CONTRACT_v1.md. B1 vektör çekirdeği var, doğrulanmış dış kimlik/QC/scaler adapter'ı yok. A1P1 frozen62 guard'ı değiştirilmedi. Yeni ana etkin madde bağımsızlığı, alias/DBSALT/kimyasal bağlantısallık, tüm62train birleşimi,5özellik/birim/sıra/maskeler, immutable scalers/head, atom/protein/PPI query-cache izolasyonu ve önceden model/ensemble kararı zorunlu. Öneri beşB1 modeli ayrı; ensemble/tekmodel henüz kullanıcı karar kapısı. Dış adapter testleri plan olarak yazıldı; uygulanmış veya geçmiş gibi gösterilmedi. Yeni dış tahmin/prospektüs karşılaştırması NOT_RUN.

Mevcut başlıklarda çoğu attribution zaten arşivde; yeni hesaplamaya gerek olmayabilir. Gerçek yeni hedef/model/atom attribution için ayrı yöntem ve onay gerekir. Maliyet karmaşıklığı ve gerekli dosyalar ayrı fizibilitede; yeni süre/RAM benchmark'ı yapılmadı. Eski OOF/PDF incelemesi retrospektif/keşifseldir; genel dış klinik doğruluk değildir.

## Test ve kanıtlar

15yeni test PASS: SHAP işaret/büyüklük, maske ayrımı, Δz iki işaret, fixed/delete ayrımı, NA/sıfır, yanlışmodel/fold/PT/ilaç, dört gerçekörnekte SHAPtoplam/logit/sigmoid ve Δz, eksik açıklama uydurmama/kapsam. Önceki FINALv1'in16regresyon testi ayrıca PASS; eski log değiştirilmedi. Test kanıtları yeni final_demo_v2 dizininde. Gerçek browser'da seçili C0000731 Türkçe adı, skor187.sıra/0.145759180188179, rol müdahalesi ve B1 sözlü SHAP görüldü. Bu örnekteki skor yalnız Erythromycin/A1P1 ownfold3 içindir. Görseller gerçeklocalhost8510; notebook çalıştırılmıştır.

Yeni API/eğitim/forward/attribution/dış inference0. Eski hash kontrol kapsamı final_verification.json'dadır; tüm disk taraması yapılmadı. Gizli .env/anahtar okunmadı veya hashlenmedi. Eski run_status baytları yeni giriş altında aynen saklandı. Kullanıcı değerlendirmesi bekleniyor.

## Çalıştırma

`& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP13_Start_FINAL_DEMO_v2.ps1" -Port 8511`

Hazır QA: http://127.0.0.1:8510. Eski sunucular kapatılmadı; yalnız bu turdaki v2 QA sunucusu etiket/NA sunumu düzeltmesi için yeniden başlatıldı. Model açıklanabilirliği sekmesini açın; üstteki Açıklanabilir örnekler seçicisi hedefi değiştirir. Teknik tablolar kapalıdır. Yeni dış deney için ayrı onay gerekir.
