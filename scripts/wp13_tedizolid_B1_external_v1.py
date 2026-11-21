"""User-authorized one-query external B1 run. Two phases: precommit, then immutable lock.
No web, labels, PDF, fitting, attribution, GNN or stress-model access.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
import numpy as np,pandas as pd
from scipy.special import expit
from wp12_api_security import public_sha
from wp13_b1_external_parity_v1 import transform,FIELDS
ROOT=Path(__file__).resolve().parents[1];PREP=ROOT/'reports/qa/WP13/tedizolid_preparation_v1'
Q=ROOT/'reports/qa/WP13/tedizolid_B1_external_v1'
SCHEMA=['chem__'+k for k in FIELDS]+['mask__chemistry']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def now():return datetime.now(timezone.utc).isoformat()
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest_obj(x):return hashlib.sha256(canonical(x)).hexdigest()
def write(p,data):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
def check_hashes(pins,root=ROOT):
 for p,h in pins.items():
  if public_sha(root/p)!=h:raise ValueError('INPUT_HASH_MISMATCH: '+p)
def validate_input(x):
 expected={'drug_id','representation','raw_smiles','InChIKey','features','units','chemistry_available','descriptor_definition','rdkit_version','source_provenance'}
 if set(x)!=expected:raise ValueError('UNEXPECTED_OR_MISSING_INPUT_FIELD')
 if x['drug_id']!='DB14569' or x['representation']!='active_tedizolid':raise ValueError('UNAUTHORIZED_REPRESENTATION')
 if list(x['features'])!=FIELDS or not x['chemistry_available']:raise ValueError('FEATURE_ORDER_OR_MASK')
 if x['units']!=['g/mol','dimensionless Crippen LogP','count','count','angstrom^2']:raise ValueError('UNITS_MISMATCH')
 if not np.isfinite(list(x['features'].values())).all():raise ValueError('NONFINITE_FEATURE')
def rank_frame(classes,scores):
 if len(classes)!=len(set(classes)) or len(classes)!=len(scores):raise ValueError('TARGET_ALIGNMENT')
 if not np.isfinite(scores).all() or np.any((scores<0)|(scores>1)):raise ValueError('BAD_SCORE')
 d=pd.DataFrame({'class_id':classes,'record_ranking_score':scores}).sort_values(['record_ranking_score','class_id'],ascending=[False,True],kind='mergesort').reset_index(drop=True)
 d.insert(0,'rank',np.arange(1,len(d)+1));return d
def common_summary(frames,common):
 if len(frames)!=5 or len(common)!=201:raise ValueError('COMMON_HEAD_POLICY')
 matrix=np.column_stack([f.set_index('class_id').loc[common,'record_ranking_score'].to_numpy() for f in frames])
 return rank_frame(common,matrix.mean(axis=1)),matrix
def precommit():
 if Q.exists():raise RuntimeError('VERSION_ALREADY_EXISTS_NO_OVERWRITE_OR_AUTORETRY')
 Q.mkdir(parents=True)
 preserved=read(PREP/'prior_pins.json');preserved.update(read(PREP/'evidence_manifest.json'));preserved.pop('run_status.md',None)
 preserved['reports/qa/WP13/tedizolid_preparation_v1/evidence_manifest.json']=public_sha(PREP/'evidence_manifest.json')
 check_hashes(preserved);write(Q/'preserved_prior_files.json',preserved);(Q/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
 # Accepted preparation is immutable. No ADR source is read here.
 accepted=read(PREP/'evidence_manifest.json');input_pins={k:v for k,v in accepted.items() if k.endswith(('chemical_QC_features.csv','identity_vs_frozen62.json','B1_heldout_replay.csv','B1_replay_source_pins.json'))}
 check_hashes(input_pins)
 replay=pd.read_csv(PREP/'B1_heldout_replay.csv');assert sum(replay.status.eq('PARITY_PASS'))==108 and sum(replay.status.eq('ABSTAIN'))==16
 assert replay.transform_error.max()<1e-12 and replay.score_error.max()<1e-12
 identities=read(PREP/'identity_vs_frozen62.json');assert next(r for r in identities if r['id']=='DB14569')['outside_frozen62']
 c=pd.read_csv(PREP/'chemical_QC_features.csv');c=c[c.id.eq('DB14569')];assert len(c)==1;c=c.iloc[0]
 from wp04_chemistry import parse_smiles,identity,descriptors,rdBase
 mol,status=parse_smiles(c.raw_smiles);assert status=='valid';ident=identity(mol);values=descriptors(mol)
 assert ident['rdkit_inchikey']==c.XML_InChIKey=='XFALPSLJIHVRKE-GFCCVEGCSA-N'
 assert all(abs(values[k]-float(c[k]))<1e-10 for k in FIELDS)
 x={'drug_id':'DB14569','representation':'active_tedizolid','raw_smiles':c.raw_smiles,'InChIKey':c.XML_InChIKey,'features':{k:float(c[k]) for k in FIELDS},'units':['g/mol','dimensionless Crippen LogP','count','count','angstrom^2'],'chemistry_available':True,'descriptor_definition':'WP04 descriptors: MolWt/MolLogP/NumHDonors/NumHAcceptors/CalcTPSA(includeSandP=False); no fragment removal','rdkit_version':rdBase.rdkitVersion,'source_provenance':'accepted local DrugBank XML SMILES; preparation source CSV SHA pinned'}
 validate_input(x);write(Q/'active_input.json',x)
 inventory=ROOT/'reports/qa/WP07/drug_modality_QA.csv';assert 'DB14569' not in set(pd.read_csv(inventory,usecols=['drug_id']).drug_id)
 input_pins[inventory.relative_to(ROOT).as_posix()]=public_sha(inventory)
 model_manifest={k.replace('\\','/'):v for k,v in read(ROOT/'reports/qa/WP08/baseline_v1/model_artifact_manifest.json').items()}
 models=[]
 for fold in range(1,6):
  job=f'primary_o{fold:02d}_final_PT_B1_selected';rel='models/WP08_baseline_v1/'+job
  for ext in ['json','npz']:input_pins[rel+'.'+ext]=model_manifest[rel+'.'+ext]
  check_hashes({rel+'.'+e:input_pins[rel+'.'+e] for e in ['json','npz']})
  meta=read(ROOT/(rel+'.json'));assert meta['baseline']=='B1' and meta['family']=='PT' and meta['context']==f'primary_o{fold:02d}_final'
  assert 'DB14569' not in meta['train_drug_ids'] and 'DB09042' not in meta['train_drug_ids'];assert meta['feature_schema']==SCHEMA
  assert 'DB14569' not in meta['transform_fit_sources']['chemistry_fit_drug_ids']
  with np.load(ROOT/(rel+'.npz'),allow_pickle=False) as p:
   targets=list(p['class_ids'].astype(str));assert targets==meta['fitted_classes'];assert p['coef'].shape==(len(targets),6) and p['intercept'].shape==(len(targets),)
  statistics=meta['transform_fit_sources']['chemistry'];vector=transform(x['features'],statistics,True)
  models.append({'fold':fold,'job':job,'model_json':rel+'.json','model_npz':rel+'.npz','model_version':meta['model_version'],'classes':targets,'class_order_sha256':digest_obj(targets),'feature_schema':SCHEMA,'scaler':statistics,'scaler_sha256':digest_obj(statistics),'transformed_input':vector.tolist(),'transformed_input_sha256':digest_obj(vector.tolist()),'train_ids_sha256':digest_obj(meta['train_drug_ids'])})
 common=sorted(set.intersection(*(set(m['classes']) for m in models)));assert len(common)==201
 policy={'version':'WP13-TEDIZOLID-B1-external-v1','user_authorized':True,'status':'EXPLORATORY_EXTERNAL_LABEL_ISOLATED','analyst_blindness':'STRICT_ANALYST_BLINDNESS_COMPROMISED_PRESERVED','drug_id':'DB14569','DB09042':'NOT_RUN','A1P1':'NOT_RUN','SHAP':'DEFERRED_NOT_RUN','primary_models':'all5 selected frozen primary outer B1 PT; no stress','common_summary':'201 intersection PT; arithmetic mean of 5 sigmoid record-ranking scores; equal weights .2; not average logits','common_classes':common,'common_classes_sha256':digest_obj(common),'missing_scores':'NO_ZERO_FILL_NO_FOLD_SELECTION','ranking':'descending score; exact-score ties CUI lexicographic; stable mergesort','reference_policy':'NO_REFERENCE_ACCESS_BEFORE_OR_AFTER_LOCK_THIS_TURN','features_only':SCHEMA,'semantics':'SIDER observed-record proxy; unknown NOT biological negative; NOT clinical risk/frequency/calibration','seed':'20261106 frozen training; no new stochastic inference or seed search','stopping_rule':'write one lock then STOP; never overwrite or automatic retry'}
 write(Q/'approved_policy.json',policy)
 for p in [Q/'active_input.json',Q/'approved_policy.json',Path(__file__),ROOT/'scripts/wp13_b1_external_parity_v1.py',ROOT/'scripts/wp04_chemistry.py']:input_pins[p.relative_to(ROOT).as_posix()]=public_sha(p)
 splitbase=ROOT/'reports/qa/WP08/experimental_preparation'
 for name,h in read(splitbase/'frozen_split_manifest.json').items():input_pins[(splitbase/name).relative_to(ROOT).as_posix()]=h
 check_hashes(input_pins)
 commit={'created_utc':now(),'phase':'PRECOMMIT_BEFORE_EXTERNAL_SCORES','input_sha256':public_sha(Q/'active_input.json'),'policy_sha256':public_sha(Q/'approved_policy.json'),'source_files_sha256':input_pins,'models':models,'reference_inputs':[],'external_score_outputs_present':False,'local_integrity_limit':'SHA-256 internal precommit; no third-party timestamp or signature'}
 assert not list(Q.glob('*scores*'))
 write(Q/'precommit_manifest.json',commit);write(Q/'precommit_sha256.json',{'precommit_sha256':public_sha(Q/'precommit_manifest.json'),'committed_utc':now()})
 print('PRECOMMIT_WRITTEN',public_sha(Q/'precommit_manifest.json'))
def verify_precommit():
 expected=read(Q/'precommit_sha256.json')['precommit_sha256']
 if public_sha(Q/'precommit_manifest.json')!=expected:raise ValueError('PRECOMMIT_HASH_MISMATCH')
 c=read(Q/'precommit_manifest.json');check_hashes(c['source_files_sha256']);validate_input(read(Q/'active_input.json'))
 return c
def infer():
 if (Q/'inference_started.json').exists() or (Q/'prediction_lock.json').exists():raise RuntimeError('ONE_QUERY_NO_RETRY_NO_OVERWRITE')
 c=verify_precommit();policy=read(Q/'approved_policy.json');assert len(c['models'])==5
 write(Q/'inference_started.json',{'created_utc':now(),'precommit_sha256':public_sha(Q/'precommit_manifest.json'),'query_count':1,'models':5,'reference_access':False})
 frames=[];outputs={};numeric=[]
 for model in c['models']:
  with np.load(ROOT/model['model_npz'],allow_pickle=False) as p:
   vector=np.asarray(model['transformed_input']);logits=p['coef']@vector+p['intercept'];scores=expit(logits)
   frame=rank_frame(model['classes'],scores);z=dict(zip(model['classes'],logits));frame['logit']=[z[t] for t in frame.class_id]
  frame['drug_id']='DB14569';frame['fold']=model['fold'];frame['model_job']=model['job'];frame['model_sha256']=c['source_files_sha256'][model['model_npz']];frame['input_sha256']=c['input_sha256'];frame['scaler_sha256']=model['scaler_sha256'];frame['head_order_sha256']=model['class_order_sha256'];frame['feature_sha256']=model['transformed_input_sha256'];frame['model_version']=model['model_version'];frame['semantics']=policy['semantics']
  for suffix in ['csv','json']:
   p=Q/f"fold{model['fold']}_scores.{suffix}"
   if suffix=='csv':
    with p.open('x',encoding='utf-8-sig',newline='') as f:frame.to_csv(f,index=False,float_format='%.17g')
   else:write(p,frame.to_dict('records'))
   outputs[p.relative_to(ROOT).as_posix()]=public_sha(p)
  frames.append(frame);numeric.append({'fold':model['fold'],'PT_count':len(frame),'finite_scores':bool(np.isfinite(scores).all()),'sigmoid_logit_max_error':float(np.max(np.abs(expit(frame.logit.to_numpy())-frame.record_ranking_score.to_numpy())))})
 common,matrix=common_summary(frames,policy['common_classes']);common['drug_id']='DB14569';common['contributing_models']=5;common['aggregation']='equal_weight_arithmetic_score_mean';common['semantics']=policy['semantics']
 keyed=pd.DataFrame(matrix,index=policy['common_classes'],columns=[f'fold{i}' for i in range(1,6)]).loc[common.class_id]
 for column in keyed:common[column+'_score']=keyed[column].to_numpy()
 for suffix in ['csv','json']:
  p=Q/f'common201_scores.{suffix}'
  if suffix=='csv':
   with p.open('x',encoding='utf-8-sig',newline='') as f:common.to_csv(f,index=False,float_format='%.17g')
  else:write(p,common.to_dict('records'))
  outputs[p.relative_to(ROOT).as_posix()]=public_sha(p)
 write(Q/'numerical_checks.json',numeric);outputs[(Q/'numerical_checks.json').relative_to(ROOT).as_posix()]=public_sha(Q/'numerical_checks.json')
 verify_precommit()
 lock={'created_utc':now(),'status':'PREDICTIONS_LOCKED_STOP_BEFORE_REFERENCE','experiment_status':policy['status'],'drug_id':'DB14569','precommit_sha256':public_sha(Q/'precommit_manifest.json'),'input_sha256':c['input_sha256'],'policy_sha256':c['policy_sha256'],'input_and_models_sha256':c['source_files_sha256'],'outputs_sha256':outputs,'individual_targets':[len(f) for f in frames],'common_targets':201,'query_count':1,'forward_calls':5,'DB09042':'NOT_RUN','stress':'NOT_RUN','A1P1':'NOT_RUN','SHAP':'DEFERRED_NOT_RUN','reference_access':False,'source_labels_accessed':False,'strict_analyst_blindness':'COMPROMISED_FROM_PRIOR_STAGE_PRESERVED'}
 write(Q/'prediction_lock.json',lock);write(Q/'prediction_lock_sha256.json',{'prediction_lock_sha256':public_sha(Q/'prediction_lock.json')})
 print('LOCKED',public_sha(Q/'prediction_lock.json'))
if __name__=='__main__':
 if sys.argv[1:] == ['--precommit']:precommit()
 elif sys.argv[1:] == ['--infer-once']:infer()
 else:raise SystemExit('Use --precommit, then --infer-once. No automatic retry.')
