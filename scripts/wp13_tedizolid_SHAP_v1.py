"""New local logit SHAP for preselected locked targets; no predict/fit/network/reference."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import numpy as np,pandas as pd
from scipy.special import expit
from wp12_api_security import public_sha
ROOT=Path(__file__).resolve().parents[1];PRED=ROOT/'reports/qa/WP13/tedizolid_B1_external_v1';Q=ROOT/'reports/qa/WP13/tedizolid_B1_SHAP_v1'
EXPECTED='301a116e8f7de4c40c3d10fbbd2e4a122689f8319d82f36eb6183f4b8b0de2f1'
FEATURES=['chem__MW','chem__LogP','chem__HBD','chem__HBA','chem__TPSA','mask__chemistry']
TR_NAMES={'C0011991':'İshal','C0015230':'Döküntü','C0002792':'Anafilaktik şok','C0042963':'Kusma','C0000737':'Karın ağrısı','C0687713':'Gastrointestinal ağrı','C0020517':'Aşırı duyarlılık','C0033774':'Kaşıntı','C0040034':'Trombositopeni','C0042109':'Ürtiker'}
FEATURE_NAMES=['Molekül ağırlığı','LogP','Hidrojen bağı verici sayısı','Hidrojen bağı alıcı sayısı','Topolojik polar yüzey alanı','Kimya bulunabilirlik maskesi']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def now():return datetime.now(timezone.utc).isoformat()
def checks(pins):
 for p,h in pins.items():
  if public_sha(ROOT/p)!=h:raise ValueError('SOURCE_HASH_MISMATCH: '+p)
def verify_predictions():
 # Separate digest implementation, independent of public_sha helper.
 h=hashlib.sha256()
 with (PRED/'prediction_lock.json').open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 if h.hexdigest()!=EXPECTED:raise ValueError('PREDICTION_LOCK_MISMATCH')
 lock=read(PRED/'prediction_lock.json');checks(lock['outputs_sha256']);checks(lock['input_and_models_sha256'])
 if public_sha(PRED/'precommit_manifest.json')!=lock['precommit_sha256']:raise ValueError('PREDICTION_PRECOMMIT_MISMATCH')
 return lock,read(PRED/'precommit_manifest.json')
def exact_phi_base(x,b,w,a):
 x=np.asarray(x,float);b=np.asarray(b,float);w=np.asarray(w,float);a=np.asarray(a,float)
 if x.shape!=(6,) or b.ndim!=2 or b.shape[1]!=6 or not len(b) or w.ndim!=2 or w.shape[1]!=6 or a.shape!=(len(w),):raise ValueError('SCHEMA_MISMATCH')
 if not all(np.isfinite(v).all() for v in [x,b,w,a]):raise ValueError('NONFINITE_INPUT')
 mu=b.mean(axis=0);phi=w*(x-mu);base=a+w@mu
 return phi,base,mu
def sentence(name,value,is_mask=False):
 effect='artırıcı' if value>0 else 'azaltıcı' if value<0 else 'sıfır katkı'
 kind='Kimya bulunabilirlik maskesi (kimyasal tanımlayıcı değil)' if is_mask else name
 return f'{kind}: SHAP={float(value)!r}; bu B1 modelinde train-only background’a göre logiti {effect} yönde etkiler. Klinik görülme sıklığı veya biyolojik mekanizma değildir.'
def precommit():
 if Q.exists():raise RuntimeError('VERSION_EXISTS_NO_OVERWRITE')
 lock,pc=verify_predictions();Q.mkdir(parents=True)
 prior=read(PRED/'preserved_prior_files.json');prior.update(read(PRED/'evidence_manifest.json'));prior.pop('run_status.md',None)
 prior['reports/qa/WP13/tedizolid_B1_external_v1/evidence_manifest.json']=public_sha(PRED/'evidence_manifest.json');checks(prior)
 write(Q/'prior_pins.json',prior);(Q/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
 common=pd.read_csv(PRED/'common201_scores.csv',float_precision='round_trip');assert len(common)==201
 selected=common.iloc[:10][['rank','class_id','record_ranking_score']].to_dict('records');assert [r['rank'] for r in selected]==list(range(1,11))
 pins={**lock['outputs_sha256'],**lock['input_and_models_sha256']}
 for p in [PRED/'prediction_lock.json',PRED/'precommit_manifest.json',ROOT/'docs/plan/WP11_B1_SHAP_CONTRACT_v1.md',ROOT/'reports/qa/WP11/B1_SHAP_v1/policy_v1.json',Path(__file__),ROOT/'reports/qa/WP03/pt_concept_dictionary.csv']:
  pins[p.relative_to(ROOT).as_posix()]=public_sha(p)
 # Cross-check frozen target NAME taxonomy only. No drug-label relation is opened.
 taxonomy=ROOT/'reports/qa/WP03/pt_concept_dictionary.csv'
 oldpins=read(ROOT/'reports/qa/WP13/v1_2/blind_source_pins.json')
 if taxonomy.relative_to(ROOT).as_posix() in oldpins:assert public_sha(taxonomy)==oldpins[taxonomy.relative_to(ROOT).as_posix()]
 contexts=read(ROOT/'reports/qa/WP11/B1_SHAP_v1/frozen_contexts.json');wp11pins=read(ROOT/'reports/qa/WP11/B1_SHAP_v1/input_manifest.json')
 backgrounds=[]
 for m in pc['models']:
  meta=read(ROOT/m['model_json']);context=meta['context'];train=meta['train_drug_ids']
  assert train==contexts[context]['train_background_ids'] and 'DB14569' not in train
  assert not set(train)&set(meta['test_drug_ids_never_fit']);assert meta['feature_schema']==FEATURES
  rel=f'reports/qa/WP08/experimental_preparation/features/{context}.npz';assert public_sha(ROOT/rel)==meta['feature_file_sha256']==wp11pins[rel]
  pins[rel]=public_sha(ROOT/rel)
  backgrounds.append({'fold':m['fold'],'context':context,'feature_file':rel,'train_ids':train,'n_train':len(train),'equal_weights':True,'model_json':m['model_json'],'model_npz':m['model_npz'],'frozen_scaler':m['scaler'],'transformed_query':m['transformed_input'],'classes':m['classes']})
 method={'version':'WP13-Tedizolid-exact-linear-SHAP-v1','scale':'per-model B1 LOGIT only','formula':'phi=w*(x-mean_train);base=intercept+w*mean_train','background':'all exact saved train_drug_ids; uniform; existing standardized B1 rows','selection':'first10 rows in LOCKED common201 rank; score-based, reference/label-independent; not independent of predictions','selected':selected,'model_folds':[1,2,3,4,5],'drug_id':'DB14569','outside_selection':'NOT_RUN','no_ensemble_SHAP':True,'term_names':'frozen CUI/term dictionary, no association labels; TR names editorial/unapproved terminology','additivity_tolerance':1e-10,'locked_score_tolerance':1e-12,'no_new_predictions':True,'no_reference_access':True,'prior_blindness':'STRICT_ANALYST_BLINDNESS_COMPROMISED_PRESERVED'}
 checks(pins);write(Q/'method_policy.json',method)
 pins[(Q/'method_policy.json').relative_to(ROOT).as_posix()]=public_sha(Q/'method_policy.json')
 pre={'created_utc':now(),'prediction_lock_sha256':EXPECTED,'method':method,'backgrounds':backgrounds,'source_pins':pins,'SHAP_computed':False}
 write(Q/'pre_explanation_manifest.json',pre);write(Q/'pre_explanation_sha256.json',{'sha256':public_sha(Q/'pre_explanation_manifest.json')})
 print('PRE_EXPLANATION_LOCKED',public_sha(Q/'pre_explanation_manifest.json'))
def verify_pre():
 if public_sha(Q/'pre_explanation_manifest.json')!=read(Q/'pre_explanation_sha256.json')['sha256']:raise ValueError('PRE_EXPLANATION_MISMATCH')
 pre=read(Q/'pre_explanation_manifest.json');checks(pre['source_pins']);verify_predictions();return pre
def explain():
 if (Q/'explanation_started.json').exists():raise RuntimeError('NO_AUTORETRY_OR_OVERWRITE')
 pre=verify_pre();write(Q/'explanation_started.json',{'created_utc':now(),'pre_explanation_sha256':public_sha(Q/'pre_explanation_manifest.json'),'new_predict_calls':0})
 names=pd.read_csv(ROOT/'reports/qa/WP03/pt_concept_dictionary.csv',usecols=['meddra_cui','term']).groupby('meddra_cui').term.agg(lambda v:' | '.join(sorted(set(v)))).to_dict()
 selected=[r['class_id'] for r in pre['method']['selected']];features=[];pairs=[];background=[];coverage=[];verbal=[]
 raw=read(PRED/'active_input.json')['features']
 for b in pre['backgrounds']:
  fold=b['fold'];x=np.array(b['transformed_query'],float)
  with np.load(ROOT/b['feature_file'],allow_pickle=False) as f:
   ids=list(f['drug_ids'].astype(str));B=f['B1'][[ids.index(d) for d in b['train_ids']]]
  assert np.all(B[:,5]==1) and x[5]==1
  with np.load(ROOT/b['model_npz'],allow_pickle=False) as model:
   classes=list(model['class_ids'].astype(str));indices=[classes.index(t) for t in selected];w=model['coef'][indices];intercept=model['intercept'][indices]
  locked=pd.read_csv(PRED/f'fold{fold}_scores.csv',float_precision='round_trip').set_index('class_id')
  phi,base,mu=exact_phi_base(x,B,w,intercept)
  for i,t in enumerate(selected):
   z=float(locked.loc[t,'logit']);score=float(locked.loc[t,'record_ranking_score']);reconstructed=float(base[i]+phi[i].sum());error=abs(reconstructed-z);scoreerr=abs(float(expit(reconstructed))-score)
   assert error<1e-10 and scoreerr<1e-12
   term=names.get(t,t);tr=TR_NAMES.get(t,term)
   pairs.append({'drug_id':'DB14569','fold':fold,'model':'B1','class_id':t,'term':term,'term_tr_editorial':tr,'base_logit':float(base[i]),'sum_phi':float(phi[i].sum()),'locked_logit':z,'locked_record_score':score,'additivity_error':error,'sigmoid_check_error':scoreerr,'n_background_train':len(B),'scale':'B1 per-model logit; not ensemble','model_sha256':public_sha(ROOT/b['model_npz']),'pre_explanation_sha256':public_sha(Q/'pre_explanation_manifest.json')})
   for j,feat in enumerate(FEATURES):
    val=float(phi[i,j]);comment=sentence(FEATURE_NAMES[j],val,j==5)
    features.append({'drug_id':'DB14569','fold':fold,'model':'B1','class_id':t,'term':term,'term_tr_editorial':tr,'feature':feat,'feature_name_tr':FEATURE_NAMES[j],'feature_type':'chemistry' if j<5 else 'availability_mask','raw_value':float(raw[feat[6:]]) if j<5 else 1.,'standardized_query':float(x[j]),'background_mean_standardized':float(mu[j]),'coefficient':float(w[i,j]),'SHAP_logit':val,'comment_tr':comment})
   pos=[f'{FEATURE_NAMES[j]} ({phi[i,j]!r})' for j in range(5) if phi[i,j]>0];neg=[f'{FEATURE_NAMES[j]} ({phi[i,j]!r})' for j in range(5) if phi[i,j]<0]
   verbal.append({'class_id':t,'term':term,'term_tr_editorial':tr,'fold':fold,'explanation_tr':f'B1 primary model{fold}, {tr} ({term}): train-only background’a göre logiti artırıcı kimyasal katkılar: '+('; '.join(pos) or 'yok')+'. Azaltıcı kimyasal katkılar: '+('; '.join(neg) or 'yok')+f'. Kimya maskesi ayrı: SHAP={float(phi[i,5])!r}. Base={float(base[i])!r} ve katkı toplamı={float(phi[i].sum())!r}, kilitli logit={z!r} ile uyumludur. Bu bireysel model açıklamasıdır; ortak201 skor ortalamasının SHAP’ı veya biyolojik neden değildir.'})
  for j,feat in enumerate(FEATURES):background.append({'fold':fold,'feature':feat,'train_ids':b['train_ids'],'n_train':len(B),'mean_standardized':float(mu[j]),'minimum':float(B[:,j].min()),'maximum':float(B[:,j].max())})
  for t in classes:coverage.append({'fold':fold,'class_id':t,'status':'EXPLAINED' if t in selected else 'NOT_RUN','reason':'locked_common201_top10' if t in selected else 'outside_preselected_top10; no computation'})
 for name,rows in [('local_feature_SHAP',features),('pair_additivity',pairs),('background_summary',background),('coverage',coverage),('Turkish_verbal_explanations',verbal)]:
  pd.DataFrame(rows).to_csv(Q/(name+'.csv'),index=False,encoding='utf-8-sig',float_format='%.17g');write(Q/(name+'.json'),rows)
 write(Q/'selected_PT_names.json',[{'rank':r['rank'],'class_id':r['class_id'],'term':names.get(r['class_id'],r['class_id']),'term_tr_editorial':TR_NAMES.get(r['class_id'],names.get(r['class_id'],r['class_id'])),'locked_common_record_score':r['record_ranking_score']} for r in pre['method']['selected']])
 verify_pre();outputs={p.relative_to(ROOT).as_posix():public_sha(p) for p in Q.iterdir() if p.is_file() and p.name not in ['prior_pins.json','run_status_before.md']}
 write(Q/'explanation_lock.json',{'created_utc':now(),'status':'SHAP_LOCKED_STOP_BEFORE_REFERENCE','prediction_lock_sha256':EXPECTED,'pre_explanation_sha256':public_sha(Q/'pre_explanation_manifest.json'),'source_pins':pre['source_pins'],'outputs_sha256':outputs,'selected_PT':10,'model_PT_pairs':50,'feature_contributions':300,'outside_common201_top10_PT':191,'uncomputed_individual_model_PT_pairs':len(coverage)-50,'new_model_predict_calls':0,'no_ensemble_SHAP':True,'reference_access':False,'prior_blindness':'STRICT_ANALYST_BLINDNESS_COMPROMISED_PRESERVED'})
 write(Q/'explanation_lock_sha256.json',{'sha256':public_sha(Q/'explanation_lock.json')});print('SHAP_LOCKED',public_sha(Q/'explanation_lock.json'))
if __name__=='__main__':
 if sys.argv[1:]==['--precommit']:precommit()
 elif sys.argv[1:]==['--explain-once']:explain()
 else:raise SystemExit('Use --precommit then --explain-once')
