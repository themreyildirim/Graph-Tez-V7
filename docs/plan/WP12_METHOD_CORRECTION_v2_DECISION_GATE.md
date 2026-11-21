# WP12 v2 yöntem karar kapısı — ÖNERİ

08.11.2026. Gerçek ilk S01-R1 başarısızlığı korunur.36 yeni+25 tarihsel test geçti; yeni prompt724 gerçek token; inference0.

| Karar | Öneri | Sınır |
|---|---|---|
|Schema|Ayrı candidate/refused oneOf, v2/tr beyanı|Schema semantik veya dil kanıtı değil|
|S01 kaynak|Tam iki alıntı ve kind-primary-ID bağı|Diğer18 vaka uygulanmış değil|
|S01 ret|Okunabilir metinde IMAGE_TEXT_UNAVAILABLE yok; kaynak profiline göre uygunsuz retler kapalı|Düşük kaliteli candidate başarıya çevrilmez|
|Dil|Açık system Türkçe, sınırlı İngilizce uyarısı, her aday için insan incelemesi|Otomatik dil/semantik başarı yok|
|Prompt|System+user, format alanında şema;724token|Gerçek server count/grammar desteği henüz sınanmadı|
|Donanım/model|EXPERIMENTAL_LOW_MEMORY_v1 yalnız hardware alanları; mevcut Gemma/digest/ayarlar|Kapılar yeniden ölçülür; garanti yok|
|Gelecek deneme|WP12-method-v2-S01-R1-validation-01;en fazla1, no retry|Henüz yürütücü/çıkarım yok; kullanıcı yöntem onayı beklenir|

Ayrıntı reports/WP12_METHOD_CORRECTION_v2_PROPOSAL.md ve QA change_manifest_v2.json. Başarılı olursa bile aynı gözlenen vaka üzerinde yöntem geliştirme kontrolüdür; bağımsız genelleme deneyi sayılmaz.19×3/model indirme/eğitim/otomatik yayın/WP13 yok.
