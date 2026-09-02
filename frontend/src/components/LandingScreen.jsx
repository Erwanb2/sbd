import { useState } from 'react';
import { Play, Sparkles } from 'lucide-react';
import UploadZone from './UploadZone.jsx';
import Wordmark from './Wordmark.jsx';

const PHOTO_MASK = 'linear-gradient(to right, transparent 0%, rgba(0,0,0,0.45) 14%, #000 40%)';

// Page d'accueil (visiteur non connecté). Une seule vue, sans scroll.
// Le sign-in Google n'apparaît qu'après le choix d'une vraie vidéo (AuthModal,
// déclenché dans App.jsx).
export default function LandingScreen({
  file,
  setFile,
  onSubmit,
  limits,
  onOpenSample,
  pendingClaim = false,
  onResumeClaim,
}) {
  // La photo est portrait : on la laisse occuper la moitié droite sur grand
  // écran et on la fond dans le noir au masque — pas de calque de dégradé qui
  // dessinerait une couture verticale si le fichier est absent.
  const [ photoOk, setPhotoOk ] = useState(true);

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-gray-950">
      {/* Lueur froide diffuse, dans l'axe du spot de la photo. */}
      <div
        className="absolute inset-0"
        style={{ background: 'radial-gradient(110% 75% at 68% 12%, rgba(150,158,170,0.10), transparent 62%)' }}
      />

      { photoOk && (
        <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-[52%] lg:block xl:w-[48%]">
          <img
            src="/images/hero-bg.jpg"
            alt=""
            aria-hidden="true"
            onError={ () => setPhotoOk(false) }
            className="h-full w-full object-cover object-[center_28%]"
            style={{ maskImage: PHOTO_MASK, WebkitMaskImage: PHOTO_MASK }}
          />
          <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-gray-950 to-transparent" />
        </div>
      ) }

      {/* Sans photo, la colonne de gauche laisserait un grand vide à droite :
          on recentre tout pour que la page reste équilibrée. */}
      {/* Le padding en % recentre la colonne dans la moitié gauche laissée par
          la photo, au lieu de la coller au bord sur les grands écrans. */}
      <div className={ `relative z-10 flex min-h-screen items-center px-6 sm:px-10 lg:px-16 xl:px-[8%] ${ photoOk ? '' : 'justify-center' }` }>
        {/* min-w-0 : sans lui, un flex item refuse de descendre sous la largeur
            min-content de son contenu et déborde du viewport sur mobile. */}
        <div className={ `w-full min-w-0 max-w-xl py-16 ${ photoOk ? '' : 'text-center' }` }>
          <Wordmark size="lg" className={ photoOk ? '' : 'inline-block text-left' } />

          {/* L'analyse est calculée mais pas encore déverrouillée : le visiteur
              a fermé la modale de connexion, on lui laisse un moyen d'y revenir. */}
          { pendingClaim && (
            <button
              onClick={ onResumeClaim }
              className="animate-fade-in-up mt-8 flex w-full items-center gap-3 rounded-2xl border border-emerald-500/40 bg-emerald-500/10 px-5 py-4 text-left transition-colors hover:bg-emerald-500/15"
            >
              <Sparkles className="h-5 w-5 flex-shrink-0 text-emerald-400" />
              <span className="flex-1">
                <span className="block text-sm font-bold text-white">
                  Your analysis is ready
                </span>
                <span className="block text-xs text-emerald-400/90">
                  Sign in to unlock your score
                </span>
              </span>
            </button>
          ) }

          <div className="mt-9">
            <UploadZone
              file={ file }
              setFile={ setFile }
              handleUpload={ onSubmit }
              limits={ limits }
              compact
            />
          </div>

          <button
            onClick={ onOpenSample }
            className="group mt-5 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 py-2 pl-2 pr-5 text-sm font-semibold text-gray-300 backdrop-blur transition-all hover:border-white/25 hover:bg-white/10 hover:text-white"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-white transition-colors group-hover:bg-emerald-500 group-hover:text-black">
              <Play className="h-3.5 w-3.5 fill-current" />
            </span>
            See it on a sample video
          </button>

          <p className="mt-10 text-xs text-gray-400">
            Free · No account needed to try · Video never stored
          </p>
        </div>
      </div>
    </div>
  );
}
