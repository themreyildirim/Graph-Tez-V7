# WP00 kaynak ve tarihsel kanıt karşılaştırması

05.11.2026. Durum: **yerel inceleme ve Drive karşılaştırması tamamlandı**. [Drive klasörünün](https://drive.google.com/drive/folders/1P7BHnV5CWtx38ToYVJnYqbD8gf0lEW4m) 69 doğrudan girdisi listelendi; yalnız allowlist CSV'leri ve DATASET_SUMMARY metni okundu. Dışlanan girdiler yalnız ad olarak kaydedildi. Ham CSV'ler yerel diske kaydedilmedi; raporlarda türetilmiş istatistikler ve üç örnek tutuldu.

## Kanıt katmanları

1. **Gerçek yerel veri:** XML ilk üç üst düzey drug; SIDER ve dört STRING dosyasının ilk 1000 kaydı. Ek kaynak izi kontrolünde yerel SIDER 309849 satır akış halinde tarandı; eski 865 pozitif kaydın tamamı bulundu. Ölçümler `profiles.json` ve `source_trace.json` içindedir.
2. **Statik kod kanıtı:** `legacy/MASTER_KOD.py` okunmuştur; çalıştırılmamıştır. Kaynak okuma, özellik oluşturma ve `forward` akışı incelenmiştir.
3. **Tarihsel anlatı:** Word/PDF/Markdown belgeleri ve notebook kaynak hücreleri metin olarak incelenmiştir. Belgedeki sayı bir veri ölçümü sayılmaz. Notebook çıktıları çalıştırılmamış; gömülü görsellerin doğruluğu denetlenmemiştir.
4. **Gerçek Drive verisi:** Yedi CSV'nin tüm satır sayımları, tekrarları, boşlukları ve kesişimleri `drive_profiles.json` / `drive_findings.json` içinde. Yanıtların UTF-8 bayt uzunlukları metadata boyutuyla eşleşti; boyut ve modified_time okuma öncesi/sonrası aynı kaldı. Tam hash kontrolü yapılmadı.

## Mevcut kaynak ile kodun karşılaştırılması

| Kaynak | Yerel gözlem | Eski kod / belge | Sonuç |
|---|---|---|---|
| DrugBank | Kök 5.1, dışa aktarma 2026-01-04, 1.898.100.846 bayt | XML ilaç, ATC ve hedef alanları için okunuyor | Dosya erişilebilir; tam J01 taraması yapılmadı |
| Protein dizi alanı | 10/10 örnek polipeptitte `amino-acid-sequence`; FASTA satır sınırı mevcut | MASTER_KOD.py:452 `pp.find(tag('sequence'))` | Gerçek şema ile kod uyuşmuyor. Mevcut XML üzerinde bu arama örneklerde dizi bulamaz; tüm eski CSV'lerin hangi kod revizyonundan üretildiği henüz bilinmiyor |
| SIDER | Başlıksız 6 sütun, ilk 1000 kayıtta 527 PT, 469 LLT, 4 boş tür | Bölüm 3, PT filtresi | Şema örnekte uyumlu; sürüm 4.1 yalnız tarihsel belge beyanı |
| DrugBank–CID köprüsü | Drive'da boşluklu `drug links.csv`, 19842×23 | Kod aynı adı okuyor; süreç raporu `drug_links.csv` diyor | 11120 Compound ID boş; feature tablosundaki 56 CID köprüyle uyumlu |
| STRING | İki organizma için links + aliases yerelde; iki işlenmiş PPI Drive'da mevcut | Bölüm 8 işlenmiş CSV okuyor | İşlenmiş PPI yalnız metadata: insan 437072545, bakteri 16012129 bayt. Topolojik kapsam ölçülmedi |
| PubChem | XML örneklerinde Substance var; kimyasal CSV'de beş özellik 56/56 dolu | Bölüm 4 PUG REST ile beş özellik istiyor | SID/CID karışmamalı. Yeni API isteği yapılmadı; eski sayısal kimya değerlerinin kimyasal doğruluğu ayrıca doğrulanmadı |
| UniProt | Hedef polipeptit kimliği ve UniProtKB alanı XML'de mevcut | Kod XML okuyor; süreç raporu API'ye geçildi diyor | Bağımsız UniProt API kullanımına MASTER_KOD tanıklık etmiyor; UniProt Dataset klasörüne girilmedi |

## Belge çelişkileri ve yöntem hataları

| İddia / sorun | Yerel belge veya kod kanıtı | WP00 değerlendirmesi |
|---|---|---|
| Birçok kaynak tamamlanmış modelin girdisidir | Ara rapor PDF s.25–27, özellikle Çizelge 4.2 açıkça planlanan kaynaklar; bilgi formu daha geniş direnç/klinik hedefler içeriyor | Planlanan kaynaklar fiili veri listesi sayılmaz; kapsam dışı dosyalar okunmadı |
| Yaklaşık 150 antibiyotik | Ara rapor PDF s.27 gelecek zamanlı tasarım hedefi | Gerçek sayım değildir |
| Kalite skoru STRING güvenidir | Mimari Markdown §3.2 böyle anlatıyor; MASTER_KOD.py:540–543 P/Q/O ilk harf kuralı kullanıyor | Keyfi kimlik kodu; `X_prot` içine eklendiği satır 626'da görülüyor. Yeni girdide yasak |
| Gerçek PPI mesaj geçirme / GiG | Görsel raporu Şekil 1 ve mimari anlatı PPI iç ağı iddia ediyor; MASTER_KOD.py:733–765 `forward` PPI almıyor | Kod üç MLP ve ilaç→hedef ortalaması kullanıyor. PPI graf hazırlığında var, bu forward'da yok |
| Bağımsız indüktif test | Mimari Markdown indüktif genellemeyi anlatıyor; MASTER_KOD.py:785 satır indeksleriyle split yapıyor | İlaç ayrık değerlendirme değil; test ilaçlarının eğitimde görülmesi engellenmiyor |
| Train-only ölçekleme | MASTER_KOD.py:269 tüm ilaç özelliklerinde min/max; split daha sonra | Öğrenme/değerlendirme ayrımından önce fit edilmiş ön işleme |
| Tekrarsız negatif havuz | MASTER_KOD.py:776–780 yalnız pozitif kümede olmamayı kontrol ediyor | Aynı unknown çift tekrar seçilebilir. Unknown klinik negatif değildir |
| Early stopping ve tüm rastgelelik sabit | Mimari Markdown §5.2; kod 200 epoch sabit döngü ve yalnız NumPy seed içeriyor | Validation/early stopping ve PyTorch seed bu dosyada yok; test metrikleri her 20 epoch gözleniyor |
| 35 hedef kategori | Özellik Word belgesi 35 hedef istiyor; kod `HEDEF_35_SE` sözlüğü statik AST ile sayıldı | 40 İngilizce anahtar → 33 benzersiz Türkçe değer; gerçek ADR CSV'sinde 30 kategori. Sözlük adı ve klinik kavram kapsamı aynı şey değil |
| Beş AA grubu doğru sınıflandırma | MASTER_KOD.py:500–505: hidrofobik AILMFVP, aromatik FYW | F iki grupta; C/G hiçbir grupta yok. Yeni özellikler üretilmedi |
| FASTA'dan dizi güvenle temizlenmiş | MASTER_KOD.py:455 satır sonlarını siliyor; 516 regex sadece AA harflerini tutuyor | Başlık sözcüklerindeki AA harfleri de kalabilir; birleşik başlık kesin sınır olmadan tahminle ayrıştırılmamalı |
| XML büyüklüğü iterparse'ı kendiliğinden bozuyor | Süreç raporu §4.3/8.2 bu açıklamayı yapıyor | Bu teşhis kanıtlanmış değil. WP00 örneği namespace ve derinliği izleyen iterparse ile başarıyla okundu. Eski satır tabanlı parser nested `drug` ile karışabilir; sentetik regresyon testi eklendi |
| Tüm insan dışı proteinler bakteri | Kod `Organizma != Humans` diye ayırıyor; DATASET_SUMMARY ilk protein örneği Yeast | İnsan dışı ≠ bakteri. Organizma sınıflaması tekrar kurulmalı |
| Güçlü önem/ROC klinik doğrulama gösterir | Görsel raporu Şekil 4–5 güçlü çıkarımlar yapıyor; kod gradient×input kullanıyor | Metrikler tekrar üretilmedi; klinik veya nedensel doğrulama iddiası yok. Bu hesap SHAP değil |
| Kimlik köprüsü bire bir | MASTER_KOD.py:217 CID indeksli `to_dict()` | Aynı CID birden çok DB kaydına bağlıysa son değer diğerlerini ezebilir. Ancak bu gerçek köprüde 8722 dolu CID tekil; bu hata gerçekleşmiş diye raporlanamaz |
| ADR çıktısı 6 sütundur | Gerçek CSV 865×6; kod bölüm 3 iki alan seçip kategori ve DB ID ekliyor | Gerçek dosyada ayrıca `umls_cui` ve `Drug_Name` var. Görünen kod dört sütun üretir; üretim revizyonu bilinmiyor |

## Tarihsel sayıların gerçek Drive dosyalarıyla doğrulanması

Aşağıdaki değerler bugün gerçek CSV'lerden yeniden ölçüldü. DATASET_SUMMARY'nin Drive metnindeki dört ilgili tablo şekli de gerçek dosyalarla uyumlu. Özet belgesindeki XAI tabloları aktif allowlist dışında olduğundan yeniden okunmadı veya doğrulanmadı.

| İddia | Tarihsel değer | Güncel gerçek dosya kontrolü |
|---|---:|---|
| İlaç feature | 56×33 | 56×33, uyumlu |
| ADR ilaç sayısı | 53 | 53, uyumlu |
| Hedef bağlantılı ilaç | 41 | 41, uyumlu |
| V6 kesişim ilaç sayısı | 38 | 38; kimya dahil üçlü kesişim de 38 |
| Protein dizi / feature | 70×4 / 70×54 | 70×4 / 70×54, uyumlu |
| İlaç–protein satırı | 153 | 153 benzersiz ilaç–protein çifti |
| ADR satırı / benzersiz çift | 865 / 844 | 865 / 844; 21 ilişki tekrar fazlası |
| V6 pozitif satır / benzersiz çift | 605 / 590 | 605 / 590; 15 ilişki tekrar fazlası |
| V6 olası / etiketsiz çift | 1140 / 550 | Gerçek 38×30 ve 590 ile 1140 / 550; klinik negatif değil |
| Tümü sıfır ATC satırı | 12/56 | 12/56, uyumlu; biyolojik yokluk değildir |
| Başlık kirlenmesi | 70/70 | 70/70 başlık ve dizi aynı satırda, satır sınırı yok |
| Aday / DBSALT | 209 / 125 | 209 tekil ID; 125 DBSALT, 84 DB |

## Yeni ölçülen ayrıntılar

- Köprü: 19842 satır ve tekil DrugBank ID; 11120 Compound ID boş (%56,04). İlk 1000 satırda yalnız 107 boş (%10,7); başlangıç örneği tüm dosyayı temsil etmez. Dolu 8722 CID tekil ve rakamsal. 56 feature ID/CID eşlemesi tam uyumlu.
- Aday listesinin 125 DBSALT kimliği köprüde doğrudan bulunmuyor; 84 DB kimliği var. Tuz–ana ilaç ilişkisi doğrulanmadan otomatik birleştirme yapılmadı.
- 15 ilaçta kimya + ADR var, hedef tablosunda kayıt yok. Örnekler: Erythromycin, Azithromycin, Doxycycline, Vancomycin, Linezolid. Bu 15 kaydın tamamı doğrulanmış J01 değildir; geri kazanım garantisi yok.
- 56 feature kaydının 31'inde eski J01 bayrağı açık, 13'ünde başka ATC bayrağı açık ama J01 yok, 12'sinde tümü sıfır. Fluconazole kaydında bile J01R açık olduğundan eski bayraklardan güvenilir kohort oluşturulamaz.
- Protein feature ve dizi tablolarında Gene_Name 2/70 (%2,86), kenar tablosunda 2/153 (%1,31) boş. Diğer küçük QC CSV alanlarında boş hücre yok; dolu alanın doğru olması ayrıca sınanmalı.
- Protein organizma metinleri: 17 Humans; ayrıca Yeast 2, Baker's yeast 1 ve Plasmodium falciparum 1 var. Bu yüzden “17 insan + 53 bakteri” anlatımı doğru değil. E. coli (strain K12) 14 ve Escherichia coli 3; diğer türlerde mevcut PPI kapsamı varsayılamaz.
- `kalite_skoru` dağılımı 1:43, 2:24, 3:3; 70/70 satır ID ön ek kuralıyla eşleşiyor. Beş normalize kimya sütununun tamamı 56 ilacın global min/max hesabıyla uyumlu (tolerans 1e-10); leakage tasarım sorunu veride de izleniyor.
- ADR tablosunun 865 ayrı `(CID, PT adı, UMLS)` anahtarının tamamı yerel SIDER'da bulundu. Bu, kategoriye indirgenince 844 ilişkiye düşmesiyle çelişmez; farklı PT/kavramlar aynı Türkçe kategoriye birleşiyor.
- Drive ve yereldeki altı büyük ham kaynağın metadata boyutları eşit. Bu içerik/hash eşitliği veya XML revizyonunun aynı olduğunu kanıtlamaz; büyük uzak kopyalar okunmadı.

## Belge inceleme kapsamı

Zorunlu altı belge ve `COHORT_EXPANSION.md` tamamen okundu. `legacy/` içindeki Python, notebook kaynak hücreleri, iki PDF, dört DOCX ve Markdown belgeleri metin çıkarımıyla incelendi. PDF ara raporun 40, bilgi formunun 4 sayfasından metin çıkarıldı. Notebook 88 hücre içeriyor; `torch.randn` ile örnek üreten eğitim gösterimleri final V6 verisi olarak kullanılmadı. `Tez Öneri.md` genel graf ders notları ve gömülü görseller içeriyor; aktif plan değildir. Word/PDF gömülü görselleri veya sayfa yerleşimi için görsel doğrulama yapılmadı; sayısal kanıt bu görsellere dayandırılmadı. PDF okuyucu iki nesne ofseti uyarısı verdi, sayfa metni çıkarımı tamamlandı. Manifest: `legacy_review_manifest.json`.

## Talimat farklarının çözümü

- Başlangıç prompt'u STRING için yalnız metadata istiyordu; kullanıcının güncel WP00 isteği sınırlı örneklemeyi açıkça istediği için yalnız iki izinli organizma örneklendi.
- Başlangıç prompt'u Drive bağımlılığı istemiyordu; kullanıcı daha sonra doğrudan Drive erişimini açıkça istedi. Bağlantı kuruldu ve okumalar başarıyla yapıldı; uzak yazma işlemi yapılmadı. OAuth token kapsamının teknik olarak yalnız okuma olduğu iddia edilmiyor.
- Eski ve yeni çıktı adları birlikte desteklendi: `source_inventory.csv` ve `data_inventory.csv` aynı içerik; eski sözlük adı güncel sözlüğe yönlendiriyor.
- Aktif plan değiştirilmedi; bu rapordaki şema uyuşmazlıkları sonraki kullanıcı onaylı pakette çözülmek üzere işaretlendi.
