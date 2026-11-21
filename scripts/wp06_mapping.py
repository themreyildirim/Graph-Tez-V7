"""İzinli iki STRING aliases kaynağında tam accession eşlemesi; akış ve iz."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,hashlib,os,time
import pandas as pd
import psutil

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP06'
DEFAULT=Path(r'C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset')
NETWORK_DIR={'9606':'Homo Sapiens','511145':'Escherichia coli'}


def source_path(root,taxid,kind):
    if taxid not in NETWORK_DIR or kind not in ['links','aliases']:raise ValueError('Source not allowlisted')
    name=f'{taxid}.protein.{kind}.v12.0.txt'
    p=Path(root)/'string-db'/NETWORK_DIR[taxid]/name/name
    if not p.is_file():raise FileNotFoundError(p)
    return p


def scan_aliases(path,taxid,accessions):
    before=path.stat();sha=hashlib.sha256();start=time.monotonic();wanted={a.encode() for a in accessions};hits=[]
    stats=Counter();examples=[]
    with path.open('rb') as f:
        header=f.readline();sha.update(header)
        if header.decode().strip()!='#string_protein_id\talias\tsource':raise ValueError('Unexpected aliases schema')
        for line_no,line in enumerate(f,2):
            sha.update(line);stats['rows']+=1;parts=line.rstrip(b'\r\n').split(b'\t',2)
            if len(parts)!=3:stats['malformed_rows']+=1;continue
            sid,alias,src=parts
            if not sid.startswith((taxid+'.').encode()):stats['wrong_taxon_prefix']+=1
            if not all(parts):stats['missing_fields']+=1
            if len(examples)<3:examples.append([x.decode('utf-8') for x in parts])
            if alias in wanted:
                hits.append({'accession':alias.decode(),'network_taxid':taxid,'string_id':sid.decode(),
                             'alias_source':src.decode(),'source_line':line_no,'source_path':str(path)})
    after=path.stat();mem=psutil.Process().memory_info()
    meta={'file':str(path),'taxid':taxid,'kind':'aliases','version':'12.0 filename',
        'size_bytes':before.st_size,'mtime_ns':before.st_mtime_ns,'sha256':sha.hexdigest(),
        'columns':['string_protein_id','alias','source'],'examples':examples,**stats,
        'elapsed_seconds':time.monotonic()-start,'os_peak_wset_mib':getattr(mem,'peak_wset',mem.rss)/2**20,
        'metadata_unchanged':before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns}
    return hits,meta


def classify_mapping(protein,hits):
    """Tüm kayıtlar korunur; taksonomi kesinliği alias kimliğinden ayrı tutulur."""
    tax=str(protein.get('taxid',''));org=protein.get('organism','')
    if tax=='9606':network='9606';scope='exact_taxon'
    elif tax=='511145':network='511145';scope='exact_taxon'
    elif tax=='83333':network='511145';scope='K12_parent_vs_MG1655_substrain'
    elif tax=='562':network='511145';scope='species_only_strain_unresolved'
    else:return {'network_taxid':'','scope':'outside_available_network_taxa','status':'out_of_scope_organism',
                 'string_id':'','candidate_count':0,'alias_identity_unique':False,'strict_taxon_match':False}
    # Tam alias değeri accession olmalı, kaynak UniProt_AC bunu açıkça accession olarak tanımlar.
    candidates={h['string_id'] for h in hits if h['accession']==protein['accession'] and h['network_taxid']==network
                and 'UniProt_AC' in h['alias_source'].split() and h['string_id'].startswith(network+'.')}
    unique=len(candidates)==1
    if not candidates:status='unmatched_accession_alias'
    elif len(candidates)>1:status='ambiguous_multiple_STRING_ids'
    elif scope=='exact_taxon':status='exact_alias_exact_taxon'
    elif scope=='K12_parent_vs_MG1655_substrain':status='exact_alias_K12_parent_scope_review'
    else:status='exact_alias_species_strain_review'
    return {'network_taxid':network,'scope':scope,'status':status,'string_id':next(iter(candidates)) if unique else '',
            'candidate_count':len(candidates),'alias_identity_unique':unique,'strict_taxon_match':unique and scope=='exact_taxon'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset-root',type=Path,default=Path(os.environ.get('GRAPH_TEZ_DATA_ROOT',str(DEFAULT))))
    args=parser.parse_args();QA.mkdir(parents=True,exist_ok=True)
    registry=pd.read_csv(ROOT/'reports/qa/WP05/protein_registry.csv',dtype=str,keep_default_na=False).to_dict('records')
    assert len(registry)==141
    all_hits=[];manifests=[]
    for tax in NETWORK_DIR:
        hits,meta=scan_aliases(source_path(args.dataset_root,tax,'aliases'),tax,{r['accession'] for r in registry})
        all_hits+=hits;manifests.append(meta);print(tax,'alias rows',meta['rows'],'hits',len(hits),flush=True)
    rows=[{k:r[k] for k in ['accession','protein_name','organism','taxid','organism_group']}|classify_mapping(r,all_hits) for r in registry]
    pd.DataFrame(all_hits).to_csv(QA/'alias_evidence.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(rows).to_csv(QA/'protein_string_mapping.csv',index=False,encoding='utf-8-sig')
    (QA/'aliases_manifest.json').write_text(json.dumps(manifests,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Mapping',Counter(r['status'] for r in rows));print('Alias source counts',Counter(h['alias_source'] for h in all_hits))


if __name__=='__main__':main()
