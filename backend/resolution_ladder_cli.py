"""À quelle résolution la lecture de la stance s'effondre-t-elle ?

Expérience contrôlée : on prend des clips que le modèle lit correctement et on
ne fait varier QUE les pixels. Le contenu, l'angle et les frames restent
identiques — donc tout basculement observé est imputable à la résolution seule.

Sert à calibrer le diagnostic tiré d'oscar_sumo_short (266x480 contre 480x864,
soit 55 %), qui ne reposait que sur un seul exemple.

Usage:
    uv run python resolution_ladder_cli.py -r 3
"""

import argparse
import collections
import os
import sys
import time

from classify_frames_cli import _load_env
from extract_frames_cli import _load_extraire_images
from flakiness_cli import _with_retry
from observe_cli import PROMPT_OBSERVE, StanceObservation

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Clips lus correctement et de façon stable par flash-lite : deux sumos, deux
# conventionnels. On veut voir lequel des deux camps casse en premier.
CLIPS = [
    ("engueran_sumo.mp4", "sumo"),
    ("sumo_deadlift.mp4", "sumo"),
    ("jeff_nippard.mp4", "conventional"),
    ("erwan_last.mp4", "conventional"),
]
ECHELLE = [1.0, 0.75, 0.55, 0.40, 0.30]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-r", "--runs", type=int, default=3)
    parser.add_argument("-n", "--num-images", type=int, default=3)
    parser.add_argument("-m", "--model", default="gemini-3.5-flash-lite")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    _load_env()
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY manquante")

    from google import genai
    from google.genai import types

    client = genai.Client()
    extraire = _load_extraire_images()

    print(f"{len(CLIPS)} clips x {len(ECHELLE)} paliers x {args.runs} runs "
          f"= {len(CLIPS) * len(ECHELLE) * args.runs} appels | {args.model}\n")

    for fichier, verite in CLIPS:
        path = os.path.join(DATA, fichier)
        if not os.path.isfile(path):
            print(f"{fichier} : INTROUVABLE")
            continue
        base = extraire(path, num_images=args.num_images)
        w0, h0 = base[0].size
        print(f"--- {fichier}  ({verite})  source {w0}x{h0}")

        for echelle in ECHELLE:
            if echelle == 1.0:
                frames = base
            else:
                frames = [
                    img.resize((max(1, int(w0 * echelle)), max(1, int(h0 * echelle))))
                    for img in base
                ]
            w, h = frames[0].size
            largeurs, mains = collections.Counter(), collections.Counter()
            for _ in range(args.runs):
                try:
                    chat = client.chats.create(
                        model=args.model,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=StanceObservation,
                            temperature=0.0,
                        ),
                    )
                    obs = _with_retry(
                        lambda: chat.send_message(message=[*frames, PROMPT_OBSERVE])
                    ).parsed
                    largeurs[obs.feet_width] += 1
                    mains[obs.hands_vs_shins] += 1
                except Exception as exc:
                    largeurs[f"ERR:{type(exc).__name__}"] += 1
                time.sleep(args.delay)

            fw = "  ".join(f"{k} x{v}" for k, v in largeurs.most_common())
            hd = "  ".join(f"{k} x{v}" for k, v in mains.most_common())
            print(f"  {echelle:>5.0%} {w:>4}x{h:<4} | feet: {fw:<38} | mains: {hd}")
        print()


if __name__ == "__main__":
    main()
