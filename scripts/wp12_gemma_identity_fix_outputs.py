"""Kimlik düzeltmesi v2.1; önceki v2 dosyalarını değiştirmez, smoke çalıştırmaz."""
import difflib
import json
from pathlib import Path
import subprocess
import sys
from wp12_local_llm_preflight import ROOT,sha,save

QA=ROOT/'reports/qa/WP12/gemma1b_identity_fix_v1'
API='sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c'
LOCAL='sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16'


def main():
    assert not (QA/'artifact_validation.json').exists()
    if '--finish-existing-draft' in sys.argv:
        finish_existing()
        return
    helper=ROOT/'scripts/WP12_GemmaIdentity_v1.ps1'
    old=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2.ps1'
    target=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1';assert not target.exists()
    original=old.read_text(encoding='utf-8');text=original
    for a,b in {'WP12-gemma1b-user-smoke-run-v2':'WP12-gemma1b-user-smoke-run-v2_1',
                'gemma1b_v2_user_smoke_runs':'gemma1b_v2_1_user_smoke_runs'}.items():text=text.replace(a,b)
    text=text.replace("    expected_digest = '"+LOCAL+"'",
        "    expected_digest = '"+API+"'\n    local_wrapper_expected_sha256 = '"+LOCAL+"'\n    identity_binding_version = 'WP12-gemma-api-source-v1'\n    identity_helper_sha256 = '"+sha(helper)+"'")
    guard="    if ($digest -cne $record.expected_digest) { throw 'MODEL_DIGEST_MISMATCH: do not silently switch model' }"
    fixed='''    $identityHelper = Join-Path $PSScriptRoot 'WP12_GemmaIdentity_v1.ps1'
    $actualHelperHash = (Get-FileHash -LiteralPath $identityHelper -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHelperHash -cne $record.identity_helper_sha256) { throw 'IDENTITY_HELPER_SHA256_MISMATCH' }
    . $identityHelper
    $modelRoot = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { Join-Path ([Environment]::GetFolderPath('UserProfile')) '.ollama\\models' }
    $record['identity_validation'] = Assert-WP12GemmaIdentity -ModelRoot $modelRoot -ApiDigest $digest'''
    assert guard in text;text=text.replace(guard,fixed)
    target.write_text('# Identity fix only; memory policy v2 and request payload unchanged.\n'+text,encoding='utf-8')
    (QA/'runner_identity_only.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),target.read_text(encoding='utf-8').splitlines(True),fromfile=old.name,tofile=target.name)),encoding='utf-8')
    # Bütün payload ve bellek kontrol kaynak blokları birebir kalmalı.
    def block(s,start,end):return s[s.index(start):s.index(end,s.index(start))]
    invariants={
        'payload_source_identical':block(original,'    $schema = @{','    $requestText =')==block(text,'    $schema = @{','    $requestText ='),
        'native_memory_and_GPU_functions_identical':block(original,'    if (-not (\'WP12GemmaSmokeNativeV2\'','    $record[\'is_appcontainer\']')==block(text,'    if (-not (\'WP12GemmaSmokeNativeV2\'','    $record[\'is_appcontainer\']'),
        'admission_and_commit_and_stability_identical':block(original,'    if ($record.is_appcontainer)','    $schema = @{')==block(text,'    if ($record.is_appcontainer)','    $schema = @{'),
        'immediate_gates_and_all_inference_control_identical':original[original.index("    $record['memory_immediately_before']"):]==text[text.index("    $record['memory_immediately_before']"):],
        'timeout_line_identical':"$apiClient.Timeout = [TimeSpan]::FromSeconds(60)" in original and "$apiClient.Timeout = [TimeSpan]::FromSeconds(60)" in text}
    assert all(invariants.values()),invariants
    save(QA/'identity_only_invariants.json',invariants)
    make_reviewer_tests()
    base=json.loads((ROOT/'configs/WP12_GEMMA1B_MEMORY_POLICY_v2.json').read_text(encoding='utf-8'))
    cfg=dict(base);cfg.pop('manifest_digest')
    cfg.update(version='WP12-gemma1b-v2+identity-fix-v1',memory_policy_version=base['version'],
        identity_binding_version='WP12-gemma-api-source-v1',expected_API_model_digest=API,
        local_wrapper_manifest_file_sha256=LOCAL,source_manifest_file_sha256=API,
        runner_sha256=sha(target),identity_helper_sha256=sha(helper),
        status='IDENTITY_FIXED_AWAITING_USER_SINGLE_SMOKE',
        runner='scripts/WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1',
        reviewer='scripts/wp12_gemma_v2_1_smoke_review.py')
    for k in ['v2_admission','runtime_host_warning_bytes','reference_critical_floor_bytes','warning_action',
              'num_ctx','num_predict','num_batch','temperature','seed','think','stream','keep_alive','max_requests','HTTP_timeout_seconds']:
        assert cfg[k]==base[k]
    save(ROOT/'configs/WP12_GEMMA1B_IDENTITY_FIX_v2_1.json',cfg)
    finish_existing()


def finish_existing():
    assert not (QA/'artifact_validation.json').exists()
    helper=ROOT/'scripts/WP12_GemmaIdentity_v1.ps1'
    old=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2.ps1'
    target=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1'
    cfg=json.loads((ROOT/'configs/WP12_GEMMA1B_IDENTITY_FIX_v2_1.json').read_text(encoding='utf-8'))
    base=json.loads((ROOT/'configs/WP12_GEMMA1B_MEMORY_POLICY_v2.json').read_text(encoding='utf-8'))
    assert cfg['runner_sha256']==sha(target) and cfg['identity_helper_sha256']==sha(helper)
    # Yalnız saf kimlik fonksiyonu; runner/inference çalıştırılmaz.
    log=QA/'PowerShell_identity_regressions.json'
    cmd="& '"+str(ROOT/'tests/test_wp12_gemma_identity.ps1')+"' -OutputPath '"+str(log)+"'"
    if not log.exists():
        ps=subprocess.run(['pwsh','-NoProfile','-Command',cmd],capture_output=True,text=True,timeout=60)
        (QA/'PowerShell_identity_regressions_native.txt').write_text(ps.stdout+ps.stderr,encoding='utf-8');assert ps.returncode==0,ps.stderr
    results=json.loads(log.read_text(encoding='utf-8-sig'));assert results['count']==9 and all(x['status']=='PASS' for x in results['results'])
    for pattern in ['test_wp12_gemma_v2_1_smoke_review.py','test_wp12_gemma_failure_diagnosis.py']:
        t=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        (QA/(pattern+'.log')).write_text(t.stdout+t.stderr,encoding='utf-8');assert t.returncode==0,t.stderr
    cmd="$bad=0;foreach($p in @('"+str(target)+"','"+str(helper)+"')){$t=$null;$e=$null;$null=[System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e);$bad+=$e.Count;if($e.Count){$e|Out-String}};if($bad){exit 1};'ParseErrors=0; identity helper and v2.1 runner'"
    parsed=subprocess.run(['powershell','-NoProfile','-Command',cmd],capture_output=True,text=True,timeout=30)
    (QA/'PowerShell_syntax_check.txt').write_text(parsed.stdout+parsed.stderr,encoding='utf-8');assert parsed.returncode==0
    save(QA/'runner_sha256.json',{'runner':target.relative_to(ROOT).as_posix(),'sha256':sha(target),
        'identity_helper':helper.relative_to(ROOT).as_posix(),'helper_sha256':sha(helper),
        'old_v2_runner_sha256':sha(old),'old_v2_unchanged':sha(old)==base['runner_sha256'],
        'PowerShell_syntax_errors':0,'identity_tests_executed_in':'native PowerShell; version in PowerShell_native_engine.json; no HTTP/inference',
        'PowerShell_5_1_test_file_execution':'blocked by AuthorizationManager; no execution-policy change; parser check succeeded'})
    report=write_report(target,cfg);notebook();close(report,target,results['count'])


def make_reviewer_tests():
    replacements={
        "DIGEST='"+LOCAL+"'":"DIGEST='"+API+"'",
        'WP12-gemma1b-user-smoke-run-v2':'WP12-gemma1b-user-smoke-run-v2_1',
        'WP12_Gemma1B_UserPowerShellSmoke_v2.ps1':'WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1',
        'gemma1b_v2_user_smoke_runs':'gemma1b_v2_1_user_smoke_runs',
        'gemma1b_v2_user_smoke_reviews':'gemma1b_v2_1_user_smoke_reviews',
        'import wp12_gemma_v2_smoke_review as v':'import wp12_gemma_v2_1_smoke_review as v'}
    for a,b in [('scripts/wp12_gemma_v2_smoke_review.py','scripts/wp12_gemma_v2_1_smoke_review.py'),
                ('tests/test_wp12_gemma_v2_smoke_review.py','tests/test_wp12_gemma_v2_1_smoke_review.py')]:
        text=(ROOT/a).read_text(encoding='utf-8')
        for old,new in replacements.items():text=text.replace(old,new)
        if b.startswith('scripts/'):
            marker="    require(r['inference_attempts'] in (0,1)"
            extra="    require(r.get('local_wrapper_expected_sha256')=='"+LOCAL+"','local wrapper identity changed')\n    require(r.get('identity_helper_sha256')==sha(ROOT/'scripts/WP12_GemmaIdentity_v1.ps1'),'identity helper changed')\n"
            assert marker in text;text=text.replace(marker,extra+marker)
            marker="    require(r.get('memory_policy')"
            extra="    iv=r.get('identity_validation',{})\n    require(iv.get('identity_binding_valid') is True and iv.get('config_and_layer_references_equal') is True,'identity lineage not verified')\n    require(iv.get('local_wrapper_manifest_file_sha256')=='"+LOCAL+"','wrapper SHA mismatch')\n    require(iv.get('expected_API_model_digest')==DIGEST and iv.get('observed_API_model_digest')==DIGEST and iv.get('source_manifest_file_sha256')==DIGEST,'API/source identity mismatch')\n"
            assert marker in text;text=text.replace(marker,extra+marker)
        else:
            marker="        self.record['memory_policy']"
            extra="        self.record['local_wrapper_expected_sha256']='"+LOCAL+"'\n        self.record['identity_helper_sha256']=v.sha(v.ROOT/'scripts/WP12_GemmaIdentity_v1.ps1')\n        self.record['identity_validation']={'identity_binding_valid':True,'config_and_layer_references_equal':True,'local_wrapper_manifest_file_sha256':'"+LOCAL+"','expected_API_model_digest':v.DIGEST,'observed_API_model_digest':v.DIGEST,'source_manifest_file_sha256':v.DIGEST}\n"
            assert marker in text;text=text.replace(marker,extra+marker)
        target=ROOT/b;assert not target.exists();target.write_text(text,encoding='utf-8')


def write_report(runner,cfg):
    p=ROOT/'reports/WP12_GEMMA1B_IDENTITY_FIX.md';assert not p.exists()
    p.write_text(f'''# WP12 — Gemma kimlik kontrolü düzeltmesi v2.1

**IDENTITY_FIXED — AWAITING_USER_SINGLE_SMOKE.** Kullanıcının onayıyla yalnız API/yerel dosya kimlik bağlaması düzeltildi. Eski v2 betiği/config/inceleyici, iki gerçek başarısız deneme ve önceki sonuçlar değişmedi. Yeni sürüm: `{runner.relative_to(ROOT).as_posix()}`. Bu tur smoke/inference/API/indirme yapılmadı.

## Değişen kontrol
API için beklenen model/source manifest digest: **{API}**. Yerel wrapper dosyasının ayrı SHA-256 değeri: **{LOCAL}**. Yeni saf PowerShell yardımcısı API digest'ini ilk değerle karşılaştırır; gerçek wrapper dosyasını hash'leyip ikinci değerle karşılaştırır. Ardından wrapper'ın içerdiği kaynak manifesti hash'ler ve config/katman referanslarının aynı kaldığını doğrular. Kontrol kaldırılmadı; yanlış API kimliği veya değiştirilmiş metadata reddedilir. GGUF ağırlık dosyası bu kimlik kontrolünde yeniden okunmaz/yüklenmez; hash kontrolü wrapper ve kaynak manifest dosyalarına uygulanır.

Yardımcı betiğin SHA'sı da runner'a sabitlendi. Gerçek kullanıcı kaydında API digest, wrapper SHA ve kaynak SHA ayrı `identity_validation` alanlarında tutulur. Eski iki kaydı yeni digest ile yeniden yazmak veya başarıya çevirmek yoktur. v2.1 sonuç/inceleme dizinleri ayrıdır; probe/payload mantığı aynıdır.

## Değişmeyen koşullar
RAM **2,5GiB**, VRAM **2048MiB (2GiB)**, commit boşluğu **3GiB**, beş kararlı örnek/en az4sn, host uyarı sınırı1GiB ve **60sn timeout** aynen korundu. Context2048, çıktı384, batch32, seed20261108, sıcaklık0, think:false, stream:false ve keep_alive0 değişmedi. Payload, native ölçüm fonksiyonları, bellek/commit/kararlılık kapıları ve inference/iptal akışı kaynak blokları birebir karşılaştırıldı. Bir istek sınırı, retry/download yasağı ve19×3 kapısı aynı kaldı. Kimlik düzeltmesi RAM uygunluğunu veya modelin çalışmasını garanti etmez.

## Doğrulama
Ortamın varsayılan PowerShell motorunda **9 gerçek offline kimlik regresyonu** geçti: gerçek yerel cache+doğru API kimliği, raw/prefix biçimi, API yerine wrapper hash'inin reddi, yabancı digest, değiştirilmiş wrapper, değiştirilmiş kaynak manifest, yalnız küçük metadata kopyasıyla doğrulama ve iki eski gerçek API kaydının doğru kimlikle eşleşmesi. Testlerde HTTP, Ollama servisi veya inference yoktur. Yalnız testin kendi doğrulanmış TEMP dizinindeki küçük metadata kopyaları kullanılıp temizlendi; model dosyaları değişmedi. Gerçek motor sürümü PowerShell_native_engine.json içinde kayıtlıdır. İlk Windows PowerShell5.1 test dosyası çağrısı AuthorizationManager erişim hatası verdi; başarısız log korundu, yetki/ExecutionPolicy değiştirilmedi. Aynı yetkili offline test standart varsayılan motorla çalıştı; Windows PowerShell5.1 runtime başarısı iddia edilmez. PS5.1 ayrıştırıcısıyla runner/helper sözdizimi kontrolü ayrıca geçti.

Yeni inceleyici12 offline testi ve eski iki başarısız denemenin8 teşhis testi de geçti: **toplam29 test**. Bunlar gerçek yeni smoke başarısı değildir. Güncel runner ve yardımcı betik Windows PowerShell ayrıştırıcısından **0 sözdizimi hatasıyla** geçti.

Runner SHA-256: `{cfg['runner_sha256']}`.

Yardımcı SHA-256: `{cfg['identity_helper_sha256']}`.

Sabitler ve kaynak-block eşitliği `reports/qa/WP12/gemma1b_identity_fix_v1/identity_only_invariants.json`, salt kimlik farkı `runner_identity_only.diff`, test/parse/hash kanıtları aynı yeni QA dizinindedir. Önceki bütün dosyalar başlangıç manifestiyle korunur; yalnız run_status öne eklenir, önceki tam baytları arşivlenir. Notebook gerçek test tablolarını ve doğru/yanlış kimlik ayrımını gösterir.

## Kullanıcının tek smoke komutu
Normal PowerShell'de RAM koşullarını sağladıktan sonra:

```powershell
& '{runner}' -RunSmoke
```

Betik bütün mevcut kapıları tekrar denetler; koşullar sağlanmazsa model yüklemeden durur. Çıktı yeni `reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/tarih_GUID/` dizinine gider. Yeni `scripts/wp12_gemma_v2_1_smoke_review.py` yalnız bu sürümün gerçek çıktılarını inceler; eski v2 inceleyici değişmez. Kullanıcı gerçek klasör yolunu paylaşınca ayrı inceleme yapılabilir. Yeni inference çalıştırılmadı; gerçek19×3, model indirme, eğitim veya WP13 başlamadı.
''',encoding='utf-8')
    return p


def notebook():
    from wp09_close_wp10_notebooks import execute
    execute('WP12_gemma1b_identity_fix.ipynb',[
        ('md','# WP12 — Yalnız kimlik kontrolünün düzeltilmesi\nAPI digest ve yerel dosya hash farklı rollerdir. Yeni v2.1 ayrı dosyada; v2 ve eski iki deneme korunur. Model/API/inference çalıştırılmaz.'),
        ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/gemma1b_identity_fix_v1'\nc=json.loads((ROOT/'configs/WP12_GEMMA1B_IDENTITY_FIX_v2_1.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([{'Rol':'API/source model digest','SHA':c['expected_API_model_digest']},{'Rol':'Yerel wrapper dosya SHA','SHA':c['local_wrapper_manifest_file_sha256']},{'Rol':'Kaynak manifest dosya SHA','SHA':c['source_manifest_file_sha256']}]))\ndisplay(pd.DataFrame([json.loads((Q/'identity_only_invariants.json').read_text(encoding='utf-8'))]).T)"),
        ('md','**Yorum:**API için9755… ile yerel wrapper313f… artık ayrı kontrol edilir. Kaynak manifestin hash\'i ve katman bağlantıları aynı model soyunu doğrular. Eşik/timeout veya payload değiştirilmedi.'),
        ('code',"r=json.loads((Q/'PowerShell_identity_regressions.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame(r['results']))\nfig,ax=plt.subplots(figsize=(7,2.5));ax.bar(['PowerShell kimlik','Yeni inceleyici','Eski kayıt teşhisi'],[9,12,8]);ax.set_ylabel('Geçen offline test');ax.set_title('Gerçek model/smoke başarı metriği değildir');fig.tight_layout();F=ROOT/'reports/figures/WP12/gemma1b_identity_fix_v1';F.mkdir(parents=True,exist_ok=True);fig.savefig(F/'regression_checks.png',dpi=150);plt.show()"),
        ('md','**Yorum:**Kimlik fonksiyonu varsayılan PowerShell motorunda yalnız yerel metadata ve geçmiş API dosyalarıyla sınandı. Windows PowerShell5.1 dosya çalıştırması yetkilendirme engeline takıldı; bu motor için runtime başarısı iddia edilmez. Smoke runner çalıştırılmadı. Yanlış API hash\'i ve bozuk dosya ayrı reddediliyor.'),
        ('code',"display(pd.DataFrame([json.loads((Q/'runner_sha256.json').read_text(encoding='utf-8'))]).T)\nprint((Q/'PowerShell_syntax_check.txt').read_text(encoding='utf-8'))\nfor name in ['test_wp12_gemma_v2_1_smoke_review.py.log','test_wp12_gemma_failure_diagnosis.py.log']:\n print(name);print((Q/name).read_text(encoding='utf-8'))"),
        ('md','**Yorum:**Yeni v2.1 betiğinin sözdizimi ve SHA\'sı doğrulandı. RAM/GPU/commit/timeout ve19 senaryo değişmedi. Kullanıcı tek gerçek smoke kaydını üretmeden başarı iddiası yok; WP13 başlamaz.')])


def close(report,runner,count):
    prior=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in prior.items())
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    prefix=f'''# WP12 Gemma kimlik düzeltmesi v2.1 — tek kullanıcı smoke kaydı bekleniyor ·08.11.2026

- Yalnız kimlik bağlaması düzeltildi: API/source9755… ile yerel wrapper313f… ayrı. Yeni saf PS yardımcısı gerçek wrapper/kaynak dosyalarını hash'ler, aynı config/layer zincirini doğrular; yardımcı dosya SHA'sı da kilitli. Eski v2 ve iki başarısız deneme değişmedi.
- Yeni betik scripts/WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1; yeni inceleyici ve config ayrı.2,5GiB RAM/2048MiB VRAM/3GiB commit/60sn timeout ve bütün v2 payload/bellek akışı korundu.
-9 varsayılan PowerShell kimlik +12 inceleyici +8 eski kayıt testi geçti; runner/helper PS5.1 parse0 hata ve SHA doğrulandı. PS5.1 test dosyası çalıştırması AuthorizationManager engeline takıldı; güvenlik ayarı değiştirilmeden varsayılan motorda test edildi. Smoke runner/API/inference çalıştırılmadı. Model indirme/retry/19×3/WP13 yok.
- Önceki{len(prior)} dosya korundu. Rapor reports/WP12_GEMMA1B_IDENTITY_FIX.md; QA reports/qa/WP12/gemma1b_identity_fix_v1/; notebook notebooks/WP12_gemma1b_identity_fix.ipynb. Kullanıcının normal PowerShell'de üreteceği tek gerçek deneme bekleniyor.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if k=='run_status.md' else ROOT/k)==v for k,v in prior.items())
    save(QA/'artifact_validation.json',{'status':'IDENTITY_FIXED_AWAITING_USER_SINGLE_SMOKE',
        'prior_artifacts_preserved':len(prior),'failed_original_run_records_preserved':2,
        'old_v2_runner_config_reviewer_unchanged':True,'PowerShell_identity_tests_passed':count,
        'python_tests_passed':20,'total_tests_passed':29,'runner_and_helper_parse_errors':0,
        'runner_sha256':sha(runner),'identity_only_invariants_passed':True,
        'RAM_bytes_unchanged':2684354560,'GPU_MiB_unchanged':2048,'timeout_seconds_unchanged':60,
        'Codex_smoke_or_inference_calls':0,'API_calls':0,'downloads':0,'automatic_retries':0,
        'real_scenario_repeats':0,'WP13_started':False,'notebook_executed_cells':3,
        'prior_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,runner,ROOT/'scripts/WP12_GemmaIdentity_v1.ps1',
        ROOT/'scripts/wp12_gemma_v2_1_smoke_review.py',ROOT/'scripts/wp12_gemma_identity_fix_outputs.py',
        ROOT/'tests/test_wp12_gemma_identity.ps1',ROOT/'tests/test_wp12_gemma_v2_1_smoke_review.py',
        ROOT/'configs/WP12_GEMMA1B_IDENTITY_FIX_v2_1.json',ROOT/'notebooks/WP12_gemma1b_identity_fix.ipynb',
        ROOT/'reports/figures/WP12/gemma1b_identity_fix_v1/regression_checks.png',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('Identity fix complete; tests29; prior files preserved',len(prior),'no inference')


if __name__=='__main__':main()
