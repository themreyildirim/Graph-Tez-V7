# WP13_EXTERNAL_REFERENCE_COMPARISON_v1 — Tedizolid / SIVEXTRO KÜB

## Sonuç ve kapsam

Kilitli ilk10'un tamamı, ortak201'in tüm skorları,50 bireysel model/PT açıklaması ve300gerçek SHAP katkısı korunarak karşılaştırıldı. İlk10'da **6 çeviri/eşanlam adayı,2 ilişkili, eşdeğerliği doğrulanmamış kavram,1 yalnız sınıf uyarısı,1 eşleme saptanmayan PT** var. Hepsi uzman onayı açısından PENDING; klinik doğruluk/başarı yüzdesi üretilmedi. “Destek” burada ancak kaynakta açık terim bulunması/anotasyon adayı anlamındadır; onaylı klinik eşdeğerlik değildir.

EXPLORATORY_EXTERNAL_LABEL_ISOLATED korunur. Hazırlık aramasında istenmeyen güvenlilik parçacıklarına maruziyet nedeniyle STRICT_ANALYST_BLINDNESS_COMPROMISED silinmedi. Bu çalışma tam araştırmacı-kör veya genel dış validasyon değildir.

## Kilit, kronoloji ve koruma

Prediction SHA-256: `301a116e8f7de4c40c3d10fbbd2e4a122689f8319d82f36eb6183f4b8b0de2f1`

Explanation SHA-256: `db756d0a8a34de7be962e2dacde7be399b6b10bb868cb35798ab4be76ec8a0c1`

Precommit ve pre-explanation dosyaları,5 model/metadata/scaler/head/girdi kaynakları,1294bireysel skor ve201ortak skor,10hedef,50açıklama,300katkı yeniden hash doğrulandı.1.069önceki dosya koruma kapsamındadır; tüm disk için iddia yok. Tahmin2026-11-08T23:22:47Z ve daha sonraki açıklama kaydı, bu referansın alınmasından önce gelir. Tam saatler before_reference_checks.json'dadır. Yerel manifest/hash kronolojisi bağımsız zaman damgası veya geçmiş analist bilgisinin yokluğuna kanıt değildir. İlk kod yürütmesinde gizli dosya koruyucusu herkese açık .gitignore'u da reddetti; PDF açılmadan yalnız bu allowlist hatası düzeltildi. Gerçek hash uyuşmazlığı olmadı. Hücre terimi Prürit/Prüritik alt-dize çakışması tam satır ankrajıyla engellendi; eski veriler değiştirilmedi.

## Gerçek belge

Kullanıcı sağladığı PDF367.220bayt/15fiziksel sayfa. Ham SHA-256 `5af224b13e1724fea94fb778dd492bcfc310a06d02f92abc73a2ba4668a5fd56`. Ham kopya reference/ klasöründe; asıl Downloads dosyası değişmedi. Bütün15sayfa PyMuPDF2.1 text/flags195/sort=False ile çıkarıldı; OCR uygulanmadı, boş sayfa atlanmadı. Sayfa6–8 görsel olarak sütunlarıyla kontrol edildi. Her hücre fiziksel sayfa, quote-ID, SHA ve değişmemiş metnin Python Unicode [start,end) aralığına bağlıdır; byte/görsel koordinat indeksi değildir.

Ürün: SIVEXTRO200mg/flakon **tedizolid fosfat**, IV infüzyonluk liyofilize toz; sulandırılınca50mg/mL. Tahmin **DB14569aktif tedizolid** üzerinden kilitlenmişti; DB09042fosfat NOT_RUN. Sayfa8/10ön ilaç→aktif dönüşümü bildirir, birebir molekül/formülasyon/doz eşitliği kurmaz.4.8güvenlilik tabanı oral ve/veya IV havuzudur; yalnız IV advers reaksiyon sıklığı diye sunulmaz. İlk ruhsat27.03.2019; KÜB yenilenme tarihi boş. PDF metadata2019tarihleri güncellik kanıtı değildir; currentness/publisher authenticity NOT_VERIFIED. Kaynağın m.2 ve m.6.1yardımcı madde ayrıntıları farklı kapsamlarla listelenir; bu çalışmada yeni yardımcı madde eşdeğerliği çıkarılmadı.

## Kilitli ilk10

|rank|class_id|term_tr_editorial|record_ranking_score|source_terms|reference_status|
|---|---|---|---|---|---|
|1|C0011991|İshal|0.864200|Diyare|Çeviri / eşanlam adayı|
|2|C0015230|Döküntü|0.855534|Döküntü|Çeviri / eşanlam adayı|
|3|C0002792|Anafilaktik şok|0.854920|—|Eşleme saptanmadı; negatif değil|
|4|C0042963|Kusma|0.847858|Kusma|Çeviri / eşanlam adayı|
|5|C0000737|Karın ağrısı|0.823995|Karın ağrısı|Çeviri / eşanlam adayı|
|6|C0687713|Gastrointestinal ağrı|0.823995|Karın ağrısı|İlişkili; eşdeğerlik doğrulanmadı|
|7|C0020517|Aşırı duyarlılık|0.821030|İlaca aşırı duyarlılık|İlişkili; eşdeğerlik doğrulanmadı|
|8|C0033774|Kaşıntı|0.817670|Prürit  /  Genel prürit  /  Alerjik prürit|Çeviri / eşanlam adayı|
|9|C0040034|Trombositopeni|0.816634|trombositopeni  /  platelet düşüşü|Yalnız sınıf uyarısı|
|10|C0042109|Ürtiker|0.805517|Ürtiker|Çeviri / eşanlam adayı|

İshal↔Diyare, kusma, döküntü, karın ağrısı, prürit ve ürtiker çeviri/eşanlam adaylarıdır. Aşırı duyarlılık hedefi, **ilaca** aşırı duyarlılıktan daha geniştir; gastrointestinal ağrı, karın ağrısıyla birleştirilmedi. Anafilaktik şok, aşırı duyarlılık veya belgedeki septik şok ifadesinden türetilmedi. Trombositopeni sayfa3'te oksazolidinon sınıfının başka üyesine ait uyarıda; sayfa2'deki platelet düşüşü ayrı laboratuvar değişimidir. Doğrudan4.8ürün trombositopeni kaydı ilan edilmedi.

## Tüm201, kaynak kapsamı ve ilk10 dışında kalanlar

comparison201.csv/json, beş model skorunu, eski ortalamayı/sırayı ve ayrı kaynak durumunu içerir.1294eski bireysel skor dosyasının hiçbiri değişmedi.201'de38çeviri/eşanlam adayı,21yalnız ilişkili geniş/dar/farklı terim,3yalnız sınıf,3yalnız ilaç uyarısı,136eşleme saptanmayan hedef var. Bunlar tamamlanmış tıbbi terminoloji taraması değildir; açık70anotasyon satırının sonuçlarıdır. Kaynakta tam onaylı birebir klinik eşleşme ilan edilen kayıt0. relation alanları translation/synonym/target broader/narrower/source narrower/related distinct biçiminde ayrıdır.

76özgün4.8tablo hücresi (7yaygın,69yaygın olmayan) klinik76bağımsız yan etki sayısı değildir. Özet paragrafın tekrarı yeni kayıt sayılmadı. Genel prürit ve nitelemesiz prürit farklı hücre/sıklıkla korunur. Ortak201'e/ilk10'a eşlenemeyen hücreler all_reference_terms_target_coverage.csv'de; ilk10adayı bulunmayan67hücre reference_terms_outside_top10.csv'de. Örneğin bulantı kaynakta en sık bildirimlerdendir ama ortak201başlığında yoktur; hedef sonradan eklenmedi. Aynı karın ağrısı hücresinin hem abdominal pain hem daha geniş GI pain adayı olması iki bağımsız ürün kanıtı sayılmaz. Alt terimler, genel kavramlar, laboratuvar ve tanı, injection/infusion bölgesi, üst/alt anatomik kapsam otomatik eşitlenmez.

Çapraz eşleme bu referans görüldükten sonra açık gerekçelerle oluşturulan **ajan inceleme adayıdır**. Yeni web/yan etki veri tabanı/lisanslı MedDRA çeviri kaynağı kullanılmadı. İnsan/uzman human_review_TEMPLATE.csv'de adayın anlam, ürün/sınıf ve sıklık kapsamını ayrıca kaydetmelidir. Ajan yorumu resmî insan onayına dönüştürülmedi.

## Sıralama değerlendirmesi neden hesaplanmadı?

Uzman doğrulanmış eşleme alt kümesi0, tek aktif molekül ve farklı fosfat ürün/karma uygulama kaynağı var. KÜB'de yokluk gerçek negatif değildir. Bu koşullarda precision@10, recall, AP, AUROC, duyarlılık/özgüllük veya klinik başarı oranı için geçerli altın standart yok: **NOT_CALCULABLE**. Yalnız gözlemsel terim örtüşmesi ve sıralar betimlenir.38aday/201ve6aday/10 oranları semantik doğruluk ya da model başarı yüzdesi olarak sunulmaz. Bağımsız klinik genelleme kanıtı yoktur.

## Gerçek SHAP ve kullanıcı sunumu

İlk10hedefin tamamının mevcut50model/PT ve300katkısı gösterilir. Her modelin base+SHAP toplamı önceki kilitli logitle uyumlu kalır; yeni SHAP, tahmin tekrarı veya model seçimi yok. Pozitif/negatif katkı yalnız ilgili LR logitinin kendi train-only background'una göre yönüdür. Maske kimyadan ayrıdır; beşsigmoid ortalaması tekLRlogiti/ensembleSHAP değildir. Kaynakta olay geçmesi SHAP'ın kimyasal/biyolojik nedeni olarak açıklanmadı. Tam50Türkçe deterministik paragraf önceki immutable Turkish_verbal_explanations.json'dan okunur.

Eski FINALv2uygulama dosyası korunur; yeni FINALv3'te “Tedizolid dış tahmin deneyi” modu vardır. İki sütunda kayıtlı B1skoru/SHAP ile sonradan açılan KÜB alıntısı ayrı görünür. Seçim CUI/fold ile eşleşir; kaynak sayfası/quote-ID/aralık görünür. Grafikler yeni model sonucu değil, gerçek kilitli çıktının sunumudur. Lokal sunucu QAport8513; kullanıcı launcher varsayılan8501. Ekran kanıtları ayrı browser_QA kaydında, gerçek localhost'tan alınır; temsili UI üretilmez.

## Çıktılar, test ve durma

29kaynak/kilit/scope/skor-ayrımı testi reference_tests.log'da. UI akışı ayrıca gerçek Streamlit ve tarayıcı üzerinden denetlenir. Çalıştırılmış notebook: WP13_EXTERNAL_REFERENCE_COMPARISON_v1.ipynb.3karşılaştırma görseli ve7orijinal sayfa renderı, kaynak/iddia CSV/JSON, insan inceleme şablonu, ayrı referans sözleşmesi ve finalmanifest üretilir. Önceki WP00–WP13, QA, modeller, PDF'ler ve insan durumları değişmez. run_statuseski baytları aynen arşivlenir.

**STOP:** yeni training/prediction forward/SHAP/API, dış model veya başka referans incelemesi yapılmadı. Kaynak eşlemesi/ürün kapsamı için insan incelemesi bekleniyor. Klinik doğruluk veya mekanizma sonucu çıkarılmadı.


## Nihai QA eki

Nihai kaynak/kilit/izolasyon kontrolü **36/36 PASS**, Streamlit AppTest **7/7 PASS**. Önceki29test logu korunur; final log ayrı dosyadır. Notebook6çalıştırılmış kod hücresidir ve gerçek tarayıcı ekranlarını da içerir.6sunum ekranı screenshots/02–07 dosyalarıdır;01ilk ara ekran olarak ayrıca saklandı. İlk host AppTest denemesi testin st.markdown metnini okuma kapsamına almaması nedeniyle false-failure verdi; arayüz/sayısal sonuç değiştirilmeden test okuması düzeltildi ve ayrı rerun logu üretildi. Kısıtlı yürütme ortamındaki ilk sunucu/testrunner yerel port açmadı; kesin neden UNKNOWN. Kullanıcı uygulamaları durdurulmadı, bağımlılık kurulmadı. Gerçek ekran denetimi normal localhost QAport8513 üzerinden tamamlandı. Kullanıcı launcher varsayılan8501.

Çapraz sayfa sınıf cümlesi class_scope_bridge.json ile sayfa2sonundan sayfa3uyarısına bağlanır.50mevcut açıklama ve kaynak durumu model_reference_explanations50.csv/json içinde ayrı sütunlardadır. SHAP metnindeki numpy scalar yazımı arayüzde yalnız tip sarmalayıcısı kaldırılarak gösterilir; ham immutable paragraf ve sayısal değerler değişmez. TümPROVISIONAL ve insanPENDING durumları korunur.

Çalıştırma: normal PowerShell'de proje kökünden `& ".\scripts\WP13_Start_FINAL_DEMO_v3.ps1"` ve tarayıcıda localhost:8501. QAörneği mevcut localhost:8513 adresindedir. “Çalışma alanı → Tedizolid dış tahmin deneyi” seçilir. Önceki demosu aynı v3içinden açılır; eski v2dosyası değişmedi.
