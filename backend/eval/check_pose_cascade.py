"""Rejoue la detection sumo/conventionnel sur tous les clips etiquetes de data/.

    uv run python eval/check_pose_cascade.py                 # cascade seule, ~2.5 s/clip
    uv run python eval/check_pose_cascade.py --kinematics    # + cinematique, ~4.5 s/clip

Attendu au 2026-09-05 : 46 clips corrects sur 47. Les seuils vivent dans
pose_analysis.REGLES ; ce script sert a verifier qu'un changement de version de
MediaPipe, de modele ou d'echantillonnage ne les a pas invalides.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pose_analysis

ICI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(ICI, "..", "..", "data"))
GT = os.path.join(ICI, "ground_truth.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinematics", action="store_true", help="calcule aussi la cinematique")
    ap.add_argument("--data", default=DATA)
    a = ap.parse_args()

    gt = {v["file"]: v["movement"] for v in json.load(open(GT))["videos"]}
    clips = [f for f in sorted(os.listdir(a.data))
             if f.endswith(".mp4") and "deadlift" in gt.get(f, "")]
    if not clips:
        raise SystemExit(f"aucun clip etiquete dans {a.data}")

    bons, sans_pose, sans_kin, total_t = 0, [], [], 0.0
    for f in clips:
        t0 = time.time()
        r = pose_analysis.analyse(os.path.join(a.data, f), with_kinematics=a.kinematics)
        total_t += time.time() - t0
        attendu = "sumo" if gt[f].startswith("sumo") else "conventional"
        if not r.get("ok"):
            sans_pose.append(f)
            print(f"  {f[:38]:40} PAS DE POSE ({r.get('raison')})")
            continue
        juste = r["variante"] == attendu
        bons += juste
        if a.kinematics and not r.get("kinematics"):
            sans_kin.append(f)
        print(f"  {f[:38]:40} {r['variante']:13} {'ok' if juste else 'RATE':5}"
              f" par {r['regle']:11} largeur={r['largeur']:5.2f} conf={r['confiance']:.4f}")

    print(f"\n{bons}/{len(clips)} corrects, {total_t / len(clips):.1f} s par clip")
    if sans_pose:
        print(f"sans pose : {', '.join(sans_pose)}")
    if sans_kin:
        print(f"sans cinematique : {', '.join(sans_kin)}")
    return 0 if bons >= len(clips) - 2 else 1


if __name__ == "__main__":
    sys.exit(main())
