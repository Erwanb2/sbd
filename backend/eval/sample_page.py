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
    dict(hanches_ratio=0.62, epaules_barre=0.18, ratio_montee=1.15, bascule_deg=1.5,
         derive_ratio=0.22, duree_tiree_s=1.35, hanche_lockout_deg=174,
         genou_lockout_deg=176, bascule_arriere_deg=2.0, duree_lockout_s=0.2,
         descente_ordre=11.0, stagnation=-1.0),
    dict(hanches_ratio=0.60, epaules_barre=0.17, ratio_montee=1.42, bascule_deg=4.0,
         derive_ratio=0.31, duree_tiree_s=1.55, hanche_lockout_deg=172,
         genou_lockout_deg=175, bascule_arriere_deg=3.0, duree_lockout_s=0.3,
         descente_ordre=9.0, stagnation=0.62),
    dict(hanches_ratio=0.58, epaules_barre=0.16, ratio_montee=2.85, bascule_deg=12.0,
         derive_ratio=0.58, duree_tiree_s=2.10, hanche_lockout_deg=170,
         genou_lockout_deg=173, bascule_arriere_deg=4.0, duree_lockout_s=0.6,
         descente_ordre=-7.0, stagnation=0.55),
    dict(hanches_ratio=0.35, epaules_barre=0.14, ratio_montee=3.10, bascule_deg=15.0,
         derive_ratio=0.74, duree_tiree_s=2.60, hanche_lockout_deg=168,
         genou_lockout_deg=171, bascule_arriere_deg=6.0, duree_lockout_s=0.9,
         descente_ordre=-12.0, stagnation=0.48),
]
pose = {"variante": "conventional", "vue": 0.08, "visibilite": 0.83,
        "reps": [{"debut_s": 1.2 + 5 * i, "fin_s": 5.4 + 5 * i, "mesures": m}
                 for i, m in enumerate(mesures)]}

resumes = ["Textbook first pull, everything stacked.",
           "Still tight, the bar drifts a touch more.",
           "The hips beat the shoulders out of the floor.",
           "Last rep: the back rounds and the bar swings out."]
obs = []
for i, r in enumerate(resumes, 1):
    obs.append({
        "rep_index": i, "barre_milieu_pied": "milieu_pied",
        "dos_au_setup": "neutre", "bras_tendus": "tendus",
        "mise_en_tension": "progressive" if i <= 2 else "partielle",
        "a_coup_depart": "progressif", "bar_left_floor": "oui",
        "passage_genoux": "direct" if i <= 2 else "boucle",
        "contact_barre_jambes": "contact" if i <= 2 else "perte_breve",
        "dos_sous_charge": "inchange" if i <= 2 else ("flexion_apparait" if i == 3 else "effondrement"),
        "hitch": "non", "asymetrie": "symetrique", "flexion_coude_tiree": "tendus",
        "haussement_epaules": "non", "equilibre_lockout": "stable",
        "controle_descente": "accompagnee", "enchainement": "reset", "resume": r,
    })
llm = {"materiel": "barre_libre", "prise": "mixte", "orientation_pieds": "droits",
       "reps": obs}

r = rules.evalue(pose, llm)
r["modele"] = "gemini-3.5-flash"
print(json.dumps(r, ensure_ascii=False, indent=2))
