---
name: lift-video-labeling
description: L'outil d'annotation humaine du projet (backend/eval/scorer) — ce qu'on y annote, comment les instants de répétition (`verrous`) y sont marqués, et les pièges qui fabriquent de fausses données. À charger avant de toucher à eval/scorer/, à verite_terrain.json, à human_labels.json, ou avant de proposer une nouvelle campagne d'annotation.
---

# Annoter les vidéos à la main

## L'outil

`backend/eval/scorer/` — un serveur HTTP minimal plus une page unique.

```bash
cd backend && uv run python eval/scorer/server.py     # http://localhost:8800
```

Depuis Windows via WSL, remplacer `localhost` par la sortie de `hostname -I`.

C'est **la seule page du projet qui montre la vidéo**. Toute annotation doit s'y faire :
compter ou dater des reps sur des planches de frames s'est trompé 6 fois sur 49.

## Ce qui s'y annote, et où ça atterrit

| Dans la page | Fichier | Clé |
|---|---|---|
| Notes par critère, persona, commentaire | `eval/scorer/human_labels.json` | `scores`, `persona` |
| Nombre de répétitions | `eval/reps/verite_terrain.json` | `n` + `source: humain` |
| **Instants de verrouillage** | `eval/reps/verite_terrain.json` | `verrous` |

Le comptage préalable de Claude est conservé sous `claude_n`, jamais écrasé : c'est ce qui
permet de mesurer après coup de combien je me suis trompé (43/49 justes).

## Les instants (`verrous`) — pourquoi ils existent

Ajoutés le 2026-09-08. **Un compte ne dit pas OÙ**, et deux mesures ont conclu de travers
faute de cette information : sur `conventionnal_deadlift_14`, trois candidats de pose pour
trois vraies reps donnaient une couverture « parfaite » alors qu'un seul candidat était réel.

Avec les instants, on mesure enfin le vrai rappel du détecteur et la justesse de
`pose_analysis._phases`. Voir la skill `comptage-reps`.

```
m   marque le verrouillage à l'instant courant de la vidéo
u   retire le dernier repère
```

**Le verrouillage et non le décollage**, délibérément : l'athlète debout est net à l'œil,
alors que l'instant où la barre quitte le sol se joue à deux dixièmes près. Une vérité
terrain floue ne sert à rien, et un repère par rep au lieu de deux divise le travail par deux.

`n` reste la référence et **n'est jamais diminué tout seul** : un marquage interrompu ne peut
pas effacer un comptage fait avec soin. Il monte en revanche pour suivre les repères.

## Pièges payés cash

1. **Un outil d'annotation peut fabriquer de fausses données.** `poitrine_relevee` est apparu
   dans les clips fautifs avec 1 rep couverte sur 3 ; ses instants annotés étaient
   `[0.02, 0.12, 1.74]` alors que les reps culminent vers 2,2 / 6,2 / 10,2 s. Le détecteur
   avait bon. Deux causes, toutes deux dans l'outil : la vidéo est en `autoplay loop` (appuyer
   sur `m` avant de l'avoir amenée sur la bonne image enregistre ≈0), et le garde-fou
   anti-doublon comparait au **dernier** élément d'une liste que la fonction venait de trier,
   donc jamais au repère qu'on venait de poser.
   **Corrigé** : marques sous 0,3 s refusées, doublon cherché sur le repère le plus proche,
   seuil à 1 s (`PERIODE_MIN` du détecteur).
2. **Toujours valider la vraisemblance physique d'une annotation avant de s'en servir.**
   Deux verrouillages à moins d'une seconde, ou un repère à t≈0, sont des artefacts.
   Le balayage tient en cinq lignes de Python et évite d'accuser le code à tort.
3. **Le navigateur garde l'ancien JavaScript.** Après une modification de `ui.html`, une page
   déjà ouverte continue de tourner sur l'ancienne version — un correctif de l'outil peut
   sembler sans effet. Recharger (Ctrl+Shift+R).
4. **Ne jamais écrire dans la vérité terrain à la place de l'humain.** Mes propres lectures
   d'images, même justes à deux dixièmes près, n'ont rien à y faire : elles vont sous
   `claude_n` ou nulle part. C'est ce qui permet de mesurer mon écart.

## Ce que la page lit du catalogue

Depuis le refacto, `criteres_du_schema` et `personas_du_schema` lisent `indicators.py` et non
plus un schéma Pydantic. Effet heureux : **les niveaux affichés à l'annotateur sont exactement
les états observables qui serviront à noter le clip**. L'humain et le système lisent le même
texte — si une formulation est mauvaise, ça se voit en annotant.
