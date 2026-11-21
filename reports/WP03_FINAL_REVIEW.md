# WP03 son kontrol ve kapanış incelemesi

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

| Test | Sonuç |
|---|---|
| `test_every_evidence_line_matches_the_raw_pt_record` | GEÇTİ |
| `test_notebook_executed_and_labels_remain_audits` | GEÇTİ |
| `test_old_reference_reproduced_from_raw` | GEÇTİ |
| `test_partition_and_coverage` | GEÇTİ |
| `test_raw_integrity_and_old_outputs` | GEÇTİ |
| `test_telavancin_not_in_exact_positives` | GEÇTİ |
| `test_unique_valid_positive_keys_and_trace` | GEÇTİ |
| `test_exact_and_flat_only_not_equivalent` | GEÇTİ |
| `test_flat_and_stereo_have_distinct_semantics` | GEÇTİ |
| `test_roundtrip_and_large_modern_cid` | GEÇTİ |
| `test_shared_cid_xml_conflict_and_missing_cid` | GEÇTİ |
| `test_sid_not_accepted_as_a_stitch_token` | GEÇTİ |
| `test_wrong_type_and_invalid_format_rejected` | GEÇTİ |

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

| DrugBank ID | İlaç | Benzersiz PT | Mevcut kimya | XML protein kimliği | Eski V6 38 üyeliği |
|---|---|---|---|---|---|
| DB00479 | Amikacin | 27 | Yok | Var | Yok |
| DB01060 | Amoxicillin | 79 | Var | Var | Var |
| DB00415 | Ampicillin | 27 | Var | Var | Var |
| DB00207 | Azithromycin | 177 | Var | Var | Yok |
| DB01053 | Benzylpenicillin | 135 | Var | Var | Var |
| DB00578 | Carbenicillin | 26 | Var | Var | Var |
| DB01327 | Cefazolin | 84 | Yok | Var | Yok |
| DB00535 | Cefdinir | 100 | Yok | Var | Yok |
| DB01413 | Cefepime | 91 | Yok | Var | Yok |
| DB00671 | Cefixime | 49 | Yok | Var | Yok |
| DB00493 | Cefotaxime | 58 | Yok | Var | Yok |
| DB01331 | Cefoxitin | 62 | Yok | Var | Yok |
| DB01416 | Cefpodoxime | 174 | Yok | Var | Yok |
| DB01150 | Cefprozil | 59 | Yok | Var | Yok |
| DB06590 | Ceftaroline fosamil | 44 | Yok | Var | Yok |
| DB00438 | Ceftazidime | 79 | Yok | Var | Yok |
| DB01332 | Ceftizoxime | 42 | Yok | Var | Yok |
| DB01212 | Ceftriaxone | 105 | Yok | Var | Yok |
| DB01112 | Cefuroxime | 112 | Yok | Var | Yok |
| DB00567 | Cephalexin | 76 | Yok | Var | Yok |
| DB00446 | Chloramphenicol | 52 | Var | Var | Yok |
| DB00827 | Cinoxacin | 27 | Var | Var | Var |
| DB00537 | Ciprofloxacin | 431 | Var | Var | Var |
| DB01211 | Clarithromycin | 203 | Var | Var | Yok |
| DB00485 | Dicloxacillin | 75 | Var | Var | Var |
| DB06211 | Doripenem | 33 | Var | Var | Var |
| DB00254 | Doxycycline | 150 | Var | Yok | Yok |
| DB00303 | Ertapenem | 282 | Var | Var | Var |
| DB00199 | Erythromycin | 56 | Var | Var | Yok |
| DB00301 | Flucloxacillin | 61 | Var | Var | Var |
| DB02703 | Fusidic acid | 44 | Yok | Var | Yok |
| DB01044 | Gatifloxacin | 174 | Var | Var | Var |
| DB01155 | Gemifloxacin | 148 | Var | Var | Var |
| DB00798 | Gentamicin | 74 | Yok | Var | Yok |
| DB01172 | Kanamycin | 24 | Var | Var | Yok |
| DB01137 | Levofloxacin | 338 | Var | Var | Var |
| DB00601 | Linezolid | 115 | Var | Yok | Yok |
| DB00978 | Lomefloxacin | 186 | Var | Var | Var |
| DB06799 | Methenamine | 11 | Yok | Yok | Yok |
| DB00916 | Metronidazole | 205 | Var | Var | Var |
| DB00607 | Nafcillin | 57 | Var | Var | Var |
| DB00779 | Nalidixic acid | 47 | Yok | Var | Yok |
| DB00698 | Nitrofurantoin | 85 | Var | Var | Var |
| DB01059 | Norfloxacin | 149 | Var | Var | Var |
| DB01165 | Ofloxacin | 233 | Var | Var | Var |
| DB04911 | Oritavancin | 46 | Yok | Var | Yok |
| DB00713 | Oxacillin | 47 | Yok | Var | Yok |
| DB00595 | Oxytetracycline | 28 | Var | Var | Yok |
| DB00417 | Phenoxymethylpenicillin | 19 | Var | Var | Var |
| DB00319 | Piperacillin | 102 | Var | Var | Var |
| DB01208 | Sparfloxacin | 216 | Var | Var | Var |
| DB00919 | Spectinomycin | 12 | Var | Var | Yok |
| DB00359 | Sulfadiazine | 67 | Var | Var | Var |
| DB01015 | Sulfamethoxazole | 81 | Var | Var | Var |
| DB00259 | Sulfanilamide | 2 | Var | Var | Yok |
| DB00976 | Telithromycin | 143 | Var | Yok | Yok |
| DB00560 | Tigecycline | 173 | Var | Var | Yok |
| DB00911 | Tinidazole | 86 | Var | Yok | Yok |
| DB00684 | Tobramycin | 158 | Var | Yok | Yok |
| DB00440 | Trimethoprim | 94 | Var | Var | Var |
| DB00685 | Trovafloxacin | 196 | Var | Var | Var |
| DB00512 | Vancomycin | 80 | Var | Yok | Yok |

62'nin 21'inde mevcut kimya, 7'sinde XML protein kimliği yok. Protein kimliği eksik yedi ilaç: Doxycycline, Linezolid, Methenamine, Telithromycin, Tinidazole, Tobramycin, Vancomycin. Bunların PT ilişkileri korunuyor; mevcut kayıtlar bilinmeyen protein ilişkileriyle doldurulmadı.

## 4. Eski 38 dışında kazanılan 36 ilacın tam tablosu

Karşılaştırma aynı kapsamda **26→62**. Eski 38'deki 12 kayıt muhafazakâr kapsam dışında (bir kombinasyon-only, 11 J01 dışı); dolayısıyla ham 38→62 farkı 24 olsa da yeni ID kazanımı **36**. Bu sayı yeni ilaç keşfi veya onaylanmış eğitim örneği sayısı değildir. Kaynak: [new_36.csv](qa/WP03/final_review/new_36.csv).

| DrugBank ID | İlaç | Benzersiz PT | Mevcut kimya | XML protein kimliği | Eski V6 38 üyeliği |
|---|---|---|---|---|---|
| DB00479 | Amikacin | 27 | Yok | Var | Yok |
| DB00207 | Azithromycin | 177 | Var | Var | Yok |
| DB01327 | Cefazolin | 84 | Yok | Var | Yok |
| DB00535 | Cefdinir | 100 | Yok | Var | Yok |
| DB01413 | Cefepime | 91 | Yok | Var | Yok |
| DB00671 | Cefixime | 49 | Yok | Var | Yok |
| DB00493 | Cefotaxime | 58 | Yok | Var | Yok |
| DB01331 | Cefoxitin | 62 | Yok | Var | Yok |
| DB01416 | Cefpodoxime | 174 | Yok | Var | Yok |
| DB01150 | Cefprozil | 59 | Yok | Var | Yok |
| DB06590 | Ceftaroline fosamil | 44 | Yok | Var | Yok |
| DB00438 | Ceftazidime | 79 | Yok | Var | Yok |
| DB01332 | Ceftizoxime | 42 | Yok | Var | Yok |
| DB01212 | Ceftriaxone | 105 | Yok | Var | Yok |
| DB01112 | Cefuroxime | 112 | Yok | Var | Yok |
| DB00567 | Cephalexin | 76 | Yok | Var | Yok |
| DB00446 | Chloramphenicol | 52 | Var | Var | Yok |
| DB01211 | Clarithromycin | 203 | Var | Var | Yok |
| DB00254 | Doxycycline | 150 | Var | Yok | Yok |
| DB00199 | Erythromycin | 56 | Var | Var | Yok |
| DB02703 | Fusidic acid | 44 | Yok | Var | Yok |
| DB00798 | Gentamicin | 74 | Yok | Var | Yok |
| DB01172 | Kanamycin | 24 | Var | Var | Yok |
| DB00601 | Linezolid | 115 | Var | Yok | Yok |
| DB06799 | Methenamine | 11 | Yok | Yok | Yok |
| DB00779 | Nalidixic acid | 47 | Yok | Var | Yok |
| DB04911 | Oritavancin | 46 | Yok | Var | Yok |
| DB00713 | Oxacillin | 47 | Yok | Var | Yok |
| DB00595 | Oxytetracycline | 28 | Var | Var | Yok |
| DB00919 | Spectinomycin | 12 | Var | Var | Yok |
| DB00259 | Sulfanilamide | 2 | Var | Var | Yok |
| DB00976 | Telithromycin | 143 | Var | Yok | Yok |
| DB00560 | Tigecycline | 173 | Var | Var | Yok |
| DB00911 | Tinidazole | 86 | Var | Yok | Yok |
| DB00684 | Tobramycin | 158 | Var | Yok | Yok |
| DB00512 | Vancomycin | 80 | Var | Yok | Yok |

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

Referans kök `C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset`. [Yol referansları](qa/WP03/final_review/source_path_references.csv) doğrudan script satırlarını kaydeder; dolaylı kullanım aşağıda ayrıca açıklanır.

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
