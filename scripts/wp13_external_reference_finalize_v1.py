"""Finalise this reference-only evidence, preserve previous status bytes exactly."""
from pathlib import Path
import json
import pandas as pd
import nbformat
import wp13_external_reference_v1 as r

def main():
    if (r.Q/'reference_comparison_lock.json').exists():raise RuntimeError('VERSION_ALREADY_FINAL_NO_OVERWRITE')
    r.verify_locks();r.verify_pins(r.read(r.Q/'prior_pins.json'));r.verify_pins(r.read(r.Q/'presentation_pins.json'))
    old=(r.Q/'run_status_before.md').read_bytes()
    if (r.ROOT/'run_status.md').read_bytes()!=old:raise RuntimeError('STATUS_CHANGED_DURING_WORK_STOP_NO_CLOBBER')
    ui=r.read(r.Q/'Streamlit_AppTest_results.json');assert len(ui['checks'])==7 and all(t['status']=='PASS' for t in ui['checks'])
    finaltest=(r.Q/'reference_tests_final.log').read_text(encoding='utf-8-sig');assert 'Ran 36 tests' in finaltest and '\nOK' in finaltest
    # Notebook closing QA is actually executed; frozen input/explanation cells are not rerun.
    npath=r.ROOT/'notebooks/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.ipynb';n=nbformat.read(npath,as_version=4)
    cell=nbformat.v4.new_code_cell("from IPython.display import Image, display\nprint((r.Q/'reference_tests_final.log').read_text(encoding='utf-8-sig'))\ndisplay(pd.DataFrame(r.read(r.Q/'Streamlit_AppTest_results.json')['checks']))\ndisplay(Image(filename=str(r.F/'screenshots/04_diarrhoea_two_columns.jpg')))\ndisplay(Image(filename=str(r.F/'screenshots/06_thrombocytopenia_class_warning.jpg')))\ndisplay(Image(filename=str(r.F/'screenshots/07_anaphylactic_shock_no_crosswalk.jpg')))\n")
    # Use standard IPython capture to execute the new evidence-display cell, no model operations.
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    shell=InteractiveShell.instance();shell.user_ns.update({'r':r,'pd':pd})
    with capture_output(display=True) as cap: result=shell.run_cell(cell.source,store_history=False)
    if result.error_in_exec or result.error_before_exec:raise RuntimeError('FINAL_NOTEBOOK_CELL_FAILED')
    import base64
    cell.execution_count=6;cell.outputs=[]
    if cap.stdout:cell.outputs.append(nbformat.v4.new_output('stream',name='stdout',text=cap.stdout))
    for out in cap.outputs:
        data={k:base64.b64encode(v).decode('ascii') if isinstance(v,bytes) else v for k,v in out.data.items()}
        cell.outputs.append(nbformat.v4.new_output('display_data',data=data,metadata=out.metadata))
    n.cells += [nbformat.v4.new_markdown_cell('## Nihai teknik kanıt ve gerçek ekranlar\n\n36 kaynak/kilit/izolasyon testi ve7 gerçek Streamlit widget kontrolü PASS. Aşağıdaki görüntüler gerçek localhost arayüzünden alınmıştır; semantik doğruluk veya klinik başarı ölçütü değildir. İlk AppTest false-failure, Markdown metnini incelemeyen test harness sorunuydu; başarısız log korunup okuma kapsamı düzeltilerek ayrı rerun kaydı tutuldu. İnsan incelemesi PENDING. STOP.'),cell]
    nbformat.validate(n);nbformat.write(n,npath)
    shots=[]
    from PIL import Image
    for p in sorted((r.F/'screenshots').glob('*.jpg')):
        with Image.open(p) as image: w,h=image.size
        shots.append({'file':p.relative_to(r.ROOT).as_posix(),'sha256':r.sha(p),'width':w,'height':h,
            'source':'real browser screenshot of local Streamlit, no synthetic image',
            'role':'INTERMEDIATE_NOT_PRESENTATION' if p.name.startswith('01_') else 'PRESENTATION_EVIDENCE'})
    r.dump(r.Q/'browser_QA.json',{'verified_utc':r.now(),'url':'http://127.0.0.1:8513/',
        'app':'apps/drug_safety_explorer_FINAL_v3.py','browser':'Codex in-app Chromium browser',
        'observed_cases':['all10 locked rankings','diarrhoea: correct p7 quote, score and model1 SHAP',
            'thrombocytopenia: class-other-member p2→p3 plus distinct volunteer platelet decrease',
            'anaphylactic shock: no crosswalk, not negative; preserved real SHAP'],
        'screenshots':shots,'presentation_screenshots':6,
        'human_clinical_review':'PENDING','API':False,'new_model_execution':False,
        'restricted_environment_startup':'Did not expose a listening localhost server; root cause UNKNOWN. Own stalled commands stopped. Normal local host server used with approved tool execution.',
        'AppTest_first_host_failure':'Test harness omitted st.markdown from content inspection, not model/source failure. Original failure log kept; corrected read-only assertions rerun separately.',
        'user_programs_stopped':False,'dependencies_installed':False})
    report=r.ROOT/'reports/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.md'
    with report.open('a',encoding='utf-8') as f:
        f.write('''\n\n## Nihai QA eki\n\nNihai kaynak/kilit/izolasyon kontrolü **36/36 PASS**, Streamlit AppTest **7/7 PASS**. Önceki29test logu korunur; final log ayrı dosyadır. Notebook6çalıştırılmış kod hücresidir ve gerçek tarayıcı ekranlarını da içerir.6sunum ekranı screenshots/02–07 dosyalarıdır;01ilk ara ekran olarak ayrıca saklandı. İlk host AppTest denemesi testin st.markdown metnini okuma kapsamına almaması nedeniyle false-failure verdi; arayüz/sayısal sonuç değiştirilmeden test okuması düzeltildi ve ayrı rerun logu üretildi. Kısıtlı yürütme ortamındaki ilk sunucu/testrunner yerel port açmadı; kesin neden UNKNOWN. Kullanıcı uygulamaları durdurulmadı, bağımlılık kurulmadı. Gerçek ekran denetimi normal localhost QAport8513 üzerinden tamamlandı. Kullanıcı launcher varsayılan8501.\n\nÇapraz sayfa sınıf cümlesi class_scope_bridge.json ile sayfa2sonundan sayfa3uyarısına bağlanır.50mevcut açıklama ve kaynak durumu model_reference_explanations50.csv/json içinde ayrı sütunlardadır. SHAP metnindeki numpy scalar yazımı arayüzde yalnız tip sarmalayıcısı kaldırılarak gösterilir; ham immutable paragraf ve sayısal değerler değişmez. TümPROVISIONAL ve insanPENDING durumları korunur.\n\nÇalıştırma: normal PowerShell'de proje kökünden `& ".\\scripts\\WP13_Start_FINAL_DEMO_v3.ps1"` ve tarayıcıda localhost:8501. QAörneği mevcut localhost:8513 adresindedir. “Çalışma alanı → Tedizolid dış tahmin deneyi” seçilir. Önceki demosu aynı v3içinden açılır; eski v2dosyası değişmedi.\n''')
    # Archive exact history, then append-only-style prepend (all old bytes retained).
    entry='''# 2026-11-09 — WP13_EXTERNAL_REFERENCE_COMPARISON_v1 tamamlandı / STOP

SIVEXTRO kullanıcı KÜB referansı ayrı kaydedildi:15 sayfa,76 özgün4.8 tablo terimi (7 yaygın,69 yaygın olmayan). Prediction301a116e… ve explanationdb756d0a… değişmedi. Önceden kilitli ilk10'da6 çeviri/eşanlam adayı,2 ilişkili eşdeğerliği doğrulanmamış,1 sınıf uyarısı,1 eşleme saptanmayan hedef; uzman eşlemesi PROVISIONAL/insan PENDING.201 skor,50 model/PT ve300 SHAP katkısı değişmedi. Klinik başarı/AP/AUROC NOT_CALCULABLE. Aktif tedizolid ile fosfat IV ürün farkı ve STRICT_ANALYST_BLINDNESS_COMPROMISED korundu.

36 kaynak/kilit/izolasyon testi +7 Streamlit akış kontrolü PASS.6 gerçek sunum ekranı,çalıştırılmış6 hücreli notebook,Türkçe rapor,CSV/JSON,ayrı hamPDF kopyası,aralıklar ve hash manifestleri hazır. Eski1.069 dosya doğrulandı; eski run_status baytları bu girişin altında ve yeni QA/run_status_before.md içinde aynen korunur. Yeni model forward/SHAP/eğitim/API/OCR yok. Yeni FINALv3 modu: scripts/WP13_Start_FINAL_DEMO_v3.ps1 (varsayılan localhost:8501). Referans/PT uzman incelemesi için kullanıcı değerlendirmesi bekleniyor; WP14 veya başka deney başlatılmadı.

---

'''
    (r.ROOT/'run_status.md').write_bytes(entry.encode('utf-8')+old)
    assert (r.ROOT/'run_status.md').read_bytes().endswith(old)
    r.verify_locks();r.verify_pins(r.read(r.Q/'prior_pins.json'));r.verify_pins(r.read(r.Q/'presentation_pins.json'))
    r.dump(r.Q/'final_verification.json',{'verified_utc':r.now(),'status':'REFERENCE_COMPARISON_COMPLETE_STOP_HUMAN_REVIEW_PENDING',
        'prediction_lock_sha256':r.PRED_HASH,'explanation_lock_sha256':r.SHAP_HASH,
        'prior_artifacts_unchanged':len(r.read(r.Q/'prior_pins.json')),'source_tests_passed':36,
        'Streamlit_checks_passed':7,'notebook_executed_code_cells':6,'real_presentation_screenshots':6,
        'comparison_PT':201,'locked_top_PT':10,'existing_model_PT_explanations':50,'existing_SHAP_values':300,
        'source_terms':76,'all_page_texts':15,'new_model_forward':0,'new_SHAP_computations':0,'training':0,'API':0,'OCR':0,
        'expert_approved_crosswalk':0,'human_review':'PENDING','clinical_success_metric':'NOT_CALCULABLE',
        'old_status_exact_bytes_preserved':True,'prior_blindness':'STRICT_ANALYST_BLINDNESS_COMPROMISED_PRESERVED'})
    paths=[p for folder in [r.Q,r.F] for p in folder.rglob('*') if p.is_file()]
    paths += [r.ROOT/p for p in ['scripts/wp13_external_reference_v1.py','scripts/wp13_external_reference_ui_v1.py',
        'scripts/wp13_external_reference_deliverables_v1.py','scripts/wp13_external_reference_ui_tests_v1.py',
        'scripts/wp13_external_reference_finalize_v1.py','scripts/WP13_Start_FINAL_DEMO_v3.ps1',
        'apps/drug_safety_explorer_FINAL_v3.py','tests/test_wp13_external_reference_v1.py',
        'docs/plan/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.md','reports/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.md',
        'notebooks/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.ipynb','run_status.md']]
    pins={p.relative_to(r.ROOT).as_posix():r.sha(p) for p in paths}
    r.dump(r.Q/'reference_comparison_lock.json',{'created_utc':r.now(),'prediction_lock_sha256':r.PRED_HASH,
        'explanation_lock_sha256':r.SHAP_HASH,'outputs_sha256':pins,'status':'LOCKED_REFERENCE_REVIEW_PENDING',
        'human_approval':False,'performance_metric':None})
    r.dump(r.Q/'reference_comparison_lock_sha256.json',{'sha256':r.sha(r.Q/'reference_comparison_lock.json')})
    pins[(r.Q/'reference_comparison_lock.json').relative_to(r.ROOT).as_posix()]=r.sha(r.Q/'reference_comparison_lock.json')
    pins[(r.Q/'reference_comparison_lock_sha256.json').relative_to(r.ROOT).as_posix()]=r.sha(r.Q/'reference_comparison_lock_sha256.json')
    r.dump(r.Q/'evidence_manifest.json',pins);r.verify_pins(pins)
    print(json.dumps({'status':'COMPLETE_STOP','outputs':len(pins),'reference_comparison_lock':r.sha(r.Q/'reference_comparison_lock.json'),'prior_unchanged':len(r.read(r.Q/'prior_pins.json')),'tests':36,'UI_checks':7,'human':'PENDING'},ensure_ascii=False))

if __name__=='__main__':main()
