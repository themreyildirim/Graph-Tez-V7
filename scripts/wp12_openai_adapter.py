"""OpenAI Responses Structured Outputs adaptörü v1; yalnız S01 yürütümü açık."""
import copy
import hashlib
import json
from pathlib import Path
from decimal import Decimal
from jsonschema import Draft202012Validator
import wp12_source_case as c
import wp12_method_v2 as v

QA=c.ROOT/'reports/qa/WP12/openai_api_pilot_v1'
POLICY=c.ROOT/'configs/WP12_OPENAI_API_PILOT_v1.json'
MODEL='gpt-5.4-mini'


def to_supported(node):
    if isinstance(node,list):return [to_supported(x) for x in node]
    if not isinstance(node,dict):return node
    out={}
    for k,value in node.items():
        if k in ['$schema','uniqueItems']:continue
        if k=='oneOf':out['anyOf']=to_supported(value)
        elif k=='const':
            out['enum']=[value];out['type']='null' if value is None else 'string'
        else:out[k]=to_supported(value)
    return out


def api_schema():
    # Root union yok; bütün object alanları required ve additionalProperties=false.
    return {'type':'object','properties':{'result':to_supported(v.case_schema())},
        'required':['result'],'additionalProperties':False}


def source_payload():
    ctx=v.verified_S01_context()
    mapping=c.read(c.ROOT/'reports/qa/WP12/pilot_v1/drug_identity_review.json')
    record=next(x for x in mapping if x.get('DrugBank_parent_id')=='DB00199')
    assert record['existing_parent_name']=='Erythromycin'
    refs={x['quote_id']:x for x in ctx['scenario']['sources']}
    return {'scenario_id':'S01','question_tr':ctx['scenario']['question_tr'],
        'acceptance_criteria_tr':ctx['scenario']['acceptance_criteria_tr'],
        'DrugBank_parent_id':record['DrugBank_parent_id'],
        'identity_caveat':'Ana ilaç kimliği ürün, tuz, doz ve formülasyon eşdeğerliği değildir.',
        'sources':[{**s,**refs[s['quote_id']]} for s in ctx['sources']]}


def build_request():
    instructions=v.SYSTEM.read_text(encoding='utf-8')+'\nAPI adapter v1: Kök JSON yalnız result alanını taşır; yukarıdaki açıklama nesnesini result içine yaz. language=tr beyanı yanında her açıklama cümlesi gerçekten Türkçe olmalıdır.'
    return {'model':MODEL,'instructions':instructions,
        'input':[{'role':'user','content':[{'type':'input_text','text':c.dump(source_payload())}]}],
        'text':{'format':{'type':'json_schema','name':'wp12_s01_source_explanation_api_v1','strict':True,'schema':api_schema()}},
        'reasoning':{'effort':'none'},'max_output_tokens':1200,'store':False,'stream':False,
        'background':False,'tools':[],'tool_choice':'none','service_tier':'default','truncation':'disabled'}


def token_count_payload(req):
    return {k:copy.deepcopy(req[k]) for k in ['model','instructions','input','text','reasoning']}


def estimate_upper(input_tokens,policy):
    if type(input_tokens) is not int or not 0<input_tokens<=policy['input_token_cap']:
        raise ValueError('INPUT_TOKEN_CAP_STOP_NO_INFERENCE')
    rates=policy['prices_per_million_USD']
    base=(Decimal(input_tokens)*Decimal(rates['input'])+Decimal(policy['max_output_tokens'])*Decimal(rates['output']))/1000000
    guarded=base*Decimal(policy['cost_margin_multiplier'])
    if guarded>Decimal(policy['reservation_per_inference_USD']):raise ValueError('PER_REQUEST_COST_CAP_STOP')
    return {'input_tokens_exact_server_preflight':input_tokens,'max_output_tokens_including_reasoning':policy['max_output_tokens'],
        'worst_case_no_cache_USD':str(base),'margin_upper_USD':str(guarded),
        'reservation_USD':policy['reservation_per_inference_USD'],'cached_discount_assumed':False}


def usage_cost(usage,policy):
    if not isinstance(usage,dict):return {'status':'UNKNOWN_USAGE_STOP','actual_token_cost_USD':None}
    details=usage.get('input_tokens_details') or {};output_details=usage.get('output_tokens_details') or {}
    if not isinstance(details,dict):details={}
    if not isinstance(output_details,dict):output_details={}
    inp=usage.get('input_tokens');out=usage.get('output_tokens');cached=details.get('cached_tokens')
    reasoning=output_details.get('reasoning_tokens')
    fields={'input_tokens':inp,'cached_input_tokens':cached,'output_tokens_total':out,'reasoning_tokens_included_in_output':reasoning}
    if any(type(x) is not int or x<0 for x in [inp,out,cached]) or cached>inp:
        return {**fields,'status':'UNKNOWN_USAGE_STOP','actual_token_cost_USD':None}
    if details.get('cache_write_tokens',0):
        return {**fields,'status':'UNPRICED_CACHE_WRITE_STOP','actual_token_cost_USD':None}
    rates=policy['prices_per_million_USD']
    cost=(Decimal(inp-cached)*Decimal(rates['input'])+Decimal(cached)*Decimal(rates['cached_input'])+Decimal(out)*Decimal(rates['output']))/1000000
    return {**fields,'status':'CALCULATED_FROM_USAGE','actual_token_cost_USD':str(cost),
        'excludes_tax_or_unreported_billing_adjustments':True,'reasoning_not_double_counted':True}


def assess_response(response):
    base={'model':response.get('model'),'response_id':response.get('id'),'completion_status':response.get('status'),
        'schema_status':'NOT_EVALUABLE','application_status':'NOT_EVALUABLE','Turkish_quality':'PENDING',
        'source_faithfulness':'PENDING_AGENT_AND_HUMAN_REVIEW','human_review':'PENDING','automatic_release':False}
    if response.get('status')!='completed':return {**base,'status':'INCOMPLETE_OR_FAILED_NO_RETRY'}
    allowed={'gpt-5.4-mini','gpt-5.4-mini-2026-03-17'}
    if response.get('model') not in allowed:return {**base,'status':'UNEXPECTED_MODEL_VERSION_STOP'}
    contents=[x for item in response.get('output',[]) if item.get('type')=='message' for x in item.get('content',[])]
    if any(x.get('type')=='refusal' for x in contents):return {**base,'status':'API_NATIVE_REFUSAL_RECORDED_NO_RETRY'}
    texts=[x['text'] for x in contents if x.get('type')=='output_text' and isinstance(x.get('text'),str)]
    if len(texts)!=1:return {**base,'status':'MISSING_OR_MULTIPLE_OUTPUT_TEXTS'}
    try:
        def pairs(items):
            d={}
            for k,value in items:
                if k in d:raise ValueError('DUPLICATE_KEY')
                d[k]=value
            return d
        def invalid(value):raise ValueError('NON_JSON_CONSTANT')
        parsed=json.loads(texts[0],object_pairs_hook=pairs,parse_constant=invalid)
        Draft202012Validator(api_schema()).validate(parsed)
    except Exception:return {**base,'status':'JSON_OR_API_SCHEMA_FAIL','schema_status':'FAIL'}
    check=v.inspect_candidate(parsed['result'])
    passed=check['schema_valid'] and check['source_contract_valid'] and not check['errors']
    return {**base,'status':'PENDING_SOURCE_AND_HUMAN_REVIEW' if passed else 'APPLICATION_OR_LANGUAGE_FLAG_FAIL',
        'schema_status':'PASS','application_status':'PASS' if passed else 'FAIL',
        'Turkish_quality':'FAIL' if 'OBVIOUS_NON_TURKISH' in check['errors'] else 'PENDING',
        'parsed_json':parsed,'validation':check,'semantic_success':None}
