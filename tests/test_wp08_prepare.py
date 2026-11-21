"""WP08 gerçek split/fit/graf hazırlığı; model veya başarım testi değildir."""
from pathlib import Path
import sys,json,hashlib,inspect,re,unittest
import numpy as np
import pandas as pd
import nbformat
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp08_prepare import (QA,SPEC,CHEM,PROTEIN,ROLES,group_folds,make_partitions,
                          candidate_vocabulary,fit_statistics,transformed_features,feature_schema)


class PreparedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.read=staticmethod(lambda name:pd.read_csv(QA/name,keep_default_na=False))
        cls.parts=cls.read('nested_partitions_v1.csv');cls.outer=cls.read('outer_membership_v1.csv')
        cls.coverage=cls.read('prediction_eligibility.csv');cls.stats=json.loads((QA/'transform_fit_sources_and_statistics.json').read_text(encoding='utf-8'))
        cls.vocab=json.loads((QA/'train_vocabularies.json').read_text(encoding='utf-8'))
        cls.typed=pd.read_csv(ROOT/'reports/qa/WP05/drug_protein_edges.csv')
        cls.pf=pd.read_csv(ROOT/'reports/qa/WP05/protein_features.csv').set_index('accession')
        cls.chem=pd.read_csv(ROOT/'reports/qa/WP04/chemical_features_clean.csv').set_index('id')
        cls.masks=pd.read_csv(ROOT/'reports/qa/WP07/drug_modality_QA.csv',keep_default_na=False)
        pt=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv');pt=pt[pt.conservative]
        cls.labels=pt[['id','meddra_cui']].rename(columns={'id':'drug_id','meddra_cui':'class_id'})
        sys.path.insert(0,str(ROOT/'.deps/pyg'))
        import torch
        cls.graphs=torch.load(QA/'train_only_graphs_v1.pt',weights_only=False,map_location='cpu')

    def test_01_prior_and_inputs_unchanged(self):
        for file in ('prior_outputs_hashes.json','input_manifest.json'):
            expected=json.loads((QA/file).read_text(encoding='utf-8'))
            self.assertTrue(expected);self.assertEqual([],[p for p,h in expected.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h])

    def test_02_split_lock_and_manifest(self):
        lock=json.loads((QA/'split_lock_v1.json').read_text(encoding='utf-8'))
        self.assertEqual(lock['specification'],SPEC)
        digest=lock.pop('specification_sha256')
        self.assertEqual(hashlib.sha256(json.dumps(lock,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),digest)
        for name,sha in json.loads((QA/'frozen_split_manifest.json').read_text(encoding='utf-8')).items():
            self.assertEqual(hashlib.sha256((QA/name).read_bytes()).hexdigest(),sha)

    def test_03_label_free_deterministic_allocation(self):
        groups=pd.read_csv(ROOT/'reports/qa/WP08/group_candidates.csv')
        outer,parts=make_partitions(groups.sample(frac=1,random_state=1))
        pd.testing.assert_frame_equal(outer,self.outer);pd.testing.assert_frame_equal(parts,self.parts)
        self.assertNotIn('labels',inspect.signature(group_folds).parameters)
        self.assertEqual(SPEC['seed'],20261106)

    def test_04_actual_62_ids_every_context(self):
        expected=set(self.masks.drug_id);self.assertEqual(len(expected),62)
        self.assertEqual(self.parts.context.nunique(),40)
        for context,sub in self.parts.groupby('context'):
            self.assertEqual(len(sub),62);self.assertEqual(set(sub.drug_id),expected)
            self.assertFalse(sub.drug_id.duplicated().any())

    def test_05_each_drug_exactly_one_outer_test(self):
        for protocol,sub in self.outer.groupby('protocol'):
            self.assertEqual(len(sub),62)
            self.assertEqual(sorted(sub.groupby('outer_test_fold').size()),[12,12,12,13,13])
            for fold in range(1,6):
                parts=self.parts[self.parts.context.eq(f'{protocol}_o{fold:02}_final')]
                self.assertEqual(set(parts[parts.split.eq('test')].drug_id),set(sub[sub.outer_test_fold.eq(fold)].drug_id))

    def test_06_group_disjoint_all_contexts(self):
        for context,sub in self.parts.groupby('context'):
            self.assertEqual(sub.groupby('group_id').split.nunique().max(),1)
            sets={split:set(sub[sub.split.eq(split)].drug_id) for split in ['train','validation','test']}
            self.assertFalse(sets['train']&sets['test'] or sets['train']&sets['validation'] or sets['test']&sets['validation'])

    def test_07_levo_oflox_never_separated(self):
        for context,sub in self.parts.groupby('context'):
            pair=sub[sub.drug_id.isin(['DB01137','DB01165'])]
            self.assertEqual(pair.split.nunique(),1);self.assertEqual(pair.group_id.nunique(),1)

    def test_08_nested_train_validation_within_outer_train(self):
        for protocol in ('primary','stress'):
            for ofold in range(1,6):
                final=self.parts[self.parts.context.eq(f'{protocol}_o{ofold:02}_final')]
                outer_train=set(final[final.split.eq('train')].drug_id);test=set(final[final.split.eq('test')].drug_id)
                all_val=[]
                for ifold in range(1,4):
                    sub=self.parts[self.parts.context.eq(f'{protocol}_o{ofold:02}_i{ifold:02}')]
                    self.assertEqual(set(sub[sub.split.eq('test')].drug_id),test)
                    self.assertEqual(set(sub[~sub.split.eq('test')].drug_id),outer_train)
                    all_val.extend(sub[sub.split.eq('validation')].drug_id)
                self.assertEqual(set(all_val),outer_train);self.assertEqual(len(all_val),len(outer_train))

    def test_09_train_vocab_independent_recalculation(self):
        for context,sub in self.parts.groupby('context'):
            groups=dict(zip(sub.drug_id,sub.group_id));train=set(sub[sub.split.eq('train')].drug_id)
            expected={}
            for scope in ('cohort','B1','B2'):
                usable=train if scope=='cohort' else train&set(self.coverage[self.coverage.model.eq(scope)&self.coverage.eligible].drug_id)
                labels=self.labels[self.labels.drug_id.isin(usable)].copy();labels['g']=labels.drug_id.map(groups)
                count=labels.groupby('class_id').agg(d=('drug_id','nunique'),g=('g','nunique'))
                expected[scope]=sorted(count[(count.d>=5)&(count.g>=2)].index)
            expected['paired']=sorted(set(expected['B1'])&set(expected['B2']))
            self.assertEqual(self.vocab[context],expected)

    def test_10_heldout_label_mutation_cannot_change_vocabulary(self):
        sub=self.parts[self.parts.context.eq('primary_o01_i01')];groups=dict(zip(sub.drug_id,sub.group_id));train=set(sub[sub.split.eq('train')].drug_id)
        original=candidate_vocabulary(self.labels,train,groups)
        changed=self.labels.copy();changed.loc[~changed.drug_id.isin(train),'class_id']='FAKE_HELDOUT'
        self.assertEqual(candidate_vocabulary(changed,train,groups),original)

    def test_11_inner_vocab_not_copied_from_outer(self):
        for protocol in ('primary','stress'):
            for ofold in range(1,6):
                outer=self.vocab[f'{protocol}_o{ofold:02}_final']
                for ifold in range(1,4):
                    inner=self.vocab[f'{protocol}_o{ofold:02}_i{ifold:02}']
                    for scope in ('cohort','B1','B2','paired'):self.assertTrue(set(inner[scope])<=set(outer[scope]))
        self.assertNotEqual(self.vocab['primary_o01_i01'],self.vocab['primary_o01_final'])

    def test_12_eligibility_abstention_and_62_inventory(self):
        self.assertEqual(len(self.coverage),124)
        self.assertEqual(self.coverage.groupby('model').eligible.sum().to_dict(),{'B1':54,'B2':61})
        meth=self.coverage[self.coverage.drug_id.eq('DB06799')]
        self.assertEqual(len(meth),2);self.assertFalse(meth.eligible.any());self.assertTrue(meth.cohort_retained.all())
        self.assertTrue(self.coverage[self.coverage.drug_id.eq('DB00684')].eligible.all())

    def test_13_qc_flags_not_changed(self):
        for model,frame in self.coverage.groupby('model'):
            actual=frame.set_index('drug_id');source=self.masks.set_index('drug_id')
            self.assertEqual(actual.review_flags.to_dict(),source.review_flags.to_dict())
            self.assertEqual(actual.molecule_review.to_dict(),source.molecule_review.to_dict())

    def test_14_fit_sources_exactly_training_sources(self):
        for context,sub in self.parts.groupby('context'):
            train=set(sub[sub.split.eq('train')].drug_id)
            expected_chem=train&set(self.coverage[self.coverage.model.eq('B1')&self.coverage.eligible].drug_id)
            expected_protein=set(self.typed[self.typed.drug_id.isin(train)].accession)
            stats=self.stats[context]
            self.assertEqual(set(stats['chemistry_fit_drug_ids']),expected_chem)
            self.assertEqual(set(stats['protein_fit_accessions']),expected_protein)

    def test_15_saved_means_scales_recomputed(self):
        for context,stats in self.stats.items():
            for name,source,ids,columns in [('chemistry',self.chem,stats['chemistry_fit_drug_ids'],CHEM),('protein',self.pf,stats['protein_fit_accessions'],PROTEIN)]:
                frame=source.loc[ids,columns]
                np.testing.assert_allclose(pd.Series(stats[name]['mean'])[columns],frame.mean(),rtol=1e-12,atol=1e-12)
                np.testing.assert_allclose(pd.Series(stats[name]['scale'])[columns],frame.std(ddof=0).replace(0,1),rtol=1e-12,atol=1e-12)

    def test_16_heldout_only_features_do_not_change_fit(self):
        context='primary_o01_final';sub=self.parts[self.parts.context.eq(context)];train=set(sub[sub.split.eq('train')].drug_id)
        avail=set(self.coverage[self.coverage.model.eq('B1')&self.coverage.eligible].drug_id)
        changed_chem=self.chem.copy();changed_chem.loc[~changed_chem.index.isin(train),CHEM]=1e9
        seen=set(self.typed[self.typed.drug_id.isin(train)].accession)
        changed_pf=self.pf.copy();changed_pf.loc[~changed_pf.index.isin(seen),PROTEIN]=1e9
        result=fit_statistics(changed_chem,changed_pf,self.typed,train,avail)
        self.assertEqual(result,self.stats[context])

    def test_17_feature_shapes_finite_and_schema_no_label_or_id(self):
        schema=feature_schema();self.assertEqual({m:len(c) for m,c in schema.items()},{'B1':6,'B2':234})
        for context in self.stats:
            with np.load(QA/'features'/(context+'.npz'),allow_pickle=False) as arrays:
                self.assertEqual(set(arrays.files),{'drug_ids','B1','B2'})
                self.assertEqual(len(set(arrays['drug_ids'])),62)
                for model,size in [('B1',6),('B2',234)]:self.assertEqual(arrays[model].shape,(62,size));self.assertTrue(np.isfinite(arrays[model]).all())
        self.assertFalse(any(s in '|'.join(sum(schema.values(),[])) for s in ['pt_count','kalite_skoru','DrugBank','CID']))

    def test_18_masked_zeros_are_placeholders_not_source_imputation(self):
        with np.load(QA/'features/primary_o01_final.npz',allow_pickle=False) as arr:
            lookup={d:i for i,d in enumerate(arr['drug_ids'])};m=self.masks.set_index('drug_id')
            for drug,i in lookup.items():
                for j,role in enumerate(ROLES):
                    absent=not ((self.typed.drug_id.eq(drug))&(self.typed.role.eq(role))).any()
                    self.assertEqual(arr['B2'][i,230+j],int(not absent))
                    if absent:self.assertTrue(np.equal(arr['B2'][i,5+j*56:5+(j+1)*56],0).all())
                self.assertEqual(arr['B2'][i,229],int(m.loc[drug,'chemistry_qc_available']))
                if not m.loc[drug,'chemistry_qc_available']:self.assertTrue((arr['B2'][i,:5]==0).all())
            self.assertTrue((arr['B2'][lookup['DB06799']]==0).all())
        self.assertEqual(int(self.chem[CHEM].isna().all(axis=1).sum()),8)

    def test_19_role_summary_matches_train_scaled_source(self):
        context='primary_o01_final';stats=self.stats[context]
        with np.load(QA/'features'/(context+'.npz'),allow_pickle=False) as arr:
            i=list(arr['drug_ids']).index('DB00199')
            pm=pd.Series(stats['protein']['mean']);ps=pd.Series(stats['protein']['scale'])
            for j,role in enumerate(ROLES):
                acc=sorted(set(self.typed[self.typed.drug_id.eq('DB00199')&self.typed.role.eq(role)].accession))
                if acc:np.testing.assert_allclose(arr['B2'][i,5+j*56:5+(j+1)*56],((self.pf.loc[acc,PROTEIN]-pm)/ps).mean(),rtol=1e-12,atol=1e-12)

    def test_20_all_new_graphs_have_train_drugs_only(self):
        self.assertEqual(len(self.graphs),40)
        for context,g in self.graphs.items():
            g.validate(raise_on_error=True);sub=self.parts[self.parts.context.eq(context)];train=set(sub[sub.split.eq('train')].drug_id)
            self.assertEqual(set(g['drug'].canonical_ids),train)
            self.assertEqual(set(g['protein'].canonical_ids),set(self.stats[context]['protein_fit_accessions']))
            self.assertEqual(g.purpose,'WP08_prepared_train_only_no_model_fit');self.assertFalse(g.training_ready)

    def test_21_graph_relations_exact_source_no_reverse_PPI_targets(self):
        for context,g in self.graphs.items():
            train=set(g['drug'].canonical_ids);di=g['drug'].canonical_ids;pi=g['protein'].canonical_ids
            self.assertEqual(set(g.edge_types),{('drug',r,'protein') for r in ROLES})
            self.assertEqual(set(g.node_types),{'drug','protein'})
            for role in ROLES:
                expected=set(self.typed[self.typed.drug_id.isin(train)&self.typed.role.eq(role)][['drug_id','accession']].itertuples(index=False,name=None))
                actual={(di[a],pi[b]) for a,b in g['drug',role,'protein'].edge_index.t().tolist()}
                self.assertEqual(expected,actual)

    def test_22_query_feature_preparation_does_not_expand_train_graph(self):
        for context,g in self.graphs.items():
            test=set(self.parts[self.parts.context.eq(context)&self.parts.split.eq('test')].drug_id)
            self.assertFalse(test&set(g['drug'].canonical_ids))
            for t in g.node_types:self.assertNotIn('x',g[t]);self.assertNotIn('y',g[t])

    def test_23_secondary30_unchanged_and_support_train_only(self):
        reference=json.loads((QA/'historical30_reference.json').read_text(encoding='utf-8'))
        self.assertEqual(len(reference['classes']),30);self.assertTrue(reference['no_new_merge_or_selection'])
        support=self.read('secondary30_train_support.csv');self.assertEqual(len(support),40*2*30)
        self.assertTrue(support.semantic_warnings_preserved.all())

    def test_24_metric_tables_are_support_only(self):
        f=self.read('metric_evaluability_NO_scores.csv');self.assertEqual(len(f),40*2*3)
        self.assertFalse(f.metric_values_computed.any())
        self.assertTrue((f.observed_positive_pairs+f.unobserved_pairs_NOT_verified_negatives==f.eligible_drugs*f.train_selected_PT_classes).all())
        self.assertTrue((f.eligible_drugs+f.abstained_drugs==f.cohort_drugs).all())
        self.assertTrue((f.train_and_split_proxy_AUROC_possible_classes<=f.proxy_AUROC_evaluable_classes).all())
        fit_vocab=json.loads((QA/'train_fittable_vocabularies_NO_model_fit.json').read_text(encoding='utf-8'))
        trainability=self.read('proxy_trainability_NO_model_fit.csv')
        for (context,model),sub in trainability.groupby(['context','model']):
            self.assertTrue(sub.proxy_classifier_fittable_if_approved.eq(sub.observed_train_positive_drugs.gt(0)&sub.observed_train_positive_drugs.lt(sub.usable_train_drugs)).all())
            self.assertEqual(fit_vocab[context][model],sorted(sub[sub.proxy_classifier_fittable_if_approved].class_id))
            self.assertTrue(set(fit_vocab[context][model])<=set(self.vocab[context][model]))

    def test_25_gate_closed_and_preparation_not_WP08_closure(self):
        gate=json.loads((QA/'training_gate.json').read_text(encoding='utf-8'))
        self.assertFalse(gate['model_training_authorized']);self.assertFalse(gate['performance_authorized'])
        self.assertFalse(gate['WP08_closed']);self.assertFalse(gate['WP09_authorized'])
        self.assertEqual(len(self.read('final_pretraining_decisions.csv')),7)

    def test_26_notebook_executed_and_figures(self):
        nb=nbformat.read(ROOT/'notebooks/WP08_experimental_preparation.ipynb',as_version=4);nbformat.validate(nb)
        code=[c for c in nb.cells if c.cell_type=='code'];self.assertEqual([c.execution_count for c in code],list(range(1,8)))
        outputs=[o for c in code for o in c.outputs]
        self.assertFalse(any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs))
        self.assertEqual(sum('image/png' in o.get('data',{}) for o in outputs),5)
        rows=[len(re.findall(r'<tr(?:\s[^>]*)?>',o.get('data',{}).get('text/html','')))-1 for o in outputs];self.assertIn(62,rows)
        fig=ROOT/'reports/figures/WP08/experimental_preparation'
        self.assertEqual(len(list(fig.glob('*.png'))),5)
        self.assertNotRegex((fig/'frozen_fold_membership_interactive.html').read_text(encoding='utf-8'),r'<script[^>]+src\s*=')

    def test_27_classifier_row_plan_excludes_heldout_and_abstention(self):
        plan=self.read('baseline_row_plan.csv');self.assertEqual(len(plan),40*2*62)
        expected=plan.split.eq('train')&plan.input_eligible
        self.assertTrue(plan.future_classifier_fit_row.eq(expected).all())
        self.assertFalse(plan.model_fit_performed.any())
        self.assertFalse(plan[plan.drug_id.eq('DB06799')].future_classifier_fit_row.any())

    def test_28_positive_coverage_and_paired_scope_are_explicit(self):
        f=self.read('metric_evaluability_NO_scores.csv')
        self.assertTrue((f.observed_positive_pairs+f.out_of_vocab_observed_positive_pairs==f.observed_source_positive_pairs_all_PT).all())
        paired=self.read('paired_evaluation_scope_NO_scores.csv');self.assertEqual(len(paired),40*2)
        self.assertFalse(paired.scores_computed.any())
        complete=self.read('complete_case_53_inventory_ONLY.csv');self.assertEqual(len(complete),62)
        self.assertEqual(int(complete.complete_case_sensitivity.sum()),53)


if __name__=='__main__':unittest.main(verbosity=2)
