"""Passe le pipeline de production sur tous les clips de data/ et stocke la note LLM.

    cd backend
    uv run python eval/scorer/run_llm.py                 # tous les clips manquants
    uv run python eval/scorer/run_llm.py --model 3.5     # gemini-3.5-flash (payant)
    uv run python eval/scorer/run_llm.py --only worst_deadlift.mp4 --force

Ecrit eval/scorer/llm_scores.json au fil de l'eau : le fichier reste exploitable
si le passage est interrompu, et un relancement reprend ou il s'est arrete.
Le modele par defaut est flash-lite (le seul sans contrainte de budget ici).
"""

import argparse
import json
import os
import sys
import time
import traceback

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
SORTIE = os.path.join(ICI, "llm_scores.json")


def charge_env(chemin=os.path.join(BACKEND, ".env")):
    """Le backend lit son environnement de docker-compose ; en local il faut le .env."""
    try:
        with open(chemin, encoding="utf-8") as f:
            lignes = f.read().splitlines()
    except FileNotFoundError:
        return
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


def charge():
    try:
        with open(SORTIE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def ecrit(obj):
    tmp = SORTIE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, SORTIE)


def compact(resultat, mouvement, modele, pose):
    """Ne garde du resultat brut que ce que l'outil de notation affiche."""
    criteres = {}
    for nom, valeur in resultat.items():
        if isinstance(valeur, dict) and "score" in valeur:
            criteres[nom] = {
                "score": valeur.get("score"),          # deja compresse en 1..3, ou None si NA
                # Score avant compression : permet de rejouer n'importe quelle
                # correspondance 1-4 -> 1-3 hors ligne, sans redepenser un appel.
                "raw_score": valeur.get("raw_score"),
                "feedback": valeur.get("feedback", ""),
                "visual_analysis": valeur.get("visual_analysis", ""),
                "not_assessable": bool(valeur.get("not_assessable")),
            }
            if criteres[nom]["score"] is None:
                criteres[nom]["score"] = "NA"
    return {
        "model": modele,
        "movement": mouvement,
        "criteria": criteres,
        "persona": resultat.get("lifter_persona"),
        "persona_justification": resultat.get("persona_justification"),
        "total": resultat.get("total_raw_score"),
        "max": resultat.get("raw_max_score"),
        "pose_variant": pose.get("variante"),
        "kinematics": resultat.get("kinematics"),
        "run_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None,
                    help="cle de MODELES_ANALYSE (3.5, 3.7). Par defaut flash-lite.")
    ap.add_argument("--only", nargs="*", help="ne traiter que ces fichiers")
    ap.add_argument("--force", action="store_true", help="refaire meme si deja present")
    ap.add_argument("--out", help="fichier de sortie (defaut: llm_scores.json). Sert a "
                                  "garder plusieurs passes cote a cote pour les comparer.")
    a = ap.parse_args()
    if a.out:
        global SORTIE
        SORTIE = a.out if os.path.isabs(a.out) else os.path.join(ICI, a.out)

    charge_env()
    if a.model is None:
        # Le budget n'est illimite que sur flash-lite : c'est le defaut du batch.
        os.environ["MODEL_GEMINI"] = "gemini-3.5-flash-lite"

    import ai_service                                    # apres le reglage du modele

    fichiers = a.only or sorted(f for f in os.listdir(DATA) if f.lower().endswith(".mp4"))
    resultats = charge()
    faits = 0
    for k, f in enumerate(fichiers, 1):
        if not a.force and f in resultats and "criteria" in resultats[f]:
            print(f"[{k}/{len(fichiers)}] {f} — deja fait")
            continue
        chemin = os.path.join(DATA, f)
        t0 = time.time()
        try:
            detect = ai_service.upload_and_detect_concurrent(chemin)
            mouvement = detect["mouvement_detecte"]
            brut = ai_service.analyze_movement(detect["file_name"], mouvement, a.model)
            modele = ai_service.MODELES_ANALYSE.get(a.model) or os.environ["MODEL_GEMINI"]
            resultats[f] = compact(brut, mouvement, modele, detect.get("pose") or {})
            faits += 1
            notes = {n: c["score"] for n, c in resultats[f]["criteria"].items()}
            print(f"[{k}/{len(fichiers)}] {f} — {mouvement} — {notes} "
                  f"({time.time() - t0:.0f}s)")
        except Exception as exc:
            resultats[f] = {"error": f"{type(exc).__name__}: {exc}",
                            "run_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            print(f"[{k}/{len(fichiers)}] {f} — ECHEC : {exc}")
            traceback.print_exc(limit=2)
        ecrit(resultats)
    print(f"\n{faits} clip(s) analyses. -> {SORTIE}")


if __name__ == "__main__":
    main()
