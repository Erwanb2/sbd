import { useState } from 'react';
import Header from './components/Header.jsx';
import Tabs from './components/Tabs.jsx';
import UploadZone from './components/UploadZone.jsx';
import ResultCard from './components/ResultCard.jsx';
import LoadingProgress from './components/LoadingProgress.jsx'; // NOUVEAU

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  
  // NOUVEAU: 0 = Repo, 1 = Détection, 2 = Analyse
  const [loadingStep, setLoadingStep] = useState(0); 
  
  const [activeTab, setActiveTab] = useState('squat');
  const [expandedCard, setExpandedCard] = useState(null);

  const demoAnimations = {
    hauteur_stabilite_hanches: "https://media.giphy.com/media/v1/giphy.gif",
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoadingStep(1); // Démarrage: Étape Détection
    setResult(null);
    setExpandedCard(null);

    try {
      // ----------------------------------------------------
      // ÉTAPE 1 : DÉTECTION (Upload + Triage)
      // ----------------------------------------------------
      const formData = new FormData();
      formData.append('video', file);

      const detectResponse = await fetch('http://localhost:8000/detect', {
        method: 'POST',
        body: formData,
      });
      const detectData = await detectResponse.json();

      if (!detectResponse.ok) throw new Error(detectData.detail || "Erreur de détection");

      // Super effet UX : l'onglet change tout seul sous les yeux de l'utilisateur !
      setActiveTab(detectData.mouvement_detecte);
      setLoadingStep(2); // Passage à l'étape Analyse

      // ----------------------------------------------------
      // ÉTAPE 2 : ANALYSE (Avec le fichier déjà uploadé)
      // ----------------------------------------------------
      const analyzeResponse = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      setLoadingStep(0); // Fin du chargement
    }
  };

  const noteSur20 = result ? Math.round((result.note_globale_brute / result.score_max_brut) * 20) : 0;

  return (
    <div className="max-w-4xl mx-auto p-6 pt-12 pb-24 text-white">
      <Header />
      
      <Tabs activeTab={activeTab} setActiveTab={setActiveTab} disabled={!!result || loadingStep > 0} />

      {/* ZONE D'UPLOAD */}
      {loadingStep === 0 && !result && (
        <UploadZone file={file} setFile={setFile} handleUpload={handleUpload} />
      )}

      {/* BARRE DE CHARGEMENT ANIMÉE EN 2 ÉTAPES */}
      {loadingStep > 0 && (
        <LoadingProgress step={loadingStep} />
      )}

      {/* RÉSULTATS */}
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
              if (key === 'note_globale_brute' || key === 'score_max_brut' || key === 'mouvement_detecte') return null;
              return (
                <ResultCard 
                  key={key} criterionKey={key} data={data} 
                  isExpanded={expandedCard === key} 
                  onToggle={() => setExpandedCard(expandedCard === key ? null : key)}
                  demoUrl={demoAnimations[key]}
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