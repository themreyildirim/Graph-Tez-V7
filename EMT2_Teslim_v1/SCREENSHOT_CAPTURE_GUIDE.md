# Gerçek localhost ekranları · EMT2 v4

Adres: http://127.0.0.1:8527 · Başlatıcı: [DEMO_BASLAT.ps1](DEMO_BASLAT.ps1). Var olan sunucu çalışıyorsa aynı portta ikinci kez başlatmayın. Proje kökündeki kayıtlı dosyalar gereklidir. Tarayıcı: Chromium/Chrome, 1640×1060. Her görsel canlı arayüzden alınmıştır; model veya kaynak tekrar üretilmemiştir.

|Dosya / önerilen ek şekli|İlaç|PT|Sekme|Seçim veya filtre|Görsel açıklaması|Tez §|Slayt|
|---|---|---|---|---|---|---|---|
|[E1 · 01_ana.png](ekranlar/01_ana.png)|ERİTRO|—|İlaç ve belge|PDF kapalı|Ürün bileşimi ve ana etkin madde ayrımı|5.12|15|
|[E2 · 02_eritro.png](ekranlar/02_eritro.png)|ERİTRO|—|Prospektüs karşılaştırması|Türkçe prospektüs açık; ilk aday|Nefes darlığı, sayfa 6, kaynak sıklığı|5.10|12|
|[E3 · 03_monodoks.png](ekranlar/03_monodoks.png)|MONODOKS|—|Prospektüs karşılaştırması|Türkçe prospektüs açık; ilk aday|Süperenfeksiyonlar, ürün/sınıf ve kaynak sayfası|5.10|12|
|[E4 · 04_gnn.png](ekranlar/04_gnn.png)|MONODOKS|C0000731|Yan etki tahminleri|Primary own-fold|A1P1 kayıtlı hedefleri ve sıralama|5.12|15|
|[E5 · 05_maske.png](ekranlar/05_maske.png)|MONODOKS|C0000731|Model açıklanabilirliği|Sabit payda bölümüne kaydır|A1P1 gerçek mesaj katkıları|5.8|10|
|[E6 · 06_shap.png](ekranlar/06_shap.png)|MONODOKS|C0000731|Model açıklanabilirliği|B1 bölümüne kaydır|Aynı ilaç için ayrı lojistik modelin SHAP grafiği|5.8|10|
|[E7 · 07_yontem.png](ekranlar/07_yontem.png)|Tedizolid|—|Tedizolid dış tahmin deneyi|Sayfanın üstü|Kimya kolu, beş model, dış deney sınırı|4.10|13|
|[E8 · 08_ilk10.png](ekranlar/08_ilk10.png)|Tedizolid|İlk 10|Tedizolid dış tahmin deneyi|İlk tablo|Model sırası, skor ve gerçek KÜB terimi|5.11|14|
|[E9 · 09_skorlar.png](ekranlar/09_skorlar.png)|Tedizolid|C0011991|Tedizolid dış tahmin deneyi|İshal|Beş ayrı skor; ortalama ≈0,864|5.11|13|
|[E10 · 10_dis_shap.png](ekranlar/10_dis_shap.png)|Tedizolid|C0011991|Tedizolid dış tahmin deneyi|Model 1; SHAP bölümüne kaydır|HBD artırıcı; HBA azaltıcı; logit ölçeği|5.11|13|
|[E11 · 11_kub.png](ekranlar/11_kub.png)|Tedizolid|C0011991|Tedizolid dış tahmin deneyi|İshal; sağ sütun|Diyare, fiziksel s.7, ürünün oral/IV havuzu|5.11|14|
|[E12 · 12_eslenmeyen.png](ekranlar/12_eslenmeyen.png)|Tedizolid|C0002792|Tedizolid dış tahmin deneyi|Anafilaktik şok|Eşleme yok; gerçek negatif değil|5.11|14|
|[E13 · 13_pdf.png](ekranlar/13_pdf.png)|Kayıtsız örnek PDF|—|Yan etki tahminleri|Prospektüs PDF yükle → build/ornek.pdf|B1/GNN için NOT_SUPPORTED; yeni çıkarım yok|5.12|15|
|[E14 · 14_sinirlar.png](ekranlar/14_sinirlar.png)|Tedizolid|C0002792|Tedizolid dış tahmin deneyi|Üst yöntem uyarısı|Araştırmacı körlüğü ve insan inceleme sınırı|6.3|17|

Canlı sıra: ERİTRO kaynağı → kayıtlı PT ve mesaj maskeleri → tedizolid ilk 10 → ishal modeli ve KÜB sayfası → anafilaktik şok → bilinmeyen PDF. Sunum sırasında internet veya model hizmeti gerekli değildir.