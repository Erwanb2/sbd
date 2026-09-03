"""Description biomécanique riche sur la vidéo, décision en Python.

Idée d'Erwan. Tous les marqueurs du sumo ne passent pas par l'écartement des
pieds — le torse plus redressé, les hanches plus basses, les tibias verticaux,
les genoux poussés vers l'extérieur, la course de barre plus courte se lisent DE
PROFIL. Or c'est justement le profil qui rend la stance illisible. On demande donc
beaucoup de variables observables, aucune conclusion, et on arbitre en Python.

Le prompt ne prononce jamais "sumo" ni "conventional" (cf. règle de méthode 4 :
sinon le modèle rationalise un verdict déjà échantillonné).

Usage:
    uv run python biomech_video_cli.py ../data/oscar_sumo_short.mp4 -r 2
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

PROMPT = """
    This is a video of a barbell deadlift. Describe the lifter's body position at the
    START of the pull, when the bar is still on the floor and the hands are gripping it.

    Report only what you can SEE. Do not name or classify the style of the lift.
    If something is genuinely not visible, say so rather than guessing.

    Use the whole video: the walk-in, the setup, the pull and the lockout.
    """


class Biomech(BaseModel):
    torso_angle: str = Field(description="near_vertical, mid_lean, near_horizontal, not_visible")
    hip_height: str = Field(description="above_knees, level_with_knees, below_knees, not_visible")
    shin_angle: str = Field(description="vertical, slightly_forward, strongly_forward, not_visible")
    knee_direction: str = Field(description="pushed_out_laterally, tracking_forward, not_visible")
    toe_direction: str = Field(description="forward, flared_outward, not_visible")
    arms_vs_legs: str = Field(description="between_the_legs, outside_the_legs, not_visible")
    bar_travel: str = Field(description="short, medium, long, not_visible")
    stance_width: str = Field(description="narrow, hip_width, shoulder_width, wider_than_shoulders, not_visible")
    camera_sees: str = Field(description="one short factual sentence on what the camera actually shows")


# Chaque marqueur vote. Les poids reflètent la robustesse à la vue de profil :
# torse, hanches et tibias se lisent sans voir l'écartement, la stance non.
INDICES_SUMO = {
    "torso_angle": {"near_vertical": 2},
    "hip_height": {"below_knees": 2, "level_with_knees": 1},
    "shin_angle": {"vertical": 2},
    "knee_direction": {"pushed_out_laterally": 2},
    "toe_direction": {"flared_outward": 1},
    "arms_vs_legs": {"between_the_legs": 1},
    "bar_travel": {"short": 1},
    "stance_width": {"wider_than_shoulders": 2},
}
INDICES_CONV = {
    "torso_angle": {"near_horizontal": 2, "mid_lean": 1},
    "hip_height": {"above_knees": 2},
    "shin_angle": {"strongly_forward": 2, "slightly_forward": 1},
    "knee_direction": {"tracking_forward": 2},
    "toe_direction": {"forward": 1},
    "arms_vs_legs": {"outside_the_legs": 2},
    "bar_travel": {"long": 1},
    "stance_width": {"narrow": 1, "hip_width": 1, "shoulder_width": 1},
}


def score(obs):
    s = c = 0
    detail = []
    for champ, table in INDICES_SUMO.items():
        v = getattr(obs, champ)
        ps, pc = table.get(v, 0), INDICES_CONV[champ].get(v, 0)
        s += ps
        c += pc
        detail.append(f"{champ}={v}(+{ps}S/+{pc}C)")
    return s, c, detail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("-r", "--runs", type=int, default=2)
    parser.add_argument("-m", "--model", default="gemini-3.5-flash")
    parser.add_argument("--images", type=int, default=0,
                        help="0 = vidéo ; sinon N frames au lieu de la vidéo")
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")
    _load_env()

    from google import genai
    from google.genai import types

    client = genai.Client()

    if args.images:
        contenu = _load_extraire_images()(args.video, num_images=args.images)
        source = f"{args.images} images"
    else:
        t0 = time.time()
        f = client.files.upload(file=args.video)
        while f.state.name == "PROCESSING":
            time.sleep(2)
            f = client.files.get(name=f.name)
        if f.state.name == "FAILED":
            sys.exit("Upload échoué")
        contenu = [f]
        source = f"vidéo (upload {time.time()-t0:.0f}s)"

    print(f"=== {os.path.basename(args.video)} | {source} | {args.model}\n")
    verdicts = collections.Counter()
    try:
        for run in range(1, args.runs + 1):
            t = time.time()
            chat = client.chats.create(
                model=args.model,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Biomech,
                    temperature=0.0,
                ),
            )
            o = _with_retry(lambda: chat.send_message([*contenu, PROMPT])).parsed
            s, c, detail = score(o)
            verdict = "sumo deadlift" if s > c else "conventional deadlift" if c > s else "egalite"
            verdicts[verdict] += 1
            print(f"run {run} ({time.time()-t:.0f}s)  sumo={s}  conv={c}  -> {verdict}")
            for d in detail:
                print(f"      {d}")
            print(f"      · {o.camera_sees}\n")
    finally:
        if not args.images:
            try:
                client.files.delete(name=contenu[0].name)
            except Exception:
                pass
    print("  ".join(f"{k} x{v}" for k, v in verdicts.most_common()))


if __name__ == "__main__":
    main()
