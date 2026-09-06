import { formatKey, getScoreColor } from '../utils/helpers';

// Hauteur minimale d'une barre, en pourcentage : une rep très faible doit
// rester visible et cliquable.
const HAUTEUR_MIN = 10;

// La hauteur suit le total exact de la rep (ex. 21/24), pas sa note arrondie :
// c'est ce qui permet de comparer deux reps que l'arrondi met à égalité. Le
// badge, lui, porte la note affichée — le même calcul que les critères plus bas.
const hauteur = (rep) =>
  rep.max ? Math.max(HAUTEUR_MIN, Math.round((rep.total / rep.max) * 100)) : HAUTEUR_MIN;

// Seules les reps parfaites sont mises en valeur. Pas de mise en valeur
// négative : le graphique est là pour montrer à l'utilisateur ses belles reps.
// Ce qui ne va pas est déjà dit, en toutes lettres, dans les critères.
const estParfaite = (rep) => rep.score === 3;

// Histogramme du set : une barre par rep, cliquable, et le détail des critères
// de la rep sélectionnée. `criteria` donne l'ordre des critères, celui du schéma.
export default function RepHistogram({ reps, criteria, selected, onSelect }) {
  if (!reps?.length) return null;

  const parfaites = reps.filter(estParfaite).length;
  const ouverte = reps.find((r) => r.rep_index === selected) || null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-3xl p-6 sm:p-8 shadow-lg">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-white font-black uppercase tracking-widest text-sm">
          Rep by rep
        </h3>
        <span className="text-xs text-gray-500 uppercase tracking-wider">
          { reps.length } rep{ reps.length > 1 ? 's' : '' } detected
        </span>
      </div>
      <p className="text-sm text-gray-400 mt-1">
        { parfaites > 0
          ? `${ parfaites } clean rep${ parfaites > 1 ? 's' : '' } in there. Tap a bar for the full breakdown.`
          : 'Tap a bar for the full breakdown of that rep.' }
      </p>

      { /* Les barres sont bornees en largeur : a trois reps, des colonnes
           pleine largeur ressemblent a des blocs, plus a un graphique. */ }
      <div className="flex items-end justify-center gap-3 sm:gap-4 h-44 mt-6">
        { reps.map((rep) => {
          const actif = rep.rep_index === selected;
          const parfaite = estParfaite(rep);

          return (
            <button
              key={ rep.rep_index }
              onClick={ () => onSelect(actif ? null : rep.rep_index) }
              aria-pressed={ actif }
              title={ `Rep ${ rep.rep_index } — ${ rep.total }/${ rep.max }` }
              className="group flex-1 min-w-0 max-w-[120px] h-full flex flex-col justify-end items-center gap-2"
            >
              <span
                className={ `text-[11px] font-bold tabular-nums transition-colors ${
                  parfaite ? 'text-emerald-400' : actif ? 'text-white' : 'text-gray-500'
                }` }
              >
                { rep.score === null || rep.score === undefined ? '–' : `${ rep.score }/3` }
              </span>

              <div
                style={ { height: `${ hauteur(rep) }%` } }
                className={ `w-full rounded-t-lg transition-all duration-300 ${
                  parfaite
                    ? 'bg-gradient-to-t from-emerald-700/60 to-emerald-400 shadow-[0_0_24px_-4px] shadow-emerald-500/60'
                    : 'bg-gray-700 group-hover:bg-gray-600'
                } ${ actif ? 'ring-2 ring-white/70' : '' }` }
              />

              <span
                className={ `text-xs font-bold ${ actif ? 'text-white' : 'text-gray-500' }` }
              >
                { rep.rep_index }
              </span>
            </button>
          );
        }) }
      </div>

      { ouverte && (
        <div className="mt-6 border-t border-gray-800 pt-5 animate-fade-in">
          <div className="flex items-baseline justify-between mb-4">
            <h4 className="text-white font-black">Rep { ouverte.rep_index }</h4>
            <span className="text-sm text-gray-500 font-mono tabular-nums">
              { ouverte.total }/{ ouverte.max }
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            { criteria.filter((cle) => ouverte[cle]).map((cle) => {
              const critere = ouverte[cle];
              // Le backend met score: null quand la rep n'était pas lisible sur
              // ce critère — hors cadre, masquée, coupée au montage.
              const invisible = critere.score === null || critere.score === undefined;

              return (
                <div
                  key={ cle }
                  className={ `rounded-xl border p-3 ${ getScoreColor(critere.score) }` }
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-[13px] font-bold text-white leading-tight">
                      { formatKey(cle) }
                    </span>
                    <span className="text-xs font-bold whitespace-nowrap">
                      { invisible ? 'Not visible' : `${ critere.score }/3` }
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs leading-relaxed text-white/70">
                    { critere.note }
                  </p>
                </div>
              );
            }) }
          </div>
        </div>
      ) }
    </div>
  );
}
