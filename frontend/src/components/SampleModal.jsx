import { useEffect, useState } from 'react';
import { X, Upload, Sparkles } from 'lucide-react';
import ResultView from './ResultView.jsx';
import AnalysisLoader from './AnalysisLoader.jsx';
import PoseShowcase from './PoseShowcase.jsx';
import { sampleResult } from '../data/sampleResult.js';

// Fausse attente : on rejoue le vrai loader pour que la démo se déroule
// exactement comme une analyse réelle (détection du mouvement, puis résultat).
const DETECT_DELAY_MS = 3000;
const ANALYZE_DELAY_MS = 4000;

// step 0 = la vidéo est là, rien n'est lancé ; 1 = détection ; 2 = analyse ;
// 3 = résultat.
const STEP_IDLE = 0;

// Aperçu "sample" : la vidéo de démo + l'analyse figée, rendue avec les mêmes
// composants que le résultat réel. Le visiteur déclenche lui-même l'analyse,
// comme il le ferait avec sa propre vidéo. `onUploadOwn` referme l'aperçu et
// renvoie l'utilisateur vers la dropzone.
export default function SampleModal({ onClose, onUploadOwn }) {
  const [ step, setStep ] = useState(STEP_IDLE);

  // Une étape à la fois : l'effet est rejoué à chaque changement de `step` et
  // son cleanup annule le timer en cours, donc on ne peut pas armer les deux
  // attentes d'un coup.
  useEffect(() => {
    if (step !== 1 && step !== 2) return;

    const delay = step === 1 ? DETECT_DELAY_MS : ANALYZE_DELAY_MS;
    const timer = setTimeout(() => setStep(step + 1), delay);
    return () => clearTimeout(timer);
  }, [ step ]);

  const movement = sampleResult.movement_detected;
  const isIdle = step === STEP_IDLE;
  const isLoading = step > STEP_IDLE && step < 3;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm overflow-y-auto animate-fade-in">
      <div className="min-h-full flex items-start justify-center p-4 sm:p-8">
        <div className="relative w-full max-w-3xl bg-gray-950 border border-gray-800 rounded-3xl shadow-2xl p-5 sm:p-8 my-4 animate-fade-in-up">

          <button
            onClick={ onClose }
            className="absolute top-4 right-4 z-10 w-9 h-9 flex items-center justify-center rounded-full bg-gray-900/80 border border-gray-800 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="mb-6">
            <span className="inline-flex items-center gap-2 text-[11px] font-black uppercase tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Sample analysis
            </span>
            <p className="text-gray-400 text-sm mt-1">
              { isIdle && 'Run the analysis on this clip — it works exactly like it would on yours.' }
              { isLoading && 'Analyzing the clip below — exactly how it runs on your own video.' }
              { step === 3 && 'A full breakdown of that clip — your own analysis looks just like this.' }
            </p>
          </div>

          { /* La vitrine pose n'a plus lieu d'être une fois les scores là : à
               partir de step 3 l'écran ne garde que le score, le persona et les
               critères. */ }
          { step < 3 && <PoseShowcase active={ !isIdle } /> }

          { isIdle && (
            <button
              onClick={ () => setStep(1) }
              className="animate-fade-in-up flex w-full items-center justify-center gap-2 rounded-xl bg-white px-8 py-4 text-sm font-bold uppercase tracking-wide text-black transition-all hover:bg-gray-200 active:scale-[0.99]"
            >
              <Sparkles className="h-5 w-5" />
              Analyze this video
            </button>
          ) }

          { isLoading && (
            <AnalysisLoader step={ step } movement={ movement } />
          ) }

          { step === 3 && (
            <div className="animate-fade-in-up">
              <ResultView result={ sampleResult } />

              <button
                onClick={ onUploadOwn }
                className="w-full mt-8 bg-white text-black hover:bg-gray-200 font-bold py-4 px-8 rounded-xl transition-all uppercase tracking-wide flex items-center justify-center gap-2"
              >
                <Upload className="w-5 h-5" />
                Analyze my own video
              </button>
            </div>
          ) }
        </div>
      </div>
    </div>
  );
}
