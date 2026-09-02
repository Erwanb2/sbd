"""Envoie les 10 frames extraites à Gemini et demande une justification
détaillée sumo vs conventionnel (texte libre, pas de schéma contraint).

Usage:
    uv run python classify_frames_cli.py
    uv run python classify_frames_cli.py ../data/oscar_sumo.mp4 -m gemini-3.5-flash-lite
"""

import argparse
import os
import sys

from extract_frames_cli import DEFAULT_VIDEO, _load_extraire_images

PROMPT = """These 10 images are evenly spaced frames from a single powerlifting video.

Decide whether the lift is a SUMO deadlift or a CONVENTIONAL deadlift.

Reference rules used by our system:
  - Sumo if feet are wide apart, OR arms are inside the knees.
  - Otherwise conventional.

Answer in French, structured like this:
1. Frame par frame: pour chaque image utile (numérotée 1 à 10), décris ce que tu
   vois du stance (largeur des pieds par rapport aux épaules, position des mains
   par rapport aux genoux, angle des tibias, orientation des pieds).
2. Indices pour SUMO / indices pour CONVENTIONNEL: liste les deux côtés.
3. Verdict: SUMO ou CONVENTIONNEL, avec un niveau de confiance en %.
4. Ce qui pourrait te tromper: angle de caméra, cadrage, occlusions.

Sois factuel: si une image ne montre pas le bas du corps, dis-le au lieu d'inventer.
"""


def _load_env():
    """Charge .env pour GEMINI_API_KEY (le backend le fait via docker/uvicorn)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", default=DEFAULT_VIDEO)
    parser.add_argument("-n", "--num-images", type=int, default=10)
    # gemini-2.5-flash-lite est retiré côté Google (404 pour les nouveaux clients).
    parser.add_argument(
        "-m", "--model", default=os.getenv("MODEL_GEMINI_CLASSIFICATION", "gemini-3.5-flash-lite")
    )
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
    numbered = []
    for i, img in enumerate(images, start=1):
        numbered.extend([f"Frame {i}:", img])

    response = client.models.generate_content(
        model=args.model,
        contents=[*numbered, PROMPT],
        config=types.GenerateContentConfig(temperature=0.0),
    )

    print(f"=== {args.model} — {len(images)} frames — {os.path.basename(args.video)} ===\n")
    print(response.text)

    usage = getattr(response, "usage_metadata", None)
    if usage:
        print(
            f"\n[tokens] in={usage.prompt_token_count} "
            f"out={usage.candidates_token_count} total={usage.total_token_count}"
        )


if __name__ == "__main__":
    main()
