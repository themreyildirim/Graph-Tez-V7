"""Stream complete existing WP11 attribution tables; index, never compute attribution."""
import json
import pandas as pd
from collections import Counter
import wp13_explain_v2 as m
from wp12_api_security import public_sha
ROOT=m.ROOT;Q=m.Q
def main():
 Q.mkdir(parents=True,exist_ok=False)
 prior=m.old.read(ROOT/'reports/qa/WP13/final_demo_v1/prior_pins.json');prior.update(m.old.read(ROOT/'reports/qa/WP13/final_demo_v1/evidence_manifest.json'));prior.pop('run_status.md',None)
 for p,h in prior.items():assert public_sha(ROOT/p)==h,p
 (Q/'prior_pins.json').write_text(json.dumps(prior,indent=2));(Q/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
 counts=Counter();parts={p:{'shap':[],'graph':[]} for p in m.old.PARENTS};pins={};sourcepins={}
 for rel,kind,cols in [
 ('reports/qa/WP11/B1_SHAP_v1/local_shap.csv','shap',None),
 ('reports/qa/WP11/graph_v1/role_contributions.csv.gz','graph',None),
 ('reports/qa/WP11/graph_v1/ppi_contributions.csv.gz','graph',None)]:
  manifest=m.old.read(ROOT/(str(__import__('pathlib').Path(rel).parent).replace('\\','/')+'/final_artifact_manifest.json'))
  assert public_sha(ROOT/rel)==manifest[rel];sourcepins[rel]=manifest[rel]
  for chunk in pd.read_csv(ROOT/rel,chunksize=50000):
   for (protocol,fold,drug),group in chunk.groupby(['protocol','outer_fold','drug_id']):counts[(kind,protocol,int(fold),drug)]+=len(group)
   if kind=='graph' and 'kind' not in chunk:chunk['kind']='ppi' if '/ppi_' in rel else 'role'
   for p in parts:parts[p][kind].append(chunk[chunk.protocol.eq('primary')&chunk.drug_id.eq(p)].copy())
 for p in parts:
  index={}
  for kind in ['shap','graph']:
   df=pd.concat(parts[p][kind],ignore_index=True);fold=m.old.recorded(p)['fold'];assert set(df.outer_fold)=={fold}
   name=p+'_'+kind+'.csv.gz';df.to_csv(Q/name,index=False,compression='gzip');pins[name]=public_sha(Q/name)
   index[kind]=sorted(set(df.class_id))
  (Q/(p+'_index.json')).write_text(json.dumps(index,indent=2))
 pd.DataFrame([{'method':k[0],'protocol':k[1],'fold':k[2],'drug_id':k[3],'rows':v} for k,v in counts.items()]).to_csv(Q/'full_WP11_coverage_by_drug_fold.csv',index=False)
 (Q/'explanation_pins.json').write_text(json.dumps(pins,indent=2));(Q/'WP11_source_pins.json').write_text(json.dumps(sourcepins,indent=2))
 print('Complete WP11 rows scanned:',sum(counts.values()))
if __name__=='__main__':main()
