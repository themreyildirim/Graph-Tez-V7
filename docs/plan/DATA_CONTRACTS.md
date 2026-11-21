# V7 Minimal Veri Kontratları

## Zorunlu girdi katmanı

| Kaynak | Dosya/API | Kimlik alanları | Amaç | Yasak / uyarı |
|---|---|---|---|---|
| DrugBank | `full database.xml` | Primary DrugBank ID; secondary DB/DBSALT; ATC; protein UniProtKB; ingredient/salt; organizma | İlaç listesi, ATC sınıflaması, ilaç→protein, dizi | Benzersiz ilaç sayısı = DB/DBSALT satır sayısı değildir; XML parsing kontrollü |
| SIDER | `meddra_all_se.tsv` | STITCH CID0/CID1, UMLS/PT, etiket metni | Bilinen pozitif ilaç→yan etki ilişkisi | `label absent != clinically negative`; PT/LLT ve synonym kontrolü |
| Crosswalk | `drug links.csv` | `DrugBank ID`, `PubChem Compound ID` | DB↔SIDER↔PubChem eşleme | aynı isim ≠ otomatik aynı molekül; salt/ingredient doğrulanmalı |
| PubChem REST | CID→properties/structure | CID, canonical/isomeric SMILES, MW, LogP, HBD, HBA, TPSA | Kimya feature ve sonraki atom grafı | API cache, rate limit, yanlış CID/salt olası |
| XML protein | DrugBank `<polypeptide>` | UniProt accession, organism, sequence | Protein AAC/grup DC/özet feature | FASTA header/metin temizle; ID prefix score girdi değil |
| Koşullu PPI | `ppi_insan_v3.csv`, `ppi_bakteri_v3.csv`; gerekirse raw STRING insan/E.coli | taxon + STRING/UniProt protein kimlikleri | Gerçek biyolojik komşuluk deneyi | Organizma çapraz bağ yok, `combined_score` node.x değil |

## Yalnız geçmişe dönük kıyas için legacy çıktılar
`ilac_feature_v5_atc.csv` (56×33), `ilac_yan_etki_v5.csv` (865×6), `ilac_protein_eslesmesi_v6.csv` (153×5), `protein_dizileri_v6.csv` (70×4), `protein_feature_v6.csv` (70×54), `heterogen_ag_v6.pt`.

Bu dosyalar yeni model için **hazır doğru sayılmaz**. İmkân oldukça ana kaynaktan **yeniden üret**. `/data/raw` dosyalarını doğrudan değiştirme. `sadece_antibiyotikler.csv` 209 kaydı tekil ingredient saymaz.

## Ayrı öğrenme setleri
- `cohort_raw`: kaynak kaydı/ingredient ID/version/source.
- `drug_registry`: doğrulanmış ana kimlik, tuz/formülasyon varyantları, ATC, kimyasal kimlik, source & decision.
- `drug_features`: doğrulanmış 5 kimya özelliği, SMILES/Mol optional; her özellik için source ve missingness mask.
- `drug_target_edges`: DrugBank hedef ID, UniProtKB, takson/organizma, kanıt/metadata.
- `protein_features`: clean AA sequence, 20 AAC, düzgün atanmış grup dipeptit oranları, yeni canonical feature listesi; **`kalite_skoru` çıkar**.
- `drug_adr_positives`: canonical drug ID, canonical yan etki ID, raw UMLS/PT, label source, unique(drug,ADR).
- `ppi_edges` (koşullu): protein1,protein2,taxon, STRING mapping, source; combined_score sadece metadata/deney konfigürasyonu.
- `splits`: train/val/test ilaç ID'leri ve (drug,ADR) çiftleri, aynı ID birden çok splitte olamaz.

## Test sözleşmeleri
1. `DrugBank ↔ PubChem ↔ SIDER` mapping success/failure + manual review table; kesin olmayan eşleşme eklenecekse onay.
2. Protein sekansında yalnız `ACDEFGHIKLMNPQRSTVWY` (belirsiz X/U/O/B/Z için policy ayrı), metadata yok; AAC sum≈1; grup tanımları ayrık ve kapsamlı.
3. 35 hedef ADR konsepti → MedDRA PT/UMLS eşleme açıklanacak; 30 kategoriyle oluşan fark belgelenir.
4. ATC J01'li doğrulanmış sistemik antibakteriyel veri kümesi, antifungal/topikal/TB/diğer gruplardan ayrı tutulur.
5. Model input'unda `kalite_skoru`, UMLS/ADR label, label-based score/frequency, test target adjacency, PDF'le bulunan ADR listesi **bulunmaz**.
6. V6 590 benzersiz pozitif çift ile beklenen 550 etiketsiz çift birebir eşleşirse raporla; farklı sayıyı gizleme. Unknown çiftleri otomatik gerçek negatif kabul etme.
7. Drug-disjoint split, preprocessing train-only, tekrar yok; model checkpoint + seed + kaynak manifestleri reproducible.
8. PPI etkisi yalnız gerçek edge_index `forward()` akışına girince sınanacak; yoksa V6-like baseline diye adlandırılacak.
