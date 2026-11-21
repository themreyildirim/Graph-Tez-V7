"""İzinli iki kullanıcı PDF'si: salt okunur PyMuPDF pilotu; model/LLM yok."""
from pathlib import Path
import argparse,csv,datetime,json,sys
from wp12_prepare import sha,save
from wp12_document_contract import (VERSION,document_id_for,run_id_for,page_id_for,quote_id_for,text_digest,validate_bundle)
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP12/pilot_v1'
SOURCE=ROOT/'data/user_pdfs'
FILES=('pil.502.pdf','050641Orig1s032lbl.pdf')


def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(path):return json.loads(path.read_text(encoding='utf-8'))


def preserve():
    m=read(QA/'prior_artifacts_sha256.json');bad=[p for p,h in m.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(bad)
    return len(m)


def init():
    if (QA/'prior_artifacts_sha256.json').exists():raise RuntimeError('Pilot v1 already initialized')
    # Her iki dosya bulunmadan kaynak açılmaz;alternatif kaynak araması yok.
    if not all((SOURCE/f).is_file() for f in FILES):raise FileNotFoundError('Selected PDFs missing;STOP;no download')
    QA.mkdir(parents=True,exist_ok=True);previous={}
    for folder in ['docs','reports','notebooks','scripts','tests','configs','models']:
        for p in sorted((ROOT/folder).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or QA in p.parents or p.name.startswith(('wp12_pilot','test_wp12_pilot')):continue
            previous[p.relative_to(ROOT).as_posix()]=sha(p)
    for name in ['AGENTS.md','README.md']:previous[name]=sha(ROOT/name)
    for name in FILES:p=SOURCE/name;previous[p.relative_to(ROOT).as_posix()]=sha(p)
    save(QA/'prior_artifacts_sha256.json',previous);(QA/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
    receipts=[]
    for name in FILES:
        p=SOURCE/name
        receipts.append({'filename':name,'absolute_user_path':str(p.resolve()),'raw_sha256':sha(p),'bytes':p.stat().st_size,'user_provided_basis':'explicit user selection of these exact two local files in current request','receipt_observed_at':now(),'filesystem_mtime_is_not_publication_or_supply_date':True})
    save(QA/'user_source_receipts.json',{'authorization_date':'2026-11-08','records':receipts,'publisher_authenticity_verified':False,'downloaded':False,'LLM':False})
    print('Pilot sources verified;protected prior files',len(previous))


def get_engine():
    sys.path.insert(0,str(ROOT/'.deps/pymupdf'))
    import pymupdf
    return pymupdf


def extract():
    if (QA/'document_bundle.json').exists():raise RuntimeError('Pilot extraction already exists')
    preserve();engine=get_engine();bundle={'schema_version':VERSION,'data_status':'user_pdf_records','documents':[],'extraction_runs':[],'pages':[],'quotes':[]};audit=[];metadata=[]
    options={'output':'text','sort':False,'flags':int(engine.TEXTFLAGS_TEXT),'OCR':False,'text_normalization':'NONE','clip':'full_page_default'}
    save(QA/'extraction_policy_before_run.json',{'engine':'PyMuPDF','version':engine.VersionBind,'options':options,'sources':list(FILES),'all_physical_pages':True,'new_training':False,'LLM':False})
    folder=QA/'page_text';folder.mkdir(exist_ok=False)
    for name in FILES:
        path=SOURCE/name;digest=sha(path);docid=document_id_for(digest);runid=run_id_for(docid,'PyMuPDF',engine.VersionBind,options)
        with path.open('rb') as stream:header=stream.read(8)
        if not header.startswith(b'%PDF-'):raise ValueError('Selected file lacks PDF header')
        with engine.open(str(path)) as pdf:
            if not pdf.is_pdf or pdf.needs_pass:raise ValueError('Not PDF or encrypted;STOP no fallback')
            declared='December 2025' if name==FILES[0] else 'Rev. 02/2022'
            bundle['documents'].append({'document_id':docid,'raw_sha256':digest,'raw_size_bytes':path.stat().st_size,'mime_type':'application/pdf','declared_version':declared,'page_count':len(pdf),'receipts':[{'receipt_id':'user-selection:'+name,'source_kind':'user_provided_pdf','receipt_kind':'explicit_user_file','reference':str(path.resolve()),'original_filename':name,'supplied_at':read(QA/'user_source_receipts.json')['records'][FILES.index(name)]['receipt_observed_at']}]})
            bundle['extraction_runs'].append({'extraction_run_id':runid,'document_id':docid,'extractor_name':'PyMuPDF','extractor_version':engine.VersionBind,'extractor_options':options,'created_at':now(),'status':'complete'})
            metadata.append({'filename':name,'document_id':docid,'raw_sha256':digest,'page_count':len(pdf),'PDF_header':header.decode('ascii','replace'),'is_repaired':bool(pdf.is_repaired),'encrypted':bool(pdf.is_encrypted),'metadata':pdf.metadata,'page_labels_rules':pdf.get_page_labels(),'user_declared_version':declared,'document_type':'patient_information_leaflet' if name==FILES[0] else 'prescribing_information_label','type_and_version_status':'USER_DECLARED_PENDING_CONTENT_REVIEW'})
            for i in range(len(pdf)):
                page=pdf[i];text=page.get_text('text',sort=False,flags=options['flags']);th=text_digest(text);pid=page_id_for(docid,runid,i,th)
                bundle['pages'].append({'page_id':pid,'document_id':docid,'extraction_run_id':runid,'page_index':i,'page_number':i+1,'printed_page_label':None,'text':text,'text_sha256':th,'text_length_codepoints':len(text),'text_status':'text_extracted' if text else 'no_text'})
                # bytes write preserves CR/LF exactly;no platform newline translation.
                out=folder/(name+f'.page_{i+1:03}.txt');out.write_bytes(text.encode('utf-8'))
                imageinfo=page.get_image_info();area=max(float(page.rect.width*page.rect.height),1.)
                image_area_sum=sum(max(0,float(b['bbox'][2]-b['bbox'][0]))*max(0,float(b['bbox'][3]-b['bbox'][1])) for b in imageinfo)
                audit.append({'filename':name,'document_id':docid,'page_id':pid,'physical_page_number':i+1,'chars':len(text),'text_sha256':th,'width_points':float(page.rect.width),'height_points':float(page.rect.height),'image_objects':len(imageinfo),'image_area_sum_over_page_not_union':image_area_sum/area,'blank_text':len(text)==0,'replacement_char_count':text.count('\ufffd'),'text_file':out.relative_to(ROOT).as_posix()})
        if sha(path)!=digest:raise AssertionError('Source PDF changed during read')
    validate_bundle(bundle);save(QA/'document_bundle.json',bundle);save(QA/'source_document_metadata.json',metadata)
    with (QA/'page_inventory.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(audit[0]));w.writeheader();w.writerows(audit)
    save(QA/'extraction_complete.json',{'documents':len(bundle['documents']),'pages':len(bundle['pages']),'empty_text_pages':sum(not p['text'] for p in bundle['pages']),'quotes':0,'engine_version':engine.VersionBind,'source_hashes_unchanged':True,'old_artifacts_preserved':preserve(),'LLM':False})
    print(read(QA/'extraction_complete.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['init','extract','preserve']);a=p.parse_args()
    if a.action=='init':init()
    elif a.action=='extract':extract()
    else:print(preserve())
