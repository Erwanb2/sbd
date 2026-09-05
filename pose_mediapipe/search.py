"""Rank every feature, alone then in pairs, with leave-one-out validation."""
import json, sys, itertools, numpy as np
sys.path.insert(0, "/tmp/claude-1000/-mnt-c-Users-erwan-Documents-dev-projects-sbd/6bd5742a-9369-4889-9a3b-82993eae086f/scratchpad")
from features import clip_features

SP = sys.argv[1] if len(sys.argv) > 1 else "."
L = json.load(open(f"{SP}/landmarks.json"))
gt = {v["file"]: v["movement"] for v in
      json.load(open("/mnt/c/Users/erwan/Documents/dev_projects/sbd/backend/eval/ground_truth.json"))["videos"]}
X, y, names = [], [], []
for f, e in L.items():
    lab = gt.get(f, "?")
    if "deadlift" not in lab: continue
    c = clip_features(e)
    if c is None: print("no pose:", f); continue
    X.append(c); y.append(1 if lab.startswith("sumo") else 0); names.append(f)
keys = sorted(set.intersection(*[set(x) for x in X]) - {"n_rows"})
M = np.array([[x[k] for k in keys] for x in X], float)
y = np.array(y)
print(f"{len(y)} clips, {y.sum()} sumo, {len(keys)} features\n")

def best_rule(v, yy):
    """Best single threshold (either direction): returns (acc, thr, sign)."""
    best = (0, None, 1)
    for thr in np.unique(v):
        for s in (1, -1):
            acc = np.mean(((v * s) >= thr * s) == yy)
            if acc > best[0]: best = (acc, thr, s)
    return best

def loo(v, yy):
    ok = 0
    for i in range(len(yy)):
        m = np.ones(len(yy), bool); m[i] = False
        _, thr, s = best_rule(v[m], yy[m])
        ok += int((((v[i] * s) >= thr * s)) == yy[i])
    return ok / len(yy)

def auc(v, yy):
    r = np.argsort(np.argsort(v)) + 1
    n1, n0 = yy.sum(), (1 - yy).sum()
    a = (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    return max(a, 1 - a)

rows = []
for j, k in enumerate(keys):
    v = M[:, j]
    if np.allclose(v, v[0]): continue
    rows.append((loo(v, y), best_rule(v, y)[0], auc(v, y), k, j))
rows.sort(reverse=True)
print(f"{'LOO':>6}{'fit':>6}{'AUC':>6}  feature")
for r in rows[:25]: print(f"{r[0]:6.2f}{r[1]:6.2f}{r[2]:6.2f}  {r[3]}")

print("\n--- paires (OR / AND de deux regles), LOO ---")
top = [r[4] for r in rows[:40]]
def loo_pair(j1, j2, mode):
    ok = 0
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        _, t1, s1 = best_rule(M[m, j1], y[m]); _, t2, s2 = best_rule(M[m, j2], y[m])
        a = (M[i, j1] * s1) >= t1 * s1; b = (M[i, j2] * s2) >= t2 * s2
        ok += int((a or b if mode == "or" else a and b) == bool(y[i]))
    return ok / len(y)
pairs = []
for j1, j2 in itertools.combinations(top, 2):
    for mode in ("or", "and"):
        pairs.append((loo_pair(j1, j2, mode), mode, keys[j1], keys[j2]))
pairs.sort(reverse=True)
seen = set(); shown = 0
for acc, mode, a, b in pairs:
    if (a, b) in seen: continue
    seen.add((a, b)); print(f"{acc:6.2f}  {a}  {mode.upper()}  {b}"); shown += 1
    if shown >= 15: break

json.dump({"names": names, "y": y.tolist(), "keys": keys, "M": M.tolist()},
          open(f"{SP}/matrix.json", "w"))
print("\nmatrice -> matrix.json")
