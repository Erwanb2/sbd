"""Can several rules do better than one - and can they say 'I don't know'?

Three designs, all scored with nested leave-one-out: the rules, their thresholds and
the abstention band are chosen on the training folds only, never on the held-out clip.
"""
import json, itertools, numpy as np
SP="/tmp/claude-1000/-mnt-c-Users-erwan-Documents-dev-projects-sbd/6bd5742a-9369-4889-9a3b-82993eae086f/scratchpad"
D=json.load(open(f"{SP}/matrix.json")); M=np.array(D["M"]); y=np.array(D["y"]); K=D["keys"]; N=D["names"]
n, p = M.shape
usable=[j for j in range(p) if not np.allclose(M[:,j], M[0,j])]

def best_rule(v, yy):
    b=(-1., None, 1)
    for t in np.unique(v):
        for s in (1,-1):
            a=float(np.mean(((v*s)>=t*s)==yy))
            if a>b[0]: b=(a,t,s)
    return b

def margin_of(v, yy, t, s):
    """Normalised gap between the two classes at that threshold - a tie-break that prefers safe cuts."""
    pos=v[(v*s)>=t*s]; neg=v[(v*s)<t*s]
    if not len(pos) or not len(neg): return 0.
    return float((abs(pos*s).min()-abs(neg*s).max())/(v.std()+1e-9))

def pick_committee(tr, yy, k=7, maxcorr=0.85):
    """Greedy: best training rules, skipping any feature too correlated with one already in."""
    scored=[]
    for j in usable:
        a,t,s=best_rule(M[tr,j], yy)
        scored.append((a, margin_of(M[tr,j],yy,t,s), j, t, s))
    scored.sort(key=lambda r:(-r[0], -r[1]))
    chosen=[]
    for a,m,j,t,s in scored:
        if len(chosen)>=k: break
        if any(abs(np.corrcoef(M[tr,j], M[tr,j2])[0,1])>maxcorr for _,_,j2,_,_ in chosen): continue
        chosen.append((a,m,j,t,s))
    return chosen

def vote(row, committee):
    return sum(1 if (row[j]*s)>=t*s else -1 for _,_,j,t,s in committee)

print(f"{n} clips, {y.sum()} sumo, {len(usable)} features\n")

# ---------- 1. comite de regles, sans abstention ----------
print("=== 1. comite de 7 regles decorrelees, vote a la majorite (LOO imbriquee) ===")
ok=0; votes=[]
for i in range(n):
    tr=np.ones(n,bool); tr[i]=False
    c=pick_committee(tr, y[tr]); v=vote(M[i], c); votes.append(v)
    pred=int(v>0); ok+=pred==y[i]
    if pred!=y[i]: print(f"   rate: {N[i][:40]:42} vrai={'sumo' if y[i] else 'conv'}  vote {v:+d}/7")
print(f"   {ok}/{n} = {ok/n:.2f}\n")

# ---------- 2. le meme comite, mais il a le droit de s'abstenir ----------
print("=== 2. le comite peut dire 'doute' quand il n'est pas net (LOO imbriquee) ===")
for need in (3, 5, 7):
    dec=cor=0; abst=[]
    for i in range(n):
        if abs(votes[i]) < need: abst.append(i); continue
        dec+=1; cor+=int((votes[i]>0)==y[i])
    print(f"   |vote| >= {need}/7 : {dec}/{n} clips tranches ({dec/n:.0%}), {cor}/{dec} corrects"
          + (f" = {cor/dec:.2f}" if dec else "")
          + (f"   doutes: {', '.join(N[i].replace('.mp4','')[:22] for i in abst)}" if abst else ""))

# ---------- 3. une regle unique + garde-fous explicites (angle, visibilite, marge) ----------
print("\n=== 3. regle unique + garde-fous lisibles (LOO imbriquee) ===")
jv, jl = K.index("all_view"), K.index("all_vis_legs")
for band in (0.0, 0.15, 0.30):
    dec=cor=0; abst=[]
    for i in range(n):
        tr=np.ones(n,bool); tr[i]=False
        scored=sorted(((best_rule(M[tr,j],y[tr])[0], j) for j in usable), reverse=True)
        j=scored[0][1]; _,t,s=best_rule(M[tr,j], y[tr])
        sd=M[tr,j].std()
        unsure = abs(M[i,j]-t) < band*sd or M[i,jv] < 0.30 and abs(M[i,j]-t) < 2*band*sd
        if unsure: abst.append(i); continue
        dec+=1; cor+=int(((M[i,j]*s)>=t*s)==y[i])
    lab=f"bande +/-{band:.2f} ecart-type" + (" (aucune abstention)" if band==0 else "")
    print(f"   {lab:44} {dec}/{n} tranches ({dec/n:.0%}), {cor}/{dec} corrects = {cor/dec:.2f}")
    if abst: print(f"      doutes: {', '.join(N[i].replace('.mp4','')[:22] for i in abst)}")
