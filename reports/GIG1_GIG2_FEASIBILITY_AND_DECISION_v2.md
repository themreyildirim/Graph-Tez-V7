# Geliştirilmiş Graph-in-Graph — GiG-1 ve GiG-2 Fizibilitesi

> 14.11.2026 · Yalnız çözümleme ve karar. **Hiçbir model eğitilmedi.**
> Önceki rapor: `GIG_VS_A1P1_FEASIBILITY_AND_DECISION.md` (EMT1'in özgün
> tasarımı). Bu rapor farklı bir soruyu ele alır: EMT1'in GiG *fikrini*
> A1P1'in güncel bilgi kaynaklarıyla birleştirmek anlamlı mı?

---

## 1. Doğru soru: A1P1'in geç füzyonu neyi temsil **edemez**?

Yeni katman eklemeden önce mevcut mimarinin matematiksel sınırını
saptamak gerekir. A1P1'in skor fonksiyonu kod düzeyinde şudur:

```
h_p   = g(x_p, PPI komşuları)                    # yalnız dizi türevi
z_d   = [ ⊕_r mean_{p∈N_r(d)} h_p ] ⊕ kimya(d) ⊕ molekül(d) ⊕ maskeler
skor(d,s) = w_s · z_d + b_s                      # tek doğrusal katman
```

`torch.cat` ile birleştirip tek bir `Linear(150, K)` uygulamak şu anlama
gelir:

> **skor(d,s) = w_s^protein · (protein bloğu) + w_s^kimya · (kimya bloğu)
> + w_s^molekül · (molekül bloğu) + sabit**

Yani model, modaliteler üzerinde **toplamsal (additive)** bir fonksiyondur.
Bundan üç somut yetenek eksikliği çıkar:

| # | A1P1'in temsil edemediği | Neden |
|---|---|---|
| **S1** | **Modaliteler arası etkileşim.** "Bu kimyasal iskelet, *şu* protein ailesine bağlandığında riskli" türünden bir *birleşim* kuralı | Birleştirme sonrası doğrusal olmayan katman yok; bloklar yalnız toplanır |
| **S2** | **Göreve uyarlanan protein temsili.** `h_p` tamamen 56 boyutlu dizi özelliğinden türer; hangi ilaçların bağlandığından etkilenmez | İlaç → protein mesajı yok; serbest protein gömmesi de yok |
| **S3** | **Ortak hedef üzerinden kimyasal komşuluk.** İlaç A'nın kimyası, aynı proteini hedefleyen ilaç B'nin temsiline hiç ulaşmaz | Bilgi akışı tek yönlü (protein → ilaç) ve tek adımdır |

**Önemli bir düzeltme:** "Ortak protein" sinyalinin kendisi A1P1'de
**zaten vardır** — aynı proteini hedefleyen iki ilaç aynı `h_p` vektörünü
alır. Eksik olan, o proteinin ilaç bağlamına göre *değişebilmesi* (S2) ve
kimya ile protein bilgisinin *çarpışabilmesi* (S1).

İşte heterojen mesajlaşmanın kazandıracağı gerçek yetenek budur. Katman
sayısını artırmak değil, **toplamsal modeli etkileşimli modele
dönüştürmek.**

---

## 2. Yapısal önkoşul gerçekten var mı? (ölçüldü)

Bir 2-adım (ilaç → protein → ilaç) mesajlaşmasının anlamlı olması için
ilaçların protein paylaşması gerekir. `reports/qa/WP07/typed_drug_protein_edges.csv`
üzerinden ölçüldü (476 kenar, 60 ilaç, 141 protein):

### 2.1 Ortak hedef grafı yoğun

| Ölçüm | Değer |
|---|---|
| En az bir protein paylaşan ilaç çifti | **743 / 1.770** (%42,0) |
| Ortak-hedef derecesi (medyan) | **25** (azami 59) |
| Hiç komşusu olmayan ilaç | **1** |
| Toplam 2-adım yolu | **1.583** |

### 2.2 Her test ilacına ulaşıyor

Dondurulmuş beş dış katta, her test ilacının kaç **eğitim** ilacıyla
protein paylaştığı:

| Kat | Test ilacı | Bağlantısız | Medyan train komşusu | Azami |
|---|---:|---:|---:|---:|
| primary_o01_final | 13 | 0 | 26 | 31 |
| primary_o02_final | 13 | 0 | 22 | 36 |
| primary_o03_final | 12 | 0 | 19 | 31 |
| primary_o04_final | 12 | **1** | 18 | 26 |
| primary_o05_final | 12 | 0 | 23 | 33 |

Beş katın tamamında yalnız **bir** test ilacı yalıtık. Yani yapısal
önkoşul **karşılanıyor** — bu, WP09'daki seyrek PPI grafından (63 düğüm,
184 kenar, 12 izole) belirgin biçimde farklı bir durum.

### 2.3 Ancak sinyal hub'larda yoğunlaşmış — kritik çekince

| Ölçüm | Değer |
|---|---|
| 2-adım yolu **taşımayan** protein | **83 / 141** (%59) |
| En büyük 1 proteinin payı | %12,0 |
| En büyük 5 proteinin payı | **%43,6** |
| En büyük 10 proteinin payı | **%61,7** |

En çok paylaşılan proteinler:

| Accession | İlaç | Rol | Niteliği |
|---|---:|---|---|
| P02768 | 20 | carrier/target | Serum albümin — genel taşıyıcı |
| Q4U2R8 | 20 | target/transporter | Taşıyıcı |
| P08684 | 18 | enzyme | CYP3A4 — genel metabolize edici |
| P46059 | 14 | target/transporter | Taşıyıcı |
| P05177 | 12 | enzyme | CYP1A2 |

**Sonuç:** Yolların çoğu, neredeyse her ilacın bağlandığı spesifik
olmayan ADME proteinlerinden geçiyor. Ortalama tabanlı mesajlaşmada
albümin gibi 20 ilaçlı bir hub, 20 farklı ilacın ortalamasını alır ve
**neredeyse sabit** bir vektör üretir — ayırt ediciliği düşüktür
(oversmoothing). Buna karşılık mekanistik açıdan en bilgilendirici olması
beklenen, tek ilaca özgü 83 protein **hiç 2-adım yolu taşımaz**.

> Yapı var, ama bilgi en çok olduğu yerde en az spesifik.

---

## 3. GiG-1 — Kimya ve protein destekli heterojen graf

### 3.1 Tanım

A1P1 omurgası korunur; tek ekleme **ilaç → protein** mesaj adımıdır:

```
h_d⁽⁰⁾ = W_proj · [kimya(8) ⊕ molekül(8) ⊕ maskeler(5)]        # 21 → 32
h_p⁽¹⁾ = h_p + ReLU( W_dp · mean_{d ∈ N_r(p)} h_d⁽⁰⁾ )         # ilaç bağlamı
h_p⁽²⁾ = PPI mesajlaşması(h_p⁽¹⁾)                              # mevcut katman
z_d    = [ ⊕_r mean_{p∈N_r(d)} h_p⁽²⁾ ] ⊕ kimya ⊕ molekül ⊕ maskeler
```

Korunanlar: 44/14 atom-bağ grafı, beş kimyasal tanımlayıcı, 56 protein
alanı, dört DrugBank rolü, STRING insan PPI ağı, QC/maske/abstention
politikası, dondurulmuş bölmeler.

### 3.2 Hangi yeni yeteneği kazandırır?

- **S2 çözülür:** `h_p⁽¹⁾` artık proteine bağlanan ilaçların kimyasından
  etkilenir. Dizi olarak benzer ama farmakolojik olarak farklı iki
  protein ayrışabilir.
- **S3 çözülür:** İlaç A'nın kimyası, ortak protein üzerinden ilaç B'nin
  temsiline ulaşır.
- **S1 kısmen çözülür:** Protein bloğu artık kimya türevi bilgi taşıdığı
  için, doğrusal başlık altında bile kimya × protein etkileşimi örtük
  olarak temsil edilebilir hale gelir.

### 3.3 İzolasyon ve sızıntı

- Yan etki etiketi encoder'a **girmez** (`side_effect_edges = False`
  korunur).
- Mesajlar yalnız **özellik** taşır (kimya, molekül), etiket taşımaz.
- Önbellek kuralı korunur: `h_p⁽¹⁾` **yalnız eğitim ilaçlarından**
  hesaplanır; test ilacı proteinleri okur ama onlara yazmaz. Böylece
  mevcut `query_readout` izolasyonu (query → train geri mesajı yok)
  bozulmaz.
- Test ilacının kendi kimyası kendi temsiline girer — bu meşrudur ve
  A1P1'de de böyledir.

### 3.4 Maliyet

| Varyant | Ek parametre | Toplam (K=240) | A1P1'e göre |
|---|---:|---:|---:|
| GiG-1a (tipsiz `W_dp`) | 1.728 | 43.480 | **+%4,1** |
| GiG-1b (rol-tipli 4 × `W_dp`) | 4.800 | 46.552 | +%11,5 |

Omurga 5.512 → 7.240 (GiG-1a). Aşırı öğrenme riski artar ama ılımlı;
parametrelerin ağırlığı hâlâ başlıktadır (%83).

---

## 4. GiG-2 — Yan etki düğümlerini içeren tam heterojen graf

### 4.1 Tanım ve zorunlu kısıt

GiG-1'e ek olarak yan etki düğümleri ve **yalnız eğitim kapsamında**
izinli `ilaç → yan etki` kenarları:

```
h_s = ReLU( W_s · mean_{d : (d,s) ∈ E_train} h_d )
skor(d,s) = f(h_d, h_s)
```

### 4.2 Belirleyici bulgu: çıkarımda prototip başlığına indirgenir

Görülmemiş bir test ilacının **hiç** yan etki kenarı yoktur — olmamalıdır
da. Dolayısıyla test ilacı yan etki mesajlaşmasına **katılamaz**; yalnızca
`h_s`'yi *okur*.

`h_s` ise eğitim ilaçlarının temsillerinin ortalamasıdır. Yani:

> **GiG-2, çıkarım anında bir sınıf-prototipi başlığına indirgenir:**
> `skor(d,s) = ⟨h_d, (s etiketli eğitim ilaçlarının ortalama temsili)⟩`

Bu meşru ve iyi bilinen bir yöntemdir (nearest-class-mean). Ancak:

- **Test ilacına, GiG-1'in sağladığının ötesinde hiçbir yeni bilgi yolu
  açmaz.** Graf mekanizmasının tamamı, bir başlık değişikliğine denktir.
- Dolayısıyla "tam heterojen graf" çerçevesi, önem verdiğimiz ilaçlar
  (yeni ilaçlar) için **yanıltıcıdır**.

### 4.3 Eğitim sırasında kendi kendine sızıntı

Eğitimde `d` ilacının `s` etiketi tahmin edilirken, `h_s` ortalamasına
`d`'nin kendisi de katılıyorsa model **kendi cevabını görür**. Bu,
eğitim/doğrulama karşılaştırmasını bozar ve sessizce iyimser sonuç verir.

Çözüm gerekir: her örnek için **birini-dışarıda-bırak kenar maskelemesi**
(`h_s^{-d}`). Bu uygulanabilir ama:
- her (ilaç, PT) çifti için ayrı ortalama gerektirir,
- maskeleme hatası sessiz kalır — mevcut `side_effect_edges = False`
  gibi tek satırlık bir güvence ile denetlenemez,
- doğrulaması için ek bir mutasyon testi altyapısı gerekir.

### 4.4 Maliyet

| | Parametre (K=240) |
|---|---:|
| GiG-2 prototip başlığı | ~15.176 (**K'dan bağımsız**) |
| A1P1 | 41.752 |
| Fark | **%64 daha az** |

Parametre açısından çekicidir — ancak bu kazanç graf yapısından değil,
**başlık değişikliğinden** gelir ve önceki raporda `GiG-Head` olarak
zaten ayrı bir öneri hâlindedir.

---

## 5. Karşılaştırma

| Kriter | A1P1 (mevcut) | GiG-1 | GiG-2 |
|---|---|---|---|
| Bilgi akışı | protein → ilaç, tek adım | ilaç ↔ protein, iki adım | + yan etki prototipi |
| S1 modaliteler arası etkileşim | yok | **kısmen çözer** | kısmen çözer |
| S2 bağlama uyarlanan protein | yok | **çözer** | çözer |
| S3 ortak hedef üzerinden kimya | yok | **çözer** | çözer |
| Test ilacına yeni bilgi yolu | — | **evet** | **hayır** (GiG-1'in ötesinde) |
| Yapısal önkoşul | — | **var** (medyan 18–26 train komşusu) | var ama çıkarımda kullanılamaz |
| Sinyal niteliği | — | hub'larda yoğun (top-10 = %61,7) | aynı + sınıf prototipi |
| Etiket sızıntısı riski | yok | **yok** (yalnız özellik taşır) | **eğitimde var** → LOO maskeleme şart |
| Denetlenebilirlik | `side_effect_edges=False` | aynı güvence korunur | tek satırlık güvence **yetmez** |
| İndüktif tahmin | kanıtlı | önbellek kuralıyla korunur | prototip okunabilir, katılım yok |
| Ek parametre | — | +1.728 (%4,1) | başlık değişimi: −%64 |
| Hesaplama maliyeti | 152 fit | +38 fit/kol | +38 fit/kol + LOO yükü |
| Açıklanabilirlik | WP11 Δz uygulanabilir | **Δz uygulanabilir** (yeni kenar tipi eklenir) | prototip başlığı Δz'yi karmaşıklaştırır |
| Gerçekten yeni öğrenme | — | **evet, tanımlı** | **hayır** (başlık etkisi) |

---

## 6. Karar

### GiG-1 → **IMPLEMENT_CONDITIONALLY**

**Gerekçe:**
- Mevcut mimarinin **kanıtlanmış** bir temsil sınırını (S1–S3) hedefler;
  katman eklemek için eklenmiş değildir.
- Yapısal önkoşul ölçülmüştür ve karşılanmaktadır: her dış katta test
  ilaçlarının medyan 18–26 eğitim komşusu vardır, beş katta toplam yalnız
  bir yalıtık ilaç vardır.
- Sızıntı riski yoktur; mevcut `side_effect_edges = False` güvencesi ve
  önbellek izolasyonu olduğu gibi korunur.
- Parametre artışı %4,1'dir — küçük kohort için kabul edilebilir.

**Beklenti düşük tutulmalıdır.** Üç bağımsız gösterge aynı yöne işaret
eder: gerçek PPI mesajlaşması katkı vermedi (`−0,000142`), atom dalının
katkısı çok küçüktü (`+0,002894`, stres alt sınırı `+0,000006`) ve 234
alanlı protein özeti B2, altı alanlı B1'in altında kaldı
(`0,6262 < 0,6556`). Üstelik 2-adım yollarının %61,7'si on hub proteinden
geçer ve proteinlerin %59'u hiç yol taşımaz. Gerçekçi beklenti: **küçük
bir iyileşme veya bilgilendirici bir sıfır sonuç.**

### GiG-2 → **NOT_RECOMMENDED** (graf olarak)

**Gerekçe:**
- Görülmemiş ilaç için **GiG-1'in ötesinde hiçbir yeni bilgi yolu
  açmaz**; çıkarımda sınıf-prototipi başlığına indirgenir (§4.2).
- Eğitimde kendi kendine sızıntı riski taşır ve bunu önlemek için
  birini-dışarıda-bırak kenar maskelemesi gerekir; bu, projenin tek
  satırlık denetlenebilir güvence disiplinini zayıflatır (§4.3).
- Parametre kazancı graf yapısından değil başlıktan gelir; o fikir zaten
  `GiG-Head` olarak ayrı ve daha yalın biçimde önerilmiştir.

> **Not:** Yan etki düğümü fikri değersiz değildir — yanlış katmanda
> konumlandırılmıştır. Değeri başlıktadır, mesajlaşmada değil.

---

## 7. Önerilen deney protokolü (onay sonrası kilitlenecek)

### 7.1 Kollar

| Kol | Tanım | Durum |
|---|---|---|
| A1P1 | Mevcut dondurulmuş OOF skorları | **yeniden eğitilmez** |
| B1 | Mevcut kimyasal referans | **yeniden eğitilmez** |
| B0 | Sıklık referansı | **yeniden eğitilmez** |
| **GiG-1a** | A1P1 + tipsiz ilaç→protein mesajı | **yeni, 38 bağlam** |

Tek yeni kol. Rol-tipli GiG-1b, yalnız GiG-1a kabul kriterini geçerse
ayrıca değerlendirilir.

### 7.2 Sabit tutulacaklar

Dondurulmuş 62 ilaçlık kohort · ortak 54 karşılaştırma · 5 dış / 3 iç
ilaç-ayrık bölme · train-only hedef sözlüğü (≥5 pozitif, ≥2 grup) ·
train-only ölçekleyici · `BCEWithLogitsLoss` gözlenen-kayıt vekili ·
AdamW lr 1e-3 wd 1e-3 · max 200 epoch, patience 20 · seed 20261106
formülü · PPI eşiği 700 katı insan · QC54/8 atom maskesi.

### 7.3 Doğrulama kapıları (gerçek eğitimden **önce**)

1. **Sentetik graf:** ilaç→protein mesajının analitik doğrulaması
   (elle hesaplanmış küçük örnek), gradyan akışı.
2. **İzolasyon:** `h_p⁽¹⁾`'in yalnız eğitim ilaçlarından hesaplandığı;
   test ilacının protein önbelleğine yazmadığı.
3. **Sızıntı:** `side_effect_edges = False` yeni kolda da doğrulanır.
4. **Mutasyon:** test etiketleri değiştirildiğinde eğitim ağırlıkları
   değişmemeli.
5. **Dejenerasyon kontrolü:** hub proteinlerde mesaj varyansı ölçülür;
   `mean` neredeyse sabit vektör üretiyorsa bu **sonuçla birlikte
   raporlanır** (oversmoothing kanıtı).

### 7.4 Kabul kriteri (sonuçlardan önce kilitlenir)

- **Birincil:** ortak 54 ilaç, drug-macro observed-record AP.
- **Kabul:** `GiG-1a − A1P1` farkının koşullu %95 grup bootstrap GA'sı
  **tamamen sıfırın üzerinde** **ve** stres protokolünde nokta tahmini
  negatif olmamalı.
- Sağlanmazsa: **"ek katkı gösterilemedi"**; A1P1 ana araştırma mimarisi
  olarak korunur.
- B1 (0,6556) her durumda raporlanır. **Daha iyi sonuç çıksa bile GiG-1
  otomatik olarak ana model ilan edilmez**; §7.5'teki ölçütlerle
  değerlendirilip kullanıcıya önerilir.

### 7.5 Ana model önerisi için birlikte değerlendirilecekler

Ortak kapsamda AP farkı · farkın belirsizliği · stres dayanıklılığı ·
indüktif kabiliyet · sızıntı yokluğu · model karmaşıklığı · hesaplama
maliyeti · açıklanabilirlik (WP11 Δz uygulanabilirliği) ·
tekrarlanabilirlik · B1 referansına göre konum.

### 7.6 Dokunulmayacaklar

`models/`, `reports/qa/WP08–WP11`, dondurulmuş OOF skorları, mevcut
manifestler, A1P1/B0/B1/B2 ağırlıkları. Yeni çıktılar `WP14/` ad
alanına yazılır; kod ayrı sürümde (`scripts/wp14_gig1_*.py`).

---

## 8. Diyagramlar

| Dosya | İçerik |
|---|---|
| `reports/figures/WP14/01_mimari_karsilastirma.png` | EMT1 GiG ↔ A1P1 |
| `reports/figures/WP14/02_veri_akisi.png` | Veri akışı ve sızıntı sınırı |

GiG-1'in mesaj akışı, onay sonrası `03_gig1_mesaj_akisi` olarak eklenecektir.

---

## 9. Durma noktası

Bu rapor **karar aşamasında durur.** Eğitim, kullanıcı onayı ve §7'deki
protokolün hash ile kilitlenmesinden sonra başlatılacaktır.
