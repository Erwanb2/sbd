"""Compare plusieurs passes du pipeline sur une ligne chacune.

    cd backend
    uv run python eval/scorer/compare_runs.py llm_scores.json llm_scores_persona_last.json

Sert a repondre a une seule question : ce changement a-t-il ameliore quelque chose ?
Chaque passe est confrontee aux memes etiquettes humaines, donc les colonnes se
comparent directement d'une ligne a l'autre.

Comment lire les colonnes :

  exact   accord case a case. **A comparer a la reference** affichee en bas : les
          etiquettes sont concentrees sur 2/3, donc repondre "2/3" partout obtient
          deja ~48%. Un pipeline sous cette barre est nuisible, pas seulement faible.
  EAM     erreur absolue moyenne, sur une echelle a trois niveaux.
  biais   negatif = le modele note plus severement que l'humain.
  1/2/3   distribution des notes rendues. Une distribution qui colle sans que
          l'accord monte signale un juge bien calibre en moyenne mais qui attribue
          ses notes aux mauvais clips.
  persona part des clips ou l'archetype rendu figure dans l'ensemble accepte par
          l'humain (qui peut en accepter plusieurs pour un meme defaut).

Aucun appel reseau : tout est relu sur disque.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)


def _charge(nom: str) -> dict:
    chemin = nom if os.path.isabs(nom) else os.path.join(ICI, nom)
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _personas_acceptes(valeur) -> list:
    """L'humain peut cocher plusieurs archetypes : on compare l'appartenance."""
    try:
        import server
        return server.liste_persona(valeur)
    except Exception:
        if valeur is None:
            return []
        return list(valeur) if isinstance(valeur, (list, tuple)) else [valeur]


def _mesures(humain: dict, passe: dict) -> dict:
    paires, rendus = [], []
    for fichier, entree in passe.items():
        scores_h = (humain.get(fichier) or {}).get("scores") or {}
        for nom, bloc in (entree.get("criteria") or {}).items():
            h, l = scores_h.get(nom), bloc.get("score")
            if isinstance(l, int):
                rendus.append(l)
            if isinstance(h, int) and isinstance(l, int):
                paires.append((h, l))
    if not paires:
        return {}
    d = collections.Counter(rendus)
    ok = tot = 0
    for fichier, entree in passe.items():
        acceptes = _personas_acceptes((humain.get(fichier) or {}).get("persona"))
        rendu = entree.get("persona")
        if rendu and acceptes:
            tot += 1
            ok += rendu in acceptes
    archetypes = collections.Counter(e.get("persona") for e in passe.values()
                                     if e.get("persona"))
    return {
        "n": len(paires),
        "exact": sum(h == l for h, l in paires) / len(paires),
        "eam": statistics.mean(abs(h - l) for h, l in paires),
        "biais": statistics.mean(l - h for h, l in paires),
        "dist": "/".join(str(d.get(k, 0)) for k in (1, 2, 3)),
        "persona": (ok / tot) if tot else None,
        "persona_txt": f"{ok}/{tot}" if tot else "—",
        "archetypes": len(archetypes),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("passes", nargs="+", help="fichiers de scores a comparer")
    a = ap.parse_args()

    humain = _charge("human_labels.json")
    print(f"{'passe':34} {'n':>4} {'exact':>6} {'EAM':>5} {'biais':>6} "
          f"{'1/2/3':>14} {'persona':>9} {'types':>6}")
    lignes = []
    for nom in a.passes:
        try:
            m = _mesures(humain, _charge(nom))
        except FileNotFoundError:
            print(f"{os.path.basename(nom)[:34]:34} introuvable")
            continue
        if not m:
            print(f"{os.path.basename(nom)[:34]:34} aucune case comparable")
            continue
        lignes.append((nom, m))
        print(f"{os.path.basename(nom)[:34]:34} {m['n']:>4} {m['exact']:5.0%} "
              f"{m['eam']:5.2f} {m['biais']:+6.2f} {m['dist']:>14} "
              f"{m['persona_txt']:>9} {m['archetypes']:>6}")

    # La reference constante : sans elle un accord de 50% peut passer pour un succes.
    vals = [s for v in humain.values() for s in (v.get("scores") or {}).values()
            if isinstance(s, int)]
    if vals:
        c = collections.Counter(vals)
        print("\n  reference — repondre la meme chose partout : "
              + "  ".join(f"{k}/3 -> {c[k] / len(vals):.0%}" for k in sorted(c)))
        print(f"  etiquettes humaines : {'/'.join(str(c.get(k, 0)) for k in (1, 2, 3))}"
              f" sur {len(vals)} cases")
    if len(lignes) >= 2:
        (n0, a0), (n1, a1) = lignes[0], lignes[-1]
        print(f"\n  {os.path.basename(n0)} -> {os.path.basename(n1)} : "
              f"exact {a1['exact'] - a0['exact']:+.0%}, "
              f"biais {a1['biais'] - a0['biais']:+.2f}"
              + (f", persona {a1['persona'] - a0['persona']:+.0%}"
                 if a0["persona"] is not None and a1["persona"] is not None else ""))
        _bruit(_charge(lignes[0][0]), _charge(lignes[-1][0]))
    return 0


def _bruit(p0: dict, p1: dict) -> None:
    """Accord des deux passes entre elles, independamment de l'humain.

    Sur deux passes de configurations DIFFERENTES, ce chiffre mesure l'ampleur du
    changement. Sur deux passes de la MEME configuration, il mesure le plancher de
    bruit : en dessous de cet ecart, aucune comparaison n'est interpretable.
    L'appel est fait a temperature=0, ce qui ne garantit pas le determinisme.
    """
    paires, personas_id, personas_n = [], 0, 0
    for fichier, e0 in p0.items():
        e1 = p1.get(fichier)
        if not e1:
            continue
        for nom, b0 in (e0.get("criteria") or {}).items():
            b1 = (e1.get("criteria") or {}).get(nom)
            if b1 and isinstance(b0.get("score"), int) and isinstance(b1.get("score"), int):
                paires.append((b0["score"], b1["score"]))
        if e0.get("persona") and e1.get("persona"):
            personas_n += 1
            personas_id += e0["persona"] == e1["persona"]
    if not paires:
        return
    identiques = sum(a == b for a, b in paires) / len(paires)
    print(f"\n  accord des deux passes ENTRE ELLES : {identiques:.0%} de cases identiques, "
          f"ecart moyen {statistics.mean(abs(a - b) for a, b in paires):.2f} "
          f"sur {len(paires)} cases"
          + (f", meme persona sur {personas_id}/{personas_n} clips" if personas_n else ""))
    print("  (memes configurations -> c'est le plancher de bruit ; "
          "configurations differentes -> c'est l'ampleur du changement)")


if __name__ == "__main__":
    raise SystemExit(main())
