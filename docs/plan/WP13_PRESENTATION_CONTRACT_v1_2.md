# WP13 — Sunum sözleşmesi v1.2

Aktif ROADMAP WP13 ve WP13_DEMO_SCOPE_v1 kapsamındaki kullanıcı düzeltmesidir; yeni yol haritası değildir. Önceki v1/v1.1, WP08–WP12 kaynak/model/QA dosyaları değişmez.

1. Aday çıkarımı **aynen wp13_candidates_v1_1**: sözlük, anchor, kaynak metni ve candidate_id değişmez. Sayımda yalnız kaynak teriminin boşlukları birleştirilir, harf büyüklüğü yok sayılır. Satır, farklı terim, Türkçe ad, kapsam ve tekrar ayrı gösterilir. Klinik doğrulanmış sayı NOT_ESTABLISHED.
2. İlk metin açıkça **source-bound editorial translation**, LLM çıktısı değil ve **PENDING**. Sıklık/kapsam/istisna yalnız bağlı gerçek alıntı ve context_quotes üzerinden aktarılır. Belirsizlik ve olumsuzluk korunur; yüzde veya yeni risk üretilmez. Aktarılamayan koşul NOT_AVAILABLE; orijinal kaynak değişmez. Bu editoryal gösterim yeni extraction veya etiket stratejisi değildir.
3. Orijinal İngilizce kanıt, fiziksel sayfa, quote-ID ve Python Unicode `[start,end)` aralıkları açılır bölümde. Bağlam/istisna alıntıları ayrı kimlikleriyle görünür.
4. Kayıtlı WP12 metni v1.1'in terim + kaynak/aralık bağlantısı varsa ayrı PENDING panelinde aynen gösterilir; önceki kusur notları korunur. Bu sonlu eşleme genel semantik doğrulayıcı değildir. Bağlantı yoksa NOT_AVAILABLE; başka adayın yanıtı eklenmez. İnsan QA değiştirilmez.
5. Tek gerçek seçim durumu belge SHA + mod namespace'indeki **active candidate_id**. Selectbox ID saklar; tablo row-index yalnız mevcut sıralı ID listesine çevrilir. İki callback active ID'yi günceller. Tablo callback'i picker'ı eşitler; epoch yeni tablo seçimini aynı ID ile başlatır. Her iki detay/sekme aynı candidate nesnesini alır. Belge/mod durumları birbirinden ayrıdır.
6. API düğmesi/otomatik inference yok. GNN paneli yalnız mevcut ilgili outer-test OOF'yi okur. PDF adayları PT'ye otomatik eşlenmez. Ürün/doz/tuz eşdeğerliği varsayılmaz. Yeni PDF deneysel; kimliği belirsiz kaynakta GNN NOT_AVAILABLE.
7. Yeni dış antibiyotik çıkarımı bu sürümde kapalıdır. Önce ayrı fizibilite/kimlik/girdi/protokol onayı gerekir. Kaynak karşılaştırması, tahmin/method hash kilidinden sonra yapılır. PDF'de yokluk negatif değildir.

Kanıt: reports/qa/WP13/v1_2; gerçek browser8504; tests/test_wp13_v1_2.py. Streamlit dataframe seçim varsayılanı ve callback'i için kullanılan resmî API: https://docs.streamlit.io/develop/api-reference/data/st.dataframe . Çalışan ortam1.67.0; önceki sanal ortam korunur, yeni paket kurulmadı.
