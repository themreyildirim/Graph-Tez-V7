"""S01-R1 gerçek kullanıcı run'ı için salt-okunur, ağsız bağımsız denetim.

Kaynak run'a hiçbir dosya yazmaz; yeni QA açıkça ayrı klasördedir.
"""
from pathlib import Path
import hashlib
import json
import sys
from datetime import datetime
from jsonschema import Draft202012Validator
import wp12_source_case as c
import wp12_source_low_memory as low

RUN=c.ROOT/'reports/qa/WP12/experimental_low_memory_user_runs_v1/20261108_065325_050e95866a054763b9ac7d5551e1f8f5'
QA=c.ROOT/'reports/qa/WP12/experimental_low_memory_S01_R1_review_v1'


def source_checks(folder=RUN):
    """Ham manifest, request, source identity, prompt ve kayıtlı model kimliği."""
    assert folder==max((p for p in folder.parent.iterdir() if p.is_dir()),key=lambda p:p.stat().st_ctime_ns),'specified run is not latest'
    hashes=c.read(folder/'file_hashes.json')
    files={p.name for p in folder.iterdir() if p.is_file()}
    assert files==set(hashes)|{'file_hashes.json'},'unexpected/missing run file'
    assert all(Path(name).name==name for name in hashes),'invalid run filename'
    assert all(c.sha(folder/name)==h for name,h in hashes.items()),'raw run hash mismatch'
    r=c.read(folder/'run_record.json');policy=c.read(low.POLICY)
    req=c.read(folder/'source_request.json');proof=c.read(folder/'token_budget.json')
    context=c.context();expected=c.request_for(context)
    assert req==expected==c.read(c.QA/'package/request.json')
    assert (folder/'source_request.json').read_text(encoding='utf-8')==c.dump(expected)
    assert c.read(folder/'case_context.json')==c.read(c.QA/'package/context.json')
    assert c.sha(folder/'source_request.json')==r['request_sha256']
    assert c.sha(folder/'source_response_raw.json')==r['response_sha256']
    assert c.sha(low.POLICY)==r['case_policy_sha256']
    assert c.sha(c.ROOT/policy['runner'])==r['script_sha256']==policy['runner_sha256']
    assert c.sha(c.ROOT/'scripts/WP12_LowMemoryObservation_v1.ps1')==r['observation_helper_sha256']
    assert c.sha(c.ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md')==r['source_contract_sha256']
    assert c.sha(c.ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')==r['frozen_scenarios_sha256']
    tags=c.read(folder/'metadata_2_tags.json')
    tag=next(x for x in tags['models'] if x['name']==policy['model'])
    normalize=lambda s:s if s.startswith('sha256:') else 'sha256:'+s
    digest=policy['API_model_digest']
    assert normalize(tag['digest'])==r['observed_digest']==r['expected_digest']==digest
    binding=r['identity_validation']
    wrapper=Path(binding['local_wrapper_path']);manifest=Path(binding['source_manifest_path'])
    assert 'sha256:'+c.sha(wrapper)==binding['local_wrapper_manifest_file_sha256']
    assert 'sha256:'+c.sha(manifest)==binding['source_manifest_file_sha256']==digest
    wrap=c.read(wrapper);src=c.read(manifest)
    manifest_type='application/vnd.docker.distribution.manifest.v2+json'
    links=[x for x in wrap['layers'] if x['mediaType']==manifest_type]
    assert len(links)==1 and links[0]['digest']==digest
    model_layers=[x for x in wrap['layers'] if x['mediaType']!=manifest_type]
    assert wrap['config']==src['config'] and model_layers==src['layers']
    assert binding['identity_binding_valid'] is True
    assert c.read(folder/'metadata_1_version.json')['version']==r['server_version']=='0.40.6'
    assert c.read(folder/'metadata_3_ps.json')['models']==[]
    assert proof==c.read(c.QA/'package/offline_token_proof.json')
    assert proof['admitted'] is True and proof['input_token_count']==919
    assert r['inference_attempts']==1 and r['real_scenario_repeats']==1
    assert r['new_downloads']==r['models_pulled']==0
    assert r['is_appcontainer'] is False and r['scenario_id']=='S01' and r['repeat']==1
    return {'raw_files':len(files),'manifest_entries':len(hashes),'all_raw_hashes_valid':True,
        'request_and_frozen_context_equal':True,'API_digest':digest,'wrapper_and_source_manifest_independently_valid':True,
        'case_policy_hash_valid':True,'script_hash_valid':True,'recorded_attempts':1,
        'new_downloads_recorded':0,'global_other_client_activity':'NOT_OBSERVABLE_FROM_THIS_RUN',
        'token_proof_equals_frozen_proof':True}


def memory_checks(folder=RUN):
    r=c.read(folder/'run_record.json');policy=c.read(low.POLICY)
    before=c.read(folder/'preflight_measurements.json')
    stable=r['admission_samples'];runtime=c.read(folder/'memory_samples.json')
    assert len(stable)==5
    span=(datetime.fromisoformat(stable[-1]['at'])-datetime.fromisoformat(stable[0]['at'])).total_seconds()
    assert span>=4
    entries=[('initial',r['memory_before'],r['GPU_before']),('preflight',before['memory'],before['GPU']),
        *[(f'stable_{i+1}',m,r['GPU_before']) for i,m in enumerate(stable)],
        ('immediately_before',r['memory_immediately_before'],r['GPU_immediately_before'])]
    assert all(low.entry_gate(m,g,policy) for _,m,g in entries)
    assert runtime and all(not low.runtime_warning(m,policy) for m in runtime)
    assert not low.runtime_warning(r['memory_after'],policy)
    return {'entry_RAM_GiB':r['memory_before']['available_bytes']/2**30,
        'immediate_RAM_GiB':r['memory_immediately_before']['available_bytes']/2**30,
        'after_RAM_GiB':r['memory_after']['available_bytes']/2**30,
        'stable_sample_count':len(stable),'stable_span_seconds':span,'entry_gates_passed':True,
        'runtime_sample_count':len(runtime),'sampled_RAM_min_GiB':min(m['available_bytes'] for m in runtime)/2**30,
        'sampled_RAM_max_GiB':max(m['available_bytes'] for m in runtime)/2**30,
        'sampled_commit_min_GiB':min(m['commit_available_bytes'] for m in runtime)/2**30,
        'OS_low_memory_signal_true_count':sum(m['low_memory_notification'] for m in runtime),
        'runtime_warning_observed':False,'GPU_before_MiB':r['GPU_before']['free_MiB'],
        'GPU_immediate_MiB':r['GPU_immediately_before']['free_MiB'],'GPU_after_MiB':r['GPU_after']['free_MiB'],
        'runtime_GPU_peak':'UNKNOWN_NOT_SAMPLED','system_unsampled_RAM_min':'UNKNOWN',
        'inference_process_RAM_peak':'UNKNOWN_NOT_MEASURED','safety_guarantee':False}


def structural_checks(folder=RUN):
    r=c.read(folder/'run_record.json');res=c.read(folder/'source_response_raw.json')
    candidate=json.loads(res['message']['content'])
    ctx=c.context();schema=c.case_schema(ctx)
    errors=list(Draft202012Validator(schema).iter_errors(candidate))
    v1errors=list(Draft202012Validator(c.read(c.ROOT/'docs/schemas/WP12_local_llm_candidate_v1.schema.json')).iter_errors(candidate))
    result=c.validate_response(res,ctx,c.read(folder/'token_budget.json'))
    assert result==c.read(folder/'structural_review.json')
    byid={a['quote_id']:a for a in ctx['annotations']}
    item_audit=[]
    for i,item in enumerate(candidate['items']):
        ids=item['evidence_ids'];primary=byid[ids[0]]
        item_audit.append({'item_index':i,'selected_real_quote':set(ids)<=set(ctx['scenario']['evidence_ids']),
            'source_scope_matches_primary':item['source_scope']==primary['attribution_scope'],
            'statement_kind_matches_primary':item['statement_kind']==primary['purpose'],
            'output_kind':item['statement_kind'],'cited_quote_kind':primary['purpose'],
            'cited_quote_ids':ids})
    return {'JSON_syntax_valid':True,'case_JSON_Schema_valid':not errors,'v1_JSON_Schema_valid':not v1errors,
        'schema_errors':[e.message for e in errors],
        'application_contract_valid':result['structural_valid'],'application_error':result.get('error'),
        'status':result['status'],'refused_with_nonempty_items':candidate['status']=='refused' and bool(candidate['items']),
        'item_checks':item_audit,'original_semantic_success':result['semantic_success'],
        'human_review':'PENDING_USER_HUMAN_REVIEW','automatic_release':False,
        'schema_limitation':'V1 schema has no conditional status/refused=>empty-items constraint; application validator catches invalid refusal'},candidate


def technical_checks(folder=RUN):
    r=c.read(folder/'run_record.json');res=c.read(folder/'source_response_raw.json')
    assert r['HTTP_status']==200 and res['done'] is True and res['done_reason']=='stop'
    assert res['model']==r['model']=='gemma3:1b-it-q4_K_M'
    assert res['prompt_eval_count']==r['input_token_count']==919
    assert 0<res['eval_count']<=384
    assert res['message']['content']
    return {'model_produced_nonempty_response':True,'HTTP_status':r['HTTP_status'],'done':res['done'],'done_reason':res['done_reason'],
        'prompt_tokens':res['prompt_eval_count'],'prompt_cached_tokens':res['prompt_eval_cached_count'],
        'output_tokens':res['eval_count'],'output_budget':384,'prompt_limit':1536,'context':2048,
        'prompt_plus_output_tokens':res['prompt_eval_count']+res['eval_count'],
        'server_total_seconds':res['total_duration']/1e9,'server_load_seconds':res['load_duration']/1e9,
        'server_prompt_eval_seconds':res['prompt_eval_duration']/1e9,'server_output_eval_seconds':res['eval_duration']/1e9,
        'client_generation_plus_review_block_seconds':r['elapsed_seconds'],
        'client_elapsed_includes_python_review':True,'recorded_timeout_or_exception':r.get('error'),
        'token_truncation_evidence':False,'root_cause_of_model_content_error':'UNKNOWN_NO_CAUSAL_DIAGNOSIS_FROM_SINGLE_RUN'}


def verify_pdf_pages(output_dir=None):
    """Özgün PDF sayfalarını yeniden OKUR; kaynak veya eski extraction yazılmaz."""
    # Kabul edilmiş PDF pilotunun mevcut yerel bağımlılığı; kurulum/indirme yok.
    sys.path.insert(0,str(c.ROOT/'.deps/pymupdf'))
    import pymupdf as fitz
    ctx=c.context();bundle=ctx['bundle'];quotes,pages,_=c.source_index(bundle,ctx['annotations'])
    refs=ctx['scenario']['sources'];doc_id=refs[0]['document_id']
    doc=next(d for d in bundle['documents'] if d['document_id']==doc_id)
    path=c.ROOT/'data/user_pdfs'/doc['receipts'][0]['original_filename']
    assert c.sha(path)==doc['raw_sha256']
    rows=[]
    with fitz.open(path) as pdf:
        for ref in refs:
            page=pdf[ref['physical_page']-1];text=page.get_text('text',sort=False,flags=195)
            q=quotes[ref['quote_id']];cached=pages[q['page_id']]
            assert text==cached['text'],'current page extraction differs from cached text'
            assert text[ref['char_start']:ref['char_end']]==q['quote']
            assert hashlib.sha256(q['quote'].encode()).hexdigest()==ref['quote_sha256']
            rows.append({'filename':path.name,'raw_sha256':c.sha(path),'page':ref['physical_page'],
                'char_start':ref['char_start'],'char_end':ref['char_end'],'quote_id':ref['quote_id'],
                'quote_sha256':ref['quote_sha256'],'quote':q['quote'],
                'page_text_matches_cached':True,'source_span_matches_original_PDF':True})
            if output_dir:
                c.save_new(Path(output_dir)/f'original_physical_page_{ref["physical_page"]}.json',{
                    'file':str(path),'page':ref['physical_page'],'text':text,'source_read_only':True})
    return rows


def semantic_review(candidate):
    """Bu tek gerçek yanıt için açık analist değerlendirmesi; insan onayı DEĞİL."""
    exact=candidate['items'][0]['explanation_tr']
    assert exact=="The provided text does not contain any information about the product's form or formulation."
    rows=[
        ('ürün','Page1 names Erythromycin Tablets BP 250 mg','Ürün adı/doz açıklanmamış.','OMITTED'),
        ('etkin_madde','Page1: contains active ingredient erythromycin; macrolide antibiotics','Etkin madde ve ilaç sınıfı aktarılmamış.','OMITTED'),
        ('formülasyon','Page6: red coloured, round, biconvex, enteric-coated tablets','Formülasyon bilgisi yok iddiası açık kaynakla çelişiyor.','CONTRADICTED'),
        ('ambalaj','Page6: blister28/56/84/100; containers21/100/250/500/1000','Ambalaj bilgileri aktarılmamış.','OMITTED'),
        ('belirsizlik','Selected quotes have no image-only or unknown-text qualifier','IMAGE_TEXT_UNAVAILABLE desteklenmiyor; bu sayfalar metin katmanından okunabilir.','UNSUPPORTED_REFUSAL'),
        ('atıf','Cited page1 quote is identity; page6 formulation quote was supplied but not cited','Gerçek quote-ID seçilmiş ancak formulation amacı identity alıntısına bağlanmış.','MISATTRIBUTED'),
        ('dil','Frozen prompt requests Turkish explanation','explanation_tr İngilizce; gerçek Türkçe açıklama yok.','WRONG_LANGUAGE'),
        ('eşdeğerlik','Parent/product equivalence must not be invented','Yeni ana ilaç/ürün eşdeğerliği iddiası yok; bu durum yanlış reti başarılı kılmaz.','NO_EQUIVALENCE_CLAIM'),
        ('yasak_çıktı','No model score, SHAP, delta-z, ADR or MedDRA generation','Bu yanıtta yeni skor/etiket/yan etki üretilmemiş.','NO_FORBIDDEN_GENERATION')]
    return {'review_kind':'CODEX_SOURCE_COMPARISON_NOT_HUMAN_APPROVAL','agent_assessment':'SOURCE_FAITHFULNESS_FAIL',
        'human_semantic_review':'PENDING','approved_or_publishable':False,'automatic_release':False,
        'exact_explanation_field':exact,'actual_Turkish_model_explanation':None,
        'reviewer_Turkish_translation_NOT_MODEL_OUTPUT':'Sağlanan metin, ürünün şekli veya formülasyonu hakkında herhangi bir bilgi içermiyor.',
        'findings':[{'topic':t,'source_fact':s,'assessment_tr':a,'status':v} for t,s,a,v in rows],
        'next_stage_recommendation':'DO_NOT_START_19x3; await human review. Optional separately versioned method repair proposal requires explicit decision; no silent prompt/schema change or retry.',
        'uncertainty':'Single-case content-error cause UNKNOWN; cannot attribute to RAM, model size, language capacity or seed without further authorized evidence.'}


def audit(folder=RUN):
    structural,candidate=structural_checks(folder)
    return {'source':source_checks(folder),'technical':technical_checks(folder),
        'memory':memory_checks(folder),'structural':structural,'semantic':semantic_review(candidate)}
