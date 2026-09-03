"""Pipeline en 2 passes : flash-lite SÉLECTIONNE les frames, flash JUGE.

Hypothèse testée : si flash rate un clip, ce n'est pas qu'il en est incapable
(il réussit le même mouvement en version longue) mais que les 3 frames uniformes
tombent sur le lockout et ratent le setup.

Passe 1 — flash-lite choisit K frames dans un pool de 50 (il encaisse ce volume,
          flash non). Gratuit.
Passe 2 — flash observe UNIQUEMENT ces K frames, sans qu'on nomme jamais les
          catégories, puis la règle ET s'applique en Python.

Les frames retenues sont écrites sur disque à chaque run pour relecture humaine :
un échec de sélection et un échec de perception ne se corrigent pas pareil.

Usage:
    uv run python select_then_judge_cli.py ../data/oscar_sumo_short.mp4 -r 3
"""

import argparse
import collections
import os
import sys
import time

from classify_frames_cli import _load_env
from corpus_eval import decide
from extract_frames_cli import DEFAULT_VIDEO, _load_extraire_images
from flakiness_cli import _select_frames, _with_retry
from observe_cli import PROMPT_OBSERVE, StanceObservation

MODEL_SELECT = "gemini-3.5-flash-lite"
MODEL_JUDGE = "gemini-3.5-flash"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", default=DEFAULT_VIDEO)
    parser.add_argument("-r", "--runs", type=int, default=3)
    parser.add_argument("-k", "--keep", type=int, default=3, help="frames envoyées au juge")
    parser.add_argument("-p", "--pool", type=int, default=50)
    parser.add_argument("--model-select", default=MODEL_SELECT)
    parser.add_argument("--model-judge", default=MODEL_JUDGE)
    parser.add_argument("-o", "--output-dir", default="extracted_frames/select_judge")
    parser.add_argument("--delay", type=float, default=3.0)
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")

    _load_env()
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY manquante (backend/.env)")

    pool = _load_extraire_images()(args.video, num_images=args.pool)
    if not pool:
        sys.exit("Aucune image extraite (vidéo illisible ?)")

    from google import genai
    from google.genai import types

    client = genai.Client()

    base = os.path.splitext(os.path.basename(args.video))[0].replace(" ", "_")
    out_dir = os.path.join(args.output_dir, base)
    os.makedirs(out_dir, exist_ok=True)

    # Planche contact du pool complet : sert de référence pour juger la sélection.
    cols = 10
    rows = (len(pool) + cols - 1) // cols
    w, h = pool[0].size
    tw, th = int(w * 200 / w), int(h * 200 / w)
    from PIL import Image, ImageDraw

    sheet = Image.new("RGB", (cols * tw, rows * th), "black")
    draw = ImageDraw.Draw(sheet)
    for i, img in enumerate(pool):
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(img.resize((tw, th)), (x, y))
        draw.text((x + 4, y + 4), str(i + 1), fill="yellow")
    sheet.save(os.path.join(out_dir, "pool_planche_contact.png"))

    print(f"Vidéo        : {os.path.basename(args.video)}")
    print(f"Sélection    : {args.model_select} sur {len(pool)} frames -> {args.keep}")
    print(f"Juge         : {args.model_judge}")
    print(f"Frames       : {out_dir}\n")

    verdicts = collections.Counter()
    for run in range(1, args.runs + 1):
        try:
            frames, idx = _select_frames(
                client, types, pool, args.keep, args.model_select
            )
            run_dir = os.path.join(out_dir, f"run_{run}")
            os.makedirs(run_dir, exist_ok=True)
            for rang, (img, i) in enumerate(zip(frames, idx), start=1):
                img.save(os.path.join(run_dir, f"{rang}_frame_{i:02d}.png"))

            chat = client.chats.create(
                model=args.model_judge,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StanceObservation,
                    temperature=0.0,
                ),
            )
            obs = _with_retry(
                lambda: chat.send_message(message=[*frames, PROMPT_OBSERVE])
            ).parsed
            pred = decide(obs.feet_width, obs.hands_vs_shins)
            verdicts[pred] += 1
            print(
                f"run {run} | frames {idx} | {obs.feet_width} + {obs.hands_vs_shins} "
                f"| visible={obs.feet_visible} -> {pred}"
            )
            print(f"        · {obs.lower_body_notes}")
        except Exception as exc:
            verdicts[f"ERREUR: {type(exc).__name__}"] += 1
            print(f"run {run} | ERREUR {type(exc).__name__}: {str(exc)[:100]}")
        time.sleep(args.delay)

    print("\n" + "  ".join(f"{k} x{v}" for k, v in verdicts.most_common()))


if __name__ == "__main__":
    main()
