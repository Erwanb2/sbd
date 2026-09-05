"""Honest estimate: pick the feature INSIDE each fold, never on the held-out clip."""
import json, sys, numpy as np
SP = "/tmp/claude-1000/-mnt-c-Users-erwan-Documents-dev-projects-sbd/6bd5742a-9369-4889-9a3b-82993eae086f/scratchpad"
D = json.load(open(f"{SP}/matrix.json"))
M = np.array(D["M"]); y = np.array(D["y"]); keys = D["keys"]; names = D["names"]

def best_rule(v, yy):
    best = (-1, None, 1)
    for thr in np.unique(v):
        for s in (1, -1):
            acc = np.mean(((v*s) >= thr*s) == yy)
            if acc > best[0]: best = (acc, thr, s)
    return best

# --- nested LOO: feature choice happens on the training folds only
ok, picks = 0, []
for i in range(len(y)):
    m = np.ones(len(y), bool); m[i] = False
    scores = []
    for j in range(M.shape[1]):
        v = M[m, j]
        if np.allclose(v, v[0]): continue
        acc, thr, sg = best_rule(v, y[m])
        pos = v[(v*sg) >= thr*sg]; neg = v[(v*sg) < thr*sg]
        margin = (abs(pos*sg).min() - abs(neg*sg).max()) if len(pos) and len(neg) else 0
        scores.append((acc, float(margin / (v.std() + 1e-9)), j))
    scores.sort(reverse=True)
    j = scores[0][-1]
    _, thr, s = best_rule(M[m, j], y[m])
    pred = int((M[i, j]*s) >= thr*s)
    ok += int(pred == y[i]); picks.append(keys[j])
    if pred != y[i]: print(f"  rate: {names[i]} (vrai={'sumo' if y[i] else 'conv'}) via {keys[j]}")
print(f"\nLOO imbriquee (choix de feature inclus): {ok}/{len(y)} = {ok/len(y):.2f}")
from collections import Counter
print("features choisies:", Counter(picks).most_common(5))

# --- how likely is a 340-feature sweep to produce a perfect separator by chance?
rng = np.random.default_rng(0)
hits = 0
for _ in range(400):
    yp = rng.permutation(y)
    best = max(best_rule(M[:, j], yp)[0] for j in range(0, M.shape[1], 7))
    hits += int(best >= 1.0)
print(f"sur 400 tirages d'etiquettes au hasard, un separateur parfait apparait {hits/4:.0f}% du temps")

# --- values of the leading feature, clip by clip
j = keys.index("all_ank_sh3d")
order = np.argsort(-M[:, j])
print("\nall_ank_sh3d (mediane sur tout le clip de ecart chevilles / ecart epaules, axe 3D):")
for i in order:
    print(f"  {M[i,j]:5.2f}  {'SUMO' if y[i] else 'conv'}  {names[i]}")
