---
name: rapporter-un-defaut
description: Ce que le modele accepte de rapporter d'un soulevé de terre, et ce qu'il refuse. Onze leviers de reglage mesures, un seul qui marche, et le protocole pour en tester un nouveau sans se raconter d'histoires. A charger avant de reformuler une question du catalogue, d'ajouter ou de retirer un etat, de toucher au champ d'observation libre de schemas.py, ou avant de proposer un prompt plus severe.
---

# Faire dire au modele qu'une chose est mauvaise

## Le fait central

**Le modele ne penalise jamais une faute technique.** Mesure sur 17 runs stockes, 260
reponses d'indicateur :

| | |
|---|---|
| etats a 3/3 | 220 |
| non notes (`not_visible`, non applicable) | 32 |
| **etats a 2/3** | **0** |
| etats a 1/3 | 8 — *tous* `descent_control:dropped`, un objet qui tombe |

Zero etat a 2/3 sur 260 reponses. Le seul etat penalisant jamais choisi decrit un
evenement physique, pas un jugement technique.

Ce n'est PAS un probleme de perception. Interroge en TEXTE LIBRE sur les memes images, le
modele decrit finement : « *the lumbar spine starts in a state of mild flexion, rounding
slightly outward from the pelvis* », et identifie de lui-meme la ceinture de force qui
masque le rachis. Somme de choisir dans une liste fermee, il repond « dos plat ».

## Le seul levier qui marche

**Retirer l'etat gratuit qui permet de reconnaitre le defaut sans le compter.**

`back_at_setup` proposait `flat` (3/3) / `upper_back_rounded` (3/3) / `lower_back_rounded`
(2/3). L'etat du milieu voulait dire « je le vois, mais je ne te le compte pas ». Le
modele le prenait, et c'etait **fidele a sa perception** : la liste imposait un OU EXCLUSIF
a une realite qui est un ET, et somme de designer un seul segment il nommait le dominant.

Correctif : deux questions, une par zone du corps.

    lumbar_at_setup     neutral(3)  flexed(2)
    thoracic_at_setup   neutral(3)  rounded(3)

Il peut toujours dire que le haut du dos est arrondi, gratuitement — mais ca ne repond plus
a la question sur le bas du dos. **Reproduit sur deux passes a entree identique** :
`flexed`, 18/20, bandeau `caution`, avec la meme justification mot pour mot.

## Les dix leviers qui ne marchent pas

Tous mesures sur `pr_160`, tous a **0 etat change** :

| levier | detail |
|---|---|
| rotation du clip | corrigee cote pose depuis longtemps ; Gemini decode le flag lui-meme |
| resolution | `MEDIA_RESOLUTION_HIGH` est le plafond de l'API, et la source plafonne plus bas |
| transport | `inline_data` vs `file_uri` : 0/20 etats differents |
| cadrage | fenetre resserree a la main, la tiree passe de 11 % a 50 % des images |
| densite d'images | 24 im/s (plafond API, 30 refuse) : 178 images au lieu de 75 |
| ordre des etats | faute placee en premier dans la liste |
| ton des descriptions | clauses de consequence et adoucisseurs retires |
| raisonnement | `thinking_level=HIGH`, reflexion 761 -> 1256 tokens |
| **prompt severe** | voir ci-dessous |
| support | images fixes au lieu de video |

### Le prompt severe est un contournement, pas une solution

« Pars du principe que la pire option est vraie » a fait passer le clip 14 de `flat` a
`upper_back_rounded` — un cran, et il s'arrete **pile avant la frontiere du cout**
(`upper_back_rounded` vaut 3/3, `lower_back_rounded` 2/3). La severite poussait vers l'aveu
gratuit le plus proche.

Mesure decisive : **strict + decoupage rend les memes 23 etats que neutre + decoupage.** La
porte de sortie supprimee, le modele va a `flexed` tout seul. Inutile de demander la
severite, et on evite son risque de sur-sanction.

## Le champ d'observation libre : ce qui marche et ce qui se retourne

`schemas.py` genere `<nom>_observed` AVANT chaque etat. L'ordre des champs etant l'ordre de
generation en decodage contraint, ce texte ne peut pas etre reecrit apres coup.

**Sa valeur est le DIAGNOSTIC**, et elle est reelle : c'est par lui qu'on a appris que le
modele croyait regarder un profil sur un clip filme de face, et que la ceinture masque le
lombaire. Il n'est PAS demontre qu'ecrire avant de classer change les etats.

Deux formulations mesurees, deux echecs — la formulation compte enormement :

1. « ecris ce que tu VOIS qui tranche ce champ, avec un horodatage »
   -> 21 phrases qui sont le verdict avec une heure collee devant
      (« At 4.50s the hips and shoulders rise together »). 0 etat change.
2. « donne l'horodatage, ou dis que tu as suivi le mouvement image par image et
    **nomme les images verifiees** »
   -> les champs exprimant une reserve tombent de **22/23 a 2/23**, et 22/23 se terminent
      par « Nothing stops me from being sure ». `lumbar_at_setup` repasse a `neutral`,
      `asymmetry` d'une abstention correcte a `even`. **Regression.**

**Regle : demander une GEOMETRIE — les formes, les positions, leur evolution — en
interdisant de nommer une option et de qualifier. Ne jamais demander de certifier une
verification : il certifiera.**

Autre echec de la meme famille : reecrire 13 questions en « *Pick X only if you verified
Y* ». Zero etat change, et les reserves disparaissent pour la meme raison.

## Les quatre formes de question qui garantissent une reponse gratuite

Recensement sur les 22 indicateurs notes :

**A. Le milieu encadre** (`hip_height`, `shoulders_over_bar`) — l'etat gratuit est une
bande entre deux extremes. « The hips sit between the knees and the shoulders » est vrai de
presque tout depart. Indice : le modele a ecrit « *thighs at roughly 45 degrees* » sur deux
clips sans rien de commun. C'est une formule, pas une mesure.

**B. Plusieurs sorties gratuites** (9 indicateurs) — l'ideal ET sa variante toleree valent
3/3. `hips_slightly_ahead`, `brief_loss`, `slight`, `fast_but_controlled` : ce sont des
« un peu mauvais ». Passes a 2/3 le 2026-09-11, **effet non encore observe** — le modele ne
les choisit jamais, il prend l'ideal.

**C. L'etat gratuit est une ABSENCE** (9 indicateurs : `no`, `smooth`, `unchanged`, `even`,
`clean`, `locked`, `straight`) — nier un evenement ne demande aucune preuve et ne peut pas
etre pris en defaut.

**D. Une qualite vague** (`slack_pull`, `brace`) — `brace` demandait trois choses en une :
une inspiration, une rigidite, son maintien.

Constat transversal : **10 indicateurs sur 22 n'ont aucun etat a 2/3.** On saute de 3
directement a 1. Pour signaler que les hanches partent devant, il fallait declarer « *the
lift turns into a stiff-legged pull finished by the back* ».

## Les six facons dont la description contredit la case cochee

Audit des textes libres, clip `pr_160`. Huit champs seulement sont irreprochables.

1. **Verification partielle** — la definition porte plusieurs clauses, il en controle une.
   `hip_height` ignore « et le buste loin de l'horizontale », qui est tout le discriminant.
   `bar_over_midfoot` ne parle jamais du pied.
2. **Il repond a une autre question** — la definition demande de COMPARER deux instants,
   il affirme une qualite globale (`past_the_knees`, `hitch`, `jerky_start`).
3. **Il rapporte l'inobservable** — « *the lifter applies upward force gradually* ». Une
   force ne se voit pas. « *the abdominal wall is seen expanding against the belt* », alors
   qu'il ecrivait ailleurs que la ceinture masque cette zone.
4. **Il conclut d'un continu a partir de deux images** — `shrug` juge sur deux images
   POSTERIEURES au verrouillage ; a 0,2 s d'echantillonnage un hitch de 0,1 s est invisible.
5. **Il tranche dans l'axe de profondeur sans le signaler** — quatre indicateurs PROFIL sur
   un clip de face, et il affirme meme « *the camera angle allows a clear view* ».
6. **Deux champs qui se contredisent** — `past_the_knees` « sans contact avec les rotules »
   contre `bar_leg_contact` « contact continu avec les tibias et les cuisses ».

Les huit champs propres ont un point commun : **une seule affirmation verifiable sur un
instant.**

## Ce qui est refute

* **Le prompt severe** — meme resultat que le neutre une fois la porte de sortie fermee.
* **Decouper une EVOLUTION en instants** — `lumbar_under_load` decoupe en trois questions
  (sol, genou, verrouillage) a fait perdre l'acquis : les trois repondent `neutral`, et
  `thoracic_at_setup`, auquel on n'avait pas touche, a bascule aussi. Trois questions quasi
  identiques d'affilee poussent a une reponse uniforme.
* **Les 13 reecritures « Pick X only if… »** — 0 etat change, et perte des reserves.

## Le protocole, et c'est la qu'on se trompe le plus

**Deux natures de modification, a ne jamais melanger :**

* **Le bareme** — ce que vaut un etat, les poids, l'agregation. **Zero appel.** Les 21 runs
  de `backend/eval/runs/` contiennent les etats choisis : tout se rejoue en arithmetique
  locale, sur tous les clips a la fois.
* **Les questions** — le texte envoye au modele. **Cher, et il faut au moins deux passes**
  avant de conclure.

**Ne jamais conclure sur n=1.** Le 2026-09-10 et 11, quinze conclusions ont ete tirees d'un
run unique, dont une commitee. Deux passes a entree identique donnent **91 % de cases
identiques** sur `pr_160` — au-dessus du plancher documente de 77 %, donc la configuration
est stable — mais les deux ecarts tombent precisement sur les champs fragiles
(`bar_over_midfoot`, `knee_valgus`), ceux qui dependent d'un angle que le clip n'a pas.

**Un changement a la fois.** Appliquer 13 reecritures plus une consigne globale d'un coup
rend toute attribution impossible : il a fallu un aller-retour A/B/A pour retrouver lequel
des deux avait casse quoi.

## Le prochain candidat

> 2026-09-11 soir : le catalogue a été réécrit en frontières binaires (voir
> `sbd-grading-changes`). Les noms ci-dessous sont les anciens ; `hip_vs_shoulder_rise`
> s'appelle maintenant `initiation_sequence`, sans cran « un peu ». Le test proposé
> reste le bon.

`hip_vs_shoulder_rise` : `hips_slightly_ahead` y joue exactement le role qu'avait
`upper_back_rounded`. Il vaut 2/3 depuis le 2026-09-11, donc la porte est a moitie fermee,
mais il n'a jamais ete choisi. **A tester sur un clip de profil ou les hanches partent
vraiment devant** — `erwan_mauvais_slack` porte le commentaire humain « hip shoot up a lot ».
Pas sur `pr_160`, qui est filme de face et ou la question n'est pas repondable.

## Run A du 2026-09-11 soir : quatre questions en geometrie, une passe, video

Le catalogue a ete reecrit sur les remarques humaines de `pr_160` : `hip_height` compare deux
distances sur l'image du decollage (le milieu `between_knees_and_shoulders` — la forme A —
est mort), `hip_vs_shoulder_rise` gagne `shoulders_only` (aucun etat ne decrivait des
epaules qui montent seules), `arms_long` gagne `slightly_bent` (le cran 2/3), `bar_over_midfoot`
projette sur le pied et perd `against_the_shins`, `brace` sort du schema, et
`*_under_load:unchanged` ne vaut plus rien (descriptif).

Une passe, video 24 im/s, HIGH, raisonnement HIGH, prompt de prod neutre — `pr_160_A_video24.json`,
tableau complet dans `backend/eval/runs/README.md`. Ce qui bouge : `hip_height:too_high`
avec "torso nearly parallel to the floor", `shoulders_over_bar:far_ahead`, `slack_pull:yanked`
(premier etat technique a 1/3 jamais choisi) et `jerky_start:jerked`. Ce qui ne bouge pas :
`hip_vs_shoulder_rise:together` avec "constant torso angle" — **dans la meme reponse que le
buste horizontal au depart et debout a 5,5 s**. C'est la sixieme facon (deux champs qui se
contredisent), et c'est la cible exacte d'un prompt de coherence, pas de severite.
`bar_over_midfoot:over_midfoot` malgre la consigne de vue et un aveu "the plates block a
direct view of the feet". `lumbar_at_setup` **repasse a `neutral`** : la video sans gros plan
ne montre pas le rachis, la ou les runs decoupes avaient six crops du buste.

**Deux variables ont change a la fois** (catalogue et support), n=1. Rien n'est attribuable
avant la passe symetrique : meme catalogue sur les images fixes + gros plans de `run_final.py`.

> Architecture de la notation : `.claude/skills/sbd-grading-changes/`.
> Sorties brutes et manifeste : `backend/eval/runs/README.md`.
