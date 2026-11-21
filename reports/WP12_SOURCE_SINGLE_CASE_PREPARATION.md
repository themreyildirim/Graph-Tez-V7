# WP12 — Kaynaklı tek-vaka pilot hazırlığı v1

08.11.2026 · **S01-R1 kullanıcı çalıştırması bekleniyor. Gerçek açıklama üretilmedi.**

AGENTS.md, aktif ROADMAP WP12 ve `WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md` korundu. Kullanıcı kabul ettiği teknik echo ardından gerçek PDF açıklamasını normal PowerShell'de tek istekle sınayacak. Codex AppContainer'dan Ollama API'ye bağlanılmadı; kısıt aşılmadı. İndirme, yeni eğitim, servis kapatma, güvenlik değişikliği veya WP13 yok.

## 1. Değişmeyen kaynak ve ilk vaka

- Frozen19 listesinin ilk vakası **S01**; seçim sonuç başarısına bağlı değil. Soru: “Ürün ve formülasyon kaynakta nasıl tanımlanıyor?”
- Kabul ölçütü aynen: “Ürün beyanını ana ilaç kimliğine eşdeğerlik iddiasına dönüştürme.”
- Erythromycin kullanıcı PDF'sinin fiziksel sayfa1 ve6'sından `E_identity` ve `E_formulation`; iki tam alıntı toplam537 karakter. Ham PDF hash'leri,44 alıntının sayfa/aralık/hash'i ve bağlam bağımlılıkları doğrulandı. Yeni PDF çıkarımı yapılmadı.
- `package/context.json` kaynak metinlerini, `package/request.json` gönderilecek sabit isteği taşır. Tam prompt, kaynak quote-ID/metin/sayfa/scope/kind/qualifier ve v1'in yalnız bu vaka için daraltılmış geçerli JSON Schema alt kümesini içerir. Eski v1 şeması değişmez. Sayfa/aralık/ham SHA çıktıya trusted wrapper ile eklenir.
- Model **gemma3:1b-it-q4_K_M**; API/source digest **sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c**. Yerel wrapper `313f48e3…` ayrı dosya SHA'sıdır, API digest ile karıştırılmaz. Önceki teknik identity helper aynen kullanılır. GGUF tensor dosyasının SHA'sı ayrıca kontrol edilir.

## 2. Gerçek token bütçesi ve sınırları

Kurulu Ollama0.40.6 için genel `/api/tokenize` uç noktasına güvenilmedi. Aynı kurulu libllama/ggml DLL hash'leri ve model GGUF `tokenizer.chat_template` sabitlendi. Küçük Python ctypes adaptörü, mevcut native build620d2225c ABI'sinde `vocab_only=True`, GPU layers0 ile **yalnız sözlük** okur; tensor/context/decode/sampler veya model inference oluşturmaz. Paket kurulmadı. GGUF metadatası16MiB üst sınırla okunur; model dosyası bütünlük hash'i1MiB bloklarla alınır, belleğe bütünüyle yüklenmez.

| Alan | Değer |
|---|---:|
| S01 yönerge + JSON Schema + soru + tam alıntı + özgün chat şablonu | **919 token** |
| İzinli giriş |1536|
| Çıktı rezervi |384|
| Güvenlik rezervi |128|
| Toplam context |2048|
|919+384+128 sonrası boşluk|617|

Geçmiş gerçek smoke'un41 `prompt_eval_count` değeri aynı offline yolla41 bulundu; ikinci BOS eklense42 olur. Şablonun kendi dış boşluk temizliği kaynak kesmek değildir; JSON içindeki ham alıntılar değişmez. Bu geçmiş hizalama gelecekteki gerçek istekte token eşitliğini garanti etmez: **yeni yanıttaki sunucu sayısı919 ile ayrıca karşılaştırılır; fark varsa TOKEN_COUNT_ALIGNMENT_FAILED ve insan incelemesi gerekir**. Karakter/token oranı tahmini veya sessiz kesme yok. `truncate=false`, `shift=false`;1536 üzeri tam prompt'ta üretim yapılmaz. Şema ayrıca prompt'ta olduğundan grammar için görünmeyen metin varsayılmaz. Büyük sahte test eki yalnız testte kullanıldı; gerçek kaynak veya frozen vaka değiştirilmedi.

Resmî uygulama dayanakları: [Ollama0.40.6 routes](https://github.com/ollama/ollama/blob/v0.40.6/server/routes.go), [API tipleri](https://github.com/ollama/ollama/blob/v0.40.6/api/types.go), [tokenizer köprüsü](https://github.com/ollama/ollama/blob/v0.40.6/llm/llama_server.go), [kurulu native commit ABI](https://github.com/ggml-org/llama.cpp/blob/620d2225c/include/llama.h). Bu yerel adaptör tam bu hash/sürümle sınırlıdır; runtime değişirse işlem durur, tahmini sayıya dönmez.

## 3. İstek kapıları ve kayıtlar

Onaylı v2 eşikler değişmedi: başlangıç RAM≥2,5GiB, boş GPU≥2GiB, commit alanı≥3GiB; RAM/commit için5 örnek/4 saniye ve gönderim öncesi RAM/GPU yeniden kontrolü. HTTP timeout60s, çalışma RAM uyarısı1GiB. Hazırlık anlık ölçümü RAM **1.683GiB**: model başlatma kapısı **geçmedi**. GPU3935MiB boştu; bu tepe ölçümü veya çalışma garantisi değildir. Kullanıcı uygulamalarını kendi kararıyla kapatıp komutu çalıştırdığında kapılar tekrar ölçülür. Betik uygulama/servis kapatmaz; eşik düşürmez.

Teknik echo'dan farklı gerçek kaynaklı üretim bütçesi mevcut açıklama sözleşmesiyle2048context/384output/batch32/temperature0/seed20261108/thinkfalse/streamfalse/keep_alive0 olarak kilitlidir. Üretim bir kez `/api/chat`; retry, en iyi tekrar seçimi veya fallback yok. Önce version/tags/ps salt okunur metadata; tam kimlik/helper/source/native/PDF hash ve gerçek tokenizer kapısı; sonra kararlı bellek ve tek üretim. Başka yüklü model varsa otomatik unload yerine durur. AppContainer algılanırsa üretim yok.

Her kullanıcı çalıştırması benzersiz `reports/qa/WP12/source_single_case_user_runs/<zaman_GUID>/` klasörü açar. `run_record.json`, metadata, token bütçesi, tam prompt/request, kaynak bağlamı, ham yanıt, Python stdout/stderr, bellek örnekleri, süre/HTTP/hata ve dosya hash'leri saklanır. Timeout'ta sunucunun durmuş olduğu iddia edilmez; HTTP iptali süreç sonlandırmaz. `inference_attempts` gönderim teşebbüsüdür; yerel istemci kaydı sunucudaki başka istemciler için global ağ kanıtı değildir. Ham HTTP hata gövdesi de korunur; hata veya ret başarıya çevrilmez.

## 4. Yapısal ve semantik değerlendirme ayrı

JSON Schema, tamamlanma/stop, doğru model, token sayısı, seçilmiş quote-ID, kaynak scope/kind, bağlam bağımlılıkları kontrol edilir. Eksik kaynak, fazla skor alanı, yanlış kimlik, eksik çıktı, length stop ve duplicate JSON anahtarları reddedilir. Geçerli aday bile **SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW**, semantic_success=null, automatic_release=false kalır. Ret **MODEL_REFUSAL_RECORDED**; başarı değildir. Yanlış Türkçe cümle doğru quote-ID ile yapısal kapıyı geçebilir; bu sınırlama testte gösterildi. İnsan alıntıyı, ürünü, formülasyonu, belirsizliği ve kaynak dışı iddiayı karşılaştırmadan açıklama kabul edilmez.

`reported_in_PDF` gerçek kaynak cümlesi/sayfasıyla ayrı; `predicted_by_GNN` trusted wrapper'da NOT_REQUESTED/null. Model skoru, SHAP, Δz veya MedDRA üretimi ve otomatik yayın yok. Bu çalışma klinik risk veya nedensellik doğrulaması değildir. `first_case_human_review_template.json` henüz boş/kararsız inceleme formudur; gerçek model çıktısı değildir.

## 5. Gelecek ikinci aşama — bu tur kapalı

`stage2_plan_NOT_EXECUTABLE.json` frozen19×3=57 yuvayı aynen kaydeder; bulk executor verilmedi. S01-R1 yalnız aynı prompt/model/ayar hash'leriyle insan kabulü alırsa ilk yuva olarak sayılabilir; kalan56. İlk yanıt kötü/ret/eksik olursa otomatik devam yok; yeni sonuç seçimi veya sessiz prompt ayarı yok. Bellek/API/source/token kapıları ileride her istekten önce yeniden gerekir. Bütçe reddi veya kaynak eksikliği olan yuva kayıtlı ret/NOT_RUN kalabilir;57 gerçek generation garantisi verilmez.

Özellikle S04 Erythromycin bilinmeyen sıklık/sayfa4–5 bağlamı, S06 tetracycline sınıf listesi, S07 BUN sınıf ifadesi ve doxycycline istisnasının tam bağlamı, S17 kaynak dışı skor/etiket talebi için gerçek kanıtlar `critical_scenario_review_materials_NOT_RUN.json` içindedir. Kaynaklar/kriterler değişmedi; bu vakalar çalıştırılmadı. Uyarı, etkileşim, sınıf ve doğrudan ilaç ifadeleri tek kanıt gibi birleştirilmeyecek.

## 6. QA ve korunma kanıtı

- İlk turda2 test beklentisi hatası vardı: özgün Jinja dış trim'i ve ilk-yuva bekleme durumu. Test beklentileri düzeltildi, ilk başarısız log korundu. Kaynak veya yöntem bu nedenle değişmedi.
- Tam tur **30/30** geçti; gerçek native41/919 sayımı ve aşırı context reddi dahil. Eski saf kaynak sözleşmesi **24/24** geçti.
- Son çalıştırıcı güvenlik düzenlemesinden sonra **25 test geçti;5 native test**, kendi1,5GiB yalnız-sözlük utility guard'ında o anki RAM nedeniyle sınıf olarak atlandı. Bu, gerçek model için2,5GiB kapısını değiştirmez. Başarılı önceki native test/tam sayım kanıtı saklıdır; son atlama gizlenmez.
- Windows PowerShell **5.1.26100.9711** parser:0 hata; AST'de1 PostAsync. Betik çalıştırılmadı. Son hash: `606e5601a685b1aa10a8d8e7eb25f1c05117da9f89426fc343c7ea75fc2c54d5`. Geliştirme parser logları da korunur; güncel hash `powershell_5_1_release_syntax.json` içindedir.
- Önceki **3503** dosyanın tamamı güncelleme öncesi aynı SHA ile doğrulandı. WP00–11/GNN/SHAP/PPI/model/QA, PDF ve frozen19 korunur. Kapanış manifesti yeni dosyaları kapsar. Sadece güncel run_status yeni bölüm ekler; önceki baytlar `run_status_before.md` ve dosyanın tarihsel devamında korunur.

## 7. Kullanıcı komutu ve durma noktası

Normal kullanıcı PowerShell'inde, RAM kapısının yeniden ölçülmesine izin vererek **yalnız bir kez**:

```powershell
& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_SourceSingleCase_v1.ps1" -RunFirstCase
```

ExecutionPolicy değiştirme veya yönetici çalıştırma talimatı yoktur. Komutun yazdığı `Evidence directory` klasörü ilk gerçek yanıtın bağımsız incelemesi için paylaşılmalıdır. Bu aşamada yalnız S01-R1 hazırlandı; kullanıcı çıktısı bekleniyor.19×3 çalıştırılmadı, WP13 başlatılmadı.

Çıktılar: `notebooks/WP12_source_single_case_preparation.ipynb` çalıştırılmış Türkçe öğretici notebook; `reports/figures/WP12/source_single_case_v1/` gerçek token/bellek PNG'leri; `reports/qa/WP12/source_single_case_v1/` test, kaynak/prompt, plan ve manifest kanıtları; `configs/WP12_SOURCE_SINGLE_CASE_v1.json` sabit politika; modüler Python dosyaları kaynak/token/yanıt doğrulayıcılarıdır.
