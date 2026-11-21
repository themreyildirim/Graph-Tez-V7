# WP11 — Kayıtlı A1P1 için protein/PPI açıklaması yöntem önerisi v1

07.11.2026. **Yalnız sözleşme; attribution uygulanmadı. Sonraki uygulama için kullanıcı onayı gerekir.** WP11 ilk aşamasında gerçek protein/kenar katkısı, yeni graph forward veya optimizasyon yapılmaz. Aşağıdaki öneri B1 SHAP yöntemiyle aynı şey değildir.

## Sabit model ve açıklanacak büyüklük

WP10 `models/WP10_factorial_training_v1/{context}_A1P1.npz` ve eş metadata kullanılacak. Her gerçek test query yalnız ait olduğu frozen outer modelde, o modelin fit edilmiş PT CUI başlığı için açıklanacak. Primary ve stres ayrı kalacak. Aynı alfabetik kimlik/CUI kuralı performans görülmeden uygulanabilir; başlığı olmayan PT `NA` kalır. Yeni hedef, yeni seed, fit, optimizer veya test başarısına göre örnek araması yoktur.

Önerilen ölçü `Δz=z_orijinal−z_müdahale`, kayıt sıralama **logiti** üzerindedir. Bu bir-at-a-time silme/maske duyarlılığıdır; SHAP veya nedensel etki olarak adlandırılmaz. Nonlineerlik ve paylaşılan yollar nedeniyle katkılar toplanınca toplam protein/PPI etkisini vermek zorunda değildir. Sigmoid farkı ayrıca gösterilirse ölçeği ayrı yazılmalı; klinik risk azalması denmemeli.

## Birincil maske ile silme duyarlılığının farkı

| Yol | Önerilen birincil müdahale | Ayrı duyarlılık: fiziksel silme | Korunan bilgiler |
| --- | --- | --- | --- |
| İlaç–protein rolü | İlgili protein temsilinin yalnız o query ve target/enzyme/transporter/carrier rolündeki readout terimini sıfırla; **orijinal rol bağlantı sayısına böl** | İlişkiyi kaldır; kalan ilişkilerin sayısına yeniden böl. Son ilişki kaldırılırsa boş blok ve buna uygun maskenin değişmesi ayrıca raporlanır | Birincil maskede orijinal rol availability maskesi sabit; protein dizisi, node feature ve diğer roller değişmez |
| Yönsüz PPI bağı | Kanonik insan protein çiftinin iki yönlü mesajını birlikte sıfırla; **orijinal degree paydası sabit** | Her iki yönlü edge_index sütununu çıkar; etkilenen düğümlerde degree yeniden hesaplanır. Kalan tüm mesajların ağırlığı değişir | Node feature, self/residual yol, train/query üyelikleri ve molekül/kimya dalları sabit |

Encoder'ın gerçek hesabı `z_i=ReLU(Px_i)`, `m_i=Σ_j z_j/max(d_i,1)`, `h_i=z_i+ReLU(Sz_i+Mm_i)` biçimindedir. Sabit derece maskesinde `m_i(g)=Σ_j g_ji z_j/max(d_i_original,1)`; kenar silmede payda `max(Σ_j g_ji,1)` olur. Tek bir bağ kaldırıldığında bu iki işlem genellikle aynı değildir. PPI mesaj ağırlığında bias yoktur; izolasyonda komşu ortalaması sıfırdır, self/residual devam eder. Komşu mesajı kapatmak protein bilgisini tümüyle yok etmez.

Rol maskesi de aynı ayrımı taşır: `r_drug,role=Σ_p h_p/n_original` içinde tek terimi kaldırmak, kalan proteinlerin ortalamasını yeniden almakla eşdeğer değildir. Aynı protein birden fazla role bağlıysa her rol kenarı ayrı açıklanır. “Protein düğümünü silme” ise tüm rollerini ve PPI bağlantılarını değiştiren başka, bu sözleşmenin ilk uygulamasına dahil olmayan müdahaledir.

## Query ve cache izolasyonu

- Kaynak model ve train bundle salt okunur tutulacak. Başlangıçta NPZ/metadata hash'i, model state digest'i, graph digest'i ve kayıtlı query skoru eşitliği doğrulanacak; forward `eval` ve gradient gerektirmeyen modda yapılacak.
- Query'ye ait rol maskesi yalnız query readout'a uygulanacak. Train protein cache'i ve diğer query çıktıları değişmemeli. Query ilaçları veya PT ilişkileri train grafına eklenmeyecek.
- PPI maskesi paylaşılan train protein temsillerini değiştirdiği için **yeni bir kopyada fresh train cache hesaplanması gerekir**. Orijinal cache'e in-place yazılmaz. Karşılaştırılan bütün query'ler aynı müdahale cache'ini kullanabilir; başka query eklemek cache'i değiştiremez.
- Mevcut `ProteinCache` graph/model digest kontrolü korunacak. Graf silme digest'i değiştiriyorsa yeni kopya için yeni cache üretilecek; eski cache'e yanlış digest takılarak kontrol atlanmayacak. Sabit-degree maskeli açıklama forward'ı ayrıca sürümlenecek; eğitim encoder'ı değiştirilmez.
- Train'de bulunmayan query proteinleri mevcut sözleşmede self-only kodlanır. Bunlara yeni PPI komşuluğu uydurulmaz; olmayan kenarın attribution'ı **NA / kaynakta yol yok** olarak yazılır. Geçerli kenardaki gerçek sıfır Δz ile karıştırılmaz.

## Sabit kapsam ve zorunlu gelecek testler

Strict aynı-taxID insan STRING700, mevcut train protein evreni; koşullu E. coli K12/MG1655 ve özellikleri eksik context80 eklenmez. 62 ilaç,54/8 atom QC maskesi, Methenamine abstention ve Tobramycin protein eksikliği korunur. Molekül/kimya girdileri maskeler arasında sabit kalır; atom veya bağ attribution bu kısa önerinin kapsamında değildir.

Gelecek uygulama öncesi test kapısı: (1) sıfır müdahale ile kayıtlı skor eşitliği; (2) yönsüz PPI'nin iki yönüne aynı maske ve doğru ID hizası; (3) sabit ve yeniden hesaplanan paydanın analitik küçük graf kontrolü; (4) protein/kenar indeks permütasyonu; (5) PPI kapalı kontrolünde PPI maskesinin sıfır etkisi; (6) query rol maskesinin diğer query/cache'i değiştirmemesi; (7) PPI maskesinde yalnız kopya cache'in değişmesi; (8) tekrarlanabilir Δz ve model/source hash eşitliği; (9) olmayan yol ve abstention için NA; (10) tek tek maskelerin toplamını nedensel/toplamsal açıklama sanmama.

Bu yöntem teknik model duyarlılığını açıklar. PPI ek tahmin üstünlüğünün WP09/WP10'da gösterilememesini değiştirmez; protein biyolojisinin yararsızlığı da çıkarılamaz. Unknown gerçek biyolojik negatif değildir. WP12, eğitim, gerçek protein/kenar attribution hesabı bu aşamada başlamaz.
