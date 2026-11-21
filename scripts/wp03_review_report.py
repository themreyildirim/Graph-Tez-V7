"""Mevcut kapanış tablolarından Türkçe raporları üretir; ham veri okumaz."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'reports/qa/WP03/final_review'


def main():
    checks = json.loads((QA/'consistency_checks.json').read_text(encoding='utf-8'))
    assert len(checks) == 17 and all(x['passed'] for x in checks)
    test_log = (QA.parent/'final_review_test_results.txt').read_text(encoding='utf-8-sig')
    test_names = re.findall(r'^(test_\w+).*?\.\.\. ok$', test_log, re.M)
    assert len(test_names) == 13 and 'Ran 13 tests' in test_log and test_log.rstrip().endswith('OK')
    test_table = '| Test | Sonuç |\n|---|---|\n' + '\n'.join(f'| `{n}` | GEÇTİ |' for n in test_names)
    full = (QA/'accepted_62.md').read_text(encoding='utf-8')
    new = (QA/'new_36.md').read_text(encoding='utf-8')
    semantics = (QA/'category_semantic_review.md').read_text(encoding='utf-8')

    decision = '''# WP03 — etiket stratejisi karar dosyası

05.11.2026 — **Karar önerisi; nihai kategori seti değiştirilmedi.**

## Ölçüm tanımı ve aynı paydada karşılaştırma

Payda, muhafazakâr J01 kohortunda kesin stereo-CID ve geçerli PT ilişkisi bulunan **62 DrugBank ana ID**. Pozitif anahtarı PT için `(id, meddra_cui)`, kategori için `(id, category)`; tekrarlar tekilleştirildi. Sıklık, pozitif kaydı bulunan **ilaç sayısıdır**. Hasta sayısı, bildirim olay sayısı, yan etki görülme oranı veya klinik risk değildir. PT CUI, burada kullanılan UMLS kimliğidir; sayısal MedDRA koduyla karıştırılmamalı.

| Ölçüm | Kaynak PT CUI | Tarihsel 30 kategori | MASTER kod sözlüğü projeksiyonu — yalnız denetim |
|---|---:|---:|---:|
| Bu kohortta gözlenen sınıf | 1.061 | 30 | 30 |
| En az bir pozitifli ilaç | 62 | 61 | 61 |
| Benzersiz pozitif çift | 6.416 | 1.011 | 977 |
| Sınıf başına pozitif ilaç min–maks | 1–61 | 7–61 | 7–61 |
| Yalnız bir ilaçta görülen sınıf | 406 | 0 | 0 |
| En çok iki ilaçta görülen sınıf | 556 | 0 | 0 |
| Beşten az ilaçta görülen sınıf | 710 | 0 | 0 |
| 31'den fazla ilaçta görülen sınıf | 33 | 16 | 15 |
| En sık / en seyrek destek oranı | 61,00 | 8,71 | 8,71 |
| İlaç başına pozitif min / medyan / maks | 2 / 79,5 / 431 | 0 / 16,5 / 28 | 0 / 16 / 28 |
| Gözlenen sözlükte olası çift | 65.782 | 1.860 | 1.860 |
| Gözlenmeyen, etiketsiz çift | 59.366 | 849 | 883 |

Kaynaklar: [ölçümler](qa/WP03/final_review/label_strategy_metrics.csv), [ilaç başına sayımlar](qa/WP03/final_review/per_drug_positive_counts.csv), [PT sıklıkları](qa/WP03/final_review/class_frequency_PT_CUI.csv), [kategori sıklıkları](qa/WP03/final_review/class_frequency_historical_30.csv). Kod sözlüğü tasarımda 40 terim → 33 kategori içeriyor; bu 62 ilaçta gözlenen sayının 30 olması tasarımın 30 olduğu anlamına gelmiyor. Bu alternatif yeni hedef seti olarak benimsenmedi.

Sulfanilamide (DB00259) iki PT taşırken tarihsel seçilmiş kategorilerde sıfır pozitif taşıyor. Bu, 30 kesin negatif veya ilacın yan etkisiz olduğu anlamına gelmez. 1.061→30 dönüşümü salt eşanlamlı tekilleştirmesi değildir: kavram seçimi, kapsam dışı bırakma ve bazı PT'leri birleştirme içerir. 6.416 ile 1.011 farklı kavram uzaylarının çift sayılarıdır; fark doğrudan kayıp oranı veya klinik bilgi kaybı yüzdesi olarak sunulmaz.

## Grafiklerle ne öğreniyoruz?

![Sınıf destek dağılımı](figures/WP03/final_review/class_support.png)

Sol panel PT sınıf desteğinin uzun seyrek kuyruğunu, sağ panel tarihsel 30 kategorinin her birinin desteğini gösteriyor. PT sınıflarının 406/1.061'i (%38,3) tek ilaçta; 710/1.061'i (%66,9) beşten az ilaçta. Tarihsel kategoride Hırıltı 7, Karaciğer toksisitesi 9, Şişkinlik 10; Mide bulantısı 61, Deri döküntüsü 60 ilaçta. Birleştirme sınıfları daha sık yapabilir; bu sonuç kategori anlamını veya klinik geçerliliğini doğrulamaz. Tez açısından sınıf düzeyinde öğrenilebilirlik ve belirsizlik sınırını görünür kılar.

![İlaç başına pozitif sayıları](figures/WP03/final_review/per_drug_support.png)

PT pozitif sayısı 2–431, kategori sayısı 0–28 arasında. İlaçlar arasındaki etiket yoğunluğu değişiyor; kapsam ve kayıt süreçleri buna katkıda bulunabilir. Buradan nedensel açıklama, raporlama hızı veya biyolojik risk sıralaması çıkarılamaz. Tez açısından çok etiketli değerlendirmede bazı ilaçların çok daha fazla gözlenen pozitif taşıdığını gösterir. Bu sayılar QA'da kalmalı, ilaç özelliklerine eklenmemeli.

## Seçenekler ve karar kapısı

| Strateji | Güçlü taraf | Sorun / gerekli karar | Şimdiki durum |
|---|---|---|---|
| Tarihsel 30'u sabit karşılaştırma olarak koru | V6 ile izlenebilir karşılaştırma, görece yoğun sınıflar | Semantik sorunlar, seçilmemiş PT'lerin kapsam kaybı, 61 pozitifli ilaç | Mevcut tanım korunuyor; klinik doğrulanmış hedef iddiası yok |
| Kaynak PT CUI düzeyi | Kimlik izi ve kavramsal ayrıntı korunur, 62 ilaç | 1.061 sınıfa karşı 62 ilaç; 406 singleton, sınıf bazında güvenilir ölçüm güç | Keşif alternatifi; yeni nihai hedef seti yapılmadı |
| Semantik olarak gözden geçirilmiş kategori eşlemesi | Yanlış neden/yerleşim eklemelerini ve birleşmeleri ele alır | Her kural için PT/CUI kanıtı, kapsam gerekçesi ve kullanıcı onayı gerekir | Önce 30 satırlık inceleme kararı; otomatik merge/drop yok |
| Önceden tanımlanan destek eşiğiyle PT alt kümesi | Çok seyrek hedefleri ayrı raporlama olanağı | Eşik keyfi olmamalı; tüm kohorta bakarak test odaklı sınıf seçimi sızıntı yaratır | Eşik seçilmedi, sınıf elenmedi |

Öneri: Tarihsel 30 karşılaştırmasını koru, kaynak PT ilişkilerini kayıpsız QA/provenans olarak sakla; aşağıdaki semantik bayrakları karara bağlamadan nihai hedef sayısını değiştirme. Destek eşiği, yeniden adlandırma veya birleştirme burada onaylanmış değil.

## Seyreklik, dengesizlik ve gelecekteki değerlendirme

1. Tek ilaçta pozitif bulunan bir PT'nin bağımsız ilaç gruplarında hem eğitim hem değerlendirme pozitifi bulunması sağlanamaz. Sınıf başına sıfır eğitim/değerlendirme desteği açıkça “hesaplanamaz” raporlanmalı; bu bir başarım sıfırı değildir. Eğitim yapılmadan stratifikasyonun sorunu çözdüğü söylenemez.
2. Micro ölçümler sık sınıflarca baskılanabilir; macro ölçümler seyrek sınıflarda kararsızlaşabilir. İleride her sınıfın desteği, değerlendirmeye uygun sınıf sayısı ve belirsizlik birlikte raporlanmalı. Dengeleme/ağırlık hesapları yalnız eğitim ilaçlarından yapılmalı; bu rapordaki 62 ilaç sıklıkları model ayarı değildir.
3. 59.366 ve 849 gözlenmeyen çift **unknown**. Hepsini 0 yapmak, gerçek negatif kabulüne dayalı ölçümleri yanıltır. Positive–unlabeled varsayımları ve değerlendirme protokolü daha sonraki ilgili pakette önceden kararlaştırılmalı; burada negatif oluşturulmadı. Gözlenen kayıt varlığını öngören skor, bireysel klinik risk olarak sunulamaz.
4. Gelecekte drug-disjoint ayrım yapılınca ölçekleyici, veriyle öğrenilen sözlük/özellik seçimi, destek eşiği uygulaması ve sınıf ağırlıkları yalnız train üzerinde öğrenilmeli. Sabit uzman hedef sözlüğü önceden dondurulabilir; test etiketleri karar seçmek için kullanılmamalı. Bu aşamada ayrım veya eğitim yapılmadı.

## Tarihsel 30'un PT/CUI karşılaştırması

Bu inceleme, mevcut kaynak kayıtları ile tarihsel adların karşılaştırılmasıdır. “Daralma/genişleme” notları terminoloji açısından inceleme gerekçeleridir; yeni bir dış ontoloji veya klinik değerlendirmeyle eşdeğerlik doğrulanmadı. PT adları ve CUI listeleri ayrı kümeler olarak sıralanmıştır; çoklu listelerin konumsal sırası bire bir eşleme değildir. Tam terim–CUI izi orijinal projeksiyon dosyasında tutulur.

__SEMANTICS__

Özellikle **Bilinç kaybı** iki ayrı CUI'yi (Syncope / Loss of consciousness), **C.diff ishal** iki ayrı kolit PT'sini birleştiriyor. **Nefrotoksisite** adına Renal impairment'ta bulunmayan toksik neden yüklenebilir. Gerçek tarihsel **Kolit** kategorisinin kaynağı Colitis; “Antibiyotikle ilişkili kolit” adı gerçek dosyaya değil MASTER kod sözlüğüne ait. Bu iki sürümü karıştırmamak gerekir. Genel mantar adları Candida özgüllüğünü kaybediyor. Convulsion/Seizure için de gerçek dosya ile kodun tasarım kapsamı ayrıdır. Birleştirmeden kaynaklanan tekrarlar kategori düzeyinde `(id, category)` anahtarıyla kaldırılmıştır; iki farklı PT'nin aynı kategoriye gitmesi iki ayrı kategori pozitifi sayılmaz.

Karar dosyası, WP03 kapanışına ek öneridir. **30 kategori korunuyor; nihai hedef stratejisi kullanıcı onayı gerektiriyor.**
'''.replace('__SEMANTICS__', semantics)
    (ROOT/'reports/WP03_LABEL_STRATEGY_DECISION.md').write_text(decision, encoding='utf-8')

    report = '''# WP03 son kontrol ve kapanış incelemesi

05.11.2026 — **Kapanış kontrolleri tamamlandı; kullanıcı kapanış onayı bekleniyor. WP04 başlamadı.** Kullanıcı WP03 keşif ve kimlik eşleme yaklaşımını onaylamıştır; bu dosya istenen son kontrolleri ayrı kaydeder. Önceki WP03 raporu ve notebook'u tarihsel sonuç olarak korunmuştur.

## Sonuç ve kapsam

**233 muhafazakâr J01 adayının 167'sinde mevcut doğrulanabilir Compound CID köprüsü, 62'sinde kesin stereo-CID eşleşmesiyle geçerli SIDER PT ilişkisi var.** 62 ilaçta 6.416 benzersiz ilaç–PT CUI çifti bulunuyor. Eski 38'in 26'sı bu muhafazakâr kohortta; **36 yeni DrugBank ana ID** eski 38 dışında. Bunlar kaynak-kimlik düzeyinde kazanımdır; tamamı eğitime hazır veya klinik olarak eşdeğer ürünler demek değildir.

| Kapanış kontrolü | Sonuç |
|---|---|
| test_wp03.py yeniden çalıştırma | 13/13 geçti, hata/atlanan test yok |
| Üç dosya arasında bağımsız tutarlılık | 17/17 kontrol geçti |
| Kesin 62 ve yeni 36 için açıklayıcı tablolar | Aşağıda tam listeler; CSV ve notebook eki de mevcut |
| 30 kategori – PT karşılaştırması | 30 satır incelendi; anlam/karışma bayrakları ayrı karar dosyasında |
| Nihai etiket sayısı | Değişmedi; alternatifler yalnız karar önerisi |
| Sızıntı kontrolü | Mevcut QA kodu incelendi; karma QA tablosunu girdi sayma riski kaydedildi |
| Yerel yol bağımlılığı | Doğrudan/dolaylı bağımlılıklar ve merkezileştirme önerisi belgelendi |
| Önceki çıktılar | WP00–WP02'nin 85 dosyası mevcut testte hash ile doğrulandı |
| Büyük kaynak taraması | XML/PPI tekrar okunmadı; istenen 13 testten biri SIDER kanıt satırlarını akışla doğruladı |
| Kapsam sınırı | Yeni kimya, negatif örnek, eğitim, split veya WP04 yok |

## 1. Yeniden çalıştırılan 13 test

Komut: `python -m unittest discover -s tests -p test_wp03.py -v`. Sonuç **Ran 13 tests in 6.198s — OK**. Tam çıktı: [test kaydı](qa/WP03/final_review_test_results.txt).

__TESTS__

Kimlik testleri flat/stereo ayrımını, SID reddini, dönüşümün gidiş/dönüşünü ve çakışma/eksik kimlik ayrımını doğruladı. Artefakt testleri tekrarsız pozitifleri, Telavancin'in kesin listeye alınmamasını, ham SIDER PT satır izini, eski 590 kategori çifti referansını ve notebook çıktısını kontrol etti. `test_raw_integrity_and_old_outputs`, eski 85 çıktının mevcut hash'lerini ve daha önce kaydedilmiş kaynak metadata değişmezliği bayrağını kontrol eder; bu testin ham kaynağa yeniden tam hash attığı iddia edilmiyor.

## 2. 233 → 167 → 62 zincirinin bağımsız kontrolü

Yeni [kontrol modülü](../scripts/wp03_final_review.py), orijinal WP03 üreticisini çağırmadan küçük QA dosyalarını yeniden grupladı. `drug_mapping.csv` içindeki 237 benzersiz ana ID'den `conservative=True` olan 233 satır seçildi. Ana ID/CUI'ler metin olarak korunarak hesaplandı; boş CID ile sıfır ayrıldı. Kaynaklar `coverage_summary.json`, `drug_mapping.csv`, `drug_pt_positives.csv`; eski üyelik için WP02 `legacy_membership.json` bağımsız referanstır.

| Adım / ayrım | Yeniden sayılan | Doğrulama |
|---|---:|---|
| Muhafazakâr aday | 233 | JSON ve mapping eşit |
| CID boş | 66 | 233 − 167 |
| CID dolu | 167 | 62 + 1 + 104 |
| Kesin stereo-CID + PT | 62 | Eşleşen ID kümesi = pozitif dosyasındaki muhafazakâr ID kümesi |
| Flat-only belirsiz | 1 | Telavancin; etiket aktarılmadı |
| CID var, SIDER stereo eşleşmesi yok | 104 | Etiketsiz; kesin negatif değil |
| Benzersiz muhafazakâr ilaç–PT çifti | 6.416 | Mapping PT sayıları her ilaç için ayrı doğrulandı |
| Tekrarlı `(id, meddra_cui)` anahtarı | 0 | Pozitif dosyasının tamamında kontrol |
| Eski üyelikte korunmuş / eski dışında | 26 / 36 | 26 + 36 = 62, WP02 eski ID listesiyle kontrol |

`drug_pt_positives.csv` geniş kohortta 64 ilaç / 6.616 çift içerir. Muhafazakâr filtre uygulanmadan bu sayıları 62 / 6.416 ile karşılaştırmak hatalı olur. 237 geniş ile 233 muhafazakâr aday farkı dört kombinasyon-only kayıttır; muhafazakâr sayıya eklenmedi.

Ek kontroller: `has_pt` bayrağı ile pozitif ID kümesi bire bir aynı, her ilaçta benzersiz CUI sayısı `pt_count` ile aynı, kimya+PT **41**, protein kimliği+PT **55**, her üç alan **35**. Makine okunur 17 sonuç: [consistency_checks.json](qa/WP03/final_review/consistency_checks.json). Girdi içerik hash'leri: [inputs_manifest.json](qa/WP03/final_review/inputs_manifest.json); bunlar küçük QA girdilerinin provenansıdır, yeni ham dosya taraması değildir.

## 3. Kesin eşleşen 62 ilacın tam tablosu

**Benzersiz PT** = ilaç başına tekil kaynak UMLS PT CUI sayısı. **Mevcut kimya** = WP02'de eski beş fizikokimyasal özellik tablosunda kaydı var; güncel SMILES doğrulaması veya yeni özellik üretimi yapılmadı. **XML protein kimliği** = WP02 XML kayıtlarında en az bir protein kimliği var; dizi temizliği, protein özellikleri ve eğitime hazır hedef doğrulaması anlamına gelmez. “Yok”, mevcut modalitenin eksikliğidir; biyolojik hedef/yan etki yokluğu değildir. **Eski V6 üyeliği**, 38 ana ID referansıyla ölçülür. Kaynak: [accepted_62.csv](qa/WP03/final_review/accepted_62.csv).

__FULL__

62'nin 21'inde mevcut kimya, 7'sinde XML protein kimliği yok. Protein kimliği eksik yedi ilaç: Doxycycline, Linezolid, Methenamine, Telithromycin, Tinidazole, Tobramycin, Vancomycin. Bunların PT ilişkileri korunuyor; mevcut kayıtlar bilinmeyen protein ilişkileriyle doldurulmadı.

## 4. Eski 38 dışında kazanılan 36 ilacın tam tablosu

Karşılaştırma aynı kapsamda **26→62**. Eski 38'deki 12 kayıt muhafazakâr kapsam dışında (bir kombinasyon-only, 11 J01 dışı); dolayısıyla ham 38→62 farkı 24 olsa da yeni ID kazanımı **36**. Bu sayı yeni ilaç keşfi veya onaylanmış eğitim örneği sayısı değildir. Kaynak: [new_36.csv](qa/WP03/final_review/new_36.csv).

__NEW__

| Yeni 36'nın modaliteleri | İlaç |
|---|---:|
| Mevcut kimya + XML protein kimliği + PT | 9 |
| Mevcut kimya + PT; protein kimliği eksik | 6 |
| XML protein kimliği + PT; mevcut kimya eksik | 20 |
| Yalnız PT; mevcut kimya ve protein kimliği eksik | 1 |

Yeni 36'nın 15'inde mevcut kimya, 29'unda protein kimliği var. Eski kesişim tarzında tüm modaliteleri zorunlu tutmak bu kazanımın büyük bölümünü yeniden kaybettirir. Bu bir eksik modalite araştırma gerekçesidir; uygulanmış model kararı değildir. Erythromycin/Azithromycin'de kimya+protein kimliği+PT mevcut. Doxycycline/Linezolid/Vancomycin'de kimya+PT var, XML protein kimliği eksik. Methenamine'de iki giriş modalitesi de eksik. Hiçbiri doğrulanmamış protein ilişkisiyle tamamlanmadı.

## 5–6. Tarihsel kategoriler ve etiket stratejisi

[Ayrıntılı karar raporu](WP03_LABEL_STRATEGY_DECISION.md), 30 kategorinin tamamını PT/CUI ve 62 ilaçtaki destekleriyle karşılaştırır. **Bilinç kaybı** ile **C.diff ishal** birden çok CUI'yi birleştiriyor; **Nefrotoksisite** için Renal impairment'a toksik neden ekleme riski, mantar kategorilerinde kaynak özgüllüğünü genişletme riski var. Gerçek **Kolit** adı ile kod sözlüğündeki **Antibiyotikle ilişkili kolit** ayrıldı. Bunlar terminoloji inceleme bayrakları; klinik eşdeğerlik onayı değildir.

Kaynak PT düzeyinde 1.061 sınıf / 6.416 çift / 62 ilaç; tarihsel 30 kategoride 1.011 çift / 61 ilaç var. PT'lerin 406'sı tek, 710'u beşten az ilaçta görülüyor. Kategori desteği 7–61; ilaç başına kategori pozitif medyanı 16,5 (0–28). Seyreklik ve dengesizlik, sonraki değerlendirmede açık destek raporu gerektiriyor. Sözlükteki 849 etiketsiz kategori çifti gerçek negatif kabul edilmedi. **Kategori sayısı değişmedi; destek eşiği, merge/drop veya nihai yeni hedef seti seçilmedi.**

## 7. Veri sızıntısı incelemesi

Kapsam: aktif `scripts/`, `tests/` ve notebook kaynak hücrelerinin ilgili okuma/yazma yolları incelendi; tarihsel eğitim kodu çalıştırılmadı. [Statik çağrı listesi](qa/WP03/final_review/static_io_call_inventory.csv) yardımcı bir envanterdir; kapsamlı veri akışı kanıtı değildir. Mevcut aktif WP03 çıktıları QA/etiket/provenans amaçlı; eğitim tensörü veya model girdisi üretilmiyor.

**Somut risk:** `wp03_sider.py:88–91` tek mapping tablosuna kimlik, etiket kapsamı ve eski üyelik alanlarını birlikte yazıyor. Gelecekte `select_dtypes(number)` veya tüm sütunları vektöre çevirme yaklaşımı yasak hedef bilgilerini içeri alabilir. Bugün bu tabloyu öğrenen model yok; gelecekte sızıntı olmayacağına dair uçtan uca garanti verilemez.

| Alan / bilgi | İzinli kullanım | Gelecekte ilaç model girdisi olarak durum |
|---|---|---|
| PT CUI, PT adı, kategori, ilaç–yan etki pozitifleri | Hedef/provenans ve QA | İlaç X'ine, etiket embedding özeti olarak bile eklenmemeli |
| `pt_count`, kategori sayısı, ilaç başına pozitif yoğunluğu | QA tablosu/grafik | Yasak: doğrudan hedef türevi |
| `has_pt`, `old_adr`, eski 38 üyeliği | Kohort ve tarihsel karşılaştırma | Yasak: etiket bulunurluğu/seçilim bilgisi |
| Sınıf desteği, kaynak satırı/kanıt tekrarı, raporlama sıklığı, bunlardan skorlar | Provenans ve betimleyici QA | Yasak: hedef/kayıt sürecinden türeme riski; gerçek olay sıklığı da ölçülmedi |
| `kalite_skoru`, hedeflerden türetilmiş güvenilirlik puanı | Hata kaydı / denetim | Yasak |
| DB/CID/SID/STITCH ID ve eşleme durumu | Join, kimlik izleme | Sayısal biyolojik özellik veya kimlik ezberi girdisi yapılmamalı |
| Kimya/protein değerleri ve bu girişlerin bağımsız eksiklik maskeleri | İleride onaylı giriş modaliteleri | Etiket varlığına göre maske üretmeden, kaynak yanlılığı denetlenerek |

Sonraki entegrasyon için öneri: X yalnız açık isimli onaylı kimya/protein/graf alanlarından oluşturulsun; QA tablosundan toplu sütun seçilmesin. Girdi şema testi yasak sütunları ve hedef dosyası bağımlılığını reddetsin. Train/val/test ilaçları ayrılmalı; val/test hedef kenarları eğitim mesaj geçişine girmemeli. Ölçekleyici, sınıf ağırlığı ve veriyle seçilen hedef sözlüğü yalnız train'de öğrenilmeli. B0 etiket önseli gibi gelecekteki baseline hesapları da yalnız train'de kalmalı; ilaç özelliği yapılmamalı. Bu kontrollerin uygulanması WP07/WP08 kapsamındadır; burada model veya split yapılmadı.

## 8. Yerel ham veri yoluna bağımlılık ve öneri

Referans kök `C:\\Users\\emrey\\OneDrive\\Masaüstü\\Tez Dosyalar\\Dataset`. [Yol referansları](qa/WP03/final_review/source_path_references.csv) doğrudan script satırlarını kaydeder; dolaylı kullanım aşağıda ayrıca açıklanır.

| Dosya / kullanım | Bağımlılık | Etki |
|---|---|---|
| `scripts/wp00_audit.py:19,282` | Sabit `DEFAULT_DATA`; mevcut `--dataset-root` override var | Yeniden ham envanter üretiminde kök gerekir |
| `scripts/wp02_drugbank.py:10` | Sabit tam XML yolu | DrugBank akış taramasını yeniden üretmekte gerekir |
| `scripts/wp02_schema_evidence.py:3` | XML sabitini WP02 modülünden alır | Dolaylı aynı yerel yol bağımlılığı |
| `scripts/wp03_sider.py:9` | Sabit tam SIDER yolu | Yeni ham SIDER analizi için gerekir |
| `tests/test_wp03.py:5` ve ham kanıt testi | SIDER sabitini import eder; bir test dosyayı açar | Tam 13 test başka bilgisayarda ham dosya olmadan geçmez |
| `tests/test_wp02.py:5` | Parser yardımcılarını import eder | Sabitin import edilmesi tek başına XML açmaz |
| `scripts/wp00_source_trace.cjs:4` | `traceSider(path, queries)` parametresi | Çağıran doğru ham yolu vermeli |
| `configs/data_paths.example.yaml` | Örnek sabit kök | Şu anda WP02/WP03'ün merkezi çalışan yükleyicisi değil |
| WP01–WP03 tablo/grafik notebook'ları, yeni kapanış araçları | Proje kökünü AGENTS.md ile / script konumuyla bulur; kayıtlı QA okur | Mevcut analizi görüntüleme ve QA üzerinden çalıştırma ham Dataset/Drive erişimi gerektirmez |

WP02/WP03 notebook çıktılarında eski ham yol metni ve bazı bağlantılarda mutlak yerel yol bulunabilir. Bunlar okunabilir provenans kaydıdır; taşınabilir ham veri konfigürasyonu sağlamaz. `read_only: true` örnek YAML bayrağı işletim sistemi düzeyinde yazma engeli değildir.

**İlerisi için öneri, henüz uygulanmadı:** Tek bir yol çözümleyici: açık CLI parametresi → `GRAPH_TEZ_DATA_ROOT` ortam değişkeni → kişisel `configs/data_paths.local.yaml` → belgelenmiş varsayılan. Mevcut `--dataset-root` davranışı korunmalı. Kök altında yalnız allowlist'teki tanımlı göreli yollar kullanılmalı; eksik dosya için tüm dış dizini recursive aramak yerine açık hata verilmeli. XML/SIDER için dosya bazlı override ve Drive kimliği gibi farklı konumlar ayrı tanımlanabilir. Kişisel mutlak yollar git'e eklenmemeli; örnek config paylaşılmalı. Provenansta kaynak rolü, çözülmüş konum ve boyut/mtime tutulmalı. Salt okunur açma, eksik dosya, override önceliği ve kapsam dışı yol reddi ileride test edilmeli. Ham dosya kopyalama/taşıma gerekmiyor. Mevcut çalışan WP00–WP03 kodu bu kapanışta yeniden yazılmadı.

## 9–10. Koruma, çıktılar ve kapanış durumu

Önceki WP00–WP02 raporları, notebook'ları, QA ve görselleri değiştirilmedi; istenen testte 85 dosyanın içerik hash'i eşleşti. Orijinal WP03 raporu/notebook'u ve analiz girdileri de korunarak kapanış ekleri ayrı dosyalara yazıldı. XML/PPI veya kapsam dışı kaynak okunmadı. Tek ham erişim, istenen testin 19,5 MB SIDER dosyasında kanıt satırlarını doğrulamak için yaptığı akış okumadır. Yeni API isteği veya veri indirmesi yok.

| Çıktı | Ne işe yarar? |
|---|---|
| `reports/WP03_FINAL_REVIEW.md` | On kapanış kontrolünün sonuçları; tam 62/36 tabloları |
| `reports/WP03_LABEL_STRATEGY_DECISION.md` | Sıklık, seyreklik, unknown ve 30 kategori için anlam incelemesi; karar seçenekleri |
| `notebooks/WP03_final_review.ipynb` | Orijinal notebook'u değiştirmeyen, altı yürütülmüş kod hücreli kapanış eki; tam tablolar ve iki grafik |
| `reports/qa/WP03/final_review/` | Yeniden hesaplanan tablolar, 17 kontrol ve küçük kaynak girdi hash'leri |
| `reports/qa/WP03/final_review_test_results.txt` | İstenen 13 testin gerçek yeniden çalıştırma kaydı |
| `reports/figures/WP03/final_review/` | Sınıf desteği ve ilaç başına pozitif dağılımının iki PNG'si |
| `scripts/wp03_final_review.py` | Ham kaynak taramadan bağımsız kapsam/etiket istatistiği kontrolü |
| `scripts/wp03_review_notebook.py`, `scripts/wp03_review_report.py` | Yeni kapanış notebook'u ve raporlarını mevcut küçük tablolardan tekrar üretir |
| `run_status.md` | WP03 kapanış kontrolü tamam; kullanıcı onayı bekleniyor kaydı |

Yalnız ekleri yeniden üretme sırası: `python scripts/wp03_final_review.py`, `python scripts/wp03_review_notebook.py`, `python scripts/wp03_review_report.py`. İlk araç küçük QA girdilerini okur, ikincisi bunların tablolarını/grafiklerini çalıştırıp kaydeder; ham analiz üreticilerini veya eski notebook'ları çalıştırmaz. Tam 13 testin tekrarında ham SIDER erişimi gerektiği ayrıca yukarıda belirtilmiştir.

**WP03 kapanış kontrolleri tamamlandı. Nihai kategori sayısı değişmedi. WP04, yeni fizikokimyasal özellik üretimi ve eğitim başlatılmadı. Kullanıcı kapanış onayı bekleniyor.**
'''
    report = report.replace('__TESTS__', test_table).replace('__FULL__', full).replace('__NEW__', new)
    (ROOT/'reports/WP03_FINAL_REVIEW.md').write_text(report, encoding='utf-8')
    print('Wrote WP03 final review and label strategy decision reports')


if __name__ == '__main__':
    main()
