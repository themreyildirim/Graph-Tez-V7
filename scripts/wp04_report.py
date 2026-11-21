"""WP04 küçük QA tablolarından Türkçe rapor; kaynak/API yeniden okunmaz."""
from pathlib import Path
import json
import re
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP04'


def table(df):
    def fmt(v):
        if pd.isna(v):return 'eksik / bekletildi'
        if isinstance(v,bool):return 'Evet' if v else 'Hayır'
        if isinstance(v,float):return f'{v:.4f}'
        return str(v).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(str,df.columns))+' |','|'+'|'.join(['---']*len(df.columns))+'|']+
        ['| '+' | '.join(fmt(x) for x in row)+' |' for row in df.itertuples(index=False,name=None)])


def main():
    def read(n):return pd.read_csv(QA/n,keep_default_na=False)
    s=json.loads((QA/'coverage_summary.json').read_text(encoding='utf-8'))
    meta=json.loads((QA/'xml_extract_manifest.json').read_text(encoding='utf-8'))
    q=read('structure_validation.csv');src=read('structure_sources.csv');rec=read('coverage_and_recovery.csv')
    full=q[['id','name','cid','parse_status','identity_verified_local','strict_qc_pass','review_flags']].sort_values('name')
    full.columns=['DrugBank ID','İlaç','CID','RDKit SMILES','Yerel kimlik uyumu','Temkinli QC','İnceleme bayrağı']
    new=rec[~rec.old_chemistry_available].copy().sort_values('name')
    new=new[['id','name','newly_computed_raw','recovered_strict','review_flags']]
    new.columns=['DrugBank ID','Önceden eksik ilaç','Ham beş değer hesaplandı','Temkinli QC geri kazanım','İnceleme bayrağı']
    problems=q[q.review_flags.ne('')][['id','name','components','chiral_unassigned','legacy_chiral_unassigned','double_stereo_unassigned','review_flags']]
    old=read('legacy_difference_summary.csv')
    log=(QA/'test_results.txt').read_text(encoding='utf-8-sig')
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s',log)
    assert match and match.group(1)=='20' and log.rstrip().endswith('OK')
    text='''# WP04 — Moleküler veri keşfi, RDKit ve kimya kapsamı

05.11.2026 — **Tamamlandı; kullanıcı onayı bekleniyor.** WP03 kapanışı kullanıcı tarafından onaylandı. Yalnız WP04 yapıldı; önceki raporlar/notebook'lar korunarak yeni çıktılar ayrı dizine yazıldı.

## Sonuç: 62 yapının ne kadarı güvenilir temsil edilebiliyor?

**62 ilacın tamamında yerel DrugBank XML'de SMILES, InChI, InChIKey ve formül bulundu.** 62 SMILES RDKit tarafından ayrıştırıldı. Hesaplanan tam InChIKey'ler hem kaynak anahtarla hem kaynak InChI'den ayrı hesaplanan anahtarla uyumlu; 62 CID mevcut WP02 köprü kaydıyla uyuşuyor. Bu, **yerel kaynak ve kimlik bağı tutarlılığıdır**. Güncel PubChem yapı kaydı bağımsız olarak sorgulanıp doğrulandı veya her ticari ürün/formülasyon aynı moleküldür denmiyor.

| Kapsam ölçüsü | İlaç / 62 |
|---|---:|
| Önceden beş kimya özelliği mevcut | 41 |
| Önceden kimya eksik | 21 |
| Yerel SMILES + InChI + InChIKey | 62 |
| RDKit ayrıştırması başarılı | 62 |
| Yerel tam yapı anahtarı + CID köprü uyumu | 62 |
| Ham beş özellik hesaplandı | 62 |
| Bu WP'nin temkinli, bayraksız QC tablosu | 54 |
| İnceleme nedeniyle temiz tabloda bekleyen | 8 |
| Önceki 21 eksikten ham hesaplanan | 21 |
| Önceki 21 eksikten temkinli QC'de geri kazanılan | 18 |

**54, nihai model ilaç sayısı değildir.** QC politikası eksik stereo adaylarını, çok bileşenli kaydı ve algoritma uyuşmazlığını temkinli olarak bekletir. Bu kayıtların hepsinin yanlış olduğu iddia edilmiyor. 36 eski bayraksız kayıt + 18 geri kazanım = 54. Önceki 41'in beşi de inceleme listesine girdi; 41+18 şeklinde toplamak yanlış olur.

## Kaynaklar, sürüm ve işlem sınırı

- DrugBank XML: `Dataset/DrugBank/drugbank_all_full_database.xml/full database.xml`; kök `version=5.1`, `exported-on=2026-01-04`. Kaynak 1.898.100.846 bayt; daha ayrıntılı sürüm kanıtı yok.
- Onaylı 62 kimlik, WP03 mapping'den yalnız `id/name/cid` olarak ayrıldı. PT veya kategori sayıları kimyasal modüle geçirilmedi. WP02 `bridge_qc.json` önceki doğrulanmış köprü anlık görüntüsüdür; yeni Drive köprü revizyonu sorgusu yapılmadı.
- Önceki gerçek `drug links.csv` şemasında CID/SID var, SMILES/InChI alanı yok. Köprü molekül yapısı yerine kullanılamaz; SID CID yerine geçirilmedi.
- Eski V5 sayısal karşılaştırması izinli Drive `ilac_feature_v5_atc.csv` dosyasından salt okunur yapıldı. Kaynak 56 satır, değiştirilme zamanı `2026-05-15T02:44:25.295Z`. Ham CSV diske indirilmedi; yalnız ID/ad/CID ve beş ham değer QC JSON'una yansıtıldı. 41 ortak ilacın CID'si kohortla aynı. Normalizasyon/ATC sütunları yeni hesaba alınmadı.
- Aktif Python'da RDKit bulunmadığından kullanıcının istediği kütüphane yalnız `.deps/rdkit` içine kuruldu: pip sürümü `2026.9.1`, çalışma sürümü `2026.09.1`, Python `3.11.3`. Mevcut NumPy/Pillow kullanıldı; başka bağımlılık kurulmadı. İlk sandbox DNS denemesi başarısızdı; proje içi kurulum izinli ağ erişimiyle tamamlandı. Sistem Python paketleri değiştirilmedi.

**XML yöntemi:** Üst düzey `drug` kaydı ve doğrudan birincil DB kimliği ile seçim; nested drug referansları/tuz ID'leri ana ID yapılmadı. Her biten üst kayıt kökten çıkarılıp temizlendi. Yalnız 62 kaydın kimyasal alanları saklandı; protein dizileri/özellikleri çıkarılmadı. Son seçili kayıt olan 6.014. kayıtta duruldu: **__BYTES__ bayt**, **__SECONDS__ saniye**. Örneklenmiş RSS maksimum __RSS__ MiB, OS tepe çalışma kümesi __PEAK__ MiB; örneklenmiş ölçü tüm süreç tepe garantisi değildir. XML boyut/mtime aynı kaldı, büyük kaynak hash'i veya ikinci tam tarama yapılmadı. [Akış manifesti](qa/WP04/xml_extract_manifest.json).

Eski MASTER kodunda “XML'den çekmek başarısız olduğu için API kullanıldı” yorumu var. Gerçek XML'de `SMILES`, `InChI`, `InChIKey`, `Molecular Weight`, H-bağı alanları ve PSA **62/62** mevcut. Eski uygulama başarısızlığı alan yokluğu kanıtı değil. Aynı `logP` türü farklı kaynaklarla birden fazla geçebiliyor; tüm değerler ve sağlayıcıları korundu, birleştirilmedi. [Alan kapsamı](qa/WP04/xml_field_coverage.csv), [ham alan kanıtı](qa/WP04/xml_property_evidence.csv).

## Kavramlar ve gerçek örnekler

| Kavram | Öğretici gerçek karşılık | Dikkat |
|---|---|---|
| Atom / bağ | Linezolid atom indeksi, element, yük; SINGLE/DOUBLE/AROMATIC bağ tabloları | Atom indeksi kimlik standardı değil, bu RDKit nesnesinin sırası |
| SMILES | Kaynak ChemAxon SMILES alanı | Dallanma, halka kapanışı ve stereo işaretlerini taşır; adla yapı tahmini yok |
| Canonical SMILES | RDKit canonical çıktı | Yazılım/sürüm bağımlı sıralama; farklı canonical dizeler farklı molekül olmak zorunda değil |
| Isomeric SMILES | RDKit canonical + isomeric çıktı | Stereo ve izotop bilgisini destekler; canonical ile karşıt kavram değil |
| Nonisomeric yazım | Levofloxacin / Ofloxacin bağlantı karşılaştırması | Stereo/isotop ayrıntısı dışarıda; kimlik köprüsüne tek başına yeterli değil |
| InChI | Aynı kaydın katmanlı yapı dizgesi | Standartlaştırma/tautomer/protonasyon katmanları nedeniyle basit dize eşitliğiyle yorumlanmaz |
| InChIKey | Kaynak / SMILES / InChI karşılaştırması | Özet kimlikten yapı geri kurulmaz; ilk blok eşitliği tam eşitlik değil |
| `@/@@`, CIP R/S | Linezolid atom tablosu ve indeksli çizim | `@` sabit R demek değil; komşu sırası önemlidir |
| `.` ve tuz | Gentamicin'in üç bileşeni; XML salt bağlantıları | Çok bileşenlilik her zaman tuz değildir; salt bağlantısı da çizilen yapıya tuz eklemez |

Kavramların kodu, gerçek tablo ve şekilleri [çalıştırılmış notebook](../notebooks/WP04_molecular_exploration.ipynb) içinde birbirinin hemen altında bulunur. Molekül çizimleri 2D gösterimdir; 3D konformer, enerji, farmakolojik etkinlik veya yan etki riski hesabı değildir. Molekül yapıları kimyasal açıdan karşılaştırılırken klinik üstünlük çıkarılmaz.

## Tüm 62 ilacın yapı kaynağı ve QC tablosu

Aşağıdaki 62 satırın her birinde kaynak **yerel DrugBank XML ana kaydı**; SMILES/InChI/InChIKey mevcut, RDKit ayrıştırması ve CID köprü uyumu başarılı. `valid` yalnız ayrıştırma başarısı; “yerel kimlik uyumu” yukarıdaki kaynak içi denetimdir. Ayrı canlı PubChem yapı kaydı bu WP'de elde edilmedi. Gerçek SMILES/InChI, sağlayıcı, kaynak XML yolu ve kayıt indeksi [structure_sources.csv](qa/WP04/structure_sources.csv) içinde tam olarak korunur. [Doğrulama tablosu](qa/WP04/structure_validation.csv) hesaplanan yazımları ve anahtarları taşır.

__FULL__

## Sekiz inceleme kaydı: hatadan çok temsil sınırı

__PROBLEMS__

- **Gentamicin:** kaynak SMILES üç bağlantısız organik bileşen, toplam formül `C60H123N15O21`; bu bir tek ana bileşen seçme problemi değil, kaynak karışım temsilidir. Ham MW/LogP/HBD/HBA/TPSA bütün kayıt üzerinde hesaplandı. Bu sayılar bir bileşenin veya ağırlık oranları bilinmeyen bir ticari karışımın fiziksel özelliği olarak sunulamaz. En büyük fragment seçilmedi, atom/bağ silinmedi.
- **Carbenicillin, Lomefloxacin, Gatifloxacin, Gemifloxacin, Ofloxacin:** en az bir potansiyel tetrahedral merkez kaynakta belirtilmemiş. Kaydın rasemat/karışım tanımı veya eksik stereo olması bu dosyalardan kesin ayrıştırılmadı. Bir enantiyomer seçilip tamamlanmadı.
- **Cefprozil:** bir potansiyel çift bağ geometrisi belirtilmemiş. Bu bir E/Z uyuşmazlığı tespiti değil, kaynağın belirtmediği geometri bayrağıdır; mevcut tam anahtar tutarlı.
- **Methenamine:** yeni RDKit stereo algılayıcısı dört potansiyel N merkezi, eski algılayıcı sıfır bildiriyor. Algoritma farkı ayrıca kaydedildi. Bu **dört gerçek kayıp stereomer veya kanıtlanmış yapı hatası** olarak yorumlanmaz. Temkinli tablo geçici inceleme için bekletiyor; molekülün kullanılabilirliği üzerinde nihai karar verilmedi.

62 kayıtta ayrıştırma başarısızlığı **0**, yerel tam anahtar çatışması **0**, metal içeren kayıt **0**; bu tür problemlerin genel olarak olmadığı sonucu çıkarılamaz. Kaynak tuz bağlantıları ayrı sayıldı; bunlar otomatik olarak yeni molekül veya noktalı tuz yapısı sayılmadı. Metal/tuz hatalarının kod yolu sentetik testlerle doğrulanmıştır; sentetik örnekler kohorta eklenmemiştir.

## Beş özellik: tanımlar, ham/temiz/eksik ayrımı

| Alan | Yeni hesap | Birim / yorum |
|---|---|---|
| MW | `Descriptors.MolWt` | g/mol; ortalama molekül ağırlığı, monoisotopik ağırlık değil |
| LogP | `Crippen.MolLogP` | Wildman–Crippen; eski PubChem XLogP ile aynı yöntem değil, deneysel logD değil |
| HBD | `Lipinski.NumHDonors` | H-bağı donor merkez sayısı, H atom sayısı değil |
| HBA | `Lipinski.NumHAcceptors` | H-bağı acceptor merkez sayısı, tüm heteroatomların sayısı değil |
| TPSA | `CalcTPSA(includeSandP=False)` | Å²; N/O katkıları; S/P eklenen alternatif ayrı duyarlılık tablosunda |

Kaynak SMILES'in tüm bileşenleri korunarak hesaplandı; nötralizasyon, parent seçimi, tautomer düzenleme veya stereo tamamlama yapılmadı. RDKit canonical çıktısı kaynak SMILES'i ezmedi. Salt string boşluğu dışında bir temizleme ile kaynak değiştirilmedi.

- **Ham:** [chemical_features_raw.csv](qa/WP04/chemical_features_raw.csv), 62 satır ve yalnız `id,MW,LogP,HBD,HBA,TPSA`. Bütün hesaplanabilir sayılar korunur.
- **Temiz/temkinli:** [chemical_features_clean.csv](qa/WP04/chemical_features_clean.csv), aynı 62 ID; 54 bayraksız kayıt değer taşır, sekiz inceleme kaydının beş alanı boş. Bu tablo son model kohortu/özellik tensörü değildir.
- **Eksik / bekletilmiş:** [missingness.csv](qa/WP04/missingness.csv) her özellik için önceki 21 eksik, yeni ham 0 eksik ve temiz tabloda 8 bekletilmiş değeri ayırır. Gerçek sıfır eksik yerine kullanılmadı; dolgu/ölçekleme yapılmadı. Gerekçeler QC tablosunda korunur.

**Sızıntı kontrolü:** Hesap fonksiyonu yalnız RDKit `Mol` alır. PT, kategori, etiket yoğunluğu, `has_pt`, raporlama sıklığı ve `kalite_skoru` özellik şemasında yok. Kohort/QA bayrakları kimya vektörüne alınmadı. Henüz eğitim olmadığı için gelecekteki eğitim hattına uçtan uca sızıntı yok garantisi verilmez; yalnız bu hesabın sınırı doğrulandı. Mevcut 30 kategori tanımı değişmedi.

## Eski V5 sayısal değerleri ile karşılaştırma

Eski kodun yalnız ilgili API tanımı metin olarak incelendi; kod çalıştırılmadı/kopyalanmadı. Eski sütunlar PubChem MolecularWeight, XLogP, HBondDonorCount, HBondAcceptorCount, TPSA yanıtlarından geliyor. 41 ortak CID'de 205 karşılaştırma; sekiz inceleme kaydından eski özellik taşıyanların **ham karşılaştırmaları da**, bayraklarıyla birlikte korunur. Bu karşılaştırma tüm kayıtların temiz olduğu iddiası değil.

__DIFFERENCES__

MW'de en büyük mutlak fark yaklaşık **0,071 g/mol**; küçük farkların yuvarlama/atomik ağırlık tanımına bağlı olması mümkün, tek neden kanıtlanmadı. HBD 41/41 aynı. HBA'da ortalama mutlak fark yaklaşık **1,317** merkez, LogP'de **1,134**, N/O-only TPSA'da **8,574 Å²**. LogP'nin XLogP yerine Wildman–Crippen ile hesaplanması yöntem değişimidir; daha doğru/yanlış olduğu bu karşılaştırmayla söylenemez. HBA tanımları ve hesaplayıcı kuralları da farklı olabilir; her farkın mekanik nedeni tek tek ispatlanmadı.

TPSA tanımı önemli bir somut örnek: Ampicillin N/O-only yaklaşık **112,73**, S/P dahil **138,03 Å²**, eski değer **138,0**. [TPSA tanım duyarlılığı](qa/WP04/tpsa_definition_sensitivity.csv) bütün yapılar için iki tanımı yan yana saklar. Bu gözlem eski farkların tümünün S/P nedeniyle olduğunu kanıtlamaz. Eski değere yakın olsun diye ilaç bazında yöntem seçilmedi; tek tanım tüm kohortta tutarlı tutuldu. Yeni beş değer PubChem XLogP özelliklerinin bire bir yeni kopyası olarak adlandırılmamalı.

## Önceki 21 eksik kimya kaydı

__NEW__

Önceki 21 kaydın hepsinde yerel yapıdan hesap var; **18** bayraksız. Gentamicin, Cefprozil ve Methenamine belirsizlik gerekçeleriyle temkinli tabloda bekliyor. “Eksikliği tamamladık” ile “nihai modele aldık” farklı kararlardır. Yeni kimyası geri kazanılan ilaçların hedef protein verisi bu aşamada yeniden üretilmedi veya tahminle doldurulmadı.

## Görseller: gösterdikleri ve tez açısından önemi

12 statik PNG, notebook hücreleri altında gerçek çıktılar ve Türkçe yorumlarla kaydedildi. RDKit'in çizgi-yazı motorunda Türkçe karakter kaybını önlemek için molekül içi başlıklar ID/ilaç adıyla sınırlı; açıklamalar Türkçe hücrelerde ve bu tabloda.

| PNG | Ne gösteriyor / ne öğreniyoruz? |
|---|---|
| `01_structure_coverage.png` | 62 yapı / 62 ayrıştırma / 62 yerel uyum / 54 temkinli QC; farklı başarı tanımlarını ayırır |
| `02_gentamicin_components.png` | Üç organik bileşenin tamamı; karışım temsili toplam özelliklerini tek bileşene yüklememeyi öğretir |
| `03_legacy_comparison.png` | 41 ortak ilacın beş alanında eski/yeni saçılımı; yöntem farkının görünürlüğü |
| `04_tpsa_definition.png` | Aynı yapı üzerinde S/P katkısı duyarlılığı; özellik adı kadar tanımın da kaydedilmesi |
| `DB01060_2D.png` | Amoxicillin: beta-laktam, S içeren halkalı iskelet ve fonksiyonel gruplar |
| `DB00537_2D.png` | Ciprofloxacin: aromatik/heterosiklik sistem ve F; makrolidden farklı bağlantı yapısı |
| `DB00207_2D.png` | Azithromycin: büyük makrolid ve bağlı halkalar; atom/bağ çeşitliliği ve yüksek yapı boyutu |
| `05_vancomycin_full.png` | Karmaşık molekülün tam çizimi; okunabilirlik için atom/bağ silinmedi |
| `DB00601_indexed.png` | Linezolid RDKit çiziminde atom indeksleri, bağ tipleri ve stereo; tabloya geri izlenebilirlik |
| `06_linezolid_teaching_graph.png` | Aynı atomları düğüm, bağları kenar yapan NetworkX örneği; aromatiklik işareti, eğitim grafı değil |
| `07_recovery.png` | Eski/ham/temkinli kapsam ve 21→21/18 geri kazanım; kazanım tanımı açık |
| `08_descriptor_distributions.png` | Ham 62 ile temkinli 54 dağılımı; karışım/uç değerler otomatik silinmez |

Molekül çizimlerinde karbon/H'nin geleneksel örtük gösterimi molekülden atom silmek değildir. Öğretici grafın düğüm/kenar sayısı RDKit atom/bağ sayısıyla eşit kontrol edildi. Linezolid atom/bond tabloları aromatic, bond type, yük, implicit/explicit H, chiral tag/CIP ve bond stereo alanlarını gösterir; eğitim tensörü, atom embedding'i veya moleküler GNN oluşturulmadı.

## PubChem kararı ve kaynak sınırı

Yerel kaynak yeterli olduğu için **üretim analiz istemcisiyle 0 PUG REST isteği** yapıldı, yeni Compound yanıtı elde edilmedi. API dokümanı araştırılırken web aracıyla CID 12560 için bir yapı alanı keşif isteği denendi; araç URL'yi erişilebilir bulmadı ve veri döndürmedi. Bu başarısız deneme hesaplarda kullanılmadı, tekrarlanmadı ve [pubchem_query_audit.json](qa/WP04/pubchem_query_audit.json) içinde kaydedildi. “Hiç deneme yapılmadı” veya “canlı API doğrulaması yapıldı” iddiası yok.

Gerekirse kullanılmak üzere ayrı `wp04_pubchem.py`: onaylı CID allowlist'i, en fazla 8 CID/istek, varsayılan ağ kapalı, toplam 3 istek, en fazla 1 istek/saniye, 30 saniye timeout, gelen CID kümesi kontrolü, URL/payload hash'li cache, zaman ve başarısızlık kaydı. SID veya ilaç adına göre yapı aranmaz. Canlı CID çağrısı değil **sentetik yanıtlarla** önbellek ve kimlik hata yolları test edildi; bu test yanıtları gerçek kimyasal kanıt değil ve geçici test dizininde silinir.

Yerel stereo-belirsiz yapı, mevcut CID'nin tanımladığı kaynak kapsamı olabilir. Aynı yapıyı başka servisten almak tek başına rasemat/karışım kararını çözmez. Daha sonra klinik/formülasyon düzeyinde karar gerekirse ayrıca kapsam ve kanıt değerlendirilmelidir; burada ek veri seti veya bağımsız UniProt/API kaynağı eklenmedi.

## Testler, yeniden üretim ve dosyaların amacı

**20/20 test geçti; __TEST_SECONDS__ saniye.** [Tam test çıktısı](qa/WP04/test_results.txt). Kapsam: geçersiz/eksik SMILES, bilinen küçük molekül hesabı, atom sırası değişmezliği, enantiyomer tam anahtar farkı, metal/çok bileşen koruma, TPSA tanımı, atom/bağ tabloları, nested XML ID ve kayıt temizleme/erken durma, CID allowlist ve SID reddi, ağ kapalı varsayılanı, cache/yanıt kimliği/bütçe/başarısızlık, 62 kimlik/özellik şeması, 21/18 kazanım, 54/8 maskeleme, gerçek notebook/görseller ve önceki 173 dosyanın korunması.

İlk önbellek testi sistem geçici dizininde sandbox'ın dosya yeniden adlandırmasını engellemesi nedeniyle kaldı; test geçici dizini izinli proje QA dizinine taşındı. Üretim cache doğrulaması zayıflatılmadı; düzeltilmiş testlerin tamamı tekrar çalıştırıldı. Ham XML sadece stat/metadata ile kontrol edilir, testte yeniden taranmaz.

| Dosya / grup | Amaç |
|---|---|
| `notebooks/WP04_molecular_exploration.ipynb` | 12 yürütülmüş kod hücresiyle kavram, tablo, molekül, grafik, yorum |
| `reports/WP04.md` | Bu Türkçe bilimsel keşif/QC ve karar sınırı raporu |
| `xml_chemical_records.json`, `xml_property_evidence.csv` | Seçili gerçek kimyasal alanların kaynaklı ham projeksiyonu |
| `structure_sources.csv`, `structure_validation.csv` | 62 yapı kaynağı, yazım/anahtar/formül ve sorun izi |
| `chemical_features_raw.csv`, `chemical_features_clean.csv`, `missingness.csv` | Ham hesap, temkinli hesap ve eksiklik ayrımı |
| `coverage_and_recovery.csv`, `coverage_summary.json` | 62 kapsam ve önceki 21'in açık kazanım durumları |
| `legacy_chemistry_reference.json`, `legacy_feature_comparison.csv`, `legacy_difference_summary.csv` | Drive V5 kaydıyla sayısal yöntem karşılaştırması |
| `tpsa_definition_sensitivity.csv` | S/P dahil/haricinin aynı yapı üzerindeki etkisi |
| `DB*_atoms.csv`, `DB*_bonds.csv` | Beş gerçek örneğin öğretici atom/bağ tabloları |
| `xml_extract_manifest.json`, `analysis_input_manifest.json`, `prior_outputs_hashes.json`, `method_sources.json` | Kaynak/sürüm/bellek/bütünlük ve resmi yöntem referansları |
| `scripts/wp04_extract.py` | Yeni XML alanlarını tek akışla seçer; CLI/env ham kök desteği |
| `scripts/wp04_chemistry.py`, `scripts/wp04_analyze.py` | Etiketten bağımsız RDKit fonksiyonları ve kaynaklı QA hattı |
| `scripts/wp04_pubchem.py` | Gerekirse kullanılabilecek kontrollü/cache'li istemci; burada canlı analiz çağrısı yok |
| `scripts/wp04_notebook.py`, `scripts/wp04_report.py` | Küçük WP04 QA girdilerinden notebook/rapor/grafik üretimi |
| `tests/test_wp04.py`, `reports/qa/WP04/test_results.txt` | 20 test ve gerçek sonuçları |
| `reports/figures/WP04/`, `run_status.md` | 12 PNG ve onay kapısı durumu |

İlk XML çıkarımı zaten tamamlandı. Normal tekrar üretimde büyük kaynağı yeniden tarama:

```powershell
python scripts/wp04_analyze.py
python scripts/wp04_notebook.py
python -m unittest discover -s tests -p test_wp04.py -v
python scripts/wp04_report.py
```

`wp04_extract.py` yalnız kaynak alanlarını bilinçli yeniden çıkarmak gerektiğinde çalıştırılır. `--dataset-root` veya `GRAPH_TEZ_DATA_ROOT` override destekler; eski WP00–WP03 kodu yeniden yazılmadı. `.deps/rdkit` taşınmazsa aynı RDKit sürümü gerekli; notebook bu yerel kurulum varsa otomatik import yoluna ekler. Eski raporlar yeniden üretilmez. Son korunma hash'leri ham büyük dosyaları içermez; önceki proje çıktıları içindir.

## Yöntem kaynakları ve sınırlamalar

- [RDKit başlangıç ve SMILES](https://rdkit.org/docs/GettingStartedInPython.html): ayrıştırma, canonical/isomeric yazım ve gösterim.
- [RDKit Crippen](https://rdkit.org/docs/source/rdkit.Chem.Crippen.html): atom katkılı Wildman–Crippen LogP tanımı.
- [RDKit Book — TPSA ve stereo](https://www.rdkit.org/docs/RDKit_Book.html): varsayılan N/O katkıları ve S/P seçeneği; stereo algılamasının yöntem sınırları.
- [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest): alan semantiği; doğrudan sayfa erişimi CAPTCHA döndürdü, resmi arama indeksi açıklaması okunabildi. Güncel `ConnectivitySMILES` bağlantı katmanıdır, `SMILES` stereo destekli alan; eski CanonicalSMILES/IsomericSMILES adlarıyla dönen anahtar varsayılmamalı.
- [PubChem programatik erişim](https://pubchem.ncbi.nlm.nih.gov/docs/programmatic-access): servis kullanım sınırları; hazırlanan istemci daha temkinli tek çağrı/saniye uygular.

Tam InChIKey uyumu bu çalışmada kaynak içi güçlü bir kontrol olsa da tek başına tüm kimyasal/formülasyon belirsizliklerini çözmez. Stereosu belirtilmemiş kayıtlar tamamlanmadı; çok bileşenlerin oranları tahmin edilmedi; hasta riski/tedavi veya biyolojik nedensellik çıkarımı yapılmadı.

**WP04 tamamlandı; kullanıcı onayı bekleniyor. WP05'e geçilmedi. Model, moleküler GNN, öğrenme grafı/tensörü, train/test ayrımı veya protein özellikleri üretilmedi. Ham kaynaklar ve önceki çıktılar değiştirilmedi.**
'''
    text=text.replace('__FULL__',table(full)).replace('__NEW__',table(new)).replace('__PROBLEMS__',table(problems)).replace('__DIFFERENCES__',table(old))
    values={'__BYTES__':f"{meta['bytes_read']:,}".replace(',','.'),'__SECONDS__':f"{meta['elapsed_seconds']:.1f}".replace('.',','),
            '__RSS__':f"{meta['sampled_rss_max_mib']:.1f}".replace('.',','),'__PEAK__':f"{meta['os_peak_wset_mib']:.1f}".replace('.',','),
            '__TEST_SECONDS__':match.group(2).replace('.',',')}
    for k,v in values.items():text=text.replace(k,v)
    (ROOT/'reports/WP04.md').write_text(text,encoding='utf-8')
    print('WP04 report: 62 structure rows, 21 recovery rows, 8 review rows')


if __name__=='__main__':main()
