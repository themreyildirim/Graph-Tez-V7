# WP12 — Yerel Qwen3 pilotu: ön kontrol ve bellek nedeniyle durma

08.11.2026 · **STOPPED_INSUFFICIENT_RAM**. Seçilen aday `qwen3:4b-instruct-2507-q4_K_M`; yeni model indirilmedi. Model yüklenmedi, smoke test veya gerçek LLM senaryosu çalıştırılmadı. WP13 başlamadı.

## Doğrulananlar
AGENTS, aktif ROADMAP ve WP12 kaynaklı LLM sözleşmesi korundu. Kullanıcının mevcut4B modeli seçmesi yalnız bu yeni aday kaydına işlendi; önceki öneri/config/19 senaryo/44 alıntı değiştirilmedi.

| Kontrol | Gerçek sonuç |
|---|---|
| Ollama istemci sürümü | `ollama.exe --version`: **0.40.6**; istemciye ait sürüm, servis sürümü doğrulanmadı |
| Yerel model manifest digest | `sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` |
| İçerik bütünlüğü | Manifest config ve4 layer dosyasının boyutu/tam SHA-256 doğrulandı; ağırlık akışla hash'lendi, inference için yüklenmedi |
| İlk RAM ölçümü | 03:23:20+03:00; boş **0,36GiB**, kullanım%95,1 |
| Kayıtlı ikinci ölçüm | 2026-11-08T03:24:53.806012+03:00; boş **0.93GiB**, toplam 7.42GiB, kullanım%87.4 |
| GPU | NVIDIA GeForce GTX 1650 Ti; toplam4096MiB, boş3935MiB; sürücü555.97 |
| Bellek kapısı | En az3GiB boş host RAM ve2,5GiB boş VRAM planlama tabanı; **RAM koşulu geçilmedi** |
| Yerel API metadata | Yalnız GET /api/version ve /api/tags denendi; WinError10013 socket erişim hatası; cevap alınamadı |
| JSON Schema API desteği | **UNVERIFIED**; gerçek şema kontrollü çıkarım yapılmadı |

Ölçümler anlıktır; 0,36→0.93GiB değişimi bellek boşaltıldığı veya kapının geçtiği anlamına gelmez. 3GiB kuralı üretici minimumu/sığma garantisi değildir; önceki tasarımın küçük aday planlama tabanıdır. Mevcut4B için bu taban sağlansa bile yeterlilik ayrıca sınırlı smoke testle ölçülmelidir. Burada taban dahi geçilmediğinden model yüklenmedi.

CLI “could not connect to a running Ollama instance” uyarısı verdi. API socket hatası, servisin kurulu olmadığı veya kesinlikle çalışmadığı kanıtı değildir; bu ortamda erişilemediği anlamına gelir. Servis başlatılmadı, güvenlik/izin ayarı değiştirilmedi, otomatik yetki yükseltme denenmedi. Bellek engeli bağımsız olarak devam ettiği için API erişimi zorlanmadı. İstemci sürüm numarası tek başına yerel JSON Schema desteğinin uygulamada doğrulandığı anlamına gelmez.

## Durdurulan işler ve bilimsel sınırlar
- Smoke test: **NOT_RUN_MEMORY_GATE**; başarısız LLM cevabı veya başarılı test gibi sunulmaz.
- Dondurulmuş19 senaryo ×3 tekrar = **57 planlı kayıt**; hepsi NOT_RUN_MEMORY_GATE, çıktı ve şema/kaynak değerlendirmesi null. Hiçbiri başarı0 değildir; en iyi çıktı seçilmedi.
- İnsan semantik incelemesi: **NOT_PERFORMED_NO_OUTPUT**. Yerine otomatik/AI anlam onayı konmadı.
- `reported_in_PDF` / `predicted_by_GNN` sözleşmesi değişmedi; LLM çıktısı bulunmadığından açıklama zarfı veya sahte yanıt üretilmedi. Otomatik yayın sayısı0.
- 24 mevcut kaynaklı sözleşme testi ve6 yeni bellek kapısı testi geçti. Bunlar offline Python kontrolleridir; **Ollama JSON Schema API testi veya LLM kalite kanıtı değildir**. Eski loglar ezilmedi.
- Model skoru, SHAP, Δz, MedDRA etiketi, yeni yan etki, PDF/eğitim girdisi veya klinik risk bilgisi üretilmedi. Model eğitimi ve PDF indirme yoktur.

## Çıktılar ve yeniden başlama koşulu
Yeni QA dizini: `reports/qa/WP12/local_llm_pilot_v1/`. `preflight.json` gerçek RAM/VRAM/sürüm/API hatalarını; `model_identity.json` tam model digest ve akış hash kanıtını; `scenario_execution_status.json`57 çalıştırılmayan kaydı; `approved_candidate_record.json` kullanıcı seçimi ve değişmeyen sözleşme/senaryo hash'lerini tutar. Notebook yalnız bu gerçek kayıtları gösterir; LLM çıktısı üretmez.

Önceki3.310 dosya başlangıç hash kaydıyla korundu; ham PDF'ler,44 alıntı ve tüm kabul edilmiş model/QA sonuçları değişmedi. `run_status.md` güncel durumu öne ekler; önceki tam baytlar yeni QA arşivinde ve dosyanın sonunda tutulur. Son kanıt manifesti ve koruma sonucu ayrı dosyadadır.

Devam etmek için kullanıcı RAM kullanan uygulamaları kapattıktan sonra ölçüm yenilenmeli. Bellek yeterliyse erişilebilir yerel Ollama servis sürümü ve API yeteneği doğrulanmalı; model/prompt/config tam hash'leri ilk çıkarımdan önce dondurulmalı. Mevcut tam digest farklı çıkarsa sessiz tag değişimi yapılmamalı. Ardından yalnız onaylanan sınırlı smoke test, geçerse aynı sabit ayarla19×3 senaryo uygulanabilir. Bellek/API engeli çözülmeden yeniden deneme yapılmadı. Bu tur burada durur.
