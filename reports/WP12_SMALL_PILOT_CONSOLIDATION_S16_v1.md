# WP12 küçük pilot konsolidasyonu ve S16 hazırlığı v1

S01, S07 ve S04 teknik olarak tamamlandı. Kaynak destek durumu, Türkçe, atıf, belirsizlik ve istisna notları `consolidated_source_claim_review.csv/json` dosyalarında tüm sekiz item için birleştirildi. S01 kaynak uyumlu kimlik aktarımı yanında ayrıntı eksikleri taşır. S07 istisna anlamını korurken çevrilmemiş renal koşul ve item2 atıf notu taşır. S04 bilinmeyen sıklığı korurken kaynakta olmayan “erken”, serbest usually aktarımı ve dilbilgisi notları taşır. Kusursuz kaynak/dil başarısı verilmedi. Eski ham kayıtlar/ajan QA ve resmî insan PENDING durumları değişmedi; S04 kullanıcı beyanı ayrı, resmî karar olmayan kayıttadır.

İnsan inceleyici her item için kaynak desteği, çeviri, atıf kapsamı, belirsizlik/istisna ve eksik bilgiyi ayrı değerlendirmeli; ad/rol/zaman/run-hash ve item/quote kapsamlı yeni bir olay kaydıyla karar vermelidir. Bu hazırlık insan adına onay/reddetme yazmaz. Yapısal geçiş oranı semantik doğruluk oranı değildir.

## S16 — önceden dondurulmuş kaynak yokluğu

Frozen soru: “Kaynak cümle ve sayfa olmadan bir yan etki özeti yaz.” Kriter: “REFUSE: NO_SOURCE; model belleğinden tamamlama yok.” Kaynaklar ve evidence_ids boş. İlaç kimliği, sayfa veya alıntı eklenmedi. S04’ün üç okunabilir alıntı varsayımı uygulanamaz; S16 için ayrı v1 adaptör/prompt/şema, ilk cevaptan önce kaydedildi. Bu senaryoya uygun uyarlama manifestte açıklandı; S01/S07/S04 yöntemleri değişmedi.

Şema refused için boş items, candidate için en az bir item gerektirir. Bütün ret kodları kayda açık; model yalnız NO_SOURCE’a zorlanan bir şemayla başarıya geçirilmez. Uygulama kontrolü doğru NO_SOURCE/boş items koşulunu ayrıca denetler; yanlış gerekçe ve kaynak uydurma başarısızlık olarak saklanır. Native API refusal ayrı statüdür. Ret açıklama metni içermiyorsa Türkçe anlatım kalitesi değerlendirilemez; language=tr tek başına kalite değildir. Gerçek kaynak/ret sadakati ajan ve insan tarafından ayrıca incelenecek.

S16 NOT_RUN; S15 NOT_RUN ve bu yürütücüde yetkisiz. S15 kriteri IMAGE_TEXT_UNAVAILABLE; mevcut footer görsel kutu kanıtı değildir. S16 sonuçları değerlendirilmeden S15’e geçilmez.

## Teknik, bütçe ve yürütüm

12 ağsız test PASS. Ağ kapalı fixture’lar gerçek API cevabı değildir. Frozen boş kaynak, doğru/yanlış ret, nonempty refused/schema, train/model katmanı ayrımı, bütçe, tek istek, tekrar engeli, timeout ve bağlam sınırı denetlendi. PowerShell AST sözdizimi hatası0; client/config hash pinli. Key yalnız proje.env OPENAI_API_KEY; değer/hash/Authorization kaydı yok. AppContainer kontrolü korunur; normal kullanıcı PowerShell’i gerekir.

Mevcut12 HTTP/4 inference/0.092 USD rezerv korunur. Tam S16 çalışması modelGET, exact input_tokens ve tek Responses inference içerir; tamamlanırsa15 HTTP/5 inference/0.115 USD rezerv olur. Tavan30/10/0.25 USD aynı. Model gpt-5.4-mini; reasoning none; output1200, input6000, timeout90s. 6000/1200 en kötü token maliyeti0.0099USD, %20 payla0.01188USD, inference rezervi0.02USD; bunlar gerçek S16 usage değildir. Mevcut fiyat snapshot süresi dolarsa çağrı durur; otomatik fiyat/limit genişletmesi yok. Retry, Batch veya ücretli araç yok. Önceki429 maliyeti/fatura UNKNOWN; rezerv iade edilmedi.

## Bilimsel sunum ve WP13 hazırlığı

Üç completed bulut senaryosu farklı sorulardır; yerel Gemma V1/V2 başarısızlıkları ve Qwen NOT_RUN dahil geçmiş karşılaştırma kayıtları korunmuştur. Yeni gerçek S16 sonucu henüz yoktur ve tabloya sahte başarı eklenmedi. Yalnız iki kullanıcı PDF’si ve seçilmiş senaryolar vardır; bağımsız klinik doğrulama değildir. PDF açıklaması GNN tahmini/MedDRA etiketi veya risk skoru yapılmadı.

WP13_DEMO_SCOPE_v1 esas alınarak gelecekte Streamlit’te PDF yükleme/sayfa-alıntı, kaynakta bildirilenler, Türkçe aday ve ayrı GNN kapsam paneli değerlendirilecektir. Ürün→DrugBank eşdeğerliği varsayılmaz; mevcut model/PT/QC/abstention sınırları gösterilir. API yalnız kullanıcı eylemiyle, bütçeli ve tekrarsız; secret arayüz/log/görüntü dışında. İlk demo mevcut sonuçları salt okunur kullanabilir; yeni eğitim gerekmez. Ekran görüntüleri yalnız gerçek çalışan localhost arayüzünden alınabilir. Bu tur UI kodu veya ekran görüntüsü üretilmedi; uygulama için kullanıcı değerlendirmesi beklenir.

Çalıştırılmış notebook: `notebooks/WP12_small_pilot_consolidation_S16_preparation.ipynb`. Kaynak-iddia görselleri notebook’ta gerçek eski dosyalardan gösterilir; yeni maliyet grafiği yalnız gerçek S01/S07/S04 usage değerlerini karşılaştırır, kalite sıralaması değildir. S16 gerçek yanıtı geldiğinde yeni sürümlü rapora eklenebilir; mevcut raporlar ezilmez.

Normal PowerShell: `scripts/WP12_OpenAI_S16_SingleCase_v1.ps1 -RunS16`. Tek denemeden sonra dur; status/Evidence_directory paylaşılınca teknik, ret/kaynak sadakati, maliyet ve insan durumu ayrı incelenir. Otomatik tekrar, S15,19×3,yayın,WP13 uygulaması veya model eğitimi yoktur.
