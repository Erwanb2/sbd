import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

const ANALYSIS_PHASES = [
  "Scan de la trajectoire de la barre (Bar Path)...",
  "Calcul des angles articulaires (Genoux & Hanches)...",
  "Mesure du bras de levier et contraintes lombaires...",
  "Évaluation du calage initial & pré-tension...",
  "Génération du rapport biomécanique détaillé..."
];

export default function LoadingProgress({ step, detectedMovement }) {
  const isDetecting = step === 1;
  const progress = isDetecting ? 35 : 85;
  const title = isDetecting ? "Movement detection" : "Technical analysis";

  // Défilement dynamique des micro-étapes techniques pour occuper l'attention
  const [phaseIndex, setPhaseIndex] = useState(0);

  useEffect(() => {
    if (step === 2) {
      const interval = setInterval(() => {
        setPhaseIndex((prev) => (prev + 1) % ANALYSIS_PHASES.length);
      }, 2500);
      return () => clearInterval(interval);
    }
  }, [step]);

  return (
    <div className="flex flex-col items-center justify-center py-10 max-w-md mx-auto animate-in fade-in duration-700">
      
      {/* --- FORMULATION GÉOMÉTRIQUE HYPNOTIQUE --- */}
      <div className="relative w-48 h-48 mb-8 flex items-center justify-center">
        {/* Halo lumineux diffus */}
        <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/20 via-indigo-500/30 to-emerald-500/20 rounded-full blur-2xl animate-pulse"></div>

        {/* Anneau 1 - Cercle externe pointillé lent */}
        <div className="absolute inset-0 border-2 border-dashed border-cyan-500/30 rounded-full animate-[spin_12s_linear_infinite]"></div>

        {/* Anneau 2 - Carré arrondi rotatif (Sens horaire) */}
        <div 
          className="absolute w-36 h-36 border border-indigo-400/50 rounded-[28%] shadow-[0_0_15px_rgba(99,102,241,0.2)]"
          style={{ animation: 'spin 8s linear infinite' }}
        ></div>

        {/* Anneau 3 - Octogone / Carré intérieur rotatif (Sens anti-horaire) */}
        <div 
          className="absolute w-28 h-28 border border-emerald-400/60 rounded-[20%] shadow-[0_0_20px_rgba(52,211,153,0.3)]"
          style={{ animation: 'spin 5s linear infinite reverse' }}
        ></div>

        {/* Anneau 4 - Triangle / Losange rapide au centre */}
        <div 
          className="absolute w-20 h-20 border-2 border-cyan-400/70 rounded-lg shadow-[0_0_25px_rgba(34,211,238,0.5)]"
          style={{ animation: 'spin 3s cubic-bezier(0.4, 0, 0.2, 1) infinite' }}
        ></div>

        {/* Noyau central - Cœur palpitant */}
        <div className="relative z-10 w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-400 via-indigo-400 to-emerald-400 animate-ping opacity-75"></div>
        <div className="absolute z-10 w-6 h-6 rounded-full bg-white shadow-[0_0_20px_#fff]"></div>

        {/* Particules orbitales flottantes */}
        <div className="absolute w-44 h-44 animate-[spin_6s_linear_infinite]">
          <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full shadow-[0_0_10px_#34d399] -translate-y-1"></div>
        </div>
        <div className="absolute w-32 h-32 animate-[spin_4s_linear_infinite_reverse]">
          <div className="w-2 h-2 bg-cyan-400 rounded-full shadow-[0_0_10px_#22d3ee] translate-x-32"></div>
        </div>
      </div>

      {/* Titre de l'étape */}
      <h3 className="text-2xl font-black mb-2 text-white tracking-wide text-center">
        {title}
      </h3>

      {/* Badge du mouvement détecté (Apparaît à l'étape 2) */}
      {step === 2 && detectedMovement && (
        <div className="mb-4 inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-bold animate-in fade-in zoom-in-95 duration-500">
          <Sparkles className="w-4 h-4 animate-spin" />
          <span>Mouvement : <span className="text-white uppercase tracking-wider">{detectedMovement}</span></span>
        </div>
      )}

      {/* Message technique dynamique hypnotique (Step 2) */}
      {step === 2 && (
        <p className="text-xs font-mono text-gray-400 mb-6 h-4 text-center animate-pulse tracking-tight">
          {ANALYSIS_PHASES[phaseIndex]}
        </p>
      )}

      {/* Barre de progression avec brillance animée */}
      <div className="w-full bg-gray-900 rounded-full h-2.5 mb-2 overflow-hidden border border-gray-800 shadow-inner">
        <div 
          className="bg-gradient-to-r from-cyan-500 via-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-1000 ease-out relative"
          style={{ width: `${progress}%` }}
        >
          <div className="absolute inset-0 bg-white/30 w-full h-full animate-[shimmer_1.5s_infinite]"></div>
        </div>
      </div>

    </div>
  );
}