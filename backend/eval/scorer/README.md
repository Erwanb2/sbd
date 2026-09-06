# Outil de notation humaine des clips de `data/`

But : produire un jeu de test fiable sur les 49 clips. Pour chaque clip et chaque critère
du schéma du mouvement on veut, sur la **même échelle 1/3 · 2/3 · 3/3 que le pipeline**
(le schéma demande directement 1, 2 ou 3 au modèle : il n'y a plus de note sur 4 ni de
compression) :

| source | fichier | état |
|---|---|---|
| note **humaine** par critère, **personas** et commentaire | `human_labels.json` | à remplir avec l'outil |
| **mon avis** (Claude) par critère + persona + confiance | `claude_review.json` | fait, 49 clips |
| note du **LLM** (pipeline Gemini) | `llm_scores.json` | 1 clip seulement, à lancer sur accord |
| mesures de **pose** (stance + cinématique) | `pose_measures.json` | fait, 49 clips |

## Noter

```bash
cd backend
uv run python eval/scorer/server.py        # http://localhost:8800
```

Une page, un clip à la fois. La vidéo à gauche, les 8 critères à droite avec trois boutons.

* `1` `2` `3` notent le critère courant et descendent au suivant, `0` met `NA`
* `↑` `↓` changent de critère, `←` `→` changent de clip, `espace` lit / met en pause
* sous les critères, le **persona** : une puce par archétype de l'enum du mouvement, plus
  `aucun / pas visible`. Le `?` déplie les définitions. **Le choix est multiple** : plusieurs
  archétypes décrivent parfois le même défaut, donc on coche l'ensemble des réponses qu'on
  accepte, et le modèle — qui n'en renvoie qu'une — est jugé sur son appartenance à cet
  ensemble plutôt que sur une égalité stricte (`persona.llm_dans_choix_humain` dans le jeu de
  test). `aucun / pas visible` est exclusif des autres. Les trois puces grisées
  (`The Meteor`, `The Bouncer`, `The Pez Dispenser`) sont dans l'enum **sans être définies
  dans le prompt** : le modèle peut les sortir sans savoir ce qu'elles désignent.
  `The Technician` n'est pas dans l'enum non plus — c'est `ai_service` qui l'attribue au-delà
  de 90 % du maximum — mais il est proposé puisqu'il sort bel et bien du pipeline.
  Le développé couché n'a pas de persona du tout (`AnalyzeBench` n'a pas le champ).
* `?` à côté d'un critère déplie la grille du barème, telle quelle : le barème du schéma
  est sur les trois mêmes niveaux que les boutons
* l'avis de Claude et la note du LLM sont **repliés par défaut** — pour ne pas orienter la
  note humaine. Les déplier ne modifie rien.

Un clip est marqué terminé (pastille verte) quand ses 8 critères **et** au moins un persona
sont renseignés. Chaque clic est enregistré dans `human_labels.json` (écriture atomique). Le dernier clip
consulté est mémorisé dans le navigateur, on peut fermer et reprendre.

## Assembler le jeu de test

```bash
uv run python eval/scorer/build_dataset.py   # -> eval/test_dataset.json
```

C'est ce fichier qui est le livrable : une ligne par clip, avec les quatre sources côte à côte.

## Regénérer les planches de frames et les mesures de pose

```bash
uv run --with opencv-python-headless,pillow,numpy python eval/scorer/prepare_frames.py
# fenêtre choisie à la main quand le repérage automatique se trompe :
uv run --with opencv-python-headless,pillow,numpy python eval/scorer/prepare_frames.py \
    --clip conventionnal_deadlift_13.mp4 --start 14.5 --end 19.5
```

Sort dans `backend/extracted_frames/scorer/` (ignoré par git) : `<clip>__vue.jpg` (12 images
sur tout le clip) et `<clip>__rep.jpg` (16 images sur la répétition).

## Passer le pipeline Gemini (coûte des appels)

```bash
uv run python eval/scorer/run_llm.py              # flash-lite, tous les clips manquants
uv run python eval/scorer/run_llm.py --model 3.5  # gemini-3.5-flash, payant
```

Non lancé pour l'instant : un seul clip (`worst_deadlift.mp4`) a servi de test de bon
fonctionnement.
