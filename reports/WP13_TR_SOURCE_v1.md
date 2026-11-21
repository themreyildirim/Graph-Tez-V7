# WP13 — İki Türkçe belgeyle offline kaynak pilotu v1

09.11.2026. **Kaynak ve teknik inceleme tamamlandı; klinik/insan aday onayı PENDING.** Yeni uygulama apps/drug_safety_explorer_TR_v1.py; sözleşme docs/plan/WP13_TR_SOURCE_v1.md. Aktif ROADMAP WP13 kapsamındadır; WP08–WP12 yöntemleri/deneyleri değiştirilmedi. İngilizce PDF'ler tarihsel kaynak olarak yerinde, eski launcher ve QA'larıyla korunur. Yeni Türkçe ekranda yalnız iki Türkçe belge aktiftir.

## Gerçek dosya / ürün kimliği

| Belge | Boyut | Fiziksel sayfa | Doğrulanan ürün bileşimi |
|---|---:|---:|---|
|eritro-500-mg-film-tablet-8ccc-kt.pdf|88707 bayt|8|500 mg eritromisine eşdeğer750 mg eritromisin stearat / film tablet|
|monodoks-100-mg-kapsul-kub-07-11-2018.pdf|243099 bayt|13|100 mg doksisikline eşdeğer115,414 mg doksisiklin hiklat / kapsül|

Ham SHA-256:

- ERİTRO: `289acdc2d85c283d5e94db955f40a0acd190d535e7e2c822a6c043165e835310`
- MONODOKS: `065f43273bc71165580f566f8cf78e52fb86f607c89923c42058ff86936c6387`

İki dosya kullanıcı tarafından sağlandı; internetten indirme yapılmadı, ham dosyalar değiştirilmedi/kopyalanmadı. Sayfa1 bileşim alıntıları ve mevcut DB00199/DB00254 ana etkin madde kayıtları ilişkilendirildi; bu, ürün/doz/tuz eşdeğerliği onayı değildir. İngilizce erythromycin250 mg ve doxycycline monohydrate ürünleri Türkçe ERİTRO stearat500 mg / MONODOKS hiklat100 mg ürünleriyle birebir eşdeğer sayılmadı. GNN ana etkin madde araştırma bağlantısı ayrı tutuldu.

**Güncellik doğrulanmadı — UNVERIFIED_CURRENTNESS.** ERİTRO belgesi üzerinde Kullanma Talimatı (KT), MONODOKS üzerinde Kısa Ürün Bilgisi (KÜB) yazıyor. ERİTRO8'de onay tarihi yer tutucu; MONODOKS13'te KÜB yenilenme tarihi boş.07-11-2018 yalnız dosya adı ipucudur. Ruhsat/ruhsat yenileme tarihleri ve PDF teknik metadata tarihleri belge güncelliği veya güncel resmî onay gibi yorumlanmadı. İnternetten güncel sürüm doğrulaması yapılmadı.

## Metin katmanı ve birebir kaynaklar

21 fiziksel sayfanın tamamı PyMuPDF metin katmanından, sort=False/flags195 ile çıkarıldı. Hiçbir boş/görsel sayfa atlanmaz; sayfa text hash/status/image_count/karakter sayısı page_quality.csv'de. OCR veya görselden yeni metin çıkarımı yok. Gerçek6/7/8 ve9/10 sayfaları PNG'ye render edilip görsel olarak da kontrol edildi. İlk konsol metin basımı CP1254 karakter hatası verdi; UTF-8 kaydedilmiş sayfa verileri sağlamdı. UTF-8 konsol okumasıyla içerikler doğrulandı; bu olay extraction_execution_note.json'da korunur, OCR ile kapatılmadı.

source_0.json/source_1.json tüm sayfaları ve bağımsız trquote/trcandidate kimliklerini içerir. Kaynak alıntısı fiziksel sayfa ve Python Unicode `[start,end)` aralığıyla birebir eşittir. Terim aralıkları ayrıca saklanır; Türkçe gösterimde yalnız boşluk/satır sonu sadeleşebilir. all_quotes.* kanıt tablosu, document_registry.json ürün/sürüm/provenans tablosudur. source_bundle_pins.json çalışma anında kayıtlı alıntı bütünlüğünü korur. Yeni Türkçe kimlikler frozen WP12 quote-ID'lerine dönüştürülmedi.

## Sayım yöntemi ve gerçek sonuçlar

| Ürün | Aday satır | Benzersiz terim / Türkçe ad | Tekrar fazlası | Ürün kapsamı | Açık sınıf | Kısmen belirsiz |
|---|---:|---:|---:|---:|---:|---:|
|ERİTRO|25|25 /25|0|25|0|0|
|MONODOKS|48|47 /47|1|37|6|5|

Bu bir **manuel incelenmiş, sonlu bölüm/anchor taramasıdır**, genel tıbbi NER veya klinik doğrulanmış yan etki envanteri değildir. ERİTRO bölüm4/6–8'deki6 ciddi-bulgu madde satırı +19 diğer madde satırı alınır. Bir birleşik maddeyi her sendrom için parçalamadık; bu nedenle İngilizce sözlükteki34/34 ile sayım birimi aynı değildir. MONODOKS4.8/9–10'da açık listelenen terimler ayrı alınır:48 kayıt; glossit hem enfeksiyonlar hem gastrointestinal listede bulunduğundan47 farklı normalize kaynak terimi vardır. Sıra ve kaynak korunur; tekrar bağımsız kanıt yapılmaz. inflamatuvar/enflamatuar gibi farklı özgün yazımları sessizce klinik kavram olarak birleştirmedik. Türkçe terimler MedDRA UNMAPPED kalır.

Sıklık: ERİTRO6 ciddi kayda sayfa7'deki **oldukça seyrek** ifadesi bağlanır, sayısal oran uydurulmaz.19 diğer kayıtta **Bilinmiyor** başlığı7'den8'e devam eder. MONODOKS40 kayıtta Bilinmiyor;8 kayıtta yerel Seyrek başlığı var. Bunların5'inde parantez sonrası sınıf/kapsam uzanımı açık olmadığından unresolved ve insan inceleme notu tutulur. Yerel başlık teknik olarak gösterilir, bu5 kaydın bağımsız kesin frekans/kapsam onayı verilmez. Sıklık tanım listesinde yaygın vb. yazması, diğer olayları o sınıflara sokmaz. Sıklık belirtilmemiş olsaydı NOT_SPECIFIED kullanılacaktı; bu73 seçilmiş adayda yerel sıklık kaynağı vardır. Uyarı/aşırı doz/hayvan bağlamlarına bu aday sıklıkları taşınmaz.

## Kritik anlam ayrımları

- ERİTRO6 aşırı doz: geçici işitme kaybı/bulantı/kusma/ishal cümlesi **overdose**, normal25 aday toplamına eklenmedi. Normal bölümdeki geri dönüşümlü işitme kaybı ayrı; yüksek doz/böbrek koşulu kaynakta korunur.
- MONODOKS4.8/10: **Bilinmiyor: BUN artışı** aynen saklanır.4.2/4'teki tetrasiklin antianabolik/BUN uyarısı class_level; ardından mutad doz MONODOKS'un renal bozuklukta **akümülasyona neden olmaması** product_specific uyarı cümlesi olarak ayrı quote-ID ile bağlıdır. Birikim yokluğu BUN yokluğu değildir. İngilizce PDF'deki farklı cümle buraya taşınmadı.
- MONODOKS özofajit/özofajiyal ülserler, hepatotoksik etki, tiroid renk değişimi ve diş/mine cümleleri açık tetrasiklin sınıf ifadesi olarak işaretlendi. Bütün Türkçe4.8 listesi eski İngilizce sınıf girişinin kapsamına sokulmadı.4.4'te doğrudan doksisiklin bildirimi varsa ayrı drug_direct context olarak tutulur.
- Tiroid renk değişimi cümlesinin devamındaki tiroid fonksiyonlarında anormallik bilinmediği ifadesi korunur; fonksiyon bozukluğu uydurulmaz. Gebelik/hayvan ve5.3/11–12 verileri animal_study, insan normal kullanım tablosundan ayrıdır.4.9 MONODOKS aşırı doz ayrı tutulur.

## Offline arayüz

Önce ürün bileşimi/güncellik durumu, özgün Türkçe aday, sıklık/kapsam, orijinal Türkçe kanıt ve bağlı uyarı gösterilir. Kaynak metni LLM yanıtı diye etiketlenmez. Bu yeni belge/alıntılara atıf yapan kayıtlı model açıklaması yok: **NOT_AVAILABLE**. Eski İngilizce ürünün PENDING yanıtı buraya iliştirilmez. Mekanizma veya model attribution değeri eklenmez; insan PENDING değişmez.

Seçici ve tablo aynı candidate_id'yi kullanır. Gerçek browser kontrolünde iki glossit kaydının aynı görünen selectbox etiketiyle yeniden çizimde karışabildiği saptandı. Başarısız ilk trace/screenshot'lar silinmedi. Etiketlere fiziksel sayfa + kısa ID eklendi; yeni test ve gerçek rerun kontrolünde sayfa9 glossit aynı ID/sayfada kaldı. Kaynaklar, adaylar veya sayımlar bu düzeltmeden etkilenmedi. Eski20 testlik ara loglar ve son21 testlik log ayrı saklanır. Son sürüm kanıtları08 ve sonrası ekran adlarıdır;01–06 erken gerçek UI kayıtlarıdır, son sürüm gibi etiketlenmez.

GNN paneli isteğe bağlı, ayrı read-only ana etkin madde araştırma kaydıdır: Erythromycin primary outer3/318 PT ve Doxycycline outer1/240 PT önceki kendi-fold OOF skorları. Bu Türkçe ürünlere yeni tahmin değildir; tuz/doz/ürün eşdeğerliği varsayılmaz. Browser'da MONODOKS bağlantısında DB00254/outer1/240 PT ve ürün tahmini NOT_AVAILABLE ayrımı görüldü. Model ağırlığı inference için yüklenmez, yalnız eski OOF ve hash/provenans okunur. PDF yan etkileri model girdisi/etiketi yapılmaz. Unknown biyolojik negatif, skor klinik bireysel olasılık değildir.

## Test, kanıt ve koruma

21 yeni test PASS: ham SHA/sayfa eşitliği, tüm alıntı/terim aralıkları, gerçek bileşim, KT/KÜB/tarih/güncellik, ürün eşdeğerliği yasağı,25/48 yeni sayım, glossit tekrarı, PENDING/PT eşlemesiz durum, sayfalar arası sıklık, unknown, aşırı doz ve hayvan ayrımı, BUN/birikim, sınıf/doğrudan/ürün bağlamı, tiroid olumsuzluk, yeni kaynağa eski LLM bağlamama, yanlış hash/anchor reddi, ağsız UI, seçim ve benzersiz etiketler. Önceki v1.1'den20 ve v1.2'den18 regresyon testi PASS: toplam59 test. Eski loglar değiştirilmedi. Test logları/gerçek browser trace'leri yeni tr_source_v1 altında.

Gerçek ekranlar: Türkçe ürün ve yan etki tabloları, bilinmeyen sıklık, BUN/birikim kanıtı, kaynak-ID/sayfa, kayıtsız açıklama ve seçim. reports/figures/WP13/tr_source_v1; ekran görüntüleri mockup değildir. Defter notebooks/WP13_Turkish_source_pilot_v1.ipynb çalıştırılmış Türkçe tablolar ve gerçek görseller içerir. Teknik UI başarısı semantik/klinik başarı oranı değildir.

583 önceki seçilmiş kamuya açık dosya hash'i, önceki kör denetim252 kaynak pini ve iki yeni ham PDF/hash'i son kontrolde doğrulanır. Bu, bütün disk için bütünlük iddiası değildir; kapsam manifestte açıktır. Kaynak .env/anahtar okunmadı/hashlenmedi. Önceki model/ham API/başarısızlık/PENDING/bütçe kayıtları korunur; yeni API/eğitim/inference/OCR0. run_status eski baytları arşivlenip yeni giriş altında aynen korunur. Yeni sunucu yalnız localhost8506; eski demolar/sunucular değiştirilmedi. Yalnız bu işte başlatılan Türkçe QA sunucusu seçim düzeltmesini yüklemek için yeniden başlatıldı.

## Çalıştırma ve sınırlar

`& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP13_StartDemo_TR_v1.ps1"`

Varsayılan localhost8501. Port doluysa eski servisi bu çalışma kapatmaz; ayrı boş port seçilebilir (`-Port 8507`). Hazır QA ekranı http://127.0.0.1:8506. Türkçe pilotta sabit iki kayıtlı kaynak seçilir; serbest yeni PDF yükleme/deneysel İngilizce akışları eski v1.2 uygulamasında korunur. Yeni yüklenen belgeyi otomatik klinik onaya sokan bir mod eklenmedi.

Kalan insan kararları: aday klinik/kapsam incelemesi, unresolved5 kaydın yorumu, sayım birimi/terim stratejisi, güncel belge doğrulaması. Bunlar kullanıcı adına onaylanmadı. Yeni dış antibiyotik denemesi, API veya sonraki aşama başlamadı; değerlendirme bekleniyor.
