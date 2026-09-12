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
| `pr_160_prod_video24_v2.json` | **temoin du 2026-09-12** : la prod (`eval/run_prod.py`) sur le catalogue reecrit en geometrie (c51c894) | 19/20 | `neutral_or_concave` |
| `pr_160_prod_video24_thoughts.json` | idem temoin, avec `include_thoughts` : le texte des pensees est dans `debug.appel.pensees`. 18/18 etats identiques a v2 | 19/20 | `neutral_or_concave` |
| `pr_160_description_libre.json` | **sans schema** : prose biomecanique libre (`eval/description_libre.py`), clip entier, 24 im/s, HIGH/HIGH, pensees conservees | — | « appears neutral, belt obscures » ; thoracique « slight flexion » ; initiation « torso angle constant, no hip shoot » |
| `pr_160_description_libre_court.json` | idem, prompt de deux phrases sans plan impose (`--prompt court`) : 1 105 tokens de sortie au lieu de 2 745, decollage date a 5,0 s (4,0 s pour le prompt long, 4,44 s pour la pose), Valsalva et flexion de la barre « observes » | — | non mentionne ; « torso angle constant » |
| `pr_160_description_severe.json` | prose libre, prompt « judge known for being extremely critical, find every fault » (`--prompt severe`). Trouve le hip shoot (« stripper pull », 4,0-4,5 s) et le dos rond ; mais aussi une derive avant de la barre, un hitching, un verrouillage incomplet — verdict « no lift » | — | « pronounced flexion » |
| `pr_160_description_porte_fermee.json` | prose libre, prompt « assume a coach saw something wrong, describe what he saw » (`--prompt porte_fermee`), sans demande de severite. Trouve le hip shoot, le dos rond, un lockout « soft », hitching au conditionnel | — | « noticeable flexion » |
| `tibo_description_porte_fermee.json` | **garde-fou** du prompt « porte fermée » sur un clip que l'humain juge sans défaut majeur. Un seul défaut rendu : haussement d'épaules au lockout, 3,0-4,0 s. Sur les images 2,4-4,6 s (12 images) rien de net : trapèzes saillants d'un lifteur en débardeur, distance épaule-oreille stable. Le prompt fabrique un défaut quand il n'y en a pas | — | non mentionné |
| `pr_160_description_porte_couteuse.json` | porte fermée + sortie explicite « if no real fault, say *No fault found* and explain what you checked » (`--prompt porte_couteuse`). Hip shoot, dos rond, hitching à 6,2 s, « red lights » | — | « noticeable flexion » |
| `tibo_description_porte_couteuse.json` | idem sur `tibo` entier : « **No fault found** … *confirmed by the green checkmark that appears at the end of the video* ». **`tibo.mp4` porte une coche verte incrustée à partir de 5,2 s** (extrait d'une vidéo pédagogique) : toute passe LLM sur ce fichier est contaminée. `tibo_sans_coche.mp4` = les 5,0 premières secondes, réencodées avec cv2 | — | — |
| `tibo_sans_coche_description_porte_couteuse.json` | la porte coûteuse sans la coche : « hips shooting up », buste « nearly parallel to the floor » (clip filmé de face), nuque en hyperextension. L'humain : « hanches ne remontent pratiquement pas ». Douze images 1,3-2,5 s : barre et épaules montent ensemble. **Fabriqué** | — | — |
| `tibo_sans_coche_description_porte_fermee.json` | la porte fermée sans la coche : « stripper pull » à 1,67-2,13 s, même diagnostic fabriqué | — | — |
| `paires_tibo_sans_coche_pr_160.json` | **comparaison par paires** (`eval/paires.py`) : les deux clips dans le même appel, « in which of these two lifts do the hips rise faster than the shoulders? Answer A or B ». Six appels sur deux lancements (le 4e coupé par le quota gratuit à chaque fois, 250 k tokens/min puis 20 requêtes/jour) : **« B » six fois sur six**, quel que soit le contenu. Quand pr_160 est en A, il décrit tibo avec « hips shoot up rapidly, torso nearly parallel » et pr_160 avec « hips and shoulders rise at the exact same rate » — les deux descriptions permutent avec l'étiquette. Biais de position, pas de perception | — | — |
| `pr_160_images_cles.json` | idem, mais **6 images cles** annotees (fin du setup, 3 sur la tiree, verrouillage, fin) — `eval/images_annotees.py --cles` | 20/20 | `neutral_or_concave` |
| `pr_160_images_annotees.json` | idem, mais 180 images fixes annotees (squelette MediaPipe, recadrage, bandeau rep/temps/phase) a la place du Part video (`eval/images_annotees.py`) | 19/20 | `neutral_or_concave` |

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


## Images annotees contre video (2026-09-12)

Une seule variable : le support. Meme pose, meme fenetre 3.41-10.89 s, meme cadence
24 im/s (180 images), meme prompt a une phrase pres, memes reglages HIGH/HIGH/0. Les
images portent le squelette MediaPipe, un recadrage stable sur l'athlete et un bandeau
`rep 1 | 4.44 s | PULL`. Temoin : `pr_160_prod_video24_v2.json`, rejoue le meme jour parce
que `pr_160_prod_video24.json` date d'avant la reecriture du catalogue.

**16 etats sur 18 identiques, meme note, meme epingle.** Les deux ecarts vont tous deux
vers `not_visible` (`knee_valgus_tracking`, `rep_transition_velocity`) — le second est
meme plus juste, il n'y a pas de rep suivante. Rien ne bouge sur ce qu'on cherche a
faire dire (`lumbar_at_setup`, `initiation_sequence`, `hip_height_via_femur`).

Cout : 194 753 tokens d'entree (0,33 $) contre 47 748 (0,12 $) — chaque image fixe en
HIGH vaut ~1 080 tokens, contre ~265 pour une image de video. Le douzieme levier mesure
a 0 gain, a trois fois le prix. Le squelette dessine ne change pas non plus la lecture de
l'angle de camera : « direct side profile » sur les images, « diagonal view » sur la video.

**Six images cles au lieu de 180** (`pr_160_images_cles.json`, `--cles`) : 15 etats sur 18
identiques a la video, les trois ecarts vers `not_visible` — dont `descent_hand_contact`,
parce que la selection (derniere image du setup, trois sur la tiree, premiere du
verrouillage, derniere du segment) ne contient pas l'instant du lacher a 8,42 s : c'est
la selection qui l'a perdu, pas le modele, qui le dit lui-meme. Sans `reset`, la note
monte a 20/20 et il n'y a plus d'epingle. 6 850 tokens d'entree (0,09 $, dont 7 365 tokens
de reflexion — il reflechit plus sur 6 images que sur 180). Les 15 etats communs sont les
memes en 6 images, 180 images et video : le support ne fait rien bouger, seule
l'existence de l'instant dans l'entree compte.
