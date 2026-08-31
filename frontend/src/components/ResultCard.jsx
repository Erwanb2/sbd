import { PlayCircle, ChevronDown, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { formatKey, getScoreColor } from '../utils/helpers';

export default function ResultCard({ criterionKey, data, isExpanded, onToggle, demo }) {
  const score = data.score;
  // Le backend renvoie score: null quand le critère n'est pas visible à l'image.
  const notAssessable = score === null || score === undefined;

  // On détermine si la démo est un guide complet (objet avec bad/good) ou un lien simple
  const isDetailedGuide = demo && typeof demo === 'object' && demo.bad && demo.good;
  const isSimpleUrl = demo && typeof demo === 'string';

  return (
    <div 
      onClick={onToggle}
      className={`flex flex-col p-5 rounded-2xl border cursor-pointer transition-all duration-300 hover:bg-gray-800/50 ${getScoreColor(score)}`}
    >
      <div className="flex justify-between items-center">
        <span className="font-bold text-white text-lg">{formatKey(criterionKey)}</span>
        <div className="flex items-center gap-4">
          {notAssessable ? (
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-1 rounded-md bg-gray-500/15 border border-gray-500/30">
              Not visible
            </span>
          ) : (
            <span className="text-xl font-bold">{score}/3</span>
          )}
          <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${isExpanded ? 'rotate-180 text-white' : 'text-gray-500'}`} />
        </div>
      </div>

      {/* Barres de score — masquées si le critère n'a pas pu être noté */}
      {!notAssessable && (
        <div className="flex gap-1 w-full mt-3 mb-4">
          {[1, 2, 3].map((star) => (
            <div key={star} className={`flex-1 h-1.5 rounded-full ${star <= score ? 'bg-current' : 'bg-gray-800/50'}`} />
          ))}
        </div>
      )}
      {notAssessable && <div className="mt-3 mb-4" />}

      {/* Le commentaire du coach */}
      <div className="bg-black/30 p-4 rounded-xl border border-current/10">
        <p className="text-[15px] opacity-90 leading-relaxed italic text-white/90">
          "{data.feedback}"
        </p>
      </div>

      {/* ZONE GUIDE & DEMO DÉPLIABLE */}
      <div className={`overflow-hidden transition-all duration-500 ease-in-out ${isExpanded ? 'max-h-[1200px] mt-4 opacity-100' : 'max-h-0 opacity-0'}`}>
        
        {/* CAS 1 : Guide comparatif complet (comme le Leg Drive) */}
        {isDetailedGuide ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            
            {/* CARTE ERREUR */}
            <div className="bg-red-950/20 border border-red-900/40 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3 text-red-400 font-bold text-sm uppercase tracking-wide">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Image 1 : {demo.bad.title}</span>
                </div>

                <div className="rounded-lg overflow-hidden bg-black/60 mb-4 border border-red-900/30">
                  <img 
                    src={demo.bad.image} 
                    alt="Mauvaise exécution" 
                    className="w-full h-48 object-contain"
                  />
                </div>

                <div className="space-y-2 text-xs md:text-sm text-gray-300">
                  <p>
                    <span className="font-semibold text-red-400">❌ Ce qu'il ne faut pas faire : </span>
                    {demo.bad.description}
                  </p>
                  <p>
                    <span className="font-semibold text-red-400">Le problème : </span>
                    {demo.bad.problem}
                  </p>
                </div>
              </div>
            </div>

            {/* CARTE BONNE POSTURE */}
            <div className="bg-emerald-950/20 border border-emerald-900/40 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3 text-emerald-400 font-bold text-sm uppercase tracking-wide">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Image 2 : {demo.good.title}</span>
                </div>

                <div className="rounded-lg overflow-hidden bg-black/60 mb-4 border border-emerald-900/30">
                  <img 
                    src={demo.good.image} 
                    alt="Bonne posture" 
                    className="w-full h-48 object-contain"
                  />
                </div>

                <div className="space-y-2 text-xs md:text-sm text-gray-300">
                  <p>
                    <span className="font-semibold text-emerald-400">✅ Ce qu'il faut faire : </span>
                    {demo.good.description}
                  </p>
                  <p>
                    <span className="font-semibold text-emerald-400">L'astuce : </span>
                    {demo.good.tip}
                  </p>
                </div>
              </div>
            </div>

          </div>
        ) : isSimpleUrl ? (
          /* CAS 2 : Démo simple (GIF/Vidéo) */
          <div className="bg-gray-950 rounded-xl p-4 flex flex-col items-center justify-center border border-gray-800">
            <img src={demo} alt="Demo" className="rounded-lg max-h-64 object-cover" />
          </div>
        ) : (
          /* CAS 3 : Pas de démo */
          <div className="bg-gray-950 rounded-xl p-4 flex flex-col items-center justify-center border border-gray-800">
            <div className="flex flex-col items-center text-gray-500 py-6">
              <PlayCircle className="w-10 h-10 mb-2 opacity-30" />
              <span className="text-xs font-medium uppercase tracking-wider">Guide à venir</span>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}