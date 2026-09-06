---
name: comptage-reps
description: Compter les répétitions d'un deadlift — pourquoi MediaPipe seul n'y arrive pas (58% d'exactitude, mesuré sur 47 clips), et l'architecture retenue en production où la pose propose des instants candidats et Gemini tranche si la barre a décollé. À charger avant de toucher au comptage de reps, au champ `bar_left_floor`, au mode segments d'`ai_service`, à `rep_detection.py`, ou avant de proposer un détecteur de barre.
---

# Compter les répétitions

## L'état des lieux en une phrase

**La pose voit le corps, pas la barre.** Se redresser après avoir reposé la barre produit
exactement le même mouvement qu'une répétition. C'est toute la difficulté, et aucun réglage
de seuils ne la contourne.

## Ce qui est en production (depuis le 2026-09-06)

La pose **propose**, le modèle **tranche**.

1. `backend/rep_detection.py` — passe de pose dense (6 im/s), **séparée** de la cascade
   sumo/conventionnel. Rend `[{lockout_s, debut_s, fin_s}]` : la fenêtre d'un candidat va du
   creux avant la montée au creux après la descente, plus 0,6 s de marge.
2. `ai_service.analyze_movement` — mode segments : **un `Part` vidéo par candidat** avec
   `start_offset`/`end_offset`, `media_resolution=HIGH`, budget de 300 images réparti sur les
   segments (`fps = 300 / durée totale`, borné 2-10).
3. Le modèle renseigne `bar_left_floor` par candidat ; le backend retire les `false` avant
   toute notation. Tous écartés → **422** avec un message dédié, pas la 502 générique.

**Deadlift uniquement.** `bar_left_floor` n'a pas de sens au squat (barre sur le dos) ni au
bench, et le compteur n'a été validé que sur des soulevés de terre. Le **modèle de repli**
(flash-lite sur 503) repasse par l'ancien prompt et la vidéo entière.

## Les trois règles de conception, chacune payée par une mesure

* **Régler l'hystérésis pour le RAPPEL** (0,40/0,60), pas pour l'exactitude : le modèle ne peut
  qu'élaguer. Ce réglage met toutes les vraies reps dans la liste sur 43 clips sur 47, contre
  42 au réglage équilibré.
* **Champ dédié, jamais `NA`.** `NA` répond déjà à « est-ce que je VOIS ce critère ». Confondre
  les deux supprimerait une vraie rep filmée sous un mauvais angle.
* **Pas de « c'est la dernière rep ».** Les faux candidats sont partout : installation à 0,5 s
  (`conventionnal_deadlift_8`), plan de coupe à 10,5 s (`jeff_nippard_sumo`), marche d'approche
  à 1,7 s (`700 lbs`).

## Ce que vaut MediaPipe seul — mesuré sur 47 clips, 148 reps

| | |
|---|---|
| compte exact | **58 %** |
| à ±1 rep | 96 % |
| biais | **+0,17 — il ajoute des reps, il n'en rate presque pas** |
| détection à l'heure (±1,5 s) | **91 % de rappel**, 20 % de fausses |
| plafond si on savait choisir le bon signal par clip | 83 % |

**Bon détecteur, mauvais compteur.** C'est ce qui justifie l'architecture : on garde le rappel
de 91 %, on confie la précision au modèle.

Vérité terrain : `backend/eval/reps/verite_terrain.json`, comptée **par Erwan sur la vidéo**
dans l'outil de notation (`eval/scorer`, bloc « Répétitions »), clé `n` + `source: humain`.
Mon comptage préalable sur planches de frames est sous `claude_n` : **43/49 seulement**.

## Pièges payés cash

1. **Ne jamais compter des reps sur des planches de frames.** Je me suis trompé 6 fois sur 49,
   dans les deux sens, dont deux tirées jamais effectuées comptées comme des reps : sur une
   vignette on ne voit pas si la barre est en main. Les planches servent à **instruire un
   désaccord**, pas à établir la vérité. Passer par la vidéo, dans l'outil de notation.
2. **Vérifier une lecture d'image avant d'en tirer une explication.** J'ai bâti et répété deux
   fois une théorie de « tremblement du suivi » sur `conventionnal_deadlift_14` — sauts de 100°
   sur un corps immobile. Faux : il montait et descendait vraiment. Le squelette avait raison.
   **Fabriquer le rendu avec squelette AVANT de théoriser** (`eval/reps/rendu.py`).
3. **`flash-lite` ne suit pas le protocole des candidats.** Mesuré : il supprime une entrée au
   lieu de la marquer `false`, et invente une 3e rep avec des notes copiées-collées sur un clip
   à 2 candidats. `flash` fait les deux correctement (rejette le faux, ne sur-élague pas le
   témoin).
4. **Deux runs identiques à `temperature=0` peuvent donner 0 case identique sur 8.** Observé sur
   `conventionnal_deadlift_11` en mode segments. Pire que le plancher de bruit déjà documenté
   dans AGENT.md (77 % de cases identiques). Aucune comparaison de prompt ne vaut sur un run.

## Ce qui a été essayé et écarté

* **Seuils absolus en degrés** (verrouillage = hanche et genou tendus) : 43 % d'exacts contre
  58 %. Les angles articulaires mesurés à l'image ne veulent rien dire hors vue de profil.
* **Repasser la pose à pleine cadence** (30 im/s au lieu de 6, le mode pour lequel
  `running_mode=VIDEO` est fait). Le bruit de suivi s'effondre sur **1 clip sur 5**
  (`sumo_deadlift_4`, 32,0° → 3,9°, confirmé par un contrôle par décimation) **mais le comptage
  ne s'améliore pas** : 2/5 dans les deux cas. Coût ×5. L'échantillon était choisi pour
  favoriser l'hypothèse et elle n'a rien rapporté.
* **Détecter la barre en vision classique.** Deux tentatives, deux échecs : Hough sur les
  disques trouve 19 et 23 cercles dans une salle de sport ; la corrélation de phase d'une bande
  à hauteur des mains donne 0,00 de déplacement dans tous les cas, vrais comme faux.
* **YOLO** : le CPU n'est pas le problème (on ne tournerait que sur ~10 instants candidats,
  <1 s par vidéo). Le problème est que COCO n'a pas de classe « barre » — il faudrait annoter
  et fine-tuner, des jours de travail pour une question que le modèle traite déjà en regardant
  l'image.

## Conséquences connues, non résolues

* **Le droit d'ajouter une rep manquante est perdu** en mode segments : le modèle ne peut pas
  voir ce qui n'est dans aucun segment. Sur les ~9 % de clips où la pose rate une vraie rep,
  on sous-compte silencieusement.
* **Le coût est multiplié par ~4** : 0,12 $ pour une série de 5 reps contre ~0,03 $ avant
  (210 images à ~270 tokens). Leviers : `BUDGET_IMAGES` (300) et `media_resolution` (HIGH),
  deux constantes en haut d'`ai_service.py`.
* **Les notes par rep peuvent sortir strictement identiques** sur toute une série
  (`sumo_deadlift_1` : 2 partout, 8 critères, 5 reps). L'histogramme est alors plat. Pas de
  vérité terrain par rep dans le projet pour trancher entre série homogène et recopie.
* **`RepHistogram.jsx` calcule la hauteur en `total/max`** : une rep avec des critères `NA`
  affiche une barre pleine, à égalité visuelle avec une rep jugée sur 8 critères.
  `not_assessable_count` est calculé côté back et ignoré par le composant.

## Outillage

Tout dans `backend/eval/reps/` (README dedans avec les chiffres détaillés) :

```bash
cd backend
uv run python eval/reps/dump_signal.py --fps 6      # cache signaux.json, ~12 min
uv run python eval/reps/compare.py --signal med     # contre verite_terrain.json
uv run python eval/reps/rendu.py <clip> --debut X --fin Y   # squelette + signal + reps comptées
uv run python eval/reps/planches.py --clip <c> --pas 0.25 --debut X --fin Y  # zoom sur un litige
```

`signaux.json` est un cache : le comptage se met au point dessus sans repasser la pose.
`test_candidats.py` et `test_offsets.py` sont les deux harnais qui ont validé l'architecture
(schéma de production non touché : ils dérivent une variante locale).
