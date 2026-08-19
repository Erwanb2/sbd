import { PlayCircle, ChevronDown } from 'lucide-react';
import { formatKey, getScoreColor } from '../utils/helpers';

export default function ResultCard({ criterionKey, data, isExpanded, onToggle, demoUrl }) {
  const score = data.note;

  return (
    <div 
      onClick={onToggle}
      className={`flex flex-col p-5 rounded-2xl border cursor-pointer transition-all duration-300 hover:bg-gray-800/50 ${getScoreColor(score)}`}
    >
      <div className="flex justify-between items-center">
        <span className="font-bold text-white text-lg">{formatKey(criterionKey)}</span>
        <div className="flex items-center gap-4">
          <span className="text-xl font-bold">{score}/3</span>
          <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${isExpanded ? 'rotate-180 text-white' : 'text-gray-500'}`} />
        </div>
      </div>
      
      {/* Barres de score */}
      <div className="flex gap-1 w-full mt-3 mb-4">
        {[1, 2, 3].map((star) => (
          <div key={star} className={`flex-1 h-1.5 rounded-full ${star <= score ? 'bg-current' : 'bg-gray-800/50'}`} />
        ))}
      </div>

      {/* Le commentaire du coach */}
      <div className="bg-black/30 p-4 rounded-xl border border-current/10">
        <p className="text-[15px] opacity-90 leading-relaxed italic text-white/90">
          "{data.commentaire}"
        </p>
      </div>

      {/* ZONE VIDÉO DÉMO (Cachée par défaut) */}
      <div className={`overflow-hidden transition-all duration-500 ease-in-out ${isExpanded ? 'max-h-96 mt-4 opacity-100' : 'max-h-0 opacity-0'}`}>
        <div className="bg-gray-950 rounded-xl p-4 flex flex-col items-center justify-center border border-gray-800">
          {demoUrl ? (
            <img src={demoUrl} alt="Demo" className="rounded-lg max-h-64 object-cover" />
          ) : (
            <div className="flex flex-col items-center text-gray-500 py-10">
              <PlayCircle className="w-12 h-12 mb-3 opacity-30" />
              <span className="text-sm font-medium uppercase tracking-wider">Vidéo démo à venir</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}