# WP08 — Tahmin ve değerlendirme protokolü: onay kapısı

06.11.2026 — **Yalnız protokol önerisi. D01–D07 nihai olarak sabitlenmedi; eğitim izni bekleniyor.**

## Öneri ve gerekçe tablosu

| decision_id | topic | recommended_candidate | pending_approval | reason_or_limit |
|---|---|---|---|---|
| D01 | Etiket | Kaynak PT kimliğini koru; destek uygunluğunu her train içinde öğren; tarihsel 30 yalnız sabit ikincil karşılaştırma | 3/5/10 ilaç ve >=2 grup eşikleri seçenek; nihai eşik/klinik alt küme onayı yok | Global QA frekansları train sözlüğü seçemez; dış fold etiketleri seçim dışında |
| D02 | Eksik modalite | 62 ilaç, kaynak girdisinden maskeli dallar birincil aday; 53 complete-case yalnız duyarlılık | Gating/loss ve Methenamine fallback onayı gerekir | Gerçek AAC/MW eksikliği biyolojik sıfır değildir; tüm dallar yoksa train önseli veya abstain açıkça tanımlanır |
| D03 | Context | 80 özelliksiz STRING context başlangıç modeline alınmasın | Kullanıcı tercihiyle uyumlu öneri; nihai eğitim henüz yok | WP06 insan 700: seed 184 çift/12 izole, expanded 372/7; bağlantı kaybı model başarımı değildir |
| D04 | PPI | B1/B2 PPI yok; WP09 için yalnız katı insan PPI ayrı; K12 kapsamı ayrı beklesin | 150/400/700/900 seçenek; en iyi eşik seçilmedi | PPI/no-PPI ancak WP09 forward kanıtından sonra; WP08 PPI eğitimi yok |
| D05 | Bölme | Etiket körü connectivity kilidi; yapı-gruplu nested CV birincil aday; scaffold+benzerlik stres varyantı | Dış 3 veya 5 fold / iç 3 seçenekleri; scaffold vs identity genelleme hedefi onay bekler | 40 gruplu scaffold+0.8 aday; 62 zaten keşfedilmiş ilaçta iç doğrulama, bağımsız yeni test değil |
| D06 | Giriş | v0.1 taslak: 5 kimya, 56 dizi, 4 rol ayrı, kaynak kimlikleri metadata; input maskeleri | ATC isteğe bağlı yol haritası varyantı; encode seviyesi/train vocab onayı gerekir | Train-only kimya scaler; protein scaler yalnız train-linked benzersiz accession; ID/PT/QA skorları X değil |
| D07 | PU ve metrik | Gözlenen kayıt ilişkisi sıralaması ile biyolojik risk tahminini ayır; unknown bilimsel negatif değil | PU varsayımı/önsel belirsiz; proxy AP/AUROC ayrı onay gerektirir | SCAR/etiketlenme eğilimi SIDER için doğrulanmadı; klinik kalibrasyon/özgüllük iddiası yok |

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

| metric_or_goal | assumption | meaning | limitation |
|---|---|---|---|
| Observed-label AP (micro/macro) | s=1 kayıt, s=0 unknown vekil karşılaştırma; onay olmadan hesaplanmaz | Kayıt varlığını sıralama; biyolojik pozitif precision veya klinik AUPRC değil | AP adım ağırlıklı özet; trapez PR alanıyla aynı tanım değil |
| Observed-label AUROC | Aynı proxy s varsayımı ve iki gözlenen sınıf gerekli | Rastgele gözlenen pozitifin unknown üstünde sıralanması; gerçek negatif özgüllüğü değil | Pozitif/unknown hiç yoksa sınıf metriği NA; sıfır başarı sayılmaz |
| Known-positive Recall@k / ranking | Sabit k ve candidate sözlüğü, test pozitifleriyle tek son ölçüm | Bilinen pozitifleri yakalama; tüm gerçek yan etkilerin duyarlılığı değil | Eksik annotation recall ve ranking yorumunu sınırlar; k val içinde ayarlanır |
| PU-corrected ölçümler / nnPU loss | Pozitif etiket hatası, class prior ve SCAR/SAR/propensity varsayımları açık | Varsayımlar geçerliyse gizli y hakkında çıkarım; burada doğrulanmış değil | Class prior 62 ilacın kayıt oranı değildir; önsel duyarlılığı gerekir |
| Klinik kalibrasyon, özgüllük, bireysel risk | Temsili gerçek negatif ve olay/payda verisi gerektirir | Mevcut SIDER ilişkilerinden doğrulanamaz | Bu WP08 deneyi için hedeflenmez |
| CI / belirsizlik | Gelecekte ilaç veya yapısal grup düzeyinde örnekleme | Seçilmiş iç doğrulama örnekleminin belirsizliği | Çift düzeyi bootstrap bağımsızlık varsaymaz; CV fold skorları bağımsız örnek değildir |

Öneri: tez deneyinin erişilebilir estimand'ını **kaynakta gözlenen ilaç–yan etki ilişkilerinin sıralanması** olarak sınırlamayı değerlendir; klinik yan etki risk tahmini gibi sunma. Kullanıcı onaylarsa observed-label AP/AUROC, unknown'ı vekil referans olarak kullandığını açıkça bildirerek hesaplanabilir. Bu bilimsel negatif doğrulaması değildir. Gerçek PU loss/düzeltme istenirse sınıf önseli/etiketlenme eğilimi ve duyarlılık planı ayrıca onaylanmalı; 62 ilacın gözlenen pozitif oranı gerçek class prior değildir. SCAR (pozitiflerin rastgele etiketlenmesi) veya SAR (özelliklere bağlı etiketlenme) SIDER için bu dosyalardan doğrulanamaz.

Micro sık sınıflarca baskılanabilir, macro seyrek sınıflarda kararsızlaşır. Her sınıfın train/test gözlenen desteği, hesaplanabilen sınıf sayısı, kapsam dışı hedefler ve ilaç başına sonuç kapsamı birlikte sunulmalı. All-positive proxy sınıfta AUROC tanımsızdır; AP'nin araçça üretilebilmesi ayırt edici test anlamına gelmez, ayrı işaretlenmeli. AP ve trapez PR-AUC aynı hesap değildir; yöntem adı, average ayarı ve aday çift evreni önceden kaydedilmeli.

Belirsizlik için ileride ilaç/yapısal grup düzeyinde paired bootstrap ve aynı foldlarda yöntem kıyası adaydır. Pooled OOF çıktıları aynı hedef uzayını kullanıyorsa yorumlanabilir; foldlar arasında öğrenilmiş farklı sözlükler/kapsamlar ayrıca bildirilir. Sabit OOF tahmin bootstrap'ı eğitim belirsizliğinin tamamını kapsamaz; fold skorlarını bağımsız 5 gözlem gibi t CI'ya sokmak veya çiftleri bağımsız bootstrap etmek yeterli değildir. Gerekirse tüm fit sürecini tekrarlayan grup örnekleme/tekrarlı iç doğrulama maliyeti ayrıca kararlaştırılır. Bugün CI/başarım/negatif örnek yoktur.

## Karar kapısının somut sonucu

Önerilerin hiçbirinde `APPROVED_BY_USER` durumu yoktur. Onay gerektiren çekirdek seçimler: PT/klinik/kategori hedef yolu ve destek kuralı; maskeli dal ve Methenamine abstention/fallback; ana grup kuralı ve CV düzeni; 5/56+maskeler ve isteğe bağlı ATC; proxy kayıt-sıralama mı açık varsayımlı PU mu. Context dışarıda ve K12 ayrı kalması önerinin kapsam korumasıdır; PPI eşiği seçilmez. Yeni model eğitimi için ayrıca açık talimat gerekir.

## Yöntem kaynakları

[RDKit Morgan generator API](https://www.rdkit.org/docs/source/rdkit.Chem.rdFingerprintGenerator.html) fingerprint ayarlarını; [Murcko API](https://rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html) scaffold çıkarımını belgeler. [Scikit-learn veri sızıntısı](https://scikit-learn.org/stable/common_pitfalls) train-only dönüşüm sınırını, [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html) grup ayrıklığını açıklar. [Jain, White ve Radivojac (2017)](https://arxiv.org/abs/1702.00518) PU koşullarında klasik performansın neden yanlı olabildiğini ve düzeltmede önsel bilgisinin rolünü inceler. [Metrik tanımları](https://scikit-learn.org/stable/modules/model_evaluation.html) AP/AUROC hesaplarının referansıdır. Bunlar yöntem kaynaklarıdır; yeni biyolojik veri seti eklenmedi.
