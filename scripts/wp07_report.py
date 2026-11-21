"""WP07 raporu: yalnız küçük, test edilmiş entegrasyon çıktılarını raporlar."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP07'


def table(frame):
    def fmt(x):return str(x).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(frame.columns)+' |','|'+'|'.join(['---']*len(frame.columns))+'|']+
                     ['| '+' | '.join(fmt(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)])


def main():
    s=json.loads((QA/'integration_summary.json').read_text(encoding='utf-8'))
    a=json.loads((QA/'artifact_validation.json').read_text(encoding='utf-8'))
    env=json.loads((QA/'environment.json').read_text(encoding='utf-8'))
    read=lambda n:pd.read_csv(QA/n,keep_default_na=False)
    m=read('drug_modality_QA.csv')
    held=m[m.molecule_review | ~m.protein_modality_available][['drug_id','name','molecule_review','review_flags','protein_modality_available']]
    text=f'''# WP07 — Veri entegrasyonu ve heterojen graf incelemesi

06.11.2026 — **WP07 tamamlandı; kullanıcı onayı bekleniyor.** WP06 kullanıcı tarafından onaylandı. WP08 başlamadı.

## Ne tamamlandı?

Aktif ROADMAP WP07, kanonik ID ile veri entegrasyonu, maskeler, uygunsuz girdi/kenar engeli ve doğrulanmış HeteroData ister. Bu kapsamda **altı gerçek PyG HeteroData inceleme nesnesi** üretildi. Hepsinde **62 ilaç, 141 protein ve 1061 kaynak PT denetim düğümü** korunur. İlaç–protein **476 tipli kenar** ayrı target/enzyme/transporter/carrier ilişkileridir. Bu nesneler **training_ready=False** taşır; nihai eğitim kohortu, model giriş matrisi x, hedef tensörü y, split veya model oluşturulmadı.

Kullanıcının açık karar gerektiren seçenekleri sabitlememe kuralına uygun olarak, [D01–D07 karar raporu](WP07_DECISION_GATE.md) hazırlandı. Bu yapısal inceleme kapsamı nihai model şeması yerine geçmez. Öğrenme için gerekli eksik modalite/etiket/protokol kararları verilmiş sayılmaz.

## Önceki çıktıların bütünlüğü ve kaynak sınırı

- Başlangıçta WP06 koruma manifestindeki 275 önceki dosyanın hash'i doğrulandı. WP00–WP06 rapor, QA, notebook, görsel, kod, test, plan ve konfigürasyonlarından **{s['prior_files_verified']} dosyalık yeni koruma manifesti** alındı; kapanışta hepsi aynı SHA-256 ile bulundu. Önceki testler/QC/kimlikler değiştirilmedi veya yeniden üretilmedi. `run_status.md` istenen güncel kayıt olarak bu korumanın dışındadır.
- WP00–WP06'nın yedi raporu mevcut. Önceki notebook ve ilgili dosyalar koruma manifestindedir. Önceki tüm test takımları yeniden çalıştırılmadı; hash koruması eski testlerin bugün yeniden çalıştırıldığı anlamına gelmez.
- Yalnız proje içindeki küçük QA okundu. XML, SIDER ve iki organizmanın STRING links/aliases dosyalarında **altı farklı ham dosya için yalnız boyut/mtime** kontrolü yapıldı; metadata aynı. Ham içerik yeniden taranmadı/hash alınmadı. Metadata eşitliği bağımsız içerik hash doğrulaması değildir. Kapsam dışı klasörler açılmadı.
- Provenans zinciri: DrugBank XML 5.1 / 2026-01-04 export → WP04/WP05 kimlik/yapı/dizi; SIDER 4.1 → WP03 pozitif ve PT kanıtı; STRING v12.0 → WP06 alias/kenar kaynak satırları → WP07 indeksler. Mevcut kaynak sürümleri yeniden güncellenmedi. [Girdi hash'leri](qa/WP07/input_manifest.json), [koruma manifesti](qa/WP07/prior_outputs_hashes.json), [kapanış kontrolü](qa/WP07/artifact_validation.json).
- ROADMAP/eskiden kalan DATA_CONTRACTS içindeki “35 hedef” sayısı güncel nihai sözlük değildir. WP03 gerçek 1061 PT/30 tarihsel kategori ayrımıyla denetlendi; eski belgeler ezilmedi. Drug-disjoint ayrıklık AGENTS gereği zorunludur; açık karar yalnız bunun uygulama düzeni/oranı/CV ayrıntılarıdır.

## Kanonik kimlik, düğüm ve ilişki sözleşmesi

| Tür | Kimlik | Sayı | İnceleme işlevi |
|---|---|---:|---|
| drug | Primary DrugBank ID | 62 | Kohort sabit; DBSALT sayısı bağımsız ilaç değil |
| protein | WP05 UniProt accession | 141 | PPI yok diye elenmez; organizma kaynak registry'de |
| se_pt_audit | UMLS PT CUI | 1061 | Gözlenen kaynak sözlüğü; ilişki kenarı/x yok; nihai hedef seti değil |
| STRING_context_only | Kaynak STRING ID | 80 | Ayrı envanter; HeteroData'ya eklenmedi; dizi özellikleri yok |

Node_index sıralı kanonik ID'den deterministik hesaplanır, biyolojik özellik değildir. Protein ve ilaç sayıları her senaryoda sabit tutulur; PPI ilişkisi olmayan düğümler korunur. Context dışarıda tutma bu incelemenin güvenli kapsamıdır; nihai context stratejisi seçilmedi. İlaç kimyası veya protein dizileri yeniden hesaplanmadı.

| DrugBank rolü | Benzersiz tipli kenar |
|---|---:|
| target | 241 |
| enzyme | 78 |
| transporter | 135 |
| carrier | 22 |

Toplam 476 tipli kenar, WP05'in 457 farklı ilaç–protein çiftinden farklı bir sayımdır; bir çift birden fazla rol taşıyabilir. `source_type=drug, target_type=protein` depolama yönüdür; `target` rolünün biyolojik anlamıyla karıştırılmaz. Otomatik ters DrugBank ilişkisi oluşturulmadı; gelecekte ters mesaj ilişkisi ayrı tasarım kararıdır.

![İnceleme şeması](figures/WP07/01_review_schema.png)

**Şekil yorumu:** İlaç ve protein girdi yapısı ile SIDER hedef deposu farklıdır. 1061 PT düğümüne hiçbir hedef/ters hedef kenarı bağlanmaz; bu düğümlerde sıfır veya öğrenilen embedding üretilmedi. PyG `validate()` bu düğüm tipinin izole olduğunu uyarır; uyarı bilinçli hedef ayrımını yansıtır ve testlerde yalnız bu beklenen uyarı kabul edilir. Yapısal doğrulama klinik doğruluk/öğrenme faydası kanıtı değildir.

## PPI senaryoları ve korunmuş taksonomi kapsamı

PPI'sız temel nesneye ek aşağıdaki senaryolar oluşturuldu. İnsan **63 aynı-taxID** accession; K-12 **23 tam alias fakat 83333→511145 çözünürlük incelemesi** accession. Alt suş kapsamı kabul edilmedi. Hiçbir nesnede iki PPI kapsamı birleştirilmedi. K12 700 yalnız mevcut WP06 örnek eşiğidir, nihai eğitim eşiği değildir.

{table(read('ppi_scenarios.csv'))}

Yönsüz kaynak çifti iki yönlü PyG edge_index sütunuyla saklanır; 184 insan çifti 368 sütundur. Bu depolama tercihi kenar sayısını biyolojik olarak ikiye katlamaz. Skorlar nesnenin node.x veya edge_attr alanına yazılmadı; yalnız kaynak provenansı ve senaryo filtresinde tutulur. Kaynak STRING ID, accession uçları, scope, skor ve kaynak satırları [ppi_edge_provenance.csv](qa/WP07/ppi_edge_provenance.csv) içindedir. WP06 kenar/mapping dosyaları değiştirilmedi.

![PPI kapsamı ve sayımı](figures/WP07/04_ppi_scope_and_counts.png)

**Şekil yorumu:** 63/23/6/49 ayrımı korunur; katı PPI kapsamı dışındaki 78 protein hâlâ 141 protein düğümünün parçasıdır. Yüksek eşik daha az kenar bırakır, daha iyi model sonucu olduğu iddia edilmez.

## Modaliteler, inceleme bayrakları ve eksiklik

{table(read('modality_patterns.csv'))}

54 temiz kimya, sekiz bekletilmiş kimya ve 60 protein modalitesi kaynaklardan tekrar sayıldı. **53**, temiz kimya ve protein modalitesi bulunan kesişimdir; nihai eğitim kohortu değildir. 62'nin hiçbiri atılmadı. Boolean 0/1 maskesi özellik vektörü dolgusuyla aynı şey değildir.

{table(held)}

Tobramycin/Methenamine protein olmadan korunur; Methenamine ayrıca WP04 incelemesindedir. Sekiz ilacın isimleri ve review_flags değerleri WP04 ile bire bir aynı. Kimya temiz tabloda beş alanın her birinde 8/62 (**%12,90**) eksik/bekletilmiş değer; protein 56 alanın her birinde 0/141 eksik. Ham 62 kimya hesabı kaynak WP04'te kalır; bekletilmiş değerler burada hamdan geçirilmedi. [Alan bazlı eksiklik tablosu](qa/WP07/source_feature_missingness.csv).

![Modalite örüntüleri](figures/WP07/02_modality_patterns.png)

**Şekil yorumu:** 53/7/1/1 dağılımı hangi dalın nasıl ele alınacağını görünür kılar. Özellikle yalnız inputları sınırlı olan Methenamine için model yolu karar gerektirir. Maskeli dal, train-only imputasyon veya alt kohort duyarlılığı karşılaştırılabilir; bugün birini seçip veri daraltılmadı.

![Ayrı ilişki rolleri](figures/WP07/03_role_edges.png)

**Şekil yorumu:** Taşıma/metabolizma proteinlerini antibakteriyel target gibi yeniden adlandırmak biyolojik anlamı değiştirir. Dört kenar tipi ayrı korunmuştur; ileride rol bazlı katkı analizi mümkündür.

**80 context düğümü:** doğrulanmış amino asit özelliği yoktur; sıfır vektör üretilmedi. Context kullanmama, tip tokenı+maske, ayrı topoloji encoder'ı ve sıfır+maske seçeneğinin biyolojik/sayısal riskleri D03'te karşılaştırıldı. Öğrenilen token dizi özelliği değildir; sıfır gerçek AAC/DC değildir. Context için yeni veri indirilmedi, hedef ilişkisi uydurulmadı.

## Etiketler: kayıpsız hedef deposu, nihai seçim yok

{table(read('label_strategy_comparison.csv'))}

WP03 geniş dosya 64 ilaç/6616 çift taşır; açık `conservative=True` filtresiyle onaylı 62 ilaç/6416 çift alındı. Filtre ve kimlik kümesi bağımsız testte doğrulandı. Her çift unique(drug_id,pt_cui), durum `observed_positive`. Gözlenmeyen çiftler otomatik 0/negatif yapılmadı; yoğun unknown matrisi bile üretilmedi. Tarihsel kategori projeksiyonu yalnız QA'dır, yeni hedef deposu olarak kullanılmadı.

![Etiket stratejisi QA](figures/WP07/05_label_strategy_QA.png)

**Şekil yorumu:** 406 singleton ve 710 beşten az ilaç destekli PT, 62 ilaçta çok seyrek hedef uzayı oluşturur. İlaç başına PT sayısı yalnız QA; X veya güvenilirlik puanı değildir. Tarihsel 30'un daha yoğun olması semantik doğruluk kanıtı değildir. Sulfanilamide kategori projeksiyonunda sıfır pozitif taşır; 30 gerçek negatif taşıdığı söylenemez.

## Sızıntı denetimi ve değerlendirme protokolü

{table(read('leakage_audit.csv'))}

![Sızıntı sınırı](figures/WP07/06_leakage_boundary.png)

**Şekil yorumu:** İnceleme nesnesi tüm kohortu kapsar ve **doğrudan eğitim grafı olarak kullanılamaz**. `training_ready=False` ve kapalı eğitim kontrolü yardımcı korumadır; başka kodun veriyi kötüye kullanmasını mutlak olarak önlemez. Henüz eğitim hattı olmadığı için uçtan uca gelecek sızıntısızlık iddiası yoktur.

Gelecekte train grafında test ilaç düğümleri ve bu ilaçların ileri/ters ilişkileri bulunmamalı. Paylaşılan harici protein/PPI bağlamının sabit mi fold'a özgü mü olacağı açık protokol kararıdır. Input ölçekleme, imputasyon, destek tabanlı etiket/özellik seçimi ve sınıf ağırlıkları train-only olmalı. Drug-disjoint zorunlu; oran/fold/seed atanmadı. Yakın yapı/parent/tuz varyantlarının gruplar arasında benzerlik etkisi ayrıca incelenmeli.

Unknown gerçek negatif değildir. PU varsayımı veya unknown=0 kayıt-tahmin proxy değerlendirmesi ancak açık kararla seçilir. AUROC/AUPRC, sınıf desteği, hesaplanamayan sınıf sayısı ve ilaç/grup düzeyinde belirsizlik raporu planlandı; burada hiçbir başarım veya CI üretilmedi. Tüm ayrıntılar [karar raporundadır](WP07_DECISION_GATE.md).

## PPI encoder için ileride zorunlu kanıt

WP09 geliştirmesinde gerçek forward PPI komşuluğunu işlemeli. Deterministik küçük graf, ayırt edici komşu özellikleri ve kontrollü ağırlıklarla kenar/komşu değişiminin izinli reseptif alandaki temsili değiştirdiği sınanmalı; gradient/trace kontrolü eklenmeli. Her kenarın her koşulda çıktıyı değiştirmesi gibi yanlış bir test beklentisi yoktur.

Aynı onaylı split/preprocessing/seed altında protein-mean baseline, PPI yok, gerçek PPI ve organizma içinde karıştırılmış PPI ablation planı zorunludur. Eşik ve context duyarlılığı test sonuçlarına göre seçilmez. Bu encoder/test/deneyler bugün uygulanmadı; eski forward eksikliğinin giderildiği iddia edilmez, giderme ve doğrulama planı hazırdır.

## Çalıştırma, test ve görsel doğrulama

**{a['tests']['passed']}/{a['tests']['passed']} otomatik test geçti; {str(a['tests']['seconds']).replace('.',',')} saniye.** [Tam test kaydı](qa/WP07/test_results.txt). Gerçek kaynak QA ile kimlik/rol/maskeler, 62/141/63/23/80 ayrımı, 6416 pozitif, iki protein eksiği ve sekiz molekül QC bayrağı karşılaştırıldı. Kusur enjeksiyonunda hedef/ters hedef kenarı, yasak x/y/skor alanı, organizma karışması, aralık dışı indeks ve duplicate kenar reddedildi. Eğitim kapısı kapalıdır. Testlerde büyük kaynak içeriği okunmadı.

[Notebook](../notebooks/WP07_data_integration.ipynb) **8 çalıştırılmış kod hücresi, 6 gömülü PNG ve tam 62 ilaç tablosu** içerir; stderr/hata yok. Altı PNG görsel olarak kontrol edildi. [Çevrimdışı etkileşimli modalite HTML](figures/WP07/drug_modality_interactive.html) kimlik/ad/QC hover sunar; Plotly gömülüdür, canlı tarayıcı etkileşimi test edilmedi.

Ortam: Python 3.11.3, mevcut torch **{env['torch']}**, PyG **{env['pyg']}**. PyG başlangıçta yoktu; yalnız `.deps/pyg` içine kuruldu. İmport için eksik xxhash ve aiohttp ile zorunlu alt bağımlılıkları aynı dizine kuruldu; sistem paketleri değiştirilmedi. Tam sürümler [environment.json](qa/WP07/environment.json) içinde. Yeni biyolojik veri/API sorgusu yok. HeteroData depolama/doğrulama amacıyla kullanıldı; GNN katmanı/mesaj geçişi çalıştırılmadı.

## Dosyaların amacı

| Çıktı | Ne işe yarar? |
|---|---|
| notebooks/WP07_data_integration.ipynb | Kavram, gerçek tablo, şekil ve Türkçe bilimsel yorum |
| reports/WP07_DECISION_GATE.md | D01–D07 seçenekleri, değerlendirme ve PPI kanıt/ablation planı |
| review_contract.json | İnceleme sözleşmesi; nihai model şeması değil |
| heterodata_review_scenarios.pt | Altı doğrulanmış yapısal HeteroData; x/y yok, eğitim hazır değil |
| drug_nodes.csv, protein_nodes.csv, pt_audit_nodes.csv | Deterministik kanonik ID→indeks sözlükleri |
| typed_drug_protein_edges.csv, edge_counts.csv | Dört rolün kaynak kenarları ve senaryo sayımları |
| ppi_scenarios.csv, ppi_edge_provenance.csv | Katı/koşullu ağ ayrımı, eşik ve kaynak satır izi |
| drug_modality_QA.csv, modality_patterns.csv | Tam 62 ilaç, QC/maskeler ve modalite kesişimleri |
| context_inventory_no_features.csv | 80 ek proteinin özellik eksikliğini koruyan envanter |
| observed_pt_positives_external.csv | Kaynaklı, tekrarsız pozitif hedef deposu; encoder girdisi değil |
| label_strategy_comparison.csv, decision_options.csv | Nihai seçim yapmadan seçenekleri karşılaştırma |
| leakage_audit.csv, source_feature_missingness.csv | Yasak bilgi yolları ve kaynak alanların eksikliği |
| input_manifest.json, prior_outputs_hashes.json, artifact_validation.json | Tekrar üretim ve korunma kanıtı |
| scripts/wp07_integration.py | Kanonik indeks, kaynak şeması/kenar/organizmalar ve inceleme nesnesi doğrulaması |
| scripts/wp07_decisions.py, wp07_notebook.py, wp07_report.py | Karar, yürütülmüş notebook ve raporu yeniden üretme |
| tests/test_wp07.py, scripts/wp07_validate_artifacts.py | 25 otomatik test ve kapanış kontrolleri |

Tekrar üretim; ham Dataset erişimi yalnız son doğrulamanın stat kontrolü için gerekir, içerik taraması yapılmaz:

```powershell
python scripts/wp07_integration.py
python scripts/wp07_decisions.py
python scripts/wp07_notebook.py
python -m unittest discover -s tests -p test_wp07.py -v
# Test çıktısını reports/qa/WP07/test_results.txt olarak kaydettikten sonra:
python scripts/wp07_validate_artifacts.py
python scripts/wp07_report.py
```

Kaynakları açan eski üreticiler çalıştırılmaz. Yeni modül kişisel ham köke bağımlı değildir, proje kökünden QA okur. PyG nesnesi yalnız güvenilir yerel üretimden yüklenir; geçmiş `.pt` veya dış pickle çalıştırılmaz.

## Onay için açık kararlar

D01 hedef etiket; D02 eksik ilaç modalitesi; D03 context temsili; D04 PPI kapsam/eşik; D05 drug-disjoint uygulama düzeni; D06 nihai giriş alanları; D07 unknown/PU varsayımları. Seçenek ve sonuçlar [karar raporunda](WP07_DECISION_GATE.md) incelenebilir. Şu anda hiçbirinin nihai değeri otomatik atanmadı.

**WP07 entegrasyon incelemesi tamamlandı; kullanıcı onayı bekleniyor. WP08'e geçilmedi.**
'''
    (ROOT/'reports/WP07.md').write_text(text,encoding='utf-8');print('Wrote WP07 report')


if __name__=='__main__': main()
