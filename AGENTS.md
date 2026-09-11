# 🏋️‍♂️ SBD Reviews - Documentation & Architecture

Ce document décrit le concept, l'architecture technique et les procédures de déploiement du projet **SBD Reviews**. Il est destiné aux développeurs et aux assistants IA pour comprendre rapidement la structure du projet.

---

## 🔄 Méthode de travail : rien n'est figé

Ce projet est en itération permanente. **Aucun choix décrit dans ce document n'est définitif** : architecture, prompts, schéma de notation, seuils de la cascade de pose, bloc de cinématique, modèle Gemini retenu, découpage des vidéos envoyées — tout est une version courante, pas une contrainte.

L'objectif est un produit **utile et de qualité**, pas la préservation de l'existant. Un assistant qui repère un choix discutable doit le dire et proposer mieux, y compris sur du code récent ou soigneusement réglé.

Nous sommes limités par le budget. Aujourd'hui on utilise les api de dev de google. On peut donc faire 500 apels de gemini-3.5 flash lite et 20 appels de gemini-3.5-flash normal.

Le modèle lite semble ne pas être de très bonne qualité et donc il faut prendre avec des pincettes les résultats actuel de benchmark.

L'approche actuelle consiste donc à identifier 2-3 vidéos et se concentrer dessus pendant l'ittération puis à élargir / tester les conclusions sur le reste.

Nous sommes dicter par le bon sens et la simplicité. Plus les choix sont obvious, moins on a besoin de les tester avec rigueur.

**Un clip qui résiste sert d'abord à éliminer, pas à conclure.** C'est vrai qu'un test réussi sur une seule vidéo ne prouve pas que le reste est corrigé — il faudra élargir. Mais s'il continue de ne pas marcher sur ce clip-là, alors le tester sur les autres cas n'aurait servi à rien : on aurait payé des appels pour confirmer un échec qu'on connaissait déjà.

Donc l'ordre est : on prend le cas le plus dur, on y élimine tout ce qui ne marche pas, et on n'élargit qu'à partir du moment où quelque chose bouge. Une variante qui ne déplace rien sur le clip difficile est abandonnée sans deuxième mesure.

La seule exception est le **garde-fou anti-sévérité** : dès qu'une variante rend le système plus critique, elle se remesure immédiatement sur un clip que l'humain juge bon, sinon on confond « mieux discriminer » et « taper plus fort sur tout le monde ».

## 💡 1. Concept du Projet
**SBD Reviews** est une application web d'analyse vidéo assistée par l'Intelligence Artificielle pour les mouvements de force athlétique (Squat, Bench, Deadlift). 

L'objectif ultime de l'application est d'aider les pratiquants intermédiaires à exploser leurs performances en peaufinant des détails techniques qui bloquent leur progression. Elle agit comme un véritable partenaire éducatif qui décode la biomécanique de leur corps, leur permettant de mieux comprendre le mouvement. L'expérience intègre une forte dose de fun qui fait passer un bon moment à l'utilisateur.

L'aspect suivi sur le long terme est encore en cours de réfléxion et à voir dans un lot 2.
---

## 🏗️ 2. Architecture Technique

Le projet est divisé en deux parties principales (Frontend et Backend), orchestrées par un Reverse Proxy (Caddy) et conteneurisées via Docker.

### 💻 Frontend (Client)
*   **Technologie :** React (via Vite)
*   **Styling :** Tailwind CSS
*   **Authentification :** Google OAuth 2.0 (`@react-oauth/google`)
*   **Rôle :** Interface utilisateur, gestion des uploads vidéo, affichage des résultats dynamiques.
*   **Port interne :** 80 (Nginx dans le conteneur)

### ⚙️ Backend (API)
*   **Technologie :** Python avec FastAPI (serveur Uvicorn)
*   **Gestionnaire de paquets :** `uv` (Astral)
*   **Rôle :** Traitement des vidéos, vérification des quotas utilisateurs, appel aux modèles d'IA (détection de mouvement, analyse biomécanique), et gestion des sessions via tokens.
*   **Port interne :** 8000

### 🛡️ Reverse Proxy (Caddy)
*   **Technologie :** Caddy Server (v2)
*   **Rôle :** 
    *   Gère le trafic entrant public sur les ports 80 (HTTP) et 443 (HTTPS).
    *   Génère et renouvelle automatiquement les certificats SSL (Let's Encrypt).
    *   Redirige le trafic racine `/` vers le Frontend.
    *   Redirige le trafic `/api/*` vers le Backend.

---

### 🎬 Pipeline d'analyse d'une vidéo

We try to be smart engineer on this project. For now we have trois tâches qui partent **en parallèle** dès l'upload (`ai_service.upload_and_detect_concurrent`) :

1. **Upload** du fichier vers l'API Gemini.
2. **Classification** de la famille du mouvement par le modèle (squat / bench / deadlift).
3. **Pose** (`pose_analysis.py`) — pour un deadlift, la variante sumo/conventionnel 
4. **Répétitions candidates** (`rep_detection.py`) — passe de pose dense, volontairement

Puis `analyze_movement` envoie la vidéo à Gemini. **Sur un deadlift avec des candidats**, elle
part en **mode segments** : un `Part` vidéo par répétition candidate, borné par
`start_offset`/`end_offset`, `media_resolution=HIGH`. Le modèle renseigne `bar_left_floor` pour chaque candidat, et le backend retire les
`false` avant toute notation — la pose voit le corps, pas la barre, et se redresser après
l'avoir reposée produit exactement le même mouvement qu'une répétition.


🚀 Déploiement et Commandes Utiles
sudo docker compose up -d --build


Dataset d'évaluation
Les personas positionnés par moi même ne sont pas très fiable pour le moment et positionné un peu rapidement. Ne tient pas trop rigueur à un modèle si il met le mauvais persona pour l'instant.

Comportement de l'agent
Fait preuve de pédagogie avec moi quand tu parles de biomécanique, d'angles, de secondes. Ne va pas dans explications trop compliquées qui partent dans tous les sens. Soit le plus clair et le plus simple possible.

Il faut toujours fabriquer le rendu de la pose avant de théoriser dessus
%

⚖️ 2. Règles Fondamentales (Le "Mindset" de l'Agent)
Règle 2.1 : Éradiquer les adjectifs subjectifs
le llm coach en biomécanique ne doit jamais utiliser ni se baser sur des mots qui nécessitent une interprétation humaine.

❌ Interdit : Léger, extrême, beaucoup, un peu, presque, trop, pas assez.
✅ Requis : Utiliser des repères fixes, des angles, des lignes ou des plans.
Exemple : Ne dis pas "le dos est un peu courbé", dis "l'alignement entre les lombaires et les thoraciques est brisé".
Règle 2.2 : Forcer des choix mutuellement exclusifs
Lorsqu'une question est posée à l'Agent coach en biomécanique, les options proposées ne doivent laisser aucune place à l'hésitation. Les catégories doivent couvrir 100% des cas de figure sans se chevaucher. L'Agent doit choisir une catégorie. Pas de réponse "entre les deux".

⚠️ Règle 2.2 : Le piège des mots d'intensité (Bannir les "extrêmes")
L'Agent et le système d'évaluation ne doivent jamais utiliser d'adverbes d'intensité ou de gradation, tels que : extrêmement, excessivement, totalement, fortement, légèrement, brutalement.

Le problème de ces mots : Ils créent un seuil subjectif invisible. L'IA (ou l'évaluateur) ne sait pas mathématiquement où commence l' "extrême". Face à une position qui est visiblement basse, mais peut-être pas extrêmement basse, l'Agent va hésiter. Pour ne pas prendre de risque, il va se rabattre sur une mauvaise catégorie (le choix par défaut), faussant ainsi toute l'analyse.
La règle de substitution : Toute notion d'intensité doit être remplacée par une frontière géométrique ou chronologique binaire (ça coupe une ligne ou ça ne la coupe pas).


Eviter le piège du "Ventre Mou" (ou de la zone de confort).

Vous avez parfaitement compris comment le modèle "triche" :

L'option 1 est un point exact (le plan du genou).
L'option 3 est un point exact (le plan de l'épaule).
L'option 2 est une zone gigantesque (tout l'espace entre les deux).
Mathématiquement, le modèle a 95% de chances de tomber dans la zone 2. S'il voit un bassin beaucoup trop bas, mais qu'il est 3 centimètres au-dessus du genou, il n'osera pas choisir l'option 1 car elle est trop extrême ("exactly on the same plane"). Il se réfugiera dans l'option 2, et validera à tort un mauvais mouvement.

Zéro "ventre mou" : L'IA est obligée de trancher, les options couvrent 100% de la physique, sans zone de confort.
Hard Boundaries (Lignes rouges) : Les notes (1, 2, 3) sont déclenchées par le franchissement d'un repère physique précis, pas par une appréciation subjective.
Résilience 3D (Topologie & Gravité) : Les consignes utilisent des repères universels (lacets, fémur, verticalité sous gravité, occlusions) qui fonctionnent aussi bien sur une vidéo de strict profil (2D) que sur un angle de 3/4 face