"""WP03 SIDER kimlik ve pozitif ilişki keşfi; model girdisi/split/negatif üretmez."""
from pathlib import Path
from collections import Counter,defaultdict
import json,re,ast,time,hashlib
import pandas as pd
import psutil

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/qa/WP03'
SIDER=Path(r'C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset\SIDER\meddra_all_se.tsv\meddra_all_se.tsv')
COLS=['flat_id','stereo_id','label_cui','meddra_type','meddra_cui','term']

def decode_stitch(value,kind):
    """CID + tür biti + en az 8 haneli suffix. Flat ≠ stereo; tür doğrulanır."""
    marker={'stereo':'0','flat':'1'}[kind]
    if not re.fullmatch('CID'+marker+r'\d{8,}',value):raise ValueError('invalid STITCH '+kind+': '+str(value))
    cid=int(value[4:])
    if cid<=0:raise ValueError('nonpositive CID')
    return str(cid)

def encode_stitch(cid,kind):
    if not re.fullmatch(r'[1-9]\d*',str(cid)):raise ValueError('invalid CID')
    return 'CID'+{'stereo':'0','flat':'1'}[kind]+f'{int(cid):08d}'

def jread(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha256_stream(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def jsave(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def csvsave(name,df):df.to_csv(OUT/name,index=False,encoding='utf-8-sig')

def resolve_candidate(cid,xml_cids,stereo_to_flat,flat_to_stereo,cid_owners):
    if not cid:return 'unmatched_no_cid',[],[]
    if not re.fullmatch(r'[1-9]\d*',cid):return 'ambiguous_invalid_cid',[],[]
    if xml_cids and set(xml_cids)!={cid}:return 'ambiguous_xml_bridge_conflict',[],[]
    if len(cid_owners.get(cid,[]))>1:return 'ambiguous_shared_cid',[],[]
    sid=encode_stitch(cid,'stereo');flat=encode_stitch(cid,'flat')
    if sid in stereo_to_flat:
        f=sorted(stereo_to_flat[sid])
        return ('exact_stereo_cid' if len(f)==1 else 'ambiguous_stereo_multi_flat'),f,[sid]
    if flat in flat_to_stereo:return 'ambiguous_flat_only', [flat],sorted(flat_to_stereo[flat])
    return 'unmatched_cid_not_in_sider',[],[]

def legacy_map():
    tree=ast.parse((ROOT/'legacy/MASTER_KOD.py').read_text(encoding='utf-8'))
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HEDEF_35_SE' for x in n.targets))

def main():
    OUT.mkdir(parents=True,exist_ok=True);before=SIDER.stat();start=time.perf_counter()
    df=pd.read_csv(SIDER,sep='\t',header=None,names=COLS,dtype=str,keep_default_na=False)
    pair=df[['flat_id','stereo_id']].drop_duplicates();s2f=defaultdict(set);f2s=defaultdict(set)
    invalid=[]
    for row in pair.itertuples(index=False):
        try:decode_stitch(row.flat_id,'flat');decode_stitch(row.stereo_id,'stereo')
        except ValueError:invalid.append(row._asdict());continue
        s2f[row.stereo_id].add(row.flat_id);f2s[row.flat_id].add(row.stereo_id)
    pt=df[(df.meddra_type=='PT') & df.meddra_cui.str.fullmatch(r'C\d{7}') & df.term.ne('')].copy()
    quality={'rows':len(df),'unique_flat':df.flat_id.nunique(),'unique_stereo':df.stereo_id.nunique(),
        'unique_flat_stereo_pairs':len(pair),'type_counts':df.meddra_type.value_counts().to_dict(),
        'missing':{c:int(df[c].str.strip().eq('').sum()) for c in COLS},
        'duplicate_full_rows_excess':int(df.duplicated().sum()),
        'duplicate_stereo_type_cui_excess':int(df.duplicated(['stereo_id','meddra_type','meddra_cui']).sum()),
        'pt_rows_eligible':len(pt),'pt_unique_stereo_cui':len(pt[['stereo_id','meddra_cui']].drop_duplicates()),
        'pt_unique_cui':pt.meddra_cui.nunique(),'pt_unique_names':pt.term.nunique(),
        'flat_with_multiple_stereo':sum(len(v)>1 for v in f2s.values()),
        'stereo_with_multiple_flat':sum(len(v)>1 for v in s2f.values()),'invalid_stitch_pairs':invalid}
    jsave('sider_quality.json',quality)
    pair['flat_cid']=pair.flat_id.map(lambda v:decode_stitch(v,'flat'));pair['stereo_cid']=pair.stereo_id.map(lambda v:decode_stitch(v,'stereo'))
    csvsave('stitch_pair_map.csv',pair)
    csvsave('sider_examples.csv',df.head(12))
    terms=pt[['meddra_cui','term']].drop_duplicates()
    csvsave('pt_concept_dictionary.csv',terms)
    reg=jread(ROOT/'reports/qa/WP02/drug_registry.json');bridge=jread(ROOT/'reports/qa/WP02/bridge_qc.json')['rows']
    bidx={r['id']:r for r in bridge};old=jread(ROOT/'reports/qa/WP02/legacy_membership.json')
    oldidx={r['id']:r for r in old['members']};owners=defaultdict(list)
    for r in bridge:
        if r['bridge_cid']:owners[r['bridge_cid']].append(r['id'])
    records=[]
    for r in reg:
        if not r['j01']:continue
        b=bidx[r['id']];cid=b['bridge_cid'];status,flats,stereos=resolve_candidate(cid,r['pubchem_cid'],s2f,f2s,owners)
        exact=status=='exact_stereo_cid';sid=encode_stitch(cid,'stereo') if cid else ''
        subset=pt[pt.stereo_id==sid] if exact else pt.iloc[0:0]
        o=oldidx.get(r['id'],{})
        records.append({'id':r['id'],'name':r['name'],'conservative':r['j01_noncombination'],
            'xml_cids':r['pubchem_cid'],'cid':cid,'sid':b['bridge_sid'],'status':status,
            'flat_ids':flats,'stereo_ids':stereos,'pt_count':subset.meddra_cui.nunique(),
            'has_pt':bool(len(subset)),'chemistry_available':bool(o.get('chemistry',False)),
            'protein_available':bool(r['protein_ids']),'protein_count':len(r['protein_ids']),
            'old38':bool(o.get('old38',False)),'old_adr':bool(o.get('adr',False)),
            'salt_ids':[s['salt_id'] for s in r['salts']], 'secondary_ids':r['secondary_ids'],
            'compound_identity_scope':'source CID equality, not clinical causality or formulation equivalence'})
    mapping=pd.DataFrame(records)
    jsave('drug_mapping.json',records)
    csvsave('drug_mapping.csv',mapping)
    exact=mapping[mapping.status.eq('exact_stereo_cid')]
    # Join only exact stereo identity; retain row-level SIDER provenance, never flat-only labels.
    em=exact[['id','name','cid','conservative']].copy();em['stereo_id']=em.cid.map(lambda c:encode_stitch(c,'stereo'))
    df['source_line']=range(1,len(df)+1)
    rawpt=df[(df.meddra_type=='PT') & df.meddra_cui.str.fullmatch(r'C\d{7}') & df.term.ne('')]
    positives=em.merge(rawpt,on='stereo_id',validate='one_to_many')
    provenance=positives[['id','name','cid','conservative','flat_id','stereo_id','label_cui','meddra_cui','term','source_line']]
    csvsave('pt_evidence.csv',provenance)
    unique=provenance.drop_duplicates(['id','meddra_cui'])[['id','name','cid','conservative','meddra_cui','term']]
    csvsave('drug_pt_positives.csv',unique)
    # Audit old categories; this is not a new approved target definition.
    cmap=legacy_map();cat=provenance[provenance.term.isin(cmap)].copy();cat['code_category']=cat.term.map(cmap)
    csvsave('legacy_code_category_projection.csv',cat)
    olddata=jread(OUT/'legacy_comparison_input.json');odf=pd.DataFrame(olddata['rows'])
    ref38={x['id'] for x in old['members'] if x['old38']}
    old38=odf[odf.id.isin(ref38)]
    oldpairs=old38[['id','category']].drop_duplicates()
    # Mapping from actual historical PT/CUI to categories can expose code/file revision drift.
    actualmap=odf[['pt','cui','category']].drop_duplicates()
    historical=provenance.merge(actualmap,left_on=['term','meddra_cui'],right_on=['pt','cui'],how='inner')
    csvsave('historical_category_projection_audit.csv',historical)
    cat_audit=[]
    for category,g in actualmap.groupby('category'):
        cuis=sorted(g.cui.unique());names=sorted(g.pt.unique())
        cat_audit.append({'category':category,'pt_names':names,'cuis':cuis,'n_cui':len(cuis),'n_names':len(names),
            'code_categories':sorted({cmap[n] for n in names if n in cmap}),
            'code_missing_terms':[n for n in names if n not in cmap]})
    jsave('category_audit.json',cat_audit);csvsave('category_audit.csv',pd.DataFrame(cat_audit))
    comparisons={'old_rows':len(odf),'old_unique_drug_category':len(odf[['id','category']].drop_duplicates()),
        'old38_rows':len(old38),'old38_unique_pairs':len(oldpairs),'actual_categories':odf.category.nunique(),
        'code_terms':len(cmap),'code_categories':len(set(cmap.values())),
        'old_pt_name_absent_in_code':sorted(set(odf.pt)-set(cmap)),
        'actual_pt_cui_to_multiple_categories':int((actualmap.groupby(['pt','cui']).category.nunique()>1).sum()),
        'old38_unique_cui':len(old38[['id','cui']].drop_duplicates()),
        'reference_all_legacy_keys_in_raw_sider':0}
    # Check old labels using raw SIDER, including out-of-cohort legacy IDs, strictly QC.
    keys=set(zip(rawpt.stereo_id.map(lambda v:decode_stitch(v,'stereo')),rawpt.term,rawpt.meddra_cui))
    comparisons['reference_all_legacy_keys_in_raw_sider']=sum((r.cid,r.pt,r.cui) in keys for r in odf.itertuples())
    old38ids=odf[odf.id.isin(ref38)][['id','cid']].drop_duplicates()
    old38ids['stereo_id']=old38ids.cid.map(lambda v:encode_stitch(v,'stereo'))
    rebuilt=old38ids.merge(rawpt,on='stereo_id',validate='one_to_many').merge(actualmap,left_on=['term','meddra_cui'],right_on=['pt','cui'])
    comparisons['rebuilt_old38_unique_categories_from_raw']=len(rebuilt[['id','category']].drop_duplicates())
    comparisons['rebuilt_old38_unique_pt_from_raw']=len(rebuilt[['id','meddra_cui']].drop_duplicates())
    csvsave('old38_reproduction_audit.csv',rebuilt[['id','stereo_id','meddra_cui','term','category','source_line']].drop_duplicates())
    jsave('legacy_comparison.json',comparisons)
    summary={}
    for label,pop in [('broad',mapping),('conservative',mapping[mapping.conservative])]:
        accepted=pop[pop.has_pt]
        summary[label]={'candidates':len(pop),'cid_available':int(pop.cid.ne('').sum()),'status_counts':pop.status.value_counts().to_dict(),
            'exact_sider':int(pop.status.eq('exact_stereo_cid').sum()),'with_pt':len(accepted),
            'chemistry_and_pt':int(accepted.chemistry_available.sum()),'protein_and_pt':int(accepted.protein_available.sum()),
            'all_three':int((accepted.chemistry_available & accepted.protein_available).sum()),
            'missing_chemistry_with_pt':int((~accepted.chemistry_available).sum()),
            'missing_protein_with_pt':int((~accepted.protein_available).sum()),
            'new_vs_old38':int((~accepted.old38).sum()),'retained_old38':int(accepted.old38.sum()),
            'old_adr_but_missing_now':pop[pop.old_adr & ~pop.has_pt].id.tolist(),
            'positive_drug_pt_pairs':int(unique[unique.id.isin(accepted.id)].shape[0]),
            'code_category_pairs_audit':int(cat[cat.id.isin(accepted.id)][['id','code_category']].drop_duplicates().shape[0]),
            'historical_category_pairs_audit':int(historical[historical.id.isin(accepted.id)][['id','category']].drop_duplicates().shape[0])}
        summary[label]['with_historical_category_audit']=historical[historical.id.isin(accepted.id)].id.nunique()
        summary[label]['with_code_category_audit']=cat[cat.id.isin(accepted.id)].id.nunique()
    jsave('coverage_summary.json',summary)
    csvsave('unmatched_or_ambiguous.csv',mapping[~mapping.status.eq('exact_stereo_cid')])
    csvsave('new_drugs_vs_old38.csv',mapping[mapping.conservative & mapping.has_pt & ~mapping.old38])
    csvsave('missing_modalities.csv',mapping[mapping.conservative & mapping.has_pt & (~mapping.chemistry_available | ~mapping.protein_available)])
    # Parent salt links are provenance, not automatic salt CID/ADR equivalence.
    saltrows=[{'parent_id':r['id'],'salt_id':s['salt_id'],'salt_name':s['salt_name'],
               'parent_mapping_status':mapping.set_index('id').loc[r['id'],'status'],
               'salt_compound_cid':'not_available_in_WP02','label_transfer':'not_performed'}
              for r in reg if r['j01'] for s in r['salts']]
    csvsave('salt_mapping_review.csv',pd.DataFrame(saltrows))
    term_conflicts=terms.groupby('term').meddra_cui.nunique()
    csvsave('pt_name_cui_conflicts.csv',term_conflicts[term_conflicts>1].rename('distinct_cui').reset_index())
    crosswalk=rawpt[['label_cui','meddra_cui','term']].drop_duplicates()
    csvsave('label_to_pt_crosswalk.csv',crosswalk)
    jsave('source_manifest.json',{'sider_path':str(SIDER),'source_size':before.st_size,'source_mtime_ns':before.st_mtime_ns,
        'metadata_unchanged':(before.st_size,before.st_mtime_ns)==(SIDER.stat().st_size,SIDER.stat().st_mtime_ns),
        'sha256':sha256_stream(SIDER),'elapsed_seconds':time.perf_counter()-start,
        'os_peak_wset_mib':getattr(psutil.Process().memory_info(),'peak_wset',0)/2**20,
        'mapping_policy':'exact validated stereo CID only; flat-only review; no SID-as-CID; no fuzzy names',
        'legacy_source':{k:v for k,v in olddata.items() if k!='rows'}})
    print(json.dumps({'quality':quality,'coverage':summary,'legacy':comparisons},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
