# WP12 — Gemma1B v2 bellek politikası ve tek teknik test

**Yeni, açık v2 öneri; v1 ve eski kararlar değişmez.** Bu tur model yükleme/API/indirme yapılmadı.19×3 ve WP13 yok. Tekrarlanan v1 hazırlığı yerine modelin gerçek mimarisinden hesap ve tek kullanıcı komutu sunulur.

## 1. Gerçek kanıt
Mevcut806.058.400bayt GGUF dosyasının yalnız metadata bölümü okundu: GGUFv3,340tensor kaydı,42 metadata alanı,6.513.118bayt metadata aralığı; tensor verisi veya ağırlık tensörü yüklenmedi.26 katman,1KV başlığı, K256/V256, sliding-window512, eğitim context32768 gerçek dosyadan doğrulandı. Kaynak model/digest önceki kabul edilmiş kimliğiyle aynı; yeniden indirme yok.

KV hesabı: `katman × KV başlığı × context × (Kboyutu+Vboyutu) × eleman_baytı`. Context2048 için FP16=52MiB, FP32=104MiB. Sliding-window512 indirimi uygulanmadan bütün26 katman tam context varsayıldı; motorun gerçek layout/padding/dtype tahsisi ölçülmedi. Bunlar tensor KV içeriği için teorik hesaplar, toplam runtime belleği değildir. [GGUF uygulama metadata tanımları](https://github.com/ggml-org/llama.cpp/blob/master/gguf-py/gguf/constants.py). Google config sayfası erişilemediği için oradan değer doğrulanmış sayılmadı.

## 2. v2 sayısal bütçe ve gerekçe
| Kalem | Host bütçesi | GPU bütçesi | Kanıt türü |
|---|---:|---:|---|
| Tam dosya ağırlığı |0,751GiB|0,751GiB|Gerçek dosya boyutu; iki alana birden maliyet yazılması muhafazakâr senaryo|
| Tam context FP32 KV |104MiB|104MiB|Gerçek mimariden hesap; SWA indirimi yok|
| Runtime/allocator/compute payı |0,5GiB|0,5GiB|**Ölçülmemiş mühendislik bütçesi**|
| Host staging/ek pay |0,25GiB|—|**Ölçülmemiş ek bütçe**|
| Sistem/display için referans rezerv |0,75GiB|0,5GiB|Politika seçimi; kritik işletim sistemi sınırının resmi tanımı değil|
| Toplam |2.352GiB|1.852GiB|Garantili üst sınır değildir|
| Yukarı yuvarlanmış v2 başlangıç kapısı |**2,5GiB boş RAM**|**2GiB boş VRAM**|Yalnız Gemma tek teknik smoke için|

Runtime payları tahmindir; belgelenmiş tepe bellek ölçümü değildir. Bu nedenle eşik çalışma veya kritik seviyeye hiç düşmeme garantisi olarak sunulmaz. GPU'ya tüm ağırlıkların yerleştiği varsayılmadı; host bütçesinde tam ağırlık+KV tekrar sayıldı. [Ollama FAQ](https://docs.ollama.com/faq) CPU/GPU/karışık yerleşimi ayırır; gerçek yerleşim ancak koşullar sağlanırsa test çıktısıyla değerlendirilir.

v1 **3GiB RAM /2,5GiB VRAM** aynen saklanır. v2 düşüşü, yalnız1B'nin gerçek0,751GiB ağırlığı ve hesaplanan KV'si, küçük batch32 ve ek rezerv bütçesine dayanır. Bu seçim hiçbir model başarımı veya gerçek senaryo sonucuna göre yapılmadı. Context2048, çıktı384, seed20261108 ve sıcaklık0 korunur; **num_batch32 v2'ye özgü yeni, açık bellek kısıtıdır**. Diğer kullanıcının servis ortamı/değişkenleri değiştirilmez. [Ollama context belgesi](https://docs.ollama.com/context-length) bağlam arttıkça belleğin arttığını belirtir; context yükseltme veya performans ayarı yoktur.

## 3. Başlamadan önce zorunlu koşullar
- Kullanıcının normal non-AppContainer PowerShell'i; aynı yerel tag ve tam313f… digest; doğrulanmış yerel API ve uygun motor sürümü.
- Başlangıçta ve inference hemen öncesinde RAM≥2,5GiB, VRAM≥2048MiB, **sistem commit boşluğu≥3GiB**. Commit boşluğu fiziksel RAM değildir; ayrı şarttır.
- En az4sn aralığa yayılan5 host RAM/commit örneğinin tamamı tabanı karşılamalı. Tek anlık iyileşme yeterli değildir.
- Önceden yüklü model varsa otomatik unload yok; servis/uygulama kapatmadan durur. Yeni model indirme, firewall veya yetki değişikliği yok.
- En fazla bir klinik içeriksiz JSON Schema echo; başka istek, otomatik retry veya19×3 döngüsü yok.

Çalışma sırasında host RAM250ms örneklenir.1GiB altında **yalnız mevcut HTTP isteğine iptal talebi** gönderilir; servis/süreç sonlandırılmaz. Bu, sunucu inference'ının kesin durduğunu göstermez. Sonuç CLIENT_CANCELLED_MEMORY_WARNING ve sunucu durumu UNKNOWN olarak korunur; yeniden deneme yapılmaz.0,75GiB referans rezervine yaklaşmadan uyarı marjı amaçlanır; diğer süreçlerin ani tahsisleri, örnekleme gecikmesi ve sunucunun iptale davranışı nedeniyle tam güvence verilemez. Bu sınırlama gizlenmedi; yeterli başlangıç/kararlılık kanıtı yoksa model hiç yüklenmez.60sn istemci timeout'u da sunucu tamamlanması garantisi değildir.

## 4. Bu makinede gerçek durum ve karar
Ölçüm **2026-11-08T04:17:20.583283+03:00**: boş RAM**1.54GiB**, boş VRAM3935MiB, commit boşluğu11.39GiB. GetPerformanceInfo commit sorgusu başarılı; yerel API çağrısı yapılmadı. Yeni2,5GiB RAM kapısı da geçilmiyor. **Şu anda kritik seviyeye düşmeden yükleme için yeterli kanıt yok; model yüklenmedi.** Kullanıcı uygulaması veya Ollama kapatılmadı. Bu ölçüm eski kararların yerine yazılmadı.

## 5. Tek kullanıcı komutu
Koşullar uygun hale geldiğinde normal PowerShell'de:

```powershell
& 'C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_Gemma1B_UserPowerShellSmoke_v2.ps1' -RunSmoke
```

Betik v2 koşullarını kendisi uygular; başarısız kapıda inference0 ile kayıt üretir. Varsayılan parametresiz kullanım yalnız metadata kontrolüdür. Her deneme ayrı `reports/qa/WP12/gemma1b_v2_user_smoke_runs/tarih_GUID/` klasörüne yazılır; tam klasör yolu paylaşılabilir. Yeni ağsız doğrulayıcı `scripts/wp12_gemma_v2_smoke_review.py`, yalnız bu sürümün klasörlerini, yeni schema/probe ve num_batch32 dahil sabit payload'u kabul eder. v1 dosya/kararları ezilmez. Ham kayıt korunur; gerçek kullanıcı çıktısı henüz yoktur.

Teknik echo başarılsa bile bu PDF özet kalitesi veya kaynak sadakati değildir. reported_in_PDF /predicted_by_GNN ayrımı,44 alıntı,19 senaryo ve insan semantik inceleme kapıları değişmez. Yeni yan etki, MedDRA, skor, SHAP veyaΔz üretilmez. Kaynaklı19×3 çalışması bu aşamada etkin değildir.

## 6. QA ve sınırlar
Gerçek metadata okuma, KV formülü, yanlış/truncated GGUF, v2 eşikleri/commit/NA ve kayıt doğrulaması için yeni testler; eski3GiB kapısı testleri ayrı korunur.50 offline test ve yeni PowerShell AST kontrolü yapıldı; bunlar gerçek model çalışması değildir. Notebook gerçek metadata, bütçe/varsayım ve güncel ölçümü kod altında gösterir. Runtime/tepe bellek ve JSON Schema desteği **NOT_RUN**; modelin çalışacağı iddiası yoktur. Önceki3.395 proje dosyası, bütün kabul edilmiş kaynak/deney/QA korunur. run_status eski tam baytlarını saklayarak güncellenir. Tek sonuç: gerekçeli v2 politika ve koşullu tek teknik test; mevcut düşük RAM ile yükleme yok.

Son kontrol: son örnekte veya kayıtlı çalışma örneklerinde host RAM1GiB altındaysa tamamlanmış echo da teknik başarı sayılmaz. Son test logları `.final.log` ekiyle ayrıca korundu;50 test yeniden geçti. Bu koruma örnekler arasındaki ölçülmemiş düşüşleri veya sunucu iptal davranışını garanti etmez.
