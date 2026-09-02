import { GoogleLogin } from '@react-oauth/google';
import { X, ShieldCheck, Sparkles } from 'lucide-react';

// Modale d'authentification. Elle n'apparaît qu'une fois l'analyse RÉELLEMENT
// terminée côté serveur : le visiteur a vu sa vidéo être analysée, il ne reste
// qu'à déverrouiller le résultat. Se connecter devient un déblocage, pas un
// péage à l'entrée du site.
export default function AuthModal({ fileName, movement, onSuccess, onError, onClose }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
      onClick={ onClose }
    >
      <div
        className="relative w-full max-w-md bg-gray-900 border border-gray-800 rounded-3xl p-8 shadow-2xl animate-fade-in-up"
        onClick={ (e) => e.stopPropagation() }
      >
        <button
          onClick={ onClose }
          className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex flex-col items-center text-center">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mb-5">
            <Sparkles className="w-7 h-7 text-emerald-400" />
          </div>

          <h2 className="text-2xl font-black text-white mb-2">Your analysis is ready</h2>
          <p className="text-gray-400 text-sm leading-relaxed mb-1">
            Sign in with Google to unlock your score and the full
            criterion-by-criterion breakdown.
          </p>
          <p className="text-emerald-400/90 text-xs font-semibold uppercase tracking-wider mb-6">
            Free · Takes 5 seconds
          </p>

          { movement && (
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-500/40 bg-indigo-500/20 px-4 py-1.5 text-[11px] font-black uppercase tracking-widest text-indigo-100">
              <span>🎯</span> { movement } analyzed
            </div>
          ) }

          { fileName && (
            <div className="w-full mb-6 px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-gray-300 text-sm font-medium truncate">
              { fileName }
            </div>
          ) }

          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={ onSuccess }
              onError={ onError }
              theme="filled_black"
              shape="pill"
              text="continue_with"
            />
          </div>

          <div className="flex items-center gap-2 mt-6 text-gray-500 text-xs">
            <ShieldCheck className="w-4 h-4 flex-shrink-0" />
            <span>Your video was analyzed on the fly and never stored.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
