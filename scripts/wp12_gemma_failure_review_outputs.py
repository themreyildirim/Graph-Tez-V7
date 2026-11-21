"""Gerçek iki hata kaydından rapor/notebook; eski betik/config/çıktılar değişmez."""
import json
from pathlib import Path
import subprocess
import sys

from wp12_gemma_failure_diagnosis import ROOT,diagnose
from wp12_user_smoke_review import read,verify_file_manifest
from wp12_local_llm_preflight import sha,save

QA=ROOT/'reports/qa/WP12/gemma1b_v2_failure_review'


def main():
    import pandas as pd
    assert not (QA/'artifact_validation.json').exists()
    runner=ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2.ps1'
    rows=[];sources={}
    paths=sorted((ROOT/'reports/qa/WP12/gemma1b_v2_user_smoke_runs').glob('*/run_record.json'))
    assert len(paths)==2
    for p in paths:
        m=verify_file_manifest(p.parent);r=read(p)
        d=diagnose(r,read(p.parent/'metadata_1_version.json'),read(p.parent/'metadata_2_tags.json'),
            script_hash=sha(runner),filenames={x.name for x in p.parent.iterdir()})
        d.update(run_id=p.parent.name,source_record=p.relative_to(ROOT).as_posix(),
                 source_manifest_entries_verified=len(m),source_script_hash_verified=True)
        assert r['source_contract_sha256']==sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md')
        assert r['frozen_scenarios_sha256']==sha(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')
        rows.append(d)
        sources.update({x.relative_to(ROOT).as_posix():sha(x) for x in p.parent.iterdir() if x.is_file()})
    save(QA/'run_diagnoses.json',rows);pd.DataFrame(rows).to_csv(QA/'run_comparison.csv',index=False,encoding='utf-8-sig')
    save(QA/'actual_run_sources_sha256.json',sources)
    # Aynı ağırlık/config/template soy ağacını yalnız küçük metadata dosyalarıyla doğrula.
    cache=Path('C:/Users/emrey/.ollama/models')
    wrapper=cache/'manifests/registry.ollama.ai/library/gemma3/1b-it-q4_K_M'
    w=read(wrapper);entry=next(e for e in w['layers'] if e['mediaType']=='application/vnd.docker.distribution.manifest.v2+json')
    srcpath=cache/'blobs'/entry['digest'].replace(':','-');src=read(srcpath)
    assert 'sha256:'+sha(wrapper)==rows[0]['expected_digest_in_script']
    assert 'sha256:'+sha(srcpath)==entry['digest']==rows[0]['observed_API_digest']==rows[1]['observed_API_digest']
    assert w['config']==src['config'] and w['layers'][:-1]==src['layers']
    lineage={'local_wrapper_manifest_file_sha256':'sha256:'+sha(wrapper),
             'API_model_digest_in_both_records':entry['digest'],'source_manifest_content_sha256':'sha256:'+sha(srcpath),
             'config_identical':True,'weight_template_license_params_layers_identical':True,
             'weight_content_rehashed_this_review':False,'metadata_only_read':True}
    save(QA/'digest_semantics_evidence.json',lineage)
    save(QA/'minimal_correction_PROPOSED_ONLY.json',{
        'status':'REPORT_ONLY_NOT_APPLIED','scope':'identity binding correction only; no new memory/timeout policy',
        'local_wrapper_manifest_file_sha256':lineage['local_wrapper_manifest_file_sha256'],
        'expected_API_model_digest':entry['digest'],
        'required_validation':'explicit local-wrapper -> source-manifest -> same config/weight layers -> exact API tag/digest',
        'required_consistency_updates_if_implemented':['future runner expected API digest','future config API digest field',
            'future reviewer API identity check','offline source-lineage regression test'],
        'guard_not_removed':True,'no_arbitrary_digest_acceptance':True,
        'memory_thresholds_unchanged':{'RAM_bytes':2684354560,'GPU_MiB':2048,'commit_bytes':3221225472},
        'HTTP_timeout_seconds_unchanged':60,'existing_records_rewritten':False,
        'same_recorded_initial_memory_would_pass_after_identity_correction':[False,False],
        'future_memory_and_server_residency':'UNKNOWN; new run not requested'})
    # Kontrol akışı satırları kaynağın doğrulanmış sürümüne bağlanır.
    tokens=['GetStringAsync(',"Read-LocalMetadata 'version'","Read-LocalMetadata 'tags'",'MODEL_DIGEST_MISMATCH',
            "Read-LocalMetadata 'ps'",'if ($record.memory_before.available_bytes',"$record['inference_attempts'] = 1",'PostAsync(']
    locations={t:next(i for i,s in enumerate(runner.read_text(encoding='utf-8').splitlines(),1) if t in s) for t in tokens}
    assert locations['MODEL_DIGEST_MISMATCH']<locations["Read-LocalMetadata 'ps'"]<locations['if ($record.memory_before.available_bytes']<locations['PostAsync(']
    save(QA/'verified_runner_control_flow.json',{'script_sha256':sha(runner),'locations':locations})
    t=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_wp12_gemma_failure_diagnosis.py','-v'],
        cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (QA/'diagnosis_tests.txt').write_text(t.stdout+t.stderr,encoding='utf-8');assert t.returncode==0
    report=write_report(rows,lineage);notebook();close(report,sources)


def write_report(rows,lineage):
    p=ROOT/'reports/WP12_GEMMA1B_V2_FAILURE_REVIEW.md';assert not p.exists()
    a,b=rows
    def short(d):
        return f"{d['RAM_available_GiB']:.6f}GiB; açık {d['RAM_deficit_MiB']:.3f}MiB"
    p.write_text(f'''# WP12 — İki gerçek Gemma1B v2 denemesinin hata incelemesi

08.11.2026 · **READ_ONLY_DIAGNOSIS_COMPLETE — NO_RETRY.** İki deneme de aynı digest kontrolünde durdu. Gerçek neden kayıtlarda açık: `System.Management.Automation.RuntimeException: MODEL_DIGEST_MISMATCH: do not silently switch model`. Timeout veya model inference başarısızlığı teşhisi yoktur.

Önceki betikte API model digest'ini yerel sarmalayıcı manifest dosyasının hash'iyle eşleştirmiştim. Bu iki farklı kimliği aynı kontrol alanında kullanmam yanlıştı. Önceki v2 betiği ve deney kayıtları bu incelemede değiştirilmedi; gereken düzeltme aşağıda yalnız öneri olarak kaydedildi.

## 1. Her denemenin ayrı sonucu
| Kontrol | Deneme1 —04:28:56 | Deneme2 —04:29:06 |
|---|---|---|
| Tam run ID |{a['run_id']}|{b['run_id']}|
| Betik başlangıç/bitiş |{a['started_at']} / {a['finished_at']}|{b['started_at']} / {b['finished_at']}|
| Toplam duvar saati süresi |{a['wall_clock_elapsed_seconds']:.3f}sn|{b['wall_clock_elapsed_seconds']:.3f}sn|
| Kaydedilen genel durum |FAILED_OR_TIMED_OUT_NO_RETRY|FAILED_OR_TIMED_OUT_NO_RETRY|
| Gerçek exception |MODEL_DIGEST_MISMATCH|MODEL_DIGEST_MISMATCH|
| Hata aşaması |Digest kontrolü; API ps/bellek kapısı/chat öncesi|Aynı aşama|
| Non-AppContainer kullanıcı ortamı |is_appcontainer=false|is_appcontainer=false|
| Ollama servis erişimi |GET version ve tags yanıtları mevcut; servis0.40.6|GET version ve tags yanıtları mevcut; servis0.40.6|
| Metadata HTTP tam status |**UNKNOWN — kaydedilmemiş**|**UNKNOWN — kaydedilmemiş**|
| Smoke HTTP status |N/A — istek gönderilmedi|N/A — istek gönderilmedi|
| Timeout aşaması |Ulaşılmadı; açık guard exception'ı|Ulaşılmadı; açık guard exception'ı|
| Kaydedilen inference_attempts |0|0|
| Bu betikten model yükleme isteği |Gönderilmedi|Gönderilmedi|
| Sunucuda önceden yüklü model durumu |**UNKNOWN**; api/ps cevabı yok|**UNKNOWN**; api/ps cevabı yok|
| İlk boş RAM |{short(a)}|{short(b)}|
| İlk boş VRAM |{a['GPU_free_MiB']}MiB;2GiB koşulu uygun|{b['GPU_free_MiB']}MiB;2GiB koşulu uygun|
| İlk commit boşluğu |{a['commit_available_GiB']:.3f}GiB;3GiB koşulu uygun|{b['commit_available_GiB']:.3f}GiB;3GiB koşulu uygun|
| Betiğin bellek kapısı çalıştı mı? |**Hayır**, önce digest guard attı|**Hayır**, önce digest guard attı|
| İlk ölçümden bağımsız yeniden hesap |RAM koşulu **FAIL**|RAM koşulu **FAIL**|
|5 kararlı örnek/hemen önce ölçüm |Alınmadı|Alınmadı|

Her klasörde yalnız file_hashes.json, metadata_1_version.json, metadata_2_tags.json, run_record.json var. Manifest başına3 içerik girdisi; iki klasörde toplam8 gerçek dosyanın bayt/hash'leri korundu. metadata_3_ps, smoke_request, smoke_response ve memory_samples dosyaları yok. Bu yokluk tek başına değil, run_record inference0/exception ve **aynı SHA'lı betiğin kontrol akışıyla birlikte** gönderilmemiş chat isteğini doğruluyor.

`FAILED_OR_TIMED_OUT_NO_RETRY` genel catch etiketidir; içinde “TIMED_OUT” bulunması timeout kanıtı değildir. Yaklaşık1,315sn/0,662sn toplam süre HTTP gecikmesi veya model yükleme süresi değildir. Burada açıkça digest guard atılmış;60sn timeout'a dayalı hata yoktur. Genel `server_completion_if_request_started=UNKNOWN_ON_CLIENT_ERROR` metni koşullu boilerplate'tir; bu kayıtlarda istek başlamamıştır.

GetStringAsync başarılı gövde dönüşünde2xx başarı sınıfını sağlar, fakat betik tam HTTP status kodunu saklamamış. Bu nedenle200 diye doldurmadık. [Microsoft GetStringAsync açıklaması](https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpclient.getstringasync). Servis erişiminin çalışması, Gemma modelinin yüklendiği veya JSON Schema inference desteğinin sınandığı anlamına gelmez.

## 2. Digest uyuşmazlığının kesin açıklaması
| Kimlik | Değer |
|---|---|
| Betiğin beklediği yerel sarmalayıcı dosya SHA |{lineage['local_wrapper_manifest_file_sha256']}|
| Her iki gerçek API tags cevabının model digest'i |{lineage['API_model_digest_in_both_records']}|
| Yerel sarmalayıcının içerdiği üst manifestin doğrulanmış SHA'sı |{lineage['source_manifest_content_sha256']}|

İki gerçek API yanıtı tam aynı Gemma tag'ini, family=gemma3,999.89M,Q4_K_M ve9755… digest'ini döndürüyor. [Ollama tags API](https://docs.ollama.com/api/tags) bu alanı model metadata'sının parçası olarak sunar. Yerel313f… dosyasının içindeki9755… manifesti küçük metadata dosyasından yeniden hash'lendi; config ve ağırlık/template/license/params layer listelerinin birebir aynı olduğu doğrulandı. Model ağırlıkları yeniden yüklenmedi veya inference yapılmadı.

Dolayısıyla bu kayıtlarda **farklı hash nesnelerinin karşılaştırıldığı** kanıtlıdır. Bundan bütün Ollama sürümlerinin her zaman aynı digest normalizasyonunu yaptığı genellemesi çıkarılmaz. Modelin bozuk olduğu, değiştirilmesi/yeniden indirilmesi gerektiği veya AppContainer10013 hatası bu iki denemenin nedeni olduğu iddia edilmez. Kaydedilmiş hata yerel kullanıcı ortamında digest guard'dır.

## 3. En küçük gerekli düzeltme — uygulanmadı
Kimlik kontrolünü kaldırmadan iki alanı ayrı tutmak gerekir:

```text
local_wrapper_manifest_file_sha256 = sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16
expected_API_model_digest         = sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c
```

Gelecekte yalnız kimlik bağlama düzeltmesi olarak runner/config/inceleyicinin API digest alanı9755… ile eşleştirilir;313f… yerel dosya bütünlüğü alanında korunur. Sarmalayıcı→kaynak manifest→aynı layer zinciri ayrıca denetlenir. Rastgele digest kabulü, kontrolü kaldırma veya model değiştirme yoktur. Ayrı öneri `minimal_correction_PROPOSED_ONLY.json` içindedir. Bu tur aktif betiğe/config'e/inceleyiciye düzeltme uygulanmadı, yeniden çalıştırma komutu verilmedi.

**Bu düzeltme tek başına smoke testini başlatmaya yetmez.** İlk ölçümler2,404907GiB ve2,395996GiB; v2 RAM tabanı2,5GiB'nin sırasıyla97,375 ve106,500MiB altındadır. Aynı başlangıç değerleriyle digest düzeltmesinden sonra bellek kapısı da durdururdu. Bu, kaydedilmiş ölçümlere dayalı koşullu hesap; ilerideki boş RAM tahmini değildir. Eşiklerin veya timeout'un değiştirilmesi için bu hatalar gerekçe oluşturmaz. Modelin gerçekten çalışıp çalışmayacağı ve tepe belleği **UNKNOWN/NOT_TESTED** kalır.

## 4. QA, koruma ve durma
8 offline test: iki gerçek manifest, aynı betik SHA'sı, doğru hata aşaması, timeout ayrımı, gönderilmemiş inference, bilinmeyen sunucu residency'si, yeniden hesaplanan bellek, uydurulmayan HTTP status ve farklı hata/sürümde otomatik teşhis reddi. Önerilen kaynak digest eşleşmesi yalnız offline sınandı; hiçbir HTTP isteği gönderilmedi.

Notebook iki gerçek kaydı, bellek farklarını, digest zincirini ve test çıktısını kod altında gösterir. Önceki3.432 proje dosyası başlangıç hash kaydıyla korunur; iki ham deneme klasörü değiştirilmedi. run_status eski tam baytlarını saklayarak güncellenir. Yeni model/PDF indirme, servis/süreç müdahalesi, timeout/eşik değişimi, inference,19×3, yeni eğitim veya WP13 yoktur. İnceleme burada biter.
''',encoding='utf-8')
    return p


def notebook():
    from wp09_close_wp10_notebooks import execute
    execute('WP12_gemma1b_v2_failure_review.ipynb',[
        ('md','# WP12 — İki gerçek v2 hata kaydı\nYalnız kayıt okuma ve offline teşhis. Model/API/yeniden deneme yok. Genel FAILED_OR_TIMED_OUT etiketi gerçek exception yerine yorumlanmaz.'),
        ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/gemma1b_v2_failure_review'\nrows=json.loads((Q/'run_diagnoses.json').read_text(encoding='utf-8'));df=pd.DataFrame(rows)\ndisplay(df[['run_id','confirmed_failure','failure_stage','server_version','metadata_HTTP_exact_status','inference_attempts','server_model_residency']].T)\nfor r in rows:print(r['run_id'],r['exception'])"),
        ('md','**Yorum:**Her iki kayıt aynı digest guard hatasında durdu. API version/tags erişimi var; tam HTTP status kaydedilmemiş. Chat isteği gönderilmedi. Önceden yüklü model durumunu api/ps cevabı olmadan UNKNOWN tutuyoruz.'),
        ('code',"display(df[['run_id','RAM_available_GiB','RAM_deficit_MiB','GPU_free_MiB','commit_available_GiB','memory_gate_executed','initial_combined_gate_recomputed_pass']])\nfig,ax=plt.subplots(figsize=(7,3.4));ax.bar(['Deneme1','Deneme2'],df['RAM_available_GiB']);ax.axhline(2.5,color='red',ls='--',label='Değişmeyen v2 RAM tabanı');ax.set_ylabel('Kaydedilmiş ilk boş RAM GiB');ax.set_title('Digest guard sonrası bellek de izin vermeyecekti');ax.legend();fig.tight_layout();F=ROOT/'reports/figures/WP12/gemma1b_v2_failure_review';F.mkdir(parents=True,exist_ok=True);fig.savefig(F/'recorded_memory_gates.png',dpi=150);plt.show()"),
        ('md','**Yorum:**Betiğin bellek kapısına ulaşılmadı; tablo kayıtlı ilk ölçümü bağımsız yeniden hesaplıyor. RAM her iki durumda2,5GiB altında. Eşik veya timeout değişmiyor. Bu grafik modelin bellek tüketimi değildir.'),
        ('code',"display(pd.DataFrame([json.loads((Q/'digest_semantics_evidence.json').read_text(encoding='utf-8'))]).T)\ndisplay(pd.DataFrame([json.loads((Q/'minimal_correction_PROPOSED_ONLY.json').read_text(encoding='utf-8'))]).T)\nprint((Q/'diagnosis_tests.txt').read_text(encoding='utf-8'))"),
        ('md','**Yorum:**Yerel sarmalayıcı313f… ile API/kaynak manifest9755… farklı kimlik nesneleridir. Küçük metadata zinciri aynı config/layer içeriğini doğruluyor. Öneri yalnız kimlik alanlarını ayırmak; uygulanmadı.8 test gerçek kayıt teşhisini sınadı, inference başarısını değil. WP13 ve19×3 başlamadan burada durulur.')])


def close(report,source_hashes):
    prior=read(QA/'prior_artifacts_sha256.json')
    assert all(sha(ROOT/k)==v for k,v in prior.items())
    assert all(sha(ROOT/k)==v for k,v in source_hashes.items())
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    prefix=f'''# WP12 iki gerçek Gemma v2 hatası — teşhis tamamlandı, yeniden deneme yok ·08.11.2026

- İki ham deneme aynı MODEL_DIGEST_MISMATCH guard'ında durdu; timeout değil. API version/tags erişimi0.40.6 doğrulandı; tam metadata HTTP status UNKNOWN. Chat/inference0; sunucuda önceden yüklü model UNKNOWN.
- Betik313f… yerel sarmalayıcı SHA'sını bekliyor, API9755… kaynak manifest digest'ini döndürüyor. Aynı config/weight-layer zinciri metadata hash'iyle doğrulandı. Önceki kimlik bağlama hatası açıklandı; aktif runner/config/reviewer değiştirilmedi. Yalnız minimal düzeltme önerisi kaydedildi.
- Bellek kapısı çalışmadan guard attı. İlk RAM2,404907/2,395996GiB; bağımsız yeniden hesapta2,5GiB tabanı geçilmiyor. Timeout/eşik/seed değişmedi; model yükleme veya retry yapılmadı.
-8 offline gerçek kayıt testi geçti; önceki{len(prior)} dosya ve iki ham deneme korundu. Rapor reports/WP12_GEMMA1B_V2_FAILURE_REVIEW.md; notebook notebooks/WP12_gemma1b_v2_failure_review.ipynb; QA reports/qa/WP12/gemma1b_v2_failure_review/.
- Yeni inference/indirme/eğitim/19×3/WP13 yok. Sonuçlar kullanıcı incelemesine sunulmak üzere duruldu.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if k=='run_status.md' else ROOT/k)==v for k,v in prior.items())
    save(QA/'artifact_validation.json',{'status':'READ_ONLY_FAILURE_DIAGNOSIS_COMPLETE_NO_RETRY',
        'prior_artifacts_preserved':len(prior),'original_run_files_preserved':len(source_hashes),
        'runs_reviewed':2,'source_manifests_valid':2,'offline_tests_passed':8,
        'failure':'MODEL_DIGEST_MISMATCH_BEFORE_MEMORY_GATE_AND_CHAT',
        'API_metadata_access_verified':True,'exact_metadata_HTTP_status':'UNKNOWN_NOT_LOGGED',
        'timeout_failure_detected':False,'original_runs_inference_attempts':[0,0],
        'original_runs_model_residency':'UNKNOWN','original_first_RAM_gate_recomputed':[False,False],
        'active_runner_config_reviewer_changed':False,'memory_thresholds_changed':False,'timeout_changed':False,
        'proposed_identity_fix_applied':False,'review_inference_calls':0,'review_API_calls':0,'model_downloads':0,
        'real_scenario_repeats':0,'WP13_started':False,'notebook_executed_code_cells':3,
        'prior_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,ROOT/'scripts/wp12_gemma_failure_diagnosis.py',
        ROOT/'scripts/wp12_gemma_failure_review_outputs.py',ROOT/'tests/test_wp12_gemma_failure_diagnosis.py',
        ROOT/'notebooks/WP12_gemma1b_v2_failure_review.ipynb',
        ROOT/'reports/figures/WP12/gemma1b_v2_failure_review/recorded_memory_gates.png',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('Read-only diagnosis complete; original files preserved',len(prior),'tests8; no retry or active fix')


if __name__=='__main__':main()
