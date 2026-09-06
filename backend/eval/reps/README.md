# Compter les répétitions avec MediaPipe — ce que ça vaut

**Verdict : pas assez fiable pour afficher un nombre de reps. 58 % de comptes exacts sur les
48 clips de deadlift de `data/`, 96 % à ±1 rep.** En revanche c'est un bon *détecteur* :
91 % des reps réelles sont trouvées au bon moment (±1,5 s), avec 20 % de fausses détections.
Si le besoin est de découper la vidéo en répétitions plutôt que d'annoncer « 5 reps », ça marche.

## La vérité terrain

Les 49 clips de `data/` comptés **à l'œil par Erwan**, sur la vidéo, dans l'outil de notation
(`eval/scorer/server.py`, bloc « Répétitions ») → `verite_terrain.json`, clé `n`,
`source: "humain"`. 149 reps.

Un clip est marqué `ambigu` : `arthur_froler_fesse`, où le lifter se relève en cours de série
sans reprendre la barre — la frontière entre une répétition et une pause debout n'y est pas
tranchable à l'image, ni par un humain ni par la pose. Il **reste dans le calcul** (les vraies
vidéos ressemblent à ça), et `compare.py` affiche systématiquement le score sans lui : l'écart
est de 1 point d'exactitude, il ne porte aucune conclusion.

Mon propre comptage préalable, fait sur des planches de frames, est conservé sous `claude_n` :
**43/49 justes, 6 erreurs, dans les deux sens** (−1 à +2). Une planche à 0,75 s rate les
verrouillages brefs, et surtout elle ne permet pas de voir si la barre est en main : deux de mes
erreurs sont des tirées jamais effectuées que j'ai comptées comme des reps.

## Les chiffres

| signal | exact | à ±1 rep | erreur abs. moyenne | biais |
|---|---|---|---|---|
| `ext`  angles hanche+genou | 28/48 (58 %) | 45/48 (94 %) | 0,50 | +0,25 |
| `wri`  hauteur des poignets | 26/48 (54 %) | 45/48 (94 %) | 0,56 | +0,48 |
| `post` (genou−épaule)/tronc | 24/48 (50 %) | 40/48 (83 %) | 0,79 | +0,21 |
| `hip`  hauteur des hanches | 19/48 (40 %) | 41/48 (85 %) | 0,83 | +0,25 |
| **`med` médiane des quatre** | **28/48 (58 %)** | **46/48 (96 %)** | **0,46** | **+0,17** |

Le biais est positif partout : **le compteur ajoute des reps, il n'en rate presque pas.**

Les singles ne sont pas plus faciles que les séries (62 % contre 61 %) : l'erreur ne vient pas
de la longueur de la série mais de ce qu'il y a autour de la tirée.

## Pourquoi ça se trompe

1. **Se redresser sans la barre est indiscernable d'une rep.** Le corps fait exactement le même
   cycle bas → haut. Les deux cas les plus nets sont des tirées **jamais effectuées** :
   `engueran_fail_deadlift` (la barre ne décolle pas, il se relève à vide) et `sumo_deadlift`
   (le carton dit que la ceinture a lâché *avant* la tentative). Vérité 0 rep, MediaPipe en
   compte 1 sur les deux — et moi aussi, sur planches de frames.
   **Sans suivre la barre, aucune règle de pose ne tranche ça.** Même chose, en moins spectaculaire,
   quand le lifter repose la barre en fin de série puis se redresse.
2. **Les poignets cachés derrière un disque.** MediaPipe invente alors leur position et le
   signal saute. Sur `conventionnal_deadlift_13` (cadrage serré), le signal poignet compte un
   même verrouillage tenu trois secondes deux fois, quatre fois de suite : 11 pour 7. C'est le
   défaut que le consensus `med` rattrape le mieux — il rend 7.
3. **L'installation ressemble à une rep.** Se pencher pour saisir la barre, se relever,
   se repencher.
4. **Les plans de coupe.** `jeff_nippard_sumo` coupe sur un plateau où quelqu'un est debout :
   une rep de plus.

## Ce qui a été essayé et écarté

* **Seuils absolus en degrés** (verrouillage = hanche et genou tendus, `--signal abs`) :
  43 % d'exacts, erreur moyenne 1,06 — nettement pire. Les angles articulaires mesurés à
  l'image ne veulent rien dire hors vue de profil, ce que la skill `sumo-stance-mediapipe`
  et les mesures de `eval/pose_model/` disaient déjà. Ne pas y revenir sans vue de profil.
* **Anti-rebond** (exiger deux frames consécutives sous le seuil bas avant de réarmer) :
  aucun effet. Les décrochages de suivi durent plus de deux frames.
* **Repasser la pose à pleine cadence** (`--fps 0`, toutes les frames, le mode pour lequel le
  `running_mode=VIDEO` de MediaPipe est fait). Pilote sur 5 clips — quatre échecs connus et un
  témoin — après avoir mis les constantes du compteur en **secondes**, pour que changer la
  cadence ne change que la pose et pas la nervosité du filtre :
  - le bruit de suivi s'effondre **sur un clip sur cinq** (`sumo_deadlift_4` : écart-type de
    l'extension sur corps immobile 32,0° → 3,9°). Le contrôle par décimation — reprendre le
    signal pleine cadence et n'en garder qu'un point sur cinq — donne 4,1° : **c'est bien le
    suivi qui s'améliore, pas un artefact du nombre de points.** Sur les quatre autres clips,
    le bruit ne bouge pas.
  - **mais le comptage ne s'améliore pas** : consensus exact 2/5 dans les deux cas. Deux clips
    sont réparés (`conventionnal_deadlift_14` 2→3, `sumo_deadlift_4` 6→5), deux sont cassés
    (`conventionnal_deadlift_13` 7→8, `conventionnal_deadlift_2` 2→3).
  - à noter quand même : le double comptage du signal poignet sur `conventionnal_deadlift_13`
    (11 pour 7) **disparaît** à pleine cadence — il rend 7. C'était donc bien en partie un
    artefact du sous-échantillonnage.

  Coût ×5 (≈2 s de calcul par seconde de vidéo contre 0,4 s). L'échantillon était **choisi pour
  favoriser l'hypothèse** — quatre échecs suspectés de tremblement — et elle n'a quand même rien
  rapporté en exactitude. Ne pas repasser les 49 clips sans une raison nouvelle.
* **Hauteur des hanches brute** : le plus mauvais des quatre signaux. Un panoramique ou un
  zoom déplace la hanche dans l'image autant qu'une répétition.

## Une piste non mesurée

Quand les quatre signaux s'écartent de plus d'une rep entre eux, le suivi a décroché et le
compte ne vaut rien : ça donnerait un « je ne sais pas » plutôt qu'un chiffre faux. Testable
sur les 49 clips avec les comptes déjà en cache.

## Rejouer

```bash
cd backend
uv run python eval/reps/dump_signal.py --fps 6     # ~12 min, ecrit signaux.json (1,3 Mo)
uv run python eval/reps/compare.py --signal med    # confronte a verite_terrain.json
uv run python eval/reps/compte_reps.py --signal med --json
```

`signaux.json` est un cache : le comptage se met au point dessus sans repasser la pose.
`planches.py` régénère les planches de frames (`--debut/--fin/--pas 0.25` pour zoomer sur une
fenêtre litigieuse) — utiles pour instruire un désaccord, **pas** pour établir la vérité :
c'est en comptant dessus que je me suis trompé six fois.

## Si on veut vraiment un compte fiable

Les erreurs viennent en majorité de mouvements du corps **sans la barre**. Il faudrait donc la
barre : suivre le disque (un cercle sombre, très détectable) et n'accepter une rep que s'il
décolle vraiment du sol. C'est ce que le compteur de pose ne peut pas savoir, pas un réglage
de seuils.
