"""Évalue l'approche par observations sur tout le corpus deadlift.

Pour chaque clip : N observations flash-lite (3 frames), vote majoritaire sur
chaque champ, puis application EN PYTHON de la règle de décision. On compare au
label de eval/ground_truth.json et on mesure le taux d'escalade — la proportion
de vidéos dont les observations sont trop douteuses pour trancher sans flash.

Usage:
    uv run python corpus_eval.py -r 3
    uv run python corpus_eval.py -r 3 --skip "Arthur Garrec...,oscar_sumo"
"""

import argparse
import collections
import json
import os
import sys
import time

from classify_frames_cli import _load_env
from extract_frames_cli import _load_extraire_images
from observe_cli import PROMPT_OBSERVE, StanceObservation

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
GT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval", "ground_truth.json")


def crop_fixe(img):
    """Bande centrale + moitié basse : la zone où se joue la stance.

    Recadrer ne crée aucun pixel, mais supprime la surface inutile (plafond, murs)
    qui consomme le budget de tokens de l'image. Validé à l'œil sur les 21 clips :
    correct sur ~16, mauvais sur long_deadlift (ne garde que le sol). D'où le mode
    "both", qui conserve l'image entière à côté du recadrage.
    """
    w, h = img.size
    return img.crop((int(w * 0.10), int(h * 0.42), int(w * 0.90), int(h * 0.88)))


def prepare(images, mode):
    if mode == "plain":
        return list(images)
    if mode == "crop":
        return [crop_fixe(i) for i in images]
    if mode == "both":
        paires = []
        for i in images:
            paires.extend([i, crop_fixe(i)])
        return paires
    raise ValueError(mode)


def decide(feet_width, hands_vs_shins):
    """Règle de décision, appliquée en Python et non par le modèle.

    Sumo seulement si les DEUX critères concordent — c'est le OU du prompt de prod
    qui fait basculer en sumo les conventionnels à prise étroite.
    """
    if feet_width == "wider_than_shoulders" and hands_vs_shins == "inside":
        return "sumo deadlift"
    return "conventional deadlift"


def is_doubtful(feet_width, hands_vs_shins, stable):
    """Signature des observations sur lesquelles flash-lite s'est montré non fiable.

    Les 3 clips ratés partagent : largeur illisible ou moyenne, mains 'inside'.
    Un champ instable entre les runs vaut aussi escalade.
    """
    if not stable:
        return True
    return hands_vs_shins == "inside" and feet_width in ("not_visible", "shoulder_width")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-r", "--runs", type=int, default=3)
    parser.add_argument("-n", "--num-images", type=int, default=3)
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("-m", "--model", default="gemini-3.5-flash-lite")
    parser.add_argument("--skip", default="")
    parser.add_argument(
        "--mode", default="plain", choices=["plain", "crop", "both"],
        help="plain = frames telles quelles ; crop = recadrées ; both = les deux",
    )
    args = parser.parse_args()

    _load_env()
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY manquante (backend/.env)")

    gt = json.load(open(GT_PATH, encoding="utf-8"))
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    clips = [
        v for v in gt["videos"]
        if "deadlift" in v["movement"] and v["file"] not in skip
    ]

    from google import genai
    from google.genai import types

    client = genai.Client()
    extraire = _load_extraire_images()

    print(f"{len(clips)} clips | {args.runs} runs | {args.num_images} frames "
          f"| mode={args.mode} | {args.model}")
    print(f"~{len(clips) * args.runs} appels\n")
    print(f"{'clip':<46} {'vérité':<12} {'feet_width':<21} {'hands':<9} {'prédit':<12} {'':4} escalade")

    ok = escalades = 0
    for clip in clips:
        path = os.path.join(DATA_DIR, clip["file"])
        if not os.path.isfile(path):
            print(f"{clip['file'][:45]:<46} FICHIER INTROUVABLE")
            continue

        images = prepare(extraire(path, num_images=args.num_images), args.mode)
        fields = collections.defaultdict(collections.Counter)
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
                obs = chat.send_message(message=[*images, PROMPT_OBSERVE]).parsed
                fields["feet_width"][obs.feet_width] += 1
                fields["hands"][obs.hands_vs_shins] += 1
            except Exception as exc:
                fields["erreur"][type(exc).__name__] += 1
            time.sleep(args.delay)

        if not fields["feet_width"]:
            print(f"{clip['file'][:45]:<46} ÉCHEC : {dict(fields['erreur'])}")
            continue

        fw = fields["feet_width"].most_common(1)[0][0]
        hd = fields["hands"].most_common(1)[0][0]
        stable = len(fields["feet_width"]) == 1 and len(fields["hands"]) == 1
        pred = decide(fw, hd)
        doubt = is_doubtful(fw, hd, stable)

        ok += pred == clip["movement"]
        escalades += doubt
        mark = "OK " if pred == clip["movement"] else "FAUX"
        fw_disp = fw + ("" if stable else "*")
        print(
            f"{clip['file'][:45]:<46} {clip['movement'][:11]:<12} {fw_disp:<21} "
            f"{hd:<9} {pred[:11]:<12} {mark:<4} {'OUI' if doubt else '-'}"
        )

    n = len(clips)
    print(f"\nRègle Python sur flash-lite seul : {ok}/{n} corrects")
    print(f"Escalade vers flash              : {escalades}/{n} clips "
          f"({100 * escalades / n:.0f} %)")
    if escalades:
        print(f"→ avec 20 runs flash/jour, capacité ≈ {int(20 * n / escalades)} vidéos/jour")
    print("(* = champ instable entre les runs)")


if __name__ == "__main__":
    main()
