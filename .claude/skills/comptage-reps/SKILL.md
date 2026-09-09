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
| **rappel** — une vraie rep tombe dans la fenêtre d'un candidat | **97 %** (141/146) | 97 % (142/146) |
| **précision** — un candidat contient une vraie rep | 84 % | 83 % |

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

## L'entrée de la vidéo est élaguée avant toute mesure

**Depuis le 2026-09-09** (`_des_la_premiere_extension`, `rep_detection.py`). On suit le minimum
courant depuis le début ; dès que le signal remonte de `AMPLITUDE_MIN` au-dessus, l'extension a
commencé : on jette tout ce qui précède **le creux d'où elle part**, et on ne touche plus à rien
après. Porte et normalisation se font ensuite sur ce qui reste, toutes deux sur les centiles.

Le temps mort d'entrée — filmer, poser le téléphone, tourner autour de la barre — faussait les
**deux** repères, et le second dégât était le plus coûteux :

* **le p5 ne descend pas jusqu'au creux.** `engueran_sumo`, 34 s de mise en place et une rep à
  33,4 s : p5 = 155,4° là où le creux réel est à 140°, amplitude apparente 18,8° < 25°, et
  `candidats` rendait `[]` sans même chercher. (Le p95, lui, était juste : 174,2 contre 174,4.)
* **le p95 est tiré vers le haut, donc la normalisation est étalonnée sur du temps mort.**
  `long_deadlift` : p95 = 170,7° sur le clip entier contre **163,7°** sur la série seule.
  L'hystérésis ne se ré-armait plus entre deux reps enchaînées → 2 des 11 reps ratées.
  C'est la réponse à l'hypothèse de ré-armement laissée ouverte : la cause était en amont.

| | 6 im/s | 15 im/s |
|---|---|---|
| p95−p5 sur le clip entier | 138/146 (94,5 %) — précision 85,2 % | 141/146 (96,6 %) — 83,4 % |
| porte sur `max − min` | 139/146 (95,2 %) — 85,4 % | 142/146 (97,3 %) — 83,1 % |
| **élagage de l'entrée** | **141/146 (96,6 %)** — 84,4 % | 142/146 (97,3 %) — 82,5 % |

Deux propriétés à ne pas perdre en retouchant : le seuil est `AMPLITUDE_MIN` lui-même, pas une
nouvelle constante ; et exiger en plus « du temps mort pendant N secondes » est **inutile**
(2, 5 ou 10 s donnent le même résultat) — ne pas rajouter ce paramètre.

**`max − min` a été en production quelques heures le 2026-09-09, puis retiré** : il ouvrait la
porte mais ne corrigeait pas la normalisation, donc ne réparait pas `long_deadlift`, et il
abandonnait la robustesse des centiles au point aberrant pour rien.

**Effet de bord sur l'arbitrage de cadence** : 6 im/s est passé de 138 à 141, contre 142 à
15 im/s. L'écart entre les deux cadences n'est plus qu'**une répétition** — l'argument pour
payer +64 % de temps de pose a pratiquement disparu.

## Les clips fautifs restants, et leur mécanisme

Après l'élagage de l'entrée, il en reste **deux** (plus un faux positif d'annotation).

* **`conventionnal_deadlift_8`** — 7,7 s, une rep à 5,89 s, deux candidats `[0–2,93]` et
  `[6,07–7,67]` : **aucun ne la contient**. Le système note deux non-reps en silence, c'est le
  pire comportement produit du lot. Mécanisme connu depuis le 2026-09-08 : un disque de 5 kg est
  entre la caméra (posée au sol) et les jambes, et MediaPipe replie genou et cheville dessus
  pendant toute la montée — au verrouillage réel le signal dit « plié en deux » (0,04 normalisé).
  Il est **confiant et faux** : visibilité 0,77-0,87 sur le genou. Durcir le filtre de visibilité
  et vérifier la plausibilité anatomique ont été testés et ne séparent rien. Piste ouverte : le
  redressement du tronc (épaule-hanche) est propre là où l'angulaire est inversé, et se comporte
  en **complément** (répare 3 clips, en casse 2) — l'union des deux listes reste à mesurer.
* **`conventionnal_deadlift_14`** — 1 rep couverte sur 3. Non instruit depuis l'élagage.
* **`poitrine_relevee`** (1/3) n'est PAS fautif : ses instants annotés sont un artefact
  d'annotation, voir le piège n°4.

## Ce qui a été essayé et écarté

* **Élaguer AUSSI les plages mortes du milieu** (2026-09-09) — la variante trop gourmande de
  l'élagage d'entrée qui est, lui, en production : jeter toute plage de N secondes sans
  extension, où qu'elle soit. **Mesurée : 136/146 à 5 s, contre 141 pour l'élagage d'entrée seul.**
  Le mécanisme est net et disqualifiant : sur `worst_deadlift` la règle jette **tout le clip**
  (plages `0,00-5,50 s` à 128-152° et `5,67-11,83 s` à 154-171°). L'extension complète est bien
  là, 43°, mais étalée sur 12 s — aucune tranche de 5 s n'atteint 25°. Mesurer une amplitude sur
  une durée fixe, c'est mesurer une **vitesse** d'extension : la règle punit précisément les
  tirées lentes, celles qui grindent. Le balayage le confirme, le rappel monte avec la fenêtre
  (2 s → 126/146, 10 s → 139/146) : la règle ne devient bonne qu'en cessant d'élaguer.
  La leçon vaut au-delà : **ne jamais élaguer au milieu du clip**, seulement à l'entrée.

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
