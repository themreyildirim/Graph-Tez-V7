"""Bellek nedeniyle durdurulan yerel pilotun gerçek QA/rapor/notebook kaydı."""
import json
from pathlib import Path
import subprocess
import sys
from wp12_local_llm_preflight import ROOT,QA,sha,save


def main():
    p=json.loads((QA/'preflight.json').read_text(encoding='utf-8'))
    model=json.loads((QA/'model_identity.json').read_text(encoding='utf-8'))
    assert p['status']=='STOPPED_INSUFFICIENT_RAM'
    assert not (QA/'artifact_validation.json').exists()
    test_results=[]
    for pattern in ['test_wp12_llm_contract.py','test_wp12_llm_preflight.py']:
        r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=ROOT)
        name=pattern.removesuffix('.py')+'_audit.txt';assert not (QA/name).exists()
        (QA/name).write_text(r.stdout+r.stderr,encoding='utf-8')
        test_results.append({'pattern':pattern,'exitcode':r.returncode,'log':name})
        assert r.returncode==0
    save(QA/'initial_memory_observation.json',{
        'observed_at':'2026-11-08T03:23:20.065213+03:00','total_bytes':7968415744,
        'available_bytes':386510848,'used_percent':95.1,
        'GPU_total_MiB':4096,'GPU_free_MiB':3935,
        'source':'initial read-only psutil/nvidia-smi tool stdout; before Ollama metadata checks'})
    ram=p['RAM'];gpu=p['GPU']
    text=f'''# WP12 — Yerel Qwen3 pilotu: ön kontrol ve bellek nedeniyle durma

08.11.2026 · **STOPPED_INSUFFICIENT_RAM**. Seçilen aday `{model['tag']}`; yeni model indirilmedi. Model yüklenmedi, smoke test veya gerçek LLM senaryosu çalıştırılmadı. WP13 başlamadı.

## Doğrulananlar
AGENTS, aktif ROADMAP ve WP12 kaynaklı LLM sözleşmesi korundu. Kullanıcının mevcut4B modeli seçmesi yalnız bu yeni aday kaydına işlendi; önceki öneri/config/19 senaryo/44 alıntı değiştirilmedi.

| Kontrol | Gerçek sonuç |
|---|---|
| Ollama istemci sürümü | `ollama.exe --version`: **0.40.6**; istemciye ait sürüm, servis sürümü doğrulanmadı |
| Yerel model manifest digest | `{model['manifest_digest']}` |
| İçerik bütünlüğü | Manifest config ve4 layer dosyasının boyutu/tam SHA-256 doğrulandı; ağırlık akışla hash'lendi, inference için yüklenmedi |
| İlk RAM ölçümü | 03:23:20+03:00; boş **0,36GiB**, kullanım%95,1 |
| Kayıtlı ikinci ölçüm | {p['captured_at']}; boş **{ram['available']/2**30:.2f}GiB**, toplam {ram['total']/2**30:.2f}GiB, kullanım%{ram['percent']} |
| GPU | {gpu['name']}; toplam{gpu['total_MiB']}MiB, boş{gpu['free_MiB']}MiB; sürücü{gpu['driver']} |
| Bellek kapısı | En az3GiB boş host RAM ve2,5GiB boş VRAM planlama tabanı; **RAM koşulu geçilmedi** |
| Yerel API metadata | Yalnız GET /api/version ve /api/tags denendi; WinError10013 socket erişim hatası; cevap alınamadı |
| JSON Schema API desteği | **UNVERIFIED**; gerçek şema kontrollü çıkarım yapılmadı |

Ölçümler anlıktır; 0,36→{ram['available']/2**30:.2f}GiB değişimi bellek boşaltıldığı veya kapının geçtiği anlamına gelmez. 3GiB kuralı üretici minimumu/sığma garantisi değildir; önceki tasarımın küçük aday planlama tabanıdır. Mevcut4B için bu taban sağlansa bile yeterlilik ayrıca sınırlı smoke testle ölçülmelidir. Burada taban dahi geçilmediğinden model yüklenmedi.

CLI “could not connect to a running Ollama instance” uyarısı verdi. API socket hatası, servisin kurulu olmadığı veya kesinlikle çalışmadığı kanıtı değildir; bu ortamda erişilemediği anlamına gelir. Servis başlatılmadı, güvenlik/izin ayarı değiştirilmedi, otomatik yetki yükseltme denenmedi. Bellek engeli bağımsız olarak devam ettiği için API erişimi zorlanmadı. İstemci sürüm numarası tek başına yerel JSON Schema desteğinin uygulamada doğrulandığı anlamına gelmez.

## Durdurulan işler ve bilimsel sınırlar
- Smoke test: **NOT_RUN_MEMORY_GATE**; başarısız LLM cevabı veya başarılı test gibi sunulmaz.
- Dondurulmuş19 senaryo ×3 tekrar = **57 planlı kayıt**; hepsi NOT_RUN_MEMORY_GATE, çıktı ve şema/kaynak değerlendirmesi null. Hiçbiri başarı0 değildir; en iyi çıktı seçilmedi.
- İnsan semantik incelemesi: **NOT_PERFORMED_NO_OUTPUT**. Yerine otomatik/AI anlam onayı konmadı.
- `reported_in_PDF` / `predicted_by_GNN` sözleşmesi değişmedi; LLM çıktısı bulunmadığından açıklama zarfı veya sahte yanıt üretilmedi. Otomatik yayın sayısı0.
- 24 mevcut kaynaklı sözleşme testi ve6 yeni bellek kapısı testi geçti. Bunlar offline Python kontrolleridir; **Ollama JSON Schema API testi veya LLM kalite kanıtı değildir**. Eski loglar ezilmedi.
- Model skoru, SHAP, Δz, MedDRA etiketi, yeni yan etki, PDF/eğitim girdisi veya klinik risk bilgisi üretilmedi. Model eğitimi ve PDF indirme yoktur.

## Çıktılar ve yeniden başlama koşulu
Yeni QA dizini: `reports/qa/WP12/local_llm_pilot_v1/`. `preflight.json` gerçek RAM/VRAM/sürüm/API hatalarını; `model_identity.json` tam model digest ve akış hash kanıtını; `scenario_execution_status.json`57 çalıştırılmayan kaydı; `approved_candidate_record.json` kullanıcı seçimi ve değişmeyen sözleşme/senaryo hash'lerini tutar. Notebook yalnız bu gerçek kayıtları gösterir; LLM çıktısı üretmez.

Önceki3.310 dosya başlangıç hash kaydıyla korundu; ham PDF'ler,44 alıntı ve tüm kabul edilmiş model/QA sonuçları değişmedi. `run_status.md` güncel durumu öne ekler; önceki tam baytlar yeni QA arşivinde ve dosyanın sonunda tutulur. Son kanıt manifesti ve koruma sonucu ayrı dosyadadır.

Devam etmek için kullanıcı RAM kullanan uygulamaları kapattıktan sonra ölçüm yenilenmeli. Bellek yeterliyse erişilebilir yerel Ollama servis sürümü ve API yeteneği doğrulanmalı; model/prompt/config tam hash'leri ilk çıkarımdan önce dondurulmalı. Mevcut tam digest farklı çıkarsa sessiz tag değişimi yapılmamalı. Ardından yalnız onaylanan sınırlı smoke test, geçerse aynı sabit ayarla19×3 senaryo uygulanabilir. Bellek/API engeli çözülmeden yeniden deneme yapılmadı. Bu tur burada durur.
'''
    report=ROOT/'reports/WP12_LOCAL_LLM_PILOT_PREFLIGHT.md'
    assert not report.exists();report.write_text(text,encoding='utf-8')
    make_notebook()
    prior=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in prior.items())
    previous=json.loads((ROOT/'reports/qa/WP12/llm_design_v1/evidence_manifest.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/k)==v for k,v in previous.items())
    history=(QA/'run_status_before.md').read_bytes()
    assert (ROOT/'run_status.md').read_bytes()==history
    prefix=f'''# WP12 yerel Qwen3 pilotu — bellek nedeniyle durdu · 08.11.2026

- Kullanıcı mevcut qwen3:4b-instruct-2507-q4_K_M modelini seçti; yeni indirme yok. İstemci sürümü0.40.6; tam manifest/config/layer hash doğrulandı.
- İlk boş RAM0,36GiB, kayıtlı ikinci ölçüm{ram['available']/2**30:.2f}GiB;3GiB planlama tabanı geçilmedi. GPU4GiB, boş3935MiB. Model yüklenmedi.
- Yerel API metadata GET denemeleri WinError10013 verdi; servis sürümü ve JSON Schema API desteği UNVERIFIED. Erişim zorlanmadı/servis başlatılmadı.
- Smoke ve19×3 senaryo NOT_RUN_MEMORY_GATE; insan anlam incelemesi NOT_PERFORMED_NO_OUTPUT; otomatik yayın0. Offline24 sözleşme+6 bellek testi geçti; API/LLM başarısı sayılmaz.
- Önceki3.310 dosya, ikiPDF/44 alıntı, modeller ve sonuçlar korundu. Rapor: reports/WP12_LOCAL_LLM_PILOT_PREFLIGHT.md; notebook: notebooks/WP12_local_llm_preflight.ipynb; QA: reports/qa/WP12/local_llm_pilot_v1/.
- Yeni eğitim/model/etiket/skor yok; WP13 başlamadı. RAM ve yerel API erişimi uygun hale getirilmeden inference yapılmayacak. Kullanıcı incelemesi bekleniyor.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert all(sha(QA/'run_status_before.md' if k=='run_status.md' else ROOT/k)==v for k,v in prior.items())
    save(QA/'artifact_validation.json',{'status':'STOPPED_INSUFFICIENT_RAM','prior_artifacts_preserved':len(prior),
        'previous_design_manifest_entries_verified':len(previous),'offline_tests_passed':30,
        'model_manifest_and_all_layer_hashes_valid':model['all_layers_content_verified'],
        'actual_inference_calls':0,'model_loads':0,'planned_scenario_repeats':57,'executed_scenario_repeats':0,
        'schema_API_support':'UNVERIFIED','human_semantic_review':'NOT_PERFORMED_NO_OUTPUT',
        'model_download':False,'training':False,'new_labels_or_scores':0,'auto_published_explanations':0,
        'WP13_started':False,'previous_run_status_exact_bytes_retained':True})
    files=list(QA.glob('*'))+[report,ROOT/'notebooks/WP12_local_llm_preflight.ipynb',ROOT/'reports/figures/WP12/local_llm_pilot_v1/memory_gate.png',
        ROOT/'scripts/wp12_local_llm_preflight.py',ROOT/'scripts/wp12_local_llm_preflight_outputs.py',ROOT/'tests/test_wp12_llm_preflight.py',ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files)) if p.is_file()})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print('Preserved:',len(prior),'offline tests:30; inference:0; STOPPED_INSUFFICIENT_RAM')


def make_notebook():
    from wp09_close_wp10_notebooks import execute
    parts=[('md','# WP12 — Mevcut Qwen3 modeli ön kontrolü\n**Bellek kapısında duruldu.** Notebook gerçek kayıtları gösterir; model yükleme, çıkarım, indirme veya eğitim içermez. Kaynaklı açıklama/insan incelemesi kuralları değişmedi.'),
      ('code',"from pathlib import Path\nimport json,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT=Path.cwd();Q=ROOT/'reports/qa/WP12/local_llm_pilot_v1'\np=json.loads((Q/'preflight.json').read_text(encoding='utf-8'));m=json.loads((Q/'model_identity.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([{'Ölçüm':p['captured_at'],'Boş RAM GiB':p['RAM']['available']/2**30,'RAM kullanım %':p['RAM']['percent'],'GPU boş MiB':p['GPU']['free_MiB'],'Bellek kapısı':p['memory_gate_passed']}]))\nfig,ax=plt.subplots(figsize=(7,3));ax.barh(['İlk boş RAM','İkinci boş RAM','Planlama tabanı'],[386510848/2**30,p['RAM']['available']/2**30,3],color=['orange','orange','grey']);ax.set_xlabel('GiB');ax.set_title('İki gerçek ölçüm de RAM kapısının altında')\nF=ROOT/'reports/figures/WP12/local_llm_pilot_v1';F.mkdir(parents=True,exist_ok=True);fig.tight_layout();fig.savefig(F/'memory_gate.png',dpi=150);plt.show()"),
      ('md','**Yorum:** Bellek anlık değişiyor; her iki ölçüm de3GiB tabanının altında. Bu bir üretici sığma garantisi değildir. Mevcut4B modeli bu durumda zorla yüklemiyoruz.'),
      ('code',"print(p['client_version_check']['stdout']);print('Tam model manifest digest:',m['manifest_digest'])\ndisplay(pd.DataFrame(m['layers'])[['digest','size','actual_size','digest_valid','size_valid']])\ndisplay(pd.DataFrame(p['loopback_metadata_attempts']))"),
      ('md','**Yorum:** İstemci0.40.6 ve modelin gerçek dosya hash\'leri doğrulandı. Servis sürümü ve JSON Schema API desteği doğrulanamadı: socket erişim hatası alındı; bu, servisin yokluğunun kanıtı değildir. Akışla ağırlık hash\'i almak inference için modeli yüklemek değildir.'),
      ('code',"records=pd.DataFrame(json.loads((Q/'scenario_execution_status.json').read_text(encoding='utf-8')))\ndisplay(records.groupby(['scenario_id','status'],as_index=False).agg(planlanan_tekrar=('repeat','count')))\ndisplay(records[['status','LLM_output','schema_result','human_semantic_review']].head(3))\nprint('Planlanan',len(records),'Çalıştırılan',0)"),
      ('md','**Yorum:**19×3 planın tamamı NOT_RUN_MEMORY_GATE. Null kalite/şema sonuçları başarı sıfırı değildir. Gerçek yanıt bulunmadığından insan semantik incelemesi veya otomatik yayın yoktur. reported_in_PDF ile predicted_by_GNN alanları için sahte açıklama üretilmedi.'),
      ('code',"for name in ['test_wp12_llm_contract_audit.txt','test_wp12_llm_preflight_audit.txt']:\n print(name);print((Q/name).read_text(encoding='utf-8'))"),
      ('md','**Yorum:**24 kaynak sözleşmesi ve6 bellek kapısı testi offline geçti. Bunlar yerel Ollama JSON Schema desteğini veya LLM kalitesini doğrulamaz. Kaynak/model sonuçları korunur. RAM ve API erişimi uygun hale gelene kadar bu aşamada durulur; WP13 başlamadı.')]
    execute('WP12_local_llm_preflight.ipynb',parts)


if __name__=='__main__':
    main()
