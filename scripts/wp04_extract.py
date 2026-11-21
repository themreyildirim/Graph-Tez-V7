"""Yalnız 62 seçili ana kaydın kimyasal XML alanlarını tek akışla çıkarır."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
import psutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/qa/WP04'
DEFAULT_ROOT = Path(r'C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset')
NS = '{http://www.drugbank.ca}'


def text(e, path):
    return (e.findtext('/'.join(NS+x for x in path.split('/'))) or '').strip()


def chemical_record(e, index):
    prim = [x.text.strip() for x in e.findall(NS+'drugbank-id') if x.get('primary') == 'true' and x.text]
    props = []
    for section in ['calculated-properties', 'experimental-properties']:
        for p in e.findall(f'{NS}{section}/{NS}property'):
            props.append({'section':section, 'kind':text(p,'kind'), 'value':text(p,'value'),
                          'source':text(p,'source'), 'xml_path':f'drug/{section}/property'})
    external = [{'resource':text(x,'resource'), 'identifier':text(x,'identifier')}
                for x in e.findall(f'{NS}external-identifiers/{NS}external-identifier')
                if text(x,'resource') in ['PubChem Compound','PubChem Substance']]
    salts = [{'id':text(s,'drugbank-id'),'name':text(s,'name'),'inchikey':text(s,'inchikey'),
              'cas':text(s,'cas-number')} for s in e.findall(f'{NS}salts/{NS}salt')]
    return {'id':prim[0] if len(prim)==1 else '', 'primary_count':len(prim),
            'name':text(e,'name'), 'record_index':index, 'type':e.get('type',''),
            'properties':props, 'external_identifiers':external,'salt_links':salts}


def extract(path, selected):
    """Bellek üst sınırı geçmiş kayıt sayısıyla büyümez; son seçili kayıtta durur."""
    before=path.stat(); meta={'source':str(path),'size_bytes':before.st_size,'mtime_ns':before.st_mtime_ns}
    depth=0; index=0; records=[]; found=set(); peak=0; start=time.monotonic()
    with path.open('rb') as f:
        for event,e in ET.iterparse(f,events=('start','end')):
            if event=='start':
                depth+=1
                if depth==1:
                    root=e;meta['root_attributes']=dict(e.attrib)
            else:
                if depth==2 and e.tag.rsplit('}',1)[-1]=='drug':
                    index+=1
                    ids=[x.text.strip() for x in e.findall(NS+'drugbank-id') if x.get('primary')=='true' and x.text]
                    if set(ids)&selected:
                        r=chemical_record(e,index);records.append(r);found.add(r['id'])
                    root.remove(e);e.clear()
                    if index%500==0:
                        peak=max(peak,psutil.Process().memory_info().rss)
                        print(f'XML {index} kayıt, seçili {len(found)}/{len(selected)}',flush=True)
                    if found==selected:break
                depth-=1
        meta.update(bytes_read=f.tell(),records_scanned=index,selected_found=len(found),
                    requested=len(selected),missing=sorted(selected-found),stopped_early=found==selected)
    after=path.stat();mem=psutil.Process().memory_info()
    meta.update(elapsed_seconds=time.monotonic()-start,sampled_rss_max_mib=max(peak,mem.rss)/2**20,
                os_peak_wset_mib=getattr(mem,'peak_wset',mem.rss)/2**20,
                metadata_unchanged=before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns)
    return records,meta


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset-root',type=Path,
        default=Path(os.environ.get('GRAPH_TEZ_DATA_ROOT',str(DEFAULT_ROOT))))
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    mapping=json.loads((ROOT/'reports/qa/WP03/drug_mapping.json').read_text(encoding='utf-8'))
    # Etiket sayıları hesaplamaya geçmez: yalnız önce onaylı kohortun kimlikleri alınır.
    cohort=[{k:r[k] for k in ['id','name','cid']} for r in mapping if r['conservative'] and r['status']=='exact_stereo_cid']
    assert len(cohort)==62 and len({r['id'] for r in cohort})==62
    (OUT/'cohort_identity.json').write_text(json.dumps(cohort,ensure_ascii=False,indent=2),encoding='utf-8')
    path=args.dataset_root/'DrugBank/drugbank_all_full_database.xml/full database.xml'
    records,meta=extract(path,{r['id'] for r in cohort})
    for name,obj in [('xml_chemical_records.json',records),('xml_extract_manifest.json',meta)]:
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=True,indent=2))
    assert not meta['missing'] and meta['metadata_unchanged']


if __name__=='__main__':main()
