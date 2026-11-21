"""WP09 kapanış ve WP10 kısa tasarım raporları; eski raporları değiştirmez."""
import json
import pandas as pd
from wp09_train import ROOT,QA
from wp09_closure import CLOSE


def table(frame):
    def fmt(x):
        if pd.isna(x):return 'NA'
        if isinstance(x,float):return f'{x:.8g}'
        return str(x).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def main():
    close=json.loads((CLOSE/'closure_checks.json').read_text(encoding='utf-8'))
    proof=pd.read_csv(CLOSE/'trained_forward_gradient.csv')
    reconstruction=pd.read_csv(CLOSE/'NPZ_score_reconstruction.csv')
    coverage=pd.read_csv(QA/'evaluation_coverage.csv');coverage=coverage[coverage.model.eq('G_realPPI')]
    report=f'''# WP09 — Kullanıcı onaylı sonuçların nihai kapanışı

06.11.2026. **WP09_CLOSED_ACCEPTED_BY_USER.** Kullanıcı protein-PPI GNN ve ablation sonuçlarını araştırma kapsamında kabul etti. Bu ek son denetimdir;önceki model,skor,seed,hiperparametre,eşik,split,PT sözlüğü veQC kararları değiştirilmedi. WP10 yalnız aşağıdaki ayrı tasarım/uygulanabilirlik çalışmasıdır;model eğitimi için izin yoktur.

## 1. Değişmeyen bilimsel sonuç

Ana paired54 drug-macro observed-record AP: **G_noPPI=0.643021; G_realPPI=0.642880; üç shuffled metriğinin eşit ortalaması=0.643259.** B0/B1/B2 sabit referanslardır. Real−noPPI −0.000142,koşullu%95 CI[−0.003611;+0.003248];real−shuffled_mean −0.000379,CI[−0.002039;+0.001310]. Bunlar eşdeğerlik testi veya genel üstünlük kanıtı değildir.

| Ayrı bilimsel soru | Hüküm | Kanıt / sınır |
| --- | --- | --- |
| PPI gerçekten hesaplanıp öğrenildi mi? | Teknik olarak gösterildi | Gerçek eğitimde optimizer/gradient/parametre güncellemesi;kayıtlı ağırlıkta kenar ve backward etkisi |
| Gerçek PPI bağlantıları ek birincil sıralama başarısı sağladı mı? | Bu deneyde gösterilemedi | Aynı mimari/kapsam real−noPPI ve real−shuffled farkları;koşulluCI sıfırı içeriyor |
| Protein biyolojisi genel olarak yararsız mı? | Bu sonuç çıkarılamaz | Küçük kohort,insan PPI erişimi,rol-mean,query self-only ve SIDER kayıt mekanizmasıyla sınırlı deney |

**B1–GNN farkı tek başına PPI topoloji etkisi değildir.** B1 beş kimya+maske LR,GNN ise protein/rol temsilleri ve farklı nonlineer kapasite/optimizasyon taşır. Aynı mimarideki PPI aç/kapat ve karıştırılmış-topoloji karşılaştırmaları topoloji sorusuna daha doğrudan yaklaşır. Stres B2 kazancı noPPI'da da görüldüğünden PPI'ye atfedilemez. Olası sınırlamalar neden olarak ayrıştırılmış veya kanıtlanmış değildir.

## 2. Son kapanış kontrolleri

| Kontrol | Sonuç |
| --- | --- |
| 190 NPZ +190 metadata SHA-256 | PASS;380 dosya frozen model manifestiyle aynı |
| Sayısal state hash'i | 190/190 NPZ'den dtype/shape/byte sırasıyla yeniden hesaplandı;metadata ve fit kaydıyla aynı |
| Önceki tüm proje artefaktları | {close['previous_artifacts_preserved']} dosya içerik hash'i aynı;eski test logu dahil |
| Gerçek trainer testleri yeniden | **24/24 PASS;{close['test_seconds']} saniye**;yeni log ayrı |
| NPZ→OOF skor yeniden üretimi | Primary outer1 bütün5 model;max mutlak fark{close['max_score_reconstruction_error']:.3g} |
| Drug/fold/PT karşılaştırma anahtarları | Bütün5 model ana/stres aynı;frozen baseline eşleşmesi trainer testinde geçti |
| Kayıtlı ağırlıkta forward/backward | 5 probe;PPI etkisi/gradient real ve3null'da>0,noPPI'da0;optimizer0,state aynı |
| Ek kapanış/tasarım testleri | 12/12 PASS;4.422 saniye |

Yeni log [trainer_tests_rerun.txt](qa/WP09/final_closure_v1/trainer_tests_rerun.txt),özgün `training_v1/test_results.txt` yerine geçmez ve onu ezmez. Yeniden çalıştırılan özgün testler kontrollü RAM tekrar-fit/mutasyon denemelerini içerir;üretim190 modeline yazmaz,hiperparametre aramaz. Kapanış probe'u yalnız kaydedilmiş modeli yükler ve train-only BCE.backward çağırır;optimizer kurulmaz. Ortam aynı kütüphanelerdir;farklı sürümlerde bit düzeyinde genel garanti yoktur.

{table(reconstruction)}

**Yorum:** Sıralama ve değerler floating-point/CSV toleransında yeniden üretildi. Bu yeni OOF tahmini kaydetme veya test sonucuyla seçim yapma değildir.

{table(proof[['model','same_weights_PPI_removed_protein_L2','trained_message_weight_gradient_norm','optimizer_steps_this_check','state_unchanged']])}

![Kayıtlı ağırlıkta PPI kanıtı](figures/WP09/final_closure_v1/01_trained_edge_gradient_check.png)

**Yorum:** G_realPPI'nin **aynı** kaydedilmiş ağırlıklarıyla komşuluğu kaldırmak protein temsillerindeL2=13.1622 fark yaratır. Train BCE message.weight gradient normu0.00401604. NoPPI'nin her ikisi0. Teknik kullanım/öğrenme kanıtı performans katkısı kanıtından ayrıdır;yalnız AdamW weight-decay kaynaklı ağırlık değişimi PPI kanıtı sayılmaz.

![Kabul edilmiş sonuçlar](figures/WP09/final_closure_v1/02_frozen_primary_result.png)

**Yorum:** Grafik önceki frozen metrikleri gösterir;yeniden model seçilmedi. CI sabitOOF ve yapısal grup bootstrap'ına koşulludur;bağımsız dış doğrulama veya full-retraining belirsizliği değildir. Önceki sonuçlar görüldüğü için kıyas keşifseldir.

## 3. Kapsam,abstention ve NA

{table(coverage[['protocol','scope','scored_drugs','scored_pairs','observed_positive_scored','unknown_NOT_verified_negative','out_of_scored_vocab_positive','class_AUROC_NA']])}

**1685**,primary paired54 ilaçlarındaki5505 kaynak pozitifin skorlanabilir sözlük/fit kapsamı dışında kalan kısmıdır;bütün62'nin veya1061 PT evreninin hata sayısı değildir. Primary paired54'te3820 gözlenen pozitif ve10144 unknown vardır. Her model/protokol61 ilaç skorlar;Methenamine girdisiz abstention olarak kalır. Tobramycin'in protein eksiği korunur. Envanter **62 ilaç/1061 kaynakPT/6416 pozitif** olarak aynıdır.

Üç başarısız null NA kaldı;primary_o02_i01 ve stress_o02_i02 ortak inner seçiminden bütün5 varyant için çıkarıldı:10 iş çalıştırılmadı. Seed/bütçe/değişim eşiği değiştirilmedi. 25 context/PT single-proxy oluşumu,sınıf metriği NA ve sözlük dışı pozitifler sıfır başarı/gerçek negatif sayılmadı. Shuffled özet üç ayrı modelin metrik ortalamasıdır;skor ensemble veya best-replica değildir.

**Unknown gerçek biyolojik negatif değildir.** Sigmoidler SIDER kaynak kayıtlarını sıralama skorudur;klinik yan etki olasılığı,özgüllük,kalibrasyon,nedensellik veya hasta güvenliği doğrulaması değildir. Mevcut encoder protein-PPI GNN+skaler kimyadır;atom–bağ GNN veya tam moleküler GiG değildir.

## 4. Dosyalar ve kapanış

- `reports/qa/WP09/final_closure_v1/`:önceki2347 dosyanın manifesti,yeni24 test logu,190state/metadata ve5outer skor/gradient/kapsam kanıtları. Önceki QA salt okunur kaldı.
- `notebooks/WP09_final_closure.ipynb`:5 çalıştırılmış kod hücresi;gerçek tablolar,2 PNG ve Türkçe yorumlar.
- `reports/figures/WP09/final_closure_v1/`:PPI teknik kanıtı ve frozenAP grafikleri.
- `tests/test_wp09_closure_wp10_design.py`:12 yeni kapanış/tasarım sözleşmesi testi.
- [WP10 tasarım önerisi](WP10_DESIGN_FEASIBILITY.md):aktif ROADMAP kapsamı içinde ayrı hazırlık;model/optimizer yok.

AGENTS,aktif ROADMAP/SOURCE_USAGE_AUDIT,WP09 tasarım/veri/karar/son eğitim kapısı,v3 config,karşılaştırma taslağı,eğitim raporu/model kartı ve ilgiliWP04/WP08 kaynak/QC belgeleri esas alındı. Eski belgelerdeki“onay bekliyor/eğitim yok” kayıtları tarihsel aşamalardır;silinmedi. **WP09 kullanıcı kabulüyle kapandı. WP10 yalnız tasarım önerisinde durur;uygulama/eğitim için yeni onay beklenir.**
'''
    q=ROOT/'reports/qa/WP10/design_v1';summary=json.loads((q/'feasibility_summary.json').read_text(encoding='utf-8'))
    review=pd.read_csv(q/'QC_review_eight_preserved.csv');budget=pd.read_csv(q/'parameter_budget_by_train_PT.csv')
    gate=pd.read_csv(q/'decision_gate.csv')
    design=f'''# WP10 — Kısa tasarım,uygulanabilirlik ve karar önerisi

06.11.2026. **DESIGN_FEASIBILITY_COMPLETE; AWAITING_USER_DESIGN_APPROVAL.** WP09 kullanıcı onayıyla kapatıldı. Bu aşamada moleküler model,PyG Data/eğitim tensörü,optimizer veya PT tahmini oluşturulmadı. Model eğitimi için yetki yoktur.

## 1. Yol haritasına uyum ve gerçek kaynak

Aktif `ROADMAP_V7.md` WP10'u **SMILES→atom/bond graf,RDKit→PyG Data,readout,küçük Molecular GNN,validasyon/scaffold ve kademeli karşılaştırma** olarak tanımlar;veri küçükse deney ertelenebilir. Yeni iş paketi icat edilmedi. Bu kullanıcı isteği yalnız tasarım/uygulanabilirlik kapısını açar.

Kaynak **WP04'te yerel DrugBank XML'den çıkarılmış SMILES**;PubChem CID köprüsü yerel kimlik bağıdır. Yol haritasındaki“mevcut PubChem SMILES” ifadesi,eldeki62 yapının canlı PubChem servisiyle bağımsız yapı doğrulaması yapıldığı anlamına gelmez. Bu kaynak farkı açık tutulur;yeniAPI/indirme yapılmadı. Aynı RDKit{summary['rdkit']} ve salt okunur küçükWP04 tabloları kullanıldı. Mevcut `.deps/pyg` **2.8.0** import edildi;varsayılan yolda görünmemesi yokluğu değildir,yeni kurulum yapılmadı. Başvurulan çevrimiçi PyG latest belgesi2.9.0'dır;ileride uygulama önce kurulu2.8.0 API'siyle test edilmelidir.

## 2. Uygulanabilirlik ve sekiz QC kararı

62/62 SMILES yeniden parse/sanitize edildi;tam kaynak InChIKey,CID köprüsü ve önceki atom/bağ sayıları aynı. **2061 atom/2219 bağ**,ilaç başına10–125 atom;teknik atom-graf dönüşümü62/62 mümkündür. Bellekte küçük adjacency denetimi yapıldı;PyG üretim nesnesi/tensörü yazılmadı.

**Öneri:atom dalı için54 bayraksız yapı;sekiz QC kaydı mevcut maskeli kimya/protein yollarıyla kalsın.** Bu yeni nihai uygunluk kararı değildir,onay bekler.62 envanter,eski61 girdi uygunluğu veMethenamine abstention değişmez. Atom dalı bu ilk öneride ilaç sayısını artırdığını iddia etmez.

{table(review[['id','name','review_flags','atoms','components']])}

Gentamicin üç organik bileşenin kaynak temsilidir;en büyük fragment veya tahmini karışım oranı seçilmez. Belirtilmemiş atom/çiftbağ stereo tamamlanmaz,rasemat varsayılmaz. Methenamine'in yeni/eski stereo algılayıcı farkı gerçek kayıp stereomer/yapı hatası sayılmaz. Hiçbir atom/bağ silinmez,nötralizasyon/tautomer/ana-fragment dönüşümü yapılmaz.54 kabul edilse bile kaynak kimliği “biyolojik doğruluk tamamen kanıtlandı” anlamına gelmez.

![QC ve boyutlar](figures/WP10/design_v1/01_QC_and_graph_sizes.png)

**Yorum:**62 teknik parse ile54 QC uygunluğu farklıdır. Büyük molekül daha fazla bağımsız eğitim ilacı sağlamaz;kimyasal bileşenler yeni ilaç diye çoğaltılmaz. İzotop belirtilmiş atom ve radikal sayısı bu62'de0'dır;gelecekte böyle bir kayıt ayrı QC gerektirir.

## 3. Önerilen atom/bağ veri sözleşmesi

| Bölüm | Sabit öneri | Koruma |
| --- | --- | --- |
| Atom x | 44 boyut:element10,total_degree8,charge6,totalH6,hybrid6,aromatic1,ring1,CIP5,isotope_flag1 | Kategoriler config'te sabit;OTHER;testten sözlük/normalizasyon öğrenme yok |
| Bağ edge_attr | 14 boyut:bond_type5,stereo7,conjugated1,ring1 | Her kovalent bağ iki yön;sütun/özellik hizası test edilir |
| PyG sınırı | x float32[N,44];edge_index int64[2,2B];edge_attr float32[2B,14];num_nodes=N | Self-loop/cross-molecule edge yok;izole atom sayısı explicit |
| Stereo | CIP R/S,UNASSIGNED_POTENTIAL,NONE,OTHER;bond stereo none/any/Z/E/cis/trans/OTHER | Ham chiralTag,stereo atomları,bond direction metadata korunur;çıkarılamayan stereo tahmin edilmez |
| Kimlik / hedef | drugID,CID,kaynakSMILES/hash ayrı metadata;y yok | ID,PT sayısı,sıklık,kalite_skoru,ATC veetiket girdi değildir |
| Batched readout | Her ilaç kendi atom altgrafı;batch sınırları explicit | Query molekülü train protein/cache'ini veya diğer ilaçları değiştiremez |

Ardışık atom indeksleri veya ham @/@@ yönleri doğrudan invariant sayısal özellik değildir;atom renumbering sonrası stereo/CIP ve readout tutarlılığı test edilmelidir. Aromatik atom ve aromatik bağ ayrı alanlardır. [RDKit Book](https://www.rdkit.org/docs/RDKit_Book.html). PyG'nin x/edge_index/edge_attr şekilleri veexplicit num_nodes yaklaşımı önerinin temelidir. [PyG Data](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.data.Data.html).

![Öğretici gerçek atom komşuluğu](figures/WP10/design_v1/02_Linezolid_atom_graph_preview.png)

**Yorum:**Linezolid'in gerçek kovalent komşuluğu çizilir;bu çizim bond-order/stereo'nun tamamını görsel olarak kodlamaz. Bunlar sözleşmede edge_attr/metadatadır.2D çizim koordinatları girdi değildir;3D konformer veya moleküler mesaj geçişi henüz çalıştırılmadı.

## 4. Küçük mimari,füzyon ve kapasite

Önerilen tek katman: `h0=ReLU(P_atom x)`;`h1=h0+ReLU(S h0+mean_j ReLU(U h0_j+V e_ji))`;hidden16,boş komşuluk mean0. Bütün atomların mean readout'u→Linear16→8/ReLU→atom maskesi. Mean readout bir PyG seçeneğidir;sum/count duyarlılığı ayrıca onay olmadan eklenmez. [global_mean_pool](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.pool.global_mean_pool.html). Bağ koşullu mesaj gereklidir;büyük edge-conditionedNNConv alternatif olup uygulanmadı. [NNConv](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.NNConv.html).

İlk öneri **geç füzyon**:mevcut56→32 protein-PPI/4rol+5→8 kimya temsil141'e masked atom8+atom_mask1 ekle→150→trainPT başlığı. Daha karmaşık drug-node/üst-graf mesaj geçişi ek kapasite ve yeni sızıntı testleri gerektirir;şimdilik önerilmez. Atom-only dal daha ucuz keşif alternatifidir;aynı multimodal factorial sorusunun yerine geçmez.

Yeni molekül dalı cebirsel **1592 parametre**;başlığa9K eklenir,toplam **5512+151K**. Mevcut inner/outer K158–326 için **{int(budget.proposed_total.min())}–{int(budget.proposed_total.max())}** parametre;WP09 sayımı26356–50212. Bunlar model kurulmadan denklemlerden hesaplandı. Train ilaçları az,PT'ler bağımlı ve unknown;başlık baskın kapasitedir. Bir katman sadece yerel çevreyi taşır,3D stereo etkileşim veya biyolojik mekanizma çözümü iddia edilmez.

![Önerilen kapasite](figures/WP10/design_v1/03_proposed_parameter_budget.png)

**Yorum:**1592 parametrelik ek dal bile head boyutu ve küçük kohort nedeniyle risksiz değildir. Sonuçları iyileştirmek için genişlik/katman/seed araması önerilmedi. İleride yeterli örnek/inner destek/kararlı gerçek encoder testi sağlanmazsa ROADMAP gereği eğitim ertelenebilir;başarı vaat edilmez.

## 5. Kontrollü karşılaştırma ve değişmeyecek protokol

Birincil öneri aynı genişletilmiş mimaride **A0P0/A0P1/A1P0/A1P1**:atom mesaj dalı var/yok × PPI komşu mesajı var/yok. A0'da atom blok/maske kapalı,P0'da PPI edge_index boş;diğer girdiler/uygunluk vehead şekli aynı. Her contextte aynı başlangıç/seed veortak geçerli inner kapsamı gerekir. Atom katkısı sabitP durumunda,PPI katkısı sabitA durumunda;etkileşim farkların farkıyla keşifsel incelenebilir.

**EskiWP09 A0 modeli yeni mimarinin kontrollüA0 hücresi yerine geçirilmez:**başlık/kapasite farklıdır. Yeni deney izin alırsa dört hücre birlikte aynı init ilekurulur;eskiWP09,B0/B1/B2 modelleri veOOF skorları değişmez tarihsel referans olarak kalır. R0/R1/R2 eklenmesi ayrı kapsam kararıdır;eklenirse mevcut null hash/seed/v3 NA politikası veüç metrik eşit ortalaması korunur,en iyi tekrar/score ensemble yoktur.

Eski connectivity dış5/iç3 ve ayrı scaffold OR≥0,8 stres üyelik/hash'leri,seed20261106,train-only scaler/PT/fittable sözlükleri ve paired54/own61 anahtarları korunur. Levofloxacin/Ofloxacin ayrılmaz. Yeni atom girdileri label-free statik kaynak olup train kaynaklarını genişletmez;unknown gerçek negatif ilan edilmez. Öğrenilen işlemler yalnız train'de fit edilir;outer test mimari,epoch veya seçime girmez. Önerilen gelecekteki optimizer/early-stop öncekiWP09 politikasının aynısıdır;bugün çalıştırılmadı.

## 6. Uygulamadan önce zorunlu test planı ve karar kapısı

Gelecek uygulamada:atom/bondID ve iki-yön edge_attr hizası;parsing/QC/fragment korunumu;OTHER ve bilinmeyen stereo;atom permütasyonu/readout değişmezliği;ayırt edici gerçek/sentetik örnekte bağ kaldırma/bağ tipinin forward etkisi vegradient;atom kapalı/PPI kapalı davranışı;izole atom;batch izolasyonu;heldout etiket/değer mutasyonu;query→protein cache izolasyonu;train-only fit/target veparametre sayısı testleri zorunludur. **Bu encoder henüz yazılmadığı için bu gelecekteki testler geçmiş sayılmaz.** Mevcut12 kapanış/tasarım testi kaynak/QC/cebirsel sözleşmeyi doğrular.

{table(gate)}

Girdi/karar sözleşmesi `configs/WP10_design_PROPOSED_v1.json` içinde **training_enabled=False/model_implemented=False** olarak açık kalır. `notebooks/WP10_design_feasibility.ipynb` beş çalıştırılmış hücreyle62 tabloyu,8 bayrağı,gerçek Linezolid grafını,özellik/kapasite veonay seçeneklerini gösterir. `reports/qa/WP10/design_v1/` kaynak hash'lerini,tüm62 yapı auditini,alan dağılımlarını vekarar tablosunu taşır. **Tam moleküler GiG tamamlanmış değildir;bu tasarım uygulanıp gerçek forward/gradient veablation doğrulanmadan bu ad kullanılmaz. Tasarım önerisinde duruldu;uygulama veözellikle eğitim için kullanıcı onayı bekleniyor.**
'''
    for name,text in [('WP09_FINAL_CLOSURE.md',report),('WP10_DESIGN_FEASIBILITY.md',design)]:
        path=ROOT/'reports'/name
        if path.exists():raise RuntimeError('Önceki rapor ezilmez: '+name)
        path.write_text(text,encoding='utf-8')
    print('WP09 kapanış ve WP10 tasarım raporları yazıldı')


if __name__=='__main__':main()
