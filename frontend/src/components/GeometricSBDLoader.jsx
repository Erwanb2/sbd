import { useState, useEffect } from 'react';

// Constantes d'animation partagées pour synchroniser les 3 lifters
const REP = '1.8s';
const EASE = '0.45 0 0.55 1;0.45 0 0.55 1';

const bodyStroke = {
  fill: 'none',
  stroke: '#c7d2fe',
  strokeWidth: 4,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

// Sous-composant Barbell avec option "Vue de coupe" (isSideView)
const Barbell = ({ span = 22, plate = 7, values, begin, isSideView = false }) => (
  <g filter="url(#sbdGlow)">
    <animateTransform
      attributeName="transform" 
      type="translate" 
      additive="replace"
      values={ values } 
      keyTimes="0;0.5;1" 
      calcMode="spline" 
      keySplines={ EASE }
      dur={ REP } 
      begin={ begin } 
      repeatCount="indefinite"
    />
    
    { isSideView ? (
      // --- VUE DE COUPE (Profil pour le Bench) ---
      <>
        { /* Grand disque extérieur */ }
        <circle cx="0" cy="0" r={ plate * 1.35 } fill="#4f46e5" />
        { /* Détail intérieur du disque */ }
        <circle cx="0" cy="0" r={ plate * 0.7 } fill="#c7d2fe" opacity="0.8" />
        { /* Extrémité de la barre (Sleeve) */ }
        <circle cx="0" cy="0" r="2.5" fill="#a5b4fc" />
        { /* Centre creux de la barre */ }
        <circle cx="0" cy="0" r="1" fill="#312e81" />
      </>
    ) : (
      // --- VUE DE FACE (Squat et Deadlift) ---
      <>
        <line x1={ -span } y1="0" x2={ span } y2="0" stroke="#a5b4fc" strokeWidth="3" strokeLinecap="round" />
        <circle cx={ -span } cy="0" r={ plate } fill="#4f46e5" />
        <circle cx={ span } cy="0" r={ plate } fill="#4f46e5" />
        <circle cx={ -span } cy="0" r={ plate * 0.42 } fill="#c7d2fe" />
        <circle cx={ span } cy="0" r={ plate * 0.42 } fill="#c7d2fe" />
        <circle cx={ -span + 6 } cy="0" r="2.4" fill="#6366f1" />
        <circle cx={ span - 6 } cy="0" r="2.4" fill="#6366f1" />
      </>
    ) }
  </g>
);

// Sous-composant Flex (pour l'animation des bras/jambes)
const Flex = ({ attr = 'd', values, begin, type }) => (
  <animate
    attributeName={ attr } 
    { ...(type ? { type } : { }) }
    values={ values } 
    keyTimes="0;0.5;1" 
    calcMode="spline" 
    keySplines={ EASE }
    dur={ REP } 
    begin={ begin } 
    repeatCount="indefinite"
  />
);

export default function GeometricSBDLoader() {
  const statusMessages = [
    'Detecting persona',
    'Evaluating form',
    'Tracking the bar path',
    'Scoring depth & lockout',
    'Compiling results',
  ];
  
  const [ statusIndex, setStatusIndex ] = useState(0);

  useEffect(() => {
    const id = setInterval(
      () => setStatusIndex((i) => (i + 1) % statusMessages.length),
      1500
    );
    return () => clearInterval(id);
  }, [ statusMessages.length ]);

  return (
    <div className="flex flex-col items-center justify-center p-6 sm:p-8 w-full">
      <style>{ `
        @keyframes sbdSweep { 0%{transform:translateX(-130%)} 100%{transform:translateX(340%)} }
        @keyframes sbdShimmer { 0%{background-position:0% 50%} 100%{background-position:200% 50%} }
      ` }</style>

      { /* ---- SCENE : 3 lifters (Squat / Bench / Deadlift) ---- */ }
      <div className="relative w-full max-w-lg">
        <div className="absolute -inset-6 bg-indigo-500/10 blur-3xl rounded-full" />
        <svg
          viewBox="0 0 360 175"
          className="relative w-full overflow-visible"
          role="img"
          aria-label="Animation of three lifters performing squat, bench and deadlift"
        >
          <defs>
            <filter id="sbdGlow" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="1.6" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <linearGradient id="sbdScan" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0" />
              <stop offset="50%" stopColor="#a5b4fc" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
            </linearGradient>
          </defs>

          { /* Ambient rotating rings behind the scene */ }
          <g opacity="0.18" fill="none" stroke="#6366f1">
            <circle cx="180" cy="80" r="84" strokeDasharray="3 10">
              <animateTransform attributeName="transform" type="rotate" from="0 180 80" to="360 180 80" dur="22s" repeatCount="indefinite" />
            </circle>
            <circle cx="180" cy="80" r="62" strokeDasharray="2 12">
              <animateTransform attributeName="transform" type="rotate" from="360 180 80" to="0 180 80" dur="16s" repeatCount="indefinite" />
            </circle>
          </g>

          { /* Analysis scan beam */ }
          <g style={ { animation: 'sbdSweep 4.2s ease-in-out infinite' } }>
            <rect x="0" y="14" width="34" height="140" fill="url(#sbdScan)" opacity="0.35" />
          </g>

          { /* Platform */ }
          <line x1="20" y1="151" x2="340" y2="151" stroke="#4338ca" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
          <line x1="20" y1="151" x2="340" y2="151" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeDasharray="2 14" opacity="0.9" />

          { /* ============================= SQUAT ============================= */ }
          <g transform="translate(60,0)">
            <ellipse cx="0" cy="150" rx="16" ry="3" fill="#312e81">
              <animate attributeName="rx" values="15;20;15" keyTimes="0;0.5;1" dur={ REP } begin="0s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.4;0.7;0.4" keyTimes="0;0.5;1" dur={ REP } begin="0s" repeatCount="indefinite" />
            </ellipse>
            <path style={ bodyStroke }>
              <Flex values="M 10 140 L 12 118 L 0 95 L -12 118 L -10 140;M 10 140 L 20 128 L 0 112 L -20 128 L -10 140;M 10 140 L 12 118 L 0 95 L -12 118 L -10 140" begin="0s" />
            </path>
            <path style={ bodyStroke }>
              <Flex values="M 0 95 L 0 66;M 0 112 L 0 83;M 0 95 L 0 66" begin="0s" />
            </path>
            
            { /* NOUVEAUX BRAS DU SQUAT : Coudes pliés vers le bas, mains sur la barre */ }
            <path style={ { ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' } }>
              <Flex values="M 0 68 L -12 80 L -18 64 M 0 68 L 12 80 L 18 64;M 0 85 L -12 97 L -18 81 M 0 85 L 12 97 L 18 81;M 0 68 L -12 80 L -18 64 M 0 68 L 12 80 L 18 64" begin="0s" />
            </path>

            <circle cx="0" r="7.5" fill="#a5b4fc">
              <Flex attr="cy" values="56;73;56" begin="0s" />
            </circle>
            <Barbell span="36" plate="7" values="0 64;0 81;0 64" begin="0s" />
          </g>

          { /* ============================= BENCH ============================= */ }
          <g transform="translate(180,0)">
            <ellipse cx="0" cy="150" rx="26" ry="3" fill="#312e81" opacity="0.5" />
            { /* Bench */ }
            <rect x="-30" y="112" width="60" height="6" rx="3" fill="#3730a3" />
            <line x1="-22" y1="118" x2="-22" y2="140" stroke="#4338ca" strokeWidth="3" strokeLinecap="round" />
            <line x1="22" y1="118" x2="22" y2="140" stroke="#4338ca" strokeWidth="3" strokeLinecap="round" />
            
            { /* Planted legs */ }
            <path style={ { ...bodyStroke, strokeWidth: 4 } } d="M 16 104 L 28 120 L 26 140" />
            { /* Torso lying on the bench */ }
            <path style={ bodyStroke } d="M 20 104 L -12 104" />
            <circle cx="-22" cy="104" r="6.5" fill="#a5b4fc" />
            
            { /* Pressing arms */ }
            <path style={ { ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' } }>
              <Flex values="M -12 104 L -8 88 L -4 76;M -12 104 L -8 116 L -4 100;M -12 104 L -8 88 L -4 76" begin="-0.6s" />
            </path>
            { /* isSideView={true} active la vue de coupe pour le disque */ }
            <Barbell plate="8.5" values="-4 76;-4 100;-4 76" begin="-0.6s" isSideView={ true } />
          </g>

          { /* ============================ DEADLIFT ============================ */ }
          <g transform="translate(300,0)">
            <ellipse cx="0" cy="150" rx="16" ry="3" fill="#312e81">
              <animate attributeName="rx" values="19;14;19" keyTimes="0;0.5;1" dur={ REP } begin="-1.2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.7;0.4;0.7" keyTimes="0;0.5;1" dur={ REP } begin="-1.2s" repeatCount="indefinite" />
            </ellipse>
            <path style={ bodyStroke }>
              <Flex values="M 10 140 L 13 126 L 0 116 L -13 126 L -10 140;M 10 140 L 11 118 L 0 96 L -11 118 L -10 140;M 10 140 L 13 126 L 0 116 L -13 126 L -10 140" begin="-1.2s" />
            </path>
            <path style={ bodyStroke }>
              <Flex values="M 0 116 L 0 92;M 0 96 L 0 70;M 0 116 L 0 92" begin="-1.2s" />
            </path>
            <circle cx="0" r="7.5" fill="#a5b4fc">
              <Flex attr="cy" values="82;60;82" begin="-1.2s" />
            </circle>
            <path style={ { ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' } }>
              <Flex values="M -12 92 L -13 131 M 12 92 L 13 131;M -12 70 L -12 110 M 12 70 L 12 110;M -12 92 L -13 131 M 12 92 L 13 131" begin="-1.2s" />
            </path>
            <Barbell span="34" plate="7.5" values="0 131;0 110;0 131" begin="-1.2s" />
          </g>

          { /* Discipline labels */ }
          <g fontFamily="monospace" fontSize="8" fontWeight="700" letterSpacing="2" fill="#818cf8" textAnchor="middle">
            <text x="60" y="168">
              SQUAT
              <animate attributeName="opacity" values="0.35;1;0.35" keyTimes="0;0.5;1" dur={ REP } begin="0s" repeatCount="indefinite" />
            </text>
            <text x="180" y="168">
              BENCH
              <animate attributeName="opacity" values="0.35;1;0.35" keyTimes="0;0.5;1" dur={ REP } begin="-0.6s" repeatCount="indefinite" />
            </text>
            <text x="300" y="168">
              DEADLIFT
              <animate attributeName="opacity" values="0.35;1;0.35" keyTimes="0;0.5;1" dur={ REP } begin="-1.2s" repeatCount="indefinite" />
            </text>
          </g>
        </svg>
      </div>

      { /* ---- STATUS + INDETERMINATE PROGRESS ---- */ }
      <div className="mt-8 flex flex-col items-center gap-4 w-full max-w-sm">
        <div
          className="font-mono text-sm sm:text-base uppercase tracking-[0.3em] font-bold text-transparent bg-clip-text"
          style={ {
            backgroundImage: 'linear-gradient(90deg,#6366f1,#a5b4fc,#818cf8,#a5b4fc,#6366f1)',
            backgroundSize: '200% auto',
            animation: 'sbdShimmer 3s linear infinite',
          } }
        >
          Computing Biomechanics
        </div>

        <div className="h-5 relative w-56 text-center">
          { statusMessages.map((msg, i) => (
            <span
              key={ i }
              className="absolute inset-0 text-xs text-indigo-300/80 font-mono tracking-wide"
              style={ { opacity: i === statusIndex ? 1 : 0, transition: 'opacity 0.4s ease' } }
            >
              { msg } <span className="animate-pulse">…</span>
            </span>
          )) }
        </div>

        <div className="w-full h-1.5 rounded-full bg-indigo-950/80 overflow-hidden border border-indigo-500/20">
          <div
            className="h-full w-1/3 rounded-full bg-gradient-to-r from-transparent via-indigo-400 to-transparent"
            style={ { animation: 'sbdSweep 1.4s ease-in-out infinite' } }
          />
        </div>

        <div className="flex justify-center gap-1.5">
          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={ { animationDelay: '0s' } } />
          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={ { animationDelay: '0.15s' } } />
          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={ { animationDelay: '0.3s' } } />
        </div>
      </div>
    </div>
  );
}