"""WP12 yöntem v2 ÖNERİSİ: ağsız schema/prompt/kaynak/dil kontrolleri.

Gerçek inference istemcisi yoktur. Eski v1 modülleri/çıktıları değiştirilmez.
"""
import copy
import hashlib
import json
import re
from pathlib import Path
from jinja2 import Environment,StrictUndefined
from jsonschema import Draft202012Validator
import wp12_source_case as old
from wp12_llm_contract import validate_candidate,build_review_envelope
from wp12_vocab_counter import render_single_user

ROOT=old.ROOT
QA=ROOT/'reports/qa/WP12/method_correction_v2'
SCHEMA=ROOT/'docs/schemas/WP12_local_llm_candidate_v2_PROPOSED.schema.json'
SYSTEM=ROOT/'docs/prompts/WP12_SOURCE_EXPLANATION_SYSTEM_v2_PROPOSED.txt'
VERSION='WP12-local-llm-candidate-v2'


def generic_schema():
    """Tam object oneOf dalları: refused boş items, candidate>=1 ve null code."""
    s=copy.deepcopy(old.read(ROOT/'docs/schemas/WP12_local_llm_candidate_v1.schema.json'))
    props=s['properties'];props['schema_version']['const']=VERSION
    props['language']={'const':'tr'}
    required=[*s['required'],'language']
    branches=[]
    for status in ['candidate','refused']:
        p=copy.deepcopy(props);p['status']={'const':status}
        if status=='candidate':
            p['refusal_code']={'const':None};p['items']['minItems']=1
        else:
            p['refusal_code']={'enum':[x for x in props['refusal_code']['enum'] if x is not None]}
            p['items']={'type':'array','maxItems':0}
        branches.append({'type':'object','additionalProperties':False,'required':required,'properties':p})
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','oneOf':branches}


def verified_S01_context():
    ctx=old.context('S01')
    expected=old.read(old.QA/'package/context.json')
    if {'scenario':ctx['scenario'],'sources':ctx['sources']}!=expected:
        raise ValueError('FROZEN_S01_CONTEXT_CHANGED')
    # Bu kanıt seti dışında ret uygunluğu sessizce genelleştirilmez.
    if len(ctx['sources'])!=2 or {(x['physical_page'],x['kind']) for x in ctx['sources']}!={(1,'identity'),(6,'formulation')}:
        raise ValueError('S01_SOURCE_PROFILE_CHANGED')
    return ctx


def S01_refusal_policy(ctx=None):
    ctx=verified_S01_context() if ctx is None else ctx
    canonical=verified_S01_context()
    if ctx['sources']!=canonical['sources'] or ctx['scenario']!=canonical['scenario']:
        raise ValueError('MISSING_OR_CHANGED_CONTEXT_NO_GENERATION')
    return {'scenario_id':'S01','verified_readable_source_count':2,'required_context_complete':True,
        'requested_task':'product_identity_and_formulation_transcription',
        'model_allowed_refusal_codes':[],
        'ineligible_refusal_reasons':{'NO_SOURCE':'İki kaynak alıntısı mevcut.',
            'IMAGE_TEXT_UNAVAILABLE':'İstenen kimlik/formülasyon iki tam metin katmanı alıntısında mevcut.',
            'MISSING_CONTEXT':'Dondurulmuş zorunlu bağlam tam.',
            'FORBIDDEN_TASK':'S01 kaynak aktarımıdır, skor/etiket görevi değil.',
            'CONTEXT_BUDGET':'Gerçek tokenizer kapısı model çağrısından önce host tarafından değerlendirilir.',
            'UNCERTAIN_EVIDENCE':'Bu S01 kaynak profilinde belirsiz/çatışan kanıt işareti yok; modelin salt özgüveni kaynak kanıtı değildir.'},
        'host_refusal_before_request':['CONTEXT_BUDGET','SOURCE_HASH_OR_CONTEXT_FAILURE','MEMORY_OR_API_GATE'],
        'forcing_truth_guarantee':False,'invalid_or_low_quality_candidate_is_failure_not_repaired':True}


def case_schema(ctx=None):
    ctx=verified_S01_context() if ctx is None else ctx
    S01_refusal_policy(ctx)
    # Yalnız bu hazır S01 profilinde gerekçesiz ret dalı üretim şemasına girmez.
    candidate=copy.deepcopy(generic_schema()['oneOf'][0])
    item_variants=[]
    for src in ctx['sources']:
        item=copy.deepcopy(candidate['properties']['items']['items'])
        item['properties']['source_scope']={'const':src['scope']}
        item['properties']['statement_kind']={'const':src['kind']}
        item['properties']['evidence_ids']={'type':'array','minItems':1,'maxItems':1,
            'items':{'const':src['quote_id']}}
        item_variants.append(item)
    candidate['properties']['items']['items']={'oneOf':item_variants}
    candidate['properties']['items']['maxItems']=2
    candidate['$schema']='https://json-schema.org/draft/2020-12/schema'
    return candidate


def request_for_S01():
    ctx=verified_S01_context();schema=case_schema(ctx)
    system=SYSTEM.read_text(encoding='utf-8')
    # Büyük biçimsel şema grammar alanındadır; user prompt'ta kaynaklar+görev bulunur.
    # Kaynak metni/ID, soru ve frozen kabul ölçütü değiştirilmez.
    data={'scenario_id':'S01','question_tr':ctx['scenario']['question_tr'],
        'acceptance_criteria_tr':ctx['scenario']['acceptance_criteria_tr'],'sources':ctx['sources']}
    req=copy.deepcopy(old.request_for(ctx))
    req['messages']=[{'role':'system','content':system},{'role':'user','content':old.dump(data)}]
    req['format']=schema
    return req


def render_request(req,template):
    if [x['role'] for x in req['messages']]!=['system','user']:raise ValueError('PINNED_TWO_MESSAGE_SHAPE_REQUIRED')
    def refuse(message):raise ValueError(message)
    return Environment(undefined=StrictUndefined).from_string(template).render(messages=req['messages'],
        bos_token='<bos>',eos_token='<eos>',add_generation_prompt=True,raise_exception=refuse)


def token_proof(req,counter,template):
    rendered=render_request(req,template);tokens=counter.tokens(rendered,False)
    # Gemma3 yerel şablonunun system+user birleştirmesini bağımsız yolla denetle.
    equivalent=req['messages'][0]['content']+'\n\n'+req['messages'][1]['content'].strip()
    folded=render_single_user(equivalent,template)
    if rendered!=folded:raise ValueError('SYSTEM_RENDER_ALIGNMENT_FAILED')
    return {'method':'same GGUF/native vocabulary-only + actual system/user chat template',
        'input_token_count':len(tokens),'input_token_limit':1536,'output_reserve':384,'safety_reserve':128,
        'context':2048,'admitted':len(tokens)<=1536,'status':'TOKEN_BUDGET_PASS' if len(tokens)<=1536 else 'CONTEXT_BUDGET',
        'silent_truncation':False,'rendered_prompt':rendered,
        'rendered_prompt_sha256':hashlib.sha256(rendered.encode()).hexdigest(),
        'token_ids_sha256':hashlib.sha256(old.dump(tokens).encode()).hexdigest(),
        'native_version':counter.version,'system_fold_equivalence_verified':True,
        'grammar_schema_in_format_not_hidden_prompt_text':True,'weights_loaded':False,'inference':False,
        'real_server_prompt_eval_count_verification':'PENDING_FUTURE_USER_RUN'}


EN_MARKERS=frozenset('the provided text does not contain information about product form formulation this contains available'.split())
TR_MARKERS=frozenset('bu ve bir olarak içerir icerir belirtilir belirtilmiştir belirtilmistir bulunur adlı adli olan kaplı kapli tabletlerdir sunulur'.split())


def language_screen(text):
    """Sınırlı İngilizce uyarısı; Türkçe doğruluğu ya da semantiği kanıtlamaz."""
    words=set(re.findall(r'[^\W\d_]+',text.casefold(),flags=re.UNICODE))
    en=sorted(words&EN_MARKERS);tr=sorted(words&TR_MARKERS)
    return {'status':'OBVIOUS_NON_TURKISH' if len(en)>=3 and not tr else 'PENDING_HUMAN_LANGUAGE_REVIEW',
        'English_markers':en,'Turkish_markers':tr,'language_declared_tr_is_proof':False,
        'human_required':True,'automatic_success':False}


def inspect_candidate(value,ctx=None):
    ctx=verified_S01_context() if ctx is None else ctx
    result={'schema_valid':False,'source_contract_valid':False,'semantic_success':None,
        'automatic_release':False,'human_review':'PENDING','method':VERSION,'errors':[]}
    errors=list(Draft202012Validator(case_schema(ctx)).iter_errors(value))
    result['schema_valid']=not errors
    if errors:
        result['errors']=[e.message for e in errors];return result
    # V2 dil/meta alanı v1 trusted citation işlevine yalnız RAM kopyasında adapte edilir.
    adapted=copy.deepcopy(value);adapted.pop('language');adapted['schema_version']='WP12-local-llm-candidate-v1'
    try:
        validate_candidate(adapted,allowed_ids=ctx['scenario']['evidence_ids'],bundle=ctx['bundle'],annotations=ctx['annotations'])
        result['source_contract_valid']=True
        result['trusted_envelope']=build_review_envelope(adapted,allowed_ids=ctx['scenario']['evidence_ids'],
            bundle=ctx['bundle'],annotations=ctx['annotations'])
        result['language_checks']=[language_screen(x['explanation_tr']) for x in value['items']]
        if any(x['status']=='OBVIOUS_NON_TURKISH' for x in result['language_checks']):
            result['errors'].append('OBVIOUS_NON_TURKISH')
        covered={x['statement_kind'] for x in value['items']}
        result['task_coverage']='BOTH_SOURCE_PURPOSES_PRESENT' if covered=={'identity','formulation'} else 'TASK_COVERAGE_INCOMPLETE'
        if result['task_coverage']=='TASK_COVERAGE_INCOMPLETE':result['errors'].append('TASK_COVERAGE_INCOMPLETE')
    except ValueError as e:result['errors'].append(str(e))
    result['status']='REJECTED_OR_INCOMPLETE' if result['errors'] else 'PENDING_HUMAN_SOURCE_AND_LANGUAGE_REVIEW'
    return result
