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

**36 indicateurs** pour le deadlift, répartis en trois sources :

| `Source` | nombre | sens |
|---|---|---|
| `POSE` | 17 | MediaPipe le mesure ; `seuils` transforme la valeur en état |
| `LLM` | 10 | seul un modèle peut le voir |
| `A_TESTER` | 9 | mesurable en théorie, non tranché → **posé au modèle en attendant**, avec dans `note_source` ce qu'il faudrait mesurer |

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
5. **Ne pas tout afficher.** La première version des cartes de critère listait les huit faits
   observés, y compris les bons, sous un critère à 3/3 : la page doublait de longueur. Seuls les
   faits sous le maximum s'affichent, le reste va dans le dépliant.

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
