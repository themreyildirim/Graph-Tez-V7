"""Hazırlanan splitler için ikincil kapsam ve tek kısa eğitim karar tablosu."""
import json
import pandas as pd
from wp08_prepare import ROOT,QA,read,write_json,write_csv,sha,support_counts


def main():
    parts=pd.read_csv(QA/'nested_partitions_v1.csv');elig=pd.read_csv(QA/'prediction_eligibility.csv')
    elig['planned_prediction_status']=elig.eligible.map({True:'PREDICTION_NOT_RUN',False:'ABSTAIN'})
    write_csv(QA/'prediction_eligibility.csv',elig)
    pt=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv');pt=pt[pt.conservative]
    pt=pt.rename(columns={'id':'drug_id','meddra_cui':'class_id'})
    hist=pd.read_csv(ROOT/'reports/qa/WP03/historical_category_projection_audit.csv')
    hist=hist[hist.conservative][['id','category']].drop_duplicates().rename(columns={'id':'drug_id','category':'class_id'})
    classes=json.loads((QA/'historical30_reference.json').read_text(encoding='utf-8'))['classes']
    rows=[];secondary=[]
    for context,sub in parts.groupby('context'):
        train=set(sub[sub.split.eq('train')].drug_id);groups=dict(zip(sub.drug_id,sub.group_id))
        for model in ('B1','B2'):
            available=set(elig[elig.model.eq(model)&elig.eligible].drug_id)
            usable_train=train&available;support=support_counts(hist,usable_train,groups)
            for cls in classes:
                positive=int(support.loc[cls,'drugs']) if cls in support.index else 0
                groups_count=int(support.loc[cls,'groups']) if cls in support.index else 0
                rows.append({'context':context,'model':model,'historical_category':cls,'usable_train_drugs':len(usable_train),
                    'train_positive_drugs':positive,'train_positive_groups':groups_count,
                    'train_unobserved_NOT_verified_negative':len(usable_train)-positive,
                    'has_both_proxy_outcomes':0<positive<len(usable_train),'semantic_warnings_preserved':True})
            for split in ('validation','test'):
                usable=set(sub[sub.split.eq(split)].drug_id)&available
                observed=hist[hist.drug_id.isin(usable)].groupby('class_id').drug_id.nunique().reindex(classes,fill_value=0)
                secondary.append({'context':context,'model':model,'split':split,'eligible_drugs':len(usable),'fixed_categories':30,
                    'classes_no_observed_positive':int(observed.eq(0).sum()),
                    'classes_all_observed_positive':int(observed.eq(len(usable)).sum()) if usable else 0,
                    'proxy_AUROC_evaluable_classes':int((observed.gt(0)&observed.lt(len(usable))).sum()),'metric_values_computed':False})
    write_csv(QA/'secondary30_train_support.csv',pd.DataFrame(rows))
    write_csv(QA/'secondary30_evaluability_NO_scores.csv',pd.DataFrame(secondary))
    evaluation=pd.read_csv(QA/'metric_evaluability_NO_scores.csv')
    source_totals=[];paired=[];row_plans=[];trainability=[];fittable={}
    vocab=json.loads((QA/'train_vocabularies.json').read_text(encoding='utf-8'))
    for context,sub in parts.groupby('context'):
        train=set(sub[sub.split.eq('train')].drug_id)
        fittable[context]={}
        for model in ('B1','B2'):
            usable=train&set(elig[elig.model.eq(model)&elig.eligible].drug_id)
            counts=pt[pt.drug_id.isin(usable)].groupby('class_id').drug_id.nunique()
            chosen=[]
            for cls in vocab[context][model]:
                n=int(counts.get(cls,0));can_fit=0<n<len(usable)
                if can_fit:chosen.append(cls)
                trainability.append({'context':context,'model':model,'class_id':cls,'usable_train_drugs':len(usable),
                    'observed_train_positive_drugs':n,'unobserved_train_NOT_verified_negative':len(usable)-n,
                    'proxy_classifier_fittable_if_approved':can_fit,'reason_if_not':'' if can_fit else 'single_proxy_outcome_train__NA_no_probability_fallback'})
            fittable[context][model]=sorted(chosen)
        fittable[context]['paired']=sorted(set(fittable[context]['B1'])&set(fittable[context]['B2']))
    write_csv(QA/'proxy_trainability_NO_model_fit.csv',pd.DataFrame(trainability))
    write_json(QA/'train_fittable_vocabularies_NO_model_fit.json',fittable)
    both_support=[]
    for r in evaluation.itertuples():
        split_ids=set(parts[parts.context.eq(r.context)&parts.split.eq(r.split)].drug_id)
        available=set(elig[elig.model.eq(r.model)&elig.eligible].drug_id)
        total=len(pt[pt.drug_id.isin(split_ids&available)])
        source_totals.append(total)
        train_fit_classes=fittable[r.context][r.model]
        count=pt[pt.drug_id.isin(split_ids&available)&pt.class_id.isin(train_fit_classes)].groupby('class_id').drug_id.nunique().reindex(train_fit_classes,fill_value=0)
        both_support.append(int((count.gt(0)&count.lt(len(split_ids&available))).sum()))
    evaluation['observed_source_positive_pairs_all_PT']=source_totals
    evaluation['out_of_vocab_observed_positive_pairs']=evaluation.observed_source_positive_pairs_all_PT-evaluation.observed_positive_pairs
    evaluation['train_and_split_proxy_AUROC_possible_classes']=both_support
    write_csv(QA/'metric_evaluability_NO_scores.csv',evaluation)
    common=set.intersection(*[set(elig[elig.model.eq(model)&elig.eligible].drug_id) for model in ('B1','B2')])
    m=read('reports/qa/WP07/drug_modality_QA.csv')
    complete=set(m[m.chemistry_qc_available&m.protein_modality_available].drug_id)
    write_csv(QA/'complete_case_53_inventory_ONLY.csv',pd.DataFrame({'drug_id':sorted(m.drug_id),'complete_case_sensitivity': [d in complete for d in sorted(m.drug_id)]}))
    for context,sub in parts.groupby('context'):
        for r in sub.itertuples():
            for model in ('B1','B2'):
                e=elig[elig.model.eq(model)&elig.drug_id.eq(r.drug_id)].iloc[0]
                row_plans.append({'context':context,'model':model,'drug_id':r.drug_id,'group_id':r.group_id,'split':r.split,
                    'input_eligible':bool(e.eligible),'future_classifier_fit_row':r.split=='train' and bool(e.eligible),
                    'abstention_reason':e.abstention_reason if not e.eligible else '', 'model_fit_performed':False})
        for split in ('validation','test'):
            split_ids=set(sub[sub.split.eq(split)].drug_id)
            cls=set(vocab[context]['paired'])
            usable=split_ids&common
            paired.append({'context':context,'split':split,'paired_input_drugs':len(usable),'paired_train_selected_targets':len(cls),
                'paired_proxy_train_fittable_targets':len(fittable[context]['paired']),
                'paired_observed_positive_pairs':len(pt[pt.drug_id.isin(usable)&pt.class_id.isin(cls)]),
                'complete_case_sensitivity_drugs':len(split_ids&complete),'scores_computed':False})
    write_csv(QA/'baseline_row_plan.csv',pd.DataFrame(row_plans))
    write_csv(QA/'paired_evaluation_scope_NO_scores.csv',pd.DataFrame(paired))
    # Karar tablosu: kullanıcı yönü uygulanır, detayların onayı eğitimin önündedir.
    decisions=[
        ('Seed ve fold kilidi','20261106; tek kez etiket körü 5 dış/3 iç; inner seed=base+100*outer; primary connectivity, stress scaffold OR >=0.8',
         'Hazırlık v1 kilitlendi; seed için son eğitim onayı bekliyor'),
        ('PT destek paydası','>=5 pozitif kullanılabilir train ilacı ve >=2 train grup; kohort sözlüğü ayrıca; B1/B2 ortak hedefler train kesişimi',
         '5/2 adayının ve kullanılabilir-train paydasının onayı bekliyor'),
        ('Proxy varsayımı ve ölçüm','Yalnız SIDER kayıt sıralaması; unknown doğrulanmış negatif değil; birincil drug-macro AP, micro/class-macro AP ve AUROC ikincil',
         'Proxy eğitim/ölçüm varsayımı onaylanmadan sınıflandırıcı ve skor yok'),
        ('Abstention ve masked blok','B1 kimya yoksa abstain; B2 iki modalite yoksa abstain; Methenamine için iki modelde de tahmin yok; standartlaştırılmış eksik blok 0 + açık maske',
         'Abstention kullanıcı yönüyle uygulandı; maskeli nötr kodlama ve kapsam kıyasının son onayı'),
        ('Başlangıç learner / iç seçim','Eşleştirilmiş B1/B2 için düzenlileştirilmiş LR önerisi; C={0.1,1,10}, class_weight=None; iç-fold mean drug-macro AP; eşitlikte küçük C',
         'Öneri; LR/ayar seçimi onayı bekliyor. RF/MLP ayrıca deney gerektirir'),
        ('NA, fallback ve kıyas','Train iki proxy sonucu taşımıyorsa sınıfı fit etme, NA; val/test pozitif veya unknown yoksa ayırt edici metrik NA; her modelin kapsamı + ortak drug/target kıyası',
         'Fallback olasılığı veya ortak önsel üretilmedi; NA/ortak kıyas politikasının onayı'),
        ('ATC ve ek analizler','ATC başlangıç matrise eklenmedi; WP02 kaynağıyla ayrı varyant önerisi. 53 complete-case yalnız aynı ana splitlerde duyarlılık; PPI/context yok',
         'ATC/ek learner eğitimleri ayrı onay; WP09 kapalı'),
    ]
    write_csv(QA/'final_pretraining_decisions.csv',pd.DataFrame(decisions,columns=['detay','hazirlanan_veya_onerilen_v1','egitim_onayi']))
    lock=json.loads((QA/'split_lock_v1.json').read_text(encoding='utf-8'))
    write_json(QA/'training_gate.json',{'preparation_version':'WP08-preparation-v1','split_specification_sha256':lock['specification_sha256'],
       'status':'AWAITING_FINAL_METHOD_APPROVAL','model_training_authorized':False,'performance_authorized':False,
       'unknown_semantics':'unobserved != verified biological negative',
       'primary_estimand':'ranking observed SIDER drug-adverse-effect records for unseen drugs',
       'pending_table':'final_pretraining_decisions.csv','WP08_closed':False,'WP09_authorized':False})
    print('Secondary 30-category coverage and final pretraining decision table written')


if __name__=='__main__':main()
