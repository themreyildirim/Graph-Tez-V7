"""Mevcut gerçek Gemma smoke kaydından bağımsız rapor/QA. Ağ ve inference yok."""
import datetime
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from wp12_local_llm_preflight import ROOT,sha,save
from wp12_gemma_v2_1_smoke_review import read,validate_run,verify_file_manifest
from wp12_smoke_independent_audit import audit_content

SOURCE=ROOT/'reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586'
QA=ROOT/'reports/qa/WP12/gemma1b_v2_1_smoke_validation_v1'


def main():
    import pandas as pd
    assert not (QA/'artifact_validation.json').exists()
    manifest=verify_file_manifest(SOURCE)
    source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in SOURCE.iterdir() if p.is_file()}
    save(QA/'raw_source_hashes.json',source_hashes)
    existing=validate_run(SOURCE);save(QA/'existing_reviewer_result.json',existing)
    r=read(SOURCE/'run_record.json');request=read(SOURCE/'smoke_request.json');response=read(SOURCE/'smoke_response_raw.json');samples=read(SOURCE/'memory_samples.json')
    cfg=read(ROOT/'configs/WP12_GEMMA1B_IDENTITY_FIX_v2_1.json')
    independent=audit_content(r,request,response,samples,cfg)
    save(QA/'independent_checks.json',independent)
    assert sha(SOURCE/'smoke_request.json')==r['request_sha256']
    assert sha(SOURCE/'smoke_response_raw.json')==r['response_sha256']
    assert sha(ROOT/cfg['runner'])==cfg['runner_sha256']==r['script_sha256']
    assert sha(ROOT/'scripts/WP12_GemmaIdentity_v1.ps1')==cfg['identity_helper_sha256']==r['identity_helper_sha256']
    assert sha(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')==cfg['scenario_sha256']==r['frozen_scenarios_sha256']
    assert sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md')==cfg['source_contract_sha256']==r['source_contract_sha256']
    runner=(ROOT/cfg['runner']).read_text(encoding='utf-8')
    assert runner.count('$apiClient.PostAsync(')==1 and runner.count("/api/chat'")==1
    assert '/api/pull' not in runner and 'ollama pull' not in runner
    save(QA/'single_request_no_download_scope.json',{
        'recorded_inference_attempts':r['inference_attempts'],'one_saved_request_and_complete_response':True,
        'matching_frozen_runner_PostAsync_sites':1,'automatic_retry_loop':False,
        'runner_model_pull_route_or_command':False,'record_new_downloads':r['new_downloads'],
        'model_present_in_pre_request_tags':True,'tags_model_modified_at':next(x['modified_at'] for x in read(SOURCE/'metadata_2_tags.json')['models'] if x['name']==cfg['model']),
        'scope':'This supplied run and matching runner. No system-wide server/network audit; other clients UNKNOWN.',
        'runtime_authentication':'User-supplied record consistency; not cryptographic process attestation'})
    # Yalnız önceden izinli küçük model metadata dosyaları; weights tekrar yüklenmez.
    cache=Path('C:/Users/emrey/.ollama/models')
    wrapper=cache/'manifests/registry.ollama.ai/library/gemma3/1b-it-q4_K_M'
    source=cache/'blobs'/cfg['source_manifest_file_sha256'].replace(':','-')
    assert 'sha256:'+sha(wrapper)==cfg['local_wrapper_manifest_file_sha256']
    assert 'sha256:'+sha(source)==cfg['expected_API_model_digest']
    w=read(wrapper);s=read(source)
    assert w['config']==s['config'] and w['layers'][:-1]==s['layers']
    save(QA/'independent_identity_and_hash_checks.json',{
        'model':cfg['model'],'API_digest':cfg['expected_API_model_digest'],
        'local_wrapper_SHA256':'sha256:'+sha(wrapper),'source_manifest_SHA256':'sha256:'+sha(source),
        'local_config_and_layer_references_equal':True,'weights_rehashed':False,
        'request_SHA256':sha(SOURCE/'smoke_request.json'),'response_SHA256':sha(SOURCE/'smoke_response_raw.json'),
        'runner_SHA256':sha(ROOT/cfg['runner']),'identity_helper_SHA256':sha(ROOT/'scripts/WP12_GemmaIdentity_v1.ps1'),
        'source_manifest_entries_verified':len(manifest),'all8_raw_files_preserved':True,
        'frozen19_scenarios_SHA256':cfg['scenario_sha256'],'document_contract_SHA256':cfg['source_contract_sha256']})
    pd.DataFrame(r['admission_samples']).to_csv(QA/'admission_samples.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(samples).to_csv(QA/'runtime_host_samples.csv',index=False,encoding='utf-8-sig')
    save(QA/'validation_record.json',{
        'reviewed_at':datetime.datetime.now().astimezone().isoformat(),'status':'TECHNICAL_SMOKE_VERIFIED',
        'source_run':SOURCE.relative_to(ROOT).as_posix(),'source_run_status_unchanged':r['status'],
        'existing_reviewer_pass':True,'independent_schema_memory_identity_pass':True,
        'jsonschema_version':importlib.metadata.version('jsonschema'),
        'request_schema_applied_to_actual_response':True,'ready_for_next_controlled19x3_stage':True,
        'readiness_scope':'Technical smoke prerequisite passed; per-case full prompt budget/evidence dependencies/memory and human semantic review still apply',
        'actual19x3_started':False,'actual_full_source_summary_quality':'NOT_TESTED',
        'automatic_publication':False,'human_semantic_review':'NOT_PERFORMED_TECHNICAL_ECHO_ONLY',
        'review_API_or_inference_calls':0,'new_downloads':0,'WP13_started':False})
    for pattern in ['test_wp12_smoke_independent_audit.py','test_wp12_gemma_v2_1_smoke_review.py']:
        t=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        (QA/(pattern+'.log')).write_text(t.stdout+t.stderr,encoding='utf-8');assert t.returncode==0,t.stderr
    report=write_report(r,response,independent);notebook();close(report,source_hashes)


def write_report(r,response,d):
    p=ROOT/'reports/WP12_GEMMA1B_V2_1_SMOKE_VALIDATION.md';assert not p.exists()
    p.write_text(f'''# WP12 — Gerçek Gemma1B v2.1 smoke testinin bağımsız teknik doğrulaması

08.11.2026 · **TECHNICAL_SMOKE_VERIFIED.** Kullanıcının gerçek `20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586` çıktısı salt okunur incelendi. Ham durum SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW olarak değişmeden kaldı; bu yeni inceleme ayrı QA kaydıdır. Codex yeni API/inference/indirme yapmadı.

**Sonuç:** Sonraki kontrollü19×3 kaynaklı açıklama aşamasına geçiş için teknik smoke önkoşulu doğrulandı. Bu tur57 açıklama çalıştırılmadı. Her gerçek istekte mevcut kaynak/bağlam bağımlılıkları, tam prompt token bütçesi ve bellek kapıları uygulanmalı; insan semantik incelemesi ve yayın yasağı devam eder. Bu tek echo testi uzun kaynak bağlamı veya Türkçe özet kalitesini doğrulamaz.

## 1. Model ve dosya kimliği
Gemma tag'i request/response/pre-request tags/record içinde aynı: `gemma3:1b-it-q4_K_M`. API ve kaynak model digest'i **sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c**. Ayrı yerel wrapper SHA'sı **sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16**. Kimlik yardımcısı ve runner hash'leri sabit config ve gerçek record ile eşleşti. Küçük wrapper/kaynak dosyaları bağımsız tekrar hash'lendi; config ve ağırlık/template/lisans/params referansları aynı. GGUF ağırlıkları bu incelemede yeniden hash'lenmedi veya yüklenmedi.

Ollama servis sürümü0.40.6; gerçek kullanıcı PowerShell5.1.26100.9711, is_appcontainer=false. api/ps başlangıç yanıtı boş: test öncesinde yüklü model listesi yok. Bu kullanıcı ortamında başarılı çalışma kanıtıdır; önceki Codex AppContainer erişim reddi model arızasına dönüştürülmez.

## 2. Gerçek istek, şema ve tamamlanma
| Kontrol | Gerçek sonuç |
|---|---|
| HTTP |**200**|
| Tamamlama |**done=true; done_reason=stop**|
| assistant content |`{{"probe":"WP12_GEMMA1B_SMOKE_V2"}}`|
| Şema |object; required probe; tek enum sabiti; additionalProperties=false — **PASS**|
| prompt/output token |**{response['prompt_eval_count']} / {response['eval_count']}**;1536/384 bütçeleri içinde|
| Context/batch/seed |2048 /32 /20261108|
| Diğer sabit ayarlar |temperature0, think:false, stream:false, keep_alive0|
| İstemci ölçülen süre |{r['elapsed_seconds']:.3f}sn|
| Sunucu total/load süreleri |{d['server_total_seconds']:.3f} / {d['server_load_seconds']:.3f}sn|

`smoke_request.json` sabit v2 payload'u ile birebir içerik eşleştirmesinden geçti. `smoke_response_raw.json` strict JSON parse ile okundu; tekrar eden JSON anahtarına izin verilmedi. İstek içindeki gerçek JSON Schema, mevcut jsonschema kütüphanesiyle gerçek assistant content'e ayrıca uygulandı. Ham yanıtta ek düşünce/tool çıktısı yok; yalnız probe alanı var. Response created_at UTC zamanı, kayıtlı Europe/Istanbul başlangıç/bitiş aralığına düşüyor. Tam HTTP status ve tamamlanma bu kayıtta doğrudan mevcut; önceki UNKNOWN alanları geriye dönük değiştirilmedi.

Tek şemalı isteğin kabul edilmesi ve uyumlu tamamlanması doğrulandı. Genel şema uyumu, halüsinasyonsuz özet, klinik bilgi veya model risk skoru başarısı sonucu çıkarılmaz. Bu teknik içerik PDF alıntısı/MedDRA etiketi değildir. SHAP/Δz/GNN tahmini üretilmedi.

## 3. Gemma v2 bellek politikasına uygunluk
| Koşul | Gerçek değer | Karar |
|---|---:|---|
| İlk boş host RAM≥2,5GiB |{d['initial_available_RAM_GiB']:.3f}GiB|PASS|
|5 kararlı örnek: her biri≥2,5GiB |en düşük{d['stability_min_RAM_GiB']:.3f}GiB|PASS|
| Örneklerin kapsadığı süre≥4sn |{d['stability_span_seconds']:.3f}sn|PASS|
| İnference hemen öncesi boş RAM≥2,5GiB |{d['pre_inference_available_RAM_GiB']:.3f}GiB|PASS|
| Başlangıç/hemen önce VRAM≥2048MiB |3935 /3935MiB|PASS|
| Başlangıç/kararlılık/hemen önce commit≥3GiB |tüm kayıtlı değerler uygun|PASS|
| Çalışırken host RAM≥1GiB uyarı sınırı |28 örnekte minimum**{d['sampled_min_available_RAM_GiB']:.3f}GiB**|PASS|
| Son boş host RAM≥1GiB |{d['post_available_RAM_GiB']:.3f}GiB|PASS|
| Çalışma sırasında minimum commit boşluğu |{d['sampled_min_commit_available_GiB']:.3f}GiB|Bilgi; başlangıç şartı da geçti|
| Son boş VRAM |3935MiB|Son nokta ölçümü|

**2,5GiB başlangıç kapısıdır; bütün çalışma boyunca uygulanmış alt sınır değildir.** Runtime örnekleri2,5GiB altına inse de kabul edilmiş1GiB uyarı sınırının üstünde kaldı; eşik değiştirilmedi.28 örnek host'un toplam kullanılabilir RAM'ini gösterir; kesin inference tepe RAM'i veya bütünü modele atfedilebilir kullanım değildir. Runtime GPU ölçümü yoktur: **tepe VRAM/CPU-GPU offload durumu UNKNOWN**. Başlangıç/son3935MiB'den “GPU kullanılmadı” veya kesin GPU tepe belleği çıkarılmaz. keep_alive0 bir istek ayarıdır; ayrı son api/ps cevabı olmadan servis residency hakkında ek kanıt üretilmez.

## 4. Tek inference ve yeni indirme denetimi
Kayıtta inference_attempts=1; bir sabit request dosyası ve bir tamamlanmış response var. Aynı hash'li runner tek PostAsync/api-chat çağrı noktası içeriyor; retry döngüsü yok. Önceki üç GET version/tags/ps metadata'dır, inference sayılmaz. Runner'da model pull/indirme endpoint'i/komutu yok; new_downloads/models_pulled0. Gemma, istek öncesi tags listesinde zaten mevcut ve modified_at04:02:20; test04:49'da yapıldı. Bu run ve betik kapsamında **tek inference/yeni indirme0** kanıtı tutarlı.

Bu sonuç sistem çapında paket yakalama veya başka istemcilerin sunucu erişim denetimi değildir. Kullanıcı sağladığı dosyaların hash'leri içerik tutarlılığı sağlar, gerçek process çalışmasını kriptografik olarak tasdik etmez. Bu sınır saklanır; global “hiçbir uygulama indirme yapmadı/başka istek yoktu” iddiası kurulmaz.

## 5. Hash, QA ve koruma
file_hashes.json içindeki7 ham dosya girdisi birebir doğrulandı; manifestin kendisi dahil **8 orijinal dosyanın** yeni SHA envanteri alındı ve inceleme sonunda aynı kaldı. Request SHA: `{r['request_sha256']}`; response SHA: `{r['response_sha256']}`. Dondurulmuş19 senaryo ve kaynak sözleşmesi hash'leri config/record/gerçek dosya arasında eşleşti. Önceki3.482 proje dosyası korundu; eski başarısız denemeler başarıya çevrilmedi. run_status eski tam baytları saklanarak öne eklenir.

Mevcut inceleyici ve ikinci bağımsız kontrol aynı teknik sonuca ulaştı.9 gerçek-record regresyon testi ve12 mevcut inceleyici testi =**21 offline test** geçti; mutation testleri yalnız RAM kopyalarında yapıldı. Yeni model çalıştırılmadı. Notebook gerçek echo, kimlik/şema/bellek tabloları ve kayıtlı host RAM grafiğini içerir. Yeni QA: reports/qa/WP12/gemma1b_v2_1_smoke_validation_v1/; teknik sonuç validation_record.json içinde. Semantik PDF incelemesi NOT_TESTED; otomatik yayın yok.19×3, yeni eğitim ve WP13 başlatılmadan burada durulur.
''',encoding='utf-8')
    return p


def notebook():
    from wp09_close_wp10_notebooks import execute
    execute('WP12_gemma1b_v2_1_smoke_validation.ipynb',[
        ('md','# WP12 — Gerçek Gemma smoke testinin bağımsız doğrulaması\nKullanıcının tek gerçek run\'ı okunur; bu notebook API/inference yapmaz. Ham run durumu ve eski kayıtlar değişmez.'),
        ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/gemma1b_v2_1_smoke_validation_v1';S=ROOT/'reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586'\nr=json.loads((S/'run_record.json').read_text(encoding='utf-8-sig'));response=json.loads((S/'smoke_response_raw.json').read_text(encoding='utf-8-sig'));d=json.loads((Q/'independent_checks.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([{'Model':response['model'],'API digest':r['observed_digest'],'Wrapper SHA':r['identity_validation']['local_wrapper_manifest_file_sha256'],'HTTP':r['HTTP_status'],'done':response['done'],'done_reason':response['done_reason'],'Gerçek echo':response['message']['content']}]).T)\ndisplay(pd.DataFrame([d]).T)"),
        ('md','**Yorum:**Bu gerçek teknik echo, şema/tamamlanma ve kimlik zinciri kanıtıdır. PDF özeti veya klinik tahmin değildir. Gerçek41 prompt/19 çıktı token ile tamamlandı; uzun kaynak bağlamı ve Türkçe sadakat henüz ölçülmedi.'),
        ('code',"admission=pd.read_csv(Q/'admission_samples.csv');runtime=pd.read_csv(Q/'runtime_host_samples.csv')\ndisplay(admission);display(runtime)\nfig,axs=plt.subplots(1,2,figsize=(10,3.5));axs[0].plot(range(1,6),admission['available_bytes']/2**30,marker='o');axs[0].axhline(2.5,color='red',ls='--',label='Başlangıç tabanı2,5GiB');axs[0].set_title('Beş kararlı başlangıç örneği');axs[0].set_xlabel('Örnek');axs[0].set_ylabel('Boş host RAM GiB');axs[0].legend()\nt=pd.to_datetime(runtime['at']);elapsed=(t-t.iloc[0]).dt.total_seconds();axs[1].plot(elapsed,runtime['available_bytes']/2**30);axs[1].axhline(1,color='red',ls='--',label='Runtime uyarısı1GiB');axs[1].set_title('Gerçek çalışma örnekleri');axs[1].set_xlabel('İlk örnekten saniye');axs[1].set_ylabel('Boş host RAM GiB');axs[1].legend();fig.tight_layout();F=ROOT/'reports/figures/WP12/gemma1b_v2_1_smoke_validation_v1';F.mkdir(parents=True,exist_ok=True);fig.savefig(F/'recorded_host_memory.png',dpi=150);plt.show()"),
        ('md','**Yorum:**2,5GiB başlangıç,1GiB runtime uyarı eşiğidir. Minimum kayıtlı RAM1,963GiB; eşik ihlali yok. Bu host toplam belleği örneklemesidir; modele ait kesin tepe RAM veya tepe VRAM değildir. GPU çalışma aralığı ölçülmediği için UNKNOWN kalır.'),
        ('code',"display(pd.DataFrame([json.loads((Q/'validation_record.json').read_text(encoding='utf-8'))]).T)\ndisplay(pd.DataFrame([json.loads((Q/'single_request_no_download_scope.json').read_text(encoding='utf-8'))]).T)\nfor name in ['test_wp12_smoke_independent_audit.py.log','test_wp12_gemma_v2_1_smoke_review.py.log']:\n print(name);print((Q/name).read_text(encoding='utf-8'))"),
        ('md','**Sonuç:**Teknik smoke doğrulandı; kontrollü19×3 aşamasına geçişin teknik kapısı açık. Bu tur gerçek senaryolar başlatılmadı. Kaynak doğrulama, tam prompt bütçesi, bellek kontrolleri ve insan semantik inceleme şartları devam ediyor; otomatik yayın/eğitim/WP13 yok.')])


def close(report,sources):
    prior=read(QA/'prior_artifacts_sha256.json')
    assert all(sha(ROOT/k)==v for k,v in prior.items())
    assert all(sha(ROOT/k)==v for k,v in sources.items())
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    prefix=f'''# WP12 gerçek Gemma v2.1 smoke — bağımsız teknik doğrulama geçti ·08.11.2026

- Kullanıcı run20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586 salt okunur incelendi. HTTP200/done true/stop/tek doğru JSON echo; API9755… ve wrapper313f… ayrı doğrulandı. Gerçek user PS5.1/servis0.40.6;41 prompt/19 çıktı token.
- Başlangıç/5kararlı örnek/immediate RAM-GPU-commit kapıları geçti.28 runtime örneğinde boş RAM minimum1,963GiB;1GiB uyarısı aşılmadı. Tepe model RAM/tepe VRAM UNKNOWN; başlangıç/sonGPU ölçümü runtime peak sayılmadı.
- Tek kayıtlı inference ve aynı hash'li runner'da tek PostAsync; indirme yolu/retry yok, mevcut model/new_downloads0. Bu run kapsamındaki kanıt, global ağ denetimi değildir.8 ham dosya değişmedi.
-21 offline test geçti; önceki{len(prior)} dosya ve19 senaryo korundu. Rapor reports/WP12_GEMMA1B_V2_1_SMOKE_VALIDATION.md; QA reports/qa/WP12/gemma1b_v2_1_smoke_validation_v1/; notebook notebooks/WP12_gemma1b_v2_1_smoke_validation.ipynb.
- Kontrollü19×3 için teknik smoke önkoşulu doğrulandı; kaynak/prompt/bellek ve insan anlam inceleme şartları sürer. Bu tur gerçek senaryolar, yeni API/inference/indirme, eğitim, otomatik yayın veya WP13 yok. Kullanıcı onayı bekleniyor.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if k=='run_status.md' else ROOT/k)==v for k,v in prior.items())
    save(QA/'artifact_validation.json',{'status':'TECHNICAL_SMOKE_VERIFIED_READY_FOR_NEXT_CONTROLLED_STAGE',
        'source_run_count':1,'original_raw_files_preserved':len(sources),'prior_artifacts_preserved':len(prior),
        'hash_manifest_entries_verified':7,'identity_and_request_response_schema_pass':True,'memory_v2_pass':True,
        'recorded_user_inference_requests':1,'additional_review_inference_requests':0,'recorded_model_downloads':0,
        'observed_min_host_available_GiB':2107588608/2**30,'runtime_peak_GPU':'UNKNOWN',
        'offline_tests_passed':21,'frozen_scenarios_unchanged':19,'actual19x3_started':False,
        'automatic_publication':False,'new_training':False,'WP13_started':False,
        'notebook_executed_code_cells':3,'prior_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,ROOT/'scripts/wp12_smoke_independent_audit.py',
        ROOT/'scripts/wp12_smoke_validation_outputs.py',ROOT/'tests/test_wp12_smoke_independent_audit.py',
        ROOT/'notebooks/WP12_gemma1b_v2_1_smoke_validation.ipynb',
        ROOT/'reports/figures/WP12/gemma1b_v2_1_smoke_validation_v1/recorded_host_memory.png',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('TECHNICAL_SMOKE_VERIFIED; prior preserved',len(prior),'tests21; actual19x3 NOT_STARTED')


if __name__=='__main__':main()
