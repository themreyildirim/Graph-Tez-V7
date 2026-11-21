"""Read-only recorded outputs adapter. No training, prediction, API or clinical mapping."""
import json,math
from pathlib import Path
import pandas as pd
import wp13_tr_sources_v1 as tr
from wp12_api_security import public_sha
ROOT=tr.ROOT;Q=ROOT/'reports/qa/WP13/final_demo_v1'
PARENTS=['DB00199','DB00254']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def source_view(c):
    return {'term':c['source_term'],'page':c['source']['physical_page'],'start':c['term_start'],'end':c['term_end'],
      'full_section':c['source']['quote_exact'],'frequency':c['frequency_exact'],'scope':c['scope'],'note':c['source_note']}
def upload(data,name):
    d=tr.core.extract_pdf(data);d['display_name']=Path(name).name[:100]
    for i,h in enumerate(tr.EXPECTED):
        if d['sha256']==h:return {'status':'KNOWN_TR_HASH','index':i,'document':tr.load(i)}
    text=' '.join(p['text'] for p in d['pages'])
    headings=[h for h in ['KULLANMA TALİMATI','KISA ÜRÜN BİLGİSİ','Package leaflet','ADVERSE REACTIONS','Possible side effects'] if h.casefold() in text.casefold()]
    return {'status':'UNVERIFIED','index':None,'document':d,'headings':headings,'windows':tr.core.candidates(d),'GNN':'NOT_SUPPORTED','OCR':'OCR_NOT_AVAILABLE'}
def recorded(parent):
    if parent not in PARENTS:raise ValueError('NOT_SUPPORTED')
    pins=read(Q/'data_pins.json')
    for name,h in pins.items():
        if public_sha(ROOT/name)!=h:raise ValueError('RECORD_INTEGRITY')
    return read(Q/(parent+'.json'))
def attribution(bundle,pt):
    if pt not in {r['class_id'] for r in bundle['predictions']}:return {'status':'NOT_AVAILABLE','graph':[],'SHAP_B1':[]}
    return {'status':'RECORDED_ONLY','graph':[r for r in bundle['graph'] if r['class_id']==pt],
      'SHAP_B1':[r for r in bundle['shap'] if r['class_id']==pt]}
def comparison(doc):
    return [{'candidate_id':c['candidate_id'],'Türkçe kaynak terimi':c['name_tr'],'Sayfa':c['source']['physical_page'],
      'Kapsam':c['scope'],'PT eşlemesi':'UNMAPPED','İnsan kararı':'PENDING'} for c in doc['candidates']]
def prepare():
    Q.mkdir(parents=True,exist_ok=False)
    prior=read(ROOT/'reports/qa/WP13/tr_source_v1/prior_public_files.json')
    prior.update(read(ROOT/'reports/qa/WP13/tr_source_v1/evidence_manifest.json'));prior.pop('run_status.md',None)
    prior.update(read(ROOT/'reports/qa/WP13/v1_2/blind_source_pins.json'))
    prior['reports/qa/WP13/tr_source_v1/evidence_manifest.json']=public_sha(ROOT/'reports/qa/WP13/tr_source_v1/evidence_manifest.json')
    for n,h in prior.items():assert public_sha(ROOT/n)==h,n
    (Q/'prior_pins.json').write_text(json.dumps(prior,indent=2),encoding='utf-8')
    (Q/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
    pins={}
    def checked(rel,manifest):
        h=public_sha(ROOT/rel);assert h==manifest[rel],rel;pins[rel]=h;return ROOT/rel
    gbase='reports/qa/WP11/graph_v1/';sbase='reports/qa/WP11/B1_SHAP_v1/'
    gm=read(ROOT/(gbase+'final_artifact_manifest.json'));sm=read(ROOT/(sbase+'final_artifact_manifest.json'))
    graph=pd.read_csv(checked(gbase+'example_contributions.csv',gm));original=pd.read_csv(checked(gbase+'original_outputs.csv',gm))
    shap=pd.read_csv(checked(sbase+'example_local_shap.csv',sm));spairs=pd.read_csv(checked(sbase+'local_pair_outputs.csv',sm))
    oofpath='reports/qa/WP10/training_v1/oof_predictions.csv';assert public_sha(ROOT/oofpath)==prior[oofpath];pins[oofpath]=prior[oofpath]
    frames=[]
    for part in pd.read_csv(ROOT/oofpath,chunksize=20000):frames.append(part[(part.protocol=='primary')&(part.model=='A1P1')&part.drug_id.isin(PARENTS)])
    oof=pd.concat(frames)
    for i,parent in enumerate(PARENTS):
        # Original adapter verifies actual own-fold model JSON/NPZ and frozen term dictionary.
        import wp13_presentation_v1_2 as old
        saved=old.gnn_named(tr.core.verified_document(['pil.502.pdf','050641Orig1s032lbl.pdf'][i]))
        predictions=saved['rows'];fold=saved['fold'];target={r['class_id']:r for r in predictions}
        assert fold==[3,1][i]
        for prefix,manifest in [(gbase,gm),(sbase,sm)]:
            inp=read(ROOT/(prefix+'input_manifest.json'))
            for rel,h in inp.items():
                if '/primary_o%02d_final'%fold in rel and ('models/' in rel):assert public_sha(ROOT/rel)==h;pins[rel]=h
        gg=graph[(graph.protocol=='primary')&(graph.drug_id==parent)&(graph.outer_fold==fold)].copy()
        ss=shap[(shap.protocol=='primary')&(shap.drug_id==parent)&(shap.outer_fold==fold)].copy()
        for pt in set(gg.class_id):
            baseline=original[(original.protocol=='primary')&(original.drug_id==parent)&(original.class_id==pt)]
            assert len(baseline)==1
            z=float(baseline.original_logit.iloc[0]);assert abs(1/(1+math.exp(-z))-target[pt]['score_observed_record_proxy'])<1e-6
            for r in gg[gg.class_id==pt].to_dict('records'):
                if r['status']=='OK':assert abs(r['original_logit']-r['intervened_logit']-r['delta_z'])<1e-6
        for pt in set(ss.class_id):
            p=spairs[(spairs.protocol=='primary')&(spairs.drug_id==parent)&(spairs.class_id==pt)]
            assert len(p)==1 and abs(float(p['base'].iloc[0])+float(ss[ss.class_id==pt].SHAP_logit.sum())-float(p.logit.iloc[0]))<1e-8
        bundle={'parent':parent,'fold':fold,'model':'A1P1','version':saved['model_version'],'predictions':predictions,
          'graph':json.loads(gg.to_json(orient='records')),'shap':json.loads(ss.to_json(orient='records')),
          'shap_outputs':json.loads(spairs[(spairs.protocol=='primary')&(spairs.drug_id==parent)&(spairs.outer_fold==fold)].to_json(orient='records')),
          'scope':'own-fold primary OOF; NOT commercial product equivalence; no new inference'}
        (Q/(parent+'.json')).write_text(json.dumps(bundle,ensure_ascii=False,indent=2),encoding='utf-8')
        pd.DataFrame(predictions).to_csv(Q/(parent+'_ranked_OOF.csv'),index=False,encoding='utf-8-sig')
        pd.DataFrame(comparison(tr.load(i))).to_csv(Q/(parent+'_reference_UNMAPPED.csv'),index=False,encoding='utf-8-sig')
        pins[(Q/(parent+'.json')).relative_to(ROOT).as_posix()]=public_sha(Q/(parent+'.json'))
    (Q/'data_pins.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
if __name__=='__main__':prepare()
