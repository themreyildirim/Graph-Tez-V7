"""Özel şema sorusu için erken kayıtlardan sınırlı kanıt; tam taramayı tekrarlamaz."""
import xml.etree.ElementTree as ET
from wp02_drugbank import XML,OUT,save_json
def main():
    ns='{http://www.drugbank.ca}';depth=0;examples=[]
    wanted={'DB00196','DB00199','DB00207','DB00254','DB00512','DB00601'}
    with XML.open('rb') as f:
        for event,e in ET.iterparse(f,events=('start','end')):
            if event=='start':
                depth+=1
                if depth==1:root=e
            else:
                if depth==2 and e.tag==ns+'drug':
                    pid=next((i.text for i in e.findall(ns+'drugbank-id') if i.get('primary')=='true'),'')
                    if pid in wanted:
                        examples.append({'id':pid,'atc_hierarchy':[ET.tostring(a,encoding='unicode') for a in e.findall(f'{ns}atc-codes/{ns}atc-code')],
                            'salt_id_attributes':[{'text':i.text,'attributes':i.attrib} for i in e.findall(f'{ns}salts/{ns}salt/{ns}drugbank-id')]})
                    root.remove(e);e.clear()
                    if len(examples)==len(wanted):break
                depth-=1
        save_json('schema_evidence.json',{'bytes_read':f.tell(),'examples':examples})
    print('Schema evidence saved',flush=True)
if __name__=='__main__':main()
