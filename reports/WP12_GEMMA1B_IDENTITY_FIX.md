# WP12 — Gemma kimlik kontrolü düzeltmesi v2.1

**IDENTITY_FIXED — AWAITING_USER_SINGLE_SMOKE.** Kullanıcının onayıyla yalnız API/yerel dosya kimlik bağlaması düzeltildi. Eski v2 betiği/config/inceleyici, iki gerçek başarısız deneme ve önceki sonuçlar değişmedi. Yeni sürüm: `scripts/WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1`. Bu tur smoke/inference/API/indirme yapılmadı.

## Değişen kontrol
API için beklenen model/source manifest digest: **sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c**. Yerel wrapper dosyasının ayrı SHA-256 değeri: **sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16**. Yeni saf PowerShell yardımcısı API digest'ini ilk değerle karşılaştırır; gerçek wrapper dosyasını hash'leyip ikinci değerle karşılaştırır. Ardından wrapper'ın içerdiği kaynak manifesti hash'ler ve config/katman referanslarının aynı kaldığını doğrular. Kontrol kaldırılmadı; yanlış API kimliği veya değiştirilmiş metadata reddedilir. GGUF ağırlık dosyası bu kimlik kontrolünde yeniden okunmaz/yüklenmez; hash kontrolü wrapper ve kaynak manifest dosyalarına uygulanır.

Yardımcı betiğin SHA'sı da runner'a sabitlendi. Gerçek kullanıcı kaydında API digest, wrapper SHA ve kaynak SHA ayrı `identity_validation` alanlarında tutulur. Eski iki kaydı yeni digest ile yeniden yazmak veya başarıya çevirmek yoktur. v2.1 sonuç/inceleme dizinleri ayrıdır; probe/payload mantığı aynıdır.

## Değişmeyen koşullar
RAM **2,5GiB**, VRAM **2048MiB (2GiB)**, commit boşluğu **3GiB**, beş kararlı örnek/en az4sn, host uyarı sınırı1GiB ve **60sn timeout** aynen korundu. Context2048, çıktı384, batch32, seed20261108, sıcaklık0, think:false, stream:false ve keep_alive0 değişmedi. Payload, native ölçüm fonksiyonları, bellek/commit/kararlılık kapıları ve inference/iptal akışı kaynak blokları birebir karşılaştırıldı. Bir istek sınırı, retry/download yasağı ve19×3 kapısı aynı kaldı. Kimlik düzeltmesi RAM uygunluğunu veya modelin çalışmasını garanti etmez.

## Doğrulama
Ortamın varsayılan PowerShell motorunda **9 gerçek offline kimlik regresyonu** geçti: gerçek yerel cache+doğru API kimliği, raw/prefix biçimi, API yerine wrapper hash'inin reddi, yabancı digest, değiştirilmiş wrapper, değiştirilmiş kaynak manifest, yalnız küçük metadata kopyasıyla doğrulama ve iki eski gerçek API kaydının doğru kimlikle eşleşmesi. Testlerde HTTP, Ollama servisi veya inference yoktur. Yalnız testin kendi doğrulanmış TEMP dizinindeki küçük metadata kopyaları kullanılıp temizlendi; model dosyaları değişmedi. Gerçek motor sürümü PowerShell_native_engine.json içinde kayıtlıdır. İlk Windows PowerShell5.1 test dosyası çağrısı AuthorizationManager erişim hatası verdi; başarısız log korundu, yetki/ExecutionPolicy değiştirilmedi. Aynı yetkili offline test standart varsayılan motorla çalıştı; Windows PowerShell5.1 runtime başarısı iddia edilmez. PS5.1 ayrıştırıcısıyla runner/helper sözdizimi kontrolü ayrıca geçti.

Yeni inceleyici12 offline testi ve eski iki başarısız denemenin8 teşhis testi de geçti: **toplam29 test**. Bunlar gerçek yeni smoke başarısı değildir. Güncel runner ve yardımcı betik Windows PowerShell ayrıştırıcısından **0 sözdizimi hatasıyla** geçti.

Runner SHA-256: `86d6945fe00ae5b2d4b521cf85645f0b3bb70546f9fee9020e400cee63f77a6c`.

Yardımcı SHA-256: `27fb36d02fb9c6017450fdb8b9a54e9b3819d46465cdfdd3f697a352b60ef6f4`.

Sabitler ve kaynak-block eşitliği `reports/qa/WP12/gemma1b_identity_fix_v1/identity_only_invariants.json`, salt kimlik farkı `runner_identity_only.diff`, test/parse/hash kanıtları aynı yeni QA dizinindedir. Önceki bütün dosyalar başlangıç manifestiyle korunur; yalnız run_status öne eklenir, önceki tam baytları arşivlenir. Notebook gerçek test tablolarını ve doğru/yanlış kimlik ayrımını gösterir.

## Kullanıcının tek smoke komutu
Normal PowerShell'de RAM koşullarını sağladıktan sonra:

```powershell
& 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1' -RunSmoke
```

Betik bütün mevcut kapıları tekrar denetler; koşullar sağlanmazsa model yüklemeden durur. Çıktı yeni `reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/tarih_GUID/` dizinine gider. Yeni `scripts/wp12_gemma_v2_1_smoke_review.py` yalnız bu sürümün gerçek çıktılarını inceler; eski v2 inceleyici değişmez. Kullanıcı gerçek klasör yolunu paylaşınca ayrı inceleme yapılabilir. Yeni inference çalıştırılmadı; gerçek19×3, model indirme, eğitim veya WP13 başlamadı.
