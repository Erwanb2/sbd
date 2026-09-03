"""Jugement COMPARATIF plutôt qu'absolu, avec deux références étiquetées.

Constat : mesurer « quelle largeur ? » dans l'absolu échoue sur les clips filmés
dans l'axe de la barre, où la perspective écrase l'écartement. Mais apparier une
image à un exemple de référence est une tâche bien plus facile.

Le modèle ne voit que « Style A » et « Style B » — jamais les mots sumo ou
conventional. La correspondance est tenue en Python, ce qui supprime tout biais
lexical et empêche la rationalisation (règle de méthode 4).

L'ordre A/B est contrebalancé : si le modèle répond toujours « A », c'est un biais
de position, pas une reconnaissance.

Usage:
    uv run python fewshot_compare_cli.py ../data/oscar_sumo_short.mp4 -r 3
"""

import argparse
import collections
import os
import sys
import time

from pydantic import BaseModel, Field

from classify_frames_cli import _load_env
from extract_frames_cli import _load_extraire_images
from flakiness_cli import _with_retry

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Les références doivent être des clips que le modèle PERÇOIT correctement, pas
# seulement des clips dont on connaît le label. Premier essai avec jeff_nippard en
# référence conventionnelle : raté, le modèle le décrit lui-même comme « wide-stance
# sumo » (il est filmé dans l'axe de la barre, cas où il lit `hands=inside` à tort).
# p_deadlift est filmé de face et sort `hip_width + outside` de façon stable.
REF_SUMO = "engueran_sumo.mp4"
REF_CONV = "p_deadlift.mp4"

# Un choix forcé entre deux options s'est révélé contaminé par un biais de position
# (le modèle répondait "A" quel que soit le contenu de A). On note donc UNE seule
# référence à la fois, sur une échelle, et c'est Python qui compare les deux scores.
PROMPT = """
    The REFERENCE images and the TEST images show two deadlifts.

    Rate how similar the TEST lift's setup is to the REFERENCE lift's setup, on a
    scale of 0 to 10, where 10 means the two lifters set up the same way.

    Judge by resemblance, not by measurement — the camera angle may hide the feet, so
    rely on whatever is visible: the spread of the thighs, where the arms hang
    relative to the legs, how the knees point, how upright the torso is.

    - similarity: integer 0 to 10
    - reason: one short sentence naming the visual cue that decided it
    """


class Comparaison(BaseModel):
    similarity: int = Field(description="0 to 10, how similar the TEST setup is to the REFERENCE")
    reason: str


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("-r", "--runs", type=int, default=3, help="runs par ordre A/B")
    parser.add_argument("-n", "--num-images", type=int, default=2)
    parser.add_argument("-m", "--model", default="gemini-3.5-flash-lite")
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--ref-sumo", default=REF_SUMO)
    parser.add_argument("--ref-conv", default=REF_CONV)
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")
    _load_env()

    from google import genai
    from google.genai import types

    client = genai.Client()
    ex = _load_extraire_images()

    ref_sumo = ex(os.path.join(DATA, args.ref_sumo), num_images=args.num_images)
    ref_conv = ex(os.path.join(DATA, args.ref_conv), num_images=args.num_images)
    cible = ex(args.video, num_images=args.num_images + 1)

    def noter(ref):
        chat = client.chats.create(
            model=args.model,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Comparaison,
                temperature=0.0,
            ),
        )
        contenu = ["REFERENCE lift:", *ref, "TEST lift:", *cible]
        return _with_retry(lambda: chat.send_message(message=[*contenu, PROMPT])).parsed

    verdicts = collections.Counter()
    scores_s, scores_c, raisons = [], [], []
    for _ in range(args.runs):
        try:
            os_ = noter(ref_sumo)
            time.sleep(args.delay)
            oc = noter(ref_conv)
            scores_s.append(os_.similarity)
            scores_c.append(oc.similarity)
            if os_.similarity > oc.similarity:
                verdicts["sumo deadlift"] += 1
            elif oc.similarity > os_.similarity:
                verdicts["conventional deadlift"] += 1
            else:
                verdicts["egalite"] += 1
            raisons.append(f"S={os_.similarity} « {os_.reason[:70]} » | "
                           f"C={oc.similarity} « {oc.reason[:70]} »")
        except Exception as exc:
            verdicts[f"ERREUR:{type(exc).__name__}"] += 1
        time.sleep(args.delay)

    print(f"=== {os.path.basename(args.video)} | {args.model} | {args.runs} runs")
    print(f"  similarité au SUMO de réf         -> {scores_s}")
    print(f"  similarité au CONVENTIONNEL de réf -> {scores_c}")
    print("  verdict -> " + "  ".join(f"{k} x{v}" for k, v in verdicts.most_common()))
    for r in raisons[:2]:
        print(f"     · {r}")


if __name__ == "__main__":
    main()
