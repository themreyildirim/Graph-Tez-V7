"""S16 actual evidence: read-only, no environment key or network access."""
import hashlib
from decimal import Decimal
from pathlib import Path
from jsonschema import Draft202012Validator
import wp12_openai_S16_adapter_v1 as a
import wp12_openai_S16_execution_v1 as b
from wp12_api_security import public_sha,is_private_path
from wp12_openai_client import parse_json
ROOT=a.ROOT
RUN=ROOT/'reports/qa/WP12/openai_S16_user_runs_v1/20261108_183945_1573b5b2bedc4d9db98e5348884f6749'
QA=ROOT/'reports/qa/WP12/openai_S16_actual_review_v1'
read=a.old.c.read

def inspect():
    manifest=read(RUN/'file_hashes.json')
    assert all(Path(n).name==n and not is_private_path(n) for n in manifest)
    raw=read(RUN/'inference_response_raw.json');record=read(RUN/'run_record.json')
    request=read(RUN/'source_request.json');source=read(RUN/'source_provenance.json')
    value=read(RUN/'validated_JSON.json')
    texts=[c['text'] for m in raw['output'] if m.get('type')=='message' for c in m.get('content',[]) if c.get('type')=='output_text']
    assert len(texts)==1
    Draft202012Validator(a.schema('S16')).validate(value)
    assessed=a.assess(raw,'S16');policy=read(b.prior.base.POLICY)
    use=raw['usage'];inp=use['input_tokens'];out=use['output_tokens'];cache=use['input_tokens_details']['cached_tokens']
    prices=policy['prices_per_million_USD']
    ci=Decimal(inp-cache)*Decimal(prices['input'])/1000000
    cc=Decimal(cache)*Decimal(prices['cached_input'])/1000000
    co=Decimal(out)*Decimal(prices['output'])/1000000;cost=ci+cc+co
    stages=[{'stage':n,**read(RUN/(n+'_HTTP_metadata.json'))} for n in ['model_access','input_token_count','inference']]
    components={'instructions_sha256':hashlib.sha256(request['instructions'].encode()).hexdigest(),
        'input_text_sha256':hashlib.sha256(request['input'][0]['content'][0]['text'].encode()).hexdigest(),
        'schema_sha256':hashlib.sha256(a.old.c.dump(request['text']['format']['schema']).encode()).hexdigest(),'quote_sha256':[]}
    cfg=read(b.POLICY);budget=b.aggregate(policy)
    checks={
        'raw_manifest_and_inventory':all(public_sha(RUN/n)==h for n,h in manifest.items()) and
            {p.name for p in RUN.iterdir() if p.is_file()}==set(manifest)|{'file_hashes.json'},
        'raw_response_hash':public_sha(RUN/'inference_response_raw.json')==record['raw_response_sha256'],
        'frozen_request_and_no_source_payload':request==a.request('S16')==read(b.QA/'S16_request_NOT_SENT.json')
            and source==a.context('S16')[1] and source['sources']==[],
        'prompt_and_execution_hash':components==read(RUN/'prompt_components_sha256.json') and
            read(RUN/'execution_scope.json')['source_request_sha256']==public_sha(RUN/'source_request.json'),
        'raw_JSON_and_recomputed_assessment':parse_json(texts[0])==value and assessed==read(RUN/'technical_and_review_gates.json'),
        'schema_and_application':assessed['schema_status']=='PASS' and assessed['application_status']=='PASS',
        'expected_refusal_no_claims':value['result']['status']=='refused' and value['result']['refusal_code']=='NO_SOURCE'
            and value['result']['items']==[],
        'completed_model_and_IDs':raw['status']==record['completion_status']=='completed' and
            raw['model']==record['model_returned']=='gpt-5.4-mini-2026-03-17' and raw['id']==record['response_id']
            and raw.get('error') is None and raw.get('incomplete_details') is None and record['API_request_id']==stages[-1]['request_id'],
        'single_inference_three_HTTP200':record['http_attempts']==3 and record['inference_attempts']==1 and
            not record['automatic_retry'] and [s['HTTP_status'] for s in stages]==[200,200,200],
        'exact_token_count_and_limits':read(RUN/'input_token_count_response_raw.json')['input_tokens']==inp and
            inp<=6000 and out<=1200 and use['total_tokens']==inp+out and 0<=cache<=inp,
        'usage_cost_independent':cost==Decimal(record['usage_token_cost_USD']) and
            a.old.usage_cost(use,policy)==read(RUN/'usage_and_token_cost.json') and
            a.old.estimate_upper(inp,policy)==read(RUN/'cost_preflight.json'),
        'all_pinned_sources_and_prior_records':all(public_sha(ROOT/n)==h for n,h in cfg['public_files_sha256'].items()),
        'budget15_HTTP5_inference115':budget==read(RUN/'aggregate_budget_after_run.json') and
            (budget['HTTP_reservations_total'],budget['inference_reservations_total'],budget['reserved_USD'])==(15,5,'0.115'),
        'single_scope_locks_and_old_stop':len(list(b.CONTROL.glob('S16_attempt*.json')))==1 and
            len(list(b.CONTROL.glob('http_*.json')))==3 and len(list(b.CONTROL.glob('inference_reservation*.json')))==1 and
            (b.prior.base.PRIOR_ROOTS[0]/'BILLING_OR_LIMIT_STOP.json').exists(),
        'human_pending_no_release_no_GNN':record['human_review']==assessed['human_review']=='PENDING' and
            assessed['semantic_success'] is None and not record['automatic_release'] and
            assessed['trusted_envelope']['predicted_by_GNN']=={'status':'NOT_REQUESTED_IN_WP12','artifact_ref':None},
        'no_tools':raw['tools']==[] and all(m.get('type')=='message' for m in raw['output']),
    }
    prior=read(ROOT/'reports/qa/WP12/openai_S04_actual_review_v1/independent_review.json')
    return {'status':'TECHNICAL_PASS_EXPECTED_NO_SOURCE_REFUSAL_AGENT_REVIEW_PENDING_HUMAN',
        'checks':checks,'model':raw['model'],'API_request_id':record['API_request_id'],
        'HTTP_status':record['HTTP_status'],'completion_status':raw['status'],'latency_seconds':record['latency_seconds'],
        'exact_model_message':texts[0],'parsed_json':value,'usage':use,'input_cost_USD':str(ci),
        'cached_cost_USD':str(cc),'output_cost_USD':str(co),'usage_token_cost_USD':str(cost),
        'known_completed_S01_S07_S04_S16_token_cost_USD':str(Decimal(prior['known_completed_S01_S07_S04_token_cost_USD'])+cost),
        'invoice_total':'UNKNOWN_PRIOR_429_USAGE_AND_BILLING_NOT_QUERIED','schema_status':'PASS','application_status':'PASS',
        'agent_source_review':'EXPECTED_NO_SOURCE_REFUSAL_NO_GENERATED_CLAIMS_IN_THIS_RESPONSE',
        'actual_Turkish_explanation_quality':'NOT_EVALUABLE_NO_EXPLANATION_TEXT',
        'page_quote_alignment':'NOT_APPLICABLE_NO_SOURCES','exception_uncertainty':'NOT_APPLICABLE_NO_CLAIMS',
        'formal_human_review':'PENDING','automatic_release':False,'RAM_VRAM':'NOT_COLLECTED',
        'repeat_stability':'NOT_EVALUABLE_SINGLE_RESPONSE','source_quote_count':0,'raw_files_verified':len(manifest),
        'aggregate_budget':budget,'HTTP_stages':stages,'new_API_requests':0,
        'interpretation_limit':'System and frozen criterion explicitly request NO_SOURCE. One prompted case is not an independent hallucination benchmark.'}
