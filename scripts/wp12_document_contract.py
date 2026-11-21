"""WP12 saf veri sözleşmesi. PDF/LLM/ağ/dosya erişimi içermez."""
import datetime,hashlib,json,re

VERSION='WP12-document-bundle-v1'
DIGEST=r'^[0-9a-f]{64}$'


def sha256_bytes(value):
    if not isinstance(value,bytes):raise ValueError('Exact bytes required')
    return hashlib.sha256(value).hexdigest()


def text_digest(text):
    if not isinstance(text,str):raise ValueError('Unicode page text required')
    return sha256_bytes(text.encode('utf-8'))


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def stable_id(prefix,*parts):return prefix+sha256_bytes(canonical(parts).encode('utf-8'))


def document_id_for(raw_sha256):
    if not isinstance(raw_sha256,str) or not re.fullmatch(DIGEST,raw_sha256):raise ValueError('Lowercase SHA-256 required')
    return 'sha256:'+raw_sha256


def run_id_for(document_id,extractor_name,extractor_version,options):return stable_id('run:',document_id,extractor_name,extractor_version,options)
def page_id_for(document_id,run_id,page_index,text_sha256):return stable_id('page:',document_id,run_id,page_index,text_sha256)
def quote_id_for(page_id,start,end,quote_sha256):return stable_id('quote:',page_id,start,end,quote_sha256)


def empty_bundle():return {'schema_version':VERSION,'data_status':'awaiting_user_pdfs','documents':[],'extraction_runs':[],'pages':[],'quotes':[]}


def schema():
    def obj(properties,required=None):return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}
    def string(**kw):return {'type':'string',**kw}
    def integer(**kw):return {'type':'integer',**kw}
    nonempty=string(minLength=1);digest=string(pattern=DIGEST);docid=string(pattern=r'^sha256:[0-9a-f]{64}$')
    nullable={'type':['string','null']}
    definitions={
        'receipt':obj({'receipt_id':nonempty,'source_kind':{'const':'user_provided_pdf'},'receipt_kind':{'enum':['user_attachment','explicit_user_file']},'reference':nonempty,'original_filename':nonempty,'supplied_at':nonempty}),
        'document':obj({'document_id':docid,'raw_sha256':digest,'raw_size_bytes':integer(minimum=1),'mime_type':{'const':'application/pdf'},'declared_version':nullable,'page_count':{'type':['integer','null'],'minimum':1},'receipts':{'type':'array','items':{'$ref':'#/$defs/receipt'},'minItems':1}}),
        'run':obj({'extraction_run_id':string(pattern=r'^run:[0-9a-f]{64}$'),'document_id':docid,'extractor_name':nonempty,'extractor_version':nonempty,'extractor_options':{'type':'object','additionalProperties':True},'created_at':nonempty,'status':{'enum':['partial','complete']}}),
        'page':obj({'page_id':string(pattern=r'^page:[0-9a-f]{64}$'),'document_id':docid,'extraction_run_id':string(pattern=r'^run:[0-9a-f]{64}$'),'page_index':integer(minimum=0),'page_number':integer(minimum=1),'printed_page_label':nullable,'text':string(),'text_sha256':digest,'text_length_codepoints':integer(minimum=0),'text_status':{'enum':['text_extracted','no_text']}}),
        'quote':obj({'quote_id':string(pattern=r'^quote:[0-9a-f]{64}$'),'document_id':docid,'extraction_run_id':string(pattern=r'^run:[0-9a-f]{64}$'),'page_id':string(pattern=r'^page:[0-9a-f]{64}$'),'page_number':integer(minimum=1),'char_start':integer(minimum=0),'char_end':integer(minimum=1),'quote':string(minLength=1),'quote_sha256':digest,'claim_kind':{'const':'verbatim_source_quote'}})}
    result=obj({'schema_version':{'const':VERSION},'data_status':{'enum':['awaiting_user_pdfs','technical_test_fixture','user_pdf_records']},'documents':{'type':'array','items':{'$ref':'#/$defs/document'}},'extraction_runs':{'type':'array','items':{'$ref':'#/$defs/run'}},'pages':{'type':'array','items':{'$ref':'#/$defs/page'}},'quotes':{'type':'array','items':{'$ref':'#/$defs/quote'}}})
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:graph-tez:wp12:document-bundle:v1','title':'WP12 user-supplied PDF provenance bundle',**result,'$defs':definitions}


def _shape(value,rule,root,location='$'):
    if '$ref' in rule:return _shape(value,root['$defs'][rule['$ref'].split('/')[-1]],root,location)
    expected=rule.get('type');types=expected if isinstance(expected,list) else [expected] if expected else []
    valid={'object':type(value)is dict,'array':type(value)is list,'string':type(value)is str,'integer':type(value)is int,'null':value is None}
    if types and not any(valid[t] for t in types):raise ValueError(location+':type')
    if 'const' in rule and value!=rule['const']:raise ValueError(location+':const')
    if 'enum' in rule and value not in rule['enum']:raise ValueError(location+':enum')
    if isinstance(value,dict):
        props=rule.get('properties',{})
        if set(rule.get('required',[]))-set(value):raise ValueError(location+':missing field')
        if rule.get('additionalProperties',True) is False and set(value)-set(props):raise ValueError(location+':unknown field')
        for key,item in value.items():
            if key in props:_shape(item,props[key],root,location+'.'+key)
    if isinstance(value,list):
        if len(value)<rule.get('minItems',0):raise ValueError(location+':minItems')
        for i,item in enumerate(value):_shape(item,rule['items'],root,location+f'[{i}]')
    if isinstance(value,str):
        if len(value)<rule.get('minLength',0) or ('pattern' in rule and not re.fullmatch(rule['pattern'],value)):raise ValueError(location+':string constraint')
    if type(value)is int and value<rule.get('minimum',value):raise ValueError(location+':minimum')


def _timestamp(value):
    try:parsed=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:raise ValueError('Timestamp must be ISO-8601') from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:raise ValueError('Timezone required')


def _index(rows,key):
    result={}
    for row in rows:
        if row[key] in result:raise ValueError('Duplicate '+key)
        result[row[key]]=row
    return result


def validate_bundle(bundle,*,allow_test_fixtures=False):
    """Yalnız supplied JSON'u doğrular;ham PDF'nin gerçekliğini/çıkarımını doğrulamaz."""
    shape=schema();_shape(bundle,shape,shape);canonical(bundle)
    status=bundle['data_status']
    if status=='technical_test_fixture' and not allow_test_fixtures:raise ValueError('Technical fixtures cannot enter production registry')
    if status=='awaiting_user_pdfs' and any(bundle[k] for k in ['documents','extraction_runs','pages','quotes']):raise ValueError('Waiting state must have zero records')
    if status=='user_pdf_records' and not bundle['documents']:raise ValueError('Real-record state requires user documents')
    docs=_index(bundle['documents'],'document_id');runs=_index(bundle['extraction_runs'],'extraction_run_id');pages=_index(bundle['pages'],'page_id');quotes=_index(bundle['quotes'],'quote_id');receipts=set();page_positions=set()
    for d in docs.values():
        if d['document_id']!=document_id_for(d['raw_sha256']):raise ValueError('Document content identity mismatch')
        for r in d['receipts']:
            if r['receipt_id'] in receipts:raise ValueError('Duplicate receipt identity')
            receipts.add(r['receipt_id']);_timestamp(r['supplied_at'])
            name=r['original_filename']
            if not name.lower().endswith('.pdf') or '/' in name or '\\' in name:raise ValueError('Receipt requires original PDF basename')
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://',r['reference']):raise ValueError('URL fetch is outside user-file intake')
    for r in runs.values():
        if r['document_id'] not in docs:raise ValueError('Run document foreign key')
        if docs[r['document_id']]['page_count'] is None:raise ValueError('Run requires inspected physical page count')
        if r['extraction_run_id']!=run_id_for(r['document_id'],r['extractor_name'],r['extractor_version'],r['extractor_options']):raise ValueError('Extractor/config identity mismatch')
        _timestamp(r['created_at'])
    for p in pages.values():
        r=runs.get(p['extraction_run_id'])
        if r is None or p['document_id']!=r['document_id']:raise ValueError('Page document/run mismatch')
        if p['page_number']!=p['page_index']+1:raise ValueError('Physical page index/number mismatch')
        if p['page_index']>=docs[p['document_id']]['page_count']:raise ValueError('Page outside declared physical document')
        position=(p['extraction_run_id'],p['page_index'])
        if position in page_positions:raise ValueError('Duplicate physical page in run')
        page_positions.add(position)
        if p['text_length_codepoints']!=len(p['text']) or p['text_sha256']!=text_digest(p['text']):raise ValueError('Stored exact page text hash/length mismatch')
        if (p['text_status']=='no_text')!=(len(p['text'])==0):raise ValueError('No-text status mismatch')
        if p['page_id']!=page_id_for(p['document_id'],p['extraction_run_id'],p['page_index'],p['text_sha256']):raise ValueError('Page identity mismatch')
    for r in runs.values():
        present={p['page_index'] for p in pages.values() if p['extraction_run_id']==r['extraction_run_id']}
        if r['status']=='complete' and present!=set(range(docs[r['document_id']]['page_count'])):raise ValueError('Complete run must preserve every physical page,including no-text pages')
    for q in quotes.values():
        p=pages.get(q['page_id'])
        if p is None or any(q[k]!=p[k] for k in ['document_id','extraction_run_id','page_number']):raise ValueError('Quote source page mismatch')
        start,end=q['char_start'],q['char_end']
        if not 0<=start<end<=len(p['text']):raise ValueError('Invalid half-open Unicode codepoint span')
        if q['quote']!=p['text'][start:end] or q['quote_sha256']!=text_digest(q['quote']):raise ValueError('Quote is not exact source slice')
        if q['quote_id']!=quote_id_for(q['page_id'],start,end,q['quote_sha256']):raise ValueError('Quote identity mismatch')
    return {'documents':len(docs),'extraction_runs':len(runs),'pages':len(pages),'quotes':len(quotes),'data_status':status}


class AwaitingUserPDFError(RuntimeError):pass


def extract_user_pdfs(*args,**kwargs):
    """Hazırlık kapısı:parser bağlı değil;dosya açmadan durur."""
    raise AwaitingUserPDFError('AWAITING_USER_PDFS:real extraction is not implemented in preparation-v1')
