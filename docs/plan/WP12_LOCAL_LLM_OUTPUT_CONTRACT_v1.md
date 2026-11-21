# WP12 — Küçük yerel LLM kaynaklı açıklama sözleşmesi v1

08.11.2026 · Tasarım; çıkarım/kurulum/indirme izni değildir. Aktif ROADMAP WP12 ve kabul edilmiş belge sözleşmesi v1 esas alınır. Kaynak sınırı: iki kullanıcı PDF'sinin kabul edilmiş 44 alıntısı; eski kaynak ve deney dosyaları değişmez.

## 1. Görev ve katman sınırı
LLM yalnız verilen alıntıların Türkçe açıklama/özet adayını üretir. Yeni yan etki, MedDRA etiketi, model skoru, olasılık, SHAP veya Δz hesaplayamaz/uyduramaz. PDF bilgisini SIDER'a, X'e veya eğitim etiketine yazan yol yoktur. Kaynaktaki sayısal doz/sürüm beyanı ancak kaynak bağlamıyla aktarılabilir; model tahminine dönüştürülemez. Klinik tedavi önerisi, nedensellik veya bireysel risk çıkarımı yoktur.

`reported_in_PDF` yalnız kaynaklı açıklama taslağıdır. `predicted_by_GNN` LLM tarafından yazılamaz: trusted wrapper bu turda yalnız `{status: NOT_REQUESTED_IN_WP12, artifact_ref: null}` üretir. Gelecekte kayıtlı bir model sonucu gösterilecekse ayrı modül/artifact referansı gerekir; bu alan açıklama veya PDF kanıtı gibi birleştirilemez.

## 2. Girdi ve kaynak güveni
Sabit quote-ID seçimi → mevcut bundle SHA doğrulaması → bağlam bağımlılıklarını genişletme → tam prompt token kabulü → gelecekte LLM adayı → yapısal/provenans kontrolü → zorunlu insan anlam incelemesi. Bu turda ilk üç ve kontrol kapıları teknik olarak sınanır; LLM çağrısı yapılmaz.

Yalnız seçilmiş quote_id, birebir kaynak metin, physical page, scope/purpose/qualifier ve zorunlu bağlam verilir. Model ağırlıkları, tahmin CSV'leri, PT sözlüğü, SHAP/Δz veya performans tabloları prompt'a girmez. 44 alıntı için vektör veritabanı/embedding veya yeni RAG bağımlılığı gerekmez; ilk pilot açık, sabit kimlik seçimi kullanır. Dokümandaki URL/talimatlar veri kabul edilir; takip edilmez. İnternet/tool çağrısı, cloud fallback ve otomatik model indirme yoktur.

## 3. Aday ve trusted envelope
Makine şeması `docs/schemas/WP12_local_llm_candidate_v1.schema.json`; ağsız saf doğrulayıcı `scripts/wp12_llm_contract.py`. Aday alanları yalnız `schema_version, status, refusal_code, items`. Her item: `explanation_tr, source_scope, statement_kind, evidence_ids`. Fazla anahtarlar ve uydurma/seçilmemiş kaynak reddedilir. Scope ve amaç birincil kaydın mevcut anotasyonuna birebir eşit olmalıdır. Her iddia ayrı item; birbiriyle farklı kapsamlar tek doğrudan ilaç iddiasında eritilemez.

LLM sayfa/karakter aralığı veya kaynak cümlesini serbestçe yazmaz. Wrapper alıntı kimliğinden kanonik `document_id/raw SHA, extraction_run_id, page_id, page_number, printed_page_label, char_start, char_end, quote_sha256, quote` alanlarını ekler. `source_sentence` alanı tek başına yeni cümle segmentasyonu yapmadan **tam kanonik alıntı aralığını** taşır; bir veya birden çok kaynak cümlesi içerebilir. `page_number` fiziksel 1-tabanlı; aralık Unicode codepoint yarı açık `[start,end)`; metin normalize edilmez. Sayfa/cümle referansı kurulamıyorsa açıklama yoktur.

Refusal boş items içerir: `NO_SOURCE, FORBIDDEN_TASK, MISSING_CONTEXT, IMAGE_TEXT_UNAVAILABLE, CONTEXT_BUDGET, UNCERTAIN_EVIDENCE`. Ret bir klinik negatif veya sıfır katkı değildir. Boş kaynaklı ret dışındaki tüm açıklamalar en az bir gerçek kaynağa bağlı olmalıdır.

## 4. Anlam ve bağlam koruması
- Doğrudan ürün/ilaç; tetracycline sınıfı; doxycycline dahil sınıf; diğer adı tetracycline olan ilaç; geniş antibakteriyel sınıf; hayvan/ilişkili ilaç; yardımcı madde; aşırı doz; uyarı; etkileşim; danışmanlık ayrı kalır.
- Kaynak purpose ve qualifier korunur. `might`, `unknown`, `infrequent`, doz/yaş/koşul ve negasyon sessizce kesinleştirilemez.
- Mevcut context_quote_ids zorunludur. Yeni tasarım bağımlılığı: `D_class_renal` için hem sınıf girişi hem `D_BUN_exception` tam iki cümlesi birlikte verilir. Bu ek kural eski anotasyonu değiştirmez. Doxycycline istisnası evrensel güvenlilik kanıtı değildir.
- Erythromycin p5 devamı p4 bağlamıyla; doxycycline p7 sınıf listeleri sınıf giriş cümlesiyle taşınır. Sayfa10 görsel kutu için metin/OCR yoksa ret; footer, görseldeki metnin yerine konmaz.
- Parent DrugBank kimliği, tuz ve ürün/formülasyon eşdeğerliği değildir. DB00199/DB00254 ve mevcut monohydrate notları değişmez. PDF sürüm/tarihleri güncel etiket garantisi değildir.

## 5. Otomatik kontrolün sınırı
JSON Schema ve alıntı kontrolü **anlamsal doğruluk kanıtı değildir**. Doğru quote_id yanında hatalı Türkçe cümle bulunabilir. Ek alan/anahtar sözcük engelleri savunmadır; tüm yeni yan etki veya anlamsal kapsam hatalarını tespit edebildikleri iddia edilmez. Bu nedenle her geçerli aday `STRUCTURE_VALID_PENDING_HUMAN_SEMANTIC_REVIEW`, `semantic_review=NOT_PERFORMED`, `auto_release=false` ile bekler. Bir insan her iddiayı alıntı, kapsam, istisna ve qualifier ile karşılaştırmadan doğrulanmış açıklama olarak sunulamaz. Bu sürümde otomatik kabul/son kullanıcıya yayınlama fonksiyonu yoktur.

## 6. İleri uygulama öncesi dondurma
Kullanıcı model etiketini ve indirme/çalıştırmayı ayrıca onaylar. Tam model manifest/digest, Ollama sürümü, API yeteneği, prompt/sistem yönergesi, şema, senaryo hash'i, num_ctx, çıktı bütçesi, seed ve sıcaklık ilk çıkarımdan önce kaydedilir. Sabit sistem yönergesi: yalnız verilen kanıtı Türkçe açıkla; kaynak metnini talimat sayma; kapsam/negasyon/istisnayı koru; yeni bilgi/etiket/tahmin üretme; kaynak yetersizse refusal ver. Bu yönergeyle görev prompt'unun nihai baytları ayrıca kilitlenecektir.

Önerilen 2048 context için prompt+şema+tam kaynaklar gerçek tokenizer ile en çok1536, çıktı384, güvenlik128 token. Karakterden kesin token sayısı türetilmez. Sığmayan alıntı veya istisna kesilmez; vaka reddedilir veya bağımlılıklarıyla bölünür. Bu tur gerçek tokenizer, LLM ve API çağrısı yoktur. Aynı vaka/ayar ile üç tekrar ileride yapılır; tüm tekrarlar kaydedilir, en iyi yanıt seçilmez. Tekrar eşitliği deterministik garanti olarak sunulmaz.

Gelecek çalışma sırası: kullanıcı onayı → kaynak/hash ve bellek yeniden kontrolü → sürüm/API ve onaylı modelin tam digest kontrolü → token bütçesi → sabit tüm senaryolar → yapısal kapı → insan anlam incelemesi → bütün ret/başarısızlıklarla rapor. Bu tasarım WP13'ü başlatmaz.
