# WP12 — Beş senaryolu OpenAI küçük pilot bilimsel sonuçları v1

08.11.2026. Kayıtlı S15 gerçek yanıtı ve önceki S01/S07/S04/S16 incelemeleri birleştirildi. Yeni API isteği, OCR/görsel inference, eğitim veya otomatik yayın yapılmadı. **Tüm resmî insan QA kararları PENDING.** Bu rapor WP12’yi kendiliğinden nihai kapatmaz.

## S15 gerçek sonuç

Model gpt-5.4-mini-2026-03-17; request-ID req_d4b390c27f4546068795893431dc64cf; HTTP200/completed; tek inference/üçHTTP. Gerçek yanıt:

```json
{"result":{"schema_version":"WP12-local-llm-candidate-v2","language":"tr","status":"refused","refusal_code":"IMAGE_TEXT_UNAVAILABLE","items":[]}}
```

PDF/sayfa/görsel gerçekten mevcut. Doxycycline fiziksel10’da1görsel nesne ve154karakter footer var; kutunun metni frozen metin çıkarımında bulunmuyor. Sayfa tam metni, PDF hash’i ve kabul edilmiş çıkarıcı seçenekleri tekrar doğrulandı. Footer görsel kutusunun kanıtı değildir. API’ye görsel, PDF veya footer alıntısı gönderilmedi; yalnız frozen soru/kriter ve kaynak kullanılabilirlik metadatası gitti. OCR/vision eklenmedi. Bu nedenle NO_SOURCE yerine IMAGE_TEXT_UNAVAILABLE gerekçesi doğru koşulla uyumludur (ajan değerlendirmesi). Model kutu içeriği, yan etki veya alıntı üretmemiştir.

Bu native API güvenlik reddi değil, tamamlanmış JSON içinde uygulama reddidir. Şema farklı retleri kaydedebilir; yanlış NO_SOURCE uygulama kontrolünden geçmez. Sistem ve kriter doğru ret koşulunu açıkça bildirir: tek yönlendirilmiş ret görsel anlama veya genel halüsinasyon önleme başarısı değildir. Açıklama metni olmadığı için Türkçe kalite NOT_EVALUABLE; language=tr başarı kanıtı değildir. Görsel kutu quote-ID eşlemesi NO_EXTRACTED_BOX_QUOTE; belirsizlik/istisna değerlendirmesi bu boş ret için uygulanamaz.

766input/cache0 +52output/reasoning0 =818token;1,328s. Input0.0005745 +output0.000234 =**0.0008085USD** token maliyeti. Exact server precount766 ile rawusage eşit. Fiyatlar frozen standart input0.75/cached0.075/output4.50USD/milyon snapshot'ıdır; önceki resmî kaynak https://developers.openai.com/api/docs/models/gpt-5.4-mini . Vergi/fatura düzeltmeleri dahil değildir.

## Beş senaryonun karşılaştırılması

|Senaryo|Teknik|Kaynak/ret değerlendirmesi (ajan)|Türkçe ve kapsam sınırlaması|İnsan|
|---|---|---|---|---|
|S01|JSON/uygulama PASS|Kaynak uyumlu ürün/etkin madde aktarımı|Bazı kaynak ayrıntıları eksik; iki cümle için olumlu kullanıcı beyanı ayrı kayıtta|PENDING|
|S07|PASS|İstisnanın iki koşulu korunmuş|impaired renal function çevrilmemiş; item2 atıf kapsamı notu; kusursuz kalite verilmedi|PENDING|
|S04|PASS|Bilinmeyen sıklık ve iki sayfa bağlamı korunmuş|Kaynakta olmayan erken; usually serbest aktarımı; dilbilgisi/özet eksikleri|PENDING|
|S16|PASS|Beklenen NO_SOURCE/boş items|Türkçe açıklama yok; yönlendirilmiş ret, genelleme kanıtı değil|PENDING|
|S15|PASS|Beklenen IMAGE_TEXT_UNAVAILABLE/boş items|Vision çalıştırılmadı; Türkçe anlatım değerlendirilemez|PENDING|

Beş tamamlanmış yanıtta JSON/uygulama kontrollerinin geçmesi **semantik doğruluk oranı değildir**. Açıklama kalitesi ve ret davranışı ayrı görevlerdir. Kaynakta olmayan nitelemeler, çevrilmeyen koşul ve atıf kusurları gizlenmedi. Tam model metinleri, gerçek PDF alıntıları ve önceki ajan notları `five_case_source_claim_comparison.csv/json` içinde; boş retler kaynak alıntısı uydurulmadan eklenmiştir. Yeni grafikler sadece gerçek kullanım/ret kaydından; notebook gerçek eski kaynak–iddia görsellerini de salt okunur gösterir.

Yerel GemmaV1/V2 başarısızlıkları, QwenNOT_RUN ve ilkOpenAI429 kaydı yeni tüm-denemeler CSV/JSON’unda ve eski dosyalarında korunur. Tarihsel NOT_RUN dosyaları yeniden yazılmadı. İlk429 inference rezervi dahil global18HTTP/6inference vardır; bunların5’i tamamlanmış bulut vakasıdır. Otomatik retry/en iyi çıktı seçimi yapılmadı. Senaryolar/model yöntemleri farklı olduğundan kontrollü eş görevli model üstünlüğü iddiası kurulamaz. S01 üzerinde yöntem geliştirme geçmişi açıkça korunur.

## Kaynak, örneklem ve değerlendirme sınırları

İki kullanıcı PDF’si,44frozen alıntı ve19frozen senaryo vardır. Bu küçük bulut pilotunda5senaryo uygulanmıştır; diğer14senaryo NOT_RUN. Beş farklı prospektüs, rastgele örneklem veya bağımsız klinik doğrulama yoktur. Üç kaynaklı açıklama ve iki kaynak-yetersizliği reddi, güvenilirlik/klinik doğruluk yüzdesine birleştirilemez. Tekrar kararlılığı tek cevapla değerlendirilemez. PDF sürümleri güncellik veya ürün→DrugBank eşdeğerlik garantisi değildir. Prospektüs bilgisi SIDER etiketi/model girdisi yapılmadı; predicted_by_GNN NOT_REQUESTED/null, reported_in_PDF ayrı katmandır.

## Harcama ve QA

|Senaryo|Input|Output|Token maliyetiUSD|
|---|---:|---:|---:|
|S01|1236|217|0.0019035|
|S07|1962|504|0.0037395|
|S04|2828|776|0.005613|
|S16|589|50|0.00066675|
|S15|766|52|0.0008085|

Bilinen completed token alt toplamı **0.01273125USD**. İlk429 usage/fatura UNKNOWN; bu kesin toplam fatura veya bakiye değildir. Rezerv15HTTP/5inference/.115USD'den18HTTP/6inference/.138USD'ye çıktı; eski stop/rezervler korunur. Tavan30/10/.25USD aynı, kalan kapasite yeni istek izni değildir.

10 yeni ağsız gerçek-kayıt testi PASS. Runhash/eksiksiz envanter, raw→JSON, request/source/prompt/şema eşitliği, response/requestID, exactprecount, bağımsız Decimal maliyet, kaynak metadatası, tek istek ve insan/yayın kapıları doğrulandı. Yanlış ret kodunun schema geçişi semantik başarı sayılmadı. Anahtar/.env okunmadı/hash'lenmedi; Authorization kaydı yok. RAM/VRAM NOT_COLLECTED, sıfır değildir. Önceki kabul edilmiş model/QC/deney çıktılarına yazılmadı.

## Çıktılar ve karar noktası

Çalıştırılmış `notebooks/WP12_OpenAI_five_case_pilot_results.ipynb`; QA `reports/qa/WP12/openai_S15_actual_review_v1/`; beş vaka özeti, tam geçmiş CSV/JSON, kaynak–iddia CSV/JSON, ham yanıt referansı, agent/insan ayrımı, test ve koruma manifestleri; `reports/figures/WP12/openai_five_case_pilot_v1/` altında gerçek ret ve usage grafikleri. `run_status.md` yeni durumla güncellendi; eski içerik tam baytlarıyla saklandı.

**Öneri:** Beş senaryolu sınırlı pilotu kullanıcı değerlendirsin. İnsan kararları ad/rol/zaman/run-hash/item-quote kapsamlı ayrı kayıtla yönetilmeli; ajan notları bu kararları değiştirmez. Mevcut WP13_DEMO_SCOPE_v1 localhost demo sınırları korunur: PDF/GNN ayrı paneller, kimlik/kapsam/QC sınırları, güvenli anahtar, kullanıcı başlatmalı bütçeli API ve gerçek uygulama ekran görüntüleri. WP13 kodlaması için ayrıca kullanıcı değerlendirmesi beklenir. Bu tur yeni API,19×3,yayın,eğitim veya WP13 uygulaması yoktur.
