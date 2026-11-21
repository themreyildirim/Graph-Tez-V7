# WP12 — S04 Erythromycin tek istek hazırlığı v1

S04 **NOT_RUN**. Bu hazırlıkta yeni API isteği, model eğitimi veya yöntem geliştirme yapılmadı. Kullanıcı S07 teknik sonucunu kabul etti; tam Türkçe/atıf kalitesini başarılı saymadı. Beyanı ayrı `S07_user_feedback_NOT_FORMAL_QA.json` kaydındadır; S01/S07 resmî insan QA kararları PENDING olarak korundu.

## Değişmeyen yöntem ve kaynak

S04 soru, kabul ölçütü, prompt ve Structured Outputs şeması S07 sonucu öncesi kaydedilmiş dosyalarla içerik/hash düzeyinde doğrulandı. Yeni sürüm yalnız S04 yürütüm yetkisi, ayrı sayaç/çıktı konumu ve tek komut sağlar. Önceki şema, kaynak alıntısı, prompt veya başarı kriteri değiştirilmedi.

DB00199 Erythromycin PDF fiziksel4–5 kaynakları: üç alıntı, örtüşmeler dahil3803karakter. Unknown alıntısı sayfa5→sayfa4 bağlamını taşır. Tam alıntılar `S04_source_dependencies.csv` ve notebook'ta görünür; API'ye tam PDF veya GNN çıktısı gönderilmez.

GPT-5.4-mini, reasoning=none, max_output_tokens=1200, input cap6000, timeout90s, store=false, tools=[], truncation=disabled; otomatik retry yoktur. Model erişimi ve exact `/responses/input_tokens` kontrolünden sonra yalnız bir inference yapılabilir. Bağlam sığmazsa kesme yerine durur. Kaynak/provider retleri ayrı kaydedilir, başarı sayılmaz.

## Bütçe ve anahtar

Mevcut toplam9HTTP/3inference/.069USD rezervi değişmedi. Üç S04HTTP adımı tamamlanırsa12HTTP/4inference/.092USD rezerv olur; toplam30HTTP/10inference ve.25USD tavan aynı kalır. Önceki429 ve bilinmeyen maliyetler silinmez/iade varsayılmaz. Altı bin input ve1200output üst sınırında uncached maliyet.0099USD, %20payla.01188USD; inference rezervi.02USD'dir. Bu plan gerçek kullanım/fatura/bakiye değildir.

Fiyatlar mevcut dondurulmuş v2 politikada input.75/cached.075/output4.50USD/milyon token olarak korunur ([resmî model belgesi](https://developers.openai.com/api/docs/models/gpt-5.4-mini)). Fiyat geçerlilik tarihi dolarsa yürütücü durur; limitleri kendisi genişletmez. Anahtar yalnız proje.env OPENAI_API_KEY'den alınır; raporda yalnız var/yok, Authorization veya anahtar/hash yoktur. API kimlik doğrulaması bu tur NOT_RUN.

## Doğrulama ve insan incelemesi

16 yeni ağsız test PASS; PowerShell AST sözdizimi hatası0. İlk16 testin birinde dosya serileştirme/satır sonu karşılaştırması başarısızdı. İlk log korundu; istek nesnesi ve prompt içerikleri değişmeden, kontrol serileştirme biçimini içerikten ayıracak şekilde düzeltildi. Test fixture'ları yalnız TEST_ONLY'dir ve model yanıtı diye sunulmaz.

İnceleme boyutları ayrıdır: teknik JSON/ID/bağımlılık; ajan kaynak okuması; tam Türkçe; item düzeyinde atıf; yetkili insan kararı. Bilinmeyen sıklık nadir/yaygın/yüzde veya kesin yokluk yapılamaz. May/usually/high doses/kidney problems gibi mevcut nitelemeler korunmalı; prospektüs uyarısı kişisel tedavi önerisine dönüşmemelidir. S01'e özgü sabit cümle kontrolü genel semantik değerlendirici olarak kullanılmaz. JSON geçişi ve doğruquote-ID tek başına semantik başarı değildir.

Mevcut245 önceki kamusal dosyanın hash'i, frozen19senaryo/44alıntı, PDF'ler, eskiGemmaFAIL/QwenNOT_RUN ve S01/S07 kayıtları doğrulandı. Bu sayım tüm proje dosyalarının yeni taraması değildir; önceki manifestlerden gelen açık allowlist kontrolüdür. Gizli dosyalar envantere/hash'e alınmaz. Gerçek S04 cevabı, token/maliyet ve anlam değerlendirmesi henüz yoktur; NOT_RUN/PENDING korunur.

## Normal kullanıcı PowerShell komutu

```powershell
& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_OpenAI_S04_SingleCase_v1.ps1" -RunS04
```

Yalnız tek S04 denemesi yetkilidir. Hata/timeout/ret dahil otomatik tekrar yapılmaz. Çıktı `reports/qa/WP12/openai_S04_user_runs_v1/` altında yeni benzersiz klasöre yazılır. Kullanıcı durum satırını ve Evidence_directory yolunu paylaşınca gerçek yanıt ayrıca değerlendirilir. Başka senaryo,19×3 ve otomatik yayın kapalıdır.

## WP13 ile ilişki

`docs/plan/WP13_DEMO_SCOPE_v1.md`, aktif ROADMAP'in mevcutWP13 satırının localhost Streamlit hedefini ayrıntılandırır. ROADMAP baytları ve önceki kabul edilmiş belgeler değiştirilmedi. WP12 S04/küçük pilotun bilimsel değerlendirmesi önceliklidir. WP13 uygulaması, yeni API ve yeni eğitim başlamadı.

Çıktılar: çalıştırılmış `notebooks/WP12_OpenAI_S04_preparation_v1.ipynb`, gerçek sayaç/koşullu plan PNG'si, kaynak bağımlılık CSV'si, yeni yetki/config manifesti,16test logu, PowerShell parse/hash ve ayrı kullanıcı beyanı. Gerçek API sonucu gibi sunulan temsilî veri yoktur.
