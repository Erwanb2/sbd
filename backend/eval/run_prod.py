"""Le chemin de production tel quel, sur un clip de data/, sortie dans eval/runs.

    cd backend
    uv run python eval/run_prod.py [--clip pr_160.mp4] [--modele 3.5] [--suffixe prod_video24]

`upload_and_detect_concurrent` puis `analyze_movement`, rien d'autre : c'est la run
temoin contre laquelle se compare tout essai qui change une seule variable
(eval/images_annotees.py, par exemple). Le fichier Google est supprime apres.
"""

import argparse
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(ICI)
sys.path.insert(0, BACKEND)

import ai_service                                   # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", default="pr_160.mp4")
    ap.add_argument("--modele", default="3.5")
    ap.add_argument("--suffixe", default="prod_video24")
    args = ap.parse_args()

    path = os.path.join(DATA, args.clip)
    det = ai_service.upload_and_detect_concurrent(path)
    print(f"{det['mouvement_detecte']}, {det['nb_candidats']} candidat(s)", file=sys.stderr)
    try:
        res = ai_service.analyze_movement(det["file_name"], det["mouvement_detecte"], args.modele)
    finally:
        try:
            ai_service.client.files.delete(name=det["file_name"])
        except Exception:
            pass
    nom = os.path.splitext(args.clip)[0]
    sortie = os.path.join(ICI, "runs", f"{nom}_{args.suffixe}.json")
    with open(sortie, "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print(f"{sortie} : {res['note_sur_20']}/20, usage {res['debug']['appel']['usage']}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
