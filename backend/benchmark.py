import json
import logging
import os
import time
import pandas as pd
from google import genai
from google.genai import types
from schemas import schema_mapping

client = genai.Client()
logger = logging.getLogger(__name__)

# Liste des critères du schéma Deadlift
CRITERES_DEADLIFT = [
    "starting_position",
    "slack_pull_and_lat_engagement",
    "leg_drive_activation",
    "hip_hinge_mechanics",
    "core_bracing_and_spine_neutrality",
    "bar_path_and_proximity",
    "lockout_execution",
    "eccentric_control_and_descent",
]

# ==============================================================================
# 1. FONCTIONS DÉDIÉES AU BENCHMARK (Upload & Analyse)
# ==============================================================================

def upload_video(file_path: str):
    """Upload du fichier chez Google (Attente active de la fin du processing)."""
    video_file = client.files.upload(file=file_path)

    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        client.files.delete(name=video_file.name)
        raise ValueError("L'analyse de la vidéo a échoué côté Google.")

    return video_file


def analyze_movement_with_model(file_name: str, model_name: str, max_retries: int = 20) -> dict:
    """Analyse un Deadlift Conventionnel avec le modèle spécifié avec 5 retries."""
    mouvement_detecte = "Conventional deadlift"

    chosen_schema = schema_mapping.get(mouvement_detecte)
    if not chosen_schema:
        raise ValueError(
            f"Type de mouvement '{ mouvement_detecte }' non reconnu dans schema_mapping."
        )

    prompt_analyse = f"""
    You are a brutally strict, elite IPF powerlifting judge and highly analytical biomechanics coach. 
    The athlete executes a CONVENTIONAL { mouvement_detecte.upper() }.
    
    GRADING RULE: 
      1. Assume the default score is 1 (Poor)
      2. A Score: An integer from 1 to 4, based strictly on the provided rubrics.
      3. A Brief Explanation: A concise 1-2 sentence justification explaining EXACTLY what visual evidence led to this score.

    CRITICAL VISIBILITY RULE (The "NA" Rule): 
    If the camera angle, framing, lighting, or video quality makes it impossible to accurately assess a specific body part or phase of the lift (e.g., the lifter's feet are out of frame, making 'Starting Position' impossible to judge), you MUST output "NA" for the score. Do not guess. In the explanation, state exactly why it cannot be scored (e.g., "NA - Lower legs and feet are out of frame, cannot evaluate bar proximity").

    At the end of your analysis, calculate the AVERAGE SCORE of the lift based only on the criteria that received a numerical score (exclude "NA" from the math).

    Output your analysis in the following structured format:

    1. Starting Position
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on mid-foot placement, hip height, and scapula position]

    2. Slack Pull and Lat Engagement
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on upper back tension and pre-lift tightness]

    3. Leg Drive Activation
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on hip rise and quad usage off the floor]

    4. Hip Hinge Mechanics
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on posterior chain tension and joint synchronization]

    5. Core Bracing and Spine Neutrality
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on lumbar/thoracic rounding and brace]

    6. Bar Path and Proximity
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on how close the bar stays to the shins/thighs]

    7. Lockout Execution
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on hip/knee extension and posture at the top]

    8. Eccentric Control and Descent
    - Score: [1, 2, 3, 4, or NA]
    - Explanation: [Briefly explain the score based on how the weight is lowered]

    LIFTER PERSONA CLASSIFICATION
    Based on your analysis, assign exactly ONE fun 'lifter_persona'. 
    
    - 'The Technician': Form is perfect.
    - 'The Crane': Hips shoot up early.
    - 'The Squatter': Hips are way too low. 
    - 'The Fishing Rod': Visible back rounding. 
    - 'The Hitcher': Bar rests on thighs. 
    - 'The Over-Extender': Leans backward at lockout. 
    - 'The Grip & Rip': Rushes setup.
    
    Provide a fun, engaging 'persona_justification'.
    """

    for attempt in range(1, max_retries + 1):
        try:
            video_file = client.files.get(name=file_name)

            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=chosen_schema,
                    temperature=0.0,
                ),
            )

            reponse_analyse = chat.send_message([video_file, prompt_analyse])
            resultat = json.loads(reponse_analyse.text)

            # --- GESTION DES NOTES (Brute sur 4 + Scalée sur 3) ---
            for critere_key in CRITERES_DEADLIFT:
                critere = resultat.get(critere_key)
                if isinstance(critere, dict) and "score" in critere:
                    raw_score = critere["score"]
                    critere["raw_score_4"] = raw_score

                    if isinstance(raw_score, (int, float)):
                        if raw_score <= 2:
                            critere["score_3"] = 1
                        elif raw_score == 3:
                            critere["score_3"] = 2
                        elif raw_score >= 4:
                            critere["score_3"] = 3
                    else:
                        critere["score_3"] = "NA"

            # --- CALCUL DU SCORE GLOBAL SUR 3 (en ignorant les "NA") ---
            scores_numeriques = [
                critere["score_3"]
                for k in CRITERES_DEADLIFT
                if (critere := resultat.get(k))
                and isinstance(critere, dict)
                and isinstance(critere.get("score_3"), int)
            ]

            resultat["total_score_3"] = sum(scores_numeriques)
            resultat["max_score_3"] = len(scores_numeriques) * 3
            resultat["movement_detected"] = mouvement_detecte

            return resultat

        except Exception as e:
            logger.warning(
                f"[Tentative { attempt }/{ max_retries }] Échec avec le modèle { model_name } : { e }"
            )
            if attempt == max_retries:
                logger.error(
                    f"Échec définitif pour le modèle { model_name } après { max_retries } tentatives : { e }"
                )
                return None
            time.sleep(2 * attempt)


# ==============================================================================
# 2. SCRIPT D'ORCHESTRATION DU BENCHMARK
# ==============================================================================

def run_benchmark():
    videos_paths = [
        "/mnt/c/Users/erwan/Documents/dev_projects/sbd/data/erwan_mauvais_slack.mp4",
        "/mnt/c/Users/erwan/Documents/dev_projects/sbd/data/p_deadlift.mp4",
        "/mnt/c/Users/erwan/Documents/dev_projects/sbd/data/pas_poitrine_relevee.mp4",
        "/mnt/c/Users/erwan/Documents/dev_projects/sbd/data/poitrine_relevee.mp4",
        "/mnt/c/Users/erwan/Documents/dev_projects/sbd/data/pr_160.mp4",
    ]

    modeles = [
        # "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        # "gemini-3.7-flash",
    ]

    nombre_essais = 2
    resultats_totaux = []

    for i, path in enumerate(videos_paths):
        if not os.path.exists(path):
            print(f"⚠️ Fichier introuvable, ignoré : { path }")
            continue

        nom_fichier_local = os.path.basename(path)
        print(f"\n--- Traitement de la vidéo { i + 1 }/{ len(videos_paths) } : { nom_fichier_local } ---")

        google_file_name = None
        try:
            print("Upload de la vidéo en cours...")
            uploaded_file = upload_video(path)
            google_file_name = uploaded_file.name
            print("✅ Upload terminé. Mouvement forcé à : DEADLIFT (Conventional)")

            for modele in modeles:
                for essai in range(1, nombre_essais + 1):
                    print(f"  -> Analyse avec { modele } (Essai { essai }/{ nombre_essais })...")
                    analyse_result = analyze_movement_with_model(
                        google_file_name, modele, max_retries=5
                    )

                    if analyse_result:
                        row_data = {
                            "Fichier": nom_fichier_local,
                            "Modèle": modele,
                            "Essai": essai,
                            "Mouvement": analyse_result.get("movement_detected", "deadlift"),
                            "Score_Global_3": analyse_result.get("total_score_3"),
                            "Max_Global_3": analyse_result.get("max_score_3"),
                        }

                        # Extraction du Persona
                        persona = analyse_result.get("lifter_persona", "Non défini")
                        if isinstance(persona, dict):
                            persona = persona.get("persona", persona)
                        row_data["Persona"] = persona
                        row_data["Persona_Justification"] = analyse_result.get(
                            "persona_justification", ""
                        )

                        # Extraction EXPLICITE pour chacun des 8 critères
                        for critere_key in CRITERES_DEADLIFT:
                            data = analyse_result.get(critere_key, {})
                            if isinstance(data, dict):
                                row_data[f"{ critere_key }_note_4"] = data.get("raw_score_4", "NA")
                                row_data[f"{ critere_key }_note_3"] = data.get("score_3", "NA")
                                row_data[f"{ critere_key }_explanation"] = data.get("explanation", "")
                            else:
                                row_data[f"{ critere_key }_note_4"] = "NA"
                                row_data[f"{ critere_key }_note_3"] = "NA"
                                row_data[f"{ critere_key }_explanation"] = ""

                        resultats_totaux.append(row_data)
                    else:
                        print(f"  ❌ Échec de l'analyse avec { modele } pour l'essai { essai }.")

        except Exception as e:
            print(f"Erreur globale sur la vidéo { path } : { str(e) }")

        finally:
            try:
                if google_file_name:
                    client.files.delete(name=google_file_name)
                    print(f"🗑️ Fichier { google_file_name } supprimé des serveurs Google.")
            except Exception as e:
                print(f"Attention: Impossible de supprimer le fichier { google_file_name } - { str(e) }")

    # ==============================================================================
    # 3. AFFICHAGE DES RÉSULTATS ET EXPORT CSV
    # ==============================================================================
    if resultats_totaux:
        df = pd.DataFrame(resultats_totaux)

        nom_csv = "resultats_deadlift_benchmark.csv"
        df.to_csv(nom_csv, index=False, encoding="utf-8")

        print("\n" + "=" * 80)
        print(f"✅ EXPORT RÉUSSI : Les données ont été sauvegardées dans '{ nom_csv }'.")
        print("=" * 80)

        # Aperçu avec les notes brutes sur 4 de chaque critère
        colonnes_notes = [f"{ c }_note_4" for c in CRITERES_DEADLIFT]
        colonnes_a_afficher = ["Fichier", "Modèle", "Essai", "Score_Global_3", "Persona"] + colonnes_notes[:4]

        print("\nAPERÇU DES RÉSULTATS :")
        pd.set_option("display.max_rows", None)
        pd.set_option("display.width", 1000)
        print(df[colonnes_a_afficher].head(15))
    else:
        print("\nAucun résultat n'a pu être généré.")


if __name__ == "__main__":
    run_benchmark()