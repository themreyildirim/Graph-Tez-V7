"""Pilotun ham kaynak/alıntı/test bütünlüğünü mühürler;LLM veyaeğitim yok."""
import csv,json
import nbformat
from wp12_pilot import ROOT,QA,SOURCE,FILES,read,preserve
from wp12_prepare import save,sha
from wp12_document_contract import validate_bundle


def verify_only():
    m=read(QA/'evidence_manifest.json');assert all(sha(ROOT/p)==h for p,h in m.items())
    assert sha(QA/'evidence_manifest.json')==(QA/'evidence_manifest.sha256').read_text().split()[0]
    return {'evidence_entries_verified':len(m),'protected_prior_files_and_selected_PDFs':preserve()}


def main():
    if (QA/'artifact_validation.json').exists():raise RuntimeError('Pilot v1 already finalized')
    previous=preserve();assert previous==3208
    bundle=read(QA/'source_evidence_bundle.json');summary=validate_bundle(bundle);assert summary=={'documents':2,'extraction_runs':2,'pages':17,'quotes':44,'data_status':'user_pdf_records'}
    for d in bundle['documents']:
        path=SOURCE/d['receipts'][0]['original_filename'];assert path.is_file() and sha(path)==d['raw_sha256'] and path.stat().st_size==d['raw_size_bytes']
    q={q['quote_id']:q for q in bundle['quotes']};annotations=read(QA/'source_context_annotations.json');assert len(annotations)==len(q)
    assert all(not a['is_model_input'] and not a['is_training_label'] and all(i in q for i in a['context_quote_ids']) for a in annotations)
    with (QA/'source_quotes.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==44
    for row in rows:
        original=q[row['quote_id']];assert row['quote']==original['quote'] and int(row['char_start'])==original['char_start'] and int(row['char_end'])==original['char_end'] and int(row['page_number'])==original['page_number']
    for p,h in read(QA/'identity_input_manifest.json').items():assert sha(ROOT/p)==h
    tests=(QA/'pilot_tests_v1.txt').read_text(encoding='utf-8');assert 'Ran 18 tests' in tests and tests.rstrip().endswith('OK') and tests.count('... ok')==18
    meta=read(QA/'document_metadata_content_review.json');assert [r['content_revision'] for r in meta]==['December 2025','02/2022'] and not any(r['latest_label_verified'] for r in meta)
    identity=read(QA/'drug_identity_review.json');assert [i['DrugBank_parent_id'] for i in identity]==['DB00199','DB00254'] and identity[1]['existing_salt_link_id']=='DBSALT001956'
    nbpath=ROOT/'notebooks/WP12_user_pdf_pilot.ipynb';nb=nbformat.read(nbpath,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs];assert len(code)==7 and all(c.execution_count for c in code) and not any(o.output_type=='error' for o in outputs)
    images=sum('image/png' in o.get('data',{}) for o in outputs);assert images==8
    fig=ROOT/'reports/figures/WP12/pilot_v1';source_images=list((fig/'pages').rglob('page-*.png'));assert len(source_images)==17
    assert all(p.stat().st_size>10000 for p in source_images)
    log=read(QA/'runtime_provenance.json');assert not log['LLM_models_downloaded'] and not log['OCR_or_layout_inference_executed'] and not log['pymupdf4llm_used'];assert log['bundled_OCR_layout_ONNX_resources_installed']
    # Eski hazırlık manifesti yalnız mutable status için o aşamanın arşivini kullanır.
    old=read(ROOT/'reports/qa/WP12/preparation_v1/evidence_manifest.json')
    assert all(sha(QA/'run_status_before.md' if p=='run_status.md' else ROOT/p)==h for p,h in old.items())
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    prefix='''# WP12 gerçek kullanıcı PDF pilotu — inceleme bekleniyor · 08.11.2026

Kullanıcı iki yerel dosyayı açıkça seçti:pil.502.pdf ve050641Orig1s032lbl.pdf,data/user_pdfs. İkisi gerçekten bulundu;alternatif PDF aranmadı/indirilmedi. Ham dosyalar salt okunur kaldı;SHA-256 önce/sonra aynı.

- Erythromycin6+Doxycycline11=17 fiziksel sayfa PyMuPDF2.1 ile metin katmanından çıkarıldı. Boşmetin0;hiçbir sayfa atlanmadı. Doxycycline10 görsel ambalaj ve154 karakterfooter;OCR yok.11 imza temsilidir;ana9 sayfalık basılı numara ile fiziksel11 sayfa ayrı tutulur.
- 44 birebir quote sayfa/[start,end)/hash ile saklandı. Erythromycin4–5,Doxycycline7 veuyarı4–6 kaynakları incelendi. 18 gerçek test geçti;tüm17 sayfa ağ vealt süreç kapalı tekrar çıkarımda aynımetni verdi.
- Doxycycline sınıf listesi,direct-drug ifade,including-doxycycline uyarısı,diğer named tetracycline vehayvan/related-agent bağlamları ayrıldı. BUN istisnası iki cümlesiyle korundu;pozitif veya kesinnegatif etiket üretilmedi. Bunlar kullanıcı incelemesini bekleyen pilot source-context anotasyonlarıdır,klinik gold-standard değildir.
- DB00199/CID12560 veDB00254/CID54671203 parent düzeyinde mevcut kaynakla desteklendi. Monohydrate DBSALT001956→DB00254 mevcutilişkidir;ürün/doz/tuz/hydrate eşdeğerliği varsayılmadı. PDF bilgisi eski özellik veyaSIDER etiketine aktarılmadı.
- Rapor:reports/WP12_PDF_PILOT.md;notebook:notebooks/WP12_user_pdf_pilot.ipynb (7çalıştırılmışhücre). JSON:reports/qa/WP12/pilot_v1/source_evidence_bundle.json;sourcepagegörselleri:reports/figures/WP12/pilot_v1/pages/.
- PyMuPDF projeiçi izolekuruldu. Pip'in getirdiği pasifOCR/layoutONNX kaynakları runtime_provenance.json içinde açık kayıttadır;OCR/layout inference yapılmadı. Ollama/LLM modeli indirilmedi/çalıştırılmadı;yeni eğitim yok.
- Önceki3208 dosya (seçilenikiPDF dahil) hashile korundu. WP00–WP11 modelleri/sonuçları/QA veWP12 hazırlıkv1 sözleşmesi değişmedi. Önceki run_status tam baytları aşağıda veQA arşivinde korundu.

**DURUM:GerçekPDF çıkarımı vekaynak doğrulama pilotu tamamlandı. Kullanıcı incelemesi beklenir;LLM veya sonraki uygulamaya geçilmez.**

---

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    result={'date':'2026-11-08','status':'PDF_PILOT_PASS_PENDING_USER_REVIEW','user_supplied_documents':2,'physical_pages':17,'page_counts':[6,11],'source_quotes':44,'source_quotes_CSV_JSON_exact_match':True,'pilot_tests_passed':18,'raw_PDF_hashes_unchanged':True,'old_artifacts_and_selected_PDFs_preserved':preserve(),'independent_Poppler_page_count_agreement':True,'text_reextraction_offline_exact':True,'OCR_executed':False,'image_substantive_page_without_OCR':'Doxycycline physical10 preserved as raster+footer text','class_vs_direct_scope_review':'PILOT_NOT_CLINICAL_GOLD_STANDARD','DB00199_DB00254_parent_mapping_supported':True,'monohydrate_existing_salt_link':'DBSALT001956','product_or_dose_equivalence_claim':False,'new_SIDER_labels_or_model_inputs':0,'new_training':False,'Ollama_or_LLM_model_download_or_execution':False,'software_bundled_OCR_layout_resources_installed_but_unused':True,'executed_notebook_cells':7,'embedded_images':images,'rendered_physical_pages':17,'visually_reviewed_full_pages':[ 'E1','E4','E5','E6','D1','D4','D5','D6','D7','D9','D10'],'all17_pages_contact_sheet_reviewed':True,'publisher_authenticity_or_latest_version_verified':False,'previous_run_status_bytes_retained':True,'stop':'WAIT_FOR_USER_REVIEW'}
    save(QA/'artifact_validation.json',result)
    files=[p for p in QA.rglob('*') if p.is_file() and p.name not in ['evidence_manifest.json','evidence_manifest.sha256']]
    files+=list(fig.rglob('*.png'))+list((ROOT/'scripts').glob('wp12_pilot*.py'))
    files+=[ROOT/'tests/test_wp12_pilot.py',ROOT/'reports/WP12_PDF_PILOT.md',nbpath,ROOT/'run_status.md']+[SOURCE/name for name in FILES]
    save(QA/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files))})
    (QA/'evidence_manifest.sha256').write_text(sha(QA/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print(json.dumps(result,ensure_ascii=False,indent=2));print(verify_only())


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    if a.verify_only:print(verify_only())
    else:main()
