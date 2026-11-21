"""WP12 hazırlığı:eski sonuçları korur;PDF okumaz veya çıkarım başlatmaz."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP12/preparation_v1'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def preserve():
    previous=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    bad=[p for p,h in previous.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(bad)
    return len(previous)


def init():
    if (QA/'prior_artifacts_sha256.json').exists():raise RuntimeError('Preparation v1 already initialized')
    QA.mkdir(parents=True,exist_ok=True);previous={}
    for folder in ['docs','reports','notebooks','scripts','tests','configs','models']:
        for path in sorted((ROOT/folder).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or QA in path.parents or path.name.startswith(('wp12_','test_wp12_')):continue
            previous[path.relative_to(ROOT).as_posix()]=sha(path)
    for name in ['AGENTS.md','README.md']:previous[name]=sha(ROOT/name)
    save(QA/'prior_artifacts_sha256.json',previous)
    (QA/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
    # WP11 kapanış manifestinin mutable status alanını doğru tarihsel arşivle doğrula.
    manifest=ROOT/'reports/qa/WP11/final_closure_v1/evidence_manifest.json';checks=json.loads(manifest.read_text(encoding='utf-8'))
    assert all(sha(QA/'run_status_before.md' if p=='run_status.md' else ROOT/p)==h for p,h in checks.items())
    save(QA/'user_source_decision.json',{'date':'2026-11-08','source_decision':'ONLY_USER_SUPPLIED_PROSPECTUS_PDFS','PDFs_provided_in_current_request':0,'automatic_search':False,'download':False,'document_extraction':False,'Ollama_installation_or_model_download':False,'training':False,'stop_state':'AWAITING_USER_PDFS','previous_WP11_evidence_entries_verified':len(checks)})
    print('Prior files protected:',len(previous),';WP11 closure evidence verified:',len(checks),';awaiting user PDFs')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['init','preserve']);a=p.parse_args()
    if a.action=='init':init()
    else:print(preserve())
