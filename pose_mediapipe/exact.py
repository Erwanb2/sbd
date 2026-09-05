"""Exact search for rule combinations that fit all 27 clips.

Every atomic rule (feature >= threshold, or <=) becomes a 27-bit mask of the clips it
calls sumo. A combination is perfect when its mask equals the ground-truth mask, so the
search is set cover on bitmasks - exhaustive rather than sampled.
"""
import json, itertools, numpy as np
from collections import defaultdict
SP="/tmp/claude-1000/-mnt-c-Users-erwan-Documents-dev-projects-sbd/6bd5742a-9369-4889-9a3b-82993eae086f/scratchpad"
D=json.load(open(f"{SP}/matrix.json")); M=np.array(D["M"]); y=np.array(D["y"]); K=D["keys"]; N=D["names"]
n=len(y); TARGET=sum(1<<i for i in range(n) if y[i])
FULL=(1<<n)-1

def family(k):
    for pat,f in (("ank","chevilles"),("hee","talons"),("toe","orteils"),("kne","genoux"),
                  ("hip","hanches"),("wri","poignets"),("wr_in","poignets"),("elb","coudes"),
                  ("el_in","coudes"),("abduction","abduction"),("foot_","pieds"),("shin","tibias"),
                  ("torso","tronc"),("view","angle"),("vis_","visibilite"),("leg_m","taille"),
                  ("arm","bras"),("knee_","genoux"),("hip_","hanches")):
        if pat in k: return f
    return "autre"

# --- toutes les regles atomiques, dedupliquees par masque
rules={}   # mask -> (feature, thr, sign, margin)
for j in range(M.shape[1]):
    v=M[:,j]
    if np.allclose(v,v[0]): continue
    sd=v.std()+1e-9
    for t in np.unique(v):
        for s in (1,-1):
            pred=(v*s)>=t*s
            m=int(sum(1<<i for i in range(n) if pred[i]))
            if m in (0,FULL): continue
            pos=v[pred]; neg=v[~pred]
            marg=float((abs(pos*s).min()-abs(neg*s).max())/sd)
            prev=rules.get(m)
            if prev is None or marg>prev[3]: rules[m]=(K[j], float(t), s, marg)
print(f"{len(rules)} regles atomiques distinctes (par masque) sur {n} clips")

subs=[m for m in rules if m & ~TARGET & FULL == 0]      # ne se trompe jamais en disant sumo
sups=[m for m in rules if TARGET & ~m == 0]             # n'oublie jamais un sumo
print(f"  {len(subs)} regles sans faux positif, {len(sups)} regles sans faux negatif\n")

def show(tag, combos, limit=8):
    print(f"=== {tag} : {len(combos)} solutions parfaites ===")
    for score, parts in combos[:limit]:
        desc=" ".join(f"[{rules[m][0]} {'>=' if rules[m][2]==1 else '<='} {rules[m][1]:.2f}]" for m in parts)
        fams=sorted({family(rules[m][0]) for m in parts})
        print(f"  marge {score:5.2f}  familles {','.join(fams):28} {desc}")
    print()

# --- OR de 2 regles sans faux positif
ors=[]
for a,b in itertools.combinations(subs,2):
    if a|b==TARGET: ors.append((min(rules[a][3],rules[b][3]), (a,b)))
ors.sort(reverse=True); show("OR de 2 regles", ors)

# --- AND de 2 regles sans faux negatif
ands=[]
for a,b in itertools.combinations(sups,2):
    if a&b==TARGET: ands.append((min(rules[a][3],rules[b][3]), (a,b)))
ands.sort(reverse=True); show("AND de 2 regles", ands)

# --- OR de 3
ors3=[]
for a,b,c in itertools.combinations(subs,3):
    if a|b|c==TARGET: ors3.append((min(rules[a][3],rules[b][3],rules[c][3]), (a,b,c)))
ors3.sort(reverse=True); show("OR de 3 regles", ors3, 5)

json.dump({"rules":{str(m):rules[m] for m in rules},
           "or2":[[s,list(p)] for s,p in ors[:400]],
           "and2":[[s,list(p)] for s,p in ands[:400]],
           "or3":[[s,list(p)] for s,p in ors3[:200]]}, open(f"{SP}/exact.json","w"))
