"""Fusionne un fragment d'avis (JSON sur stdin) dans claude_review.json.

    uv run python eval/scorer/ajoute_avis.py < fragment.json

Format attendu : {"<clip>.mp4": {"summary": "...", "method": "...",
                  "criteria": {"<critere>": {"score": 1|2|3|"NA",
                                             "why": "...", "confidence": "high|medium|low"}}}}
"""

import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
CIBLE = os.path.join(ICI, "claude_review.json")

VALIDES = {1, 2, 3, "NA"}


def main():
    fragment = json.load(sys.stdin)
    try:
        with open(CIBLE, encoding="utf-8") as f:
            tout = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        tout = {}

    for clip, avis in fragment.items():
        if "persona" in avis and avis["persona"] is not None and not isinstance(avis["persona"], str):
            raise SystemExit(f"{clip} : persona doit etre une chaine ou null")
        for nom, c in (avis.get("criteria") or {}).items():
            if c.get("score") not in VALIDES:
                raise SystemExit(f"{clip}/{nom} : score invalide {c.get('score')!r}")
            if c.get("confidence") not in ("high", "medium", "low"):
                raise SystemExit(f"{clip}/{nom} : confidence manquante")
        # fusion et non remplacement : ajouter un persona ne doit pas effacer les criteres
        tout[clip] = {**tout.get(clip, {}), **avis}

    tmp = CIBLE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(tout, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CIBLE)
    print(f"{len(fragment)} clip(s) ajoutes, {len(tout)} au total -> {CIBLE}")


if __name__ == "__main__":
    main()
