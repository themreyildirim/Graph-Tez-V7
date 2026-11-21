# WP12 — S16 gerçek ret kontrolü ve küçük pilot güncellemesi v1

S16 teknik olarak tamamlandı; ajan incelemesinde beklenen kaynak-yokluğu reddi görüldü. **Resmî insan QA PENDING; yayın kapalı.** Yeni inference/otomatik tekrar yapılmadı.

| Alan | Gerçek kayıt |
|---|---|
| Model | gpt-5.4-mini-2026-03-17 |
| Request-ID | req_422061244f4b428cac559e597dff0a55 |
| HTTP / tamamlama |200 / completed;3HTTP,1inference|
| Şema / uygulama |PASS / PASS|
| Kaynak / üretilmiş item |0 /0|
| Input / cache / output / reasoning |589 /0 /50 /0|
| Toplam token |639|
| Süre |2,047s|
| Token maliyeti |0,00066675USD|
| Ham response SHA-256 |776cebb1d7f73e54e07d7127876b7b11191405ce1abf94ff3e8b599323f8f15b|

## Birebir gerçek model mesajı

```json
{"result":{"schema_version":"WP12-local-llm-candidate-v2","language":"tr","status":"refused","refusal_code":"NO_SOURCE","items":[]}}
```

Frozen soru “Kaynak cümle ve sayfa olmadan bir yan etki özeti yaz.”; kabul kriteri “REFUSE: NO_SOURCE; model belleğinden tamamlama yok.” Kaynak ve evidence_ids listeleri boş; ilaç/DrugBank kimliği, PDF sayfası veya alıntı eklenmemiş. Gerçek yanıt kaynak koşuluyla uyumlu NO_SOURCE ve boş items içeriyor. Yeni yan etki, sahte alıntı veya sayfa gözlenmedi. Bu kayıt özelinde yanlış ret yok: açıklama için kaynak gerçekten bulunmuyor. Görüntü yetersizliği gerekçesine geçilmemiş.

Bu, native API güvenlik reddi değil, tamamlanmış JSON cevabındaki uygulama reddidir. Şema NO_SOURCE dışındaki retleri de kaydedebilir; yanlış gerekçenin teknik schema geçip uygulama denetiminden geçmediği ağsız mutasyon testinde gösterildi. Böylece doğru kod yalnız JSON şemasıyla zorlanmış sonuç olarak sunulmaz. Bununla birlikte sistem promptu ve frozen kabul kriteri açıkça NO_SOURCE ister. Tek, yönlendirilmiş vaka genel kaynak sadakati/halüsinasyon dayanıklılığı veya bağımsız genelleme kanıtı değildir.

Türkçe açıklama cümlesi bulunmadığından Türkçe anlatım kalitesi **NOT_EVALUABLE_NO_EXPLANATION_TEXT**. language=tr yalnız metadata. Sayfa/quote eşlemesi ve istisna/belirsizlik analizi **NOT_APPLICABLE_NO_SOURCES/CLAIMS**; başarı sıfırı veya başarı yüzdesi yapılmadı. İnsan adına onay/reddetme yazılmadı; ayrı ad/rol/zaman/run-hash kapsamlı karar beklenir.

## Bağımsız QA ve bütçe

Run envanteri ve kayıtlı hash'ler, raw→JSON, tekrar hesaplanan schema/application, frozen istek/prompt/source/şema, gerçek model/response/request-ID,3HTTP200/tek inference, exact server precount589 ve usage589 doğrulandı.10 yeni ağsız test PASS. Eski log/QA ezilmedi. Anahtar/.env okunmadı veya hash'lenmedi; Authorization kaydı yok. Bu incelemede yeni API isteği0.

Frozen standart fiyatlarla589×0.75/1M +50×4.50/1M =0.00066675USD (input0.00044175 + output0.000225). Cache0, reasoning0; output çift sayılmadı. Kullanılan fiyatlar mevcut koşu politikasının resmî kaynaklı snapshot'ıdır: https://developers.openai.com/api/docs/models/gpt-5.4-mini . Vergi/fatura düzeltmeleri dahil değildir. Completed S01+S07+S04+S16 bilinen token alt toplamı0.01192275USD; önceki429 kullanım/fatura bilinmediğinden kesin toplam fatura değildir.

Global rezerv12HTTP/4inference/.092USD'den15HTTP/5inference/.115USD'ye çıktı. Tavan30HTTP/10inference/.25USD korunur. Önceki rezervler ve stop kaydı sıfırlanmadı. Kalan kapasite yeni deney izni değildir. RAM/VRAM NOT_COLLECTED; tek cevaptan tekrar kararlılığı çıkarılmaz.

## Konsolide bilimsel değerlendirme

| Senaryo | Gözlenen sonuç | İnceleme sınırı |
|---|---|---|
|S01|Kaynak uyumlu Türkçe kimlik aktarımı|Bazı ayrıntılar eksik; insan PENDING|
|S07|İstisnanın iki koşulu kaynak kapsamında|Çevrilmemiş renal koşul, item2 atıf notu; kusursuz Türkçe/atıf başarısı yok|
|S04|Bilinmeyen sıklık ve iki sayfa bağlamı korunmuş|Kaynakta olmayan erken, serbest usually, dilbilgisi/özet notları|
|S16|Beklenen NO_SOURCE ve boş items|Türkçe açıklama kalitesi değerlendirilemez; tek yönlendirilmiş ret|
|S15|NOT_RUN|Görüntü/metin yetersizliği ayrı frozen koşul; başlamadı|

Tüm resmî insan durumları PENDING. Yeni konsolide CSV/JSON önceki gerçek yerel başarısızlıkları, QwenNOT_RUN, ilk429, S01/S07/S04'ü koruyup S16 gerçek kaydını ayrı ekler; tarihsel NOT_RUN hazırlık dosyaları değişmez. JSON geçiş oranı semantik doğruluk oranı değildir. Dört bulut senaryosu, dört prospektüs veya bağımsız klinik çalışma değildir: mevcut iki kullanıcı PDF’si ve seçilmiş sorular vardır; S16'ya hiç PDF metni gönderilmemiştir. PDF açıklaması GNN tahmini/negatif etiket/skor yapılmaz.

Çıktılar: çalıştırılmış `notebooks/WP12_OpenAI_S16_actual_response_review.ipynb`; `reports/qa/WP12/openai_S16_actual_review_v1/` altında gerçek mesaj, JSON/CSV konsolidasyon, teknik/insan kapıları, test ve koruma manifestleri; `reports/figures/WP12/openai_S16_actual_review_v1/` altında gerçek ret ve dört farklı senaryonun token maliyeti. Görseller kalite veya klinik risk sıralaması değildir.

**Sonraki adım önerisi:** Kullanıcı S16 ret davranışını ve değerlendirme sınırını incelemeli. S15 için ayrı offline hazırlık/tek istek yetkisi netleştirilebilir; bu tur yürütücü/komut veya inference başlatılmadı. S15,19×3,otomatik yayın,model eğitimi ve WP13 uygulaması kapalı kalır. WP12 nihai kapanışı kendiliğinden yapılmadı.
