"""Local read-only demo services. No training, OCR, network or automatic identity matching."""
import hashlib
import json
import re
from pathlib import Path
import pandas as pd
from wp12_api_security import public_sha
from wp12_pilot import get_engine

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP13/demo_v1'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def digest(data):return hashlib.sha256(data).hexdigest()

def pinned(relative):
    path=ROOT/relative
    expected=read(QA/'prior_public_files.json').get(relative)
    if not expected or not path.is_file() or public_sha(path)!=expected:
        raise ValueError('SOURCE_INTEGRITY_UNAVAILABLE')
    return path

def registry():
    return read(pinned('reports/qa/WP12/pilot_v1/drug_identity_review.json'))

def extract_pdf(data):
    if len(data)>20*1024*1024:raise ValueError('PDF_SIZE_LIMIT_20MB')
    if not data.startswith(b'%PDF-'):raise ValueError('INVALID_PDF')
    try:
        with get_engine().open(stream=data,filetype='pdf') as doc:
            if doc.needs_pass:raise ValueError('ENCRYPTED_PDF')
            if len(doc)>120:raise ValueError('PDF_PAGE_LIMIT_120')
            pages=[];total=0
            for i,p in enumerate(doc):
                text=p.get_text('text',sort=False,flags=195);total+=len(text)
                if total>2000000:raise ValueError('PDF_TEXT_LIMIT')
                images=len(p.get_images(full=True))
                status='TEXT_AVAILABLE' if text.strip() else 'NO_TEXT'
                if images and len(text.strip())<200:status='IMAGE_TEXT_UNAVAILABLE'
                pages.append({'physical_page':i+1,'text':text,'text_sha256':digest(text.encode()),'image_count':images,'status':status})
    except ValueError:raise
    except Exception:raise ValueError('PDF_EXTRACTION_FAILED') from None
    return {'document_id':'sha256:'+digest(data),'sha256':digest(data),'pages':pages,
            'page_count':len(pages),'OCR':False,'identity':'UNVERIFIED','mode':'EXPERIMENTAL_UPLOAD'}

def verified_document(filename):
    rec=next((r for r in registry() if r['filename']==filename),None)
    if rec is None:raise ValueError('UNKNOWN_DOCUMENT')
    path=pinned('data/user_pdfs/'+filename)
    bundle=read(pinned('reports/qa/WP12/pilot_v1/source_evidence_bundle.json'))
    docid='sha256:'+public_sha(path)
    if docid!=rec['document_id']:raise ValueError('IDENTITY_MISMATCH')
    fresh=extract_pdf(path.read_bytes())
    frozen=sorted([p for p in bundle['pages'] if p['document_id']==docid],key=lambda p:p['page_number'])
    if len(frozen)!=fresh['page_count'] or any(p['text']!=f['text'] for p,f in zip(fresh['pages'],frozen)):
        raise ValueError('PAGE_TEXT_MISMATCH')
    ann=read(pinned('reports/qa/WP12/pilot_v1/source_context_annotations.json'))
    amap={a['quote_id']:a for a in ann}
    quotes=[]
    for q in bundle['quotes']:
        if q['document_id']!=docid:continue
        p=fresh['pages'][q['page_number']-1]
        if p['text'][q['char_start']:q['char_end']]!=q['quote'] or digest(q['quote'].encode())!=q['quote_sha256']:
            raise ValueError('QUOTE_RANGE_MISMATCH')
        a=amap[q['quote_id']]
        quotes.append({**q,'purpose':a['purpose'],'scope':a['attribution_scope'],'qualifier':a['qualifier']})
    return {**fresh,'mode':'VERIFIED_DEMO','identity':'SOURCE_PARENT_MAPPING_ONLY',
            'record':rec,'quotes':quotes,'source_verification':'VERIFIED','clinical_validation':'NOT_ESTABLISHED'}

def match_upload(data,claimed_parent=None):
    found=next((r for r in registry() if r['document_id']=='sha256:'+digest(data)),None)
    if claimed_parent is not None and (found is None or found['DrugBank_parent_id']!=claimed_parent):
        raise ValueError('IDENTITY_MISMATCH')
    return found

def candidates(document):
    """Transparent lexical context windows, NOT ADR extraction/clinical validation."""
    rows=[]
    for p in document['pages']:
        if p['status']!='TEXT_AVAILABLE':continue
        for m in re.finditer(r'(?i)side effects?|adverse reactions?|yan etk|istenmeyen etki',p['text']):
            start=max(0,m.start()-80);end=min(len(p['text']),m.end()+480);quote=p['text'][start:end]
            rows.append({'physical_page':p['physical_page'],'char_start':start,'char_end':end,
                'quote':quote,'quote_id':'experimental:'+digest((document['document_id']+str(p['physical_page'])+str(start)+str(end)+quote).encode()),
                'status':'EXPERIMENTAL','method':'literal_keyword_context_not_clinical_extraction'})
            if len(rows)>=40:return rows
    return rows

def saved_explanations(filename):
    cases=['S01','S04'] if filename=='pil.502.pdf' else ['S07']
    all_rows=read(pinned('reports/qa/WP12/openai_S15_actual_review_v1/five_case_source_claim_comparison.json'))
    return [r for r in all_rows if r.get('scenario') in cases]

def gnn(document):
    if document.get('mode')!='VERIFIED_DEMO' or 'record' not in document:
        return {'status':'NOT_AVAILABLE','reason':'Doğrulanmış kaynak–ana ilaç eşlemesi yok.','rows':[]}
    parent=document['record']['DrugBank_parent_id']
    try:path=pinned('reports/qa/WP10/training_v1/oof_predictions.csv')
    except ValueError:return {'status':'NOT_AVAILABLE','reason':'Kayıtlı GNN çıktısı bulunamadı veya hash uyuşmadı.','rows':[]}
    blocks=[]
    for part in pd.read_csv(path,chunksize=20000):
        chosen=part[(part.drug_id==parent)&(part.model=='A1P1')&(part.protocol=='primary')]
        if len(chosen):blocks.append(chosen)
    if not blocks:return {'status':'NOT_AVAILABLE','reason':'Bu ana ilaç için kayıtlı A1P1 OOF kapsamı yok.','rows':[]}
    data=pd.concat(blocks).sort_values('score_observed_record_proxy',ascending=False)
    if data[['drug_id','class_id','outer_fold']].duplicated().any():raise ValueError('GNN_KEY_CONFLICT')
    return {'status':'AVAILABLE_RECORDED_OOF','parent_id':parent,'fold':int(data.outer_fold.iloc[0]),
        'model_version':str(data.model_version.iloc[0]),'targets':len(data),
        'rows':data[['class_id','score_observed_record_proxy','model_job_key']].to_dict('records')}
