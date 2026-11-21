# WP12 — Aktif yol haritasına göre hazırlık ve karar notu

08.11.2026. **Yalnız kapsam/karar hazırlığı. WP12 uygulaması başlamadı.** Bu belge yeni yol haritası, PDF işleme veya kurulum onayı değildir. Esas kaynak `docs/plan/ROADMAP_V7.md` içindeki WP12 satırıdır; kabul edilmiş WP11 sonuçları değiştirilmez.

## Yol haritasının gerçek kapsamı

WP12: **PDF bilgi çıkarımı ve küçük yerel LLM**. Yalnız kullanıcının seçtiği prospektüs PDF'leri; PyMuPDF ile sayfa kaynaklı JSON, düşük parametreli yerel Ollama modülü ve mevcut RDKit kimya doğrulaması. LLM yan etki tahmini yapmaz. `reported_in_PDF` ile `predicted_by_GNN` açıkça ayrılır. WP13'ün arayüz/tez demosu bu aşamanın kendiliğinden genişlemesi değildir.

Önerilen işleyiş, WP12 ayrıca başlatıldığında: seçilen belgeyi kimliği/sürümüyle kaydet → sayfa ve metin aralıklarını koruyarak çıkar → ilaç/etkin madde eşleşmesini incele → kaynak alıntısını ve modelden gelen açıklamayı ayrı göster → doğrulama/test/notebook/rapor → onay için dur. Bu akış mevcut planı somutlaştırır; yeni klinik veri kaynağı veya yeni eğitim hattı eklemez.

## Uygulama öncesindeki açık kararlar

| Karar | Önerilen sınır / kullanıcı değerlendirmesi |
| --- | --- |
| PDF listesi | Tam olarak hangi dosyalar ve belge sürümleri kullanılacak? Bu turda PDF aranmadı, açılmadı veya indirilmedi. Toplu prospektüs/etiket kaynağı eklenmez |
| Belge–ilaç kimliği | Etkin madde, tuz/formülasyon ve marka ayrımı mevcut DrugBank/CID kayıtlarıyla kaynaklı tutulur. Çözülemeyen eşleşme belirsiz kalır; kabul edilmiş kimlik/QC değişmez |
| Çıkarma yöntemi | Önce metin katmanı ve gerçek sayfa numarası incelenecek. Taranmış veya bozuk PDF görülürse OCR ihtiyacı ayrıca karara bağlanacak; sessiz kurulum yapılmayacak |
| Sayfa kaynaklı şema | Önerilen alanlar: belge kimliği/SHA-256, dosya ve sürüm, fiziksel PDF sayfa indeksi, basılı sayfa etiketi varsa ayrı alan, alıntı/metin aralığı, çıkarılan terim, doğrulama durumu ve parser sürümü. Bu turda parser veya veri çıktısı oluşturulmadı |
| Yerel LLM | Donanım/çalışma koşulları ve uygun küçük model, açık WP12 başlangıcında değerlendirilecek. Bu turda model seçimi, Ollama kurulumu, model indirmesi veya servis başlatılması yapılmadı |
| Çıktı semantiği | PDF'de raporlanan bilgi, kaynak metin ve sayfa ile gösterilir. GNN/LR skoru ve SHAP/Δz, mevcut sayısal dosyadan gelir; LLM bu sayıları üretmez veya değiştirmez |

RDKit doğrulaması, metindeki kimyasal kimliğin mevcut onaylı yapı/kimlik kaydıyla uyumu açısından ele alınmalıdır. Belge içinde bulunan yeni veya belirsiz SMILES/kimlik, eski QC-onaylı yapının yerine otomatik geçirilmez. Yeni molekül veya yan etki etiketi üretmek WP12'nin bu hazırlık notuyla yetkilendirilmiş değildir.

## Ayrım ve doğrulama kapısı

Prospektüsten çıkarılan yan etki aynı hedefi tahmin eden modelin girdisine veya geriye dönük eğitim etiketine dönüştürülmez. Mevcut split, hedef sözlüğü, skor, protein/PPI açıklaması ve B1 SHAP sabit kalır. Kaynakta bulunmayan bilgi uydurulmaz; alıntısız LLM iddiası doğrulanmış bilgi sayılmaz. Model çıktıları bireysel klinik risk veya tedavi önerisi değildir.

WP12 uygulandığında gerekli kontroller: dosya hash'i/sürümü ve sayfa hizası; alıntının gerçekten o sayfada bulunması; belirsiz ilaç kimliğinin görünür olması; `reported_in_PDF` ve model çıktısının karışmaması; LLM'nin kaynak veya sayısal katkı uydurmasının reddi; önceki modellerin/QA dosyalarının korunması. Çalıştırılmış Türkçe notebook, gerçek belge örnekleri, kaynaklı JSON ve küçük testler ancak uygulama onayı sonrasında üretilecek.

**Şimdi durulur. WP11 kapanış kanıtları sunulur; WP12 uygulaması için kullanıcı kararı beklenir.**
