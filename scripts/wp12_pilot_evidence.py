"""Kaynak sayfa dilimleri + ayrı pilot bağlam incelemesi;etiket/özellik üretmez."""
import copy,csv,json,re
import pandas as pd
from wp12_pilot import ROOT,QA,FILES,read,preserve
from wp12_prepare import save,sha
from wp12_document_contract import quote_id_for,text_digest,validate_bundle


def make_plan():
    rows=[]
    def add(key,file,page,start,end,scope,purpose,qualifier='',context=None):
        rows.append({'key':key,'filename':file,'physical_page':page,'start_anchor':start,'end_anchor':end,'attribution_scope':scope,'purpose':purpose,'qualifier':qualifier,'context_key':context})
    e,d=FILES
    add('E_identity',e,1,'The name of your medicine','Erythromycin Tablets are used to prevent','product_identity','identity')
    add('E_ingredients',e,6,'What Erythromycin Tablets contain','What Erythromycin Tablets look like','product_identity','identity')
    add('E_formulation',e,6,'What Erythromycin Tablets look like','Marketing Authorisation Holder and Manufacturer','product_identity','formulation')
    add('E_manufacturer',e,6,'Marketing Authorisation Holder and Manufacturer','This leaflet was last revised','product_identity','manufacturer')
    add('E_revision',e,6,'This leaflet was last revised','To request a copy','document_metadata','revision')
    add('E_excipient',e,4,None,'Driving and using machines','excipient_specific','warning','Named dyes;do not assign automatically to active erythromycin')
    add('E_overdose',e,4,'An overdose of Erythromycin Tablets could cause','If you forget to take','overdose_context','warning','Overdose statement;not ordinary-use ADR list')
    add('E_adverse_p4',e,4,'4.  Possible side effects',None,'product_specific','adverse_section','Section4 starts here and continues on physical5')
    add('E_adverse_p5',e,5,None,'5.  How to store','product_specific','adverse_section','Continuation of section4;retain reporting/frequency context',context='E_adverse_p4')
    add('E_unknown_frequency',e,5,'Other side effects of Erythromycin Tablets include-:','Additional side effects in children','product_specific','adverse_context','Frequency not known;no numeric probability',context='E_adverse_p5')
    add('E_warnings',e,2,'Warnings and precautions','Children  ','product_specific','warning')
    add('E_pregnancy',e,3,'Pregnancy and breast-feeding','Erythromycin Tablets contain Sunset','product_specific','warning','Preserve inconsistent-study qualification;historical leaflet')
    add('D_identity',d,1,'DESCRIPTION','CLINICAL PHARMACOLOGY','product_identity','identity','Capsules with monohydrate equivalent to parent doxycycline')
    add('D_formulation',d,8,'HOW SUPPLIED','STORE AT','product_identity','formulation')
    add('D_manufacturer',d,9,'Manufactured by:','L70564','product_identity','manufacturer')
    add('D_revision',d,9,'Rev: 02/2022','Reference ID:','document_metadata','revision')
    add('D_latest_notice',d,10,'This label may not be the latest approved by FDA.',None,'document_metadata','currency_notice','No external URL followed;current-label status not verified')
    add('D_adverse_all',d,7,'ADVERSE REACTIONS','OVERDOSAGE','mixed_drug_intro_and_class_list','adverse_section','Whole section retained;not a uniform direct-doxycycline list')
    add('D_direct_intro',d,7,'Due to oral doxycycline','The following adverse reactions','drug_direct','adverse_context','Retain infrequent qualifier;no numerical frequency')
    add('D_class_intro',d,7,'The following adverse reactions','Gastrointestinal:','class_level','scope_anchor','Governs following ADR subsections;not drug-specific proof')
    for key,start,end in [('GI','Gastrointestinal:','Skin:'),('skin','Skin:','Renal Toxicity:'),('renal','Renal Toxicity:','Hypersensitivity Reactions:'),('hypersensitivity','Hypersensitivity Reactions:','Blood:'),('blood','Blood:','Other:'),('other','Other:','When given over prolonged'),('thyroid','When given over prolonged','OVERDOSAGE')]:
        add('D_class_'+key,d,7,start,end,'class_level','adverse_context','Inherited tetracycline-class scope;not independent direct-doxycycline evidence',context='D_class_intro')
    add('D_warnings_all',d,4,'WARNINGS','PRECAUTIONS','mixed_warning_scopes','warning_section')
    add('D_teeth',d,4,'The use of drugs of the tetracycline class','Clostridium difficile associated diarrhea','class_including_doxycycline','warning','Including-doxycycline class statement;development/population conditions retained')
    add('D_CDAD',d,4,'Clostridium difficile associated diarrhea','C. difficile produces toxins','broad_antibacterial_including_doxycycline','warning','Nearly all antibacterial agents including doxycycline capsules')
    add('D_IH',d,4,'Intracranial hypertension (IH','All tetracyclines form a stable calcium complex','class_including_doxycycline','warning','Including doxycycline capsules;population/risk qualifiers retained')
    add('D_BUN_exception',d,4,'The antianabolic action of the tetracyclines','Photosensitivity manifested','class_statement_with_doxycycline_exception','warning','Retain BOTH sentences;doxycycline exception in renal-impairment context;not positive doxycycline-BUN label')
    add('D_photosensitivity',d,4,'Photosensitivity manifested','PRECAUTIONS','class_level','warning')
    add('D_general',d,5,'General:','Information for Patients:','broad_antibacterial_product_context','warning')
    add('D_patient_context',d,5,'All patients taking doxycycline should be advised:','Patients should be counseled','mixed_drug_and_class_advice','warning_section','Do not convert counseling text to observed ADR incidence')
    add('D_direct_sun',d,5,'–to avoid excessive sunlight','–to drink fluids','drug_direct_advice','warning','Advice context;not an observed event count')
    add('D_direct_esophagus',d,5,'–to drink fluids liberally','–that the absorption of tetracyclines','drug_direct_advice','warning','Risk/counseling phrasing retained')
    add('D_direct_candidiasis',d,5,'–that the use of doxycycline might increase','Diarrhea is a common problem','drug_direct','warning','Might qualifier retained')
    add('D_tetracycline_methoxyflurane',d,6,'The concurrent use of tetracycline and methoxyflurane','Concurrent use of tetracycline may','other_named_drug_tetracycline','interaction','Named tetracycline;not silently relabeled doxycycline')
    add('D_related_animals',d,6,'Long-term studies in animals','Doxycycline administered orally','related_drug_animal_invitro_context','warning','Doxycycline studies not conducted;related oxytetracycline/minocycline evidence not direct human-doxycycline ADR')
    add('D_pregnancy',d,6,'Pregnancy:','Labor and Delivery:','drug_specific_historical_study_context','warning','Study limitations and unconfirmed/qualified associations retained')
    add('D_nursing',d,6,'Nursing Mothers:','Pediatric Use:','class_including_doxycycline_unknown','warning','Extent/longer-term effects unknown;not a positive label')
    add('D_pediatric',d,6,'Pediatric Use:','Reference ID:','class_including_doxycycline','warning')
    add('D_animal_thyroid',d,9,'ANIMAL PHARMACOLOGY AND ANIMAL TOXICOLOGY','REFERENCES','animal_class_context','warning','Animal species and named agents retained;not a human clinical ADR label')
    return rows


def span(text,start,end):
    a=0 if start is None else text.find(start)
    if a<0 or (start is not None and text.count(start)!=1):raise ValueError('Missing/ambiguous start anchor:'+str(start))
    b=len(text) if end is None else text.find(end,a+len(start or ''))
    if not a<b<=len(text):raise ValueError('Missing end anchor:'+str(end))
    return a,b


def main():
    if (QA/'source_evidence_bundle.json').exists():raise RuntimeError('Pilot evidence v1 exists')
    preserve();bundle=copy.deepcopy(read(QA/'document_bundle.json'));plan=make_plan();save(QA/'quote_selection_plan.json',plan)
    docnames={d['document_id']:d['receipts'][0]['original_filename'] for d in bundle['documents']};pages={(docnames[p['document_id']],p['page_number']):p for p in bundle['pages']}
    for p in bundle['pages']:
        # Visible printed labels are distinct from PDF logical labels and physical number.
        text=p['text'];m=re.search(r'^Page (\d+) of (\d+)\s*$',text[:100],re.M)
        if m:p['printed_page_label']=f'Page {m.group(1)} of {m.group(2)}'
        elif 'Signature Page 1 of 1' in text:p['printed_page_label']='Signature Page 1 of 1'
    ids={};annotations=[]
    for row in plan:
        p=pages[(row['filename'],row['physical_page'])];a,b=span(p['text'],row['start_anchor'],row['end_anchor']);text=p['text'][a:b];qsha=text_digest(text);qid=quote_id_for(p['page_id'],a,b,qsha)
        if qid in ids.values():raise ValueError('Duplicate quote selector')
        ids[row['key']]=qid;bundle['quotes'].append({'quote_id':qid,'document_id':p['document_id'],'extraction_run_id':p['extraction_run_id'],'page_id':p['page_id'],'page_number':p['page_number'],'char_start':a,'char_end':b,'quote':text,'quote_sha256':qsha,'claim_kind':'verbatim_source_quote'})
        annotations.append({**row,'quote_id':qid,'review_status':'PILOT_SOURCE_CONTEXT_REVIEW_USER_REVIEW_PENDING','review_method':'source reading;no local LLM or classifier','context_quote_ids':[],'is_training_label':False,'is_model_input':False})
    for a in annotations:
        if a['context_key']:a['context_quote_ids']=[ids[a['context_key']]]
    validate_bundle(bundle);save(QA/'source_evidence_bundle.json',bundle);save(QA/'source_context_annotations.json',annotations)
    frames=[]
    for q in bundle['quotes']:
        a=next(a for a in annotations if a['quote_id']==q['quote_id'])
        frames.append({'selection_key':a['key'],'filename':a['filename'],'quote_id':q['quote_id'],'page_number':q['page_number'],'char_start':q['char_start'],'char_end':q['char_end'],'attribution_scope':a['attribution_scope'],'purpose':a['purpose'],'qualifier':a['qualifier'],'quote':q['quote']})
    pd.DataFrame(frames).to_csv(QA/'source_quotes.csv',index=False,encoding='utf-8-sig')
    registry=pd.read_csv(ROOT/'reports/qa/WP02/drug_registry.csv');salts=pd.read_csv(ROOT/'reports/qa/WP02/salt_parent_links.csv');structure=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv');identity=[]
    for name,drug,cid in [(FILES[0],'DB00199',12560),(FILES[1],'DB00254',54671203)]:
        r=registry[registry.id.eq(drug)].iloc[0];s=structure[structure.id.eq(drug)].iloc[0];assert r.primary_count==1 and int(s.bridge_cid)==int(s.cid)==cid and str(cid) in json.loads(r.pubchem_cid)
        identity.append({'filename':name,'document_id':next(d['document_id'] for d in bundle['documents'] if d['receipts'][0]['original_filename']==name),'DrugBank_parent_id':drug,'existing_parent_name':r['name'],'existing_CID':cid,'existing_parent_formula':s.xml_formula,'existing_parent_inchikey':s.raw_inchikey,'mapping_level':'active_ingredient_parent','mapping_status':'SUPPORTED_BY_PDF_INGREDIENT_AND_EXISTING_REGISTRY','product_or_dose_equivalence':'NOT_ESTABLISHED_NOT_USED_IN_MODEL','PDF_formulation':'250 mg enteric-coated tablet' if drug=='DB00199' else 'oral capsules 50/75/100/150 mg parent-equivalent;doxycycline monohydrate','PDF_named_salt_or_hydrate':'no specific salt/ester named beyond erythromycin' if drug=='DB00199' else 'doxycycline monohydrate','existing_salt_link_id':None if drug=='DB00199' else 'DBSALT001956','identity_quote_ids':[ids['E_identity'],ids['E_ingredients'],ids['E_formulation']] if drug=='DB00199' else [ids['D_identity'],ids['D_formulation']]})
    assert ((salts.salt_id=='DBSALT001956')&(salts.parent_id=='DB00254')&(salts.salt_name=='Doxycycline monohydrate')).sum()==1
    save(QA/'drug_identity_review.json',identity);salts[salts.parent_id.isin(['DB00199','DB00254'])].to_csv(QA/'existing_parent_salt_links_review.csv',index=False,encoding='utf-8-sig')
    review=[]
    for meta in read(QA/'source_document_metadata.json'):
        e=meta['filename']==FILES[0];review.append({'filename':meta['filename'],'document_id':meta['document_id'],'document_type_content_verified':'patient_information_leaflet' if e else 'prescribing_information_label_with_package_image_and_signature','content_revision':'December 2025' if e else '02/2022','revision_quote_id':ids['E_revision' if e else 'D_revision'],'identity_quote_id':ids['E_identity' if e else 'D_identity'],'manufacturer_quote_id':ids['E_manufacturer' if e else 'D_manufacturer'],'marketing_holder_or_manufacturer':'Sovereign Medical / Waymade Plc' if e else 'Chartwell Pharmaceuticals LLC / Chartwell RX LLC','trade_brand_name_status':'generic product name;corporate name is not silently treated as a distinct drug brand','latest_label_verified':False,'currency_notice_quote_id':None if e else ids['D_latest_notice'],'PDF_CreationDate':meta['metadata'].get('creationDate'),'PDF_ModDate':meta['metadata'].get('modDate'),'metadata_dates_are_not_document_revision':True,'publisher_authenticity_or_digital_signature_validation':False})
    save(QA/'document_metadata_content_review.json',review)
    inventory=pd.read_csv(QA/'page_inventory.csv');coverage=[]
    for row in inventory.to_dict('records'):
        n=row['physical_page_number'];ispack=row['filename']==FILES[1] and n==10;row['text_coverage_status']='SPARSE_TEXT_SUBSTANTIVE_IMAGE_NO_OCR' if ispack else 'TEXT_LAYER_PRESENT';row['image_content_not_transcribed']=bool(row['image_objects']>0);row['visual_review']='all-page contact sheet;priority pages full-size';coverage.append(row)
    pd.DataFrame(coverage).to_csv(QA/'page_text_coverage_review.csv',index=False,encoding='utf-8-sig')
    save(QA/'visual_content_notes.json',[{'filename':FILES[1],'physical_page':10,'status':'IMAGE_PACKAGE_LABEL_PRESERVED_NO_OCR','observation':'Package-label image visually present;only 154 text-layer codepoints (footer).No image text fabricated as text-layer quote.','render':'reports/figures/WP12/pilot_v1/pages/doxycycline/page-10.png'},{'filename':FILES[1],'physical_page':11,'status':'SIGNATURE_REPRESENTATION_PAGE_PRESERVED','observation':'Electronic-signature representation;not cryptographic validation.','render':'reports/figures/WP12/pilot_v1/pages/doxycycline/page-11.png'}])
    inputs=['reports/qa/WP02/drug_registry.csv','reports/qa/WP02/salt_parent_links.csv','reports/qa/WP04/structure_sources.csv','docs/plan/WP12_DOCUMENT_DATA_CONTRACT_v1.md','scripts/wp12_document_contract.py']
    save(QA/'identity_input_manifest.json',{p:sha(ROOT/p) for p in inputs});preserve()
    save(QA/'evidence_complete.json',{'documents':2,'physical_pages':17,'source_quotes':len(bundle['quotes']),'context_annotations':len(annotations),'training_labels_generated':0,'model_inputs_generated':0,'clinical_adjudication':False,'LLM':False,'OCR':False,'old_files_preserved':preserve()})
    print(read(QA/'evidence_complete.json'))


if __name__=='__main__':main()
