---
name: sumo-stance-mediapipe
description: Détecter sumo vs conventionnel sur une vidéo de deadlift avec MediaPipe Pose — la mesure qui marche, ses seuils, sa zone aveugle, et les pièges de validation rencontrés. À charger avant de toucher à la classification de mouvement, d'ajouter des features de pose, ou de valider une règle sur le jeu de clips de data/.
---

# Sumo vs conventionnel par la pose

## En production (depuis le 2026-09-05)

`backend/pose_analysis.py` est le module de production : il decode la video une fois,
passe 30 frames dans MediaPipe et rend la variante du deadlift plus un bloc de
cinematique. `ai_service._task_detect_movement` ne demande plus que la **famille** du
mouvement au modele (squat / bench press / deadlift) ; la variante vient de la cascade.
Repli sur flash-lite si la pose echoue. Verification : `uv run python
eval/check_pose_cascade.py` (46/47 attendu).

**Ne pas toucher sans rejouer ce script** : les seuils dependent de l'echantillonnage.
Trois details les invalident silencieusement — le nombre de frames (30), les horodatages
passes a `detect_for_video` (position reelle dans la video : le suivi inter-frames en
depend) et le modele (`heavy` ; `full` et `lite` font perdre 15 a 20 points).

## Le modèle : largeur, puis profondeur

Deux mesures et un aiguillage. La largeur tranche quand la caméra voit la stance ; sinon on
bascule sur l'ordre de profondeur main / genou, qui est ce qu'un humain lit instantanément de
profil (« l'avant-bras passe devant ou derrière le genou »).

```
largeur    = médiane sur le clip de (écart talons / écart épaules), axe 3D cheville→cheville
confiance  = minimum sur le clip de (écart des poignets / longueur du tronc), en 2D
profondeur = médiane sur le tiers bas de (z_main − z_genou) du côté caméra, ÷ épaisseur du corps

si confiance >= 0.004  ->  sumo si largeur >= 1.70, sinon conventionnel
sinon                  ->  sumo si profondeur >= -0.0178, sinon conventionnel
```

`all_hee_an3d`, `min_wri_over_torso_2d` (`pose_mediapipe/features.py`) et
`bot_idx_kn_near_zext` (`pose_mediapipe/zfeats.py`). Seuils dans `regles.json`.

**39/39 sur le jeu complet, couverture totale, plus aucune abstention.** 36/39 en LOO avec tous
les seuils réappris. 12/12 sur les 12 clips arrivés après le figeage des seuils. Six clips sont
aiguillés vers la profondeur ; les six sont corrects.

Pourquoi ça marche : les deux mesures échouent sur des axes orthogonaux. La largeur a besoin
d'un écartement visible dans le plan image, la profondeur a besoin d'un membre proche de la
caméra et bien visible — ce qui est justement le cas quand le corps est vu par la tranche.
Sept autres features de la même famille (poignet ou coude contre genou ou hanche, en z monde ou
z image) donnent le même 6/6 sur les clips durs : c'est un effet de famille, pas une feature
chanceuse.

**Réserve à connaître.** La feature de profondeur a été choisie en regardant quels clips durs
elle sauvait, sur les 39. En refaisant la sélection sur les 27 anciens seulement, elle tombe à
10/12 — mais il n'y avait alors que 2 clips « non fiables » pour la choisir, donc c'est un test
de la sélection sur 2 points, pas du design. Le prochain lot tranchera.

La variante prudente (`si confiance < 0.004 -> DOUTE`) reste disponible : 33/33 sur 85% de
couverture, à préférer si un faux positif coûte plus cher qu'une abstention.

## Ce qui est déjà tranché — ne pas refaire

- **Mesurer à la frame de setup est la pire option.** Corps replié, membres occultés.
  La médiane sur tout le clip gagne (AUC 0.81 contre 0.74 au setup).
- **Les tests d'inclusion** (poignets ou coudes entre les jambes) sont précis mais s'effondrent
  dès que le côté opposé à la caméra est occulté : ces landmarks-là sont inventés
  (visibility 0.03-0.26 en profil). Vérifier `visibility` avant de croire un landmark.
- **L'ouverture des pieds** a été testée deux fois. Version naïve (angle du pied contre l'axe des
  hanches) : sans valeur, l'axe des hanches est dégénéré de profil. Version correcte, **l'angle
  entre les deux pieds en 3D** — sans aucune référence externe, médiane sur le clip, seuil 24.7° :
  AUC 0.82, LOO 0.83. Signal réel mais sous la mesure de largeur (0.92 / 0.90), et surtout
  **inutile là où il faudrait** : dans la zone de doute il tranche 4 clips sur 6 et se trompe sur
  2 — le pied subit le même repliement que la stance en vue de profil (9.6° et 7.2° sur deux
  sumos). En OU avec la largeur il dégrade (32/36 contre 34/36). Ne pas y revenir.
- **Aucune combinaison de règles ne bat durablement la mesure seule.** Comité de règles 0.78,
  sélection automatique de feature 0.67, conjonctions parfaites sur 27 clips → 1/6 à 4/6 sur
  le lot suivant. Voir les pièges ci-dessous.
- **L'ordre de profondeur est un mauvais classifieur global** (AUC 0.85, LOO 0.77) mais un
  excellent second recours : il est fort exactement là où la largeur est aveugle. Ne pas
  l'évaluer sur tout le jeu et le jeter — l'évaluer sur les clips que la largeur ne peut pas
  juger. C'est ce qui a fait passer le modèle de 33/33 sur 85% de couverture à 39/39 sur 100%.
- **Le z des landmarks image** (`landmark.z`) est resté hors de la batterie initiale pendant
  tout le balayage des 340 features : elle n'utilisait que x et y. Vérifier qu'une coordonnée
  disponible n'est pas simplement oubliée.

- **`cv2.VideoCapture` ignore le flag de rotation mp4.** Deux clips de `data/` partent couchés.
  `pose_mediapipe/evaluate_new.py` contient le parseur de `tkhd` qui règle ça.
- **MediaPipe 1.0 ne charge pas sous WSL** (`libGLESv2.so.2`). Épingler `mediapipe==0.10.21`,
  tasks API, `pose_landmarker_heavy.task`. Un landmarker **par clip** en mode VIDEO : les
  timestamps doivent croître sur toute la vie de l'objet.

## Les pièges de validation, payés cash

1. **Une séparation parfaite sur ~25 clips ne vaut rien.** Obtenue deux fois (21 clips, puis 27),
   effacée deux fois par le lot suivant. Avec 340 features candidates, la perfection est le
   comportement attendu, pas un résultat.
2. **Un test de permutation ne protège pas de ça.** Il dit que le signal existe, pas que le
   seuil tient. Seul un lot neuf tranche.
3. **La sélection de feature est le maillon faible**, pas le classifieur. En LOO imbriquée, choisir
   la feature dans le pli fait tomber le score à 0.67 : la sélection surapprend à elle seule.
4. **Une histoire physique plausible rend un artefact plus convaincant, pas plus vrai.**
   `min_toe_over_sh_2d` (« les pieds ne se superposent jamais à l'image ») expliquait
   élégamment une conjonction parfaite. Faux : deux sumos de profil valent 0.008 et 0.039.
5. **Vérifier une étiquette qui contredit fortement la mesure.** `jeff_nippard_sumo.mp4` était
   l'unique raté ; c'était le nom du fichier qui mentait, pas la mesure. Renommé depuis.

## Outils

Tout est dans `pose_mediapipe/` : `features.py` (~50 mesures par frame × 5 agrégations),
`evaluate_new.py` (juge de nouveaux clips contre tous les modèles, télécharge le modèle tout
seul), `features_39_clips.json` (matrice prête à rejouer sans repasser la pose),
`search.py` / `exact.py` / `joint_loo.py` (classement, énumération exhaustive par masques de
bits, LOO à seuils conjoints).

```bash
cd pose_mediapipe
uv run --with mediapipe==0.10.21,opencv-python-headless,numpy python evaluate_new.py \
    ../data/nouveau.mp4 --truth sumo
```

## En production

La mesure est un **indice fourni au modèle**, pas un classifieur de remplacement : joindre la
valeur et le `view` au prompt de classification quand `view >= 0.30`, ne rien injecter sinon et
laisser Gemini juger sur les images. La zone aveugle est réelle — 15 des 33 clips sont filmés de
profil, dont 7 sumos.
