# -*- coding: utf-8 -*-
"""Bolum 6: Deneysel Bulgular.

Butun sayisal degerler dondurulmus QA ciktilarindan alinmistir:
  reports/qa/WP08, WP09, WP10, WP11, WP13, WP14, WP15
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "reports/figures"
TESLIM = ROOT / "EMT2_Teslim_v1"


def bolum6(k):
    k.baslik1("DENEYSEL BULGULAR")

    # ------------------------------------------------------------ 6.1
    k.baslik(2, "Kohort ve Kapsam")
    k.govde_metni(
        "Kohortun kurulmasında belirleyici olan, kimlik kabullerinin aday havuzunu "
        "nasıl daralttığıdır. Ham aday listesindeki 209 kimliğin 84’ü ana DrugBank "
        "kaydı, 125’i tuz kaydıdır; her tuz ayrı bir ana kayda çözülmüş ve hiçbiri "
        "diğer 84 kaydı yinelememiştir. Tuz sayısının tek başına kaç ana etkin madde "
        "kaldığını belirlemeye yetmediği bu adımda görülür.")
    k.cizelge(
        "İlaç kohortunun aşamaları; birimler her satırda yeniden tanımlanır.",
        [["Aşama", "Birim", "Sayı"],
         ["DrugBank ana kaydı", "Ana kayıt", "19.830"],
         ["J01 ATC kodu taşıyan", "Ana kayıt", "237"],
         ["Yalnız kombinasyon kodlu kayıtlar çıkarıldıktan sonra", "Aday", "233"],
         ["PubChem CID köprüsü doğrulanan", "Aday", "167"],
         ["SIDER stereo-PT eşleşmesi bulunan", "İlaç", "62"],
         ["Kimyasal model kurulabilen", "İlaç", "54"],
         ["Gözlenen benzersiz ilaç–PT çifti", "Çift", "6.416"],
         ["Kaynak terim evreni", "PT (CUI)", "1.061"]],
        [8.0, 3.4, 2.6])
    k.sekil(FIG / "WP03/03_identity_flow.png",
            "J01 adaylarında ana kimlik ve kaynak eşleşmesinin kapsamı.", 12.5)
    k.govde_metni(
        "Doğrulanan 167 adayın 62’sinde kaynak eşleşmesi bulunmuştur. Kimyasal "
        "kalite denetimi çift yönlü çalışmıştır: önceden yapısı eksik görünen 21 "
        "ilacın 18’i geri kazanılırken, önceden kullanılabilir görünen 41 kaydın "
        "beşi yeniden incelemeye ayrılmıştır. Sonuç olarak 62 ilaçtan 54’ünde "
        "kimyasal model kurulabilmiştir. Bu ayrım önemli bir tercih getirir: "
        "kesinliği düşük bir yapıyı zorla kabul etmek kimya kapsamını sayısal "
        "olarak büyütür, ancak üretilen skorun hangi moleküle ait olduğunu "
        "belirsizleştirir.")
    k.govde_metni(
        "Kimya tablosundaki 56 ilacın 12’sinde ATC vektörünün tamamı sıfırdır. Bu "
        "sıfırlar biyolojik yokluğu değil, kayıt ya da eşleme kapsamındaki boşluğu "
        "gösterir. Benzer biçimde, etiketsiz bir ilaç–terim çifti doğrulanmış bir "
        "olumsuzluk değildir; bu çalışmada negatif örnekleme yapılmamış, gözlenen "
        "kayıt ile bilinmeyen ayrımı korunmuştur.")
    k.govde_metni(
        "İlaç–protein ilişkileri tekilleştirildiğinde 457 farklı çift elde edilir. "
        "Bir çift birden çok rol taşıyabildiği için tipli ilişki sayısı 476’dır. "
        "Bunların 241’i hedef, 135’i taşıyıcı, 78’i enzim ve 22’si taşıyıcı protein "
        "rolündedir. 62 ilacın 60’ında en az bir rol, 55’inde hedef ilişkisi vardır. "
        "Kaynakta 141 accession’a karşılık 140 benzersiz dizi bulunur. Dolayısıyla "
        "yalnız açık bir hedefi olan ilaçlara veya yalnız benzersiz dizilere "
        "indirgenen bir analiz, sırasıyla rol kapsamını veya kimlik ayrımını "
        "kaybeder.")
    k.cizelge(
        "Destek eşiğine göre insan protein ağının kapsamı; 63 düğüm sabittir.",
        [["Destek eşiği", "Benzersiz yönsüz çift", "İzole düğüm"],
         ["150", "1.200", "—"],
         ["400", "583", "2"],
         ["700 (eğitimde kullanılan)", "184", "12"],
         ["900", "79", "27"]],
        [5.0, 5.4, 4.0])
    k.sekil(TESLIM / "graf_v1/derece.png",
            "İnsan altgrafında komşu sayısının dağılımı; 63 protein, 184 yönsüz "
            "çift.", 12.0)
    k.govde_metni(
        "Eğitimde kullanılan 700 eşiğindeki ağ 63 düğüm ve 184 yönsüz kenar içerir. "
        "Yoğunluk 0,0942’dir. On dört bağlı bileşenin on ikisi izolattır; en "
        "büyüğü 49 düğümlüdür ve bu bileşende çap 5, ortalama en kısa yol 2,458’dir. "
        "Ortalama kümeleme 0,3723, sabit tohumla hesaplanan modülerlik 0,4149’dur. "
        "Ağın betimsel olarak bağlantılı görünen bölümleri izleyen deneyin "
        "gerekçesini oluşturur; bu bağlantıların sıralamaya yarar sağlayıp "
        "sağlamadığını ise yalnız model karşılaştırması gösterebilir.")

    # ------------------------------------------------------------ 6.2
    k.baslik(2, "Referans Modellerin Başarımı")
    k.govde_metni(
        "Önce, bir ilacı tanımanın terimlerin genel sıklığını bilmeye göre ne "
        "kattığı incelendi. Ortak 54 ilaçta kimyasal lojistik modelin birincil "
        "ilaç-makro ortalama kesinliği 0,6556, aynı eğitim uygunluğuna sahip sıklık "
        "referansının ise 0,6438’dir. Eşleştirilmiş fark +0,0119, koşullu %95 aralık "
        "−0,0021 ile +0,0274 arasındadır. **Aralık sıfırı içerdiği için kimyasal "
        "bilginin sıklık referansı üzerindeki kazancı bu örneklemde "
        "kesinleşmemiştir.**")
    k.cizelge(
        "Ortak 54 ilaçta referans modellerin ilaç-makro ortalama kesinliği.",
        [["Model", "Birincil", "Stres", "Kendi sıklık referansı (birincil)"],
         ["B1 kimya + lojistik", "0,6556", "0,6319", "0,6438"],
         ["B2 kimya + protein", "0,6262", "0,5997", "0,6466"]],
        [5.2, 2.6, 2.6, 4.6])
    k.sekil(FIG / "WP08/final_closure_v1/01_accepted_paired_AP.png",
            "Ortak 54 ilaçta sıklık ve lojistik modellerin birincil ve stres "
            "sonuçları.", 12.5)
    k.govde_metni(
        "B2, protein rolleri sayesinde kimyasal modelin skorlayamadığı yedi ek ilacı "
        "kapsar. Buna karşılık aynı 54 ilaçta B2’nin başarımı daha düşüktür: "
        "B2−B1 farkı −0,0294 ve aralığı −0,0511 ile −0,0093’tür; bu fark ayırt "
        "edilebilirdir. Böylece protein özetleri iki ayrı ölçütte farklı sonuç "
        "vermiştir. Bir araştırmacı daha fazla ilaç için inceleme başlatabilir, "
        "ancak ortak ilaçlarda kimya modelinden daha iyi bir ilk terim listesi elde "
        "edememiştir. Bu bulgu proteinlerin biyolojik önemini ölçmez; rol başına "
        "ortalama ile temsil edilen bilginin bu veri ve bu öğrenici içindeki "
        "sonucunu ölçer.")

    # ------------------------------------------------------------ 6.3
    k.baslik(2, "Protein Ağı Topolojisinin Katkısı")
    k.govde_metni(
        "Protein bilgisinin kullanılmasıyla proteinler arasındaki gerçek topolojinin "
        "kullanılması aynı deneysel iddia değildir. Aynı kodlayıcı gerçek insan "
        "ağıyla, ağ kapatılarak ve üç karıştırılmış ağla çalıştırılmıştır. Birincil "
        "ilaç-makro ortalama kesinlik gerçek bağlantılarda 0,642880, ağ kapalıyken "
        "0,643021, karıştırılmış üç modelin ölçüt ortalamasında 0,643259’dur.")
    k.cizelge(
        "Protein ağı topolojisini değiştiren deneyin eşleştirilmiş farkları.",
        [["Karşılaştırma", "Fark", "%95 aralık", "Ayırt edilebilir mi?"],
         ["Gerçek ağ − ağ kapalı", "−0,000142",
          "[−0,003611; +0,003248]", "Hayır"],
         ["Gerçek ağ − karıştırılmış", "−0,000379",
          "[−0,002039; +0,001310]", "Hayır"]],
        [5.0, 2.4, 4.6, 3.0])
    k.sekil(FIG / "WP09/final_closure_v1/02_frozen_primary_result.png",
            "Ortak ilaçlarda protein ağı topolojisini değiştiren deneyin "
            "dondurulmuş sonuçları.", 12.5)
    k.govde_metni(
        "Kayıtlı modellerin ileri geçiş ve gradyan kontrolleri, protein ağı "
        "mesajının hesaplamaya **gerçekten girdiğini** doğrulamıştır: kenarlar "
        "silindiğinde protein temsilleri ölçülebilir biçimde değişmiş, mesaj yolu "
        "sıfırdan farklı gradyan taşımış ve ağ kapalı koşulda bu iki değer de "
        "sıfır olmuştur. Buradaki sonuç, gerçek ağın veri akışında kullanıldığı, "
        "ancak kapalı veya karıştırılmış koşullara göre **ek sıralama yararının "
        "gösterilemediğidir**. Seyrek insan altgrafı bu bulguyu yorumlarken "
        "önemlidir; yararın neden sınırlı kaldığını tek başına kanıtlamaz.")

    # ------------------------------------------------------------ 6.4
    k.baslik(2, "Atom ve Protein Ağı Dallarının Faktöriyel Sonuçları")
    k.govde_metni(
        "Dört koşulda birincil ilaç-makro ortalama kesinlik değerleri A0P0 için "
        "0,642740, A0P1 için 0,643636, A1P0 için 0,645930 ve A1P1 için 0,646234’tür. "
        "Toplam 152 modelin 40 dış modeline ait 143.896 skor yeniden "
        "hesaplandığında en büyük fark 1,11×10⁻¹⁶ olmuştur; bu, kayıtlı skorların "
        "yeniden üretilebilir olduğunu gösterir.")
    k.cizelge(
        "Faktöriyel karşılaştırmada koşullu ana etkiler ve etkileşim.",
        [["Etki", "Fark", "%95 aralık", "Ayırt edilebilir mi?"],
         ["Atom dalı (ana etki)", "+0,002894",
          "[+0,000773; +0,005470]", "Evet"],
         ["Protein ağı dalı (ana etki)", "+0,000600",
          "[−0,001133; +0,002316]", "Hayır"],
         ["Etkileşim", "−0,000591", "[−0,003102; +0,001541]", "Hayır"]],
        [5.2, 2.4, 4.4, 3.0])
    k.sekil(FIG / "WP10/training_v1/04_factorial_contrasts.png",
            "Atom ve protein ağı katkıları: sabit dış bölme tahminlerine koşullu "
            "faktöriyel farklar.", 12.5)
    k.govde_metni(
        "Birincil protokol, moleküler topolojinin aynı mimari içinde küçük bir "
        "katkısını desteklemektedir. Ancak stres protokolünde atom dalının koşullu "
        "karşılaştırmalarının aralıkları sıfırı içerir. Dolayısıyla örneklem "
        "içindeki marjinal kazanım, yeni bir iskelette güvenilir bir artış veya iki "
        "grafın birlikte kullanımından doğan bir sinerji olarak genişletilemez; "
        "etkileşim terimi de sıfırdan ayırt edilememiştir.")
    k.govde_metni(
        "Burada iki ayrı soruyu karıştırmamak gerekir. Atom dalını kendi mimarisi "
        "içinde açmak küçük bir kazanç sağlar. Buna karşılık en gelişmiş graf "
        "kolunun bağımsız kimya referansıyla farkı yaklaşık −0,009408’dir ve "
        "eşleştirilmiş aralık sıfırı içerir. Bir mimari içindeki iyileşme ile "
        "modeller arası üstünlük farklı iddialardır; bu veride yalnız birincisi "
        "gösterilebilmiştir.")

    # ------------------------------------------------------------ 6.5
    k.baslik(2, "Graph-in-Graph Varyantının Sonuçları")
    k.govde_metni(
        "Eğitimden önce sekiz maddelik sentetik doğrulama kapısı geçilmiş; eklenen "
        "mesajın analitik olarak beklenen değeri ürettiği ve yeni yolun ağırlığı "
        "sıfırlandığında modelin karşılaştırma mimarisiyle aynı protein gömmesini "
        "verdiği gösterilmiştir. Otuz sekiz bağlamın tamamı sorunsuz eğitilmiş, "
        "dondurulmuş karşılaştırma anahtarlarının tamamı karşılanmış ve eklenen "
        "yolun her uyumda gradyan taşıdığı kaydedilmiştir.")
    k.govde_metni(
        "**Varyant, önceden tanımlanan kabul ölçütünü karşılamamıştır.** Ortak 54 "
        "ilaç üzerinde ilaç-makro ortalama kesinlik farkı −0,003536 olmuş ve koşullu "
        "%95 aralık tümüyle sıfırın altında kalmıştır. Yapısal stres protokolünde de "
        "nokta tahmini negatiftir. Genişletilmiş varyant, atom ve protein ağı "
        "dallarının ikisinin de kapalı olduğu koşulla sayısal olarak aynı düzeye "
        "inmiştir.")
    k.sekil(FIG / "WP14/04_gig1a_AP_karsilastirmasi.png",
            "Genişletilmiş varyant ile dondurulmuş karşılaştırma modellerinin "
            "ilaç-makro ortalama kesinlik değerleri.", 12.5)
    k.govde_metni(
        "Başarısızlığın nedeni ayrıca ölçülmüştür. Eklenen mesaj, taban protein "
        "gömmesinin yaklaşık yüzde otuz sekizi kadar bir genliktedir; yani hesaba "
        "zayıf değil, güçlü biçimde girmektedir. Buna karşılık mesaj proteinler "
        "arasında büyük ölçüde **sabittir**: yayılımın merkeze oranı yalnız yüzde "
        "yirmi dokuzdur ve yüksek dereceli proteinlerle düşük dereceli proteinleri "
        "birbirinden ayırmamaktadır. Başka bir deyişle eklenen yol, bütün "
        "proteinlere yaklaşık aynı bilgiyi taşımakta ve ayırt edici olmayan ortak "
        "bir bileşen eklemektedir. Bu, kapasitenin değil, aktarılan bilginin "
        "çözünürlüğünün sınırlayıcı olduğunu gösterir.")

    # ------------------------------------------------------------ 6.6
    k.baslik(2, "İki Sıralama Yönü")
    k.govde_metni(
        "Buraya kadarki bulguların yorumlanması, birincil ölçütün hangi yönde "
        "sıralama yaptığının ayrıştırılmasını gerektirir. İlaç-makro ortalama "
        "kesinlik sabit bir ilaç için yan etki terimlerini sıralar; sınıf-makro "
        "ortalama kesinlik ise sabit bir terim için ilaçları sıralar. Aynı "
        "dondurulmuş skorlar bu iki yönde okunduğunda tablo değişmektedir.")
    k.cizelge(
        "Aynı dondurulmuş skorların iki yönde okunması; birincil protokol, ortak "
        "54 ilaç.",
        [["Model", "Terim yönü (sınıf-makro)", "İlaç yönü (ilaç-makro)"],
         ["T1 rastgele orman", "0,3588", "0,6573"],
         ["B2 kimya + protein", "0,3489", "0,6262"],
         ["T2 gradyan artırma", "0,3255", "0,6325"],
         ["GiG-1 varyantı", "0,3205", "0,6427"],
         ["A1P1 atom + ağ", "0,3173", "0,6462"],
         ["B1 kimya + lojistik", "0,3152", "0,6556"],
         ["B0 sıklık referansı", "0,2382", "0,6466"]],
        [5.6, 4.6, 4.4])
    k.sekil(FIG / "WP15/03_agac_iki_yon.png",
            "İki sıralama yönünün aynı skorlardan okunması.", 12.0)
    k.govde_metni(
        "Terim yönünde öğrenme içeren bütün modeller sıklık referansını belirgin "
        "biçimde aşar; ilaç yönünde ise hiçbiri aşamaz. Bu fark, sınıf başına "
        "gözlenen pozitif sayısının bütün yoğunluk bantlarında korunur: tek "
        "pozitifli elli dokuz sınıfta bile öğrenilmiş model sıklık referansının "
        "üzerindedir ve üç yüz altı sınıfın iki yüz yetmiş sekizinde daha iyidir. "
        "Dolayısıyla tahmin başlığının seyrek sınıflarda aşırı öğrendiği yönündeki "
        "açıklama bu veriyle **desteklenmemektedir**.")
    k.govde_metni(
        "Bu kohortta sınırlayıcı etken kodlayıcının zenginliği ya da başlığın "
        "kapasitesi değil, bir ilacın terim sıralamasında **kayıt yaygınlığının "
        "baskın olmasıdır**. Sık kaydedilen terimler hemen her ilaç için listenin "
        "başında yer alır ve bu sıralamayı iyileştirmek için ilaca özgü bilgi "
        "gerekir; oysa ilaca özgü sinyal, terim yönünde görülebildiği hâlde ilaç "
        "yönünde yaygınlık etkisini aşacak büyüklükte değildir.")
    k.govde_metni(
        "Önemli bir kısıt belirtilmelidir: sınıf-makro ortalama kesinlik bu "
        "çalışmada havuzlanmış **betimleyici** bir ölçüt olarak tanımlanmış ve "
        "bağımsız bir güven aralığı üretilmemiştir. Buradaki yorum, bütün "
        "modellerde tutarlı olan nokta tahmini farkına dayanır ve kalibre edilmiş "
        "bir üstünlük iddiası değildir.")

    # ------------------------------------------------------------ 6.7
    k.baslik(2, "Ağaç Tabanlı Modellerin Sonuçları")
    k.govde_metni(
        "Ağaç kolları, kimyasal lojistik modelle birebir aynı girdiler ve bölmeler "
        "üzerinde çalıştırılmıştır; değişen tek unsur kestiricidir. İç seçimde iki "
        "kolda da **en sığ adaylar** seçilmiştir: rastgele ormanda yirmi katın "
        "yedisinde derinlik üçle ve yaprak başına en az üç örnekle sınırlanan "
        "yapılandırma, gradyan artırmada ise yirmi katın tamamında derinlik iki "
        "seçilmiştir. Bu, küçük eğitim bölmelerinde derinliğin karşılığının "
        "bulunmadığını gösterir.")
    k.cizelge(
        "Ağaç kollarının dondurulmuş referanslarla karşılaştırması; ortak 54 ilaç.",
        [["Karşılaştırma", "Birincil fark", "%95 aralık", "Ayırt edilebilir mi?"],
         ["T1 − B1 kimya", "+0,001697", "[−0,013428; +0,018248]", "Hayır"],
         ["T1 − A1P1", "+0,011105", "[−0,008565; +0,030573]", "Hayır"],
         ["T1 − B2", "+0,031100", "[+0,010025; +0,052217]", "Evet"],
         ["T2 − B1 kimya", "−0,023159", "[−0,039580; −0,009189]", "Evet (daha kötü)"],
         ["T2 − A1P1", "−0,013751", "[−0,030343; +0,002082]", "Hayır"]],
        [4.2, 2.8, 4.4, 3.4])
    k.sekil(FIG / "WP15/01_agac_AP_karsilastirmasi.png",
            "Ağaç tabanlı kolların dondurulmuş referanslarla karşılaştırması; iki "
            "protokol.", 13.5)
    k.govde_metni(
        "Önceden belirlenmiş tek sınama, rastgele ormanın kimyasal lojistik modelle "
        "birincil protokoldeki farkıdır. Bu fark +0,001697’dir ve aralık sıfırı "
        "içerir; **kabul ölçütü karşılanmamıştır.** Doğrusal olmayan bir kestirici, "
        "bu veri ve bu ölçüt altında doğrusal modele göre ayırt edilebilir bir "
        "üstünlük sağlamamıştır. Gradyan artırma ise kimyasal modelden ayırt "
        "edilebilir biçimde daha kötüdür; altı özellik ve küçük eğitim bölmeleriyle "
        "ardışık artırma bu kurulumda zarar vermektedir.")
    k.govde_metni(
        "Önceden kaydedilmiş stres protokolünde ise tablo değişir. Kimyasal olarak "
        "ayrık bölmelere geçildiğinde kimyasal lojistik modelin başarımı 0,6556’dan "
        "0,6319’a düşerken rastgele ormanınki 0,6573’ten 0,6566’ya, yani neredeyse "
        "hiç düşmez. Bu protokolde iki model arasındaki fark +0,024713 ve aralık "
        "[+0,002413; +0,048397] olup tümüyle sıfırın üstündedir.")
    k.govde_metni(
        "Bu gözlem, doğrusal modelin başarımının bir bölümünün **eğitim ilaçlarına "
        "kimyasal benzerlikten** geldiğini düşündürür; bu destek kaldırıldığında "
        "başarım geriler, sığ ağaç topluluğu ise aynı koşuldan etkilenmez. Ancak "
        "bulgu kabul kararını değiştirmez. Kabul ölçütü birincil protokolde "
        "tanımlıdır; ayrıca bu bölümde çok sayıda karşılaştırma yapılmış ve çokluk "
        "düzeltmesi uygulanmamıştır. Önceden belirlenmiş tek sınama dışındaki her "
        "sonuç **keşifseldir** ve sınanmaya değer bir hipotez olarak sunulur.")
    k.govde_metni(
        "Ağaç kolları kimyasal modelin uygunluk tanımını kullandığı için yalnız "
        "ortak 54 ilaçlık kapsamda karşılaştırılabilir. Daha geniş kapsamda "
        "dondurulmuş anahtarların bir bölümü ağaç kollarında bulunmadığından "
        "değerlendirme bu kapsamı doldurmak yerine **atlamıştır**; eksik kapsam "
        "ayrıca kayıt altına alınmıştır.")

    # ------------------------------------------------------------ 6.8
    k.baslik(2, "Açıklanabilirlik Bulguları")
    k.govde_metni(
        "Doğrusal modelde j girdisinin katkısı ϕⱼ=wⱼ(x′ⱼ−Eₜ[X′ⱼ]) biçimindedir; "
        "eğitim arka planının beklenen logiti ile bu katkıların toplamı, sorgu "
        "ilacının logitini verir. Sigmoid uygulanmış puanlarda böyle bir toplamsallık "
        "yoktur. Ortak terimler üzerindeki özet birincil protokolde 201×54=10.854, "
        "stres protokolünde 186×54=10.044 ilaç–terim çiftini kapsar. Birincil "
        "durumda ortalama mutlak logit katkısı en yüksek alan hidrojen bağı verici "
        "sayısıdır (0,206057); streste ise lipofilisitedir (0,300700). Sıralamanın "
        "bölme rejimiyle değişmesi, bu sonucun maddenin evrensel bir biyolojik "
        "özelliği olarak okunamayacağını gösterir.")
    k.sekil(FIG / "WP11/B1_SHAP_v1/03_local_primary_waterfall.png",
            "Kayıtlı bir kimyasal modelde tek test örneğinin logit katkıları.",
            12.0)
    k.govde_metni(
        "Graf modelinde açıklama, mesaj yoluna yapılan müdahaleye duyarlılıkla "
        "ölçülür: Δz=z_özgün−z_müdahale. Eritromisin örneğinde bir hedef mesajı "
        "sabit paydada kapatıldığında fark −0,452095, aynı kenar fiziksel olarak "
        "silinip payda yeniden hesaplandığında ise −0,147869’dur. Başka bir "
        "proteinde aynı iki işlem sırasıyla −0,304226 ve +0,147869 vermektedir. "
        "**İşaretin müdahale tanımına göre değişebilmesi**, bir proteine artırıcı "
        "veya azaltıcı rol yüklemeden önce müdahalenin matematiksel tanımının "
        "belirtilmesini zorunlu kılar.")
    k.sekil(FIG / "WP11/graph_v1/03_Erythromycin_real_network.png",
            "Eritromisin için kayıtlı mesaj yolları ve müdahale etkileri.", 12.0)
    k.govde_metni(
        "Kayıt altına alınan açıklama sayıları büyük görünse de bunlar bağımsız "
        "biyolojik gözlem sayısı değildir: aynı ilaç, terim, model ve müdahale "
        "bağlamı altında çok sayıda hesap yapılır. Bu nedenle açıklama sayıları bir "
        "kanıt gücü ölçüsü olarak sunulmamaktadır.")

    # ------------------------------------------------------------ 6.9
    k.baslik(2, "Belge Temelli Açıklama ve Eğitim Dışı İlaç Örneği")
    k.govde_metni(
        "Dil modeli denemelerinde başarının birden çok aşaması vardır. İlk iki yerel "
        "deneme model dosyasının özeti doğrulanamadığı için üretime geçmeden "
        "durmuştur; bunlar zaman aşımı olarak yorumlanamaz. Sonraki düşük bellekli "
        "denemede metin üretilmiş, fakat kaynaklı Türkçe açıklama ölçütleri "
        "karşılanmamıştır. Tamamlanan beş bulut vakasının üçü kaynaklı açıklama, "
        "ikisi kaynak yetersizliğinde yönlendirilmiş ret gerektirmiştir. Bir vakada "
        "bir istisna korunmuş fakat bir koşul çevrilmemiş, bir başkasında ise "
        "kaynakta yer almayan bir niteleme eklenmiştir. Bu örneklerde **biçimsel "
        "geçerlilik, cümlenin kaynağa sadık olduğunu güvenceye almamıştır.** Beş "
        "vaka için bağımsız insan incelemesi beklemektedir; bu nedenle bu kol için "
        "kesinlik ve duyarlılık değeri hesaplanmamıştır.")
    k.govde_metni(
        "Eğitim dışı etkin tedizolidin doğrulanmış girdileri MW=370,344, "
        "LogP=1,3957, HBD=1, HBA=7, TPSA=106,26 ve kimya maskesi=1’dir. Etkin "
        "molekülün eğitim kimlikleri ve yapısal bağlantısallık anahtarları arasında "
        "yer almadığı doğrulanmıştır. Önceden belirlenmiş beş birincil modelin ortak "
        "201 terimi sıralanmış, ilk on terim ve model başına açıklamalar "
        "**kilitlenmiş**, ardından ürün belgesi incelenmiştir.")
    k.sekil(FIG / "WP13/tedizolid_B1_SHAP_v1/PT01_C0011991_five_models.png",
            "Tedizolid–ishal çifti: beş modelin ayrı logit açıklamaları.", 12.5)
    k.govde_metni(
        "İshal terimi için beş skorun ortalaması 0,8642’dir. Bu bir **sıra "
        "skorudur**; hastada yüzde 86,42 olay sıklığı biçiminde yorumlanabilmesi "
        "için gerekli hasta paydası ve izlem bilgisi yoktur. Sonradan açılan ürün "
        "belgesi intravenöz ön ilaç ürününe aittir ve tablosunda 76 terim yer alır. "
        "Kilitli ilk on terimin altısında çeviri veya eşanlam adayı, ikisinde "
        "ilişkili fakat eşdeğerliği belirsiz kavram, birinde sınıf uyarısı ve "
        "birinde eşleme bulunmaması kaydedilmiştir. Trombositopeniye dair sınıf "
        "uyarısı ile gönüllülerde ölçülen trombosit düşüşü aynı kanıt değildir; "
        "anafilaktik şok için karşılık saptanmaması da olayın yokluğunu göstermez. "
        "Tek molekül, kısmi ön bilgi ve bekleyen uzman kararı nedeniyle bu "
        "örnekten bir başarı oranı veya dış başarım değeri hesaplanmamıştır.")
    k.sekil(FIG / "WP13/arayuz_v5/05_tedizolid_v5.png",
            "Tedizolid ilk on hedefinde kilitli model sırası ve sonradan açılan "
            "ürün belgesi karşılığı.", 13.5)

    # ------------------------------------------------------------ 6.10
    k.baslik(2, "Araştırma Prototipi")
    k.govde_metni(
        "Prototipte bir araştırmacı, dışarıda bırakılmış bir ilacın kayıtlı "
        "çıktısından ilgili model ve terime, oradan da o modele özgü açıklamaya "
        "ilerleyebilir. Belge incelemesinde aynı araştırmacı, modelden bağımsız "
        "olarak ilgili sayfaya gidip sıklık ve ürün kapsamını okuyabilir. Böylece "
        "Bölüm 2.3’te tanımlanan **kanıt ayrımı** gereksinimi işletim sırasında "
        "gözlenebilir duruma gelir.")
    k.govde_metni(
        "Çekimserlik gereksinimi de doğrudan sınanmıştır. Kimliği bilinmeyen bir "
        "belge yüklendiğinde uygulama desteklenmeyen durum bildirimi döndürmüş, "
        "ilaç tahmini başlatmamıştır. Böylece belge yükleme işlevinin kendiliğinden "
        "ilaç tahminine dönüşmediği gösterilmiştir.")
    k.sekil(FIG / "WP13/arayuz_v5/07_dogrulanmayan_pdf_v5.png",
            "Kimliği doğrulanmayan belgede kişiselleştirilmiş tahmin "
            "desteklenmez.", 13.5)
    k.govde_metni(
        "Sunum katmanı, veri ve kilit denetimleri değiştirilmeden yeniden "
        "düzenlenmiştir. Önceki sürümde ilk on hedefin çubuk grafiği kategori "
        "adlarını abecesel sırada çizdiğinden, aynı ekranda görülen tablo ile grafik "
        "farklı bir sıralama gösterebiliyordu; bu, sıralama amaçlı bir arayüzde "
        "doğrudan yanıltıcı bir kusurdur. Yeni sürümde çizim sırası doğrudan skora "
        "bağlanmış ve bu davranış bir regresyon testiyle sabitlenmiştir. Uyarı ve "
        "sınır metinleri her sekmede tek bir bölümde toplanmış, hiçbiri "
        "kaldırılmamıştır; ayrı bir denetim testi bu metinlerin varlığını sınar.")
    k.bolum_sonu("arap")
