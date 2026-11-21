"""Yeni kapanış kanıtını mühürler;eski manifest veya sonuçlara yazmaz."""
import argparse,json,re
import nbformat
import numpy as np
import pandas as pd
from wp11_close_audit import ROOT,C,G,B,read,csv,preserve
from wp11_linear_shap import sha,write_json


def verify_only():
    m=read(C/'evidence_manifest.json');bad=[p for p,h in m.items() if sha(ROOT/p)!=h];assert not bad,bad
    expected=(C/'evidence_manifest.sha256').read_text().split()[0];assert expected==sha(C/'evidence_manifest.json')
    return {'evidence_files_verified':len(m),'preserved_accepted_files':preserve(),'manifest_sha256':expected}


def main():
    if (C/'closure_checks.json').exists():raise RuntimeError('WP11 final closure v1 already sealed')
    prior=preserve();assert prior==3139
    for filename in ['replay_complete.json','table_audit_complete.json']:assert read(C/filename)['status']=='PASS'
    manifests=pd.read_csv(C/'manifest_checks.csv');assert len(manifests)==8 and manifests.status.eq('PASS').all()
    models=pd.read_csv(C/'model_integrity_all742.csv');assert len(models)==742 and models.status.eq('PASS').all()
    tests=pd.read_csv(C/'tests_rerun_summary.csv');assert tests.passed.sum()==44
    for name,n in [('synthetic_tests_before_real.txt',10),('real_tests_v1.txt',16)]:
        text=(G/name).read_text(encoding='utf-8');assert f'Ran {n} tests' in text and text.rstrip().endswith('OK')
    for r in tests.itertuples():
        p=C/(r.module+'_closure_rerun.txt');assert sha(p)==r.log_sha256 and f'Ran {r.passed} tests' in p.read_text() and p.read_text().rstrip().endswith('OK')
    stream=pd.read_csv(C/'contribution_stream_checks.csv');assert stream.rows.sum()==2440976
    assert stream[stream.kind.eq('ppi')].exact_zero.iloc[0]==48 and stream[stream.kind.eq('ppi')].near_zero_including_exact.iloc[0]==56
    assert stream.NA_measurement_rows.sum()==0 and stream.all_source_keys_valid.all()
    keys=pd.read_csv(C/'all_intervention_key_checks.csv');assert len(keys)==8358 and keys.unique_complete_CUI_dictionary.all()
    images=pd.read_csv(C/'image_data_checks.csv');assert len(images)==6 and images.differing_pixels.eq(0).all() and images.embedded_differing_pixels.eq(0).all()
    # Node color/NA rendering flags independently resolve to actual query/train IDs.
    names=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['id','name']).drop_duplicates().set_index('id')['name'].to_dict();nodechecks=[]
    for network in read(G/'real_networks.json'):
        context=network['context']
        with np.load(ROOT/f'reports/qa/WP09/design_v1/folds/{context}_train.npz',allow_pickle=False) as a:train_ids=list(a['protein_ids'])
        with np.load(ROOT/f'reports/qa/WP09/design_v1/folds/{context}_query.npz',allow_pickle=False) as a:
            d=list(a['drug_ids']).index(network['drug_id']);pool=train_ids+list(a['unseen_protein_ids']);role_set={pool[int(p)] for role in ['target','enzyme','transporter','carrier'] for p in a['role_'+role][1,a['role_'+role][0]==d]}
        assert network['drug_name']==names[network['drug_id']]
        for node in network['nodes']:
            assert node['query_role_protein']==(node['id'] in role_set) and node['train_pool']==(node['id'] in train_ids)
        nodechecks.append({'context':context,'drug_id':network['drug_id'],'protein_nodes':len(network['nodes']),'drug_name_source_aligned':True,'query_role_train_pool_flags_source_aligned':True})
    csv('network_node_flags_check.csv',nodechecks)
    nb=nbformat.read(ROOT/'notebooks/WP11_final_closure.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs];assert len(code)==6 and all(c.execution_count for c in code) and not any(o.output_type=='error' for o in outputs)
    assert sum('image/png' in o.get('data',{}) for o in outputs)==6
    perf=pd.read_csv(C/'accepted_performance_unchanged.csv')
    assert len(perf)==7 and not perf.recomputed.any()
    for r in perf.itertuples():assert sha(ROOT/r.source_CSV)==r.source_sha256
    metadata=read(ROOT/'reports/qa/WP10/training_v1/training_complete.json');assert (metadata['source_drugs'],metadata['source_PT'],metadata['source_positives'])==(62,1061,6416)
    assert (ROOT/'reports/WP11_FINAL_CLOSURE.md').is_file() and (ROOT/'reports/WP12_PREPARATION_DECISION.md').is_file()
    history=(C/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==history
    prefix='''# WP11 nihai kapanışı — PASS · 08.11.2026

Kullanıcı B1 SHAP ve A1P1 protein/PPI açıklamalarını araştırma kapsamında kabul etti. Nihai kapanış denetimi tamamlandı;sonuçlar değişmedi.

- Önceki3139 kabul edilmişdosya ve8 manifest doğrulandı.742 NPZ+742 metadata (WP08:400,WP09:190,WP10:152) eşleşti;B1 SHAP,graf QA,split/QC veönceki performanslar korundu.
- 26 graf testi yeni kapanış loglarında tekrar geçti;B1'in18 testi de geçti:44/44. Eğitim/optimizer/backward çağrısı0. Eski test logları ezilmedi.
- Tam557574 rol+1883402 PPI satırı ve8358 müdahale anahtarı source drug/protein/kenar,fold PT,orijinal logit,Δz cebiri veözetle doğrulandı. Eksik yollarNA;48 gerçek sıfır PPI katkısı korundu.
- 10 A1P1 dış modelinin35974 orijinal logiti veönceden kimlik sırasıyla seçilmiş100 mevcut müdahalenin29560 PT kaydı yeniden doğrulandı. Bu yeni attribution yöntemi/sonuç seçimi değildir;tamCSV forward'ı yeniden çalıştırıldı iddiası yoktur.
- Altı grafPNG ve notebook'taki altı gömülü görsel,eski veri/çizim kodu yeni QA konumuna yönlendirilerek piksel düzeyinde eşleşti. Eski grafik/notebook'a yazılmadı.
- B1 exact linear SHAP ile tekil graf mesaj maskeleme/silme Δz duyarlılığı ayrı yöntemlerdir. Unknown gerçek negatif değildir;hiçbiri klinik risk veya biyolojik nedensellik kanıtı değildir. WP09/WP10'un PPI ek başarı gösterilememesi veWP10 küçük/koşullu atom katkısı yorumu aynen korundu.
- Kapanış:`reports/WP11_FINAL_CLOSURE.md`;kanıt:`reports/qa/WP11/final_closure_v1/evidence_manifest.json`;çalıştırılmışnotebook:`notebooks/WP11_final_closure.ipynb`.
- WP12 yalnız aktif ROADMAP kapsamıyla incelendi:`reports/WP12_PREPARATION_DECISION.md`. PDF okunmadı/indirilmedi;Ollama/LLM kurulumu veya model indirmesi yapılmadı;WP12 kodu/uygulaması başlamadı.

**DURUM: WP11 nihai olarak kapandı. WP12 yalnız hazırlık/karar notu;uygulama için kullanıcı onayı beklenerek duruldu.**

Önceki run_status tam baytları aşağıda ve kapanış QA arşivinde aynen korunur.

---

'''
    (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+history)
    replay=read(C/'replay_complete.json');na=pd.read_csv(C/'NA_source_consistency.csv')
    result={'date':'2026-11-08','status':'PASS','WP11':'CLOSED_ACCEPTED_BY_USER','WP12':'PREPARATION_ONLY_NOT_STARTED','previous_accepted_files_unchanged':preserve(),'old_manifest_files_verified':8,'NPZ_model_files_verified':742,'metadata_files_verified':742,'graph_tests_rerun_passed':26,'B1_tests_rerun_passed':18,'graph_rows_stream_checked':2440976,'unique_native_PT_complete_interventions':8358,'old_original_logit_rows_replayed':35974,'old_interventions_replayed':100,'old_intervention_PT_rows_replayed':29560,'max_existing_replay_error':replay['max_replay_logit_delta_error'],'full_CSV_summary_max_error':keys.summary_max_error.max(),'source_missing_path_NA_rows':int(na.absent_role_PPI_rows.iloc[0]),'source_protein_path_rows':int(na.protein_path_rows.iloc[0]),'exact_zero_PPI_rows_preserved':48,'near_zero_including_exact_PPI_rows_preserved':56,'PNG_verified_against_data_and_pixels':6,'notebook_embedded_images_pixel_equal':6,'closure_notebook_executed_cells':6,'old_outputs_rewritten':False,'new_training_optimizer_backward_calls':0,'new_attribution_method':False,'old_WP09_WP10_performance_unchanged':True,'raw_XML_STRING_rescanned':False,'PDF_or_Ollama_implementation_started':False,'run_status_history_retained':True}
    write_json(C/'closure_checks.json',result)
    files=[p for p in C.rglob('*') if p.is_file() and p.name not in ['evidence_manifest.json','evidence_manifest.sha256']]
    files+=list((ROOT/'scripts').glob('wp11_close*.py'))
    files+=[ROOT/'reports/WP11_FINAL_CLOSURE.md',ROOT/'reports/WP12_PREPARATION_DECISION.md',ROOT/'notebooks/WP11_final_closure.ipynb',ROOT/'run_status.md']
    write_json(C/'evidence_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)})
    (C/'evidence_manifest.sha256').write_text(sha(C/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='ascii')
    print(json.dumps(result,ensure_ascii=False,indent=2));print(verify_only())


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    if a.verify_only:print(verify_only())
    else:main()
