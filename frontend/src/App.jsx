import { useState, useEffect } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import Header from './components/Header.jsx';
import UploadZone from './components/UploadZone.jsx';
import ResultCard from './components/ResultCard.jsx';
import LoadingProgress from './components/LoadingProgress.jsx';
import ProfileModal from './components/ProfileModal.jsx';

// IMPORT PROPRE DES GUIDES
import { criteriaGuides } from './data/criteriaGuides.js';

function AdBannerPlaceholder({ className = '', format = 'banner' }) {
  return (
    <div
      className={`w-full bg-gray-900/60 border border-dashed
border-gray-700/70 rounded-2xl p-4 flex flex-col items-center
justify-center text-center overflow-hidden ${format === 'rectangle' ?
'min-h-[250px]' : 'min-h-[90px]'} ${className}`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] uppercase font-bold
tracking-widest text-gray-400 bg-gray-800 px-2 py-0.5 rounded border
border-gray-700">
          Sponsored / Advertisement
        </span>
      </div>
      <p className="text-xs text-gray-400">
        Google AdSense Reserved Space (Free Users)
      </p>
    </div>
  );
}

const getPersonaAssets = (persona) => {
  if (!persona) return { emoji: "🏋️", filename: "default.webp" };
  const p = persona.toLowerCase();

  if (p.includes('technician')) return { emoji: "🥇", filename:
"technician.webp" };
  if (p.includes('grip')) return { emoji: "🚀", filename: "grip-and-rip.webp" };
  if (p.includes('crane')) return { emoji: "🏗️", filename: "crane.webp" };
  if (p.includes('squatter')) return { emoji: "📉", filename: "squatter.webp" };
  if (p.includes('fishing')) return { emoji: "🎣", filename:
"fishing-rod.webp" };
  if (p.includes('extender')) return { emoji: "⚠️", filename:
"over-extender.webp" };
  if (p.includes('hitcher')) return { emoji: "🛑", filename: "hitcher.webp" };

  return { emoji: "💪", filename: "default.webp" };
};

const loadingTips = {
  "squat": "Focus on bracing your core before descending to maintain a neutral spine under heavy load.",
  "bench": "Keep your shoulder blades retracted and depressed into the bench to protect your shoulders.",
  "Conventional deadlift": "Ensure the bar is exactly over you mid-foot before you pull the slack out.",
  "Sumo deadlift": "Think about 'spreading the floor' apart with your feet to engage your adductors and glutes."
};

// Timing shared by every figure so the three lifters stay in a coherent rhythm.
const REP = '1.8s';
const EASE = '0.45 0 0.55 1;0.45 0 0.55 1';

// Small helper: a geometric barbell (bar + weight plates + collars) that can be
// translated as a whole via an <animateTransform>.
const Barbell = ({ span = 22, plate = 7, values, begin }) => (
  <g filter="url(#sbdGlow)">
    <animateTransform
      attributeName="transform" type="translate" additive="replace"
      values={values} keyTimes="0;0.5;1" calcMode="spline" keySplines={EASE}
      dur={REP} begin={begin} repeatCount="indefinite"
    />
    <line x1={-span} y1="0" x2={span} y2="0" stroke="#a5b4fc"
strokeWidth="3" strokeLinecap="round" />
    <circle cx={-span} cy="0" r={plate} fill="#4f46e5" />
    <circle cx={span} cy="0" r={plate} fill="#4f46e5" />
    <circle cx={-span} cy="0" r={plate * 0.42} fill="#c7d2fe" />
    <circle cx={span} cy="0" r={plate * 0.42} fill="#c7d2fe" />
    <circle cx={-span + 6} cy="0" r="2.4" fill="#6366f1" />
    <circle cx={span - 6} cy="0" r="2.4" fill="#6366f1" />
  </g>
);

// A single animated attribute (d / cy / transform) driving a body segment.
const Flex = ({ attr = 'd', values, begin, type }) => (
  <animate
    attributeName={attr} {...(type ? { type } : {})}
    values={values} keyTimes="0;0.5;1" calcMode="spline" keySplines={EASE}
    dur={REP} begin={begin} repeatCount="indefinite"
  />
);

const bodyStroke = {
  fill: 'none', stroke: '#c7d2fe', strokeWidth: 4,
  strokeLinecap: 'round', strokeLinejoin: 'round',
};

const GeometricSBDLoader = () => {
  const statusMessages = [
    'Detecting body joints',
    'Measuring joint angles',
    'Tracking the bar path',
    'Scoring depth & lockout',
    'Compiling biomechanics',
  ];
  const [statusIndex, setStatusIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(
      () => setStatusIndex((i) => (i + 1) % statusMessages.length),
      1500
    );
    return () => clearInterval(id);
  }, [statusMessages.length]);

  return (
    <div className="flex flex-col items-center justify-center p-6
sm:p-8 w-full">
      <style>{`
        @keyframes sbdSweep { 0%{transform:translateX(-130%)}
100%{transform:translateX(340%)} }
        @keyframes sbdShimmer { 0%{background-position:0% 50%}
100%{background-position:200% 50%} }
        @keyframes sbdStatus {
0%,100%{opacity:0;transform:translateY(4px)}
15%,85%{opacity:1;transform:translateY(0)} }
      `}</style>

      {/* ---- SCENE : 3 lifters (Squat / Bench / Deadlift) in simple
geometry ---- */}
      <div className="relative w-full max-w-lg">
        <div className="absolute -inset-6 bg-indigo-500/10 blur-3xl
rounded-full" />
        <svg
          viewBox="0 0 360 175"
          className="relative w-full overflow-visible"
          role="img"
          aria-label="Animation of three lifters performing squat,
bench and deadlift"
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

          {/* Ambient rotating rings behind the scene */}
          <g opacity="0.18" fill="none" stroke="#6366f1">
            <circle cx="180" cy="80" r="84" strokeDasharray="3 10">
              <animateTransform attributeName="transform"
type="rotate" from="0 180 80" to="360 180 80" dur="22s"
repeatCount="indefinite" />
            </circle>
            <circle cx="180" cy="80" r="62" strokeDasharray="2 12">
              <animateTransform attributeName="transform"
type="rotate" from="360 180 80" to="0 180 80" dur="16s"
repeatCount="indefinite" />
            </circle>
          </g>

          {/* Analysis scan beam sweeping across the platform */}
          <g style={{ animation: 'sbdSweep 4.2s ease-in-out infinite' }}>
            <rect x="0" y="14" width="34" height="140"
fill="url(#sbdScan)" opacity="0.35" />
          </g>

          {/* Platform */}
          <line x1="20" y1="151" x2="340" y2="151" stroke="#4338ca"
strokeWidth="2" strokeLinecap="round" opacity="0.7" />
          <line x1="20" y1="151" x2="340" y2="151" stroke="#6366f1"
strokeWidth="2" strokeLinecap="round" strokeDasharray="2 14"
opacity="0.9" />

          {/* ============================= SQUAT
============================= */}
          <g transform="translate(60,0)">
            <ellipse cx="0" cy="150" rx="16" ry="3" fill="#312e81">
              <animate attributeName="rx" values="15;20;15"
keyTimes="0;0.5;1" dur={REP} begin="0s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.4;0.7;0.4"
keyTimes="0;0.5;1" dur={REP} begin="0s" repeatCount="indefinite" />
            </ellipse>

            <path style={bodyStroke}>
              <Flex values="M 10 140 L 12 118 L 0 95 L -12 118 L -10
140;M 10 140 L 20 128 L 0 112 L -20 128 L -10 140;M 10 140 L 12 118 L
0 95 L -12 118 L -10 140" begin="0s" />
            </path>
            <path style={bodyStroke}>
              <Flex values="M 0 95 L 0 66;M 0 112 L 0 83;M 0 95 L 0
66" begin="0s" />
            </path>
            <path style={{ ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' }}>
              <Flex values="M 0 68 L -16 63 M 0 68 L 16 63;M 0 85 L
-16 80 M 0 85 L 16 80;M 0 68 L -16 63 M 0 68 L 16 63" begin="0s" />
            </path>
            <circle cx="0" r="7.5" fill="#a5b4fc">
              <Flex attr="cy" values="56;73;56" begin="0s" />
            </circle>
            <Barbell span="24" plate="7" values="0 64;0 81;0 64" begin="0s" />
          </g>

          {/* ============================= BENCH
============================= */}
          <g transform="translate(180,0)">
            <ellipse cx="0" cy="150" rx="26" ry="3" fill="#312e81"
opacity="0.5" />
            {/* Bench */}
            <rect x="-30" y="112" width="60" height="6" rx="3" fill="#3730a3" />
            <line x1="-22" y1="118" x2="-22" y2="140" stroke="#4338ca"
strokeWidth="3" strokeLinecap="round" />
            <line x1="22" y1="118" x2="22" y2="140" stroke="#4338ca"
strokeWidth="3" strokeLinecap="round" />
            {/* Planted legs */}
            <path style={{ ...bodyStroke, strokeWidth: 4 }} d="M 16
104 L 28 120 L 26 140" />
            {/* Torso lying on the bench */}
            <path style={bodyStroke} d="M 20 104 L -12 104" />
            <circle cx="-22" cy="104" r="6.5" fill="#a5b4fc" />
            {/* Pressing arms */}
            <path style={{ ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' }}>
              <Flex values="M -12 104 L -8 88 L -4 76;M -12 104 L -21
98 L -4 100;M -12 104 L -8 88 L -4 76" begin="-0.6s" />
            </path>
            <Barbell span="18" plate="6" values="-4 76;-4 100;-4 76"
begin="-0.6s" />
          </g>

          {/* ============================ DEADLIFT
============================ */}
          <g transform="translate(300,0)">
            <ellipse cx="0" cy="150" rx="16" ry="3" fill="#312e81">
              <animate attributeName="rx" values="19;14;19"
keyTimes="0;0.5;1" dur={REP} begin="-1.2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.7;0.4;0.7"
keyTimes="0;0.5;1" dur={REP} begin="-1.2s" repeatCount="indefinite" />
            </ellipse>

            <path style={bodyStroke}>
              <Flex values="M 10 140 L 13 126 L 0 116 L -13 126 L -10
140;M 10 140 L 11 118 L 0 96 L -11 118 L -10 140;M 10 140 L 13 126 L 0
116 L -13 126 L -10 140" begin="-1.2s" />
            </path>
            <path style={bodyStroke}>
              <Flex values="M 0 116 L 0 92;M 0 96 L 0 70;M 0 116 L 0
92" begin="-1.2s" />
            </path>
            <circle cx="0" r="7.5" fill="#a5b4fc">
              <Flex attr="cy" values="82;60;82" begin="-1.2s" />
            </circle>
            <path style={{ ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' }}>
              <Flex values="M -12 92 L -13 131 M 12 92 L 13 131;M -12
70 L -12 110 M 12 70 L 12 110;M -12 92 L -13 131 M 12 92 L 13 131"
begin="-1.2s" />
            </path>
            <Barbell span="26" plate="7.5" values="0 131;0 110;0 131"
begin="-1.2s" />
          </g>

          {/* Discipline labels with a sequential highlight */}
          <g fontFamily="monospace" fontSize="8" fontWeight="700"
letterSpacing="2" fill="#818cf8" textAnchor="middle">
            <text x="60" y="168">
              SQUAT
              <animate attributeName="opacity" values="0.35;1;0.35"
keyTimes="0;0.5;1" dur={REP} begin="0s" repeatCount="indefinite" />
            </text>
            <text x="180" y="168">
              BENCH
              <animate attributeName="opacity" values="0.35;1;0.35"
keyTimes="0;0.5;1" dur={REP} begin="-0.6s" repeatCount="indefinite" />
            </text>
            <text x="300" y="168">
              DEADLIFT
              <animate attributeName="opacity" values="0.35;1;0.35"
keyTimes="0;0.5;1" dur={REP} begin="-1.2s" repeatCount="indefinite" />
            </text>
          </g>
        </svg>
      </div>

      {/* ---- STATUS + INDETERMINATE PROGRESS ---- */}
      <div className="mt-8 flex flex-col items-center gap-4 w-full max-w-sm">
        <div
          className="font-mono text-sm sm:text-base uppercase
tracking-[0.3em] font-bold text-transparent bg-clip-text"
          style={{
            backgroundImage:
'linear-gradient(90deg,#6366f1,#a5b4fc,#818cf8,#a5b4fc,#6366f1)',
            backgroundSize: '200% auto',
            animation: 'sbdShimmer 3s linear infinite',
          }}
        >
          Computing Biomechanics
        </div>

        <div className="h-5 relative w-56 text-center">
          {statusMessages.map((msg, i) => (
            <span
              key={msg}
              className="absolute inset-0 text-xs text-indigo-300/80
font-mono tracking-wide"
              style={{ opacity: i === statusIndex ? 1 : 0, transition:
'opacity 0.4s ease' }}
            >
              {msg}
              <span className="animate-pulse">…</span>
            </span>
          ))}
        </div>

        <div className="w-full h-1.5 rounded-full bg-indigo-950/80
overflow-hidden border border-indigo-500/20">
          <div
            className="h-full w-1/3 rounded-full bg-gradient-to-r
from-transparent via-indigo-400 to-transparent"
            style={{ animation: 'sbdSweep 1.4s ease-in-out infinite' }}
          />
        </div>

        <div className="flex justify-center gap-1.5">
          <div className="w-2 h-2 bg-indigo-500 rounded-full
animate-bounce" style={{ animationDelay: '0s' }} />
          <div className="w-2 h-2 bg-indigo-500 rounded-full
animate-bounce" style={{ animationDelay: '0.15s' }} />
          <div className="w-2 h-2 bg-indigo-500 rounded-full
animate-bounce" style={{ animationDelay: '0.3s' }} />
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [detectedMovement, setDetectedMovement] = useState(null);
  const [expandedCard, setExpandedCard] = useState(null);

  const [tokenAPI, setTokenAPI] = useState(null);
  const [user, setUser] = useState(null);
  const [showProfile, setShowProfile] = useState(false);

  const isFreeUser = user?.plan?.toLowerCase() !== 'premium' &&
user?.plan?.toLowerCase() !== 'pro';

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credentialResponse.credential })
      });

      const data = await res.json();
      if (res.ok) {
        setTokenAPI(data.access_token);
        setUser(data.user);
      } else {
        alert("Authentication error: " + data.detail);
      }
    } catch (error) {
      console.error("Connection error", error);
    }
  };

  const handleUpdateUser = (updatedData) => {
    setUser(prev => ({ ...prev, ...updatedData }));
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    if (!tokenAPI) {
      alert("You must be logged in to analyze a video.");
      return;
    }

    setLoadingStep(1);
    setResult(null);
    setDetectedMovement(null);
    setExpandedCard(null);

    try {
      const formData = new FormData();
      formData.append('video', file);

      // On utilise le bon endpoint !
      const initResponse = await fetch('/api/upload_and_detect', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${tokenAPI}` },
        body: formData,
      });
      const initData = await initResponse.json();

      if (!initResponse.ok) throw new Error(initData.detail ||
"Initialisation failed");

      if (initData.quota_restant !== undefined) {
        setUser(prev => ({ ...prev, quota_left: initData.quota_restant }));
      }
      setDetectedMovement(initData.mouvement_detecte);
      setLoadingStep(2);

      const analyzeResponse = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenAPI}`
        },
        body: JSON.stringify({
          file_name: initData.file_name,
          movement: initData.mouvement_detecte
        }),
      });

      const analyzeData = await analyzeResponse.json();
      if (!analyzeResponse.ok) throw new Error(analyzeData.detail ||
"Analysis error");

      setResult(analyzeData);

    } catch (error) {
      alert(`Error ❌ : ${error.message}`);
    } finally {
      setLoadingStep(0);
    }
  };

  const scoreObtenu = result?.total_raw_score ||
result?.note_globale_brute || 0;
  const scoreMax = result?.raw_max_score || 24;
  const scorePercentage = (scoreObtenu / scoreMax) * 100;

  if (!tokenAPI) {
    return (
      <div className="flex flex-col items-center justify-center
min-h-screen bg-gray-950 text-white gap-6">
        <h1 className="text-4xl font-black uppercase tracking-wider
mb-2">SBD Reviews</h1>
        <p className="text-gray-400 mb-6 text-center max-w-md">
          Sign in with Google to have your form analyzed by our AI.
        </p>
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={() => alert('Login failed')}
          theme="filled_black"
          shape="pill"
        />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 pt-12 pb-24 text-white relative">
      <Header user={user} onOpenProfile={() => setShowProfile(true)} />

      {showProfile && (
        <ProfileModal
          user={user}
          tokenAPI={tokenAPI}
          onClose={() => setShowProfile(false)}
          onUpdateUser={handleUpdateUser}
        />
      )}

      {/* --- ZONE D'UPLOAD + MESSAGE DE CONFIDENTIALITÉ --- */}
      {loadingStep === 0 && !result && (
        <div className="animate-in fade-in duration-500 flex flex-col
items-center w-full">
          <div className="w-full">
            <UploadZone file={file} setFile={setFile}
handleUpload={handleUpload} />
          </div>

          {/* Nouveau placement du message Privacy First (sous la box
d'upload) */}
          <div className="mt-6 bg-emerald-900/20 border
border-emerald-500/30 text-emerald-400 py-3 px-6 rounded-xl flex
flex-col sm:flex-row items-center justify-center gap-3 text-sm
text-center shadow-lg max-w-lg w-full transition-all
hover:bg-emerald-900/30">
            <span className="text-xl">🔒</span>
            <p className="leading-tight">
              <strong>Privacy First:</strong> The video uploaded won't
be saved. Our servers delete it instantly after analysis.
            </p>
          </div>
        </div>
      )}

      {/* --- ZONE DE CHARGEMENT --- */}
      {loadingStep > 0 && (
        <div className="space-y-6 animate-in fade-in duration-500
max-w-2xl mx-auto mt-10">

          <GeometricSBDLoader />

          {/* Conseils dynamiques + Mouvement détecté */}
          {loadingStep === 2 && detectedMovement && (
            <div className="bg-indigo-900/30 border
border-indigo-500/30 text-indigo-300 p-6 rounded-2xl text-center
shadow-inner mt-8 animate-in slide-in-from-bottom-4 duration-700">

              {/* Le badge du mouvement + Pro tip */}
              <div className="flex flex-col sm:flex-row items-center
justify-center gap-2 sm:gap-3 text-xs font-black uppercase
tracking-widest mb-4">
                <span className="bg-indigo-500/30 text-indigo-100
py-1.5 px-4 rounded-full border border-indigo-500/40 shadow-sm flex
items-center gap-2">
                  <span>🎯</span> {detectedMovement} DETECTED
                </span>
                <span className="opacity-70 hidden sm:inline">•</span>
                <span className="opacity-70 mt-2 sm:mt-0">PRO TIP
WHILE YOU WAIT</span>
              </div>

              <p className="italic text-lg font-medium leading-relaxed
max-w-lg mx-auto">
                "{loadingTips[detectedMovement] || "Hold tight, analyzing your biomechanics..."}"
              </p>
            </div>
          )}

          {isFreeUser && (
            <div className="mt-8 animate-in fade-in duration-500">
              <AdBannerPlaceholder format="rectangle" />
            </div>
          )}
        </div>
      )}

      {/* --- ZONE DE RÉSULTATS --- */}
      {result && loadingStep === 0 && (
        <div className="space-y-6 animate-in fade-in
slide-in-from-bottom-4 duration-700">

          <div className="flex flex-col items-center justify-center
p-10 bg-gray-900 border border-gray-800 rounded-3xl shadow-lg">
            <span className="text-gray-400 font-semibold mb-2
uppercase tracking-widest text-sm">
              Technical Score: {result.movement_detected || detectedMovement}
            </span>
            <div className="flex items-baseline gap-2">
              <span className={`text-7xl font-black ${scorePercentage
>= 80 ? 'text-emerald-400' : scorePercentage >= 50 ? 'text-amber-400'
: 'text-red-400'}`}>
                {scoreObtenu}
              </span>
              <span className="text-4xl text-gray-600 font-bold">/
{scoreMax}</span>
            </div>
          </div>

          {result.lifter_persona && (() => {
            const { emoji, filename } = getPersonaAssets(result.lifter_persona);
            return (
              <div className="bg-gradient-to-br from-indigo-900
to-purple-900 border border-indigo-500/30 rounded-3xl p-6 sm:p-8
shadow-xl flex flex-col sm:flex-row items-center gap-6 sm:gap-8
text-center sm:text-left transform transition-transform
hover:scale-[1.02]">

                <div className="w-32 h-32 sm:w-40 sm:h-40
flex-shrink-0 bg-indigo-950/50 rounded-full border-4
border-indigo-400/50 overflow-hidden flex items-center justify-center
shadow-inner relative">
                  <img
                    src={`/images/personas/${filename}`}
                    alt={result.lifter_persona}
                    className="w-full h-full object-cover z-10"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                  <div className="absolute inset-0 hidden items-center
justify-center text-6xl sm:text-7xl z-0">
                    {emoji}
                  </div>
                </div>

                <div className="flex-1">
                  <span className="text-indigo-300 font-black
uppercase tracking-widest text-xs mb-2 block">
                    AI Assessment • Your Deadlift Persona
                  </span>
                  <h3 className="text-3xl sm:text-4xl font-black
text-white mb-4 drop-shadow-md">
                    {result.lifter_persona}
                  </h3>
                  <p className="text-indigo-100 text-base sm:text-lg
italic bg-black/20 p-4 rounded-xl leading-relaxed border
border-indigo-500/20">
                    "{result.persona_justification}"
                  </p>
                </div>
              </div>
            );
          })()}

          <div className="grid grid-cols-1 gap-4">
            {Object.entries(result).map(([key, data]) => {
              const ignoredKeys = [
                'note_globale_brute', 'score_max_brut',
'mouvement_detecte', 'quota_restant',
                'raw_overall_score', 'raw_max_score',
'movement_detected', 'quota_left',
                'lifter_persona', 'persona_justification', 'total_raw_score'
              ];
              if (ignoredKeys.includes(key)) return null;

              return (
                <ResultCard
                  key={key}
                  criterionKey={key}
                  data={data}
                  isExpanded={expandedCard === key}
                  onToggle={() => setExpandedCard(expandedCard === key
? null : key)}
                  demo={criteriaGuides[key]}
                />
              );
            })}
          </div>

          <button
            onClick={() => { setResult(null); setFile(null);
setExpandedCard(null); setDetectedMovement(null); }}
            className="w-full mt-8 bg-gray-800 hover:bg-gray-700
text-white font-bold py-4 px-8 rounded-xl transition-all uppercase
tracking-wider text-sm"
          >
            Analyze another video
          </button>
        </div>
      )}

      {isFreeUser && loadingStep === 0 && !result && (
        <div className="mt-12">
          <AdBannerPlaceholder format="banner" />
        </div>
      )}
    </div>
  );
}
