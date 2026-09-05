"""Two targeted designs: a camera-aware rule, and a 'do the normalisations agree?' detector."""
import json, numpy as np
SP="/tmp/claude-1000/-mnt-c-Users-erwan-Documents-dev-projects-sbd/6bd5742a-9369-4889-9a3b-82993eae086f/scratchpad"
D=json.load(open(f"{SP}/matrix.json")); M=np.array(D["M"]); y=np.array(D["y"]); K=D["keys"]; N=D["names"]
n=len(y); jv=K.index("all_view"); jl=K.index("all_vis_legs")

def best_rule(v,yy):
    b=(-1.,None,1)
    for t in np.unique(v):
        for s in (1,-1):
            a=float(np.mean(((v*s)>=t*s)==yy))
            if a>b[0]: b=(a,t,s)
    return b

def report(tag, dec, cor, abst):
    print(f"  {tag:52} {dec:2}/{n} tranches ({dec/n:3.0%}), {cor}/{dec} corrects"
          + (f" = {cor/dec:.2f}" if dec else "")
          + (f"\n      doutes: {', '.join(N[i].replace('.mp4','')[:22] for i in abst)}" if abst else ""))

# ============ design 4 : la camera decide si on ose ============
# view > seuil -> on tranche sur la mesure ; sinon on n'ose que si la valeur est loin du seuil.
print("=== 4. regle consciente de l'angle de camera (LOO imbriquee, feature fixee a all_hee_an3d) ===")
j=K.index("all_hee_an3d")
for vmin in (0.25, 0.30, 0.35):
    for band in (0.5, 0.8, 1.2):
        dec=cor=0; abst=[]
        for i in range(n):
            tr=np.ones(n,bool); tr[i]=False
            _,t,s=best_rule(M[tr,j], y[tr]); sd=M[tr,j].std()
            far = abs(M[i,j]-t) > band*sd
            if M[i,jv] < vmin and not far: abst.append(i); continue
            dec+=1; cor+=int(((M[i,j]*s)>=t*s)==y[i])
        report(f"view >= {vmin}, sinon marge > {band} ecart-type", dec, cor, abst)

# ============ design 5 : accord entre normalisations de la meme grandeur ============
# Meme quantite physique (largeur de stance) mesuree de 6 facons ; si elles divergent, doute.
fam=["all_hee_an3d","all_ank_an3d","all_toe_an3d","all_ank_sh3d","all_ank_over_hip_2d","all_ank_dist_over_leg"]
js=[K.index(f) for f in fam]
print("\n=== 5. six normalisations de la largeur de stance votent; le desaccord = doute (LOO imbriquee) ===")
allv=[]
for i in range(n):
    tr=np.ones(n,bool); tr[i]=False
    v=0
    for j2 in js:
        _,t,s=best_rule(M[tr,j2], y[tr]); v += 1 if (M[i,j2]*s)>=t*s else -1
    allv.append(v)
allv=np.array(allv)
for need in (2,4,6):
    dec=int((abs(allv)>=need).sum()); cor=int(((allv[abs(allv)>=need]>0)==y[abs(allv)>=need]).sum())
    abst=[i for i in range(n) if abs(allv[i])<need]
    report(f"|vote| >= {need}/6", dec, cor, abst)

# ============ design 6 : 5 + le garde-fou d'angle ============
print("\n=== 6. accord des normalisations OU camera favorable (LOO imbriquee) ===")
for need in (4,6):
    for vmin in (0.30, 0.35):
        dec=cor=0; abst=[]
        for i in range(n):
            if abs(allv[i]) < need and M[i,jv] < vmin: abst.append(i); continue
            dec+=1; cor+=int((allv[i]>0)==y[i])
        report(f"|vote| >= {need}/6, ou view >= {vmin}", dec, cor, abst)
