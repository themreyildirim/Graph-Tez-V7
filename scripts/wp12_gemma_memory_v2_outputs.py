"""Gemma v2 açık bellek politikası; model/API/indirme çalıştırmaz."""
import json
from pathlib import Path
import subprocess
import sys

from wp12_local_llm_preflight import ROOT,sha,save
from wp12_gemma_memory import MODEL_BLOB,read_metadata,budget,admission

QA=ROOT/'reports/qa/WP12/gemma1b_memory_v2'


def make_runner():
    old=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1'
    text=old.read_text(encoding='utf-8')
    replacements={
        'WP12GemmaSmokeNativeV1':'WP12GemmaSmokeNativeV2',
        'WP12-gemma1b-user-smoke-run-v1':'WP12-gemma1b-user-smoke-run-v2',
        'WP12_GEMMA1B_SMOKE_V1':'WP12_GEMMA1B_SMOKE_V2',
        'gemma1b_user_smoke_runs':'gemma1b_v2_user_smoke_runs',
        '3221225472':'2684354560','2560':'2048',
        'seed = 20261108 }':'seed = 20261108; num_batch = 32 }',
        "schema_version = 'WP12-gemma1b-user-smoke-run-v2'":"schema_version = 'WP12-gemma1b-user-smoke-run-v2'\n    memory_policy = 'WP12-gemma1b-memory-v2'",
        'load_percent = $m.load }':'load_percent = $m.load; commit_available_bytes = [WP12GemmaSmokeNativeV2]::ReadCommitAvailable() }',
        '$record.memory_before.available_bytes -lt 2684354560 -or $record.GPU_before.free_MiB -lt 2048':
            '$record.memory_before.available_bytes -lt 2684354560 -or $record.GPU_before.free_MiB -lt 2048 -or $record.memory_before.commit_available_bytes -lt 3221225472',
        '$record.memory_immediately_before.available_bytes -lt 2684354560 -or $record.GPU_immediately_before.free_MiB -lt 2048':
            '$record.memory_immediately_before.available_bytes -lt 2684354560 -or $record.GPU_immediately_before.free_MiB -lt 2048 -or $record.memory_immediately_before.commit_available_bytes -lt 3221225472'}
    for a,b in replacements.items():
        assert a in text,a;text=text.replace(a,b)
    marker=' public static Memory ReadMemory()'
    native=''' [StructLayout(LayoutKind.Sequential)] public struct Performance {
  public uint cb; public UIntPtr CommitTotal,CommitLimit,CommitPeak,PhysicalTotal,PhysicalAvailable,SystemCache,KernelTotal,KernelPaged,KernelNonpaged,PageSize;
  public uint HandleCount,ProcessCount,ThreadCount;
 }
 [DllImport("psapi.dll", SetLastError=true)] static extern bool GetPerformanceInfo(ref Performance p,uint cb);
 public static ulong ReadCommitAvailable() { Performance p=new Performance(); p.cb=(uint)Marshal.SizeOf(typeof(Performance));
  if(!GetPerformanceInfo(ref p,p.cb)) throw new Win32Exception();
  return (p.CommitLimit.ToUInt64()-p.CommitTotal.ToUInt64())*p.PageSize.ToUInt64(); }
'''
    assert marker in text;text=text.replace(marker,native+marker)
    marker='    $schema = @{'
    stable='''    $record['admission_samples'] = @()
    for ($j=0; $j -lt 5; $j++) {
        $sample = Sample-Memory
        $record.admission_samples += $sample
        if ($sample.available_bytes -lt 2684354560 -or $sample.commit_available_bytes -lt 3221225472) {
            $record.status = 'STOP_V2_STABILITY_OR_COMMIT_GATE'; return
        }
        if ($j -lt 4) { Start-Sleep -Milliseconds 1000 }
    }
'''
    assert marker in text;text=text.replace(marker,stable+marker)
    marker='        while (-not $task.IsCompleted) { $samples.Add((Sample-Memory)); Start-Sleep -Milliseconds 1000 }'
    monitor='''        while (-not $task.IsCompleted) {
            $sample = Sample-Memory; $samples.Add($sample)
            if ($sample.available_bytes -lt 1073741824) {
                $record['memory_warning'] = $true
                $record.status = 'SMOKE_CLIENT_CANCELLED_MEMORY_WARNING'
                $apiClient.CancelPendingRequests()
                break
            }
            Start-Sleep -Milliseconds 250
        }
        if ($record.status -ceq 'SMOKE_CLIENT_CANCELLED_MEMORY_WARNING') {
            throw 'HOST_RAM_BELOW_1GiB: HTTP cancellation only; server completion is unknown; no retry or process termination'
        }'''
    assert marker in text;text=text.replace(marker,monitor)
    text=text.replace("    $record.status = 'FAILED_OR_TIMED_OUT_NO_RETRY'",
        "    if ($record.status -cne 'SMOKE_CLIENT_CANCELLED_MEMORY_WARNING') { $record.status = 'FAILED_OR_TIMED_OUT_NO_RETRY' }")
    text=text.replace("$record['memory_after'] = Sample-Memory; $record['GPU_after'] = Sample-GPU",
        "$record['memory_after'] = Sample-Memory; $record['GPU_after'] = Sample-GPU\n        if ($record.memory_after.available_bytes -lt 1073741824 -and $record.status -ceq 'SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW') { $record.status = 'SMOKE_COMPLETED_WITH_MEMORY_WARNING' }")
    target=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2.ps1';assert not target.exists()
    target.write_text('# v2: explicitly separate policy; v1 files and decisions remain immutable.\n'+text,encoding='utf-8')
    return target


def make_reviewer_and_tests():
    replacements={
        'WP12-gemma1b-user-smoke-run-v1':'WP12-gemma1b-user-smoke-run-v2',
        'WP12_GEMMA1B_SMOKE_V1':'WP12_GEMMA1B_SMOKE_V2',
        'WP12_Gemma1B_UserPowerShellSmoke_v1.ps1':'WP12_Gemma1B_UserPowerShellSmoke_v2.ps1',
        'gemma1b_user_smoke_runs':'gemma1b_v2_user_smoke_runs',
        'gemma1b_user_smoke_reviews':'gemma1b_v2_user_smoke_reviews',
        'import wp12_gemma_smoke_review as v':'import wp12_gemma_v2_smoke_review as v',
        '3221225472':'2684354560','3221225471':'2684354559','2560':'2048',
        "'temperature':0,'seed':20261108}":"'temperature':0,'seed':20261108,'num_batch':32}"}
    for old,new in [('scripts/wp12_gemma_smoke_review.py','scripts/wp12_gemma_v2_smoke_review.py'),
                    ('tests/test_wp12_gemma_smoke_review.py','tests/test_wp12_gemma_v2_smoke_review.py')]:
        text=(ROOT/old).read_text(encoding='utf-8')
        for a,b in replacements.items():text=text.replace(a,b)
        if new.startswith('scripts/'):
            marker="    require(r['is_appcontainer'] is False"
            extra='''    require(r.get('memory_policy')=='WP12-gemma1b-memory-v2','v2 policy missing')
    stable=r.get('admission_samples',[])
    require(len(stable)==5,'five stability samples required')
    require(all(s['available_bytes']>=2684354560 and s['commit_available_bytes']>=3221225472 for s in stable),'stability/commit gate failed')
    span=datetime.datetime.fromisoformat(stable[-1]['at'])-datetime.datetime.fromisoformat(stable[0]['at'])
    require(span.total_seconds()>=4,'stability interval too short')
    for key in ('memory_before','memory_immediately_before'):
        require(r[key].get('commit_available_bytes',0)>=3221225472,'commit floor failed')
'''
            assert marker in text;text=text.replace(marker,extra+marker)
            text=text.replace("    base.update(status=", "    require(all(s['available_bytes']>=1073741824 for s in samples),'host memory warning in successful run')\n    base.update(status=")
        else:
            marker="        self.save('metadata_1_version.json'"
            extra='''        self.record['memory_policy']='WP12-gemma1b-memory-v2'
        for key in ('memory_before','memory_immediately_before'):
            self.record[key]['commit_available_bytes']=6*2**30
        self.record['admission_samples']=[{'at':f'2026-11-08T00:00:0{j}+00:00','available_bytes':4*2**30,'commit_available_bytes':6*2**30} for j in range(5)]
'''
            assert marker in text;text=text.replace(marker,extra+marker)
            text=text.replace("self.assertFalse(r['auto_release']);self.assertEqual(r['PDF_explanation_quality'],'NOT_TESTED')",
                "self.assertFalse(r['auto_release']);self.assertEqual(r['PDF_explanation_quality'],'NOT_TESTED')\n        self.save('memory_samples.json',[{'available_bytes':4*2**30},{'available_bytes':1073741823}]);self.seal()\n        with self.assertRaises(ValueError):v.validate_run(self.folder)")
        target=ROOT/new;assert not target.exists();target.write_text(text,encoding='utf-8')


def main():
    assert not (QA/'artifact_validation.json').exists()
    meta=read_metadata(MODEL_BLOB);b=budget(meta)
    save(QA/'GGUF_metadata.json',meta);save(QA/'memory_budget.json',b)
    runner=make_runner();make_reviewer_and_tests()
    h=json.loads((QA/'hardware_snapshot.json').read_text(encoding='utf-8'))
    identity=json.loads((ROOT/'reports/qa/WP12/gemma1b_candidate_v1/model_identity.json').read_text(encoding='utf-8'))
    config={
        'version':'WP12-gemma1b-memory-v2','status':'PROPOSED_CONDITIONAL_TECHNICAL_SMOKE_ONLY',
        'v1_retained':{'RAM_GiB':3,'VRAM_GiB':2.5,'decisions_rewritten':False},
        'model':'gemma3:1b-it-q4_K_M','manifest_digest':identity['local_manifest_digest'],
        'v2_admission':{'host_available_bytes':2684354560,'GPU_free_MiB':2048,
                        'system_commit_available_bytes':3221225472,'stable_host_samples':5,'stable_span_seconds_at_least':4},
        'runtime_host_warning_bytes':1073741824,'reference_critical_floor_bytes':805306368,
        'warning_action':'cancel client HTTP only; server may continue; no process/service termination or retries',
        'num_ctx':2048,'num_predict':384,'num_batch':32,'temperature':0,'seed':20261108,
        'think':False,'stream':False,'keep_alive':0,'max_requests':1,'HTTP_timeout_seconds':60,
        'budget_basis':'actual GGUF26layers/1KVhead/256K/256V; FP32fullcontextKV104MiB; runtime margins estimated not measured',
        'runtime_peak_known':False,'safe_execution_guaranteed':False,
        'budget_file':'reports/qa/WP12/gemma1b_memory_v2/memory_budget.json',
        'runner_sha256':sha(runner),'execution_location':'user non-AppContainer PowerShell only',
        'model_download':False,'server_restart':False,'real19x3_allowed':False,
        'source_contract_sha256':sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md'),
        'scenario_sha256':sha(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')}
    save(ROOT/'configs/WP12_GEMMA1B_MEMORY_POLICY_v2.json',config)
    admitted=admission(h['RAM']['available'],h['GPU']['free_MiB'],h['system_commit']['available_bytes'])
    save(QA/'decision.json',{'status':'WAIT_USER_HOST_V2_GATES; NO_MODEL_LOAD',
        'current_v2_admission':admitted,'current_free_host_GiB':h['RAM']['available']/2**30,
        'current_free_GPU_MiB':h['GPU']['free_MiB'],'memory_policy_version':config['version'],
        'sufficient_evidence_to_load_now':False,'runtime_peak_RAM_VRAM':'NOT_MEASURED',
        'actual_smoke_result':None,'Codex_inference_calls':0,'API_calls':0,'downloads':0,'real_scenario_repeats':0,
        'human_semantic_review':'NOT_PERFORMED_TECHNICAL_TEST_NOT_RUN','automatic_release':False,'WP13_started':False})
    for pattern in ['test_wp12_gemma_memory_v2.py','test_wp12_gemma_v2_smoke_review.py','test_wp12_llm_preflight.py','test_wp12_llm_contract.py']:
        t=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        (QA/(pattern+'.log')).write_text(t.stdout+t.stderr,encoding='utf-8');assert t.returncode==0,pattern
    command="$t=$null;$e=$null;$null=[System.Management.Automation.Language.Parser]::ParseFile('"+str(runner)+"',[ref]$t,[ref]$e);if($e.Count){$e|Out-String;exit 1};'ParseErrors=0; v2 script NOT executed'"
    p=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,timeout=30)
    (QA/'PowerShell_parse_check.txt').write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0
    report=report_file(h,b);notebook();close(report)


def report_file(h,b):
    p=ROOT/'reports/WP12_GEMMA1B_MEMORY_POLICY_v2.md';assert not p.exists()
    p.write_text(f'''# WP12 — Gemma1B v2 bellek politikası ve tek teknik test

**Yeni, açık v2 öneri; v1 ve eski kararlar değişmez.** Bu tur model yükleme/API/indirme yapılmadı.19×3 ve WP13 yok. Tekrarlanan v1 hazırlığı yerine modelin gerçek mimarisinden hesap ve tek kullanıcı komutu sunulur.

## 1. Gerçek kanıt
Mevcut806.058.400bayt GGUF dosyasının yalnız metadata bölümü okundu: GGUFv3,340tensor kaydı,42 metadata alanı,6.513.118bayt metadata aralığı; tensor verisi veya ağırlık tensörü yüklenmedi.26 katman,1KV başlığı, K256/V256, sliding-window512, eğitim context32768 gerçek dosyadan doğrulandı. Kaynak model/digest önceki kabul edilmiş kimliğiyle aynı; yeniden indirme yok.

KV hesabı: `katman × KV başlığı × context × (Kboyutu+Vboyutu) × eleman_baytı`. Context2048 için FP16=52MiB, FP32=104MiB. Sliding-window512 indirimi uygulanmadan bütün26 katman tam context varsayıldı; motorun gerçek layout/padding/dtype tahsisi ölçülmedi. Bunlar tensor KV içeriği için teorik hesaplar, toplam runtime belleği değildir. [GGUF uygulama metadata tanımları](https://github.com/ggml-org/llama.cpp/blob/master/gguf-py/gguf/constants.py). Google config sayfası erişilemediği için oradan değer doğrulanmış sayılmadı.

## 2. v2 sayısal bütçe ve gerekçe
| Kalem | Host bütçesi | GPU bütçesi | Kanıt türü |
|---|---:|---:|---|
| Tam dosya ağırlığı |0,751GiB|0,751GiB|Gerçek dosya boyutu; iki alana birden maliyet yazılması muhafazakâr senaryo|
| Tam context FP32 KV |104MiB|104MiB|Gerçek mimariden hesap; SWA indirimi yok|
| Runtime/allocator/compute payı |0,5GiB|0,5GiB|**Ölçülmemiş mühendislik bütçesi**|
| Host staging/ek pay |0,25GiB|—|**Ölçülmemiş ek bütçe**|
| Sistem/display için referans rezerv |0,75GiB|0,5GiB|Politika seçimi; kritik işletim sistemi sınırının resmi tanımı değil|
| Toplam |{b['host_budget_total_bytes']/2**30:.3f}GiB|{b['GPU_budget_total_bytes']/2**30:.3f}GiB|Garantili üst sınır değildir|
| Yukarı yuvarlanmış v2 başlangıç kapısı |**2,5GiB boş RAM**|**2GiB boş VRAM**|Yalnız Gemma tek teknik smoke için|

Runtime payları tahmindir; belgelenmiş tepe bellek ölçümü değildir. Bu nedenle eşik çalışma veya kritik seviyeye hiç düşmeme garantisi olarak sunulmaz. GPU'ya tüm ağırlıkların yerleştiği varsayılmadı; host bütçesinde tam ağırlık+KV tekrar sayıldı. [Ollama FAQ](https://docs.ollama.com/faq) CPU/GPU/karışık yerleşimi ayırır; gerçek yerleşim ancak koşullar sağlanırsa test çıktısıyla değerlendirilir.

v1 **3GiB RAM /2,5GiB VRAM** aynen saklanır. v2 düşüşü, yalnız1B'nin gerçek0,751GiB ağırlığı ve hesaplanan KV'si, küçük batch32 ve ek rezerv bütçesine dayanır. Bu seçim hiçbir model başarımı veya gerçek senaryo sonucuna göre yapılmadı. Context2048, çıktı384, seed20261108 ve sıcaklık0 korunur; **num_batch32 v2'ye özgü yeni, açık bellek kısıtıdır**. Diğer kullanıcının servis ortamı/değişkenleri değiştirilmez. [Ollama context belgesi](https://docs.ollama.com/context-length) bağlam arttıkça belleğin arttığını belirtir; context yükseltme veya performans ayarı yoktur.

## 3. Başlamadan önce zorunlu koşullar
- Kullanıcının normal non-AppContainer PowerShell'i; aynı yerel tag ve tam313f… digest; doğrulanmış yerel API ve uygun motor sürümü.
- Başlangıçta ve inference hemen öncesinde RAM≥2,5GiB, VRAM≥2048MiB, **sistem commit boşluğu≥3GiB**. Commit boşluğu fiziksel RAM değildir; ayrı şarttır.
- En az4sn aralığa yayılan5 host RAM/commit örneğinin tamamı tabanı karşılamalı. Tek anlık iyileşme yeterli değildir.
- Önceden yüklü model varsa otomatik unload yok; servis/uygulama kapatmadan durur. Yeni model indirme, firewall veya yetki değişikliği yok.
- En fazla bir klinik içeriksiz JSON Schema echo; başka istek, otomatik retry veya19×3 döngüsü yok.

Çalışma sırasında host RAM250ms örneklenir.1GiB altında **yalnız mevcut HTTP isteğine iptal talebi** gönderilir; servis/süreç sonlandırılmaz. Bu, sunucu inference'ının kesin durduğunu göstermez. Sonuç CLIENT_CANCELLED_MEMORY_WARNING ve sunucu durumu UNKNOWN olarak korunur; yeniden deneme yapılmaz.0,75GiB referans rezervine yaklaşmadan uyarı marjı amaçlanır; diğer süreçlerin ani tahsisleri, örnekleme gecikmesi ve sunucunun iptale davranışı nedeniyle tam güvence verilemez. Bu sınırlama gizlenmedi; yeterli başlangıç/kararlılık kanıtı yoksa model hiç yüklenmez.60sn istemci timeout'u da sunucu tamamlanması garantisi değildir.

## 4. Bu makinede gerçek durum ve karar
Ölçüm **{h['captured_at']}**: boş RAM**{h['RAM']['available']/2**30:.2f}GiB**, boş VRAM{h['GPU']['free_MiB']}MiB, commit boşluğu{h['system_commit']['available_bytes']/2**30:.2f}GiB. GetPerformanceInfo commit sorgusu başarılı; yerel API çağrısı yapılmadı. Yeni2,5GiB RAM kapısı da geçilmiyor. **Şu anda kritik seviyeye düşmeden yükleme için yeterli kanıt yok; model yüklenmedi.** Kullanıcı uygulaması veya Ollama kapatılmadı. Bu ölçüm eski kararların yerine yazılmadı.

## 5. Tek kullanıcı komutu
Koşullar uygun hale geldiğinde normal PowerShell'de:

```powershell
& '{ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2.ps1'}' -RunSmoke
```

Betik v2 koşullarını kendisi uygular; başarısız kapıda inference0 ile kayıt üretir. Varsayılan parametresiz kullanım yalnız metadata kontrolüdür. Her deneme ayrı `reports/qa/WP12/gemma1b_v2_user_smoke_runs/tarih_GUID/` klasörüne yazılır; tam klasör yolu paylaşılabilir. Yeni ağsız doğrulayıcı `scripts/wp12_gemma_v2_smoke_review.py`, yalnız bu sürümün klasörlerini, yeni schema/probe ve num_batch32 dahil sabit payload'u kabul eder. v1 dosya/kararları ezilmez. Ham kayıt korunur; gerçek kullanıcı çıktısı henüz yoktur.

Teknik echo başarılsa bile bu PDF özet kalitesi veya kaynak sadakati değildir. reported_in_PDF /predicted_by_GNN ayrımı,44 alıntı,19 senaryo ve insan semantik inceleme kapıları değişmez. Yeni yan etki, MedDRA, skor, SHAP veyaΔz üretilmez. Kaynaklı19×3 çalışması bu aşamada etkin değildir.

## 6. QA ve sınırlar
Gerçek metadata okuma, KV formülü, yanlış/truncated GGUF, v2 eşikleri/commit/NA ve kayıt doğrulaması için yeni testler; eski3GiB kapısı testleri ayrı korunur.50 offline test ve yeni PowerShell AST kontrolü yapıldı; bunlar gerçek model çalışması değildir. Notebook gerçek metadata, bütçe/varsayım ve güncel ölçümü kod altında gösterir. Runtime/tepe bellek ve JSON Schema desteği **NOT_RUN**; modelin çalışacağı iddiası yoktur. Önceki3.395 proje dosyası, bütün kabul edilmiş kaynak/deney/QA korunur. run_status eski tam baytlarını saklayarak güncellenir. Tek sonuç: gerekçeli v2 politika ve koşullu tek teknik test; mevcut düşük RAM ile yükleme yok.
''',encoding='utf-8')
    with p.open('a',encoding='utf-8') as f:
        f.write('\nSon kontrol: son örnekte veya kayıtlı çalışma örneklerinde host RAM1GiB altındaysa tamamlanmış echo da teknik başarı sayılmaz. Son test logları `.final.log` ekiyle ayrıca korundu;50 test yeniden geçti. Bu koruma örnekler arasındaki ölçülmemiş düşüşleri veya sunucu iptal davranışını garanti etmez.\n')
    return p


def notebook():
    from wp09_close_wp10_notebooks import execute
    execute('WP12_gemma1b_memory_policy_v2.ipynb',[
        ('md','# WP12 — Gemma1B v2 bellek politikası\nGerçek GGUF metadata ve teorik KV hesabı. Eski v1 eşikleri/kararları değişmez. Bu notebook API, model yükleme veya indirme yapmaz.'),
        ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/gemma1b_memory_v2'\nm=json.loads((Q/'GGUF_metadata.json').read_text(encoding='utf-8'));b=json.loads((Q/'memory_budget.json').read_text(encoding='utf-8'));h=json.loads((Q/'hardware_snapshot.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([m['metadata']]).T)\ndisplay(pd.DataFrame([{'Context':c,'KV FP16 MiB':26*c*512*2/2**20,'KV FP32 MiB':26*c*512*4/2**20} for c in [512,1024,2048]]))"),
        ('md','**Yorum:**Tüm26 katmanda tam context hesaplandı;512 sliding-window indirimi uygulanmadı. KV sayıları toplam runtime belleği değildir. Tensor verisi yüklenmeden yalnız6,51MB metadata aralığı geçildi.'),
        ('code',"display(pd.DataFrame([b]).T)\nfig,axs=plt.subplots(1,2,figsize=(9,3));axs[0].bar(['v1','v2','Anlık boş'],[3,2.5,h['RAM']['available']/2**30]);axs[0].set_ylabel('Host RAM GiB');axs[1].bar(['v1','v2','Anlık boş'],[2.5,2,h['GPU']['free_MiB']/1024]);axs[1].set_ylabel('VRAM GiB');fig.suptitle('Ayrı v2 öneri; eski eşikler değişmedi');fig.tight_layout();F=ROOT/'reports/figures/WP12/gemma1b_memory_v2';F.mkdir(parents=True,exist_ok=True);fig.savefig(F/'policy_comparison.png',dpi=150);plt.show()"),
        ('md','**Yorum:**Runtime payları ölçülmemiş bütçelerdir.2,5GiB RAM/2GiB VRAM v2 kapısı;5 örnek/commit şartıyla yalnız tek teknik test için önerilir.1GiB uyarısındaki HTTP iptali sunucunun durduğunu garanti etmez. Güncel RAM yeni kapıyı da karşılamıyor; yükleme yok.'),
        ('code',"display(pd.DataFrame([json.loads((Q/'decision.json').read_text(encoding='utf-8'))]).T)\nfor name in ['test_wp12_gemma_memory_v2.py.log','test_wp12_gemma_v2_smoke_review.py.log','test_wp12_llm_preflight.py.log','test_wp12_llm_contract.py.log']:\n print(name);print((Q/name).read_text(encoding='utf-8'))\nprint((Q/'PowerShell_parse_check.txt').read_text(encoding='utf-8'))"),
        ('md','**Yorum:**50 offline test, gerçek Gemma runtime başarısı değildir. Başlangıç ve kararlılık koşulları geçmeden yükleme yapılmaz. Kullanıcı kendi PowerShell\'inde tek test kaydı üretir;19×3 ve WP13 başlamadı.')])


def close(report):
    prior=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p)==h for p,h in prior.items())
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    h=json.loads((QA/'hardware_snapshot.json').read_text(encoding='utf-8'))
    prefix=f'''# WP12 Gemma v2 bellek politikası — mevcut RAM ile yükleme yok ·08.11.2026

- v1 3GiB RAM/2,5GiB VRAM ve kararları korundu. Ayrı v2:2,5GiB RAM/2GiB VRAM,3GiB commit boşluğu,5 kararlı örnek; gerçek GGUF26katman/1KV/256K-V ve104MiB FP32 KV hesabı + açık ölçülmemiş runtime/rezerv bütçeleri. Garanti değildir.
- Yeni açık num_batch32; context2048/seed/sıcaklık korundu. Yalnız kullanıcı PowerShell'inde tek teknik JSON Schema echo.1GiB host uyarısında HTTP iptali; sunucunun durması garanti değil, servis/süreç kapatma yok. İndirme/API/inference Codex'ten yapılmadı.
- Güncel boş RAM{h['RAM']['available']/2**30:.2f}GiB, VRAM{h['GPU']['free_MiB']}MiB; v2 RAM kapısı da geçilmiyor. Model yüklemek için yeterli kanıt yok.19×3/eğitim/WP13 yok.
-50 offline test ve PS AST kontrolü geçti; gerçek runtime NOT_RUN. Önceki{len(prior)} dosya ve kaynaklar korundu. Rapor reports/WP12_GEMMA1B_MEMORY_POLICY_v2.md; config configs/WP12_GEMMA1B_MEMORY_POLICY_v2.json; QA reports/qa/WP12/gemma1b_memory_v2/; notebook notebooks/WP12_gemma1b_memory_policy_v2.ipynb.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if p=='run_status.md' else ROOT/p)==v for p,v in prior.items())
    save(QA/'artifact_validation.json',{'status':'V2_PROPOSED_CURRENT_RAM_FAIL_NO_MODEL_LOAD',
        'prior_artifacts_preserved':len(prior),'v1_thresholds_and_decisions_unchanged':True,
        'offline_tests_passed':50,'GGUF_metadata_span_bytes':6513118,'tensor_data_loaded':False,
        'KV_FP16_MiB_2048':52,'KV_FP32_MiB_2048':104,'budgets_are_measured_runtime_peaks':False,
        'PowerShell_AST_parse_errors':0,'actual_smoke_result':None,'runtime_model_execution':False,
        'Codex_API_calls':0,'downloads':0,'processes_terminated':0,'services_closed':0,
        'source_quotes_unchanged':44,'frozen_scenarios_unchanged':19,'real_scenario_repeats':0,
        'new_training':False,'WP13_started':False,'notebook_executed_code_cells':3,
        'prior_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,ROOT/'scripts/wp12_gemma_memory.py',ROOT/'scripts/wp12_gemma_memory_v2_outputs.py',
        ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2.ps1',ROOT/'scripts/wp12_gemma_v2_smoke_review.py',
        ROOT/'tests/test_wp12_gemma_memory_v2.py',ROOT/'tests/test_wp12_gemma_v2_smoke_review.py',
        ROOT/'configs/WP12_GEMMA1B_MEMORY_POLICY_v2.json',ROOT/'notebooks/WP12_gemma1b_memory_policy_v2.ipynb',
        ROOT/'reports/figures/WP12/gemma1b_memory_v2/policy_comparison.png',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('Separate v2 policy complete; preserved',len(prior),'offline50; no model load/API/download')


if __name__=='__main__':main()
