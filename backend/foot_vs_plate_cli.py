"""Reformulation : position du pied par rapport aux DISQUES, pas écartement des pieds.

Constat visuel : sur les clips filmés dans l'axe de la barre, on ne voit jamais les
deux pieds en même temps — le disque du premier plan masque le second. Demander
« quel écartement ? » est donc une question sans réponse.

Mais un seul pied suffit si on le situe par rapport à un repère fixe : en sumo les
pieds sont écartés jusqu'à frôler les disques, en conventionnel ils sont au centre
de la barre, loin des disques. Le proxy survit à la perspective.

Usage:
    uv run python foot_vs_plate_cli.py ../data/oscar_sumo_short.mp4 -r 5
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

PROMPT = """
    These images show a barbell deadlift setup.

    Do NOT try to measure how far apart the two feet are — in many camera angles the
    second foot is hidden behind the near plate, so that question has no answer.

    Instead, locate the feet ALONG THE BAR, using the plates as the reference:
    - "near_plates"   the foot (or feet) sits close to the weight plates, out near
                      the end of the bar, almost touching the plates or the sleeve
    - "mid_bar"       the foot sits well inside, around the middle of the bar, with a
                      clear gap of bare bar between the foot and the plates
    - "not_visible"   no foot can be located at all

    Also report how much bare bar you can see between the nearest foot and the plate:
    "none", "small_gap", "large_gap", or "not_visible".
    """


class FootVsPlate(BaseModel):
    foot_position: str = Field(description="near_plates, mid_bar, or not_visible")
    gap_foot_to_plate: str = Field(description="none, small_gap, large_gap, not_visible")
    notes: str


def decide(foot_position, gap):
    """Pieds vers les disques = stance large = sumo."""
    if foot_position == "near_plates" or gap == "none":
        return "sumo deadlift"
    if foot_position == "mid_bar" or gap in ("small_gap", "large_gap"):
        return "conventional deadlift"
    return "indetermine"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", default=DEFAULT_VIDEO)
    parser.add_argument("-r", "--runs", type=int, default=5)
    parser.add_argument("-n", "--num-images", type=int, default=3)
    parser.add_argument("-m", "--model", default="gemini-3.5-flash-lite")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")
    _load_env()

    from google import genai
    from google.genai import types

    client = genai.Client()
    images = _load_extraire_images()(args.video, num_images=args.num_images)

    verdicts, champs = collections.Counter(), collections.defaultdict(collections.Counter)
    notes = []
    for _ in range(args.runs):
        try:
            chat = client.chats.create(
                model=args.model,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FootVsPlate,
                    temperature=0.0,
                ),
            )
            o = _with_retry(lambda: chat.send_message(message=[*images, PROMPT])).parsed
            champs["pos"][o.foot_position] += 1
            champs["gap"][o.gap_foot_to_plate] += 1
            verdicts[decide(o.foot_position, o.gap_foot_to_plate)] += 1
            notes.append(o.notes)
        except Exception as exc:
            verdicts[f"ERREUR:{type(exc).__name__}"] += 1
        time.sleep(args.delay)

    print(f"=== {os.path.basename(args.video)} | {args.runs} runs | {args.model}")
    for nom, c in champs.items():
        print(f"  {nom:<4} -> " + "  ".join(f"{k} x{v}" for k, v in c.most_common()))
    print("  verdict -> " + "  ".join(f"{k} x{v}" for k, v in verdicts.most_common()))
    for n in notes[:3]:
        print(f"     · {n}")


if __name__ == "__main__":
    main()
