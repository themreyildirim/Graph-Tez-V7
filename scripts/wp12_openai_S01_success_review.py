"""Gerçek kaydedilmiş API yanıtını inceler; ağ/key/model çalıştırma yoktur."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import wp12_openai_adapter as a
import wp12_openai_corrected_account_v1 as attempt
from wp12_api_security import public_sha,is_private_path
from wp12_pilot import get_engine
from jsonschema import Draft202012Validator

ROOT=a.c.ROOT
RUN=ROOT/'reports/qa/WP12/openai_corrected_account_user_runs_v1/20261108_164416_6fd67845f94e4074818e71b22470cf22'
QA=ROOT/'reports/qa/WP12/openai_S01_success_review_v1'
FIG=ROOT/'reports/figures/WP12/openai_S01_success_review_v1'
PDF=ROOT/'data/user_pdfs/pil.502.pdf'


def read(path):return a.c.read(path)


def output_text(raw):
    parts=[c for m in raw['output'] if m.get('type')=='message' for c in m['content'] if c.get('type')=='output_text']
    if len(parts)!=1:raise ValueError('EXACT_SINGLE_MESSAGE_REQUIRED')
    return parts[0]['text']


def inspect():
    files=read(RUN/'file_hashes.json')
    if any(Path(p).name!=p or is_private_path(p) for p in files):raise ValueError('INVALID_PUBLIC_MANIFEST')
    file_checks={p:public_sha(RUN/p)==digest for p,digest in files.items()}
    raw=read(RUN/'inference_response_raw.json');saved=read(RUN/'validated_JSON.json')
    record=read(RUN/'run_record.json');request=read(RUN/'source_request.json')
    source=read(RUN/'source_provenance.json');canonical=a.source_payload()
    derived=a.assess_response(raw);validation=read(RUN/'structural_and_language_review.json')
    Draft202012Validator(request['text']['format']['schema']).validate(saved)
    Draft202012Validator(a.v.case_schema()).validate(saved['result'])
    ctx=a.v.verified_S01_context();bundle=ctx['bundle']
    docid=source['sources'][0]['document_id'];doc=next(d for d in bundle['documents'] if d['document_id']==docid)
    extraction=next(x for x in bundle['extraction_runs'] if x['document_id']==docid)
    engine=get_engine();pdf_checks=[]
    with engine.open(str(PDF)) as pdf:
        count=len(pdf)
        for s in source['sources']:
            page=next(x for x in bundle['pages'] if x['document_id']==docid and x['page_number']==s['physical_page'])
            fresh=pdf[s['physical_page']-1].get_text('text',sort=False,flags=extraction['extractor_options']['flags'])
            pdf_checks.append({'physical_page':s['physical_page'],'quote_id':s['quote_id'],
                'full_page_text_matches_stored':fresh==page['text'],
                'fresh_page_range_equals_quote':fresh[s['char_start']:s['char_end']]==s['quote'],
                'quote_sha256_matches':hashlib.sha256(s['quote'].encode('utf-8')).hexdigest()==s['quote_sha256'],
                'full_page_codepoints':len(fresh)})
    usage=raw['usage'];inp=usage['input_tokens'];cached=usage['input_tokens_details']['cached_tokens'];out=usage['output_tokens']
    reason=usage['output_tokens_details']['reasoning_tokens'];policy=read(a.POLICY);prices=policy['prices_per_million_USD']
    input_cost=Decimal(inp-cached)*Decimal(prices['input'])/1000000
    cached_cost=Decimal(cached)*Decimal(prices['cached_input'])/1000000
    output_cost=Decimal(out)*Decimal(prices['output'])/1000000
    cost=input_cost+cached_cost+output_cost
    billed=read(RUN/'usage_and_token_cost.json');counted=read(RUN/'input_token_count_response_raw.json')
    transport=read(RUN/'actual_transport_attempts.json');budget=attempt.aggregate_budget(policy)
    envelope=derived['validation']['trusted_envelope']
    prior=ROOT/'reports/qa/WP12/openai_api_user_runs_v1/20261108_162120_31419480b91f4396a7a018152c5c5f7b'
    stages=[{'stage':s,**read(RUN/(s+'_HTTP_metadata.json'))} for s in ['model_access','input_token_count','inference']]
    components=read(RUN/'prompt_components_sha256.json')
    expected_components={
        'instructions_sha256':hashlib.sha256(request['instructions'].encode()).hexdigest(),
        'user_content_sha256':hashlib.sha256(request['input'][0]['content'][0]['text'].encode()).hexdigest(),
        'JSON_schema_sha256':hashlib.sha256(a.c.dump(request['text']['format']['schema']).encode()).hexdigest(),
        'source_quote_sha256':[s['quote_sha256'] for s in source['sources']]}
    checks={
        'run_hashes_all_match':all(file_checks.values()),
        'run_inventory_matches_manifest':{p.name for p in RUN.iterdir() if p.is_file()}==set(files)|{'file_hashes.json'},
        'record_raw_and_prompt_hashes_match':record['raw_response_sha256']==public_sha(RUN/'inference_response_raw.json') and
            record['source_request_sha256']==public_sha(RUN/'source_request.json') and components==expected_components,
        'same_source_request_as_first_failed_account_byte_for_byte':public_sha(RUN/'source_request.json')==public_sha(prior/'source_request.json'),
        'frozen_request_and_source_unchanged':request==a.build_request() and source==canonical,
        'all_HTTP_200':[s['HTTP_status'] for s in stages]==[200,200,200],
        'completed_expected_model':raw['status']=='completed' and raw['model']=='gpt-5.4-mini-2026-03-17' and raw.get('error') is None and raw.get('incomplete_details') is None,
        'strict_parsed_raw_matches_saved_JSON':attempt.original.parse_json(output_text(raw))==saved,
        'independent_validator_matches_saved_review':derived==validation,
        'no_tools_or_GNN_prediction':raw['tools']==[] and raw['service_tier']=='default' and
            envelope['predicted_by_GNN']=={'status':'NOT_REQUESTED_IN_WP12','artifact_ref':None},
        'raw_PDF_identity_and_page_count':public_sha(PDF)==doc['raw_sha256'] and count==doc['page_count'],
        'fresh_PDF_page_range_and_quote_hashes':all(all(p[k] for k in ['full_page_text_matches_stored','fresh_page_range_equals_quote','quote_sha256_matches']) for p in pdf_checks),
        'extractor_version_matches_original':engine.VersionBind==extraction['extractor_version'],
        'actual_usage_matches_server_preflight':inp==counted['input_tokens'],
        'usage_within_input_output_caps':inp<=policy['input_token_cap'] and out<=policy['max_output_tokens'] and usage['total_tokens']==inp+out and reason<=out,
        'independent_Decimal_cost_matches_saved':cost==Decimal(billed['actual_token_cost_USD'])==Decimal(record['estimated_actual_token_cost_USD']) and
            a.usage_cost(usage,policy)==billed,
        'one_inference_three_HTTP_no_retry':record['inference_attempts']==1 and record['http_attempts']==3 and transport['inference_transport_attempts']==1 and
            len(transport['HTTP_transport_attempts'])==3 and record['automatic_retry'] is False,
        'both_accounts_budget_retained':budget==read(RUN/'aggregate_budget_after_run.json') and budget['within_original_pilot_caps'] and
            budget['HTTP_attempt_reservations_all_accounts']==6 and budget['inference_reservations_all_accounts']==2,
        'human_and_release_gate_preserved':record['human_review']=='PENDING' and record['automatic_release'] is False and
            envelope['semantic_review']=={'status':'NOT_PERFORMED','auto_release':False},
        'prior_billing_stop_and_new_single_attempt_lock_retained':(attempt.PRIOR_CONTROL/'BILLING_OR_LIMIT_STOP.json').exists() and
            (attempt.CONTROL/'S01_attempt_01.json').exists() and not (attempt.CONTROL/'S01_attempt_02.json').exists()}
    return {'status':'TECHNICAL_PASS_AGENT_SOURCE_SUPPORTED_PENDING_HUMAN_REVIEW','checks':checks,
        'model':raw['model'],'API_request_id':record['API_request_id'],'response_id':raw['id'],
        'HTTP_status':record['HTTP_status'],'completion_status':raw['status'],'usage':usage,
        'input_cost_USD':str(input_cost),'cached_cost_USD':str(cached_cost),'output_cost_USD':str(output_cost),
        'usage_token_cost_USD':str(cost),'price_source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini',
        'invoice_including_taxes':'NOT_QUERIED','earlier_failed_request_actual_cost':'UNKNOWN_NO_USAGE',
        'latency_HTTP_seconds':record['latency_seconds'],'input_token_preflight':counted['input_tokens'],
        'schema_status':'PASS','application_status':'PASS','source_faithfulness_agent':'SUPPORTED_FOR_TWO_RETURNED_ITEMS',
        'Turkish_quality_agent':'TURKISH_SUPPORTED_SOURCE_PROPER_NAMES_RETAINED',
        'source_omissions':['Macrolide sınıf ifadesi özetlenmedi.','Ambalaj adetleri özetlenmedi.'],
        'omissions_interpretation':'Kısa S01 özeti; kaynakla çelişki değil. Tam alıntı çevirisi veya tüm alanların kapsandığı iddia edilmez.',
        'uncertainty_review':'İki seçilmiş alıntının qualifier alanı boş; ek kesinlik, sıklık, risk veya eşdeğerlik iddiası gözlenmedi.',
        'false_refusal_observed':False,'unsupported_claim_observed_in_returned_items':False,
        'human_review':'PENDING','automatic_release':False,'repeat_stability':'NOT_EVALUABLE_SINGLE_COMPLETED_RESPONSE',
        'RAM_VRAM_telemetry':'NOT_COLLECTED_FOR_API_RUN','new_API_requests_during_review':0,
        'raw_files_verified':len(file_checks),'source_page_checks':pdf_checks,'PDF_sha256':doc['raw_sha256'],
        'PDF_page_count':count,'extractor_version':engine.VersionBind,'aggregate_reservations':budget,
        'exact_model_message':output_text(raw),'parsed_json':saved,'stages':stages,
        'semantic_assessment_author':'Codex agent; not independent human/clinical validation'}


def item_reviews(review):
    """Bu tek gerçek yanıt için açık ajan okuması; otomatik semantik sınıflayıcı değil."""
    sources={x['quote_id']:x for x in a.source_payload()['sources']}
    expected=['İlacın adı Erythromycin Tablets BP 250 mg’dir ve etkin madde eritromisindir.',
        'Erythromycin Tablets kırmızı renkli, yuvarlak, bikonveks ve enterik kaplı tabletlerdir.']
    items=review['parsed_json']['result']['items']
    if [x['explanation_tr'] for x in items]!=expected:raise ValueError('THIS_AGENT_REVIEW_APPLIES_TO_EXACT_OBSERVED_RESPONSE_ONLY')
    rows=[]
    for i,item in enumerate(items,1):
        s=sources[item['evidence_ids'][0]]
        rows.append({'item':i,'statement_kind':item['statement_kind'],'physical_page':s['physical_page'],
            'document_id':s['document_id'],'quote_id':s['quote_id'],'char_start':s['char_start'],'char_end':s['char_end'],
            'quote_sha256':s['quote_sha256'],'source_quote_exact':s['quote'],'model_explanation_exact':item['explanation_tr'],
            'agent_source_review':'SUPPORTED_PENDING_HUMAN','agent_Turkish_review':'TURKISH_SUPPORTED',
            'agent_note_tr':'Tam ürün adı ve etkin madde kaynakta mevcut; macrolide sınıfı aktarılmamış.' if i==1 else
                'Kırmızı/yuvarlak/bikonveks/enterik kaplı özellikler kaynakta birebir; ambalaj adetleri aktarılmamış.',
            'human_decision':'PENDING','human_reviewer':None,'human_comment':None,'auto_release':False})
    return rows
