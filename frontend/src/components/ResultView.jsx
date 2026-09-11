import { useEffect, useRef, useState } from 'react';
import ResultCard from './ResultCard.jsx';
import RepHistogram from './RepHistogram.jsx';
import SkeletonOverlay from './SkeletonOverlay.jsx';
import PoseZoomFrame from './PoseZoomFrame.jsx';
import DebugView from './DebugView.jsx';
import { criteriaGuides } from '../data/criteriaGuides.js';
import { getPersonaAssets } from '../data/personaAssets.js';
import { formatTemps } from '../utils/helpers.js';

// Rendu d'une analyse : vidéo + note, puis les deux axes — le bandeau `structure`
// (ce qui a lâché, avec son urgence) et l'épingle (la seule chose à corriger, avec
// ce qui en découle rattaché dessous) — puis les reps, le persona et les six cartes
// de mécanique.
// Utilisé à la fois pour le résultat réel (App.jsx) et pour la démo de la page
// d'accueil. `onReset` et `videoUrl` sont optionnels.
//
// La forme lue ici est celle de `rules.evalue` côté backend : le modèle n'écrit
// plus de commentaire et ne donne plus de note, il observe. Tous les nombres de
// cette page sont calculés en Python à partir des états observés.
export default function ResultView({ result, movement, videoUrl, onReset }) {
  const [ expandedCard, setExpandedCard ] = useState(null);
  const [ selectedRep, setSelectedRep ] = useState(null);
  const [ squeletteVisible, setSqueletteVisible ] = useState(true);
  // Le zoom pose-tracké part désactivé : la bbox lissée reste en défaut sur les clips
  // à plusieurs personnes proches (cf. poseCrop.js), mieux vaut que ce soit un choix.
  const [ zoomActif, setZoomActif ] = useState(false);
  // Deux onglets : la page (ce qui cloche, une chose à corriger) et le debug (TOUT ce
  // que le modèle a rendu, champ par champ). Le second ne rallonge pas le premier.
  const [ onglet, setOnglet ] = useState('result');
  const videoRef = useRef(null);

  const note = result?.note_sur_20 ?? 0;
  const pourcentage = (note / 20) * 100;

  // Les cartes montrent les six MÉCANIQUES, dans l'ordre causal donné par le backend.
  // `structure` est noté comme les autres et compte dans le /20, mais il ne va pas
  // dans la grille : il s'affiche en bandeau, avec sa propre urgence. Ce ne sont pas
  // des choses qu'on exécute, ce sont des choses qui lâchent.
  const mecaniques = Array.isArray(result?.mecaniques)
    ? result.mecaniques
    : Object.keys(result?.criteres || {});
  const criteres = mecaniques
    .filter((c) => result?.criteres?.[c])
    .map((c) => [ c, result.criteres[c] ]);
  const reps = Array.isArray(result?.reps) ? result.reps : [];
  const epingle = result?.epingle;
  const structure = result?.structure;
  const persona = result?.persona;
  const squelette = result?.squelette;
  const repSelectionnee = reps.find((r) => r.index === selectedRep) || null;

  // Cliquer une rep dans l'histogramme saute la vidéo à son début et boucle la
  // lecture sur sa fenêtre (`debut_s`/`fin_s`, la même détection que les barres) :
  // pas besoin de chercher la répétition à la main dans le lecteur. Désélectionner
  // relâche la contrainte, la vidéo garde son `loop` sur le clip entier.
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !repSelectionnee || repSelectionnee.debut_s == null) return undefined;

    video.currentTime = repSelectionnee.debut_s;
    video.play().catch(() => {});

    const surProgression = () => {
      if (repSelectionnee.fin_s != null && video.currentTime >= repSelectionnee.fin_s) {
        video.currentTime = repSelectionnee.debut_s;
      }
    };
    video.addEventListener('timeupdate', surProgression);
    return () => video.removeEventListener('timeupdate', surProgression);
  }, [ repSelectionnee ]);

  const urgenceStyle = {
    stop: 'border-red-500/40 bg-red-500/10 text-red-300',
    caution: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    ok: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300',
    inconnu: 'border-gray-700 bg-gray-900 text-gray-400',
  }[structure?.etat] || 'border-gray-700 bg-gray-900 text-gray-400';
  const urgenceIcone = { stop: '🛑', caution: '⚠️', ok: '✅' }[structure?.etat] || '👁️';

  const mouvement = result?.contexte?.variant?.etat
    ? `${ result.contexte.variant.etat } deadlift`
    : movement;

  const Onglets = () => (
    <div className="flex justify-end">
      <div className="inline-flex rounded-xl border border-gray-800 bg-gray-900 p-1 text-xs font-bold uppercase tracking-wider">
        { [ [ 'result', 'Result' ], [ 'debug', 'Debug' ] ].map(([ cle, libelle ]) => (
          <button
            key={ cle }
            type="button"
            onClick={ () => setOnglet(cle) }
            className={ `rounded-lg px-3 py-1.5 transition-colors ${
              onglet === cle ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'
            }` }
          >
            { libelle }
          </button>
        )) }
      </div>
    </div>
  );

  if (onglet === 'debug') {
    return (
      <div className="space-y-6">
        <Onglets />
        <DebugView result={ result } />
        { onReset && (
          <button
            onClick={ onReset }
            className="w-full mt-8 bg-gray-800 hover:bg-gray-700 text-white font-bold py-4 px-8 rounded-xl transition-all uppercase tracking-wider text-sm"
          >
            Analyze another video
          </button>
        ) }
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Onglets />
      { result?.avertissement && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-500/40 bg-amber-500/10 px-5 py-4 text-left">
          <span className="text-lg leading-none">⚠️</span>
          <div className="text-sm">
            <p className="font-bold text-amber-300">Fallback model used</p>
            <p className="mt-0.5 text-amber-200/70">{ result.avertissement }</p>
          </div>
        </div>
      ) }

      { /* La vidéo à côté de la note, et non au-dessus : la page ne s'allonge pas
           d'un bloc, elle remplit une largeur qui était vide. */ }
      <div className="flex flex-col sm:flex-row bg-gray-900 border border-gray-800 rounded-3xl shadow-lg overflow-hidden">
        { videoUrl && (
          <div className="relative sm:w-1/2 bg-black flex items-center justify-center overflow-hidden">
            { /* Le zoom pose-tracké enveloppe la vidéo ET son overlay : les deux
                 bougent ensemble, l'overlay reste calé sur le squelette qu'il dessine. */ }
            <PoseZoomFrame videoRef={ videoRef } squelette={ squelette } enabled={ zoomActif }>
              { /* Le fragment #t force le rendu de la première image : sans lui, la
                   carte s'ouvre sur un rectangle noir qui a l'air cassé. */ }
              <video
                ref={ videoRef }
                src={ `${ videoUrl }#t=0.1` }
                controls
                loop
                playsInline
                preload="metadata"
                className="w-full max-h-[340px] object-contain bg-black"
              />

              { /* Le squelette dessiné vient de la même passe MediaPipe que la variante
                   et les répétitions : jamais recalculé côté navigateur. */ }
              <SkeletonOverlay videoRef={ videoRef } squelette={ squelette } visible={ squeletteVisible } />
            </PoseZoomFrame>

            { repSelectionnee && (
              <span className="pointer-events-none absolute top-2 left-2 rounded-md bg-black/70 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-300 backdrop-blur-sm">
                Rep { repSelectionnee.index } · { formatTemps(repSelectionnee.debut_s) }–{ formatTemps(repSelectionnee.fin_s) }
              </span>
            ) }

            { squelette?.frames?.length > 0 && (
              <div className="absolute top-2 right-2 flex gap-1">
                <button
                  type="button"
                  onClick={ () => setZoomActif((v) => !v) }
                  title={ zoomActif ? 'Disable pose-tracked zoom' : 'Enable pose-tracked zoom' }
                  className={ `flex h-6 w-6 items-center justify-center rounded-md bg-black/70 text-xs backdrop-blur-sm transition-colors hover:text-white ${
                    zoomActif ? 'text-emerald-400' : 'text-gray-300'
                  }` }
                >
                  🔍
                </button>
                <button
                  type="button"
                  onClick={ () => setSqueletteVisible((v) => !v) }
                  title={ squeletteVisible ? 'Hide pose skeleton' : 'Show pose skeleton' }
                  className="flex h-6 w-6 items-center justify-center rounded-md bg-black/70 text-xs text-gray-300 backdrop-blur-sm transition-colors hover:text-white"
                >
                  { squeletteVisible ? '🦴' : '🚫' }
                </button>
              </div>
            ) }

            <span className="pointer-events-none absolute bottom-2 left-2 rounded-md bg-black/70 px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-gray-300 backdrop-blur-sm">
              Video deleted in 24h
            </span>
          </div>
        ) }

        <div className="flex-1 flex flex-col items-center justify-center gap-2 p-8 sm:p-10">
          <span className="text-gray-400 font-semibold uppercase tracking-widest text-sm text-center">
            { mouvement }
          </span>
          <div className="flex items-baseline gap-2">
            <span className={ `text-7xl font-black ${ pourcentage >= 80 ? 'text-emerald-400' : pourcentage >= 50 ? 'text-amber-400' : 'text-red-400' }` }>
              { note }
            </span>
            <span className="text-4xl text-gray-600 font-bold">/ 20</span>
          </div>
          { reps.length > 0 && (
            <span className="text-xs text-gray-500 uppercase tracking-wider">
              across { reps.length } rep{ reps.length > 1 ? 's' : '' }
              { result?.segments_ecartes?.length > 0 && ' · false starts dropped' }
            </span>
          ) }
        </div>
      </div>

      { /* L'axe STRUCTURE, en bandeau au-dessus de tout. Le danger fixe l'urgence, la
           cause fixe l'action : ce bandeau dit s'il faut s'arrêter, jamais quoi faire
           du geste — « utilise moins tes lombaires » n'est pas exécutable. */ }
      { structure?.texte && (
        <div className={ `flex items-start gap-3 rounded-2xl border px-5 py-4 text-left ${ urgenceStyle }` }>
          <span className="text-lg leading-none">{ urgenceIcone }</span>
          <div className="min-w-0 text-sm">
            <p className="font-bold">{ structure.texte }</p>
            { structure.defauts?.length > 0 && (
              <ul className="mt-1.5 space-y-1 text-current/70">
                { structure.defauts.map((d) => (
                  <li key={ d.indicateur }>
                    { d.constat }
                    { reps.length > 1 && (
                      <span className="opacity-50">
                        { ' ' }(rep{ d.reps.length > 1 ? 's' : '' } { d.reps.join(', ') })
                      </span>
                    ) }
                  </li>
                )) }
              </ul>
            ) }
          </div>
        </div>
      ) }

      { /* UNE chose à corriger, et une seule. Cinq cartes à 3/3 et une à 2/3, ce n'est
           pas du coaching, c'est un bulletin. L'épingle est le défaut le plus EN AMONT,
           pas le plus grave : ce qui en découle est rattaché dessous, parce que
           demander deux corrections pour une cause n'en obtient aucune. */ }
      { epingle && (
        <div className="bg-gray-900 border border-gray-800 rounded-3xl p-6 sm:p-8 shadow-lg">
          <h3 className="text-white font-black uppercase tracking-widest text-sm mb-4">
            What to work on
          </h3>
          <div className="flex items-start gap-4">
            <span
              className={ `mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg text-xs font-black ${
                epingle.note === 1
                  ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              }` }
            >
              { epingle.note }
            </span>
            <div className="min-w-0">
              <p className="text-white font-semibold leading-snug text-lg">{ epingle.a_essayer }</p>
              <p className="mt-1 text-sm text-gray-400 leading-relaxed">
                { epingle.constat }
                { reps.length > 1 && (
                  <span className="text-gray-600">
                    { ' ' }(rep{ epingle.reps.length > 1 ? 's' : '' } { epingle.reps.join(', ') })
                  </span>
                ) }
              </p>

              { /* Rattaché, pas listé à côté : c'est la même cause. */ }
              { epingle.consequences?.length > 0 && (
                <div className="mt-3 border-l-2 border-gray-700 pl-3">
                  <p className="text-xs uppercase tracking-wider text-gray-500 font-bold">
                    And that is why
                  </p>
                  <ul className="mt-1 space-y-0.5 text-sm text-gray-500">
                    { epingle.consequences.map((c) => (
                      <li key={ c.indicateur }>{ c.constat }</li>
                    )) }
                  </ul>
                </div>
              ) }
            </div>
          </div>

          { /* Ce que l'épingle n'explique pas : un seul, en petit. La page ne doit
               pas s'allonger, et deux reproches indépendants se neutralisent. */ }
          { epingle.autres?.length > 0 && (
            <div className="mt-5 border-t border-gray-800 pt-4 text-sm">
              <p className="text-xs uppercase tracking-wider text-gray-600 font-bold mb-1.5">
                Separately
              </p>
              { epingle.autres.map((c) => (
                <p key={ c.indicateur } className="text-gray-400">
                  <span className="text-gray-300">{ c.a_essayer }</span>{ ' ' }
                  <span className="text-gray-600">{ c.constat }</span>
                </p>
              )) }
            </div>
          ) }
        </div>
      ) }

      <RepHistogram
        reps={ reps }
        tenue={ result?.tenue_du_set?.texte }
        selected={ selectedRep }
        onSelect={ setSelectedRep }
      />

      { persona?.nom && (() => {
        const { emoji, filename } = getPersonaAssets(persona.nom);
        return (
          <div className="bg-gradient-to-br from-indigo-900 to-purple-900 border border-indigo-500/30 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row items-center gap-6 sm:gap-8 text-center sm:text-left transform transition-transform hover:scale-[1.02]">
            <div className="w-32 h-32 sm:w-40 sm:h-40 flex-shrink-0 bg-indigo-950/50 rounded-full border-4 border-indigo-400/50 overflow-hidden flex items-center justify-center shadow-inner relative">
              <img
                src={ `/images/personas/${ filename }` }
                alt={ persona.nom }
                className="w-full h-full object-cover z-10"
                onError={ (e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                } }
              />
              <div className="absolute inset-0 hidden items-center justify-center text-6xl sm:text-7xl z-0">
                { emoji }
              </div>
            </div>

            <div className="flex-1">
              <span className="text-indigo-300 font-black uppercase tracking-widest text-xs mb-2 block">
                Your Deadlift Persona
              </span>
              <h3 className="text-3xl sm:text-4xl font-black text-white mb-4 drop-shadow-md">
                { persona.nom }
              </h3>
              { /* La justification est le FAIT qui a déclenché le persona, pas une
                   phrase générée à côté : l'étiquette et son explication ne peuvent
                   plus se contredire. */ }
              <p className="text-indigo-100 text-base sm:text-lg italic bg-black/20 p-4 rounded-xl leading-relaxed border border-indigo-500/20">
                "{ persona.fait }"
                { persona.rep && (
                  <span className="not-italic text-indigo-300/60 text-sm"> — rep { persona.rep }</span>
                ) }
              </p>
            </div>
          </div>
        );
      })() }

      <div className="grid grid-cols-1 gap-4">
        { criteres.map(([ cle, data ]) => (
          <ResultCard
            key={ cle }
            data={ data }
            isExpanded={ expandedCard === cle }
            onToggle={ () => setExpandedCard(expandedCard === cle ? null : cle) }
            demo={ criteriaGuides[cle] }
          />
        )) }
      </div>

      { onReset && (
        <button
          onClick={ onReset }
          className="w-full mt-8 bg-gray-800 hover:bg-gray-700 text-white font-bold py-4 px-8 rounded-xl transition-all uppercase tracking-wider text-sm"
        >
          Analyze another video
        </button>
      ) }
    </div>
  );
}
