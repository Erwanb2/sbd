---
name: sbd-grading-changes
description: L'architecture de notation du deadlift depuis le refacto du 2026-09-08 — le catalogue d'indicateurs (indicators.py) d'où découlent le schéma, les mesures de pose, la note et le persona, et les règles d'agrégation avec la mesure qui justifie chacune. À charger avant de toucher à indicators.py, schemas.py, rules.py, persona.py, aux seuils de mesure, au barème, ou avant d'ajouter un critère.
---

# Noter un deadlift

## Le principe en une phrase

**Le modèle observe, Python note.** Le modèle ne rend aucun chiffre : il choisit un état
observable dans une liste fermée imposée par le décodage contraint, et `rules.py` traduit en
1, 2 ou 3.

Le gain décisif n'est pas la qualité, c'est le **coût de la mesure** : le barème devient du
code, rejouable sur des sorties déjà stockées sans dépenser un appel. Vu le plancher de bruit
du projet (77 % de cases identiques entre deux passes identiques), pouvoir renoter à volonté
sans repasser par Gemini est le levier le plus rentable disponible.

## Une liste, trois consommateurs

```
indicators.py  ->  schemas.py        le schéma Pydantic des indicateurs jugés par le modèle
               ->  pose_analysis.py  les mesures MediaPipe, par répétition
               ->  rules.py          indicateurs -> critères notés -> note /20 -> conseils
               ->  persona.py        l'archétype, déduit des états observés
```

Ajouter un indicateur = ajouter une entrée dans `INDICATEURS`. Le reste suit.

**19 indicateurs** pour le deadlift depuis le 2026-09-09, en deux sources :

| `Source` | nombre | sens |
|---|---|---|
| `LLM` | 10 | seul un modèle peut le voir |
| `A_TESTER` | 9 | mesurable en théorie, non tranché → **posé au modèle en attendant**, avec dans `note_source` ce qu'il faudrait mesurer |
| ~~`POSE`~~ | ~~17~~ → **0** | **retirés du catalogue**, voir la section dédiée plus bas |

## La pose ne note plus rien (2026-09-09)

**Les 17 indicateurs `Source.POSE` sont commentés dans `indicators.py`.** Le catalogue est
passé de 36 à 19 indicateurs, tous jugés par le modèle.

**Ce qui l'a déclenché.** L'instruction de `conventionnal_deadlift_12`, un lift propre noté
19/20 avec deux conseils correctifs — **les deux issus de mesures de pose fausses, aucun du
modèle** :

* `P01 hand_drift` lisait la dérive d'un poignet dont MediaPipe annonce lui-même **0,05 à 0,12
  de visibilité sur 100 % des images** (le projet rejette sous 0,30). Il contredisait frontalement
  `P03` (LLM), dans le même critère, qui voyait la barre collée aux jambes sur les 5 reps.
* `L01 hip_vs_shoulder_rise` sortait sa sentinelle **9,99** sur une rep où `_phases` avait retenu
  une fenêtre **postérieure au verrouillage**, sur un squelette où le fémur — un os rigide —
  passait de **460 à 85 px en une demi-seconde**, et où la hanche était lue à **3,2°**.

Le détail le plus parlant : sur cette rep, **4 mesures sur 6 avaient été rejetées** par leurs
bornes de plausibilité (`hip_ratio`, `lean_back_deg`, `pitch_deg`, `shin_deg`). Les garde-fous ont
attrapé les mesures inoffensives et laissé passer **les deux seules qui accusaient**. Sans ces
deux artefacts, le lift vaut **20/20 sans aucun conseil**.

**Ce que la pose continue de faire, et qui n'est pas touché** : la cascade sumo/conventionnel
(39/39) et la détection des répétitions candidates (142/146 de rappel). C'est la **notation** par
la pose qui s'arrête, pas la pose.

### Ce que le retrait a emporté

| | avant | après |
|---|---|---|
| critères notés | 6 | **5** — `leg_drive` n'avait QUE des indicateurs POSE (L01, L02, P05) |
| somme des poids | 7,5 | **6,5** |
| personas atteignables | 14 | **8** — perdus : The Squatter, The Crane, The X-Wing, The Soft-Lock, The Over-Extender, The Kneecapper |
| bloc `contexte` | variant, camera_view, pose_quality, equipment, grip, foot_orientation | **equipment, grip, foot_orientation** |
| durées affichées | `pull_s`, `lockout_s`, sticking point | **aucune** |

`ResultView.jsx` retombe sur `mouvement_detecte` quand `contexte.variant` manque : le titre reste
juste. `criteriaGuides.js` et `sampleResult.js` gardent une entrée `leg_drive` — inoffensive pour
le premier (table de correspondance), mais **la démo mockée de la page d'accueil affiche encore un
critère que le produit ne rend plus**.

**Pour rétablir un indicateur** : le remettre dans le tuple `INDICATEURS`, décommenter ses entrées
dans `CONSEILS` (`_verifie()` refuse un conseil vers un état inexistant), et pour L01/L02/P05
remettre `"leg_drive"` dans `CRITERES`. `pose_analysis.mesures_de_rep` calcule toujours toutes les
grandeurs : rien n'a été supprimé côté mesure, elles ne sont simplement plus consommées.

## Deux limites dures — ne jamais les contourner par un proxy

1. **MediaPipe ne voit pas la barre.** Aucun repère de barre ni de disque. Le poignet est un
   substitut acceptable au setup (la main tient la barre) et douteux pendant la tirée. Le champ
   s'appelle `hand_drift`, pas `bar_drift`, et c'est délibéré.
2. **MediaPipe ne voit pas le rachis.** Aucun repère entre épaules et hanches : le tronc est un
   segment droit par construction. Un « angle de flexion lombaire » calculé depuis épaule-hanche
   mesure l'inclinaison du buste, pas sa courbure. `back_at_setup` et `back_under_load` restent
   `LLM`, définitivement — et c'est le critère pondéré 2, celui où une mauvaise note est une
   blessure. Sur `conventionnal_deadlift_14`, l'humain écrit « dos beaucoup arrondi » et le
   modèle répond « flat » trois fois sur trois. Rien dans l'architecture ne peut le contredire.

## Les règles d'agrégation, et la mesure derrière chacune

* **Note d'un critère sur une rep = la plus basse de ses indicateurs.** Un critère est aussi bon
  que son pire élément, comme un juge lit un lift.
* **Note d'un critère sur le set = moyenne des notes par rep, arrondie au plus proche, les
  ÉGALITÉS VERS LE BAS.** L'arrondi à l'inférieur a été mesuré comme arithmétiquement identique
  au minimum sur ≤3 reps (45 critères sur 45), donc écarté. Mais l'arrondi au plus proche
  classique affichait « Setup and tension 3/3 » au-dessus de deux fautes listées : sur 4 reps
  notées 3,3,2,2 la moyenne vaut exactement 2,5. Seules les égalités changent.
* **Note sur 20 = moyenne pondérée des critères, sur les moyennes NON arrondies.** Sinon un set
  à moitié fautif sortait à 19/20 sous deux conseils correctifs.
* **Un critère non évaluable sort du calcul ET du dénominateur.** Un clip où le dos n'est pas
  visible n'est pas un clip où le dos est mauvais.

## Le persona se mérite sur la série

Deux conditions, chacune contre une erreur constatée :

1. **Le défaut doit survivre à l'agrégation** — le persona n'est retenu que si son critère est
   sous le maximum au niveau du set. Une descente notée 2 sur 2 reps sur 5 décrochait « The
   Kneecapper » sur un lift que l'humain qualifie de « très propre » et que le système note
   20/20 : un critère à 1 sur une rep sur cinq ressort à 20/20 après moyenne, donc l'étiquette
   contredisait le chiffre.
2. **Au-dessus de `SEUIL_TECHNICIEN` (18/20) et sans aucun critère à 1, c'est The Technician.**
   La seconde moitié n'est pas décorative : la note est pondérée, et **quatre critères sur six
   peuvent valoir 1/3 pour un total d'exactement 18**. Sans elle, le produit féliciterait un
   lifter dont la barre part loin du corps.

Résultat vérifié : `conventionnal_deadlift_12` rend The Technician, comme l'humain.

## Pièges payés cash

1. **Des identifiants français font répondre le modèle en français.** Les descriptions étaient
   en anglais mais les noms de champs (`mise_en_tension`) et les clés d'états (`progressive`,
   `a_coup`) ne l'étaient pas : les cinq résumés du clip 12 sont sortis en français sur un site
   anglais. **Tout ce que le modèle voit est en anglais** ; les commentaires restent en français.
2. **Pas de centimètres sans calibration.** L'ancien code convertissait les pixels avec un fémur
   supposé de 40 cm : le résultat était un ratio habillé en unité calibrée. Les distances sont
   en **fraction de fémur**, et le disent.
3. **Une borne de plausibilité vérifie la VALEUR, pas la validité de l'INSTANT.** `PLAUSIBLE`
   rejette un tibia à 157°, mais 137,5° d'angle de hanche est parfaitement banal — sauf qu'il
   avait été relevé à un instant qui n'était pas un verrouillage. La mesure était crédible, le
   moment ne l'était pas. Voir `comptage-reps` pour le correctif de `_phases`.
4. **Figer le côté caméra ET le sens du regard sur le CLIP.** Les redécouvrir par répétition les
   fait basculer en cours de série, et le signe de toutes les mesures orientées s'inverse : une
   rep sortait à 50,9° de bascule arrière, une autre à 157° de tibia.
5. **Le `summary` par rep ne parle pas des fautes qu'il vient de noter.** Mesuré le 2026-09-09
   sur `conventionnal_deadlift_12`, deux runs indépendants. La rep 3 est la plus mauvaise du set
   (`leg_drive` 1, `bar_path` 2, citée dans les deux conseils), et son résumé dit *« solid
   technique with a flat back »* puis *« stable back positioning and a smooth ascent »*. Rien
   n'est faux — `spine` vaut bien 3 — mais **rien ne lie le résumé aux critères** : la consigne
   du schéma dit seulement « one short sentence describing what you saw on THIS repetition, no
   score, no advice » (`schemas.py:54`). Le modèle est donc libre de ne décrire que ce qui va
   bien, sur la rep qui va le moins bien. Un lecteur qui parcourt les reps une par une lit
   l'inverse de la note. À corriger dans la consigne, pas dans le code.
6. **Ne pas tout afficher.** La première version des cartes de critère listait les huit faits
   observés, y compris les bons, sous un critère à 3/3 : la page doublait de longueur. Seuls les
   faits sous le maximum s'affichent, le reste va dans le dépliant.

## Le bruit run-à-run dépend du clip

`AGENTS.md` retient un plancher de **77 % de cases identiques** entre deux passes identiques, et
`comptage-reps` un cas à **0 case sur 8** (`conventionnal_deadlift_11`, en mode segments).

Mesure du 2026-09-09 sur `conventionnal_deadlift_12`, `gemini-3.5-flash`, deux runs complets :
**30 cases sur 30 identiques**, plus la note globale (19/20), le persona, la tenue du set, la
qualité de pose et les deux conseils — mot pour mot. Seuls les résumés en texte libre diffèrent.

**Hypothèse, pas fait établi** (2 runs sur 1 clip) : le bruit serait une propriété du **clip**
plutôt que du modèle — une série nette et bien segmentée se reproduit, un clip ambigu part dans
tous les sens. Les deux seuls points de mesure vont dans ce sens (30/30 ici, 0/8 sur le clip 11),
c'est tout ce qu'on peut en dire.

**Ce que ça ouvre.** Le désaccord entre deux runs mesure l'hésitation du JUGE, là où toutes les
pistes tentées le 2026-09-09 pour « savoir qu'on ne sait pas » mesuraient la qualité de l'IMAGE —
et ont toutes échoué. C'est la bonne grandeur, mais elle **double le coût** (~0,24 $ par vidéo),
donc à réserver à l'évaluation. **Non validé** : il reste à mesurer, sur une dizaine de clips
faciles et litigieux, si le désaccord prédit vraiment l'erreur. Sans ça, ne pas s'en servir.

## Outillage

```bash
cd backend
uv run python eval/check_pose_cascade.py         # la cascade sumo/conv, 44/47, ~3 s/clip
uv run python eval/sample_page.py                # régénère la démo de la page d'accueil
uv run python eval/scorer/server.py              # l'outil d'annotation humaine
```

`indicators._verifie()` tourne à l'import : identifiants en double, critère inconnu, mesure
`POSE` sans seuils ni bornes, conseil pointant vers un état inexistant — tout ça échoue là où
ça se voit.
