"""Post-lock reporting only. No prediction, reference, model load, attribution or API calls."""
from pathlib import Path
import json,platform,sys
import numpy as np,pandas as pd,scipy
from wp12_api_security import public_sha
from wp09_close_wp10_notebooks import execute,INIT
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/tedizolid_B1_external_v1';F=ROOT/'reports/figures/WP13/tedizolid_B1_external_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,data):
 with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 F.mkdir(parents=True,exist_ok=False)
 lock=read(Q/'prediction_lock.json');lockhash=public_sha(Q/'prediction_lock.json');assert lockhash==read(Q/'prediction_lock_sha256.json')['prediction_lock_sha256']
 for collection in [lock['outputs_sha256'],lock['input_and_models_sha256']]:
  for p,h in collection.items():assert public_sha(ROOT/p)==h,p
 before_lock_hash=lockhash
 frames=[pd.read_csv(Q/f'fold{i}_scores.csv',float_precision='round_trip') for i in range(1,6)]
 common=pd.read_csv(Q/'common201_scores.csv',float_precision='round_trip');coverage=[]
 for i,f in enumerate(frames,1):coverage.append({'fold':i,'valid_PT':len(f),'common_PT':len(common),'outside_common_PT':len(f)-len(common),'query':'DB14569','scope':'primary B1; NOT OOF; external label-isolated exploratory'})
 pd.DataFrame(coverage).to_csv(Q/'coverage_summary.csv',index=False,encoding='utf-8-sig')
 write(Q/'runtime_record_post_execution.json',{'record_timing':'post-lock environment record; not a new inference','python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'platform':platform.system(),'repeat_limit':'only numerical portability tolerances; no inference repeated here'})
 (Q/'prediction_lock.sha256').write_text(lockhash+'  prediction_lock.json\n',encoding='ascii')
 write(Q/'SHAP_feasibility_DEFERRED.json',{'status':'DEFERRED_NOT_RUN','method_reference':'docs/plan/WP11_B1_SHAP_CONTRACT_v1.md','eligible_future_method':'exact interventional linear SHAP per frozen B1 logit','background':'all and only each model train_drug_ids, equal weights; frozen standardized feature rows','required_artifacts':['model JSON/NPZ hashes','frozen per-context features NPZ','train_drug_ids and feature schema','current external input and model-specific transformed vectors','prediction_lock binding'],'formula':'phi_i=w_i*(x_i-mean_train_i);base=b+w*mean_train;z=base+sum(phi)','no_refit':True,'no_reference_or_outcome_selection':True,'ensemble_limit':'201 summary averages sigmoid scores. Averaged per-model logit SHAP is NOT a SHAP explanation of that nonlinear score-average output; requires separate approved output-scale/method contract if desired.','reason_for_deferral':'User prioritizes immutable prediction_lock; no new attribution calculated in this first external run.'})
 execute('WP13_Tedizolid_B1_external_v1.ipynb',[
 ('md','''# WP13 — Gerçek DB14569 B1 dış tahmini v1

**EXPLORATORY_EXTERNAL_LABEL_ISOLATED**. Önceki STRICT_ANALYST_BLINDNESS_COMPROMISED sınırlaması korunur. Bu defter yalnız hash ile kilitlenmiş çıktıları okur; model forward/fit, yeni SHAP, API veya referans belgesi erişimi yoktur. Skorlar SIDER observed-record proxy; klinik olasılık/sıklık/kalibrasyon değildir. Unknown çiftler biyolojik negatif değildir.'''),
 ('code',INIT+r'''
Q=ROOT/'reports/qa/WP13/tedizolid_B1_external_v1';F=ROOT/'reports/figures/WP13/tedizolid_B1_external_v1'
lock=json.loads((Q/'prediction_lock.json').read_text(encoding='utf-8'));pre=json.loads((Q/'precommit_manifest.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{k:lock[k] for k in ['experiment_status','drug_id','query_count','forward_calls','common_targets','DB09042','stress','A1P1','SHAP','reference_access']}]).T)
display(pd.read_csv(Q/'coverage_summary.csv'))
display(pd.read_json(Q/'active_input.json',typ='series').to_frame('onaylı_girdi'))
'''),
 ('md','''**Yorum:** Tek dış aktif-molekül query, önceden seçilmiş beş primary model. Ön ilaç/stress/GNN NOT_RUN. Beş modelin tüm geçerli1294 skor kaydı korunur; farklı başlıklar sıfırla doldurulmaz. Bu drug-disjoint OOF değil, yeni ve etiketten yalıtılmış dış araştırma query'sidir.'''),
 ('code',r'''
common=pd.read_csv(Q/'common201_scores.csv',float_precision='round_trip')
display(common.head(15))
fig,ax=plt.subplots(figsize=(10,5));top=common.head(12).iloc[::-1];ax.barh(top.class_id,top.record_ranking_score,color='#277b8e');ax.set(xlabel='Eşit ağırlıklı kayıt sıralama skoru; klinik risk değil',ylabel='Frozen PT CUI',title='DB14569 · Ortak201 hedef sıralamasının ilk12 kaydı',xlim=(0,1));plt.tight_layout();plt.savefig(F/'01_common201_record_ranking.png',dpi=170);plt.show()
'''),
 ('md','''**Yorum:** Aritmetik ortalama beş SIGMOID skorundadır; logit ortalaması değildir. Grafik yalnız yeni dosyanın sıralamasını gösterir; başarı, görülme sıklığı veya klinik risk sonucu çıkarılmaz. PT adlandırmak için bu tur dış referans veya prospektüs açılmadı; hedefler modelin sabit CUI'leridir.'''),
 ('code',r'''
fig,axs=plt.subplots(1,5,figsize=(18,5),sharex=True)
for i,ax in enumerate(axs,1):
    f=pd.read_csv(Q/f'fold{i}_scores.csv');display(f[['rank','class_id','record_ranking_score','logit']].head(8))
    t=f.head(8).iloc[::-1];ax.barh(t.class_id,t.record_ranking_score,color='#6497a1');ax.set(title=f'Primary B1 model {i}\n{len(f)} geçerli PT',xlim=(0,1),xlabel='Kayıt sıralama skoru')
plt.tight_layout();plt.savefig(F/'02_five_individual_rankings.png',dpi=160);plt.show()
'''),
 ('md','''**Yorum:** Bireysel modeller kendi native hedef uzayındadır. Farklı başlıklar nedeniyle bu paneller farklı sayıda hedef taşır; ortalama yalnız ortak201'de yapılır. Model/fold seçiminde bu sonuçlar kullanılmadı.'''),
 ('code',r'''
cols=[f'fold{i}_score' for i in range(1,6)]
t=common.head(10).iloc[::-1]
fig,ax=plt.subplots(figsize=(10,5))
for i,c in enumerate(cols,1):ax.scatter(t[c],t.class_id,label=f'B1 model{i}',s=35)
ax.set(xlabel='Kayıt sıralama skoru',ylabel='Ortak PT CUI',title='İlk10 ortak hedefte beş kayıtlı modelin skorları',xlim=(0,1));ax.legend();plt.tight_layout();plt.savefig(F/'03_common_target_model_spread.png',dpi=170);plt.show()
display(pd.read_json(Q/'numerical_checks.json'))
'''),
 ('md','''**Yorum:** Nokta yayılımı farklı donmuş train modellerinin aynı hedefe verdiği skorları gösterir; güven aralığı, bağımsız tekrar veya klinik belirsizlik ölçüsü değildir. Yeni SHAP DEFERRED_NOT_RUN; eski WP11 background/logit sözleşmesine uygun ayrı hesaplama ileride yapılabilir. Skor-ortalama ensemble'ı tek doğrusal logit modeli değildir; ortalama logit-SHAP doğrudan ensemble açıklaması yapılamaz. Prediction_lock sonrası da referans açılmadı. Bu aşama STOP; PDF karşılaştırması ayrı kullanıcı aşamasıdır.''')])
 report=f'''# WP13 — DB14569 gerçek B1 dış tahmini ve prediction lock v1

Durum: **PREDICTIONS_LOCKED_STOP_BEFORE_REFERENCE**. Deney: **EXPLORATORY_EXTERNAL_LABEL_ISOLATED**. Kullanıcı bu politikayı çıkarımdan önce açıkça onayladı. Önceki STRICT_ANALYST_BLINDNESS_COMPROMISED sınırlaması aynen geçerlidir; bu deney tam araştırmacı-kör veya bağımsız klinik validasyon diye sunulmaz.

## Onay ve precommit

Yalnız DB14569 aktif tedizolid. DB09042 fosfat, stress modeller, A1P1 ve yeni GNN müdahalesi NOT_RUN. Beş frozen primary outer PT–B1 modelinin tamamı tek dış query için kullanıldı; performansa göre seçim veya retry yok. Seed20261106 mevcut eğitim seed'idir; inference deterministik, yeni rastgele seçim yok.

Precommit SHA-256: `{lock['precommit_sha256']}`

Prediction_lock SHA-256: `{lockhash}`

precommit_manifest.json, active_input.json ve approved_policy.json girdiyi/yöntemi; her modelin NPZ/JSON hash'ini, scaler mean/scale'ini, exact class-ID sırasını/head hash'ini, ham ve dönüştürülmüş özellikleri, train-ID hash'ini ve split hash'lerini içerir. Precommit gerçek skorlardan önce diske yazıldı; precommit_sha256.json sabitleme kaydıdır. Bütün kaynak hash'leri çıkarımdan hemen önce ve lock öncesi tekrar doğrulandı. Bu SHA kayıtları yerel iç bütünlük ve işlem sırasını belgeler; bağımsız zaman damgası veya dijital imza değildir.

DB14569 frozen62 ve beş model train/scaler fit kimliklerinde yokluğu yeniden kontrol edildi. Önceki kabul edilmiş alias/tam InChIKey/bağlantısallık denetimi hash ile bağlıdır. RDKit ham SMILES yeniden doğrulandı; key XFALPSLJIHVRKE-GFCCVEGCSA-N. Sıra/birim MW370.344g/mol, Crippen LogP1.3957,boyutsuz;HBD1,HBA7,TPSA106.26Å²,mask1. WP04 tanımları, tam yapı ve includeSandP=False korunur. Fosfatın kaynak dosyada ayrı kayıt olarak bulunması onun model girdisi yapılması değildir; active_input yalnız DB14569 değerleridir.

108başarılı heldout replay/16abstention ve27854eski skor kanıtı korunup denetlendi. Eski guard modülü değiştirilmedi; yeni yetkilendirilmiş dış modül ayrıdır. Bu tur eski OOF yeniden yazılmadı veya baseline fit yapılmadı. Ön kapıda16offline test geçti; ardından tek query/beş matris-vektör model çağrısı yapıldı. Model sınıfları zaten fit edilmiş geçerli başlıklardır; eski NA/başlık dışı hedefe yeni skor uydurulmadı.

## Gerçek çıktılar

|Model|Geçerli PT|Ortak201 dışındaki geçerli PT|
|---|---:|---:|
|Primary B1 outer1|220|19|
|Primary B1 outer2|262|61|
|Primary B1 outer3|267|66|
|Primary B1 outer4|270|69|
|Primary B1 outer5|275|74|

Toplam1294bireysel skor kaydı; fold1_scores…fold5_scores CSV/JSON dosyalarında tümü korunur. Her satırda rank,CUI,skor,logit,drug,fold,modeljob/sürüm,model/input/scaler/head/feature hash'i ve proxy semantiği yer alır. CUI dizilişi NPZ head'iyle aynı hedefe bağlanır; çıktı sıralaması skor azalan, tam eşitlikte CUI leksikografik artan olarak önceden belirlenmiştir.

common201_scores.csv/json yalnız beş fit edilmiş başlığın201PT kesişimidir. Her hedefte **5 sigmoid skorunun .2 ağırlıklı aritmetik ortalaması**; logit ortalaması, en iyi fold veya eksik skorun sıfırla doldurulması değil. Beş bileşen skor da aynı satırda saklanır.201dışındaki1093? böyle bir sayı kullanılmaz: bu deneyde ortak dışı bireysel satır toplamı289'dur; benzersiz hedef union'u ile karıştırılmaz. Başarı/duyarlılık/klinik risk paydası yoktur.

İlk ortak skorlar sayısal olarak frozen PT CUI'lerle notebook/tablolarda gösterilir. Bu tur PT adları/tedizolid eşleşmeleri için dış sözlük, prospektüs, SIDER etiketleri veya advers reaksiyon başvuru kaynağı açılmadı. CUI skorlarının büyüklüğü SIDER observed-record eğitim proxy'sinin sıralama çıktısıdır; bireysel yan etki görülme olasılığı, sıklık, kalibrasyon veya nedensellik değildir. Unknown biyolojik negatif değildir. Referans olmadan başarı metriği hesaplanmadı.

## Kilit ve sayısal doğrulama

prediction_lock.json girdi/model/politika ve tüm bireysel/ortak skor CSV/JSON hash'lerini bağlar. prediction_lock_sha256.json ve prediction_lock.sha256 kolay doğrulama kopyalarıdır. inference_started.json tek query başlangıcını; numerical_checks.json finite skor/logit ve sigmoid eşitliğini kaydeder. Tekrar çağrı, model dosyasını açmadan ONE_QUERY_NO_RETRY_NO_OVERWRITE ile reddedilir.

13post-lock test PASS: lock/çıktı/input hash'leri,1query/5model,precommit<başlangıç<lock sırası,exact head üyeliği,finite/bounds ve sigmoid-logit ayrımı,CSV/JSON float roundtrip eşitliği,rank/tie politikası,201aritmetik ortalama ve bileşenler,NOT_RUN kapsamı,tekrar kilidi. Sayısal testler kayıtlı sonuçlar üzerinde çalışır; gerçek modeli ikinci kez çağırmaz. Ön kapı16+son kapı13=29test PASS. Sahte label alanları/yanlış temsil/birim/sıra/nonfinite girdi reddedilir. Reference mutation testi giriş şemasında yasak alan enjeksiyonunu reddetme düzeyindedir; bu bütün gelecekteki kod için evrensel sızıntısızlık iddiası değildir.

## SHAP uygulanabilirliği ve erteleme

docs/plan/WP11_B1_SHAP_CONTRACT_v1.md okundu. Yeni dış query için her modelin exact train_drug_ids listesindeki eşit ağırlıklı frozen standardized feature background'u kullanılabilir; aynı logit kapalı formu phi=w*(x−mean_train),base=b+w*mean_train,z=base+sum(phi). Model/scaler/head fit edilmez. Mevcut feature NPZ, train-ID hizası,6özellik/mask şeması ve kilitli query vektörü gerekir. Bunlar teknik olarak mevcuttur; bu tur yeni SHAP **DEFERRED_NOT_RUN**. Öncelik prediction_lock olduğundan kullanıcıya yeni attribution sonucu sunulmaz. İleride ayrı sürüm aynı WP11 logit/background sözleşmesini doğrulamalıdır.

201PT özeti sigmoid skor ortalamasıdır; tek doğrusal logit modeline eşit değildir. Beş modelin logit-SHAP değerlerini ortalamak bu skor-ortalama ensemble'ının SHAP açıklaması sayılmaz. Ensemble açıklaması istenirse çıktı ölçeği/değer fonksiyonu ayrı sözleşme gerektirir. Klinik risk veya mekanizma çıkarımı yapılamaz.

## Bilimsel durum ve koruma

Geçmiş istenmeyen arama parçacığı maruziyeti silinmedi. Bu tur ağ/arama/API/prospektüs/tedizolid SIDER etiketi erişimi0. Önceki parçacıklar hiçbir girdide/seçimde kullanılmadı; yöntem kullanıcı tarafından sonuçlardan önce sabitlendi. Hazırlık policy'sindeki eski PENDING veNOT_RUN kayıtları tarihsel olarak aynen korundu; bu yeni dizin onaylı dış aşamayı kaydeder.

DB09042/stress/A1P1/SHAP NOT_RUN ve insan QA PENDING durumları korunur. Önceki kabul edilmiş hash'ler final_verification.json kapsamında denetlenir; tüm disk taraması yoktur. Gizli .env/anahtar okunmadı veya hash envanterine alınmadı. Eski run_status baytları yeni giriş altında aynen saklanır. Bu çıktı OOF değildir; WP08–WP10 skorlarının yerine yazılmaz. Grafikler gerçek kilitli skor dosyalarından, notebook çalıştırılmıştır; model yeniden çalıştırmaz.

## Kullanıcıya sonuç ve STOP

Tedizolidin beş B1 modeline ait bireysel sıralamaları ve ortak201hedef sıralaması tamamlanıp kilitlendi. Değerler araştırma kayıt sıralama skorlarıdır; herhangi bir prospektüsle uyum veya klinik doğruluk değerlendirmesi henüz yoktur. Gerçek model skorları artık referans kolundan önce sabittir. **STOP: bu tur kilitten sonra da referans açılmadı.** Kullanıcı PDF'yi ayrı sonraki değerlendirme aşamasında sağlayabilir; o aşama ayrıca kaynak kimliği ve uzman PT crosswalk gerektirir. PDF'de yokluk gerçek negatif veya kesin yanlış tahmin sayılamaz.
'''
 # Remove explanatory arithmetic anti-example from final narrative; keep final statement concrete.
 report=report.replace("201dışındaki1093? böyle bir sayı kullanılmaz: bu deneyde ortak dışı bireysel satır toplamı289'dur; benzersiz hedef union'u ile karıştırılmaz.","Ortak dışı bireysel satır toplamı289'dur; benzersiz hedef union'u ile karıştırılmaz.")
 (ROOT/'reports/WP13_TEDIZOLID_B1_EXTERNAL_v1.md').write_text(report,encoding='utf-8')
 preserved=read(Q/'preserved_prior_files.json')
 for p,h in preserved.items():assert public_sha(ROOT/p)==h,p
 assert public_sha(Q/'prediction_lock.json')==before_lock_hash
 for log,n in [('pre_inference_tests.log',16),('post_lock_tests.log',13)]:
  value=(Q/log).read_text(encoding='utf-8-sig');assert f'Ran {n} tests' in value and value.rstrip().endswith('OK')
 before=(Q/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==before
 prefix=f'''# WP13 Tedizolid B1 gerçek dış tahmin v1 ·09.11.2026

EXPLORATORY_EXTERNAL_LABEL_ISOLATED. Kullanıcı onayıyla yalnızDB14569aktif tedizolid/beşfrozen primary B1 çalıştı. Precommit {lock['precommit_sha256']};prediction_lock {lockhash}.1query/5model/1294bireyselskor+201ortakPTeşitağırlıklıskorortalaması kilitli; eksik0doldurma/modelseçimi yok. DB09042/stress/A1P1 NOT_RUN; yeniSHAP DEFERRED_NOT_RUN.16önkapı+13sonkapı=29testPASS; eski108replay/16abstentionkanıtı aynı. GeçmişSTRICT_ANALYST_BLINDNESS_COMPROMISED korunur. Bu tur referansPDF/tedizolidSIDERetiketi/ağAPI/arama0; yeni eğitim/attribution0. Rapor reports/WP13_TEDIZOLID_B1_EXTERNAL_v1.md; notebook notebooks/WP13_Tedizolid_B1_external_v1.ipynb; QA/figures WP13/tedizolid_B1_external_v1. EskiOOF/modeller/PDF/QA/PENDING ve tarihçe korunur. STOP: kilitten sonra da referans açılmadı; PDF sonraki ayrı değerlendirme aşamasında kullanıcı tarafından sağlanabilir.

---
Önceki durum (tam baytları korunmuş):

'''
 (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
 write(Q/'final_verification.json',{'previous_files_verified':len(preserved),'precommit_sha256':lock['precommit_sha256'],'prediction_lock_sha256':lockhash,'prediction_lock_unchanged':True,'pre_inference_tests_PASS':16,'post_lock_tests_PASS':13,'external_query_count':1,'frozen_primary_B1_forward_calls':5,'individual_score_rows':sum(map(len,frames)),'common_PT_scores':len(common),'new_training':0,'new_SHAP_or_GNN_attribution':0,'reference_access_this_turn':False,'API_or_network_this_turn':False,'status':'EXPLORATORY_EXTERNAL_LABEL_ISOLATED','analyst_blindness':'STRICT_ANALYST_BLINDNESS_COMPROMISED_PRESERVED','history_exact_suffix':(ROOT/'run_status.md').read_bytes().endswith(before),'private_files_read':False})
 files=['scripts/wp13_tedizolid_B1_external_v1.py','scripts/wp13_tedizolid_B1_external_deliverables_v1.py','tests/test_wp13_tedizolid_B1_external_v1.py','tests/test_wp13_tedizolid_prediction_lock_v1.py','reports/WP13_TEDIZOLID_B1_EXTERNAL_v1.md','notebooks/WP13_Tedizolid_B1_external_v1.ipynb','run_status.md']
 files.extend(p.relative_to(ROOT).as_posix() for folder in [Q,F] for p in folder.iterdir() if p.is_file())
 write(Q/'evidence_manifest.json',{p:public_sha(ROOT/p) for p in sorted(set(files))});print('Prior preserved files:',len(preserved));print('Prediction lock unchanged:',lockhash)
if __name__=='__main__':main()
