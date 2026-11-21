"""Read-only OOF/split provenance audit; no scoring, fitting or target-label loading."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from wp12_api_security import public_sha
ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'reports/qa/WP08/experimental_preparation'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def audit():
    pins={}
    def record(path):
        path=Path(path);pins[path.relative_to(ROOT).as_posix()]=public_sha(path);return path
    manifest=read(record(PREP/'frozen_split_manifest.json'))
    for name,digest in manifest.items():
        if public_sha(record(PREP/name))!=digest:raise ValueError('FROZEN_SPLIT_HASH_MISMATCH')
    part=pd.read_csv(record(PREP/'nested_partitions_v1.csv'))
    outer=pd.read_csv(record(PREP/'outer_membership_v1.csv'))
    stats=read(record(PREP/'transform_fit_sources_and_statistics.json'))
    voc=read(record(PREP/'train_fittable_vocabularies_NO_model_fit.json'))
    rows=[];examples=[]
    for wp,directory in [('WP08','WP08_baseline_v1'),('WP09','WP09_PPI_v3_training_v1'),('WP10','WP10_factorial_training_v1')]:
        qa=ROOT/'reports/qa'/wp/('baseline_v1' if wp=='WP08' else 'training_v1')
        artifact={n.replace('\\','/'):h for n,h in read(record(qa/'model_artifact_manifest.json')).items()}
        path=record(qa/'oof_predictions.csv')
        groups={}
        for chunk in pd.read_csv(path,chunksize=20000):
            if wp=='WP08':chunk=chunk[chunk.family.eq('PT')]
            for (protocol,fold,model),data in chunk.groupby(['protocol','outer_fold','model']):
                key=(protocol,int(fold),model)
                state=groups.setdefault(key,{'drugs':set(),'targets':set(),'jobs':set(),'rows':0})
                state['drugs'].update(data.drug_id);state['targets'].update(data.class_id);state['rows']+=len(data)
                if 'model_job_key' in data:state['jobs'].update(data.model_job_key)
                expected=outer[(outer.protocol==protocol)&(outer.outer_test_fold==fold)]
                if not set(data.drug_id)<=set(expected.drug_id):raise ValueError('OOF_DRUG_NOT_OUTER_TEST')
        for (protocol,fold,model),state in sorted(groups.items()):
            context=f'{protocol}_o{fold:02d}_final'
            parts=part[part.context.eq(context)]
            train=set(parts[parts.split.eq('train')].drug_id);test=set(parts[parts.split.eq('test')].drug_id)
            if train&test:raise ValueError('TRAIN_TEST_OVERLAP')
            group_train=set(parts[parts.split.eq('train')].group_id);group_test=set(parts[parts.split.eq('test')].group_id)
            if group_train&group_test:raise ValueError('STRUCTURAL_GROUP_LEAK')
            if wp=='WP08':
                job=f'{context}_PT_{model}_selected';meta_path=ROOT/'models'/directory/(job+'.json')
            else:
                if len(state['jobs'])!=1:raise ValueError('ONE_OUTER_MODEL_PER_KEY_REQUIRED')
                job=next(iter(state['jobs']));meta_path=ROOT/'models'/directory/(job+'.json')
            meta=read(record(meta_path));parameter=ROOT/'models'/directory/(job+'.npz')
            for p in [meta_path,parameter]:
                rel=p.relative_to(ROOT).as_posix()
                if rel not in artifact or public_sha(record(p))!=artifact[rel]:raise ValueError('MODEL_MANIFEST_MISMATCH')
            fit=set(meta['train_drug_ids'] if wp=='WP08' else meta['train_fit_drug_ids'])
            if not fit<=train or fit&test or state['drugs']-test:raise ValueError('HELDOUT_FIT_LEAK')
            chemistry=set((meta['transform_fit_sources'] if wp=='WP08' else stats[context])['chemistry_fit_drug_ids'])
            if not chemistry<=train or chemistry&test:raise ValueError('HELDOUT_SCALER_LEAK')
            targets=set(meta['fitted_classes'] if wp=='WP08' else meta['fitted_targets'])
            approved=set(voc[context][model if wp=='WP08' else 'B2'])
            if not state['targets']<=targets<=approved:raise ValueError('TARGET_VOCAB_MISMATCH')
            graph_ids=set();graph_targets_absent=True;role_columns=0
            if wp!='WP08':
                train_path=record(ROOT/meta['training_graph_file'])
                if public_sha(train_path)!=meta['training_graph_sha256']:raise ValueError('TRAIN_GRAPH_HASH')
                query_path=record(ROOT/f'reports/qa/WP09/design_v1/folds/{context}_query.npz')
                if public_sha(query_path)!=meta['query_file_sha256']:raise ValueError('QUERY_HASH')
                with np.load(train_path,allow_pickle=False) as a:
                    graph_ids=set(a['drug_ids'].astype(str));proteins=set(a['protein_ids'].astype(str))
                    graph_targets_absent=not any(k in a.files for k in ['labels','y','PT','side_effects'])
                    role_columns=sum(a['role_'+r].shape[1] for r in ['target','enzyme','transporter','carrier'])
                with np.load(query_path,allow_pickle=False) as a:query_ids=set(a['drug_ids'].astype(str))
                if graph_ids!=train or graph_ids&test or query_ids!=test:raise ValueError('TRAIN_GRAPH_QUERY_ISOLATION')
                if not graph_targets_absent:raise ValueError('TRAIN_GRAPH_LABEL_ARRAY')
                # Protein nodes can be shared across drugs; only their fit provenance is train-linked.
                source_proteins=set(stats[context]['protein_fit_accessions'])
                if proteins!=source_proteins:raise ValueError('PROTEIN_SCALER_UNIVERSE')
            rows.append({'package':wp,'protocol':protocol,'outer_fold':fold,'model':model,'job_key':job,
                'train_drugs':len(train),'fitted_drugs':len(fit),'OOF_drugs':len(state['drugs']),
                'OOF_rows':state['rows'],'OOF_targets':len(state['targets']),'fitted_targets':len(targets),
                'drug_disjoint':True,'group_disjoint':True,'transform_train_only':True,'target_train_only':True,
                'graph_train_drugs':len(graph_ids),'graph_label_arrays_absent':graph_targets_absent,'role_edges':role_columns,
                'parameters_sha256':public_sha(parameter),'OOF_file_sha256':pins[path.relative_to(ROOT).as_posix()]})
            for drug in ['DB00199','DB00254']:
                if drug in state['drugs']:
                    examples.append({'drug_id':drug,'package':wp,'protocol':protocol,'model':model,'outer_fold':fold,
                        'job_key':job,'in_own_model_train':drug in fit,'in_train_graph':drug in graph_ids,'in_transform_fit':drug in chemistry,
                        'in_outer_test':drug in test,'PT_count':len(state['targets'])})
    return {'fold_checks':rows,'example_checks':examples,'source_pins':pins,
            'new_model_fit':False,'new_prediction':False,'new_performance_metric':False,
            'scope':'PT OOF for all saved final models/folds in WP08/WP09/WP10, not a general proof of all future code',
            'external_status':'BLOCKED_NO_APPROVED_EXTERNAL_INPUT_ADAPTER'}

if __name__=='__main__':
    q=ROOT/'reports/qa/WP13/v1_2';a=audit()
    for name,data in [('blind_audit.json',a),('blind_source_pins.json',a['source_pins'])]:
        with (q/name).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
    pd.DataFrame(a['fold_checks']).to_csv(q/'OOF_fold_isolation_checks.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(a['example_checks']).to_csv(q/'OOF_demo_drug_checks.csv',index=False,encoding='utf-8-sig')
    print('audited',len(a['fold_checks']),'outer model/fold groups')
