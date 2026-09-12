"""Comparaison par paires : deux clips dans le meme appel, lequel a le defaut ?

    cd backend
    uv run --env-file .env python eval/paires.py [--a tibo_sans_coche.mp4 --b pr_160.mp4] [--passes 2]

Jugement relatif plutot qu'absolu. Seul en absolu, le modele fabrique un defaut sur un lift
propre trois fois sur quatre (voir eval/runs/README.md, tibo). Ici la question ne dit rien
sur aucun des deux clips : il doit regarder pour choisir. Chaque paire est envoyee dans les
deux ordres, pour separer une perception d'un biais de position, et `--passes` fois chacune,
a cause du bruit run-a-run. Reglages au plafond, sans schema, pensees conservees.

Sortie : eval/runs/paires_<a>_<b>.json, une entree par appel, avec le verdict extrait.
"""

import argparse
import json
import os
import re
import sys
import time

from google.genai import types

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(ICI)
sys.path.insert(0, BACKEND)

import ai_service                                   # noqa: E402
from pricing import log_usage                       # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))

PROMPT = """You are a powerlifting specialist and a biomechanics researcher. You are given two
deadlift videos, labelled A and B.

In which of these two lifts do the hips rise faster than the shoulders at liftoff?
Start your answer with exactly one line: "Answer: A" or "Answer: B". Then describe the
difference you see between the two lifts."""


def _part(video_file):
    return types.Part(
        file_data=types.FileData(file_uri=video_file.uri, mime_type=video_file.mime_type),
        video_metadata=types.VideoMetadata(fps=ai_service.FPS_MAX))


def _appel(modele, premier, second):
    return ai_service.client.models.generate_content(
        model=modele,
        contents=["Video A:", _part(premier), "Video B:", _part(second), PROMPT],
        config=types.GenerateContentConfig(
            temperature=0.0,
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH,
                                                 include_thoughts=True)))


def _verdict(texte: str) -> str | None:
    m = re.search(r"Answer:\s*([AB])\b", texte or "")
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="tibo_sans_coche.mp4")
    ap.add_argument("--b", default="pr_160.mp4")
    ap.add_argument("--modele", default="3.5")
    ap.add_argument("--passes", type=int, default=2)
    args = ap.parse_args()

    modele = ai_service.MODELES_ANALYSE[args.modele]
    nom = f"paires_{os.path.splitext(args.a)[0]}_{os.path.splitext(args.b)[0]}"
    sortie = os.path.join(ICI, "runs", f"{nom}.json")
    fichiers = {}
    appels = []

    def ecrit():
        with open(sortie, "w") as fh:
            json.dump({"modele": modele, "prompt": PROMPT, "fps": ai_service.FPS_MAX,
                       "appels": appels}, fh, ensure_ascii=False, indent=2)

    try:
        for clip in (args.a, args.b):
            fichiers[clip] = ai_service._task_upload(os.path.join(DATA, clip))
        for passe in range(1, args.passes + 1):
            for ordre in ((args.a, args.b), (args.b, args.a)):
                if appels:
                    # Deux videos par appel, ~100 k tokens : le palier gratuit plafonne a
                    # 250 k tokens d'entree par minute, et coupe le troisieme appel.
                    time.sleep(40)
                rep = _appel(modele, fichiers[ordre[0]], fichiers[ordre[1]])
                usage = log_usage(model=modele, response=rep, label=f"paire {ordre}")
                v = _verdict(rep.text)
                designe = {"A": ordre[0], "B": ordre[1]}.get(v)
                appels.append({"passe": passe, "A": ordre[0], "B": ordre[1], "verdict": v,
                               "designe": designe, "texte": rep.text,
                               "pensees": ai_service._pensees(rep),
                               "usage": ai_service._usage_public(usage)})
                print(f"passe {passe}  A={ordre[0]}  B={ordre[1]}  -> {v} = {designe}",
                      file=sys.stderr)
                ecrit()
    finally:
        for f in fichiers.values():
            try:
                ai_service.client.files.delete(name=f.name)
            except Exception:
                pass

    print(sortie, file=sys.stderr)


if __name__ == "__main__":
    main()
