"""WP12 bulut pilotunu OFFLINE hazırlar. API/key değeri/log başlığı içermez."""
from datetime import datetime,timezone,timedelta
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import wp12_source_case as c
import wp12_openai_adapter as a
from wp12_api_security import public_sha,key_available,is_private_path
from jsonschema import Draft202012Validator


def main():
    req=a.build_request();Draft202012Validator.check_schema(req['text']['format']['schema'])
    c.save_new(a.QA/'S01_Responses_request_NOT_SENT.json',req)
    c.save_new(a.QA/'S01_Structured_Outputs_schema_adapter_v1.json',req['text']['format']['schema'])
    c.save_new(a.QA/'outbound_disclosure_S01.json',{'status':'NOT_SENT_WAIT_USER_APPROVAL',
        'provider':'OpenAI','model':a.MODEL,'scenarios':['S01'],'quote_count':2,'source_chars':537,
        'exact_source_payload':a.source_payload(),'prompt_and_request_sha256':public_sha(a.QA/'S01_Responses_request_NOT_SENT.json'),
        'transmission_plan':['POST /v1/responses/input_tokens receives instructions/schema/selected quotes',
            'POST /v1/responses receives same sources only after cost gate'],
        'no_full_PDF_or_project_upload':True,'authentication_material_not_recorded':True})
    frozen=c.read(c.ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')
    selected=[next(x for x in frozen if x['scenario_id']==s) for s in ['S01','S04','S07','S17']]
    c.save_new(a.QA/'small_evaluation_plan_NOT_AUTHORIZED.json',{'status':'ONLY_S01_EXECUTOR_PREPARED_OTHERS_REQUIRE_USER_RESULT_REVIEW',
        'selection_before_cloud_results':True,'max_total_HTTP_requests_including_metadata_and_count':10,
        'planned_max_inference_requests':4,'HTTP_plan_if_all_preflights_pass':{'model_access_GET':1,'token_count_POST':4,'inference_POST':4,'total':9},
        'why_fewer_than10_inferences':'Conservative interpretation counts every HTTP request against10; no hidden preflight calls.',
        'case_types':['identity/formulation','unknown frequency/context','class/BUN exception','forbidden score/label refusal'],
        'frozen_scenarios_unchanged':selected,'repeat_or_best_output_selection':False})
    inputs=['AGENTS.md','docs/plan/ROADMAP_V7.md','docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md',
        'docs/plan/WP12_DOCUMENT_DATA_CONTRACT_v1.md','reports/qa/WP12/llm_design_v1/frozen_scenarios.json',
        'reports/qa/WP12/llm_design_v1/acceptance_criteria.csv','reports/qa/WP12/pilot_v1/source_evidence_bundle.json',
        'reports/qa/WP12/pilot_v1/source_context_annotations.json','reports/qa/WP12/pilot_v1/drug_identity_review.json',
        'docs/prompts/WP12_SOURCE_EXPLANATION_SYSTEM_v2_PROPOSED.txt','scripts/wp12_method_v2.py',
        'scripts/wp12_source_case.py','scripts/wp12_llm_contract.py','scripts/wp12_api_security.py',
        'scripts/wp12_openai_adapter.py','scripts/wp12_openai_client.py','.gitignore',
        'reports/qa/WP12/openai_api_pilot_v1/S01_Responses_request_NOT_SENT.json',
        'reports/qa/WP12/openai_api_pilot_v1/S01_Structured_Outputs_schema_adapter_v1.json']
    now=datetime.now(timezone.utc)
    policy={'version':'WP12-OpenAI-API-pilot-v1','model':a.MODEL,'cloud_experiment_separate_from_local':True,
        'status':'WAIT_USER_APPROVAL_BEFORE_ANY_AUTHENTICATED_API_CALL','only_executable_scenario':'S01',
        'max_inference_requests':10,'max_total_HTTP_requests':10,'current_executor_max_inference':1,
        'pilot_target_USD':'0.25','operational_reservation_ceiling_USD':'0.24',
        'reservation_per_inference_USD':'0.02','reservation_per_HTTP_USD':'0.001','fixed_reservation_max_USD':'0.21',
        'prices_per_million_USD':{'input':'0.75','cached_input':'0.075','output':'4.50'},
        'pricing_verified_at_UTC':now.isoformat(),'pricing_valid_until_UTC':(now+timedelta(hours=24)).isoformat(),
        'pricing_source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini',
        'structured_outputs_source':'https://developers.openai.com/api/docs/guides/structured-outputs',
        'token_count_source':'https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count',
        'account_model_access':'PENDING_NORMAL_USER_GET_MODEL','adapter_runtime_acceptance':'PENDING_TOKEN_COUNT_AND_FIRST_RESPONSE',
        'input_token_cap':6000,'max_output_tokens':1200,'reasoning_effort':'none','cost_margin_multiplier':'1.20',
        'no_cache_discount_in_preflight':True,'automatic_retry':False,'Batch_or_paid_tools':False,
        'further_scenarios_require_user_review_of_first_result':True,'new_training':False,'automatic_publication':False,'WP13':False,
        'immutable_public_inputs_sha256':{p:public_sha(c.ROOT/p) for p in inputs}}
    c.save_new(a.POLICY,policy)
    script=c.ROOT/'scripts/WP12_OpenAI_UserSingleCase_v1.ps1'
    text=f'''# Normal kullanici PowerShell'i; ilk S01 icin kullanici onayi sonrasi tek komut.
[CmdletBinding()]
param([switch]$RunFirstCase)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$policy=Join-Path $projectRoot 'configs/WP12_OPENAI_API_PILOT_v1.json'
if ((Get-FileHash -LiteralPath $policy -Algorithm SHA256).Hash.ToLowerInvariant() -cne '{public_sha(a.POLICY)}') {{ throw 'POLICY_CHANGED_SAFE_STOP' }}
$python='C:\\Users\\emrey\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
$entry=Join-Path $PSScriptRoot 'wp12_openai_client.py'
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne '{public_sha(c.ROOT/'scripts/wp12_openai_client.py')}') {{ throw 'CLIENT_CHANGED_SAFE_STOP' }}
# Key env/dotenv'den Python icinde yuklenir; argv/header/transcript/env dump yok.
if ($RunFirstCase) {{ & $python -B -X utf8 $entry --run-first-case }} else {{ & $python -B -X utf8 $entry }}
exit $LASTEXITCODE
'''
    with script.open('x',encoding='utf-8') as f:f.write(text)
    c.save_new(a.QA/'key_availability_boolean_only.json',{'api_key_available':key_available(c.ROOT),
        'raw_secret_read_by_inventory':False,'secret_files_hashed':False,'authenticated_API_calls':0})
    print('Offline OpenAI client/adapter/budget package prepared; no API requests.')


if __name__=='__main__':main()
