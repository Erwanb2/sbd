---
name: comptage-reps
description: Compter les répétitions d'un deadlift — le rappel réel du détecteur (95%, mesuré sur 146 répétitions horodatées à la main), pourquoi un compte de candidats ne prouve rien, et l'architecture où la pose propose des instants et Gemini tranche si la barre a décollé. À charger avant de toucher au comptage de reps, au champ `bar_left_floor`, au mode segments d'`ai_service`, à `rep_detection.py`, à `_phases`, ou avant de proposer un détecteur de barre ou de changer la cadence d'échantillonnage.
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
  qu'élaguer. Mesuré sur les instants : 95 % des vraies reps sont dans la liste.
* **Champ dédié, jamais `NA`.** `NA` répond déjà à « est-ce que je VOIS ce critère ». Confondre
  les deux supprimerait une vraie rep filmée sous un mauvais angle.
* **Pas de « c'est la dernière rep ».** Les faux candidats sont partout : installation à 0,5 s
  (`conventionnal_deadlift_8`), plan de coupe à 10,5 s (`jeff_nippard_sumo`), marche d'approche
  à 1,7 s (`700 lbs`).

## Ce que vaut le détecteur — mesuré sur 46 clips, 146 répétitions HORODATÉES

Depuis le 2026-09-08, la vérité terrain contient les **instants** de verrouillage
(`verrous` dans `verite_terrain.json`), pas seulement un compte. Ça change tout ce qu'on
peut mesurer.

|  | 6 im/s (production) | 15 im/s |
|---|---|---|
| **rappel** — une vraie rep tombe dans la fenêtre d'un candidat | **95 %** (139/146) | 97 % (142/146) |
| **précision** — un candidat contient une vraie rep | 85 % | 83 % |

`uv run python eval/reps/rappel_instants.py` depuis `backend/`. Gratuit, aucun appel Gemini.

**Le rappel est la seule métrique qui compte** : le modèle ne peut qu'élaguer. Les 15 % de
candidats en trop ne sont pas un défaut, c'est le réglage voulu.

### ⚠️ Un compte de candidats ne prouve RIEN

C'est le piège le plus coûteux de la journée du 2026-09-08. `conventionnal_deadlift_14` a
**3 candidats pour 3 vraies reps** — couverture « parfaite » au sens d'un comptage — alors
qu'**un seul candidat correspond à une rep** : les deux autres sont le lifter qui marche vers
la caméra pour arrêter l'enregistrement.

Conséquence directe : une mesure de la cadence 15 im/s a d'abord conclu « aucun gain, même
légèrement pire » sur le proxy par comptage (91 % → 89 %), et l'inverse sur les instants
(95 % → 97 %). **Comparer des comptes n'est pas comparer des instants.**

## Pièges payés cash

1. **Ne jamais compter des reps sur des planches de frames.** Je me suis trompé 6 fois sur 49,
   dans les deux sens, dont deux tirées jamais effectuées comptées comme des reps : sur une
   vignette on ne voit pas si la barre est en main. Les planches servent à **instruire un
   désaccord**, pas à établir la vérité. Passer par la vidéo, dans l'outil de notation.
2. **Regarder les images AVANT de théoriser.** Le 2026-09-08 je me suis trompé trois fois de
   suite sur `conventionnal_deadlift_14` : d'abord « la rep n'existe pas », puis « MediaPipe a
   trouvé 3 candidats sur 3 reps donc il a bon », puis « les étapes 1 et 2 de `_phases` sont
   correctes ». Les trois ont été démenties par une planche de frames, la dernière par la
   remarque d'Erwan à l'œil nu (« je vois le lifter debout vers 5,7 s, pas 6,33 »), plus juste
   que le code d'une seconde et demie. Plus tôt encore, une théorie de « tremblement du suivi »
   avait été bâtie deux fois sur ce même clip, et démentie de même.
   **Fabriquer le rendu ou la planche AVANT d'expliquer** (`eval/reps/rendu.py`).
3. **`flash-lite` ne suit pas le protocole des candidats.** Mesuré : il supprime une entrée au
   lieu de la marquer `false`, et invente une 3e rep avec des notes copiées-collées sur un clip
   à 2 candidats. `flash` fait les deux correctement (rejette le faux, ne sur-élague pas le
   témoin).
4. **Un outil d'annotation peut fabriquer de fausses données.** `poitrine_relevee` figurait
   parmi les clips fautifs avec 1 rep couverte sur 3 — en réalité ses trois instants annotés
   étaient `[0.02, 0.12, 1.74]` alors que les reps culminent vers 2,2 / 6,2 / 10,2 s, et les
   trois candidats les couvraient parfaitement. Deux double-appuis et une vidéo en autoplay.
   **Avant d'accuser le détecteur, vérifier que l'annotation est physiquement possible** :
   deux verrouillages à moins d'une seconde, ou un repère à t≈0, sont des artefacts.
5. **Deux runs identiques à `temperature=0` peuvent donner 0 case identique sur 8.** Observé sur
   `conventionnal_deadlift_11` en mode segments. Pire que le plancher de bruit déjà documenté
   dans AGENT.md (77 % de cases identiques). Aucune comparaison de prompt ne vaut sur un run.

## Le système ne sait PAS quand il ne sait pas

Mesuré sur les 46 clips (`eval/reps/sait_il_qu_il_ne_sait_pas.py`) :

| | clips | le dit-il ? |
|---|---|---|
| rappel complet | 39 | — |
| rappel partiel | 3 | **non** |
| aucun candidat | 1 | oui → 422 |

**Trois clips sur 46 rendent une analyse amputée en silence.** Le seul cas où le système
s'abstient est le cas extrême où il ne trouve rien du tout.

**L'instabilité du suivi ne permet PAS de le prévoir.** L'idée paraissait excellente sur deux
clips (6,4 % de sauts impossibles contre 14,9 %). Sur 46 les distributions se recouvrent :
médiane 1,0 % sur les clips justes contre 2,5 % sur les fautifs, et un seuil à 8 % signale
5 clips dont **un seul** est vraiment fautif tout en en manquant 4. La visibilité ne sépare pas
davantage (0,96 contre 0,95) — `poitrine_relevee` ratait avec une visibilité de 0,99.
**Proposition abandonnée : ne pas la refaire sans une idée nouvelle.**

## Les instants : `lockout_s` est mal nommé

Deux instants différents circulent, et il ne faut pas les confondre :

| | ce que c'est | biais contre l'humain |
|---|---|---|
| `lockout_s` d'un candidat | le franchissement de 60 % de l'amplitude — un **déclencheur** | **−0,71 s**, en avance 91 % du temps |
| `pose_analysis._phases` | le verrouillage situé DANS la fenêtre, sur lequel toutes les mesures sont accrochées | **+0,13 s**, écart absolu médian 0,35 s |

Le biais du déclencheur est structurel et sans conséquence sur le rappel (la fenêtre est
large). Une seule conséquence réelle : dans `analyse()`, les images de la descente sont prises
après `lockout_s`, donc ce lot contient encore un bout de la montée.

## La porte d'amplitude : centiles pour normaliser, étendue brute pour décider

**Corrigé le 2026-09-09** (`rep_detection.py`). La porte se juge désormais sur `max − min`, la
normalisation reste sur `p95 − p5`.

Le p95 n'a jamais été en cause : sur `engueran_sumo` il vaut 174,2° contre 174,4° au vrai pic.
C'est le **p5** qui manque le creux : le lifter n'est en bas que 3,3 s sur 35,5 (9,4 % du clip),
donc le 5e centile tombe en pleine descente à 155,4° là où le creux réel est à 140°. Amplitude
apparente 18,8° < 25° → `candidats` rendait `[]` sans même chercher, pour une vraie rep. Le motif
est courant chez un vrai utilisateur : filmer, tourner autour de la barre, faire un lourd, repartir.

**Exactement 2 clips sur 48 changent**, aux deux cadences :

| | 6 im/s | 15 im/s |
|---|---|---|
| p95−p5 (avant) | 138/146 (94,5 %) — précision 85,2 % | 141/146 (96,6 %) — 83,4 % |
| max−min (en prod) | **139/146 (95,2 %)** — précision 85,4 % | 142/146 (97,3 %) — 83,1 % |

`engueran_sumo` réparé. `engueran_fail_deadlift` — le seul clip à 0 rep, une tirée échouée où la
barre ne quitte pas le sol — passe de 0 à 2 candidats (il se redresse à vide à 32,7 s et 36,2 s).
**Arbitrage tranché : on accepte.** La porte n'était une protection déterministe pour ce clip que
par accident ; le champ prévu pour ça est `bar_left_floor`, et les deux candidats sont exactement
ce qu'il rejette. Le coût réel est ailleurs : ce clip déclenche maintenant un appel Gemini avant
son 422 au lieu d'être écarté gratuitement, et sur le **modèle de repli** (flash-lite, sur 503)
la protection saute — il supprime l'entrée au lieu de la marquer `false`, et `rules.py` retombe
alors sur `bar_left_floor = "yes"` par défaut, donc note une tirée échouée. Non vérifié contre
Gemini sur ce clip.

## Les clips fautifs restants, et leur mécanisme

* **`long_deadlift`** — 11 reps, 2 ratées (28,49 s et 41,27 s) qui tombent dans des TROUS entre
  candidats. Hypothèse non vérifiée : le ré-armement de l'hystérésis exige que le signal
  redescende sous 0,40 pendant 0,33 s, ce qui n'arrive peut-être pas sur une série enchaînée.
  Testable sur le cache, gratuitement.
* **`conventionnal_deadlift_8`** — 7,7 s, une rep à 5,89 s, deux candidats `[0–2,93]` et
  `[6,07–7,67]` : **aucun ne la contient**. Le système note deux non-reps en silence. C'est le
  pire comportement produit du lot, et le seul dont le mécanisme reste inconnu.

## Ce qui a été essayé et écarté

* **Élaguer le temps mort au lieu de changer la porte** (2026-09-09) : « s'il n'y a pas
  d'extension de hanche pendant N secondes, on jette ce bout de vidéo », puis centiles,
  porte et hystérésis sur ce qui reste. Idée séduisante — elle garde la robustesse des
  centiles que `max − min` abandonne. **Mesurée : 136/146 à 5 s contre 139 pour `max − min`.**
  Le mécanisme est net et disqualifiant : sur `worst_deadlift` la règle jette **tout le clip**
  (plages `0,00-5,50 s` à 128-152° et `5,67-11,83 s` à 154-171°). L'extension complète est bien
  là, 43°, mais étalée sur 12 s — aucune tranche de 5 s n'atteint 25°. Mesurer une amplitude sur
  une durée fixe, c'est mesurer une **vitesse** d'extension : la règle punit précisément les
  tirées lentes, celles qui grindent. Le balayage le confirme, le rappel monte avec la fenêtre
  (2 s → 126/146, 10 s → 139/146) : la règle ne devient bonne qu'en cessant d'élaguer.
  Ne pas la refaire sous une autre forme temporelle. Si la fragilité de `max − min` au point
  aberrant se manifeste un jour, la réparation est un min/max **robuste** (p2/p98, lissage plus
  fort) — pas une fenêtre.

* **Seuils absolus en degrés** (verrouillage = hanche et genou tendus) : 43 % d'exacts contre
  58 %. Les angles articulaires mesurés à l'image ne veulent rien dire hors vue de profil.
* **Repasser la pose à pleine cadence** (30 im/s au lieu de 6, le mode pour lequel
  `running_mode=VIDEO` est fait). Le bruit de suivi s'effondre sur **1 clip sur 5**
  (`sumo_deadlift_4`, 32,0° → 3,9°, confirmé par un contrôle par décimation) **mais le comptage
  ne s'améliore pas** : 2/5 dans les deux cas. Coût ×5. L'échantillon était choisi pour
  favoriser l'hypothèse et elle n'a rien rapporté.
* **Passer à 15 im/s.** Mesuré sur les instants : +2 points de rappel (95 → 97 %), −2 de
  précision, **+64 % de temps de pose**. Le gain est réel mais petit ; c'est un arbitrage
  produit, pas une évidence technique. Attention : une première mesure sur le proxy par
  comptage avait conclu l'inverse — voir l'encadré plus haut. À ne pas trancher sans refaire
  la mesure sur les instants.
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
