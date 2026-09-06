"""Teste l'architecture candidats : la pose propose des instants, le LLM tranche la barre.

    cd backend
    uv run python eval/reps/test_candidats.py                    # les 2 clips, les 2 modeles
    uv run python eval/reps/test_candidats.py --modeles gemini-3.5-flash-lite

Le schema de production n'est pas touche : on derive une variante locale des modeles
`...Rep` en y ajoutant `bar_left_floor`. Tant que le test n'a pas conclu, `schemas.py`
reste tel quel.

Sortie : eval/reps/resultats_candidats.json, plus un resume lisible sur la sortie standard.
"""

import argparse
import json
import os
import sys
import time

from pydantic import BaseModel, Field, create_model

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)
sys.path.insert(0, ICI)

sys.path.insert(0, os.path.join(BACKEND, "eval", "scorer"))
from run_llm import charge_env                                  # noqa: E402
charge_env()                    # le .env avant d'importer ai_service, qui cree le client

from google.genai import types                                  # noqa: E402
import schemas                                                  # noqa: E402
from ai_service import client                                   # noqa: E402
from pricing import log_usage                                   # noqa: E402
from compte_reps import compte                                  # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
SIGNAUX = os.path.join(ICI, "signaux.json")
SORTIE = os.path.join(ICI, "resultats_candidats.json")

# Reglage rappel-first : le LLM ne peut qu'elaguer, mieux vaut lui proposer trop que trop peu.
BAS, HAUT = 0.40, 0.60
FPS_VIDEO = 4          # sans VideoMetadata, Gemini echantillonne a 1 image/s : trop grossier
                       # pour trancher "barre en main" a un instant precis.

CLIPS = [
    ("conventionnal_deadlift_11.mp4", "conventional deadlift", 1),   # 1 vraie rep, 2 candidats
    ("conventionnal_deadlift_2.mp4",  "conventional deadlift", 2),   # temoin : 2 vraies, 2 candidats
]


def schema_avec_barre(mouvement):
    """Le schema du mouvement, avec `bar_left_floor` ajoute a chaque repetition.

    Champ dedie et non 'NA' : 'NA' repond deja a "est-ce que je VOIS ce critere", et
    une vraie rep filmee sous un mauvais angle sortirait tous ses criteres en NA. Les
    deux questions doivent rester separees, sinon on supprime des reps reelles.
    """
    base = schemas.schema_mapping[mouvement]
    rep_base = base.model_fields["reps"].annotation.__args__[0]
    rep = create_model(
        rep_base.__name__ + "AvecBarre",
        __base__=rep_base,
        bar_left_floor=(bool, Field(description=(
            "true if the bar left the floor and was lifted to lockout on this candidate. "
            "false if the bar stayed on the floor, or was already down and the athlete "
            "simply stood back up: that is not a repetition."))),
    )
    champs = {n: (f.annotation, f) for n, f in base.model_fields.items() if n != "reps"}
    champs["reps"] = (list[rep], Field(description=base.model_fields["reps"].description))
    return create_model(base.__name__ + "AvecBarre", **champs)


def mmss(t):
    return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def prompt(mouvement, candidats):
    lignes = "\n".join(f"  candidate {k} — {mmss(t)} ({t:.1f} s)"
                       for k, t in enumerate(candidats, 1))
    return f"""
You are a brutally strict, elite IPF powerlifting judge and highly analytical biomechanics coach.
The athlete executes a {mouvement.upper()}.

GRADING RULE:
  1. Assume the default score of a rep is 1 (Poor)
  2. A Score: "1" to "3", based strictly on the provided rubrics in the schema.

REP CANDIDATES (from pose analysis):
Pose tracking found the athlete standing up at these moments, each one a POSSIBLE
repetition. Times are approximate, +/- 0.5 s:
{lignes}
Fill `reps` with ONE ENTRY PER CANDIDATE, in this order.

THE BAR RULE (this is why the candidates exist):
Pose tracking sees the body, not the bar. Standing up after LOWERING the bar to the
floor, standing up EMPTY-HANDED, or straightening up while setting up produces exactly
the same body movement as a repetition. You can see the bar; the tracker cannot.
For each candidate, set `bar_left_floor`:
  true  — the bar left the floor and was lifted to lockout. This is a real repetition.
  false — the bar stayed on the floor, or was already down and the athlete simply stood
          back up. This is NOT a repetition.
Judge each candidate on its own. A false candidate can occur anywhere — at the start
during setup, in the middle on a camera cut, or at the end of the set. Do not assume
it is the last one.
When `bar_left_floor` is false, still return the entry, and set every criterion of that
rep to "NA": the entry will be discarded.

If you see a repetition that is NOT in the candidate list, add it as an extra entry and
set `bar_left_floor` to true. Do not drop a real repetition just because pose missed it.

REP-BY-REP RULE:
Score EVERY criterion on EVERY candidate whose `bar_left_floor` is true, against the
rubric of the field of the same name in the schema. Judge each rep on its own: if the
third rep is worse than the first, its scores must be lower. Only then write the summary
blocks — they carry no score of their own, the displayed score is computed from your
per-rep scores.

CRITICAL VISIBILITY RULE (The "NA" Rule):
If the camera angle, framing, lighting or video quality makes a specific criterion
impossible to assess, output "NA" for that criterion and say in the feedback exactly
what is not visible. Do not guess.
"NA" means you could not SEE it, never that you saw it and disliked it: a flaw you can
see is a low score, not "NA".
Judge every other criterion normally; one "NA" must not drag the others down.
"NA" answers "could I SEE this criterion?". It never answers "was this a repetition?" —
that question is `bar_left_floor`, and only that field removes an entry.
"""


def envoie(fichier, modele, mouvement, candidats):
    print(f"    upload…", end="", flush=True)
    f = client.files.upload(file=os.path.join(DATA, fichier))
    while f.state.name == "PROCESSING":
        time.sleep(1)
        f = client.files.get(name=f.name)
    if f.state.name == "FAILED":
        raise RuntimeError("upload echoue")
    part = types.Part(file_data=types.FileData(file_uri=f.uri, mime_type=f.mime_type),
                      video_metadata=types.VideoMetadata(fps=FPS_VIDEO))
    print(" analyse…", end="", flush=True)
    rep = client.models.generate_content(
        model=modele,
        contents=[part, prompt(mouvement, candidats)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema_avec_barre(mouvement),
            temperature=0.0),
    )
    cout = log_usage(model=modele, response=rep, label="test_candidats", extra=fichier)
    try:
        client.files.delete(name=f.name)
    except Exception:
        pass
    return json.loads(rep.text), cout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modeles", nargs="+",
                    default=["gemini-3.5-flash-lite", "gemini-3.5-flash"])
    a = ap.parse_args()

    sig = json.load(open(SIGNAUX))
    out = json.load(open(SORTIE)) if os.path.exists(SORTIE) else {}
    for clip, mouvement, vrai in CLIPS:
        _, cand = compte(sig[clip]["points"], "ext", bas=BAS, haut=HAUT, details=True)
        print(f"\n=== {clip}   verite {vrai} rep(s)   candidats {cand}")
        for modele in a.modeles:
            print(f"  {modele}")
            try:
                res, cout = envoie(clip, modele, mouvement, cand)
            except Exception as e:
                print(f"    ECHEC {type(e).__name__}: {e}")
                continue
            reps = res.get("reps") or []
            gardees = [r for r in reps if r.get("bar_left_floor")]
            print(f"    -> {len(reps)} entrees, {len(gardees)} gardees "
                  f"(verite {vrai}) {'OK' if len(gardees) == vrai else 'ECART'}")
            for k, r in enumerate(reps, 1):
                notes = [v.get("score") for n, v in r.items() if isinstance(v, dict)]
                print(f"       cand {k}: bar_left_floor={r.get('bar_left_floor')}  "
                      f"notes {notes}")
            out.setdefault(clip, {})[modele] = {
                "candidats": cand, "verite": vrai,
                "gardees": len(gardees), "reps": reps}
            json.dump(out, open(SORTIE, "w"), indent=1, ensure_ascii=False)
    print(f"\n-> {SORTIE}")


if __name__ == "__main__":
    main()
