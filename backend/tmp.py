import os
from google import genai
os.environ["GEMINI_API_KEY"]="AIzaSyC225bzxD83AI_TCm-_pfglpEJ_5yW9ZW4"
def test_connexion():
    print("🔄 Initialisation du client Gemini...")
    
    # 1. Le client lit automatiquement la variable GEMINI_API_KEY
    try:
        client = genai.Client()
    except Exception as e:
        print(f"❌ Erreur d'initialisation (Clé API manquante ?) : {e}")
        return

    prompt = "Réponds uniquement par 'Coucou ! Le monde de l'IA fonctionne parfaitement !'"
    print(f"💬 Envoi du prompt à Gemini...")

    # 2. Appel basique (pas de vidéo, juste du texte)
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash", 
            contents=prompt
        )
        
        print("\n" + "="*30)
        print("🤖 RÉPONSE DE GEMINI :")
        print("="*30)
        print(response.text.strip())
        print("="*30)
        print("✅ Test réussi avec succès !\n")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'appel à l'API : {e}")

if __name__ == "__main__":
    test_connexion()