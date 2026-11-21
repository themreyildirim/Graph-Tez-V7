# -*- coding: utf-8 -*-
"""Bolum 7-8 ve arka bolumler: Tartisma, Sonuc ve Oneriler, Kaynaklar, Ekler."""

KAYNAKLAR = [
    "Kuhn, M., Letunic, I., Jensen, L. J. ve Bork, P. (2016). The SIDER database "
    "of drugs and side effects. Nucleic Acids Research, 44(D1), D1075–D1079. "
    "https://doi.org/10.1093/nar/gkv1075",
    "Wishart, D. S., Feunang, Y. D., Guo, A. C., Lo, E. J. vd. (2018). DrugBank "
    "5.0: a major update to the DrugBank database for 2018. Nucleic Acids "
    "Research, 46(D1), D1074–D1082. https://doi.org/10.1093/nar/gkx1037",
    "Szklarczyk, D., Kirsch, R., Koutrouli, M., Nastou, K. vd. (2023). The STRING "
    "database in 2023: protein–protein association networks and functional "
    "enrichment analyses for any sequenced genome of interest. Nucleic Acids "
    "Research, 51(D1), D638–D646. https://doi.org/10.1093/nar/gkac1000",
    "Wu, Z., Ramsundar, B., Feinberg, E. N., Gomes, J. vd. (2018). MoleculeNet: a "
    "benchmark for molecular machine learning. Chemical Science, 9(2), 513–530. "
    "https://doi.org/10.1039/C7SC02664A",
    "Saito, T. ve Rehmsmeier, M. (2015). The precision-recall plot is more "
    "informative than the ROC plot when evaluating binary classifiers on "
    "imbalanced datasets. PLOS ONE, 10(3), e0118432. "
    "https://doi.org/10.1371/journal.pone.0118432",
    "Elkan, C. ve Noto, K. (2008). Learning classifiers from only positive and "
    "unlabeled data. Proceedings of the 14th ACM SIGKDD International Conference "
    "on Knowledge Discovery and Data Mining, 213–220. "
    "https://doi.org/10.1145/1401890.1401920",
    "Sun, C., Yin, J. ve Lu, H. (2025). ISLRWR: A network diffusion algorithm for "
    "drug–target interactions prediction. PLOS ONE, 20(1), e0302281. "
    "https://doi.org/10.1371/journal.pone.0302281",
    "Chen, Y.-H., Shih, Y.-T., Chien, C.-S. ve Tsai, C.-S. (2022). Predicting "
    "adverse drug effects: A heterogeneous graph convolution network with a "
    "multi-layer perceptron approach. PLOS ONE, 17(4), e0266435. "
    "https://doi.org/10.1371/journal.pone.0266435",
    "Zitnik, M., Agrawal, M. ve Leskovec, J. (2018). Modeling polypharmacy side "
    "effects with graph convolutional networks. Bioinformatics, 34(13), "
    "i457–i466. https://doi.org/10.1093/bioinformatics/bty294",
    "Gao, T., Yen, H., Yu, J. ve Chen, D. (2023). Enabling large language models "
    "to generate text with citations. Proceedings of EMNLP 2023, 6465–6488. "
    "https://doi.org/10.18653/v1/2023.emnlp-main.398",
    "Freeman, L. C. (1978). Centrality in social networks: Conceptual "
    "clarification. Social Networks, 1(3), 215–239. "
    "https://doi.org/10.1016/0378-8733(78)90021-7",
    "Rudin, C. (2019). Stop explaining black box machine learning models for high "
    "stakes decisions and use interpretable models instead. Nature Machine "
    "Intelligence, 1(5), 206–215. https://doi.org/10.1038/s42256-019-0048-x",
    "Gilmer, J., Schoenholz, S. S., Riley, P. F., Vinyals, O. ve Dahl, G. E. "
    "(2017). Neural message passing for quantum chemistry. Proceedings of the "
    "34th International Conference on Machine Learning, 1263–1272. "
    "https://proceedings.mlr.press/v70/gilmer17a.html",
    "Lundberg, S. M. ve Lee, S.-I. (2017). A unified approach to interpreting "
    "model predictions. Advances in Neural Information Processing Systems, 30, "
    "4765–4774. https://papers.nips.cc/paper_files/paper/2017/hash/"
    "8a20a8621978632d76c43dfd28b67767-Abstract.html",
]


def bolum7(k):
    k.baslik1("TARTIŞMA")

    k.baslik(2, "Bulguların Bilimsel Yorumu")
    k.govde_metni(
        "Bu çalışmanın en dikkat çekici bulgusu, öğrenme içeren hiçbir modelin "
        "birincil ölçütte sıklık referansını ayırt edilebilir biçimde "
        "aşamamasıdır. Bu sonucun yüzeysel okunuşu, kimyasal ve biyolojik bilginin "
        "yararsız olduğudur. Bölüm 6.6’daki iki yön ayrımı bu okumanın yanlış "
        "olduğunu göstermektedir: aynı skorlar terim yönünde okunduğunda öğrenme "
        "içeren bütün modeller sıklık referansını belirgin biçimde aşar. "
        "Dolayısıyla ilaca özgü sinyal **vardır ve ölçülebilirdir**; ancak bir "
        "ilacın terim sıralamasında kayıt yaygınlığının yarattığı etkiyi aşacak "
        "büyüklükte değildir.")
    k.govde_metni(
        "Bu ayrım, ölçüt seçiminin bir sonucu değil, problemin yapısına ilişkin bir "
        "bulgudur. Sık kaydedilen yan etki terimleri hemen her antibakteriyel için "
        "listenin başında yer alır. Bir modelin bu sıralamayı iyileştirebilmesi "
        "için yalnız hangi terimlerin yaygın olduğunu değil, **belirli bir ilaçta "
        "yaygın olmayan hangi terimin öne çıkacağını** bilmesi gerekir. Mevcut "
        "kohort bu ayrımı öğrenmek için gereken çeşitliliği sağlamamaktadır.")
    k.govde_metni(
        "İkinci önemli bulgu, protein ağı topolojisinin katkısının "
        "gösterilememesidir. Burada yöntemsel titizlik, olumsuz sonucun "
        "güvenilirliğini belirler: mesajın hesaba fiilen girdiği, kenar silme ve "
        "gradyan ölçümleriyle ayrı ayrı doğrulanmıştır. Bu nedenle sonuç bir "
        "uygulama hatası değil, gerçek bir ölçümdür. Yine de bu ölçüm topolojinin "
        "biyolojik önemsizliğini değil, **bu kohortta, bu seyreklikte ve bu "
        "mimaride** katkısının gösterilemediğini söyler.")

    k.baslik(2, "Mimari Karmaşıklık ve Veri Ölçeği")
    k.govde_metni(
        "Çalışmada sınanan modeller, girdi genişliği altı alandan birkaç bin "
        "parametreye uzanan geniş bir aralığı kapsar. Sonuçların ortak örüntüsü "
        "açıktır: **karmaşıklık artışı başarım artışına dönüşmemiştir.** Altı "
        "girdili doğrusal model, iki yüz otuz dört girdili doğrusal modelden ayırt "
        "edilebilir biçimde daha iyidir; graf tabanlı mimariler doğrusal kimya "
        "modelinden ayırt edilemez; bilgi aktarımı ekleyen varyant ise ayırt "
        "edilebilir biçimde daha kötüdür.")
    k.govde_metni(
        "Bu örüntünün en olası açıklaması örneklem büyüklüğüdür. Altmış iki ilaçtan "
        "elli dördünün skorlanabildiği bir kohortta, dış bölmelerin eğitim kümeleri "
        "kırk civarında ilaç içerir. Bu ölçekte esnek bir modelin kapasitesini "
        "kullanabilmesi için gereken örnek çeşitliliği bulunmamaktadır. Ağaç "
        "kolunda iç seçimin iki kolda da **en sığ adayları** seçmesi bu açıklamayı "
        "doğrudan desteklemektedir: veri, derinliğin karşılığını vermemektedir.")
    k.govde_metni(
        "Bilgi aktarımı varyantının başarısızlığı ise ayrı bir ders içerir. Eklenen "
        "mesaj zayıf değil, güçlüdür; ancak proteinler arasında ayırt edici "
        "değildir. Bir mimari genişletmenin yararlı olması için bilgiyi **taşıması** "
        "yetmez; taşıdığı bilginin varlıklar arasında **farklılaşması** gerekir. Bu "
        "ölçüm, başarısızlığın kapasiteden değil çözünürlükten kaynaklandığını "
        "gösterdiği için, modeli büyütmenin çözüm olmadığını da söyler.")

    k.baslik(2, "Ölçüt Yönünün Sonuçlara Etkisi")
    k.govde_metni(
        "İki sıralama yönünün farklı sonuç vermesi, yöntemsel bir uyarı "
        "niteliğindedir. Literatürde ilaç–yan etki modellerinin başarımı çoğu kez "
        "havuzlanmış ölçütlerle bildirilir ve hangi yönde sıralama yapıldığı her "
        "zaman belirtilmez. Bu çalışmanın verisi, aynı skor kümesinin iki yönde "
        "farklı sıralama ürettiğini ve referansa göre konumun bile "
        "değişebildiğini göstermektedir. Bir modelin ‘sıklık referansını aştığı’ "
        "iddiası, hangi yönde ölçüldüğü belirtilmeden yorumlanamaz.")
    k.govde_metni(
        "Bu çalışmada birincil ölçüt olarak ilaç yönünün seçilmesinin nedeni "
        "yöntemsel değil kullanım amacına ilişkindir: sistemin kullanıcısı bir "
        "ilacı sabitleyip terimleri inceler. Ölçütün kullanıcının inceleme birimine "
        "uyması, elde edilen sayının karar için anlamlı olmasını sağlar. Terim "
        "yönündeki sonuçlar bu nedenle tamamlayıcı kanıt olarak sunulmuş, birincil "
        "başarım iddiası olarak kullanılmamıştır.")

    k.baslik(2, "Kısıtlar")
    k.govde_metni(
        "Kohort büyüklüğü en belirleyici kısıttır; altmış iki ilaç, model sınıfları "
        "arasındaki küçük farkları ayırt etmeye yetecek istatistiksel güç "
        "sağlamamaktadır. Güven aralıklarının genişliği bu durumun doğrudan "
        "göstergesidir. İkinci kısıt etiket semantiğidir: doğrulanmış negatif "
        "bulunmadığından bütün ölçütler **gözlenen kayıt sıralaması** üzerinden "
        "tanımlanmıştır ve klinik olay sıklığına çevrilemez.")
    k.govde_metni(
        "Üçüncü kısıt protein ağının seyrekliğidir: kullanılan eşikte altmış üç "
        "düğümün on ikisi izoledir ve en büyük bağlı bileşen kırk dokuz düğüm "
        "içerir. Bu yapıda mesaj geçişinin taşıyabileceği bilgi sınırlıdır. "
        "Dördüncü kısıt, güven aralıklarının yalnız ilaç grubu değişkenliğini "
        "yansıtmasıdır; yeniden öğrenme ve yeni popülasyona aktarım belirsizliği "
        "ölçülmemiştir. Son olarak, dil modeli ve terminoloji kollarında bağımsız "
        "uzman değerlendirmesi tamamlanmadığından bu kollar için kesinlik ve "
        "duyarlılık değeri bildirilmemiştir.")
    k.govde_metni(
        "Bu çalışmada yapılan çok sayıda karşılaştırma için çokluk düzeltmesi "
        "uygulanmamıştır. Her deneyde önceden belirlenmiş tek bir sınama "
        "tanımlanmış ve kabul kararı yalnız ona dayandırılmıştır; geri kalan "
        "karşılaştırmalar keşifsel olarak sunulmuştur. Stres protokolünde ağaç "
        "kolunun gösterdiği fark da bu niteliktedir ve bağımsız olarak "
        "sınanmalıdır.")

    k.baslik(2, "Gelecek Çalışmalar")
    k.govde_metni(
        "En öncelikli adım kohortun genişletilmesidir. Bu çalışmanın bulguları, "
        "mimari karmaşıklığın değil örneklem büyüklüğünün sınırlayıcı olduğuna "
        "işaret etmektedir; dolayısıyla daha gelişmiş bir mimari denemek yerine "
        "daha fazla ilaç ve daha geniş terim kapsamı sağlamak daha yüksek beklenen "
        "getiriye sahiptir. İkinci adım, stres protokolünde gözlenen ağaç kolu "
        "farkının bağımsız bir veri kümesinde ve önceden kaydedilmiş tek bir "
        "sınamayla doğrulanmasıdır.")
    k.govde_metni(
        "Üçüncü adım terminoloji doğrulamasıdır: kilitli terim–alıntı çiftlerinin "
        "model sırasını görmeyen bağımsız uzmanlara verilmesi, hem ilk kararların "
        "hem de anlaşmazlıkların çözüm biçiminin kaydedilmesi gerekir. Böyle bir "
        "tasarım, terim eşlemesindeki belirsizliği model sıralamasındaki "
        "değişkenlikten ayırır. Hasta düzeyinde risk ise ayrı bir araştırma "
        "sorusudur; bunun için maruz kalan nüfus, zaman, doz, hasta sonuçları ve "
        "bağımsız onay içeren yeni bir çalışma tasarımı gerekir.")
    k.bolum_sonu("arap")


def bolum8(k):
    k.baslik1("SONUÇ VE ÖNERİLER")

    k.baslik(2, "Tasarım Kararı")
    k.govde_metni(
        "Birinci araştırma sorusuna verilen yanıt, ana etkin madde, stereo kimlik ve "
        "tercih edilen terim düzeyinde uzlaşıldığında aynı kaynaklardan 62 ilaç ve "
        "6.416 benzersiz gözlenen ilişkinin izlenebildiğidir.")
    k.govde_metni(
        "İkinci soruda kanıtın yönü kullanılan karşılaştırmaya bağlıdır. Kimya "
        "modelinin sıklık referansına göre farkının aralığı sıfırı içerir. Protein "
        "rol özetleri kapsamı genişletirken ortak sıralamayı iyileştirmemiştir. "
        "Gerçek protein ağı mesajlarının işlendiği doğrulanmış, ek sıralama yararı "
        "gösterilememiştir. Atom topolojisi kendi mimarisi içinde birincil "
        "protokolde küçük bir katkı sağlamıştır. Bilgi aktarımı ekleyen mimari "
        "genişletme ve doğrusal olmayan ağaç kolları ise önceden kilitlenen kabul "
        "ölçütlerini karşılamamıştır. Terim yönünde ise öğrenme içeren bütün "
        "modeller sıklık referansını belirgin biçimde aşmaktadır.")
    k.govde_metni(
        "Üçüncü soruda tedizolid örneği, bir model açıklamasıyla ürün kanıtının "
        "birbirini nasıl tamamlayabildiğini ve nerede ayrıldığını göstermektedir. "
        "Bir alıntı modelin hesap yolunu, bir katkı değeri de alıntının klinik "
        "kapsamını doğrulamaz. Araştırmacı iki kanıtı kendi birimleriyle "
        "görebildiğinde, uyuşmazlığı bir skor içinde kaybetmeden inceleyebilir.")
    k.govde_metni(
        "**Tasarım kararı şudur:** dış kimyasal sorgu için düşük girdi "
        "gereksinimli, doğrulanabilir adaptöre sahip ve model başına tam logit "
        "açıklaması üretilebilen kimyasal lojistik model kullanılır; belirli bir "
        "model yolunun incelenmesi gerektiğinde atom ve protein ağı dallarının açık "
        "olduğu graf modeli kullanılır. Hiçbir deney sonucuna bakılarak model "
        "geriye dönük yeniden seçilmemiş, önceden kilitlenen kabul ölçütleri "
        "uygulanmıştır. Karşılaştırmada en yüksek nokta tahminine ulaşan ağaç "
        "kolunun ana model yapılmaması bu ilkenin doğrudan sonucudur.")

    k.baslik(2, "Çözüm Önerisinin Çevresel Etkilerinin İncelenmesi")
    k.govde_metni(
        "Tasarımın çevresel etkisi hesaplama kaynağı kullanımı üzerindendir. "
        "Çalışmada bilinçli olarak küçük modeller seçilmiş, bütün eğitim ve "
        "değerlendirme işlemleri tek bir kişisel bilgisayarda ve merkezi işlem "
        "birimi üzerinde yürütülmüştür; grafik işlem birimi kümesi "
        "kullanılmamıştır. Dondurulmuş skorların saklanması, aynı sonucun yeniden "
        "hesaplanmasını gereksiz kılarak tekrar eden hesap yükünü azaltmaktadır.")
    k.govde_metni(
        "Bu tasarım tercihlerinin sayısal bir çevresel kazanca çevrilmesi ise "
        "yapılmamıştır. Elektrik tüketimi ve karbon salımı ölçülmediğinden, "
        "azaltılan hesap yüküne doğrudan bir çevre kazanımı atfedilmemektedir. "
        "Belirtilebilecek tek şey, tasarımın büyük ölçekli hesaplama gerektiren bir "
        "yaklaşımı **gerektirmediği** ve bulguların bunu desteklediğidir.")

    k.baslik(2, "Çözüm Önerisinin Toplumsal Etkilerinin İncelenmesi")
    k.govde_metni(
        "Tasarımın toplumsal etkisi, ilaç güvenliliği incelemesinde çalışan "
        "araştırmacıların inceleme sırasını gerekçelendirebilmesiyle ilgilidir. "
        "Kayıtlı bir modelin yeniden eğitilmeden açılabilmesi ve uzmanın terimi "
        "doğrudan kaynak sayfasında inceleyebilmesi, araştırma grubunun görev "
        "paylaşımını somutlaştırır. Bunun zamana veya hasta sonucuna çevrilmiş bir "
        "karşılığı bu çalışmada ölçülmemiştir.")
    k.govde_metni(
        "Toplumsal açıdan asıl sorumluluk, araştırma skorunun hasta riski olarak "
        "anlaşılmasını önleyecek bağlamı sağlamaktır. Bir sıralama skorunun olay "
        "sıklığı gibi okunması, var olmayan bir kesinlik izlenimi yaratır ve yanlış "
        "yönlendirir. Bu nedenle prototipte her skorun yanında anlamı belirtilmiş, "
        "sınır metinleri kaldırılmamış ve bu metinlerin varlığı bir denetim testiyle "
        "sabitlenmiştir. Ayrıca az temsil edilen bir ilaçta kayıt eksikliğinin düşük "
        "risk gibi görünmesi, bilgi açığının karar sırasını haksız biçimde "
        "etkilemesine yol açabilir; bu durum raporda açık bir kısıt olarak "
        "belirtilmiştir.")

    k.baslik(2, "Çözüm Önerisinin Ekonomik Etkilerinin İncelenmesi")
    k.govde_metni(
        "Ekonomik olarak doğrulanabilen tek değer, tamamlanan beş dil modeli "
        "isteğinin belge başına yaklaşık birkaç kuruşluk işlem maliyetidir; bu "
        "deneyin doğrulanmış alt toplamı 0,0127 ABD dolarıdır. Bunun dışındaki "
        "maliyet kalemleri açık kaynaklı kütüphaneler ve mevcut donanımla "
        "karşılanmıştır; ek lisans veya altyapı gideri oluşmamıştır.")
    k.govde_metni(
        "Beklenen ekonomik fayda, araştırmacının inceleme sırasını daha erken "
        "daraltabilmesidir. Ancak bu faydanın büyüklüğü bu çalışmada "
        "ölçülmemiştir: inceleme süresinin kısalıp kısalmadığına ilişkin bir "
        "kullanıcı denemesi yapılmamış, karşılaştırmalı iş yükü ölçümü "
        "üretilmemiştir. Bulgular ışığında dürüst bir ekonomik değerlendirme, "
        "modelin birincil ölçütte sıklık referansına göre ayırt edilebilir bir "
        "kazanç sağlamadığını ve dolayısıyla beklenen tasarrufun şu aşamada "
        "**gösterilmemiş** olduğunu belirtmelidir.")

    k.baslik(2, "Çözüm Önerisinin Etik Boyutunun İncelenmesi")
    k.govde_metni(
        "Araştırma etiği açısından ilk sorumluluk, başlangıçtaki beklentiyi "
        "desteklemeyen bulguları da görünür kılmaktır. Protein ağının ek katkı "
        "göstermemesi, mimari genişletmenin kabul ölçütünü karşılamaması ve ağaç "
        "kolunun birincil ölçütte ayırt edilebilir bir üstünlük sağlamaması bu "
        "nedenle raporun ana sonuçlarına dâhildir. Sonuçlara bakılarak ölçüt veya "
        "protokol değiştirilmemiş; yapılan iki protokol düzeltmesi hiçbir eğitim "
        "çalıştırılmadan önce ve gerekçesiyle kayda geçirilmiştir.")
    k.govde_metni(
        "Karar yetkisi açısından sistem, uzmanın yerine geçmek üzere değil, "
        "incelemesini sıralamak üzere tasarlanmıştır. Sıralama ile belge kanıtının "
        "ayrı sunulması, son kararın kaynak metni okuyan kişide kalmasını sağlar. "
        "Veri etiği açısından prototip hasta verisi işlememekte, dağıtım lisanslı "
        "ham veri ve hizmet anahtarı içermemektedir.")
    k.govde_metni(
        "Fayda–zarar dengesinde araştırmacının zaman kazanma olasılığı, "
        "doğrulanmamış bir sıralamanın tedavi kararına taşınması hâlindeki zararla "
        "birlikte düşünülmelidir. İkinci olasılığın sonuçları ağır olduğundan, "
        "prototipin kullanımı araştırma ve eğitim bağlamıyla sınırlandırılmıştır. "
        "Bu sınır bir eksiklik değil, bulguların desteklediği kapsamın dürüst "
        "ifadesidir.")
    k.bolum_sonu("arap")


def arka_bolumler(k, ozgecmis_var: bool):
    k.baslik1("KAYNAKLAR", numarali=False)
    for i, kaynak in enumerate(KAYNAKLAR, start=1):
        k.kaynak_satiri(f"[{i}] {kaynak}")
    k.bolum_sonu("arap")

    k.baslik1("EKLER", numarali=False)
    k.bolum = "EKLER"
    k.govde_metni(
        "Bu bölüm yalnız akademik değeri olan özet bilgiyi içerir. Deney kayıtları, "
        "bütünlük özetleri, dosya yolları ve test kayıtları ana metne "
        "taşınmamış; ayrı bir teknik doğrulama arşivinde tutulmuştur.")
    k.baslik(2, "Ek A: Model yapılandırmalarının özeti", numarali=False)
    k.cizelge(
        "Karşılaştırılan modellerin eğitim yapılandırması.",
        [["Model", "Öğrenici", "Seçilen ayar", "Seçim ölçütü"],
         ["B1", "L2 lojistik regresyon", "C ∈ {0,1; 1; 10}", "İç kat ilaç-makro AP"],
         ["B2", "L2 lojistik regresyon", "C ∈ {0,1; 1; 10}", "İç kat ilaç-makro AP"],
         ["Graf kolları", "AdamW", "lr = 0,001; ağırlık bozunumu 0,001",
          "İç kat en iyi epoch medyanı"],
         ["T1", "Rastgele orman (300 ağaç)", "Derinlik 3; yaprak ≥ 3",
          "İç kat ilaç-makro AP"],
         ["T2", "Gradyan artırma (100 yineleme)", "Derinlik 2",
          "İç kat ilaç-makro AP"]],
        [2.6, 4.6, 4.6, 4.0])
    k.govde_metni(
        "Graf kollarında üst sınır 200 epoch, erken durdurma sabrı 20 ve asgari "
        "değişim 0,0001’dir. Bütün kollarda rastgelelik tohumu sabittir ve model "
        "seçimi yalnız iç katlarda yapılmıştır.")
    k.bolum_sonu("arap")

    k.baslik1("ÖZGEÇMİŞ", numarali=False)
    if not ozgecmis_var:
        k.govde_metni(
            "[Bu bölüm şablonun zorunlu tuttuğu özgeçmiş metinlerini içerir ve "
            "yazarlar tarafından doldurulacaktır.]")
