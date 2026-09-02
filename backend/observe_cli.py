"""Mesure la stabilité de la PERCEPTION, séparément du verdict.

Le prompt ne mentionne ni "sumo" ni "conventional" ni aucune catégorie : le
modèle n'a donc aucune conclusion à rationaliser, et ses réponses reflètent ce
qu'il voit plutôt qu'une justification a posteriori du verdict échantillonné.

On rejoue N fois et on compte, champ par champ.

Usage:
    uv run python observe_cli.py ../data/oscar_sumo.mp4 -r 5
"""

import argparse
import collections
import os
import sys
import time

from pydantic import BaseModel, Field

from classify_frames_cli import _load_env
from extract_frames_cli import DEFAULT_VIDEO, _load_extraire_images
from flakiness_cli import _with_retry

PROMPT_OBSERVE = """
    These images are frames from a barbell lifting video.

    Look ONLY at the moment where the lifter is bent over with both hands gripping
    the bar and the bar still resting on the floor. Describe what you SEE.
    Do not name or classify the exercise variation.

    - feet_width: how far apart the feet are, relative to the lifter's own shoulders.
    - hands_vs_shins: whether the hands grip the bar inside the shins (between the
      legs) or outside the shins.
    - feet_visible: whether BOTH feet are fully visible and not hidden by a plate,
      a limb, or the edge of the frame.
    - lower_body_notes: one short factual sentence on what is or isn't visible.
    """


class StanceObservation(BaseModel):
    feet_width: str = Field(
        description="one of: narrow, hip_width, shoulder_width, wider_than_shoulders, not_visible"
    )
    hands_vs_shins: str = Field(description="one of: inside, outside, not_visible")
    feet_visible: bool
    lower_body_notes: str


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", default=DEFAULT_VIDEO)
    parser.add_argument("-r", "--runs", type=int, default=5)
    parser.add_argument("-n", "--num-images", type=int, default=10)
    parser.add_argument("--delay", type=float, default=4.0)
    parser.add_argument("-m", "--model", default="gemini-3.5-flash")
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")

    _load_env()
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY manquante (backend/.env)")

    images = _load_extraire_images()(args.video, num_images=args.num_images)
    if not images:
        sys.exit("Aucune image extraite (vidéo illisible ?)")

    from google import genai
    from google.genai import types

    client = genai.Client()
    print(f"Modèle utilisé : {args.model}", flush=True)

    fields = collections.defaultdict(collections.Counter)
    notes = []
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
                lambda: chat.send_message(message=[*images, PROMPT_OBSERVE])
            ).parsed
            fields["feet_width"][obs.feet_width] += 1
            fields["hands_vs_shins"][obs.hands_vs_shins] += 1
            fields["feet_visible"][obs.feet_visible] += 1
            notes.append(obs.lower_body_notes)
        except Exception as exc:
            fields["ERREUR"][f"{type(exc).__name__}: {str(exc)[:80]}"] += 1
        time.sleep(args.delay)

    print(f"=== {os.path.basename(args.video)} | {args.runs} runs | {len(images)} frames ===")
    for name, counter in fields.items():
        detail = "  ".join(f"{k} x{v}" for k, v in counter.most_common())
        stable = "STABLE  " if len(counter) == 1 else "INSTABLE"
        print(f"  [{stable}] {name:16} -> {detail}")
    for n in notes:
        print(f"     · {n}")


if __name__ == "__main__":
    main()
