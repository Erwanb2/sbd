import { useState } from 'react';
import ResultCard from './ResultCard.jsx';
import RepHistogram from './RepHistogram.jsx';
import { criteriaGuides } from '../data/criteriaGuides.js';
import { getPersonaAssets } from '../data/personaAssets.js';

// Rendu d'une analyse (vidéo + note + reps + conseils + persona + critères).
// Utilisé à la fois pour le résultat réel (App.jsx) et pour la démo de la page
// d'accueil. `onReset` et `videoUrl` sont optionnels.
//
// La forme lue ici est celle de `rules.evalue` côté backend : le modèle n'écrit
// plus de commentaire et ne donne plus de note, il observe. Tous les nombres de
// cette page sont calculés en Python à partir des états observés.
export default function ResultView({ result, movement, videoUrl, onReset }) {
  const [ expandedCard, setExpandedCard ] = useState(null);
  const [ selectedRep, setSelectedRep ] = useState(null);

  const note = result?.note_sur_20 ?? 0;
  const pourcentage = (note / 20) * 100;

  const criteres = Object.entries(result?.criteres || {});
  const reps = Array.isArray(result?.reps) ? result.reps : [];
  const conseils = Array.isArray(result?.conseils) ? result.conseils : [];
  const persona = result?.persona;

  const mouvement = result?.contexte?.variant?.etat
    ? `${ result.contexte.variant.etat } deadlift`
    : movement;

  return (
    <div className="space-y-6">
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
          <div className="relative sm:w-1/2 bg-black flex items-center justify-center">
            { /* Le fragment #t force le rendu de la première image : sans lui, la
                 carte s'ouvre sur un rectangle noir qui a l'air cassé. */ }
            <video
              src={ `${ videoUrl }#t=0.1` }
              controls
              loop
              playsInline
              preload="metadata"
              className="w-full max-h-[340px] object-contain bg-black"
            />
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

      { /* Au plus deux conseils, et ils passent avant tout le reste : c'est la seule
           partie de la page sur laquelle l'utilisateur peut agir demain. Deux et non
           huit — une page qui reproche huit choses ne fait rien changer. */ }
      { conseils.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-3xl p-6 sm:p-8 shadow-lg">
          <h3 className="text-white font-black uppercase tracking-widest text-sm mb-4">
            What to work on
          </h3>
          <div className="space-y-4">
            { conseils.map((c) => (
              <div key={ c.indicateur } className="flex items-start gap-4">
                <span
                  className={ `mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg text-xs font-black ${
                    c.note === 1
                      ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                      : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                  }` }
                >
                  { c.note }
                </span>
                <div className="min-w-0">
                  <p className="text-white font-semibold leading-snug">{ c.a_essayer }</p>
                  <p className="mt-1 text-sm text-gray-400 leading-relaxed">
                    { c.constat }
                    { reps.length > 1 && (
                      <span className="text-gray-600">
                        { ' ' }(rep{ c.reps.length > 1 ? 's' : '' } { c.reps.join(', ') })
                      </span>
                    ) }
                  </p>
                </div>
              </div>
            )) }
          </div>
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

      { result?.contexte && (
        <details className="mt-6 text-[11px] text-gray-500 border border-gray-800 rounded-lg bg-gray-900/40">
          <summary className="cursor-pointer px-3 py-2 uppercase tracking-wider select-none hover:text-gray-300">
            Capture et mesures (debug)
          </summary>
          <div className="px-3 pb-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 font-mono">
            { Object.entries(result.contexte).map(([ cle, valeur ]) => (
              <div key={ cle } className="flex justify-between gap-3 border-b border-gray-800/60 py-0.5">
                <span className="text-gray-600 truncate">{ cle }</span>
                <span className="text-gray-400 text-right whitespace-nowrap">
                  { valeur && typeof valeur === 'object'
                    ? (valeur.etat ?? Object.entries(valeur).map(([ a, b ]) => `${ a }=${ b }`).join(' '))
                    : String(valeur) }
                </span>
              </div>
            )) }
            { result.modele && (
              <div className="flex justify-between gap-3 border-b border-gray-800/60 py-0.5">
                <span className="text-gray-600 truncate">modele</span>
                <span className="text-gray-400 text-right whitespace-nowrap">{ result.modele }</span>
              </div>
            ) }
          </div>
        </details>
      ) }

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
