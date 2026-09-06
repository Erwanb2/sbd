"""Compare la note humaine et la note du pipeline, critere par critere.

    cd backend
    uv run python eval/scorer/report.py

A lire avec `assertions.py`, pas a la place : l'accord moyen ci-dessous flatte
mecaniquement un juge qui repond toujours la meme chose, puisque les etiquettes
humaines sont elles-memes concentrees. Les colonnes qui comptent sont donc moins
l'accord que **l'usage de l'echelle** (le modele descend-il jamais ?) et
**l'ecart signe** (est-il systematiquement plus genereux ou plus severe ?).

Ce script ne fait aucun appel : il lit eval/test_dataset.json.
"""

from __future__ import annotations

import collections
import json
import os
import statistics
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
JEU = os.path.join(BACKEND, "eval", "test_dataset.json")

NIVEAUX = [1, 2, 3]


def _dist(vals) -> str:
    """Distribution 1/2/3/NA, en comptant les None comme NA."""
    c = collections.Counter(v if isinstance(v, int) else "NA" for v in vals)
    return "/".join(str(c.get(n, 0)) for n in NIVEAUX) + f"/{c.get('NA', 0)}"


def main() -> int:
    if not os.path.exists(JEU):
        print(f"{JEU} absent — lance build_dataset.py", file=sys.stderr)
        return 2
    with open(JEU, encoding="utf-8") as f:
        jeu = json.load(f)
    clips = jeu["clips"]

    criteres = sorted({c for v in clips for c in (v.get("criteria") or {})})
    print(f"{len(clips)} clips · echelle 1/3 · 2/3 · 3/3\n")
    print(f"{'critere':38} {'n':>3} {'exact':>6} {'EAM':>5} {'biais':>6} | "
          f"{'humain 1/2/3/NA':>16} | {'modele 1/2/3/NA':>16}")

    lignes, tous = [], []
    for crit in criteres:
        h_all, l_all, paires = [], [], []
        for v in clips:
            bloc = (v.get("criteria") or {}).get(crit)
            if bloc is None:
                continue
            h, l = bloc.get("human"), bloc.get("llm")
            h_all.append(h)
            l_all.append(l)
            if isinstance(h, int) and isinstance(l, int):
                paires.append((h, l))
        if not paires:
            continue
        exact = sum(h == l for h, l in paires) / len(paires)
        eam = statistics.mean(abs(h - l) for h, l in paires)
        # Ecart signe : positif = le modele note plus haut que l'humain.
        biais = statistics.mean(l - h for h, l in paires)
        tous += paires
        lignes.append((exact, crit))
        print(f"{crit:38} {len(paires):>3} {exact:5.0%} {eam:5.2f} {biais:+6.2f} | "
              f"{_dist(h_all):>16} | {_dist(l_all):>16}")

    if tous:
        print(f"\n  global : {sum(h == l for h, l in tous) / len(tous):.0%} d'accord exact, "
              f"EAM {statistics.mean(abs(h - l) for h, l in tous):.2f}, "
              f"biais {statistics.mean(l - h for h, l in tous):+.2f} "
              f"sur {len(tous)} cases")
        # Reference : ce qu'obtiendrait un juge constant. Si le modele ne fait pas
        # nettement mieux, son accord ne vient pas de son jugement.
        for n in NIVEAUX:
            const = sum(h == n for h, _ in tous) / len(tous)
            print(f"  reference : repondre toujours {n}/3 donnerait {const:.0%}")

    # --- NA : le modele s'abstient-il la ou l'humain s'abstient ? ---
    na_h = sum(1 for v in clips for b in (v.get("criteria") or {}).values()
               if b.get("human") is None)
    na_l = sum(1 for v in clips for b in (v.get("criteria") or {}).values()
               if b.get("llm") is None)
    accord_na = sum(1 for v in clips for b in (v.get("criteria") or {}).values()
                    if b.get("human") is None and b.get("llm") is None)
    print(f"\n  NA : humain {na_h}, modele {na_l}, en commun {accord_na}")

    # --- persona ---
    dans = [v["persona"].get("llm_dans_choix_humain") for v in clips]
    juges = [x for x in dans if x is not None]
    if juges:
        print(f"\n  persona : {sum(juges)}/{len(juges)} dans l'ensemble accepte par l'humain")
    compte = collections.Counter(v["persona"].get("llm") for v in clips
                                 if v["persona"].get("llm"))
    if compte:
        top, n = compte.most_common(1)[0]
        print(f"  {len(compte)} archetypes distincts sur {sum(compte.values())} clips ; "
              f"le plus frequent : {top} ({n})")

    if lignes:
        print("\n  criteres du moins au mieux reproduit :")
        for exact, crit in sorted(lignes):
            print(f"    {exact:5.0%}  {crit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
