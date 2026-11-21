"""WP08 protokol önerisi: kimlik, gruplama ve sızıntı sınırı doğrulaması."""
from pathlib import Path
import sys,json,hashlib,copy,unittest,re
import pandas as pd
import numpy as np
import nbformat

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp08_structure_audit import connected_groups,same_nonempty_pairs,greedy_fold_sizes,audit_structures
from wp08_protocol import (check_partition,training_vocabulary,GuardedPreprocessor,
                          new_partition_graph,validate_partition_graph,training_gate)
from wp08_analysis import CHEM,PROTEIN
QA=ROOT/'reports/qa/WP08'
def read(name):return pd.read_csv(QA/name,keep_default_na=False)


class StructureTests(unittest.TestCase):
    def test_01_all_prior_and_input_hashes_unchanged(self):
        for name in ('prior_outputs_hashes.json','input_manifest.json'):
            m=json.loads((QA/name).read_text(encoding='utf-8'))
            self.assertTrue(m);self.assertEqual([], [p for p,h in m.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h])

    def test_02_cohort_and_review_flags_preserved(self):
        actual=read('structure_grouping_evidence.csv').set_index('drug_id')
        source=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv',keep_default_na=False).set_index('id')
        self.assertEqual(set(actual.index),set(source.index));self.assertEqual(len(actual),62)
        self.assertEqual(actual.WP04_review_flags.to_dict(),source.review_flags.to_dict())
        self.assertEqual(actual.WP04_review.to_dict(),(~source.strict_qc_pass).to_dict())

    def test_03_pairwise_complete_unique_bounds(self):
        p=read('pairwise_structure_similarity.csv');self.assertEqual(len(p),62*61//2)
        self.assertFalse(p.duplicated(['drug_id1','drug_id2']).any())
        self.assertTrue(p.drug_id1.lt(p.drug_id2).all())
        self.assertTrue(p.morgan2_2048_no_stereo_tanimoto.between(0,1).all())

    def test_04_levo_oflox_locked_in_all_guard_methods(self):
        s=read('shared_structure_pairs.csv');pair=s[s.drug_id1.eq('DB01137') & s.drug_id2.eq('DB01165')]
        self.assertEqual(len(pair),1);self.assertIn('connectivity',pair.iloc[0].matching_representations)
        g=read('group_candidates.csv')
        for method,rows in g.groupby('method'):
            if method!='primary_drug_only':
                groups=rows.set_index('drug_id').group_id
                self.assertEqual(groups['DB01137'],groups['DB01165'])

    def test_05_identity_not_salt_count(self):
        self.assertFalse(read('structure_grouping_evidence.csv').source_inchikey.duplicated().any())
        self.assertEqual(len(read('cohort_salt_parent_evidence.csv')),99)
        self.assertTrue(read('cohort_salt_parent_evidence.csv').salt_id.str.startswith('DBSALT').all())
        self.assertEqual(len(read('cohort_secondary_parent_evidence.csv')),63)
        self.assertEqual(read('drug_modality_QA_preserved.csv').drug_id.nunique(),62)

    def test_06_transitive_groups_and_empty_scaffold_policy(self):
        groups=connected_groups(['a','b','c','d'],[('a','b'),('b','c')],'m')
        self.assertEqual(groups['a'],groups['c']);self.assertNotEqual(groups['a'],groups['d'])
        self.assertEqual(same_nonempty_pairs(pd.DataFrame({'drug_id':['a','b'],'sc':['','']}),'sc'),[])
        with self.assertRaises(ValueError):connected_groups(['a','a'],[],'m')
        with self.assertRaises(ValueError):connected_groups(['a'],[('a','b')],'m')

    def test_07_group_candidate_constraints_and_counts(self):
        g=read('group_candidates.csv');summary=read('group_summary.csv').set_index('method')
        self.assertFalse(g.approved_for_split.any())
        self.assertEqual(summary.loc['connectivity_guard','groups'],61)
        self.assertEqual(summary.loc['scaffold_or_similarity_0.8','groups'],40)
        self.assertEqual(summary.loc['scaffold_or_similarity_0.8','largest_group'],5)
        pairs=read('pairwise_structure_similarity.csv')
        for threshold in (.7,.8,.9):
            lookup=g[g.method.eq(f'similarity_{threshold:.1f}')].set_index('drug_id').group_id
            for r in pairs[pairs.morgan2_2048_no_stereo_tanimoto.ge(threshold)].itertuples():
                self.assertEqual(lookup[r.drug_id1],lookup[r.drug_id2])

    def test_08_size_feasibility_not_final_assignment(self):
        f=read('split_size_feasibility.csv');self.assertFalse({'drug_id','fold','split'}&set(f.columns))
        self.assertTrue(all(sum(json.loads(x))==62 for x in f.fold_size_vector_only))
        self.assertEqual(sum(greedy_fold_sizes([5,4,3,2,1],3)),15)
        with self.assertRaises(ValueError):greedy_fold_sizes([2],3)


class BoundaryTests(unittest.TestCase):
    def test_09_partition_drug_and_group_disjoint(self):
        self.assertTrue(check_partition(['a','b'],['c'],['d'],['a','b','c','d'],{'a':1,'b':1,'c':2,'d':3}))
        with self.assertRaises(ValueError):check_partition(['a'],['b'],['c'],['a','b','c'],{'a':1,'b':1,'c':2})
        with self.assertRaises(ValueError):check_partition(['a'],['a'],['c'],['a','b','c'],{'a':1,'b':2,'c':3})
        with self.assertRaises(ValueError):check_partition(['a'],['b'],['d'],['a','b','c'],{'a':1,'b':2,'c':3})

    def test_10_train_vocabulary_heldout_label_mutation_invariant(self):
        labels=pd.DataFrame({'drug_id':['a','b','c'],'pt_cui':['X','X','Y']});groups={'a':1,'b':2,'c':3}
        before=training_vocabulary(labels,['a','b'],groups,2,2)
        changed=pd.concat([labels.iloc[:2],pd.DataFrame({'drug_id':['c']*100,'pt_cui':['NEW']*100})],ignore_index=True)
        self.assertEqual(before,['X']);self.assertEqual(training_vocabulary(changed,['a','b'],groups,2,2),before)

    def test_11_vocab_positive_group_support_required(self):
        labels=pd.DataFrame({'drug_id':['a','b'],'pt_cui':['X','X']})
        self.assertEqual(training_vocabulary(labels,['a','b'],{'a':1,'b':1},2,2),[])
        with self.assertRaises(ValueError):training_vocabulary(pd.concat([labels,labels]),['a','b'],{'a':1,'b':2},2,2)

    def test_12_scaler_fit_exact_train_ids_only(self):
        f=pd.DataFrame({'MW':[1.,3.,1000.]},index=['a','b','TEST']);sc=GuardedPreprocessor(['MW'])
        with self.assertRaises(ValueError):sc.fit(f,['a','b'])
        sc.fit(f.loc[['a','b']],['a','b']);self.assertEqual(sc.mean['MW'],2.)
        self.assertEqual(sc.fit_ids,('a','b'))
        sc.transform(f.loc[['TEST']]);self.assertEqual(sc.mean['MW'],2.)

    def test_13_missing_feature_imputation_not_biological_zero(self):
        f=pd.DataFrame({'v':[2.,4.,np.nan]},index=['a','b','c']);sc=GuardedPreprocessor(['v']).fit(f,['a','b','c'])
        self.assertEqual(sc.median['v'],3.)
        with self.assertRaises(ValueError):GuardedPreprocessor(['v']).fit(pd.DataFrame({'v':[np.nan]},index=['a']),['a'])
        with self.assertRaises(ValueError):sc.transform(f.assign(has_pt=1))

    @staticmethod
    def small_graph():
        edges=pd.DataFrame({'drug_id':['a','b','c'],'accession':['P1','P2','P2'],'role':['target','enzyme','carrier']})
        registry=pd.DataFrame({'accession':['P1','P2','P3'],'taxid':['9606','9606','511145']})
        return edges,registry

    def test_14_new_graph_excludes_all_heldout_drug_relations(self):
        edges,registry=self.small_graph()
        g=new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],'train_linked_only')
        self.assertEqual(g['drug'].canonical_ids,['a']);self.assertEqual(g['protein'].canonical_ids,['P1'])
        self.assertEqual(g['drug','target','protein'].num_edges,1)
        self.assertEqual(g['drug','enzyme','protein'].num_edges,0)
        self.assertEqual(g['drug','carrier','protein'].num_edges,0)
        self.assertFalse(g.training_ready)

    def test_15_fixed_registry_does_not_add_test_drug(self):
        edges,registry=self.small_graph()
        g=new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],'fixed_registry_review')
        self.assertEqual(g['protein'].num_nodes,3);self.assertEqual(g['drug'].canonical_ids,['a'])
        with self.assertRaises(ValueError):new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],None)

    def test_16_unknown_reverse_target_relation_rejected(self):
        edges,registry=self.small_graph();edges.loc[0,'role']='reported_PT'
        with self.assertRaises(ValueError):new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],'train_linked_only')
        edges,registry=self.small_graph();g=new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],'train_linked_only')
        import torch
        g['protein','reverse_target','drug'].edge_index=torch.tensor([[0],[0]])
        with self.assertRaises(ValueError):validate_partition_graph(g,['a'],['b','c'])

    def test_17_ppi_strict_human_guard_not_k12_or_context(self):
        edges,registry=self.small_graph()
        with self.assertRaises(ValueError):new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],'fixed_registry_review',[('P1','P2')],['P1'])
        g=new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],'fixed_registry_review',[('P1','P2')],['P1','P2'])
        self.assertEqual(g['protein','ppi_human','protein'].num_edges,2)
        with self.assertRaises(ValueError):new_partition_graph(['a','b','c'],edges,registry,['a'],['b','c'],'fixed_registry_review',[('P1','P3')],['P1','P3'])

    def test_18_real_QA_boundary_probe_without_production_split(self):
        edges=pd.read_csv(ROOT/'reports/qa/WP05/drug_protein_edges.csv')
        registry=pd.read_csv(ROOT/'reports/qa/WP05/protein_registry.csv')
        ids=set(read('drug_modality_QA_preserved.csv').drug_id)
        # Mekanik tek ilaç sınır testi; gerçek train/val/test seçimi değildir.
        train={'DB00199'}
        g=new_partition_graph(ids,edges,registry,train,ids-train,'train_linked_only')
        self.assertEqual(g['drug'].canonical_ids,['DB00199'])
        self.assertEqual(g['protein'].num_nodes,edges[edges.drug_id.eq('DB00199')].accession.nunique())
        self.assertEqual(sum(g[e].num_edges for e in g.edge_types),len(edges[edges.drug_id.eq('DB00199')]))


class ArtifactTests(unittest.TestCase):
    def test_19_label_counts_recomputed_not_target_finalization(self):
        f=read('class_frequencies_QA.csv');pt=f[f.strategy.eq('PT_CUI')];cat=f[f.strategy.eq('historical_30')]
        self.assertEqual((len(pt),int(pt.positive_drugs_QA.sum())),(1061,6416))
        self.assertEqual((len(cat),int(cat.positive_drugs_QA.sum())),(30,1011))
        self.assertEqual(int(pt.positive_drugs_QA.eq(1).sum()),406)
        self.assertEqual(int(pt.positive_drugs_QA.lt(5).sum()),710)
        options=read('label_options.csv');self.assertFalse(options.target_approved.any())
        self.assertFalse(options[options.strategy.eq('clinical_subset')].iloc[0].defined)

    def test_20_group_support_derived_from_real_unique_positives(self):
        pt=pd.read_csv(ROOT/'reports/qa/WP07/observed_pt_positives_external.csv')
        groups=read('group_candidates.csv');groups=groups[groups.method.eq('scaffold_or_similarity_0.8')]
        expected=pt.merge(groups,on='drug_id').groupby('pt_cui').group_id.nunique().to_dict()
        actual=read('class_group_support_QA.csv');actual=actual[actual.strategy.eq('PT_CUI') & actual.method.eq('scaffold_or_similarity_0.8')]
        self.assertEqual(actual.set_index('class_id').positive_groups_QA.to_dict(),expected)
        self.assertEqual(sum(n==1 for n in expected.values()),416)

    def test_21_62_modalities_preserved_no_auto_complete_case(self):
        actual=read('drug_modality_QA_preserved.csv')
        source=pd.read_csv(ROOT/'reports/qa/WP07/drug_modality_QA.csv',keep_default_na=False)
        pd.testing.assert_frame_equal(actual,source)
        self.assertEqual(int((actual.chemistry_qc_available & actual.protein_modality_available).sum()),53)
        self.assertEqual(set(actual[~actual.protein_modality_available].drug_id),{'DB00684','DB06799'})

    def test_22_draft_input_5_56_with_metadata_no_id_encoding(self):
        c=json.loads((QA/'input_contract_v0_1_DRAFT.json').read_text(encoding='utf-8'))
        self.assertEqual(c['chemical_columns'],CHEM);self.assertEqual(c['protein_columns'],PROTEIN)
        self.assertEqual((len(CHEM),len(PROTEIN)),(5,56));self.assertEqual(len(c['cohort_ids']),62)
        self.assertFalse(c['identity_encoding_as_feature']);self.assertFalse(c['label_or_frequency_input'])
        fields=read('input_fields_v0_1_DRAFT.csv');numeric=set(fields[fields.role.eq('candidate_numeric_input')].field)
        self.assertFalse(numeric&{'DrugBank_ID','CID','taxid','accession','has_pt','pt_count','kalite_skoru','combined_score'})

    def test_23_methodology_not_frozen_no_training_or_scores(self):
        p=json.loads((QA/'protocol_proposal.json').read_text(encoding='utf-8'))
        for key in ['D01_D07_values_final','actual_split_created','model_training_run','real_preprocessing_fit','negative_sampling','performance_metrics_computed']:
            self.assertFalse(p[key])
        self.assertIsNone(p['group_definition_final']);self.assertIsNone(p['seed_final'])
        with self.assertRaises(RuntimeError):training_gate(p)
        self.assertFalse(list(QA.glob('*.pt')))

    def test_24_context_and_k12_flags_not_overridden(self):
        contract=json.loads((QA/'input_contract_v0_1_DRAFT.json').read_text(encoding='utf-8'))
        self.assertFalse(contract['context_nodes_in_initial_candidate'])
        self.assertIn('not admitted',contract['K12'])
        context=pd.read_csv(ROOT/'reports/qa/WP07/context_inventory_no_features.csv')
        self.assertEqual(len(context),80);self.assertFalse(context.sequence_feature_available.any())

    def test_25_notebook_executed_real_tables(self):
        nb=nbformat.read(ROOT/'notebooks/WP08_prediction_protocol.ipynb',as_version=4);nbformat.validate(nb)
        code=[c for c in nb.cells if c.cell_type=='code'];self.assertEqual([c.execution_count for c in code],list(range(1,10)))
        outputs=[o for c in code for o in c.outputs];self.assertFalse(any(o.output_type=='error' for o in outputs))
        self.assertFalse(any(o.output_type=='stream' and o.name=='stderr' for o in outputs))
        self.assertEqual(sum('image/png' in o.get('data',{}) for o in outputs),7)
        rows=[len(re.findall(r'<tr(?:\s[^>]*)?>',o.get('data',{}).get('text/html','')))-1 for o in outputs]
        self.assertIn(62,rows)

    def test_26_figures_and_offline_HTML(self):
        fig=ROOT/'reports/figures/WP08';self.assertEqual(len(list(fig.glob('*.png'))),7)
        html=(fig/'structure_similarity_interactive.html').read_text(encoding='utf-8')
        self.assertNotRegex(html,r'<script[^>]+src\s*=');self.assertIn('DB01137',html);self.assertIn('DB01165',html)

    def test_27_clinical_subset_queue_not_approved(self):
        queue=read('clinical_subset_review_queue.csv');self.assertEqual(len(queue),30)
        self.assertFalse(queue.clinical_expert_approved.any())
        source=pd.read_csv(ROOT/'reports/qa/WP03/final_review/category_semantic_review.csv',keep_default_na=False)
        pd.testing.assert_frame_equal(queue[source.columns],source)

    def test_28_metric_semantics_and_wp09_requirements_preserved(self):
        m=read('metric_interpretation.csv');self.assertTrue(m.assumption.str.len().gt(0).all())
        p=json.loads((QA/'protocol_proposal.json').read_text(encoding='utf-8'))
        self.assertIn('actual forward neighbor sensitivity',p['WP09_required'])
        self.assertIn('PPI/no-PPI/shuffled PPI matched ablation',p['WP09_required'])


if __name__=='__main__':unittest.main(verbosity=2)
