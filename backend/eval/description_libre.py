"""Description libre d'un clip par le modele, SANS schema : texte, pas de cases.

    cd backend
    uv run --env-file .env python eval/description_libre.py [--clip pr_160.mp4] [--modele 3.5]
                                                          [--prompt court] [--suffixe description_libre]

Le contraire exact de la prod : aucun `response_schema`, aucune liste d'options, aucun
nom de champ. On demande une description biomecanique aussi detaillee que possible et on
lit ce que le modele dit quand rien ne l'amorce. Reglages au plafond : raisonnement HIGH,
resolution HIGH, 24 im/s (30 est refuse par l'API). Le thinking est conserve aussi.

Sortie : eval/runs/<clip>_description_libre.json (prompt, pensees, texte, usage).
"""

import argparse
import json
import os
import sys

from google.genai import types

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(ICI)
sys.path.insert(0, BACKEND)

import ai_service                                   # noqa: E402
from pricing import log_usage                       # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))

PROMPTS = {}
PROMPTS["long"] = """You are an elite powerlifting coach and a biomechanics researcher. Watch this deadlift video.

Describe, in as much biomechanical detail as you possibly can, everything you observe about the
lifter, the bar, and how they move through time. Give timestamps. Go phase by phase (setup,
the instant the plates leave the floor, the pull to the knees, knees to lockout, the lockout
itself, the descent, and what happens after the bar is down), and for each phase describe the
geometry: joint angles and how they change, segment orientations relative to the floor, the
position of the bar relative to the feet, shins, knees and hips, the shape of the lumbar and
thoracic spine, the head and neck, the arms, the hands, the feet, and any asymmetry between
the two sides. Describe velocities and their changes. Describe what you can and cannot see
given the camera angle, the framing, the clothing and the equipment, and say explicitly which
observations are limited by that.

Write freely, in prose, as long as you need. Do not summarise, do not skip anything, do not
give a score. Describe first; if you want to add a coach's interpretation, do it in a
separate final section clearly labelled as interpretation."""

# La meme demande sans la liste de phases ni la liste de choses a regarder : ce que le
# modele choisit de decrire quand on ne lui dicte meme pas le plan.
PROMPTS["court"] = """You are a powerlifting specialist and a biomechanics researcher. Watch this deadlift video.

Describe, in as much biomechanical detail as you possibly can, everything you observe about the
lifter, the bar, and how they move through time."""

# Deux prompts critiques, aussi courts que "court". "severe" demande la severite ;
# "porte_fermee" ne la demande pas mais pose qu'il y a un defaut a trouver — la forme qui,
# sur le catalogue, a fait bouger le modele la ou la severite seule s'arretait avant le cout.
# Sans horodatage demande : entre les passes A et B ils divergeaient d'une seconde.
PROMPTS["severe"] = """You are a powerlifting judge known for being extremely critical. Watch this deadlift video.

Find every technical fault in this lift, however small, and describe each one in as much
biomechanical detail as you can."""

PROMPTS["porte_fermee"] = """You are a powerlifting specialist and a biomechanics researcher. Watch this deadlift video.

Assume this lift was filmed because a coach saw something wrong with it. Describe, in as
much biomechanical detail as you can, what that coach saw."""

# La porte fermee, avec une sortie explicite mais couteuse : dire qu'il n'y a rien oblige a
# raconter ce qu'on a verifie. Le test : la prend-il sur tibo (propre) et pas sur pr_160 ?
PROMPTS["porte_couteuse"] = """You are a powerlifting specialist and a biomechanics researcher. Watch this deadlift video.

Assume this lift was filmed because a coach saw something wrong with it. Describe, in as
much biomechanical detail as you can, what that coach saw. If, after looking carefully, you
find no real fault, say "No fault found" and explain what you checked and what you saw."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", default="pr_160.mp4")
    ap.add_argument("--modele", default="3.5")
    ap.add_argument("--prompt", choices=sorted(PROMPTS), default="long")
    ap.add_argument("--suffixe", default="description_libre")
    args = ap.parse_args()
    prompt = PROMPTS[args.prompt]

    modele = ai_service.MODELES_ANALYSE[args.modele]
    video_file = ai_service._task_upload(os.path.join(DATA, args.clip))
    try:
        reponse = ai_service.client.models.generate_content(
            model=modele,
            contents=[
                types.Part(file_data=types.FileData(file_uri=video_file.uri,
                                                    mime_type=video_file.mime_type),
                           video_metadata=types.VideoMetadata(fps=ai_service.FPS_MAX)),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH,
                                                     include_thoughts=True)),
        )
    finally:
        try:
            ai_service.client.files.delete(name=video_file.name)
        except Exception:
            pass

    usage = log_usage(model=modele, response=reponse, label="description libre")
    res = {
        "clip": args.clip, "modele": modele,
        "reglages": {"media_resolution": "HIGH", "thinking_level": "HIGH",
                     "temperature": 0.0, "fps": ai_service.FPS_MAX, "response_schema": None},
        "prompt": prompt,
        "pensees": ai_service._pensees(reponse),
        "texte": reponse.text,
        "usage": ai_service._usage_public(usage),
    }
    nom = os.path.splitext(args.clip)[0]
    sortie = os.path.join(ICI, "runs", f"{nom}_{args.suffixe}.json")
    with open(sortie, "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print(f"{sortie} : usage {res['usage']}", file=sys.stderr)
    print(res["texte"])


if __name__ == "__main__":
    main()
