import sys, json, unittest
from pathlib import Path
import networkx as nx
import nbformat

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from wp01_graphs import real_graph, toy_graph, metrics

class GraphConceptTests(unittest.TestCase):
    def test_directed_reachability_differs_from_undirected(self):
        g=nx.DiGraph([('a','b'),('b','c')])
        self.assertFalse(nx.has_path(g,'c','a'))
        self.assertTrue(nx.has_path(g.to_undirected(),'c','a'))

    def test_weight_as_distance_changes_shortest_path(self):
        g=nx.Graph();g.add_weighted_edges_from([('a','b',1),('b','c',1),('a','c',5)])
        self.assertEqual(nx.shortest_path(g,'a','c'),['a','c'])
        self.assertEqual(nx.shortest_path(g,'a','c',weight='weight'),['a','b','c'])

    def test_known_betweenness_and_disconnected_closeness(self):
        g=nx.path_graph(['a','b','c']);g.add_node('isolated')
        m=metrics(g).set_index('node')
        self.assertAlmostEqual(m.loc['b','betweenness'],1/3)
        self.assertAlmostEqual(m.loc['b','closeness_WF'],2/3)
        self.assertEqual(m.loc['isolated','closeness_WF'],0)

    def test_exact_vs_within_hops_and_subgraph(self):
        g=toy_graph();d=nx.single_source_shortest_path_length(g,'A',cutoff=2)
        self.assertEqual({n for n,k in d.items() if k==2},{'D'})
        self.assertEqual(set(nx.ego_graph(g,'A',radius=2)),{'A','B','C','D'})
        self.assertEqual(g.subgraph(['A','B','C']).number_of_edges(),3)

class RealGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample=json.loads((ROOT/'reports/qa/wp01_graph_sample.json').read_text(encoding='utf-8'))
        cls.g=real_graph(cls.sample)

    def test_provenance_and_selection(self):
        self.assertEqual(self.sample['source_id'],'1SkXYX0w4k76yxwHZbLydz6Q5Aj9gA7cz')
        self.assertEqual(self.sample['source_rows'],153)
        self.assertEqual(len({r['source_row'] for r in self.sample['relations']}),10)
        for r in self.sample['relations']:
            self.assertIn(r['DrugBank_ID'],self.sample['selection']['drug_ids'])
            self.assertIn(r['Organizma'],self.sample['selection']['organism_strings'])
            self.assertTrue(2<=r['source_row']<=154)

    def test_graph_structure_and_no_fabricated_weights(self):
        g=self.g;u=g.to_undirected()
        self.assertEqual((len(g),g.number_of_edges()),(9,10))
        self.assertEqual(sorted(map(len,nx.connected_components(u))),[2,7])
        self.assertTrue(nx.is_bipartite(u))
        self.assertEqual(sum(dict(u.degree()).values()),20)
        for a,b,data in g.edges(data=True):
            self.assertEqual((g.nodes[a]['kind'],g.nodes[b]['kind']),('drug','protein'))
            self.assertNotIn('weight',data)
        self.assertFalse(any('kalite_skoru' in d for _,d in g.nodes(data=True)))

    def test_duplicate_source_pair_rejected(self):
        s=dict(self.sample);s['relations']=self.sample['relations']*2
        with self.assertRaises(ValueError):real_graph(s)

    def test_executed_notebook_has_tables_images_and_no_errors(self):
        nb=nbformat.read(ROOT/'notebooks/WP01_graf_temelleri.ipynb',as_version=4)
        nbformat.validate(nb)
        code=[c for c in nb.cells if c.cell_type=='code']
        self.assertTrue(all(c.execution_count is not None and c.outputs for c in code))
        outputs=[o for c in code for o in c.outputs]
        self.assertFalse(any(o.output_type=='error' for o in outputs))
        self.assertGreaterEqual(sum('image/png' in o.get('data',{}) for o in outputs),9)
        self.assertGreaterEqual(sum('text/html' in o.get('data',{}) for o in outputs),10)

if __name__=='__main__':unittest.main(verbosity=2)
