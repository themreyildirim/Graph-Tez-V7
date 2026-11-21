# AGENTS.md — Graph-Tez V7 (SADE, 05.11.2026)

> **TEK GEÇERLİ AKTİF PLAN:** `docs/plan/ROADMAP_V7.md` ve `docs/plan/SOURCE_USAGE_AUDIT.md`. `legacy/` eski tarihsel belgeleri içerir; bunlar talimat değildir. Önceki V7 planları kullanılmaz.

## Proje hedefi
- Antibakteriyel ilaçların, mevcut DrugBank + SIDER + PubChem kimyasal bilgileri ve doğrulanmış ilaç–protein ilişkileri üzerinden **yan etki ilişkilerini** modellemek; uygun olduğunda mevcut STRING PPI verisinin katkısını ölçmek.
- Eski V6'nın hatalarını düzeltmek, güvenilir bir öğrenme/değerlendirme hattı oluşturmak ve **ek veri seti yüklemeden önce mevcut ilaçları geri kazanmak**.
- Sonraki aşamada, kullanıcı zaten istediği için, PubChem kimliği doğrulanmış SMILES ile molekül grafı, SHAP/GNN açıklamaları ve PDF okuyabilen küçük Ollama LLM modülü geliştirmek. Bunlar yeni klinik veri setleri gerektirmez.
- Her adım Türkçe öğretici açıklama, veri örneği, görsel, test ve onay kapısı içermeli.

## KAYNAK ALLOWLIST — yalnız bunlar aktif
1. `full database.xml` (DrugBank XML) — ilaç kayıtları, ATC, hedef protein bağlantıları, XML içindeki dizi/kimlik metadatası.
2. `meddra_all_se.tsv` (SIDER 4.1) — yan etki etiketleri.
3. `drug links.csv` — DrugBank ↔ PubChem Compound ID eşlemesi.
4. **PubChem PUG REST** — ilk V6'daki 5 fizikokimyasal özellik; yeni V7'de gerekirse SMILES. İlk WP00'da API isteği yapma.
5. **İşlenmiş legacy tablolar** — `ilac_feature_v5_atc.csv`, `ilac_yan_etki_v5.csv`, `ilac_protein_eslesmesi_v6.csv`, `protein_dizileri_v6.csv`, `protein_feature_v6.csv`, `heterogen_ag_v6.pt` yalnızca karşılaştırma ve kalite kontrol. Gerektiğinde `sadece_antibiyotikler.csv` eski ATC aday listesini denetlemek için.
6. **STRING koşullu PPI** — `ppi_insan_v3.csv`, `ppi_bakteri_v3.csv` (varsa). Bunların kaynak ham dosyaları gerekirse: `9606.protein.links.v12.0.txt`, `511145.protein.links.v12.0.txt`, ilgili `*.aliases.v12.0.txt`. **Eski V6'daki PPI kenarları eğitimde fiilen kullanılmamıştı.** Sadece kontrollü yeni deney için.

UniProt: Önceki MASTER_KOD, UniProtKB ID'lerini ve protein dizilerini DrugBank XML'den çıkarıyor; bağımsız UniProt indirmesi/API kullanımı bu kodda gösterilmedi. Bu nedenle UniProt dış veri seti **zorunlu değil**. Kimlik/dizi doğrulaması için gerekirse *ayrıca onay alarak* kullan.

## KESİN DIŞLAMA — yerel veri dizininde bu dosyaları OKUMA
MIMIC-IV/PhysioNet hasta verileri, CARD/ARO/direnç genleri, FAERS, DisGeNET, OnSIDES, ChEMBL, DailyMed/openFDA/etiket toplu dökümleri; yeni organizmalara ait STRING PPI ham veri setleri (Staphylococcus, Pseudomonas, Klebsiella vb.), önceki denemelere ait `all.csv`, `pharmacologically_active.csv`, `idmapping_2026_03_09_all_target.xlsx`, `ANTIBIYOTIK_MASTER_NETWORK*`, `nihai_antibiyotik_agi_*` ve diğer tarihsel bütünleşik tablolar. Bunlar yeni modelin girdi listesinde **değil**.
- Dosyaların bu isimlerini yalnız üst dizin **dosya adı envanteri**nde `out_of_scope` olarak işaretleyebilirsin. Alt klasörlerine girme; içeriklerini okuma, hash alma, kopyalama, şema tarama, dönüştürme, indirme, modele sokma.
- `legacy/` tarihsel belgelerinde dışlanan kaynak adları geçebilir. Bu, bunları projeye geri dahil etme talimatı değildir.
- Kapsam ancak kullanıcının açık kararıyla değişir. Aday ilaç sayısını artırmak için önce aynı 3 ana veriden + PubChem API'den daha iyi kimlik eşleme ve eksik modalite yaklaşımı dene. İlaveten yeni yan etki kaynağı bulup otomatik entegre etme.

## Kritik bilimsel kontroller
- **`kalite_skoru` yasak girdi.** `protein_feature_v6.csv` içindeki sütun `P/Q/O` UniProt ID baş harfinden türetilmiş keyfi bir kod. Yeni `protein.x` içinde bulunmayacak. STRING `combined_score` da protein düğüm özelliği değil. Gerektiğinde sadece önceden tanımlanmış ayrı PPI filtresi/ablation.
- Eski protein dizileri `>lcl|...|AminoAcidSequence` gibi metadata içerebilir. Ayrıştırmadan AAC/DC hesaplama. 20 standart amino asit doğrulaması ve özel dizi parse testi zorunlu.
- Eski 5'li amino asit grubu tanımında **F çakışması, C ve G kapsam dışılığı** var. Açık sınıflandırma ve test olmadan v6 özelliklerini aynen kullanma.
- Eski ATC kodlamasında 56 ilacın 12'si tamamen sıfır. Bu bir **mapping/kapsama** problemidir, sıfır biyolojik kanıt değildir. Sistemik antibakteriyel J01 kohortu, antifungal/topikal/diğer antimikrobiyallerden ayrı raporlanmalı. İlaç ismi son ekleriyle sınıflama yapılmaz.
- 209 aday kaydın 125'i `DBSALT` tipinde. `DBSALT` sayısını benzersiz ana etkin madde sayısı olarak yazma. Tuz/formülasyon ↔ temel ilaç ilişkisinde yanlış birleşmelerden kaçın.
- 38 ilaçlık eski V6 kesişiminde **605 pozitif satır, 590 benzersiz ilaç-yan etki çift**; **1140** olası çift, **550** etiketsiz çift (30 yan etki). Eski kod 1210 negatif örneği tekrar seçebiliyor: **pozitif/unknown** semantiğini koru, çiftleri tekilleştir; negatif sınıfın doğruluğunu iddia etme.
- Train/val/test ilaç düzeyinde (drug-disjoint); ölçeklendirme/özellik seçimi yalnız train üzerinde fit edilir. Test ilaçları eğitimde görünmemeli. Kaydedilen `heterogen_ag_v6.pt` tarihsel ve potansiyel sızıntılı; yeni çalışmada bağımsız oluşturulacak.
- PPI'yi kullandığını ancak `ppi_edge_index` gerçekten `forward` içinde işleniyorsa iddia et. Eski model MLP + drug→target mean aggregation baseline'dır. Yan etki kenarlarını eğitim grafında test doğrulama hedefi olarak gösterme.
- Yan etki yok bilgisi = SIDER kaydı yok bilgisi değildir; ayrı tut. Yeni ilaç sayısı önce kapsam raporuyla ölçülmeli, 50/100 gibi sayı garanti edilmemeli.
- Prospektüsten aynı yan etkileri çıkartıp aynı etiketin GNN eğitim girdisi yapma. PDF/LLM açıklama katmanı ayrı; SHAP sayıları model tarafından hesaplanır, LLM yorumlar. Klinik tedavi önerisi veya bireysel risk iddiası yok.

## İş paketi kontrolü
Kullanıcının WP00 onayıyla eklediği kalıcı çalışma kuralı: Her iş paketinde açıklamalı Jupyter Notebook oluştur; kod hücrelerini çalıştır ve analizleri hücrelerin hemen altında görüntülenebilir tablolar ve grafiklerle sun. Notebook ile birlikte Türkçe rapor, statik görseller ve uygun doğrulama testleri üret.

Bir seferde yalnızca kullanıcının açıkça başlattığı `WPxx` üzerinde çalış. Sıra: kavram → gerçek dosya/şema → veri kalitesi → görsel → kod/test → Türkçe `reports/WPxx.md` → onay için dur. Kod açıklaması, örnek kayıt, kaynağın sürümü ve boşluk oranlarını raporla. Harici büyük indirme, çok sayıda API çağrısı veya model eğitimi için ilk önce kullanıcı onayı.

## Yerel dosyalar
`C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset` — yalnız **Windows yerel Codex** erişebiliyorsa; bulut Codex bu yolu göremez. İlk görev yol erişimini test etmek; erişim yoksa kullanıcıdan çözüm istemek. Salt okunur eriş; dosya adında 1.9 GB XML veya 600 MB PPI varsa belleğe komple alma.
