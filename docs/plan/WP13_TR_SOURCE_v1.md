# WP13_TR_SOURCE_v1 — Kullanıcı Türkçe PDF kaynak sözleşmesi

09.11.2026. Aktif ROADMAP WP13 / WP13_DEMO_SCOPE_v1 kapsamında ayrı Türkçe pilot; frozen WP12 ve İngilizce v1.1/v1.2 değiştirilmez. Yeni API, eğitim, OCR ve dış ilaç tahmini yok.

## Kaynak kimliği ve sürüm

İzinli iki kullanıcı dosyası data/user_pdfs altında yerinde okunur. ERİTRO500 mg film tablet **Kullanma Talimatı (KT)**, MONODOKS100 mg kapsül **Kısa Ürün Bilgisi (KÜB)**. Kullanıcının KÜT ifadesi belge üzerindeki KT başlığını değiştirmez. Ham SHA-256 bağımsız document_id; fiziksel sayfa1 tabanlı, karakter aralığı Python Unicode `[start,end)`. PyMuPDF get_text(text,sort=False,flags=195) çıktısı değiştirilmeden tüm sayfalarda saklanır. Ad gösteriminde yalnız satır sonu/boşluk sadeleştirilebilir; birebir alıntı ve hash değişmez. Boş/görsel sayfa atlanmaz; OCR yok. Metin kaynağı eksikse STOP/NOT_AVAILABLE.

ERİTRO:500 mg eritromisine eşdeğer750 mg eritromisin stearat/film tablet; MONODOKS:100 mg doksisikline eşdeğer115,414 mg doksisiklin hiklat/kapsül. Bileşim ve ürün sayfa1 alıntılarıyla bağlanır. DB00199/DB00254 yalnız mevcut ana etkin madde kayıtlarıyla araştırma bağlantısıdır. İngilizce250 mg eritromisin tablet veya doksisiklin monohidrat ürünleriyle ürün/tuz/doz eşdeğerliği **NOT_ESTABLISHED**. PDF'den yeni DrugBank ID üretilmez.

Her kayıtta raw_sha256, byte_size, tüm sayfalar/text hash/image_count/status, parser sürümü, dil, belge türü, ürün/tuz/doz, kimlik kanıtı, dosya adı tarih ipucu ve belge içi tarih kanıtı tutulur. **Güncellik UNVERIFIED_CURRENTNESS**: ERİTRO onay tarihi alanı boş/yer tutucu, MONODOKS KÜB yenilenme tarihi alanı boş;07-11-2018 yalnız dosya adı ipucudur, doğrulanmış onay tarihi değildir. PDF metadata tarihlerinin editoryal/regülatör güncellik anlamı yok.

## Çıkarım ve kapsam

Bu iki belgede manuel incelenmiş bölüm/terim anchor listesi uygulanır; genel Türkçe tıbbi NER değildir. ERİTRO6–8 bölüm4: fiziksel6'daki6 ciddi-bulgu madde satırı ve7–8'de Bilinmiyor altında19 madde satırı; birleşik satırdaki her sendrom ayrı sayılmaz. MONODOKS9–10 bölüm4.8: her yerel sıklık paragrafında açıkça belirtilen terimler sonlu sürümlü listede ayrı adaydır. Terim eşleşmesi sıklık tanım paragrafından, endikasyondan veya4.9'dan yapılamaz. Örtüşen terim/pasaj bağımsız klinik kanıt değildir. Eski34/34 kopyalanmaz; toplam satır/benzersiz terim/başlık/kapsam/tekrar gerçek yeni kayıtlardan hesaplanır. Sayım birimleri iki belge formatında farklı olabilir; klinik sıklık karşılaştırması yapılamaz.

scope ve statement_kind iki ayrı alandır: product_specific, drug_direct, class_level, unresolved; adverse_candidate, warning, overdose, animal_study, identity, frequency_definition, version. Normal yan etki tablosu yalnız adverse_candidate.4.2/4.4 uyarılar ve hayvan/4.9 aşırı doz kaynak bağlamı ayrı, normal yan etki toplamına girmez.4.8'de açık tetrasiklin sınıf cümleleri sınıf düzeyinde; tüm KÜB listesi İngilizce sınıf girişi nedeniyle sınıf düzeyi yapılmaz. Bağlı uyarıda farklı kapsam varsa context kendi scope'unu korur.

frequency_state UNKNOWN / RARE_SOURCE_WORDING / NOT_SPECIFIED; frequency_exact ve frequency_quote ayrı. ERİTRO ciddi6bulguda sayfa7'deki **oldukça seyrek** aynen, sayısal oran atanmaz.19 diğer maddede **Bilinmiyor**; tabloda tanım bulunması diğer adayları yaygın/seyrek yapmaz. MONODOKS yerel Seyrek/Bilinmiyor başlığı sürer; belirsiz4.8 cümle kapsamı source_block ve inceleme notuyla korunur. Aktarılamayan kapsam unresolved/NOT_AVAILABLE olur; negatif iddia üretilmez.

MONODOKS4.2 akümülasyon yokluğu **BUN yokluğu değildir**;4.8 BUN artışı UNKNOWN kalır. Tiroid fonksiyonunda anormallik bilinmediği cümlesi, renk değişimi kaydına bağlı tutulur. Hayvan güvenlilik verileri insan yan etkisi yapılmaz. ERİTRO doz aşımı6 ve MONODOKS4.9/10 ayrı bağlamdır.

## UI ve koruma

Yeni offline Türkçe uygulamada aktif kaynaklar yalnız bu iki Türkçe PDF. İngilizceler tarihsel dosya/önceki launcher ile korunur. Önce Türkçe kaynak bilgisi, kaynakta yazan özgün aday adı, sıklık, kapsam, kaynak cümlesi ve uyarı/istisna gösterilir. Yeni çeviri/LLM yanıtı üretilmez. Yeni quote-ID'lere atıf yapan kayıtlı model açıklaması yoksa **NOT_AVAILABLE**, İngilizce kaydın cevabı Türkçe ürünün açıklamasıymış gibi iliştirilmez. İnsan adayı **PENDING**, klinik doğrulama NOT_ESTABLISHED; mekanizma/attribution kaynaksız eklenmez.

Tek candidate_id seçici/tablo/detay durumunu yönetir. Kaynak/hash doğrulaması klinik onay değildir. GNN paneli ayrı; açıkça ana etkin madde araştırma kaydı, kendi-fold kayıtlı A1P1 OOF, ürün eşdeğerliği kanıtı değil. PDF yan etkileri model girdisi olmaz. Yeni skor/fit yok.

Testler tüm belge/sayfa/alıntı/terim hash ve aralıklarını, KT/KÜB sürüm/güncellik, sıklık/kapsam/overdose/animal ayrımını, yanlış kimlik, BUN/birikim yanılgısını, kayıtsız açıklama ve seçim eşitliğini denetler. Gerçek tarayıcı ekranları, çalıştırılmış Türkçe notebook, QA ve koruma manifesti yeni tr_source_v1 dizininde tutulur. Önceki537+v1.2 kanıtları ayrı prior manifest ile salt okunur korunur. .env ve gizli dosyalar okunmaz/hashlenmez. run_status eski baytları arşiv+ek girişle korunur.
