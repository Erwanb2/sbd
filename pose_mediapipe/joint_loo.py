"""LOO for rule combinations, optimising the thresholds JOINTLY on each training fold.

Fitting a conjunction's thresholds one rule at a time is the wrong question: neither rule
is meant to be good alone. This searches the threshold grid of the combination itself.
"""
import json, itertools, numpy as np
SP="/tmp/claude-1000/-mnt-c-Users-erwan-Documents-dev-projects-sbd/6bd5742a-9369-4889-9a3b-82993eae086f/scratchpad"
D=json.load(open(f"{SP}/matrix.json")); M=np.array(D["M"]); y=np.array(D["y"]); K=D["keys"]; N=D["names"]
n=len(y)

def fit_joint(js, signs, mode, tr):
    """Best thresholds for the combination, on the training rows only."""
    grids=[np.unique(M[tr,j]) for j in js]
    best=(-1,None)
    for combo in itertools.product(*grids):
        preds=[(M[tr,j]*s)>=t*s for j,s,t in zip(js,signs,combo)]
        p=preds[0].copy()
        for q in preds[1:]: p = (p|q) if mode=="or" else (p&q)
        a=float(np.mean(p==y[tr]))
        if a>best[0]: best=(a,combo)
    return best[1]

def loo(feats, signs, mode):
    js=[K.index(f) for f in feats]; ok=0; errs=[]
    for i in range(n):
        tr=np.ones(n,bool); tr[i]=False
        thr=fit_joint(js, signs, mode, tr)
        preds=[(M[i,j]*s)>=t*s for j,s,t in zip(js,signs,thr)]
        p=preds[0]
        for q in preds[1:]: p = (p or q) if mode=="or" else (p and q)
        ok+=int(bool(p)==bool(y[i]))
        if bool(p)!=bool(y[i]): errs.append(N[i].replace(".mp4","")[:20])
    return ok, errs

E=json.load(open(f"{SP}/exact.json")); rules={int(k):v for k,v in E["rules"].items()}
cands=[]
for key,mode in (("and2","and"),("or2","or"),("or3","or")):
    for score,parts in E[key][:40]:
        feats=tuple(rules[m][0] for m in parts); signs=tuple(rules[m][2] for m in parts)
        if len(set(feats))<len(feats): continue
        cands.append((mode,feats,signs,score))
seen=set(); res=[]
for mode,feats,signs,score in cands:
    key=(mode,feats)
    if key in seen: continue
    seen.add(key)
    ok,errs=loo(feats,signs,mode)
    res.append((ok,score,mode,feats,signs,errs))
res.sort(reverse=True)
print(f"{'LOO':>7} {'marge':>6}  combinaison (seuils optimises conjointement a chaque pli)")
for ok,score,mode,feats,signs,errs in res[:14]:
    d=f" {mode.upper()} ".join(f"{f} {'>=' if s==1 else '<='}" for f,s in zip(feats,signs))
    print(f"  {ok:2}/{n} {score:6.2f}  {d}")
    if errs: print(f"          rates: {', '.join(errs)}")
json.dump([[ok,score,mode,list(feats),list(signs),errs] for ok,score,mode,feats,signs,errs in res[:20]],
          open(f"{SP}/joint_results.json","w"))
