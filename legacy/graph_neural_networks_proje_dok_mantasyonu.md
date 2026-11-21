# Graph Neural Networks for Drug-Protein Interaction and Side Effect Modeling
## Proje Tasarım, Mimari ve Metodoloji Dokümantasyonu

Bu doküman, ilaç-protein etkileşimleri ve klinik yan etkilerin modellenmesi amacıyla geliştirilen **Graph-in-Graph (GiG)** mimarisine sahip Derin Graf Sinir Ağı (GNN) projesinin tüm teorik altyapısını, veri mühendisliği kararlarını, matematiksel modellemesini ve değerlendirme protokollerini içermektedir.

---

## 1. Proje Amacı ve Temel Yaklaşım

Projenin temel amacı, bir ilacın protein hedefleri ve biyolojik etkileşim ağları üzerinden klinik yan etkilerini yüksek doğrulukla ve **açıklanabilir (interpretable)** bir şekilde tahmin etmektir. 

Klasik yöntemlerde ilaçlar sadece kimyasal yapılarıyla veya doğrudan yan etki etiketleriyle ele alınırken, bu projede ilacın etki mekanizması (mechanism of action) biyolojik bağlamıyla birlikte bir **Heterojen Graf** yapısında modellenmiştir.

### Temel Kararlar ve Fikirler:
* **Çok Katmanlı Temsil:** İlaç, hedef protein ve yan etki düğümleri arasındaki ilişkiler tek bir düzlemsel yolda (lineer pathwalking) değil, **Temsil Öğrenimi (Representation Learning)** yaklaşımıyla zenginleştirilmiştir.
* **İndüktif (Inductive) Model Tercihi:** Transdüktif modellerin aksine, eğitim sırasında graf içinde yer almayan **yeni/görmediğimiz** moleküller için de tahmin üretebilen bir indüktif yapı tercih edilmiştir.

---

## 2. Veri Entegrasyonu ve Kimlik Eşleme (ID Mapping Hub)

Proje, 5 farklı açık kaynak veri tabanının entegrasyonu üzerine kurulmuştur. Veri mühendisliği aşamasındaki en büyük zorluk, her veritabanının farklı bir kimlik (ID) ve veri formatı kullanması olmuştur.

### 2.1 Entegre Edilen Veri Kaynakları

1. **DrugBank (XML / ~1.9 GB):** İlaçların birincil ID'leri (`DB00316` vb.), ATC kodları ve hedef protein bağlantıları çekilmiştir.
2. **PubChem (CSV):** İlaçların kimyasal ve fiziksel özellikleri Compound ID (`CID`) üzerinden alınmıştır.
3. **UniProt (FASTA & Tablo):** Proteinlerin erişim numaraları (`Accession ID`), gen sembolleri ve amino asit dizilimleri çekilmiştir.
4. **STRING (TSV):** Protein-Protein Etkileşim (PPI) ağı ve etkileşim güvenilirlik skorları (`Ensembl ID`) toplanmıştır.
5. **SIDER (TSV):** İlaçların klinik yan etki kayıtları (`STITCH CID` ve `UMLS` konsept kimlikleri) target olarak kullanılmıştır.

### 2.2 Merkezi Kimlik Köprüleme (ID Mapping)

Girdi verilerinin PyTorch Geometric `HeteroData` yapısına aktarılabilmesi için heterojen bir köprüleme katmanı tasarlanmıştır:

| Ortak İlaç Düğümü ID | Ortak Protein Düğümü ID |
| :--- | :--- |
| **`DB00316`** (DrugBank) | **`P35354`** (UniProt) |
| $= 1983$ (PubChem CID) | $= \text{ENSP00000361234}$ (STRING) |
| $= \text{CID10000316}$ (SIDER) | |

---

## 3. Düğüm Özellik Mühendisliği (Node Feature Engineering)

Modelin biyokimyasal mantığı kavrayabilmesi adına ham veriler sayısal vektör uzaylarına izdüşürülmüştür.

### 3.1 İlaç Temsili (25 Boyutlu Vektör)
* **Fizikokimyasal Özellikler (5 Boyut):**
  * **MW (Moleküler Ağırlık):** Molekül büyüklüğü ve hücre zarından geçiş kapasitesi.
  * **LogP (Lipofiliklik):** Yağda çözünürlük ve vücut içi dağılım katsayısı.
  * **HBD / HBA:** Hidrojen bağı donör ve akseptör sayıları (proteine tutunma kapasitesi).
* **ATC Sınıflandırması (20 Boyut):** İlacın anatomik ve terapötik işlevini tanımlayan kategorik kodlar.

### 3.2 Protein Temsili (51 Boyutlu Vektör)
* **Yan Zincir Kimyası (Biyokimyasal Uyum):** İlaç-protein bağlanması temel olarak kimyasal ve elektriksel bir uyum meselesidir. Bu nedenle amino asitler yan zincir karakterlerine göre gruplandırılmıştır:
  * **Asidik (- Yüklü) & Bazik (+ Yüklü):** Elektriksel çekim (mıknatıs etkisi) oluşturan bölgeler.
  * **Hidrofobik (Suyu Sevmeyen):** Yağlı ilaç moleküllerinin (yüksek LogP) tutunmayı tercih ettiği yüzeyler.
* **Yapısal Bileşim:** Dipeptit ve amino asit dizilim oranları.
* **Kalite Skoru:** STRING veritabanından gelen etkileşim güvenilirlik derecesi.

---

## 4. Graph-in-Graph (GiG) Mimarisi ve Matematiksel İşleyiş

GiG mimarisi, iç içe geçmiş iki katmanlı bir mesaj iletim (Message Passing) mekanizması ile çalışır.

### 4.1 İki Seviyeli Mesaj İletimi
1. **İç Ağ (Inner Graph):** Dizi özelliklerinden faydalanılarak her bir protein için özelleştirilmiş bir temsil vektörü öğrenilir.
2. **Bilgi Akış Köprüsü ($\mu_d$):** İlaç $d$'nin hedeflediği proteinlerin temsil vektörlerinin ortalaması alınır:
   $$\mu_d = \frac{1}{|N(d)|} \sum_{p \in N(d)} h_p$$
3. **Zenginleştirilmiş İlaç Temsili:** İlacın kendi 25 boyutlu fizikokimyasal/ATC vektörü ile iç ağdan gelen biyolojik bağlam vektörü ($\mu_d$) birleştirilir (concat/aggregate).
4. **Tahmin Katmanı (Outer Graph Link Prediction):** Zenginleştirilmiş ilaç temsili ile yan etki temsil vektörü birleştirilip Sigmoid fonksiyonundan geçirilerek $[0, 1]$ aralığında bir olasılık skoru hesaplanır:
   $$\hat{y}_{d, se} = \sigma(\text{MLP}(h_d^{\text{enriched}} \mathbin{\Vert} h_{se}))$$

---

## 5. Eğitim Protokolü ve Metodolojik Kararlar

### 5.1 Negatif Örnekleme Stratejisi (1:2 Oranı)
* **Problem:** Veri setinde sadece gözlemlenmiş (pozitif) yan etkiler bulunmaktadır. Modelin sınırı öğrenebilmesi için "olmayan" yan etkilere (negatif örnekler) ihtiyacı vardır.
* **Çözüm:** Her 1 pozitif ilaç-yan etki bağlantısı için **2 adet negatif örnek** rastgele seçilmiştir.
* **Çakışma Önleme:** Bilinen pozitif yan etkiler negatif örnekleme havuzundan kesin olarak ayıklanmıştır.
* **Neden Bire İki?** Tüm gözlemlenmemiş çiftleri (binlerce negatif) eklemek bellek yükünü aşırı artıracak ve aşırı sınıf dengesizliğine yol açacaktı. $1:2$ oranı hem dengeli öğrenmeyi hem de hesaplama verimliliğini sağlar.

### 5.2 Yeniden Üretilebilirlik ve Overfitting Yönetimi
* **Sabit Rastgele Tohum (Random Seed):** Negatif örneklemelerin, başlangıç ağırlıklarının ve $\%80 / \%20$ train-test ayrımının her çalıştırmada birebir aynı kalması sağlanmıştır.
* **Epoch ve Early Stopping:** Model $200$ epoch boyunca eğitilmekte, doğrulama kaybı (validation loss) duraksadığında erken durdurma (early stopping) ile ezberleme (overfitting) engellenmektedir.

### 5.3 Değerlendirme Metrikleri: AUROC ve AUPR
Sınıf dengesizliği içeren biyolojik verilerde tek başına doğrusal başarı (Accuracy) yanıltıcıdır.
* **AUROC (Area Under ROC Curve):** Genel ayırt etme gücünü ölçer.
  $$TPR = \frac{TP}{TP + FN}, \quad FPR = \frac{FP}{FP + TN}$$
  $$\text{AUROC} = \int_{0}^{1} TPR \, d(FPR)$$
* **AUPR (Area Under Precision-Recall Curve):** Azınlıkta olan gerçek pozitif sınıfa odaklanır.
  $$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}$$
  $$\text{AUPR} = \int_{0}^{1} \text{Precision} \, d(\text{Recall})$$

---

## 6. Proje Sınırlamaları ve Gelecek Çalışmalar

1. **Örneklem Büyüklüğü Kısıtı:** 5 farklı veri tabanının kesişimi alındığında filtreyi geçen ilaç sayısı (örn. 38 ilaç) derin öğrenme standartlarına göre kısıtlı kalmaktadır.
2. **Eksik Yan Etki Kayıtları (SIDER Incompleteness):** SIDER'da bir yan etkinin olmaması, o ilacın o yan etkiyi göstermediğini garanti etmez (raporlanmamış olabilir).

### Gelecek Planlar / Çözüm Stratejileri:
* **Ek Kaynak Entegrasyonu:** Veri seyrekliğini azaltmak için ChEMBL ve PubChem Assay verilerinin sürece dahil edilmesi.
* **Çoklu Kaynak Doğrulama:** SIDER verilerinin literatür taraması ve tıbbi veri tabanlarıyla çapraz doğrulamadan geçirilmesi.
* **Açıklanabilirlik (SHAP Analizi):** Model tahminlerinin arkasındaki biyokimyasal nedenleri (hangi LogP değerinin veya hangi proteinin yan etkiyi tetiklediğini) gösteren SHAP analizi eklenmesi.
* **Klinik Karar Destek Arayüzü:** Moleküler özellikleri girilen yeni bir antibiyotiğin olası yan etkilerini ve gerekçelerini sunan bir prototip arayüz geliştirilmesi.