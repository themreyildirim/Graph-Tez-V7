"""Deterministic Turkish descriptions of EXISTING attributions. No fitting or forward."""
import math,json
import pandas as pd
import wp13_final_data_v1 as old
from wp12_api_security import public_sha
ROOT=old.ROOT;Q=ROOT/'reports/qa/WP13/final_demo_v2'
FEATURES={'chem__MW':'Molekül ağırlığı','chem__LogP':'LogP','chem__HBD':'Hidrojen bağı verici sayısı','chem__HBA':'Hidrojen bağı alıcı sayısı','chem__TPSA':'Topolojik polar yüzey alanı'}
TR_PT={'C0000731':'Karında şişkinlik','C0000737':'Karın ağrısı'}
def number(x):return repr(float(x))
def shap_sentence(r):
    v=float(r['SHAP_logit']);name=FEATURES.get(r['feature'],r['feature'])
    kind='Eksiklik/modalite maskesi' if r['feature_type']!='chemistry' else 'Kimyasal özellik'
    direction='artırıcı' if v>0 else 'azaltıcı' if v<0 else 'sıfır katkı'
    return f"B1 — {kind}: {name}. SHAP logit katkısı {number(v)}; eğitim background'una göre model logiti için {direction} yöndedir. Klinik görülme olasılığı değildir."
def delta_sentence(r):
    method='Sabit derece/rol paydalı mesaj maskesi' if r['mode']=='fixed' else 'Fiziksel silme ve yeniden normalizasyon'
    if r['status']!='OK' or pd.isna(r['delta_z']):return method+': NA — uygulanabilir yol/sonuç yok; sıfır etki olarak yorumlanamaz.'
    v=float(r['delta_z']);effect='azaldı' if v>0 else 'arttı' if v<0 else 'değişmedi'
    return f"A1P1 — {method}. Δz=orijinal−müdahale={number(v)}; müdahaleden sonra logit {effect}. Bu tekil model duyarlılığıdır; biyolojik nedensellik veya advers reaksiyon mekanizması değildir."
def guard(rows,parent,pt,fold,kind):
    for r in rows:
        if r['drug_id']!=parent or r['class_id']!=pt or int(r['outer_fold'])!=fold or r['protocol']!='primary':raise ValueError('EXPLANATION_ID_MISMATCH')
        if kind not in ['B1','A1P1']:raise ValueError('MODEL_MISMATCH')
        if kind=='B1' and 'SHAP_logit' not in r:raise ValueError('MODEL_MISMATCH')
        if kind=='A1P1' and 'delta_z' not in r:raise ValueError('MODEL_MISMATCH')
    return rows
def available(parent):return json.loads((Q/(parent+'_index.json')).read_text(encoding='utf-8'))
def get(parent,pt,fold):
    if parent not in old.PARENTS:raise ValueError('NOT_SUPPORTED')
    bundle=old.recorded(parent)
    if fold!=bundle['fold'] or pt not in {r['class_id'] for r in bundle['predictions']}:raise ValueError('EXPLANATION_ID_MISMATCH')
    rows={}
    for name,kind in [('shap','B1'),('graph','A1P1')]:
        p=Q/(parent+'_'+name+'.csv.gz');pins=json.loads((Q/'explanation_pins.json').read_text())
        if public_sha(p)!=pins[p.name]:raise ValueError('EXPLANATION_HASH_MISMATCH')
        df=pd.read_csv(p);selected=df[df.class_id.eq(pt)].where(pd.notna(df),None).to_dict('records')
        rows[name]=guard(selected,parent,pt,fold,kind)
    rel='reports/qa/WP11/graph_v1/absent_paths_NA.csv'
    manifest=old.read(ROOT/'reports/qa/WP11/graph_v1/final_artifact_manifest.json')
    if public_sha(ROOT/rel)!=manifest[rel]:raise ValueError('EXPLANATION_HASH_MISMATCH')
    absent=pd.read_csv(ROOT/rel)
    rows['absent_paths']=absent[absent.context.eq(f'primary_o{fold:02d}_final')&absent.drug_id.eq(parent)].to_dict('records')
    return rows
