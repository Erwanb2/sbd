"""Is a perfect fit meaningful here, or just cheap? And do the best ones survive LOO?"""
import json, itertools, numpy as np
SP="/tmp/claude-1000/-mnt-c-Users-erwan-Documents-dev-projects-sbd/6bd5742a-9369-4889-9a3b-82993eae086f/scratchpad"
D=json.load(open(f"{SP}/matrix.json")); M=np.array(D["M"]); y=np.array(D["y"]); K=D["keys"]; N=D["names"]
n=len(y); FULL=(1<<n)-1
E=json.load(open(f"{SP}/exact.json")); rules={int(k):v for k,v in E["rules"].items()}
masks=np.array(list(rules.keys()), dtype=object)

def counts(target):
    subs=[m for m in rules if m & ~target & FULL == 0]
    sups=[m for m in rules if target & ~m == 0]
    o2=sum(1 for a,b in itertools.combinations(subs,2) if a|b==target)
    a2=sum(1 for a,b in itertools.combinations(sups,2) if a&b==target)
    o3=sum(1 for a,b,c in itertools.combinations(subs,3) if a|b|c==target)
    return len(subs), len(sups), o2, a2, o3

T=sum(1<<i for i in range(n) if y[i])
print("etiquettes reelles      :", "subs=%d sups=%d | OR2=%d AND2=%d OR3=%d" % counts(T))
rng=np.random.default_rng(0)
tot=[]
for r in range(12):
    yp=rng.permutation(y); Tp=sum(1<<i for i in range(n) if yp[i])
    c=counts(Tp); tot.append(c)
    print(f"etiquettes melangees #{r+1:<2}: subs={c[0]:4d} sups={c[1]:4d} | OR2={c[2]:5d} AND2={c[3]:5d} OR3={c[4]:7d}")
t=np.array(tot)
print(f"\nmoyenne sur etiquettes melangees : OR2={t[:,2].mean():.0f}, AND2={t[:,3].mean():.0f}, OR3={t[:,4].mean():.0f}")

# ---- LOO avec la STRUCTURE fixee (memes features, meme combinateur), seuils reappris
def best_thr(v, yy, s):
    b=(-1., None)
    for t_ in np.unique(v):
        a=float(np.mean(((v*s)>=t_*s)==yy))
        if a>b[0]: b=(a,t_)
    return b[1]
def loo_combo(feats, signs, mode):
    js=[K.index(f) for f in feats]; ok=0
    for i in range(n):
        tr=np.ones(n,bool); tr[i]=False
        preds=[]
        for j,s in zip(js,signs):
            t_=best_thr(M[tr,j], y[tr], s)          # each rule fitted alone on the fold
            preds.append((M[i,j]*s)>=t_*s)
        p = any(preds) if mode=="or" else all(preds)
        ok += int(p==bool(y[i]))
    return ok
print("\n=== LOO, structure fixee, seuils reappris a chaque pli ===")
cands=[]
for tag, key, mode in (("OR2","or2","or"), ("AND2","and2","and"), ("OR3","or3","or")):
    for score, parts in E[key][:60]:
        feats=[rules[m][0] for m in parts]; signs=[rules[m][2] for m in parts]
        if len(set(feats))<len(feats): continue
        cands.append((tag, mode, tuple(feats), tuple(signs), score))
seen=set(); out=[]
for tag,mode,feats,signs,score in cands:
    if feats in seen: continue
    seen.add(feats)
    out.append((loo_combo(feats,signs,mode), score, tag, feats, signs, mode))
out.sort(reverse=True)
for ok,score,tag,feats,signs,mode in out[:12]:
    desc=f" {mode.upper()} ".join(f"{f} {'>=' if s==1 else '<='}" for f,s in zip(feats,signs))
    print(f"  LOO {ok:2}/{n}  marge {score:5.2f}  [{tag}] {desc}")
json.dump([[ok,score,tag,list(feats),list(signs),mode] for ok,score,tag,feats,signs,mode in out[:40]],
          open(f"{SP}/candidats.json","w"))
