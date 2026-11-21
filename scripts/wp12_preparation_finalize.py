"""WP12 hazırlığını belge bekleme durumunda doğrular;çıkarım başlatmaz."""
import ast,csv,json
import nbformat
from wp12_prepare import ROOT,QA,sha,save,preserve
from wp12_document_contract import schema,validate_bundle


def verify_only():
    m=json.loads((QA/'evidence_manifest.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p)==h for p,h in m.items())
    assert sha(QA/'evidence_manifest.json')==(QA/'evidence_manifest.sha256').read_text().split()[0]
    return {'evidence_entries_verified':len(m),'previous_files_unchanged':preserve(),'state':'AWAITING_USER_PDFS'}


def main():
    if (QA/'artifact_validation.json').exists():raise RuntimeError('Preparation v1 already finalized')
    old_count=preserve();assert old_count==3183
    exported=json.loads((ROOT/'docs/schemas/WP12_document_bundle_v1.schema.json').read_text(encoding='utf-8'));assert exported==schema()
    bundle=json.loads((QA/'empty_document_bundle.json').read_text(encoding='utf-8'));counts=validate_bundle(bundle)
    assert counts=={'documents':0,'extraction_runs':0,'pages':0,'quotes':0,'data_status':'awaiting_user_pdfs'}
    with (QA/'document_inventory.csv').open(encoding='utf-8-sig',newline='') as f:assert list(csv.DictReader(f))==[]
    assert not list(QA.rglob('*.pdf'))
    policy=json.loads((ROOT/'configs/WP12_preparation_v1.json').read_text());assert policy['state']=='AWAITING_USER_PDFS' and policy['source_policy']=='only_user_supplied_pdf_files'
    assert not any(policy[k] for k in ['automatic_discovery','network_download','extractor_implemented','Ollama_or_LLM_enabled','training_enabled','source_documents_writable','model_input_or_label_updates_allowed'])
    tree=ast.parse((ROOT/'scripts/wp12_document_contract.py').read_text(encoding='utf-8'))
    imports={alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names}
    assert imports=={'datetime','hashlib','json','re'} and not any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree))
    calls=[n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)];assert 'open' not in calls
    log=(QA/'contract_tests_v1.txt').read_text(encoding='utf-8');assert 'Ran 24 tests' in log and log.rstrip().endswith('OK') and log.count('... ok')==24
    nb=nbformat.read(ROOT/'notebooks/WP12_document_contract_preparation.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs];assert len(code)==5 and all(c.execution_count for c in code) and not any(o.output_type=='error' for o in outputs)
    assert sum('image/png' in o.get('data',{}) for o in outputs)==1
    image=ROOT/'reports/figures/WP12/preparation_v1/01_document_provenance_contract.png';assert image.stat().st_size>10000
    archive=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==archive
    prefix='''# WP12 veri sözleşmesi hazırlığı — BELGE BEKLENİYOR · 08.11.2026

Kullanıcı kaynak kararı:prospektüs PDF'lerini kullanıcı sağlayacak. Yalnız kullanıcı eki/açık kullanıcı dosyası kabul edilecek;otomatik arama/indirme yoktur.

- Sözleşme:`docs/plan/WP12_DOCUMENT_DATA_CONTRACT_v1.md`;makine şeması:`docs/schemas/WP12_document_bundle_v1.schema.json`;politika:`configs/WP12_preparation_v1.json`.
- document hamSHA-256 → extractor/run sürüm/seçenek → fiziksel sayfa/tammetin hash'i → [start,end) Unicode kod noktası/birebir alıntı zinciri tanımlandı. Basılı sayfa etiketi ayrı;sessiz metin normalizasyonu yok.
- SafJSON doğrulayıcı ve24 teknik birim testi geçti. Teknik kayıtlar gerçek prospektüs/PDF değildir;üretim envanterine alınmaz. Gerçekbelge/run/sayfa/alıntı0/0/0/0.
- Çalıştırılmış Türkçe notebook:`notebooks/WP12_document_contract_preparation.ipynb`;rapor:`reports/WP12.md`;QA:`reports/qa/WP12/preparation_v1/`. Görsel yalnız kavramsal sözleşmedir;gerçek çıkarım sonucu değildir.
- Gerçek PDF açılmadı/hash'lenmedi/çıkarılmadı. Parser bağlı değil;giriş dosya açmadan bekleme hatasıyla durur. Ollama/LLM kurulumu,model indirme veya eğitim yapılmadı.
- Önceki3183 kabul edilmiş dosya veWP11 kapanışının43 kanıt girdisi korundu. WP00–WP11 kaynak/model/sonuç/QA değişmedi. Bu başlık ilerleme kaydıdır;önceki tam baytlar aşağıda veQA arşivinde aynen tutulur.

**DURUM:WP12 yalnız veri sözleşmesi/ön hazırlık tamamlandı. AWAITING_USER_PDFS. Kullanıcı PDF'leri sağlayana kadar burada durulur.**

---

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+archive)
    # Önceki WP11 kanıtı değişmedi;status'un doğru tarihsel arşivi kullanılır.
    previous=json.loads((ROOT/'reports/qa/WP11/final_closure_v1/evidence_manifest.json').read_text(encoding='utf-8'))
    assert all(sha(QA/'run_status_before.md' if p=='run_status.md' else ROOT/p)==h for p,h in previous.items())
    result={'date':'2026-11-08','status':'PREPARATION_PASS_AWAITING_DOCUMENTS','state':'AWAITING_USER_PDFS','source_policy':'ONLY_USER_SUPPLIED_PDFS','previous_accepted_files_unchanged':preserve(),'previous_WP11_evidence_entries_unchanged':len(previous),'contract_tests_passed':24,'technical_fixtures_in_production':False,'real_documents':0,'real_extraction_runs':0,'real_pages':0,'real_quotes':0,'real_PDF_validation':'NOT_RUN_NO_USER_PDF','PDF_parser_implemented':False,'PDF_extraction_performed':False,'automatic_search_or_download':False,'Ollama_installation_or_model_download':False,'new_training':False,'new_libraries_installed':False,'executed_notebook_cells':5,'conceptual_schema_figures':1,'run_status_history_retained':True,'WP12_real_application_completed':False}
    save(QA/'artifact_validation.json',result)
    files=[p for p in QA.rglob('*') if p.is_file() and p.name not in ['evidence_manifest.json','evidence_manifest.sha256']]
    files+=list((ROOT/'scripts').glob('wp12_*.py'))+[ROOT/'tests/test_wp12_document_contract.py',ROOT/'docs/plan/WP12_DOCUMENT_DATA_CONTRACT_v1.md',ROOT/'docs/schemas/WP12_document_bundle_v1.schema.json',ROOT/'configs/WP12_preparation_v1.json',ROOT/'reports/WP12.md',ROOT/'notebooks/WP12_document_contract_preparation.ipynb',image,ROOT/'run_status.md']
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files))})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print(json.dumps(result,ensure_ascii=False,indent=2));print(verify_only())


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    if a.verify_only:print(verify_only())
    else:main()
