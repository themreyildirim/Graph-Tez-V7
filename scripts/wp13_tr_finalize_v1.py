"""Finalize explicit public evidence only; preserve prior bytes. No model/API execution."""
from pathlib import Path
import json,ast
from wp12_api_security import public_sha
from wp13_tr_sources_v1 import load,validate,FILES,EXPECTED
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/tr_source_v1';F=ROOT/'reports/figures/WP13/tr_source_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,data):
    with (Q/name).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
prior=read(Q/'prior_public_files.json')
old_sources=read(ROOT/'reports/qa/WP13/v1_2/blind_source_pins.json')
for collection in [prior,old_sources]:
    for name,h in collection.items():
        if public_sha(ROOT/name)!=h:raise ValueError('PRESERVATION_FAILED: '+name)
docs=[load(i) for i in range(2)]
for i,d in enumerate(docs):
    assert validate(d)
    assert public_sha(ROOT/'data/user_pdfs'/FILES[i])==EXPECTED[i]
for name,n in [('tests_duplicate_label_fix.log',21),('v1_1_regression.log',20),('v1_2_regression.log',18)]:
    text=(Q/name).read_text(encoding='utf-8-sig');assert f'Ran {n} tests' in text and text.rstrip().endswith('OK')
nb=read(ROOT/'notebooks/WP13_Turkish_source_pilot_v1.ipynb');cells=[c for c in nb['cells'] if c['cell_type']=='code']
assert len(cells)==4 and all(c['execution_count'] for c in cells)
assert not any(o['output_type']=='error' for c in cells for o in c['outputs'])
for p in ['scripts/wp13_tr_sources_v1.py','scripts/wp13_tr_deliverables_v1.py','apps/drug_safety_explorer_TR_v1.py','tests/test_wp13_tr_source_v1.py']:
    ast.parse((ROOT/p).read_text(encoding='utf-8'))
assert read(Q/'launcher_syntax.json')['syntax_errors']==0
write('browser_checks.json',{'url':'http://127.0.0.1:8506','real_browser':True,'TR_active_sources_only':'PASS',
 'ERITRO_25_and_source':'PASS','MONODOKS_48_47':'PASS','BUN_4_8_and_accumulation_4_2_separate':'PASS',
 'table_selection_ID_alignment':'PASS','duplicate_label_initial_failure':'OBSERVED_AND_PRESERVED',
 'duplicate_label_fix_then_rerun_same_page9_ID':'PASS','currentness_notice':'PASS','new_TR_LLM':'NOT_AVAILABLE',
 'existing_OOF_parent_record_read_only':'DB00254_A1P1_primary_outer1_240PT',
 'new_inference':False,'human_clinical_QA':'PENDING','screenshots_01_to06':'PRE_LABEL_FIX_ACTUAL_UI','screenshots_08_and_later':'FINAL_ACTUAL_UI'})
write('technical_issues.json',{'console':'Initial CP1254 output failed; UTF8 saved extraction intact; UTF8 read verified',
 'server':'Initial sandbox server not reachable from real browser; approved user-session localhost server used; no security settings changed',
 'duplicate_selection':'Two identical display labels could switch glossit9 to glossit10 on rerun. Distinct page/ID labels fixed; final21 tests PASS and real rerun preserved page9 ID.',
 'earlier_evidence':'Initial logs, traces and screenshots kept; not reclassified as final proof'})
before=(Q/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==before
prefix='''# WP13 Türkçe kaynak pilotu v1 ·09.11.2026

İki yeni kullanıcı PDF'si bağımsız TR_SOURCE_v1 sözleşmesiyle eklendi: ERİTRO500mg eritromisin stearat KT8sayfa; MONODOKS100mg doksisiklin hiklat KÜB13sayfa.21 fiziksel sayfa, ham SHA ve Unicode alıntı/terim aralıkları doğrulandı. Güncellik UNVERIFIED_CURRENTNESS; İngilizce ürün/tuz/doz eşdeğerliği yok. ERİTRO25 aday madde satırı/25terim; MONODOKS48kayıt/47terim (glossit2bölüm). Klinik doğrulanmış sayı değil; insanPENDING, MedDRAUNMAPPED. BUN artışı4.8 ile birikim yokluğu4.2 ayrı; aşırı doz/hayvan bağlamları normal tabloya katılmadı. Yeni Türkçe quote-ID için kayıtlı LLM NOT_AVAILABLE; yeniAPI/eğitim/model inference/OCR0.21yeni +38regresyon test PASS. Çift glossit seçim sorunu gözlendi ve sayfa/kısaID etiketiyle düzeltildi; ilk kanıtlar korundu.583önceki seçilmiş dosya ve252önceki model/split/OOF kaynak pini aynı. Ayrı read-only GNN paneli ürün tahmini değil, ana etkin madde kendi-foldOOF kaydı. Gerçek QA localhost8506; başlatıcı scripts/WP13_StartDemo_TR_v1.ps1 varsayılan8501, port doluysa boş port seçin. Rapor reports/WP13_TR_SOURCE_v1.md; çalıştırılmış notebook notebooks/WP13_Turkish_source_pilot_v1.ipynb; QA/figures WP13/tr_source_v1. İngilizce demolar ve tüm frozenWP12/önceki sonuç/PENDING/bütçe kayıtları korundu. Kullanıcı değerlendirmesi bekleniyor; dış antibiyotik denemesi başlatılmadı.

---
Önceki durum (tam baytları korunmuş):

'''
(ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
assert (ROOT/'run_status.md').read_bytes().endswith(before)
result={'previous_public_files_verified':len(prior),'previous_model_split_OOF_source_pins_verified':len(old_sources),
 'raw_new_PDF_hashes_verified':2,'physical_pages':sum(d['page_count'] for d in docs),
 'new_candidate_records':sum(len(d['candidates']) for d in docs),'new_tests_PASS':21,'old_regression_tests_PASS':38,
 'notebook_code_cells_executed':4,'new_API':0,'new_model_inference':0,'new_training':0,'OCR':False,
 'human_QA':'PENDING_UNCHANGED','currentness':'UNVERIFIED_CURRENTNESS','run_status_exact_history_suffix':True,
 'new_sources_separate_from_WP12':True,'private_files_read_or_hashed':False}
write('final_verification.json',result)
files=['scripts/wp13_tr_sources_v1.py','scripts/wp13_tr_deliverables_v1.py','scripts/wp13_tr_finalize_v1.py',
 'scripts/WP13_StartDemo_TR_v1.ps1','apps/drug_safety_explorer_TR_v1.py','tests/test_wp13_tr_source_v1.py',
 'docs/plan/WP13_TR_SOURCE_v1.md','reports/WP13_TR_SOURCE_v1.md','notebooks/WP13_Turkish_source_pilot_v1.ipynb','run_status.md']
files.extend('data/user_pdfs/'+f for f in FILES)
files.extend(p.relative_to(ROOT).as_posix() for directory in [Q,F] for p in directory.iterdir() if p.is_file())
write('evidence_manifest.json',{p:public_sha(ROOT/p) for p in sorted(set(files))})
print(json.dumps(result,ensure_ascii=False))
