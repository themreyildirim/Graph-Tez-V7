"""Yerel kimyasal kayıtlar -> kaynak izi, QC, ham/temiz tanımlayıcılar."""
from pathlib import Path
import json
import sys
import hashlib
import platform
from collections import Counter
import pandas as pd
from wp04_chemistry import (parse_smiles,parse_inchi,identity,compare_keys,descriptors,
                            atom_bond_tables,FEATURES,rdBase,rdMolDescriptors)

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/qa/WP04'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def save(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def csv(name,rows):pd.DataFrame(rows).to_csv(OUT/name,index=False,encoding='utf-8-sig')


def property_values(record,kind):
    return [p['value'] for p in record['properties'] if p['kind']==kind and p['value']]


def unique_property(record,kind):
    v=set(property_values(record,kind));return next(iter(v)) if len(v)==1 else ''


def main():
    records=read('xml_chemical_records.json');cohort={r['id']:r for r in read('cohort_identity.json')}
    bridge=json.loads((ROOT/'reports/qa/WP02/bridge_qc.json').read_text(encoding='utf-8'))
    bridge={r['id']:r for r in bridge['rows']}
    legacy={r['DrugBank_ID']:r for r in read('legacy_chemistry_reference.json')['rows']}
    source=[];quality=[];raw=[];clean=[];comparison=[];props=[];molecules={}
    for r in records:
        c=cohort[r['id']];sm=unique_property(r,'SMILES');inc=unique_property(r,'InChI');key=unique_property(r,'InChIKey')
        mol,parse_status=parse_smiles(sm);imol,iparse=parse_inchi(inc)
        mid=identity(mol);iid=identity(imol)
        xml_cids=sorted({x['identifier'] for x in r['external_identifiers'] if x['resource']=='PubChem Compound'})
        cid_verified=xml_cids==[c['cid']]==[bridge[r['id']]['bridge_cid']]
        sm_key=compare_keys(mid.get('rdkit_inchikey',''),key)
        inchi_key=compare_keys(iid.get('rdkit_inchikey',''),key)
        verified=bool(mol is not None and key and sm_key=='full_inchikey_match' and inchi_key=='full_inchikey_match' and cid_verified)
        flags=[]
        if parse_status!='valid':flags.append(parse_status)
        if not cid_verified:flags.append('cid_conflict')
        if sm_key!='full_inchikey_match':flags.append('smiles_'+sm_key)
        if inchi_key!='full_inchikey_match':flags.append('inchi_'+inchi_key)
        if mid.get('components',0)>1:flags.append('multiple_components')
        if mid.get('metal_atoms'):flags.append('metal_containing')
        if mid.get('chiral_unassigned',0)>0:flags.append('unspecified_atom_stereo')
        if mid.get('double_stereo_unassigned',0)>0:flags.append('unspecified_double_bond_stereo')
        formula=unique_property(r,'Molecular Formula')
        if mid and formula and mid['formula']!=formula:flags.append('formula_conflict')
        eligible=verified and not flags
        src={'id':r['id'],'name':r['name'],'cid':c['cid'],'xml_record_index':r['record_index'],
             'raw_smiles':sm,'raw_inchi':inc,'raw_inchikey':key,'xml_formula':formula,
             'smiles_source':' / '.join(sorted({p['source'] for p in r['properties'] if p['kind']=='SMILES'})),
             'source_path':'drug/calculated-properties/property[kind=SMILES]/value',
             'source_kind':'local_DrugBank_XML','structure_selection':'unaltered_source_SMILES',
             'xml_cids':'|'.join(xml_cids),'bridge_cid':bridge[r['id']]['bridge_cid'],
             'declared_salt_links':len(r['salt_links'])}
        source.append(src)
        q={'id':r['id'],'name':r['name'],'cid':c['cid'],'parse_status':parse_status,
           'inchi_parse_status':iparse,'smiles_key_relation':sm_key,'inchi_key_relation':inchi_key,
           'cid_verified':cid_verified,'identity_verified_local':verified,
           'strict_qc_pass':eligible,'review_flags':'|'.join(flags),**mid}
        quality.append(q)
        d=descriptors(mol);raw.append({'id':r['id'],**d})
        clean.append({'id':r['id'],**(d if eligible else {k:None for k in FEATURES})})
        if mol is not None:molecules[r['id']]=mol
        for p in r['properties']:props.append({'id':r['id'],**p})
        old=legacy.get(r['id'])
        for k in FEATURES:
            ov=float(old[k]) if old and old[k]!='' else None;nv=d[k]
            comparison.append({'id':r['id'],'name':r['name'],'feature':k,'old_value':ov,
                'rdkit_value':nv,'delta_rdkit_minus_old':nv-ov if nv is not None and ov is not None else None,
                'legacy_cid':old['pubchem_clean'] if old else '',
                'cid_agrees':old['pubchem_clean']==c['cid'] if old else None,
                'strict_qc_pass':eligible,
                'definition_note':{'LogP':'legacy PubChem XLogP vs RDKit Wildman-Crippen',
                    'TPSA':'legacy PubChem TPSA vs RDKit N/O-only; S/P sensitivity separately',
                    'HBD':'legacy PubChem vs RDKit Lipinski.NumHDonors',
                    'HBA':'legacy PubChem vs RDKit Lipinski.NumHAcceptors',
                    'MW':'legacy PubChem reported molecular weight vs RDKit average MolWt'}[k]})
    csv('structure_sources.csv',source);csv('structure_validation.csv',quality)
    csv('xml_property_evidence.csv',props)
    csv('chemical_features_raw.csv',raw);csv('chemical_features_clean.csv',clean)
    csv('legacy_feature_comparison.csv',comparison)
    qdf=pd.DataFrame(quality);rdf=pd.DataFrame(raw);cdf=pd.DataFrame(clean)
    oldids=set(legacy);recovery=[]
    for r in quality:
        recovery.append({k:r[k] for k in ['id','name','cid','parse_status','identity_verified_local','strict_qc_pass','review_flags']}
            |{'old_chemistry_available':r['id'] in oldids,
              'newly_computed_raw':r['id'] not in oldids and r['parse_status']=='valid',
              'recovered_strict':r['id'] not in oldids and r['strict_qc_pass']})
    csv('coverage_and_recovery.csv',recovery)
    csv('missingness.csv',[{'feature':k,'cohort':62,'old_missing':sum(r['id'] not in oldids for r in quality),
        'raw_missing':int(rdf[k].isna().sum()),'clean_missing_or_held':int(cdf[k].isna().sum())} for k in FEATURES])
    comp=pd.DataFrame(comparison);stats=[]
    for k,g in comp.dropna(subset=['old_value','rdkit_value']).groupby('feature'):
        delta=g.delta_rdkit_minus_old
        stats.append({'feature':k,'comparable_drugs':len(g),'mean_absolute_difference':float(delta.abs().mean()),
                      'median_signed_difference':float(delta.median()),'max_absolute_difference':float(delta.abs().max()),
                      'exact_numeric_matches':int((delta.abs()<1e-9).sum())})
    csv('legacy_difference_summary.csv',stats)
    sensitivity=[]
    for r in quality:
        mol=molecules.get(r['id'])
        if mol is None:continue
        no=float(rdMolDescriptors.CalcTPSA(mol,includeSandP=False));sp=float(rdMolDescriptors.CalcTPSA(mol,includeSandP=True))
        sensitivity.append({'id':r['id'],'name':r['name'],'TPSA_N_O':no,'TPSA_with_S_P':sp,'delta_S_P':sp-no})
    csv('tpsa_definition_sensitivity.csv',sensitivity)
    for example in ['DB01060','DB00537','DB00601','DB00207','DB00512']:
        if example in molecules:
            a,b=atom_bond_tables(molecules[example]);csv(f'{example}_atoms.csv',a);csv(f'{example}_bonds.csv',b)
    fields=Counter(p['kind'] for p in props)
    csv('xml_field_coverage.csv',[{'kind':k,'property_rows':n,
        'drugs_with_field':len({p['id'] for p in props if p['kind']==k})} for k,n in fields.items()])
    summary={'cohort':len(cohort),'xml_structures':sum(bool(s['raw_smiles']) for s in source),
        'valid_smiles':sum(r['parse_status']=='valid' for r in quality),
        'local_identity_verified':sum(r['identity_verified_local'] for r in quality),
        'strict_qc_pass':sum(r['strict_qc_pass'] for r in quality),
        'old_chemistry_available':sum(r['old_chemistry_available'] for r in recovery),
        'old_chemistry_missing':sum(not r['old_chemistry_available'] for r in recovery),
        'recovered_raw':sum(r['newly_computed_raw'] for r in recovery),
        'recovered_strict':sum(r['recovered_strict'] for r in recovery),
        'flags':dict(Counter(f for r in quality for f in r['review_flags'].split('|') if f)),
        'pubchem_requests_this_analysis':0,'descriptor_policy':'whole source molecule; no atom/bond/fragment removal',
        'feature_schema':['id',*FEATURES],
        'rdkit_version':rdBase.rdkitVersion,'python_version':platform.python_version(),
        'tpsa_default':'includeSandP=False (N/O only); sensitivity with True separate',
        'missing_policy':'null; no filling; strict QC holds all five descriptors for reviewed structures'}
    save('coverage_summary.json',summary)
    save('analysis_input_manifest.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [OUT/'cohort_identity.json',OUT/'xml_chemical_records.json',OUT/'legacy_chemistry_reference.json',ROOT/'reports/qa/WP02/bridge_qc.json']})
    print(json.dumps(summary,ensure_ascii=True,indent=2))
    print('REVIEW',qdf[qdf.review_flags.ne('')][['id','name','review_flags']].to_string(index=False))


if __name__=='__main__':main()
