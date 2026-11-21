"""Tek gerçek S07 kaydının salt okunur denetimi; ağ/key/LLM çağırmaz."""
from pathlib import Path
from decimal import Decimal
import hashlib
from jsonschema import Draft202012Validator
import wp12_openai_scenarios_v2 as scenario
import wp12_openai_pilot_budget_v2 as budget
from wp12_api_security import public_sha,is_private_path
from wp12_pilot import get_engine
from wp12_openai_client import parse_json

ROOT=scenario.ROOT
RUN=ROOT/'reports/qa/WP12/openai_S07_user_runs_v2/20261108_173049_106b5d49c4f64383ad0b59cd7fd50e0e'
QA=ROOT/'reports/qa/WP12/openai_S07_actual_review_v1'
FIG=ROOT/'reports/figures/WP12/openai_S07_actual_review_v1'
PDF=ROOT/'data/user_pdfs/050641Orig1s032lbl.pdf'


def read(path):return scenario.old.c.read(path)


def model_message(raw):
    chunks=[c for m in raw['output'] if m.get('type')=='message' for c in m.get('content',[]) if c.get('type')=='output_text']
    if len(chunks)!=1:raise ValueError('ONE_OUTPUT_TEXT_REQUIRED')
    return chunks[0]['text']


def inspect():
    manifest=read(RUN/'file_hashes.json')
    if any(Path(name).name!=name or is_private_path(name) for name in manifest):raise ValueError('PUBLIC_MANIFEST_REQUIRED')
    verified={name:public_sha(RUN/name)==digest for name,digest in manifest.items()}
    raw=read(RUN/'inference_response_raw.json');record=read(RUN/'run_record.json')
    value=read(RUN/'validated_JSON.json');request=read(RUN/'source_request.json');sources=read(RUN/'source_provenance.json')
    Draft202012Validator(request['text']['format']['schema']).validate(value)
    assessment=scenario.assess(raw,'S07');saved=read(RUN/'technical_and_review_gates.json')
    ctx,payload,_,_=scenario.context('S07');bundle=ctx['bundle'];docid=sources['sources'][0]['document_id']
    doc=next(x for x in bundle['documents'] if x['document_id']==docid)
    extraction=next(x for x in bundle['extraction_runs'] if x['document_id']==docid)
    engine=get_engine();page_checks=[];slice_checks=[]
    with engine.open(str(PDF)) as pdf:
        n_pages=len(pdf);texts={}
        for number in sorted({s['physical_page'] for s in sources['sources']}):
            fresh=pdf[number-1].get_text('text',sort=False,flags=extraction['extractor_options']['flags']);texts[number]=fresh
            old_page=next(p for p in bundle['pages'] if p['document_id']==docid and p['page_number']==number)
            page_checks.append({'physical_page':number,'full_text_matches_frozen':fresh==old_page['text'],'text_codepoints':len(fresh)})
        for s in sources['sources']:
            slice_checks.append({'quote_id':s['quote_id'],'physical_page':s['physical_page'],
                'slice_matches':texts[s['physical_page']][s['char_start']:s['char_end']]==s['quote'],
                'quote_hash_matches':hashlib.sha256(s['quote'].encode()).hexdigest()==s['quote_sha256']})
    policy=read(budget.POLICY);usage=raw['usage'];prices=policy['prices_per_million_USD']
    inp=usage['input_tokens'];cached=usage['input_tokens_details']['cached_tokens'];out=usage['output_tokens']
    reason=usage['output_tokens_details']['reasoning_tokens']
    input_cost=Decimal(inp-cached)*Decimal(prices['input'])/1000000
    cached_cost=Decimal(cached)*Decimal(prices['cached_input'])/1000000
    output_cost=Decimal(out)*Decimal(prices['output'])/1000000;cost=input_cost+cached_cost+output_cost
    saved_cost=read(RUN/'usage_and_token_cost.json');count=read(RUN/'input_token_count_response_raw.json')
    preflight=read(RUN/'cost_preflight.json');components=read(RUN/'prompt_components_sha256.json')
    expected_components={'instructions_sha256':hashlib.sha256(request['instructions'].encode()).hexdigest(),
        'input_text_sha256':hashlib.sha256(request['input'][0]['content'][0]['text'].encode()).hexdigest(),
        'schema_sha256':hashlib.sha256(scenario.old.c.dump(request['text']['format']['schema']).encode()).hexdigest(),
        'quote_sha256':[x['quote_sha256'] for x in payload['sources']]}
    scope=read(RUN/'execution_scope.json');aggregate=budget.aggregate(policy)
    stages=[{'stage':name,**read(RUN/(name+'_HTTP_metadata.json'))} for name in ['model_access','input_token_count','inference']]
    prior_match={p:public_sha(ROOT/p)==h for p,h in policy['prior_public_records_sha256'].items()}
    input_match={p:public_sha(ROOT/p)==h for p,h in policy['immutable_public_inputs_sha256'].items()}
    envelope=assessment['trusted_envelope']
    checks={
        'raw_run_hashes_match':all(verified.values()),
        'run_inventory_matches_manifest':{p.name for p in RUN.iterdir() if p.is_file()}==set(manifest)|{'file_hashes.json'},
        'raw_response_hash_matches_record':public_sha(RUN/'inference_response_raw.json')==record['raw_response_sha256'],
        'request_and_source_equal_frozen_S07':request==scenario.request('S07') and sources==payload,
        'prompt_components_and_execution_scope_hash_match':components==expected_components and scope['source_request_sha256']==public_sha(RUN/'source_request.json'),
        'raw_JSON_matches_validated_and_independent_assessment':parse_json(model_message(raw))==value and assessment==saved,
        'schema_and_source_application_pass':assessment['schema_status']=='PASS' and assessment['application_status']=='PASS',
        'expected_completed_model':raw['model']=='gpt-5.4-mini-2026-03-17' and raw['status']=='completed' and raw.get('error') is None and raw.get('incomplete_details') is None,
        'three_HTTP_200_single_inference':[x['HTTP_status'] for x in stages]==[200,200,200] and record['http_attempts']==3 and record['inference_attempts']==1 and record['automatic_retry'] is False,
        'raw_PDF_identity_and_page_count':public_sha(PDF)==doc['raw_sha256'] and n_pages==doc['page_count'],
        'PDF_full_pages_ranges_and_hashes':all(x['full_text_matches_frozen'] for x in page_checks) and all(x['slice_matches'] and x['quote_hash_matches'] for x in slice_checks),
        'same_original_extractor':engine.VersionBind==extraction['extractor_version'],
        'token_usage_matches_preflight_and_caps':count['input_tokens']==inp and inp<=policy['input_token_cap'] and out<=policy['max_output_tokens'] and reason<=out and usage['total_tokens']==inp+out,
        'independent_usage_cost_matches':cost==Decimal(saved_cost['actual_token_cost_USD'])==Decimal(record['usage_token_cost_USD']) and scenario.old.usage_cost(usage,policy)==saved_cost,
        'preflight_estimate_matches_frozen_policy':scenario.old.estimate_upper(count['input_tokens'],policy)==preflight,
        'all_prior_public_records_and_inputs_unchanged':all(prior_match.values()) and all(input_match.values()),
        'budget_9_HTTP_3_reservations_retained':aggregate==read(RUN/'aggregate_budget_after_run.json') and aggregate['HTTP_reservations_total']==9 and aggregate['inference_reservations_total']==3 and aggregate['within_limits'],
        'budget_v2_user_acceptance_recorded':scope['budget_v2_explicitly_accepted_in_user_command'] is True,
        'human_and_no_release_gate_preserved':record['human_review']=='PENDING' and record['automatic_release'] is False and assessment['semantic_success'] is None and assessment['human_review']=='PENDING',
        'no_GNN_or_tool_outputs':envelope['predicted_by_GNN']=={'status':'NOT_REQUESTED_IN_WP12','artifact_ref':None} and raw['tools']==[] and raw['service_tier']=='default',
        'S04_stays_execution_locked':policy['only_executable_scenario']=='S07' and scope['S04']=='LOCKED_NOT_RUN' and not list(budget.CONTROL.glob('S04_attempt*.json')),
        'previous_stop_and_current_single_attempt_retained':(budget.PRIOR_ROOTS[0]/'BILLING_OR_LIMIT_STOP.json').exists() and (budget.CONTROL/'S07_attempt_01.json').exists() and not (budget.CONTROL/'S07_attempt_02.json').exists()}
    s01=read(ROOT/'reports/qa/WP12/openai_S01_success_review_v1/independent_review.json')
    return {'status':'TECHNICAL_PASS_QUALITY_FLAGS_PENDING_HUMAN','checks':checks,
        'model':raw['model'],'response_id':raw['id'],'API_request_id':record['API_request_id'],
        'HTTP_status':record['HTTP_status'],'completion_status':raw['status'],'latency_HTTP_seconds':record['latency_seconds'],
        'usage':usage,'input_cost_USD':str(input_cost),'cached_cost_USD':str(cached_cost),'output_cost_USD':str(output_cost),
        'usage_token_cost_USD':str(cost),'known_completed_S01_plus_S07_token_cost_USD':str(Decimal(s01['usage_token_cost_USD'])+cost),
        'pilot_total_invoice_cost':'UNKNOWN_PRIOR_429_USAGE_AND_INVOICE_NOT_QUERIED','schema_status':'PASS','application_status':'PASS',
        'agent_semantic_method':'manual reading of this exact recorded S07; not a general semantic classifier',
        'S01_fixed_sentence_validator_used':False,'source_core_agent':'CLASS_SCOPE_AND_BOTH_EXCEPTION_CLAUSES_RETAINED_WITH_NOTES',
        'Turkish_quality_agent':'NOT_FULL_PASS_UNTRANSLATED_CRITICAL_CONDITION',
        'citation_granularity_agent':'ITEM2_CONTEXT_REFERENCE_REVIEW_NOTE_NOT_SCHEMA_FAILURE',
        'human_review':'PENDING','automatic_release':False,'false_refusal_observed':False,
        'unconditional_doxycycline_positive_or_negative_label_observed':False,
        'repeat_stability':'NOT_EVALUABLE_SINGLE_S07_RESPONSE','RAM_VRAM_telemetry':'NOT_COLLECTED',
        'raw_run_files_verified':len(verified),'prior_public_records_verified':len(prior_match),
        'source_PDF_sha256':doc['raw_sha256'],'source_PDF_page_count':n_pages,'page_checks':page_checks,'quote_checks':slice_checks,
        'exact_model_message':model_message(raw),'parsed_json':value,'aggregate_budget':aggregate,'stages':stages,
        'source_meaning_not_clinical_validation':True,'new_API_requests_during_review':0,
        'method_or_frozen_criteria_changed_after_result':False}


def agent_annotations(review):
    """Bu run/hash'e bağlı ajan okuma notları; kaynak/çıktı değiştirmez."""
    sources={x['quote_id']:x for x in scenario.context('S07')[1]['sources']}
    items=review['parsed_json']['result']['items']
    notes=[
        ('CORE_SUPPORTED_WITH_LANGUAGE_NOTE','tetracyclines sınıf adı İngilizce bırakılmış. BUN bildirimi ve dozla ilişkili olabileceği ifadesi sınıf kapsamında; doğrudan doxycycline kanıtı olmadığı belirtilmiş.'),
        ('CORE_CLASS_INTRO_SUPPORTED_CITATION_CONTEXT_NOTE','İlk sınıf gözlemi doğrudan alıntıyla destekli. Renal alt başlık/doxycycline yorumu tüm girdi bağlamında destekleniyor; yalnız cite edilen sınıf-giriş cümlesi bu sözcükleri içermiyor. Bu, mevcut teknik kuralı değiştiren bir FAIL değildir; item düzeyinde atıf ayrıntısı için ajan inceleme notudur.'),
        ('CORE_EXCEPTION_SUPPORTED_LANGUAGE_QUALITY_FLAG','May cause → yol açabilir; studies to date indicate → mevcut çalışmalara göre; doxycycline ve renal koşul korunmuş. Ancak impaired renal function çevrilmeden kalmış; tetracyclines de İngilizce. Tam Türkçe açıklama gereksinimi tam karşılanmıyor. Yeni klinik negatif/evrensel güvenlik iddiası gözlenmedi.')]
    rows=[]
    for index,(item,(status,note)) in enumerate(zip(items,notes),1):
        primary=sources[item['evidence_ids'][0]]
        rows.append({'item':index,'primary_quote_id':primary['quote_id'],'physical_page':primary['physical_page'],
            'scope':item['source_scope'],'kind':item['statement_kind'],'model_explanation_exact':item['explanation_tr'],
            'primary_quote_exact':primary['quote'],'all_cited_ids':item['evidence_ids'],
            'all_cited_quotes_exact':[sources[q]['quote'] for q in item['evidence_ids']],
            'source_qualifier_exact':primary['qualifier'],'agent_source_status':status,'agent_note_tr':note,
            'manual_review_bound_to_raw_sha256':public_sha(RUN/'inference_response_raw.json'),
            'human_decision':'PENDING','human_reviewer':None,'human_comment':None,'automatic_release':False})
    # Yalnız gözlenmiş dil sorununun span'ı; genel dil/semantik başarı sınıflayıcısı değildir.
    phrase='impaired renal function';position=items[2]['explanation_tr'].find(phrase)
    if position<0:raise ValueError('MANUAL_ANNOTATION_FOR_OBSERVED_RESPONSE_ONLY')
    return rows,{'item':3,'text_exact':phrase,'char_start':position,'char_end':position+len(phrase),
        'agent_explanatory_gloss_tr':'böbrek işlevi bozulmuş','gloss_is_not_modified_LLM_output':True,
        'status':'UNTRANSLATED_CLINICAL_CONDITION','not_a_general_language_classifier':True}
