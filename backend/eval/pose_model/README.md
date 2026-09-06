# Prédire les critères humains à partir des seules mesures de pose

Question posée : avec ce que MediaPipe observe — et rien d'autre, pas de LLM, pas d'image
donnée à un modèle — peut-on retrouver les notes humaines de `eval/scorer/human_labels.json` ?

```bash
cd backend
uv run python eval/pose_model/dump_landmarks.py     # ~8 min, une fois
uv run python eval/pose_model/features.py           # features.json
uv run python eval/pose_model/fit.py --mesurable    # validation, ~6 min
uv run python eval/pose_model/explore.py            # corrélations, contrôle du halo
```

## Le pipeline

| étape | fichier | ce qu'elle fait |
|---|---|---|
| 1. pose | `dump_landmarks.py` | 49 clips → `backend/extracted_frames/landmarks/*.npz` (repères image + monde, ~12 img/s autour de la répétition). C'est la seule étape coûteuse, et elle ne se rejoue pas : itérer sur les features est ensuite gratuit. |
| 2. mesures | `features.py` | 38 grandeurs par clip, écrites en lisant le libellé de chaque critère dans `schemas.py` |
| 3. validation | `fit.py` | une feature, deux seuils, LOO imbriquée, test de permutation, comparaison à Gemini |
| 4. lecture | `explore.py` | corrélations brutes, hors halo, et par variante |

## Ce qui a été mesuré, et pourquoi ce protocole

Le modèle est volontairement minuscule : **une feature, deux seuils, monotone**. Avec 13 à 36
clips notés par critère et trois classes, tout ce qui est plus riche apprend le bruit — c'est
la leçon déjà payée sur la cascade sumo (skill `sumo-stance-mediapipe`).

Deux lectures, toujours affichées ensemble :

* **guidée** — les 3 à 6 features candidates du critère sont déclarées à l'avance d'après le
  barème. Seuls les seuils sont appris dans le pli.
* **libre** — la feature est choisie dans le pli parmi les 38. C'est la mesure honnête d'un
  modèle qu'on laisserait se débrouiller, et elle est presque toujours **moins bonne** : la
  sélection de feature surapprend à elle seule.

Trois garde-fous, chacun issu d'une erreur commise pendant ce travail :

1. **La référence est la meilleure note constante**, pas la médiane d'apprentissage. En LOO,
   la médiane est *anti-corrélée* avec le point retiré quand les classes sont à égalité :
   retirer un 3 fait baisser la médiane. Sa MAE de référence passait de 0,6 à 1,2 et
   fabriquait un gain sur deux critères. Une référence constante dont l'exactitude vaut 0 %
   est impossible : c'est ce qui a mis la puce à l'oreille.
2. **Le halo.** L'humain note un bon lifter bon partout. Une mesure corrélée au niveau général
   corrèle mécaniquement avec chaque critère sans rien dire du défaut visé — la vitesse de
   descente arrive ainsi en tête de huit critères sur onze (ρ = +0,55 avec le niveau du clip).
   `explore.py` affiche la corrélation **hors halo** (note du critère moins moyenne du clip).
3. **La fenêtre de tirée se vérifie aux images.** `--mesurable` écarte les clips dont la
   fenêtre n'est pas crédible (course de barre hors de [0,5 ; 1,2] longueur de jambe, sujet
   hors cadre, repères invisibles) : 39 clips sur 49. Sans ce filtre, des features
   parfaitement calculées sur une fenêtre fausse entrent dans le modèle.

## Repérage de la répétition

`pose_analysis._phases` cherche la répétition sur l'**extension articulaire**, qui n'a de sens
qu'en vue sagittale — c'est ce qui avait pollué l'annotation des 49 clips. Ici le repérage se
fait sur la **hauteur de barre**, parce que l'axe vertical de l'image survit à n'importe quel
azimut de caméra. Trois corrections successives, chacune vérifiée aux images :

* segmentation en zigzag, sinon la plus forte montée d'un clip de cinq répétitions va du creux
  de la première au sommet de la dernière (15 s de « tirée ») ;
* hauteurs prises sur les repères **monde** de MediaPipe, métriques et indépendants de la
  distance caméra. En pixels, un lifter qui recule après avoir lâché la barre remonte dans le
  cadre et fabrique un faux verrouillage — `pr_160` verrouillait sur une image sans barre dans
  les mains ;
* les mains ne montent jamais au-dessus des hanches pendant un soulevé de terre : au-delà, la
  barre est lâchée et le signal de poignet ne dit plus rien.

## Résultats

Erreur absolue moyenne en LOO imbriquée, 39 clips crédibles, échelle 1/2/3. `constante` =
la meilleure note fixe possible ; `gemini` = flash-lite (`llm_scores_persona_last.json`) sur
exactement les mêmes clips. **Plus bas est meilleur.**

| critère | n | pose (guidée) | constante | gemini | p |
|---|---|---|---|---|---|
| hip_hinge_mechanics (conv) | 23 | **0,348** | 0,478 | 0,381 | 0,050 |
| slack_pull_and_lat_engagement (conv) | 23 | **0,478** | 0,739 | 0,619 | 0,040 |
| hip_opening_and_knee_tracking (sumo) | 13 | 0,308 | 0,615 | 0,769 | 0,020 → *artefact, voir plus bas* |
| lockout_execution | 33 | 0,303 | 0,333 | 0,606 | 0,158 |
| bar_path_and_proximity | 20 | 0,350 (libre) | 0,450 | 0,692 | 0,139 |
| eccentric_control_and_descent | 31 | 0,258 | 0,226 | 0,258 | — |
| core_bracing_and_spine_neutrality | 36 | 0,556 | 0,556 | 0,500 | — |
| starting_position | 36 | 0,722 | 0,556 | 0,486 | — |
| leg_drive_activation (conv) | 23 | 0,870 | 0,565 | 0,524 | — |
| slack_pull_and_wedge (sumo) | 14 | 1,214 | 0,714 | 0,714 | — |
| leg_drive_and_floor_spread (sumo) | 14 | 1,286 | 0,714 | 0,786 | — |
| *niveau général du clip* | 36 | 0,624 | 0,481 | — | — |

⚠️ **La colonne `gemini` est une passe unique.** Deux passes identiques du pipeline ne rendent
que 77 % de cases identiques (écart moyen 0,23 par case), donc un écart de moins de ~0,10 de
MAE avec la pose ne veut rien dire. Concrètement : sur `hip_hinge_mechanics`, 0,348 contre
0,381 est une égalité, pas une victoire. Sur `lockout_execution` (0,303 contre 0,606) et
`bar_path_and_proximity` (0,350 contre 0,692), l'écart est trois fois le bruit.

**Un signal crédible.** `hip_hinge_mechanics` ← `pull_hip_share_t1`, la part de l'extension de
hanche déjà consommée au premier tiers de la course de barre. Beaucoup d'extension tôt = les
hanches partent seules = « squatting the weight up » : c'est mot pour mot le mécanisme du
barème. Feature retenue dans 23 plis sur 23, 74 % d'exactitude en apprentissage, 65 % en LOO.
À égalité avec flash-lite, qui a vu la vidéo.

**Un signal unilatéral.** `slack_pull_and_lat_engagement` ← `pre_bar_rise`, le mouvement du
poignet dans les 0,8 s qui précèdent le décollage. Le signe est **l'inverse** de ce que la
feature devait mesurer : ce n'est pas la barre qui se tend contre les disques (sous-pixel,
invisible), c'est la main qui plonge et remonte d'un coup — un « grip and rip ». Les sept
clips au-dessus de 0,045 sont notés 1 six fois. En dessous, la mesure ne discrimine plus rien.

**Un artefact, à ne pas retenir.** `hip_opening_and_knee_tracking` ← `setup_knee_deg` :
les deux clips notés 1 ont un genou à 175° au « décollage », c'est-à-dire un lifter debout.
`engueran_fail_deadlift` est une tirée ratée où la barre ne quitte jamais le sol. La règle
détecte un raté du repérage de phase, pas le suivi du genou.

**Le reste ne bat pas une constante.** Dont `core_bracing_and_spine_neutrality`, et c'est
attendu : MediaPipe n'a aucun repère entre les épaules et les hanches, donc aucune courbure
de rachis. Le seul substitut disponible (longueur projetée du tronc) ne porte rien.

**Le halo domine tout le reste.** La vitesse maximale de descente corrèle à +0,55 avec le
niveau général du clip et arrive en tête de huit critères sur onze. Elle ne mesure pas la
technique : elle sépare les lifters qui lâchent la barre au verrouillage de ceux qui
l'accompagnent. Une fois le halo retiré, elle ne prédit plus rien de spécifique.

## Ce qu'il faut savoir avant d'y revenir

* **11 critères × 2 modes = 22 évaluations.** Sous l'hypothèse nulle on attend ~1 résultat à
  p < 0,05 ; il y en a 3, dont un démonté ci-dessus. Aucun des deux restants n'est *établi* —
  ils sont *candidats*. Un lot de clips neufs tranchera, rien d'autre.
* **La sélection libre de feature perd presque partout** contre la sélection guidée par le
  barème. C'est la même conclusion que sur la cascade sumo : le maillon faible est la
  sélection, pas le classifieur.
* **Gemini est moins bon qu'une constante sur `lockout_execution` (0,606 contre 0,333) et
  `bar_path_and_proximity` (0,692 contre 0,450).** Sur ces deux critères la pose fait mieux
  que le modèle de langage — c'est la piste la plus utile pour le produit, davantage que la
  prédiction complète d'un critère.

## Le résultat le plus important : les deux signaux ne survivent pas sans le filtre

Rejoué sur les 47 clips à phases plutôt que sur les 39 crédibles :

| critère | 39 crédibles | 47 clips | constante (47) |
|---|---|---|---|
| hip_hinge_mechanics | 0,348 | 0,633 | 0,500 |
| slack_pull_and_lat_engagement | 0,478 | 1,033 | 0,700 |

Les deux passent sous la constante. La cause est vérifiée : en apprenant la règle sur les
clips crédibles et en l'appliquant aux 7 écartés, la MAE est de 0,714 contre 0,571 pour la
constante (hip_hinge) et 1,000 contre 0,571 (slack_pull) — et les mesures y sont visiblement
cassées, `pull_hip_share_t1 = -4,96` pour une course de barre de 2,19 longueurs de jambe,
deux NaN, une course de 0,07 sur `conventionnal_deadlift_13`.

Autrement dit : **la règle ne vaut que là où la pose elle-même est exploitable, et le pipeline
sait le dire sans étiquette** (la course de barre est un contrôle interne). En production cela
veut dire s'abstenir sur ~20 % des clips, pas noter au hasard. Ce n'est pas un défaut caché,
c'est une condition d'emploi — mais il faut l'énoncer, parce qu'un signal qui n'existe que sur
le sous-ensemble facile n'est pas encore un signal établi.

### Et symétriquement : ce qui apparaît sans le filtre est du halo

Sur les 47 clips, trois gains passent p < 0,05 — aucun ne tient l'examen :

| critère | modèle | MAE | constante | feature retenue | ce que c'est |
|---|---|---|---|---|---|
| starting_position | libre | 0,372 | 0,535 | `desc_vitesse_max` 43/43 | **du halo pur** : 70 % d'exactitude, mieux que Gemini (50 %), en mesurant à quelle vitesse la barre redescend. Rien à voir avec la position de départ. |
| core_bracing | guidée | 0,500 | 0,568 | `tronc_long_setup` 44/44 | disparaît sur les 39 crédibles (0,556 = constante). La longueur projetée du tronc mesure l'angle de caméra, pas le rachis. |
| hip_opening (sumo) | guidée | 0,286 | 0,643 | `setup_knee_deg` 14/14 | l'artefact décrit plus haut, deux tirées ratées à 175° de genou. |

`lockout_execution` est le seul cas où la même règle (`lock_temps_dernier_10pct`, la part du
temps de tirée passée dans les 10 derniers pour cent d'extension) gagne un peu **sur les deux
sous-ensembles** — 0,303 contre 0,333 et 0,350 contre 0,400 — sans jamais passer sous
p = 0,05. C'est la piste la plus régulière du lot, et flash-lite y est bien plus mauvais
(0,575 à 0,606) qu'une constante.
