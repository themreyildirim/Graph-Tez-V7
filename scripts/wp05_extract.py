"""Seçili ilaçlarda dört XML ilişki türünü, protein ve protein-dışı kanıtı korur."""
from pathlib import Path
import argparse,json,os,time
import xml.etree.ElementTree as ET
import psutil

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/qa/WP05'
DEFAULT=Path(r'C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset')
NS='{http://www.drugbank.ca}'
ROLES={'targets':'target','enzymes':'enzyme','transporters':'transporter','carriers':'carrier'}


def txt(e,path):return (e.findtext('/'.join(NS+p for p in path.split('/'))) or '').strip()


def extract_record(e,index):
    ids=[x.text.strip() for x in e.findall(NS+'drugbank-id') if x.get('primary')=='true' and x.text]
    if len(ids)!=1:raise ValueError('Missing/multiple direct primary DrugBank ID')
    rows=[]
    for section,role in ROLES.items():
        for j,t in enumerate(e.findall(f'{NS}{section}/{NS}{role}'),1):
            base={'drug_id':ids[0],'drug_name':txt(e,'name'),'role':role,'relation_id':txt(t,'id'),
                  'relation_name':txt(t,'name'),'relation_organism':txt(t,'organism'),
                  'known_action':txt(t,'known-action'),
                  'actions':[x.text.strip() for x in t.findall(f'{NS}actions/{NS}action') if x.text],
                  'source_path':f'drug/{section}/{role}[{j}]','xml_record_index':index,
                  'reference_pubmed_ids':[txt(x,'pubmed-id') for x in t.findall(f'{NS}references/{NS}articles/{NS}article')]}
            pps=t.findall(NS+'polypeptide')
            if not pps:rows.append({**base,'has_polypeptide':False});continue
            for k,pp in enumerate(pps,1):
                aa=pp.find(NS+'amino-acid-sequence');org=pp.find(NS+'organism')
                rows.append({**base,'has_polypeptide':True,'polypeptide_index':k,
                    'polypeptide_id':pp.get('id',''),'polypeptide_source':pp.get('source',''),
                    'uniprot_external_ids':[txt(x,'identifier') for x in pp.findall(f'{NS}external-identifiers/{NS}external-identifier') if txt(x,'resource')=='UniProtKB'],
                    'protein_name':txt(pp,'name'),'gene_name':txt(pp,'gene-name'),
                    'organism':txt(pp,'organism'),'organism_attributes':dict(org.attrib) if org is not None else {},
                    'raw_sequence':aa.text or '' if aa is not None else '',
                    'sequence_attributes':dict(aa.attrib) if aa is not None else {},
                    'old_sequence_tag_present':pp.find(NS+'sequence') is not None,
                    'sequence_xml_path':base['source_path']+f'/polypeptide[{k}]/amino-acid-sequence',
                    'cellular_location':txt(pp,'cellular-location'),'chromosome_location':txt(pp,'chromosome-location')})
    return {'id':ids[0],'name':txt(e,'name'),'record_index':index,'relations':rows}


def stream_extract(path,selected):
    path=Path(path);before=path.stat();start=time.monotonic();depth=0;index=0;found=set();records=[];rss=0
    meta={'source':str(path),'size_bytes':before.st_size,'mtime_ns':before.st_mtime_ns}
    with path.open('rb') as f:
        for event,e in ET.iterparse(f,events=('start','end')):
            if event=='start':
                depth+=1
                if depth==1:root=e;meta['root_attributes']=dict(e.attrib)
            else:
                if depth==2 and e.tag.rsplit('}',1)[-1]=='drug':
                    index+=1
                    ids={x.text.strip() for x in e.findall(NS+'drugbank-id') if x.get('primary')=='true' and x.text}
                    if ids&selected:
                        r=extract_record(e,index);records.append(r);found.add(r['id'])
                    root.remove(e);e.clear()
                    if index%500==0:
                        rss=max(rss,psutil.Process().memory_info().rss);print(f'{index} ana kayıt; {len(found)}/{len(selected)} seçili',flush=True)
                    if found==selected:break
                depth-=1
        meta.update(bytes_read=f.tell(),records_scanned=index,selected_found=len(found),missing=sorted(selected-found),stopped_early=found==selected)
    after=path.stat();mem=psutil.Process().memory_info()
    meta.update(elapsed_seconds=time.monotonic()-start,sampled_rss_max_mib=max(rss,mem.rss)/2**20,
                os_peak_wset_mib=getattr(mem,'peak_wset',mem.rss)/2**20,
                metadata_unchanged=before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns)
    return records,meta


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset-root',type=Path,default=Path(os.environ.get('GRAPH_TEZ_DATA_ROOT',str(DEFAULT))))
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    cohort=json.loads((ROOT/'reports/qa/WP04/cohort_identity.json').read_text(encoding='utf-8'))
    selected={r['id'] for r in cohort};assert len(selected)==62
    records,meta=stream_extract(args.dataset_root/'DrugBank/drugbank_all_full_database.xml/full database.xml',selected)
    for name,obj in [('cohort_identity.json',cohort),('xml_protein_records.json',records),('xml_extract_manifest.json',meta)]:
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=True,indent=2));assert not meta['missing'] and meta['metadata_unchanged']


if __name__=='__main__':main()
