"""Locked SHAP presentation only. No model load, fit, prediction, network or reference."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from wp12_api_security import public_sha
from wp09_close_wp10_notebooks import execute,INIT
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/tedizolid_B1_SHAP_v1';F=ROOT/'reports/figures/WP13/tedizolid_B1_SHAP_v1';PRED=ROOT/'reports/qa/WP13/tedizolid_B1_external_v1'
EXPECTED='301a116e8f7de4c40c3d10fbbd2e4a122689f8319d82f36eb6183f4b8b0de2f1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,data):
 with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 F.mkdir(parents=True,exist_ok=False)
 lock=read(Q/'explanation_lock.json');ehash=public_sha(Q/'explanation_lock.json');assert ehash==read(Q/'explanation_lock_sha256.json')['sha256'];assert public_sha(PRED/'prediction_lock.json')==EXPECTED
 for collection in [lock['source_pins'],lock['outputs_sha256']]:
  for p,h in collection.items():assert public_sha(ROOT/p)==h,p
 local=pd.read_csv(Q/'local_feature_SHAP.csv',float_precision='round_trip');pairs=pd.read_csv(Q/'pair_additivity.csv',float_precision='round_trip');names=read(Q/'selected_PT_names.json')
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 labels=['Molekül ağırlığı','LogP','HBD','HBA','TPSA','Kimya maskesi']
 for n in names:
  sub=local[local.class_id.eq(n['class_id'])];fig,axes=plt.subplots(1,5,figsize=(18,5.3),sharex=True,sharey=True)
  bound=max(float(sub.SHAP_logit.abs().max())*1.25,.01)
  for fold,ax in enumerate(axes,1):
   rows=sub[sub.fold.eq(fold)];values=rows.SHAP_logit.to_numpy();pair=pairs[pairs.fold.eq(fold)&pairs.class_id.eq(n['class_id'])].iloc[0]
   ax.barh(np.arange(6),values,color=['#247c8d' if v>0 else '#b65e6c' if v<0 else '#aaaaaa' for v in values]);ax.axvline(0,color='#777777',linewidth=.7);ax.set_yticks(np.arange(6),labels);ax.set_xlim(-bound,bound);ax.invert_yaxis() if fold==1 else None
   ax.set_title(f'Model {fold}\nbase={pair.base_logit:.4f}\nkilitli logit={pair.locked_logit:.4f}',fontsize=10);ax.set_xlabel('SHAP logit katkısı')
   for j,v in enumerate(values):ax.text(v,j,f' {v:.3g} ' if v>=0 else f'{v:.3g} ',va='center',ha='left' if v>=0 else 'right',fontsize=8)
  fig.suptitle(f"DB14569 · {n['rank']}. hedef: {n['term_tr_editorial']} / {n['term']} · {n['class_id']}",fontsize=13)
  fig.text(.5,.02,'Her panel ayrı B1 modeli; ensemble SHAP yok. Pozitif/negatif logit katkısı klinik risk veya neden değildir.',ha='center',fontsize=10)
  fig.tight_layout(rect=(0,.06,1,.88));fig.savefig(F/f"PT{n['rank']:02d}_{n['class_id']}_five_models.png",dpi=170);plt.close(fig)
 # A complete readable per-target verbal appendix, not only one example.
 verbal=read(Q/'Turkish_verbal_explanations.json');appendix=['# DB14569 — Kilitli ilk10 hedefin model bazlı Türkçe açıklamaları','Türkçe adlar editoryaldir; onaylı MedDRA çevirisi veya prospektüs eşlemesi değildir. Modeller ayrı açıklanır.']
 for n in names:
  appendix.append(f"\n## {n['rank']}. {n['term_tr_editorial']} / {n['term']} ({n['class_id']})\n")
  for row in verbal:
   if row['class_id']==n['class_id']:appendix.append(row['explanation_tr']+'\n')
 (ROOT/'reports/WP13_TEDIZOLID_B1_SHAP_VERBAL_v1.md').write_text('\n\n'.join(appendix),encoding='utf-8')
 execute('WP13_Tedizolid_B1_SHAP_v1.ipynb',[
 ('md','''# WP13 — DB14569 kilitli ilk10 hedef için B1 SHAP v1

Tahmin SHA301a116e… yeniden doğrulandı.10hedef kilitli ortak201sıralamasının ilk10'udur: seçim tahminlerden bağımsız değil, **referans/etiketten bağımsızdır**. Yeni tahmin veya eğitim yok.50model/PT ve300özellik katkısı ayrı yeni sürümdür. Ensemble SHAP veya biyolojik mekanizma açıklaması değildir. Geçmiş bilgi körlüğü sınırlaması aynen korunur.'''),
 ('code',INIT+r'''
Q=ROOT/'reports/qa/WP13/tedizolid_B1_SHAP_v1';F=ROOT/'reports/figures/WP13/tedizolid_B1_SHAP_v1'
display(pd.read_json(Q/'selected_PT_names.json'))
pre=json.loads((Q/'pre_explanation_manifest.json').read_text(encoding='utf-8'))
display(pd.DataFrame([{'fold':b['fold'],'train_background_size':b['n_train'],'model':b['model_npz'],'background_query_excluded':'DB14569' not in b['train_ids']} for b in pre['backgrounds']]))
'''),
 ('md','''**Yorum:** Adlar yalnız donmuş CUI–terim sözlüğünden; ilaç/yan etki eşlemesi veya sıklık bilgisi okunmadı. Türkçe gösterimler editoryaldir. Her modelin kendi tam train background'u eşit ağırlıkla kullanılır; test ve yeni query referansa girmez.'''),
 ('code',r'''
f=pd.read_csv(Q/'local_feature_SHAP.csv',float_precision='round_trip');p=pd.read_csv(Q/'pair_additivity.csv',float_precision='round_trip')
display(p[['fold','class_id','base_logit','sum_phi','locked_logit','locked_record_score','additivity_error','sigmoid_check_error']])
display(p[['additivity_error','sigmoid_check_error']].max().to_frame('en_büyük_hata'))
display(f[f.feature.eq('mask__chemistry')][['fold','class_id','raw_value','background_mean_standardized','coefficient','SHAP_logit']])
'''),
 ('md','''**Yorum:** base+Σφ kilitli gerçek logitle uyumludur; açıklama olasılık ölçeğinde toplamsal değildir. Maskenin katkısı bu query/background karşılaştırmasında0; eksik kimyanın genel olarak önemsiz olduğu sonucunu vermez. Pozitif/negatif kimyasal katkılar modele göre değişebilir.'''),
 ('code',r'''
from IPython.display import Image
selected=json.loads((Q/'selected_PT_names.json').read_text(encoding='utf-8'))
verbal=pd.read_csv(Q/'Turkish_verbal_explanations.csv')
for n in selected:
    display(Image(filename=str(F/f"PT{n['rank']:02d}_{n['class_id']}_five_models.png"),width=1400))
    display(verbal[verbal.class_id.eq(n['class_id'])][['fold','term','explanation_tr']])
'''),
 ('md','''**Yorum:** On grafikte beş panel,50bireysel model açıklamasıdır; her panel yalnız kendi katsayı/background'u içindir. Görsellerde sayılar okunabilirlik için yuvarlanır; ham tam hassasiyet CSV/JSON'da. Gösterim seçimi kilitli ilk10 ile sınırlıdır; herhangi bir prospektüs sonucu kullanılmadı. Aynı/similar terim isimli CUI'ler birleştirilmedi.'''),
 ('code',r'''
coverage=pd.read_csv(Q/'coverage.csv');display(coverage.groupby(['fold','status']).size().unstack(fill_value=0))
lock=json.loads((Q/'explanation_lock.json').read_text(encoding='utf-8'));display(pd.Series({k:lock[k] for k in ['prediction_lock_sha256','selected_PT','model_PT_pairs','feature_contributions','outside_common201_top10_PT','uncomputed_individual_model_PT_pairs','new_model_predict_calls','no_ensemble_SHAP','reference_access','prior_blindness']}).to_frame('kilit_ve_kapsam'))
'''),
 ('md','''**Yorum:**191diğer ortak hedef ve1244diğer fitted model/PT çifti NOT_RUN; sıfır SHAP ile doldurulmadı. Beş sigmoid skorunun ortalaması tek doğrusal model değildir; bireysel SHAP ortalamaları ensemble açıklaması sayılmaz. SIVEXTRO PDF/SIDER tedizolid etiketi/ağ erişimi yok. Bu sürüm kilitlendi; referans aşaması ayrı kullanıcı işlemidir.''')])
 table='\n'.join(f"|{n['rank']}|{n['class_id']}|{n['term_tr_editorial']}|{n['term']}|" for n in names)
 maxerr=float(pairs.additivity_error.max());maxscore=float(pairs.sigmoid_check_error.max())
 report=f'''# WP13 — DB14569 ilk10 kilitli hedef için gerçek B1 SHAP v1

**SHAP_LOCKED_STOP_BEFORE_REFERENCE.** Yeni sürümde50bireysel B1model/PT açıklaması ve300özellik katkısı tamamlandı. Yeni model/fold seçimi, eğitim, tahmin tekrarı veya referans incelemesi yok. EXPLORATORY_EXTERNAL_LABEL_ISOLATED ve geçmiş STRICT_ANALYST_BLINDNESS_COMPROMISED korunur.

## Kilitler ve kaynaklar

Tahmin kilidi Python bağımsız chunked SHA-256 ve PowerShell Get-FileHash ile yeniden hesaplandı: `{EXPECTED}`. Beş NPZ/metadata, tüm bireysel ve ortak201 skor CSV/JSON dosyaları, orijinal precommit/input/policy/scaler/head/feature hash'leri doğrulandı. Tahmin kilidi ve skorlar işlem boyunca değişmedi.

Pre-explanation SHA-256: `{public_sha(Q/'pre_explanation_manifest.json')}`

Explanation lock SHA-256: `{ehash}`

pre_explanation_manifest, açıklama değerleri hesaplanmadan önce seçili hedefleri/rankları, beş model/background üyeliğini, özellik dosyası, scaler, kaynak ve yöntem hash'lerini sabitledi. Kaynak WP11_B1_SHAP_CONTRACT_v1 ve frozen policy_v1. Seçim **kilitli tahmin sıralamasına bağlı**, fakat prospektüs/gerçek etiketten bağımsızdır. Tahminlerden bağımsız örnek seçimi veya tarafsız genel açıklama örneklemi diye sunulmaz. Bu kullanıcı tarafından önceden belirlenmiş ilk10 koşullu incelemedir.

## Sabit10 hedef

|Kilitli sıra|PT CUI|Türkçe editoryal ad|Donmuş terim adı|
|---|---|---|---|
{table}

Ad kaynağı yalnız mevcut pt_concept_dictionary.csv, iki sütun CUI/term. Bu dosya ilaç–yan etki ilişkisi veya PT sıklığı içermez. Yeni web/güvenlilik referansı/SIVEXTRO etiketi açılmadı. Türkçe adlar editoryaldir; onaylı MedDRA çevirisi, klinik doğrulama veya PDF–PT çapraz eşlemesi değildir. Yakın anlamlı CUI'ler ayrı tutulur. Adlar bu olayların tedizolidde gerçekten gözlendiğini göstermez.

## Exact interventional linear SHAP

Her model için6özellik: MW,LogP,HBD,HBA,TPSA ve ayrı kimya bulunabilirlik maskesi. Query x, kilitli model-specific standardized vektördür. Background, yalnız o modelin **tam train_drug_ids** listesinin saved B1 feature NPZ satırları; eşit ağırlıklı, örnekleme/yeniden fit yok. Test kimlikleri ve DB14569 background dışında. WP11 frozen_contexts ile üyelik, metadata ile özellik hash'i ve scaler/head sırası karşılaştırıldı.

φ_i=w_i(x_i−mean_train_i), base=b+w·mean_train; base+Σφ kilitli logitle karşılaştırılır. Bu kullanıcı isteğiyle yeni attribution'dır; orijinal WP11 artefaktlarını değiştirmez. Kod yeni bir gerçek query `predict/forward` çağrısı yapmaz; yalnız katsayı/background ile katkı/base hesabı ve kilitli çıktı rekonstrüksiyonu yapar. expit(rekonstrüksiyon) kontrolü yeni tahmin dosyası üretmez; eski kilitli skorla eşitliği denetler.

50çiftte maksimum logit toplamsallık farkı **{maxerr:.17g}** (tolerans1e-10); maksimum sigmoid/locked-score farkı **{maxscore:.17g}** (tolerans1e-12).300satırın tümünde katsayı, ham/standardize değer, background ortalaması, özellik türü ve gerçek işaret korunur. Maskede50yerel katkı0 çünkü query ve background maskeleri1; bu maskenin başka eksik-modalite durumlarında önemsizliğini kanıtlamaz.

## Sözlü yorum

Pozitif φ yalnız bu modelde train-background'a göre logiti artırıcı; negatif φ azaltıcı,0sıfır katkıdır. Özelliğin ham değerinin yüksek/düşük olması tek başına yönü belirlemez; katsayı ve background farkı birlikte etkilidir. Biyolojik mekanizma, nedensellik, klinik sıklık/kalibrasyon veya yüzde risk üretilmez. Yüksek proxy skor, bütün kimyasal katkıların pozitif olduğunu göstermez; model base'i de vardır.

Örnek: model1/İshal için base1.2028393651467484 ve kimyasal+maske katkı toplamı0.15495992764950872, kilitli logit1.357799292796257 ile eşittir. HBD katkısı+0.09622034541489968, HBA−0.005849215876346629, maske0. Bu klinik ishal olasılığının açıklaması değil, ayrı B1 logitinin açıklamasıdır.

Her hedefin beş modeline ait tam Türkçe paragraf reports/WP13_TEDIZOLID_B1_SHAP_VERBAL_v1.md; feature düzeyi300cümle local_feature_SHAP.csv/json;50model/PT paragrafı Turkish_verbal_explanations.csv/json. Tablolarda exact ham değerler; grafik yazılarında okunabilirlik için yuvarlama var. Her hedef için beş ayrı panel ve Türkçe yorum notebook'ta gösterilir. Tekil model katkıları toplanıp/ortalanıp201sigmoid-ortalama ensemble'ının SHAP'ı olarak sunulmaz. Ensemble attribution bu tur NOT_RUN.

## Kapsam, test ve koruma

Ortak201'de191diğer hedef NOT_RUN; bireysel fit başlıklarında toplam1244model/PTçifti NOT_RUN. Bunun anlamı etki yok/SHAP0 değildir. Model head'i dışındaki hedefler için açıklama veya skor genişletilmedi. coverage.csv/json her modelin başlığını ve durumunu açıkça saklar.

10önkapı test PASS: lock/precommit/top10/background/işaret/maske/hassasiyet/formül/64koalisyon bağımsız **sentetik** kontrol/ölçek/schema.14sonkapı PASS: explanation/source hash'leri,50/300anahtar,lockedlogit+skor,herözellikformülü,background,NOT_RUN,NA/sıfır yokluğu,anlatım işaretleri,noensemble/predict,kronoloji,tekrar engeli. Sentetik64koalisyon testi gerçek tedizolid model tahminini tekrar çalıştırmaz. Gerçek sayısal kontroller SHAP rekonstrüksiyonunu kilitli çıktıyla karşılaştırır; performans metriği değildir.

Çalıştırılmış notebook notebooks/WP13_Tedizolid_B1_SHAP_v1.ipynb.10gerçek katkı görseli reports/figures/WP13/tedizolid_B1_SHAP_v1. QA/CSV/JSON/manifest aynı adlı QA dizininde. Önceki dosyalar hash koruma kapsamında değişmez; final_verification kapsamı tüm disk iddiası değildir. Gizli dosya/anahtar okunmaz. Eski run_status baytları yeni girişin altında aynen tutulur. Prediction_lock içindeki eski SHAP DEFERRED_NOT_RUN tarihi değiştirilmedi; yeni attribution'ın durumu yalnız yeni explanation_lock'tadır.

SIVEXTRO KÜB/KT, tedizolid SIDER ilişkisi, advers reaksiyon kaynağı, web/API erişimi yok. A1P1, fosfat duyarlılığı, yeni eğitim kapalı kaldı. Geçmiş bilgi maruziyeti sınırlaması silinmedi. Unknown gerçek negatif değildir. **STOP:** açıklamalar sürümlü kilitle tamam; SIVEXTRO KÜB referansı bundan sonraki ayrı kaynak/değerlendirme aşamasında kullanıcı tarafından yüklenebilir. Bu tur karşılaştırma/başarı metriği üretilmedi.
'''
 (ROOT/'reports/WP13_TEDIZOLID_B1_SHAP_v1.md').write_text(report,encoding='utf-8')
 prior=read(Q/'prior_pins.json')
 for p,h in prior.items():assert public_sha(ROOT/p)==h,p
 for log,n in [('pre_explanation_tests.log',10),('post_explanation_tests.log',14)]:
  text=(Q/log).read_text(encoding='utf-8-sig');assert f'Ran {n} tests' in text and text.rstrip().endswith('OK')
 assert public_sha(PRED/'prediction_lock.json')==EXPECTED and public_sha(Q/'explanation_lock.json')==ehash
 before=(Q/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==before
 prefix=f'''# WP13 Tedizolid B1 SHAP v1 ·09.11.2026

Kilitli ortak201ilk10PT ×5B1model=50logitSHAP/300katkı tamamlandı. Pre-explanationhash {public_sha(Q/'pre_explanation_manifest.json')}; explanation_lock {ehash}. Prediction_lock {EXPECTED} aynı. Train-only tam background; ensembleSHAP yok. Logitadditivite max{maxerr:.3g}, sigmoidkontrolfarkı{maxscore:.3g}.24testPASS.191diğerortakPT ve1244diğermodel/PT NOT_RUN; kimyamaskesi ayrı. ÖzgünPTadları+editoryalTürkçe/50paragraf/300özellikyorumu/10grafik/notebook hazır. Yeni model tahmini/eğitim/API/web/SIVEXTROPDF/SIDERtedizolidetiketi erişimi0; A1P1/fosfatkapalı. GeçmişSTRICT_ANALYST_BLINDNESS_COMPROMISED korunur. Rapor reports/WP13_TEDIZOLID_B1_SHAP_v1.md; sözlüek reports/WP13_TEDIZOLID_B1_SHAP_VERBAL_v1.md; notebook notebooks/WP13_Tedizolid_B1_SHAP_v1.ipynb. STOP; referansKÜB sonraki ayrı değerlendirme aşamasında kullanıcı tarafından sağlanabilir. Önceki dosyalar ve tarihçe korunur.

---
Önceki durum (tam baytları korunmuş):

'''
 (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
 dump(Q/'final_verification.json',{'previous_files_verified':len(prior),'original_prediction_lock_sha256':EXPECTED,'explanation_lock_sha256':ehash,'selected_PT':10,'individual_model_PT_pairs':50,'feature_contributions':300,'test_PASS':24,'max_additivity_error':maxerr,'max_sigmoid_check_error':maxscore,'new_prediction_calls':0,'new_training':0,'new_SHAP_pairs':50,'ensemble_SHAP':'NOT_RUN','A1P1':'NOT_RUN','phosphate':'NOT_RUN','reference_access':False,'network_or_API':False,'prior_blindness':'STRICT_ANALYST_BLINDNESS_COMPROMISED_PRESERVED','private_files_read':False,'history_exact_suffix':(ROOT/'run_status.md').read_bytes().endswith(before)})
 files=['scripts/wp13_tedizolid_SHAP_v1.py','scripts/wp13_tedizolid_SHAP_deliverables_v1.py','tests/test_wp13_tedizolid_SHAP_v1.py','tests/test_wp13_tedizolid_SHAP_lock_v1.py','reports/WP13_TEDIZOLID_B1_SHAP_v1.md','reports/WP13_TEDIZOLID_B1_SHAP_VERBAL_v1.md','notebooks/WP13_Tedizolid_B1_SHAP_v1.ipynb','run_status.md']
 files.extend(p.relative_to(ROOT).as_posix() for folder in [Q,F] for p in folder.iterdir() if p.is_file())
 dump(Q/'evidence_manifest.json',{p:public_sha(ROOT/p) for p in sorted(set(files))});print('Previous files verified:',len(prior));print('Explanation lock:',ehash)
if __name__=='__main__':main()
