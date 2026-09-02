"""Extrait les images d'une vidéo avec la fonction du backend (extraire_images)
et les enregistre sur disque pour inspection visuelle (sumo vs conventionnel).

Usage:
    uv run python extract_frames_cli.py                      # vidéo Arthur Garrec par défaut
    uv run python extract_frames_cli.py chemin/video.mp4 -n 10
"""

import argparse
import os
import sys

DEFAULT_VIDEO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "Arthur Garrec Profil de coureur Strava.mp4",
)


def _load_extraire_images():
    """Récupère extraire_images sans exiger la clé API Gemini."""
    try:
        from ai_service import extraire_images

        return extraire_images
    except Exception:
        # ai_service instancie un client genai au chargement : on isole la fonction.
        import importlib.util
        import types

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_service.py")
        src = open(path, encoding="utf-8").read()
        start = src.index("def probe_video_duration_seconds")
        end = src.index("def _task_detect_movement")
        module = types.ModuleType("ai_service_frames")
        exec("import cv2\nfrom PIL import Image\n" + src[start:end], module.__dict__)
        return module.extraire_images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", default=DEFAULT_VIDEO)
    parser.add_argument("-n", "--num-images", type=int, default=10)
    parser.add_argument("-o", "--output-dir", default="extracted_frames")
    parser.add_argument("--no-sheet", action="store_true", help="ne pas générer la planche contact")
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")

    extraire_images = _load_extraire_images()
    images = extraire_images(args.video, num_images=args.num_images)
    if not images:
        sys.exit("Aucune image extraite (vidéo illisible ?)")

    base = os.path.splitext(os.path.basename(args.video))[0].replace(" ", "_")
    out_dir = os.path.join(args.output_dir, base)
    os.makedirs(out_dir, exist_ok=True)

    for i, img in enumerate(images, start=1):
        path = os.path.join(out_dir, f"frame_{i:02d}.png")
        img.save(path)
        print(path)

    if not args.no_sheet:
        from PIL import Image

        cols = 5
        rows = (len(images) + cols - 1) // cols
        w, h = images[0].size
        scale = 320 / w
        tw, th = int(w * scale), int(h * scale)
        sheet = Image.new("RGB", (cols * tw, rows * th), "black")
        for i, img in enumerate(images):
            sheet.paste(img.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
        sheet_path = os.path.join(out_dir, "planche_contact.png")
        sheet.save(sheet_path)
        print(f"\nPlanche contact : {sheet_path}")

    print(f"\n{len(images)} images extraites dans {out_dir}")


if __name__ == "__main__":
    main()
