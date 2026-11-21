"""Gerçek WP10 teknik kanıtlarından Türkçe rapor ve ayrı eğitim kapısı."""
import json,re
import pandas as pd
from wp10_molecular_graph import ROOT,QA
from wp09_close_wp10_reports import table


def main():
    if (QA/'artifact_validation.json').exists():raise RuntimeError('Encoder v1 finalized; do not overwrite reports')
    audit=json.loads((QA/'technical_audit_complete.json').read_text(encoding='utf-8'))
    data=pd.read_csv(QA/'molecular_graph_QA_all62.csv')
    real=pd.read_csv(QA/'real_molecular_forward_gradient.csv')
    switches=pd.read_csv(QA/'integration_forward_40contexts_4variants.csv')
    first=switches[switches.context.eq('primary_o01_final')]
    log=(QA/'test_results_context_guard.txt').read_text(encoding='utf-8-sig');tests=re.search(r'Ran ([0-9]+) tests in ([0-9.]+)s',log)
    assert tests and log.rstrip().endswith('OK')
    report=f"""# WP10 — Moleküler graf ve encoder uygulaması

06.11.2026. **Teknik doğrulama tamamlandı. Gerçek dört kollu eğitim için ayrı kullanıcı onayı bekleniyor.** Bu aşamada optimizer çalıştırılmadı, gerçek PT kaybı veya outer PT skoru hesaplanmadı. WP11'e geçilmedi.

## 1. Uygulanan yapı

- **62 gerçek PyG Data**, 54 açık atom maskesi ve 8 QC bekletmesi doğrulandı. Envanterden ilaç silinmedi.
- Atom özellikleri44, bağ özellikleri14, hidden16, tek bond-aware residual mean katmanı, molekül başına mean readout ve8 boyutlu temsil uygulandı.
- Mevcut WP09 protein/kimya temsili141'e maskeli molekül8 ve atom maskesi1 eklenerek150 boyutlu füzyon kuruldu. A0P0/A0P1/A1P0/A1P1 aynı mimarinin anahtarlarıdır.
- **28/28 test geçti; {tests.group(2)} saniye.** Ayrıca40 frozen bağlamda dört varyant için160 etiketsiz train/query forward denetimi yapıldı. Gerçek veride PT başlığı kurulmadı.

## 2. Gerçek kaynak ve QC

WP04'te DrugBank XML'den çıkarılmış ChemAxon SMILES, CID köprüsü ve tam InChIKey kullanıldı. DrugBank version5.1/export2026-01-04; RDKit2026.09.1, PyG2.8.0 ve torch2.13.0 mevcut ortamda doğrulandı. Yeni biyolojik kaynak, API çağrısı veya paket kurulumu yoktur. Canlı PubChem yapısı bağımsız olarak yeniden doğrulandı denmiyor.

62 kaydın kimliği, atom/bağ/bileşen sayısı önceki WP04 ile aynı: **{int(data.atoms.sum())} atom, {int(data.bonds.sum())} bağ, {int(data.directed_edges.sum())} yönlü kenar**. Her Data için PyG validate ve ek şema/yön testleri geçti. Kaynak atomları, bağları ve fragmentleri korunur; stereo tamamlama, nötralizasyon veya tautomer düzenleme yapılmaz.

{table(data[~data.atom_eligible][['id','name','atoms','bonds','components','review_flags']])}

Gentamicin'in105 atomı ve3 bileşeni korunur; en büyük fragment seçilmez. Methenamine'in algoritma farkı bayrağı ve girdisiz eligible=False durumu aynı kalır. Tobramycin protein özelliği olmadan kimya ve uygun atom yolunda kalabilir. Sekiz QC kaydı atom dalında maskelenir; mevcut protein/kimya yolları korunur. Teknik parse başarısı tam biyolojik doğruluk kanıtı değildir.

![Gerçek graf kapsamı](figures/WP10/encoder_v1/01_real_PyG_QC_scope.png)

**Yorum:**62 teknik graf ve54 açık atom dalı farklı kapsam ölçüleridir. Sekiz kayıt yanlış yapı ilan edilmedi; inceleme gerekçeleri korundu.

## 3. Özellik sözleşmesi

| Bölüm | Kodlama |
| --- | --- |
| Atom44 | Element10, total degree8, formal charge6, total H6, hybridization6, aromatic1, ring1, CIP5, isotope flag1 |
| Bağ14 | Bond type5, stereo7, conjugated1, ring1 |
| PyG Data | x float32[N,44]; edge_index int64[2,2B]; edge_attr float32[2B,14]; explicit num_nodes=N |
| Ayrı metadata | DrugBank ID, CID, kaynak SMILES/hash, QC, ham chiralTag/BondStereo/BondDir ve stereo referans atomları |

Kategoriler sabittir; OTHER desteklenir. ID, PT, raporlama sıklığı ve kalite_skoru özellik değildir. Data.y veya ek kimlik/etiket alanı reddedilir. Total degree ve total H, RDKit GetTotalDegree/GetTotalNumHs tanımlarıdır; yük, H ve aromatiklik ayrı ayrı test edildi.

Belirtilmemiş potansiyel atom stereosu UNASSIGNED_POTENTIAL olarak kodlanır. Belirtilmemiş potansiyel çift bağ feature token'ı STEREOANY'dır; ham BondStereo aynen metadata'da kalır. Bu, R/S veya E/Z tahmini değildir. Gerçek2061 atomda1743 NONE,187 R,120 S ve11 unassigned;2219 bağda2205 NONE,12 Z,1 E ve1 ANY vardır. İzotop/radikal örnekleri yalnız sentetik testtir, kohorta eklenmedi.

Her kovalent bağ iki mesaj yönüne açılır. Invariant bağ özellikleri iki yönde aynı ve hizalıdır; ham UP/DOWN işareti ters mesaja körlemesine taşınmaz. Atom indeksleri yalnız referanstır.

![Gerçek moleküller](figures/WP10/encoder_v1/02_real_molecules_indexed.png)

**Yorum:**Linezolid, Ciprofloxacin ve Amoxicillin kaynak yapıları atom indeksleriyle gösterilir.2D koordinatlar model girdisi değildir; bu bir klinik karşılaştırma değildir.

![Linezolid mesaj yönleri](figures/WP10/encoder_v1/03_Linezolid_two_direction_edges.png)

**Yorum:**Linezolid24 atom/26 bağ/52 yönlü kenardır. Oklar mesaj yönüdür, nedensellik yönü değildir. Çizgi biçimi burada bağ derecesini kodlamaz; bu bilgi edge_attr içindedir.

## 4. Forward ve gradient kanıtları

`h0=ReLU(Px)`; `m_ji=ReLU(U h0_j+V e_ji)`; `h1=h0+ReLU(S h0+mean_j m_ji)`; `mol=ReLU(Linear16→8(mean_i h1_i))`. Boş komşuluk ortalaması0'dır. Tek katman1-hop mesaj taşır;3D etkileşim veya uzun menzilli mekanizma çözümü iddia edilmez.

Kontrollü CCO örneğinde h0=[1,1,2], h1=[3.25,3.625,4.75], readout3.875. Bağ kaldırma3.166667, bond-type perturbasyonu4.875 verir. Atom-message türevi7/6, bağ-message türevi1; analitik beklenti1e-12 toleransında doğrulandı. Bunlar elle belirlenmiş kanıt ağırlıklarıdır; optimizer yoktur.

![Analitik kanıt](figures/WP10/encoder_v1/04_synthetic_forward_gradient.png)

**Yorum:**Komşuluk ve bağ özelliğinin forward içinde gerçekten kullanıldığı gösterilir. Gradient hesabı parametre güncellemesi veya öğrenme değildir.

{table(real[['id','name','edge_removed_output_L2','bond_type_perturbed_output_L2','atom_message_gradient_norm','bond_message_gradient_norm','optimizer_steps']])}

![Gerçek molekül kanıtları](figures/WP10/encoder_v1/05_real_forward_gradient.png)

**Yorum:**Üç gerçek molekülde kenar/bond-type değişimi çıktıyı etkiler; atom ve bağ mesaj parametrelerine gradient ulaşır. Bunlar feature düzeyinde yazılım probe'larıdır; kimyasal olarak geçerli alternatif ilaç veya biyolojik açıklama değildir. Ağırlıklar değişmedi.

62 kaynak molekülün atomları yeniden sıralanıp özellikleri yeniden çıkarıldı. Float64 readout farkı en fazla **{audit['maximum_permutation_error']:.3g}**, önceden belirlenen tolerans1e-12 altındadır. Batch'e başka molekül eklemek ilgili readout'u değiştirmez.

## 5. Entegrasyon ve izolasyon

WP09 RoleMaskedPPI kodu ve sabit modelleri değişmedi. Yeni iskelet başlangıçtan kurulur; eski ağırlıklardan warm-start yapılmaz. A0'da molekül8+maske1 bloğu0; P0'da protein komşu mesajı0, self yolu korunur. Gerçek veri forward'unda head=None olduğundan PT skoru yoktur.

{table(first[['variant','train_drugs','query_drugs','train_active_atom_mask','query_active_atom_mask','train_PPI_neighbor_input_norm']])}

![Dört anahtar](figures/WP10/encoder_v1/06_four_variant_switches.png)

**Yorum:**Primary outer1'de49 train/13 query aynı kalır; A1'de43/11 atom maskesi açıktır. Komşu girdi normu bir teknik büyüklüktür, performans değildir.160 forward denetimi bütün frozen bağlamları kapsar; daha önce null nedeniyle çıkarılan iki inner bağlamı gelecek eğitim kapsamına geri almaz.

load_context/validate_context_bundles frozen train/validation/test üyeliklerini kontrol eder. Generic encoder kendisi fold seçmez; gerçek kullanımda doğrulanmış context API'si gerekir. Yanlış molekül sırası, heldout/PT enjeksiyonu ve QC maskesi açma girişimi reddedilir. Protein cache'i graph/model hash'ine bağlıdır. Bir query'nin değişmesi başka query'yi, train cache'ini veya model durumunu değiştirmez.

Gerçek PT deposu okunmadı. Gelecekteki trainer için train-only PT loss, scaler, inner seçim ve heldout mutasyon testleri ayrıca gerekir; bugünkü encoder testi henüz yazılmamış trainer'ı doğrulamış sayılmaz.

## 7. Kapasite ve tekrar üretim

Molekül dalı **1592**, başlıksız protein/kimya+molekül toplamı **5512** parametredir. Opsiyonel sentetik K başlığı ile5512+151K sayımı test edildi; K=3/158/326 yalnız şekil sayımıdır. Küçük ilaç sayısı ve bağımlı PT'ler nedeniyle aşırı öğrenme riski sürer.

Seed20261106 ve context formülü korunur. Dört anahtar aynı context başlangıcını paylaşır. UNTRAINED_initial_state.npz/json yalnız başlıksız başlangıç durumudur; eğitilmiş yan etki modeli değildir. State hash: `{audit['initialization_state_sha256']}`. Graph NPZ'leri allow_pickle=False ile gerçek Data'ya yeniden kurulur; tensor dtype/shape/byte hash'i tekrar üretim için, dosya hash'i provenans için kullanılır. Sürümler arası genel bit düzeyi garanti yoktur.

## 8. Testler ve çıktılar

**28/28 test, {tests.group(2)} saniye**; nihai log test_results_context_guard.txt. Önceki geliştirme logları korunur; başarısız test turu yoktur. Negatif şekil ve context enjeksiyon kontrolleri eklenince testler tekrar çalıştırıldı. Sentetik kimyadan sonra gerçek WP04 molekülleri kullanıldı.

**2384 önceki artefakt** aynı hash ile korundu. WP09/B0/B1/B2 modelleri, skorlar, splitler, hedefler, seed ve bütün QC kararları değişmedi. Run_status'a yalnız güncel durum eklendi.

| Çıktı | İşlev |
| --- | --- |
| scripts/wp10_molecular_graph.py | Sabit şema, gerçek Data, registry, güvenli cache ve yeniden kurulum |
| scripts/wp10_molecular_encoder.py | Bond-aware katman, readout, dört anahtar, füzyon ve cache/context sınırı |
| reports/qa/WP10/encoder_v1/ |62 graph NPZ, kaynak/stereo registry, tüm62 QA, permutation/gradient,160 forward ve hash kayıtları |
| configs/WP10_encoder_IMPLEMENTED_v1.json | Uygulama kaydı; training_enabled=False; tarihsel öneri değişmedi |
| notebooks/WP10_molecular_encoder.ipynb |9 çalıştırılmış kod hücresi, gerçek tablolar,6 açıklamalı PNG |
| tests/test_wp10_encoder.py |28 teknik test; optimizer veya PT eğitimi yok |
| docs/plan/WP10_MOLECULAR_DATA_CONTRACT_v1.md | Data, metadata, maske ve entegrasyon sınırı |
| reports/WP10_ENCODER_TRAINING_GATE.md | Gerçek dört kollu eğitim için ayrı onay kapısı |

Salt okunur tekrar kontrolü: `python -m unittest discover -s tests -p test_wp10_encoder.py -v`; eski logu ezmeden yeni dosyaya yaz. Tamamlanmış encoder v1 artefaktlarının üstüne yazılması engellenir.

**Teknik encoder doğrulamasında duruldu.** Atom/PPI performansı ölçülmedi; tam moleküler GiG araştırması tamamlandı denmez. WP09'un ek PPI katkısı gösterilemediği sonucu aynıdır. Unknown gerçek biyolojik negatif değildir; klinik risk, nedensellik veya hasta güvenliği iddiası yoktur. Gerçek dört kollu eğitim için kullanıcı onayı bekleniyor.
"""
    contract="""# WP10 moleküler veri sözleşmesi v1

Durum: teknik encoder uygulandı; gerçek PT eğitimi için yetki yoktur. Eski WP09 sözleşmesi korunur.

- Kaynak WP04 structure_sources/structure_validation:62 primary ID ve aynı CID/InChIKey;54 atom maskesi açık,8 inceleme kapalıdır.
- Data yalnız x float32[N,44], edge_index int64[2,2B], edge_attr float32[2B,14] ve explicit num_nodes taşır. y/ID/ek alan reddedilir. Kaynak ve QC bilgisi ayrı registry'dedir.
- Sabit kategoriler feature_schema.json içindedir. H sayısı/yük/aromatiklik/stereo ayrıdır. Atom indeksi özellik değildir. Belirtilmemiş potansiyel atom stereo ayrı token; belirtilmemiş potansiyel çift bağ ANY olarak kodlanır. Ham kaynak stereo ve direction metadata korunur; R/S/E/Z tamamlanmaz.
- Her kovalent bağ iki yönlüdür; invariant edge_attr iki yönde aynı ve hizalıdır. Self-loop, duplicate ve moleküller arası kenar yasaktır. İzole atomlar num_nodes ile korunur.
- Sayısal NPZ allow_pickle=False ile Data'ya yeniden kurulur. Dosya ve kanonik tensor hash'leri kontrol edilir. Bütün62 için kaynak cache'i tutmak bütün62'yi eğitim grafına eklemek değildir.
- load_context/validate_context_bundles frozen train/query üyeliklerini doğrular. Generic encoder fold seçmez; context kontrolü giriş katmanında zorunludur. Ordered MolecularInput.ids yalnız join içindir.
- QC maskesi WP04 sabit54 listesiyle kontrol edilir. A0 etkin atom maskesi0; A1 bu54 maskeyi kullanır. Frozen61 uygunluğu ve Methenamine eligible=False değişmez.
- Encoder44→16, tek bond-aware residual mean, global mean→8;1592 parametre. WP09 base141+masked8+mask1=150; başlıksız toplam5512. Gerçek veride head=None.
- A0P0/A0P1/A1P0/A1P1 aynı mimari ve context başlangıcını kullanır. P0 boş protein komşuluğu; P1 strict insan700. Context80 ve koşullu E.coli PPI eklenmez.
- ProteinCache train protein temsili, graph/model digest ve variant taşır. Query cache'e geri mesaj vermez; yeni query proteini eski self-only yolundadır. PT etiketi bu ABI'ya giremez.
- Seed20261106/context formülü, CPU1 thread; float64 permutation toleransı1e-12. İleride gerçek trainer için ayrıca kullanıcı onayı ve train-only PT/heldout/selection testleri gerekir.
"""
    gate="""# WP10 encoder sonrası gerçek eğitim kapısı

**Teknik uygulama tamamlandı. Gerçek dört kollu PT eğitimi henüz yetkili değildir.** Bu turdaki kullanıcı onayı graf, encoder, iskelet ve teknik testleri kapsar.

| Konu | Durum / sonraki adım |
| --- | --- |
|62 Data,54/8 QC,44/14,16→8,150 füzyon |28 test ve160 etiketsiz forward ile doğrulandı |
| WP09/B0/B1/B2 | Sabit referans; yeniden eğitim veya ayar yapılmaz |
| A0P0/A0P1/A1P0/A1P1 | Anahtarlar hazır; gerçek PT eğitimi için açık kullanıcı onayı gerekiyor |
| Split ve hedef | Aynı frozen train-only sözlük/fittable maske, connectivity5/3 ve ayrı stres, paired54/own61 korunacak |
| Önerilen eğitim | Önceki seed20261106/context init; AdamW lr.001/wd.001, max200/patience20/min_delta.0001, ortak inner best-epoch medyanı. Bu turda optimizer0 |
| Aynı mimari kontrolü | Yeni dört kol aynı150 boyutlu mimariden başlamalı; eski141 boyutlu WP09 yeni A0 hücresi yerine geçmez |
| Null kapsamı | R0/R1/R2 moleküler deneyleri bu turda yapılmadı. Gelecekte dahil edilmesi ayrı kapsam kararıdır; dahilse eski v3 seed/NA/ortak-inner/min2 ve metrik ortalaması korunur |
| Common inner | Tasarımın kilitli kesişimi korunacak; teknik40 context denetimi önceden dışlanan iki inner'ı eğitime geri almaz |
| Trainer testleri | Gerçek trainer üzerinde train-only PT loss/seçim/scaler, heldout label/value mutation ve query izolasyonu tekrar zorunlu |
| Bilimsel iddia | Atom/PPI ek performansı ölçülmedi; observed-record proxy, unknown gerçek negatif değil; klinik risk veya tam GiG başarısı iddiası yok |

Onay verilirse önce gerçek eğitim sözleşmesi ayrı çalışma kaydıyla dondurulur; sonra trainer ve sızıntı testleri uygulanabilir. **Şimdi durulur; gerçek eğitim veya WP11 başlatılmaz.**
"""
    paths={'reports/WP10.md':report,'docs/plan/WP10_MOLECULAR_DATA_CONTRACT_v1.md':contract,'reports/WP10_ENCODER_TRAINING_GATE.md':gate}
    for filename,text in paths.items():
        path=ROOT/filename
        if path.exists() and '--refresh-working-draft' not in __import__('sys').argv:raise RuntimeError('Belge zaten var: '+filename)
        path.write_text(text,encoding='utf-8')
    print('WP10 Türkçe uygulama raporu,Data sözleşmesi veayrıeğitimkapısı hazır')


if __name__=='__main__':main()
