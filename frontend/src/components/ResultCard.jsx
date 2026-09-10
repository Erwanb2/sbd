import { PlayCircle, ChevronDown, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { getScoreColor } from '../utils/helpers';

// Une carte de critère. `data` vient de `result.criteres[cle]` :
// { libelle, note, poids, notes_par_rep, faits }.
//
// Il n'y a plus de commentaire écrit par le modèle. La carte montre les FAITS
// observés — les états du catalogue qui ont produit la note — avec les répétitions
// concernées. Un texte qui est la cause de la note ne peut pas la contredire, ce
// qu'un paragraphe généré à côté pouvait faire.
export default function ResultCard({ data, isExpanded, onToggle, demo }) {
  const note = data.note;
  const nonEvaluable = note === null || note === undefined;
  const faits = data.faits || [];

  // On ne montre d'emblée que ce qui cloche : les faits notés en dessous du maximum,
  // et ceux qu'on n'a pas pu voir. Tout dire — y compris les huit choses qui vont
  // bien — transforme chaque critère en pavé et double la longueur de la page, alors
  // que la barre verte dit déjà que le reste est bon. Le détail complet reste à un
  // clic, dans le dépliant.
  const aCorriger = faits.filter((f) => f.note === null || f.note < 3);
  const enOrdre = aCorriger.length > 0 ? aCorriger : faits.slice(0, 1);
  const reste = faits.filter((f) => !enOrdre.includes(f));

  const isDetailedGuide = demo && typeof demo === 'object' && demo.bad && demo.good;
  const isSimpleUrl = demo && typeof demo === 'string';
  // La partie qui APPREND : identique d'une vidéo à l'autre, c'est ce qui fait qu'au
  // troisième upload le lifter connaît les six mécaniques par leur nom.
  const cours = demo && typeof demo === 'object' && demo.what ? demo : null;

  return (
    <div
      onClick={ onToggle }
      className={ `flex flex-col p-5 rounded-2xl border cursor-pointer transition-all duration-300 hover:bg-gray-800/50 ${ getScoreColor(note) }` }
    >
      <div className="flex justify-between items-center">
        <span className="font-bold text-white text-lg">{ data.libelle }</span>
        <div className="flex items-center gap-4">
          { nonEvaluable ? (
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-1 rounded-md bg-gray-500/15 border border-gray-500/30">
              Not visible
            </span>
          ) : (
            <span className="text-xl font-bold">{ note }/3</span>
          ) }
          <ChevronDown className={ `w-5 h-5 transition-transform duration-300 ${ isExpanded ? 'rotate-180 text-white' : 'text-gray-500' }` } />
        </div>
      </div>

      { !nonEvaluable && (
        <div className="flex gap-1 w-full mt-3 mb-4">
          { [ 1, 2, 3 ].map((cran) => (
            <div key={ cran } className={ `flex-1 h-1.5 rounded-full ${ cran <= note ? 'bg-current' : 'bg-gray-800/50' }` } />
          )) }
        </div>
      ) }
      { nonEvaluable && <div className="mt-3 mb-4" /> }

      { enOrdre.length > 0 && (
        <div className="bg-black/30 p-4 rounded-xl border border-current/10 space-y-2">
          { enOrdre.map((f) => (
            <div key={ f.indicateur } className="flex items-start gap-2.5">
              <span
                className={ `mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full ${
                  f.note === 3 ? 'bg-emerald-400' : f.note === 2 ? 'bg-amber-400'
                    : f.note === 1 ? 'bg-red-400' : 'bg-gray-600'
                }` }
              />
              <p className="text-[15px] leading-relaxed text-white/90">
                { f.fait }
                { /* Sur un set, savoir QUE le défaut est là compte moins que savoir OÙ.
                     On ne nomme les reps que s'il y en a plusieurs. */ }
                { f.reps.length > 0 && data.notes_par_rep.length > 1 && (
                  <span className="ml-1.5 text-xs text-white/40 whitespace-nowrap">
                    rep{ f.reps.length > 1 ? 's' : '' } { f.reps.join(', ') }
                  </span>
                ) }
              </p>
            </div>
          )) }
        </div>
      ) }

      <div className={ `overflow-hidden transition-all duration-500 ease-in-out ${ isExpanded ? 'max-h-[1600px] mt-4 opacity-100' : 'max-h-0 opacity-0' }` }>
        { reste.length > 0 && (
          <div className="mb-4 rounded-xl border border-gray-800 bg-gray-950/60 p-4">
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
              Also observed
            </span>
            <ul className="mt-2 space-y-1.5">
              { reste.map((f) => (
                <li key={ f.indicateur } className="flex items-start gap-2.5 text-sm text-gray-400">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500/60" />
                  <span>{ f.fait }</span>
                </li>
              )) }
            </ul>
          </div>
        ) }

        { cours && (
          <div className="mb-4 rounded-xl border border-gray-800 bg-gray-950/60 p-4 space-y-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-500/70">
                What good looks like
              </span>
              <p className="mt-1 text-sm leading-relaxed text-gray-300">{ cours.what }</p>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400/70">
                Cue
              </span>
              <p className="mt-1 text-sm leading-relaxed text-white/90 italic">“{ cours.cue }”</p>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                Drill it
              </span>
              <p className="mt-1 text-sm leading-relaxed text-gray-400">{ cours.drill }</p>
            </div>
          </div>
        ) }

        { isDetailedGuide ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="bg-red-950/20 border border-red-900/40 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3 text-red-400 font-bold text-sm uppercase tracking-wide">
                <AlertTriangle className="w-4 h-4" />
                <span>Image 1 : { demo.bad.title }</span>
              </div>
              <div className="rounded-lg overflow-hidden bg-black/60 mb-4 border border-red-900/30">
                <img src={ demo.bad.image } alt="Mauvaise exécution" className="w-full h-48 object-contain" />
              </div>
              <div className="space-y-2 text-xs md:text-sm text-gray-300">
                <p><span className="font-semibold text-red-400">❌ Ce qu'il ne faut pas faire : </span>{ demo.bad.description }</p>
                <p><span className="font-semibold text-red-400">Le problème : </span>{ demo.bad.problem }</p>
              </div>
            </div>

            <div className="bg-emerald-950/20 border border-emerald-900/40 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3 text-emerald-400 font-bold text-sm uppercase tracking-wide">
                <CheckCircle2 className="w-4 h-4" />
                <span>Image 2 : { demo.good.title }</span>
              </div>
              <div className="rounded-lg overflow-hidden bg-black/60 mb-4 border border-emerald-900/30">
                <img src={ demo.good.image } alt="Bonne posture" className="w-full h-48 object-contain" />
              </div>
              <div className="space-y-2 text-xs md:text-sm text-gray-300">
                <p><span className="font-semibold text-emerald-400">✅ Ce qu'il faut faire : </span>{ demo.good.description }</p>
                <p><span className="font-semibold text-emerald-400">L'astuce : </span>{ demo.good.tip }</p>
              </div>
            </div>
          </div>
        ) : isSimpleUrl ? (
          <div className="bg-gray-950 rounded-xl p-4 flex flex-col items-center justify-center border border-gray-800">
            <img src={ demo } alt="Demo" className="rounded-lg max-h-64 object-cover" />
          </div>
        ) : !cours ? (
          <div className="bg-gray-950 rounded-xl p-4 flex flex-col items-center justify-center border border-gray-800">
            <div className="flex flex-col items-center text-gray-500 py-6">
              <PlayCircle className="w-10 h-10 mb-2 opacity-30" />
              <span className="text-xs font-medium uppercase tracking-wider">Guide à venir</span>
            </div>
          </div>
        ) : null }
      </div>
    </div>
  );
}
