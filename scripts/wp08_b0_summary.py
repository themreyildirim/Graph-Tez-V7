"""Keşifsel sonuçlar için betimleyici ekler; skor/frekans/model değiştirmez."""
import pandas as pd
import numpy as np
from wp08_b0_frequency import ROOT,QA,SEMANTICS,write_csv


def main():
    frequency=pd.read_csv(QA/'train_frequency_estimates.csv')
    pop=frequency.groupby(['context','protocol','outer_fold','inner_fold','reference']).train_drugs.first().reset_index()
    pop['semantics']=SEMANTICS;write_csv(QA/'train_population_sizes.csv',pop)
    folds=pd.read_csv(QA/'within_outer_fold_metrics.csv')
    diag=folds[folds.scope.eq('paired54')&folds.metric.eq('class_macro_AUROC')].copy()
    write_csv(QA/'within_fold_class_AUROC_diagnostic.csv',diag)
    mean=diag.groupby(['protocol','model']).agg(descriptive_mean_of_5_fold_class_AUROC=('estimate','mean'),
        min_fold=('estimate','min'),max_fold=('estimate','max')).reset_index()
    mean['CI_status']='Descriptive diagnostic only; folds not independent; no t-CI or metric replacement'
    mean['semantics']=SEMANTICS;write_csv(QA/'within_fold_AUROC_descriptive_mean.csv',mean)
    drugs=pd.read_csv(QA/'per_drug_metrics.csv')
    rows=[]
    for protocol in ('primary','stress'):
        scope=drugs[drugs.protocol.eq(protocol)&drugs.scope.eq('paired54')]
        for model,reference in [('B1','B0_like_B1'),('B2','B0_like_B2')]:
            a=scope[scope.model.eq(model)][['drug_id','outer_fold','drug_AP','scored_targets','observed_positive']]
            b=scope[scope.model.eq(reference)][['drug_id','drug_AP']].rename(columns={'drug_AP':'reference_drug_AP'})
            merged=a.merge(b,on='drug_id',validate='one_to_one')
            for r in merged.itertuples():rows.append({'protocol':protocol,'scope':'paired54','model':model,'reference':reference,
                'drug_id':r.drug_id,'outer_fold':r.outer_fold,'drug_AP':r.drug_AP,'reference_drug_AP':r.reference_drug_AP,
                'AP_difference':r.drug_AP-r.reference_drug_AP,'scored_targets':r.scored_targets,
                'observed_positive':r.observed_positive,'semantics':SEMANTICS})
    write_csv(QA/'per_drug_model_minus_matched_frequency.csv',pd.DataFrame(rows))
    roadmap=[
      ('Drug-disjoint / nested split / train-only scaler','Tamamlandı, v1 kilitli','Bu ekte değişmedi; B0 farklı seed veya split aramadı'),
      ('Observed-record LR ve koşullu grup CI / leakage test','İlk B1/B2 ve keşifsel B0 tamamlandı','Sabit OOF CI tüm tekrar-eğitim belirsizliği değil'),
      ('5 kimya + ATC baseline varyantı','Yapılmadı; kullanıcı onayı bekler','WP02 kaynak kodları, train-only/sabit hiyerarşi kararı; eski one-hot kullanılmaz'),
      ('RF ve kimya MLP baseline','Yapılmadı; ilk eğitim onayı bunları dışladı','Kapasite/arama planı sonuç görmeden ayrı sürümlenmeli; bu ekte başlatılmadı'),
      ('Protein-mean MLP baseline','Yapılmadı','Mevcut B2 rol özetli LR, MLP veya PPI/GiG değildir'),
      ('Gerçek PU loss / class-prior varsayım deneyi','Ayrı yöntem seçilmedi; mevcut hedef observed-record proxy','WP08 karşılaştırmalı PU öğretimi var; ek PU modeli zorunluymuş gibi otomatik eklenmez'),
      ('Tarihsel V6 metriklerinin bağımsız doğrulanması','Doğrulandı iddiası yok','Bu 62/PT/clean giriş deneyleri eski 38/30/sızıntılı sistemi yeniden doğrulamaz'),
      ('WP08 nihai kapsam/kapanış kararı','Açık; kullanıcı onayı bekleniyor','Yapılmayan roadmap varyantları için yap/ertele/kapsam daralt kararı gerekir'),
      ('PPI encoder gerçek forward ve ablation','WP09 görevi, başlamadı','WP08 eksiğini kapatmak için kendiliğinden WP09a geçilmez'),
    ]
    write_csv(QA/'ROADMAP_WP08_remaining_tasks.csv',pd.DataFrame(roadmap,columns=['task','status','scope_note']))
    print('B0 descriptive diagnostics and explicit remaining roadmap tasks written')


if __name__=='__main__':main()
