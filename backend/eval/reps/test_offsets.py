"""Variante du test candidats : un Part video PAR candidat, borne par start/end_offset.

    cd backend
    uv run python eval/reps/test_offsets.py [--runs 2] [--modele gemini-3.5-flash]

Difference avec test_candidats.py : au lieu d'envoyer la video entiere et de citer des
instants dans le texte, on envoie un segment video par candidat. Le modele n'a plus a
deviner quelle portion de la video appartient a quelle repetition — la segmentation est
donnee par la structure de la requete, pas decrite en prose.

La fenetre d'un candidat va du creux qui precede sa montee au creux qui suit sa descente :
c'est la repetition entiere, phase excentrique comprise, ce qui manquait pour juger
`eccentric_control_and_descent`.
"""

import argparse
import json
import os
import sys
import time

import numpy as np
from pydantic import Field, create_model

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(BACKEND, "eval", "scorer"))

from run_llm import charge_env                                  # noqa: E402
charge_env()

from google.genai import types                                  # noqa: E402
import schemas                                                  # noqa: E402
from ai_service import client                                   # noqa: E402
from pricing import log_usage                                   # noqa: E402
from compte_reps import compte, serie, _lisse, _cadence, BAS    # noqa: E402
from test_candidats import schema_avec_barre                    # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
SIGNAUX = os.path.join(ICI, "signaux.json")
SORTIE = os.path.join(ICI, "resultats_offsets.json")

CLIP = "conventionnal_deadlift_11.mp4"
MOUVEMENT = "conventional deadlift"
VRAI = 1
BAS_R, HAUT_R = 0.40, 0.60      # meme reglage rappel-first que test_candidats
FPS_VIDEO = 4
MARGE = 0.6                     # s de part et d'autre : un verrouillage ne commence pas net


def fenetres(points, candidats):
    """(debut, fin) par candidat : du creux avant la montee au creux apres la descente."""
    ts, vs = serie(points, "ext")
    ts = np.array(ts)
    vs = _lisse(np.array(vs), _cadence(ts))
    lo, hi = np.percentile(vs, 5), np.percentile(vs, 95)
    norm = (vs - lo) / max(hi - lo, 1e-6)
    duree = float(ts[-1])
    out = []
    for t in candidats:
        i = int(np.argmin(np.abs(ts - t)))
        avant = [k for k in range(i, -1, -1) if norm[k] < BAS_R]
        apres = [k for k in range(i, len(ts)) if norm[k] < BAS_R]
        d = float(ts[avant[0]]) if avant else 0.0
        f = float(ts[apres[0]]) if apres else duree
        out.append((max(0.0, d - MARGE), min(duree, f + MARGE)))
    return out


def prompt(candidats, fen):
    lignes = "\n".join(
        f"  segment {k} — video part {k}, covering {d:.1f}s to {f:.1f}s of the original clip "
        f"(the athlete stands up at about {t:.1f}s)"
        for k, (t, (d, f)) in enumerate(zip(candidats, fen), 1))
    return f"""
You are a brutally strict, elite IPF powerlifting judge and highly analytical biomechanics coach.
The athlete executes a {MOUVEMENT.upper()}.

WHAT YOU ARE GIVEN:
You receive {len(candidats)} video segments, one per POSSIBLE repetition, in chronological
order. Each segment was cut by pose tracking around a moment where the athlete stood up,
and it covers that whole attempt: the pull, the lockout, and the phase that follows it.
{lignes}
Fill `reps` with ONE ENTRY PER SEGMENT, in this order. Judge each segment using ONLY what
that segment shows.

GRADING RULE:
  1. Assume the default score of a rep is 1 (Poor)
  2. A Score: "1" to "3", based strictly on the provided rubrics in the schema.

THE BAR RULE (this is why the segments exist):
Pose tracking sees the body, not the bar. Standing up after LOWERING the bar to the
floor, standing up EMPTY-HANDED, or straightening up while setting up produces exactly
the same body movement as a repetition. You can see the bar; the tracker cannot.
For each segment, set `bar_left_floor`:
  true  — the bar left the floor and was lifted to lockout. This is a real repetition.
  false — the bar stayed on the floor, or was already down and the athlete simply stood
          back up. This is NOT a repetition.
Judge each segment on its own. A false segment can occur anywhere — at the start during
setup, in the middle on a camera cut, or at the end of the set. Do not assume it is the
last one.
When `bar_left_floor` is false, still return the entry, and set every criterion of that
rep to "NA": the entry will be discarded.

REP-BY-REP RULE:
Score EVERY criterion on EVERY segment whose `bar_left_floor` is true, against the rubric
of the field of the same name in the schema. `eccentric_control_and_descent` is judged on
the lowering phase shown at the END of that same segment. Only then write the summary
blocks — they carry no score of their own, the displayed score is computed from your
per-rep scores.

CRITICAL VISIBILITY RULE (The "NA" Rule):
If the camera angle, framing, lighting or video quality makes a specific criterion
impossible to assess, output "NA" for that criterion and say in the feedback exactly
what is not visible. Do not guess.
"NA" means you could not SEE it, never that you saw it and disliked it: a flaw you can
see is a low score, not "NA".
"NA" answers "could I SEE this criterion?". It never answers "was this a repetition?" —
that question is `bar_left_floor`, and only that field removes an entry.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--modele", default="gemini-3.5-flash")
    a = ap.parse_args()

    sig = json.load(open(SIGNAUX))[CLIP]
    _, cand = compte(sig["points"], "ext", bas=BAS_R, haut=HAUT_R, details=True)
    fen = fenetres(sig["points"], cand)
    print(f"{CLIP}  verite {VRAI} rep")
    for k, (t, (d, f)) in enumerate(zip(cand, fen), 1):
        print(f"  candidat {k} : verrouillage {t:.2f}s -> segment {d:.1f}s a {f:.1f}s "
              f"({f-d:.1f}s)")

    print("\nupload…", end="", flush=True)
    vf = client.files.upload(file=os.path.join(DATA, CLIP))
    while vf.state.name == "PROCESSING":
        time.sleep(1)
        vf = client.files.get(name=vf.name)
    if vf.state.name == "FAILED":
        raise RuntimeError("upload echoue")
    print(" ok")

    parts = [types.Part(
        file_data=types.FileData(file_uri=vf.uri, mime_type=vf.mime_type),
        video_metadata=types.VideoMetadata(start_offset=f"{d:.2f}s", end_offset=f"{f:.2f}s",
                                           fps=FPS_VIDEO))
        for d, f in fen]

    out = json.load(open(SORTIE)) if os.path.exists(SORTIE) else {}
    for run in range(1, a.runs + 1):
        print(f"\n--- run {run}/{a.runs}  ({a.modele})")
        try:
            rep = client.models.generate_content(
                model=a.modele,
                contents=parts + [prompt(cand, fen)],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema_avec_barre(MOUVEMENT),
                    temperature=0.0),
            )
        except Exception as e:
            print(f"  ECHEC {type(e).__name__}: {e}")
            break
        log_usage(model=a.modele, response=rep, label="test_offsets", extra=CLIP)
        res = json.loads(rep.text)
        reps = res.get("reps") or []
        gardees = [r for r in reps if r.get("bar_left_floor")]
        print(f"  {len(reps)} entrees, {len(gardees)} gardees (verite {VRAI}) "
              f"{'OK' if len(gardees) == VRAI else 'ECART'}")
        for k, r in enumerate(reps, 1):
            notes = {n: v.get("score") for n, v in r.items() if isinstance(v, dict)}
            print(f"    seg {k}: bar_left_floor={r.get('bar_left_floor')}")
            print(f"           {notes}")
        out.setdefault(a.modele, {})[f"run{run}"] = {
            "candidats": cand, "fenetres": fen, "verite": VRAI,
            "gardees": len(gardees), "reps": reps}
        json.dump(out, open(SORTIE, "w"), indent=1, ensure_ascii=False)

    try:
        client.files.delete(name=vf.name)
    except Exception:
        pass
    print(f"\n-> {SORTIE}")


if __name__ == "__main__":
    main()
