# 🏋️‍♂️ SBD Reviews - Documentation & Architecture

Ce document décrit le concept, l'architecture technique et les procédures de déploiement du projet **SBD Reviews**. Il est destiné aux développeurs et aux assistants IA pour comprendre rapidement la structure du projet.

---

## 🔄 Méthode de travail : rien n'est figé

Ce projet est en itération permanente. **Aucun choix décrit dans ce document n'est définitif** : architecture, prompts, schéma de notation, seuils de la cascade de pose, bloc de cinématique, modèle Gemini retenu, découpage des vidéos envoyées — tout est une version courante, pas une contrainte.

L'objectif est un produit **utile et de qualité**, pas la préservation de l'existant. Un assistant qui repère un choix discutable doit le dire et proposer mieux, y compris sur du code récent ou soigneusement réglé.

La contrepartie : on change sur **preuve**, pas sur intuition.
*   Les seuils de `backend/pose_analysis.py` se revérifient avec `uv run python eval/check_pose_cascade.py` (depuis `backend/`).
*   Les changements de prompt, de schéma ou de modèle se jugent contre `backend/eval/ground_truth.json` — paires contrôlées (`pair:chest`, `pair:slack`) et ancres (`top_anchor`, `bottom_anchor`) — jamais sur un ressenti après un ou deux essais.
*   Une modification non mesurable est une préférence, pas une amélioration : le dire honnêtement plutôt que de l'habiller.
*   **Le pipeline n'est pas reproductible, et le plancher de bruit est haut.** Deux passes de la même configuration sur les 49 clips (`temperature=0`) ne rendent que **77 % de cases identiques**, avec 6 points d'écart sur l'accord avec la vérité terrain et le même persona sur seulement 26 clips sur 48. `temperature=0` ne garantit pas le déterminisme. Conséquences pratiques : **aucun changement ne se juge sur une passe unique en dessous d'environ 10 points** — deux configurations différentes bougent moins que deux exécutions identiques ; et côté produit, un utilisateur qui relance la même vidéo voit environ **2 critères sur 8 changer**. Le remède connu est d'échantillonner trois fois et de prendre la médiane par critère, au prix de 3× les appels ; il n'a pas encore été mesuré ici.

*   **Les mesures sont faites sur `gemini-3.5-flash-lite`, qui est nettement moins capable que `gemini-3.5-flash`.** C'est le modèle sans contrainte de budget, donc celui sur lequel tournent les 49 clips — mais il ne faut pas surajuster le barème ou le prompt à ses faiblesses. Un texte réécrit jusqu'à ce que flash-lite le comprenne peut être appauvri pour un modèle plus fort. Règle : flash-lite sert à détecter une direction et à éliminer ce qui ne marche pas ; toute modification de barème ou de prompt retenue doit être revalidée sur flash avant d'être considérée comme acquise.

## 💡 1. Concept du Projet
**SBD Reviews** est une application web d'analyse vidéo assistée par l'Intelligence Artificielle pour les mouvements de force athlétique (Squat, Bench, Deadlift). 
L'utilisateur se connecte via Google, upload la vidéo de son mouvement, et l'IA analyse sa technique (posture, leg drive, stabilité, etc.) pour lui attribuer un score technique sur 20 avec des retours personnalisés. Le site est en anglais. 

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

Trois tâches partent **en parallèle** dès l'upload (`ai_service.upload_and_detect_concurrent`) :

1. **Upload** du fichier vers l'API Gemini.
2. **Classification** de la famille du mouvement par le modèle (squat / bench / deadlift).
3. **Pose** (`pose_analysis.py`) — pour un deadlift, la variante sumo/conventionnel vient
   d'une cascade locale, pas du modèle. **Ne pas toucher à son échantillonnage** (30 frames,
   horodatages réels) sans rejouer `uv run python eval/check_pose_cascade.py`.
4. **Répétitions candidates** (`rep_detection.py`) — passe de pose dense, volontairement
   séparée de la cascade pour ne pas la déséquilibrer.

Puis `analyze_movement` envoie la vidéo à Gemini. **Sur un deadlift avec des candidats**, elle
part en **mode segments** : un `Part` vidéo par répétition candidate, borné par
`start_offset`/`end_offset`, `media_resolution=HIGH`, budget de 300 images réparti sur les
segments. Le modèle renseigne `bar_left_floor` pour chaque candidat, et le backend retire les
`false` avant toute notation — la pose voit le corps, pas la barre, et se redresser après
l'avoir reposée produit exactement le même mouvement qu'une répétition.

Squat, bench, absence de candidats et **modèle de repli** gardent le chemin historique (vidéo
entière, le modèle compte lui-même les reps) : `flash-lite` ne sait pas suivre le protocole des
candidats, c'est mesuré.

Conséquences assumées : le coût d'une analyse est **environ ×4**, et une répétition que la pose
ne propose pas ne peut plus être rattrapée par le modèle. Les leviers de coût sont
`BUDGET_IMAGES` et `media_resolution`, en haut d'`ai_service.py`.

> Détails, chiffres et pièges : skill projet `.claude/skills/comptage-reps/`.

---

## 🗺️ 3. Schéma de Communication

```text
[Utilisateur] -> https://sbdreviews.com (Port 443) -> [ Serveur VPS OVH ]
                                                            |
                                                      [ Conteneur Caddy ]
                                                            |
                     +--------------------------------------+--------------------------------+
                     |                                                                       |
          (Si requête vers `/`)                                                (Si requête vers `/api/*`)
                     |                                                                       |
                     v                                                                       v
          [ Conteneur Frontend ]                                                  [ Conteneur Backend ]
          - Sert les fichiers React                                               - API FastAPI (:8000)
          - Gère l'UI client                                                      - Traite l'analyse vidéo
🔐 4. Configuration et Variables d'Environnement
Pour fonctionner, le projet nécessite deux fichiers .env distincts.

frontend/.env
Contient les clés publiques, notamment pour l'authentification Google :

VITE_GOOGLE_CLIENT_ID=votre_client_id_google.apps.googleusercontent.com
backend/.env
Contient les secrets de l'API, les clés d'IA (ex: OpenAI, clés propriétaires, etc.) et les variables de base de données :

# Exemple de variables attendues :
SECRET_KEY=votre_cle_secrete_backend
GOOGLE_CLIENT_ID=votre_client_id_google
# Autres variables (Base de données, API ML, etc.)
🚀 5. Déploiement et Commandes Utiles
Le projet est hébergé sur un VPS OVH (Ubuntu). Tout est géré via Docker Compose.

Démarrer le projet (Production)
À la racine du projet (là où se trouve le docker-compose.yml), lancer :

sudo docker compose up -d --build
(Le tag -d lance les conteneurs en arrière-plan, --build force la reconstruction des images).

Arrêter le projet
sudo docker compose down
Voir les logs (Débogage)
Pour voir les logs en temps réel de tous les conteneurs :

sudo docker compose logs -f
Pour voir les logs d'un conteneur spécifique (ex: backend) :

sudo docker compose logs -f backend
⚠️ 6. Points d'attention (Checklist de maintenance)
Google OAuth (invalid_request) : Si l'authentification Google échoue, vérifier la Console Google Cloud. Les URL https://sbdreviews.com et https://www.sbdreviews.com doivent être strictement déclarées dans les Origines JavaScript et les URI de redirection.
Renouvellement SSL : Il est entièrement géré par Caddy. Ne jamais lier les ports 80/443 directement au frontend/backend dans le docker-compose.yml, c'est le rôle exclusif de Caddy.
Appels API Frontend : Toutes les requêtes fetch() ou axios depuis React doivent pointer vers des chemins relatifs (ex: /api/detect, /api/auth/google) et non plus vers localhost, pour que Caddy puisse faire le routage correctement.