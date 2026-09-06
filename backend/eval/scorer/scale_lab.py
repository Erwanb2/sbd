"""ARCHIVE. Rejoue plusieurs correspondances 1-4 -> 1/3 sur des passes anterieures.

Le pipeline ne note plus sur 4 : `schemas.py` demande directement 1/2/3 et
`ai_service` ne compresse plus rien. Ce script ne sert donc qu'a relire les dumps
`llm_scores*.json` produits AVANT la bascule, qui portent encore `raw_score` — il
est ce qui a montre que le niveau 4 ne sortait que sur 5,7 % des cases quand
l'humain met 3/3 sur 30 %, et donc que le haut de l'echelle etait inatteignable.

    cd backend
    uv run python eval/scorer/scale_lab.py
    uv run python eval/scorer/scale_lab.py --compare llm_scores_nofloor.json

Le pipeline compresse aujourd'hui `1-2 -> 1, 3 -> 2, 4 -> 3`. Cette correspondance
range "Poor / flawed" (2) dans le meme seau que "Danger" (1) : un modele qui juge un
lift imparfait mais correct ressort en 1/3, la ou l'humain met 2/3. C'est un candidat
serieux pour le biais de -0,78 mesure sur les 49 clips.

`run_llm.py` conservant desormais `raw_score`, toutes les correspondances se testent
ici sans redepenser un appel. Aucun acces reseau.

Ce que le script ne dit pas : quelle correspondance est *juste*. Il dit laquelle
reproduit le mieux les etiquettes humaines. Choisir la meilleure sur ce critere seul
reviendrait a ajuster l'echelle au jeu de test — a lire avec `assertions.py`, qui
verifie des separations et non un accord moyen.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

# Chaque correspondance associe le score brut 1-4 a la note affichee 1..3.
CORRESPONDANCES = {
    "actuelle":     {1: 1, 2: 1, 3: 2, 4: 3},   # 1-2 -> 1, 3 -> 2, 4 -> 3
    "sans_ecrase":  {1: 1, 2: 2, 3: 2, 4: 3},   # "poor" cesse d'etre "danger"
    "haut_serre":   {1: 1, 2: 2, 3: 3, 4: 3},   # 3 et 4 fusionnent, le bas s'etale
}


def _charge(chemin: str) -> dict:
    p = chemin if os.path.isabs(chemin) else os.path.join(ICI, chemin)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _paires(humain: dict, llm: dict):
    """(note humaine, score brut) pour chaque case notee des deux cotes."""
    out = []
    for fichier, entree in llm.items():
        scores_h = (humain.get(fichier) or {}).get("scores") or {}
        for nom, bloc in (entree.get("criteria") or {}).items():
            h, brut = scores_h.get(nom), bloc.get("raw_score")
            if isinstance(h, int) and isinstance(brut, int):
                out.append((h, brut))
    return out


def _dist(vals, niveaux) -> str:
    c = collections.Counter(vals)
    return "/".join(str(c.get(n, 0)) for n in niveaux)


def _rapport(nom: str, humain: dict, llm: dict) -> None:
    paires = _paires(humain, llm)
    if not paires:
        print(f"\n{nom} : aucun score brut — la passe est-elle anterieure a "
              f"l'instrumentation ?")
        return
    bruts = [b for _, b in paires]
    print(f"\n=== {nom} — {len(paires)} cases ===")
    print(f"  distribution brute 1/2/3/4 : {_dist(bruts, [1, 2, 3, 4])}"
          f"   moyenne {statistics.mean(bruts):.2f}")
    print(f"  {'correspondance':14} {'exact':>6} {'EAM':>5} {'biais':>6}   modele 1/2/3")
    for cle, table in CORRESPONDANCES.items():
        proj = [(h, table[b]) for h, b in paires]
        exact = sum(h == l for h, l in proj) / len(proj)
        eam = statistics.mean(abs(h - l) for h, l in proj)
        biais = statistics.mean(l - h for h, l in proj)
        print(f"  {cle:14} {exact:5.0%} {eam:5.2f} {biais:+6.2f}   "
              f"{_dist([l for _, l in proj], [1, 2, 3])}")
    hum = [h for h, _ in paires]
    print(f"  {'(humain)':14} {'':>6} {'':>5} {'':>6}   {_dist(hum, [1, 2, 3])}")
    # Une constante bat souvent un juge bruite : sans ce repere, un accord se lit mal.
    for n in (1, 2, 3):
        print(f"  reference : toujours {n}/3 -> {sum(h == n for h in hum) / len(hum):.0%}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="llm_scores.json", help="passe a analyser")
    ap.add_argument("--compare", help="seconde passe, comparee a la premiere")
    a = ap.parse_args()

    humain = _charge("human_labels.json")
    try:
        _rapport(a.scores, humain, _charge(a.scores))
    except FileNotFoundError:
        print(f"{a.scores} introuvable", file=sys.stderr)
        return 2
    if a.compare:
        try:
            _rapport(a.compare, humain, _charge(a.compare))
        except FileNotFoundError:
            print(f"\n{a.compare} introuvable — la passe est-elle terminee ?",
                  file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
