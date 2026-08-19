import { useState } from 'react';
import { Activity } from 'lucide-react';
import Header from './components/Headers';
import Tabs from './components/Tabs';
import UploadZone from './components/UploadZone';
import ResultCard from './components/ResultCard';

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  const [activeTab, setActiveTab] = useState('squat');
  const [expandedCard, setExpandedCard] = useState(null);

  // Configuration des URLs de démo
  const demoAnimations = {
    hauteur_stabilite_hanches: "https://media.giphy.com/media/v1/giphy.gif",
    // etc...
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setResult(null);
    setExpandedCard(null);

    const formData = new FormData();
    formData.append('video', file);

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || "Erreur lors de l'analyse");

      setActiveTab(data.mouvement_detecte);
      setResult(data);

    } catch (error) {
      alert(`Erreur ❌ : ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const noteSur20 = result ? Math.round((result.note_globale_brute / 18) * 20) : 0;

  return (
    <div className="max-w-4xl mx-auto p-6 pt-12 pb-24 text-white">
      
      <Header />
      
      <Tabs 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        disabled={!!result} 
      />

      {/* ETAT 1 : UPLOAD */}
      {!loading && !result && (
        <UploadZone file={file} setFile={setFile} handleUpload={handleUpload} />
      )}

      {/* ETAT 2 : CHARGEMENT */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-32 animate-in fade-in">
          <Activity className="w-20 h-20 text-blue-500 animate-pulse mb-6" />
          <h3 className="text-2xl font-bold mb-2 text-white">L'IA travaille...</h3>
          <p className="text-gray-400 text-center">Détection et analyse biomécanique en cours.</p>
        </div>
      )}

      {/* ETAT 3 : RÉSULTATS */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          
          {/* Grosse Note Globale */}
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

          {/* Grille des critères avec les composants importés */}
          <div className="grid grid-cols-1 gap-4">
            {Object.entries(result).map(([key, data]) => {
              if (key === 'note_globale_brute' || key === 'mouvement_detecte') return null;
              
              return (
                <ResultCard 
                  key={key}
                  criterionKey={key}
                  data={data}
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