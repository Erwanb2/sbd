import { getScoreColor } from '../utils/helpers';

// Hauteur minimale d'une barre, en pourcentage : une rep très faible doit
// rester visible et cliquable.
const HAUTEUR_MIN = 10;

// La hauteur suit la note NON ARRONDIE de la rep (`note_precise`), pas son badge :
// c'est ce qui permet de distinguer deux reps que l'arrondi met à égalité.
const hauteur = (rep) =>
  rep.note_precise ? Math.max(HAUTEUR_MIN, Math.round((rep.note_precise / rep.sur) * 100)) : HAUTEUR_MIN;

// Seules les reps parfaites sont mises en valeur. Pas de mise en valeur
// négative : le graphique est là pour montrer à l'utilisateur ses belles reps.
// Ce qui ne va pas est déjà dit, en toutes lettres, dans les critères.
const estParfaite = (rep) => rep.note === rep.sur && !rep.non_evaluables;

// Histogramme du set : une barre par rep, cliquable, et le détail des critères
// de la rep sélectionnée. `tenue` est la phrase calculée sur la tenue du set.
export default function RepHistogram({ reps, tenue, selected, onSelect }) {
  if (!reps?.length) return null;

  const ouverte = reps.find((r) => r.index === selected) || null;

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
      { /* La tenue du set est calculée (écart de note et de durée entre la première
           et la dernière rep), pas jugée à l'œil : elle a sa place ici, sous les barres
           qu'elle décrit, plutôt que dans un bloc de plus. */ }
      <p className="text-sm text-gray-400 mt-1">
        { tenue || 'Tap a bar for the full breakdown of that rep.' }
      </p>

      <div className="flex items-end justify-center gap-3 sm:gap-4 h-44 mt-6">
        { reps.map((rep) => {
          const actif = rep.index === selected;
          const parfaite = estParfaite(rep);

          return (
            <button
              key={ rep.index }
              onClick={ () => onSelect(actif ? null : rep.index) }
              aria-pressed={ actif }
              title={ `Rep ${ rep.index }${ rep.temps?.tiree_s ? ` — ${ rep.temps.tiree_s }s pull` : '' }` }
              className="group flex-1 min-w-0 max-w-[120px] h-full flex flex-col justify-end items-center gap-2"
            >
              <span
                className={ `text-[11px] font-bold tabular-nums transition-colors ${
                  parfaite ? 'text-emerald-400' : actif ? 'text-white' : 'text-gray-500'
                }` }
              >
                { rep.note == null ? '–' : `${ rep.note }/${ rep.sur }` }
              </span>

              <div
                style={ { height: `${ hauteur(rep) }%` } }
                className={ `w-full rounded-t-lg transition-all duration-300 ${
                  parfaite
                    ? 'bg-gradient-to-t from-emerald-700/60 to-emerald-400 shadow-[0_0_24px_-4px] shadow-emerald-500/60'
                    : 'bg-gray-700 group-hover:bg-gray-600'
                } ${ actif ? 'ring-2 ring-white/70' : '' }` }
              />

              <span className={ `text-xs font-bold ${ actif ? 'text-white' : 'text-gray-500' }` }>
                { rep.index }
              </span>
            </button>
          );
        }) }
      </div>

      { ouverte && (
        <div className="mt-6 border-t border-gray-800 pt-5 animate-fade-in">
          <div className="flex items-baseline justify-between gap-3 mb-1">
            <h4 className="text-white font-black">
              Rep { ouverte.index }
              { ouverte.statut === 'incomplete' && (
                <span className="ml-2 align-middle text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-300 border border-amber-500/30">
                  Not locked out
                </span>
              ) }
            </h4>
            <span className="text-xs text-gray-500 font-mono tabular-nums whitespace-nowrap">
              { ouverte.temps?.tiree_s ? `${ ouverte.temps.tiree_s }s pull` : '' }
            </span>
          </div>
          { ouverte.resume && (
            <p className="text-sm text-gray-400 italic mb-4">{ ouverte.resume }</p>
          ) }

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            { Object.entries(ouverte.criteres).map(([ cle, critere ]) => (
              <div key={ cle } className={ `rounded-xl border p-3 ${ getScoreColor(critere.note) }` }>
                <div className="flex items-start justify-between gap-3">
                  <span className="text-[13px] font-bold text-white leading-tight">
                    { critere.libelle }
                  </span>
                  <span className="text-xs font-bold whitespace-nowrap">
                    { critere.note != null
                      ? `${ critere.note }/${ ouverte.sur }`
                      : critere.statut === 'non_applicable' ? 'N/A' : 'Not visible' }
                  </span>
                </div>
                { /* Les faits observés, dans les mots du catalogue. Il n'y a plus de
                     commentaire écrit par le modèle : ce qui est montré ici est
                     exactement ce qui a produit la note, donc ne peut pas la contredire. */ }
                <ul className="mt-1.5 space-y-1">
                  { critere.faits.map((f) => (
                    <li key={ f.indicateur } className="text-xs leading-relaxed text-white/70">
                      { f.fait }
                    </li>
                  )) }
                </ul>
              </div>
            )) }
          </div>
        </div>
      ) }
    </div>
  );
}
