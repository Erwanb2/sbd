"""Mesure la stabilité de la détection sumo/conventionnel.

Rejoue l'appel EXACT de prod (_task_detect_movement) N fois, puis des variantes
qui isolent un seul paramètre, et affiche le décompte des verdicts.

Usage:
    uv run python flakiness_cli.py                                   # vidéo Arthur, 5 runs
    uv run python flakiness_cli.py ../data/oscar_sumo.mp4 -r 10
    uv run python flakiness_cli.py --variants prod,select3,select10 -r 3
"""

import argparse
import collections
import os
import sys
import time

from pydantic import BaseModel, Field

from classify_frames_cli import _load_env
from extract_frames_cli import DEFAULT_VIDEO, _load_extraire_images

# Prompt copié verbatim de ai_service._task_detect_movement.
PROMPT_PROD = """
    Based on these images, classify the exercise into one of the following categories:
        - squat
        - bench press
        - sumo deadlift
        - conventional deadlift
        - unworkable_video (if none of the above or unclear)
    Deadlift classification rules:
        Classify as sumo deadlift if at least one condition is met:
            - Feet are wide apart
            - Arms are inside the knees
        Otherwise, classify as conventional deadlift.
    """

# Même chose, mais les deux critères doivent être réunis (le OU actuel suffit à
# basculer en sumo dès qu'une prise étroite met les bras entre les genoux).
PROMPT_AND = PROMPT_PROD.replace(
    "if at least one condition is met", "only if BOTH conditions are met"
)

# Critère unique et non ambigu : c'est la largeur des pieds qui définit le sumo.
PROMPT_FEET_ONLY = """
    Based on these images, classify the exercise into one of the following categories:
        - squat
        - bench press
        - sumo deadlift
        - conventional deadlift
        - unworkable_video (if none of the above or unclear)
    Deadlift classification rules:
        Look at the FEET, not at the hands. In a conventional deadlift the feet are
        about hip-width apart and the hands grip OUTSIDE the legs. In a sumo deadlift
        the feet are much wider than the shoulders, toes flared out, and the hands
        grip INSIDE the legs. A narrow grip with the arms hanging between the knees
        is normal in a conventional deadlift and is NOT evidence of sumo.
    """

# --- Passe 1 du pipeline en deux temps : choisir les frames utiles -----------

PROMPT_SELECT = """
    These are numbered frames from a single powerlifting video, in chronological order.

    Select the {k} frames that BEST show the lifter in the SETUP / START position of
    the lift: barbell still on or near the floor, hips down, hands already gripping the
    bar, and the lower body clearly visible.

    These are the only frames where foot stance and hand placement can be judged.
    Ignore frames showing the lockout, the walk-in, the floor without a lifter, or
    anything where the feet are hidden.

    Return exactly {k} frame numbers (1-based), as integers.
    """


class FrameSelection(BaseModel):
    """Schéma de la passe 1 : les indices des frames retenues."""

    frame_indices: list[int] = Field(description="1-based frame numbers, most useful first")


def _select_frames(client, types, images, k, model):
    """Passe 1 : demande au modèle quelles frames montrent la position de départ.

    Retourne (frames, indices). Repli sur un échantillonnage uniforme si la
    sélection échoue ou revient vide, pour ne jamais casser la passe 2.
    """
    numbered = []
    for i, img in enumerate(images, start=1):
        numbered.extend([f"Frame {i}:", img])

    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FrameSelection,
            temperature=0.0,
        ),
    )
    response = _with_retry(
        lambda: chat.send_message(message=[*numbered, PROMPT_SELECT.format(k=k)])
    )

    raw = response.parsed.frame_indices if response.parsed else []
    # Le modèle peut renvoyer des indices hors bornes, dupliqués, ou en trop.
    seen, kept = set(), []
    for idx in raw:
        if 1 <= idx <= len(images) and idx not in seen:
            seen.add(idx)
            kept.append(idx)
        if len(kept) == k:
            break

    if not kept:
        step = max(1, len(images) // k)
        kept = [i for i in range(1, len(images) + 1, step)][:k]

    return [images[i - 1] for i in sorted(kept)], sorted(kept)


def _with_retry(fn, attempts=6):
    """Rejoue un appel selon le type d'erreur.

    Deux causes distinctes, deux stratégies :
      - 503 / UNAVAILABLE / overloaded ("high demand") : surcharge côté serveur,
        transitoire. On réessaie vite (5s, 10s, 20s) — ça ne consomme pas de quota.
      - 429 RESOURCE_EXHAUSTED : rate limit. Réessayer vite ne ferait que
        rallonger la fenêtre de blocage, on attend 60s pleines.
    Toute autre erreur remonte immédiatement.
    """
    surcharge = 0
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:
            msg = str(exc)
            dernier = attempt == attempts - 1
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                if dernier:
                    raise
                attente = 60.0
            elif "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                if dernier:
                    raise
                attente = min(5.0 * (2 ** surcharge), 20.0)
                surcharge += 1
            else:
                raise
            print(
                f"    {msg[:40]}... attente {attente:.0f}s "
                f"(tentative {attempt + 2}/{attempts})",
                file=sys.stderr, flush=True,
            )
            time.sleep(attente)


def run_once(client, types, schema, images, prompt, model, numbered):
    """Un appel. numbered=True intercale 'Frame N:' avant chaque image."""
    if numbered:
        content = []
        for i, img in enumerate(images, start=1):
            content.extend([f"Frame {i}:", img])
    else:
        content = list(images)

    config = types.GenerateContentConfig(temperature=0.0)
    if schema is not None:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.0,
        )

    chat = client.chats.create(model=model, config=config)
    response = _with_retry(lambda: chat.send_message(message=[*content, prompt]))
    if schema is not None:
        return response.parsed.mouvement_detecte
    text = (response.text or "").lower()
    if "sumo" in text:
        return "sumo deadlift"
    if "conventional" in text or "conventionnel" in text:
        return "conventional deadlift"
    return text.strip()[:60] or "(vide)"


# nom -> (prompt, avec_schema, frames_numerotees, select_k, n_uniform)
# select_k=K   : passe 1 de sélection sur le pool, puis passe 2 sur les K retenues.
# n_uniform=N  : N frames uniformément réparties, SANS sélection. Sert de témoin
#                aux variantes select* : à nombre de frames égal, il isole ce qui
#                vient de la sélection de ce qui vient seulement du nombre.
VARIANTS = {
    "prod": (PROMPT_PROD, True, False, None, None),
    "numbered": (PROMPT_PROD, True, True, None, None),
    "no_schema": (PROMPT_PROD, False, False, None, None),
    "rule_and": (PROMPT_AND, True, False, None, None),
    "rule_feet": (PROMPT_FEET_ONLY, True, False, None, None),
    "select3": (PROMPT_PROD, True, False, 3, None),
    "select10": (PROMPT_PROD, True, False, 10, None),
    "naive3": (PROMPT_PROD, True, False, None, 3),
    "naive10": (PROMPT_PROD, True, False, None, 10),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", default=DEFAULT_VIDEO)
    parser.add_argument("-r", "--runs", type=int, default=5)
    parser.add_argument("-n", "--num-images", type=int, default=10)
    parser.add_argument(
        "-p", "--pool", type=int, default=50,
        help="taille du pool de frames soumis à la passe 1 (variantes select*)",
    )
    parser.add_argument(
        "--delay", type=float, default=4.0, help="pause entre appels, contre les 429"
    )
    parser.add_argument("-m", "--model", default=os.getenv("MODEL_GEMINI_CLASSIFICATION", "gemini-3.5-flash-lite"))
    parser.add_argument("--variants", default="prod,numbered,no_schema,rule_and,rule_feet")
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"Vidéo introuvable : {args.video}")

    _load_env()
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY manquante (backend/.env)")

    extraire = _load_extraire_images()
    images = extraire(args.video, num_images=args.num_images)
    if not images:
        sys.exit("Aucune image extraite (vidéo illisible ?)")

    names = [v.strip() for v in args.variants.split(",") if v.strip()]
    needs_pool = any(VARIANTS.get(n, (None,) * 5)[3] for n in names)
    pool = extraire(args.video, num_images=args.pool) if needs_pool else []

    from google import genai
    from google.genai import types

    from schemas import VideoClassification

    client = genai.Client()

    print(f"Vidéo   : {os.path.basename(args.video)}")
    print(f"Modèle  : {args.model} | {len(images)} frames | {args.runs} runs/variante")
    if needs_pool:
        print(f"Pool    : {len(pool)} frames pour la passe de sélection")
    print()

    for name in names:
        if name not in VARIANTS:
            sys.exit(f"Variante inconnue : {name} (dispo : {', '.join(VARIANTS)})")
        prompt, use_schema, numbered, select_k, n_uniform = VARIANTS[name]
        schema = VideoClassification if use_schema else None
        # Les variantes naive* rejouent l'extraction uniforme avec un autre N.
        base_frames = extraire(args.video, num_images=n_uniform) if n_uniform else images

        counts = collections.Counter()
        picks = []
        for _ in range(args.runs):
            try:
                if select_k:
                    frames, idx = _select_frames(client, types, pool, select_k, args.model)
                    picks.append(idx)
                else:
                    frames = base_frames
                counts[run_once(client, types, schema, frames, prompt, args.model, numbered)] += 1
            except Exception as exc:
                counts[f"ERREUR: {type(exc).__name__}: {str(exc)[:120]}"] += 1
            time.sleep(args.delay)

        detail = "  ".join(f"{k} x{v}" for k, v in counts.most_common())
        stable = "STABLE" if len(counts) == 1 else "INSTABLE"
        print(f"[{stable:8}] {name:10} -> {detail}")
        for idx in picks:
            print(f"{'':11}   frames retenues : {idx}")


if __name__ == "__main__":
    main()
