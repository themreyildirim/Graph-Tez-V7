# WP07 — Entegrasyon ve değerlendirme karar kapısı

Bu belge seçenekleri karşılaştırır; nihai hedef, model giriş şeması, imputasyon veya bölme seçmez. 62 ilaç ve önceki QC kararları korunur. `review_contract.json` yalnız inceleme grafı sözleşmesidir. ROADMAP WP07 HeteroData ister; eğitim ve ayrım WP08, gerçek PPI encoder WP09 kapsamındadır.

## Kaynak ve graf sözleşmesi

- Kanonik ilaç primary DrugBank ID; protein WP05 accession, organizma/taxID kaynak registry'de; PT CUI ayrı kaynak hedef sözlüğüdür. İndeksler sıralı ID'den deterministik üretilir, biyolojik sayısal özellik değildir.
- 62 drug, 141 protein ve 1061 `se_pt_audit` düğümü inceleme senaryolarında korunur. PT düğümleri sıfır vektör taşımaz; `x` yoktur, ilişki kenarları da yoktur. Bu küresel gözlenen sözlük nihai train sözlüğü yapılmaz.
- DrugBank target/enzyme/transporter/carrier yönlü ve ayrı kenarlardır. Ters kenar yaratılmadı; rol anlamı kendiliğinden terslenmez. PPI yönsüzdür; PyG indeksinde iki yön sayıldığı için sütun sayısı tekil çift sayısının iki katıdır.
- Altı örnek: PPI yok; insan 150/400/700/900; yalnız koşullu K-12 700. Sonuncu insanla birleştirilmez, eşik örnekleri nihai seçimi temsil etmez. PPI'siz 78 protein çıkarılmaz; PPI yok senaryosunda tüm 141 korunur.
- 54 temiz kimya kaydı, sekiz inceleme kaydı ve protein modalitesi olmayan iki ilaç ayrı maskelenir. Raw/clean sayılar kaynak dosyalarda kalır, QC kararları kopyalanıp değiştirilmez. Input maskeleri etiketten türetilmez. QA sayıları X'e topluca aktarılmaz.
- 80 context düğümü özellik uydurulmadan envanterde tutulur; inceleme HeteroData nesnelerine girmez. Bu geçici güvenli inceleme kapsamıdır, nihai modelin context tercihi değildir. Sıfır dizi vektörü ortalama protein veya doğrulanmış protein demek değildir.
- `HeteroData.validate()` yalnız yapısal aralık/şekil kontrollerinin bir parçasıdır. Tip, kimlik, tekrar, kapsam, girdi/etiket ayrımı ek proje testleriyle doğrulanır; klinik veya model geçerliği sağlamaz.

## Onay bekleyen seçenekler

### D01: Hedef etiket

- **Tarihsel 30 karşılaştırması:** V6 izlenebilirliği; 61 ilaçta pozitif, semantik bayraklar sürüyor. Durum: Nihai hedef olarak onaylanmadı.
- **Kaynak PT CUI:** 62 ilaç, 1061 sınıf; 406 singleton; kavram izi korunur. Durum: Kayıpsız denetim sözlüğü; nihai hedef değil.
- **Semantik incelemeli kategori/PT alt kümesi:** Uzman gerekçesi; veriyle seçilecek eşik yalnız train üzerinde. Durum: Birleştirme/eleme yapılmadı.

### D02: Eksik ilaç modalitesi

- **Maskeli ayrı dallar / mevcut modaliteyi kullan:** 62 ID korunur; boş komşu toplaması biyolojik sıfır sayılmaz. Durum: Öneri; encoder/gating kararı bekliyor.
- **Train-only imputasyon + input maskesi:** Kimya için istatistiksel vekil; kimyasal doğrulama değildir. Durum: Fit/dolgu yapılmadı; QC bayrağı korunur.
- **Complete-case duyarlılık analizi:** Aynı alt grupta kıyas mümkün; seçilim yanlılığı ve kapsam kaybı. Durum: Ana 62 kohortunu daraltma kararı değil.

### D03: 80 context proteini

- **Seed-induced ağ / context kullanma:** Özelliği olmayan ek düğüm gerektirmez; bağlam kaybını raporla. Durum: İnceleme nesneleri bu seçeneği örnekler; nihai model kararı değil.
- **Öğrenilen tip tokenı + açık maske:** Sequence-derived özellik değildir; paylaşılan öğrenilen temsil önyargısı. Durum: Gelecekte onay ve ablation gerekir.
- **Topolojiye dayalı ayrı yapısal encoder:** Dizi biyokimyası iddiası yok; kapsam/transdüktif yapı etkisi denetlenmeli. Durum: Uygulanmadı.
- **Sıfır vektör + maske:** Sıfır gerçek AAC/DC veya MW değildir; ölçekleme/degree etkisi ve yapay benzerlik. Durum: Varsayılan yapılmadı; maskesiz dolgu kabul edilmez.

### D04: PPI kapsamı

- **PPI yok / katı insan induced ayrı varyantlar:** 141 protein korunur; 63 aynı-taxID seed; 150/400/700/900 incelemesi. Durum: Eşik ve kullanım seçilmedi.
- **K-12/MG1655 ayrı koşullu varyant:** 23 alias; 83333→511145 kapsam çözünürlüğü farkı. Durum: Ana ağla birleştirilmedi; kapsam kabul onayı gerekir.

### D05: İlaç ayrık değerlendirme

- **Sabit dış test + train içi seçim:** 62 ilaçta tek bölmenin varyansı; test yalnız sonda. Durum: Oran/ID/seed atanmadı.
- **Gruplu nested CV / tekrarlı gruplu CV:** Daha çok fit; seyrek sınıflarda destek sıfırı, bileşik benzerliği stresi. Durum: Fold sayısı/tekrar belirlenmedi.

### D06: Model giriş şeması

- **5 kimya ve 56 dizi alanından onaylı seçim:** Ölçekleme train-only; AAC/grup/DC bağımlılığı ve uzunluk incelenmeli. Durum: Allowlist kaynak sözleşmesi var; x oluşturulmadı.

### D07: Unknown değerlendirmesi

- **Açık varsayımlı PU protokolü:** Unknown gerçek negatif değil; sınıf önseli/SCAR-SAR varsayımları sorgulanmalı. Durum: Loss/negatif örnekleme/performans seçilmedi.
- **Gözlenen kayıt retrieval duyarlılığı:** AUPRC/AUROC unknown=0 vekil sonuç olur; klinik risk ölçümü olmaz. Durum: Ancak açık proxy etiketi ve varsayım onayıyla WP08.

## Gelecekteki değerlendirme protokolü — uygulama yok

1. Önce tahmin görevi ve hedef kavramı onaylanır. Tarihsel 30'a dönmek semantik bayrakları çözmez. Veriyle seçilen PT destek eşiği yalnız eğitim ilaçlarından öğrenilir; tam 62 ilaç destekleri bugün yalnız QA'dır. Sabit uzman sözlüğü seçilecekse etikete bakılarak optimize edilmeden gerekçesiyle dondurulur.
2. İlaç düzeyinde ayrıklık AGENTS gereğidir; rastgele çift/satır ayrımı seçenek değildir. Sabit dış test ile gruplu CV'nin oranı/fold/seed kararı açık kalır. Aynı kimyasal yapı/parent/tuz veya çok yakın stereo varyantların ayrı ID'lerle gruplar arasında kalması ayrıca kimlik ve gerekirse scaffold stres analizi gerektirir. Şimdi grup/split atanmaz.
3. Eğitim grafı yalnız eğitim ilaçlarını içerir; val/test ilaç düğümleri ve bu ilaçların ileri/ters ilişkileri eğitimde yer alamaz. Harici, etiketten bağımsız protein PPI kaynağını sabit biyolojik bağlam olarak kullanma ile fold'a özgü protein alt ağını kullanma iki ayrı protokol seçeneğidir. Paylaşılan protein tek başına hedef sızıntısı değildir; test ilacının kenarından train'e bilgi taşınması engellenmelidir. İnferansta yeni ilacın etiketsiz kimya/DrugBank ilişkisini ekleme davranışı önceden yazılır.
4. Scaler, imputasyon, özellik seçimi, sınıf ağırlıkları ve öğrenilen sözlük yalnız train üzerinde fit edilir. Val ayar içindir; test son değerlendirme içindir. QC kaynak bayrakları fit edilmeyen provenanstır; bunları değiştirmek ayrı karar gerektirir.
5. Gözlenmeyen PT ilişkisi unknown'dır. Kaynak yalnız pozitif kayıtlar sağladığından gerçek özgüllük/klinik risk bu verilerle doğrudan doğrulanamaz. Unknown=0 vekil AUPRC/AUROC ancak varsayımı açık kayıt-tahmin deneyi olarak yorumlanabilir; burada negatif havuzu veya skor üretilmedi. PU loss/önsel varsayımı WP08'de ayrıca kararlaştırılır.
6. Micro ve macro özetlerle birlikte sınıf desteği, tanımlı metrik üretebilen sınıf sayısı ve sıfır destek nedeniyle hesaplanamayan sınıflar raporlanır. Sınıf desteği 1 olan PT bağımsız iki ilaç grubunda pozitif veremez; stratifikasyon bunu düzeltemez. Bootstrap belirsizliği ileride ilaç/grup düzeyinde hesaplanmalı; çiftleri bağımsızmış gibi örneklemek belirsizliği küçültebilir. Bugün CI/başarım hesabı yok.

## WP09 için zorunlu PPI kullanım kanıtı ve ablation

Model geliştirilirse forward gerçek PPI edge_index almalı ve komşu mesajı protein temsiline katılmalıdır. Test planı: deterministik küçük ayırt edici protein grafı, sabit özellik/ağırlıklarla bir kenarı çıkarma veya komşu özelliğini değiştirme; yalnız izinli reseptif alandaki protein temsili değişimini sınama. Uygun sıfır olmayan ağırlıklar ve farklı girdilerle tasarlanmış test gerekir; rastgele her kenarın her çıktıyı değiştirmesi beklenmez. Gradient/trace testi ile PPI yoluna ulaşıldığı ayrıca kontrol edilir; edge_index'i forward argümanına koymak tek başına kanıt değildir.

Aynı onaylı split/seed/özellik/preprocessing ve karşılaştırılabilir kapasitede protein-mean baseline, PPI yok, gerçek PPI, organizma içinde karıştırılmış PPI ve önceden sabit eşik senaryoları karşılaştırılır. PPI yok varyantı kenarları gerçekten kaldırmalı; self-loop/residual farkı kaydedilmelidir. Context kullanılırsa seed-only/context ve maskeli temsil için ayrı ablation gerekir. K-12 kapsam kabul edilirse yalnız ayrı koşullu deney raporlanır. Deneyler test başarımına bakarak eşik/kenar seçmez; çoklu karşılaştırmalar ve seed varyansı raporlanır. Bu testler ve deneyler bugün çalıştırılmadı; encoder yoktur.

## Onay kapısı

WP07 veri entegrasyonu incelemesi tamamlanınca burada D01–D07 kararları kullanıcıya sunulur. Önceki onaylar nihai etiket/eksik modalite/protokol seçimi sayılmaz. `training_ready=False` nesneleri ve x/y yokluğu bilinçlidir. WP08 başlamadan kararların seçili değerleri ayrı konfigürasyonda kaydedilmelidir; eski belge ve QC tabloları ezilmez.

Yöntem referansı: [PyG HeteroData resmi API](https://pytorch-geometric.readthedocs.io/en/stable/generated/torch_geometric.data.HeteroData.html). PyG doğrulama kapsamı ve yönsüz çiftlerin iki indeks sütunu olarak sayılması bu API ile kontrol edilmiştir.
