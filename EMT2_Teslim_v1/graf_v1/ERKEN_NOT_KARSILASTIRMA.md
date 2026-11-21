# Erken graf notu ile gerçek analizlerin karşılaştırması

Kaynak: legacy/Tez Öneri.md; gömülü image6, image7 ve image8 görselleri okundu. Bu tarihsel belgenin ileriye dönük ifadeleri uygulanmış deney kanıtı değildir.

| Notta istenen | Tarihsel kanıt | EMT2 raporlama eki / sınır |
|---|---|---|
| Graph/DiGraph, komşu listesi, derece, ağırlık | WP01 sentetik örnek + 9 düğümlük gerçek örnek; WP06 ağ metrikleri | WP07 kopyasında rol bazında ilaç çıkış ve protein giriş dereceleri; güven toplamı yalnız QA |
| Derece, aradalık, yakınlık | WP01 küçük yönsüz izdüşüm | İnsan-700 PPI için tümü; özvektör yalnız 49'luk bileşende, PageRank 63 protein üzerinde |
| Bağlı bileşen ve en kısa yol | WP01 küçük örnek ve WP06 PPI bileşenleri | 14 bileşen; ana bileşende 2,458 ortalama yol ve çap 5 |
| Community detection | Öğretici öneri | EMT2 Louvain seed=42; üyelik tablosu mevcut. Modülerlik 0,4149; işlevsel/klinik kümeler kanıtlanmadı |
| Path analysis, ilaçtan yan etkiye tüm rotalar | Ders notunda öneri | PT çıktı kenarları encoder dışında olduğu için böyle bir rota hastalık mekanizması olarak kurulmadı. Tüm basit yollar listelenmedi |
| Cycle detection / geri besleme | Ders notunda öneri | Yönsüz insan PPI'da çevrim uzayı boyutu m−n+c=184−63+14=135; bu, tüm çevrimlerin sayısı veya yönlü biyolojik geri besleme değildir |
| Kenar önceliği | EMT2 analizi | 184 çiftin ağırlıksız normalize kenar aradalığı ayrı CSV’de; model müdahale değeri ile karıştırılmaz |

Bu ek yeni hesaplamadır. Hedefe özgü tedavi, virülans veya biyolojik müdahale yorumu yapılmamıştır.
