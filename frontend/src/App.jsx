import { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import Header from './components/Header.jsx';
import Tabs from './components/Tabs.jsx';
import UploadZone from './components/UploadZone.jsx';
import ResultCard from './components/ResultCard.jsx';
import LoadingProgress from './components/LoadingProgress.jsx';

// IMPORT DES IMAGES (Assure-toi qu'elles sont bien dans src/images/)
import badLegDrive from './images/bad-leg-drive.png';
import goodLegDrive from './images/good-leg-drive.png';

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [activeTab, setActiveTab] = useState('squat');
  const [expandedCard, setExpandedCard] = useState(null);

  // --- NOUVEAUX ÉTATS POUR L'AUTHENTIFICATION ---
  const [tokenAPI, setTokenAPI] = useState(null); 
  const [user, setUser] = useState(null); 

  // --- DICTIONNAIRE DES DÉMOS CORRIGÉ ---
  const demoAnimations = {
    hauteur_stabilite_hanches: "https://media.giphy.com/media/3o7TKnPOnEbGOXwQOQ/giphy.gif",
    
    poussee_active_jambes: {
      bad: {
        title: "L'erreur fréquente (Le mauvais \"Leg Drive\")",
        image: badLegDrive, 
        description: "Sur cette image, le pratiquant tend les jambes trop tôt. Résultat, son bassin monte au plafond alors que la barre n'a pas encore décollé du sol.",
        problem: "Comme les jambes sont déjà tendues, elles ne peuvent plus aider à soulever le poids. Tout l'effort se reporte violemment sur le bas du dos et l'arrière des cuisses (la zone en rouge vif). C'est le meilleur moyen de se blesser aux lombaires, car on \"tire\" la barre avec le dos au lieu d'utiliser ses jambes."
      },
      good: {
        title: "La posture idéale (Le bon \"Leg Drive\")",
        image: goodLegDrive, 
        description: "Ici, la posture est corrigée. Le bassin est plus bas, les genoux sont pliés et le buste est fier. Les cuisses et les fessiers (en bleu) sont activés et prêts à faire le gros du travail. Le dos est protégé.",
        tip: "Regardez les flèches vertes ! Pour bien soulever la barre, il ne faut pas penser à la \"tirer\" vers le haut. Il faut imaginer que l'on pousse le sol très fort vers le bas avec ses pieds (comme sur une presse à cuisses), tout en redressant le buste vers le haut. C'est ça, un bon leg drive !"
      }
    }
  };

  // --- FONCTION DE CONNEXION GOOGLE ---
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const res = await fetch('http://localhost:8000/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credentialResponse.credential })
      });
      
      const data = await res.json();
      if (res.ok) {
        setTokenAPI(data.access_token);
        setUser(data.user); 
      } else {
        alert("Erreur d'authentification : " + data.detail);
      }
    } catch (error) {
      console.error("Erreur de connexion", error);
    }
  };

  // --- FONCTION D'UPLOAD SÉCURISÉE ---
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    if (!tokenAPI) {
      alert("Vous devez être connecté pour analyser une vidéo.");
      return;
    }

    setLoadingStep(1);
    setResult(null);
    setExpandedCard(null);

    try {
      const formData = new FormData();
      formData.append('video', file);

      // ÉTAPE 1 : DÉTECTION (AVEC LE TOKEN)
      const detectResponse = await fetch('http://localhost:8000/detect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokenAPI}` // 🔐 Sécurité ajoutée ici !
        },
        body: formData,
      });
      const detectData = await detectResponse.json();

      if (!detectResponse.ok) throw new Error(detectData.detail || "Erreur de détection");

      // Mise à jour du quota restant
      if (detectData.quota_restant !== undefined) {
        setUser(prev => ({ ...prev, quota_left: detectData.quota_restant }));
      }

      setActiveTab(detectData.mouvement_detecte);
      setLoadingStep(2);

      // ÉTAPE 2 : ANALYSE (AVEC LE TOKEN)
      const analyzeResponse = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenAPI}` // 🔐 Sécurité ajoutée ici !
        },
        body: JSON.stringify({
          file_name: detectData.file_name,
          movement: detectData.mouvement_detecte
        }),
      });
      
      const analyzeData = await analyzeResponse.json();
      if (!analyzeResponse.ok) throw new Error(analyzeData.detail || "Erreur lors de l'analyse");

      setResult(analyzeData);

    } catch (error) {
      alert(`Erreur ❌ : ${error.message}`);
    } finally {
      setLoadingStep(0);
    }
  };

  const noteSur20 = result ? Math.round((result.note_globale_brute / result.score_max_brut) * 20) : 0;

  // --- ÉCRAN DE CONNEXION (Si pas de token) ---
  if (!tokenAPI) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white gap-6">
        <h1 className="text-4xl font-black uppercase tracking-wider mb-2">SBD Reviews</h1>
        <p className="text-gray-400 mb-6 text-center max-w-md">
          Connecte-toi avec Google pour faire analyser tes mouvements par notre IA.
        </p>
        <GoogleLogin 
          onSuccess={handleGoogleSuccess} 
          onError={() => alert('La connexion a échoué')}
          theme="filled_black"
          shape="pill"
        />
      </div>
    );
  }

  // --- ÉCRAN PRINCIPAL DE L'APP ---
  return (
    <div className="max-w-4xl mx-auto p-6 pt-12 pb-24 text-white">
      <Header />

      {/* BANDEAU UTILISATEUR & QUOTAS */}
      <div className="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-8 flex flex-col md:flex-row justify-between items-center shadow-lg">
        <div className="flex items-center gap-2 mb-2 md:mb-0">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-sm text-gray-400">
            Connecté : <span className="font-bold text-white">{user?.email}</span>
          </span>
        </div>
        <div className="flex gap-4">
          <span className="bg-gray-800 text-xs px-3 py-1.5 rounded-full uppercase tracking-wider font-bold">
            Plan {user?.plan}
          </span>
          <span className={`text-xs px-3 py-1.5 rounded-full uppercase tracking-wider font-bold ${user?.quota_left > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'}`}>
            Analyses restantes : {user?.quota_left}
          </span>
        </div>
      </div>
      
      <Tabs activeTab={activeTab} setActiveTab={setActiveTab} disabled={!!result || loadingStep > 0} />

      {loadingStep === 0 && !result && (
        <UploadZone file={file} setFile={setFile} handleUpload={handleUpload} />
      )}

      {loadingStep > 0 && (
        <LoadingProgress step={loadingStep} />
      )}

      {result && loadingStep === 0 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex flex-col items-center justify-center p-10 bg-gray-900 border border-gray-800 rounded-3xl shadow-lg">
            <span className="text-gray-400 font-semibold mb-2 uppercase tracking-widest text-sm">
              Score Technique {result.mouvement_detecte}
            </span>
            <div className="flex items-baseline gap-2">
              <span className={`text-7xl font-black ${noteSur20 >= 16 ? 'text-emerald-400' : noteSur20 >= 10 ? 'text-amber-400' : 'text-red-400'}`}>
                {noteSur20}
              </span>
              <span className="text-4xl text-gray-600 font-bold">/ 20</span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {Object.entries(result).map(([key, data]) => {
              if (key === 'note_globale_brute' || key === 'score_max_brut' || key === 'mouvement_detecte' || key === 'quota_restant') return null;
              return (
                <ResultCard
                  key={key} 
                  criterionKey={key} 
                  data={data}
                  isExpanded={expandedCard === key}
                  onToggle={() => setExpandedCard(expandedCard === key ? null : key)}
                  demo={demoAnimations[key]} 
                />
              );
            })}
          </div>

          <button
            onClick={() => {setResult(null); setFile(null); setExpandedCard(null);}}
            className="w-full mt-8 bg-gray-800 hover:bg-gray-700 text-white font-bold py-4 px-8 rounded-xl transition-all uppercase tracking-wider text-sm"
          >
            Analyser une autre vidéo
          </button>
        </div>
      )}
    </div>
  );
}