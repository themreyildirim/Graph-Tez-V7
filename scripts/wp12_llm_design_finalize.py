"""Yeni LLM tasarım ekini doğrular; kabul edilmiş kaynaklara yazmaz."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT/'reports/qa/WP12/llm_design_v1'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def verify_only():
    m = read(QA/'evidence_manifest.json')
    assert all(sha(ROOT/p) == h for p,h in m.items())
    assert sha(QA/'evidence_manifest.json') == (QA/'evidence_manifest.sha256').read_text().split()[0]
    print('New evidence manifest verified:', len(m))


def main():
    if '--verify-only' in sys.argv:
        verify_only(); return
    assert not (QA/'artifact_validation.json').exists(), 'Closure evidence must not be overwritten'
    prior = read(QA/'prior_artifacts_sha256.json')
    history = (QA/'run_status_before.md').read_bytes()
    assert (ROOT/'run_status.md').read_bytes() == history
    assert all(sha(ROOT/p) == h for p,h in prior.items())
    # Önceki manifestin tek değişebilir status girdisini bu aşamanın arşivine çöz.
    pilot_manifest_path = ROOT/'reports/qa/WP12/pilot_v1/evidence_manifest.json'
    pilot = read(pilot_manifest_path)
    assert all(sha(QA/'run_status_before.md' if p=='run_status.md' else ROOT/p)==h for p,h in pilot.items())
    assert sha(pilot_manifest_path) == pilot_manifest_path.with_suffix('.sha256').read_text().split()[0]
    import nbformat
    nbpath=ROOT/'notebooks/WP12_local_llm_design.ipynb'
    nb=nbformat.read(nbpath,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code']
    assert [c.execution_count for c in code]==list(range(1,len(code)+1))
    assert all(c.outputs and all(o.output_type!='error' for o in c.outputs) for c in code)
    images=sum('image/png' in o.get('data',{}) for c in code for o in c.outputs)
    assert images==3
    scenarios=read(QA/'frozen_scenarios.json')
    assert len(scenarios)==19 and all(s['LLM_status']=='NOT_RUN_NO_LLM' and s['semantic_result'] is None for s in scenarios)
    from wp12_llm_contract import load_sources, source_index, dependencies
    bundle,ann=load_sources();quotes,_,_=source_index(bundle,ann);deps=dependencies(ann)
    for s in scenarios:
        ids=set(s['evidence_ids'])
        assert all(deps[q]<=ids for q in ids)
        for ref in s['sources']:
            q=quotes[ref['quote_id']]
            assert ref['document_id']==q['document_id'] and ref['physical_page']==q['page_number']
            assert ref['char_start']==q['char_start'] and ref['char_end']==q['char_end'] and ref['quote_sha256']==q['quote_sha256']
    tests=(QA/'contract_tests_v2.txt').read_text(encoding='utf-8')
    assert 'Ran 24 tests' in tests and tests.rstrip().endswith('OK')
    report=ROOT/'reports/WP12_LOCAL_LLM_FEASIBILITY.md'
    with report.open('a',encoding='utf-8') as f:
        f.write('\n## Yürütme kaydı ve son kontrol\nNotebook\'un7 kod hücresi gerçek IPython yürütmesiyle çalıştırıldı;3 PNG gömüldü ve görsel olarak incelendi. İlk nbclient harici kernel denemesi çıktı üretmeden beklediği için durduruldu; başarılı kernel çalışması iddia edilmedi. Projede önceki paketlerde kullanılan sıralı IPython yürütücüsüyle hücreler gerçekten çalıştırılıp tablo/grafik çıktıları yakalandı. Bu teknik yürütme farkı kaynak/metot kararını veya LLM iznini değiştirmedi. İki ayrı teknik test logu korundu; ikisinde de24 test geçti.\n\nSon bütünlük denetimi:3.282 önceki dosya ve eski pilot manifestindeki74 girdi doğrulandı; run_status tarihsel baytları arşivden kontrol edildi.19 senaryonun kaynak ve bağlam bağlantıları geçerli; gerçek LLM yanıtı/başarı ölçümü yoktur.\n')
    prefix='''# WP12 yerel LLM tasarımı — kullanıcı onayı bekleniyor · 08.11.2026

- Kullanıcı iki PDF ile gerçek çıkarım pilotunu kabul etti. Yalnız kaynaklı yerel LLM tasarımı/donanım incelemesi yapıldı; WP12 nihai kapanışı veya WP13 başlamadı.
- 44 alıntı,17 sayfa,iki PDF ve3.282 önceki dosyanın hash\'leri korundu. Önceki run_status tam baytları aşağıda ve yeni QA arşivinde tutuldu.
- Kaynak cümle/sayfa/aralık/SHA zorunlu; reported_in_PDF ile predicted_by_GNN ayrı. Yapısal geçiş anlam doğruluğu değildir; bütün adaylar insan incelemesinde bekler.
- Gerçek kaynaklı19 senaryo ve24 geçen teknik sözleşme testi; LLM senaryoları NOT_RUN_NO_LLM. Çalıştırılmış tasarım notebook\'u7 kod hücresi/3 PNG içerir. Harici kernel denemesi tamamlanmadı; mevcut IPython yürütücüsüyle gerçek hücre yürütmesi yapıldı.
- Donanım:7,42GiB kullanılabilir toplam RAM, anlık yaklaşık0,77GiB boş; GTX1650Ti4GiB. Mevcut RAM ile çalıştırma önerilmedi. Ollama binary ve Qwen3 4B-instruct önbellek manifesti mevcut; sürüm/API/inference doğrulanmadı.
- Birincil küçük aday Qwen3:1.7b Q4_K_M; Gemma3:1b alternatifi ve mevcut4B koşullu seçeneği raporlandı. Hiçbir seçim kurulum/indirme/çalıştırma onayı sayılmaz.
- Çıktılar: reports/WP12_LOCAL_LLM_FEASIBILITY.md; docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md; configs/WP12_local_llm_PROPOSED_v1.json; notebooks/WP12_local_llm_design.ipynb; reports/qa/WP12/llm_design_v1/.
- Kurulum, model indirme, Ollama/LLM çalıştırma, yeni eğitim veya PDF bilgisini modele yazma yok. Gerçek uygulama için kullanıcı onayı bekleniyor.

---
Önceki run_status (tam tarihsel kayıt):

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    assert (ROOT/'run_status.md').read_bytes().endswith(history)
    assert all(sha(QA/'run_status_before.md' if p=='run_status.md' else ROOT/p)==h for p,h in prior.items())
    result={'date':'2026-11-08','status':'DESIGN_COMPLETE_AWAITING_USER_APPROVAL',
            'prior_artifacts_preserved':len(prior),'old_pilot_manifest_entries_verified':len(pilot),
            'source_documents':2,'source_pages':17,'source_quotes':44,'raw_PDFs_and_quotes_unchanged':True,
            'technical_tests_passed':24,'test_logs_retained':['contract_tests_v1.txt','contract_tests_v2.txt'],
            'scenarios_defined':19,'scenario_provenance_and_dependencies_valid':True,
            'LLM_scenarios':'NOT_RUN_NO_LLM','semantic_quality':'NOT_MEASURED',
            'executed_notebook_cells':len(code),'embedded_PNGs':images,'static_figures_visually_reviewed':3,
            'notebook_execution':'real sequential IPython execution; external kernel attempt not completed',
            'install':False,'model_download':False,'LLM_execution':False,'training':False,
            'automatically_released_explanations':0,'new_training_features_or_labels':0,
            'WP13_started':False,'previous_run_status_exact_bytes_retained':True,
            'hardware_feasibility':'CONDITIONAL; current available host RAM fails proposed planning gate',
            'Ollama_version_API_compatibility':'UNVERIFIED_NO_EXECUTION'}
    save(QA/'artifact_validation.json',result)
    new_files=[p for p in QA.rglob('*') if p.is_file() and p.name not in ['evidence_manifest.json','evidence_manifest.sha256']]
    new_files+=list((ROOT/'reports/figures/WP12/llm_design_v1').glob('*.png'))
    new_files += [ROOT/p for p in ['scripts/wp12_llm_contract.py','scripts/wp12_llm_design_outputs.py','scripts/wp12_llm_design_finalize.py','tests/test_wp12_llm_contract.py','docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md','docs/schemas/WP12_local_llm_candidate_v1.schema.json','configs/WP12_local_llm_PROPOSED_v1.json','reports/WP12_LOCAL_LLM_FEASIBILITY.md','notebooks/WP12_local_llm_design.ipynb','run_status.md','reports/qa/WP12/pilot_v1/source_evidence_bundle.json','reports/qa/WP12/pilot_v1/source_context_annotations.json','data/user_pdfs/pil.502.pdf','data/user_pdfs/050641Orig1s032lbl.pdf']]
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(new_files))})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    verify_only();print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
