"""Kapanış kanıtı ve eğitim içermeyen WP10 tasarım sözleşmesi."""
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp09_closure import CLOSE,verify_previous
from wp09_train import QA,sha
from wp10_design_audit import QA as DESIGN,SCHEMA,feature_dimensions,parameter_count,parse_smiles,identity


class ClosureAndDesignTests(unittest.TestCase):
    def test_01_previous_results_and_original_test_log_preserved(self):
        self.assertEqual(verify_previous(),2347)
        manifest=json.loads((CLOSE/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
        self.assertEqual(sha(QA/'test_results.txt'),manifest['reports/qa/WP09/training_v1/test_results.txt'])

    def test_02_all190_state_checks_and_new_trainer_log_passed(self):
        x=json.loads((CLOSE/'closure_checks.json').read_text(encoding='utf-8'))
        self.assertEqual(x['numeric_states_rehashed'],190);self.assertEqual(x['real_trainer_tests_rerun'],24)
        self.assertFalse(x['refit_production_models']);self.assertEqual(x['probe_optimizer_steps'],0)

    def test_03_saved_outer_scores_reconstructed_for_all_five_variants(self):
        x=pd.read_csv(CLOSE/'NPZ_score_reconstruction.csv')
        self.assertEqual(len(x),5);self.assertTrue(x.max_absolute_error.lt(1e-7).all());self.assertTrue(x.pairs.gt(0).all())

    def test_04_trained_edge_and_gradient_evidence_not_weight_change_alone(self):
        f=pd.read_csv(CLOSE/'trained_forward_gradient.csv');no=f.model.eq('G_noPPI')
        self.assertTrue(f.loc[no,'same_weights_PPI_removed_protein_L2'].eq(0).all())
        self.assertTrue(f.loc[no,'trained_message_weight_gradient_norm'].eq(0).all())
        self.assertTrue(f.loc[~no,'same_weights_PPI_removed_protein_L2'].gt(0).all())
        self.assertTrue(f.loc[~no,'trained_message_weight_gradient_norm'].gt(0).all())
        self.assertTrue(f.state_unchanged.all())

    def test_05_all62_and_eight_QC_holds_exactly_preserved(self):
        new=pd.read_csv(DESIGN/'molecular_graph_feasibility_all62.csv').set_index('id')
        old=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv').set_index('id')
        self.assertEqual(set(new.index),set(old.index));self.assertEqual(len(new),62)
        pd.testing.assert_series_equal(new.strict_QC_pass_unchanged.sort_index(),old.strict_qc_pass.sort_index(),check_names=False)
        self.assertEqual(int(new.strict_QC_pass_unchanged.sum()),54)
        self.assertEqual(set(new[~new.strict_QC_pass_unchanged].index),{'DB00578','DB00798','DB00978','DB01044','DB01150','DB01155','DB01165','DB06799'})
        self.assertTrue(new.technical_graph_possible.all())

    def test_06_real_complex_and_stereo_examples_match_WP04_without_deletion(self):
        sources=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv').set_index('id')
        data=pd.read_csv(DESIGN/'molecular_graph_feasibility_all62.csv').set_index('id')
        for d in ['DB00798','DB01137','DB01165','DB00512']:
            m,s=parse_smiles(sources.loc[d,'raw_smiles']);info=identity(m)
            self.assertEqual(s,'valid');self.assertEqual(m.GetNumAtoms(),data.loc[d,'atoms'])
            self.assertEqual(info['components'],data.loc[d,'components'])
        self.assertEqual(data.loc['DB00798','components'],3)
        self.assertFalse(data.loc['DB06799','proposed_atom_modality_eligible_PENDING_APPROVAL'])

    def test_07_directed_count_and_isolated_nodes_contract(self):
        f=pd.read_csv(DESIGN/'molecular_graph_feasibility_all62.csv')
        np.testing.assert_array_equal(f.directed_edges_if_materialized,2*f.bonds)
        self.assertTrue(f.atoms.gt(0).all())
        config=json.loads((ROOT/'configs/WP10_design_PROPOSED_v1.json').read_text(encoding='utf-8'))
        self.assertIn('explicit N',config['PyG_contract']['num_nodes'])
        self.assertEqual(config['PyG_contract']['y'],'absent; supervision separate by frozen train PT')

    def test_08_fixed_schema_sizes_and_parameter_arithmetic(self):
        self.assertEqual(feature_dimensions(),{'atom':44,'bond':14})
        for k in [1,158,326]:
            p=parameter_count(k);self.assertEqual(p['proposed_molecular_branch'],1592)
            self.assertEqual(p['proposed_total']-p['WP09_total'],1592+9*k)

    def test_09_stereo_unknown_separate_from_none(self):
        self.assertIn('UNASSIGNED_POTENTIAL',SCHEMA['atom']['CIP_state'])
        self.assertIn('NONE',SCHEMA['atom']['CIP_state'])
        self.assertIn('STEREOANY',SCHEMA['bond']['stereo'])
        self.assertIn('STEREONONE',SCHEMA['bond']['stereo'])

    def test_10_source_manifest_unchanged_no_training_enabled(self):
        inputs=json.loads((DESIGN/'input_manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(all(sha(ROOT/p)==h for p,h in inputs.items()))
        config=json.loads((ROOT/'configs/WP10_design_PROPOSED_v1.json').read_text(encoding='utf-8'))
        self.assertFalse(config['training_enabled']);self.assertFalse(config['model_implemented']);self.assertFalse(config['graph_tensors_materialized'])
        self.assertEqual(config['factorial_primary'],['A0_P0','A0_P1','A1_P0','A1_P1'])

    def test_11_no_label_or_ID_feature_and_no_source_expansion(self):
        forbidden={'drug_id','PT','PT_count','SIDER','kalite_skoru','combined_score','CID','ATC','source_id'}
        self.assertFalse(forbidden & set(SCHEMA['atom']));self.assertFalse(forbidden & set(SCHEMA['bond']))
        sources=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv')
        self.assertTrue(sources.source_kind.eq('local_DrugBank_XML').all())
        summary=json.loads((DESIGN/'feasibility_summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['isotope_nonzero_atoms'],0);self.assertEqual(summary['radical_atoms'],0)

    def test_12_scope_and_unknown_semantics_not_changed(self):
        f=pd.read_csv(CLOSE/'same_key_checks.csv');self.assertTrue(f.same_keys.all())
        self.assertEqual(len(f),10)
        c=json.loads((CLOSE/'closure_checks.json').read_text(encoding='utf-8'))
        self.assertEqual((c['source_drugs'],c['source_PT'],c['source_positives']),(62,1061,6416))
        self.assertEqual(c['primary_paired54_outside_source_positives'],1685)
        self.assertEqual(c['null_failures_remain_NA'],3)


if __name__=='__main__':unittest.main(verbosity=2)
