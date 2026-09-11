# Sorties brutes du modele, conservees

21 runs du 2026-09-10 et 2026-09-11, tous sur `gemini-3.5-flash`. Chaque fichier est la
sortie de `rules.evalue` **plus** les observations brutes du modele sous `_obs` ou
`_obs_brutes`.

## A quoi ca sert

**Tout changement de BAREME se rejoue ici, sans depenser un appel.** Les etats choisis par
le modele sont stockes : changer ce que vaut un etat, un poids, une regle d'agregation, et
recalculer, c'est de l'arithmetique locale sur les 21 runs a la fois.

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
