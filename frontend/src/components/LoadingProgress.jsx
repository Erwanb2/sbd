import { Search, BrainCircuit } from 'lucide-react';

export default function LoadingProgress({ step }) {
  // step 1 = Détection, step 2 = Analyse
  const isDetecting = step === 1;
  const progress = isDetecting ? 40 : 85;
  const title = isDetecting ? "Détection du mouvement..." : "Analyse biomécanique...";
  const Icon = isDetecting ? Search : BrainCircuit;

  return (
    <div className="flex flex-col items-center justify-center py-24 animate-in fade-in zoom-in-95 duration-500">
      
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full animate-pulse"></div>
        <div className="relative bg-gray-900 border border-gray-700 p-6 rounded-full shadow-2xl">
          <Icon className={`w-12 h-12 text-blue-400 ${isDetecting ? 'animate-bounce' : 'animate-pulse'}`} />
        </div>
      </div>

      <h3 className="text-2xl font-black mb-6 text-white tracking-wide">{title}</h3>
      
      {/* Barre de progression */}
      <div className="w-full max-w-md bg-gray-900 rounded-full h-3 mb-4 overflow-hidden border border-gray-800 shadow-inner">
        <div 
          className="bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-1000 ease-out relative"
          style={{ width: `${progress}%` }}
        >
          {/* Petit effet de brillance sur la barre */}
          <div className="absolute inset-0 bg-white/20 w-full h-full animate-[shimmer_2s_infinite]"></div>
        </div>
      </div>
      
      <p className="text-gray-500 text-sm font-medium">
        {isDetecting ? "L'IA visionne la vidéo pour comprendre l'exercice" : "Décomposition des angles et de la posture"}
      </p>
    </div>
  );
}