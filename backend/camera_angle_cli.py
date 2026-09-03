"""L'angle de caméra prédit-il l'échec de la détection ?

Hypothèse géométrique : dans un deadlift, les pieds sont écartés le long de l'axe
de la barre. Si la caméra est DANS cet axe (filmé depuis le bout de la barre),
l'écartement se projette en profondeur — il est écrasé, et le disque du premier
plan masque le reste. La stance devient illisible quel que soit le modèle.
Si la caméra est perpendiculaire à la barre, l'écartement traverse l'image et se lit.

Ça expliquerait mieux les échecs que la résolution : engueran_sumo est lu
correctement à 202x360, alors qu'oscar_sumo_short échoue à 266x480.

On demande au modèle une question PERCEPTIVE simple (où est la caméra ?) plutôt
qu'un jugement (quelle largeur ?), et on croise avec la justesse de la détection.

Usage:
    uv run python camera_angle_cli.py -r 3
"""

import argparse
import collections
import json
import os
import sys
import time

from pydantic import BaseModel, Field

from classify_frames_cli import _load_env
from corpus_eval import DATA_DIR, GT_PATH, decide
from extract_frames_cli import _load_extraire_images
from flakiness_cli import _with_retry

PROMPT = """
    These images are frames from a barbell deadlift video.

    Describe the CAMERA POSITION relative to the barbell, and what that makes visible.

    - camera_view:
        "along_bar"        the camera looks down the length of the bar (one loaded
                           plate is close to the lens and hides part of the lifter)
        "perpendicular"    the bar runs across the frame, left to right
        "angled"           somewhere in between
    - stance_readable: can you actually measure how far apart the feet are, left to
      right in the image? Say false if the feet are one behind the other in depth,
      or hidden behind a plate.
    - feet_width: narrow, hip_width, shoulder_width, wider_than_shoulders, not_visible
    - hands_vs_shins: inside, outside, not_visible
    """


class CameraObservation(BaseModel):
    camera_view: str = Field(description="along_bar, perpendicular, or angled")
    stance_readable: bool
    feet_width: str
    hands_vs_shins: str


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

    gt = json.load(open(GT_PATH, encoding="utf-8"))
    clips = [v for v in gt["videos"] if "deadlift" in v["movement"]]

    from google import genai
    from google.genai import types

    client = genai.Client()
    extraire = _load_extraire_images()

    print(f"{len(clips)} clips x {args.runs} runs = {len(clips) * args.runs} appels | {args.model}\n")
    print(f"{'clip':<40} {'vérité':<13} {'caméra':<15} {'lisible':<8} {'prédit':<13} ok")

    lignes = []
    for c in clips:
        p = os.path.join(DATA_DIR, c["file"])
        if not os.path.isfile(p):
            continue
        images = extraire(p, num_images=args.num_images)
        champs = collections.defaultdict(collections.Counter)
        for _ in range(args.runs):
            try:
                chat = client.chats.create(
                    model=args.model,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CameraObservation,
                        temperature=0.0,
                    ),
                )
                o = _with_retry(lambda: chat.send_message(message=[*images, PROMPT])).parsed
                champs["vue"][o.camera_view] += 1
                champs["lisible"][o.stance_readable] += 1
                champs["fw"][o.feet_width] += 1
                champs["hd"][o.hands_vs_shins] += 1
            except Exception as exc:
                champs["err"][type(exc).__name__] += 1
            time.sleep(args.delay)

        if not champs["vue"]:
            print(f"{c['file'][:39]:<40} ÉCHEC {dict(champs['err'])}")
            continue
        vue = champs["vue"].most_common(1)[0][0]
        lisible = champs["lisible"].most_common(1)[0][0]
        pred = decide(champs["fw"].most_common(1)[0][0], champs["hd"].most_common(1)[0][0])
        ok = pred == c["movement"]
        lignes.append((vue, lisible, ok))
        print(f"{c['file'][:39]:<40} {c['movement'][:12]:<13} {vue:<15} "
              f"{str(lisible):<8} {pred[:12]:<13} {'OK' if ok else 'FAUX'}")

    print("\n--- L'angle prédit-il l'échec ? ---")
    for vue in ("perpendicular", "angled", "along_bar"):
        s = [ok for v, _, ok in lignes if v == vue]
        if s:
            print(f"  caméra {vue:<15} : {sum(s)}/{len(s)} corrects")
    for lis in (True, False):
        s = [ok for _, l, ok in lignes if l == lis]
        if s:
            print(f"  stance_readable={str(lis):<5}   : {sum(s)}/{len(s)} corrects")


if __name__ == "__main__":
    main()
