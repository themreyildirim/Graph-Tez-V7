"""Presentation/state layer only; frozen v1.1 candidate lexicon and WP12 responses unchanged."""
from collections import Counter
import wp13_candidates_v1_1 as original
core=original.core
known=original.known
experimental=original.experimental
explanation=original.explanation
gnn_named=original.gnn_named

def counts(rows):
    terms=[' '.join(r['source_term'].split()).casefold() for r in rows]
    names=[r['name_tr'] for r in rows]
    repeated=[{'normalized_source_term':t,'records':n,'scopes':sorted({r['scope'] for r in rows if ' '.join(r['source_term'].split()).casefold()==t})}
              for t,n in Counter(terms).items() if n>1]
    return {'records':len(rows),'unique_source_terms':len(set(terms)),'unique_Turkish_names':len(set(names)),
            'extra_source_term_records':len(rows)-len(set(terms)),
            'scope_counts':dict(Counter(r['scope'] for r in rows)),
            'source_key_counts':dict(Counter(r['source_key'] for r in rows)),
            'repeated_terms':repeated,'clinical_validated_count':'NOT_ESTABLISHED'}

FREQUENCY={
 'UNKNOWN':'Sıklığı bilinmiyor; mevcut verilerden hesaplanamıyor.',
 'NOT_SPECIFIED':'Bu adayın alıntısında sıklık belirtilmemiş.',
 'infrequent':'Kaynak, seyrek olarak nitelendiriyor (infrequent); sayısal oran verilmemiş.',
 'Rare instances':'Kaynak, nadir olgular bildiriyor (Rare instances); sayısal oran verilmemiş.',
 'uncommon':'Kaynak, yaygın olmayan olarak nitelendiriyor (uncommon); sayısal oran verilmemiş.'}
SCOPES={
 'product_specific':'Bu ürünün prospektüsündeki bildirime ait; ürün/ana ilaç eşdeğerliği onayı değildir.',
 'drug_direct':'Alıntıda doğrudan doksisikline ait ifade; klinik doğrulama onayı değildir.',
 'class_level':'Tetrasiklin sınıfına ait bildirim; doğrudan doksisikline özgü gözlem değildir.',
 'UNVERIFIED':'Kapsam doğrulanamadı — NOT_AVAILABLE. Çevrilmemiş kaynak korunur.'}

def editorial(c):
    """Explicit, source-bound Turkish editorial gloss, never a saved/model-generated answer."""
    key=c['source_key'];term=' '.join(c['source_term'].split()).casefold()
    note='Bu aday için ek koşulun Türkçe aktarımı NOT_AVAILABLE; orijinal kanıtı inceleyin.'
    if key=='E_adverse_p4':note='Prospektüs bu listedeki belirtiler fark edildiğinde hekimle hemen iletişim kurulmasını söylüyor; burada kişisel tedavi önerisi üretilmiyor.'
    elif key=='E_unknown_frequency':
        note='Bu aday, prospektüsün sıklığı bilinmeyen yan etkiler listesinden alınmıştır.'
        if term=='reversible loss of hearing':note='İşitme kaybı geri dönüşlü olarak aktarılır; genellikle yüksek dozlarla veya böbrek sorunu olan hastalarla ilişkili olduğu belirtilir.'
        elif term in ['stomach pains','pancreatitis']:note='Kaynak karın ağrılarının pankreas iltihabının (pankreatit) bir belirtisi olabileceğini söyler.'
        elif term=='vertigo':note='Kaynak, denge sorunlarının özellikle ayağa kalkarken baş dönmesi veya bulantı hissine yol açabileceğini açıklar.'
    elif key=='E_adverse_p5':
        note='Bu kayıt ciddi belirtiler listesinden alınmıştır; sıklığı bilinmeyen diğer listeye otomatik birleştirilmez.'
        if term=='diarrhoea':note='İshal şiddetli veya uzamış olabilir; kan veya mukus içerebilir.'
        elif term=='exanthematous pustulosis':note='Kaynak deri altında kabarıklıklar ve kabarcıklarla birlikte kırmızı, pullu döküntüyü anlatır; ciddi deri reaksiyonunda hemen hekimle iletişim ifadesi vardır.'
        elif term=='liver or gall-bladder problems':note='Kaynak bu sorunların deri/göz sararmasına veya koyu idrarla birlikte açık renkli dışkıya yol açabileceğini belirtir.'
    elif key=='D_direct_intro':note='Doksisiklinin ağızdan neredeyse tam emilimi bağlamında alt bağırsak yan etkileri, özellikle ishal, seyrek olarak anlatılır.'
    elif key=='D_class_GI':
        note='Gastrointestinal bildirimler tetrasiklin sınıfında ağızdan ve parenteral kullanım bağlamında aktarılır.'
        if term in ['esophagitis','esophageal ulcerations']:note='Kaynak tetrasiklin sınıfı ilaçların kapsül/tablet biçimlerinde nadir olgular bildirir; bu hastaların çoğunun ilacı yatmadan hemen önce aldığı belirtilir.'
        elif term=='inflammatory lesions':note='Kaynak anogenital bölgedeki inflamatuvar lezyonları monilial çoğalma bağlamıyla birlikte listeler.'
    elif key=='D_class_skin':
        note='Bu deri bulguları tetrasiklin sınıf listesindedir; doğrudan doksisikline özgü olay olarak sunulmaz.'
        if term=='photosensitivity':note='Bağlı uyarıda bazı tetrasiklin kullanıcılarında abartılı güneş yanığı reaksiyonu biçiminde ışığa duyarlılık bildirildiği belirtilir. Uyarının tamamı orijinal kanıtta korunur.'
    elif key=='D_class_renal':
        note='Tetrasiklinlerin antianabolik etkisi BUN artışına yol açabilir. Bugüne kadarki çalışmalar, böbrek işlevi bozulmuş hastalarda doksisiklin kullanımıyla bunun ortaya çıkmadığını göstermektedir. Bu, sınırlı kaynak ifadesidir; genel güvenlik garantisi değildir.'
    elif key in ['D_class_hypersensitivity','D_class_blood']:note='Bu pasaj, tetrasiklin sınıfına ait bildirim listesidir; alıntıda bu aday için ayrıca bir sıklık oranı veya özel koşul verilmez.'
    elif key=='D_class_other':note='İntrakraniyal hipertansiyon tetrasiklin kullanımıyla ilişkili olarak aktarılır ve önlemler bölümüne atıf yapılır. Ek önlem bölümünün Türkçe aktarımı NOT_AVAILABLE; orijinal atıf korunur.'
    elif key=='D_class_thyroid':note='Uzun süreli tetrasiklin kullanımı bağlamında tiroid bezinde kahverengi-siyah mikroskobik renk değişimi bildirilmiştir. Kaynak, tiroid işlevinde bilinen bir bozukluk olmadığını ayrıca belirtir.'
    frequency=FREQUENCY.get(c['frequency'],'Türkçe sıklık aktarımı NOT_AVAILABLE; kaynak ifadesi korunur.')
    if c['scope']=='UNVERIFIED':frequency='Deneysel kayıtta sıklık belirlenmedi — NOT_AVAILABLE; orijinal metni inceleyin.'
    return {'candidate_id':c['candidate_id'],'name':c['name_tr'],
            'frequency_tr':frequency,
            'scope_tr':SCOPES.get(c['scope'],SCOPES['UNVERIFIED']),'condition_tr':note,
            'method':'source-bound editorial translation · WP13 v1.2',
            'LLM_generated':False,'review':'PENDING','source_quote_id':c['quote_id']}

def init_selection(state,namespace,ids):
    if not ids:return None
    active=state.get(namespace+'_active')
    if active not in ids:active=ids[0]
    state[namespace+'_active']=active
    state.setdefault(namespace+'_picker',active)
    state.setdefault(namespace+'_epoch',0)
    return active

def picker_changed(state,namespace,ids):
    chosen=state[namespace+'_picker']
    if chosen not in ids:raise ValueError('UNKNOWN_CANDIDATE')
    state[namespace+'_active']=chosen
    state[namespace+'_epoch']+=1

def table_changed(state,namespace,ids,table_key):
    event=state[table_key];rows=event.get('selection',{}).get('rows',[])
    if not rows:return
    index=rows[0]
    if not isinstance(index,int) or not 0<=index<len(ids):raise ValueError('UNKNOWN_CANDIDATE_ROW')
    chosen=ids[index]
    state[namespace+'_active']=chosen
    state[namespace+'_picker']=chosen
    state[namespace+'_epoch']+=1
