import AnalysisLoader from './AnalysisLoader.jsx';

// Attente plein écran par-dessus la page d'accueil : le visiteur pas encore
// connecté voit sa propre analyse tourner avant qu'on lui demande son compte.
export default function AnalysisOverlay({ step, movement }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center overflow-y-auto bg-gray-950/95 px-4 py-10 backdrop-blur-sm animate-fade-in">
      <AnalysisLoader step={ step } movement={ movement } />
    </div>
  );
}
