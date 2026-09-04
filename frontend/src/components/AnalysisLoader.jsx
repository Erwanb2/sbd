import GeometricSBDLoader from './GeometricSBDLoader.jsx';
import { loadingTips } from '../data/personaAssets.js';

// Écran d'attente partagé par les trois parcours : analyse réelle connectée,
// parcours anonyme (AnalysisOverlay) et démo sample (SampleModal).
// step 1 = upload + détection, step >= 2 = analyse en cours.
// `showSpinner` : à false quand l'écran montre déjà autre chose d'animé (la
// vitrine pose de la démo sample), pour ne pas avoir deux loaders concurrents.
export default function AnalysisLoader({ step, movement, showSpinner = true }) {
  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      { showSpinner && <GeometricSBDLoader /> }

      { step >= 2 && movement && (
        <div className="bg-white/[0.04] border border-white/10 text-gray-300 p-6 rounded-2xl text-center shadow-inner animate-fade-in-up">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 text-xs font-black uppercase tracking-widest mb-4">
            <span className="bg-emerald-500/15 text-emerald-300 py-1.5 px-4 rounded-full border border-emerald-500/30 shadow-sm flex items-center gap-2">
              <span>🎯</span> { movement } DETECTED
            </span>
          </div>
          <p className="italic text-lg font-medium leading-relaxed max-w-lg mx-auto">
            "{ loadingTips[movement] || 'Hold tight, analyzing your biomechanics...' }"
          </p>
        </div>
      ) }
    </div>
  );
}
