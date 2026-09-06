"""Verifie ce que le juge doit separer, plutot que son accord moyen.

    cd backend
    uv run python eval/scorer/build_dataset.py     # d'abord, pour rafraichir le jeu
    uv run python eval/scorer/assertions.py

Pourquoi pas un accord global : sur les clips notes, les huit criteres ont le meme
mode et l'echelle n'est quasiment jamais utilisee en bas. Un modele qui repond "2/3"
partout obtient deja un accord flatteur et une utilite nulle. Les paires controlees
et les ancres, elles, disent si le juge separe ce qu'il est cense separer.

Les assertions viennent de `eval/ground_truth.json` (bloc "assertions"), portees ici
avec deux changements :

  * **L'echelle.** ground_truth.json etait sur le 1-4 brut du schema ; le jeu de test
    est sur le 1/3-2/3-3/3 d'apres compression. La compression ecrase 1 et 2 sur la
    meme valeur : une paire dont les deux moities valent 1 et 2 en brut devient
    inseparable ici. Les assertions concernees le signalent au lieu d'echouer en
    silence.
  * **L'autorite.** Le sens attendu n'est plus code en dur : il est lu dans les notes
    humaines. Si l'humain ne separe pas la paire, l'assertion devient NON EXPRIMABLE
    plutot que de juger le modele contre une attente que la verite terrain ne soutient
    plus. Les etiquettes evoluent, les assertions suivent.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
JEU = os.path.join(BACKEND, "eval", "test_dataset.json")

# Portees de ground_truth.json. `criterion` nomme ce que la paire isole ; le sens
# attendu vient des notes humaines, pas d'ici.
ASSERTIONS = [
    {"id": "pair_chest", "type": "pairwise",
     "criterion": "core_bracing_and_spine_neutrality",
     "better": "poitrine_relevee.mp4", "worse": "pas_poitrine_relevee.mp4",
     "aussi_la_moyenne": True,
     "pourquoi": "Meme lifter, meme salle, meme charge ; la seule difference voulue est "
                 "la position du buste et du rachis. Un juge qui ne les separe pas ne "
                 "mesure pas ce critere."},
    {"id": "pair_slack", "type": "pairwise",
     "criterion": "slack_pull_and_lat_engagement",
     "better": "erwan_bon_slack.mp4", "worse": "erwan_mauvais_slack.mp4",
     "pourquoi": "Meme lifter, meme installation, contraste voulu sur la mise en tension."},
    {"id": "hard_failed_lockout", "type": "exact",
     "file": "engueran_fail_deadlift.mp4", "criterion": "lockout_execution",
     # Deux reponses justes : 1/3, ou NA puisqu'il n'y a pas de lockout a evaluer.
     # Ce qui est faux, c'est de le noter haut.
     "accepte": [1, "NA"],
     "pourquoi": "La rep n'est jamais verrouillee. C'est l'etiquette la moins discutable "
                 "du jeu : si le juge la note haut, rien d'autre n'est fiable."},
    {"id": "anchors_ordering", "type": "ordering",
     "files": ["jeff_nippard.mp4", "pr_160.mp4", "worst_deadlift.mp4"],
     "pourquoi": "Un juge incapable de classer une demo propre au-dessus d'un max grinde "
                 "au-dessus d'un lift casse n'a aucun signal exploitable."},
    {"id": "hard_classification", "type": "classification",
     "attendu": {"oscar_sumo.mp4": "sumo deadlift",
                 "oscar_sumo_short.mp4": "sumo deadlift",
                 "engueran_fail_deadlift.mp4": "sumo deadlift"},
     "pourquoi": "Sumo filme de profil, plateau devant la stance. L'indice qui survit a "
                 "cet angle est la position des mains par rapport aux genoux, pas "
                 "l'ecartement des pieds."},
    {"id": "filename_independence", "type": "classification",
     "attendu": {"Arthur Garrec Profil de coureur Strava.mp4": "conventional deadlift"},
     "pourquoi": "Le nom de fichier decrit un profil Strava ; le clip est un deadlift "
                 "conventionnel. Rappel de ne jamais deduire une etiquette d'un nom."},
    {"id": "duration_rejection", "type": "validation",
     "file": "long_deadlift.mp4",
     "pourquoi": "65,9 s au-dela de MAX_VIDEO_SECONDS : doit etre rejete avant tout "
                 "appel Gemini. Teste le pipeline, pas le jugement."},
]


# ------------------------------------------------------------------- lecture

def _note(clip: dict, critere: str, source: str):
    """Note d'une source pour un critere, ou None si absente ou NA."""
    val = ((clip.get("criteria") or {}).get(critere) or {}).get(source)
    return val if isinstance(val, int) else None


def _moyenne(clip: dict, source: str, criteres: list[str] | None = None):
    """Moyenne des criteres notes par cette source.

    Une moyenne et non une somme : avec des NA le denominateur bouge d'un clip a
    l'autre, et deux sommes sur des denominateurs differents ne se comparent pas.
    """
    noms = criteres if criteres is not None else list(clip.get("criteria") or {})
    vals = [n for c in noms if (n := _note(clip, c, source)) is not None]
    return statistics.mean(vals) if vals else None


def _communs(a: dict, b: dict) -> list[str]:
    """Criteres que l'humain ET le modele ont notes sur les deux clips.

    Comparer deux moyennes calculees sur des criteres differents n'a pas de sens :
    on restreint au sous-ensemble commun avant toute comparaison de totaux.
    """
    return [c for c in (a.get("criteria") or {})
            if all(_note(clip, c, src) is not None
                   for clip in (a, b) for src in ("human", "llm"))]


# ---------------------------------------------------------------- evaluation

def _pairwise(a: dict, clips: dict) -> tuple[str, str]:
    bon, mauvais = clips.get(a["better"]), clips.get(a["worse"])
    if not bon or not mauvais:
        return "MANQUANT", "clip absent du jeu"
    crit = a["criterion"]
    hb, hm = _note(bon, crit, "human"), _note(mauvais, crit, "human")
    if hb is None or hm is None:
        return "MANQUANT", f"{crit} : note humaine absente ({hb} / {hm})"
    if hb <= hm:
        # La verite terrain ne soutient plus l'attente : on ne juge pas le modele
        # contre une direction que l'humain n'a pas confirmee.
        return "NON EXPRIMABLE", (f"l'humain ne separe pas la paire sur {crit} "
                                  f"({hb} vs {hm}) — compression 1-2→1 probable")
    lb, lm = _note(bon, crit, "llm"), _note(mauvais, crit, "llm")
    if lb is None or lm is None:
        return "MANQUANT", f"{crit} : prediction absente ({lb} / {lm})"
    detail = f"{crit} : humain {hb}>{hm} · modele {lb}"
    ok = lb > lm
    detail += f"{'>' if ok else ('=' if lb == lm else '<')}{lm}"
    if ok and a.get("aussi_la_moyenne"):
        noms = _communs(bon, mauvais)
        mb, mm = _moyenne(bon, "llm", noms), _moyenne(mauvais, "llm", noms)
        if mb is not None and mm is not None:
            detail += f" | moyennes {mb:.2f} vs {mm:.2f} sur {len(noms)} criteres"
            ok = mb > mm
    return ("PASS" if ok else "FAIL"), detail


def _exact(a: dict, clips: dict) -> tuple[str, str]:
    clip = clips.get(a["file"])
    if not clip:
        return "MANQUANT", "clip absent du jeu"
    crit = a["criterion"]
    brut = ((clip.get("criteria") or {}).get(crit) or {})
    if "llm" not in brut:
        return "MANQUANT", f"{crit} : prediction absente"
    l = brut.get("llm")
    # Une rep jamais verrouillee accepte deux reponses justes : la note plancher, ou
    # l'abstention (il n'y a pas de lockout a evaluer). Ce qui est faux, c'est de la
    # noter haut. L'humain a d'ailleurs repondu NA ici et le barreme accepte les deux.
    accepte = a.get("accepte")
    if accepte is not None:
        ok = (l if l is not None else "NA") in accepte
        return ("PASS" if ok else "FAIL"), \
            f"{crit} : modele {l if l is not None else 'NA'}, attendu l'un de {accepte}"
    h = _note(clip, crit, "human")
    if h is None:
        return "MANQUANT", f"{crit} : note humaine absente"
    if l is None:
        return "MANQUANT", f"{crit} : prediction absente"
    return ("PASS" if l == h else "FAIL"), f"{crit} : modele {l}, humain {h}"


def _ordering(a: dict, clips: dict) -> tuple[str, str]:
    presents = [(f, clips.get(f)) for f in a["files"]]
    if any(c is None for _, c in presents):
        return "MANQUANT", ", ".join(f for f, c in presents if c is None)
    # Sous-ensemble commun aux trois clips, sinon les moyennes ne sont pas comparables
    noms = [c for c in (presents[0][1].get("criteria") or {})
            if all(_note(clip, c, src) is not None
                   for _, clip in presents for src in ("human", "llm"))]
    if not noms:
        return "MANQUANT", "aucun critere note par les deux sources sur les trois clips"
    hs = [(f, _moyenne(c, "human", noms)) for f, c in presents]
    ls = [(f, _moyenne(c, "llm", noms)) for f, c in presents]
    if not all(hs[i][1] > hs[i + 1][1] for i in range(len(hs) - 1)):
        return "NON EXPRIMABLE", ("l'humain n'ordonne pas ces ancres : "
                                  + " ".join(f"{f[:18]}={m:.2f}" for f, m in hs))
    detail = " > ".join(f"{f[:18]}={m:.2f}" for f, m in ls) + f"  ({len(noms)} criteres)"
    return ("PASS" if all(ls[i][1] > ls[i + 1][1] for i in range(len(ls) - 1))
            else "FAIL"), detail


def _classification(a: dict, clips: dict) -> tuple[str, str]:
    bouts, tout, vus = [], True, 0
    for fichier, attendu in a["attendu"].items():
        clip = clips.get(fichier)
        obtenu = (clip or {}).get("llm_movement")
        if not obtenu:
            bouts.append(f"{fichier[:22]}→(pas de prediction)")
            continue
        vus += 1
        juste = obtenu.lower() == attendu.lower()
        tout &= juste
        bouts.append(f"{fichier[:22]}→{obtenu}{'' if juste else ' ✗'}")
    if not vus:
        return "MANQUANT", " | ".join(bouts)
    return ("PASS" if tout else "FAIL"), " | ".join(bouts)


def _validation(a: dict, clips: dict) -> tuple[str, str]:
    """Teste le garde-fou de main.py sans depenser un appel.

    La duree est relue avec OpenCV plutot qu'en important `ai_service` : ce module
    instancie un client Gemini a l'import, ce qui rendrait une assertion hors-ligne
    dependante d'une cle API.
    """
    import cv2
    chemin = os.path.join(os.path.abspath(os.path.join(BACKEND, "..", "data")), a["file"])
    if not os.path.exists(chemin):
        return "MANQUANT", "fichier absent de data/"
    cap = cv2.VideoCapture(chemin)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    finally:
        cap.release()
    duree = (n / fps) if fps > 0 and n > 0 else None
    maxi = int(os.getenv("MAX_VIDEO_SECONDS", "60"))
    if duree is None:
        return "FAIL", "duree illisible"
    return ("PASS" if duree > maxi else "FAIL"), f"{duree:.1f}s contre MAX_VIDEO_SECONDS={maxi}"


VERIFS = {"pairwise": _pairwise, "exact": _exact, "ordering": _ordering,
          "classification": _classification, "validation": _validation}


def evaluer(clips: dict, seulement=None) -> list[dict]:
    out = []
    for a in ASSERTIONS:
        if seulement and a["id"] not in seulement:
            continue
        etat, detail = VERIFS[a["type"]](a, clips)
        out.append({"id": a["id"], "type": a["type"], "etat": etat,
                    "detail": detail, "pourquoi": a["pourquoi"]})
    return out


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="ids d'assertions a evaluer")
    ap.add_argument("--why", action="store_true", help="affiche la raison de chaque assertion")
    ap.add_argument("--json", action="store_true", help="sortie machine")
    a = ap.parse_args()

    if not os.path.exists(JEU):
        print(f"{JEU} absent — lance d'abord build_dataset.py", file=sys.stderr)
        return 2
    with open(JEU, encoding="utf-8") as f:
        jeu = json.load(f)
    clips = {c["file"]: c for c in jeu["clips"]}

    resultats = evaluer(clips, a.only)
    if a.json:
        print(json.dumps(resultats, indent=2, ensure_ascii=False))
        return 0

    predits = sum(1 for c in clips.values()
                  if any(v.get("llm") is not None for v in (c.get("criteria") or {}).values()))
    print(f"{len(clips)} clips, {predits} avec une prediction\n")
    for r in resultats:
        print(f"  [{r['etat']:14}] {r['id']:22} {r['detail']}")
        if a.why:
            print(f"{'':19}{r['pourquoi']}\n")

    juges = [r for r in resultats if r["etat"] in ("PASS", "FAIL")]
    passees = sum(1 for r in juges if r["etat"] == "PASS")
    autres = [r for r in resultats if r["etat"] not in ("PASS", "FAIL")]
    print(f"\n  {passees}/{len(juges)} assertions passees"
          + (f", {len(autres)} non evaluees" if autres else ""))
    return 0 if juges and passees == len(juges) else 1


if __name__ == "__main__":
    raise SystemExit(main())
