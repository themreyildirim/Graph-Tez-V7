# Kaynak Kullanım Denetimi — V6'nın Fiili Kaynakları ile Ara Raporda Planlananlar

**Yöntem:** Kullanıcının ilk dönem ara raporu PDF (özellikle s. 25–28), `Kod_Aciklama_Raporu.docx`, `Surec_Raporu.docx`, `MASTER_KOD.py`, `İlaç Feature ları (1).docx`, `DATASET_SUMMARY.md`, `graph_neural_networks_proje_dok_mantasyonu.md` ve `İndüktif.ipynb` karşılaştırıldı. Drive klasöründeki 69 dosyadan seçilmiş işlenmiş CSV'ler daha önce açılıp doğrulanmıştı; büyük 1.9 GB XML/STRING ham dosyaları bu denetimde tümüyle satır bazında incelenmiş **değil**. 'Raporda önerildi' ile 'koda girdi' farklı statülerdir.

## A. Fiilen kullanılan / yeniden kurulumda tutulacak

| Kaynak | Eski kodda gerçek kanıt | V7 kararı |
|---|---|---|
| DrugBank `full database.xml` | `MASTER_KOD.py` bölüm 2 (J01 aday), 5 (ATC), 6 (drug-target, UniProtKB ID, protein XML sekansı) | **Temel ham veri** |
| SIDER `meddra_all_se.tsv` | bölüm 3 `pd.read_csv`; MedDRA PT filtreleme, yan etki hedefi | **Temel ham etiket** |
| DrugBank `drug links.csv` (boşluklu ad) | bölüm 3 `drug_links` ↔ SIDER PubChem ID köprülemesi | **Temel kimlik köprüsü** |
| PubChem **REST API** | bölüm 4 `pubchem_ozellik_cek(cid)`: MW, LogP, HBD, HBA, TPSA | **Temel kimyasal zenginleştirme**; V7'de isteğe bağlı SMILES aynı API'den |
| İşlenmiş `ilac_feature_v5_atc.csv` / `ilac_yan_etki_v5.csv` / `ilac_protein_eslesmesi_v6.csv` / `protein_dizileri_v6.csv` / `protein_feature_v6.csv` | bölüm 8 graf tensörlerinin kaynakları | **Yalnız V6 karşılaştırması/QC**; V7 temiz hat baştan oluşturulacak |
| STRING'den türetilmiş `ppi_insan_v3.csv`, `ppi_bakteri_v3.csv` | bölüm 8, PPI edge_index hazırlanıyor | **Koşullu ağ testi**; eski modelin `forward()` aşamasında PPI yok |

**UniProt durumu:** Kodda `res.text == 'UniProtKB'` ile XML'den accession çıkarılıyor; protein sekansı da XML içindeki `<sequence>` alanından geliyor. Kodda UniProt REST endpoint'iyle çalışan bir istek görünmedi. Süreç raporu 'UniProt API'ye geçildi' diye anlatsa da **yayımlanan MASTER_KOD buna tanıklık etmiyor**. Bu nedenle UniProt external dataset indirmek *WP00 için gerekli değil*. Eğer mevcut XML dizileri gerçekten tutarsız kalırsa yalnız doğrulama için karar verilecek.

**STRING durumu:** İçerik hiç kullanılmadı demek yanlış: dosyalar `HeteroData['protein','interacts','protein']` için okunuyor. Ancak `GiGModel.forward(self, x_drug, x_prot, x_se, dp_ei, pred_drug_idx, pred_se_idx)` PPI edge_index almıyor. Bu nedenle STRING **graf hazırlığında kullanılmış, öğrenimde kullanılmamış**.

## B. Eski aşamalarda kullanıldı, final V6 girdisi değil

- `all.csv`: Süreç raporu V5'in kısıtlı drug-target denemesinde kullanıldığını ve V6'da DrugBank full XML'in yerine geçtiğini söylüyor. WP00'dan ve aktif pipeline'dan çıkarıldı.
- `sadece_antibiyotikler.csv`: Eski bölüm 2'nin 209 kayıtlık aday çıktısı. **125 `DBSALT`** taşıdığından benzersiz ilaç sayısı diye kullanılmamalı; yalnız eski kapsam/QC karşılaştırmasında okunabilir.
- `ilac_feature_v4`, `protein_feature_v5`, `nihai_antibiyotik_agi_*`, `ANTIBIYOTIK_MASTER_NETWORK*`, `heterogen_ag_*v2/v3`, `hub_proteinler_v3` vb.: Tarihsel deney/ara grafikler; yeni eğitim kaynağı değiller, aktife alınmayacak.
- `İndüktif.ipynb`: Graf yaklaşımını anlatan **sentetik örnekler** içerir; asıl V6 eğitim hattında kullanılan veri olarak ele alınmaz.

## C. Planlanan/indirilen ancak final modelde kullanılmayan kaynaklar — KAPSAM DIŞI

| Kaynak | Orijinal belgelerde durum | Yeni karar |
|---|---|---|
| **MIMIC-IV** | MASTER_KOD / final raporda kullanım yok | **Okuma, kullanma** |
| **CARD** | Ara rapor s. 25–26'da **direnç amacıyla planlanmış**, final V6 yan etki kodunda yok | **Okuma, kullanma** |
| **FAERS** | Ara rapor s. 25–26'da **gerçek dünya sinyali doğrulaması için önerilmiş**, kodda yok | **Okuma, kullanma** |
| **DisGeNET** | Ara rapor s. 26'da önerilmiş; `Surec_Raporu.docx` 2.6: az eşleşme sebebiyle dahil edilmedi | **Okuma, kullanma** |
| **OnSIDES** | Eski V6 kaynak değil, önceki V7 planında öneri | **Şimdilik dışla; otomatik ekleme** |
| **ChEMBL** | Eski V6 kaynak değil, önceki V7 planında öneri | **Şimdilik dışla; otomatik ekleme** |
| **DailyMed / openFDA** | Eski V6 modelinde yok, önceki V7 önerileri | **Şimdilik dışla; otomatik ekleme** |
| **Ek STRING organizma dosyaları** | Eski kod sadece `ppi_insan_v3.csv` / `ppi_bakteri_v3.csv` okuyor | **Staph/Pseudomonas/Klebsiella klasörlerini tarama** |
| `pharmacologically_active.csv`, `idmapping_2026_03_09_all_target.xlsx` | Drive'da var; V6 ana eğitim kodunun okuma çağrılarında bulunmuyor | **Aktif hat dışında** |

**STITCH notu:** SIDER satırlarında `flat_id`, `stereo_id` türü STITCH biçimli alanlar var. Bu **ayrı STITCH ağı veri seti kullanıldığı** anlamına gelmiyor. Ayrı STITCH dosyası indirme.

## D. Ara rapor ile V6 arasındaki önemli fark

- Ara rapor s. 26 Çizelge 4.2 birçok veri kaynağını 'kullanılması planlanan' olarak listeliyor; bu tablo **tamamlanmış yazılımın veri giriş listesi değildir**.
- Aynı PDF s. 26–27 DrugBank + SIDER'ı ilk iki temel açık veri kaynağı diye anlatıyor. Nihai kod daha sonra `drug links.csv` ve PubChem REST ile kimlik/özellik köprüleri ekliyor.
- Ara rapordaki `~150 antibiyotik` bir **plan**, gerçekleşmiş sayım değil.
- Geçmiş final V6 için yaklaşık 38 ilaç, 30 yan etki kategorisi, 70 protein vardı; bu kohortta antifungal ve başka sınıflardan kayıtlar karışmış. J01 doğrulaması yeniden yapılacak.

## E. Doğrulanmış eski çıktı kalite sorunları

1. 56 ilaç özelliği kaydının 12'sinde tüm ATC one-hot bayrakları sıfır.
2. 70 protein dizisinin 70'inde başta FASTA/açıklama metni görünüyordu; AAC/DC hesabında özellik kirlenmesi olası.
3. Eski `protein_feature_v6.csv` toplam 54 sütun: ID/gene/organism/`kalite_skoru` + 50 dizisel özellik. `kalite_skoru` X_prot'a eklenerek 51 özellik yapılmış: **yeni modelde yasak**.
4. V6 `ilac_yan_etki_v5.csv` toplam 865 satır, 844 benzersiz (ilaç,kategori) çifti. Final 38 ilaç kesişiminde 605 satır, **590 benzersiz çift**, 15 çoğaltma; 38×30=1140 olası çiftin 550'si etiketsiz.
5. Eski kod (605×2) 1210 negatif örneği aynı 550 etiketsiz benzersiz aday arasından tekrar seçebilir; `train_test_split` ilaç bazlı değil satır bazlıdır. Yeni doğrulama tasarımı zorunlu.
6. `UniProt_ID` ilk harfinden türetilen `kalite_skoru` XAI tablosunda en önemli özellik çıkmıştı. Kaldır ve modeli yeniden eğit.

## Nihai denetim hükmü
V7 için yeni ham kaynak yığınını genişletme. Önce yalnız **DrugBank XML + SIDER + drug links + PubChem** ile kohortu yeniden kur; mevcut **STRING (insan/E. coli)** PPI'sını ancak gerçek mesaj geçiren model ablation'ında değerlendir. Protein sekansı için önce XML'yi temiz oku. Yeni ilaç sayısı, yalnız benzersiz doğrulanmış antibakteriyel etkin madde / pozitif etiketli ilaç / uygun özellikli ilaç olarak ayrı ayrı raporlanır.
