"""WP02 DrugBank kimlik/kohort QC. Salt okunur streaming; özellik/tensör yok."""
from pathlib import Path
from collections import Counter, defaultdict
import json, csv, time, re
import xml.etree.ElementTree as ET
import psutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/qa/WP02'
XML=Path(r'C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset\DrugBank\drugbank_all_full_database.xml\full database.xml')

def direct_record(elem, index):
    ns=elem.tag.split('}')[0]+'}' if '}' in elem.tag else ''
    def text(node,name):return (node.findtext(ns+name) or '').strip()
    ids=[{'id':(c.text or '').strip(),'primary':c.get('primary')=='true'} for c in elem.findall(ns+'drugbank-id')]
    primary=[r['id'] for r in ids if r['primary']]
    atcs=sorted({c.get('code') for c in elem.findall(f'{ns}atc-codes/{ns}atc-code') if c.get('code')})
    salts=[]
    for s in elem.findall(f'{ns}salts/{ns}salt'):
        salts.append({'salt_id':text(s,'drugbank-id'),'salt_name':text(s,'name'),
                      'parent_id':primary[0] if len(primary)==1 else '', 'source':'direct drug/salts/salt'})
    ext=defaultdict(list)
    for e in elem.findall(f'{ns}external-identifiers/{ns}external-identifier'):
        if text(e,'resource') in ['PubChem Compound','PubChem Substance']:
            ext[text(e,'resource')].append(text(e,'identifier'))
    targets=[]
    for t in elem.findall(f'{ns}targets/{ns}target'):
        pps=t.findall(ns+'polypeptide')
        if not pps:
            targets.append({'target_id':text(t,'id'),'target_name':text(t,'name'),'organism':text(t,'organism'),
                            'uniprot_id':'','id_status':'no_polypeptide','aa_sequence_present':False,
                            'aa_raw_length':0,'old_sequence_tag_present':False})
        for pp in pps:
            external=[text(e,'identifier') for e in pp.findall(f'{ns}external-identifiers/{ns}external-identifier') if text(e,'resource')=='UniProtKB']
            attr=pp.get('id',''); ids_pp=set(external+([attr] if attr else []))
            status='consistent' if len(ids_pp)==1 else 'conflict' if len(ids_pp)>1 else 'missing'
            aa=pp.find(ns+'amino-acid-sequence'); raw=aa.text or '' if aa is not None else ''
            targets.append({'target_id':text(t,'id'),'target_name':text(t,'name'),
                'organism':text(pp,'organism') or text(t,'organism'),'gene_name':text(pp,'gene-name'),
                'uniprot_id':next(iter(ids_pp)) if status=='consistent' else '',
                'polypeptide_id_attribute':attr,'external_uniprot_ids':external,'id_status':status,
                'aa_sequence_present':bool(raw.strip()),'aa_raw_length':len(raw),
                'aa_header_prefix':raw[:95],'old_sequence_tag_present':pp.find(ns+'sequence') is not None})
    return {'record_index':index,'id':primary[0] if len(primary)==1 else '', 'primary_count':len(primary),
            'name':text(elem,'name'),'type':elem.get('type',''),'secondary_ids':[r['id'] for r in ids if not r['primary']],
            'atc':atcs,'j01':any(re.fullmatch(r'J01[A-Z]{2}\d{2}',c) for c in atcs),
            'groups':[c.text for c in elem.findall(f'{ns}groups/{ns}group')],
            'pubchem_cid':sorted(set(ext['PubChem Compound'])),'pubchem_sid':sorted(set(ext['PubChem Substance'])),
            'salts':salts,'targets':targets,
            'target_entries':len(elem.findall(f'{ns}targets/{ns}target')),
            'protein_ids':sorted({t['uniprot_id'] for t in targets if t['uniprot_id']})}

def iter_records(path, meta):
    depth=0;index=0
    with Path(path).open('rb') as stream:
        for event,e in ET.iterparse(stream,events=('start','end')):
            if event=='start':
                depth+=1
                if depth==1:root=e;meta['root_attributes']=dict(e.attrib)
            else:
                if depth==2 and e.tag.rsplit('}',1)[-1]=='drug':
                    index+=1
                    r=direct_record(e,index)
                    root.remove(e);e.clear() # Geçmiş kayıtlar root'ta birikmez.
                    yield r
                depth-=1
        meta['bytes_read']=stream.tell()

def identity_index(records):
    index=defaultdict(set)
    for r in records:
        for i in [r['id']]+r['secondary_ids']:
            if i:index[i].add(r['id'])
        for s in r['salts']:
            if s['salt_id']:index[s['salt_id']].add(r['id'])
    return index

def resolve(identifier, index):
    parents=sorted(index.get(identifier,set()))
    return {'query_id':identifier,'parents':parents,'status':'resolved' if len(parents)==1 else 'ambiguous' if parents else 'unresolved'}

def duplicate_primary_ids(records):
    return {i:n for i,n in Counter(r['id'] for r in records).items() if n>1}

def save_json(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def save_csv(name,rows):
    if not rows:return
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        fields=list(dict.fromkeys(k for r in rows for k in r))
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)

def analyze(records,meta):
    legacy=json.loads((OUT/'legacy_membership.json').read_text(encoding='utf-8'))
    ix=identity_index(records);byid={r['id']:r for r in records};j01=[r for r in records if r['j01'] and r['primary_count']==1]
    mapping=[]
    for old in legacy['old_candidates']:
        m=resolve(old['id'],ix);parent=byid.get(m['parents'][0]) if m['status']=='resolved' else None
        mapping.append({**old,**m,'parent_id':parent['id'] if parent else '', 'parent_name':parent['name'] if parent else '',
                        'parent_j01':parent['j01'] if parent else None,'parent_atc':parent['atc'] if parent else [],
                        'id_kind':'DBSALT' if old['id'].startswith('DBSALT') else 'primary' if old['id'] in byid else 'secondary'})
    coverage=[]
    for old in legacy['members']:
        m=resolve(old['id'],ix);r=byid.get(m['parents'][0]) if m['status']=='resolved' else None
        coverage.append({**old,'mapping_status':m['status'],'parent_id':r['id'] if r else '',
                         'xml_name':r['name'] if r else '', 'j01':r['j01'] if r else None,'atc':r['atc'] if r else [],
                         'xml_target_entries':r['target_entries'] if r else None,'xml_proteins':len(r['protein_ids']) if r else None,
                         'xml_protein_ids':r['protein_ids'] if r else [],
                         'chemistry_only_candidate':old['chemistry'] and old['adr'] and not old['legacy_targets'],
                         'xml_aa_proteins':len({t['uniprot_id'] for t in r['targets'] if t['uniprot_id'] and t['aa_sequence_present']}) if r else None})
    old38={r['parent_id'] for r in coverage if r['old38'] and r['mapping_status']=='resolved'}
    old209parents={m['parent_id'] for m in mapping if m['status']=='resolved'}
    for r in records:
        r['in_old38']=r['id'] in old38;r['in_old209_parent']=r['id'] in old209parents
        r['j01_noncombination']=any(re.fullmatch(r'J01[A-Z]{2}\d{2}',c) and not c.startswith('J01R') for c in r['atc'])
        r['j01_combination_only']=r['j01'] and not r['j01_noncombination']
    for c in coverage:
        parent=byid.get(c['parent_id'])
        c['j01_noncombination']=parent['j01_noncombination'] if parent else None
    salt_rows=[s for r in records for s in r['salts']]
    invalid=[r for r in records if r['primary_count']!=1 or not re.fullmatch(r'DB\d{5}',r['id'])]
    duplicates=duplicate_primary_ids(records)
    counts={'records':len(records),'record_types':dict(Counter(r['type'] for r in records)),
            'j01':len(j01),'j01_with_protein':sum(bool(r['protein_ids']) for r in j01),
            'j01_with_target_entry':sum(r['target_entries']>0 for r in j01),
            'j01_with_cid':sum(bool(r['pubchem_cid']) for r in j01),
            'multi_atc_all':sum(len(r['atc'])>1 for r in records),'multi_atc_j01':sum(len(r['atc'])>1 for r in j01),
            'secondary_id_occurrences':sum(len(r['secondary_ids']) for r in records),
            'salt_occurrences':len(salt_rows),'unique_salt_ids':len({s['salt_id'] for s in salt_rows}),
            'salt_ids_multiple_parents':sum(len(ix[s])>1 for s in {s['salt_id'] for s in salt_rows}),
            'old209_mapping_status':dict(Counter(m['status'] for m in mapping)),
            'old209_unique_parents':len(old209parents),'old209_unique_j01_parents':sum(byid[i]['j01'] for i in old209parents),
            'old38_j01':len(old38 & {r['id'] for r in j01}),'old38_not_j01':len(old38-{r['id'] for r in j01}),
            'j01_outside_old38':sum(not r['in_old38'] for r in j01),
            'j01_outside_old38_with_protein':sum(not r['in_old38'] and bool(r['protein_ids']) for r in j01),
            'invalid_primary_records':len(invalid),'duplicate_primary_ids':duplicates,
            'target_id_conflicts':sum(t['id_status']=='conflict' for r in records for t in r['targets'])}
    counts.update(j01_noncombination=sum(r['j01_noncombination'] for r in records),
                  j01_combination_only=sum(r['j01_combination_only'] for r in records),
                  old209_noncombination_parents=sum(byid[i]['j01_noncombination'] for i in old209parents),
                  old38_noncombination=sum(r['j01_noncombination'] and r['in_old38'] for r in records),
                  new_noncombination_with_protein=sum(r['j01_noncombination'] and not r['in_old38'] and bool(r['protein_ids']) for r in records))
    save_json('summary.json',counts);save_json('parse_manifest.json',meta)
    save_json('drug_registry.json',records)
    flat=[{k:v for k,v in r.items() if k not in ['salts','targets']} for r in records]
    save_csv('drug_registry.csv',flat);save_csv('j01_candidates.csv',[r for r in flat if r['j01']])
    save_csv('salt_parent_links.csv',salt_rows);save_csv('old209_mapping.csv',mapping);save_csv('legacy_coverage.csv',coverage)
    save_json('legacy_coverage.json',coverage)
    save_csv('secondary_ids.csv',[{'secondary_id':s,'parent_id':r['id']} for r in records for s in r['secondary_ids']])
    save_csv('target_audit.csv',[{'drug_id':r['id'],'drug_name':r['name'],**t} for r in records if r['j01'] or r['id'] in {c['parent_id'] for c in coverage} for t in r['targets']])
    save_json('old209_mapping.json',mapping)
    save_json('identity_issues.json',{'global_ambiguous_id_count':sum(len(v)>1 for v in ix.values()),
        'global_ambiguous_examples':{k:sorted(v) for k,v in ix.items() if len(v)>1},
        'legacy_members_unresolved':[x['id'] for x in coverage if x['mapping_status']=='unresolved'],
        'legacy_members_ambiguous':[x['id'] for x in coverage if x['mapping_status']=='ambiguous'],
        'all_records_missing_atc':sum(not x['atc'] for x in records)})
    save_csv('j01_noncombination_candidates.csv',[r for r in flat if r['j01_noncombination']])
    save_csv('combination_only_review.csv',[r for r in flat if r['j01_combination_only']])
    save_csv('old38_scope.csv',[r for r in coverage if r['old38']])
    save_csv('priority_drugs.csv',[r for r in coverage if r['name'] in ['Erythromycin','Azithromycin','Doxycycline','Vancomycin','Linezolid']])
    save_csv('cohort_funnel.csv',[
        {'stage':'Üst düzey ana kayıt','count':len(records),'meaning':'Kaynak kaydı; ingredient eşdeğerliği değil'},
        {'stage':'Doğrudan herhangi J01','count':len(j01),'meaning':'Kombinasyon-only dahil'},
        {'stage':'J01R dışında J01 kodu','count':counts['j01_noncombination'],'meaning':'Muhafazakâr analiz adayı'},
        {'stage':'Bu adaylarda eski ADR kaydı','count':sum(r['j01_noncombination'] and r['adr'] for r in coverage),'meaning':'Yeni SIDER taraması değil'},
        {'stage':'Önceki + XML protein kimliği','count':sum(r['j01_noncombination'] and r['adr'] and bool(r['xml_proteins']) for r in coverage),'meaning':'Yeni eğitim sayısı değil'}])
    print(json.dumps(counts,ensure_ascii=False,indent=2),flush=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    previous=[ROOT/'reports/WP00.md',ROOT/'reports/WP01.md',ROOT/'notebooks/WP01_graf_temelleri.ipynb']
    if not all(p.exists() for p in previous):raise RuntimeError('Previous outputs missing')
    before=XML.stat();start=time.perf_counter();process=psutil.Process();peak=process.memory_info().rss;meta={}
    records=[]
    for r in iter_records(XML,meta):
        records.append(r)
        if len(records)%500==0:
            peak=max(peak,process.memory_info().rss)
            print(f'Records {len(records)}; sampled RSS {peak/2**20:.1f} MiB',flush=True)
    after=XML.stat();mem=process.memory_info()
    meta.update(source_path=str(XML),size_bytes=before.st_size,elapsed_seconds=time.perf_counter()-start,
                sampled_rss_peak_mib=max(peak,mem.rss)/2**20,os_peak_wset_mib=getattr(mem,'peak_wset',0)/2**20,
                metadata_unchanged=(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),
                source_mtime_ns=before.st_mtime_ns,parse_complete=True,
                method='stdlib iterparse; only depth=2 drug; remove+clear after each record; compact QC summaries retained')
    analyze(records,meta)

if __name__=='__main__':main()
