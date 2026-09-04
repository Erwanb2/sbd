"""Confronte la sortie de batch_predict.py a backend/eval/ground_truth.json."""
import json, sys, collections

res = json.load(open(sys.argv[1]))
gt = {v["file"]: v["movement"] for v in json.load(open(sys.argv[2]))["videos"]}
MAP = {"sumo deadlift": "Sumo", "conventional deadlift": "Conventional"}

strategies = {
    "clip entier": lambda r: r["whole_clip"]["style"],
    "1re rep": lambda r: r["style_first_rep"],
    "vote des reps": lambda r: r["style_vote"],
}

rows = []
for r in res:
    if "error" in r:
        continue
    truth = MAP.get(gt.get(r["file"]))
    if truth is None:
        continue
    rows.append((r, truth))

print(f"{len(rows)} clips notes\n")
for name, fn in strategies.items():
    ok = sum(fn(r) == t for r, t in rows)
    cm = collections.Counter((t, fn(r)) for r, t in rows)
    print(f"{name:>14} : {ok}/{len(rows)} = {100*ok/len(rows):.1f}%")
    for t in ("Conventional", "Sumo"):
        d = {p: c for (tt, p), c in cm.items() if tt == t}
        n = sum(d.values())
        print(f"                 vrai {t:<13} (n={n:2d}) -> {d}")
    print()

print("Detail (strategie 'clip entier') :")
print(f"{'clip':<58} {'verite':<13} {'predit':<13} {'reps':>4}  probas")
for r, t in sorted(rows, key=lambda x: (x[1], x[0]["file"])):
    p = r["whole_clip"]["style"]
    flag = "  " if p == t else "X "
    pr = r["whole_clip"]["style_probs"]
    print(f"{flag}{r['file'][:56]:<56} {t:<13} {p:<13} {r['n_reps']:>4}  "
          f"R={pr['Romanian']:.2f} S={pr['Sumo']:.2f} C={pr['Conventional']:.2f}")
