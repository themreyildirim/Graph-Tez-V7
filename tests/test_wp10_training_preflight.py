"""Gerçek trainer öncesi referans denklem,train-only API ve sızıntı testleri."""
import sys,copy,unittest,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wp10_train as t
from wp10_molecular_encoder import initialized_model,load_context
from wp10_training_forward import prepare,train_forward,query_forward


class TrainingPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t.configure_runtime();cls.store=t.get_store();cls.source=t.source_labels()
        cls.jobs=pd.read_csv(t.QA/'training_jobs_frozen.csv',keep_default_na=False)

    def test_01_prepared_forward_and_gradients_match_reference_all_four(self):
        g,q,tm,qm=load_context('primary_o01_final',self.store)
        for variant in t.NAMES:
            ref=initialized_model(num_targets=3);fast=copy.deepcopy(ref)
            a=ref.encode_train(g,tm,variant);b=train_forward(fast,prepare(fast,g,tm),variant)
            t.torch.testing.assert_close(a['logits'],b['logits'],rtol=0,atol=0,equal_nan=True)
            c=ref.encode_query(g,q,qm,a['cache']);d=query_forward(fast,prepare(fast,q,qm),b['protein_h'],variant)
            t.torch.testing.assert_close(c['logits'],d['logits'],rtol=0,atol=0,equal_nan=True)
            a['logits'][a['eligible']].sum().backward();b['logits'][b['eligible']].sum().backward()
            for (name,p),(_,other) in zip(ref.named_parameters(),fast.named_parameters()):
                if p.grad is None:self.assertIsNone(other.grad)
                else:t.torch.testing.assert_close(p.grad,other.grad,rtol=0,atol=0)

    def test_02_frozen_jobs_have_only_four_and_same_shared_inner(self):
        self.assertEqual(len(self.jobs),152);self.assertEqual(set(self.jobs.variant),set(t.NAMES))
        self.assertTrue(self.jobs.null_file.eq('').all())
        self.assertNotIn('primary_o02_i01',set(self.jobs.context));self.assertNotIn('stress_o02_i02',set(self.jobs.context))
        self.assertTrue(self.jobs.groupby('context').init_seed.nunique().eq(1).all())

    def test_03_actual_trainer_outer_label_feature_mutation_isolated(self):
        job=self.jobs[self.jobs.context.eq('primary_o01_i01')&self.jobs.variant.eq('A1P1')].iloc[0].to_dict()
        g,q,k,n,v,y,yv,s=t.context_arguments(job,self.source)
        held=set(s['test_query_ids']);mutated=self.source[~self.source.drug_id.isin(held)]
        mutated=pd.concat([mutated,pd.DataFrame({'drug_id':list(held),'class_id':['HELDOUT_LABEL_MUTATION']*len(held)})])
        g2,q2,k2,n2,v2,y2,yv2,s2=t.context_arguments(job,mutated)
        q2['chemistry'][q2['split']=='test']=1e9;v2=t.select_query(q2,list(v2['drug_ids']),len(g2['protein_ids']))
        store2=copy.deepcopy(self.store)
        for d in held:
            # Only heldout molecular values mutate;caller API never passes these to fit.
            store2.graphs[d].x.zero_()
        m,h,i=t.fit_model(g,y,k,'A1P1',job['init_seed'],validation=v,validation_labels=yv,max_epochs=3)
        other,hh,ii=t.fit_model(g2,y2,k2,'A1P1',job['init_seed'],validation=v2,validation_labels=yv2,max_epochs=3,store=store2)
        self.assertEqual(i['selected_state_sha256'],ii['selected_state_sha256'])
        np.testing.assert_array_equal(h.validation_drug_AP,hh.validation_drug_AP)

    def test_04_train_proxy_single_outcome_and_test_validation_rejected(self):
        job=self.jobs.iloc[0].to_dict();g,q,k,n,v,y,yv,s=t.context_arguments(job,self.source)
        with self.assertRaises(ValueError):t.fit_model(g,{d:{'ALL'} for d in y},['ALL'],'A0P0',1,fixed_epochs=1)
        wrong={key:a.copy() for key,a in v.items()};wrong['split'][:]='test'
        with self.assertRaises(ValueError):t.fit_model(g,y,k,'A0P0',1,validation=wrong,validation_labels=yv,max_epochs=1)
        with self.assertRaises(ValueError):t.proxy_matrix({**y,'HELDOUT':set()},list(y),k)

    def test_05_optimizer_gradients_and_off_switches_real_trainer(self):
        job=self.jobs[self.jobs.context.eq('primary_o01_i01')].iloc[0].to_dict();g,q,k,n,v,y,yv,s=t.context_arguments(job,self.source)
        init=[]
        for arm in t.NAMES:
            m,h,info=t.fit_model(g,y,k,arm,job['init_seed'],fixed_epochs=2)
            self.assertEqual(info['status'],'OK');self.assertEqual(info['optimizer_steps'],2)
            self.assertGreater(info['selected_state_L2_change'],0);init.append(info['initial_state_sha256'])
            if arm.startswith('A0'):
                self.assertEqual(info['maximum_atom_message_gradient_norm'],0);self.assertEqual(info['molecular_state_L2_change'],0)
            else:self.assertGreater(info['maximum_atom_message_gradient_norm'],0);self.assertGreater(info['maximum_bond_message_gradient_norm'],0)
            if arm.endswith('0'):self.assertEqual(info['maximum_message_gradient_norm'],0)
            else:self.assertGreater(info['maximum_message_gradient_norm'],0)
        self.assertEqual(len(set(init)),1)

    def test_06_finite_fit_failure_stays_NA(self):
        job=self.jobs.iloc[0].to_dict();g,q,k,n,v,y,yv,s=t.context_arguments(job,self.source)
        bad={key:a.copy() for key,a in g.items()};bad['protein_x'][0,0]=np.nan
        with self.assertRaises(ValueError):t.fit_model(bad,y,k,'A0P0',1,fixed_epochs=1)


if __name__=='__main__':unittest.main(verbosity=2)
