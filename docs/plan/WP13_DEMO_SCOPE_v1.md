# WP13 — Drug Safety Explorer demo kapsamı v1

Durum: **PLANNED / IMPLEMENTATION_NOT_STARTED**. Bu belge kullanıcının WP13 demo hedefini kaydeder; uygulama veya API çalıştırma yetkisi değildir.

Üst plan: [aktif ROADMAP_V7.md](ROADMAP_V7.md), **WP13 — Tez raporlama ve açıklanabilir karar destek demo** satırı. Bu kapsam belgesi o satırın arayüz hedefini somutlaştırır; yeni yol haritası oluşturmaz veya iş paketi sırasını değiştirmez. Öncelik **WP12 S04 ve küçük pilotun bilimsel değerlendirmesinin tamamlanmasıdır**. WP13 uygulaması için ardından kullanıcı onayı gerekir. Mevcut WP08–WP12 kaynak/deney/model/QA dosyaları korunur.

## Amaç ve çalışma ortamı

Streamlit tabanlı, yalnız localhost/127.0.0.1 üzerinde çalışan, sunumda gerçek ekran görüntüleri alınabilecek sade ve profesyonel bir **Drug Safety Explorer**. Araştırma ve sunum demosudur; klinik karar desteği, kişisel tedavi önerisi veya hasta güvenliği doğrulaması iddiası taşımaz. Public hosting/yayınlama bu kapsama dahil değildir.

## Planlanan kullanıcı akışı

1. Kullanıcı gerçek bir ilaç prospektüsü PDF'si yükler. Yükleme olayı, belge SHA-256 ve fiziksel sayfa sayısı kaydedilir; kullanıcı dosyası değiştirilmez. Otomatik prospektüs arama/indirme yapılmaz.
2. Sistem mevcut WP12 belge sözleşmesiyle metin katmanını çıkarır. Boş/okunamayan sayfalar atlanmaz; fiziksel sayfa, karakter aralığı, quote-ID ve birebir alıntı izlenebilir kalır. Çıkarım başarısızlığı açık durum olarak gösterilir; sonuç uydurulmaz.
3. **Prospektüste bildirilenler** panelinde açıkça kaynakta bulunan yan etki, sıklık, uyarı ve etkileşim ifadeleri sayfa/alıntı ile gösterilir. Sınıf ifadesi, doğrudan ilaç ifadesi, istisna ve belirsizlik ayrımı korunur. Bilinmeyen sıklık nadir/yaygın veya sayısal risk olarak sınıflandırılmaz. Yeni çıkarım stratejisi gerekiyorsa ayrıca yöntem onayı gerekir; arayüz şema geçişini semantik doğruluk gibi sunmaz.
4. Kullanıcı gerekli alıntıları ve veri aktarım kapsamını görüp **açıkça başlatırsa** OpenAI API ile Türkçe kaynaklı açıklama adayı üretilir. Ham yanıt, kaynak bağları, model/request-ID, token/maliyet ve inceleme durumu korunur. Kaynak veya anlam incelemesi eksikse aday/onay bekliyor olarak gösterilir; otomatik onay/yayın yoktur.
5. **GNN kaynak-kayıt sıralaması** ayrı panelde yalnız kabul edilmiş model artefaktlarının desteklediği ilaç, fold ve PT hedef kapsamı için gösterilir. İlk demo mevcut kayıtlı sonuçları salt okunur kullanmayı esas alır. Yeni ilaçta skor üretme, yeni eğitim veya hedef uzayını genişletme bu belgede yetkilendirilmez.
6. Kullanıcı belge sürümü, quote-ID/sayfa, ilaç eşlemesinin durumu, model sürümü, hedef kapsamı, modalite/QC/abstention durumu, belirsizlik ve sınırlamaları görebilir.

## Panellerin veri sözleşmesi

| Panel | Kaynak ve anlam | Sınır |
|---|---|---|
| Belge ve alıntılar | Gerçek yüklenen, okunabilir PDF; metin/sayfa/aralık/hash | Dosya adı veya ürün adı kimlik eşdeğerliği değildir |
| Prospektüste bildirilenler | `reported_in_PDF`, kanonik alıntı ve kaynak nitelemeleri | SIDER/GNN eğitim girdisi veya yeni MedDRA etiketi yapılmaz |
| Türkçe açıklama adayı | API'nin kaynaklara bağlı yorumu; teknik/ajan/insan durumları ayrı | JSON/quote-ID tek başına doğruluk veya insan onayı değildir |
| GNN sıralaması | `predicted_by_GNN`, dondurulmuş model/split/PT kapsamı | Bireysel hastada yan etki olasılığı veya klinik risk değildir |

Prospektüs bilgisi ile GNN çıktısı birleştirilerek tek bir “doğrulanmış risk” üretilmez. SIDER'da gözlenmeyen çiftler **etiketsiz** olarak kalır, gerçek negatif sayılmaz. Kaynakta 1061 PT veya 62 ilaç envanteri bulunması her fold/modelin hepsine skor verdiği anlamına gelmez; gerçek hedef sözlüğü ve eligibility esas alınır. Eksik modalite/QC maskeleri ve abstention kararları korunur.

Yüklenen ürün/tuz/formülasyon ile dondurulmuş DrugBank ana ilaç kimliği otomatik eşitlenmez. Doğrulanmış eşleme yoksa GNN paneli uygunluk/eşleme eksikliğini açıkça gösterir. Kullanıcının yalnız bir ilaç adı seçmesi biyolojik eşdeğerlik kanıtı gibi sunulmaz.

## API, gizlilik ve çalışma güvenliği

- Anahtar yalnız güvenli yerel ortam/.env yöntemiyle alınır. UI'da yalnız VAR/YOK; değer/prefix/hash/Authorization header arayüze, hata çıktısına, loga veya ekran görüntüsüne girmez. Gizli dosyalar Git/manifest dışında kalır.
- Kullanıcıya yalnız gerekli seçilmiş alıntıların dış servise gideceği gösterilir; tam PDF/proje/model dosyaları otomatik gönderilmez. Çalışma bütçesi ve izinli model gelecekte ayrı onaylı konfigürasyondur; WP12 sayaçları sıfırlanmaz veya demo için sessizce yeniden kullanılmaz.
- Her üretim öncesi kaynak bütünlüğü, token/maliyet ve kalan bütçe kontrol edilir. Otomatik retry/model değiştirme/ücretli araç yoktur. Upload, sekme değişimi veya Streamlit rerun olayı API çağrısı başlatmaz.
- Oturum ve request kimliğiyle aynı kullanıcı eyleminin ikinci kez ücretli çağrı üretmesi engellenir. Hata/timeout/usage belirsizliği saklanır; yeniden deneme açık yeni kullanıcı kararı gerektirir.
- Çıkarım veya kaynak doğrulama başarısızsa desteklenmeyen sonuç yerine açıklayıcı durum gösterilir. Örnek/test fixture'ı gerçek analizmiş gibi sunulmaz.

## Sunum ve kabul ölçütleri — ileride doğrulanacak

- Gerçek kullanıcı PDF'si, gerçek çıkarılmış metin ve sayfa/alıntı karşılaştırması görülebilmeli; okunamayan kaynak için doğru başarısızlık ekranı bulunmalı.
- PDF bildirimi, Türkçe aday ve mevcut GNN sonucu görsel olarak açıkça ayrılmalı; ilaç/ürün eşleme ve hedef kapsamı sınırları görünür olmalı.
- Belirsiz sıklık, sınıf/ilaç ayrımı, istisna ve insan incelemesi durumları kaybolmamalı.
- Bütçe, tekrar engeli, secret sızıntısı ve veri katmanları ayrımı testlerle doğrulanmalı; önceki WP08–WP12 artefakt hash'leri korunmalı.
- Sunum ekran görüntüleri **yalnız gerçek çalışan localhost uygulamasından**, gerçek artefaktlarla alınmalı. Mockup, örnek satır veya temsilî skor gerçek çıktı diye kullanılmamalı. Görüntü öncesi secret kontrolü yapılmalı.
- Kurulum/çalıştırma notu, veri/model kartı, sınırlamalar ve gerçek ekran görüntüleri tez raporuna bağlanmalı. Tek-vaka açıklama başarısı klinik doğruluk veya genelleme kanıtı yapılmamalı.

Bu ölçütler şu an **NOT_RUN** durumundadır. WP12 tamamlanıp kullanıcı değerlendirmesinden sonra UI yerleşimi, artefakt erişimi, kimlik eşleme kontrolü, API bütçesi ve demo veri kapsamı ayrı tasarım kapısında netleştirilecektir. Bu tur Streamlit kodu, yeni API inference, model eğitimi veya uygulama ekran görüntüsü oluşturulmadı.
