# WP12 — Kullanıcı onaylı koşullu yerel LLM çalışma planı v1

08.11.2026. Bu belge aktif ROADMAP WP12 kapsamındaki A/B/C/D yetki ve durma sınırlarını kaydeder; yeni yol haritası değildir. Kullanıcı V2 yöntemini, Aşama A tek isteğini ve koşullu Qwen hazırlığını açıkça onayladı. Kabul edilen V2 dosyalarının adında PROPOSED olması tarihsel addır; mevcut onayı geçersiz kılmaz ve dosyalar yeniden yazılmaz.

## A — Şimdi açık

Gemma3 1B aynı onaylı digest, kabul edilmiş aynı V2 schema/system/user prompt ve S01'in aynı iki tam Erythromycin alıntısı. Normal kullanıcı PowerShell'inde **en fazla bir** gerçek generation isteği. Tek-slot atomik CreateNew kaydı `reports/qa/WP12/conditional_local_llm_v1/control/stage_A_generation_claim.json` ile farklı/tekrar kullanıcı çağrılarında korunur. Kayıt tüketilirse reset/force/otomatik retry yoktur. Preflight'ta durulup slot alınmadıysa actual generation0 olarak kaydedilir. Codex AppContainer erişim engeli aşılmaz.

## B — Koşullu, henüz tetiklenmedi

Tamamlanmış gerçek GemmaV2 yanıtında JSON/application/Türkçe/kaynak/görev FAIL varsa tekrar küçük hazırlık izni istemeden mevcut Qwen3 4B için hazırlığa geçilir. Kaynak/dil incelemesi henüz PENDING ise PASS uydurulmaz. Yanıt üretilemeyen API/model yükleme/bellek engeli kaynak kalitesi FAIL sayılmaz; teknik blok ve NOT_EVALUABLE raporlanır. B'nin başlangıç durumu NOT_RUN_CONDITION_NOT_TRIGGERED.

Qwen indirilmeyecek. Yerel manifest/model digest'i ve normal kullanıcı API kimliği doğrulanacak. S01 soru/alıntı/kriter ve V2 mantığı aynı kalır; yalnız modelin zorunlu chat-template/tokenizer uyarlaması ayrı hash/manifestle yapılır. Tam prompt aynı context bütçesi içinde gerçekten sayılır; kesme yok. Qwen model dosya boyutu, mimari/KV context, runtime/offload ve fiziksel RAM/VRAM/commit/OS koşulları ayrı değerlendirilir. Gemma1,5GiB/1GiB eşikleri Qwen'e kopyalanmaz; daha riskli eşiklere otomatik düşülmez. Yerel eski Qwen politikası varsa tarihsel olarak korunur; güncel ayrı uygunluk değerlendirmesi olmadan Qwen yürütücüsü/inference açılmaz. Uygunsa normal kullanıcı PowerShell komutuyla tek gerçek deneme; uygun değilse ölçüm/engel raporlanır. Süreç kapatma, güvenlik değişimi, yetki yükseltme veya indirme yok.

## C — Gerçek sonuçlardan, ayrı durumlar

Schema, uygulama, Türkçe, PDF sadakati, sayfa/primaryquote, yanlış ret/eksik/uydurma, gerçek tokens/süre/bellek, insan incelemesi ayrı tutulur. JSON/CSV ham yanıtlar, gerçek kaynak-iddia tablosu, gerçek gözlemlerin PNG'leri, Türkçe rapor ve çalıştırılmış notebook, test/QA/hashler/güncel status üretilir. Çalıştırılmayan alan NOT_RUN; gerçek başarısız alan FAIL; insan incelemesi olmayan alan PENDING. Teknik ölçüm yoksa UNKNOWN/NOT_EVALUABLE; varsayılan0 değildir. İlk V1 başarısızlığı korunur. Aynı görülen vaka üstünde yöntem geliştirmesi, bağımsız genelleme/klinik doğruluk kanıtı değildir.

## D — Otomatik kapalı

Tek-vaka iyi olsa dahi19×3 başlamaz. Sonuçlar kullanıcıya sunulur; ayrı sonuç değerlendirme/onayı beklenir. Yeni eğitim, model indirme, otomatik yayın veya WP13 yoktur.

Bu koşullu izin disk dosyası `configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json` içinde de kayıtlıdır. Karar kuralları sabit kalır; gelecekteki durum/sonuçlar yeni QA sürümlerine yazılır. Model içeriği bu yetki kurallarını değiştiremez. Kullanıcı müdahalesi gerekmeyen test/rapor/hazırlıklar tamamlanır; AppContainer nedeniyle kullanıcı PowerShell çalıştırması gerekli olduğunda yalnız açık komut ve gerçek çıktı klasörü beklenir.
