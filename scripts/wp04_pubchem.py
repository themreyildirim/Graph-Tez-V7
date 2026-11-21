"""Gerektiğinde CID allowlist'i, bütçe, önbellek ve kayıtla sınırlı PUG REST istemcisi.

Otomatik çağrı yok. Ağ kullanımı varsayılan kapalıdır. WP04'te yerel yapı yeterliyse
bu istemciyi kullanarak kaynak sorgulamak gerekmez. SID veya isim araması yapmaz.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re
import time
import requests

PROPERTIES=('SMILES','ConnectivitySMILES','InChI','InChIKey','MolecularFormula',
            'MolecularWeight','XLogP','HBondDonorCount','HBondAcceptorCount','TPSA')


class PubChemClient:
    def __init__(self,cache_dir,allowed_cids,allow_network=False,max_requests=3,session=None):
        self.cache_dir=Path(cache_dir);self.allowed_cids={str(x) for x in allowed_cids}
        self.allow_network=allow_network;self.max_requests=max_requests;self.requests_made=0
        self.session=session or requests.Session();self.last_request=0.0

    def url(self,cids):
        ids=[str(x) for x in cids]
        if not 1<=len(ids)<=8 or len(set(ids))!=len(ids):raise ValueError('Use 1-8 unique CIDs')
        if any(not re.fullmatch(r'[1-9]\d*',x) or x not in self.allowed_cids for x in ids):
            raise ValueError('CID not in approved allowlist; no SID or names')
        return 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/'+','.join(ids)+'/property/'+','.join(PROPERTIES)+'/JSON'

    @staticmethod
    def validate(payload,cids):
        rows=payload.get('PropertyTable',{}).get('Properties',[])
        got=[str(r.get('CID','')) for r in rows]
        if len(got)!=len(set(got)) or set(got)!=set(map(str,cids)):raise ValueError('Returned CID set mismatch')
        return rows

    def fetch(self,cids,reason):
        if not reason.strip():raise ValueError('Document why local structure is insufficient')
        url=self.url(cids);key=hashlib.sha256(url.encode()).hexdigest();path=self.cache_dir/(key+'.json')
        if path.exists():
            cached=json.loads(path.read_text(encoding='utf-8'))
            if cached['url']!=url:raise ValueError('Cache URL mismatch')
            self.validate(cached['payload'],cids)
            expected=hashlib.sha256(json.dumps(cached['payload'],sort_keys=True).encode()).hexdigest()
            if expected!=cached['payload_sha256']:raise ValueError('Cache payload hash mismatch')
            self._log({'url':url,'cids':list(map(str,cids)),'reason':reason,'cache_hit':True,'status':'validated_cache'})
            return cached['payload']
        if not self.allow_network:raise RuntimeError('Network disabled; no valid cached response')
        if self.requests_made>=self.max_requests:raise RuntimeError('Request budget exhausted')
        time.sleep(max(0,1.0-(time.monotonic()-self.last_request))) # En fazla 1 çağrı/saniye.
        self.requests_made+=1;self.last_request=time.monotonic()
        event={'url':url,'cids':list(map(str,cids)),'reason':reason,'cache_hit':False}
        try:
            response=self.session.get(url,timeout=30,headers={'Accept':'application/json'})
            event.update(http_status=response.status_code,response_sha256=hashlib.sha256(response.content).hexdigest())
            response.raise_for_status();payload=response.json();self.validate(payload,cids)
            obj={'url':url,'cids':list(map(str,cids)),'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                 'payload':payload,'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()}
            self.cache_dir.mkdir(parents=True,exist_ok=True)
            temp=path.with_suffix('.tmp');temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)
            event['status']='validated_saved';return payload
        except Exception as e:
            event.update(status='failed',error=type(e).__name__+': '+str(e));raise
        finally:self._log(event)

    def _log(self,event):
        self.cache_dir.mkdir(parents=True,exist_ok=True)
        event={'utc':datetime.now(timezone.utc).isoformat(),**event}
        with (self.cache_dir/'request_log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event,ensure_ascii=False)+'\n')
