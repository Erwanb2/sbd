import { useState } from 'react';
import { UploadCloud, Activity, Dumbbell, AlertCircle, CheckCircle, Clock } from 'lucide-react';

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('video', file);

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      alert("Erreur lors de l'analyse de la vidéo.");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score === 3) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    if (score === 2) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    return 'bg-red-500/20 text-red-400 border-red-500/30';
  };

  const formatKey = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="max-w-4xl mx-auto p-6 pt-12">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-blue-600/20 rounded-2xl border border-blue-500/30">
            <Dumbbell className="w-10 h-10 text-blue-400" />
          </div>
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight mb-2">
          Deadlift <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">SBD Reviews</span>
        </h1>
        <p className="text-gray-400">Analyse biomécanique propulsée par l'Intelligence Artificielle.</p>
      </div>

      {/* Upload Zone */}
      {!loading && !result && (
        <form onSubmit={handleUpload} className="bg-gray-900 border border-gray-800 rounded-3xl p-8 shadow-2xl transition-all hover:border-blue-500/50">
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-700 rounded-2xl p-12 bg-gray-950/50 group">
            <UploadCloud className="w-16 h-16 text-gray-500 group-hover:text-blue-400 transition-colors mb-4" />
            <input 
              type="file" 
              accept="video/mp4,video/mov" 
              onChange={(e) => setFile(e.target.files[0])}
              className="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600/20 file:text-blue-400 hover:file:bg-blue-600/30 cursor-pointer"
            />
          </div>
          <button 
            type="submit" 
            disabled={!file}
            className="w-full mt-6 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-bold py-4 px-8 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Lancer l'analyse
          </button>
        </form>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20">
          <Activity className="w-16 h-16 text-blue-500 animate-pulse mb-6" />
          <h3 className="text-xl font-bold mb-2">Analyse en cours...</h3>
          <p className="text-gray-400 text-center max-w-md">
            L'IA décompose tes angles, ta vitesse et ton gainage. Cela peut prendre 10 à 20 secondes.
          </p>
        </div>
      )}

       {/* Results */}
      {result && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          
          {/* Note Globale sur 21 */}
          <div className="flex flex-col items-center justify-center p-8 bg-gray-900 border border-gray-800 rounded-3xl shadow-lg">
            <span className="text-gray-400 font-semibold mb-2 uppercase tracking-widest text-sm">Score Technique</span>
            <div className="flex items-baseline gap-2">
              <span className={`text-6xl font-black ${
                result.note_globale >= 18 ? 'text-emerald-400' : 
                result.note_globale >= 13 ? 'text-amber-400' : 'text-red-400'
              }`}>
                {result.note_globale}
              </span>
              <span className="text-3xl text-gray-500 font-bold">/ 20</span>
            </div>
          </div>

          {/* Grille des 7 Critères */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(result).map(([key, data]) => {
              if (key === 'note_globale') return null;
              
              // data contient maintenant data.note et data.commentaire
              const score = data.note;
              
              return (
                <div key={key} className={`flex flex-col p-5 rounded-2xl border ${getScoreColor(score)}`}>
                  
                  {/* Titre et Note */}
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-bold text-white text-lg">{formatKey(key)}</span>
                    <span className="text-lg font-bold">{score}/3</span>
                  </div>
                  
                  {/* Barres de score */}
                  <div className="flex gap-1 w-full mb-4">
                    {[1, 2, 3].map((star) => (
                      <div 
                        key={star} 
                        className={`flex-1 h-2 rounded-full ${star <= score ? 'bg-current' : 'bg-gray-800/50'}`}
                      />
                    ))}
                  </div>

                  {/* La petite phrase de conseil */}
                  <div className="mt-auto bg-black/20 p-3 rounded-xl border border-current/10">
                    <p className="text-sm opacity-90 leading-relaxed italic">
                      "{data.commentaire}"
                    </p>
                  </div>

                </div>
              );
            })}
          </div>

          <button 
            onClick={() => {setResult(null); setFile(null);}}
            className="w-full bg-gray-800 hover:bg-gray-700 text-white font-bold py-4 px-8 rounded-xl transition-all"
          >
            Analyser une autre vidéo
          </button>
        </div>
      )}
    </div>
  );
}