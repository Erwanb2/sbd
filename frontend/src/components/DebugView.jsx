import { useState } from 'react';
import { formatTemps, getScoreColor } from '../utils/helpers.js';

// L'onglet debug : TOUT ce que le modèle a rendu, mis en face du catalogue, et tout
// ce que le backend en a fait. La page principale ne montre que ce qui cloche ; ici
// rien n'est résumé — chaque champ, la question posée, l'observation libre écrite
// avant de répondre, l'état choisi, sa note, les autres états possibles, les
// segments écartés, l'épingle, le persona, les tokens, le prompt et les pensées du modèle.
//
// La forme lue est `result.debug`, produit par `rules._debug` côté backend, plus
// les blocs déjà présents dans `result` (épingle, structure, persona, tenue du set).

const Badge = ({ note }) => (
  <span className={ `inline-flex h-6 min-w-[1.5rem] items-center justify-center rounded-md border px-1.5 font-mono text-xs font-bold ${ getScoreColor(note) }` }>
    { note ?? '–' }
  </span>
);

const Section = ({ titre, sous, children }) => (
  <section className="bg-gray-900 border border-gray-800 rounded-3xl p-5 sm:p-6 shadow-lg">
    <div className="flex flex-wrap items-baseline justify-between gap-2 mb-4">
      <h3 className="text-white font-black uppercase tracking-widest text-sm">{ titre }</h3>
      { sous && <span className="text-xs text-gray-500 font-mono">{ sous }</span> }
    </div>
    { children }
  </section>
);

// Une grille clé → valeur, en mono. `valeur` peut être n'importe quoi : les objets
// sont sérialisés tels quels plutôt que résumés, c'est le principe de l'onglet.
const Fiche = ({ entrees, colonnes = 2 }) => (
  <div className={ `grid grid-cols-1 ${ colonnes === 2 ? 'sm:grid-cols-2' : '' } gap-x-6 gap-y-1 font-mono text-[12px]` }>
    { entrees.filter(([ , v ]) => v !== undefined).map(([ cle, valeur ]) => (
      <div key={ cle } className="flex justify-between gap-3 border-b border-gray-800/60 py-1">
        <span className="text-gray-500 flex-shrink-0">{ cle }</span>
        <span className="text-gray-300 text-right break-words min-w-0">
          { valeur === null ? 'null'
            : typeof valeur === 'object' ? JSON.stringify(valeur)
              : String(valeur) }
        </span>
      </div>
    )) }
  </div>
);

const Brut = ({ titre, valeur }) => (
  <details className="border border-gray-800 rounded-xl bg-black/30">
    <summary className="cursor-pointer px-4 py-2 text-xs uppercase tracking-wider text-gray-500 select-none hover:text-gray-300">
      { titre }
    </summary>
    <pre className="px-4 pb-4 overflow-x-auto text-[11px] leading-relaxed text-gray-400 whitespace-pre-wrap break-words">
      { JSON.stringify(valeur, null, 2) }
    </pre>
  </details>
);

// Un indicateur : la question, la réponse du modèle, ce qu'elle vaut, et ce qu'il
// aurait pu répondre. Les états possibles viennent du catalogue, une seule copie.
const Indicateur = ({ fiche, cat }) => {
  const [ ouvert, setOuvert ] = useState(false);
  const inconnu = fiche.etat === null && fiche.reponse_brute != null;
  return (
    <div className="border-b border-gray-800/70 py-3 last:border-b-0">
      <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1.2fr)_minmax(0,2fr)] gap-x-5 gap-y-2">
        <div className="min-w-0">
          <button
            type="button"
            onClick={ () => setOuvert((v) => !v) }
            className="text-left font-mono text-[13px] text-white hover:text-emerald-300 transition-colors break-all"
            title="Show the question and the possible states"
          >
            { fiche.nom }
          </button>
          <p className="font-mono text-[11px] text-gray-500 mt-0.5">
            { cat?.id } · { cat?.critere ?? 'descriptive' } · { cat?.phase } · { cat?.source } · { cat?.vue }
          </p>
        </div>

        <div className="min-w-0">
          <div className="flex items-start gap-2">
            <Badge note={ fiche.note } />
            <div className="min-w-0">
              <p className={ `font-mono text-[13px] break-all ${ inconnu ? 'text-red-400' : 'text-gray-100' }` }>
                { fiche.etat ?? (inconnu ? `${ fiche.reponse_brute } (unknown to the catalogue)` : 'no answer') }
              </p>
              { fiche.fait && <p className="text-[12px] text-gray-400 leading-snug mt-0.5">{ fiche.fait }</p> }
            </div>
          </div>
        </div>

        <div className="min-w-0">
          { fiche.observation
            ? <p className="text-[13px] text-gray-300 leading-relaxed italic">« { fiche.observation } »</p>
            : <p className="text-[12px] text-gray-600">no free-text observation</p> }
        </div>
      </div>

      { ouvert && cat && (
        <div className="mt-3 rounded-xl bg-black/30 border border-gray-800 p-3 text-[12px]">
          <p className="text-gray-400 leading-relaxed"><span className="text-gray-600 uppercase tracking-wider text-[10px] font-bold mr-2">Question</span>{ cat.question }</p>
          <ul className="mt-2 space-y-1">
            { cat.etats.map((e) => (
              <li key={ e.cle } className={ `flex items-start gap-2 ${ e.cle === fiche.etat ? 'text-white' : 'text-gray-500' }` }>
                <Badge note={ e.note } />
                <span className="font-mono text-[12px] flex-shrink-0">{ e.cle }</span>
                <span className="leading-snug">{ e.description }</span>
              </li>
            )) }
          </ul>
        </div>
      ) }
    </div>
  );
};

const TableIndicateurs = ({ fiches, catalogue }) => (
  <div>
    <div className="hidden md:grid grid-cols-[minmax(0,1.1fr)_minmax(0,1.2fr)_minmax(0,2fr)] gap-x-5 text-[10px] uppercase tracking-wider text-gray-600 font-bold border-b border-gray-800 pb-2">
      <span>Field (click for the question)</span><span>Answer · score</span><span>What the model wrote before answering</span>
    </div>
    { fiches.map((f) => <Indicateur key={ f.nom } fiche={ f } cat={ catalogue?.[f.nom] } />) }
  </div>
);

const Defaut = ({ d }) => (
  <li className="text-[12px] text-gray-400 leading-snug">
    <Badge note={ d.note } /> <span className="font-mono text-gray-200">{ d.nom }:{ d.etat }</span>
    { ' ' }<span className="text-gray-500">({ d.critere }, rep{ d.reps?.length > 1 ? 's' : '' } { d.reps?.join(', ') })</span>
    <p className="ml-8 text-gray-400">{ d.constat }</p>
    { d.a_essayer && <p className="ml-8 text-gray-300">→ { d.a_essayer }</p> }
  </li>
);

export default function DebugView({ result }) {
  const debug = result?.debug;
  const appel = debug?.appel;
  const catalogue = debug?.catalogue || {};
  const criteres = result?.criteres || {};
  const epingle = result?.epingle;
  const structure = result?.structure;
  const persona = result?.persona;
  const tenue = result?.tenue_du_set;

  if (!debug) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-3xl p-6 text-sm text-gray-400">
        This result carries no debug block: it was produced before the debug tab existed.
        Analyze the video again to get one.
      </div>
    );
  }

  return (
    <div className="space-y-5 text-left">
      <Section titre="The call" sous={ appel?.modele || result?.modele }>
        { appel ? (
          <Fiche entrees={ [
            [ 'model', appel.modele ], [ 'fallback', appel.repli ],
            [ 'fps', appel.fps ], [ 'media_resolution', appel.media_resolution ],
            [ 'thinking_level', appel.thinking_level ], [ 'temperature', appel.temperature ],
            [ 'segments sent', appel.segments?.map((s) => `${ s.debut_s }–${ s.fin_s }s`).join(' | ') ],
            [ 'prompt tokens', appel.usage?.prompt_tokens ],
            [ 'thoughts tokens', appel.usage?.thoughts_tokens ],
            [ 'output tokens', appel.usage?.candidates_tokens ],
            [ 'total tokens', appel.usage?.total_tokens ],
            [ 'cost (USD)', appel.usage?.total_usd ],
          ] } />
        ) : (
          <p className="text-[12px] text-gray-500">No call details (demo result: nothing was sent to a model).</p>
        ) }
        { appel?.prompt && (
          <div className="mt-3">
            <details className="border border-gray-800 rounded-xl bg-black/30">
              <summary className="cursor-pointer px-4 py-2 text-xs uppercase tracking-wider text-gray-500 select-none hover:text-gray-300">Prompt</summary>
              <pre className="px-4 pb-4 text-[11px] leading-relaxed text-gray-400 whitespace-pre-wrap">{ appel.prompt }</pre>
            </details>
          </div>
        ) }
        { appel?.pensees && (
          <div className="mt-3">
            <details className="border border-gray-800 rounded-xl bg-black/30">
              <summary className="cursor-pointer px-4 py-2 text-xs uppercase tracking-wider text-gray-500 select-none hover:text-gray-300">
                Thinking
                <span className="normal-case tracking-normal text-gray-600"> · { appel.usage?.thoughts_tokens ?? '?' } tokens, written before the JSON</span>
              </summary>
              <pre className="px-4 pb-4 text-[11px] leading-relaxed text-gray-400 whitespace-pre-wrap">{ appel.pensees }</pre>
            </details>
          </div>
        ) }
      </Section>

      <Section titre="The set" sous={ `${ result?.note_sur_20 ?? '–' }/20 · ${ result?.nb_reps ?? 0 } rep(s)` }>
        <div className="flex flex-wrap gap-2 mb-4">
          { Object.entries(criteres).map(([ cle, c ]) => (
            <span key={ cle } className="inline-flex items-center gap-2 rounded-lg border border-gray-800 bg-black/30 px-2.5 py-1 font-mono text-[12px] text-gray-300">
              { cle } <Badge note={ c.note } /> <span className="text-gray-600">w{ c.poids } · [{ c.notes_par_rep?.map((n) => n ?? '–').join(' ') }]</span>
            </span>
          )) }
        </div>
        <Fiche entrees={ [
          [ 'variante', result?.variante ],
          [ 'segments dropped (bar never left the floor)', result?.segments_ecartes?.length ? result.segments_ecartes.join(', ') : 'none' ],
          [ 'set consistency', tenue ? `${ tenue.etat } — ${ tenue.texte }` : null ],
          [ 'score gap first→last', tenue?.ecart_note ],
          [ 'slowdown ratio', tenue?.ralentissement ],
          [ 'breaks at rep', tenue?.decroche_a ],
          [ 'pose view', result?.contexte?.mesures?.view ],
          [ 'pose visibility', result?.contexte?.mesures?.visibility ],
        ] } />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-5">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-600 font-bold mb-1.5">Pin (what to work on)</p>
            { epingle ? (
              <ul className="space-y-2">
                <Defaut d={ epingle } />
                { epingle.consequences?.length > 0 && (
                  <li className="text-[11px] text-gray-500 uppercase tracking-wider font-bold mt-2">and that is why</li>
                ) }
                { epingle.consequences?.map((c) => <Defaut key={ c.nom } d={ c } />) }
                { epingle.autres?.length > 0 && (
                  <li className="text-[11px] text-gray-500 uppercase tracking-wider font-bold mt-2">separately</li>
                ) }
                { epingle.autres?.map((c) => <Defaut key={ c.nom } d={ c } />) }
              </ul>
            ) : <p className="text-[12px] text-gray-500">no fault to pin</p> }
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-600 font-bold mb-1.5">Structure banner</p>
            { structure ? (
              <div className="text-[12px] text-gray-400">
                <p><span className="font-mono text-gray-200">{ structure.etat }</span> <Badge note={ structure.note } /></p>
                <p className="mt-1">{ structure.texte }</p>
                <ul className="mt-2 space-y-2">{ structure.defauts?.map((d) => <Defaut key={ d.nom } d={ d } />) }</ul>
              </div>
            ) : <p className="text-[12px] text-gray-500">none</p> }
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-600 font-bold mb-1.5">Persona</p>
            { persona ? <Fiche entrees={ Object.entries(persona) } colonnes={ 1 } /> : <p className="text-[12px] text-gray-500">none</p> }
          </div>
        </div>
      </Section>

      { debug.contexte?.length > 0 && (
        <Section titre="Set-level fields" sous="asked once for the whole video">
          <TableIndicateurs fiches={ debug.contexte } catalogue={ catalogue } />
        </Section>
      ) }

      { debug.reps?.map((rep) => (
        <Section
          key={ rep.index }
          titre={ `Rep ${ rep.index }` }
          sous={ `candidate ${ rep.candidat } · ${ formatTemps(rep.debut_s) }–${ formatTemps(rep.fin_s) } · ${ rep.statut }` }
        >
          <div className="flex flex-wrap gap-2 mb-3">
            { Object.entries(rep.notes || {}).map(([ cle, n ]) => (
              <span key={ cle } className="inline-flex items-center gap-1.5 rounded-lg border border-gray-800 bg-black/30 px-2 py-0.5 font-mono text-[11px] text-gray-400">
                { cle } <Badge note={ n } />
              </span>
            )) }
          </div>
          { rep.summary && (
            <p className="text-[13px] text-gray-300 italic mb-4">
              <span className="not-italic text-[10px] uppercase tracking-wider text-gray-600 font-bold mr-2">Summary</span>
              « { rep.summary } »
            </p>
          ) }
          <TableIndicateurs fiches={ rep.indicateurs } catalogue={ catalogue } />
          { rep.hors_catalogue && Object.keys(rep.hors_catalogue).length > 0 && (
            <div className="mt-3">
              <p className="text-[10px] uppercase tracking-wider text-red-400 font-bold mb-1">Fields unknown to the catalogue</p>
              <Fiche entrees={ Object.entries(rep.hors_catalogue) } />
            </div>
          ) }
        </Section>
      )) }

      { debug.ecartes?.map((seg) => (
        <Section
          key={ `ecarte-${ seg.candidat }` }
          titre={ `Dropped segment ${ seg.candidat }` }
          sous={ `${ formatTemps(seg.debut_s) }–${ formatTemps(seg.fin_s) } · the model saw no lift here` }
        >
          { seg.summary && <p className="text-[13px] text-gray-300 italic mb-4">« { seg.summary } »</p> }
          <TableIndicateurs fiches={ seg.indicateurs } catalogue={ catalogue } />
        </Section>
      )) }

      <Section titre="Raw" sous="exactly what came back, and what was built from it">
        <div className="space-y-2">
          <Brut titre="Model output (parsed JSON, untouched)" valeur={ debug.observations_brutes } />
          <Brut titre="Catalogue sent to the model (questions and states)" valeur={ catalogue } />
          <Brut titre="Full result" valeur={ result } />
        </div>
      </Section>
    </div>
  );
}
