# WP10 — Kullanıcı kabulü ve nihai kapanış

07.11.2026. **WP10 kullanıcı tarafından araştırma kapsamında kabul edildi ve kapatıldı.** Bu ek, mevcut sonuçları değiştirmeyen son denetimdir. Yeni eğitim, optimizer adımı veya yöntem/seed/etiket seçimi yapılmadı. Önceki sonuç raporu ve model kartı aynen korunur.

## Kapanış kanıtı

| Kontrol | Gerçek sonuç |
| --- | --- |
| Kayıtlı modeller |152 NPZ +152 metadata JSON;dosya ve sayısal state hash'leri uyumlu |
| Önceki artefaktlar |3013 dosyanın içeriği aynı;B0/B1/B2,WP09 veWP10 dahil |
| Kaynak/kod/model manifestleri |4 mevcut manifestte bütün girişler doğrulandı |
| OOF tekrar üretimi |40 outer modelin143896 kayıtlı skoru doğrulandı;max mutlak fark1.11e-16 |
| Karşılaştırma anahtarları |Ana/stres,paired54/own61 için dört kolda aynı drug/fold/PT kapsamı |
| Önceki test kaydı |19/19 geçiş ve17.812 saniyelik özgün log,aynı SHA-256 ile korundu |
| Bu turda yeniden çalışan testler |13/13 salt okunur test;15.263 saniye |
| Yeniden çalıştırılmayan testler |6 trainer/backward yoluna ait test;özgün başarılı kayıt korunur |
| Yeni fit/optimizer |0/0;yanlışlıkla fit/AdamW çağrısı için guard aktifti ve tetiklenmedi |

Kapanışta bütün19 testi yeniden çalıştırmak, kullanıcı tarafından yasaklanan kontrollü tekrar-fitleri de başlatırdı. Bu nedenle yalnız mevcut modelleri/kaynakları/OOF'yi doğrulayan13 test seçildi. Altı testin geçmiş doğrulaması yeni çalışmış gibi sunulmadı. Seçim ve nedenleri `test_selection.csv`, yeni log `readonly_tests_rerun.txt` içindedir.

OOF kontrolü kayıtlı ağırlıklarla salt okunur inference yapar;eski skor dosyasını veya metrikleri yazmaz. Kaynak hash kontrolü mevcut küçük QA/provenans,split,encoder ve model dosyalarını kapsar;büyük ham XML/STRING dosyaları tekrar taranmadı veya yeniden hash'lenmedi. Yeni biyolojik kaynak/paket/API yoktur.

## Aynen korunan bilimsel sonuç

| Ana paired54 model | Drug-macro observed-record AP |
| --- | ---: |
| A0P0 | 0.642740 |
| A0P1 | 0.643636 |
| A1P0 | 0.645930 |
| A1P1 | 0.646234 |

Atom dalının küçük koşullu katkısı korunur:ana marjinal fark+0.002894,koşullu%95CI[+0.000773;+0.005470]. Ana koşullu atom farkları pozitiftir;stres koşullu farklarının aralıkları sıfırı içerir. Stres marjinal alt sınırının sıfıra çok yakın olması güçlü sağlamlık kanıtı sayılmaz.

Ek PPI katkısı gösterilmedi:ana marjinal fark+0.000600,CI[−0.001133;+0.002316]. Etkileşim−0.000591,CI[−0.003102;+0.001541];sinerji veya antagonizma kanıtı yoktur. B0/B1'e belirgin üstünlük sağlanamadı. A1P1−B0_like_B2=−0.000370 veA1P1−B1=−0.009408 farklarının koşullu CI'ları sıfırı içerir. B2 karşısındaki toplam fark yalnız atom/PPI topolojisine atfedilemez.

Bu yorumlar sabit OOF modellerine koşullu,keşifsel araştırma sonuçlarıdır;bağımsız dış doğrulama veya genel istatistiksel üstünlük değildir. Sıfırı içeren CI eşdeğerlik kanıtı sayılmaz. Açıklanabilirlik çalışması bu sonuçları geriye dönük başarıya çeviremez.

## Kapsam ve klinik yorum sınırı

62 ilaç,1061 kaynak PT ve6416 pozitif ilişki;54 açık atom maskesi/8 QC bekletmesi;61 skorlanabilir ilaç veMethenamine abstention korunur. Ana paired54'te13964 çift=3820 kaynak pozitif+10144 unknown;1685 kaynak pozitif hedef/fit kapsamı dışındadır. Bu1685 bütün62'nin yanlış-negatif sayısı değildir. Sınıf NA,tek-proxy train hedefleri veönceden dışlanan ortak inner kapsamı değişmedi.

**Unknown çiftler doğrulanmış biyolojik negatif değildir.** Model çıktısı SIDER kayıt sıralama skorudur;klinik yan etki riski,kalibrasyon,nedensellik veya hasta güvenliği doğrulaması değildir. Atom/protein-PPI mesaj geçişi teknik olarak çalışır;bu bütün protein biyolojisinin yararsızlığı veya tam moleküler GiG araştırmasının tamamlandığı anlamına gelmez.

## Dosyalar ve durma noktası

- `reports/qa/WP10/final_closure_v1/`:152 model hash tablosu,40 outer OOF tekrar üretimi,anahtar/kaynak kontrolleri,test seçimi/logu ve kapanış özeti.
- `notebooks/WP10_final_closure.ipynb`:yalnız kayıtlı kanıtları gösteren çalıştırılmış kapanış notebook'u;yeniden fit yapmaz.
- `reports/figures/WP10/final_closure_v1/`:kabul edilmiş AP ve kapsam görselleri;WP11 açıklaması değildir.
- [WP11 hazırlık/karar notu](WP11_PREPARATION_DECISION.md):yalnız aktif yol haritasının kapsamı ve onay bekleyen seçimler.

Önceki rapor/kod/veri/model dosyaları değiştirilmedi. `run_status.md` yalnız güncel kapanış durumu eklenerek izlenir;önceki tam bayt içeriği `run_status_before.md` içinde saklanır ve tarihsel manifestteki hash'iyle eşleşir. Eski eğitim manifestleri güncellenmedi. **WP11 uygulaması,SHAP veya graph attribution hesabı,yeni model ve yeni eğitim başlatılmadı. Bu kapanış ve hazırlık notunda durulur.**
