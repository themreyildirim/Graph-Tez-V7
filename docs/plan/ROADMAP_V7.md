# V7 — Sade ve Öğrenme Odaklı Aşamalı Yol Haritası

**Kapsam:** Eski V6'daki gerçek veri hattını denetleyip güvenilir yeniden kurulum. Dış veri yığını yok. Büyük kaynakların yerel salt okunur erişimi. Her paketten sonra kullanıcı onayı.

## Aşamalar

| Paket | Konu / öğrenme hedefi | Somut işlem | Çıktı + durma koşulu |
|---|---|---|---|
| **WP00** | Reprodüksiyon, kaynak provenansı, CSV/XML/TSV veri türleri | Salt okunur **allowlist** yerel dosya envanteri, dosya başlık/örnek/format; mevcut V6 sayımlarıyla eşleştir | `reports/WP00.md`, `reports/qa/source_inventory.csv`, 1–2 bar grafik; kullanılmayan dosyaları okuma; onay bekle |
| **WP01** | Grafın düğüm/kenar, derece, komşuluk, bileşen, centrality, `DiGraph` ve `HeteroData` kavramları | İlk olarak çok küçük sentetik graf, sonra allowlist gerçek veriden küçük görsel; 1-hop/2-hop örneği | Öğrenme notu, NetworkX notebook, görseller; gerçek ağ nedenselliği iddiası yok |
| **WP02** | DrugBank, primary/secondary/DBSALT ve ATC | 1.9GB XML'i streaming parse; J01 scope, ingredient/salt mapping; doğrulanmamış ayrımı | `drug_registry`, eşleme başarısı, ilaç sayım hunisi |
| **WP03** | SIDER, MedDRA PT, UMLS, STITCH/CID, etiket tanımı | Yalnız `meddra_all_se.tsv` + `drug links.csv`, 35 hedefin eşlemesi, unique ilişkiler | `drug_adr_positives`, overlap ve duplicate görseli |
| **WP04** | PubChem kimya özellikleri, API + cache, RDKit SMILES temel kavramları | Mevcut CID'lerin MW/LogP/HBD/HBA/TPSA/SMILES doğrulama; API ancak kullanıcı onayıyla | Molekül örnekleri, kaynaklı `drug_features`, missingness QC |
| **WP05** | Protein dizileri, amino asit kimyası, AAC ve grup DC | İlaç–protein ilişkisinin XML'den çıkarılması; `>lcl|` metadata temizliği, grup hata düzeltmeleri; `kalite_skoru` çıkarımı | `drug_target_edges`, `protein_features`, sekans/QC testleri |
| **WP06** | STRING PPI/organizmalar ve gerçek graf bağlamı | **Yalnız hazır insan/E. coli** PPI verileriyle bağlantı kapsamını görselleştir; kullanılamayan diğer türlerde izolasyonu raporla. Ek organizma indirme yok | PPI graph stats; gerçek encoder kurmaya yeterli bağlantı var mı? karar kapısı |
| **WP07** | Veri entegrasyonu/heterojen graf, kayıp modaliteler | Kanonik ID ile ilaç/protein/SE; source/target ilişki grafı, maskeler, uygunsuz edge/girdi engeli | Validated HeteroData + node/edge count + leakage audit |
| **WP08** | Supervised vs positive-unlabeled, drug split, AUPRC | Drug-disjoint split, scaler train-only; etiket prevalansı, 5 kimya+ATC LR/RF/MLP; protein-mean MLP baseline | AUROC/AUPRC CI ve leakage unit test; tarihi V6 metrikleri doğrulandı denemez |
| **WP09** | Protein ağında message passing, GiG vs baseline | **Yalnız WP06'da topolojik yeterlilik kanıtlanırsa** PPI encoder+drug aggregator; aynı split ve ablation; aksi halde açıkça `PPI insufficient` de | Gerçek edge_index forward test ve ablation; fayda yoksa raporla |
| **WP10** | SMILES→atom/bond graf, RDKit→PyG Data, readout | Mevcut PubChem SMILES ile küçük Molecular GNN, validasyon/scaffold split (yeterli örnek varsa) | Molekül örnekleri, kademeli karşılaştırma; veri küçükse deney ertelenir |
| **WP11** | Açıklanabilirlik: SHAP ≠ nedensellik, protein/edge attribution | Kimya baseline SHAP; GiG varsa hedef protein/kenar maskelerini test et; katkı kaynaklı | Local/global SHAP ve graf açıklaması, limitler, stabilite |
| **WP12** | PDF bilgi çıkarımı ve küçük yerel LLM | Sadece kullanıcının seçtiği prospektüs PDF'leri; PyMuPDF, sayfa kaynaklı JSON, düşük parametreli Ollama; LLM yan etki tahmini yapmaz | `reported_in_PDF` ≠ `predicted_by_GNN` ayrımı, kaynak sayfası, RDKit kimya doğrulama |
| **WP13** | Tez raporlama ve açıklanabilir karar destek demo | Küçük arayüz, veri kartı, deney/etiket/split ve eksiklik dokümantasyonu | Tekrarlanabilir deney matrisi, tez tabloları/görselleri |

## Sıra ve başarı ölçütleri
- En erken model eğitimi WP08; o ana kadar yalnız veri keşfi ve kalite kontrolü.
- WP09 veya WP10, veri yetersizse **yapılmayabilir**; basit güçlü modeli dürüstçe raporlamak daha değerlidir.
- İlk hedef veri setlerinin sayısını körlemesine artırmak değil: **benzersiz gerçek J01 bileşik sayısı, ADR etiketli sayısı, kimya özellikli sayısı, hedef proteinli sayısı** ile aktarım başarısı. Genişleme garanti değil.
- `CARD, MIMIC-IV, DisGeNET, FAERS, OnSIDES, ChEMBL, DailyMed/openFDA` ve diğer organizma dosyaları hiçbir WP'nin zorunlu girdisi değildir.
- WP12, kullanıcının istediği **PDF/LLM çıktısı** için ayrıca gerekli modüldür; PDF'den okunan yan etki aynı modele özellik olarak girmez.

## Deney basamakları (eski model ile fark)

| Varyant | Kimyasal özellik | Hedef protein | PPI mesaj geçirme | Molekül atom graf | Kıyas amacı |
|---|---|---|---|---|---|
| B0 | Yok | Yok | Yok | Yok | Label önseli |
| B1 | Var | Yok | Yok | Yok | Açıklanabilir basit baseline |
| B2 | Var | Ortalama embed | Yok | Yok | Eski V6'ya yakın ama temiz alternatif |
| G1 | Var | Var | **Var** | Yok | PPI gerçek katkısı, ancak WP06 başarılıysa |
| G2 | Var | Opsiyonel | Opsiyonel | Var | Atom grafı ek fayda sağlıyor mu? |

**Yayına hazırlık:** drug-disjoint split, hiç tekrarlanmayan ilişkiler, yalnız train fit scaler, pozitif/unknown notasyonu, ablation, seed ve hata aralıkları. Klinik uygulanabilirlik veya neden-sonuç iddiası yok.
