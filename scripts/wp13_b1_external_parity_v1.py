"""B1 frozen transform + known heldout replay only. External scoring deliberately disabled."""
import json,math
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import expit
from wp12_api_security import public_sha
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/tedizolid_preparation_v1'
FIELDS=['MW','LogP','HBD','HBA','TPSA']
def transform(raw,statistics,available=True):
 if not available:return np.zeros(6,dtype=np.float64)
 if list(raw)!=FIELDS:raise ValueError('FEATURE_ORDER_MISMATCH')
 x=np.asarray([raw[k] for k in FIELDS],dtype=float)
 if not np.isfinite(x).all():raise ValueError('NONFINITE_FEATURE')
 mean=np.array([statistics['mean'][k] for k in FIELDS]);scale=np.array([statistics['scale'][k] for k in FIELDS])
 if not np.isfinite(scale).all() or (scale<=0).any():raise ValueError('INVALID_FROZEN_SCALE')
 return np.r_[(x-mean)/scale,1.]
def heldout_scores(drug,vector,model_npz,allowed):
 frozen_ids=set(pd.read_csv(ROOT/'reports/qa/WP07/drug_modality_QA.csv',usecols=['drug_id']).drug_id)
 if drug not in allowed or drug not in frozen_ids:raise ValueError('EXTERNAL_SCORING_NOT_AUTHORIZED')
 if vector.shape!=(6,) or vector[-1]!=1 or not np.isfinite(vector).all():raise ValueError('ABSTAIN_OR_BAD_VECTOR')
 return expit(model_npz['coef']@vector+model_npz['intercept'])
def replay():
 prep=ROOT/'reports/qa/WP08/experimental_preparation';chem=pd.read_csv(ROOT/'reports/qa/WP04/chemical_features_clean.csv').set_index('id')
 cohort=pd.read_csv(ROOT/'reports/qa/WP07/drug_modality_QA.csv').set_index('drug_id');parts=pd.read_csv(prep/'nested_partitions_v1.csv')
 oof=pd.read_csv(ROOT/'reports/qa/WP08/baseline_v1/oof_predictions.csv',usecols=['protocol','outer_fold','family','model','drug_id','class_id','score_observed_record_proxy'])
 oof=oof[oof.family.eq('PT')&oof.model.eq('B1')];manifest=json.loads((ROOT/'reports/qa/WP08/baseline_v1/model_artifact_manifest.json').read_text());manifest={k.replace('\\','/'):v for k,v in manifest.items()}
 audit=[];sources={};heads=[]
 for protocol in ['primary','stress']:
  for fold in range(1,6):
   context=f'{protocol}_o{fold:02d}_final';rel=f'models/WP08_baseline_v1/{context}_PT_B1_selected'
   for extension in ['json','npz']:
    p=rel+'.'+extension;assert public_sha(ROOT/p)==manifest[p];sources[p]=manifest[p]
   meta=json.loads((ROOT/(rel+'.json')).read_text());stats=meta['transform_fit_sources']['chemistry'];assert meta['feature_schema']==['chem__'+k for k in FIELDS]+['mask__chemistry']
   test=set(parts[parts.context.eq(context)&parts.split.eq('test')].drug_id);assert not test&set(meta['train_drug_ids'])
   with np.load(ROOT/(rel+'.npz'),allow_pickle=False) as model,np.load(prep/'features'/(context+'.npz'),allow_pickle=False) as feature:
    assert public_sha(prep/'features'/(context+'.npz'))==meta['feature_file_sha256']
    ids=list(feature['drug_ids'].astype(str));heads.append({'context':context,'classes':list(model['class_ids'].astype(str))})
    for drug in sorted(test):
     avail=bool(cohort.loc[drug,'chemistry_qc_available']);raw={k:float(chem.loc[drug,k]) for k in FIELDS} if avail else {}
     x=transform(raw,stats,avail);err=float(np.max(np.abs(x-feature['B1'][ids.index(drug)])))
     assert err<1e-12
     if not avail:
      audit.append({'context':context,'drug_id':drug,'status':'ABSTAIN','transform_error':err,'score_error':None,'PT':0});continue
     scores=heldout_scores(drug,x,model,test);rows=oof[oof.protocol.eq(protocol)&oof.outer_fold.eq(fold)&oof.drug_id.eq(drug)].set_index('class_id')
     classes=list(model['class_ids'].astype(str));assert set(rows.index)==set(classes)
     serr=float(np.max(np.abs(scores-rows.loc[classes,'score_observed_record_proxy'].to_numpy())))
     assert serr<1e-12
     audit.append({'context':context,'drug_id':drug,'status':'PARITY_PASS','transform_error':err,'score_error':serr,'PT':len(classes)})
 pd.DataFrame(audit).to_csv(Q/'B1_heldout_replay.csv',index=False)
 (Q/'B1_replay_source_pins.json').write_text(json.dumps(sources,indent=2))
 (Q/'frozen_B1_head_ids.json').write_text(json.dumps(heads,indent=2))
 print('Replay cases:',len(audit),'no external scores produced')
if __name__=='__main__':replay()
