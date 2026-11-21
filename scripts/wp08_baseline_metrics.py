"""Observed-record proxy ölçümleri; unknown biyolojik negatif değildir.

AP adım ağırlıklı average precision, trapez PR-AUC değildir. Tek proxy sonucu
olan drug/class metriği NA. Bootstrap birimi ilaç/yapısal grup, çift/fold değil.
"""
import numpy as np

SEMANTICS='Observed SIDER record ranking proxy; unknown is NOT a verified biological negative; not clinical risk'
METRICS=('drug_macro_AP','micro_AP','class_macro_AP','micro_AUROC','class_macro_AUROC')


class RankingCache:
    def __init__(self,y,score,drug_index):
        y=np.asarray(y,dtype=float);score=np.asarray(score,dtype=float)
        order=np.argsort(-score,kind='stable')
        self.y=y[order];self.drug=np.asarray(drug_index,dtype=int)[order]
        s=score[order]
        self.ends=np.r_[np.flatnonzero(s[1:]!=s[:-1]),len(s)-1] if len(s) else np.array([],dtype=int)

    def evaluate(self,drug_weights):
        w=np.asarray(drug_weights,dtype=float)
        if w.ndim==1:w=w[None,:]
        if not len(self.y):return np.full(len(w),np.nan),np.full(len(w),np.nan)
        pair_w=w[:,self.drug]
        tp=np.cumsum(pair_w*self.y,axis=1)[:,self.ends]
        up=np.cumsum(pair_w*(1-self.y),axis=1)[:,self.ends]
        dp=np.diff(tp,prepend=0,axis=1);du=np.diff(up,prepend=0,axis=1)
        p=tp[:,-1];u=up[:,-1];ok=(p>0)&(u>0)
        precision=np.divide(tp,tp+up,out=np.zeros_like(tp),where=(tp+up)>0)
        ap=np.divide((dp*precision).sum(axis=1),p,out=np.full(len(w),np.nan),where=ok)
        auc=np.divide((dp*(u[:,None]-up+.5*du)).sum(axis=1),p*u,out=np.full(len(w),np.nan),where=ok)
        return ap,auc


def mean_or_na(values,axis=None):
    a=np.asarray(values,dtype=float);ok=np.isfinite(a)
    count=ok.sum(axis=axis);total=np.where(ok,a,0).sum(axis=axis)
    return np.divide(total,count,out=np.full(np.shape(total),np.nan),where=count>0)


class MetricPanel:
    """Ragged OOF matrix: unavailable target/abstention score NaN, never zero label."""
    def __init__(self,y,scores,drug_ids,class_ids):
        self.y=np.asarray(y,dtype=float);self.scores=np.asarray(scores,dtype=float)
        self.ids=list(drug_ids);self.classes=list(class_ids);n=len(self.ids)
        if self.y.shape!=self.scores.shape or self.y.shape!=(n,len(self.classes)):raise ValueError('Metric shape mismatch')
        self.mask=np.isfinite(self.scores)
        self.drug_AP=np.full(n,np.nan)
        self.drug_support=[]
        for i in range(n):
            mask=self.mask[i];yy=self.y[i,mask];ss=self.scores[i,mask]
            cache=RankingCache(yy,ss,np.zeros(len(yy),dtype=int))
            self.drug_AP[i]=cache.evaluate(np.ones(1))[0][0]
            self.drug_support.append({'drug_id':self.ids[i],'scored_targets':int(mask.sum()),'observed_positive':int(yy.sum()),
                'unobserved_NOT_verified_negative':int(len(yy)-yy.sum()),'drug_AP':self.drug_AP[i],
                'NA_reason':'no_scored_targets' if not len(yy) else 'no_observed_positive' if yy.sum()==0 else 'no_unknown_reference' if yy.sum()==len(yy) else ''})
        ii,jj=np.where(self.mask)
        self.micro=RankingCache(self.y[ii,jj],self.scores[ii,jj],ii)
        self.by_class=[]
        for j in range(len(self.classes)):
            idx=np.flatnonzero(self.mask[:,j]);self.by_class.append(RankingCache(self.y[idx,j],self.scores[idx,j],idx))

    def evaluate(self,weights=None,chunk=32):
        if weights is None:weights=np.ones((1,len(self.ids)))
        w=np.asarray(weights,dtype=float)
        if w.ndim==1:w=w[None,:]
        result={m:np.full(len(w),np.nan) for m in METRICS}
        ok=np.isfinite(self.drug_AP);a=np.where(ok,self.drug_AP,0)
        denom=(w*ok).sum(axis=1)
        result['drug_macro_AP']=np.divide(w@a,denom,out=np.full(len(w),np.nan),where=denom>0)
        for start in range(0,len(w),chunk):
            ww=w[start:start+chunk];ap,auc=self.micro.evaluate(ww);result['micro_AP'][start:start+len(ww)]=ap
            result['micro_AUROC'][start:start+len(ww)]=auc
            cap=[];cauc=[]
            for c in self.by_class:
                aa,uu=c.evaluate(ww);cap.append(aa);cauc.append(uu)
            if cap:
                result['class_macro_AP'][start:start+len(ww)]=mean_or_na(np.array(cap),axis=0)
                result['class_macro_AUROC'][start:start+len(ww)]=mean_or_na(np.array(cauc),axis=0)
        return result

    def class_support(self):
        rows=[]
        for cls,c in zip(self.classes,self.by_class):
            n=len(c.y);p=int(c.y.sum());ap,auc=c.evaluate(np.ones(len(self.ids)))
            rows.append({'class_id':cls,'scored_drugs':n,'observed_positive':p,'unobserved_NOT_verified_negative':n-p,
                         'AP':ap[0],'AUROC':auc[0],'NA_reason':'no_scores' if n==0 else 'no_observed_positive' if p==0 else 'no_unknown_reference' if p==n else ''})
        return rows


def grouped_bootstrap_weights(drug_ids,group_map,reps,seed):
    ids=list(drug_ids)
    if set(ids)!=set(group_map):raise ValueError('Group identity coverage')
    groups=sorted(set(group_map.values()));positions={g:i for i,g in enumerate(groups)}
    rng=np.random.default_rng(seed)
    counts=np.array([np.bincount(rng.integers(0,len(groups),size=len(groups)),minlength=len(groups)) for _ in range(reps)])
    return counts[:,[positions[group_map[d]] for d in ids]].astype(float)


def percentile_interval(samples,min_valid=800):
    values=np.asarray(samples,dtype=float);finite=values[np.isfinite(values)]
    if len(finite)<min_valid:return None,None,len(finite),'insufficient_valid_group_bootstrap_replicates'
    low,high=np.quantile(finite,[.025,.975]);return float(low),float(high),len(finite),''
