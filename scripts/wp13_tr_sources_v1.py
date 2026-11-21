"""Two explicitly supplied Turkish PDFs only. Offline source spans, never model labels."""
from pathlib import Path
import json,re,hashlib
import wp13_core as core
ROOT=core.ROOT;Q=ROOT/'reports/qa/WP13/tr_source_v1'
FILES=['eritro-500-mg-film-tablet-8ccc-kt.pdf','monodoks-100-mg-kapsul-kub-07-11-2018.pdf']
EXPECTED=['289acdc2d85c283d5e94db955f40a0acd190d535e7e2c822a6c043165e835310','065f43273bc71165580f566f8cf78e52fb86f607c89923c42058ff86936c6387']
def norm(s):return ' '.join(s.split())
def locate(text,anchor,start=0):
    pattern=r'\s+'.join(re.escape(s) for s in anchor.split())
    m=re.search(pattern,text[start:])
    if not m:raise ValueError('ANCHOR_NOT_FOUND: '+anchor)
    return start+m.start(),start+m.end()
def quote(doc,page,start,end,kind,scope):
    text=doc['pages'][page-1]['text'];value=text[start:end]
    return {'document_id':doc['document_id'],'quote_id':'trquote:'+core.digest(f"{doc['document_id']}|{page}|{start}|{end}|{kind}|{scope}".encode()),
      'physical_page':page,'char_start':start,'char_end':end,'quote_exact':value,'quote_sha256':core.digest(value.encode()),'statement_kind':kind,'scope':scope}
def passage(doc,page,start_anchor,end_anchor=None,kind='warning',scope='product_specific'):
    t=doc['pages'][page-1]['text'];s,e=locate(t,start_anchor)
    if end_anchor:e=locate(t,end_anchor,e)[0]
    return quote(doc,page,s,e,kind,scope)
def build(index):
    name=FILES[index];data=(ROOT/'data/user_pdfs'/name).read_bytes()
    if core.digest(data)!=EXPECTED[index]:raise ValueError('SOURCE_HASH_MISMATCH')
    d=core.extract_pdf(data)
    if d['page_count']!=[8,13][index]:raise ValueError('PAGE_COUNT')
    identity=passage(d,1,'Etkin madde:','Yardımcı maddeler:',kind='identity')
    version=passage(d,[8,13][index],['Bu kullanma talimatı','10. KÜB’ÜN YENİLENME TARİHİ'][index],kind='version')
    old=core.verified_document(['pil.502.pdf','050641Orig1s032lbl.pdf'][index])['record']
    parent=['DB00199','DB00254'][index]
    if old['DrugBank_parent_id']!=parent:raise ValueError('PARENT_RECORD_MISMATCH')
    record={'filename':name,'language':'tr','source_contract':'WP13_TR_SOURCE_v1','document_type':['KT','KÜB'][index],
      'product':['ERİTRO 500 mg film tablet','MONODOKS 100 mg kapsül'][index],
      'active_parent_name':['eritromisin','doksisiklin'][index],'parent_id':parent,
      'salt':['eritromisin stearat','doksisiklin hiklat'][index],
      'composition':['500 mg eritromisine eşdeğer 750 mg eritromisin stearat / film tablet','100 mg doksisikline eşdeğer 115,414 mg doksisiklin hiklat / kapsül'][index],
      'identity_evidence':identity,'version_evidence':version,'currentness':'UNVERIFIED_CURRENTNESS',
      'document_revision_date':'NOT_AVAILABLE_EMPTY_FIELD','filename_date_hint':['NOT_AVAILABLE','07-11-2018_UNVERIFIED'][index],
      'English_product_equivalence':'NOT_ESTABLISHED','parent_mapping':'ACTIVE_INGREDIENT_RESEARCH_LINK_ONLY',
      'byte_size':len(data),'human_QA':'PENDING','clinical_validation':'NOT_ESTABLISHED'}
    from wp12_pilot import get_engine
    with get_engine().open(stream=data,filetype='pdf') as pdf:record['PDF_metadata']=pdf.metadata
    d.update(record=record,mode='TR_SOURCE_DEMO',parser={'engine':'PyMuPDF','version':get_engine().VersionBind,'get_text':'text,sort=False,flags=195'})
    rows=[];contexts=[identity,version]
    def add(block,term,freq,fq,scope=None,linked=(),note=''):
        a,b=locate(block['quote_exact'],term);scope=scope or block['scope']
        term_exact=block['quote_exact'][a:b]
        rows.append({'candidate_id':'trcandidate:'+core.digest((block['quote_id']+'|'+str(a)+'|'+str(b)+'|'+scope).encode()),
          'name_tr':norm(term_exact),'source_term':term_exact,'statement_kind':'adverse_candidate','scope':scope,
          'frequency_state':freq,'frequency_exact':fq['quote_exact'] if fq else 'Sıklık belirtilmemiş',
          'frequency_quote':fq,'source':block,'term_start':block['char_start']+a,'term_end':block['char_start']+b,
          'context_quotes':list(linked),'source_note':note,'status':'PENDING','MedDRA':'UNMAPPED'})
    if index==0:
        overdose=passage(d,6,'ERİTRO’nun aşırı dozu','ERİTRO’dan',kind='overdose');contexts.append(overdose)
        serious=passage(d,6,'Aşağıdakilerden','Bunların hepsi',kind='warning')
        freq=passage(d,7,'Bu çok ciddi yan etkilerin hepsi','Yan etkiler görülme',kind='frequency_definition')
        body=passage(d,6,'- Nefes darlığı','Bunların hepsi',kind='adverse_candidate')
        def bullets(block):
            parts=list(re.finditer(r'(?m)^-\s*\n',block['quote_exact']))
            for i,p in enumerate(parts):
                start=p.end();end=parts[i+1].start() if i+1<len(parts) else len(block['quote_exact'])
                term=block['quote_exact'][start:end].strip()
                add(block,term,'RARE_SOURCE_WORDING',freq,linked=[serious])
        bullets(body)
        unknown=passage(d,7,'Bilinmiyor: Eldeki veriler ile tahmin edilemiyor.',kind='frequency_definition')
        # Exact frequency sentence only, not the remaining page.
        ut=d['pages'][6]['text'];us,ue=locate(ut,'Bilinmiyor: Eldeki veriler ile tahmin edilemiyor.')
        unknown=quote(d,7,us,ue,'frequency_definition','product_specific')
        for page,start,end in [(7,'- Şiddetli ya da uzun süreli','END'),(8,'- Genelde kendini kötü','Eğer bu kullanma talimatında')]:
            t=d['pages'][page-1]['text'];s=locate(t,start)[0];e=len(t) if end=='END' else locate(t,end,s)[0]
            b=quote(d,page,s,e,'adverse_candidate','product_specific')
            parts=list(re.finditer(r'(?m)^-\s*\n',b['quote_exact']))
            for i,p in enumerate(parts):
                term=b['quote_exact'][p.end():parts[i+1].start() if i+1<len(parts) else len(b['quote_exact'])].strip()
                add(b,term,'UNKNOWN',unknown)
        contexts.extend([serious,freq,unknown])
    else:
        renal=passage(d,4,'Tetrasiklinlerin antianabolik etkisi','Bugüne kadar',scope='class_level')
        accumulation=passage(d,4,'Bugüne kadar yapılmış','Karaciğer yetmezliği:',scope='product_specific')
        photo=passage(d,5,'Tetrasiklin alanlarda bazen','Diğer antibiyotik',scope='class_level')
        direct=passage(d,6,'Doksisiklin alan hastalarda özofajit','Karaciğer ve böbrek',scope='drug_direct')
        animal=passage(d,8,'Hayvanlarda yapılan çalışmaların','Hamile kadınlarda',kind='animal_study',scope='class_level')
        preclinical=passage(d,11,'5.3 Klinik öncesi güvenlilik verileri',kind='animal_study',scope='class_level')
        preclinical_cont=passage(d,12,'iyotlu gıdalarla','6. FARMASÖTİK',kind='animal_study',scope='class_level')
        overdose=passage(d,10,'4.9 Doz aşımı ve tedavisi','5. FARMAKOLOJİK',kind='overdose')
        contexts.extend([renal,accumulation,photo,direct,animal,preclinical,preclinical_cont,overdose])
        specs=[
          (9,'Bilinmiyor: Süperenfeksiyonlar','Kan ve lenf','UNKNOWN','product_specific',
            ['Süperenfeksiyonlar','Kandidasis','glossit','stafilokoksik enterokolit','pseudomembranöz kolit','anogenital bölgede inflamatuvar lezyonlar','vajinit']),
          (9,'Bilinmiyor: Hemolitik anemi','Bağışıklık sistemi','UNKNOWN','product_specific',['Hemolitik anemi','trombositopeni','nötropeni','porfiri','eozinofili']),
          (9,'Bilinmiyor: Ürtiker','Endokrin hastalıklar','UNKNOWN','product_specific',['Ürtiker','anjiyonörotik ödem','anaflaksi','anaflaktoid purpura','sistemik lupus eritematozus eksaserbasyonları']),
          (9,'Bilinmiyor: Uzun süre','Sinir sistemi','UNKNOWN','class_level',['kahverengi-siyah mikroskopik renk bozuklukları']),
          (9,'Bilinmiyor: Baş ağrısı','Kulak ve iç','UNKNOWN','product_specific',['Baş ağrısı','fontanel kabarıklığı','iyi huylu kafa içi basıncı artışı']),
          (9,'Bilinmiyor: Tinnitus','Kardiyak hastalıklar','UNKNOWN','product_specific',['Tinnitus']),
          (9,'Bilinmiyor: Perikardit','Gastrointestinal hastalıklar','UNKNOWN','product_specific',['Perikardit']),
          (10,'Seyrek: Özofajit','Bilinmiyor: Anoreksi','RARE_SOURCE_WORDING','class_level',['Özofajit','Özofajiyal ülserler']),
          (10,'Seyrek: Özofajit','Bilinmiyor: Anoreksi','RARE_SOURCE_WORDING','unresolved',['disfaji']),
          (10,'Bilinmiyor: Anoreksi','Hepato-biliyer','UNKNOWN','product_specific',['Anoreksi','bulantı','kusma','diyare','glossit','enterokolit','anogenital bölgede enflamatuar lezyonlar','abdominal ağrı','pankreatit']),
          (10,'Seyrek: Hepatotoksik etki','Deri ve deri','RARE_SOURCE_WORDING','class_level',['Hepatotoksik etki']),
          (10,'Seyrek: Hepatotoksik etki','Deri ve deri','RARE_SOURCE_WORDING','unresolved',['Karaciğer fonksiyon testlerinde artış','hepatit','sarılık','hepatik yetmezlik']),
          (10,'Bilinmiyor: Makülopapüler','Kas iskelet','UNKNOWN','product_specific',['Makülopapüler ve eritematöz döküntüler','fotosensitivite reaksiyonları','eksfoliyatif dermatit']),
          (10,'Bilinmiyor: Artralji','Böbrek ve idrar','UNKNOWN','product_specific',['Artralji','miyalji']),
          (10,'Bilinmiyor: BUN artışı','Diğer','UNKNOWN','product_specific',['BUN artışı']),
          (10,'Bilinmiyor: Tetrasiklinler','Şüpheli advers','UNKNOWN','class_level',['diş renginde bozukluk','mine hipoplazisi'])]
        for page,start,end,state,scope,terms in specs:
            b=passage(d,page,start,end,kind='adverse_candidate',scope=scope)
            s,e=locate(b['quote_exact'],'Seyrek:' if state=='RARE_SOURCE_WORDING' else 'Bilinmiyor:')
            fq=quote(d,page,b['char_start']+s,b['char_start']+e,'frequency_definition',scope)
            for term in terms:
                links=[renal,accumulation] if term=='BUN artışı' else [photo] if term=='fotosensitivite reaksiyonları' else [direct] if term in ['Özofajit','Özofajiyal ülserler'] else []
                note='4.2 birikim yokluğu BUN artışının yokluğu değildir.' if term=='BUN artışı' else 'Yerel başlık Seyrek; parantez sonrası kapsam/başlık uzanımı insan incelemesi bekliyor.' if scope=='unresolved' else ''
                add(b,term,state,fq,linked=links,note=note)
    d['contexts']=contexts;d['candidates']=rows
    return d

def load(index):
    source=Q/('source_'+str(index)+'.json')
    pins=json.loads((Q/'source_bundle_pins.json').read_text(encoding='utf-8'))
    if core.digest(source.read_bytes())!=pins[source.name]:raise ValueError('BUNDLE_HASH_MISMATCH')
    d=json.loads(source.read_text(encoding='utf-8'))
    if core.digest((ROOT/'data/user_pdfs'/FILES[index]).read_bytes())!=d['sha256']:raise ValueError('SOURCE_HASH_MISMATCH')
    return d
def validate(d):
    allq=list(d['contexts'])
    for c in d['candidates']:
        allq.extend([c['source']]+c['context_quotes']+([c['frequency_quote']] if c['frequency_quote'] else []))
        t=d['pages'][c['source']['physical_page']-1]['text']
        assert t[c['term_start']:c['term_end']]==c['source_term']
    for q in allq:
        assert q['document_id']==d['document_id']
        assert d['pages'][q['physical_page']-1]['text'][q['char_start']:q['char_end']]==q['quote_exact']
        assert core.digest(q['quote_exact'].encode())==q['quote_sha256']
    assert len({c['candidate_id'] for c in d['candidates']})==len(d['candidates'])
    return True
def statistics(d):
    from collections import Counter
    rows=d['candidates'];terms=[norm(c['source_term']).casefold() for c in rows]
    return {'product':d['record']['product'],'records':len(rows),'unique_source_terms':len(set(terms)),
      'unique_names':len({c['name_tr'] for c in rows}),'extra_term_records':len(rows)-len(set(terms)),
      'scopes':dict(Counter(c['scope'] for c in rows)),'frequency':dict(Counter(c['frequency_state'] for c in rows)),
      'repeats':{t:n for t,n in Counter(terms).items() if n>1},'clinical_validated_count':'NOT_ESTABLISHED'}
def saved_explanations(c):return []  # No saved WP12 response cites these new document/quote IDs.
def candidate_label(c):
    return c['name_tr']+' · sayfa '+str(c['source']['physical_page'])+' · '+c['candidate_id'][-8:]
if __name__=='__main__':
    import pandas as pd
    stats=[]
    for i in range(2):
        d=build(i);validate(d)
        with (Q/('source_'+str(i)+'.json')).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
        stats.append(statistics(d))
        pd.json_normalize(d['candidates']).to_csv(Q/('candidates_'+str(i)+'.csv'),index=False,encoding='utf-8-sig')
    with (Q/'count_summary.json').open('x',encoding='utf-8') as f:json.dump(stats,f,ensure_ascii=False,indent=2)
    pd.json_normalize(stats).to_csv(Q/'count_summary.csv',index=False,encoding='utf-8-sig')
    with (Q/'source_bundle_pins.json').open('x',encoding='utf-8') as f:json.dump({f'source_{i}.json':core.digest((Q/f'source_{i}.json').read_bytes()) for i in range(2)},f,indent=2)
    print(json.dumps(stats,ensure_ascii=True))
