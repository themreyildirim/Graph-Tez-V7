"""Gemma1B ayrı aday kaydı: salt okunur cache/QA; indirme/API/inference yok."""
import json
from pathlib import Path
import subprocess
import sys

from wp12_local_llm_preflight import ROOT,sha,save

QA=ROOT/'reports/qa/WP12/gemma1b_candidate_v1'
TAG='gemma3:1b-it-q4_K_M'


def main():
    assert not (QA/'artifact_validation.json').exists()
    identity=json.loads((QA/'model_identity.json').read_text(encoding='utf-8'))
    hardware=json.loads((QA/'hardware_snapshot.json').read_text(encoding='utf-8'))
    digest=identity['local_manifest_digest']
    replacements={
        'qwen3:4b-instruct-2507-q4_K_M':TAG,
        'sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0':digest,
        'WP12_LOCAL_SMOKE_V1':'WP12_GEMMA1B_SMOKE_V1',
        'WP12-user-smoke-run-v1':'WP12-gemma1b-user-smoke-run-v1',
        'WP12_UserPowerShellSmoke_v1.ps1':'WP12_Gemma1B_UserPowerShellSmoke_v1.ps1',
        'user_smoke_runs':'gemma1b_user_smoke_runs','user_smoke_reviews':'gemma1b_user_smoke_reviews',
        'WP12SmokeNativeV1':'WP12GemmaSmokeNativeV1',
        'import wp12_user_smoke_review as v':'import wp12_gemma_smoke_review as v'}
    bases={
        'scripts/WP12_UserPowerShellSmoke_v1.ps1':'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1',
        'scripts/wp12_user_smoke_review.py':'scripts/wp12_gemma_smoke_review.py',
        'tests/test_wp12_user_smoke_review.py':'tests/test_wp12_gemma_smoke_review.py'}
    forks=[]
    for old,new in bases.items():
        target=ROOT/new;assert not target.exists()
        text=(ROOT/old).read_text(encoding='utf-8')
        for a,b in replacements.items():text=text.replace(a,b)
        if new.endswith('.ps1'):
            text=text.replace("$version = Read-LocalMetadata 'version'; $record['server_version'] = $version.version",
                "$version = Read-LocalMetadata 'version'; $record['server_version'] = $version.version\n    if ([version]$version.version -lt [version]'0.30.0') { throw 'RUNTIME_TOO_OLD_FOR_LOCAL_ARTIFACT' }")
        target.write_text(text,encoding='utf-8')
        forks.append({'immutable_base':old,'base_sha256':sha(ROOT/old),'new_version':new,'new_sha256':sha(target)})
    save(QA/'implementation_lineage.json',{'method':'separate versioned forks; accepted Qwen files are not edited',
        'forks':forks,'changes':['model/tag/full manifest digest','separate record version/probe/paths/native class',
                               'local artifact requires Ollama>=0.30.0'],
        'unchanged':['3GiB host RAM','2.5GiB VRAM','seed20261108','context2048','one request/no retry/no download',
                     'source contracts and frozen19 scenarios']})
    cfgpath=ROOT/'configs/WP12_GEMMA1B_CONDITIONAL_v1.json';assert not cfgpath.exists()
    save(cfgpath,{
        'version':'WP12-gemma1b-conditional-v1','candidate_id':identity['candidate_id'],'model':TAG,
        'status':'LOCAL_CACHE_VERIFIED_AWAITING_USER_API_METADATA_AND_SMOKE',
        'expected_local_manifest_digest':digest,'source_manifest_digest':identity['source_manifest_digest'],
        'API_reported_digest':None,'API_digest_verification':'PENDING_USER_POWERSHELL; mismatch stops, no fallback',
        'cache_model_bytes':806058400,'runtime_requirement_from_local_config':'0.30.0',
        'minimum_host_available_bytes':3221225472,'minimum_GPU_free_MiB':2560,'threshold_change':False,
        'num_ctx':2048,'num_predict':384,'temperature':0,'seed':20261108,'think':False,'stream':False,'keep_alive':0,
        'runner_sha256':sha(ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1'),
        'request_timeout_seconds':60,'max_inference_requests':1,'inference_location':'user independent PowerShell only',
        'Codex_download_allowed':False,'automatic_download_or_server_start':False,
        'technical_probe_only':True,'real19x3_runs_allowed':False,'automatic_release':False,
        'scope':'nonclinical schema echo; not a PDF explanation or new training feature',
        'Qwen_records_policy':'preserve; neither delete nor retune'})
    save(QA/'conditional_run_record.json',{
        'candidate_id':identity['candidate_id'],'model':TAG,'local_manifest_digest':digest,
        'state':'AWAITING_USER_HOST_METADATA_AND_TECHNICAL_SMOKE',
        'actual_smoke_result':None,'model_downloaded_by_Codex':False,'Codex_local_API_calls':0,
        'Codex_inference_calls':0,'source_contract_unchanged':True,'frozen_scenario_count':19,
        'source_contract_sha256':sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md'),
        'frozen_scenarios_sha256':sha(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'),
        'reported_in_PDF':None,'predicted_by_GNN':{'status':'NOT_REQUESTED_IN_WP12','artifact_ref':None},
        'human_semantic_review':'NOT_PERFORMED_NO_PDF_EXPLANATION','auto_release':False,
        'gates':['user-host API version/digest','RAM>=3GiB and VRAM>=2560MiB immediately before call',
                 'at most one technical schema echo; record every failure','no19x3 run in this phase']})
    # Gerçek Qwen kullanıcı kayıtları yalnız okunur; yeni özet eski QA'yı ezmez.
    from wp12_user_smoke_review import validate_run
    oldruns=[]
    for p in sorted((ROOT/'reports/qa/WP12/user_smoke_runs').glob('*/run_record.json')):
        row=json.loads(p.read_text(encoding='utf-8-sig'))
        check=validate_run(p.parent)
        oldruns.append({'record':p.relative_to(ROOT).as_posix(),'record_sha256':sha(p),
            'integrity_review':check['status'],'status':row['status'],'server_version':row.get('server_version'),
            'is_appcontainer':row.get('is_appcontainer'),'inference_attempts':row['inference_attempts']})
    save(QA/'existing_Qwen_user_runs_readonly_review.json',oldruns)
    for pattern in ['test_wp12_gemma_smoke_review.py','test_wp12_user_smoke_review.py','test_wp12_llm_preflight.py','test_wp12_llm_contract.py']:
        t=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        (QA/(pattern+'.log')).write_text(t.stdout+t.stderr,encoding='utf-8');assert t.returncode==0
    ps=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1'
    command="$t=$null;$e=$null;$null=[System.Management.Automation.Language.Parser]::ParseFile('"+str(ps)+"',[ref]$t,[ref]$e);if($e.Count){$e|Out-String;exit 1};'ParseErrors=0; Gemma script NOT executed'"
    parsed=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,timeout=30)
    (QA/'powershell_parse_check.txt').write_text(parsed.stdout+parsed.stderr,encoding='utf-8');assert parsed.returncode==0
    report=write_report(identity,hardware,len(oldruns))
    notebook()
    close(report)


def write_report(identity,hardware,oldruns):
    report=ROOT/'reports/WP12_GEMMA1B_CANDIDATE.md';assert not report.exists()
    h=hardware;ram=h['RAM'];gpu=h['GPU'];digest=identity['local_manifest_digest']
    report.write_text(f'''# WP12 — Gemma3 1B ayrı aday ve koşullu çalışma v1

**LOCAL_CACHE_VERIFIED — AWAITING_USER_HOST_METADATA_AND_TECHNICAL_SMOKE.** Kullanıcı yeni adayı seçti: `{TAG}`. Codex indirme, Ollama API çağrısı veya inference yapmadı. Qwen3 4B modeli/kayıtları ve WP00–WP12 sonuçları silinmedi/değiştirilmedi.19 dondurulmuş senaryo, AGENTS, ROADMAP ve PDF sözleşmeleri korundu.

## 1. Gerçek model kimliği ve digest ayrımı
Yerel tam tag önbelleği zaten mevcut bulundu. Bu gözlem, indirmeyi Codex'in yaptığı anlamına gelmez; kullanıcı teslim olayı veya API doğrulaması uydurulmadı. Bloblar1MiB parçalarla hash'lendi, model inference için yüklenmedi. Config dahil6 dosyanın boyut ve tam SHA-256 kontrolleri geçti.

| Alan | Gerçek kayıt |
|---|---|
| Yeni aday ID | {identity['candidate_id']} |
| Seçilen tag | {TAG} |
| Yerel manifest tam digest | {digest} |
| İçerilen üst kaynak manifesti | {identity['source_manifest_digest']} |
| Model katmanı digest | sha256:2f8c3d137f2496dcb4019e17a50f2974b89c1be1a742db3c80cc86f91cafeeef |
| Ağırlık katmanı | 806.058.400bayt ≈0,751GiB; Q4_K_M |
| Yerel config | gemma3;999.89M;GGUF; requires0.30.0 |
| Kullanıcı API'sinin bildirdiği digest | **PENDING**; Codex yerel servise bağlanmadı |

Yerel manifestin digest'i313f… ile içindeki üst manifestin9755… digest'i farklı kayıt nesnelerinin hash'leridir; birbirinin yerine yazılmaz. Yerel manifest üst manifesti ayrı bir layer olarak içerir. Üst manifestte aynı ağırlık/template/license/params bağlantıları ve runner=llamacpp bulunur. Bütün ilgili dosyaların hash'leri doğrulandı. [Resmi tam tag sayfası](https://ollama.com/library/gemma3:1b-it-q4_K_M)806MB/Q4_K_M ve97558784bdc9 kısa kaydını gösteriyor. Yerel tam kimlik ayrı saklandı; dosya tutarlılığı yayıncı özgünlüğü/klinik doğruluk onayı değildir.

Koşullu smoke betiği API'de **yerel tam digest'in** aynısını arar. API farklı bir digest döndürürse önce metadata kaydı incelenir; sessizce9755… veya başka bir tag'e geçilmez, inference yapılmaz. Yerel config'in requires0.30.0 şartı da kontrol edilir. Önceki kullanıcı Qwen kaydındaki servis0.40.6 tarihsel bilgidir; yeni Gemma çalışmasında sürüm tekrar alınacaktır. Resmi aile sayfasındaki genel0.6+ bilgisi bu gerçek artefaktın0.30.0 config şartının yerine geçirilmez.

## 2. RAM/VRAM yeniden değerlendirmesi
Güncel salt okunur ölçüm: **{h['captured_at']}**; toplam RAM{ram['total']/2**30:.2f}GiB, boş RAM**{ram['available']/2**30:.2f}GiB**, kullanım%{ram['percent']}. GPU{gpu['name']}, toplam{gpu['total_MiB']}MiB, boş**{gpu['free_MiB']}MiB**. Bu tur yerel API bağlantısı denenmedi.

Gemma ağırlık katmanı≈0,751GiB; mevcut Qwen4B'nin önceden doğrulanmış2.497.280.480bayt katmanı≈2,326GiB. Ağırlık farkı≈1,575GiB'dir; bu değer **ölçülmüş RAM/VRAM tasarrufu değildir**. KV cache,2048context, motor çalışma alanı, host/GPU kopyaları ve diğer süreçler ek bellek gerektirir. Dosya boyutundan kesin çalışma belleği hesaplanmadı. Daha küçük model için Türkçe kaynak sadakati/negasyon başarısı garanti edilmez.

**3GiB boş host RAM ve2560MiB (2,5GiB) boş VRAM tabanı aynen korunmuştur.** Daha düşük eşik önerilmedi; bu sürüm eşik gevşetmesi değildir. Sebep: bu makinede gerçek Gemma tepe belleği henüz ölçülmedi, son RAM ölçümü tabanın altında ve yalnız ağırlık boyutuna bakarak güvenlik payını küçültmek için kanıt yok. İleride alt eşik gerekirse yeni, açık karar sürümü gerekir; mevcut betikte bypass/override parametresi yoktur. Tabanın sağlanması da sığma garantisi değildir. [Ollama context belgesi](https://docs.ollama.com/context-length) büyüyen bağlamın bellek maliyetini açıklar; ilk smoke context2048 kalır.

## 3. Bağımsız kullanıcı PowerShell akışı
Gemma cache'i mevcut olduğu için yeniden indirme talep etmiyoruz. Kullanıcı kendi PowerShell'inde gerekirse yalnız seçilmiş tag'i indirir (`ollama pull gemma3:1b-it-q4_K_M`); bu komut **Codex tarafından çalıştırılmadı**, betik de pull/install içermez. Qwen için remove/rm komutu yoktur.

Önce yalnız metadata ve bellek kontrolü:

```powershell
& '{ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1'}'
```

Koşullar sağlanınca yalnız tek teknik JSON Schema smoke testi:

```powershell
& '{ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1'}' -RunSmoke
```

Yeni betik Qwen betiğinden ayrı, sürümlü bir dosyadır; eski dosya ezilmedi. Model/tag/digest, teknik probe, kayıt dizini ve minimum artefakt sürümü farklıdır; eşikler, context2048, çıktı384, seed20261108, sıcaklık0, stream:false, think:false ve keep_alive0 korunur. Modellerde thinking desteği aynı varsayılmaz: API bu alanı reddederse hata aynen kaydedilir; alanı kaldırıp sessiz fallback yoktur. Yeni örnek arama/hiperparametre optimizasyonu yapılmaz.

Normal kullanıcı PowerShell'i/non-AppContainer; yalnız127.0.0.1; proxy/redirect kapalı; servis başlatma/guvenlik değişikliği yok. API version/tags/ps metadata alınır; farklı digest veya yüklü model varsa otomatik değişiklik yapılmadan durulur. RAM/VRAM inference'tan hemen önce tekrar ölçülür. En çok bir istek,60sn istemci timeout'u; timeout sunucu tamamlanmasını kanıtlamaz ve otomatik retry yapılmaz. Host RAM örnekleri ve başlangıç/son GPU ölçümleri kaydedilir; kesin tepe bellek veya genel kalite iddiası yapılmaz.

Bu, klinik içeriksiz **WP12_GEMMA1B_SMOKE_V1** echo testidir; gerçek PDF açıklaması değildir. Şema kontrollü tek yanıtın tutarlılığını sınar. Başarı,19×3 için otomatik izin veya kaynak anlam sadakati kanıtı olmayacaktır. `reported_in_PDF`/`predicted_by_GNN` ayrımı,44 alıntı ve insan semantik inceleme şartı değişmez. Sahte prospektüs, yeni MedDRA/yan etki, model skoru, SHAP veyaΔz üretilmez.

## 4. Ayrı gerçek çıktı ve inceleme kaydı
Betik her denemeyi reports/qa/WP12/gemma1b_user_smoke_runs/tarih_GUID altında yeni kayda yazar. Ham metadata, sabit istek SHA, gerçek yanıt varsa ham yanıt ve bellek örnekleri korunur. Henüz Gemma gerçek API/çıkarım sonucu yoktur; conditional_run_record.json sonuçnull ile bekler.

Kullanıcı oluşan tam klasör yolunu paylaştığında ağsız doğrulayıcı kullanılabilir:

```powershell
python '{ROOT/'scripts/wp12_gemma_smoke_review.py'}' '<gerçek Gemma çıktı klasörü>'
```

Doğrulayıcı yalnız Gemma dizinini/modelini/digest'ini kabul eder; Qwen çıktısını Gemma gibi sunmaz. Yeni inceleme kaydı gemma1b_user_smoke_reviews/UUID altına yazılır; eski ham kayıtlar değişmez. Dosya hash'i tutarlılık sağlar, gerçek çalışmanın kriptografik tasdiki değildir. İnsan semantik onayı veya otomatik yayın yoktur.

## 5. Önceki kullanıcı Qwen kayıtlarının verdiği ek kanıt
Önceden normal PowerShell'de oluşturulmuş **{oldruns} gerçek Qwen kayıt** bulundu ve dosya manifestleri doğrulandı. İkisinde de **is_appcontainer=false**, servis0.40.6, exact Qwen digest ve STOP_MEMORY_GATE/inference0 görülüyor. Bu nedenle eski bekleme kaydı tarihsel haliyle korunurken yeni ek kayıtta kullanıcı API erişiminin çalışmış olduğu belirtilir. Bu, Codex10013 ile kullanıcı ortamını ayıran kanıttır; belirli firewall kuralı veya Gemma inference başarısı kanıtı değildir. Eski kayıtların/modelin hiçbirini silmedik/değiştirmedik.

## 6. QA ve durma noktası
Gemma betiği yalnız PowerShell AST ayrıştırmasından geçer; burada çalıştırılmaz.12 Gemma doğrulayıcı testi +12 Qwen doğrulayıcı +6 bellek +24 kaynak sözleşmesi =54 offline test; teknik fixture'lar gerçek LLM çıktısı değildir. Yeni Gemma kodu sürümlü fork olarak kayıtlı; kabul edilmiş eski kodların refaktörü/üzerine yazılması yoktur.

Önceki3.372 proje dosyası (gerçek kullanıcı Qwen çıktıları dahil),19 senaryo ve bütün sözleşmeler başlangıç SHA ile korunur. Qwen cache manifesti0edc… aynı kalır; büyük Qwen ağırlıkları gereksiz yeniden taranmadı. run_status önceki tam baytlarını arşivleyerek güncellenir. Bu noktada kullanıcı Gemma metadata/smoke çıktısı beklenir; Codex indirme/servis erişimi/inference,19×3, yeni eğitim veya WP13 yoktur.
''',encoding='utf-8')
    return report


def notebook():
    from wp09_close_wp10_notebooks import execute
    execute('WP12_gemma1b_candidate.ipynb',[
        ('md','# WP12 — Gemma3 1B model değişimi ve koşullu smoke hazırlığı\nKullanıcı yeni modeli seçti. Bu notebook gerçek cache/ölçüm/QA okur; Ollama API, model indirme veya inference içermez. Eski Qwen kayıtları ve19 senaryo korunur.'),
        ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/gemma1b_candidate_v1'\ni=json.loads((Q/'model_identity.json').read_text(encoding='utf-8'));h=json.loads((Q/'hardware_snapshot.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([{'Aday':i['candidate_id'],'Yerel manifest':i['local_manifest_digest'],'Üst kaynak manifest':i['source_manifest_digest'],'Bütün hashler':i['all_content_hashes_valid'],'API digest':i['API_reported_digest']}]).T)\ndisplay(pd.DataFrame(i['config_and_layers'])[['mediaType','size','digest','valid']])"),
        ('md','**Yorum:**313f… yerel manifest ile9755… içerilen kaynak manifest farklı nesnelerdir. Tam hashler korunur; API digest henüz doğrulanmadı. Yerel cache varlığı bir inference başarısı değildir.'),
        ('code',"display(pd.DataFrame([{'Ölçüm':h['captured_at'],'Boş RAM GiB':h['RAM']['available']/2**30,'Boş VRAM MiB':h['GPU']['free_MiB']}]))\nfig,ax=plt.subplots(figsize=(7,3));ax.bar(['Gemma1B','Qwen4B'],[806058400/2**30,2497280480/2**30]);ax.set_ylabel('Yalnız ağırlık katmanı GiB');ax.set_title('Çalışma RAM/VRAM ölçümü değildir')\nF=ROOT/'reports/figures/WP12/gemma1b_candidate_v1';F.mkdir(parents=True,exist_ok=True);fig.tight_layout();fig.savefig(F/'weight_sizes.png',dpi=150);plt.show()"),
        ('md','**Yorum:**Daha küçük ağırlık daha düşük potansiyel yük sağlar; runtime/KV/diğer süreçler hesaba katılmadan eşik düşürülmez.3GiB host RAM/2560MiB VRAM kapısı aynen kalır; gerçek tepe bellek ve Türkçe kaynak sadakati ölçülmedi.'),
        ('code',"display(pd.DataFrame([json.loads((Q/'conditional_run_record.json').read_text(encoding='utf-8'))]).T)\ndisplay(pd.DataFrame(json.loads((Q/'existing_Qwen_user_runs_readonly_review.json').read_text(encoding='utf-8'))))\nprint((Q/'powershell_parse_check.txt').read_text(encoding='utf-8'))\nfor name in ['test_wp12_gemma_smoke_review.py.log','test_wp12_user_smoke_review.py.log','test_wp12_llm_preflight.py.log','test_wp12_llm_contract.py.log']:\n print(name);print((Q/name).read_text(encoding='utf-8'))"),
        ('md','**Yorum:**Eski gerçek Qwen host kayıtlarında API çalışmış, bellek kapısı durmuş; bunlar Gemma başarısı değildir.54 offline test ve parse kontrolü, gerçek Gemma smoke testi değildir. Kaynak/PDF semantik onayı veya19×3 çalışma yoktur. Kullanıcı çıktısı beklenir; WP13 başlamadı.')])


def close(report):
    prior=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in prior.items())
    locked=json.loads((ROOT/'reports/qa/WP12/local_llm_pilot_v1/approved_candidate_record.json').read_text(encoding='utf-8'))
    assert sha(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')==locked['frozen_scenarios_sha256']
    assert sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md')==locked['existing_contract_sha256']
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    identity=json.loads((QA/'model_identity.json').read_text(encoding='utf-8'))
    prefix=f'''# WP12 Gemma1B yeni aday — kullanıcı API/smoke kaydı bekleniyor ·08.11.2026

- Kullanıcı gemma3:1b-it-q4_K_M seçti. Cache zaten mevcut; Codex indirmedi/servise bağlanmadı/inference yapmadı. Yeni aday kimliği ve tam yerel manifest313f…/üst kaynak9755… ayrı kaydedildi;6 dosya hash kontrolü geçti. API digest PENDING.
-3GiB boş RAM/2560MiB boş VRAM tabanı aynen korundu; eşik gevşetilmedi. Yalnız kullanıcı PowerShell'inde tek teknik JSON Schema smoke betiği hazır; varsayılan metadata-only. Gerçek19×3 çalışması, eğitim veya WP13 yok.
- Qwen4B cache ve bütün eski kayıtlar korundu. İki gerçek kullanıcı Qwen metadata kaydı hash ile doğrulandı; API0.40.6/non-AppContainer erişimi var, STOP_MEMORY_GATE/inference0. Bu, Gemma başarısı değildir.
-54 offline test ve Gemma PS AST kontrolü geçti; gerçek host smoke henüz NOT_RUN. Yeni kullanıcı kayıt/inceleme dizinleri Gemma'ya özeldir; otomatik açıklama yayını yok.
- Önceki{len(prior)} dosya ve19 senaryo korundu. Rapor reports/WP12_GEMMA1B_CANDIDATE.md; config configs/WP12_GEMMA1B_CONDITIONAL_v1.json; QA reports/qa/WP12/gemma1b_candidate_v1/; notebook notebooks/WP12_gemma1b_candidate.ipynb.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if k=='run_status.md' else ROOT/k)==v for k,v in prior.items())
    save(QA/'artifact_validation.json',{'status':'AWAITING_USER_GEMMA_METADATA_AND_TECHNICAL_SMOKE',
        'prior_artifacts_preserved':len(prior),'source_quotes_unchanged':44,'frozen_scenarios_unchanged':19,
        'model_identity':identity['candidate_id'],'model_local_digest':identity['local_manifest_digest'],
        'API_digest_verified':False,'verified_config_and_layers':6,'thresholds_changed':False,
        'minimum_host_available_bytes':3221225472,'minimum_GPU_free_MiB':2560,
        'offline_tests_passed':54,'PowerShell_AST_parse_errors':0,'Gemma_smoke_runtime':'NOT_RUN',
        'Codex_downloads':0,'Codex_local_API_calls':0,'inference_calls':0,'real_scenario_repeats':0,
        'existing_Qwen_host_records_readonly_reviewed':2,'Qwen_model_deleted_or_changed':False,
        'notebook_executed_cells':3,'static_PNGs':1,'new_training':False,'WP13_started':False,
        'prior_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,ROOT/'configs/WP12_GEMMA1B_CONDITIONAL_v1.json',
        ROOT/'scripts/wp12_gemma_candidate.py',ROOT/'scripts/wp12_gemma_smoke_review.py',
        ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1',ROOT/'tests/test_wp12_gemma_smoke_review.py',
        ROOT/'notebooks/WP12_gemma1b_candidate.ipynb',ROOT/'reports/figures/WP12/gemma1b_candidate_v1/weight_sizes.png',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('Gemma separate candidate complete; protected',len(prior),'offline tests54; no inference/API/download')


if __name__=='__main__':main()
