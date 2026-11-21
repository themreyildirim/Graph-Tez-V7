"""Kayıtlı B1 logitleri için exact interventional linear SHAP;model fit yok."""
from pathlib import Path
import hashlib,itertools,json,math,platform,importlib.util,importlib.metadata
import numpy as np
import pandas as pd
from scipy.special import expit

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP11/B1_SHAP_v1'
PREP=ROOT/'reports/qa/WP08/experimental_preparation'
MODELS=ROOT/'models/WP08_baseline_v1'
FEATURES=['chem__MW','chem__LogP','chem__HBD','chem__HBA','chem__TPSA','mask__chemistry']
CHEM=['MW','LogP','HBD','HBA','TPSA']
SEMANTICS='Exact interventional SHAP of frozen observed-record LR LOGIT;not clinical risk;not causality'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def write_json(path,obj):
    def clean(v):
        if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [clean(x) for x in v]
        if isinstance(v,np.generic):return clean(v.item())
        if isinstance(v,float) and not math.isfinite(v):return None
        return v
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def csv(name,frame):frame.to_csv(QA/name,index=False,encoding='utf-8-sig',lineterminator='\n')


def preserve():
    previous=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    bad=[p for p,h in previous.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(bad)
    return len(previous)


def linear_shap(x,background,coef,intercept):
    """v(S)=mean_B f(x_S,B_notS), f(x)=b+w*x. No label/ID argument."""
    x=np.asarray(x,dtype=np.float64);b=np.asarray(background,dtype=np.float64)
    w=np.asarray(coef,dtype=np.float64);a=np.asarray(intercept,dtype=np.float64)
    if x.ndim!=2 or b.ndim!=2 or w.ndim!=2 or x.shape[1]!=6 or b.shape[1]!=6 or w.shape[1]!=6 or len(b)<1 or a.shape!=(len(w),):raise ValueError('B1 6-feature linear schema')
    if not all(np.isfinite(v).all() for v in [x,b,w,a]):raise ValueError('Nonfinite explanation inputs')
    mu=b.mean(0)
    phi=(x[:,None,:]-mu[None,None,:])*w[None,:,:]
    base=a+w@mu;z=x@w.T+a
    return {'phi':phi,'base':base,'logit':z,'proxy_score':expit(z),'background_mean':mu}


def enumerate_shap(x,background,coef,intercept):
    """Bağımsız 64-koalisyon Shapley hesabı;kapalı formülü çağırmaz."""
    x=np.asarray(x,float);b=np.asarray(background,float);w=np.asarray(coef,float)
    if x.shape!=(6,) or b.ndim!=2 or b.shape[1]!=6 or w.shape!=(6,):raise ValueError('Single B1 output expected')
    values={}
    for bits in itertools.product([False,True],repeat=6):
        matrix=b.copy();matrix[:,bits]=x[np.asarray(bits)]
        values[bits]=float(np.mean(matrix@w+intercept))
    out=np.zeros(6)
    for i in range(6):
        for bits,value in values.items():
            if bits[i]:continue
            count=sum(bits);weight=math.factorial(count)*math.factorial(5-count)/math.factorial(6)
            other=list(bits);other[i]=True
            out[i]+=weight*(values[tuple(other)]-value)
    return out,values[(False,)*6]


def load_context(context):
    md_path=MODELS/(context+'_PT_B1_selected.json');md=json.loads(md_path.read_text(encoding='utf-8'))
    param_path=ROOT/Path(md['parameters_file']);feature_path=PREP/'features'/(context+'.npz')
    if sha(param_path)!=md['parameters_sha256'] or sha(feature_path)!=md['feature_file_sha256']:raise ValueError('Frozen source hash mismatch')
    if md['family']!='PT' or md['baseline']!='B1' or md['feature_schema']!=FEATURES:raise ValueError('PT B1 schema only')
    with np.load(param_path,allow_pickle=False) as data:w=data['coef'].copy();a=data['intercept'].copy();classes=data['class_ids'].astype(str).tolist()
    if classes!=md['fitted_classes'] or len(set(classes))!=len(classes):raise ValueError('Saved PT head order mismatch')
    with np.load(feature_path,allow_pickle=False) as data:ids=data['drug_ids'].astype(str).tolist();x=data['B1'].copy()
    parts=pd.read_csv(PREP/'nested_partitions_v1.csv');parts=parts[parts.context.eq(context)]
    eligible=pd.read_csv(PREP/'prediction_eligibility.csv');eligible=set(eligible[eligible.model.eq('B1')&eligible.eligible].drug_id)
    train=sorted(set(parts[parts.split.eq('train')].drug_id)&eligible);test=sorted(set(parts[parts.split.eq('test')].drug_id)&eligible)
    if train!=md['train_drug_ids'] or set(train)&set(test):raise ValueError('Train/background boundary mismatch')
    if set(md['test_drug_ids_never_fit'])!=set(parts[parts.split.eq('test')].drug_id):raise ValueError('Test membership mismatch')
    indices={d:i for i,d in enumerate(ids)}
    return {'context':context,'metadata':md,'metadata_file':md_path,'parameters_file':param_path,'feature_file':feature_path,
        'classes':classes,'coef':w,'intercept':a,'train_ids':train,'test_ids':test,
        'train_x':x[[indices[d] for d in train]],'test_x':x[[indices[d] for d in test]],
        'parts':parts,'inventory_test_ids':sorted(parts[parts.split.eq('test')].drug_id)}


def initialize():
    if (QA/'policy_v1.json').exists():raise RuntimeError('WP11 SHAP policy already frozen')
    contexts=[f'{p}_o{fold:02}_final' for p in ['primary','stress'] for fold in range(1,6)]
    policy={'version':'WP11-B1-exact-linear-SHAP-v1','date':'2026-11-07','status':'FROZEN_BEFORE_EXPLANATIONS',
        'scope':'10 saved selected outer B1 PT models only;no historical30/inner-C explanation;no refit',
        'method':'exact interventional linear SHAP,closed form;not approximate KernelSHAP or correlation-dependent allocation',
        'game':'v(S)=uniform mean over all eligible train rows of f(x_S,B_notS)',
        'formula':'phi_i=w_i*(x_i-mean_train_i);base=b+w*mean_train;f=base+sum(phi)',
        'output_scale':'saved decision logit z=b+w*x of observed-record proxy;identity link',
        'sigmoid_role':'expit(z) only reconstructs frozen OOF proxy score;SHAP contributions are NOT additive on probability scale',
        'background':'all and only exact saved model train_drug_ids;uniform row weights;existing standardized features;no sampling/stratification/outcomes',
        'no_new_scaler_fit':True,'features':FEATURES,'chemistry_features':CHEM,'mask_policy':'sixth feature separately reported;do not explain abstentions as mask0 predictions',
        'contexts':contexts,'native_targets':'each saved class_ids only;missing/not-fitted targets NA,never union-filled',
        'primary_global':'per-context/per-PT mean(abs(phi)) and mean(phi) over eligible heldout drugs',
        'secondary_global':'per-protocol5-fold INTERSECTION of fitted PT only;all eligible OOF drugs x identical common PT;descriptive average over heterogeneous frozen fold models',
        'examples':'first2 lexicographic eligible TEST drug IDs per context x first2 lexicographic FITTED CUI;no outcomes/ranking/performance selection',
        'plots':'first protocol outer1 first drug/first CUI waterfall;both protocols;native/global common-PT tables',
        'stability':'exact repeat and axis/order invariance;EXHAUSTIVE leave-one-TRAIN-background-drug-out;no seed/model fitting;range is sensitivity NOT confidence interval',
        'stability_statistics':'per-context/PT/feature max_abs_delta_phi,mean_abs_delta_phi and nonzero sign-flip fraction;max/ties use abs1e-12 sign convention',
        'validation':{'additivity_abs_tol':1e-10,'frozen_score_abs_tol':1e-12,'enumeration_abs_tol':1e-10,'order_repeat_abs_tol':1e-12},
        'enumeration':'all64 coalitions for each selected example independently of closed form',
        'SHAP_library':'not installed;implement exact documented linear Shapley game directly;no new dependencies',
        'graph_scope':'WP10 A1P1 method contract only;no graph attribution/optimizer/model run',
        'semantics':SEMANTICS,'WP12':False,'model_fit_authorized':False}
    # Yöntem kararı önce yazılır;bu fonksiyon phi veya açıklama çıktısı hesaplamaz.
    write_json(QA/'policy_v1.json',policy)
    inputs={};context_records={};examples=[];membership=[];common={}
    for context in contexts:
        c=load_context(context);md=c['metadata'];protocol=context.split('_')[0]
        context_records[context]={'train_background_ids':c['train_ids'],'test_explained_ids':c['test_ids'],
            'test_inventory_ids':c['inventory_test_ids'],'fitted_classes':c['classes'],'declared_classes':md['declared_target_dictionary'],
            'model_file':c['parameters_file'].relative_to(ROOT).as_posix(),'metadata_file':c['metadata_file'].relative_to(ROOT).as_posix(),
            'feature_file':c['feature_file'].relative_to(ROOT).as_posix()}
        common[protocol]=set(c['classes']) if protocol not in common else common[protocol]&set(c['classes'])
        for d in c['test_ids'][:2]:
            for cui in c['classes'][:2]:examples.append({'context':context,'protocol':protocol,'drug_id':d,'class_id':cui,'selection':'lexicographic only;train vocabulary and input availability;no test outcomes'})
        for d in c['train_ids']:membership.append({'context':context,'drug_id':d,'role':'TRAIN_BACKGROUND'})
        for d in c['inventory_test_ids']:membership.append({'context':context,'drug_id':d,'role':'TEST_EXPLAINED' if d in c['test_ids'] else 'TEST_ABSTAIN_QC'})
        for path in [c['parameters_file'],c['metadata_file'],c['feature_file']]:inputs[path.relative_to(ROOT).as_posix()]=sha(path)
    for name in ['feature_schema_v1.json','nested_partitions_v1.csv','prediction_eligibility.csv','transform_fit_sources_and_statistics.json','frozen_split_manifest.json']:
        path=PREP/name;inputs[path.relative_to(ROOT).as_posix()]=sha(path)
    for name in ['reports/qa/WP04/chemical_features_clean.csv','reports/qa/WP08/baseline_v1/oof_predictions.csv','reports/qa/WP03/drug_pt_positives.csv','AGENTS.md','docs/plan/ROADMAP_V7.md','reports/WP11_PREPARATION_DECISION.md']:
        inputs[name]=sha(ROOT/name)
    write_json(QA/'frozen_contexts.json',context_records);write_json(QA/'common_PT_intersections.json',{p:sorted(c) for p,c in common.items()})
    csv('examples_frozen_before_explanations.csv',pd.DataFrame(examples));csv('background_test_membership.csv',pd.DataFrame(membership))
    write_json(QA/'input_manifest.json',inputs)
    write_json(QA/'policy_commit_before_explanations.json',{p.relative_to(ROOT).as_posix():sha(p) for p in [QA/'policy_v1.json',QA/'frozen_contexts.json',QA/'common_PT_intersections.json',QA/'examples_frozen_before_explanations.csv',QA/'background_test_membership.csv',QA/'input_manifest.json']})
    write_json(QA/'method_sources.json',{'checked_date':'2026-11-07','primary_sources':[
        {'title':'SHAP LinearExplainer documented exact independent-feature formula','url':'https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html'},
        {'title':'SHAP logistic regression example:explanations in log-odds','url':'https://shap.readthedocs.io/en/latest/example_notebooks/tabular_examples/linear_models/Sentiment%20Analysis%20with%20Logistic%20Regression.html'}],
        'new_biological_data_downloaded':False})
    print('Policy frozen BEFORE explanations:10 outer B1 PT models;examples',len(examples),';common PT counts',{p:len(x) for p,x in common.items()})


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['init','preserve']);args=parser.parse_args()
    if args.action=='init':initialize()
    else:print(preserve())
