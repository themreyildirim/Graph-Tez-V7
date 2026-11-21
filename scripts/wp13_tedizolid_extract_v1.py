"""Targeted streaming DrugBank chemistry/identity audit; no safety/label fields exported."""
from pathlib import Path
import xml.etree.ElementTree as ET,json,re,time
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/tedizolid_preparation_v1'
NS={'d':'http://www.drugbank.ca'}
def text(el,path):return el.findtext(path,default='',namespaces=NS)
def main():
 Q.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((ROOT/'reports/qa/WP02/parse_manifest.json').read_text(encoding='utf-8'));p=Path(manifest['source_path']);before=p.stat();start=time.time()
 wanted={'DB09042','DB14569'};found=[];depth=0;root=None
 for event,el in ET.iterparse(p,events=('start','end')):
  if event=='start':
   depth+=1
   if root is None:root=el
   continue
  if depth==2 and el.tag.endswith('}drug'):
   primary=[x.text for x in el.findall('d:drugbank-id',NS) if x.get('primary')=='true']
   if set(primary)&wanted:
    record={'id':primary[0],'name':text(el,'d:name'),'ids':[x.text for x in el.findall('d:drugbank-id',NS)],
     'synonyms':[x.text for x in el.findall('d:synonyms/d:synonym',NS)],'salts':[],
     'properties':[],'external_identifiers':[],'roles':[],'relationship_sentences':[]}
    for section in ['calculated-properties','experimental-properties']:
     for prop in el.findall('d:'+section+'/d:property',NS):
      kind=text(prop,'d:kind')
      if kind in ['SMILES','InChI','InChIKey','Molecular Formula','Molecular Weight','logP','Polar Surface Area (PSA)','H Bond Acceptor Count','H Bond Donor Count']:
       record['properties'].append({'section':section,'kind':kind,'value':text(prop,'d:value'),'source':text(prop,'d:source')})
    for x in el.findall('d:external-identifiers/d:external-identifier',NS):record['external_identifiers'].append({'resource':text(x,'d:resource'),'identifier':text(x,'d:identifier')})
    for salt in el.findall('d:salts/d:salt',NS):record['salts'].append({'id':text(salt,'d:drugbank-id'),'name':text(salt,'d:name')})
    for role in ['targets','enzymes','transporters','carriers']:
     for target in el.findall('d:'+role+'/*',NS):
      record['roles'].append({'role':role,'name':text(target,'d:name'),'organism':text(target,'d:organism'),
       'polypeptides':[{'id':x.get('id'),'organism':text(x,'d:organism'),'sequence_present':x.find('d:amino-acid-sequence',NS) is not None} for x in target.findall('d:polypeptide',NS)]})
    # Identity-only sentence whitelist, never toxicity/adverse-reaction fields.
    for tag in ['description','mechanism-of-action']:
     for sentence in re.split(r'(?<=[.!?])\s+',text(el,'d:'+tag)):
      if re.search(r'prodrug|dephosphorylat|converted to tedizolid',sentence,re.I) and not re.search(r'adverse|side effect|toxic|safety|nausea|diarrh',sentence,re.I):record['relationship_sentences'].append({'field':tag,'sentence':sentence})
    found.append(record)
   root.remove(el);el.clear()
   if len(found)==2:break
  depth-=1
 after=p.stat();assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
 (Q/'DrugBank_identity_chemistry.json').write_text(json.dumps(found,ensure_ascii=False,indent=2),encoding='utf-8')
 (Q/'xml_read_audit.json').write_text(json.dumps({'path':str(p),'source_export':manifest['root_attributes'],'size':before.st_size,'mtime_ns':before.st_mtime_ns,'unchanged':True,'elapsed_seconds':time.time()-start,'method':'iterparse depth2 only; stop after two IDs; no label/safety export','records_found':len(found)},indent=2),encoding='utf-8')
 print('Found IDs:',[r['id'] for r in found])
if __name__=='__main__':main()
