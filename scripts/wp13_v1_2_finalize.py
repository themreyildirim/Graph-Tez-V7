"""Explicit public-file preservation check. Never reads environment files or runs inference."""
from pathlib import Path
import hashlib,json,ast
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/v1_2'
from wp12_api_security import public_sha

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,data):
    with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)

protected=read(Q/'protected_prior_public_files.json')
pins=read(Q/'blind_source_pins.json')
for label,files in [('prior',protected),('blind_sources',pins)]:
    for name,h in files.items():
        if public_sha(ROOT/name)!=h:raise ValueError(label+': '+name)

nb=read(ROOT/'notebooks/WP13_demo_v1_2.ipynb')
code=[c for c in nb['cells'] if c['cell_type']=='code']
assert len(code)==4 and all(c['execution_count'] for c in code)
assert not any(o['output_type']=='error' for c in code for o in c['outputs'])
assert 'Ran 20 tests' in (Q/'v1_1_regression_tests.log').read_text(encoding='utf-8-sig')
assert read(Q/'test_summary.json')['returncode']==0
sources=['scripts/wp08_baseline_train.py','scripts/wp09_data.py','scripts/wp10_train.py',
 'scripts/wp10_training_forward.py','scripts/wp10_molecular_encoder.py','configs/WP09_training_PROPOSED_v3.json',
 'configs/WP10_encoder_IMPLEMENTED_v1.json']
write(Q/'audited_training_code_pins.json',{n:public_sha(ROOT/n) for n in sources})
for name in ['apps/drug_safety_explorer_v1_2.py','scripts/wp13_presentation_v1_2.py','scripts/wp13_blind_audit_v1.py','scripts/wp13_v1_2_deliverables.py','tests/test_wp13_v1_2.py']:
    ast.parse((ROOT/name).read_text(encoding='utf-8'))
before=(Q/'run_status_before.md').read_bytes()
assert (ROOT/'run_status.md').read_bytes()==before,'Status changed concurrently; do not overwrite'
prefix='''# WP13 v1.2 — Türkçe kaynak sunumu ve kör tahmin fizibilitesi ·09.11.2026

Erythromycin34 kayıt/34 terim/34 Türkçe ad; Doxycycline34/33/33 (ishal iki kapsam). Klinik doğrulanmış sayı değil. Türkçe source-bound editorial translation ve eski PENDING LLM ayrı; İngilizce orijinal kanıt açılır bölümde. Tek candidate_id ile picker/tablo/iki detay senkron.18 yeni test ve20 v1.1 regresyon testi PASS;110 kayıtlı outer-model/fold OOF/fit/scaler/target/train-query/hash denetimi geçti. Yeni dış ilaç için uçtan uca adapter yok: BLOCKED; retrospektif OOF karşılaştırması yalnız tasarım. Yeni tahmin/eğitim/API/OCR0. Önceki537 seçilmiş dosya ve denetlenen kaynak hash'leri aynı. İnsan PENDING, modeller ve bütçe18HTTP/6inference/.138USD rezerv değişmedi. Rapor reports/WP13_v1_2.md, fizibilite reports/BLIND_EXTERNAL_VALIDATION_FEASIBILITY_v1.md, çalıştırılmış notebook notebooks/WP13_demo_v1_2.ipynb. Gerçek browser QA8504; launcher scripts/WP13_StartDemo_v1_2.ps1 varsayılan8501 (port doluysa ayrı boş port seçilir). Kullanıcı değerlendirmesi bekleniyor; yeni dış antibiyotik denemesi başlamadı.

---
Önceki durum (tam baytları korunmuş):

'''
(ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
assert (ROOT/'run_status.md').read_bytes().endswith(before)
result={'prior_public_files_verified':len(protected),'blind_source_hashes_verified':len(pins),
 'tests_new':18,'tests_v1_1_regression':20,'tests_total':38,'tests_PASS':38,
 'outer_model_fold_groups':len(read(Q/'blind_audit.json')['fold_checks']),
 'notebook_code_cells_executed':len(code),'new_API_requests':0,'new_predictions':0,'new_training':0,
 'human_QA':'PENDING_UNCHANGED','external_inference':'BLOCKED_NO_APPROVED_EXTERNAL_INPUT_ADAPTER',
 'run_status_history_exact_suffix':True,'private_files_read_or_hashed':False,
 'PS_syntax_record':'launcher_syntax.json','preservation_scope':'Explicit previous-public manifest and audited source pins, not whole filesystem'}
write(Q/'final_verification.json',result)
files=['apps/drug_safety_explorer_v1_2.py','scripts/wp13_presentation_v1_2.py','scripts/wp13_blind_audit_v1.py',
 'scripts/wp13_v1_2_deliverables.py','scripts/wp13_v1_2_finalize.py','scripts/WP13_StartDemo_v1_2.ps1',
 'tests/test_wp13_v1_2.py','docs/plan/WP13_PRESENTATION_CONTRACT_v1_2.md',
 'reports/WP13_v1_2.md','reports/BLIND_EXTERNAL_VALIDATION_FEASIBILITY_v1.md','notebooks/WP13_demo_v1_2.ipynb','run_status.md']
files.extend(p.relative_to(ROOT).as_posix() for p in Q.iterdir() if p.is_file())
files.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'reports/figures/WP13/v1_2').iterdir() if p.is_file())
write(Q/'evidence_manifest.json',{n:public_sha(ROOT/n) for n in sorted(set(files))})
print(json.dumps(result,ensure_ascii=False))
