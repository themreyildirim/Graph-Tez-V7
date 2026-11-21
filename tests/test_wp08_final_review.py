"""Kapanış kanıtı ve WP09 plan sınırları; encoder/PPI forward testi değildir."""
from pathlib import Path
import hashlib
import json
import unittest
import nbformat
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP08/final_closure_v1'


class FinalReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads((QA/'WP09_comparison_contract_draft.json').read_text(encoding='utf-8'))
        cls.audit=json.loads((QA/'integrity_audit.json').read_text(encoding='utf-8'))

    def test_01_existing_103_tests_really_rerun(self):
        result=pd.read_csv(QA/'existing_test_suite_results.csv')
        self.assertEqual(result.tests.tolist(),[28,28,28,19])
        self.assertTrue(result.passed.all())
        for row in result.itertuples():
            text=(QA/row.log).read_text(encoding='utf-8')
            self.assertIn(f'Ran {row.tests} tests',text)
            self.assertTrue(text.rstrip().endswith('OK'))

    def test_02_exact_reference_hashes_and_all_accepted_artifacts(self):
        paths=dict(self.contract['reference_files_sha256'])
        paths.update(json.loads((QA/'accepted_artifacts_sha256.json').read_text(encoding='utf-8')))
        bad=[name for name,h in paths.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h]
        self.assertEqual(bad,[])
        self.assertEqual(self.contract['seed'],20261106)
        self.assertEqual(len(self.contract['split_manifest']),3)

    def test_03_models_and_small_nondecisive_B1_gain_preserved(self):
        metrics=pd.read_csv(QA/'accepted_paired_metrics.csv')
        actual=metrics[metrics.protocol.eq('primary')&metrics.metric.eq('drug_macro_AP')].set_index('model').estimate
        for model,expected in {'B0_like_B1':.6438,'B1':.6556,'B0_like_B2':.6466,'B2':.6262}.items():
            self.assertAlmostEqual(actual[model],expected,places=4)
        delta=pd.read_csv(QA/'accepted_paired_differences.csv')
        row=delta[delta.protocol.eq('primary')&delta['first'].eq('B1')&delta.reference.eq('B0_like_B1')&delta.metric.eq('drug_macro_AP')].iloc[0]
        self.assertLess(row.CI95_low,0);self.assertGreater(row.CI95_high,0)

    def test_04_full_source_space_is_not_scored_space(self):
        self.assertEqual(self.audit['source_PT'],{'drugs':62,'PT_CUI':1061,'positive_pairs':6416})
        coverage=pd.read_csv(QA/'accepted_primary_coverage.csv')
        row=coverage[coverage.scope.eq('paired54')&coverage.model.eq('B0_all_train')].iloc[0]
        self.assertEqual(int(row.observed_positive_scored+row.out_of_scored_vocab_positive),5505)
        self.assertEqual(int(row.out_of_scored_vocab_positive),1685)
        self.assertEqual(int(row.scored_pairs),13964)

    def test_05_deferred_variants_are_not_completed_or_deleted(self):
        disposition=pd.read_csv(QA/'scope_disposition.csv').set_index('task')
        for name in ('ATC varyantı','Random Forest','Kimya MLP','Protein-mean MLP'):
            self.assertEqual(disposition.loc[name,'status'],'DEFERRED_OUTSIDE_PHASE1')
        roadmap=(ROOT/'docs/plan/ROADMAP_V7.md').read_text(encoding='utf-8')
        self.assertIn('LR/RF/MLP',roadmap);self.assertIn('protein-mean MLP',roadmap)

    def test_06_no_WP09_training_authorized_or_clinical_claim(self):
        c=self.contract
        self.assertFalse(c['WP09_implementation_authorized'] or c['WP09_training_authorized'])
        self.assertTrue(c['exploratory_after_seen_baselines'])
        self.assertFalse(c['clinical_risk_or_causal_claim'])
        self.assertIn('NOT verified',c['proxy']['unknown_s_0'])
        self.assertFalse(c['selection']['outer_test_used_for_hyperparameters'] or c['selection']['baseline_retuning'])
        self.assertEqual(len(c['ablations']),3)
        self.assertFalse(c['graph']['K12_MG1655_23_conditional_edges_in_human_graph'] or c['graph']['context80'])
        self.assertIsNone(c['graph']['threshold'])
        self.assertEqual(c['graph']['roles'],['target','enzyme','transporter','carrier'])
        self.assertTrue(c['tests_required_not_yet_executed'])

    def test_07_topology_preflight_independent_first_context(self):
        preflight=pd.read_csv(QA/'WP09_train_only_topology_preflight.csv')
        self.assertEqual(len(preflight),120)
        parts=pd.read_csv(ROOT/'reports/qa/WP08/experimental_preparation/nested_partitions_v1.csv')
        train=set(parts[parts.context.eq('primary_o01_final')&parts.split.eq('train')].drug_id)
        dp=pd.read_csv(ROOT/'reports/qa/WP05/drug_protein_edges.csv')
        accessions=set(dp[dp.drug_id.isin(train)&dp.sequence_available].accession)
        mapping=pd.read_csv(ROOT/'reports/qa/WP06/protein_string_mapping.csv')
        nodes=set(mapping[mapping.accession.isin(accessions)&mapping.strict_taxon_match&mapping.network_taxid.eq(9606)].string_id)
        edges=pd.read_csv(ROOT/'reports/qa/WP06/strict_taxon_induced_edges.csv')
        for threshold in (400,700,900):
            local=edges[edges.protein1.isin(nodes)&edges.protein2.isin(nodes)&edges.combined_score.ge(threshold)&~edges.score_conflict]
            row=preflight[preflight.context.eq('primary_o01_final')&preflight.threshold.eq(threshold)].iloc[0]
            self.assertEqual(row.undirected_PPI_pairs,len(local))
            self.assertEqual(row.strict_human_train_nodes,len(nodes))
            self.assertEqual(row.isolated_human_nodes,len(nodes-(set(local.protein1)|set(local.protein2))))

    def test_08_notebook_executed_with_three_new_figures(self):
        notebook=nbformat.read(ROOT/'notebooks/WP08_final_conclusions.ipynb',as_version=4)
        nbformat.validate(notebook)
        codes=[c for c in notebook.cells if c.cell_type=='code']
        self.assertEqual([c.execution_count for c in codes],list(range(1,7)))
        outputs=[o for c in codes for o in c.outputs]
        self.assertFalse(any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs))
        self.assertEqual(sum('image/png' in o.get('data',{}) for o in outputs),3)
        self.assertEqual(len(list((ROOT/'reports/figures/WP08/final_closure_v1').glob('*.png'))),3)


if __name__=='__main__':unittest.main(verbosity=2)
