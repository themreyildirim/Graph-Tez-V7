"""Read-only frozen predictions/SHAP, separately versioned user PDF reference.

No model imports, training, prediction, attribution computation, network or OCR.
Offsets refer to unnormalised PyMuPDF text in each physical page, Python [start,end).
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
Q = ROOT/'reports/qa/WP13/WP13_EXTERNAL_REFERENCE_COMPARISON_v1'
F = ROOT/'reports/figures/WP13/WP13_EXTERNAL_REFERENCE_COMPARISON_v1'
P = ROOT/'reports/qa/WP13/tedizolid_B1_external_v1'
S = ROOT/'reports/qa/WP13/tedizolid_B1_SHAP_v1'
PDF = Path('C:/Users/emrey/Downloads/sivextro-200-mg-enjeksiyonluk-cozelti-10a1e-kub.pdf')
PRED_HASH = '301a116e8f7de4c40c3d10fbbd2e4a122689f8319d82f36eb6183f4b8b0de2f1'
SHAP_HASH = 'db756d0a8a34de7be962e2dacde7be399b6b10bb868cb35798ab4be76ec8a0c1'

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    p = Path(p)
    if (p.name.startswith('.') and p.name != '.gitignore') or p.suffix.lower() in ('.env', '.pem', '.key'):
        raise ValueError('PRIVATE_FILE_EXCLUDED')
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(65536), b''): h.update(b)
    return h.hexdigest()
def dump(p, obj):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
def verify_pins(pins):
    for p, h in pins.items():
        if sha(ROOT/p) != h: raise ValueError('IMMUTABLE_HASH_MISMATCH: '+p)
def verify_locks():
    if sha(P/'prediction_lock.json') != PRED_HASH: raise ValueError('PREDICTION_LOCK_MISMATCH_STOP')
    if sha(S/'explanation_lock.json') != SHAP_HASH: raise ValueError('SHAP_LOCK_MISMATCH_STOP')
    pred, exp = read(P/'prediction_lock.json'), read(S/'explanation_lock.json')
    for pins in [pred['input_and_models_sha256'], pred['outputs_sha256'], exp['source_pins'], exp['outputs_sha256']]: verify_pins(pins)
    assert sha(P/'precommit_manifest.json') == pred['precommit_sha256']
    assert sha(S/'pre_explanation_manifest.json') == exp['pre_explanation_sha256']
    common = pd.read_csv(P/'common201_scores.csv', float_precision='round_trip')
    selected = read(S/'selected_PT_names.json')
    assert list(common.head(10).class_id) == [r['class_id'] for r in selected]
    pairs, vals = read(S/'pair_additivity.json'), read(S/'local_feature_SHAP.json')
    assert len(pairs) == 50 and len(vals) == 300 and len(common) == 201
    return pred, exp

def init_extract():
    if Q.exists(): raise RuntimeError('VERSION_EXISTS_NO_OVERWRITE')
    pred, exp = verify_locks()  # This precedes opening the reference PDF.
    if not PDF.is_file(): raise FileNotFoundError('USER_PDF_MISSING_STOP')
    prior = read(S/'prior_pins.json')
    prior.update(read(S/'evidence_manifest.json'))
    prior[(S/'evidence_manifest.json').relative_to(ROOT).as_posix()] = sha(S/'evidence_manifest.json')
    prior['apps/drug_safety_explorer_FINAL_v2.py'] = sha(ROOT/'apps/drug_safety_explorer_FINAL_v2.py')
    prior.pop('run_status.md', None)
    verify_pins(prior)
    Q.mkdir(parents=True); F.mkdir(parents=True)
    dump(Q/'prior_pins.json', prior)
    (Q/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
    dump(Q/'before_reference_checks.json', {'verified_utc': now(), 'prediction_lock_sha256': PRED_HASH,
        'explanation_lock_sha256': SHAP_HASH, 'protected_files': len(prior), 'common_PT':201,
        'selected_PT':10,'model_PT_explanations':50,'SHAP_values':300,
        'prediction_created_utc':pred['created_utc'],'explanation_created_utc':exp['created_utc'],
        'timing_scope':'Recorded timestamps plus source hashes; not an independent trusted timestamp service.',
        'status':'PASS_BEFORE_REFERENCE_OPEN','new_model_calls':0})
    source = Q/'reference'; source.mkdir()
    copy = source/PDF.name
    shutil.copyfile(PDF, copy)  # Explicitly authorised versioned reference copy, never move.
    assert sha(PDF) == sha(copy)
    from wp12_pilot import get_engine
    engine = get_engine(); pages = []
    with engine.open(str(copy)) as doc:
        if doc.needs_pass: raise ValueError('ENCRYPTED_STOP')
        meta = {'document_id':'sha256:'+sha(copy), 'raw_sha256':sha(copy), 'source_filename':PDF.name,
            'user_provided':True, 'source_receipt_utc':now(),'copied_bytes':copy.stat().st_size,
            'page_count':len(doc),'pdf_metadata':doc.metadata,'extractor':'PyMuPDF',
            'extractor_version':engine.VersionBind,'sort':False,'flags':int(engine.TEXTFLAGS_TEXT),
            'OCR':False,'currentness':'NOT_VERIFIED','publisher_authenticity':'NOT_VERIFIED',
            'reference_only':True,'model_input':False}
        for i,page in enumerate(doc):
            text = page.get_text('text', sort=False, flags=engine.TEXTFLAGS_TEXT)
            pages.append({'physical_page':i+1,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                          'image_count':len(page.get_images()),'status':'TEXT_AVAILABLE' if text.strip() else 'NO_TEXT_OCR_NOT_RUN'})
    dump(Q/'document_metadata.json',meta); dump(Q/'pages.json',pages)
    (Q/'all_physical_pages.txt').write_text('\n\n'.join(f"=== PHYSICAL PAGE {p['physical_page']} ===\n{p['text']}" for p in pages),encoding='utf-8')
    dump(Q/'extraction_complete.json',{'created_utc':now(),'pages':len(pages),'OCR':False,
        'no_reference_before_checks':True,'prior_blindness':'STRICT_ANALYST_BLINDNESS_COMPROMISED_PRESERVED'})
    print(json.dumps({'locks':'PASS','protected':len(prior),'pdf_sha256':meta['raw_sha256'],'pages':len(pages),'characters':[len(p['text']) for p in pages]},ensure_ascii=False))

def quote(page, text, kind, scope, start=None):
    pages = read(Q/'pages.json'); raw = pages[page-1]['text']
    if start is None:
        if raw.count(text) != 1: raise ValueError('NONUNIQUE_QUOTE: '+text)
        start = raw.index(text)
    end = start+len(text)
    assert raw[start:end] == text
    doc = read(Q/'document_metadata.json')['document_id']
    return {'quote_id':f'SIVEXTRO-v1-p{page:02d}-{start}-{end}', 'document_id':doc,
            'physical_page':page,'char_start':start,'char_end':end,'quote_exact':text,
            'quote_sha256':hashlib.sha256(text.encode()).hexdigest(),'statement_kind':kind,'scope':scope,
            'offset_unit':'Python Unicode characters; [start,end); raw physical page text',
            'human_review':'PENDING'}

def section_quote(page, begin, end, kind, scope):
    raw=read(Q/'pages.json')[page-1]['text']; a=raw.index(begin); b=raw.index(end,a)
    return quote(page,raw[a:b],kind,scope,a)

def extract_reference_terms():
    """Geometry + explicit layout review of table 1, not keyword clinical extraction."""
    from wp12_pilot import get_engine
    engine=get_engine(); terms=[]; seen=set()
    with engine.open(str(Q/'reference'/PDF.name)) as doc:
        for page in (6,7,8):
            raw=read(Q/'pages.json')[page-1]['text']
            for block in doc[page-1].get_text('dict',sort=False,flags=engine.TEXTFLAGS_TEXT)['blocks']:
                for line in block.get('lines',[]):
                    x,y,_,_=line['bbox']; text=''.join(s['text'] for s in line['spans']).strip()
                    if not (x>205 and text and (page==7 and y<770 or page==6 and 539<y<770 or page==8 and y<215)): continue
                    if text=='kontrolü': continue  # continuation of the preceding cell, kept in its quote below
                    if text=='Yetersiz diabetes mellitus':
                        text='Yetersiz diabetes mellitus \nkontrolü'
                    # Anchor complete table cell lines, not substrings such as Prürit/Prüritik.
                    anchor='\n'+text+' \n'
                    if raw.count(anchor)!=1: raise ValueError('NONUNIQUE_CELL_LINE: '+text)
                    q=quote(page,text,'adverse_reaction_table','PRODUCT_POOLED_ORAL_IV',raw.index(anchor)+1)
                    term=' '.join(text.split())
                    assert term not in seen; seen.add(term)
                    terms.append({'reference_term_id':f'ADR-{len(terms)+1:03d}','term_tr':term,
                        'frequency':'Yaygın' if x<300 else 'Yaygın olmayan',
                        'frequency_basis':'Table 1 column geometry, visually checked physical pp6-8',
                        'frequency_range':'≥1/100 ila <1/10' if x<300 else '≥1/1.000 ila <1/100',
                        'source_bbox':list(line['bbox']),'scope':'PRODUCT_POOLED_ORAL_IV',
                        'section':'4.8 Table 1','quote':q,'human_review':'PENDING'})
    return terms

def contexts():
    spec=[
      (1,'1. BEŞERİ','4.  KLİNİK','product_identity','PRODUCT'),
      (2,'4.3. Kontrendikasyonlar','4.4.','contraindication','CONTRAINDICATION_NOT_REACTION'),
      (2,'Nötropeni hastaları:','Mitokondriyal','warning','ANIMAL_AND_POPULATION_LIMITATION'),
      (2,'Mitokondriyal işlev','Miyelosupresyon:','warning','CLASS_OTHER_MEMBER'),
      (2,'Miyelosupresyon:','Oksazolidinon sınıfının','warning','DRUG_DIRECT_VOLUNTEER'),
      (3,'başka bir üyesiyle','Periferik nöropati','warning','CLASS_OTHER_MEMBER_CONTINUED_FROM_PAGE2'),
      (3,'Periferik nöropati','Laktik asidoz:','warning','CLASS_OTHER_MEMBER_AND_6DAY_NOT_REPORTED'),
      (3,'Laktik asidoz:','Aşırı duyarlılık reaksiyonları:','warning','CLASS_OTHER_MEMBER_AND_6DAY_NOT_REPORTED'),
      (3,'Aşırı duyarlılık reaksiyonları:','Clostridium difficile ilişkili diyare:','warning','CROSS_HYPERSENSITIVITY_CAUTION'),
      (3,'Clostridium difficile ilişkili diyare:','Monoamin oksidaz inhibisyonu:','warning','DRUG_DIRECT_WITH_CLASS_CONTEXT'),
      (3,'Serotonin sendromu:','SIVEXTRO’nun seçici','warning','CLASS_OTHER_MEMBER_INTERACTION'),
      (6,'4.8. İstenmeyen etkiler','Tablo 1','adverse_reaction_summary','PRODUCT_POOLED_ORAL_IV'),
      (8,'4.9 Doz aşımı','5. FARMAKOLOJİK','overdose','OVERDOSE_EXCLUDED_FROM_ADR_TABLE'),
      (8,'Etki mekanizması','Direnç','identity_prodrug','PRODRUG_NOT_MODEL_EXPLANATION'),
      (10,'Genel Özellikler','Emilim:','identity_prodrug','PRODRUG_NOT_MODEL_INPUT'),
      (13,'5.3 Klinik öncesi','Tedizolid fosfat, maksimum','preclinical','ANIMAL_AND_IN_VITRO_EXCLUDED'),
      (15,'8. RUHSAT NUMARALARI','10. KÜB’ÜN','document_version','DOCUMENT_METADATA'),
    ]
    result=[section_quote(*s) for s in spec]
    pages=read(Q/'pages.json')
    for page in (6,7,8):
        raw=pages[page-1]['text']
        a=raw.index('4.8. İstenmeyen etkiler') if page==6 else raw.index('\n')+1
        b=raw.index('4.9 Doz aşımı') if page==8 else len(raw)
        result.append(quote(page,raw[a:b],'complete_4.8_section_page','PRODUCT_POOLED_ORAL_IV',a))
    return result

# Explicit bilingual analyst-review candidates. No external terminology dictionary was
# downloaded; no entry is expert-approved. Term relation is kept distinct from scope.
# Tuple = target CUI, source cell, relation, scientific justification.
TABLE_MAP=[
 ('C0011991','Diyare','SYNONYM_CANDIDATE','Diyare/diarrhoea çeviri adayı; ishal editoryal adı.'),
 ('C0015230','Döküntü','TRANSLATION_CANDIDATE','Nitelemesiz döküntü/rash çeviri adayı.'),
 ('C0042963','Kusma','TRANSLATION_CANDIDATE','Kusma/vomiting çeviri adayı.'),
 ('C0000737','Karın ağrısı','TRANSLATION_CANDIDATE','Karın ağrısı/abdominal pain; üst karın ayrı hücre.'),
 ('C0687713','Karın ağrısı','TARGET_BROADER_CANDIDATE','Gastrointestinal pain daha geniş olası kavram; abdominal pain ile birleştirilmedi.'),
 ('C0020517','İlaca aşırı duyarlılık','TARGET_BROADER_CANDIDATE','Hypersensitivity nitelemesizdir; kaynak özellikle ilaca aşırı duyarlılıktır.'),
 ('C0033774','Prürit','SYNONYM_CANDIDATE','Prürit/pruritus çeviri adayı; genel/alerjik/genital alt türleri ayrı.'),
 ('C0042109','Ürtiker','TRANSLATION_CANDIDATE','Ürtiker/urticaria çeviri adayı.'),
 ('C0033774','Genel prürit','SOURCE_NARROWER_CANDIDATE','Genelleşmiş nitelemesi vardır; nitelemesiz prürit ile frekansı birleştirilmez.'),
 ('C0033774','Alerjik prürit','SOURCE_NARROWER_CANDIDATE','Alerjik nitelemesi kaynakta korunur.'),
 ('C0015967','Pireksi','RELATED_DISTINCT','Ateş/pireksi ile ölçülmüş body temperature increased otomatik eşdeğer sayılmaz.'),
 ('C1257843','Klostridiyum difisil kolit','RELATED_DISTINCT','Etken temelli kolit ve psödomembranöz kolit farklı tanımlardır.'),
 ('C0018681','Baş ağrısı','TRANSLATION_CANDIDATE','Baş ağrısı/headache çeviri adayı.'),
 ('C0012833','Baş dönmesi','TRANSLATION_CANDIDATE','Baş dönmesi/dizziness çeviri adayı; vertigo ile birleştirilmedi.'),
 ('C0013395','Dispepsi','TRANSLATION_CANDIDATE','Dispepsi/dyspepsia çeviri adayı.'),
 ('C0017178','Karın ağrısı','TARGET_BROADER_CANDIDATE','Gastrointestinal disorder daha geniştir; bağımsız aynı olay kanıtı değil.'),
 ('C0006840','Oral kandidiyaz','SOURCE_NARROWER_CANDIDATE','Candida infection daha geniş; oral alt tür ayrı.'),
 ('C0006840','Vulvovajinal kandidiyaz','SOURCE_NARROWER_CANDIDATE','Candida infection daha geniş; vulvovajinal alt tür ayrı.'),
 ('C2830004','Uyku hali','TRANSLATION_CANDIDATE','Uyku hali/somnolence çeviri adayı.'),
 ('C0003862','Artralji','TRANSLATION_CANDIDATE','Artralji/arthralgia çeviri adayı.'),
 ('C0404521','Vulvovajinal mikotik enfeksiyon','SOURCE_NARROWER_CANDIDATE','Vaginal infection daha geniş ve farklı anatomik kapsamlıdır.'),
 ('C0016204','Flatulans','TRANSLATION_CANDIDATE','Flatulans/flatulence çeviri adayı.'),
 ('C0004093','Halsizlik','SYNONYM_CANDIDATE','Asthenia/halsizlik adayı; fatigue/malaise otomatik eşdeğer değil.'),
 ('C0917801','Uykusuzluk','TRANSLATION_CANDIDATE','Uykusuzluk/insomnia çeviri adayı.'),
 ('C0009806','Kabızlık','TRANSLATION_CANDIDATE','Kabızlık/constipation çeviri adayı.'),
 ('C0234215','Uzuvlarda rahatsızlık','SOURCE_NARROWER_CANDIDATE','Discomfort daha geniş, anatomik koşul korunur.'),
 ('C0013378','Disguzi','TRANSLATION_CANDIDATE','Disguzi/dysgeusia çeviri adayı.'),
 ('C0030554','Parestezi','TRANSLATION_CANDIDATE','Parestezi/paraesthesia çeviri adayı.'),
 ('C0231218','Halsizlik','RELATED_DISTINCT','Malaise ile halsizlik belirsiz; asthenia ile birleştirilmez.'),
 ('C0020458','Hiperhidroz','TRANSLATION_CANDIDATE','Hiperhidroz/hyperhidrosis çeviri adayı.'),
 ('C0015672','Halsizlik','RELATED_DISTINCT','Fatigue ile halsizlik belirsiz; asthenia ile birleştirilmez.'),
 ('C0085593','Ürperti','SYNONYM_CANDIDATE','Ürperti/chills çeviri adayı.'),
 ('C0151904','Transaminaz artışı','TARGET_NARROWER_CANDIDATE','AST adı verilmemiş; genel transaminaz artışından AST özgüllüğü çıkarılmaz.'),
 ('C0043352','Ağız kuruluğu','TRANSLATION_CANDIDATE','Ağız kuruluğu/dry mouth çeviri adayı.'),
 ('C0009319','Klostridiyum difisil kolit','SOURCE_NARROWER_CANDIDATE','Colitis daha geniştir; etken özgüllüğü korunur.'),
 ('C0020580','Hipoestezi','TRANSLATION_CANDIDATE','Hipoestezi/hypoaesthesia çeviri adayı.'),
 ('C0031542','İnfüzyon bölgesinde flebit','SOURCE_NARROWER_CANDIDATE','Phlebitis daha geniş; uygulama bölgesi korunur.'),
 ('C0003467','Anksiyete','TRANSLATION_CANDIDATE','Anksiyete/anxiety çeviri adayı.'),
 ('C0010200','Öksürük','TRANSLATION_CANDIDATE','Öksürük/cough çeviri adayı.'),
 ('C0006849','Oral kandidiyaz','TRANSLATION_CANDIDATE','Oral kandidiyaz/oral candidiasis çeviri adayı.'),
 ('C0700345','Vulvovajinal kandidiyaz','TRANSLATION_CANDIDATE','Vulvovajinal kandidiyaz çeviri adayı.'),
 ('C1609512','Vulvovajinal mikotik enfeksiyon','TRANSLATION_CANDIDATE','Vulvovajinal mycotic infection çeviri adayı.'),
 ('C0016382','Kızarma','TRANSLATION_CANDIDATE','Kızarma/flushing çeviri adayı; sıcak basması ayrı hücre.'),
 ('C0151905','Transaminaz artışı','TARGET_NARROWER_CANDIDATE','ALT adı verilmemiş; genel transaminaz artışından ALT özgüllüğü çıkarılmaz.'),
 ('C0037763','Kas spazmı','TRANSLATION_CANDIDATE','Kas spazmı/muscle spasms çeviri adayı.'),
 ('C0344232','Bulanık görme','TRANSLATION_CANDIDATE','Bulanık görme/vision blurred çeviri adayı.'),
 ('C0040822','Titreme','TRANSLATION_CANDIDATE','Titreme/tremor çeviri adayı.'),
 ('C0013604','Periferik ödem','SOURCE_NARROWER_CANDIDATE','Oedema daha geniş; periferik niteleme korunur.'),
 ('C3665347','Bulanık görme','TARGET_BROADER_CANDIDATE','Visual impairment daha geniş, bulanık görme ile birleştirilmedi.'),
 ('C0232492','Üst karın ağrısı','TRANSLATION_CANDIDATE','Upper abdominal pain ve abdominal pain ayrı hedefler.'),
 ('C0033777','Vulvovajinal prürit','SOURCE_NARROWER_CANDIDATE','Genital pruritus daha geniş anatomik kavram.'),
 ('C0423791','Makülopapüler döküntü','TRANSLATION_CANDIDATE','Maculo-papular rash çeviri adayı; genel rash ayrı.'),
 ('C0004604','Sırt ağrısı','TRANSLATION_CANDIDATE','Sırt ağrısı/back pain çeviri adayı.'),
 ('C0232487','Karında rahatsızlık hissi','TRANSLATION_CANDIDATE','Abdominal discomfort çeviri adayı; ağrı ile birleştirilmedi.'),
 ('C0020461','Hiperkalemi','TRANSLATION_CANDIDATE','Hiperkalemi/hyperkalaemia çeviri adayı.'),
 ('C0026946','Fungal enfeksiyon','TRANSLATION_CANDIDATE','Fungal infection çeviri adayı.'),
 ('C0151828','İnfüzyon bölgesinde ağrı','RELATED_DISTINCT','Injection site ve infusion site otomatik aynı hedef değildir.'),
 ('C0238106','Klostridiyum difisil kolit','TRANSLATION_CANDIDATE','Clostridium difficile colitis çeviri adayı.'),
 ('C0011630','Dermatofitoz','SOURCE_NARROWER_CANDIDATE','Fungal skin infection daha geniş, dermatofitoz alt tür adayı.'),
 ('C0041912','Solunum yolu enfeksiyonu','TARGET_NARROWER_CANDIDATE','Kaynak üst solunum yolu demiyor; upper özgüllüğü çıkarılamaz.'),
 ('C0085649','Periferik ödem','TRANSLATION_CANDIDATE','Periferik ödem/oedema peripheral çeviri adayı.'),
 ('C0023530','Akyuvar sayımında düşüş','RELATED_DISTINCT','Laboratuvar WBC azalması ile leukopenia tanısı aynı sayılmaz.'),
]

def compare():
    verify_locks(); verify_pins(read(Q/'prior_pins.json'))
    if (Q/'comparison201.csv').exists(): raise RuntimeError('COMPARISON_EXISTS_NO_OVERWRITE')
    terms=extract_reference_terms(); ctx=contexts()
    dump(Q/'reference_terms.json',terms); dump(Q/'context_quotes.json',ctx)
    pd.DataFrame([{**{k:v for k,v in t.items() if k not in ('quote','source_bbox')},**t['quote']} for t in terms]).to_csv(Q/'reference_terms.csv',index=False,encoding='utf-8-sig')
    byterm={t['term_tr']:t for t in terms}; mappings=[]
    for cui,term,relation,why in TABLE_MAP:
        t=byterm[term]
        mappings.append({'class_id':cui,'source_term':term,'reference_term_id':t['reference_term_id'],
            'relation':relation,'scope':t['scope'],'frequency':t['frequency'],'quote_id':t['quote']['quote_id'],
            'physical_page':t['quote']['physical_page'],'rationale_tr':why,'status':'PROVISIONAL',
            'human_review':'PENDING','terminology_basis':'Explicit bilingual analyst candidate; no licensed MedDRA TR or independent expert confirmation',
            'source_channel':'4.8_TABLE'})
    # These are not product-specific tabulated ADRs. No counting as direct support.
    classq=next(c for c in ctx if c['scope']=='CLASS_OTHER_MEMBER_CONTINUED_FROM_PAGE2')
    for cui,term in [('C0040034','trombositopeni'),('C0023530','lökopeni'),('C0030312','pansitopeni'),('C0002871','anemi')]:
        assert term in classq['quote_exact']
        mappings.append({'class_id':cui,'source_term':term,'reference_term_id':None,'relation':'TRANSLATION_CANDIDATE',
            'scope':classq['scope'],'frequency':'NOT_STATED','quote_id':classq['quote_id'],'physical_page':3,
            'rationale_tr':'4.4: oksazolidinon sınıfının başka üyesi; doğrudan SIVEXTRO 4.8 bildirimi değildir.',
            'status':'PROVISIONAL','human_review':'PENDING','terminology_basis':'Analyst translation; expert pending','source_channel':'4.4_CLASS_WARNING'})
    volunteer=next(c for c in ctx if c['scope']=='DRUG_DIRECT_VOLUNTEER')
    for cui,term,rel,why in [('C0392386','platelet düşüşü','SYNONYM_CANDIDATE','Platelet count decreased adayı; trombositopeni tanısı değil.'),
        ('C0162119','hemoglobin düşüşü','TRANSLATION_CANDIDATE','Haemoglobin decreased adayı; anemi tanısı değil.'),
        ('C0027947','nötrofil düşüşü','RELATED_DISTINCT','Nötrofil sayımı azalması ile neutropenia tanısı aynı sayılmaz.'),
        ('C0040034','platelet düşüşü','RELATED_DISTINCT','Trombositopeni hedefi ile laboratuvar azalması aynı sayılmaz.')]:
        assert term in volunteer['quote_exact']
        mappings.append({'class_id':cui,'source_term':term,'reference_term_id':None,'relation':rel,'scope':'DRUG_DIRECT_VOLUNTEER',
            'frequency':'NOT_STATED','quote_id':volunteer['quote_id'],'physical_page':2,'rationale_tr':why,
            'status':'PROVISIONAL','human_review':'PENDING','terminology_basis':'Analyst candidate; expert pending','source_channel':'4.4_VOLUNTEER_WARNING'})
    dump(Q/'crosswalk_candidates.json',mappings);pd.DataFrame(mappings).to_csv(Q/'crosswalk_candidates.csv',index=False,encoding='utf-8-sig')
    dictionary=pd.read_csv(ROOT/'reports/qa/WP03/pt_concept_dictionary.csv').groupby('meddra_cui').term.agg(lambda v:' | '.join(sorted(set(v)))).to_dict()
    names={r['class_id']:r['term_tr_editorial'] for r in read(S/'selected_PT_names.json')}
    common=pd.read_csv(P/'common201_scores.csv',float_precision='round_trip');rows=[]
    for record in common.to_dict('records'):
        cui=record['class_id']; matches=[m for m in mappings if m['class_id']==cui]
        table=[m for m in matches if m['source_channel']=='4.8_TABLE']
        literal=[m for m in table if m['relation'] in ('TRANSLATION_CANDIDATE','SYNONYM_CANDIDATE')]
        if literal: state='TABLE_TRANSLATION_CANDIDATE'
        elif table: state='TABLE_RELATED_NOT_EQUIVALENT'
        elif any(m['source_channel']=='4.4_CLASS_WARNING' for m in matches): state='CLASS_WARNING_ONLY'
        elif matches: state='DRUG_WARNING_ONLY'
        else: state='NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE'
        rows.append({**record,'term_en':dictionary.get(cui,cui),'term_tr_editorial':names.get(cui,''),
            'reference_status':state,'mapping_status':'PROVISIONAL' if matches else 'UNMAPPED',
            'human_review':'PENDING','source_terms':' | '.join(dict.fromkeys(m['source_term'] for m in matches)),
            'source_pages':' | '.join(str(x) for x in sorted(set(m['physical_page'] for m in matches))),
            'quote_ids':' | '.join(dict.fromkeys(m['quote_id'] for m in matches)),
            'relations':' | '.join(dict.fromkeys(m['relation'] for m in matches)),
            'source_scopes':' | '.join(dict.fromkeys(m['scope'] for m in matches)),
            'frequencies':' | '.join(dict.fromkeys(m['frequency'] for m in matches)),
            'expert_confirmed_equivalent':False,'reference_absence_is_negative':False})
    frame=pd.DataFrame(rows);frame.to_csv(Q/'comparison201.csv',index=False,encoding='utf-8-sig',float_format='%.17g');dump(Q/'comparison201.json',rows)
    frame.head(10).to_csv(Q/'top10_comparison.csv',index=False,encoding='utf-8-sig',float_format='%.17g');dump(Q/'top10_comparison.json',rows[:10])
    top=set(common.head(10).class_id); allc=set(common.class_id);term_rows=[]
    for term in terms:
        ms=[m for m in mappings if m['reference_term_id']==term['reference_term_id']]
        ids=list(dict.fromkeys(m['class_id'] for m in ms))
        term_rows.append({'reference_term_id':term['reference_term_id'],'term_tr':term['term_tr'],
            'frequency':term['frequency'],'quote_id':term['quote']['quote_id'],'physical_page':term['quote']['physical_page'],
            'candidate_PT_CUIs':' | '.join(ids),'candidate_PT_in_common201':bool(set(ids)&allc),
            'has_candidate_top10':bool(set(ids)&top),'relation_types':' | '.join(dict.fromkeys(m['relation'] for m in ms)),
            'human_review':'PENDING','unmapped_is_not_model_error':True})
    pd.DataFrame(term_rows).to_csv(Q/'all_reference_terms_target_coverage.csv',index=False,encoding='utf-8-sig');dump(Q/'all_reference_terms_target_coverage.json',term_rows)
    pd.DataFrame([t for t in term_rows if not t['has_candidate_top10']]).to_csv(Q/'reference_terms_outside_top10.csv',index=False,encoding='utf-8-sig')
    dump(Q/'product_identity_and_limitations.json',{
      'product':'SIVEXTRO 200 mg enjeksiyonluk çözelti hazırlamak için liyofilize toz',
      'document_type':'Türkçe KÜB','route':'intravenous infusion','ingredient':'tedizolid fosfat',
      'dose':'200 mg/flakon; sulandırıldıktan sonra 50 mg/mL','model_input':'DB14569 active TEDIZOLID',
      'reference_product_relation':'Phosphate prodrug → active tedizolid supported pp8,10; not identical molecular representation or formulation.',
      'DB09042_prediction':'NOT_RUN','clinical_product_equivalence':'NOT_ESTABLISHED',
      'reference_ADR_evidence':'4.8 pooled phase3 oral and/or IV; 662 recipients; not an IV-only incidence table',
      'currentness':'NOT_VERIFIED','initial_authorization':'27.03.2019; not KÜB revision date',
      'KUB_revision_date':'NOT_STATED (heading blank on physical page15)',
      'pdf_metadata_dates':'creation 2019-04-04 / modification 2019-04-07; not independent evidence of clinical currentness',
      'all_matching':'Analyst PROVISIONAL; independent bilingual terminology/clinical expert PENDING',
      'strict_analyst_blindness':'COMPROMISED_FROM_PREPARATION_SEARCH_SNIPPETS_PRESERVED',
      'experiment':'EXPLORATORY_EXTERNAL_LABEL_ISOLATED; one compound, one product reference, no generalization performance',
      'metrics':'NOT_CALCULABLE: no expert-confirmed equivalence subset, no true-negative reference, product/input mismatch; no AP/AUROC/precision/success percent',
      'predictions_first10_selection':'Locked score rank, reference-independent; not independent of predictions',
      'training':False,'new_prediction_forward':False,'new_SHAP':False,'API':False,'OCR':False})
    verify_locks();verify_pins(read(Q/'prior_pins.json'))
    dump(Q/'comparison_summary.json',{'created_utc':now(),'table_cells':len(terms),'unique_source_terms':len(set(t['term_tr'] for t in terms)),
        'table_frequency_counts':pd.Series([t['frequency'] for t in terms]).value_counts().to_dict(),
        'common201_status_counts':frame.reference_status.value_counts().to_dict(),
        'top10_status_counts':frame.head(10).reference_status.value_counts().to_dict(),
        'all_crosswalk_rows':len(mappings),'expert_confirmed_mappings':0,'human_review':'PENDING',
        'reference_terms_without_top10_candidate':sum(not t['has_candidate_top10'] for t in term_rows),
        'performance_metrics':'NOT_CALCULABLE','clinical_success_rate':None,
        'no_new_model_execution':True,'original_locks_preserved':True})
    print(json.dumps(read(Q/'comparison_summary.json'),ensure_ascii=False))

if __name__=='__main__':
    if sys.argv[1:] == ['--extract-once']: init_extract()
    elif sys.argv[1:] == ['--compare-once']: compare()
    else: raise SystemExit('Use --extract-once; no model execution commands exist.')
