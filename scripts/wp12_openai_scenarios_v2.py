"""S07/S04 için dondurulmuş kaynak adaptörü; teknik doğruluk semantik onay değildir."""
from copy import deepcopy
import hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
import wp12_openai_adapter as old
from wp12_llm_contract import source_index,dependencies,validate_candidate,build_review_envelope,REFUSALS

ROOT=old.c.ROOT
QA=ROOT/'reports/qa/WP12/openai_S07_preparation_v2'
SYSTEM=ROOT/'docs/prompts/WP12_OPENAI_SOURCE_SYSTEM_v2.txt'
SCENARIOS=('S07','S04')


def closure(primary,deps):
    result=set();pending=[primary]
    while pending:
        qid=pending.pop()
        if qid in result:continue
        result.add(qid);pending.extend(deps[qid]-result)
    return result


def context(case):
    if case not in SCENARIOS:raise ValueError('SCENARIO_NOT_IN_VERSION')
    ctx=old.c.context(case);quotes,pages,ann=source_index(ctx['bundle'],ctx['annotations'])
    selected=set(ctx['scenario']['evidence_ids']);deps=dependencies(ctx['annotations'])
    if len(selected)!=3:raise ValueError('FROZEN_THREE_SOURCE_PROFILE_CHANGED')
    for qid in selected:
        if not closure(qid,deps)<=selected:raise ValueError('MISSING_FROZEN_SOURCE_DEPENDENCY')
    mapping=old.c.read(ROOT/'reports/qa/WP12/pilot_v1/drug_identity_review.json')
    parent='DB00254' if case=='S07' else 'DB00199'
    drug=next(x for x in mapping if x['DrugBank_parent_id']==parent)
    expected='Doxycycline' if case=='S07' else 'Erythromycin'
    if drug['existing_parent_name']!=expected:raise ValueError('EXISTING_PARENT_ID_NAME_MISMATCH')
    refs={r['quote_id']:r for r in ctx['scenario']['sources']}
    payload={'scenario_id':case,'question_tr':ctx['scenario']['question_tr'],
        'acceptance_criteria_tr':ctx['scenario']['acceptance_criteria_tr'],
        'DrugBank_parent_id':parent,'identity_caveat':'Ana ilaç kimliği ürün/tuz/formülasyon eşdeğerliği veya doğrudan yan etki kanıtı değildir.',
        'sources':[{**s,**refs[s['quote_id']],
            'required_context_quote_ids':sorted(closure(s['quote_id'],deps)-{s['quote_id']})} for s in ctx['sources']]}
    return ctx,payload,deps,ann


def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


def schema(case):
    ctx,payload,deps,ann=context(case)
    variants=[]
    for s in payload['sources']:
        required=closure(s['quote_id'],deps)
        variants.append(obj({'explanation_tr':{'type':'string','minLength':1,'maxLength':1200},
            'source_scope':{'type':'string','enum':[s['scope']]},
            'statement_kind':{'type':'string','enum':[s['kind']]},
            'evidence_ids':{'type':'array','minItems':len(required),'maxItems':len(required),
                'items':{'type':'string','enum':sorted(required)}}}))
    common={'schema_version':{'type':'string','enum':['WP12-local-llm-candidate-v2']},
        'status':{'type':'string','enum':['candidate']},'refusal_code':{'type':'null','enum':[None]},
        'language':{'type':'string','enum':['tr']},
        'items':{'type':'array','minItems':3,'maxItems':3,'items':{'anyOf':variants}}}
    candidate=obj(common);refusal=deepcopy(common)
    refusal['status']={'type':'string','enum':['refused']}
    refusal['refusal_code']={'type':'string','enum':list(REFUSALS)}
    refusal['items']={'type':'array','maxItems':0,'items':{'type':'string'}}
    # Refusal kaydedilebilir; tam okunur bağlamda uygunluğu ayrıca denetlenir.
    return obj({'result':{'anyOf':[candidate,obj(refusal)]}})


def semantic_plan(case):
    ctx,payload,_,_=context(case)
    checks=(['Tetracycline sınıf girişi ve renal bildirimin sınıf kapsamı korunuyor mu?',
        'BUN artışı bildirimindeki apparently/dose-related nitelemesi korunuyor mu?',
        'D_BUN_exception ilk cümlesindeki sınıf düzeyinde may cause anlamı korunuyor mu?',
        'İkinci cümledeki studies to date indicate, doxycycline ve impaired renal function koşulu birlikte korunuyor mu?',
        'İstisna evrensel güvenlik veya koşulsuz doxycycline-BUN negatif/pozitif etiketine çevrilmiş mi?'] if case=='S07' else
        ['Fiziksel4 başlangıcı ve fiziksel5 devam bağlamı korunuyor mu?',
        'Not known ve frequency cannot be estimated anlamı açıkça korunuyor mu?',
        'Bilinmeyen sıklık sayısal olasılık, yaygınlık, sıfır risk veya kesin yokluk olarak yazılmış mı?',
        'Seçilen örneklerde may/usually/high doses/kidney problems gibi mevcut nitelemeler korunmuş mu?',
        'Prospektüsün acil başvuru/raporlama anlatımı, bağımsız kişisel tedavi tavsiyesine dönüşmüş mü?'])
    return {'scenario_id':case,'frozen_acceptance_criteria_tr':ctx['scenario']['acceptance_criteria_tr'],
        'required_review_questions_tr':checks,'generic_semantic_classifier':False,
        'S01_fixed_sentence_tests_used':False,'source_ID_is_semantic_success':False,
        'technical_validation':'JSON/schema, primary ID, dependency closure, scope/kind, three-source coverage',
        'agent_review':'Read exact returned claims against exact quotes; record omissions/contradictions.',
        'human_review':'PENDING until separately attributed decision event; no auto release',
        'refusal_policy':{'complete_readable_sources':True,'task_allowed':True,'eligible_model_refusal_codes':[],
            'refused_schema_branch_is_for_recording_not_success':True,
            'host_stops_before_API':['MISSING_CONTEXT','SOURCE_HASH_FAILURE','CONTEXT_BUDGET','BUDGET_LIMIT'],
            'native_API_refusal':'record separately, not JSON or semantic success'}}


def request(case):
    ctx,payload,_,_=context(case)
    specific=ROOT/f'docs/prompts/WP12_OPENAI_{case}_INSTRUCTIONS_v2.txt'
    return {'model':'gpt-5.4-mini','instructions':SYSTEM.read_text(encoding='utf-8')+'\n'+specific.read_text(encoding='utf-8'),
        'input':[{'role':'user','content':[{'type':'input_text','text':old.c.dump(payload)}]}],
        'text':{'format':{'type':'json_schema','name':f'wp12_{case.lower()}_source_adapter_v2','strict':True,'schema':schema(case)}},
        'reasoning':{'effort':'none'},'max_output_tokens':1200,'store':False,'stream':False,'background':False,
        'tools':[],'tool_choice':'none','service_tier':'default','truncation':'disabled'}


def assess(response,case):
    result={'scenario_id':case,'model':response.get('model'),'completion_status':response.get('status'),
        'schema_status':'NOT_EVALUABLE','application_status':'NOT_EVALUABLE','semantic_success':None,
        'agent_source_review':'PENDING','Turkish_quality':'PENDING','human_review':'PENDING','automatic_release':False,
        'semantic_review_plan':semantic_plan(case)}
    if response.get('status')!='completed':return {**result,'status':'INCOMPLETE_OR_FAILED_NO_RETRY'}
    if response.get('model') not in {'gpt-5.4-mini','gpt-5.4-mini-2026-03-17'}:
        return {**result,'status':'UNEXPECTED_MODEL_STOP'}
    parts=[c for m in response.get('output',[]) if m.get('type')=='message' for c in m.get('content',[])]
    if any(c.get('type')=='refusal' for c in parts):return {**result,'status':'API_NATIVE_REFUSAL_PENDING_REVIEW'}
    texts=[c['text'] for c in parts if c.get('type')=='output_text' and isinstance(c.get('text'),str)]
    if len(texts)!=1:return {**result,'status':'MISSING_OR_MULTIPLE_OUTPUT_TEXTS'}
    from wp12_openai_client import parse_json
    try:
        parsed=parse_json(texts[0]);Draft202012Validator(schema(case)).validate(parsed)
    except Exception:return {**result,'schema_status':'FAIL','status':'JSON_SCHEMA_FAIL_NO_RETRY'}
    result.update(schema_status='PASS',parsed_json=parsed)
    value=parsed['result']
    if value['status']=='refused':return {**result,'application_status':'FAIL_REFUSAL_NOT_SUPPORTED_BY_FROZEN_SOURCES',
        'status':'MODEL_REFUSAL_RECORDED_PENDING_REVIEW','refusal_code':value['refusal_code']}
    ctx,_,_,_=context(case)
    adapted=deepcopy(value);adapted.pop('language');adapted['schema_version']='WP12-local-llm-candidate-v1'
    try:
        validate_candidate(adapted,allowed_ids=ctx['scenario']['evidence_ids'],bundle=ctx['bundle'],annotations=ctx['annotations'])
        primaries=[x['evidence_ids'][0] for x in adapted['items']]
        if len(primaries)!=len(set(primaries)) or set(primaries)!=set(ctx['scenario']['evidence_ids']):
            raise ValueError('MISSING_OR_DUPLICATE_PRIMARY_SOURCE_COVERAGE')
        envelope=build_review_envelope(adapted,allowed_ids=ctx['scenario']['evidence_ids'],bundle=ctx['bundle'],annotations=ctx['annotations'])
    except ValueError:return {**result,'application_status':'FAIL','status':'SOURCE_APPLICATION_FAIL_NO_RETRY'}
    return {**result,'application_status':'PASS','status':'STRUCTURE_VALID_PENDING_AGENT_AND_HUMAN_REVIEW',
        'trusted_envelope':envelope,
        'language_hints':[old.v.language_screen(x['explanation_tr']) for x in value['items']],
        'language_hints_are_not_quality_approval':True}
