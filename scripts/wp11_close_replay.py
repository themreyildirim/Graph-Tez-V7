"""Kapanışta mevcut testleri ve dondurulmuş mevcut kayıtları yeniden doğrular."""
import contextlib,io,json,sys,time,unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from wp11_close_audit import ROOT,C,G,read,csv,preserve
from wp11_linear_shap import sha,write_json
from wp11_graph_run import load,forward,old
from wp11_graph_forward import cache_for,resolve_relation,pair_index_by_ids,torch,numeric_digest


def main():
    if (C/'replay_complete.json').exists():raise RuntimeError('Closure replay already exists')
    preserve();commit=read(C/'replay_commit.json');assert all(sha(ROOT/p)==h for p,h in commit.items())
    sys.path.insert(0,str(ROOT/'tests'));calls=[]
    def forbidden(*a,**k):calls.append('forbidden');raise AssertionError('Closure forbids training/optimizer/backward')
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    results=[];probes=[];originals=[]
    with contextlib.ExitStack() as guard:
        for obj,name in [(old,'fit_model'),(old,'training'),(old,'run_job'),(torch.optim.Optimizer,'__init__'),(torch.Tensor,'backward')]:guard.enter_context(patch.object(obj,name,forbidden))
        for module,count in [('test_wp11_graph_synthetic',10),('test_wp11_graph_real',16),('test_wp11_shap',18)]:
            logpath=C/(module+'_closure_rerun.txt');assert not logpath.exists();stream=io.StringIO();start=time.perf_counter()
            suite=unittest.defaultTestLoader.loadTestsFromName(module)
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);logpath.write_text(stream.getvalue(),encoding='utf-8')
            assert result.wasSuccessful() and result.testsRun==count,stream.getvalue()
            results.append({'module':module,'passed':result.testsRun,'seconds':time.perf_counter()-start,'log_sha256':sha(logpath),'old_log_overwritten':False})
        frozen=pd.read_csv(C/'replay_keys_frozen.csv',keep_default_na=False);existing=pd.read_csv(C/'frozen_replay_existing_rows.csv',keep_default_na=False);base_table=pd.read_csv(G/'original_outputs.csv')
        with torch.no_grad():
            for context,keys in frozen.groupby('context',sort=True):
                s=load(context);q=s['q'];g=s['g'];md=s['md'];base=forward(s)['logits'];targets=md['fitted_targets']
                before=numeric_digest({'model':numeric_digest(s['model'].state_dict()),'graph':numeric_digest(g),'query':numeric_digest(q),'h':s['cache'].protein_h})
                maximum=0.;n=0
                for di,drug in enumerate(q['drug_ids']):
                    if not q['eligible'][di]:continue
                    saved=base_table[base_table.context.eq(context)&base_table.drug_id.eq(drug)].set_index('class_id').loc[targets].original_logit.to_numpy()
                    error=np.abs(base[di].numpy()-saved);maximum=max(maximum,float(error.max()));n+=len(saved)
                assert maximum<=1e-5;originals.append({'context':context,'original_logit_rows':n,'max_saved_logit_error':maximum})
                for r in keys.itertuples():
                    di=list(q['drug_ids']).index(r.drug_id)
                    for mode in ['fixed','delete']:
                        if r.kind=='role':out=forward(s,relation=resolve_relation(g,q,r.drug_id,r.role,r.protein_id),mode=mode)
                        else:out=forward(s,cache=cache_for(s['model'],g,pair_index_by_ids(g,r.protein_a,r.protein_b),mode))
                        saved=existing[existing.context.eq(context)&existing.kind.eq(r.kind)&existing.drug_id.eq(r.drug_id)&existing['mode'].eq(mode)&existing.role.eq(r.role)&existing.protein_id.eq(r.protein_id)&existing.protein_a.eq(r.protein_a)&existing.protein_b.eq(r.protein_b)].set_index('class_id').loc[targets]
                        altered=out['logits'][di].numpy();delta=(base[di]-out['logits'][di]).numpy()
                        assert np.isfinite(altered).all() and len(saved)==len(targets)
                        error=max(float(np.abs(altered-saved.intervened_logit.to_numpy()).max()),float(np.abs(delta-saved.delta_z.to_numpy()).max()))
                        assert error<=1e-5
                        probes.append({'context':context,'kind':r.kind,'drug_id':r.drug_id,'role':r.role,'protein_id':r.protein_id,'protein_a':r.protein_a,'protein_b':r.protein_b,'mode':mode,'existing_PT_rows':len(saved),'max_logit_delta_error':error})
                assert before==numeric_digest({'model':numeric_digest(s['model'].state_dict()),'graph':numeric_digest(g),'query':numeric_digest(q),'h':s['cache'].protein_h})
                print('Replay checked',context,flush=True)
    assert not calls and sum(r['original_logit_rows'] for r in originals)==35974
    csv('tests_rerun_summary.csv',results);csv('existing_attribution_replay.csv',probes);csv('original_model_output_replay.csv',originals)
    preserve();write_json(C/'replay_complete.json',{'status':'PASS','graph_tests_rerun':26,'B1_tests_rerun':18,'graph_existing_interventions_replayed':len(probes),'existing_PT_rows_replayed':sum(r['existing_PT_rows'] for r in probes),'all_original_logit_rows_checked':35974,'max_replay_logit_delta_error':max(r['max_logit_delta_error'] for r in probes),'guard_calls':len(calls),'new_results_or_methods':False,'old_outputs_written':False})
    print(read(C/'replay_complete.json'))


if __name__=='__main__':main()
