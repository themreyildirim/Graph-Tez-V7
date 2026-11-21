# WP00 veri sözlüğü

Durum: 05.11.2026, yerel örnekler ve yedi Drive CSV'si incelendi. Ayrıntılı örnekler ve ölçülen boşluk oranları `reports/qa/schema_summary.md` ve `reports/qa/drive_schema_summary.md` içindedir. Ham Drive CSV'leri yerel diske kaydedilmedi.

## Temel kavramlar

CSV virgülle, TSV sekmeyle ayrılan tablodur. Sütun adı bir alanın anlamını, satır bir kaydı gösterir. XML iç içe kayıtlar taşır; aynı `drug` etiketi farklı derinliklerde bulunabilir. Bir dosyanın mevcut olması, şemasının doğru olması ve öğrenmede kullanılması üç ayrı durumdur.

Kimlikler sayısal görünse bile nicel özellik değildir: PubChem CID üzerinde toplama veya ölçekleme yapılmaz. Birincil DrugBank ID, ikincil ID ve tuz kimliği birbirinin yerine otomatik geçirilmez. Bir ilaç birden fazla ATC kodu veya hedef protein taşıyabilir.

## DrugBank XML — gerçek örnekte gözlendi

Kök: `{http://www.drugbank.ca}drugbank`. Kök metadata `version=5.1`, `exported-on=2026-01-04`. Bu değerler kaynak dosyanın beyanıdır; indirme tarihi veya daha ayrıntılı yayın sürümü değildir.

| XML yolu / alan | Tip ve anlam | Gerçek örnek | Kullanım ve uyarı |
|---|---|---|---|
| `drug/drugbank-id[@primary='true']` | Metin, birincil ilaç kimliği | DB00001 | Düğüm anahtarının adayı; kökün doğrudan drug çocuğundan okunur |
| `drug/drugbank-id` diğerleri | Tekrarlanabilen metin | BTD00024, BIOD00024 | İkincil kimlik, yeni ilaç sayılmaz |
| `drug/name` | Metin | Lepirudin | Görünür ad; tek başına eşleme veya J01 sınıflaması yapmaz |
| `drug/@type` | Kategori | biotech | Kayıt tipi, kimyasal özellik değildir |
| `drug/atc-codes/atc-code/@code` | Metin listesi | B01AE02 | İlk üç kayıt J01 değil; kohort çıkarılmadı |
| `drug/external-identifiers` | Kaynak/kimlik çiftleri | PubChem Substance → 46507011 | Substance ID, Compound CID değildir; otomatik CID olarak kullanma |
| `targets/target/polypeptide/@id` | Protein kimliği | P00734 | Hedef düzeyinde UniProt accession |
| `polypeptide/external-identifiers` | Kaynağı belirtilmiş kimlik | UniProtKB → P00734 | Drug düzeyindeki UniProt kaydıyla hedefi karıştırma |
| `polypeptide/@source` | Kaynak metadata | Swiss-Prot | Kimlik baş harfi yerine gerçek kaynak alanı; henüz model özelliği değil |
| `polypeptide/gene-name` | Gen sembolü | F2 | Tek başına organizmalar arası anahtar olamaz |
| `polypeptide/organism` | Organizma metni | Humans | Taksonla doğrulama sonraki aşamada |
| `polypeptide/amino-acid-sequence` | FASTA metni | `>lcl…Prothrombin` + satır sonu + dizi | Başlık ayrılmadan AAC/DC hesaplanmaz |
| `polypeptide/gene-sequence` | Nükleotit dizisi | Ayrı XML etiketi | Protein dizisi değildir; A/C/G/T amino asit harfleriyle de çakışır, yalnız alfabe testi yetmez |

İlk üç ilaçta 10 hedef polipeptit görüldü. Bunların amino asit dizilerinde FASTA başlığı korundu; başlık satırı ayrıldıktan sonra 10/10 örnek 20 standart amino asit kontrolünü geçti. Özellik çıkarımı yapılmadı. Bu 10 örnek eski 70 proteinlik kümenin doğrulaması değildir. `sequence` doğrudan polipeptit çocuğu örneklerde yok; eski kodun bu alanı araması şema uyuşmazlığıdır.

## SIDER TSV — gerçek örnekte gözlendi

Dosyada başlık yoktur; aşağıdaki adlar eski kodun altı sütunluk şemasından atanmıştır. Sürüm 4.1 eski belgelerde yazılıdır; başlıksız yerel dosyada sürüm doğrulanamaz. UMLS değerlerini MedDRA'nın sayısal PT kodları diye etiketlemeyin.

| Sıra | Atanan sütun | Tip / anlam | İlk gerçek değer | İlk 1000 satır boşluk |
|---:|---|---|---|---:|
| 1 | flat_id | STITCH biçimli düz kimlik, metin | CID100000085 | 0/1000 |
| 2 | stereo_id | STITCH biçimli stereo kimlik, metin | CID000010917 | 0/1000 |
| 3 | umls_cui_from_label | Kaynak etiketin UMLS kavramı | C0000729 | 0/1000 |
| 4 | meddra_type | LLT / PT / boş | LLT | 4/1000 (%0,4) |
| 5 | umls_cui | Eşlenen kavram kimliği | C0000729 | 4/1000 (%0,4) |
| 6 | side_effect_name | Yan etki adı | Abdominal cramps | 0/1000 |

Örnekte flat alanı `CID1`, stereo alanı `CID0` ile başlıyor. Sadece `CID` yazısını silmek flat alanını doğru PubChem CID'ye çevirdiğini kanıtlamaz. Kimlik dönüşümü ve tuz/stereo ilişkisi WP03'te doğrulanacak. Aynı stereo kimlik ve kavram, farklı kaynak kavram satırlarıyla yeniden görünebilir; tam satır tekrarı ile ilişki tekrarı farklıdır.

## STRING — gerçek örnekte gözlendi

İnsan `9606`, E. coli `511145`; `v12.0` dosya adından alınır. İçeriğin indirme/sürüm manifesti bulunmadı. Links dosyası boşluk ayrımlıdır; aliases sekme ayrımlıdır.

| Dosya türü / sütun | Tip | Anlam ve örnek |
|---|---|---|
| links / protein1 | Metin | Birinci STRING kimliği: `9606.ENSP00000000233` veya `511145.b0001` |
| links / protein2 | Metin | İkinci STRING kimliği: `9606.ENSP00000356607` veya `511145.b1715` |
| links / combined_score | Tamsayı | Kenar skoru; ilk örnek 173 / 520. Protein düğüm özelliği değildir |
| aliases / #string_protein_id | Metin | Takson içeren STRING anahtarı |
| aliases / alias | Metin | Alternatif kimlik veya ad; her değer UniProt değildir |
| aliases / source | Metin | Alias kaynağı: örneğin Ensembl_PDB veya UniProt_DR_GeneID |

Her dosyanın ilk 1000 satırında üç alanın boşluk oranı %0. Aliases eşlemeleri bire bir varsayılamaz; `(protein, alias)` tekrarları farklı `source` değerleriyle geçebilir. İnsan/E. coli eşlemeleri ayrı tutulacak. Örneklerden genel kenar sayısı, bileşen veya model protein kapsaması çıkarılmadı.

## Drive tarihsel tabloları — gerçek CSV doğrulaması

Yedi CSV'nin tamamı bağlantıdan bellekte okundu. Aşağıdaki alanlar gerçek başlıklarla doğrulandı; yalnız işlenmiş PPI ve `.pt` dosyaları metadata düzeyinde bırakıldı. Tam sütun tipleri ve eksiklikler `drive_schema_summary.md` içindedir.

| Dosya | Beklenen alanlar | Rol |
|---|---|---|
| drug links.csv (19842×23) | DrugBank ID, Name, Drug Type, PubChem Compound ID, PubChem Substance ID, UniProt ID ve diğer kaynak kimlikleri | DrugBank–PubChem köprüsü; Compound ID 11120 satırda boş (%56,04). Buradaki UniProt ID hedef tablosu değildir |
| ilac_feature_v5_atc.csv | MW, LogP, HBD, HBA, TPSA; DrugBank_ID, Drug_Name, pubchem_clean; beş `_norm`; ATC_* | Yalnız geçmiş QC; tüm kümede normalize edilmiş alanlar doğrudan yeni modele verilmez |
| ilac_yan_etki_v5.csv (865×6) | pubchem_id, side_effect_name, umls_cui, se_kategori, DrugBank_ID, Drug_Name | Gerçek dosyada UMLS ve Drug_Name da var; görünen eski kodun dört sütunlu çıktısıyla revizyon farkı |
| ilac_protein_eslesmesi_v6.csv | DrugBank_ID, Drug_Name, UniProt_ID, Gene_Name, Organizma | İlişki tablosu; ilaç/protein çiftleri tekillik kontrolü |
| protein_dizileri_v6.csv | UniProt_ID, Gene_Name, Sequence, Organizma | 70/70 satırda başlık-dizi sınırı kaybolmuş; tahminle ayrıştırılmayacak |
| protein_feature_v6.csv | UniProt_ID, Gene_Name, Organizma, kalite_skoru; AAC_*, DC_*, YZ_* | 20 AAC + 25 grup DC + 5 özet; `kalite_skoru` yeni girdide yasak |
| sadece_antibiyotikler.csv | DrugBank_ID, İlaç_Adı, ATC_Kodu | 209 benzersiz ID = 84 DB + 125 DBSALT; 209 etkin madde değildir |
| ppi_insan_v3.csv / ppi_bakteri_v3.csv | protein1_uniprot, protein2_uniprot; kalan sütunlar bilinmiyor | Ham STRING'den üretilmiş geçmiş PPI |
| heterogen_ag_v6.pt | Tarihsel HeteroData | Yalnız metadata; WP00'da deserialize edilmez |

## Envanter durumlarının anlamı

`data_inventory.csv` ve `source_inventory.csv` aynı içeriği taşır. `status=exists` dosya veya izinli kaynak klasörünün mevcut olduğunu, `scope=allowed_container` yalnız gezilen klasörü belirtir. Grafikler klasörleri saymaz. `local_status=missing` yalnız izinli yerel aramada bulunamadı demektir; Drive'da mevcut kayıtlar `status=exists`, `location=drive`, `remote_status=exists` olarak gösterilir. `local_inventory.csv` ilk yerel gözlemi korur. `excluded` girdilerde boyut, tarih veya içerik analizi yoktur; yalnız ad kaydı tutulur. `unreadable` içerik okuma başarısızlığı içindir. `inspected=True` ile birlikte `reason/scope` okunmalı: yerel XML/PPI örneği, tam Drive CSV ve metadata farklı kapsamdır.

## Kaynaklar arası QC sonucu

56 ilaç feature kaydının DrugBank ve CID değerleri köprüyle 56/56 uyumlu. Köprüde 8722 dolu Compound ID birbirinden farklı; bu dosyada CID çakışması gözlenmedi. Aday listedeki 125 DBSALT köprüde doğrudan yok; 84 DB mevcut. Tuzları ana ilaca bağlamadan satır atmak kayıp yaratabilir; kimyasal eşdeğerlik ayrıca doğrulanmalıdır.

Eski 865 `(CID, PT adı, UMLS)` kaydının tamamı yerel SIDER'ın 309849 satırlık akış taramasında bulundu. Bu kaynak izi kontrolüdür; yeni kohort/etiket tablosu üretilmedi. SIDER'da bulunmak klinik nedensellik veya negatif etiket kanıtı değildir.
