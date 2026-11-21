"""Kapanış kanıtlarından rapor;WP11 için yalnız aktif planın karar notu."""
import json
import pandas as pd
from wp10_final_closure import ROOT,CLOSE
from wp10_train import QA,sha,write_json


def main():
    result=json.loads((CLOSE/'closure_checks.json').read_text(encoding='utf-8'))
    rows=pd.read_csv(CLOSE/'manifest_checks.csv')
    metrics=pd.read_csv(QA/'metrics_with_group_CI.csv')
    ap=metrics[metrics.protocol.eq('primary')&metrics.scope.eq('paired54')&metrics.metric.eq('drug_macro_AP')&metrics.model.isin(['A0P0','A0P1','A1P0','A1P1'])]
    roadmap=(ROOT/'docs/plan/ROADMAP_V7.md').read_text(encoding='utf-8')
    wp11=next(line for line in roadmap.splitlines() if line.startswith('| **WP11**'))
    write_json(CLOSE/'WP11_roadmap_scope.json',{'source':'docs/plan/ROADMAP_V7.md','source_sha256':sha(ROOT/'docs/plan/ROADMAP_V7.md'),
        'exact_WP11_row':wp11,'scope_review_only':True,'implementation_started':False})
    report=f'''# WP10 — Kullanıcı kabulü ve nihai kapanış

07.11.2026. **WP10 kullanıcı tarafından araştırma kapsamında kabul edildi ve kapatıldı.** Bu ek, mevcut sonuçları değiştirmeyen son denetimdir. Yeni eğitim, optimizer adımı veya yöntem/seed/etiket seçimi yapılmadı. Önceki sonuç raporu ve model kartı aynen korunur.

## Kapanış kanıtı

| Kontrol | Gerçek sonuç |
| --- | --- |
| Kayıtlı modeller |152 NPZ +152 metadata JSON;dosya ve sayısal state hash'leri uyumlu |
| Önceki artefaktlar |{result['accepted_prior_artifacts_preserved']} dosyanın içeriği aynı;B0/B1/B2,WP09 veWP10 dahil |
| Kaynak/kod/model manifestleri |{len(rows)} mevcut manifestte bütün girişler doğrulandı |
| OOF tekrar üretimi |40 outer modelin143896 kayıtlı skoru doğrulandı;max mutlak fark{result['OOF_max_absolute_error']:.3g} |
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
'''+''.join(f'| {r.model} | {r.estimate:.6f} |\n' for r in ap.itertuples())+'''
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
'''
    preparation='''# WP11 — Aktif yol haritasına göre kısa hazırlık ve karar notu

07.11.2026. **Yalnız kapsam incelemesi;WP11 uygulaması başlamadı.** Bu belge yeni yol haritası veya uygulama onayı değildir. WP10 kullanıcı kabulüyle kapandı;sonuçları ve bütün sabit referanslar korunur.

## Yol haritasının gerçek kapsamı

Aktif `docs/plan/ROADMAP_V7.md`,WP11'i şu şekilde tanımlar:

> Açıklanabilirlik:SHAP ≠ nedensellik,protein/edge attribution. Kimya baseline SHAP;GiG varsa hedef protein/kenar maskelerini test et;katkı kaynaklı. Çıktı:local/global SHAP ve graf açıklaması,limitler,stabilite.

İlk kapsam kimya baseline'ın açıklanmasıdır. Mevcut B1 modeli beş kimya özelliği ve kimya maskesiyle eğitilmiştir. Kayıtlı fold modelleri kullanılabilir;yeniden fit veya yeni model gerekmez. Daha yüksek test AP nedeniyle model seçmek yerine yol haritasının bu başlangıcı korunmalıdır.

Graf bölümü koşulludur. Projede gerçek atom ve protein-PPI encoder'ları ile geç füzyon vardır;bu otomatik olarak tam hiyerarşik GiG tamamlandı demek değildir. Mevcut modelde hedef protein/rol vePPI kenar yollarının açıklanabilirlik deneyi ayrıca açık seçilmelidir. Atom/bond için yeni açıklama yöntemi veya yeni mimari bu ilk notla kendiliğinden eklenmez.

## Uygulamadan önce açık yazılacak kararlar

| Konu | Hazırlık önerisi / karar sınırı |
| --- | --- |
| Açıklanacak model |Önce sabit B1;fold ve ağırlık hash'i korunur. Grafik bölümü için hangi kayıtlı WP09/WP10 kolunun kullanılacağı onayla belirlenir |
| Açıklanacak çıktı |Kaynak PT CUI ve ilgili foldun geçerli hedef sözlüğü açıkça seçilir. Logit ile observed-record sigmoid skoru karıştırılmaz;hangi ölçeğin açıklanacağı önceden yazılır |
| Background/referans |Yalnız ilgili train bölümünden;test ilacı veya test etiketleri referans seçimi/ölçekleme için kullanılmaz. Background kuralı ve kaynak ID'leri kaydedilir |
| Local/global özet |Local açıklama bir ilaç–PT–model üçlüsüne bağlanır. Global özetin ilaç/PT/fold kapsamı veNA paydası açıklanır;farklı fold sözlükleri aynı evrenmiş gibi birleştirilmez |
| Örnek seçimi |Kural sonuç hesabından önce sabitlenir;mevcut Erythromycin örneği kullanılabilecek kayıtlı adaydır. Başarılı örnekleri seçip genelleme yapılmaz |
| Protein/kenar maskesi |Target/enzyme/transporter/carrier ayrı tutulur. Strict insan700 evreni,query/train-cache sınırı veeksik modaliteler korunur. Context80 vekoşullu E.coli PPI eklenmez |
| Güvenilirlik kontrolleri |Açıklamanın seçilen model çıktısına bağlılığı,maske etkisi,indeks/kimlik hizası,tekrar hesaplama veistikrar kontrol edilir. Maske kaynak dışı biyolojik ilişki üretmez |

Kenar silme ile mesajı maskeyle sıfırlama aynı işlem varsayılmamalıdır; mean aggregation sırasında derece/normalizasyon kuralı açıkça tanımlanmalıdır. Maske denemeleri orijinal kaynak grafını ve paylaşılan train cache'ini değiştirmeyen ayrı kopyalarda planlanmalıdır. Özellik bağımlılıkları ve background varsayımı da yöntem kararında açıklanmalıdır.

Bu seçimler bu turda uygulanmadı veya nihai yöntem olarak sabitlenmedi. SHAP paketi yüklenmedi/çalıştırılmadı;protein/edge attribution veya açıklama skoru üretilmedi. Gerekli yöntem/bağımlılık ayrıntıları WP11 açıkça başlatıldığında mevcut ortam ve kayıtlı modellerle incelenmelidir.

## Değişmeyecek bilimsel sınırlar

- Açıklama model davranışını betimler;SHAP değeri veya büyük kenar katkısı biyolojik nedensellik/klinik risk kanıtı değildir. PPI açıklaması,WP09/WP10'da ek PPI performansı gösterilememiş olmasını tersine çevirmez.
- B1'in beş kimya alanı ile modalite maskesi ayrı yorumlanır. Maskeler,bilinmeyen girdiler ve8 yapı QC bayrağı biyolojik özellik gibi sunulmaz. `kalite_skoru`,PT sayısı veya raporlama sıklığı modele/açıklama girdisine eklenmez.
-62 envanter,1061 kaynak PT,6416 pozitif,54/8 atom maskesi,Methenamine abstention ve1685 ana kapsam dışı kaynak pozitif korunur. Unknown gerçek negatif değildir;etiketsiz bir çiftin açıklaması klinik yan etki doğrulaması sayılmaz.
- Yeni eğitim,seed/hiperparametre ayarı,performans iyileştirme araması veya etiketten türetilmiş yeni girdi yoktur. PDF/LLM/Ollama görevleri WP12 kapsamındadır;WP11 hazırlığı bunları başlatmaz.

## Planlanan çıktı ve onay sınırı

Kullanıcı WP11'i başlattığında,yol haritasındaki local/global kimya SHAP veonaylanan koşullu graf açıklamaları;model/çıktı/background provenansı;limit/istikrar testleri;çalıştırılmış Türkçe notebook,gerçek tablolar/görseller ve rapor beklenir. Bu turda yalnız bu hazırlık notu oluşturuldu. **WP11 uygulaması,yeni model veya yeni eğitim için yetki verilmiş sayılmaz;şimdi durulur.**
'''
    for name,text in [('WP10_FINAL_CLOSURE.md',report),('WP11_PREPARATION_DECISION.md',preparation)]:
        path=ROOT/'reports'/name
        if path.exists():raise RuntimeError('Yeni belge zaten var;ezilmez')
        path.write_text(text,encoding='utf-8')
    print('WP10 closure and roadmap-only WP11 preparation written')


if __name__=='__main__':main()
