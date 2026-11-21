# EMT2 Final Raporu v6 — Sürüm Notu

**Çıktı:** `EMT2_Akademik_v6/EMT2_FINAL_REPORT.docx` · `.pdf`
**Sayfa:** 53 · **Kelime:** 9.680 · **Şekil:** 18 · **Çizelge:** 11
**Şablon:** `docs/EMT_Sablon_v2025_v3.docx` (değiştirilmedi)
**Tarih:** 15.11.2026

> v6, önceki sürümlerin üzerine yama **değildir**. Resmî EMT şablonunun
> kendi stil, sayfa düzeni ve bölüm iskeleti korunarak içerik sıfırdan
> kurulmuştur. `EMT2_Akademik_v3`, `_v4` ve `_v5` klasörleri olduğu gibi
> durmaktadır.

---

## 1. v5'ten farkı

| Konu | v5 | v6 |
|---|---|---|
| Şablon | Kendi stilleri (`Heading 1`…) | **Resmî şablon** (`BASLIK1`–`BASLIK5`, `GOVDE`) |
| Bölüm sayısı | 6 | **8** |
| Numaralandırma | Elle yazılmış | **Word otomatik** (başlık, şekil, çizelge) |
| Şekil/çizelge numarası | Sürekli (Şekil 1, 2, 3…) | **Bölüm bazlı** (Şekil 6.3, Çizelge 4.1, Çizelge A.1) |
| İçindekiler | Sabit metin | **Word alan kodu**; sayfa numaraları dışa aktarımda dolar |
| Kısaltmalar / Semboller | Tek bölüm | **Ayrı iki bölüm** (şablon zorunlu) |
| Sistem analizi | İki alt başlık | **Beş zorunlu alt başlık** |
| Etki değerlendirmesi | Tek paragraf | **Dört zorunlu alt başlık** |
| Ağaç modelleri | Yok | **§5.5 ve §6.7** (yeni deney) |
| Ek A/B/C | Ana metinde | **Teknik arşive** taşındı |

## 2. Yeni bölüm düzeni

```
ÖNSÖZ · İÇİNDEKİLER · KISALTMALAR · SEMBOLLER
ÇİZELGE LİSTESİ · ŞEKİL LİSTESİ · ÖZET · SUMMARY
1. GİRİŞ
2. SİSTEM ANALİZİ          (5 zorunlu alt başlık)
3. KURAMSAL TEMEL VE LİTERATÜR
4. VERİ VE YÖNTEM          (10 alt başlık)
5. KARŞILAŞTIRILAN MİMARİLER
6. DENEYSEL BULGULAR       (10 alt başlık)
7. TARTIŞMA
8. SONUÇ VE ÖNERİLER       (4 zorunlu etki başlığı)
KAYNAKLAR · EKLER · ÖZGEÇMİŞ
```

## 3. Şablon mekaniği — ölçülerek çözüldü

Dört davranış şablon dosyası incelenerek belirlendi ve üretici bunlara
uyacak biçimde yazıldı:

1. **Başlık numaraları otomatiktir.** `BASLIK1`–`BASLIK4` stillerinde
   numaralandırma tanımlıdır; bu nedenle başlık metnine numara
   **yazılmaz**. Ön ve arka bölümlerde numara `numId=0` ile bastırılır.
2. **Şekil/çizelge etiketleri otomatiktir.** `Şekil 6.3 : ` ön eki
   açıklama stilinden gelir; metne yazılırsa iki kez görünür. Bölüm
   numarası, o noktadaki başlık numarasından türetilir.
3. **Açıklama stilleri yalnız I–VI ve EKLER için tanımlıdır.** Bu yüzden
   şekil ve çizelgeler 1–6. bölümlerde ve eklerde yer alır; 7. ve 8.
   bölümlerde görsel kullanılmaz.
4. **Bölüm sonu paragrafı o bölümün özelliklerini taşır.** Roman/Arap
   sayfa numaralandırması bu yolla kurulduğundan, yeni bölüm sonları
   şablondakilerin birebir kopyasıdır; kopyalanırken metinleri
   temizlenir.

Şablonun kendi "çıktı almadan önce siliniz" notları kaldırılmıştır.

## 4. İçindekiler ve listeler

Üçü de Word **alan kodudur**; sayfa numaraları
`calisma/disa_aktar.ps1` çalıştırıldığında Word tarafından doldurulur.

| Liste | Alan kodu |
|---|---|
| İçindekiler | `TOC \o "1-4" \h \z \u` |
| Şekil listesi | `TOC \h \z \t "Sekil_FBE_Sablon_BolumI,1,…"` |
| Çizelge listesi | `TOC \h \z \t "Cizelge_FBE_Sablon_BolumI,1,…"` |

İki ayrı sorun çözüldü: şablonun `BASLIK` stillerinde **anahat düzeyi
tanımlı olmadığı** için başlık paragraflarına `outlineLvl` yazılır; ayrıca
`\t` anahtarı stil ve düzeyi **düz virgülle** ayrılmış tek liste olarak
ister (noktalı virgül değil).

## 5. Doğrulama

`calisma/denetle.py` çalıştırılır ve yedi denetimi kapsar:

| Denetim | Sonuç |
|---|---|
| Zorunlu ön/arka bölümler | ✅ 8 + 3 |
| Zorunlu "Sistem…" başlıkları | ✅ 5 |
| Zorunlu dört etki başlığı | ✅ 4 |
| Çizelge/şekil adlarının nokta ile bitmesi | ✅ 29/29 |
| Metinde anılan her şekil/çizelgenin varlığı | ✅ |
| **Her sayısal değerin kayıtlı QA çıktısında bulunması** | ✅ havuz 9.357 |
| Bilimsel kısıt ifadelerinin korunması | ✅ |
| Şablon örnek metni kalıntısı | ✅ yok |

Bütünlük manifestleri **değişmedi**: 55 kapı testi geçti
(1567 / 1711 / 2487). Bu çalışmada yalnız dosya eklenmiş, hiçbir kilitli
dosya düzenlenmemiştir.

## 6. Korunan bilimsel kısıtlar

- Skorlar **gözlenen kayıt sıralama vekilidir**; klinik risk değildir.
- Kayıt bulunmaması **doğrulanmış negatif değildir**.
- Kimyasal lojistik modelin birincil ölçütteki konumu gizlenmemiştir.
- Ağaç kolunun en yüksek nokta tahminine ulaşmasına karşın ana model
  **yapılmadığı** ve gerekçesi açıkça yazılmıştır.
- Sınıf-makro ortalama kesinliğin betimleyici olduğu ve bağımsız güven
  aralığı üretilmediği belirtilmiştir.

## 7. Tamamlanması gerekenler

| Madde | Durum |
|---|---|
| Özgeçmiş metinleri | ⚠️ Şablon zorunlu kılıyor; yer tutucu konuldu |
| Kapak ad-soyad ve tarih teyidi | ⚠️ v5'teki bilgilerden devralındı |
| Önceki dönem raporunun kaynakçaya eklenmesi | ⚠️ Künye doğrulanmadan eklenmedi |
| Uzman terminoloji değerlendirmesi | ⚠️ Beklemede; raporda kısıt olarak yazılı |

## 8. Üretim

```
EMT2_Akademik_v6/calisma/
  sablon.py        Şablon iskeletini koruyan belge kurucu
  bolum_1_3.py     Giriş, Sistem Analizi, Kuramsal Temel
  bolum_4_5.py     Veri ve Yöntem, Karşılaştırılan Mimariler
  bolum_6.py       Deneysel Bulgular
  bolum_7_8.py     Tartışma, Sonuç, Kaynaklar, Ekler
  uret_v6.py       Ön bölümler + birleştirme
  disa_aktar.ps1   Word ile alan güncelleme ve PDF
  denetle.py       Teslim denetimi
```
