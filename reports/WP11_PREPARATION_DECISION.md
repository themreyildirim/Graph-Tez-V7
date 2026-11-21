# WP11 — Aktif yol haritasına göre kısa hazırlık ve karar notu

07.11.2026. **Yalnız kapsam incelemesi;WP11 uygulaması başlamadı.** Bu belge yeni yol haritası veya uygulama onayı değildir. WP10 kullanıcı kabulüyle kapandı;sonuçları ve bütün sabit referanslar korunur.

## Yol haritasının gerçek kapsamı

Aktif `docs/plan/ROADMAP_V7.md`,WP11'i şu şekilde tanımlar:

> Açıklanabilirlik:SHAP ≠ nedensellik,protein/edge attribution. Kimya baseline SHAP;GiG varsa hedef protein/kenar maskelerini test et;katkı kaynaklı. Çıktı:local/global SHAP ve graf açıklaması,limitler,stabilite.

İlk kapsam kimya baseline'ın açıklanmasıdır. Mevcut B1 modeli beş kimya özelliği ve kimya maskesiyle eğitilmiştir. Kayıtlı fold modelleri kullanılabilir;yeniden fit veya yeni model gerekmez. Daha yüksek test AP nedeniyle model seçmek yerine yol haritasının bu başlangıcı korunmalıdır.

Graf bölümü koşulludur. Projede gerçek atom ve protein-PPI encoder'ları ile geç füzyon vardır;bu otomatik olarak tam hiyerarşik GiG tamamlandı demek değildir. Mevcut modelde hedef protein/rol vePPI kenar yollarının açıklanabilirlik deneyi ayrıca açık seçilmelidir. Atom/bond için yeni açıklama yöntemi veya yeni mimari bu ilk notla kendiliğinden eklenmez.

## Uygulamadan önce açık yazılacak kararlar

| Konu | Hazırlık önerisi / karar sınırı |
| --- | --- |
| Açıklanacak model |Önce sabit B1;fold ve ağırlık hash'i korunur. Grafik bölümü için hangi kayıtlı WP09/WP10 kolunun kullanılacağı onayla belirlenir |
| Açıklanacak çıktı |Kaynak PT CUI ve ilgili foldun geçerli hedef sözlüğü açıkça seçilir. Logit ile observed-record sigmoid skoru karıştırılmaz;hangi ölçeğin açıklanacağı önceden yazılır |
| Background/referans |Yalnız ilgili train bölümünden;test ilacı veya test etiketleri referans seçimi/ölçekleme için kullanılmaz. Background kuralı ve kaynak ID'leri kaydedilir |
| Local/global özet |Local açıklama bir ilaç–PT–model üçlüsüne bağlanır. Global özetin ilaç/PT/fold kapsamı veNA paydası açıklanır;farklı fold sözlükleri aynı evrenmiş gibi birleştirilmez |
| Örnek seçimi |Kural sonuç hesabından önce sabitlenir;mevcut Erythromycin örneği kullanılabilecek kayıtlı adaydır. Başarılı örnekleri seçip genelleme yapılmaz |
| Protein/kenar maskesi |Target/enzyme/transporter/carrier ayrı tutulur. Strict insan700 evreni,query/train-cache sınırı veeksik modaliteler korunur. Context80 vekoşullu E.coli PPI eklenmez |
| Güvenilirlik kontrolleri |Açıklamanın seçilen model çıktısına bağlılığı,maske etkisi,indeks/kimlik hizası,tekrar hesaplama veistikrar kontrol edilir. Maske kaynak dışı biyolojik ilişki üretmez |

Kenar silme ile mesajı maskeyle sıfırlama aynı işlem varsayılmamalıdır; mean aggregation sırasında derece/normalizasyon kuralı açıkça tanımlanmalıdır. Maske denemeleri orijinal kaynak grafını ve paylaşılan train cache'ini değiştirmeyen ayrı kopyalarda planlanmalıdır. Özellik bağımlılıkları ve background varsayımı da yöntem kararında açıklanmalıdır.

Bu seçimler bu turda uygulanmadı veya nihai yöntem olarak sabitlenmedi. SHAP paketi yüklenmedi/çalıştırılmadı;protein/edge attribution veya açıklama skoru üretilmedi. Gerekli yöntem/bağımlılık ayrıntıları WP11 açıkça başlatıldığında mevcut ortam ve kayıtlı modellerle incelenmelidir.

## Değişmeyecek bilimsel sınırlar

- Açıklama model davranışını betimler;SHAP değeri veya büyük kenar katkısı biyolojik nedensellik/klinik risk kanıtı değildir. PPI açıklaması,WP09/WP10'da ek PPI performansı gösterilememiş olmasını tersine çevirmez.
- B1'in beş kimya alanı ile modalite maskesi ayrı yorumlanır. Maskeler,bilinmeyen girdiler ve8 yapı QC bayrağı biyolojik özellik gibi sunulmaz. `kalite_skoru`,PT sayısı veya raporlama sıklığı modele/açıklama girdisine eklenmez.
-62 envanter,1061 kaynak PT,6416 pozitif,54/8 atom maskesi,Methenamine abstention ve1685 ana kapsam dışı kaynak pozitif korunur. Unknown gerçek negatif değildir;etiketsiz bir çiftin açıklaması klinik yan etki doğrulaması sayılmaz.
- Yeni eğitim,seed/hiperparametre ayarı,performans iyileştirme araması veya etiketten türetilmiş yeni girdi yoktur. PDF/LLM/Ollama görevleri WP12 kapsamındadır;WP11 hazırlığı bunları başlatmaz.

## Planlanan çıktı ve onay sınırı

Kullanıcı WP11'i başlattığında,yol haritasındaki local/global kimya SHAP veonaylanan koşullu graf açıklamaları;model/çıktı/background provenansı;limit/istikrar testleri;çalıştırılmış Türkçe notebook,gerçek tablolar/görseller ve rapor beklenir. Bu turda yalnız bu hazırlık notu oluşturuldu. **WP11 uygulaması,yeni model veya yeni eğitim için yetki verilmiş sayılmaz;şimdi durulur.**
