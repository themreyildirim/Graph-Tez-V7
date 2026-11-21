"""WP07: gerçek küçük QA ve kusur enjeksiyonu; ham kaynak taraması yok."""
from pathlib import Path
import sys
import json
import copy
import unittest
import warnings
import pandas as pd
import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from wp07_integration import (QA, ROLES, CHEM, PROTEIN, read, digest, index_table,
    feature_schema, edge_index, select_ppi, validate_review_graph, require_training_approval, torch)


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Güvenilir, bu WP'de üretilmiş dosya. Legacy pickle kullanılmaz.
        cls.graphs = torch.load(QA / 'heterodata_review_scenarios.pt', weights_only=False, map_location='cpu')
        cls.summary = json.loads((QA / 'integration_summary.json').read_text(encoding='utf-8'))
        cls.masks = read('reports/qa/WP07/drug_modality_QA.csv')
        cls.source_edges = read('reports/qa/WP06/ppi_induced_edges.csv')
        cls.mapping = read('reports/qa/WP06/protein_string_mapping.csv')

    def valid(self, graph):
        with warnings.catch_warnings(record=True) as observed:
            warnings.simplefilter('always')
            result = validate_review_graph(graph)
        self.assertTrue(all('se_pt_audit' in str(w.message) and 'isolated' in str(w.message) for w in observed))
        return result

    def test_01_previous_and_small_input_hashes(self):
        for name in ('prior_outputs_hashes.json', 'input_manifest.json'):
            manifest = json.loads((QA / name).read_text(encoding='utf-8'))
            self.assertTrue(manifest)
            self.assertEqual([], [p for p,h in manifest.items() if digest(ROOT / p) != h])

    def test_02_all_six_graphs_pyg_and_project_validate(self):
        self.assertEqual(len(self.graphs), 6)
        for graph in self.graphs.values():
            self.assertTrue(self.valid(graph))
            self.assertEqual([graph[t].num_nodes for t in ('drug','protein','se_pt_audit')], [62,141,1061])

    def test_03_node_ids_deterministic_and_unique(self):
        for kind in ('drug','protein','se_pt_audit'):
            ids = self.graphs['no_ppi'][kind].canonical_ids
            self.assertEqual(ids, sorted(set(ids)))
            self.assertTrue(all(g[kind].canonical_ids == ids for g in self.graphs.values()))
        with self.assertRaises(ValueError): index_table(['A','A'], 'id')
        with self.assertRaises(ValueError): index_table([''], 'id')

    def test_04_drug_cohort_equals_approved_source(self):
        expected = json.loads((ROOT / 'reports/qa/WP04/cohort_identity.json').read_text())
        self.assertEqual(set(self.graphs['no_ppi']['drug'].canonical_ids), {r['id'] for r in expected})

    def test_05_proteins_without_ppi_retained(self):
        expected = set(read('reports/qa/WP05/protein_registry.csv').accession)
        strict = set(self.mapping[self.mapping.strict_taxon_match].accession)
        self.assertEqual(len(expected - strict), 78)
        for g in self.graphs.values(): self.assertEqual(set(g['protein'].canonical_ids), expected)

    def test_06_typed_edges_identical_to_wp05(self):
        source = read('reports/qa/WP05/drug_protein_edges.csv')
        for g in self.graphs.values():
            di=g['drug'].canonical_ids; pi=g['protein'].canonical_ids
            actual={(di[a],pi[b],r) for r in ROLES for a,b in g['drug',r,'protein'].edge_index.t().tolist()}
            self.assertEqual(actual,set(source[['drug_id','accession','role']].itertuples(index=False,name=None)))
        self.assertEqual(source.role.value_counts().to_dict(), {'target':241,'transporter':135,'enzyme':78,'carrier':22})

    def test_07_all_masks_recomputed_from_input_sources(self):
        chem=pd.read_csv(ROOT/'reports/qa/WP04/chemical_features_clean.csv').set_index('id')
        source=read('reports/qa/WP05/drug_coverage.csv').set_index('id')
        for r in self.masks.itertuples():
            self.assertEqual(r.chemistry_qc_available, bool(chem.loc[r.drug_id,CHEM].notna().all()))
            self.assertEqual(r.protein_modality_available,source.loc[r.drug_id,'feature_proteins']>0)
        self.assertEqual(int(self.masks.chemistry_qc_available.sum()),54)
        self.assertEqual(int(self.masks.protein_modality_available.sum()),60)

    def test_08_wp04_eight_flags_exactly_preserved(self):
        source=read('reports/qa/WP04/structure_validation.csv').set_index('id')
        actual=self.masks.set_index('drug_id')
        self.assertEqual(set(actual[actual.molecule_review].index),set(source[~source.strict_qc_pass].index))
        self.assertEqual(int(actual.molecule_review.sum()),8)
        self.assertEqual(actual.review_flags.to_dict(),source.review_flags.to_dict())

    def test_09_tobramycin_methenamine_not_dropped_or_filled(self):
        for drug in ('DB00684','DB06799'):
            r=self.masks.set_index('drug_id').loc[drug]
            self.assertFalse(r.protein_modality_available)
            self.assertIn(drug,self.graphs['human_700']['drug'].canonical_ids)
        self.assertFalse(any('x' in g['drug'] or 'x' in g['protein'] for g in self.graphs.values()))

    def test_10_context_remains_80_unfeatured_not_in_graph(self):
        context=read('reports/qa/WP07/context_inventory_no_features.csv')
        self.assertEqual(len(context),80)
        self.assertFalse(context.sequence_feature_available.any())
        self.assertTrue(context.accessions.eq('').all())
        self.assertEqual(set(context.network_taxid.astype(str)),{'9606','511145'})
        self.assertEqual(self.summary['context_in_review_graphs'],0)

    def test_11_human_counts_and_symmetric_storage(self):
        for threshold,count in [(150,1200),(400,583),(700,184),(900,79)]:
            g=self.graphs[f'human_{threshold}']
            index=g['protein','ppi_human_review','protein'].edge_index
            pairs=set(map(tuple,index.t().tolist()))
            self.assertEqual(len(pairs),2*count)
            self.assertTrue(all((b,a) in pairs and a!=b for a,b in pairs))

    def test_12_human_k12_scopes_never_merged(self):
        self.assertNotIn(('protein','ppi_k12_scope_review','protein'),self.graphs['human_700'].edge_types)
        g=self.graphs['k12_review_700'];self.assertNotIn(('protein','ppi_human_review','protein'),g.edge_types)
        self.assertEqual(g['protein','ppi_k12_scope_review','protein'].num_edges,136)
        self.assertEqual(len(self.mapping[self.mapping.status.eq('exact_alias_exact_taxon')]),63)
        self.assertEqual(len(self.mapping[self.mapping.status.eq('exact_alias_K12_parent_scope_review')]),23)

    def test_13_cross_taxon_edge_injection_rejected(self):
        edges=self.source_edges.copy();mask=edges.network_taxid.astype(str).eq('9606');idx=edges[mask].index[0]
        edges.loc[idx,'protein2']='511145.b0001'
        with self.assertRaises(ValueError):select_ppi(edges,self.mapping,'human',700)
        g=copy.deepcopy(self.graphs['human_700'])
        bad=next(i for i,a in enumerate(g['protein'].canonical_ids) if a in set(self.mapping[self.mapping.status.eq('out_of_scope_organism')].accession))
        edge=g['protein','ppi_human_review','protein'].edge_index
        a=int(edge[0,0]);g['protein','ppi_human_review','protein'].edge_index=torch.tensor([[a,bad],[bad,a]])
        with self.assertRaises(ValueError):self.valid(g)

    def test_14_invalid_role_and_unknown_endpoint_rejected(self):
        with self.assertRaises(ValueError):edge_index([('D','UNKNOWN')],{'D':0},{'P':0})
        with self.assertRaises(ValueError):edge_index([('D','P'),('D','P')],{'D':0},{'P':0})
        g=copy.deepcopy(self.graphs['no_ppi']);g['drug','fake_target','protein'].edge_index=torch.empty((2,0),dtype=torch.long)
        with self.assertRaises(ValueError):self.valid(g)

    def test_15_pt_target_and_reverse_edges_rejected(self):
        for src,dst in [('drug','se_pt_audit'),('se_pt_audit','drug')]:
            g=copy.deepcopy(self.graphs['no_ppi']);g[src,'reported',dst].edge_index=torch.tensor([[0],[0]])
            with self.assertRaises(ValueError):self.valid(g)

    def test_16_label_or_quality_node_feature_injection_rejected(self):
        for field in ('x','y','pt_count','has_pt','kalite_skoru','combined_score'):
            g=copy.deepcopy(self.graphs['no_ppi']);g['drug'][field]=torch.ones(62)
            with self.assertRaises(ValueError):self.valid(g)
        g=copy.deepcopy(self.graphs['no_ppi']);g.pt_count=6416
        with self.assertRaises(ValueError):self.valid(g)

    def test_17_ppi_edge_attribute_injection_rejected(self):
        g=copy.deepcopy(self.graphs['human_700']);g['protein','ppi_human_review','protein'].edge_attr=torch.ones(368,1)
        with self.assertRaises(ValueError):self.valid(g)

    def test_18_feature_positive_allowlist_no_leaky_extra_columns(self):
        chem=pd.read_csv(ROOT/'reports/qa/WP04/chemical_features_clean.csv')
        self.assertEqual(feature_schema(chem,'id',CHEM).shape,(62,5))
        protein=pd.read_csv(ROOT/'reports/qa/WP05/protein_features.csv')
        self.assertEqual(feature_schema(protein,'accession',PROTEIN).shape,(141,56))
        for forbidden in ('has_pt','quality_score','pt_count','frequency'):
            broken=chem.assign(**{forbidden:1})
            with self.assertRaises(ValueError):feature_schema(broken,'id',CHEM)

    def test_19_positive_external_exactly_matches_source(self):
        source=read('reports/qa/WP03/drug_pt_positives.csv');source=source[source.conservative]
        actual=read('reports/qa/WP07/observed_pt_positives_external.csv')
        self.assertEqual(set(zip(actual.drug_id,actual.pt_cui)),set(zip(source.id,source.meddra_cui)))
        self.assertEqual(len(actual),6416);self.assertFalse(actual.duplicated(['drug_id','pt_cui']).any())
        self.assertEqual(set(actual.status),{'observed_positive'})

    def test_20_unknown_not_generated_as_negative(self):
        self.assertEqual(self.summary['negative_samples'],0)
        self.assertFalse(self.summary['splits_created'])
        self.assertFalse(self.summary['training_ready'])
        rows=read('reports/qa/WP07/label_strategy_comparison.csv').set_index('strategy')
        self.assertEqual(rows.loc['PT_CUI_audit','unknown_pairs'],62*1061-6416)
        self.assertEqual(rows.loc['historical_30_audit','unknown_pairs'],62*30-1011)

    def test_21_training_gate_remains_closed(self):
        for g in self.graphs.values():
            with self.assertRaises(RuntimeError):require_training_approval(g)

    def test_22_decisions_not_frozen(self):
        contract=json.loads((QA/'review_contract.json').read_text(encoding='utf-8'))
        self.assertEqual(len(contract['pending_decisions']),7)
        self.assertFalse(contract['feature_tensor_x_created'])
        self.assertIsNone(contract['feature_imputation'])
        self.assertFalse(read('reports/qa/WP07/ppi_scenarios.csv').final_choice.any())

    def test_23_executed_notebook_real_tables_and_figures(self):
        nb=nbformat.read(ROOT/'notebooks/WP07_data_integration.ipynb',as_version=4);nbformat.validate(nb)
        code=[c for c in nb.cells if c.cell_type=='code'];self.assertEqual(len(code),8)
        self.assertEqual([c.execution_count for c in code],list(range(1,9)))
        outputs=[o for c in code for o in c.outputs];self.assertFalse(any(o.output_type=='error' for o in outputs))
        self.assertEqual(sum('image/png' in o.get('data',{}) for o in outputs),6)
        self.assertTrue(any('DB00684' in o.get('data',{}).get('text/html','') for o in outputs))
        fig=ROOT/'reports/figures/WP07';self.assertEqual(len(list(fig.glob('*.png'))),6)
        html=(fig/'drug_modality_interactive.html').read_text(encoding='utf-8')
        self.assertNotIn('<script src=',html);self.assertIn('DB06799',html)

    def test_24_out_of_range_and_duplicate_edge_corruption(self):
        g=copy.deepcopy(self.graphs['no_ppi']);g['drug','target','protein'].edge_index[0,0]=62
        with self.assertRaises(ValueError):self.valid(g)
        g=copy.deepcopy(self.graphs['no_ppi']);idx=g['drug','target','protein'].edge_index
        g['drug','target','protein'].edge_index=torch.cat((idx,idx[:,:1]),dim=1)
        with self.assertRaises(ValueError):self.valid(g)

    def test_25_ppi_provenance_resolves_graph_edges(self):
        prov=read('reports/qa/WP07/ppi_edge_provenance.csv')
        for scenario,rows in prov.groupby('scenario'):
            graph=self.graphs[scenario];ids=graph['protein'].canonical_ids
            relation=next(e for e in graph.edge_types if e[0]==e[2]=='protein')
            pairs={tuple(sorted((ids[a],ids[b]))) for a,b in graph[relation].edge_index.t().tolist()}
            self.assertEqual(pairs,{tuple(sorted((r.accession1,r.accession2))) for r in rows.itertuples()})
            self.assertTrue(rows.source_lines.ne('').all())


if __name__=='__main__': unittest.main(verbosity=2)
