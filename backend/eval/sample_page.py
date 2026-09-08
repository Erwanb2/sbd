"""Regenere la demo figee de la page d'accueil (frontend/src/data/sampleResult.js).

Aucun appel a Gemini : des mesures de pose plausibles, des observations fabriquees,
et `rules.evalue` fait le reste. C'est ce qui garantit que la demo reste coherente
avec le bareme — la recopier a la main la ferait diverger au premier seuil change.

    cd backend && uv run python eval/sample_page.py > ../frontend/src/data/sample.json
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rules


# Un set de 4 reps qui se degrade franchement : de quoi montrer l'histogramme,
# les deux conseils et un persona parlant sur la page d'accueil.
mesures = [
    dict(hip_ratio=0.62, shoulder_bar_offset=0.18, rise_ratio=1.15, pitch_deg=1.5,
         drift_ratio=0.22, pull_s=1.35, hip_lockout_deg=174,
         knee_lockout_deg=176, lean_back_deg=2.0, lockout_s=0.2,
         descent_order=11.0, sticking=-1.0),
    dict(hip_ratio=0.60, shoulder_bar_offset=0.17, rise_ratio=1.42, pitch_deg=4.0,
         drift_ratio=0.31, pull_s=1.55, hip_lockout_deg=172,
         knee_lockout_deg=175, lean_back_deg=3.0, lockout_s=0.3,
         descent_order=9.0, sticking=0.62),
    dict(hip_ratio=0.58, shoulder_bar_offset=0.16, rise_ratio=2.85, pitch_deg=12.0,
         drift_ratio=0.58, pull_s=2.10, hip_lockout_deg=170,
         knee_lockout_deg=173, lean_back_deg=4.0, lockout_s=0.6,
         descent_order=-7.0, sticking=0.55),
    dict(hip_ratio=0.35, shoulder_bar_offset=0.14, rise_ratio=3.10, pitch_deg=15.0,
         drift_ratio=0.74, pull_s=2.60, hip_lockout_deg=168,
         knee_lockout_deg=171, lean_back_deg=6.0, lockout_s=0.9,
         descent_order=-12.0, sticking=0.48),
]
pose = {"variant": "conventional", "view": 0.08, "visibility": 0.83,
        "reps": [{"debut_s": 1.2 + 5 * i, "fin_s": 5.4 + 5 * i, "mesures": m}
                 for i, m in enumerate(mesures)]}

resumes = ["Textbook first pull, everything stacked.",
           "Still tight, the bar drifts a touch more.",
           "The hips beat the shoulders out of the floor.",
           "Last rep: the back rounds and the bar swings out."]
obs = []
for i, r in enumerate(resumes, 1):
    obs.append({
        "rep_index": i, "bar_over_midfoot": "over_midfoot",
        "back_at_setup": "flat", "arms_straight": "straight",
        "slack_pull": "progressive" if i <= 2 else "partial",
        "jerky_start": "smooth", "bar_left_floor": "yes",
        "past_the_knees": "clean" if i <= 2 else "loops",
        "bar_leg_contact": "in_contact" if i <= 2 else "brief_loss",
        "back_under_load": "unchanged" if i <= 2 else ("flexion_appears" if i == 3 else "collapses"),
        "hitch": "no", "asymmetry": "even", "elbow_flexion": "straight",
        "shrug": "no", "lockout_balance": "held",
        "descent_control": "controlled", "rep_transition": "reset", "summary": r,
    })
llm = {"equipment": "barbell", "grip": "mixed", "foot_orientation": "forward",
       "reps": obs}

r = rules.evalue(pose, llm)
r["modele"] = "gemini-3.5-flash"
print(json.dumps(r, ensure_ascii=False, indent=2))
