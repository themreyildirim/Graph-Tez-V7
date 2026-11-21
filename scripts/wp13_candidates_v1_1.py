"""WP13 v1.1 finite, auditable lexical candidates; not a clinical NLP/MedDRA mapper."""
import re
import pandas as pd
import wp13_core as core
VERSION='WP13-candidate-lexicon-v1.1'
QA=core.ROOT/'reports/qa/WP13/v1_1'

# Exact English anchors only. Turkish display labels are editorial glosses, not PT identities.
LEX={
'E_adverse_p4': [('difficulty breathing','Nefes almada güçlük'),('fainting','Bayılma'),('swelling of the face, lips or throat','Yüz, dudak veya boğaz şişmesi'),('skin rashes','Deri döküntüleri'),('large fluid-filled blisters','Büyük sıvı dolu kabarcıklar'),('sores and ulcers','Yaralar ve ülserler'),('ulcers in the mouth and throat','Ağız ve boğaz ülserleri')],
'E_adverse_p5':[('diarrhoea','İshal'),('Stevens Johnson syndrome','Stevens–Johnson sendromu'),('toxic epidermal necrolysis','Toksik epidermal nekroliz'),('erythema multiforme','Eritema multiforme'),('liver or gall-bladder problems','Karaciğer veya safra kesesi sorunları'),('torsades de pointes','Torsades de pointes'),('cardiac arrest','Kalp durması'),('exanthematous pustulosis','Ekzantematöz püstüloz')],
'E_unknown_frequency':[('feeling sick','Bulantı'),('being sick','Kusma'),('eosinophilia','Eozinofili'),('stomach pains','Karın ağrısı'),('pancreatitis','Pankreatit'),('tinnitus','Kulak çınlaması'),('reversible loss of hearing','Geri dönüşlü işitme kaybı'),('chest pain','Göğüs ağrısı'),('fever','Ateş'),('abnormal heart rhythms','Anormal kalp ritimleri'),('confusion','Konfüzyon'),('Anorexia','İştahsızlık'),('seizures','Nöbet'),('vertigo','Vertigo'),('hallucinations','Halüsinasyon'),('malaise','Genel kırgınlık'),('interstitial nephritis','İnterstisyel nefrit'),('low blood pressure','Düşük tansiyon'),('visual impairment/blurred vision','Görme bozukluğu/bulanık görme')],
'D_direct_intro':[('diarrhea','İshal')],
'D_class_GI':[('Anorexia','İştahsızlık'),('nausea','Bulantı'),('vomiting','Kusma'),('diarrhea','İshal'),('glossitis','Glossit'),('dysphagia','Yutma güçlüğü'),('enterocolitis','Enterokolit'),('inflammatory lesions','İnflamatuvar lezyonlar'),('pancreatitis','Pankreatit'),('Hepatotoxicity','Hepatotoksisite'),('esophagitis','Özofajit'),('esophageal ulcerations','Özofagus ülserasyonları')],
'D_class_skin':[('Maculopapular','Makülopapüler döküntü (kaynak listesi)'),('erythematous rashes','Eritematöz döküntüler'),('Stevens-Johnson syndrome','Stevens–Johnson sendromu'),('toxic epidermal necrolysis','Toksik epidermal nekroliz'),('erythema multiforme','Eritema multiforme'),('Exfoliative dermatitis','Eksfolyatif dermatit'),('Photosensitivity','Fotosensitivite')],
'D_class_renal':[('Rise in BUN','BUN artışı')],
'D_class_hypersensitivity':[('Urticaria','Ürtiker'),('angioneurotic edema','Anjiyonörotik ödem'),('anaphylaxis','Anafilaksi'),('anaphylactoid purpura','Anafilaktoid purpura'),('serum sickness','Serum hastalığı'),('pericarditis','Perikardit'),('exacerbation of systemic lupus erythematosus','Sistemik lupus eritematozus alevlenmesi')],
'D_class_blood':[('Hemolytic anemia','Hemolitik anemi'),('thrombocytopenia','Trombositopeni'),('neutropenia','Nötropeni'),('eosinophilia','Eozinofili')],
'D_class_other':[('Intracranial hypertension','İntrakraniyal hipertansiyon')],
'D_class_thyroid':[('brown-black microscopic discoloration','Tiroidde kahverengi-siyah mikroskobik renk değişimi')]
}

def pattern(term):return re.compile(re.escape(term).replace(r'\ ',r'\s+'),re.I)

def known(doc):
    if doc.get('mode')!='VERIFIED_DEMO':raise ValueError('VERIFIED_SOURCE_REQUIRED')
    annotations=core.read(core.pinned('reports/qa/WP12/pilot_v1/source_context_annotations.json'))
    by_id={q['quote_id']:q for q in doc['quotes']}
    quotes={a['key']:by_id[a['quote_id']] for a in annotations if a['quote_id'] in by_id}
    rows=[]
    for key,terms in LEX.items():
        if key not in quotes:continue
        q=quotes[key]
        for anchor,label in terms:
            match=pattern(anchor).search(q['quote'])
            if not match:continue # Unparsed passage never becomes a fabricated candidate.
            freq='NOT_SPECIFIED';frequency_evidence=''
            if key=='E_unknown_frequency':freq='UNKNOWN';frequency_evidence='Not known (frequency cannot be estimated from the available data)'
            elif key=='E_adverse_p5' and anchor=='exanthematous pustulosis':
                freq='UNKNOWN';frequency_evidence='The frequency of this\nside effect is not known (cannot be estimated from the available data).'
            elif key=='D_direct_intro':freq='infrequent';frequency_evidence='infrequent'
            elif key=='D_class_GI' and anchor in ['esophagitis','esophageal ulcerations']:freq='Rare instances';frequency_evidence='Rare instances'
            elif key=='D_class_skin' and anchor=='Exfoliative dermatitis':freq='uncommon';frequency_evidence='uncommon'
            context=[]
            if key.startswith('D_class_'):context.append(quotes['D_class_intro'])
            if key=='D_class_renal':context.append(quotes['D_BUN_exception'])
            if key=='D_class_skin' and anchor=='Photosensitivity':context.append(quotes['D_photosensitivity'])
            if key in ['E_adverse_p5','E_unknown_frequency']:context.append(quotes['E_adverse_p4'])
            start=q['char_start']+match.start();end=q['char_start']+match.end()
            if freq=='UNKNOWN' and key=='E_adverse_p5':
                # Whitespace display difference only; require actual source phrase, not a guessed frequency.
                assert 'frequency of this' in q['quote'] and 'side effect is not known' in q['quote']
            elif frequency_evidence:assert frequency_evidence in q['quote']
            rows.append({'candidate_id':core.digest((doc['document_id']+key+str(start)+str(end)).encode()),
                'name_tr':label,'source_term':q['quote'][match.start():match.end()], 'frequency':freq,
                'frequency_source':frequency_evidence,'scope':q['scope'],'qualifier':q['qualifier'],
                'physical_page':q['page_number'],'quote_id':q['quote_id'],'quote_start':q['char_start'],'quote_end':q['char_end'],
                'term_start':start,'term_end':end,'quote_exact':q['quote'],
                'context_quotes':context,'document_id':doc['document_id'],'source_key':key,
                'status':'CANDIDATE_PENDING_HUMAN','method':VERSION,'MedDRA_mapping':'UNMAPPED',
                'condition_source':q['quote'],'is_independent_clinical_evidence':False})
    return rows

def experimental(doc):
    """Finite anchors inside explicit adverse-section pages only; no identity or scope assertion."""
    rows=[];seen=set()
    terms={anchor:label for group in LEX.values() for anchor,label in group}
    for p in doc['pages']:
        if p['status']!='TEXT_AVAILABLE':continue
        header=re.search(r'(?im)^\s*(?:4\.\s*)?(?:possible side effects|adverse reactions|olası yan etkiler)\s*$',p['text'])
        if not header:continue
        tail=p['text'][header.end():]
        boundary=re.search(r'(?im)^\s*(?:5\.\s|DOSAGE AND ADMINISTRATION\s*$|OVERDOSAGE\s*$)',tail)
        end=header.end()+(boundary.start() if boundary else len(tail))
        for term,label in terms.items():
            for m in pattern(term).finditer(p['text'],header.end(),end):
                key=(p['physical_page'],m.start(),m.end())
                if key in seen:continue
                seen.add(key);start=max(header.end(),m.start()-100);stop=min(end,m.end()+180);quote=p['text'][start:stop]
                rows.append({'candidate_id':core.digest((doc['document_id']+str(key)).encode()),'name_tr':label,
                    'source_term':m.group(),'frequency':'NOT_SPECIFIED','frequency_source':'',
                    'scope':'UNVERIFIED','qualifier':'Yerel sınırlı sözlük eşleşmesi; sıklık/kapsam belirlenmedi.',
                    'physical_page':p['physical_page'],'quote_id':'experimental:'+core.digest((doc['document_id']+str(key)+quote).encode()),
                    'quote_start':start,'quote_end':stop,'term_start':m.start(),'term_end':m.end(),'quote_exact':quote,
                    'context_quotes':[],'status':'EXPERIMENTAL_PENDING_HUMAN','method':VERSION,
                    'MedDRA_mapping':'UNMAPPED','document_id':doc['document_id'],'source_key':'EXPERIMENTAL',
                    'condition_source':quote,'is_independent_clinical_evidence':False})
    return rows

# Conservative, source-bound replay links. No match => NOT_AVAILABLE; not a semantic classifier.
LINKS={
'E_unknown_frequency':{'fever':('ateş','S04'),'chest pain':('göğüs ağrısı','S04'),
 'reversible loss of hearing':('işitme kaybı','S04'),'tinnitus':('tinnitus','S04'),
 'low blood pressure':('düşük tansiyon','S04'),'hallucinations':('halüsinasyon','S04')},
'E_adverse_p4':{'fainting':('bayılma','S04'),'difficulty breathing':('nefes almada zorluk','S04')},
'D_class_renal':{'Rise in BUN':('BUN','S07')}}

def explanation(candidate,filename):
    spec=LINKS.get(candidate['source_key'],{}).get(' '.join(candidate['source_term'].split()))
    if not spec:return []
    phrase,case=spec;rows=core.saved_explanations(filename);found=[]
    folder={'S04':'openai_S04_actual_review_v1','S07':'openai_S07_actual_review_v1'}[case]
    actual=core.read(core.pinned(f'reports/qa/WP12/{folder}/independent_review.json'))['parsed_json']['result']['items']
    doc_quotes={q['quote_id']:q for q in core.verified_document(filename)['quotes']}
    for r in rows:
        if r['scenario']!=case:continue
        original=actual[int(r['item'])-1]
        if original['explanation_tr']!=r['model_explanation_exact']:raise ValueError('SAVED_EXPLANATION_MISMATCH')
        raw_ids=original['evidence_ids']
        covered=any(qid in doc_quotes and doc_quotes[qid]['page_number']==candidate['physical_page']
                    and doc_quotes[qid]['char_start']<=candidate['term_start']<candidate['term_end']<=doc_quotes[qid]['char_end']
                    for qid in raw_ids)
        if covered and phrase.casefold() in r['model_explanation_exact'].casefold():
            found.append(r)
    return found

def gnn_named(doc):
    result=core.gnn(doc)
    if not result['rows']:return result
    extra=core.read(QA/'additional_source_pins.json')
    for name,digest in extra.items():
        if core.public_sha(core.ROOT/name)!=digest:raise ValueError('MODEL_PROVENANCE_INTEGRITY')
    manifest=core.read(core.ROOT/'reports/qa/WP10/training_v1/model_artifact_manifest.json')
    for job in {r['model_job_key'] for r in result['rows']}:
        for extension in ['json','npz']:
            name=f'models/WP10_factorial_training_v1/{job}.{extension}'
            if core.public_sha(core.ROOT/name)!=manifest[name]:raise ValueError('MODEL_ARTIFACT_INTEGRITY')
        meta=core.read(core.ROOT/f'models/WP10_factorial_training_v1/{job}.json')
        if meta['job_key']!=job or meta['model']!='A1P1' or meta['outer_fold']!=result['fold']:
            raise ValueError('MODEL_SCOPE_MISMATCH')
    result['provenance']='OOF/source hash + model metadata/NPZ manifest verified; no weights loaded for inference'
    path=core.ROOT/'reports/qa/WP03/pt_concept_dictionary.csv'
    pins=core.read(QA/'protected_prior_public_files.json')
    if core.public_sha(path)!=pins.get(path.relative_to(core.ROOT).as_posix()):raise ValueError('PT_DICTIONARY_INTEGRITY')
    table=pd.read_csv(path);names=table.groupby('meddra_cui')['term'].agg(lambda t:' | '.join(sorted(set(t)))).to_dict()
    for row in result['rows']:row['target_name']=names.get(row['class_id'],row['class_id'])
    return result
