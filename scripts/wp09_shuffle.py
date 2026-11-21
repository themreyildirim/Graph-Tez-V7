"""Etiket-kör, degree-preserving basit yönsüz PPI yeniden bağlama."""
import hashlib
import numpy as np


SHUFFLE_POLICY={'swaps_per_edge':10,'attempts_per_edge':200,'minimum_changed_fraction':0.5,
    'seed_base':20261106,'seed_formula':'base + 10000 + 100*sorted_context_index + threshold',
    'design_nulls_per_context_threshold':1,'future_proposed_null_replicates':3,
    'failure':'NA_shuffle_insufficient; no unchanged-graph fallback','label_or_performance_selection':False}


def edge_hash(pairs):
    return hashlib.sha256(';'.join(f'{a},{b}' for a,b in sorted(pairs)).encode()).hexdigest()


def shuffle_pairs(pairs,nodes,seed,swaps_per_edge=10,attempts_per_edge=200,minimum_changed_fraction=.5):
    original=[tuple(map(int,e)) for e in pairs]
    if len(set(original))!=len(original) or any(a>=b or a<0 or b>=nodes for a,b in original):
        raise ValueError('Unique canonical simple in-universe pairs required')
    if swaps_per_edge<0 or attempts_per_edge<0 or not 0<=minimum_changed_fraction<=1:raise ValueError('Invalid shuffle policy')
    current=set(original);array=sorted(current);rng=np.random.default_rng(seed)
    wanted=swaps_per_edge*len(array);budget=attempts_per_edge*len(array);accepted=attempts=0
    while len(array)>=2 and accepted<wanted and attempts<budget:
        attempts+=1;i,j=rng.choice(len(array),2,replace=False)
        a,b=array[i];c,d=array[j]
        if rng.integers(2):a,b=b,a
        if rng.integers(2):c,d=d,c
        if len({a,b,c,d})!=4:continue
        first=tuple(sorted((a,d)));second=tuple(sorted((c,b)))
        if first in current or second in current or first==second:continue
        current.remove(array[i]);current.remove(array[j]);current.update((first,second))
        array[i]=first;array[j]=second;accepted+=1
    changed=len(set(original)-current)/len(original) if original else 0.
    before=np.bincount(np.array(original,dtype=int).ravel(),minlength=nodes)
    after=np.bincount(np.array(sorted(current),dtype=int).ravel(),minlength=nodes)
    assert len(current)==len(original) and np.array_equal(before,after)
    success=bool(original) and accepted>=wanted and changed>=minimum_changed_fraction
    return sorted(current),{'seed':int(seed),'nodes':nodes,'edges':len(original),'requested_successful_swaps':wanted,
        'successful_swaps':accepted,'attempts':attempts,'attempt_budget':budget,'changed_fraction':changed,
        'minimum_changed_fraction':minimum_changed_fraction,'degree_sequence_exact':True,
        'real_edge_sha256':edge_hash(original),'shuffled_edge_sha256':edge_hash(current),
        'status':'OK_degree_preserving_null' if success else 'NA_shuffle_insufficient',
        'statistical_uniform_mixing_claim':False}
