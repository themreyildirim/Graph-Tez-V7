# -*- coding: utf-8 -*-
"""Bolum 1-3: Giris, Sistem Analizi, Kuramsal Temel ve Literatur.

Metin, dogrulanmis kayitlara dayanir. Hicbir sayisal deger burada
uretilmez; deneysel degerler Bolum 6'da kayitli QA ciktilarindan gelir.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "reports/figures"
TESLIM = ROOT / "EMT2_Teslim_v1"


def bolum1(k):
    k.baslik1("GİRİŞ")

    k.baslik(2, "Problem ve Motivasyon")
    k.govde_metni(
        "Bir antibakteriyel ilacın güvenlilik profilini inceleyen araştırmacı, "
        "molekülün kimyasal yapısı, etkileştiği proteinler ve ürün bilgisinde "
        "geçen olaylar hakkında farklı türde kanıtlarla karşılaşır. DrugBank bir "
        "etkin maddeyi ve kaynakta ona atfedilen biyolojik ilişkileri tanımlar [2]. "
        "SIDER ise ürün metinlerinden belirli bir ilaçla birlikte kaydedilmiş yan "
        "etki terimlerini derler [1]. Bu iki kaynak bir araya getirildiğinde "
        "araştırmacı, belirli bir bileşiğin hangi terimlerle ilişkilendirilmiş "
        "olabileceğini sorabilir. Olayı yaşayan hasta sayısı ve ilaca maruz kalan "
        "nüfus bilinmediği için aynı verilerden bir olay sıklığı türetilemez.")
    k.govde_metni(
        "Buradan doğan tasarım problemi bir kestirim değil, **eksik gözlem altında "
        "sıralama** problemidir. Bir araştırmacının önünde yüzlerce aday terim "
        "vardır ve bunların hepsini aynı özenle incelemeye zamanı yoktur. Değerli "
        "olan çıktı, terimlerin hangi sırayla ele alınacağına ilişkin gerekçeli bir "
        "öneridir. Bu öneri yanlış olduğunda maliyeti, araştırmacının birkaç kaydı "
        "boşuna incelemesidir; doğru olduğunda kazancı, ilgili kaydın listenin "
        "başında bulunmasıdır. Problem bu biçimde kurulduğunda başarı ölçütü de "
        "doğal olarak sıralama kalitesi olur.")

    k.baslik(2, "Gözlem Birimi ve Karar Birimi")
    k.govde_metni(
        "Bu ayrım, karar destek sisteminin karar birimini belirler. Her sorguda bir "
        "ana etkin madde sabitlenir ve incelemeye açık terimler sıralanır. Ürün adı, "
        "tuz formu ve etkin madde kimliği birbirinin yerine kullanıldığında "
        "sıralamanın dayandığı kayıtlar değişir. Protein tarafında da bir taşıyıcı "
        "ile ilacın etkisini gösterdiği hedef farklı biyolojik ilişkilerdir. "
        "Dolayısıyla modelin öğrenebileceği örüntüleri ilk belirleyen seçim, ağ "
        "algoritmasından önce, hangi kaydın hangi varlığı ve ilişkiyi temsil "
        "ettiğidir.")
    k.govde_metni(
        "Çalışmada her karara izlenebilir bir birim atanmıştır. Kimlik için ana ilaç "
        "ve stereokimyasal bileşik kimliği, başarım için dışarıda bırakılan ilaç, "
        "açıklama için ilaç–terim–model–bölme bileşimi, belge için fiziksel sayfa ve "
        "karakter aralığı kullanılır. Bu birimler rapor boyunca değişmez; bir sayının "
        "hangi birimde ölçüldüğü her zaman belirtilir.")

    k.baslik(2, "Araştırma Soruları ve Katkı")
    k.govde_metni(
        "Araştırma üç soruya dayanır. Birincisi, aynı kaynaklar dikkatli biçimde "
        "uzlaştırıldığında sistemik antibakteriyel kohortunun ne ölçüde geri "
        "kazanılabildiğidir. İkincisi, yeni bir ilaç için oluşturulan sıralamada "
        "protein bilgisinin ve atom topolojisinin basit bir kimyasal modele hangi "
        "koşullarda katkı sağladığıdır. Üçüncüsü, araştırmacının üst sıradaki bir "
        "terim için modelin dayanağını ve ürün belgesindeki ifadeyi birbirinden "
        "bağımsız olarak inceleyip inceleyemeyeceğidir.")
    k.govde_metni(
        "Endüstri mühendisliği açısından bu üç soru aynı iş akışının ardışık "
        "kararlarıdır. Bir kimlik kabulü aday havuzunu, özelliklerin bulunabilirliği "
        "hangi ilaçların skorlanacağını, sıralama da uzmanın ilk olarak hangi kayda "
        "bakacağını belirler. İzleyen bölümler bu kararların her birinin sonuç "
        "üzerindeki etkisini ayrı ayrı inceler.")
    k.govde_metni(
        "Bu raporda sunulan başarım değerleri, **ilaç düzeyinde ayrık** bir protokolle "
        "elde edilmiştir; değerlendirilen her ilaç, kendisini skorlayan modelin "
        "eğitiminde yer almamıştır. Bu ayrım yöntemsel olarak belirleyicidir. "
        "İlaç–yan etki çiftlerinin çift düzeyinde bölündüğü, ölçeklemenin bölmeden "
        "önce tüm veri üzerinde yapıldığı veya aynı etiketsiz çiftin birden çok kez "
        "negatif olarak örneklendiği kurulumlarda bir ilaç hem eğitimde hem "
        "değerlendirmede yer alabilir. Böyle kurulumlardan elde edilen değerler "
        "indüktif başarımın ölçüsü sayılamaz ve bu çalışmanın değerleriyle doğrudan "
        "karşılaştırılamaz. Bu nedenle karşılaştırma ölçütü olarak yalnız aynı "
        "dondurulmuş bölmeler üzerinde hesaplanan sıklık ve kimya referansları "
        "kullanılmıştır.")
    k.bolum_sonu("arap_bir")


def bolum2(k):
    k.baslik1("SİSTEM ANALİZİ")

    k.baslik(2, "Sistem Tanımı")
    k.govde_metni(
        "Tasarlanan sistem, bir araştırma grubunun yan etki ön incelemesinde "
        "kullanılan bir karar destek prototipidir. Girdisi doğrulanmış bir etkin "
        "madde kimliği, çıktısı ise o madde için incelenmeye değer yan etki "
        "terimlerinin gerekçeli bir sırasıdır. Sistem bir tanı koymaz, tedavi "
        "önermez ve hastaya özgü risk hesaplamaz; kaynak kayıtlarında gözlenmiş "
        "ilişkileri sıralar.")
    k.govde_metni(
        "Sistem üç katmandan oluşur. Veri katmanı kaynak sürümlerini, kimlik "
        "köprülerini ve etiket tanımını sabitler. Öğrenme katmanı, ilaç düzeyinde "
        "ayrık bölmelerde eğitilmiş modelleri ve bunların dondurulmuş skorlarını "
        "tutar. Sunum katmanı ise skoru, skorun model içindeki dayanağını ve ürün "
        "belgesindeki ilgili ifadeyi **ayrı ayrı** gösterir. Bu üç katmanın "
        "birbirine karışmaması tasarımın temel kuralıdır.")
    k.sekil(FIG / "WP14/02_veri_akisi.png",
            "Veri akışı: kaynak kayıtlardan dondurulmuş skorlara ve açıklamaya.",
            13.5)

    k.baslik(2, "Sistemin Paydaşları")
    k.govde_metni(
        "Sistemin üç paydaşı vardır ve her biri farklı bir soruyu yanıtlar. **Veri "
        "sorumlusu** ana kimliği ve kaynak sürümünü doğrular; sorusu bu kaydın hangi "
        "etkin maddeye ait olduğudur. **Modeli kullanan araştırmacı** terim sırasını "
        "ve ilgili özellikleri inceler; sorusu hangi terimden başlanacağıdır. "
        "**Alan uzmanı** ise metindeki ifadenin ürüne mi yoksa ilaç sınıfına mı "
        "atfedildiğini ve kullanılan çevirinin kavramsal karşılığını değerlendirir; "
        "sorusu bu kaydın gerçekte ne söylediğidir.")
    k.govde_metni(
        "Bu üç sorunun ayrı tutulması tasarımda somut bir karşılık bulur. Örneğin "
        "yüksek sıradaki bir terimin Kısa Ürün Bilgisi’nde (KÜB) yalnız sınıf "
        "düzeyinde geçmesi, sıralama ile belgenin farklı soruları yanıtladığı bir "
        "durumdur. Ekranda bu iki kaydı birlikte ve kaynaklarını belirterek sunmak, "
        "son kararı verecek kişinin uyuşmazlığı görebilmesini sağlar. Uyuşmazlığı "
        "tek bir bileşik skora indirgemek, paydaşlardan birinin sorusunu görünmez "
        "kılardı.")

    k.baslik(2, "Sistem Gereksinimleri")
    k.cizelge(
        "Sistem gereksinimleri ve işletim sırasında gözlenebilir kanıt.",
        [["Gereksinim", "İşletimde gözlenebilir karşılığı"],
         ["Kimlik doğrulanabilirliği",
          "Doğrulanamayan kayıtta eşleme durur; tahmin üretilmez"],
         ["Eksik modalitenin görünürlüğü",
          "Nötr sayısal değer ile ayrı bulunabilirlik maskesi birlikte tutulur"],
         ["Çekimserlik",
          "Kişiselleştirilmiş girdi yoksa skor üretilmez"],
         ["İndüktif kullanım",
          "Dış test ilacı sözlüğü, ölçeği ve model seçimini etkileyemez"],
         ["Kanıt ayrımı",
          "Model skoru ile belge alıntısı ayrı tablolarda sunulur"],
         ["Yeniden erişilebilirlik",
          "Ağırlıklar ve test anahtarları sürümlenir; skor yeniden üretilir"]],
        [5.5, 9.5])
    k.govde_metni(
        "Gereksinimler işlevsel bir listeden çok, **sınanabilir koşullar** olarak "
        "yazılmıştır. Her satırın sağ sütunu, o gereksinimin karşılanıp "
        "karşılanmadığının prototip çalışırken nasıl gözleneceğini söyler. "
        "Bölüm 6.10’da bu koşulların prototip üzerinde nasıl doğrulandığı "
        "gösterilmektedir.")

    k.baslik(2, "Tasarıma Yön Veren Kısıtlar")
    k.govde_metni(
        "En belirleyici kısıt veri kaynağının gözlem mekanizmasıdır: kayıt yokluğu "
        "olayın yokluğu değildir. Bu nedenle doğrulanmış negatif örnek "
        "üretilememiş, negatif örnekleme yapılmamış ve **gözlenen kayıt ile "
        "bilinmeyen** ayrımı bütün aşamalarda korunmuştur. İkinci kısıt kohort "
        "büyüklüğüdür; 62 ilaç, esnek modellerin kapasitesini kullanmasına izin "
        "vermeyecek kadar küçüktür ve bu sınır bütün model seçimlerini etkilemiştir.")
    k.govde_metni(
        "Teknik kısıtlar da tasarımı biçimlendirmiştir. Büyük DrugBank ve STRING "
        "dosyalarının akışla okunması yerel bellek sınırından, ağırlıkların ve test "
        "anahtarlarının sürümlenmesi ise hesaplanan bir sonuca yeniden erişme "
        "gereksiniminden doğmuştur. Teknik erişim paylaşım hakkı sağlamadığından "
        "dağıtım hasta bilgisi, hizmet anahtarı ve lisanslı ham veri içermez. "
        "Projenin kabul ölçütleri araştırma prototipinin davranışıyla sınırlıdır; "
        "kurumsal tasarruf, klinik kullanım izni ve KVKK uygunluğu bu çalışma "
        "kapsamında ölçülmüş çıktılar arasında yer almaz.")
    k.sekil(FIG / "WP07/06_leakage_boundary.png",
            "Özellik, denetim ve etiket kolları arasındaki sızıntı sınırı.", 13.0)
    k.govde_metni(
        "Kimliği belirsiz bir ürünü yanlış ana moleküle bağlamak, hesaplama doğru "
        "olsa bile sonraki açıklamaların tamamını yanlış varlığa taşır. Bu nedenle "
        "eşleme durdurulabilir. İndüktif kullanımın kabul koşulu, dış test ilacının "
        "etiketlerinin terim sözlüğünü, ölçekleri ve model seçimini "
        "etkileyememesidir; Şekil 2.2 bu sınırın nerede çizildiğini gösterir.")

    k.baslik(2, "Tasarımın İlişkili Olduğu Mesleki Standartlar")
    k.govde_metni(
        "Tasarım, terminoloji ve kimlik düzeyinde yerleşik standartlara dayanır. "
        "Yan etki terimleri MedDRA tercih edilen terim (PT) düzeyinde ve UMLS kavram "
        "kimliğiyle (CUI) tutulur; ilaç kimliği DrugBank birincil kimliği, "
        "stereokimyasal bileşik kimliği ise PubChem Compound ID ile ifade edilir. "
        "İlaç sınıflaması Dünya Sağlık Örgütü ATC sistemine göre yapılır ve bu "
        "çalışmada J01 sistemik antibakteriyeller kohortu kullanılır. Protein "
        "kimliği UniProt accession, protein ilişkileri ise STRING v12.0 "
        "kaynağındadır.")
    k.govde_metni(
        "Yazılım tarafında tekrar üretilebilirlik ilkeleri izlenmiştir: kaynak "
        "sürümleri, kütüphane sürümleri, rastgelelik tohumları, bölme kimlikleri ve "
        "çıktı özetleri kayıt altındadır. Veri kaynaklarının lisans koşulları "
        "gözetilmiş, lisanslı ham veri dağıtıma konmamıştır. Prototip hasta verisi "
        "işlemediğinden klinik yazılım standartlarının kapsamına girmez; bu durum "
        "Bölüm 8.5’te açıkça sınır olarak belirtilmiştir.")
    k.bolum_sonu("arap")


def bolum3(k):
    k.baslik1("KURAMSAL TEMEL VE LİTERATÜR")

    k.baslik(2, "Gözlenen Kayıt ile Advers Olay Ayrımı")
    k.govde_metni(
        "SIDER’in gözlem mekanizması, hangi çıkarımların yapılabileceğini sınırlar. "
        "Ürün metninde kodlanmış bir terim kaynak pozitifidir [1]. Bir terimin veri "
        "tabanında bulunmaması ise olayın görülmemesiyle, belgelenmemesiyle veya "
        "eşleme kapsamı dışında kalmasıyla uyumludur. DrugBank’ın kimya ve hedef "
        "bilgileri bu kayıtları bağlama yerleştirir [2], ancak ortak bir hasta, doz "
        "ya da zaman ekseni sağlamaz. Pozitif–etiketsiz öğrenme literatüründe bu "
        "belirsizlik, etiketlenme olasılığına ilişkin varsayımların önemini açıklar "
        "[6]. Burada bu olasılığı kestiren ayrı bir düzeltme uygulanmamıştır. "
        "Öğrenme hedefi, kaynağın kayıt örüntüsünü sıralayacak bir vekil "
        "değişkendir.")

    k.baslik(2, "Heterojen Graf Temsilleri")
    k.govde_metni(
        "Bir heterojen grafın ayırt edici özelliği, kenarın anlamını uçlarındaki "
        "varlıklarla birlikte korumasıdır. İlaç ile taşıyıcı protein arasındaki "
        "kayıt, iki insan proteini arasındaki STRING ilişkisiyle aynı biyolojik "
        "gözlemi temsil etmez. STRING’in birleşik skoru bir işlevsel ilişkinin "
        "kaynaklarca ne ölçüde desteklendiğini gösterir [3]. Bu nedenle skor, "
        "protein başına bir özellik yerine altgrafın kapsamını tanımlayan eşikte "
        "kullanılmıştır. Benzer biçimde merkezilik, düğümün seçilmiş ağdaki "
        "konumuna ilişkin bir ölçüdür [11]. Antibakteriyellere göre oluşturulmuş "
        "bir insan altgrafındaki merkezilik, organizmalar arasında doğrudan bir "
        "işlev karşılaştırmasına izin vermez.")

    k.baslik(2, "İç İçe Graf Yaklaşımları ve Ağ Difüzyonu Alternatifleri")
    k.govde_metni(
        "İç içe graf (Graph-in-Graph) yaklaşımlarının ortak fikri, bir düğümün "
        "kendisinin de bir graf olmasıdır: molekül düzeyinde bir düğüm, atom "
        "düzeyinde bir altgrafın özetidir. Bu kurgu iki düzey arasında bilgi "
        "aktarımına olanak tanır. Tam biçimselleştirmede yan etki düğümleri de ağın "
        "parçası olur ve ilaç–yan etki kenarları mesaj taşır. Bu çalışmada bu seçenek "
        "ayrıntılı biçimde değerlendirilmiş, ancak **uygulanmamıştır**: eğitim "
        "grafında yan etki kenarlarının bulunması, tahmin edilmesi istenen ilişkinin "
        "bir bölümünü girdiye taşır ve indüktif değerlendirmenin anlamını ortadan "
        "kaldırır. Bölüm 5.4 bu kararın gerekçesini ve bunun yerine sınanan "
        "varyantı açıklar.")
    k.govde_metni(
        "Bu kararın **iç içe graf yönünün tümüyle bırakılması anlamına gelmediği** "
        "vurgulanmalıdır. Uygulanan atom–molekül mesaj aktarımı ve Bölüm 5.4’te "
        "tanımlanan bilgi aktarımı varyantı bu yönün kendisidir; dışarıda bırakılan, "
        "yalnızca yan etki düğümü içeren biçimselleştirmedir.")
    k.govde_metni(
        "Klasik ağ difüzyonu yöntemleri aynı yapı üzerinde farklı bir soru sorar. "
        "Yeniden başlatmalı rastgele yürüyüş (RWR) belirli bir olasılıkla başlangıç "
        "düğümüne döner. Kişiselleştirilmiş PageRank (PPR) bu başlangıcı sorguya "
        "özgü bir dağılımla tanımlar. İlaç–hedef kestirimi için geliştirilen ISLRWR "
        "bu yöntem ailesinin bir örneğidir [7]. Bu yöntemler bu çalışmada "
        "**uygulanmamış, karşılaştırma bağlamı olarak korunmuştur.**")
    k.govde_metni(
        "Uygulanmama gerekçesi iki noktada toplanır. Birincisi, bu yöntemler "
        "sıralamayı yalnız ağ topolojisinden türetir; düğümün kendi özelliklerini — "
        "molekülün kimyasal tanımlayıcılarını veya proteinin dizi bileşimini — "
        "doğrudan kullanmaz. Oysa bu çalışmanın birincil sorusu, tam da bu "
        "özelliklerin sıralamaya ne kattığıdır. İkincisi ve daha belirleyicisi, bir "
        "yürüyüşün sorgu ilacından doğru terime ulaşabilmesi için o ilacın ağda "
        "zaten bağlantılı olması gerekir. Eğitimde hiç görülmemiş bir ilacın yan "
        "etki kenarı bulunmadığından yürüyüş başlayamaz; kenarlar baştan ağa "
        "konursa da ulaşılan sonuç, indüktif bir sıralama başarısı değil, girdiye "
        "verilmiş bir cevabın geri okunması olur.")
    k.govde_metni(
        "Bu nedenle çalışma, düğüm özelliklerini doğrudan kullanan ve eğitimde "
        "görülmemiş ilaçlar için de skor üretebilen öğrenmeli graf mimarilerine "
        "yönelmiştir. Difüzyon ailesinin incelenen kaynaklardaki uygulamaları için "
        "bağımsız, eğitim dışı başarım ölçümü bulunmadığından, bu yöntemler sayısal "
        "bir karşılaştırma kolu olarak değil, yöntem ailesi düzeyinde bir "
        "alternatif olarak anılmaktadır.")

    k.baslik(2, "Moleküler Graf Öğrenme")
    k.govde_metni(
        "Moleküler mesaj aktarımında atomun temsili, bağlarla ilişkilendirildiği "
        "komşulardan gelen bilgiyle güncellenir. Molekül düzeyindeki özet böylece "
        "aynı sayıda verici ve alıcı içeren iki yapıyı yerleşimlerine göre ayırt "
        "edebilir [13]. Bu olasılığın yeni iskeletlere taşınması ayrı bir sınama "
        "gerektirir [4]. Heterojen konvolüsyonu bir algılayıcıyla birleştiren "
        "çalışmalar [8] ve ilaç çiftlerinin yan etkilerini ele alan çok ilişkili "
        "ağlar [9], benzer hesaplama araçlarını farklı karar birimlerine uygular. "
        "Bu çalışmada karşılaştırılabilir kanıt, tek ilacın aynı terimlerinde atom "
        "dalı açıldığında veya kapatıldığında oluşan sıralama farkıdır.")

    k.baslik(2, "Açıklanabilirlik")
    k.govde_metni(
        "Açıklanabilirlik iki ayrı denetime bağlıdır. SHAP, modelin çıktısını "
        "tanımlı bir arka plana göre özellik katkılarına ayırır [14]. Graf modelinde "
        "bir mesajı kapatmak ise hesap yoluna yapılan müdahaleye duyarlılığı ölçer. "
        "Her iki sonuç da kullanılan modele ve karşılaştırmanın tanımına bağlıdır "
        "[12]. Metin tarafında benzer bir ayrım vardır: bir alıntının varlığı, o "
        "alıntının iddiayı desteklediğini tek başına göstermez [10]. Bu nedenle model "
        "açıklamasında arka plan ve çıktı ölçeği, kaynak incelemesinde ise alıntı, "
        "istisna ve kapsam birlikte raporlanmıştır.")

    k.baslik(2, "Değerlendirme Ölçütleri ve İndüktif Genelleme")
    k.govde_metni(
        "Bilinen düğümler arasındaki eksik bir ilişkiyi tamamlamak transdüktif bir "
        "görevdir. Çalışmanın hedeflediği indüktif durumda ise sorgu ilacı öğrenme "
        "sırasında görülmemiştir. Aynı ilacın farklı terimlerini rastgele bölmek bu "
        "koşulu ihlal eder. Sınamanın ilaç düzeyinde yapılması, başarı ölçütünün de "
        "kullanıcının inceleme birimiyle uyumlu olmasını gerektirir. PR ve ROC "
        "ölçütleri dengesiz sınıflarda farklı yönleri öne çıkarır [5]. Burada bir "
        "ilacın sıralamasının başında kaç kaynak pozitifinin toplandığı inceleme iş "
        "yüküyle doğrudan ilişkilidir.")
    k.govde_metni(
        "Ölçütün **hangi yönde** sıralama yaptığı da ayrıca belirtilmelidir. Sabit "
        "bir ilaç için terimleri sıralamak ile sabit bir terim için ilaçları "
        "sıralamak farklı sorulardır ve aynı skor kümesi bu iki yönde farklı "
        "sonuçlar verebilir. Bölüm 6.6 bu ayrımın bu çalışmadaki sonuçlar açısından "
        "belirleyici olduğunu göstermektedir.")
    k.bolum_sonu("arap")
