# EMT2 son kontrol · 09 Kasım 2026

**Sonuç:** proje kayıtlarına dayalı raporlama ve sunum paketi teknik kontrolleri geçti. Klinik veya idari onay anlamına gelmez. Yeni model eğitimi, dış ilaç çıkarımı veya ücretli model çağrısı yapılmadı.

| Denetim | Sonuç | Kanıt |
|---|---|---|
|Önceki içeriklerin korunması|PASS|4581 dosya, değişen []|
|tedizolid_B1_external_v1/prediction_lock.json|PASS|301a116e8f7de4c40c3d10fbbd2e4a122689f8319d82f36eb6183f4b8b0de2f1|
|tedizolid_B1_SHAP_v1/explanation_lock.json|PASS|db756d0a8a34de7be962e2dacde7be399b6b10bb868cb35798ab4be76ec8a0c1|
|WP13_EXTERNAL_REFERENCE_COMPARISON_v1/reference_comparison_lock.json|PASS|89cc467d8677605e0a0b136ad10be3e72be98d392a284c583bcc83361c726b5a|
|OOXML paketleri|PASS|6 DOCX ve 1 PPTX; CRC ve iç arşiv|
|EMT1_TO_EMT2_CHANGELOG.pdf|PASS|4 fiziksel sayfa; metin katmanı|
|EMT2_FINAL_REPORT.pdf|PASS|28 fiziksel sayfa; metin katmanı|
|Rapor içeriği|PASS|Örnek çapalar, gerçek değerler, altı bölüm ve kaynak izleri|
|EMT2_JURY_QA.pdf|PASS|4 fiziksel sayfa; metin katmanı|
|EMT2_PRESENTATION.pdf|PASS|18 fiziksel sayfa; metin katmanı|
|EMT2_PROJE_BILGI_FORMU.pdf|PASS|2 fiziksel sayfa; metin katmanı|
|EMT2_SPEAKER_NOTES.pdf|PASS|3 fiziksel sayfa; metin katmanı|
|GRAPH_TEZ_V7_THEORY_AND_DEFENSE_GUIDE.pdf|PASS|12 fiziksel sayfa; metin katmanı|
|Sunum ve konuşmacı notları|PASS|18 slayt, 18 gerçek not ve 18 PDF sayfası|
|Düzenlenebilir performans grafikleri|PASS|PPTX içinde en az dört yerel grafik|
|Yeni notebook|PASS|5 yürütülmüş hücre, kaynaklardan üretilmiş tablolar ve resimler|
|Gerçek tarayıcı akışları|PASS|14 gerçek Chrome ekranı; upload ve eşlenmeyen PT dahil. Son iki görünüm durağan durumda yeniden kaydedildi.|
|Dış karşılaştırma|PASS|10 PT / 6–2–1–1; insan kararları değiştirilmedi.|
|Figür kaynakları|PASS|15 rapor şekli; 308 manifest kaydı|
|CSV / JSON iddia eşleşmesi|PASS|39 kanıt satırı|

Kaynak sınırı: hash karşılaştırması belirtilen 4.581 eski proje dosyasını kapsar. Bütün diski, .env dosyasını veya büyük ham kaynakları kapsamaz. Tarihsel eğitim/optimizer ve eski QA testleri yeniden çalıştırılmadı; geçmiş başarı kayıtları yeni test sonucu diye sayılmadı. Yeni kontroller, yürütülmüş notebook, gerçek tarayıcı akışı ve paket okuma testleri ayrıdır.

Word ve PowerPoint PDF çıktıları açıldı; sayfalar görselleştirilerek yerleşim incelendi. Büyük kaynak graf ve tablo ayrıntıları için yerel görsel asılları figür manifestindedir. Görsel incelemede bilgi formu sayfa akışı ve son iki gerçek tarayıcı görüntüsü düzeltildi. Kaynak iddiaları insan QA yerine geçmez.

Açık kararlar: [uzman ve idari işlemler](EMT2_MISSING_EVIDENCE_AND_ACTIONS.md).
## Teslim regresyonları

Altı ayrı salt okunur regresyon testi 6/6 geçti. [Test kodu](demo/test_teslim_v4.py) · [Çalıştırma günlüğü](REGRESYON_TESTLERI.log) · [Kod ve sayı izleme kılavuzu](YENIDEN_INCELEME.md).
