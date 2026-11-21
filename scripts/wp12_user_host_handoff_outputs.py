"""WP12 kullanıcı PowerShell smoke testine devir; hiçbir betiği inference için çalıştırmaz."""
import json
from pathlib import Path
import subprocess
import sys

from wp12_local_llm_preflight import ROOT,sha,save

QA=ROOT/'reports/qa/WP12/user_powershell_smoke_v1'


def main():
    assert not (QA/'artifact_validation.json').exists()
    r=json.loads((QA/'codex_measurement.json').read_text(encoding='utf-8'))
    host_ram=r['RAM']['available']/2**30;gpu=r['GPU']['free_MiB']
    runner=ROOT/'scripts/WP12_UserPowerShellSmoke_v1.ps1'
    save(ROOT/'configs/WP12_user_host_smoke_FROZEN_v1.json',{
        'version':'WP12-user-host-smoke-v1','model':'qwen3:4b-instruct-2507-q4_K_M',
        'manifest_digest':'sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0',
        'runner_sha256':sha(runner),'inference_location':'user independent non-AppContainer PowerShell only',
        'minimum_host_available_bytes':3221225472,'minimum_GPU_free_MiB':2560,
        'require_no_preexisting_loaded_models':True,'automatic_pull':False,'server_start':False,
        'num_ctx':2048,'num_predict':384,'temperature':0,'seed':20261108,'think':False,
        'stream':False,'keep_alive':0,'max_inference_requests':1,'request_timeout_seconds':60,
        'probe':'NONCLINICAL_SCHEMA_ECHO_ONLY','real_scenario_runs_allowed':False,
        'source_contract':'unchanged WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md',
        'source_contract_scope':'PDF explanation remains separate; this is technical transport/schema echo, not a PDF summary',
        'actual_smoke_status':'NOT_RUN_BY_CODEX'})
    save(QA/'external_output_review_record.json',{
        'status':'AWAITING_USER_POWERSHELL_OUTPUT','actual_user_output_received':False,
        'smoke_technical_result':None,'source_explanation_quality':'NOT_TESTED',
        'reported_in_PDF':None,'predicted_by_GNN':{'status':'NOT_REQUESTED_IN_WP12','artifact_ref':None},
        'human_semantic_review':'NOT_PERFORMED_NO_LLM_EXPLANATION',
        'automatic_release':False,'Codex_inference_calls':0,'real_scenario_repeats':0,
        'expected_runner_sha256':sha(runner),
        'output_directory_pattern':'reports/qa/WP12/user_smoke_runs/<timestamp_GUID>/',
        'always_required_files':['run_record.json','file_hashes.json'],
        'required_for_successful_smoke':['metadata_1_version.json','metadata_2_tags.json','metadata_3_ps.json',
            'smoke_request.json','smoke_response_raw.json','memory_samples.json'],
        'validation_tool':'scripts/wp12_user_smoke_review.py',
        'source_limitation':'User-provided logs and SHA support consistency, not cryptographic runtime attestation',
        'existing_19_scenarios_unchanged':True,'WP13_started':False})
    for pattern in ['test_wp12_user_smoke_review.py','test_wp12_llm_preflight.py','test_wp12_llm_contract.py']:
        test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        (QA/(pattern+'.log')).write_text(test.stdout+test.stderr,encoding='utf-8');assert test.returncode==0
    command="$t=$null; $e=$null; $null=[System.Management.Automation.Language.Parser]::ParseFile('"+str(runner)+"',[ref]$t,[ref]$e); if($e.Count){$e | Out-String; exit 1}; Write-Output 'PowerShell AST parse: 0 errors; script NOT executed'"
    parsed=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,timeout=30)
    (QA/'powershell_parse_check.txt').write_text(parsed.stdout+parsed.stderr,encoding='utf-8');assert parsed.returncode==0
    report=ROOT/'reports/WP12_USER_POWERSHELL_SMOKE_HANDOFF.md'
    assert not report.exists()
    report.write_text(f'''# WP12 — Kullanıcı PowerShell smoke testi ve ayrı doğrulama kaydı

**AWAITING_USER_POWERSHELL_OUTPUT** · {r['captured_at']}. Bu tur kullanıcı ortamında gerçek çıktı henüz alınmadı. Codex inference başlatmadı;19×3 senaryo yok. 3GiB RAM eşiği değiştirilmedi.

## Yeni gerçek ölçüm
| Kontrol | Sonuç |
|---|---|
| Boş/toplam host RAM | **{host_ram:.2f} / {r['RAM']['total']/2**30:.2f}GiB**; kullanım%{r['RAM']['percent']} |
| Boş/toplam VRAM | **{gpu} / {r['GPU']['total_MiB']}MiB** |
| Değişmeyen kapı | Host en az3GiB; VRAM en az2560MiB (2,5GiB) |
| Çağıran süreç | TokenIsAppContainer=true |
| Yerel GET /api/version | {r['API_version']} |

Hem RAM hem mevcut VRAM koşulu geçilmedi. Önceki3935MiB boş VRAM ölçümü tarihsel olarak korunur; yeni1633MiB ölçümünden hangi uygulama/modelin belleği kullandığı çıkarılamaz. İzin sınırı nedeniyle Ollama'nın gerçek servis/model durumu bu ortamdan doğrulanamadı.10013, bu ağ erişimi denemesindeki izin reddidir; model arızası sonucu değildir. Önceki teşhis raporunda AppContainer izolasyonu olası neden olarak ayrılmıştır; belirli kural kanıtı yoktur. Bu iki engelden herhangi biri yeterli olduğundan Codex içinde inference yapılmadı.

## Kullanıcı kendi PowerShell ortamında nasıl çalıştıracak?
Normal kullanıcı PowerShell penceresinde, Codex'in komut yürütücüsünden bağımsız çalıştırın. Yönetici yetkisi veya ExecutionPolicy değişikliği gerekçesi üretilmedi. Betik güvenlik politikanız tarafından engellenirse ayarı değiştirmeden hata çıktısını paylaşın.

Yalnız bağımsız metadata/bellek kontrolü (varsayılan, inference yok):

```powershell
& '{runner}'
```

Koşullar uygunsa tek teknik smoke testine izin veren komut:

```powershell
& '{runner}' -RunSmoke
```

Betik kendi yeniden ölçümünde de3GiB RAM/2,5GiB VRAM tabanını ve non-AppContainer ortamını zorunlu tutar. Bu bir bellek garantisi değildir; koşul sağlanmazsa inference olmadan kayıt üretip durur. Model bellekte zaten yüklüyse otomatik unload etmez; başka oturumu etkilemeden durur. Ollama kapalıysa betik servis başlatmaz. Yalnız127.0.0.1:11434'e gider; proxy kapalı, HTTP redirect kapalı; başka URL/indirme/pull yolu yoktur.

Seçilmiş tam tag/digest eşleşmelidir: qwen3:4b-instruct-2507-q4_K_M / sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0. Eksik/farklı modelde otomatik indirme veya alternatif yoktur. /api/version, /api/tags ve /api/ps yalnız metadata kontrolüdür. RAM/VRAM çağrıdan hemen önce yeniden ölçülür.

## Smoke testin sınırı ve sabit ayarları
Bu test **PDF açıklaması değildir**: tek, klinik içeriksiz teknik echo talebiyle yerel JSON Schema taşımasını sınar. Sahte prospektüs, yan etki, MedDRA, SHAP, Δz veya model skoru üretmez. Teknik istekte probe sabiti WP12_LOCAL_SMOKE_V1 istenir; bu bir doğrulama işaretidir, gerçek sonuç değildir. Gerçek yanıt henüz yoktur.

Değişmeyen ayarlar: num_ctx2048, num_predict384, temperature0, seed20261108, think:false, stream:false, keep_alive0. En çok bir /api/chat isteği;60sn HTTP timeout; retry/fallback yok. İstek baytları/SHA ve model digest'i yanıt görülmeden kaydedilir. Bu echo için ayrı teknik şema kullanılması, PDF açıklaması v1 sözleşmesini veya19 senaryo kilidini değiştirmez. Kaynaklı19 senaryo uygulanacaksa gerçek tokenizer/prompt bütçesi ve insan semantik inceleme kapıları ayrıca aynen korunacaktır.

Host RAM saniyelik örneklenir; GPU başlangıç/hemen önce/sonra alınır. Bu kayıtlar kesin tepe inference RAM/VRAM ölçümü değildir.60sn istemci timeout'u sunucunun kesin durduğu anlamına gelmez; böyle durumda UNKNOWN kaydı tutulur, tekrar gönderilmez ve süreç sonlandırılmaz. Başka kullanıcı/uygulamaların eşzamanlı bellek veya servis kullanımının kontrol edildiği iddia edilmez.

Başarılı echo, tek şemalı isteğin kabulü ve onunla uyumlu yanıt için teknik kanıttır; genel JSON Schema uyumu, Türkçe özet kalitesi veya kaynak sadakati kanıtı değildir. `reported_in_PDF` ve `predicted_by_GNN` sözleşmesi değişmez. Açıklama otomatik yayınlanmaz.

## Gerçek çıktı nasıl teslim ve doğrulanacak?
Betik sonunda yeni klasörün tam yolunu yazar: reports/qa/WP12/user_smoke_runs/tarih_GUID/. Var olan kaydı ezmez. Aynı klasörde run_record.json, file_hashes.json ve yalnız gerçekten gerçekleşen aşamaların ham metadata/istek/yanıt/bellek dosyaları bulunur. Çalıştırdıktan sonra bu klasör yolunu paylaşın. Henüz çıktı gelmediği için bu turdaki ayrı external_output_review_record.json **AWAITING_USER_POWERSHELL_OUTPUT**, sonuçnull'dır.

Gelecek inceleme komutu (LLM/ağ çalıştırmaz):

```powershell
python '{ROOT/'scripts/wp12_user_smoke_review.py'}' '<betiğin yazdığı gerçek çıktı klasörü>'
```

Doğrulayıcı her gerçek teslim için ayrı user_smoke_reviews/UUID/review.json oluşturur; ham çıktıyı veya eski QA'yı değiştirmez. Dosya manifesti/SHA, script/senaryo/sözleşme kilidi, tam model digest, bağımsız host token, iki bellek kapısı, tek istek, ayarların aynılığı, echo/done/token sayıları ve metadata bağlantıları kontrol edilir. Eksik/timeout/düşük sonuç başarıya çevrilmez. Hash tutarlılığı, kullanıcının sağladığı kaydın gerçek çalışmasını kriptografik olarak tasdik etmez; bu sınır inceleme kaydında yazılır.

Kullanıcı host testi başarılı, aynı zamandaki Codex erişimi10013 ise ortamlar arası fark için kanıt güçlenir; belirli firewall kuralı yine kendiliğinden kanıtlanmış olmaz. Host'ta da hata varsa hata aynen korunur; model bozukluğu teşhisi otomatik konmaz.

## Bu turdaki gerçek doğrulama ve koruma
PowerShell betiği **yalnız AST/sözdizimi ayrıştırmasından geçti; çalıştırılmadı**. Bağımsız host çalışma başarısı henüz NOT_RUN.12 yeni offline doğrulayıcı testi +6 bellek kapısı +24 kaynak sözleşmesi testi geçti. Yeni testlerde yalnız geçici, açıkça teknik echo fixture'ları kullanıldı; bunlar kullanıcı çıktısı veya gerçek model sonucu değildir.

Önceki3.343 dosya başlangıç SHA kaydıyla korundu; önceki3.328 kümesi, kaynak alıntıları, PDF'ler, deneyler ve sözleşmeler dahildir. run_status güncel kayıtla öne eklenir; önceki tam baytlar QA arşivinde ve dosyanın sonunda tutulur.19 senaryo değişmedi. Süreç sonlandırma, firewall/yetki değişikliği, indirme, eğitim veya WP13 yoktur.
''',encoding='utf-8')
    with report.open('a',encoding='utf-8') as f:
        f.write('\nTeknik başvuru: [Ollama Chat API](https://docs.ollama.com/api/chat) şema formatı, çalışma seçenekleri ve yanıt alanlarını; [Ollama model listesi API](https://docs.ollama.com/api/tags) yerel model/digest metadata yapısını açıklar. Bu belgelerin incelenmesi yerel API desteğinin çalıştırılarak doğrulanması değildir.\n')
    notebook()
    close(report)


def notebook():
    from wp09_close_wp10_notebooks import execute
    execute('WP12_user_powershell_smoke_handoff.ipynb',[
        ('md','# WP12 — Bağımsız kullanıcı PowerShell testine devir\nBu notebook gerçek Codex ölçümünü ve bekleyen teslim kaydını gösterir. Kullanıcı betiğini, yerel LLM\'yi veya19×3 senaryoyu çalıştırmaz.'),
        ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/user_powershell_smoke_v1'\nr=json.loads((Q/'codex_measurement.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([{'Zaman':r['captured_at'],'Boş RAM GiB':r['RAM']['available']/2**30,'Boş VRAM MiB':r['GPU']['free_MiB'],'AppContainer':r['process_token']['is_appcontainer']}]))\nfig,axs=plt.subplots(1,2,figsize=(9,3))\naxs[0].bar(['Gerçek','Kapı'],[r['RAM']['available']/2**30,3],color=['orange','grey']);axs[0].set_ylabel('Boş RAM GiB')\naxs[1].bar(['Gerçek','Kapı'],[r['GPU']['free_MiB'],2560],color=['orange','grey']);axs[1].set_ylabel('Boş VRAM MiB')\nfig.suptitle('İki bellek kapısı da sağlanmıyor');fig.tight_layout();F=ROOT/'reports/figures/WP12/user_powershell_smoke_v1';F.mkdir(parents=True,exist_ok=True);fig.savefig(F/'memory_gates.png',dpi=150);plt.show()"),
        ('md','**Yorum:**3GiB RAM/2,5GiB VRAM tabanı aynen korunuyor. Ölçüm modelin bellek tüketimi değildir; hangi süreçlerin kullandığına ilişkin çıkarım yapılmadı.'),
        ('code',"display(pd.DataFrame([r['API_version']]))\ndisplay(pd.DataFrame([json.loads((Q/'external_output_review_record.json').read_text(encoding='utf-8'))]).T)\nprint((Q/'powershell_parse_check.txt').read_text(encoding='utf-8'))"),
        ('md','**Yorum:**10013 izin reddi, Qwen model arızasının kanıtı değildir. AppContainer dışındaki gerçek kullanıcı testi ayrı kanıt olacaktır. Betik yalnız parse edildi; kullanıcı çıktısı yoktur. Bekleyen inceleme kaydı LLM başarısı veya insan semantik onayı değildir.'),
        ('code',"for n in ['test_wp12_user_smoke_review.py.log','test_wp12_llm_preflight.py.log','test_wp12_llm_contract.py.log']:\n print(n);print((Q/n).read_text(encoding='utf-8'))"),
        ('md','**Yorum:**42 offline test teknik kapıları sınar. Test fixture\'ları gerçek kullanıcı/model çıktısı değildir.19 senaryo çalıştırılmadı. Gerçek dosya geldiğinde ayrı inceleme kaydı üretilecek; ham kayıt değişmeyecek. WP13 başlamadan burada durulur.')])


def close(report):
    prior=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in prior.items())
    old=ROOT/'reports/qa/WP12/local_llm_recheck_v1/evidence_manifest.json'
    old_manifest=json.loads(old.read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in old_manifest.items())
    assert sha(old)==old.with_suffix('.sha256').read_text().split()[0]
    frozen=ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'
    previous=json.loads((ROOT/'reports/qa/WP12/local_llm_pilot_v1/approved_candidate_record.json').read_text(encoding='utf-8'))
    assert sha(frozen)==previous['frozen_scenarios_sha256']
    r=json.loads((QA/'codex_measurement.json').read_text(encoding='utf-8'))
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    prefix=f'''# WP12 kullanıcı PowerShell smoke testi — gerçek çıktı bekleniyor ·08.11.2026

- Yeni salt okunur Codex ölçümü: boş RAM{r['RAM']['available']/2**30:.2f}GiB, VRAM{r['GPU']['free_MiB']}MiB.3GiB RAM ve2560MiB VRAM kapısı değişmedi; ikisi de sağlanmadı. API yine10013; token AppContainer=true. Model arızası çıkarımı yapılmadı.
- scripts/WP12_UserPowerShellSmoke_v1.ps1 bağımsız kullanıcı PowerShell'i için hazırlandı; varsayılan metadata-only, -RunSmoke ile yalnız kapılar geçerse tek klinik içeriksiz JSON Schema echo. Tam seçilmiş tag/digest; indirme/servis başlatma/retry/19×3 yok.
- Betik yalnız parse edildi; gerçek host'ta çalıştırılmadı. Ayrı external_output_review_record.json AWAITING_USER_POWERSHELL_OUTPUT. Gerçek teslim için ağsız wp12_user_smoke_review.py yeni review kaydı oluşturacak; otomatik yayın yok.
-42 offline test geçti; gerçek model/smoke başarısı sayılmaz. Önceki{len(prior)} dosya ve19 senaryo SHA ile korundu. Rapor reports/WP12_USER_POWERSHELL_SMOKE_HANDOFF.md; notebook notebooks/WP12_user_powershell_smoke_handoff.ipynb; QA reports/qa/WP12/user_powershell_smoke_v1/.
- Codex inference0; yeni model/PDF/etiket/skor/eğitim veya WP13 yok. Kullanıcının kendi PowerShell çıktısı bekleniyor.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if k=='run_status.md' else ROOT/k)==v for k,v in prior.items())
    save(QA/'artifact_validation.json',{
        'status':'AWAITING_USER_POWERSHELL_OUTPUT','prior_artifacts_preserved':len(prior),
        'previous_recheck_manifest_entries_verified':len(old_manifest),'frozen_scenarios_unchanged':19,
        'RAM_threshold_bytes_unchanged':3221225472,'VRAM_threshold_MiB_unchanged':2560,
        'Codex_inference_calls':0,'user_smoke_output_received':False,'PowerShell_AST_parse_errors':0,
        'PowerShell_runtime_test':'NOT_RUN_BY_CODEX','offline_tests_passed':42,
        'notebook_executed_code_cells':3,'static_PNGs':1,'model_downloads':0,'real_scenario_repeats':0,
        'security_changes':0,'privilege_escalations':0,'processes_terminated':0,'WP13_started':False,
        'prior_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,ROOT/'notebooks/WP12_user_powershell_smoke_handoff.ipynb',
        ROOT/'scripts/WP12_UserPowerShellSmoke_v1.ps1',ROOT/'scripts/wp12_user_smoke_review.py',
        ROOT/'scripts/wp12_user_host_handoff_outputs.py',ROOT/'tests/test_wp12_user_smoke_review.py',
        ROOT/'configs/WP12_user_host_smoke_FROZEN_v1.json',
        ROOT/'reports/figures/WP12/user_powershell_smoke_v1/memory_gates.png',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('WAITING_FOR_REAL_USER_OUTPUT; preserved',len(prior),'offline tests42; no inference')


if __name__=='__main__':main()
