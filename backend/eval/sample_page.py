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

# L'histoire que la demo raconte est CAUSALE, et c'est tout l'interet : le placement
# tient d'un bout a l'autre, mais a partir de la rep 3 les hanches decollent avant les
# epaules — et c'est ce seul defaut qui tire la barre en avant puis enroule le dos.
# L'epingle doit donc tomber sur `leg_drive`, avec la trajectoire de barre rattachee
# dessous, et le bandeau structure passer au rouge sur la derniere rep.
resumes = ["Textbook first pull, everything stacked.",
           "Still tight, the bar drifts a touch more.",
           "The hips beat the shoulders out of the floor.",
           "Last rep: the back rounds and the bar swings out."]
obs = []
for i, r in enumerate(resumes, 1):
    obs.append({
        "rep_index": i, "bar_over_midfoot_topology": "bar_over_laces",
        "hip_height_via_femur": "femur_angled_upward",
        "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
        "lumbar_at_setup": "lumbar_neutral_or_concave",
        "thoracic_at_setup": "thoracic_neutral_or_concave",
        "arms_tension_at_setup": "elbow_locked_prior",
        "bar_left_floor": "yes",
        "initiation_sequence": "torso_angle_constant" if i <= 2 else "torso_angle_decreases",
        "bar_path_at_knees_topology": "bar_slides_past_knees" if i <= 2 else "bar_deviates_forward",
        "bar_leg_daylight": "zero_daylight" if i <= 2 else "daylight_beyond_shoe",
        # Le dos se decrit en deux segments depuis le 2026-09-10. C'est le LOMBAIRE
        # qui cede a mesure que les hanches decollent.
        "lumbar_geometry_delta": "lumbar_geometry_constant" if i <= 3 else "lumbar_becomes_convex",
        "knee_valgus_tracking": "not_visible",
        "vertical_velocity_hitch": "continuous_positive_velocity",
        "shoulder_elevation_delta": "distance_remains_constant",
        "sagittal_torso_angle": "torso_perpendicular",
        "lockout_extension": "full_180_extension",
        "descent_hand_contact": "hands_maintain_contact",
        "rep_transition_velocity": "not_visible" if i == len(resumes) else "zero_velocity_maintained",
        "summary": r,
        # Le schema demande une observation libre AVANT chaque etat. La demo en
        # fabrique pour les seuls champs qui portent son histoire : le reste
        # resterait du texte mort sur une page qu'on veut courte.
        "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
        "thoracic_at_setup_observed": "The upper back is flat and set before the bar moves.",
        "lumbar_geometry_delta_observed": ("The lower back holds its shape from the floor to the knees."
                                           if i <= 3 else
                                           "The lower back rounds further as the bar passes the knees."),
        "initiation_sequence_observed": ("The torso angle is the same when the plates leave the floor."
                                         if i <= 2 else
                                         "The hips rise before the plates leave the floor; the torso tilts toward horizontal."),
    })
llm = {"equipment": "barbell", "grip": "mixed", "foot_orientation": "forward",
       "reps": obs}

r = rules.evalue(pose, llm)
r["modele"] = "gemini-3.5-flash"
print(json.dumps(r, ensure_ascii=False, indent=2))
