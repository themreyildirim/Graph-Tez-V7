"""Gerçek attributions ÖNCESİ analitik maske/normalizasyon kapısı."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wp11_graph_forward import protein_messages,typed_readout,query_logits,ExplanationCache,resolve_relation,pair_index_by_ids
from wp09_encoder import distinguishing_fixture,RoleMaskedPPI,ROLES,directed_edges
from wp10_molecular_graph import torch,numeric_digest


def fixture():
    # Drug d0 target:B,C; d1 target:A. Carrier edge only d0:C.
    q={'drug_ids':np.array(['d0','d1']),'unseen_protein_ids':np.array([],dtype=str),'chemistry':np.zeros((2,5)),
       'masks':np.array([[True,True,False,False,True],[True,True,False,False,False]])}
    for r in ROLES:q['role_'+r]=np.empty((2,0),dtype=np.int64)
    q['role_target']=np.array([[0,0,1],[1,2,0]],dtype=np.int64);q['role_carrier']=np.array([[0],[2]],dtype=np.int64)
    return q


class AnalyticGraphTests(unittest.TestCase):
    def test_01_fixed_vs_renormalized_PPI(self):
        m,x,p=distinguishing_fixture()
        with torch.no_grad():
            original=protein_messages(m,x,p);fixed=protein_messages(m,x,p,0,'fixed');deleted=protein_messages(m,x,p,0,'delete')
        # Remove A--B. B original degree2: remaining C contributes C/2 or C.
        torch.testing.assert_close(fixed['mean'][1],torch.tensor([1.,2.],dtype=torch.double))
        torch.testing.assert_close(deleted['mean'][1],torch.tensor([2.,4.],dtype=torch.double))
        torch.testing.assert_close(fixed['h'][1],torch.tensor([7.,4.],dtype=torch.double))
        torch.testing.assert_close(deleted['h'][1],torch.tensor([8.,6.],dtype=torch.double))
        self.assertEqual(fixed['degree'][1].item(),2);self.assertEqual(deleted['degree'][1].item(),1)
        self.assertEqual(int((fixed['weights']==0).sum()),2);self.assertEqual(deleted['directed_edges'].shape[1],2)

    def test_02_zero_intervention_equals_reference_encoder(self):
        m,x,p=distinguishing_fixture()
        with torch.no_grad():
            expected=m(x,directed_edges(p))
            for mode in ['fixed','delete']:torch.testing.assert_close(protein_messages(m,x,p,mode=mode)['h'],expected,rtol=0,atol=0)

    def test_03_role_count_and_last_mask(self):
        b=RoleMaskedPPI(hidden=2).double();pool=torch.tensor([[1.,2.],[3.,1.],[2.,4.]],dtype=torch.double);q=fixture()
        with torch.no_grad():
            ref=typed_readout(b,pool,q);fixed=typed_readout(b,pool,q,('target',0,1),'fixed');deleted=typed_readout(b,pool,q,('target',0,1),'delete')
            torch.testing.assert_close(ref['representation'][0,8:10],torch.tensor([2.5,2.5],dtype=torch.double))
            torch.testing.assert_close(fixed['representation'][0,8:10],torch.tensor([1.,2.],dtype=torch.double))
            torch.testing.assert_close(deleted['representation'][0,8:10],torch.tensor([2.,4.],dtype=torch.double))
            last_fixed=typed_readout(b,pool,q,('carrier',0,2),'fixed');last_delete=typed_readout(b,pool,q,('carrier',0,2),'delete')
            self.assertTrue(last_fixed['masks'][0,4]);self.assertFalse(last_delete['masks'][0,4])

    def test_04_zero_role_intervention_matches_reference(self):
        b=RoleMaskedPPI(hidden=2).double();q=fixture();pool=torch.arange(6,dtype=torch.double).reshape(3,2)
        with torch.no_grad():
            ref=b.readout(pool,torch.tensor(q['chemistry']),torch.tensor(q['masks']),{r:torch.tensor(q['role_'+r]) for r in ROLES})
            for mode in ['fixed','delete']:torch.testing.assert_close(typed_readout(b,pool,q,mode=mode)['representation'],ref['representation'],rtol=0,atol=0)

    def test_05_query_cache_and_other_drug_isolation(self):
        class Mini(torch.nn.Module):
            def __init__(self):
                super().__init__();self.base=RoleMaskedPPI(hidden=2);self.head=torch.nn.Linear(30,2)
        with torch.random.fork_rng():torch.manual_seed(41);m=Mini().eval()
        q=fixture();h=torch.arange(6,dtype=torch.float32).reshape(3,2);saved=h.clone();before=numeric_digest(m.state_dict());source=numeric_digest(q)
        cache=ExplanationCache(h,source,before,'none');args=(m,q,cache,torch.empty((0,2)),torch.zeros((2,8)),torch.ones(2,dtype=torch.bool),source)
        with torch.no_grad():
            base=query_logits(*args);changed=query_logits(*args,relation=('target',0,1))
        torch.testing.assert_close(base['logits'][1],changed['logits'][1],rtol=0,atol=0);torch.testing.assert_close(h,saved,rtol=0,atol=0)
        self.assertEqual(before,numeric_digest(m.state_dict()));self.assertEqual(source,numeric_digest(q))
        with self.assertRaises(ValueError):query_logits(*args[:-1],'wrong_graph')

    def test_06_protein_index_permutation(self):
        m,x,p=distinguishing_fixture();perm=np.array([2,0,3,1]);inverse=np.argsort(perm);remap=np.array(sorted([tuple(sorted((inverse[a],inverse[b]))) for a,b in p.T])).T
        with torch.no_grad():
            expected=protein_messages(m,x,p,0,'fixed')['h'];ix=np.flatnonzero((remap==np.sort(inverse[p[:,0]])[:,None]).all(0))[0]
            actual=protein_messages(m,x[perm],remap,int(ix),'fixed')['h'][inverse]
        torch.testing.assert_close(actual,expected,rtol=0,atol=0)

    def test_07_ID_and_role_alignment(self):
        q=fixture();g={'protein_ids':np.array(['A','B','C']),'ppi_pairs_700':np.array([[0,1],[1,2]])}
        self.assertEqual(resolve_relation(g,q,'d0','target','B'),('target',0,1));self.assertEqual(resolve_relation(g,q,'d0','carrier','C'),('carrier',0,2))
        self.assertEqual(pair_index_by_ids(g,'B','A'),pair_index_by_ids(g,'A','B'))
        with self.assertRaises(ValueError):resolve_relation(g,q,'d1','carrier','C')
        with self.assertRaises(ValueError):pair_index_by_ids(g,'A','C')

    def test_08_repeat_and_source_immutable(self):
        m,x,p=distinguishing_fixture();before=numeric_digest({'x':x,'p':p,'state':numeric_digest(m.state_dict())})
        with torch.no_grad():
            one=protein_messages(m,x,p,0);two=protein_messages(m,x,p,0)
        torch.testing.assert_close(one['h'],two['h'],rtol=0,atol=0);self.assertEqual(before,numeric_digest({'x':x,'p':p,'state':numeric_digest(m.state_dict())}))

    def test_09_noPPI_inactive_path_control(self):
        m,x,p=distinguishing_fixture()
        with torch.no_grad():
            one=protein_messages(m,x,p,ppi_enabled=False);two=protein_messages(m,x,p,0,ppi_enabled=False)
        torch.testing.assert_close(one['h'],two['h'],rtol=0,atol=0);self.assertEqual(two['mean'].abs().sum().item(),0)

    def test_10_absent_paths_and_single_role_abstention(self):
        b=RoleMaskedPPI(hidden=2).double();q=fixture();q['masks'][1,0]=False;pool=torch.ones((3,2),dtype=torch.double)
        with torch.no_grad():
            self.assertTrue(typed_readout(b,pool,q,('target',1,0),'fixed')['eligible'][1])
            self.assertFalse(typed_readout(b,pool,q,('target',1,0),'delete')['eligible'][1])
        with self.assertRaises(ValueError):typed_readout(b,pool,q,('enzyme',0,2))


if __name__=='__main__':unittest.main(verbosity=2)
