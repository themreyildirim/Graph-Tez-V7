"""Frozen S16 no-source adapter; no PDF text or guessed drug identity."""
from jsonschema import Draft202012Validator
import wp12_openai_scenarios_v2 as previous
from wp12_llm_contract import REFUSALS
old=previous.old
ROOT=previous.ROOT
QA=ROOT/'reports/qa/WP12/openai_S16_preparation_v1'

def context(case):
    if case!='S16':raise ValueError('SCENARIO_NOT_IN_VERSION')
    scenarios=old.c.read(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')
    s=next(s for s in scenarios if s['scenario_id']==case)
    if s['sources'] or s['evidence_ids'] or s['source_characters']!=0:raise ValueError('FROZEN_SOURCE_CHANGED')
    p={k:s[k] for k in ['scenario_id','question_tr','acceptance_criteria_tr','sources']}
    return {'scenario':s},p,{},{}

def schema(case):
    context(case);obj=previous.obj
    item=obj({'explanation_tr':{'type':'string'},'source_scope':{'type':'string'},
              'statement_kind':{'type':'string'},'evidence_ids':{'type':'array','items':{'type':'string'}}})
    common={'schema_version':{'type':'string','enum':['WP12-local-llm-candidate-v2']},
            'language':{'type':'string','enum':['tr']}}
    candidate=obj({**common,'status':{'type':'string','enum':['candidate']},
        'refusal_code':{'type':'null'},'items':{'type':'array','minItems':1,'items':item}})
    refused=obj({**common,'status':{'type':'string','enum':['refused']},
        'refusal_code':{'type':'string','enum':list(REFUSALS)},
        'items':{'type':'array','maxItems':0,'items':item}})
    return obj({'result':{'anyOf':[candidate,refused]}})

def request(case):
    _,p,_,_=context(case)
    return {'model':'gpt-5.4-mini','instructions':(ROOT/'docs/prompts/WP12_OPENAI_S16_SYSTEM_v1.txt').read_text(encoding='utf-8'),
        'input':[{'role':'user','content':[{'type':'input_text','text':old.c.dump(p)}]}],
        'text':{'format':{'type':'json_schema','name':'wp12_s16_no_source_v1','strict':True,'schema':schema(case)}},
        'reasoning':{'effort':'none'},'max_output_tokens':1200,'store':False,'stream':False,'background':False,
        'tools':[],'tool_choice':'none','service_tier':'default','truncation':'disabled'}

def assess(response,case):
    base={'scenario_id':case,'completion_status':response.get('status'),'schema_status':'NOT_EVALUABLE',
        'application_status':'NOT_EVALUABLE','semantic_success':None,'human_review':'PENDING',
        'agent_source_review':'PENDING','automatic_release':False,'source_status':'NO_SOURCES_FROZEN',
        'Turkish_quality':'NOT_EVALUABLE_UNTIL_RESPONSE','refusal_reason_review':'PENDING'}
    if response.get('status')!='completed':return {**base,'status':'INCOMPLETE_OR_FAILED_NO_RETRY'}
    if response.get('model') not in ['gpt-5.4-mini','gpt-5.4-mini-2026-03-17']:return {**base,'status':'UNEXPECTED_MODEL_STOP'}
    parts=[c for m in response.get('output',[]) if m.get('type')=='message' for c in m.get('content',[])]
    if any(c.get('type')=='refusal' for c in parts):return {**base,'status':'API_NATIVE_REFUSAL_PENDING_REVIEW'}
    texts=[c['text'] for c in parts if c.get('type')=='output_text']
    try:
        if len(texts)!=1:raise ValueError('ONE_OUTPUT_REQUIRED')
        value=old.c.parse_json(texts[0]) if hasattr(old.c,'parse_json') else __import__('wp12_openai_client').parse_json(texts[0])
        Draft202012Validator(schema(case)).validate(value)
    except Exception:return {**base,'schema_status':'FAIL','status':'JSON_SCHEMA_FAIL_NO_RETRY'}
    v=value['result'];valid=v['status']=='refused' and v['refusal_code']=='NO_SOURCE' and v['items']==[]
    return {**base,'schema_status':'PASS','application_status':'PASS' if valid else 'FAIL_NO_SOURCE_POLICY',
        'parsed_json':value,'status':'STRUCTURE_VALID_PENDING_AGENT_AND_HUMAN_REVIEW' if valid else 'SOURCE_APPLICATION_FAIL_NO_RETRY',
        'refusal_reason_structural_check':valid,'actual_explanatory_Turkish':'NOT_EVALUABLE_EMPTY_REFUSAL' if valid else 'PENDING',
        'trusted_envelope':{'reported_in_PDF':[], 'predicted_by_GNN':{'status':'NOT_REQUESTED_IN_WP12','artifact_ref':None}}}
