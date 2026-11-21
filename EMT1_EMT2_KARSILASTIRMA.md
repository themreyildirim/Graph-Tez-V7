# EMT1 → EMT2 — Doğrulanmış Karşılaştırma Notları

> 14.11.2026. Bu belge, EMT2 raporunun (Aşama D) kaynak notudur. Buradaki
> her sayı ya EMT1 belgelerinden ya da `reports/` altındaki doğrulanmış
> EMT2 çıktılarından alınmıştır; hiçbiri tahmin değildir.

---

## 1. Hangi EMT1 belgesi?

Yerel belge arsivinde (`<TEZ_DOSYALAR>`) **birden fazla**
EMT1 belgesi var. Karıştırılmaları raporda ciddi hataya yol açar:

| Belge | Sayfa | Tarih | İçerik |
|---|---|---|---|
| `İSTANBUL TEKNİK ÜNİVERSİTESİ - EMT1 - ARA RAPOR - SO (1).pdf` | 40 | Kapakta **Nisan 2025** | **Ara rapor.** Sistem analizi, literatür, tasarım planı |
| `EMT1_FİNAL_RAPOR_SON.pdf` | 41 | Kapakta **Haziran 2026** | **EMT1 final raporu.** Veri hazırlığı ve graf kurulumu |
| `EMT1 - ARA RAPOR - 1.pdf` / `- 2.pdf` | — | Nisan 2026 | Ara rapor taslakları |
| `Kod_Aciklama_Raporu.docx` | — | Mayıs 2026 | 12 bölümlük kod anlatımı |
| `Surec_Raporu.docx` | — | Mayıs 2026 | Kişisel süreç günlüğü (V1→V6) |

Paylaşılan üç dosya `legacy/` kopyalarıyla **bayt bayt aynıdır** (SHA-256
doğrulandı), dolayısıyla proje içinden okunabilir.

**Dikkat:** `EMT2_Teslim_v1/EMT1_TO_EMT2_CHANGELOG.csv` ve
`EMT2_Akademik_v2/EMT1_EMT2_KARSILASTIRMALI_DEGISIKLIK_RAPORU` **final
rapora** (41 sayfa) göre yazılmıştır; sayfa göndermeleri (s.17–18, s.31–32
vb.) o belgenin sayfalarıdır. Ara raporun sayfa numaraları farklıdır.

---

## 2. En önemli bulgu — EMT1 hiçbir eğitilmiş model sonucu raporlamamıştır

Bu, EMT2 raporunun çerçevesini belirleyen tespittir.

**Ara rapor, ÖZET (s.13):**
> "Bu aşamada kesin performans sonuçları sunulmamaktadır."

Ara raporun tek performans tablosu olan **Çizelge 5.2** literatür
değerleridir ve altında şu dipnot vardır:
> "* İşaretli değerler literatürdeki benzer çalışmalardan alınan referans
> değerlerdir; projenin kendi uygulamasından elde edilen nihai sonuçlar
> değildir."

(ISLRWR ~0,94/~0,90 · GCNMLP ~0,94/~0,89 · RWR ~0,875/~0,851 ·
Random Forest ~0,886/~0,840 · Isı difüzyonu ~0,852/~0,815)

**Final rapor, §5 (s.33):**
> "Model eğitimi ve karar destek arayüzü izleyen uygulama adımlarında ele
> alınacağından, bu bölüm mevcut uygulama çıktısı olarak veri hazırlığı ve
> heterojen graf kurulumuna odaklanmaktadır."

**Final rapor, §6.2 "İzleyen Uygulama Adımları" (s.35)** — hepsi gelecek zaman:
> "Sonraki aşamada GiG modeli PyTorch Geometric üzerinde eğitilecek…
> yüzde 80 / yüzde 20 eğitim-test ayrımı ve pozitif kenar başına iki
> negatif örnekleme kullanılacaktır. Açıklanabilirlik tarafında önce
> Gradient × Input yöntemiyle… ardından SHAP değerleriyle…"

### Peki 0,9004 / 0,8545 nereden geliyor?

Yalnızca iki yerden — **hiçbiri resmî EMT1 raporu değil**:
- `legacy/MASTER_KOD.py` satır 876–877
- `legacy/Surec_Raporu.docx` §7.2 (kişisel süreç günlüğü)

`Surec_Raporu.docx` §7.2 tablosu: 38 eğitim ilacı, 70 protein, 30 kategori,
605 pozitif kenar, 1.210 negatif (2×), train/test 1.452/363, AUROC 0,9004,
AUPR 0,8545, top-5 isabet %84,2, 200 epoch, ~50.000 parametre.

### Rapora yansıması

> EMT2'nin 0,6556 değeri, EMT1'in 0,9004'üne göre bir **düşüş değildir.**
> EMT1 resmî olarak hiçbir model performansı raporlamamıştır; 0,9004 ise
> aşağıda §4'te gösterilen sızıntılı protokolün ürünüdür. Doğru çerçeve
> şudur: **EMT1 tasarımı ve veri hazırlığını teslim etti; EMT2 ilk kez
> ölçüm yaptı ve ölçümü savunulabilir hale getirdi.**
>
> `AGENTS.md` bunu zaten kural olarak koyar: V6 metrikleri
> `historical, unverified` etiketlidir ve V7 karşılaştırma ölçütü sayılmaz.

---

## 3. EMT1'in hedefleri ve EMT2'nin karşılığı

| EMT1 hedefi (final §2.3, s.21) | EMT2'de karşılığı |
|---|---|
| AUROC > 0,85 | Hedef olarak **ulaşılmadı**; ilaç-makro AP 0,6556 (B1). Farklı metrik, farklı protokol — doğrudan kıyaslanamaz |
| AUPR > 0,80 | Aynı; AP ilaç-makro ve gözlenen-kayıt vekili üzerinden |
| Sorgu süresi < 10 dk | **Benchmark olarak ölçülmedi.** Arayüz kayıtlı çıktı gösterir, canlı sorgu çalıştırmaz |
| Sabit tohum, belgelenmiş adımlar | **Karşılandı.** Seed tabanı 20261106; manifest ve hash zinciri |
| Yeni antibiyotikler için tahmin (indüktif) | **Kısmen.** İlaç-ayrık CV var; tek dış ilaç denemesi (Tedizolid) keşifsel |

---

## 4. V6'nın hataları — EMT1'in kendi belgeleriyle kanıtlı

Aşağıdaki maddelerin her biri **EMT1'in kendi kod raporundan** alıntıdır;
EMT2'nin sonradan ürettiği bir suçlama değildir. Bu, raporda savunulabilir
bir "neden yeniden yaptık" gerekçesi kurar.

| # | V6'daki durum | EMT1 kaynağı | EMT2'deki karşılık |
|---|---|---|---|
| 1 | **Çift düzeyi split.** `train_test_split(range(len(all_edges)), test_size=0.2, stratify=...)` — aynı ilaç hem eğitimde hem testte | `Kod_Aciklama` §9.3 | 5 dış × 3 iç **ilaç-ayrık** CV + ayrı stres protokolü |
| 2 | **Tekrarlı negatif.** `while len(neg) < len(pos)*2: randint(...)` — yalnız pozitif kümesine bakar, daha önce seçilmiş çifti dışlamaz | `Kod_Aciklama` §9.3 | Negatif örnekleme **yok**; pozitif / unknown ayrımı korunur |
| 3 | **Split öncesi ölçekleme.** Min-max tüm veri üzerinde hesaplanır | `Kod_Aciklama` §4.3 | Scaler ve PT sözlüğü **yalnız train'de** fit |
| 4 | **`kalite_skoru` model girdisi.** `X_prot = prot_feat[aac + dc + yz + ['kalite_skoru']]` → 51 boyut | `Kod_Aciklama` §8; final §4.4 | Çıkarıldı. Protein 56 sayısal özellik, kimlik türevi alan yok |
| 5 | **Ve en çok etkili özellik çıkıyor:** protein tarafında `kalite_skoru` 4,53 ile birinci | `Kod_Aciklama` §10.2 | — |
| 6 | **EMT1 bunu kendisi fark etmiş:** "Protein tarafında kalite_skoru aşırı baskın — bu bir uyarı, modelin … kısayol kullanıyor olabilir" | `Kod_Aciklama` §12.5 | EMT2 uyarıyı eyleme çevirdi |
| 7 | **PPI `forward`'da yok.** İmza: `forward(self, x_drug, x_prot, x_se, dp_ei, pred_drug_idx, pred_se_idx)` — PPI kenar parametresi hiç yok | `Kod_Aciklama` §9.2 | `RoleMaskedPPI.forward` gerçekten mesaj geçirir: kenar silinince protein L2 farkı **13,16**; mesaj gradyan normu **0,0040**; noPPI'da ikisi de 0 |
| 8 | **Amino asit grupları hatalı.** Hidrofobik `AILMFVP` ve Aromatik `FYW` → **F iki grupta**; C ve G hiçbir grupta | `Kod_Aciklama` §7.1 | Ayrık ve kapsayıcı 5 grup: `AGILMPV`, `FWY`, `CNQST`, `HKR`, `DE` |
| 9 | **Gradient × Input, SHAP diye sunuldu** | `Kod_Aciklama` §10.2; final §6.2 | B1 için **tam interventional lineer SHAP** (additivite hatası 3,55e-15, 40 örnek × 64 koalisyon brute-force); A1P1 için mesaj maskeleme |
| 10 | 56 ilacın 12'sinde ATC tamamen sıfır | `reports/WP00.md` | Kapsama sorunu olarak raporlandı, biyolojik kanıt sayılmadı |
| 11 | 70 dizinin tamamında FASTA başlığı diziye karışmış | `reports/WP00.md` | Dizi ayrıştırma ve 20 standart AA doğrulaması |
| 12 | 605 satırda yalnız 590 benzersiz çift (15 tekrar) | `reports/WP00.md` | 6.416 **benzersiz** pozitif çift |
| 13 | "53 bakteriyel protein" içinde maya ve Plasmodium var | `reports/WP00.md` | Katı taxon denetimi; insan (9606) ve E. coli (511145) ayrı senaryolar |

---

## 5. Ölçek karşılaştırması

| | EMT1 (final §5.2, Çizelge 5.1) | EMT2 (doğrulanmış) |
|---|---|---|
| İlaç | 38 | **62** |
| Protein | 70 ("17 insan + 53 bakteriyel") | **141** accession, 140 benzersiz temiz dizi |
| Yan etki | 30 kategori | **1.061** MedDRA PT (CUI) |
| İlaç–protein kenarı | 153 | **476** rollü ilişki / 457 benzersiz çift |
| PPI kenarı | 70 | **184** (insan, eşik 700, 63 düğüm, 12 izole) |
| İlaç–yan etki | 605 kenar | **6.416** benzersiz pozitif çift |
| İlaç özelliği | 25 (5 fizikokimyasal + 20 ATC) | 5 kimyasal + maske (B1); 234 alan (B2) |
| Protein özelliği | 51 (20 AAC + 25 DC + 5 YZ + **kalite**) | **56**, kimlik türevi alan yok |

EMT1 §5.3 ayrıca ara çıktı ile final graf kapsamının farklı olduğunu
belirtir: `ilac_yan_etki_v5.csv` 865 kenar içerirken final graf 605'tir.

---

## 6. Yöntem karşılaştırması

| Konu | EMT1 | EMT2 |
|---|---|---|
| Ana yöntem | GiG; alternatifler RWR / ISLRWR / PPR | B0 / B1 / B2 + PPI GNN + atom×PPI faktöriyel |
| RWR / ISLRWR / PPR | "İzleyen adımlarda karşılaştırma referansı" (final §5.4) | **Uygulanmadı.** Raporda açık sınır olarak kalmalı |
| Değerlendirme | AUROC / AUPR hedefi | İlaç-makro AP, koşullu grup bootstrap GA, kapsam, NA |
| Etiket semantiği | Pozitif / rastgele negatif | Pozitif / **unknown**; gerçek negatif iddiası yok |
| Açıklanabilirlik | Gradient × Input, sonra SHAP planı | Tam lineer SHAP + mesaj maskeleme (Δz) |
| Arayüz | Metin mock-up (ara rapor §5.4.2) | Çalışan Streamlit prototipi (v5) |
| Belge/LLM katmanı | Yok | PyMuPDF + OpenAI pilotu (5 senaryo, insan denetimi PENDING) |

---

## 7. EMT2'de **yapılmayanlar** — raporda sınır olarak yazılmalı

1. ATC varyantı, Random Forest, kimya MLP, protein-mean MLP —
   `WP08_FINAL_CONCLUSIONS.md`'de `DEFERRED_OUTSIDE_PHASE1`. GNN'lerin
   karşılaştırılacağı doğrusal olmayan referans yok.
2. RWR / ISLRWR / PPR — EMT1'in asıl alternatifleri hiç çalıştırılmadı.
3. Moleküler scaffold split — ROADMAP'te vardı; scaffold yalnız ilaç
   düzeyi stres gruplamasında kullanıldı.
4. WP12 ve WP13 **resmî olarak kapanmadı**; uzman/insan değerlendirmesi PENDING.
5. Tedizolid deneyinde precision@10 / AP / AUROC **NOT_CALCULABLE**.
6. Yerel LLM (Gemma/Qwen) bellek kapısında başarısız; kullanılabilir tek
   çıktı bulut API'sinden.
7. `STRICT_ANALYST_BLINDNESS_COMPROMISED` — tam araştırmacı körlüğü korunmadı.
8. Sorgu süresi hedefi benchmark edilmedi.

---

## 8. Changelog denetimi

`EMT2_Teslim_v1/EMT1_TO_EMT2_CHANGELOG.csv` (15 satır) final rapora göre
tek tek doğrulandı. **Hatalı satır bulunmadı.** Doğrulananlar:

- s.19–22 → AUROC>0,85 / AUPR>0,80 / <10 dk ✓ (final §2.3)
- s.31 → "her pozitif için iki negatif" ✓ (final §6.2)
- s.31 → 25 ilaç / 51 protein özelliği + kalite skoru ✓ (final §4.4)
- s.31–32 → 4.5 ve 4.6 aynı başlık ✓ (final s.31–32)
- s.32–34 → 38 / 70 / 30 ve 153 / 70 / 605 ✓ (final Çizelge 5.1)
- s.25–26, 35–36 → Gradient × Input ve SHAP önerisi ✓ (final §6.2)
- s.27–29 → kaynak listesinde bağımsız UniProt REST ✓ (final §4.2.4)
- s.33–36 → eğitim/açıklama/arayüz gelecek iş ✓ (final §6.2)

**Eklenmesi gereken tek satır:** EMT1'in hiçbir eğitilmiş model metriği
raporlamadığı ve 0,9004/0,8545'in yalnız `MASTER_KOD.py` ile
`Surec_Raporu.docx`'te bulunduğu (§2). Mevcut changelog bunu dolaylı
anlatıyor; raporda açık cümle olmalı.

Mevcut `EMT2_Akademik_v2` metinlerinde 0,9004 **hiç geçmiyor** — doğru
davranış, korunmalı.

---

## 9. EMT1'in biçim kuralları (Aşama D için)

İki rapor da aynı düzeni kullanır:

- **Ön bölümler:** Önsöz · İçindekiler · Kısaltmalar · Semboller ·
  Çizelge listesi · (final: Şekil listesi) · ÖZET · SUMMARY
- ÖZET ve SUMMARY ayrı sayfada, sonunda **Anahtar Kelimeler / Keywords**
- Başlık ortalı, büyük harf; kapakta bölüm, yazarlar, danışman, ay-yıl
- **Altı ana bölüm:** 1 Giriş · 2 Sistem Analizi · 3 Literatür Taraması ·
  4 Metodoloji/Yöntembilim · 5 Uygulama · 6 Sonuç ve Öneriler
- Sonra: Kaynaklar · Özgeçmiş ×2
- Çizelge numaralandırması **bölüm bazlı**: `Çizelge 2.1 :`, `Çizelge 5.2 :`
- Kaynakça `[n]` numaralı; metin içinde `[1]`, `[23]` biçiminde
- Final raporda ayrıca numaralı denklemler (4.1)–(4.8) ve `Şekil 4.1`
- Boş ayırıcı sayfalar ve ön bölümlerde roma rakamı sayfa numarası

`EMT2_Akademik_v2/EMT2_FINAL_REPORT.docx` (35 sayfa) bu düzeni zaten
izliyor ve Ek A/B/C ekliyor.

---

## 10. Aşama D için öneri

1. `EMT2_Akademik_v2` taslağını temel al; `calisma/uret.py` + `metin*.txt`
   düzenini sürdür.
2. §2'deki çerçeveyi açık bir paragraf olarak ekle — jürinin "performans
   neden düştü?" sorusunun cevabı budur.
3. §7'deki sekiz sınırı Sonuç bölümünde eksiksiz koru.
4. Aşama A ve B'de yapılanları (bağımlılık kaydı, tek test komutu, yol
   yapılandırması, arayüz v5) §4 ve §5.12'ye işle; kaynak
   `GUNCEL_DURUM.md` §5b.
5. Her tabloyu `reports/qa/...` altındaki kaynağına bağla.
