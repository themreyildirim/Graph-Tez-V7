"""Seçilmiş yerel modelin yükleme yapmayan ön kontrolü. Çıkarım istemcisi YOK."""
from pathlib import Path
import datetime
import hashlib
import json
import math
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT/'reports/qa/WP12/local_llm_pilot_v1'
TAG = 'qwen3:4b-instruct-2507-q4_K_M'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def memory_gate(available_ram_bytes, free_vram_mib):
    """Mevcut kabul edilmiş planlama tabanı; sığma garantisi değildir."""
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>=0
               for x in (available_ram_bytes,free_vram_mib)):
        return False
    return available_ram_bytes >= 3*2**30 and free_vram_mib >= 2.5*1024


def main():
    import psutil
    assert not (QA/'preflight.json').exists(), 'Previous audit must not be overwritten'
    now=datetime.datetime.now().astimezone().isoformat()
    ram=dict(psutil.virtual_memory()._asdict())
    gpu_result=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.free,driver_version',
                               '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,check=True)
    g=gpu_result.stdout.strip().split(', ')
    gpu={'name':g[0],'total_MiB':int(g[1]),'free_MiB':int(g[2]),'driver':g[3]}
    passed=memory_gate(ram['available'],gpu['free_MiB'])
    exe=Path('C:/Users/emrey/AppData/Local/Programs/Ollama/ollama.exe')
    v=subprocess.run([str(exe),'--version'],capture_output=True,text=True,timeout=15)
    version={'command':'ollama.exe --version','returncode':v.returncode,'stdout':v.stdout,'stderr':v.stderr,
             'inference':False,'server_started_by_this_script':False}
    # Yalnız metadata GET; servis başlatılmaz, hiçbir generate/chat/pull isteği yoktur.
    api=[]
    for route in ('version','tags'):
        url='http://127.0.0.1:11434/api/'+route
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(urllib.request.Request(url,method='GET'),timeout=2) as res:
                api.append({'method':'GET','url':url,'http_status':res.status,'body':res.read(1024*1024).decode()})
        except Exception as e:
            api.append({'method':'GET','url':url,'error_type':type(e).__name__,'error':str(e)})
    model_root=Path.home()/'.ollama/models'
    manifest=model_root/'manifests/registry.ollama.ai/library/qwen3/4b-instruct-2507-q4_K_M'
    data=json.loads(manifest.read_text(encoding='utf-8'))
    layers=[]
    for entry in [data['config'],*data['layers']]:
        p=model_root/'blobs'/entry['digest'].replace(':','-')
        exists=p.is_file();actual=sha(p) if exists else None
        layers.append({**entry,'exists':exists,'actual_size':p.stat().st_size if exists else None,
                       'actual_sha256':actual,'digest_valid':exists and 'sha256:'+actual==entry['digest'],
                       'size_valid':exists and p.stat().st_size==entry['size']})
    model={'tag':TAG,'manifest_path':str(manifest),'manifest_digest':'sha256:'+sha(manifest),
           'layers':layers,'all_layers_content_verified':all(x['digest_valid'] and x['size_valid'] for x in layers),
           'loaded':False,'downloaded':False}
    save(QA/'model_identity.json',model)
    result={'captured_at':now,'RAM':ram,'GPU':gpu,'client_version_check':version,
            'loopback_metadata_attempts':api,'memory_gate_passed':passed,
            'minimum_planning_gate':{'host_free_GiB':3.0,'GPU_free_GiB':2.5,'fit_guarantee':False},
            'status':'STOPPED_INSUFFICIENT_RAM' if not passed else 'MEMORY_FLOOR_PASS_REQUIRES_SEPARATE_SMOKE',
            'schema_API_support':'UNVERIFIED_NO_INFERENCE; metadata endpoint access may be unavailable',
            'smoke_test':'NOT_RUN_MEMORY_GATE' if not passed else 'NOT_IMPLEMENTED_BY_PREFLIGHT',
            'scenario_execution':'NOT_RUN_MEMORY_GATE' if not passed else 'NOT_STARTED',
            'Ollama_service_started':False,'model_loads':0,'inference_calls':0,'downloads':0,'training':False,
            'semantic_review':'NOT_PERFORMED_NO_LLM_OUTPUT','auto_published_explanations':0,'WP13_started':False}
    save(QA/'preflight.json',result)
    scenarios=json.loads((ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json').read_text(encoding='utf-8'))
    records=[{'scenario_id':s['scenario_id'],'repeat':r,'source_quote_ids':s['evidence_ids'],
              'status':'NOT_RUN_MEMORY_GATE' if not passed else 'NOT_STARTED',
              'LLM_output':None,'schema_result':None,'source_validation':None,'human_semantic_review':'NOT_PERFORMED_NO_OUTPUT'}
             for s in scenarios for r in range(1,4)]
    save(QA/'scenario_execution_status.json',records)
    save(QA/'approved_candidate_record.json',{'tag':TAG,'source':'explicit user choice in current turn',
        'new_download_allowed':False,'frozen_scenarios_sha256':sha(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'),
        'existing_contract_sha256':sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md'),
        'model_identity_file':'model_identity.json','repeats':3,
        'settings_source':'unchanged configs/WP12_local_llm_PROPOSED_v1.json; selected tag overridden by explicit user instruction only',
        'settings_executed':False})
    print(json.dumps({'RAM_available_GiB':ram['available']/2**30,'GPU_free_MiB':gpu['free_MiB'],
                      'status':result['status'],'manifest_digest':model['manifest_digest'],
                      'all_layers_verified':model['all_layers_content_verified'],'version_output':v.stdout},ensure_ascii=False))


if __name__=='__main__':
    main()
