# WP09 karşılaştırma sözleşmesi — WP08 kapanış taslağı v1

06.11.2026. **Yalnız plan; WP09 uygulaması/eğitimi için kullanıcı onayı beklenir.** Bu belge, kabul edilen WP08 sonuçlarını değiştirmez. Makinece okunur eşleniği `reports/qa/WP08/final_closure_v1/WP09_comparison_contract_draft.json` dosyasıdır. Aktif ROADMAP'teki koşul sürer: topolojik yeterlilik öğrenme faydası değildir; yeterlilik yoksa `PPI insufficient` raporlanır.

## Değişmeyecek karşılaştırma sınırları

| Konu | Sözleşme |
| --- | --- |
| Araştırma sorusu | Yeni ilaçlar için SIDER'da gözlenen PT kayıtlarını sıralama; klinik risk değil |
| Veri evreni | Aynı 62 ana ilaç; kaynak PT CUI. 1.061 PT'nin tümü train hedefi değildir |
| Bölme | Mevcut `outer_membership_v1.csv`, `nested_partitions_v1.csv`, `split_lock_v1.json` aynen; seed 20261106; ana connectivity dış5/iç3 ve ayrı sabit yapı stres protokolü |
| Hedef seçimi | Her ilgili train'de ≥5 pozitif kullanılabilir ilaç ve ≥2 bağımsız grup; mevcut sözlükler kaynak. Inner sözlük outer sözlükten veya validation/test etiketinden seçilmez |
| Train uygunluğu | B2'nin mevcut 61 input-eligible ilaç politikası ve kimya+4 protein rol maskesi. PPI komşusu yokluğu eleme nedeni değildir; 62 envanterde kalır |
| Eksik modalite | Mevcut QC, sekiz kimya inceleme bayrağı, Tobramycin/Methenamine protein eksiği korunur. Methenamine kişisel girdisizken abstention; B0 nüfus referansı bunu doldurmaz |
| Özellikler | 5 QC kimya, 56 dizi özelliği ve maskeler. Yalnız aynı ilgili train'de fit edilen mevcut dönüşüm kaynakları; ID ezberlemesi, PT/kategori/raporlama frekansı, kalite_skoru yok |
| Sabit referans | `WP08-observed-record-L2LR-v1` B1/B2 ve `B0_frequency_reference_v1` skorları/model metadata'sı/hash'leri salt okunur. Yeniden C/seed/model araması yapılmaz |
| Ortak kapsam | Birincil baseline kıyası eski paired54'ün aynı drug/fold/PT anahtarlarında. PPI availability ile ilaç seçmek yok. Own61 ve complete-case53 ayrı duyarlılık kapsamı |
| Eksik yeni skor | Aynı eski kapsamın tamamında kapsama denetimi; yeni model NA'sı açık raporlanır. Gerekirse outcome-blind ortak finite-score kesişiminde bütün modellerin sabit skorları birlikte kısıtlanır; daha dar kapsam aynı eski metrikmiş gibi sunulmaz |
| B0 paydası | B0_like_B1 ve B0_like_B2 farklı train uygunluğu paydalarıdır; eski sıklıklar değişmez. Yeni B2-uyumlu model için eşleşen referans B0_like_B2; B0_all_train ayrı duyarlılık |
| Proxy ve metrik | Gözlenen=1, unknown=0 yalnız observed-record proxy. Drug-macro AP birincil; AP average precision. Class-macro/micro AP-AUROC, pozitif/unknown ve NA kapsamı ikincil; özgüllük/klinik kalibrasyon iddiası yok |
| Model seçimi | Yalnız inner-train/validation, drug-macro AP ve önceden sürümlenen aynı hedef kapsamı. Inner fold hedefleri farklı olabilir; her aday aynı fold içinde aynı sözlükte, geçerli fold ortalaması ve NA kapsamı açık. Outer test için eşik/epoch/seed/kapasite/karar seçimi yasak |
| Sonuç sonrası durum | WP08 outer sonuçları daha önce görüldü. Aynı foldları kullanmak bunları yeni bağımsız test yapmaz; gelecek WP09 karşılaştırmaları keşifseldir |

## Protein ve graf sınırı — önerilen muhafazakâr senaryo

Train grafı her inner/outer fit için yeniden ve ayrı sürümde kaynak tablolardan kurulmalıdır. WP07 inceleme `.pt` nesneleri veya WP08 grafının yerinde değiştirilmesi kullanılmaz. Train drug düğümleri yalnız ilgili train ID'leridir; validation/test drug düğümleri, bunların ileri/ters ilişkileri ve bütün yan etki hedef kenarları graf dışında kalır. `target`, `enzyme`, `transporter`, `carrier` dört ayrı ilişki/readout olarak korunur.

Birincil aday protein evreni **yalnız train ilaçlarına bağlı, doğrulanmış dizi özellikli accession'lar**dır. PPI, bunların içindeki 63 aynı-taxID insan eşlemesine uyan düğümlerin induced kenarlarıyla sınırlanır. 63'ün her foldta tamamının bulunduğu varsayılmaz. WP08 kapanışındaki `WP09_train_only_topology_preflight.csv`, mevcut küçük WP06 kenar tablosundan eşik 400/700/900 için gerçek train bağlamı sayımlarını verir; yeni graf veya eğitim nesnesi üretmez.

PPI'sız proteinlerde dizi tabanlı self/residual temsil korunur; komşusuz düğüm otomatik silinmez. K12/MG1655 kapsam incelemesindeki 23 protein katı insan PPI'sına eklenmez. Bu proteinler doğrulanmış dizileriyle ilaç rol özetinde kalabilir, fakat koşullu bakteri kenarları bu deneyde yoktur. Diğer organizmalara insan PPI'sı taşınmaz. 80 context düğümü amino asit özelliği varmış gibi sıfır doldurulmaz; başlangıç karşılaştırmasına dahil edilmez.

Query ilaç eğitim grafına eklenmez. Fit edilmiş protein temsilleri ve dondurulmuş dönüşümler üzerinden kaynak doğrulanmış etiketsiz query ilişkileri yalnız readout için kullanılır. Train protein evreninde bulunmayan query accession'ı, dizi özellikleri geçerliyse aynı train-fitted scaler ve paylaşılan self encoder ile, bu senaryoda **PPI komşuluğu olmadan** temsil edilir; bu kapsam ayrıca sayılır. Query ilacından proteinlere geri mesaj, train düğümlerini yeniden hesaplama, query etiketi veya query batch normalization istatistiği yoktur. Harici sabit 63 düğümün tamamına genişleme ayrı onaylı senaryo olmadan yapılmaz.

## Mimari adayı — henüz uygulanmadı

1. QC kimya → train-standardize 5 özellik + açık maske → küçük paylaşılan kimya projection.
2. Train proteinlerinin 56 dizi özelliği → paylaşılan protein projection → bir residual mean-message PPI katmanı. Örnek biçim: `h_i = phi(Wself*x_i + mean_{j in N(i)} Wmsg*x_j)`; boş komşulukta yalnız self yolu. Her PPI varyantında aynı projection/readout/başlık ve karşılaştırılabilir parametre sayısı.
3. DrugBank'ın dört rolü için ayrı maskeli mean readout; roller birleştirilmez. Kimya ve rol blokları + maskeler → sabit train PT sözlüğü için proxy skor başlığı. ID/etiket frekansı node özelliği veya adjacency değildir.
4. Küçük kapasite adayı: bir mesaj katmanı, 32 boyutlu protein projection. Bu sayı onaylanmış sonuç optimizasyonu değildir; genişlik, loss, optimizer/LR, epoch/early-stop bütçesi ve inner seçim/NA politikası eğitimden önce ayrı config ile onaylanmalıdır. L2-LR ile PPI modelinin farkı kapasite+topoloji içerir; PPI'nin etkisi ancak aynı yeni mimarideki ablation ile ayrıştırılır.

STRING genel işlevsel ilişki ağıdır; her kenar fiziksel etkileşim veya nedensel yan etki yolu değildir. `combined_score` protein özelliği değildir. Başlangıç adayı eşik üstü ağırlıksız bağlantıdır. **Eşik henüz seçilmedi**: 400/700/900 topoloji/coverage tabloları ve label-independent gerekçe veya önceden kilitli inner-only seçim politikası onay kapısındadır; 700 nihai en iyi eşik diye alınmaz.

## Zorunlu ablation matrisi — onaydan sonra

| Varyant | Protein yolu | Kenarlar | Sabit tutulacaklar |
| --- | --- | --- | --- |
| G_noPPI | Aynı projection/self/residual/readout | Komşu kenarı yok | Train ID/target/scaler/mask/head, kapasite ve seçim bütçesi |
| G_realPPI | Aynı model | Aynı-taxID insan gerçek PPI | Aynı kapsam, seed/init politikası ve iç seçim bütçesi |
| G_shuffledPPI | Aynı model | Yalnız aynı insan fold evreni içinde degree-preserving yeniden bağlama | Düğüm seti, kenar sayısı ve dereceler; self-loop/duplicate yok |

Karıştırma train kaynaklı PPI üzerinde, etiketten bağımsız sabit RNG politikasıyla yapılmalıdır. Başarılı swap sayısı, seed, özgün/karışık edge hash ve değişen çift oranı kaydedilir. Az/çok yoğun graf yeterince karıştırılamıyorsa başarısız null/NA raporlanır; sessizce gerçek kenarlar yeniden kullanılmaz ve iyi sonuç veren karışım seçilmez. Swap bütçesi, minimum değişim eşiği ve tekrarlı null sayısı **uygulamadan önce** onaylanır. Varyantlar arasında self-loop/residual politikası aynı olmalıdır; noPPI gerçekten komşu mesajını kaldırır.

B0/B1/B2 sabit referans, G_noPPI ise yeni ağın kapasite kontrolüdür. G_realPPI−G_noPPI ve G_realPPI−G_shuffledPPI farkları PPI yapısının ek katkısını sorgular; yalnız G_realPPI−B2 farkından topoloji katkısı sonucu çıkarılmaz. Pozitif fayda gözlenmezse açıkça raporlanır.

## Uygulamada geçmesi gereken testler — henüz çalıştırılmadı

| Test | Somut kabul koşulu |
| --- | --- |
| Gerçek forward komşuluğu | Sabit, sıfır olmayan ağırlıklarla ayırt edici küçük graf: bir kenarı veya komşu özelliğini değiştirince yalnız beklenen reseptif alanda protein temsili değişir |
| Trace ve gradient | `ppi_edge_index` gerçekten message katmanına ulaşır; ayırt edici fixture'da komşu özelliğine ve mesaj ağırlığına sıfır olmayan gradient. Rastgele her kenarın her skoru değiştirmesi beklenmez |
| Boş PPI | Komşu mesajı tam yok; self/residual yolu geçerli ve sonlu. İzole protein/missing modalite elenmez |
| Permütasyon | Düğüm sırası/indeksler birlikte permüte edilince readout skoru tolerans içinde aynı |
| Tür/eşleme | 9606 kesin alias dışında PPI kenarı, K12 kenarı veya context düğümü reddedilir; yönsüz çift bir kez kanonikleştirilir, forward için iki yön açık kaydedilir |
| Split/kenar | Her context exact train ID; heldout drug ve ileri/ters kenarlar, SE hedef kenarı yok; kayıtlı heldout kaynaklarını değiştirmek train grafını değiştirmez |
| Dönüşüm ve hedef | Heldout feature/label mutasyonunda train scaler, vocabulary ve inner seçimi değişmez; 5/2 train desteği ve maskeler korunur |
| Query izolasyonu | Test query readout'u train protein embedding/graf hash'ini değiştirmez; protein universe dışındaki dizi self yolu raporlanır |
| Null uygunluğu | Real/shuffled düğüm kümesi, kenar sayısı ve degree eşit; loop/duplicate yok; hash ve minimum gerçek değişim kuralı sağlanır |
| Kapsam ve NA | Aynı eski scored drug/PT keys veya açık daralma raporu; input olmayan Methenamine abstention, unknown gerçek negatif değil, single-proxy train sınıfı NA |
| Tekrar üretim | Aynı config/hash/seed ile aynı çevrede toleranslı tekrar; sürüm/determinism sınırları kaydı, test başarımına göre seed araması yok |

Bu kapanışta yalnız mevcut WP08 testleri ve **plan sözleşmesinin tutarlılığı** sınandı. Encoder, gradient, forward ve PPI ablation testleri uygulanmış/geçmiş değildir.

## Değerlendirme, belirsizlik ve son onay kapısı

Drug-macro observed-record AP ilk sıradadır. Class-macro AUROC için pooled ragged OOF ile fold içi tanı ayrı sunulmalı; fold skor ölçeklerinin eşdeğerliği varsayılmamalıdır. Pozitif/unknown destek, değerlendirilebilir sınıf sayısı, abstention ve sözlük dışı pozitifler her varyant için ayrıca yazılır. Tarihsel30 onaylı semantik uyarılarıyla ayrı ikincil uzaydır, PT ile karıştırılmaz.

Aynı structural-group çekimleriyle paired koşullu bootstrap kullanılabilir; sabit OOF CI'ın tam yeniden eğitim/bağımsız dış doğrulama belirsizliği olmadığı yazılır. Yeni seed tekrarı/full-retraining bootstrap ancak önceden tanımlı ek bütçe ve onayla yapılır. Aynı veri üzerinde sonuç sonrası araştırma olduğu için aralıklar genel istatistiksel üstünlük veya klinik güvenlik kanıtı olmaz.

WP09 uygulama onayından önce tek config'te: **protein evreni/query politikası, PPI eşiği, mimari kapasite, loss, optimizer/epoch/early-stop, inner karşılaştırılabilirlik ve fallback, init seed politikası, null swap/tekrar kuralları** dondurulmalıdır. Bugün yalnız bu taslak hazırdır. **Kullanıcı onayı olmadan WP09 modeli kodlanıp eğitilmeyecek.**
