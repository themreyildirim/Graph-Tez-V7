"""WP08 Türkçe protokol/karar raporu: küçük QA'dan, eğitim çalıştırmadan."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP08'


def table(f):
    def fmt(x):return str(x).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','|'+'|'.join(['---']*len(f.columns))+'|']+
                     ['| '+' | '.join(fmt(v) for v in row)+' |' for row in f.itertuples(index=False,name=None)])


def main():
    read=lambda n:pd.read_csv(QA/n,keep_default_na=False)
    summary=json.loads((QA/'structure_audit_summary.json').read_text(encoding='utf-8'))
    valid=json.loads((QA/'artifact_validation.json').read_text(encoding='utf-8'))
    proposals=read('decision_proposals.csv')
    gate='''# WP08 — Tahmin ve değerlendirme protokolü: onay kapısı

06.11.2026 — **Yalnız protokol önerisi. D01–D07 nihai olarak sabitlenmedi; eğitim izni bekleniyor.**

## Öneri ve gerekçe tablosu

'''+table(proposals)+'''

## D01 — Hedef sözlüğü nasıl seçilmeli?

Kaynak PT CUI, kavram izini koruyan birincil temsil adayıdır; 1061 sınıfın hepsinin bağımsız ilaç gruplarında öğrenilebilir olduğu varsayılmaz. Tarihsel 30 sabit bir ikincil karşılaştırma olabilir; anlam daralma/birleşme sorunları çözülmüş sayılmaz. Klinik alt küme, kaynak PT/CUI ve kapsam gerekçeleriyle uzman tarafından önceden onaylanmadan uydurulmaz. `clinical_subset_review_queue.csv` yalnız 30 mevcut kavramın onaysız inceleme kuyruğudur.

Prosedür önerisi:

1. Tahmin hedefi önce açık yazılır: bilinen/benzer kimyasal ailelerden yeni ilaç mı, yoksa yeni scaffold ailesi mi? Kaynak kayıt ilişkisini sıralamak ile biyolojik yan etki olasılığı aynı hedef değildir.
2. Yapısal gruplar yalnız girdiden oluşturulur; outer split tanımı/seed ve hedef sözlüğü seçim **kuralı** test etiketleriyle optimize edilmeden dondurulur. Bütün 62'nin frekansları QA'dır; nihai sınıf listesi değildir.
3. Her outer train içinde tekil pozitif ilaç ve pozitif grup desteği hesaplanır. 3/5/10 ilaç ve >=2 pozitif grup yalnız operasyonel aday eşiklerdir; klinik eşik veya ampirik en iyi değer iddiası yoktur. Hangisi kullanılacaksa gerekçesiyle önceden onaylanır. Seyrek sınıfları eleyerek AP'yi yükseltmeye göre eşik seçilmez.
4. Inner CV'de veriyle öğrenilen uygunluk yalnız inner train içinde yeniden hesaplanır; outer train'den gelen sınıf desteği bile inner validation'a sızdırılmaz. Her foldun öğrenilebilir hedef kapsamı saklanır. Outer test için son sözlük yalnız outer train'de belirlenir, sonra sabitlenir.
5. Outer test pozitifleri sözlüğü değiştirmez. Sözlük dışı pozitif kapsamı ve metriği hesaplanamayan sınıflar ayrı raporlanır. Farklı sözlüklerle aynı metrik adı altında tek bir kıyas yapılmaz: ortak hedef kapsamı ve toplam kapsama oranı birlikte sunulur. Pooled out-of-fold micro toplamada hangi çift/sınıfın değerlendirildiği açık kaydedilir; kapsamı değiştiren hedef eşiği hiperparametresi başarıma göre optimize edilmez.
6. Uzman sabit sözlük seçeneğinde kavramlar performansa bakılmadan dondurulur; train'de hiç pozitif olmayan hedefler için destek/yetersizlik politikası ayrıca yazılır. Klinik alt kümenin bağımsız semantik inceleme statüsü korunur.

Önceki WP03–WP07 keşiflerinde tüm 62 ilacın etiketleri incelendi. Bu bilgi geri alınamaz. Yukarıdaki teknik sınırlar yeni fit/selection sızıntısını önler; gelecekteki sonuçları “hiç incelenmemiş bağımsız test” yapmaz. Doğru tanım: keşfedilmiş küçük kohortta önceden kayıtlı kurallarla **iç doğrulama**, sonrasında uygun izinle bağımsız doğrulama gereksinimi. Bu WP'de yeni kaynak eklenmedi.

## D02 — Maskeli yaklaşım ve kapsama

Birincil aday, mevcut input modaliteleri için ayrı dallar ve girdi kaynaklı availability maskeleridir. Kimya için 54 QC-onaylı satır, protein için 60 ilaç bulunur. Sekiz kimya incelemesi ve iki protein eksiği korunur; 62'den ilaç silinmez. Complete-case 53 ilaç yalnız duyarlılık alt grubudur. Maskeli ve complete-case performansları aynı estimand değildir; ayrıca aynı 53'lük değerlendirme alt kümesinde eşleştirilmiş karşılaştırma ve tüm-62 kapsam raporu gerekir.

Boş protein rolü için üretilen “toplama yok” değeri gerçek protein özelliği değildir. Gating ya da öğrenilmiş missing token onaylanırsa istatistiksel temsil olarak açık yazılır; amino asit vektörü doğrulaması sanılmaz. Alternatif kimya imputasyonu yalnız train'de fit, bağımsız input maskesiyle ve QC bayrağını değiştirmeden uygulanabilir; burada gerçek ilaçlarda yapılmadı.

Tobramycin kimya dalıyla değerlendirilebilir adaydır. Methenamine'de temiz kimya ve protein birlikte yok: bu durumda “62 ilaç korundu” ile “62 kişiye özgü tahmin yolu var” aynı değildir. Öneri **abstention/kapsam dışı tahmin** durumunu ana raporda açık göstermek; ortak train önselini yalnız kişiselleştirilmemiş baseline alternatifi olarak ayrı tutmaktır. Bu bir kohorttan silme kararı değildir. QC incelemesi çözülmeden ham kimya clean tablo yerine geçirilmez. Fallback/abstention tercihi kullanıcı onayı ister.

## D03–D04 — Context ve PPI

Başlangıç B1/B2 için 80 özelliksiz context'i kullanmamak önerilir. Böylece sıfır vektörün gerçek protein kimyası gibi yorumlanması önlenir. Maliyeti bazı bağlantı ve yolların kaybıdır; WP06 insan 700 örneğinde seed 63 düğüm/184 çift/12 izole, geniş ağ 103/372/7'dir. Düğüm paydaları farklıdır, bu performans karşılaştırması değildir.

PPI'sız B1/B2 ve yalnız katı aynı-taxID 63 insan proteiniyle ileride PPI varyantı ayrı kalır. 23 K12/MG1655 inceleme proteini ana PPI'ye eklenmez; diğer proteinler PPI yok diye elenmez. 150/400/700/900 filtreleri alternatiflerdir; 700 yalnız görsel örneği. WP08'de PPI encoder veya onun eşiğini başarımla seçme yapılmaz.

WP09 için forward gerçekten PPI edge_index'i işlemeli; deterministik ayırt edici komşu/kenar testi ve gerektiğinde gradient/trace denetimi gerekir. Aynı onaylı split/fit/seed altında PPI yok, gerçek PPI, organizma içinde karıştırılmış PPI ve protein-mean baseline ablation planı korunur. Bir kenarın her rastgele ayarda her çıktıyı değiştirmesi beklentisi doğru test değildir. Bu çalışmalar başlamadı.

## D05 — Hangi genelleme sorusu ve hangi bölme?

- Zorunlu asgari: drug-disjoint; aynı parent/kimlik ve bağlantı yapısına ait stereo varyantları aynı grup. Levofloxacin/Ofloxacin örneği 62 primary ID'yi 61 connectivity grubuna indirir. Tuz/ikincil ID tabloları aynı parent'a çözülür; tuz satırı ayrı örnek değildir.
- Benzer ailede yeni ilaç sorusu için connectivity gruplu nested CV bir adaydır. Bu, yeni scaffold ailesine genelleme iddiası taşımaz; yüksek çapraz-fold benzerlik ayrıca raporlanır.
- Daha katı yeni-yapı sorusu için scaffold veya Morgan>=0,8 kenarlarının birleşimindeki 40 grup adaydır; 0,7/0,9 duyarlılığıyla etkisi raporlanır. 0,8 evrensel bilimsel eşik değildir. Aynı basit scaffold farklı antibakteriyel aileleri gruplayabilir; transitive bileşenlerde tüm üyeler birbirine yüksek benzer olmak zorunda değildir. Sekiz QC incelemesi gruplama belirsizliğini de taşır.
- Önerilen **çatı**, tek 80/20 satır ayrımı yerine grup ayrık nested CV'dir. Dış 3/5 ve iç 3 seçenekleri, 62 örnekte train/test büyüklüğü ve hesap maliyeti açısından karşılaştırılır. Dış 5 daha büyük train ama daha küçük ve değişken destekli test bırakır; dış 3 tersi. Fold sayısı seçilmedi. Tek dış test + iç grup CV de yöntemsel olarak mümkündür, fakat küçük test ve tek bölme varyansı açıkça raporlanmalı.
- Mevcut label-free boyut yerleştirmesi 3 fold için 21/21/20, 5 için 13/13/12/12/12 verir. Bunlar ilaç-foldu atanmış gerçek split değildir. Destek sıklığına göre tekrar tekrar seed seçmek test tasarımını iyimserleştirir; yapılmayacak.
- Stratifikasyon tek grupta pozitif kalan PT'ye iki bağımsız grupta pozitif yaratamaz. Önceden belirlenen grup kuralı altında destek yetersizliği NA/kapsam olarak kabul edilir; metrik hesaplanabilir olsun diye test yeniden seçilmez.

Onayda belirlenmesi gereken: genelleme hedefi (yeni ilaç/yeni scaffold), ana grup kuralı, dış/inner fold sayısı, tekrar/seed politikası ve destek/abstention kuralları. Burada gerçek split ID'leri kaydedilmedi.

## D06 — Sürümlü giriş ve train-only fit sözleşmesi

`input_contract_v0_1_DRAFT.json` ve alan tablosu öneridir. 5 kimya alanı (MW,LogP,HBD,HBA,TPSA), 56 dizi özelliği ve dört ayrı DrugBank rolü kaynak sürümleriyle korunur. DrugBank/CID/accession/taxID/source hash/inceleme bayrakları join/provenanstır; sayısal ID embedding veya ezberleme girdisi yapılmaz. PT/kategori/has_pt/sınıf sıklığı/raporlama skoru/kalite_skoru yasak girdidir. STRING combined_score protein özelliği değildir.

Her foldun kimya dönüşümü yalnız eğitim ilaçları ve kullanılabilir inputlar üzerinde fit edilir. Protein dönüşümü **train ilacı ilişkilerindeki benzersiz accession** kümesinde fit edilir; protein tekrarlarının sayısı yüksek dereceli düğümlere gizli ağırlık vermesin. Aynı dönüşüm validation/testteki bilinen veya yeni proteinlere uygulanır; yeniden fit yapılmaz. Gruplar, train IDs, kaynak hash'leri, feature sırası, maske tanımları ve fit accession'ları provenance'da kaydedilir.

Rol başına protein ortalaması bir B2 adayıdır; target/enzyme/transporter/carrier birleştirilmez. 56 özelliğin AAC/grup/DC alanları bağımlılık içerir; küçük örneklemde yüksek boyut ve düzenlileştirme gereksinimi vardır. Özellik seçimi/PCA gibi öğrenilen işlemler yalnız train içinde kalır. Bu WP'de gerçek özellik matrisi, imputasyon, scaler fit'i veya model yok.

ROADMAP B1 için +ATC içerir. Bu talepte ATC girişi otomatik onaylanmış sayılmaz. Mevcut WP02 J01 etiketleri kaynak QA'sı olarak var; eski sıfır one-hot kopyalanmaz. B1 kimya-only ile B1+ATC varyantı, ATC düzeyi ve sabit hiyerarşi mi train vocabulary mi kullanılacağı ayrı onaya sunulur. Yeni veri gerektirmez.

## Eğitim grafı güvenlik sınırı

WP07 altı inceleme `.pt` dosyası yüklenip train grafı yapılmaz. `new_partition_graph` yalnız split sonrası train drug ID'lerini ve onların dört rol kenarını seçen yeni üreticidir. Test/validation ilaç düğümleri, onların hedef/ters kenarları ve hiçbir SE hedef düğümü/kenarı eğitimde yer alamaz. WP08'de bu üretici yalnız sentetik ve tek ilaçlık gerçek sınır testinde kullanıldı, üretim split/graf dosyası kaydedilmedi.

Protein evreni ayrı açık parametredir:

1. `train_linked_only`: başlangıç için önerilen daha katı indüktif kapsam. Yalnız train ilacı kaynak ilişkilerinde görülen proteinler; ileride PPI bu kümede induced alınır. İnferansta test ilacı kendi etiketsiz ilişkileri/dizileriyle ayrı query kopyasına eklenebilir; train grafına geri mesaj taşınmaz. Aynı testteki diğer ilaçları ekleyip çapraz query mesajı vermek ayrı transdüktif varsayım olur.
2. `fixed_registry_review`: 141 mevcut proteinlik evren, hiçbir heldout ilaç düğümü/kenarı olmadan sabit bağlam. Ancak 141 protein başlangıçta tüm 62 ilaç üzerinden seçildi; bu yüzden “tamamen bağımsız dış protein evreni” denmez. Train-linked proteinlerle fit edilmiş dönüşüm yine korunur; bu kapsamın transdüktif yönü açık raporlanır. 80 context yine yoktur.

PPI verilirse yalnız kaynak taxID=9606 ve katı insan accession allowlist'i kabul edilir; K12/context veya caller'ın taxID kanıtıyla çelişen listesi reddedilir. Eğitim grafında PPI depolamak forward kullanımını kanıtlamaz; WP09 sınırı sürer.

## D07 — Pozitif–etiketsiz görev ve metriklerin anlamı

SIDER'da gözlenen `s=1`, gizli biyolojik gerçek `y=1` ile özdeş değildir. `s=0` kaydı olmayan çifttir. PU'nun yaygın “etiketli pozitifler doğru” varsayımı bile burada deneysel nedensellik doğrulaması değildir; kaynak ilişki pozitifi olarak kabul edilir. İlaç başına kayıt sayısı hasta paydası, olay sayısı veya güvenilirlik değildir.

'''+table(read('metric_interpretation.csv'))+'''

Öneri: tez deneyinin erişilebilir estimand'ını **kaynakta gözlenen ilaç–yan etki ilişkilerinin sıralanması** olarak sınırlamayı değerlendir; klinik yan etki risk tahmini gibi sunma. Kullanıcı onaylarsa observed-label AP/AUROC, unknown'ı vekil referans olarak kullandığını açıkça bildirerek hesaplanabilir. Bu bilimsel negatif doğrulaması değildir. Gerçek PU loss/düzeltme istenirse sınıf önseli/etiketlenme eğilimi ve duyarlılık planı ayrıca onaylanmalı; 62 ilacın gözlenen pozitif oranı gerçek class prior değildir. SCAR (pozitiflerin rastgele etiketlenmesi) veya SAR (özelliklere bağlı etiketlenme) SIDER için bu dosyalardan doğrulanamaz.

Micro sık sınıflarca baskılanabilir, macro seyrek sınıflarda kararsızlaşır. Her sınıfın train/test gözlenen desteği, hesaplanabilen sınıf sayısı, kapsam dışı hedefler ve ilaç başına sonuç kapsamı birlikte sunulmalı. All-positive proxy sınıfta AUROC tanımsızdır; AP'nin araçça üretilebilmesi ayırt edici test anlamına gelmez, ayrı işaretlenmeli. AP ve trapez PR-AUC aynı hesap değildir; yöntem adı, average ayarı ve aday çift evreni önceden kaydedilmeli.

Belirsizlik için ileride ilaç/yapısal grup düzeyinde paired bootstrap ve aynı foldlarda yöntem kıyası adaydır. Pooled OOF çıktıları aynı hedef uzayını kullanıyorsa yorumlanabilir; foldlar arasında öğrenilmiş farklı sözlükler/kapsamlar ayrıca bildirilir. Sabit OOF tahmin bootstrap'ı eğitim belirsizliğinin tamamını kapsamaz; fold skorlarını bağımsız 5 gözlem gibi t CI'ya sokmak veya çiftleri bağımsız bootstrap etmek yeterli değildir. Gerekirse tüm fit sürecini tekrarlayan grup örnekleme/tekrarlı iç doğrulama maliyeti ayrıca kararlaştırılır. Bugün CI/başarım/negatif örnek yoktur.

## Karar kapısının somut sonucu

Önerilerin hiçbirinde `APPROVED_BY_USER` durumu yoktur. Onay gerektiren çekirdek seçimler: PT/klinik/kategori hedef yolu ve destek kuralı; maskeli dal ve Methenamine abstention/fallback; ana grup kuralı ve CV düzeni; 5/56+maskeler ve isteğe bağlı ATC; proxy kayıt-sıralama mı açık varsayımlı PU mu. Context dışarıda ve K12 ayrı kalması önerinin kapsam korumasıdır; PPI eşiği seçilmez. Yeni model eğitimi için ayrıca açık talimat gerekir.

## Yöntem kaynakları

[RDKit Morgan generator API](https://www.rdkit.org/docs/source/rdkit.Chem.rdFingerprintGenerator.html) fingerprint ayarlarını; [Murcko API](https://rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html) scaffold çıkarımını belgeler. [Scikit-learn veri sızıntısı](https://scikit-learn.org/stable/common_pitfalls) train-only dönüşüm sınırını, [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html) grup ayrıklığını açıklar. [Jain, White ve Radivojac (2017)](https://arxiv.org/abs/1702.00518) PU koşullarında klasik performansın neden yanlı olabildiğini ve düzeltmede önsel bilgisinin rolünü inceler. [Metrik tanımları](https://scikit-learn.org/stable/modules/model_evaluation.html) AP/AUROC hesaplarının referansıdır. Bunlar yöntem kaynaklarıdır; yeni biyolojik veri seti eklenmedi.
'''
    (ROOT/'reports/WP08_PROTOCOL_DECISION_GATE.md').write_text(gate,encoding='utf-8')
    support=read('support_feasibility_QA.csv');support=support[support.method.isin(['primary_drug_only','connectivity_guard','scaffold_or_similarity_0.8'])]
    text=f'''# WP08 — Protokol keşfi ve metodoloji karar incelemesi

06.11.2026 — **WP08'in istenen karar öncesi protokol incelemesi tamamlandı; metodoloji/eğitim onayı bekleniyor.** WP07 onaylandı. ROADMAP WP08'in gerçek split, baseline eğitim ve AUROC/AUPRC CI deneyleri bu incelemede yapılmadı; son kullanıcı talimatı doğrultusunda yöntem kararı önce onaya sunulur. WP09 başlamadı.

## Sonuç ve öneri

62 ilaçlık kohort korunarak hedef, gruplama, eksik modalite ve PU değerlendirme seçenekleri gerçek kayıtlardan incelendi. Birincil yaklaşım adayı **input modalite maskeleriyle kohortu korumak**, bağlanma/metabolizma/taşıma rollerini ayrı tutmak ve etiket körü yapısal gruplarla nested iç doğrulama çerçevesidir. Nihai hedef sınıfları, grup/eşik/CV/seed, fallback veya loss/metrik varsayımı sabitlenmedi. [Ayrıntılı karar kapısı](WP08_PROTOCOL_DECISION_GATE.md) uygulamaya geçmeden onaylanması gereken seçenekleri açıklar.

**Önemli sınır:** Tüm 62 ilacın etiketleri önceki keşiflerde incelendi. Sonradan ayrılacak test, temiz teknik fit sınırlarıyla korunabilir; hiç incelenmemiş bağımsız dış test gibi sunulamaz. Sonuçlar bu veriyle yapılacak iç doğrulama olarak adlandırılmalıdır.

## Bütünlük ve kullanılan kaynaklar

WP07'nin 317 önceki dosyalık manifesti başlangıçta doğrulandı. WP00–WP07'nin **{summary['prior_files_verified']} dosyası** yeni başlangıç manifestine alındı; kapanışta tamamı aynı SHA-256 ile bulundu. Önceki kimlikler, testler, raporlar, notebook'lar ve QC kararları değiştirilmedi. Güncel `run_status.md` bu manifestin dışındadır. Sekiz önceki paket raporu mevcut; eski testler yeniden koşturulmuş sayılmaz.

Girdiler yalnız mevcut proje QA dosyaları: WP02 parent/tuz/ikincil ID; WP03 hamdan doğrulanmış pozitifler/tarihsel projeksiyon/semantik bayraklar; WP04 kaynak SMILES/kimlik/clean özellik/QC; WP05 registry/dizi özellik/rol kenarları; WP06 mapping/metrik/kenar; WP07 modalite envanteri. **{valid['input_manifest.json']['count']} küçük girdi hash'i** kaydedildi. XML/SIDER/STRING içerikleri veya kapsam dışı kaynaklar okunmadı. Altı ham kaynakta yalnız boyut/mtime aynı bulundu; bu içerik hash'inin yeniden doğrulanması değildir. Yeni indirme, API veya paket kurulumu yok.

Kaynak sürümleri WP02–WP06 provenansıyla korunur: DrugBank XML 5.1, export 2026-01-04; SIDER 4.1; STRING v12.0. RDKit **{summary['rdkit_version']}** mevcut `.deps/rdkit` kurulumundan kullanıldı. PyG yalnız sınır testinde mevcut `.deps/pyg` üzerinden yeni geçici nesne doğrulaması için kullanıldı; WP07 `.pt` yüklenmedi. Ne model encoder'ı ne mesaj geçişi çalıştı.

## D01 — Etiket seçeneklerinin gerçek kapsamı

{table(read('label_options.csv'))}

Kaynak PT'de 406 singleton, 710 beşten az ilaç destekli sınıf; tarihsel 30'da 7–61 ilaç desteği var. Klinik anlamlı alt küme henüz uzman onaylı olmadığı için sınıf sayısı **tanımsız** bırakıldı. Mevcut 30 kavramın kaynak PT/CUI ve anlam incelemesi ayrı kuyruğa kopyalandı; bu bir klinik doğrulama veya yeni kategori tanımı değildir. Aynı PT'lerin kategoriye birleşmesi kapsam ve anlamı değiştirebilir.

![Etiket seçenekleri](figures/WP08/01_label_options.png)

**Yorum:** Daha yoğun tarihsel etiket uzayı daha kolay metrik verebilir; klinik doğruluğunu kanıtlamaz. PT'leri tüm 62'nin sıklığına bakarak seçmek gelecek test etiketlerini seçimde kullanır. Önerilen sözlük fonksiyonu train ID'leriyle filtreledikten sonra destek hesaplar. Heldout etiketleri değiştirildiğinde seçimin değişmediği mutasyon testi geçti. 3/5/10 ve >=2 grup yalnız onay bekleyen kural seçenekleridir; gerçek train vocab oluşturulmadı.

## D05 — Yapı, tuz ve grup sızıntısı

62 mevcut kaynak SMILES üzerinde **1891 farklı çift** incelendi. Fingerprint Morgan radius=2, 2048 bit, includeChirality=False; Tanimoto yalnız gruplama QA'sıdır. Yeni öğrenme özelliği değildir. Tam InChIKey ve CID tekrarı **0**; aynı bağlantı/nonisomeric yapıya ait çift **1**: **Levofloxacin–Ofloxacin**. Bu çiftin stereo dışı Tanimoto'su 1'dir; tam kimyasal veya klinik eşdeğerlik sonucu çıkarılmaz. Kimlik kilidi olmayan drug-disjoint ayrımda bu benzerlik test zorluğunu etkileyebilir.

WP02'de onaylı 62 parent'a bağlanan **99 tuz** ve **63 ikincil ID** kanıtı var; bunlar 162 ek ilaç değildir. Canonical ana ilaç ID'leri korunur. Tuz/parent ilişkisi kimyasal parent standardizasyonuyla otomatik aynı şey sayılmadı; nötralizasyon veya fragment/stereo değişikliği yapılmadı. Salt kayıtlarından başka ana ilaçların klinik eşdeğer olduğu sonucu çıkarılmaz.

{table(read('group_summary.csv'))}

![Yapı benzerliği](figures/WP08/02_structure_similarity.png)

**Yorum:** İsimden veya yalnız ID farklılığından bağımsız yapı benzerliği görünür. Parmak izi bit çakışmaları, stereo dışı temsil, büyük/karışım yapıları ve sekiz QC incelemesi yorum sınırıdır. RDKit Murcko türevi kaynak molekülü ezmez; tam yapı model için basitleştirilmedi. Boş scaffold bu 62'de 0; kodda boş scaffold'lar tek gruba birleştirilmez ve sentetik testle doğrulanır.

![Grup seçenekleri](figures/WP08/03_grouping_candidates.png)

**Yorum:** Connectivity 61, scaffold 41, scaffold veya >=0,8 benzerlik birleşimi 40 aday grup verir; en büyük birleşim grubu 5 ilaçtır. Benzerlik 0,7/0,8/0,9 sonuçları **49/56/59 grup**; eşik performansla seçilmedi. Scaffold eşitliği 34 çiftte görülür, basit fenil gibi ortak çekirdekler farklı aileleri birleştirebilir. Dolayısıyla yeni-ilaç ve yeni-scaffold değerlendirmeleri farklı genelleme sorularıdır; karar dosyasında ayrı ele alınır.

## Split fizibilitesi ve sınıf desteği

{table(read('split_size_feasibility.csv')[['method','hypothetical_k','fold_size_vector_only','largest_group']])}

Bu tablolar **yalnız grup büyüklüğü fizibilitesi**, gerçek split/fold ataması değildir. Üç fold daha büyük test (~20–21), beş fold daha büyük train (~49–50) sağlar. Kişisel seed/ID ataması yapılmadı; hedef desteğine bakarak seed arama yok. Sabit dış test+inner CV ile nested grup CV karşılaştırıldı; küçük örneklemde tek bölme varyansı ve sınıf desteği sınırlaması açıklanmıştır.

{table(support)}

![Grup destek sınırları](figures/WP08/04_group_support_limits.png)

**Yorum:** 1061 PT'nin 411'i connectivity, 416'sı scaffold+0,8 gruplamasında yalnız tek pozitif grupta kalır. Bu sınıflarda iki bağımsız grup tarafına pozitif dağıtılamaz. En az 5 pozitif gruba sahip olmak 5 foldun hepsinde pozitif garantisi değildir. Global QA destekleri train hedef seçiminin yerine geçmez; hesaplanamayan sınıflar NA/kapsam olarak raporlanmalıdır.

## D02 — 62 ilaç ve girdi modaliteleri

Kimya QC 54, inceleme 8; protein modalitesi 60, eksik 2. Kesişim **53**, yalnız duyarlılık alt grubudur. Dağılım: 53 iki modalite var; 7 yalnız protein; 1 yalnız kimya (Tobramycin); 1 ikisi de temkinli tabloda yok (Methenamine). Kohort 62 kalır. WP04 sekiz bayrak ve iki ilaçtaki protein eksiği kaynakla bire bir test edildi.

![Modalite kapsamı](figures/WP08/05_modality_retention.png)

**Yorum:** Birincil aday maskeli yaklaşım, missing'i gerçek protein/kimya sıfırına çevirmez. Methenamine için abstention veya ortak train önseli gereklidir; bunun kişiselleştirilmiş biyolojik tahmin olmadığı açık kalır. Böylece örnek ID'sini korumakla tahmin kapsamını korumak ayrılır. Complete-case kıyası aynı alt grupta eşleştirilmiş duyarlılık olarak tasarlanmalı; ana kohorttan ilaç atılmaz.

## D03–D04 — Context ve PPI kapsamı

80 context proteininin doğrulanmış amino asit özellikleri yok; başlangıç modelinden ayrı tutulması önerilir. Sıfır dolgu, accession eşleme veya yeni DrugBank hedefi oluşturulmadı. PPI olmayan proteinler dizi dalında kalır. 63 aynı-taxID insan ve 23 K12/MG1655 inceleme kaydı birleşmez. WP08 B1/B2 adayı PPI'sızdır; gerçek PPI varyantı WP09'da kontrollü ayrı deneydir.

![Context'in topolojik etkisi](figures/WP08/06_context_topology_cost.png)

**Yorum:** İnsan 700 örneğinde 184 seed çiftine karşı 372 geniş ağ çifti ve 12'ye karşı 7 izole var; 63 ve 103 düğüm paydaları farklı. Context'siz ağın bağlantı maliyetini gösterir, model faydasını veya 700'ün en iyi eşik olduğunu kanıtlamaz. 150/400/700/900 seçenekleri korunur.

## D06 — Girdi ve graf güvenlik sınırı

Taslak **WP08-input-v0.1-DRAFT**: 5 kimya, 56 protein özelliği, dört ayrı rol ve input kaynaklı availability maskeleri; kimlik/provenans alanları X dışında. `input_fields_v0_1_DRAFT.csv` her alanın kaynağı, kimliği, fit kapsamı ve eksik anlamını listeler. Kimya clean alanlarının her birinde 8/62 (%12,90) bekletilmiş değer, protein alanlarının her birinde 0/141 eksik var; 80 context için hiçbir dizi vektörü yok. Maskeler bu eksikliği gözlemlenmiş sıfıra dönüştürmez.

İlaç ID/CID/UniProt/taxID sayısal ezberleme özelliği değildir. PT/kategori/has_pt/sıklık/raporlama skoru/kalite_skoru model girdisi olmaz. Kimya scaler'ı yalnız train drug; protein scaler'ı yalnız train-linked **benzersiz accession** üzerinde fit edilir. Fold feature seçimi/ATC vocabulary/weighting de train-only. AAC/grup/DC bağımlılığı ve küçük örneklemde boyut baskısı açıkça tartışıldı. ROADMAP'teki +ATC varyantı otomatik eklenmedi; kaynak seviye ve encoding onay bekler.

`new_partition_graph` WP07 `.pt` okumaz; train ID'lerinden **yeni** nesne kurar. Validation/test ilaçları ve dört rol bağlantıları eğitim grafına girmez; hedef/ters hedef SE veya ters drug kenarı kabul edilmez. Protein evreni `train_linked_only` veya `fixed_registry_review` olarak açık parametre ister. Sabit 141 registry tüm 62 ilaçtan elde edildiği için tam bağımsız dış evren gibi adlandırılmaz. Bu seçeneğin transdüktif etkisi ayrıca belirtilir; test bağlantıları üzerinden scaler fit edilmez.

Sınır testleri sentetik graf ve bir gerçek ilaçlık mekanik probe ile yapıldı; bunlar veri bölmesi/üretim train grafı değildir. Yeni eğitim `.pt`, x/y veya gerçek fit/scaler dosyası oluşturulmadı. İleride query ilaç etiketsiz girdisiyle ayrı inferans grafına eklenmeli; train'e geri mesaj ve query'ler arası transdüksiyon politikası açık yazılmalıdır.

![Protokol sınırı](figures/WP08/07_protocol_boundary.png)

**Yorum:** Hedefe göre seçim ve öğrenilen dönüşümler yalnız train tarafındadır. Heldout etiket mutasyonu, train-only fit-ID reddi, rol/ters kenar reddi ve kaynak taxID ile PPI doğrulaması test edildi. Bu kontroller henüz var olmayan gelecekteki trainer'ın uçtan uca sızıntısız olduğunu garanti etmez; sonraki eğitimde aynı sınırlar yeniden sınanmalıdır.

## D07 — Hangi metrik neyi ölçer?

{table(read('metric_interpretation.csv'))}

Unknown hiçbir yerde gerçek negatif etiketlenmedi, negatif örnek oluşturulmadı. AP/AUROC/Recall@k/PU düzeltme/CI seçenekleri varsayım ve anlamlarıyla karşılaştırıldı; değerleri hesaplanmadı. Proxy kayıt sınıflaması onaylanırsa pozitif/unknown karşılaştırmasının klinik negatif doğrulaması olmadığı açık yazılmalıdır. SCAR/SAR ve gerçek sınıf önseli mevcut SIDER kaydından doğrulanmış sayılmaz.

Micro/macro yanında fold sınıf desteği ve hesaplanabilir sınıf kapsamı gerekir. AP, trapez PR-AUC ile aynı değildir. Gelecekte ilaç/grup bootstrap, ortak split üzerinde paired kıyas ve eğitim belirsizliğinin sınırları raporlanmalıdır; çiftler bağımsız sayılmaz. Fold başına değişen hedef sözlüğüyle kapsamı belirtmeden metrik kıyaslamak yanıltır. Karar dosyası bu protokol ayrıntılarını içerir.

## Testler ve çıktılar

**{valid['tests']['passed']}/{valid['tests']['passed']} test geçti; {str(valid['tests']['seconds']).replace('.',',')} saniye.** Test çıktısında mevcut torch/PyG importundan `torch.jit.script` deprecation uyarısı var; başarısız test değildir. Büyük kaynak veya önceki testler yeniden çalıştırılmadı.

Test kapsamı: önceki/girdi hash'leri; 62 kimlik ve sekiz QC; 1891 pair tekilliği; stereo varyant kilidi; tuz/ikincil ID; transitif/boş scaffold politikası; aday grup kısıtları ve büyüklük toplamı; drug/group ayrıklığı; heldout etiket mutasyonuna dayanıklı train vocab; train-only scaler ve tamamen eksik alan reddi; heldout drug/rol/ters kenar reddi; gerçek kaynak taxID ile PPI koruması; 6416/1011 kaynak sayımı; context/K12/eksik modalite ve kapalı eğitim kararı; notebook/HTML doğrulaması. [Tam kayıt](qa/WP08/test_results.txt).

[Notebook](../notebooks/WP08_prediction_protocol.ipynb) **9 çalıştırılmış kod hücresi, 7 gömülü PNG ve tam 62 satırlık gerçek tablolar** içerir; hata/stderr yok. Yedi PNG görsel olarak kontrol edildi. [Çevrimdışı yapı benzerliği HTML](figures/WP08/structure_similarity_interactive.html), ilaç kimlik/ad/benzerlik hover sunar; canlı tarayıcı testi yok. Bunlar bilimsel QA görselleridir, tahmin sonuçları değildir.

| Çıktı | Amaç |
|---|---|
| reports/WP08_PROTOCOL_DECISION_GATE.md | D01–D07 önerileri, onay seçenekleri, fit/target/PPI/PU sınırı |
| notebooks/WP08_prediction_protocol.ipynb | Açıklamalar, kod altında tablolar ve yorumlu 7 görsel |
| structure_grouping_evidence.csv, pairwise_structure_similarity.csv | 62 yapı, QC ve 1891 benzerlik karşılaştırması |
| shared_structure_pairs.csv, group_candidates.csv, group_summary.csv | ID/stereo/scaffold ilişkileri ve onaysız grup seçenekleri |
| split_size_feasibility.csv | Sadece büyüklük fizibilitesi; gerçek split yok |
| cohort_salt_parent_evidence.csv, cohort_secondary_parent_evidence.csv | Mevcut ana ilaç kimliğine bağlı kaynak ID ilişkileri |
| class_frequencies_QA.csv, class_group_support_QA.csv, support_feasibility_QA.csv | Tam kohortta betimleyici destek; train seçimine giremez |
| label_options.csv, clinical_subset_review_queue.csv | Hedef seçenekleri ve onaysız klinik anlam kuyruğu |
| drug_modality_QA_preserved.csv, context_topology_cost_QA.csv | Önceki QC/modalite ve context kapsamını koruma |
| input_contract_v0_1_DRAFT.json, input_fields_v0_1_DRAFT.csv | Kaynaklı 5/56 alan, maskeler ve metadata taslağı |
| protocol_proposal.json, decision_proposals.csv, metric_interpretation.csv | Onay bekleyen metodoloji ve ölçüm semantiği |
| input_manifest.json, prior_outputs_hashes.json, artifact_validation.json | Tekrar üretim/bütünlük ve kontrol sınırı |
| scripts/wp08_structure_audit.py, wp08_analysis.py | Etiket körü yapı gruplama ve betimleyici seçenek hesapları |
| scripts/wp08_protocol.py | Train vocab/preprocess/graf sınır yardımcıları; trainer içermez |
| scripts/wp08_notebook.py, wp08_validate_artifacts.py, wp08_report.py | Çalıştırılmış çıktı/görsel/kapanış/rapor üretimi |
| tests/test_wp08.py | 28 otomatik kontrol; önceki testler değişmez |

Tekrar üretim: `python scripts/wp08_structure_audit.py`, `python scripts/wp08_analysis.py`, `python scripts/wp08_notebook.py`; ardından `python -m unittest discover -s tests -p test_wp08.py -v` test çıktısı QA'daki test_results.txt dosyasına kaydedilir; son olarak `python scripts/wp08_validate_artifacts.py` ve `python scripts/wp08_report.py`. Yeni modüller ham içerik/Drive/API erişimi gerektirmez; kapanışta yalnız kayıtlı ham yol stat kontrolü vardır.

**WP08 protokol incelemesi tamamlandı. Nihai metodoloji ve eğitim kararları kullanıcı onayında; deneysel eğitim kısmı yapılmadı. WP09'a geçilmedi.**
'''
    (ROOT/'reports/WP08.md').write_text(text,encoding='utf-8');print('Wrote WP08 report and protocol decision gate')


if __name__=='__main__':main()
