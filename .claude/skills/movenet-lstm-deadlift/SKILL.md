---
name: movenet-lstm-deadlift
description: Le repo weggry/deadlift-classifier (MoveNet Thunder + LSTM) a été testé sur data/ et écarté — 25-47% contre 39/39 pour la règle MediaPipe. À charger avant de proposer un modèle appris pour classifier sumo/conventionnel, avant de reprendre ce repo, ou pour retrouver le code du portage et la piste laissée ouverte.
---

# MoveNet + LSTM (weggry/deadlift-classifier) — testé, écarté

Testé le 2026-09-04. `github.com/weggry/deadlift-classifier`, papier MDPI *AI* 6(7):148.
Classifie Conventional / Sumo / Romanian, puis un défaut de forme parmi Correct, Early hip
elevation, Overextension, Rounded back.

## Le verdict

| Stratégie | Sur les 47 clips deadlift de `data/` |
|---|---|
| Clip entier | 12/47 = **25.5%** |
| 1re rep détectée, ou vote des reps | 17/47 = **36.2%** |
| En forçant 2 classes (Romanian ignorée) | 22/47 = **46.8%** |

À comparer aux **39/39** de la règle largeur/profondeur — voir `sumo-stance-mediapipe`.
Sous le hasard. Les conventionnels partent en « Sumo » (20/29), les sumos en
« Romanian » (8/18).

## Ce n'est pas une erreur de portage — vérifié

Ne pas reprendre l'expérience en supposant une erreur d'intégration, les trois contrôles
sont faits :

- Le portage rend **9/9** sur leurs propres vidéos, probabilités > 0.99.
- Le modèle rend **99.6%** sur leurs 550 tableaux de keypoints stockés (données
  d'entraînement, donc mémorisées — mais ça valide modèle, interpolation et mapping des classes).
- Mes keypoints reproduisent les leurs à **0.0002** d'écart moyen en coordonnées.

## Pourquoi ça ne transfère pas

Les 1100 clips d'entraînement sont un seul athlète, un seul décor, tous en 270×480. Le LSTM
mange les **coordonnées MoveNet brutes** normalisées dans le carré paddé, sans aucune
normalisation centrée sur le corps. Il a appris une position à l'image, pas une géométrie de
stance. Rien ne survit au changement de caméra.

Corollaire général : **écarter tout modèle appris sur coordonnées absolues.** Ce qui marche
sur `data/` ce sont des features invariantes — ratios, angles.

## La piste laissée ouverte

Hypothèse à tester un jour : n'appliquer ce modèle **que sur les clips dont la caméra est
dans la même configuration que leur tournage**, et abstenir ailleurs. Plutôt que de le juger
sur tout le jeu.

**Mais le critère évident est déjà éliminé.** Le format ne suffit pas : leurs 1100 clips sont
en 9:16, et les 42 clips de `data/` qui sont exactement en 9:16 donnent **24% (clip entier) /
33% (1re rep)** — pas mieux que l'ensemble. Un retest doit donc se déclencher sur quelque
chose de plus fin que le ratio d'image :

- vue strictement de profil (leur consigne de tournage), pas 3/4
- hauteur et distance de caméra proches des leurs
- cadrage : corps entier occupant la même fraction de l'image

Mesurer ces trois-là sur leurs `Raw MP4 Videos/` pour en tirer une enveloppe, puis ne juger
que les clips de `data/` qui tombent dedans. Si moins de ~5 clips passent le filtre, le test
ne conclura rien — le vérifier avant de relancer 25 minutes d'extraction de pose.

## Deux bugs de leur code, à ne pas redécouvrir

1. **`app.py` publié est incohérent sur la région de crop.** Il passe les dimensions de la
   frame brute à `init_crop_region` / `determine_crop_region` alors que l'image croppée est
   le carré paddé 256×256. Leurs tableaux ne se reproduisent qu'avec les dimensions du carré
   (coord MAE 0.0002 contre 0.005). Avec la version publiée : 2/6 sur leurs propres données.
2. **`singlepose_lightning_tflite_f16.tflite` et `singlepose_thunder_tflite_f16.tflite` sont
   le même fichier** (md5 identique). C'est thunder, entrée 256.

Et une fragilité du modèle : il est très sensible à la fenêtre temporelle. La fenêtre brute
de leur détecteur de rep tronque la redescente finale et fait chuter **leur propre jeu de
99.6% à 34%** (tout devient « Romanian »). Il faut l'étendre de 30% — d'où `EXTEND = 0.30`.

## Le code

Sur la branche **`perf/movenet-lstm-deadlift`** (poussée sur `origin`), volontairement pas
sur `main` ni sur les branches MediaPipe :

- `pose_movenet/batch_predict.py` — le portage. `app.py` est une boucle webcam interactive
  (`VideoCapture(0)` + touche `P`) ; ici on lit des mp4, on segmente toutes les reps du clip,
  on prédit sur chacune. Gère le flag de rotation mp4 que `cv2` ignore (parseur `tkhd` repris
  de `pose_mediapipe/evaluate_new.py`). Les deux correctifs ci-dessus sont commentés dedans.
- `pose_movenet/score.py` — confrontation à `backend/eval/ground_truth.json`.

```bash
git checkout perf/movenet-lstm-deadlift
DLC_REPO=/home/erwan/deadlift-classifier /home/erwan/dlc-venv/bin/python \
  pose_movenet/batch_predict.py data/*.mp4 --out /tmp/res.json --dump-kps /tmp/kps
python3 pose_movenet/score.py /tmp/res.json backend/eval/ground_truth.json
```

## Environnement (WSL)

- Repo cloné dans `/home/erwan/deadlift-classifier`, venv dans `/home/erwan/dlc-venv`.
- **Pas dans `/tmp`** : c'est un tmpfs de 3.9G, l'install de TensorFlow le sature
  (`OSError: No space left on device`). **Pas sur `/mnt/c`** non plus. `/` a ~950G.
- Python 3.11 + `tensorflow==2.15.1` (keras 2.15) charge sans problème leurs `.keras`
  sauvés en HDF5 avec keras 2.10, malgré le README qui réclame Python 3.9 / TF 2.10.
  Il faut aussi `opencv-python-headless`, `numpy<2` et `matplotlib` (importé par `utils.py`).
- ~25 min pour extraire la pose des 47 clips sur CPU. `--dump-kps` évite de refaire ce
  passage : les tableaux permettent de rejouer n'importe quelle stratégie de segmentation.
- La clé API Gemini de `app.py` n'est pas nécessaire — le portage ne fait que la
  classification, pas le retour en langage naturel.
