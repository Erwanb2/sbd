"""Escalade sur la VIDÉO plutôt que sur des images fixes.

Idée d'Erwan : la vidéo est de toute façon déjà uploadée chez Google par
_task_upload_video, en parallèle de la détection. L'escalade pourrait la
réutiliser — ce qui supprime le plafond de 3 images de flash, et surtout donne
au modèle le MOUVEMENT, qui révèle la stance bien mieux qu'une posture figée.

Test décisif sur les clips filmés dans l'axe de la barre, où l'écartement des
pieds est écrasé par la perspective sur une image fixe.

Usage:
    uv run python video_escalation_cli.py ../data/oscar_sumo_short.mp4 -r 2
"""

import argparse
import collections
import os
import sys
import time

from classify_frames_cli import _load_env
from corpus_eval import decide
from flakiness_cli import _with_retry
from flakiness_cli import PROMPT_PROD
from observe_cli import PROMPT_OBSERVE, StanceObservation
from schemas import VideoClassification

PROMPT_VIDEO = PROMPT_OBSERVE.replace(
    "These images are frames from a barbell lifting video.",
    "This is a video of a barbell lift. Use the MOTION across the whole lift — the\n"
    "setup, the pull off the floor and the lockout — to judge the stance. A moment\n"
    "where the lifter walks in or stands up often reveals the feet better than the\n"
    "setup itself.",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("-r", "--runs", type=int, default=2)
    parser.add_argument("-m", "--model", default="gemini-3.5-flash")
    parser.add_argument(
        "--prompt-mode", default="observe", choices=["observe", "prod"],
        help="observe = observations + règle Python ; prod = prompt et schéma de production",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")
    _load_env()

    from google import genai
    from google.genai import types

    client = genai.Client()

    t0 = time.time()
    fichier = client.files.upload(file=args.video)
    while fichier.state.name == "PROCESSING":
        time.sleep(2)
        fichier = client.files.get(name=fichier.name)
    if fichier.state.name == "FAILED":
        sys.exit("Upload échoué côté Google")
    print(f"upload + processing : {time.time() - t0:.0f}s")

    mode_prod = args.prompt_mode == "prod"
    schema = VideoClassification if mode_prod else StanceObservation
    prompt = PROMPT_PROD if mode_prod else PROMPT_VIDEO

    verdicts = collections.Counter()
    try:
        for run in range(1, args.runs + 1):
            t = time.time()
            chat = client.chats.create(
                model=args.model,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0,
                ),
            )
            rep = _with_retry(lambda: chat.send_message([fichier, prompt])).parsed
            if mode_prod:
                pred = rep.mouvement_detecte
                verdicts[pred] += 1
                print(f"run {run} ({time.time()-t:.0f}s) -> {pred}")
                continue
            pred = decide(rep.feet_width, rep.hands_vs_shins)
            verdicts[pred] += 1
            print(f"run {run} ({time.time()-t:.0f}s) | {rep.feet_width} + "
                  f"{rep.hands_vs_shins} | visible={rep.feet_visible} -> {pred}")
            print(f"        · {rep.lower_body_notes}")
    finally:
        try:
            client.files.delete(name=fichier.name)
        except Exception:
            pass

    print("\n" + "  ".join(f"{k} x{v}" for k, v in verdicts.most_common()))


if __name__ == "__main__":
    main()
