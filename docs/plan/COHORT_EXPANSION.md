# Ek veri yığını kurmadan ilaç sayısını artırma protokolü

## Mevcut verinin sınırları
Eski dosyalar: `sadece_antibiyotikler.csv` 209 satır (125 `DBSALT`), `ilac_feature_v5_atc.csv` 56 ilaç, `ilac_yan_etki_v5.csv` 53 ilaç ve `ilac_protein_eslesmesi_v6.csv` 41 ilaç; eski ortak kesişim 38. **Bunlar farklı kümeler**: 209 ≠ 209 tekil antibiyotik etken madde. V6 havuzunda antifungal ve farklı sınıflardan ürünler var; saf J01 cohorte ayırınca sayı düşebilir.

## Sıralı iyileştirme

**G1. DrugBank kimlik kanonikleştirme**
- Primary DB, secondary ID, DBSALT ve CAS/CID/active ingredient ilişkilerini `full database.xml` üzerinde doğrula.
- Kimyasal yapı/kök ingredient aynı mı incele; karşılık bulamadığında `unresolved` olarak tut, rastgele bağlama.
- `J01` gerçek ATC kapsamına göre ana kohortu belirle; isim son eklerinden tahmin etme.

**G2. SIDER pozitiflerini geri kazan**
- `meddra_all_se.tsv` ve `drug links.csv` içinde stereoisomer/flat CID eşleme farkını belgeleyerek ilaç↔yan etki birleştir.
- PT/LLT ve 35 seçilen hedefin eşlemesini denetle, benzer adları otomatik çakıştırma.
- `known_positive / unlabeled` ayrımını koru; tekil (drug,SE) çiftlerini üret.

**G3. PubChem ve DrugBank kimyasını tamamla**
- Kaybolan CID'ler için kontrollü API isteği ve cache; tuz/etken madde uyuşmazlıklarını kimyasal kimlikle doğrula.
- SMILES ve 5 fizikokimyasal alanın doluluk oranını göster; hesaplanamayanı sıfır diye kodlama.

**G4. Eksik protein hedefine rağmen veri kaybetme**
- **Kimya-only baseline** ile etiketi bulunan ama hedefi olmayan ilaçları ayrı etiketli eğitim havuzunda değerlendirme olasılığı var. GiG protein katmanı tüm ilaçlara zorla doldurulmayacak; `target_missing` mask ve kohort farkı raporla.
- V6'da özellikle Azithromycin, Vancomycin, Doxycycline, Linezolid, Erythromycin gibi *SIDER + kimyası bulunan ama protein ağı V6'da eksik* ilaçlar var. Bunları hatalı 'protein bilinmiyor = hedefi yok' yaklaşımıyla silme.
- Kimyasal özellikleri olsa bile yan etki etiketi olmayan ilaçlar **yalnız inference pool**, supervised eğitim başarısında sayılmaz.

**G5. Kontrollü kazanım ölçümü**
Çıktı `cohort_funnel.csv` ve görsel:
1. DB kayıt / DBSALT / doğrulanmış benzersiz ingredient.
2. J01 doğrulanmış sistemik antibakteriyel ingredient.
3. SIDER'da en az bir hedef etiketli ingredient.
4. 5 kimyasal özelliği bulunan ingredient.
5. Protein hedefi bulunan ingredient.
6. Protein + PPI içinde komşuluk varsa sayısı.
7. `baseline_trainable`, `gig_trainable`, `inference_only` sayıları.

## Yeni kaynaklar?
Bu **sürümde yeni yan etki veri seti edinimi yapılmayacak**. Önce mevcut kapsam iyileştirilsin ve net düşüş/kazanç raporu çıkarılsın. Kalan sınırlamalar yöntemle giderilemiyorsa **yalnızca kullanıcı yeni kaynak ihtiyacına özel onay verirse** ayrı bir genişletme teklifi yazılabilir. OnSIDES, FAERS, DisGeNET ve diğer veri kaynakları mevcut iş paketlerinin önkoşulu değildir.
