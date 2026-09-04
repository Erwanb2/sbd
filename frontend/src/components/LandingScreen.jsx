import { useState } from 'react';
import { Play, Sparkles } from 'lucide-react';
import UploadZone from './UploadZone.jsx';
import Wordmark from './Wordmark.jsx';

const PHOTO_MASK = 'linear-gradient(to right, transparent 0%, rgba(0,0,0,0.45) 14%, #000 40%)';
// Sur mobile la photo passe derrière le texte : masque vertical + voile sombre
// pour qu'elle reste une texture et jamais un fond qui gêne la lecture. Elle est
// calée en bas (pas d'object-cover pleine page, qui rognerait les disques sur un
// viewport étroit), donc c'est le haut qui se fond dans le noir. Elle est
// dimensionnée par la largeur ET bornée par la hauteur : sinon son cadrage suit
// la largeur de la fenêtre — trop basse sur un écran étroit, tête coupée dès que
// la fenêtre s'élargit. Sous 640 px, la photo remplit la hauteur du premier écran
// (object-cover) : sa hauteur ne dépend plus de la largeur du téléphone, et le
// recadrage à 62 % garde la barre et les disques dans le champ. Au-dessus, la
// largeur suffit à la faire tenir en entier : object-contain, sans rognage.
const PHOTO_MASK_MOBILE = 'linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.5) 9%, #000 24%)';

// Le parcours en trois temps. Le texte reste volontairement court : chaque
// étape porte un bénéfice ET ce qui nous distingue d'un coach IA générique —
// on mesure le mouvement au lieu de le commenter, et on renvoie un archétype
// de lifter (cf. personaAssets.js) plus un score par critère.
const STEPS = [
  {
    title: 'Film one set',
    text: '15 seconds of one working set, filmed on your phone.',
  },
  {
    title: 'Engineered, not prompted',
    text: 'We engineered a system that measures your lift instead of describing it without understanding it.',
  },
  {
    title: 'Get your score',
    text: 'One rating, your lifter profile, and where you stand on every criterion that matters. Not generic advice.',
  },
];

// Page d'accueil (visiteur non connecté). Tout tient au-dessus de la ligne de
// flottaison sur grand écran ; sur mobile les trois repères passent sous le CTA.
// Le sign-in Google est déclenché depuis App.jsx (AuthModal), 5 s après le
// lancement de l'analyse.
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

      {/* Hauteur bornée au premier écran (svh, pas vh : sur mobile vh compte la
          barre d'URL). Sinon le conteneur ferait la hauteur de la page, qui
          défile, et la photo se calerait sous la ligne de flottaison. */}
      { photoOk && (
        <div className="pointer-events-none absolute inset-x-0 top-0 h-[100svh] overflow-hidden lg:hidden">
          <img
            src="/images/hero-bg.jpg"
            alt=""
            aria-hidden="true"
            onError={ () => setPhotoOk(false) }
            className="absolute inset-x-0 bottom-0 h-[92svh] w-full object-cover object-[62%_100%] opacity-[0.45] sm:h-auto sm:max-h-full sm:object-contain sm:object-bottom"
            style={{ maskImage: PHOTO_MASK_MOBILE, WebkitMaskImage: PHOTO_MASK_MOBILE }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-gray-950/80 via-gray-950/55 to-gray-950/25" />
        </div>
      ) }

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

          <div className={ `mt-10 border-t border-white/10 pt-7 ${ photoOk ? '' : 'text-left' }` }>
            <p className="text-[10px] font-black uppercase tracking-[0.22em] text-emerald-400/90">
              How it works
            </p>

            <div className="relative mt-5">
              {/* Rail de liaison : vertical quand les étapes s'empilent, horizontal
                  dès qu'elles passent en colonnes. Les pastilles, opaques, le
                  découpent en segments. */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute left-4 top-4 bottom-6 w-px bg-gradient-to-b from-emerald-500/60 via-white/15 to-transparent sm:bottom-auto sm:left-4 sm:right-4 sm:h-px sm:w-auto sm:bg-gradient-to-r sm:from-emerald-500/60 sm:via-white/15 sm:to-transparent"
              />

              <ol className="relative grid gap-5 sm:grid-cols-3 sm:gap-x-4">
                { STEPS.map(({ title, text }, i) => (
                  <li key={ title } className="flex gap-3.5 text-left sm:flex-col sm:gap-3">
                    <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-emerald-500/40 bg-gray-950 text-xs font-black text-emerald-400">
                      { i + 1 }
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-bold leading-tight text-white">{ title }</p>
                      <p className="mt-1.5 text-xs leading-relaxed text-gray-400">{ text }</p>
                    </div>
                  </li>
                )) }
              </ol>
            </div>
          </div>

          <p className="mt-7 text-xs text-gray-400">
            Free · Video never stored
          </p>
        </div>
      </div>
    </div>
  );
}
