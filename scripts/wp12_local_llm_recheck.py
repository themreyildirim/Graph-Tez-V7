"""WP12 tekrar ön kontrolü: salt okunur ölçüm/teşhis, model yükleme yok."""
import ctypes
from ctypes import wintypes
import datetime
import json
from pathlib import Path
import socket
import subprocess
import sys
import urllib.request

from wp12_local_llm_preflight import ROOT, memory_gate, sha, save

QA=ROOT/'reports/qa/WP12/local_llm_recheck_v1'


def token_appcontainer():
    a=ctypes.WinDLL('advapi32',use_last_error=True)
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetCurrentProcess.restype=wintypes.HANDLE
    a.OpenProcessToken.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.POINTER(wintypes.HANDLE)]
    a.OpenProcessToken.restype=wintypes.BOOL
    a.GetTokenInformation.argtypes=[wintypes.HANDLE,ctypes.c_int,wintypes.LPVOID,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    a.GetTokenInformation.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    token=wintypes.HANDLE()
    if not a.OpenProcessToken(k.GetCurrentProcess(),8,ctypes.byref(token)):
        return {'query_ok':False,'last_error':ctypes.get_last_error()}
    try:
        value=wintypes.DWORD();length=wintypes.DWORD()
        ok=a.GetTokenInformation(token,29,ctypes.byref(value),ctypes.sizeof(value),ctypes.byref(length))
        return {'query_ok':bool(ok),'is_appcontainer':bool(value.value) if ok else None,
                'last_error':None if ok else ctypes.get_last_error(),
                'method':'GetTokenInformation(TokenIsAppContainer=29); TOKEN_QUERY only'}
    finally:
        k.CloseHandle(token)


def measure():
    import psutil
    out={'captured_at':datetime.datetime.now().astimezone().isoformat(),
         'RAM':dict(psutil.virtual_memory()._asdict()),'process_token':token_appcontainer()}
    r=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.free,driver_version',
                      '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,check=True)
    g=r.stdout.strip().split(', ')
    out['GPU']={'name':g[0],'total_MiB':int(g[1]),'free_MiB':int(g[2]),'driver':g[3]}
    try:
        out['listeners']=[{'address':c.laddr.ip,'port':c.laddr.port,'pid':c.pid}
                          for c in psutil.net_connections(kind='tcp')
                          if c.status=='LISTEN' and c.laddr and c.laddr.port==11434]
        out['listener_visibility']='query returned; sandbox visibility may be incomplete'
    except Exception as e:
        out['listener_query_error']={'type':type(e).__name__,'error':str(e)}
        out['listener_visibility']='UNVERIFIED_QUERY_FAILED'
    out['visible_ollama_processes']=[]
    for p in psutil.process_iter(['pid','name']):
        try:
            if 'ollama' in (p.info['name'] or '').lower():out['visible_ollama_processes'].append(p.info)
        except psutil.Error:
            pass
    out['process_visibility_scope']='current restricted environment; empty list does not prove host absence'
    try:
        with socket.create_connection(('127.0.0.1',11434),timeout=2):
            out['TCP_probe']={'status':'CONNECTED'}
    except OSError as e:
        out['TCP_probe']={'status':'FAILED','errno':e.errno,'winerror':getattr(e,'winerror',None),'error':str(e)}
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:11434/api/version',timeout=2) as response:
            out['API_version']={'HTTP_status':response.status,'body':response.read(10000).decode()}
    except Exception as e:
        out['API_version']={'error_type':type(e).__name__,'error':str(e)}
    r=subprocess.run(['CheckNetIsolation.exe','LoopbackExempt','-s'],capture_output=True,text=True,timeout=10)
    out['loopback_exemption_read_query']={'command':'CheckNetIsolation.exe LoopbackExempt -s',
        'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'configuration_modified':False}
    out['memory_gate_passed']=memory_gate(out['RAM']['available'],out['GPU']['free_MiB'])
    out['API_access_verified']=out['API_version'].get('HTTP_status')==200
    return out


def main():
    assert not (QA/'recheck.json').exists(), 'Previous audit evidence is immutable'
    result=measure();save(QA/'recheck.json',result)
    # Bu giriş yalnız ön kontrol yapar; tüm koşullar geçerse bile inference burada yoktur.
    if result['memory_gate_passed'] and result['API_access_verified']:
        raise RuntimeError('Both gates passed; a separately frozen bounded smoke payload is required')
    ram=result['RAM'];gpu=result['GPU']
    config=json.loads((ROOT/'configs/WP12_local_llm_PROPOSED_v1.json').read_text(encoding='utf-8'))
    save(QA/'decision.json',{'status':'STOPPED_RAM_OR_LOCAL_API_GATE','memory_gate_passed':result['memory_gate_passed'],
        'API_access_verified':result['API_access_verified'],
        'planning_thresholds':config['memory_admission_heuristic'],
        'smoke_test':'NOT_RUN_PRECONDITIONS_FAILED','real_scenarios':'NOT_RUN_SMOKE_NOT_PASSED',
        'model_loads':0,'inference_calls':0,'processes_terminated':0,'security_changes':0,
        'privilege_escalations':0,'downloads':0,'WP13_started':False})
    source=ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'
    before=json.loads((ROOT/'reports/qa/WP12/local_llm_pilot_v1/approved_candidate_record.json').read_text(encoding='utf-8'))
    assert sha(source)==before['frozen_scenarios_sha256']
    save(QA/'frozen_inputs_check.json',{'scenarios':19,'planned_repeats':3,'source_file':source.relative_to(ROOT).as_posix(),
        'sha256':sha(source),'matches_previous_approved_candidate_record':True,
        'contract_sha256':sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md'),
        'contract_unchanged':sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md')==before['existing_contract_sha256']})
    for pattern in ['test_wp12_llm_contract.py','test_wp12_llm_preflight.py']:
        r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,
                          capture_output=True,text=True,encoding='utf-8',errors='replace')
        (QA/(pattern+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0
    save(QA/'diagnostic_interpretation.json',{
        'confirmed':['Calling process token is AppContainer','TCP loopback gets WSAEACCES10013',
                     'HTTP request with proxy disabled also gets10013','Host RAM below frozen planning floor'],
        'inference':'Sandbox/AppContainer network isolation is a likely explanation, not a confirmed specific WFP rule',
        'unverified':['exact denying filter/firewall rule','loopback exemption list','host Ollama service/listener state',
                      'server version','JSON Schema inference support'],
        'not_evidence_for':['model corruption','port conflict','Ollama definitely not running','RAM causes socket10013'],
        'diagnostic_note':'First ad-hoc ctypes token query had handle signature overflow; corrected 64-bit argtypes before successful query. No system setting was changed.',
        'sources':[
            'https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2',
            'https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall']})
    report=ROOT/'reports/WP12_LOCAL_LLM_RECHECK.md'
    assert not report.exists()
    report.write_text(f'''# WP12 — RAM/VRAM ve yerel Ollama erişiminin tekrar kontrolü

**STOPPED_RAM_OR_LOCAL_API_GATE** · {result['captured_at']}. Kaynaklar ve dondurulmuş19 senaryo korundu. Hiçbir LLM modeli yüklenmedi, smoke test veya19×3 senaryo çalıştırılmadı. WP13 başlamadı.

## Gerçek ölçüm ve karar
| Kontrol | Sonuç |
|---|---|
| Toplam kullanılabilir RAM | {ram['total']/2**30:.2f}GiB |
| Anlık boş RAM | **{ram['available']/2**30:.2f}GiB**; kullanım%{ram['percent']} |
| GPU toplam/boş VRAM | {gpu['total_MiB']}/{gpu['free_MiB']}MiB |
| Eski planlama tabanı | 3GiB boş RAM /2,5GiB boş VRAM; sığma garantisi değil |
| Bellek koşulu | {'PASS' if result['memory_gate_passed'] else 'FAIL'} |
| TCP127.0.0.1:11434 | {json.dumps(result['TCP_probe'],ensure_ascii=False)} |
| Yerel API | {json.dumps(result['API_version'],ensure_ascii=False)} |

Önceki0,36 ve0,93GiB ölçümleri tarihsel olarak korundu; yeniden ölçüm bunların yerine yazılmadı. Sistem RAM'ini azalttığımız/uygulama kapattığımız iddia edilmiyor. Bu tur yalnız güncel durumu okuduk. RAM koşulu sağlanmadı; API erişimi de doğrulanamadı. Bunlar bağımsız iki engeldir; RAM eksikliği10013'ün kanıtlanmış nedeni değildir.

## WinError10013: kanıt ve neden ayrımı
1. **Doğrulandı:** Çağrıyı yapan Python sürecinin TokenIsAppContainer değeri true. Yalnız TOKEN_QUERY erişimi kullanıldı; token veya ayrıcalık değiştirilmedi.
2. **Doğrulandı:** Doğrudan TCP soketi ve proxy kapalı HTTP GET /api/version aynı erişim reddini veriyor. Sayısal loopback adresi kullanıldığı için DNS çözümleme bu denemenin parçası değil. HTTP proxy ayarı bu sonucun açıklaması olarak desteklenmiyor.
3. **Sınırlı görünürlük:** TCP dinleyici tablosu sorgusu GetExtendedTcpTable hatası verdi. Sınırlı süreç listesinde Ollama görülmedi; bu, ana bilgisayarda servis bulunmadığı/çalışmadığı kanıtı değildir. Servis/listener ve sürümü **UNVERIFIED** kaldı.
4. **Salt okunur izin sınırı:** CheckNetIsolation LoopbackExempt -s sorgusu erişim reddi verdi. Komutun yönetici çalıştırma metni bir hata mesajıdır; uygulanmadı, yetki yükseltme veya muafiyet ekleme yapılmadı.

Microsoft,10013'ü WSAEACCES/erişim reddi olarak tanımlar; hata tek başına belirli bir güvenlik kuralını teşhis etmez. [Microsoft Winsock hata kodları](https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2).

Microsoft'un AppContainer/UWP ağ yalıtımı açıklaması, loopback ve yetenek kısıtlarının bağlantıları engelleyebildiğini belirtir. Bu genel mekanizma ile gerçek token/socket bulguları birlikte değerlendirildiğinde **çalışma ortamının AppContainer ağ izolasyonu güçlü bir olası açıklamadır**. Ancak WFP drop kaydı, muafiyet listesi veya belirli engelleyen kural elde edilmedi; kesin kök neden/kural adı doğrulanmış değildir. [Microsoft ağ yalıtımı teşhisi](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall).

10013'ü model bozukluğu, port çakışması, Ollama kesin kapalı veya firewall kesin hatalı diye yorumlamıyoruz. Model dosyaları önceki turda tam hash ile doğrulanmıştı; bu tur büyük ağırlıklar gereksiz yeniden taranmadı. İlk ad-hoc token sorgusunda ctypes64-bit handle imzası hatası oluştu; doğru argtypes ile sorgu tekrarlandı ve true elde edildi. Bu uygulama hatası düzeltilirken işletim sistemi ayarı değiştirilmedi.

## Yapılmayanlar ve koruma
- Model yükleme/çıkarım0; smoke test NOT_RUN_PRECONDITIONS_FAILED.
-19×3 senaryo NOT_RUN_SMOKE_NOT_PASSED; dondurulmuş liste ve SHA değişmedi. Başarı veya başarısız LLM yanıtı uydurulmadı.
- Kaynak doğrulama24 ve bellek kapısı6 offline test geçti; bunlar JSON Schema API veya gerçek LLM kalite testi değildir.
- Süreç sonlandırma, RAM temizleme aracı, servis başlatma, firewall/muafiyet değişimi, yetki yükseltme, yeni model/PDF indirme veya eğitim yok.
- İnsan semantik incelemesi NOT_PERFORMED_NO_OUTPUT; açıklama otomatik yayınlanmadı. reported_in_PDF /predicted_by_GNN ayrımı ve kaynak sözleşmesi değişmedi.
- Önceki3.328 dosya başlangıç SHA kaydıyla korunur. run_status güncel kayıtla öne eklenir; eski tam baytlar yeni QA arşivinde ve dosyanın sonunda saklanır.

## Çıktılar ve durma noktası
QA: reports/qa/WP12/local_llm_recheck_v1/. recheck.json gerçek ölçüm ve hataları, diagnostic_interpretation.json kanıt/çıkarım sınırını, frozen_inputs_check.json19 senaryo kilidini, iki yeni log30 offline testi gösterir. Notebook yalnız kayıtları okuyup gerçek tablo/grafik üretir; model çağrısı içermez.

Bu aşamada duruldu. Devam için hem boş RAM koşulu hem erişilebilir yerel API yeniden doğrulanmalıdır. Güvenlik ayarını değiştirmeden veya yetki yükseltmeden bu oturumdan kesin servis/listener doğrulaması yapılamadı. Bir sonraki izinli işlem koşullar sağlanınca yalnız sınırlı, önceden kilitlenmiş smoke test olacaktır;19×3 çalışma bu turun kapsamına alınmadı.
''',encoding='utf-8')
    notebook()
    close(report)


def notebook():
    from wp09_close_wp10_notebooks import execute
    execute('WP12_local_llm_recheck.ipynb',[
        ('md','# WP12 — Yeniden ölçüm ve AppContainer erişim teşhisi\nBu notebook yalnız gerçek QA kayıtlarını okur. Smoke test, inference veya yeni model indirme içermez. Bütün önceki sonuçlar ve19 senaryo korunur.'),
        ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/local_llm_recheck_v1'\nr=json.loads((Q/'recheck.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([{'Zaman':r['captured_at'],'Boş RAM GiB':r['RAM']['available']/2**30,'Boş VRAM MiB':r['GPU']['free_MiB'],'Bellek kapısı':r['memory_gate_passed']}]))\nfig,ax=plt.subplots(figsize=(7,3));ax.barh(['Güncel boş RAM','Planlama tabanı'],[r['RAM']['available']/2**30,3],color=['orange','grey']);ax.set_xlabel('GiB');ax.set_title('Güncel gerçek RAM ve değişmeyen taban')\nF=ROOT/'reports/figures/WP12/local_llm_recheck_v1';F.mkdir(parents=True,exist_ok=True);fig.tight_layout();fig.savefig(F/'RAM_recheck.png',dpi=150);plt.show()"),
        ('md','**Yorum:** RAM kapısı sağlanmıyor; VRAM boşluğu host RAM koşulunun yerine geçmez. Çizim LLM tepe bellek ölçümü değildir; LLM yüklenmedi.'),
        ('code',"for key in ['process_token','TCP_probe','API_version','listener_visibility','loopback_exemption_read_query']:\n print(key);display(pd.DataFrame([r[key]]) if isinstance(r[key],dict) else r[key])\ndisplay(pd.DataFrame([json.loads((Q/'diagnostic_interpretation.json').read_text(encoding='utf-8'))]).T)"),
        ('md','**Yorum:** AppContainer=true ve TCP/HTTP erişim reddi gerçek bulgulardır. Belirli WFP kuralı veya firewall yapılandırması doğrulanmadı. Dinleyici görünürlüğünün kapalı olması, Ollama servisinin yokluğunu kanıtlamaz. Güvenlik ayarı değiştirilmedi.'),
        ('code',"display(pd.DataFrame([json.loads((Q/'decision.json').read_text(encoding='utf-8'))]).T)\ndisplay(pd.DataFrame([json.loads((Q/'frozen_inputs_check.json').read_text(encoding='utf-8'))]).T)\nfor name in ['test_wp12_llm_contract.py.log','test_wp12_llm_preflight.py.log']:\n print(name);print((Q/name).read_text(encoding='utf-8'))"),
        ('md','**Yorum:**24+6 test yalnız offline kontrollerdir.19×3 çalışma ve smoke test için gerçek çıktı yoktur; NA/NOT_RUN başarı sıfırı değildir. Kaynak, semantik inceleme ve otomatik yayın kapıları değişmedi. WP13 başlamadan burada durulur.')])


def close(report):
    prior=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in prior.items())
    old=ROOT/'reports/qa/WP12/local_llm_pilot_v1/evidence_manifest.json'
    old_manifest=json.loads(old.read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in old_manifest.items())
    assert sha(old)==old.with_suffix('.sha256').read_text().split()[0]
    r=json.loads((QA/'recheck.json').read_text(encoding='utf-8'))
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    prefix=f'''# WP12 tekrar ön kontrol — RAM/API engeli sürüyor · 08.11.2026

- Güncel boş RAM{r['RAM']['available']/2**30:.2f}GiB, VRAM{r['GPU']['free_MiB']}MiB;3GiB host RAM tabanı geçilmedi. Bellek temizleme/süreç sonlandırma yapılmadı.
- TokenIsAppContainer=true doğrulandı; TCP loopback ve proxy kapalı HTTP GET10013 erişim reddi verdi. Ağ izolasyonu olası açıklama; belirli WFP kuralı/loopback muafiyeti doğrulanamadı. Dinleyici tablosu ve muafiyet okuması erişime kapalı; servis varlığı/yokluğu çıkarılmadı.
- Yetki yükseltme, firewall/muafiyet değişimi veya servis başlatma yapılmadı. Model yükleme/smoke/inference0;19×3 NOT_RUN_SMOKE_NOT_PASSED. WP13 başlamadı.
- Önceki{len(prior)} dosya ve19 senaryo SHA ile korundu;24+6 offline test geçti. Rapor: reports/WP12_LOCAL_LLM_RECHECK.md; notebook: notebooks/WP12_local_llm_recheck.ipynb; QA: reports/qa/WP12/local_llm_recheck_v1/.
- İki koşul da sağlanana kadar duruldu; kullanıcı incelemesi bekleniyor.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if k=='run_status.md' else ROOT/k)==v for k,v in prior.items())
    save(QA/'artifact_validation.json',{'status':'STOPPED_RAM_OR_LOCAL_API_GATE','prior_artifacts_preserved':len(prior),
        'previous_pilot_manifest_entries_verified':len(old_manifest),'frozen_scenarios_unchanged':19,
        'offline_tests_passed':30,'notebook_executed_code_cells':3,'static_PNGs':1,
        'AppContainer_token_verified':r['process_token'].get('is_appcontainer'),
        'specific_denying_rule':'UNVERIFIED','smoke_test':'NOT_RUN_PRECONDITIONS_FAILED',
        'scenario_repeats_executed':0,'inference_calls':0,'models_loaded':0,'new_downloads':0,
        'security_changes':0,'privilege_escalations':0,'processes_terminated':0,'WP13_started':False,
        'prior_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,ROOT/'notebooks/WP12_local_llm_recheck.ipynb',
        ROOT/'scripts/wp12_local_llm_recheck.py',ROOT/'reports/figures/WP12/local_llm_recheck_v1/RAM_recheck.png',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('STOPPED; preserved',len(prior),'files; RAM GiB',r['RAM']['available']/2**30)


if __name__=='__main__':
    main()
