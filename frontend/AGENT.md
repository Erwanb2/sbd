# 🏋️‍♂️ SBD Reviews - Documentation & Architecture

Ce document décrit le concept, l'architecture technique et les procédures de déploiement du projet **SBD Reviews**. Il est destiné aux développeurs et aux assistants IA pour comprendre rapidement la structure du projet.

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