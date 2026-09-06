"""Assemble le jeu de test a partir des quatre sources et ecrit eval/test_dataset.json.

    cd backend
    uv run python eval/scorer/build_dataset.py

Pour chaque clip : la note humaine par critere et son commentaire (human_labels.json),
mon avis par critere avec sa confiance (claude_review.json), la note du LLM si un
passage du pipeline a eu lieu (llm_scores.json), et les mesures de pose du clip
(pose_measures.json). Le fichier produit est la seule chose a versionner.
"""

import json
import os
import sys
from datetime import datetime

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)
sys.path.insert(0, ICI)

import server  # noqa: E402  (catalogue + criteres du schema)

SORTIE = os.path.join(BACKEND, "eval", "test_dataset.json")


def main():
    cat = server.catalogue()
    mesures = server.charge(os.path.join(ICI, "pose_measures.json"), {})

    clips, notes_humaines = [], 0
    for v in cat["videos"]:
        humain = v.get("human") or {}
        scores_h = humain.get("scores") or {}
        if scores_h:
            notes_humaines += 1
        claude = v.get("claude") or {}
        llm = v.get("llm") or {}
        criteres = {}
        for c in v["criteria"]:
            n = c["name"]
            criteres[n] = {
                "human": scores_h.get(n),
                "claude": (claude.get("criteria") or {}).get(n, {}).get("score"),
                "claude_why": (claude.get("criteria") or {}).get(n, {}).get("why"),
                "claude_confidence": (claude.get("criteria") or {}).get(n, {}).get("confidence"),
                "llm": (llm.get("criteria") or {}).get(n, {}).get("score"),
                "llm_feedback": (llm.get("criteria") or {}).get(n, {}).get("feedback"),
            }
        clips.append({
            "file": v["file"],
            "movement": v["movement"],
            "criteria": criteres,
            "persona": {
                # liste : l'humain peut accepter plusieurs archetypes pour un meme defaut
                "human": server.liste_persona(humain.get("persona")),
                "claude": claude.get("persona"),
                "claude_why": claude.get("persona_why"),
                "llm": llm.get("persona"),
                "llm_justification": llm.get("persona_justification"),
                # le modele ne renvoie qu'un persona : on le juge sur son appartenance
                # a l'ensemble accepte par l'humain, pas sur une egalite stricte
                "llm_dans_choix_humain": (
                    llm.get("persona") in server.liste_persona(humain.get("persona"))
                    if llm.get("persona") and humain.get("persona") else None
                ),
            },
            "human_comment": humain.get("comment") or "",
            "human_updated_at": humain.get("updated_at"),
            "claude_summary": claude.get("summary"),
            "claude_method": claude.get("method"),
            "llm_model": llm.get("model"),
            # Mouvement rendu par la detection, distinct de "movement" qui est
            # l'etiquette humaine : les assertions de classification comparent les deux.
            "llm_movement": llm.get("movement"),
            "pose": {k: val for k, val in (mesures.get(v["file"]) or {}).items()
                     if k != "kinematics"},
            "kinematics": (mesures.get(v["file"]) or {}).get("kinematics"),
        })

    dataset = {
        "_about": {
            "built_at": datetime.now().isoformat(timespec="seconds"),
            "scale": "1 = 1/3, 2 = 2/3, 3 = 3/3, 'NA' = non evaluable a l'image. "
                     "Meme echelle que la sortie du pipeline apres compression "
                     "(ai_service.analyze_movement : 1-2 -> 1, 3 -> 2, 4 -> 3).",
            "sources": {
                "human": "eval/scorer/human_labels.json — clics dans l'outil de notation",
                "claude": "eval/scorer/claude_review.json — revue par planches de frames",
                "llm": "eval/scorer/llm_scores.json — passage du pipeline (run_llm.py)",
                "pose": "eval/scorer/pose_measures.json — pose_analysis.analyse()",
            },
            "clips": len(clips),
            "clips_notes_par_humain": notes_humaines,
        },
        "clips": clips,
    }
    tmp = SORTIE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    os.replace(tmp, SORTIE)
    print(f"{len(clips)} clips, dont {notes_humaines} notes par l'humain -> {SORTIE}")


if __name__ == "__main__":
    main()
