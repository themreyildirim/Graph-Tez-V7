# WP12 — Küçük pilot bütçesi ve S07/S04 adaptörü v2

Bu ayrı sürüm eski V1 maliyet politikasını veya kayıtlarını değiştirmez. V1'in10 toplam HTTP sınırının6'sı, toplam10 inference rezervinin2'si kullanılmıştır. Eski$0,046 rezerv aynen taşınır; bilinmeyen ilk429 maliyeti sıfır varsayılmaz.

| Alan | V1 | Önerilen v2 |
|---|---:|---:|
| Toplam HTTP sınırı |10|30|
| Mevcut kullanılmış HTTP |6|6 — taşınır|
| Toplam inference rezervi/denemesi sınırı |10|10 — ek10 değil|
| Mevcut inference rezervi |2|2 — taşınır|
| Operasyonel rezerv tavanı |$0,24|**$0,25**, kullanıcının güncel sınırı|
| Her inference sabit rezervi |$0,02|$0,02|
| Her HTTP ek rezervi |$0,001|$0,001|
| Azami sabit rezerv hesabı |$0,21|10×0,02 +30×0,001 = **$0,23**|

30 HTTP, her olası inference için model-erişim GET +tam token-sayımı POST +üretim POST olmak üzere3 çağrıdan hesaplanır. Önkontrol hataları nedeniyle10 completed yanıt garanti edilmez; tüm hatalar/rezervler sayılır. Bu tur yalnız bir S07 çalışabilir. S07 tam giderse toplam9HTTP/3inference rezervi ve$0,069 olur. S04 hâlâ kilitlidir.

Model gpt-5.4-mini, input6000/output1200, reasoning none, no-cache-discount önhesabı, %20 pay,90s timeout, retry/Batch/araç kapalı koşulları korunur.6000+1200 token üst hesabı$0,0099, paylı$0,01188; inference rezervinden küçüktür. Resmî standart fiyatlar input$0,75/cached$0,075/output$4,50/milyon olarak tekrar kontrol edildi. [OpenAI Docs](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

V2'nin ayrı fiyat kontrol zamanı/24saat geçerliliği konfigürasyondadır; eski V1 zamanı değiştirilmez. Her HTTP öncesi kaynak/hash ve finansal rezerv denetlenir. Üretim öncesi tam model/instructions/input/schema [sunucuda sayılır](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count), ardından token/maliyet üst kapısı uygulanır. Sığmayan metin kesilmez; CONTEXT_BUDGET ile durur. Gerçek ücret raw usage'tan hesaplanır; cached/muhakeme çift sayılmaz. Usage belirsizliği yeni stop kaydı doğurur. Rezerv gerçek fatura değildir; vergiler/fatura düzeltmeleri veya hesap bakiyesi sorgulanmaz.

Normal kullanıcı komutundaki `-AcceptBudgetV2`, bu ayrı sınır teklifini yalnız yetkilendirilmiş tek S07 yürütümü için açıkça kabul eder. Flag yoksa ağ yoktur. Diğer senaryolar veya kalan tüm kapasite otomatik yetkilenmez.

## Senaryo adaptörü v2

Frozen soru/kriter/metin/scope/qualifier ve quote-ID'ler aynıdır. Kaynak payload'ına yalnız hesaplanmış zorunlu bağlam-ID listesi eklenir. S07:3alıntı/380karakter, DB00254. S04:3alıntı/3803karakter, DB00199; bu sayı örtüşen sayfa5/alt-bölüm alıntılarını içerir ve benzersiz sayfa karakteri değildir.

S07 renal item'ın birincil kaynağı D_class_renal; sınıf girişi ve iki cümlelik D_BUN_exception aynı item'da bağlamdır. S04 bilinmeyen sıklık item'ı sayfa5 devamını ve geçişli olarak sayfa4 başlangıcını içerir. Kaynaklar kesilmez veya örtüşme gerekçesiyle çıkarılmaz.

Root object içindeki result alanı nested anyOf candidate/refused dalları taşır; tüm object alanları required ve additionalProperties=false'dur. Candidate tam3 item ister. Her item scope/kind'i birincil anotasyona göre sınırlar; evidence listesinin uzunluk ve izinli kimlikleri kaynak kapanışından türetilir. Uygulama denetimi birincil sırasını, tekrarları, tüm3kaynak kapsamını ve geçişli bağımlılıkları ayrıca kontrol eder. Unsupported oneOf/if/not/prefixItems/uniqueItems kullanılmaz. [Structured Outputs alt kümesi](https://developers.openai.com/api/docs/guides/structured-outputs).

Refused dalı boş items gerektirir; candidate boş olamaz. Ret dalı hata/retleri kayıt altına almak içindir. Bu iki tam okunur/izinli kaynak profilinde NO_SOURCE/IMAGE_TEXT_UNAVAILABLE/MISSING_CONTEXT gibi model retlerinin uygunluğu desteklenmez; teknik JSON geçse bile uygulama incelemesinde başarısız/ret olarak ayrılır. Eksik kaynak/token/bütçe host tarafından inference öncesi durdurulur; API-native refusal ayrı kayıttır.

Eski S01'e özgü iki sabit cümle kontrolü kullanılmaz. Ortak kaynaklı açıklama yönergesi ayrı sürümlenmiş; S01 kimlik/formülasyon talimatı çıkarılmış ve yeni case talimatları sonuç görülmeden eklenmiştir. S07 istisna item'ında kaynak iki cümlenin anlamını korumak için iki kısa Türkçe cümleye izin verilir. Bu, yeni senaryoya gerekli ve açık bir adaptasyondur; S01 yanıtı/promptu değiştirilmez.

**Doğru quote-ID semantik başarı değildir.** Testlerde doğru ID'li ama yanlış anlama sahip TEST_ONLY cümleler teknik kapıyı geçebilir; semantic_success yine null, ajan ve insan PENDING kalır. Kaynak/istisna/negasyon/qualifier anlamı gerçek yanıt geldikten sonra okunacaktır. S07 ve S04 için ayrı semantik inceleme planları hazırlanmıştır; otomatik genel semantik classifier yoktur.

S01 olumlu kullanıcı beyanı ve formal kayıt süreci [ayrı kontrol belgesinde](WP12_HUMAN_DECISION_CONTROL_v1.md) tutulur. Mevcut formal PENDING dosyaları bu teklif nedeniyle değiştirilmez.
