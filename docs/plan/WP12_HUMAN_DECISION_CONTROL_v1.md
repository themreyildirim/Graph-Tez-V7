# WP12 — İnsan kararının ayrı kaydı v1

S01'in iki cümlesi için kullanıcı bu konuşmada olumlu kaynak incelemesi bildirdi. Bu beyan `S01_positive_user_statement_NOT_FORMAL_QA.json` içinde, özgün raw-response SHA-256 ve run kimliğine bağlı bir **beyan alındısı** olarak saklanır. Kayıt bir formal QA kararı değildir. Önceki `human_review_pending.json`, model `run_record.json`, manifestler ve PENDING alanları değiştirilmez.

## Kim, nasıl kaydeder?

1. Kullanıcı, kendisini veya yetkilendirdiği inceleyiciyi açıkça bir **proje inceleyici kimliği ve rolüyle** tanımlar. İşletim sistemi kullanıcı adı, dosya yolu veya Codex ajanı insan inceleyici kimliği olarak varsayılmaz. Resmî kimlik belgesi istenmez; proje içinde izlenebilir, kullanıcı tarafından açıkça seçilmiş bir kimlik yeterlidir.
2. Yetkili proje sorumlusu bu kimliği ayrı inceleyici kaydında yetkilendirir. Mevcut registry taslağı boş/NOT_ACTIVATED durumundadır. Bu tur kimse otomatik yetkilendirilmedi.
3. İnceleyici özgün iki item'ı ve alıntıları inceler; run-ID, raw-response SHA, item1/2, iki quote-ID, açık karar (APPROVED/REJECTED/NEEDS_CHANGES), inceleyici kimliği/rolü, zaman dilimli inceleme zamanı ve açık kullanıcı teyidi referansını birlikte verir.
4. `scripts/wp12_human_review_control_v1.py::validate_event` bu olayın biçim, atıf, hash ve kapsamını doğrular. Varsayılan PENDING veya kimliksiz olumlu beyan formal onay olmaz. Doğrulayıcı **dosya yazmaz**, mevcut QA durumunu değiştirmez veya yayımlamaz.
5. Açık ve atfedilmiş kullanıcı teyidinden sonra yetkili sorumlu olayı yeni, üzerine yazılmayan bir kayıt olarak ekler. Eski PENDING dosyaları tarihsel kaynak olarak kalır; etkin insan kararı gelecekte bu ayrı olay referansı üzerinden gösterilebilir. Bu tur böyle bir olay oluşturulmadı.

Taslak: `human_decision_event_TEMPLATE_NOT_SUBMITTED.json`. İnceleyici, karar ve tarih alanları boş bırakılmıştır; mevcut haliyle formal doğrulamadan geçemez. Registry taslağı: `human_registry_TEMPLATE_NOT_ACTIVATED.json`.

Bu teknik kontrol gerçek kişinin kimliğini kriptografik olarak kanıtlamaz; insanı adlandırma ve yetki verme proje sorumlusunun açık işlemidir. Kaynak sadakati onayı, biyolojik nedensellik veya klinik güvenlilik doğrulaması değildir.

## S07 yetkisi ayrı

Kullanıcı mevcut mesajında S07 tek-deneme hazırlığını ayrıca istedi. S07 hazırlık/yürütme yetkisi bu açık istek ve normal PowerShell komutundan gelir; S01'in resmî PENDING durumunu otomatik APPROVED'e çevirmekten gelmez. S04, S07 sonucu değerlendirilmeden çalıştırılamaz.
