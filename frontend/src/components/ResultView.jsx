import { useState } from 'react';
import ResultCard from './ResultCard.jsx';
import { criteriaGuides } from '../data/criteriaGuides.js';
import { getPersonaAssets } from '../data/personaAssets.js';

// Rendu d'une analyse (score + persona + critères). Utilisé à la fois pour le
// résultat réel de l'utilisateur (App.jsx) et pour la démo sample de la page
// d'accueil. `onReset` est optionnel : absent = pas de bouton "analyze another".
export default function ResultView({ result, movement, onReset }) {
  const [ expandedCard, setExpandedCard ] = useState(null);

  const scoreObtenu = result?.total_raw_score || result?.note_globale_brute || 0;
  const scoreMax = result?.raw_max_score || 24;
  const scorePercentage = (scoreObtenu / scoreMax) * 100;

  const fallback = result?.model_fallback;

  return (
    <div className="space-y-6">
      { /* TEMPORAIRE (debug) : le modèle principal était saturé, l'analyse a
           tourné sur le modèle de repli. À retirer quand ce ne sera plus utile. */ }
      { fallback?.used && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-500/40 bg-amber-500/10 px-5 py-4 text-left">
          <span className="text-lg leading-none">⚠️</span>
          <div className="text-sm">
            <p className="font-bold text-amber-300">Debug · fallback model used</p>
            <p className="mt-0.5 text-amber-200/70">
              <span className="font-mono">{ fallback.primary }</span> was overloaded
              (503) — this analysis ran on{ ' ' }
              <span className="font-mono">{ fallback.model }</span>.
            </p>
          </div>
        </div>
      ) }

      <div className="flex flex-col items-center justify-center p-10 bg-gray-900 border border-gray-800 rounded-3xl shadow-lg">
        <span className="text-gray-400 font-semibold mb-2 uppercase tracking-widest text-sm">
          { result.movement_detected || movement }
        </span>
        <div className="flex items-baseline gap-2">
          <span className={ `text-7xl font-black ${ scorePercentage >= 80 ? 'text-emerald-400' : scorePercentage >= 50 ? 'text-amber-400' : 'text-red-400' }` }>
            { scoreObtenu }
          </span>
          <span className="text-4xl text-gray-600 font-bold">/ { scoreMax }</span>
        </div>
      </div>

      { result.lifter_persona && (() => {
        const { emoji, filename } = getPersonaAssets(result.lifter_persona);
        return (
          <div className="bg-gradient-to-br from-indigo-900 to-purple-900 border border-indigo-500/30 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row items-center gap-6 sm:gap-8 text-center sm:text-left transform transition-transform hover:scale-[1.02]">

            <div className="w-32 h-32 sm:w-40 sm:h-40 flex-shrink-0 bg-indigo-950/50 rounded-full border-4 border-indigo-400/50 overflow-hidden flex items-center justify-center shadow-inner relative">
              <img
                src={ `/images/personas/${ filename }` }
                alt={ result.lifter_persona }
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
                { result.lifter_persona }
              </h3>
              <p className="text-indigo-100 text-base sm:text-lg italic bg-black/20 p-4 rounded-xl leading-relaxed border border-indigo-500/20">
                "{ result.persona_justification }"
              </p>
            </div>
          </div>
        );
      })() }

      <div className="grid grid-cols-1 gap-4">
        { Object.entries(result).map(([ key, data ]) => {
          // Un critère est le seul objet de la réponse à porter une clé "score"
          // (éventuellement null quand il n'est pas visible à l'image). Tout le
          // reste — totaux, quota, persona — est ignoré sans liste à maintenir.
          if (!data || typeof data !== 'object' || !( 'score' in data )) return null;

          return (
            <ResultCard
              key={ key }
              criterionKey={ key }
              data={ data }
              isExpanded={ expandedCard === key }
              onToggle={ () => setExpandedCard(expandedCard === key ? null : key) }
              demo={ criteriaGuides[key] }
            />
          );
        }) }
      </div>

      { result.kinematics && (
        <details className="mt-6 text-[11px] text-gray-500 border border-gray-800 rounded-lg bg-gray-900/40">
          <summary className="cursor-pointer px-3 py-2 uppercase tracking-wider select-none hover:text-gray-300">
            Mesures de pose (debug)
          </summary>
          <div className="px-3 pb-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 font-mono">
            { Object.entries(result.kinematics).map(([ k, v ]) => (
              <div key={ k } className="flex justify-between gap-3 border-b border-gray-800/60 py-0.5">
                <span className="text-gray-600 truncate">{ k }</span>
                <span className="text-gray-400 text-right whitespace-nowrap">
                  { typeof v === 'object' && v !== null
                    ? Object.entries(v).map(([ a, b ]) => `${a}=${b}`).join(' ')
                    : String(v) }
                </span>
              </div>
            )) }
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
