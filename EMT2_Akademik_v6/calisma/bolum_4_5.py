# -*- coding: utf-8 -*-
"""Bolum 4-5: Veri ve Yontem, Karsilastirilan Mimariler."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "reports/figures"
TESLIM = ROOT / "EMT2_Teslim_v1"


def bolum4(k):
    k.baslik1("VERİ VE YÖNTEM")

    k.baslik(2, "Veri Kaynakları ve Sürümler")
    k.govde_metni(
        "Kaynak seçimi, her tablonun karşılayabileceği kanıt gereksinimine göre "
        "yapıldı. Ana ilaç kimliği, ATC kodu, protein rolü, accession ve dizi "
        "DrugBank XML’den alındı. XML kökündeki sürüm 5.1, dışa aktarım tarihi "
        "4 Ocak 2026’dır; bu tarih indirme tarihini göstermez. Etiket için SIDER "
        "4.1’in tercih edilen terim (PT) düzeyi, kimlik köprüsü için drug links.csv "
        "içindeki PubChem Compound ID kullanıldı. Proteinler arası ilişkilerde "
        "STRING v12.0’ın yerel insan ve E. coli kaynakları incelendi.")
    k.cizelge(
        "Kullanılan kaynaklar, sürümleri ve kanıt işlevleri.",
        [["Kaynak", "Sürüm", "Sağladığı kanıt", "Rolü"],
         ["DrugBank XML", "5.1", "Ana kimlik, ATC, protein rolü, dizi", "Girdi"],
         ["SIDER", "4.1", "İlaç–PT gözlenen kayıt", "Etiket"],
         ["drug links.csv", "DrugBank", "DrugBank ↔ PubChem CID köprüsü", "Kimlik"],
         ["STRING", "v12.0", "İnsan protein–protein ilişkileri", "Topoloji"],
         ["RDKit", "2026.09.1", "Yapı doğrulama, tanımlayıcı, atom grafı", "Araç"]],
        [3.6, 2.0, 6.2, 2.4])
    k.govde_metni(
        "Eğitim koluna yalnız aynı taksonda doğrulanmış insan bağlantıları, birleşik "
        "destek skoru en az 700 olduğunda alındı. Bir kaynak için erişim tarihi veya "
        "lisans ayrıntısı kayda geçmemişse tarih ya da izin tahmin edilmedi. "
        "UniProt accession’larının varlığı ayrı bir UniProt veri indirmesine işaret "
        "etmez; bu kimlikler DrugBank XML’den çıkarılmıştır. İşlenmiş deney "
        "çıktılarının SHA-256 özetleri kanıt dizininde tutulur; büyük ham dosyalar "
        "için geriye dönük tam dosya özeti üretilmemiştir.")

    k.baslik(2, "Kimlik Eşleme ve Etiket Tanımı")
    k.govde_metni(
        "Kohort, DrugBank’te J01 ATC kodu taşıyan ana kayıtlardan kuruldu. Yalnız "
        "kombinasyon kodu içeren kayıtlar ayrıca incelendi. Ad benzerliği bir tuz "
        "kaydını (DBSALT) yeni etkin maddeye dönüştürmedi. PubChem madde kimliği "
        "(SID) ile bileşik kimliği (CID) ayrıldıktan sonra SIDER stereokimyasal "
        "kimliği ve PT kavram kimliği (CUI) birlikte kontrol edildi.")
    k.sekil(FIG / "WP03/03_identity_flow.png",
            "Kimlik köprüsü: DrugBank ana kaydından SIDER tercih edilen terimine.",
            13.0)
    k.govde_metni(
        "Aynı ilacın aynı CUI için birden fazla satırı tek gözlem sayıldı. Bu sayede "
        "çok belgelenmiş bir çift, yalnız tekrar sayısından dolayı daha güçlü öğrenme "
        "sinyali kazanmadı. Etiket uzayı ikili değil, **pozitif / bilinmeyen** "
        "biçimindedir: SIDER’de kaydı bulunan çift pozitif, bulunmayan çift ise "
        "bilinmeyendir. Bu çalışmada bilinmeyen çiftler doğrulanmış negatif olarak "
        "işaretlenmemiş ve negatif örnekleme yapılmamıştır. Bu işlem terimlerin "
        "tamamı için resmî Türkçe eşdeğerlik sağlamaz.")

    k.baslik(2, "Kimyasal Yapı Kalite Kontrolü")
    k.govde_metni(
        "Moleküler yapıda ayrıştırılabilirlik, stereo kimlik ve çok bileşenli yapı "
        "ayrı denetlendi. Böylece yazılımın okuyabildiği bir yapının yanlış bileşiğe "
        "ait olma olasılığı gözden kaçmadı. İlaç için molekül ağırlığı (MW, g/mol), "
        "Crippen LogP, hidrojen bağı verici (HBD) ve alıcı (HBA) sayıları ile "
        "topolojik polar yüzey alanı (TPSA, Å²) hesaplandı. Bir arada bu beş alan "
        "büyüklük, lipofilisite ve polarite açısından düşük boyutlu bir başvuru "
        "temsili sağlar.")
    k.govde_metni(
        "Bu beş alanın seçilmesinin nedeni yalnız hesaplama kolaylığı değildir. "
        "Büyüklük, yağda çözünürlük ve polarite, bir molekülün vücutta nasıl "
        "dağıldığına ilişkin en temel üç eksendir; bu nedenle düşük boyutlu ama "
        "yorumlanabilir bir başvuru temsili oluştururlar. Kalite denetiminden "
        "geçmeyen bir yapı için bu alanlar hesaplanmamış, bunun yerine özelliğin "
        "bulunamadığı ayrı bir maske alanıyla kaydedilmiştir.")

    k.baslik(2, "Moleküler Atom–Bağ Grafı")
    k.govde_metni(
        "Atom ve bağ düzeyindeki girdiler sırasıyla 44 ve 14 alan içerir. Atom "
        "alanları element kimliğini, değerlik ve yük durumunu, halka üyeliğini ve "
        "hibritleşmeyi kodlar; bağ alanları bağ derecesini, halka içinde olup "
        "olmadığını ve konjugasyonu taşır. Bu ayrımın nedeni şudur: aynı sayıda "
        "hidrojen bağı vericisi içeren iki molekül, bu vericilerin hangi atomlara "
        "ve hangi halka yapısına bağlı olduğuna göre farklı davranabilir. Beş "
        "tanımlayıcı bu yerleşim bilgisini taşımaz; atom grafı taşır.")
    k.govde_metni(
        "Mesaj aktarımında her atomun temsili, bağ özellikleriyle birlikte "
        "komşularından gelen bilgiyle güncellenir; molekül düzeyindeki özet ise bu "
        "atom temsillerinin ortalamasıdır. Bu özet, molekülün tek bir vektörle "
        "gösterimidir ve kimyasal tanımlayıcıların yanında ek bir bilgi kanalı "
        "oluşturur.")

    k.baslik(2, "Protein Özellikleri ve İlaç–Protein Rolleri")
    k.govde_metni(
        "Protein dizisi ayrıştırılırken önce FASTA başlığı uzaklaştırıldı, ardından "
        "kalan dizinin 20 standart amino asit alfabesine uygunluğu denetlendi. Aksi "
        "durumda başlıktaki harfler dahi bileşim hesabına girebilirdi. Ayrı "
        "accession’ların aynı diziyi taşıması bir kimlik uyuşmazlığı olarak otomatik "
        "birleştirilmedi.")
    k.govde_metni(
        "Proteinin 56 alanı, altı dizi tanımlayıcısı ile üç bileşim bloğuna ayrılır. "
        "İlk altı alan uzunluk, ortalama molekül ağırlığı, teorik izoelektrik nokta, "
        "aromatik kalıntı oranı, ortalama hidropati (GRAVY) ve pH 7’de hesaplanan "
        "net yüktür. Bunlara 20 amino asit frekansı, beş grup frekansı ve sıralı "
        "grup çiftlerinin 25 dipeptit frekansı eklenir. Çakışmayan gruplar AGILMPV, "
        "FWY, CNQST, HKR ve DE’dir. Tek kalıntı frekansları dizi uzunluğuna, ardışık "
        "çiftler uzunluğun bir eksiğine bölünür.")
    k.govde_metni(
        "Grupların çakışmaması ayrıca denetlenmiştir; her kalıntının tam olarak bir "
        "gruba atandığı testle doğrulanmıştır. Protein accession’ının ilk harfinden "
        "türetilen ve bir kalite derecesi gibi görünen türetilmiş alan, bilimsel "
        "karşılığı bulunmadığı için özellik kümesinden **çıkarılmıştır**. Gözlenen "
        "uzunluk 92–4.655 amino asit, hesaplanan kütle 10,43–521,95 kDa ve teorik "
        "izoelektrik nokta yaklaşık 4,65–11,22 arasındadır. Bu büyüklükler "
        "modifikasyonsuz dizi üzerinden hesaplandığı için olgun proteinin deneysel "
        "kütlesini veya ortam içindeki işlevini ölçmez.")
    k.govde_metni(
        "İlaçtan proteine dört ayrı rol tanımlanır: hedef, enzim, taşıyıcı "
        "(transporter) ve taşıyıcı protein (carrier). Bu dört rol birleştirilmez, "
        "çünkü bir ilacın etkisini gösterdiği hedef ile onu taşıyan protein farklı "
        "biyolojik ilişkilerdir ve aynı sayısal kanalda toplanmaları bu ayrımı "
        "kaybettirir.")

    k.baslik(2, "İnsan Protein Etkileşim Ağı")
    k.govde_metni(
        "STRING birleşik destek skoru, bir işlevsel ilişkinin kaynaklarca ne ölçüde "
        "desteklendiğini gösterir. Bu skor bir bağlanma kuvveti veya yan etki "
        "olasılığı değildir; bu nedenle **protein düğümüne özellik olarak "
        "verilmemiş**, yalnız altgrafın kapsamını belirleyen eşik olarak "
        "kullanılmıştır. Yönsüz bir ilişki, mesajların iki yönde iletilmesi için iki "
        "indeks sütununda saklanır; betimsel sayımda ise tek çift olarak kalır.")
    k.sekil(FIG / "WP06/05_human_ppi.png",
            "İnsan proteinleri arasında kaynakta tanımlı etkileşim ağı; bir çizgi "
            "hasta olayı değildir.", 12.5)
    k.govde_metni(
        "E. coli tarafında 23 accession’ın takma adı eşlenebilse de DrugBank’teki "
        "K-12 taksonu 83333 ile STRING’deki MG1655 taksonu 511145 aynı kesinlikte "
        "bir eşleme değildir. Bu nedenle bakteri ağı keşif amacıyla incelenmiş, "
        "eğitilen insan koluna **katılmamıştır**.")

    k.baslik(2, "Heterojen Grafın Kurulması")
    k.govde_metni(
        "Graf G=(V,E,τ,ρ) ile gösterilir. V varlıklar kümesi, E ilişki kümesi, τ "
        "düğümün tipi, ρ kenarın rolüdür. Öğrenmede görülebilen ilişkiler ayrıca her "
        "eğitim bölmesi için yeniden oluşturulur. Sınanan ilacın yan etki kenarını "
        "modele göstermek, o ilaç için tahmin edilmesi gereken cevabı girdi olarak "
        "vermek olurdu; bu nedenle test ilaçlarına ait yan etki kenarları ve "
        "bunların ters yönleri mesaj geçişi grafından çıkarılır.")
    k.govde_metni(
        "Yönsüz ağın yoğunluğu D=2m/[n(n−1)] olarak hesaplanır; n izolatlar dâhil "
        "protein sayısı, m benzersiz yönsüz çift sayısıdır. İlaç–protein rollerinde "
        "giriş ve çıkış dereceleri ayrı tutulmuştur. Çap ve ortalama yol için "
        "yolların tanımlı olduğu bağlantılı bileşen kullanılır. Ağırlıklı derece "
        "Σsᵢⱼ komşu kenarlardaki destek puanlarını toplar; yüksek desteğin uzun bir "
        "mesafe biçiminde yorumlanmasını önlemek için bu puanlar en kısa yol "
        "hesabına mesafe olarak verilmemiştir.")

    k.baslik(2, "Eksik Veri, Maskeleme ve Çekimserlik")
    k.govde_metni(
        "Bir özelliğin bulunabilirliği ayrı bir maske alanında tutulur. Böylece eksik "
        "blok için seçilen ölçeklenmiş nötr değer, gerçekten gözlenmiş bir sıfır "
        "değerinden ayırt edilebilir. Bu ayrım yapılmazsa model, eksikliği "
        "gözlemle karıştırır ve eksik kayıtların yoğun olduğu ilaçlarda sistematik "
        "olarak yanılır. Hiçbir kişiselleştirilmiş girdi bulunmadığında sistem skor "
        "üretmekten çekinir; bu bir hata durumu değil, tanımlı bir çıktıdır.")

    k.baslik(2, "Sızıntıya Karşı Önlemler")
    k.govde_metni(
        "Her dış sınamada x′=(x−μₜ)/σₜ dönüşümünün ortalaması ve ölçeği **yalnız "
        "eğitim ilaçlarından** elde edildi. Terim sözlüğü de yalnız eğitim "
        "bölmesinden kurulur: bir terimin sözlüğe alınması için en az beş "
        "destekleyici ilaç ve iki bağımsız grup aranır; tek gözlenen sınıf içeren "
        "başlık eğitilmez. Model seçimi yalnız iç katlarda yapılır ve hiçbir dış "
        "test skoru seçime girmez.")
    k.govde_metni(
        "Bu önlemlerin fiilen çalıştığı ayrıca sınanmıştır. Eğitim ve test ilaç "
        "kümelerinin kesişiminin boş olduğu, aynı ilaç–terim çiftinin iki bölmede "
        "birden bulunmadığı ve mesaj geçişi grafında test kenarı kalmadığı otomatik "
        "denetimlerle doğrulanmıştır. Mimari genişletme deneyinde ise eğitimden önce "
        "sekiz maddelik bir sentetik doğrulama kapısı uygulanmış, eklenen hesap "
        "yolunun analitik olarak beklenen değeri ürettiği gösterilmiştir. Bütün "
        "doğrulama testleri tek komutla çalıştırılabilir durumdadır ve kayıtlı "
        "modellerin bütünlüğü her düzenlemeden sonra yeniden denetlenmiştir.")

    k.baslik(2, "Eğitim ve Değerlendirme Protokolü")
    k.govde_metni(
        "Model ayarları üç iç bölmede, nihai başarım beş dış bölmede "
        "değerlendirildi. Birincil protokolde kimyasal bağlantısallık kimliği "
        "kullanıldı ve örneğin levofloksasin ile ofloksasin aynı grupta kaldı. "
        "Önceden kaydedilmiş **stres protokolünde** ise ortak iskelet veya en az 0,8 "
        "Tanimoto benzerliği gösteren yapılar birlikte tutuldu; bu protokol "
        "kimyasal olarak daha uzak genellemeyi sınar. Bir ilacın dış bölme (OOF) "
        "skoru, o ilacı görmeyen modelden geldiği için genellemenin hangi birim "
        "üzerinde sınandığı izlenebilir.")
    k.govde_metni(
        "Ortalama kesinlik AP=Σₖ(Rₖ−Rₖ₋₁)Pₖ ile hesaplanır; bir sıralama eşiğinde P "
        "kesinlik, R duyarlılıktır. **İlaç-makro AP** önce her ilacın terim sırasını "
        "değerlendirir ve ilaçlara eşit ağırlık verir; bu çalışmanın birincil "
        "ölçütüdür, çünkü kullanıcının inceleme birimi bir ilaçtır. Mikro AP bütün "
        "skorlanabilir çiftleri havuzlar. **Sınıf-makro AP** ise her terim için "
        "ilaçların ne kadar iyi sıralandığını sorar. AUROC, gözlenen çiftin "
        "etiketsiz çiftten yüksek sıralanma payıdır ve eşitlik yarım sayılır.")
    k.govde_metni(
        "Güven aralıkları için ilaç grubu düzeyinde 1.000 yeniden örnekleme "
        "uygulanmıştır. Aralıklar sabit dış bölme tahminleri üzerindeki ilaç grubu "
        "değişkenliğini yansıtır; yeniden öğrenmenin ve yeni bir popülasyona "
        "aktarımın belirsizliğini **içermez**. İki model arasındaki farkın "
        "istatistiksel olarak ayırt edilebilir sayılması için eşleştirilmiş farkın "
        "koşullu %95 aralığının sıfırı içermemesi aranır; bu ölçüt bütün "
        "karşılaştırmalarda aynı biçimde uygulanmıştır.")
    k.bolum_sonu("arap")


def bolum5(k):
    k.baslik1("KARŞILAŞTIRILAN MİMARİLER")
    k.govde_metni(
        "Bu bölümde karşılaştırılan modeller artan bilgi içeriğine göre "
        "sıralanmıştır. Tasarım ilkesi şudur: her yeni model, bir öncekine **tek bir "
        "bilgi kanalı** ekler. Böylece gözlenen başarım farkı, eklenen kanala "
        "atfedilebilir. Modeller büyütülmek için değil, belirli bir bilginin değerini "
        "ölçmek için tanımlanmıştır.")

    k.baslik(2, "Referans Modeller")
    k.govde_metni(
        "B0 her terim için eğitim ilaçlarında gözlenen kayıt oranını yumuşatma "
        "uygulamadan hesaplar ve aynı eğitim bölmesinde her sorguya aynı sıralamayı "
        "verir. Öğrenme içermediği için **vazgeçilmez bir alt sınırdır**: bir modelin "
        "ilaca özgü bilgi kullandığını iddia edebilmesi için önce bu sıklık "
        "referansını aşması gerekir.")
    k.govde_metni(
        "B1, beş kimyasal alan ve bir maskeyle her uygun PT için ayrı bir L2 "
        "düzenlemeli lojistik regresyon öğrenir; toplam altı girdi alanı kullanır. "
        "B2’nin 234 girdisi beş kimyasal alan, dört rolün 56’şar protein özelliği ve "
        "beş maskeden oluşur. Her başlıkta z=b+wᵀx′ ve s=1/(1+exp(−z)) kullanılır. "
        "İç doğrulamada düzenleme katsayısı C için 0,1, 1 ve 10 denenmiş, eşitlikte "
        "küçük değer seçilmiştir. Böylece ek biyolojik bilginin değeri, önce aynı "
        "doğrusal öğrenici üzerinde sınanabilir.")

    k.baslik(2, "Protein–Protein Mesaj Geçişi")
    k.govde_metni(
        "Protein temsilleri 56 alandan 32 boyuta indirgenir ve tek bir artık "
        "bağlantılı katmanda komşuların ortalaması alınır. Dört ilaç–protein rolünün "
        "özetlerine kimyanın sekiz boyuta dönüştürülen temsili eklenir. Bu mimarinin "
        "amacı, bir proteinin kendi dizi özelliklerinin yanında **ağdaki komşularının "
        "da** temsiline katkı yapıp yapmadığını ölçmektir.")
    k.govde_metni(
        "Bu sorunun yanıtlanabilmesi için mesajın hesaba gerçekten girdiğinin "
        "gösterilmesi gerekir. Bu nedenle gerçek ağ, PPI kapatılmış koşul ve üç "
        "karıştırılmış ağ aynı test anahtarlarında değerlendirilmiş; ayrıca kenarlar "
        "silindiğinde protein temsilinin değiştiği ve mesaj yolunun gradyan taşıdığı "
        "ayrı ayrı ölçülmüştür. Bir mimarinin protein ağını kullandığı, ancak mesaj "
        "fiilen ileri geçişte işleniyorsa iddia edilebilir.")

    k.baslik(2, "Atom ve Protein Dallarının Faktöriyel Tasarımı")
    k.govde_metni(
        "Atom dalı ile protein ağı dalının katkılarını ayırmak için dört koşullu "
        "faktöriyel bir tasarım kurulmuştur. A0P0’da iki topoloji de kapalıyken ana "
        "kimya ve protein rol özetleri korunur; A1P0’da atom dalı, A0P1’de protein "
        "ağı dalı, A1P1’de ise iki dal birden açılır. Dört koşul aynı birleşim "
        "katmanını, aynı bölmeleri ve aynı eğitim politikasını paylaşır.")
    k.govde_metni(
        "Faktöriyel kurgunun değeri, iki dalın yalnız ayrı ayrı katkılarını değil "
        "**etkileşimlerini** de ölçebilmesidir: iki kanalın birlikte kullanımı, "
        "ayrı ayrı katkılarının toplamından fazlasını sağlıyor mu? Tek bağ bilgili "
        "katmanla ortalama okuma kullanan atom dalı sekiz boyut üretir. Eğitim "
        "bağlamındaki başlık sayısı K ise toplam parametre sayısı 5.512+151K’dir.")
    k.sekil(FIG / "WP14/01_mimari_karsilastirma.png",
            "Karşılaştırılan mimarilerde bilgi kanalları ve birleşim noktası.", 13.5)

    k.baslik(2, "Graph-in-Graph Mimarisi ve Bilgi Aktarımı")
    k.govde_metni(
        "Yukarıdaki mimarilerde protein temsilleri yalnız dizi özelliklerinden "
        "türetilir; bir protein, kendisine bağlanan ilaçtan bağımsız olarak hep aynı "
        "vektörle temsil edilir. İç içe graf yaklaşımının asıl vaadi bu sınırı "
        "kaldırmaktır: molekül düzeyindeki bilgi, protein düzeyine **aktarılabilir**.")
    k.govde_metni(
        "Bu olasılığı sınamak için iki aday değerlendirilmiştir. Birinci adayda "
        "(GiG-1) protein gömmeleri, protein–protein adımından önce kendilerine "
        "bağlanan ilaçların kimyasal ve moleküler ön durumundan bir mesaj alır; "
        "yan etki düğümü kullanılmaz. İkinci adayda (GiG-2) ağa yan etki düğümleri "
        "de eklenir ve yalnız eğitim ilaçlarının yan etki kenarları mesaj taşır.")
    k.govde_metni(
        "**GiG-2 uygulanmamıştır.** Gerekçe yöntemseldir: yan etki düğümlerinin "
        "temsili, eğitim ilaçlarının etiket örüntüsünden öğrenilir ve bu temsil test "
        "ilacının skorlanmasında kullanıldığında, tahmin edilmesi istenen ilişkinin "
        "yapısı dolaylı olarak girdiye taşınır. Kenar düzeyinde maskeleme bu riski "
        "azaltır ama ortadan kaldırmaz; elde edilecek kazancın sızıntıdan mı yoksa "
        "mimariden mi geldiği ayrılamaz. Bu nedenle ölçülebilir ve yorumlanabilir "
        "olan birinci aday uygulanmıştır.")
    k.govde_metni(
        "Uygulanan varyantta omurga, bölmeler, hedef sözlüğü, ölçekleyici, kayıp "
        "işlevi ve epoch politikası değiştirilmemiş; eklenen yol 1.728 parametreyle "
        "sınırlandırılmıştır. Yeni yolun ağırlığı sıfırlandığında modelin "
        "karşılaştırma mimarisiyle **aynı** protein gömmesini verdiği gösterilmiştir. "
        "Böylece gözlenen fark yalnız eklenen bilgi akışına atfedilebilir. Kabul "
        "ölçütü sonuçlar görülmeden kilitlenmiştir.")
    k.govde_metni(
        "Rapor boyunca üç durum ayrı tutulur: **uygulanmış ve doğrulanmış** "
        "(GiG-1 varyantı), **değerlendirilmiş fakat uygulanmamış** (GiG-2) ve "
        "**yalnız tasarlanmış, eğitilmiş kaydı bulunmayan** (literatürdeki tam iç "
        "içe graf biçimselleştirmesi). Yalnız birincisi deneysel sonuç olarak "
        "sunulur.")

    k.baslik(2, "Ağaç Tabanlı Karşılaştırma Modelleri")
    k.govde_metni(
        "Yukarıdaki modellerin tamamı ya doğrusaldır ya da sinir ağı tabanlıdır. "
        "Bu, karşılaştırmada bir boşluk bırakır: kimyasal tanımlayıcılar ile gözlenen "
        "kayıt arasındaki ilişki, doğrusal bir modelin yakalayamayacağı **eksen "
        "hizalı etkileşimler** içeriyor olabilir. Örneğin yüksek molekül ağırlığının "
        "etkisi yalnız belirli bir polarite aralığında ortaya çıkıyorsa, doğrusal "
        "model bunu temsil edemez; ağaç tabanlı bir model edebilir.")
    k.govde_metni(
        "Bu boşluğu kapatmak için iki kol tanımlanmıştır: T1 rastgele orman (300 "
        "ağaç) ve T2 histogram tabanlı gradyan artırma (100 yineleme). Her iki kol da "
        "**B1 ile birebir aynı** girdileri, aynı bölmeleri, aynı uygunluk tanımını ve "
        "aynı terim sözlüğünü kullanır; değişen tek şey kestiricidir. Hiperparametre "
        "ızgarası sonuçlar görülmeden kilitlenmiş ve seçim yalnız iç katlarda "
        "yapılmıştır.")
    k.govde_metni(
        "Tekrar üretilebilirlik bu kolda açık bir tasarım tercihi gerektirmiştir. "
        "Rastgele ormanda paralel çalıştırma, aynı rastgelelik tohumuyla bile "
        "birebir aynı olasılıkları üretmemiştir; bu nedenle süresi uzasa da tek "
        "çekirdekli, yinelenebilir çalıştırma seçilmiştir. Benzer biçimde gradyan "
        "artırmanın dahili erken durdurması, seyrek terimlerde tek üyeli sınıf "
        "nedeniyle çalışamadığı için kapatılmış ve düzenleme ağaç derinliği "
        "üzerinden iç katta seçilmiştir. Her iki değişiklik de **hiçbir eğitim "
        "çalıştırılmadan önce** yapılmış ve gerekçesiyle kayda geçirilmiştir.")

    k.baslik(2, "Model Karmaşıklığı ve Hesaplama Maliyeti")
    k.cizelge(
        "Karşılaştırılan modellerin girdi genişliği ve ek bilgi kanalı.",
        [["Model", "Girdi alanı", "Eklediği bilgi kanalı"],
         ["B0 sıklık", "—", "Yok; eğitim kayıt oranı"],
         ["B1 kimya", "6", "Beş fizikokimyasal tanımlayıcı"],
         ["B2 kimya + protein", "234", "Dört rolde protein dizi özetleri"],
         ["Protein ağı modeli", "≈3.920 parametre", "Protein–protein komşuluğu"],
         ["A1P1 atom + ağ", "5.512+151K parametre", "Atom–bağ topolojisi"],
         ["GiG-1 varyantı", "+1.728 parametre", "İlaçtan proteine bilgi aktarımı"],
         ["T1 / T2 ağaç", "6", "Doğrusal olmayan eksen hizalı bölünmeler"]],
        [4.4, 4.2, 5.8])
    k.govde_metni(
        "Çizelge 5.1 karmaşıklığın bir başarı göstergesi olmadığını okumaya "
        "hazırlar. Daha fazla parametre taşıyan bir modelin daha iyi sıralama "
        "üretmesi gerekmez; 62 ilaçlık bir kohortta esnek modellerin kapasitesini "
        "kullanabilmesi için gereken örnek sayısı bulunmayabilir. Bölüm 6 bu "
        "beklentinin veriyle nasıl karşılandığını gösterir.")
    k.bolum_sonu("arap")
