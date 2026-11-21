"""WP03 kapanışı: yalnız mevcut küçük QA tablolarını bağımsız karşılaştırır.

Ham veri, eski analiz üreticileri veya model kodu çalıştırılmaz.
"""
from pathlib import Path
import json,hashlib,ast
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP03';OUT=QA/'final_review'

def jread(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def read(p):return pd.read_csv(p,dtype=str,keep_default_na=False)
def boolcol(df,c):
    if not set(df[c])<={'True','False'}:raise ValueError('Invalid boolean '+c)
    return df[c].eq('True')
def save(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def csvsave(name,df):df.to_csv(OUT/name,index=False,encoding='utf-8-sig')
def mdtable(df):
    def esc(x):return str(x).replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(esc,df.columns))+' |','|'+'|'.join(['---']*len(df.columns))+'|']+
                     ['| '+' | '.join(map(esc,row))+' |' for row in df.itertuples(index=False,name=None)])

def strategy(name,pairs,col,ids):
    p=pairs[pairs.id.isin(ids)][['id',col]].drop_duplicates()
    counts=p.groupby(col).id.nunique().sort_values(ascending=False)
    perdrug=p.groupby('id')[col].nunique().reindex(sorted(ids),fill_value=0)
    freq=counts.rename('positive_drugs').reset_index().rename(columns={col:'class_id'})
    freq['cohort_drugs']=len(ids);freq['observed_positive_fraction']=freq.positive_drugs/len(ids)
    freq['unlabeled_drugs']=len(ids)-freq.positive_drugs
    csvsave('class_frequency_'+name+'.csv',freq)
    stats={'strategy':name,'cohort_drugs':len(ids),'drugs_with_positive':int((perdrug>0).sum()),
        'observed_classes':len(counts),'positive_pairs':len(p),'class_min':int(counts.min()),'class_max':int(counts.max()),
        'singleton_classes':int((counts==1).sum()),'classes_at_most_2':int((counts<=2).sum()),
        'classes_below_5':int((counts<5).sum()),'classes_above_half':int((counts>len(ids)/2).sum()),
        'max_min_support_ratio':float(counts.max()/counts.min()),'per_drug_min':int(perdrug.min()),
        'per_drug_median':float(perdrug.median()),'per_drug_max':int(perdrug.max()),
        'possible_pairs_observed_vocabulary':len(ids)*len(counts),
        'unlabeled_pairs_observed_vocabulary':len(ids)*len(counts)-len(p)}
    return stats,perdrug

def main():
    OUT.mkdir(exist_ok=True)
    inputs=[QA/n for n in ['coverage_summary.json','drug_mapping.csv','drug_pt_positives.csv',
        'historical_category_projection_audit.csv','legacy_code_category_projection.csv','category_audit.json']]
    inputs.append(ROOT/'reports/qa/WP02/legacy_membership.json')
    save('inputs_manifest.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    m=read(QA/'drug_mapping.csv');p=read(QA/'drug_pt_positives.csv');s=jread(QA/'coverage_summary.json')
    keep=boolcol(m,'conservative');pop=m[keep].copy();cid=pop[pop.cid.ne('')]
    exact=pop[pop.status.eq('exact_stereo_cid')];positive_ids=set(p[p.id.isin(set(pop.id))].id)
    actual=p[p.id.isin(set(pop.id))].groupby('id').meddra_cui.nunique()
    old=jread(ROOT/'reports/qa/WP02/legacy_membership.json')['members']
    oldids={r['id'] for r in old if r['old38']}
    checks=[]
    def check(name,observed,expected):checks.append({'check':name,'observed':observed,'expected':expected,'passed':observed==expected})
    check('unique_mapping_ID',m.id.nunique(),len(m));check('mapping_candidates',len(pop),s['conservative']['candidates'])
    check('cid_count',len(cid),s['conservative']['cid_available'])
    check('exact_count',len(exact),s['conservative']['exact_sider'])
    check('positive_id_set_equals_exact_set',sorted(positive_ids),sorted(set(exact.id)))
    check('has_pt_flag_equals_positive_set',sorted(pop[boolcol(pop,'has_pt')].id),sorted(positive_ids))
    check('unique_positive_key_duplicates',int(p.duplicated(['id','meddra_cui']).sum()),0)
    check('conservative_positive_rows',int(p.id.isin(set(pop.id)).sum()),s['conservative']['positive_drug_pt_pairs'])
    mismatch=pop[pop.apply(lambda r:int(r.pt_count)!=int(actual.get(r.id,0)),axis=1)]
    check('per_drug_PT_counts_mismatch',mismatch.id.tolist(),[])
    check('old38_flags_independent',sorted(pop[boolcol(pop,'old38')].id),sorted(set(pop.id)&oldids))
    check('status_partition',int(pop.status.value_counts().sum()),233)
    check('cid_partition',len(cid),len(exact)+int(pop.status.eq('ambiguous_flat_only').sum())+int(pop.status.eq('unmatched_cid_not_in_sider').sum()))
    check('233_chain',[len(pop),len(cid),len(positive_ids)],[233,167,62])
    accepted=pop[pop.id.isin(positive_ids)].copy().sort_values('name')
    for flag,summary_key in [('chemistry_available','chemistry_and_pt'),('protein_available','protein_and_pt')]:
        check(flag,int(boolcol(accepted,flag).sum()),s['conservative'][summary_key])
    check('all_three',int((boolcol(accepted,'chemistry_available')&boolcol(accepted,'protein_available')).sum()),s['conservative']['all_three'])
    check('new_vs_old38',len(positive_ids-oldids),36)
    save('consistency_checks.json',checks)
    if not all(x['passed'] for x in checks):raise RuntimeError('Independent consistency check failed')
    table=accepted[['id','name','pt_count','chemistry_available','protein_available','old38']].copy()
    table.pt_count=table.pt_count.astype(int)
    for key in ['chemistry_available','protein_available','old38']:table[key]=table[key].map({'True':'Var','False':'Yok'})
    table.columns=['DrugBank ID','İlaç','Benzersiz PT','Mevcut kimya','XML protein kimliği','Eski V6 38 üyeliği']
    new=table[~table['DrugBank ID'].isin(oldids)].copy()
    csvsave('accepted_62.csv',table);csvsave('new_36.csv',new)
    (OUT/'accepted_62.md').write_text(mdtable(table),encoding='utf-8');(OUT/'new_36.md').write_text(mdtable(new),encoding='utf-8')
    hist=read(QA/'historical_category_projection_audit.csv');code=read(QA/'legacy_code_category_projection.csv')
    stats=[];perdrug=pd.DataFrame(index=sorted(positive_ids))
    for name,data,col in [('PT_CUI',p,'meddra_cui'),('historical_30',hist,'category'),('code_dictionary_audit',code,'code_category')]:
        st,per=strategy(name,data,col,positive_ids);stats.append(st);perdrug[name]=per
    csvsave('label_strategy_metrics.csv',pd.DataFrame(stats));save('label_strategy_metrics.json',stats)
    csvsave('per_drug_positive_counts.csv',perdrug.reset_index(names='id'))
    # Narrowing/broadening here is a terminology review flag, not clinical adjudication.
    audit=jread(QA/'category_audit.json');freq=read(OUT/'class_frequency_historical_30.csv').set_index('class_id')
    notes={'Bilinç kaybı':('birleştirme / ayrıntı kaybı','Loss of consciousness ve Syncope iki ayrı CUI; aynı kategori. Klinik eşdeğerlik onaylanmadı.'),
      'C.diff ishal':('birleştirme + neden özgüllüğü riski','Clostridium difficile colitis ve Pseudomembranous colitis birleşiyor; ikinci terime C.diff nedeni otomatik yüklenmemeli.'),
      'Nefrotoksisite':('anlam daraltma / neden ekleme riski','Gerçek PT Renal impairment; nefrotoksisite adı toksik neden izlenimi ekliyor.'),
      'Kolit':('kod/file revizyonu + daraltma riski','Gerçek dosya Kolit, kaynak Colitis; MASTER kodu Antibiyotikle ilişkili kolit diyerek neden ekliyor.'),
      'Ağız mantarı':('anlam genişletme riski','Kaynak Oral candidiasis; genel mantar adı kaynak özgüllüğünü kaybedebilir.'),
      'Vajinal mantar':('anlam genişletme / yerleşim kaybı riski','Kaynak Vulvovaginal candidiasis; genel ad Candida ve vulvovajinal kapsamı eksiltebilir.'),
      'Alerjik reaksiyon':('yorumlayıcı çeviri','Hypersensitivity ile kategori adının tam kapsam eşitliği veriyle ispatlanmadı.'),
      'Nöbet':('kapsam genişleme olasılığı','Gerçek dosyada Convulsion tek PT; kod sözlüğünde Seizure da var. Gerçek veri ve tasarım sözlüğü ayrılmalı.')}
    semantic=[]
    for a in audit:
        flag,note=notes.get(a['category'],('yüzeysel karşılık; klinik onay değil','Bu dosyada açık çok-CUI birleşmesi yok; tam kavramsal eşdeğerlik ayrıca gözden geçirilmeli.'))
        semantic.append({'kategori':a['category'],'kaynak_PT':' / '.join(a['pt_names']),'CUI':' / '.join(a['cuis']),
            'pozitif_ilac_62':int(freq.loc[a['category'],'positive_drugs']) if a['category'] in freq.index else 0,
            'inceleme':flag,'not':note})
    sem=pd.DataFrame(semantic);csvsave('category_semantic_review.csv',sem)
    (OUT/'category_semantic_review.md').write_text(mdtable(sem),encoding='utf-8')
    # Source references for leakage review, not model execution.
    calls=[];paths=[]
    for file in sorted((ROOT/'scripts').glob('*')):
        if file.suffix not in ['.py','.cjs']:continue
        text=file.read_text(encoding='utf-8')
        for line_number,line in enumerate(text.splitlines(),1):
            if (any(k in line for k in ['Dataset','DEFAULT_DATA','XML=','SIDER=','--dataset-root'])
                    and ('Path(' in line or 'parser.add_argument(' in line)):
                paths.append({'file':str(file.relative_to(ROOT)),'line':line_number,'text':line.strip()})
        if file.suffix=='.py':
            tree=ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node,ast.Call):
                    name=ast.unparse(node.func)
                    if any(k in name for k in ['read_csv','to_csv','torch','fit','train_test_split','savefig']):calls.append({'file':str(file.relative_to(ROOT)),'line':node.lineno,'call':name})
    csvsave('source_path_references.csv',pd.DataFrame(paths));csvsave('static_io_call_inventory.csv',pd.DataFrame(calls))
    print(json.dumps({'checks':len(checks),'all_passed':True,'accepted':len(table),'new':len(new),'strategies':stats},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
