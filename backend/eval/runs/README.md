# Sorties brutes du modele, conservees

23 runs du 2026-09-10 et 2026-09-11, tous sur `gemini-3.5-flash`. Chaque fichier est la
sortie de `rules.evalue`. **Seuls les 9 runs du schema decoupe (a partir de
`pr_160_split.json`) portent les observations brutes sous `_obs`** ; les 13 plus anciens
n'ont que les faits notes (`criteres[*].faits`, en clair), pas les cles d'etat — ils ne se
rejouent pas.

## A quoi ca sert

**Tout changement de BAREME se rejoue ici, sans depenser un appel.** Les etats choisis par
le modele sont stockes : changer ce que vaut un etat, un poids, une regle d'agregation, et
recalculer, c'est de l'arithmetique locale sur les runs qui portent `_obs`.

Rejoue le 2026-09-11 au soir, apres le passage de `*_under_load:unchanged` a "sans note"
et la refonte de quatre questions : **aucune note ne bouge** sur les 7 runs rejouables
(18->18, 20->20). Les cles renommees (`between_knees_and_shoulders`, `against_the_shins`,
`brace`) tombent simplement du rejeu.

Seuls les changements de QUESTION (le texte envoye au modele) demandent de rappeler l'API.

## Ce que chaque run teste

Tous sur `pr_160` sauf mention. Les images fixes sont celles de `run_final.py`.

| fichier | configuration | note | `lumbar_at_setup` |
|---|---|---|---|
| `pr_160.json` | production, video, file_uri | 19/20 | — (ancien schema) |
| `pr_160_droit.json` | video reencodee a l'endroit | 19/20 | — |
| `pr_160_prod_high_inline.json` | `media_resolution` force par Part | 19/20 | — |
| `pr_160_prod_defaut_inline.json` | transport `inline_data` | 19/20 | — |
| `pr_160_prod_defaut_inline_fps24.json` | 24 im/s, le plafond de l'API | 19/20 | — |
| `pr_160_fenetre.json` | fenetre resserree a la main sur la tiree | 20/20 | — |
| `pr_160_bc.json` | ordre des etats inverse + ton neutralise | 19/20 | — |
| `pr_160_A_inline.json` | champ de preuve horodatee avant chaque etat | 19/20 | — |
| `pr_160_images.json` | images fixes au lieu de video | 19/20 | — |
| `pr_160_strict.json` | prompt severe, ancien schema | 20/20 | — |
| **`pr_160_split.json`** | **dos decoupe lombaire/thoracique** | **18/20** | **`flexed`** |
| **`pr_160_3.5_bis.json`** | **idem, seconde passe** | **18/20** | **`flexed`** |
| `pr_160_strict_v2.json` | prompt severe + decoupage | 18/20 | `flexed` |
| `pr_160_3.5_v3.json` | + 13 questions reecrites | 18/20 | `flexed` |
| `pr_160_3.5_v2.json` | + paragraphe "nomme les images verifiees" | 20/20 | `neutral` |
| `pr_160_3.5_v4.json` | lombaire decoupe en 3 instants | 20/20 | `neutral` |
| `pr_160_A_video24.json` | **run A** : catalogue du 2026-09-11 soir (voir ci-dessous), prompt de prod neutre, VIDEO 24 im/s, HIGH, raisonnement HIGH | 17/20 | `neutral` |
| `pr_160_prod_video24.json` | **la prod** (`upload_and_detect_concurrent` + `analyze_movement`), reglages identiques a A ; porte le bloc `debug` | 17/20 | `neutral` |
| `conventionnal_deadlift_14_images.json` | images fixes, profil franc, dos tres arrondi | 20/20 | — |
| `conventionnal_deadlift_14_strict.json` | idem + prompt severe | 20/20 | — |
| `conventionnal_deadlift_12_strict.json` | garde-fou : clip que l'humain juge bon | 20/20 | — |
| `conventionnal_deadlift_12_3.5.json` | idem, schema decoupe | 20/20 | `neutral` |
| `erwan_bon_slack_3.5.json` | clip de profil, hanches jugees trop hautes | 20/20 | `neutral` |

## Les deux passes identiques

`pr_160_split.json` et `pr_160_3.5_bis.json` ont **exactement la meme entree** (les 5
reclassements de notes du commit 485b871 ne figurent pas dans le schema). Elles rendent
**21 etats identiques sur 23**, soit 91 %, contre un plancher de bruit documente a 77 %.
Les deux ecarts portent sur `bar_over_midfoot` et `knee_valgus`, tous deux dependants d'un
angle de camera que ce clip n'a pas.

> Le raisonnement complet : skill projet `.claude/skills/rapporter-un-defaut/`.

## Run A (2026-09-11 soir) : nouveau catalogue, une seule passe

Quatre questions reecrites en geometrie (`hip_height` compare deux distances, `bar_over_midfoot`
projette sur le pied, `arms_long` gagne `slightly_bent`, `hip_vs_shoulder_rise` gagne
`shoulders_only`), `brace` sorti du schema, `*_under_load:unchanged` sans note. Chemin de
production (upload + Part borne 3.41-10.89 s) au lieu des images fixes, `fps=24`.

Contre la verite attendue (remarques humaines du jour + `human_labels.json`) :

| champ | attendu | run A | |
|---|---|---|---|
| `hip_height` | trop hautes | `too_high` — "torso nearly parallel to the floor" | ok |
| `shoulders_over_bar` | — | `far_ahead`, coherent avec les hanches | ok |
| `slack_pull` | Grip & Rip (labels) | `yanked` — premier etat technique a 1/3 jamais choisi | ok |
| `descent_control` | dropped (labels) | `dropped` — la video couvre la descente | ok |
| `hip_vs_shoulder_rise` | epaules seules | `together`, "constant torso angle" — contredit son propre `too_high` | rate |
| `arms_long` | legere flexion | `straight` | rate |
| `bar_over_midfoot` | `not_visible` (trois-quarts) | `over_midfoot`, en avouant "the plates block a direct view of the feet" | rate |
| `lumbar_at_setup` | `flexed` (acquis des runs decoupes) | `neutral` — **regression** | rate |

La regression du lombaire est le prix du transport, pas du catalogue : les runs decoupes
avaient 6 gros plans du buste ; la video 368x656 sans gros plan ne montre pas le rachis.
**Deux variables ont change en meme temps** (catalogue ET support), donc rien ici n'est
attribuable : la passe qui tranche est le meme catalogue sur les images fixes + gros plans
de `run_final.py`.

**Seconde passe, entree identique** (`pr_160_prod_video24.json`, par le chemin de prod) :
**22 etats sur 22 identiques**, et les trois compteurs de tokens identiques au token pres
(47 748 / 4 797 / 1 740). A temperature 0 et sur cette entree, la reponse est reproductible ;
le tableau ci-dessus n'est donc pas du bruit — mais il reste n=1 pour la question
"catalogue ou support ?".

