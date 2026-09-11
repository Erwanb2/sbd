---
name: sbd-grading-changes
description: L'architecture de notation du deadlift — le catalogue d'indicateurs (indicators.py) d'où découlent le schéma, la note et le persona, les six mécaniques en ordre causal, l'épingle unique et l'axe structure, et les règles d'agrégation avec la mesure qui justifie chacune. À charger avant de toucher à indicators.py, schemas.py, rules.py, persona.py, à ENCHAINEMENTS, au barème, ou avant d'ajouter un critère.
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

**25 indicateurs** pour le deadlift (compte du 2026-09-11 soir : le dos en quatre champs, `brace` sorti), en deux sources :

| `Source` | nombre | sens |
|---|---|---|
| `LLM` | 18 | seul un modèle peut le voir |
| `A_TESTER` | 7 | mesurable en théorie, non tranché → **posé au modèle en attendant**, avec dans `note_source` ce qu'il faudrait mesurer |
| ~~`POSE`~~ | ~~17~~ → **0** | **aucun indicateur POSE n'est noté**, voir plus bas |

22 champs par répétition dans le schéma, contre 16 avant la refonte : **+35 % de sortie
par rep**, et personne n'a encore mesuré si les 16 anciens se dégradent sous ce poids.

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

### Six de ces questions sont revenues, posées au modèle

Le même jour, la refonte des critères a **remis six questions POSE au modèle** : `S01 hip_height`,
`S02 shoulders_over_bar`, `L01 hip_vs_shoulder_rise`, `P05 knee_valgus`, `K01`+`K02` fusionnés en
`K07 lockout_completion`, et `K03 lean_back`.

**Ce n'est pas un retour en arrière** : aucun ratio n'est rebranché, on repose la question à la
seule source qui voit la barre et le rachis. Mais **rien ne prouve encore que le modèle y répond
bien** — c'est le risque principal de la refonte, et il n'a pas été mesuré. Le plus incertain de
tous était `S09 brace` — **sorti du schéma le 2026-09-11** (décision humaine sur `pr_160`, où le modèle
décrivait une ceinture de force sur un lifter en t-shirt) : le gainage est à peine visible sur une vidéo. Il ne restait que s'il
bat le hasard contre les annotations humaines.

**Pour rétablir un indicateur POSE** : le remettre dans le tuple `INDICATEURS` avec sa `mesure` et
ses `seuils`, remettre ses entrées dans `CONSEILS` (`_verifie()` refuse un conseil vers un état
inexistant). `pose_analysis.mesures_de_rep` calcule toujours toutes les grandeurs : rien n'a été
supprimé côté mesure, elles ne sont simplement plus consommées.

**Piège payé le 2026-09-09** : `_filtre` ne gardait plus AUCUNE mesure, puisqu'il ne garde que
celles réclamées par un indicateur POSE et qu'il n'y en a plus. `pull_s` et `lockout_s` tombaient
avec le reste, donc la moitié « ralentissement » de `tenue_du_set` était morte sans que rien ne le
dise. D'où `indicators.MESURES_TECHNIQUES` : des mesures qui ne notent rien et survivent quand
même, parce que du code les consomme.

## Les critères sont des MÉCANIQUES, pas des phases (2026-09-09)

C'est la refonte structurante. Avant, les critères étaient les phases du geste — setup, tirée,
lockout, descente. **Une phase est l'endroit où une faute apparaît, jamais où elle se corrige** :
personne n'a un « problème de lockout », on a des hanches qui ne passent pas, et ça se voit au
lockout. Découper par phase garantit qu'on rapporte des symptômes.

Un critère a **deux métiers**, et l'ancienne liste n'en faisait qu'un :

1. **Nommer une mécanique**, pour que la chose existe dans la tête du lifter avec un nom, un
   repère et un exercice. C'est la partie qui apprend — et c'est pourquoi on n'a pas le droit de
   fusionner deux habiletés distinctes pour raccourcir la liste : « la barre t'a quitté aux
   genoux » n'apprend ni à se placer, ni à sortir le slack, ni ce qu'est le leg drive.
2. **Désigner quoi corriger.** Ce métier n'est PAS porté par la liste : il est porté par l'ordre
   du dict, qui est causal, et par `ENCHAINEMENTS`.

| clé | libellé | poids | indicateurs |
|---|---|---|---|
| `start_position` | Start position | 1,5 | hip_height, shoulders_over_bar, bar_over_midfoot, arms_long |
| `slack_and_brace` | Slack and brace | 1,0 | slack_pull, jerky_start (`brace` retiré le 2026-09-11, le libellé et la pédagogie restent) |
| `leg_drive` | Leg drive off the floor | 1,5 | hip_vs_shoulder_rise |
| `bar_path` | Bar against the body | 1,5 | past_the_knees, bar_leg_contact |
| `finish_position` | Finish position | 1,0 | lockout_completion, lean_back, hitch, shrug |
| `reset` | Reset between reps | 0,5 | descent_control, rep_transition |
| `structure` | Structure under load | 2,0 | lumbar_at_setup, thoracic_at_setup, lumbar_under_load, thoracic_under_load, knee_valgus, asymmetry |

Trois fusions le même jour, toutes contre la règle « le même événement physique ne doit peser
qu'une fois » : `P10 elbow_flexion` → `S06 arms_long` (même faute au setup et à la tirée),
`K01`+`K02` → `K07 lockout_completion`, `K05 lockout_balance` → `K03 lean_back` (le persona
*The Heel Tipper* disparaît avec).

### Deux axes, et un seul nombre

**La séquence** — les six mécaniques, `indicators.MECANIQUES`, dans l'ordre causal. Elle produit
**l'épingle**.

**La structure** — le dos, les genoux, la symétrie. Ce ne sont pas des choses qu'on exécute, ce
sont des choses qui **lâchent**. Elle produit **l'urgence**, un bandeau au-dessus de la grille.

Montrer les deux ne disperse pas le lifter, là où montrer deux fautes de séquence le disperserait :
l'un dit *change ça dans ton geste*, l'autre *ton corps ne tient pas, baisse*. **Le danger fixe
l'urgence, la cause fixe l'action.** `structure` garde quand même son poids dans la note sur 20 —
sinon un dos qui s'effondre sortirait à 18/20 et le chiffre mentirait.

L'urgence se lit sur la **pire note vue sur une rep**, jamais sur la note agrégée : un dos qui
s'effondre sur une rep sur cinq ressort à 3/3 après moyenne. C'est l'inverse exact du persona, qui
exige au contraire que le défaut survive à la série — parce qu'un surnom étiquette une série et
qu'une blessure n'attend pas la moyenne.

### L'épingle : un seul défaut, et sa chaîne

Cinq cartes à 3/3 et une à 2/3, ce n'est pas du coaching, c'est un bulletin.

L'algorithme de `rules.epingle()` : **partir du PIRE défaut, remonter la chaîne aussi loin qu'elle
va, épingler la racine.** Puis redescendre en avant, transitivement, pour rattacher les
conséquences sous *« And that is why »*.

Deux règles apprises en le construisant, chacune contre une sortie fausse mesurée sur la démo :

* **« Le plus en amont » tout court ne marche pas.** Un `slack_pull:partial` à 2 se plaçait devant
  des hanches qui décollent à 1 et les reprochait séparément, alors que c'est la même histoire.
  Une broutille de setup masquerait en permanence un effondrement plus loin.
* **Le parcours des conséquences doit être TRANSITIF.** S'arrêter au premier cran laissait
  `bar_leg_contact` en défaut indépendant alors que la chaîne y menait en deux sauts, et la page
  reprochait deux fois la même cause.

`ENCHAINEMENTS` est une table **déclarée**, pas une règle « tout ce qui est en aval est supprimé » :
toute faute en aval n'est pas une conséquence. Une arête ne joue que si **les deux bouts sont
fautifs sur la même série**. `_verifie()` refuse une arête partant d'un état non fautif ou
remontant la chaîne causale.

**L'épingle ne pointe JAMAIS vers `structure`** : « utilise moins tes lombaires » n'est pas une
consigne exécutable. La lombaire qui prend est le prix payé pour des hanches hautes sans leg drive.

Même logique pour `hip_vs_shoulder_rise:hips_shoot_up` : **« les hanches décollent » n'est jamais
la faute à rapporter telle quelle.** C'est la *correction* d'un mauvais départ en cours de
mouvement — le corps va chercher sous charge l'angle de dos qu'il aurait dû avoir dès le début.
« Ne laisse pas tes hanches monter » est inapplicable, d'où l'arête depuis `hip_height`.

### L'honnêteté sur les causes qu'une vidéo ne sépare pas

Des hanches hautes, ce sont deux personnes : celle qui se place comme ça, et celle qui **ne peut
pas** tenir plus bas (chevilles, hanches, quadriceps). Même image, action opposée, et aucune vidéo
ne les distingue. Pareil pour les genoux qui rentrent : manque de rotation externe, ou vraie
faiblesse.

Le conseil **nomme l'observation et donne le test**, il ne devine pas la cause :
*« Drop the hips until your shoulders sit over the bar. If you cannot hold it there, that is
mobility, not technique. »* Une phrase, les deux branches couvertes, et le lifter apprend au
passage la différence entre un défaut de geste et une limite de corps.

### Ce que le front en fait

`result.mecaniques` donne les six clés dans l'ordre causal ; `ResultView.jsx` itère cette liste
pour la grille et sort `structure` en bandeau. `criteriaGuides.js` porte le contenu
**pédagogique** — `what` / `cue` / `drill` par mécanique, identique d'une vidéo à l'autre. C'est
la carte ; l'épingle y plante une punaise. La page ne s'allonge pas : les six cartes ne montrent
d'emblée que ce qui cloche.

## Deux limites dures — ne jamais les contourner par un proxy

1. **MediaPipe ne voit pas la barre.** Aucun repère de barre ni de disque. Le poignet est un
   substitut acceptable au setup (la main tient la barre) et douteux pendant la tirée. Le champ
   s'appelle `hand_drift`, pas `bar_drift`, et c'est délibéré.
2. **MediaPipe ne voit pas le rachis.** Aucun repère entre épaules et hanches : le tronc est un
   segment droit par construction. Un « angle de flexion lombaire » calculé depuis épaule-hanche
   mesure l'inclinaison du buste, pas sa courbure. Les quatre champs du dos restent `LLM`,
   définitivement — et c'est le critère pondéré 2, celui où une mauvaise note est une blessure.

### Le dos se demande en DEUX segments, jamais en un choix exclusif

Jusqu'au 2026-09-10, `back_at_setup` proposait `flat` / `upper_back_rounded` /
`lower_back_rounded`. Sur 13 runs et **260 réponses d'indicateur** : 220 états à 3/3,
**0 état à 2/3**, et 8 états à 1/3 tous identiques (la barre lâchée sur `pr_160`).
`lower_back_rounded` n'est jamais sorti une seule fois.

Aucun réglage n'y changeait rien — neuf leviers mesurés le même jour : rotation, résolution,
cadrage, proportion d'images, cadence jusqu'à 24 im/s (le plafond de l'API), ordre des états,
ton des descriptions, transport, `thinking_level=HIGH`. Zéro état changé à chaque fois.

**Ce qui a tranché : la même question en TEXTE LIBRE.** Sur les mêmes images de `pr_160`, le
modèle écrit « *the lumbar spine starts in a state of mild flexion, rounding slightly outward
from the pelvis* » ET « *the thoracic spine exhibits a more pronounced, moderate flexion* », et
identifie la ceinture de force qui masque le rachis lombaire. **La perception n'était pas le
problème.** La liste imposait un OU EXCLUSIF à une réalité qui est un ET : sommé de désigner un
seul segment, il nommait le dominant — le thoracique, à 3/3. Fidèle à sa perception, et gratuit.

D'où `S05 lumbar_at_setup` + `S10 thoracic_at_setup`, `P04 lumbar_under_load` +
`P10 thoracic_under_load`. `upper_back_rounded` et `stable_rounding` sont supprimés : ils
valaient 3/3 et disaient « je le vois mais je ne te le compte pas ».

`S10` garde ses deux états à 3/3 et ne note donc rien. C'est voulu : un haut du dos arrondi et
figé dès le départ est une technique assumée. Il existe pour que le modèle puisse le dire sans
que ce soit sa réponse à la question lombaire.

Mesure, mêmes images, prompt neutre : `pr_160` passe à `lumbar_at_setup=flexed`, 18/20 au lieu
de 19, bandeau `caution` ; `conventionnal_deadlift_12`, que l'humain juge bon, reste à 20/20
avec les quatre champs `neutral`. **Le mauvais clip bouge, le bon ne bouge pas.**

> **Ce que le modèle accepte de rapporter, et les onze leviers mesurés pour l'y amener :
> skill projet `.claude/skills/rapporter-un-defaut/`. À charger avant de reformuler une
> question, d'ajouter ou de retirer un état, ou de proposer un prompt plus sévère.**

### Une observation libre avant chaque état

Chaque champ d'état est précédé de `<nom>_observed`, texte libre. L'ordre des champs étant
l'ordre de génération en décodage contraint, ce texte est produit **avant** le choix et ne peut
pas être réécrit après coup.

La formulation vient d'une mesure : demander « la preuve qui tranche ce champ, avec un
horodatage » produit 21 verdicts avec une heure collée devant, et ne change aucun état.
Demander une **géométrie** — les formes, les positions, leur évolution — en interdisant de
nommer une option et de qualifier, produit des descriptions justes et l'incertitude avec.
C'est ce qui a révélé que le modèle croyait regarder un profil sur un clip filmé de face.

## Les règles d'agrégation, et la mesure derrière chacune

* **Note d'un critère sur une rep = la plus basse de ses indicateurs.** Un critère est aussi bon
  que son pire élément, comme un juge lit un lift.
* **Note d'un critère sur le set = moyenne des notes par rep, arrondie au plus proche, les
  ÉGALITÉS VERS LE BAS.** L'arrondi à l'inférieur a été mesuré comme arithmétiquement identique
  au minimum sur ≤3 reps (45 critères sur 45), donc écarté. Mais l'arrondi au plus proche
  classique affichait « Setup and tension 3/3 » au-dessus de deux fautes listées (le critère
  s'appelait alors `setup`) : sur 4 reps notées 3,3,2,2 la moyenne vaut exactement 2,5. Seules
  les égalités changent.
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
   La seconde moitié n'est pas décorative : la note est pondérée, et **deux critères sur sept
   peuvent valoir 1/3 pour un total d'exactement 18** (recalculé le 2026-09-09 sur les nouveaux
   poids : c'était quatre sur six avant la refonte). Sans elle, le produit féliciterait un
   lifter dont le slack et le reset sont à 1/3.

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
