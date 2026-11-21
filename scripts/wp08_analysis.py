"""WP08: destek, girdi sözleşmesi ve karar önerileri; model/gerçek split yok."""
import json,hashlib,sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP08'
sys.path.insert(0,str(ROOT/'scripts'))
from wp08_structure_audit import read,write_json

CHEM=['MW','LogP','HBD','HBA','TPSA']
GROUPS=['nonpolar_nonaromatic','aromatic','polar_uncharged','basic','acidic']
PROTEIN=['length_aa','molecular_weight_Da','isoelectric_point','aromaticity_fraction','gravy_kyte_doolittle','net_charge_pH7']
PROTEIN+=['AAC_'+a for a in 'ACDEFGHIKLMNPQRSTVWY']+['group_'+g for g in GROUPS]+['DC_'+a+'__'+b for a in GROUPS for b in GROUPS]

DECISIONS=[
 ('D01','Etiket','Kaynak PT kimliğini koru; destek uygunluğunu her train içinde öğren; tarihsel 30 yalnız sabit ikincil karşılaştırma','3/5/10 ilaç ve >=2 grup eşikleri seçenek; nihai eşik/klinik alt küme onayı yok','Global QA frekansları train sözlüğü seçemez; dış fold etiketleri seçim dışında'),
 ('D02','Eksik modalite','62 ilaç, kaynak girdisinden maskeli dallar birincil aday; 53 complete-case yalnız duyarlılık','Gating/loss ve Methenamine fallback onayı gerekir','Gerçek AAC/MW eksikliği biyolojik sıfır değildir; tüm dallar yoksa train önseli veya abstain açıkça tanımlanır'),
 ('D03','Context','80 özelliksiz STRING context başlangıç modeline alınmasın','Kullanıcı tercihiyle uyumlu öneri; nihai eğitim henüz yok','WP06 insan 700: seed 184 çift/12 izole, expanded 372/7; bağlantı kaybı model başarımı değildir'),
 ('D04','PPI','B1/B2 PPI yok; WP09 için yalnız katı insan PPI ayrı; K12 kapsamı ayrı beklesin','150/400/700/900 seçenek; en iyi eşik seçilmedi','PPI/no-PPI ancak WP09 forward kanıtından sonra; WP08 PPI eğitimi yok'),
 ('D05','Bölme','Etiket körü connectivity kilidi; yapı-gruplu nested CV birincil aday; scaffold+benzerlik stres varyantı','Dış 3 veya 5 fold / iç 3 seçenekleri; scaffold vs identity genelleme hedefi onay bekler','40 gruplu scaffold+0.8 aday; 62 zaten keşfedilmiş ilaçta iç doğrulama, bağımsız yeni test değil'),
 ('D06','Giriş','v0.1 taslak: 5 kimya, 56 dizi, 4 rol ayrı, kaynak kimlikleri metadata; input maskeleri','ATC isteğe bağlı yol haritası varyantı; encode seviyesi/train vocab onayı gerekir','Train-only kimya scaler; protein scaler yalnız train-linked benzersiz accession; ID/PT/QA skorları X değil'),
 ('D07','PU ve metrik','Gözlenen kayıt ilişkisi sıralaması ile biyolojik risk tahminini ayır; unknown bilimsel negatif değil','PU varsayımı/önsel belirsiz; proxy AP/AUROC ayrı onay gerektirir','SCAR/etiketlenme eğilimi SIDER için doğrulanmadı; klinik kalibrasyon/özgüllük iddiası yok'),
]

METRICS=[
 ('Observed-label AP (micro/macro)','s=1 kayıt, s=0 unknown vekil karşılaştırma; onay olmadan hesaplanmaz','Kayıt varlığını sıralama; biyolojik pozitif precision veya klinik AUPRC değil','AP adım ağırlıklı özet; trapez PR alanıyla aynı tanım değil'),
 ('Observed-label AUROC','Aynı proxy s varsayımı ve iki gözlenen sınıf gerekli','Rastgele gözlenen pozitifin unknown üstünde sıralanması; gerçek negatif özgüllüğü değil','Pozitif/unknown hiç yoksa sınıf metriği NA; sıfır başarı sayılmaz'),
 ('Known-positive Recall@k / ranking','Sabit k ve candidate sözlüğü, test pozitifleriyle tek son ölçüm','Bilinen pozitifleri yakalama; tüm gerçek yan etkilerin duyarlılığı değil','Eksik annotation recall ve ranking yorumunu sınırlar; k val içinde ayarlanır'),
 ('PU-corrected ölçümler / nnPU loss','Pozitif etiket hatası, class prior ve SCAR/SAR/propensity varsayımları açık','Varsayımlar geçerliyse gizli y hakkında çıkarım; burada doğrulanmış değil','Class prior 62 ilacın kayıt oranı değildir; önsel duyarlılığı gerekir'),
 ('Klinik kalibrasyon, özgüllük, bireysel risk','Temsili gerçek negatif ve olay/payda verisi gerektirir','Mevcut SIDER ilişkilerinden doğrulanamaz','Bu WP08 deneyi için hedeflenmez'),
 ('CI / belirsizlik','Gelecekte ilaç veya yapısal grup düzeyinde örnekleme','Seçilmiş iç doğrulama örnekleminin belirsizliği','Çift düzeyi bootstrap bağımsızlık varsaymaz; CV fold skorları bağımsız örnek değildir'),
]


def main():
    paths=['reports/qa/WP04/structure_sources.csv','reports/qa/WP04/structure_validation.csv',
           'reports/qa/WP04/chemical_features_clean.csv','reports/qa/WP05/protein_features.csv',
           'reports/qa/WP05/protein_registry.csv','reports/qa/WP05/drug_protein_edges.csv',
           'reports/qa/WP07/drug_modality_QA.csv','reports/qa/WP03/drug_pt_positives.csv',
           'reports/qa/WP03/historical_category_projection_audit.csv',
           'reports/qa/WP03/final_review/category_semantic_review.csv',
           'reports/qa/WP02/salt_parent_links.csv','reports/qa/WP02/secondary_ids.csv',
           'reports/qa/WP06/network_metrics.csv','reports/qa/WP06/protein_string_mapping.csv',
           'reports/qa/WP06/ppi_induced_edges.csv','reports/qa/WP02/drug_registry.csv']
    write_json('input_manifest.json',{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    masks=read(paths[6]);ids=set(masks.drug_id)
    pt=read(paths[7]);pt=pt[pt.conservative & pt.id.isin(ids)][['id','meddra_cui','term']].rename(columns={'id':'drug_id','meddra_cui':'class_id'})
    cats=read(paths[8]);cats=cats[cats.conservative & cats.id.isin(ids)][['id','category']].drop_duplicates().rename(columns={'id':'drug_id','category':'class_id'})
    assert len(pt)==6416 and len(cats)==1011 and len(ids)==62
    methods=read('reports/qa/WP08/group_candidates.csv');group_support=[];strategy=[];frequency=[]
    for name,labels in [('PT_CUI',pt),('historical_30',cats)]:
        support=labels.groupby('class_id').drug_id.nunique()
        for cls,count in support.items():frequency.append({'strategy':name,'class_id':cls,'positive_drugs_QA':int(count),'denominator':62,'observed_record_fraction_QA':count/62})
        strategy.append({'strategy':name,'defined':True,'classes':len(support),'positive_pairs':len(labels),
                         'positive_drugs':labels.drug_id.nunique(),'singleton_classes':int((support==1).sum()),
                         'classes_under5':int((support<5).sum()),'support_min':int(support.min()),'support_max':int(support.max()),
                         'median_positive_per_drug':labels.groupby('drug_id').size().reindex(sorted(ids),fill_value=0).median(),
                         'target_approved':False,'scope':'Full-cohort descriptive QA; never a train-selection result'})
        for method,groups in methods.groupby('method'):
            merged=labels.merge(groups[['drug_id','group_id']],on='drug_id',validate='many_to_one')
            counts=merged.groupby('class_id').group_id.nunique()
            for cls,num in counts.items():group_support.append({'strategy':name,'method':method,'class_id':cls,
                'positive_drugs_QA':int(support[cls]),'positive_groups_QA':int(num)})
    strategy.append({'strategy':'clinical_subset','defined':False,'classes':'not_defined','positive_pairs':'not_defined',
                     'positive_drugs':'not_defined','singleton_classes':'not_defined','classes_under5':'not_defined',
                     'support_min':'not_defined','support_max':'not_defined','median_positive_per_drug':'not_defined',
                     'target_approved':False,'scope':'No expert-approved target list; no post hoc subset invented'})
    pd.DataFrame(strategy).to_csv(QA/'label_options.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(frequency).to_csv(QA/'class_frequencies_QA.csv',index=False,encoding='utf-8-sig')
    gs=pd.DataFrame(group_support);gs.to_csv(QA/'class_group_support_QA.csv',index=False,encoding='utf-8-sig')
    feasible=[]
    for (name,method),frame in gs.groupby(['strategy','method']):
        feasible.append({'strategy':name,'method':method,'classes':len(frame),
                         'positive_in_one_group':int(frame.positive_groups_QA.eq(1).sum()),
                         'at_least_3_positive_groups':int(frame.positive_groups_QA.ge(3).sum()),
                         'at_least_5_positive_groups':int(frame.positive_groups_QA.ge(5).sum()),
                         'interpretation':'Necessary support for each outer fold positive; not sufficient, not fold assignment'})
    pd.DataFrame(feasible).to_csv(QA/'support_feasibility_QA.csv',index=False,encoding='utf-8-sig')
    review=read(paths[9]);review['clinical_expert_approved']=False;review['use']='Semantic review queue only; not a selected clinical subset'
    review.to_csv(QA/'clinical_subset_review_queue.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(DECISIONS,columns=['decision_id','topic','recommended_candidate','pending_approval','reason_or_limit']).to_csv(QA/'decision_proposals.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(METRICS,columns=['metric_or_goal','assumption','meaning','limitation']).to_csv(QA/'metric_interpretation.csv',index=False,encoding='utf-8-sig')
    input_rows=[]
    for field in CHEM:input_rows.append({'entity':'drug','field':field,'role':'candidate_numeric_input','source':paths[2],'id_key':'id','fit_scope':'training drug rows; nonmissing QC-approved values','missing':'8 held values remain missing; policy pending'})
    for field in PROTEIN:input_rows.append({'entity':'protein','field':field,'role':'candidate_numeric_input','source':paths[3],'id_key':'accession','fit_scope':'unique training-linked accessions only','missing':'141 valid source proteins; no context features'})
    for field in ['DrugBank_ID','CID','accession','taxid','source_sha256','review_flags']:
        input_rows.append({'entity':'metadata','field':field,'role':'join_or_provenance_only_NOT_X','source':'WP02/04/05/08 manifests','id_key':'canonical ID','fit_scope':'never fit/encode as numerical biology','missing':'preserve null/flags'})
    for field in ['chemistry_qc_available','protein_modality_available','target_available','enzyme_available','transporter_available','carrier_available']:
        input_rows.append({'entity':'drug','field':field,'role':'candidate_input_mask_or_gate','source':'input QC / typed DrugBank edges','id_key':'drug_id','fit_scope':'not label-derived; mask-bias sensitivity required','missing':'boolean absence != biological absence'})
    pd.DataFrame(input_rows).to_csv(QA/'input_fields_v0_1_DRAFT.csv',index=False,encoding='utf-8-sig')
    write_json('input_contract_v0_1_DRAFT.json',{'version':'WP08-input-v0.1-DRAFT','status':'PROPOSED_NOT_APPROVED',
        'cohort_ids':sorted(ids),'chemical_columns':CHEM,'protein_columns':PROTEIN,'roles':['target','enzyme','transporter','carrier'],
        'identity_encoding_as_feature':False,'source_metadata_outside_X':True,'label_or_frequency_input':False,
        'molecular_QC_flags':'preserved in metadata; not silently overridden',
        'context_nodes_in_initial_candidate':False,'PPI':'none for WP08 B1/B2; strict human comparison planned for WP09 only',
        'K12':'not admitted to primary PPI','preprocessing_fit':'training drugs / unique train-linked proteins; no fit performed on real data',
        'ATC':'Optional B1+ATC roadmap variant; separate approval and train vocabulary or fixed external hierarchy needed',
        'mask_policy':'candidate gate; no numeric feature vector, imputation or training tensor generated',
        'all_modalities_missing':'Methenamine path needs explicit train-only prior or abstention policy; never fabricate protein/chemistry',
        'target_vocabulary':'Only on train IDs inside each split; global class frequencies QA only'})
    write_json('protocol_proposal.json',{'version':'WP08-protocol-v0.1-DRAFT','status':'PENDING_USER_APPROVAL',
        'D01_D07_values_final':False,'actual_split_created':False,'model_training_run':False,
        'real_preprocessing_fit':False,'negative_sampling':False,'performance_metrics_computed':False,
        'outer_fold_candidates':[3,5],'inner_fold_candidate':3,'similarity_QA_thresholds':[.7,.8,.9],
        'group_definition_final':None,'seed_final':None,'train_support_threshold_candidates':[3,5,10],
        'train_min_groups_candidate':2,'context_initial_candidate':False,
        'prior_exploration_limit':'All 62 labels have been explored; future test internal, not untouched external validation',
        'WP09_required':['actual forward neighbor sensitivity','PPI/no-PPI/shuffled PPI matched ablation']})
    masks.to_csv(QA/'drug_modality_QA_preserved.csv',index=False,encoding='utf-8-sig')
    metric=read(paths[12]);metric=metric[metric.threshold.eq(700)][['network_taxid','mapping_scope','graph_kind','nodes','edges','isolates']] if 'graph_kind' in metric else metric[metric.threshold.eq(700)]
    metric.to_csv(QA/'context_topology_cost_QA.csv',index=False,encoding='utf-8-sig')
    print('WP08 label QA, group support, contracts and decision proposals written; no model/split fit')


if __name__=='__main__':main()
