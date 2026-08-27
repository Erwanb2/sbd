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
      className={`w-full bg-gray-950/50 border border-dashed border-indigo-500/30 backdrop-blur-sm rounded-2xl p-4 flex flex-col items-center justify-center text-center overflow-hidden font-mono ${format === 'rectangle' ? 'min-h-[250px]' : 'min-h-[90px]'} ${className}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[10px] uppercase font-bold tracking-[0.2em] text-indigo-400/70 bg-indigo-950/50 px-2 py-0.5 rounded border border-indigo-500/20">
          SYS.AD_SPACE
        </span>
      </div>
      <p className="text-xs text-indigo-500/50 tracking-widest uppercase">
        Google AdSense Reserved (Free Tier)
      </p>
    </div>
  );
}

const getPersonaAssets = (persona) => {
  if (!persona) return { emoji: "🏋️", filename: "default.webp" };
  const p = persona.toLowerCase();

  if (p.includes('technician')) return { emoji: "🥇", filename: "technician.webp" };
  if (p.includes('grip')) return { emoji: "🚀", filename: "grip-and-rip.webp" };
  if (p.includes('crane')) return { emoji: "🏗️", filename: "crane.webp" };
  if (p.includes('squatter')) return { emoji: "📉", filename: "squatter.webp" };
  if (p.includes('fishing')) return { emoji: "🎣", filename: "fishing-rod.webp" };
  if (p.includes('extender')) return { emoji: "⚠️", filename: "over-extender.webp" };
  if (p.includes('hitcher')) return { emoji: "🛑", filename: "hitcher.webp" };

  return { emoji: "💪", filename: "default.webp" };
};

const loadingTips = {
  "squat": "Focus on bracing your core before descending to maintain a neutral spine under heavy load.",
  "bench": "Keep your shoulder blades retracted and depressed into the bench to protect your shoulders.",
  "Conventional deadlift": "Ensure the bar is exactly over your mid-foot before you pull the slack out.",
  "Sumo deadlift": "Think about 'spreading the floor' apart with your feet to engage your adductors and glutes."
};

// Timing shared by every figure so the three lifters stay in a coherent rhythm.
const REP = '1.8s';
const EASE = '0.45 0 0.55 1;0.45 0 0.55 1';

const Barbell = ({ span = 22, plate = 7, values, begin, isSideView = false }) => (
  <g filter="url(#sbdGlow)">
    <animateTransform attributeName="transform" type="translate" additive="replace" values={values} keyTimes="0;0.5;1" calcMode="spline" keySplines={EASE} dur={REP} begin={begin} repeatCount="indefinite" />
    {isSideView ? (
      <>
        <circle cx="0" cy="0" r={plate * 1.35} fill="#4f46e5" />
        <circle cx="0" cy="0" r={plate * 0.7} fill="#c7d2fe" opacity="0.8" />
        <circle cx="0" cy="0" r="2.5" fill="#a5b4fc" />
        <circle cx="0" cy="0" r="1" fill="#312e81" />
      </>
    ) : (
      <>
        <line x1={-span} y1="0" x2={span} y2="0" stroke="#a5b4fc" strokeWidth="3" strokeLinecap="round" />
        <circle cx={-span} cy="0" r={plate} fill="#4f46e5" />
        <circle cx={span} cy="0" r={plate} fill="#4f46e5" />
        <circle cx={-span} cy="0" r={plate * 0.42} fill="#c7d2fe" />
        <circle cx={span} cy="0" r={plate * 0.42} fill="#c7d2fe" />
        <circle cx={-span + 6} cy="0" r="2.4" fill="#6366f1" />
        <circle cx={span - 6} cy="0" r="2.4" fill="#6366f1" />
      </>
    )}
  </g>
);

const Flex = ({ attr = 'd', values, begin, type }) => (
  <animate attributeName={attr} {...(type ? { type } : {})} values={values} keyTimes="0;0.5;1" calcMode="spline" keySplines={EASE} dur={REP} begin={begin} repeatCount="indefinite" />
);

const bodyStroke = {
  fill: 'none', stroke: '#c7d2fe', strokeWidth: 4, strokeLinecap: 'round', strokeLinejoin: 'round',
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
    const id = setInterval(() => setStatusIndex((i) => (i + 1) % statusMessages.length), 1500);
    return () => clearInterval(id);
  }, [statusMessages.length]);

  return (
    <div className="flex flex-col items-center justify-center p-6 sm:p-8 w-full bg-indigo-950/20 border border-indigo-500/30 backdrop-blur-md rounded-3xl shadow-[0_0_40px_rgba(99,102,241,0.05)]">
      <style>{`
        @keyframes sbdSweep { 0%{transform:translateX(-130%)} 100%{transform:translateX(340%)} }
        @keyframes sbdShimmer { 0%{background-position:0% 50%} 100%{background-position:200% 50%} }
      `}</style>

      <div className="relative w-full max-w-lg">
        <div className="absolute -inset-6 bg-indigo-500/10 blur-3xl rounded-full" />
        <svg viewBox="0 0 360 175" className="relative w-full overflow-visible" role="img" aria-label="Animation of three lifters performing squat, bench and deadlift">
          <defs>
            <filter id="sbdGlow" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="1.6" result="b" />
              <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <linearGradient id="sbdScan" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0" />
              <stop offset="50%" stopColor="#a5b4fc" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Background Elements */}
          <g opacity="0.18" fill="none" stroke="#6366f1">
            <circle cx="180" cy="80" r="84" strokeDasharray="3 10">
              <animateTransform attributeName="transform" type="rotate" from="0 180 80" to="360 180 80" dur="22s" repeatCount="indefinite" />
            </circle>
            <circle cx="180" cy="80" r="62" strokeDasharray="2 12">
              <animateTransform attributeName="transform" type="rotate" from="360 180 80" to="0 180 80" dur="16s" repeatCount="indefinite" />
            </circle>
          </g>

          {/* Scan Beam */}
          <g style={{ animation: 'sbdSweep 4.2s ease-in-out infinite' }}>
            <rect x="0" y="14" width="34" height="140" fill="url(#sbdScan)" opacity="0.35" />
          </g>

          {/* Platform */}
          <line x1="20" y1="151" x2="340" y2="151" stroke="#4338ca" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
          <line x1="20" y1="151" x2="340" y2="151" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeDasharray="2 14" opacity="0.9" />

          {/* SQUAT */}
          <g transform="translate(60,0)">
            <ellipse cx="0" cy="150" rx="16" ry="3" fill="#312e81">
              <animate attributeName="rx" values="15;20;15" keyTimes="0;0.5;1" dur={REP} begin="0s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.4;0.7;0.4" keyTimes="0;0.5;1" dur={REP} begin="0s" repeatCount="indefinite" />
            </ellipse>
            <path style={bodyStroke}>
              <Flex values="M 10 140 L 12 118 L 0 95 L -12 118 L -10 140;M 10 140 L 20 128 L 0 112 L -20 128 L -10 140;M 10 140 L 12 118 L 0 95 L -12 118 L -10 140" begin="0s" />
            </path>
            <path style={bodyStroke}>
              <Flex values="M 0 95 L 0 66;M 0 112 L 0 83;M 0 95 L 0 66" begin="0s" />
            </path>
            <path style={{ ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' }}>
              <Flex values="M 0 68 L -12 80 L -18 64 M 0 68 L 12 80 L 18 64;M 0 85 L -12 97 L -18 81 M 0 85 L 12 97 L 18 81;M 0 68 L -12 80 L -18 64 M 0 68 L 12 80 L 18 64" begin="0s" />
            </path>
            <circle cx="0" r="7.5" fill="#a5b4fc">
              <Flex attr="cy" values="56;73;56" begin="0s" />
            </circle>
            <Barbell span="36" plate="7" values="0 64;0 81;0 64" begin="0s" />
          </g>

          {/* BENCH */}
          <g transform="translate(180,0)">
            <ellipse cx="0" cy="150" rx="26" ry="3" fill="#312e81" opacity="0.5" />
            <rect x="-30" y="112" width="60" height="6" rx="3" fill="#3730a3" />
            <line x1="-22" y1="118" x2="-22" y2="140" stroke="#4338ca" strokeWidth="3" strokeLinecap="round" />
            <line x1="22" y1="118" x2="22" y2="140" stroke="#4338ca" strokeWidth="3" strokeLinecap="round" />
            <path style={{ ...bodyStroke, strokeWidth: 4 }} d="M 16 104 L 28 120 L 26 140" />
            <path style={bodyStroke} d="M 20 104 L -12 104" />
            <circle cx="-22" cy="104" r="6.5" fill="#a5b4fc" />
            <path style={{ ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' }}>
              <Flex values="M -12 104 L -8 88 L -4 76;M -12 104 L -8 116 L -4 100;M -12 104 L -8 88 L -4 76" begin="-0.6s" />
            </path>
            <Barbell plate="8.5" values="-4 76;-4 100;-4 76" begin="-0.6s" isSideView={} />
          </g>

          {/* DEADLIFT */}
          <g transform="translate(300,0)">
            <ellipse cx="0" cy="150" rx="16" ry="3" fill="#312e81">
              <animate attributeName="rx" values="19;14;19" keyTimes="0;0.5;1" dur={REP} begin="-1.2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.7;0.4;0.7" keyTimes="0;0.5;1" dur={REP} begin="-1.2s" repeatCount="indefinite" />
            </ellipse>
            <path style={bodyStroke}>
              <Flex values="M 10 140 L 13 126 L 0 116 L -13 126 L -10 140;M 10 140 L 11 118 L 0 96 L -11 118 L -10 140;M 10 140 L 13 126 L 0 116 L -13 126 L -10 140" begin="-1.2s" />
            </path>
            <path style={bodyStroke}>
              <Flex values="M 0 116 L 0 92;M 0 96 L 0 70;M 0 116 L 0 92" begin="-1.2s" />
            </path>
            <circle cx="0" r="7.5" fill="#a5b4fc">
              <Flex attr="cy" values="82;60;82" begin="-1.2s" />
            </circle>
            <path style={{ ...bodyStroke, strokeWidth: 3, stroke: '#a5b4fc' }}>
              <Flex values="M -12 92 L -13 131 M 12 92 L 13 131;M -12 70 L -12 110 M 12 70 L 12 110;M -12 92 L -13 131 M 12 92 L 13 131" begin="-1.2s" />
            </path>
            <Barbell span="34" plate="7.5" values="0 131;0 110;0 131" begin="-1.2s" />
          </g>

          {/* LABELS */}
          <g fontFamily="monospace" fontSize="8" fontWeight="700" letterSpacing="2" fill="#818cf8" textAnchor="middle">
            <text x="60" y="168">SQUAT<animate attributeName="opacity" values="0.35;1;0.35" keyTimes="0;0.5;1" dur={REP} begin="0s" repeatCount="indefinite" /></text>
            <text x="180" y="168">BENCH<animate attributeName="opacity" values="0.35;1;0.35" keyTimes="0;0.5;1" dur={REP} begin="-0.6s" repeatCount="indefinite" /></text>
            <text x="300" y="168">DEADLIFT<animate attributeName="opacity" values="0.35;1;0.35" keyTimes="0;0.5;1" dur={REP} begin="-1.2s" repeatCount="indefinite" /></text>
          </g>
        </svg>
      </div>

      {/* STATUS */}
      <div className="mt-8 flex flex-col items-center gap-4 w-full max-w-sm">
        <div className="font-mono text-sm sm:text-base uppercase tracking-[0.3em] font-bold text-transparent bg-clip-text" style={{ backgroundImage: 'linear-gradient(90deg,#6366f1,#a5b4fc,#818cf8,#a5b4fc,#6366f1)', backgroundSize: '200% auto', animation: 'sbdShimmer 3s linear infinite' }}>
          Computing Biomechanics
        </div>
        <div className="h-5 relative w-56 text-center">
          {statusMessages.map((msg, i) => (
            <span key={msg} className="absolute inset-0 text-xs text-indigo-300/80 font-mono tracking-wide" style={{ opacity: i === statusIndex ? 1 : 0, transition: 'opacity 0.4s ease' }}>
              {msg}<span className="animate-pulse">…</span>
            </span>
          ))}
        </div>
        <div className="w-full h-1.5 rounded-full bg-indigo-950/80 overflow-hidden border border-indigo-500/20">
          <div className="h-full w-1/3 rounded-full bg-gradient-to-r from-transparent via-indigo-400 to-transparent" style={{ animation: 'sbdSweep 1.4s ease-in-out infinite' }} />
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

  const isFreeUser = user?.plan?.toLowerCase() !== 'premium' && user?.plan?.toLowerCase() !== 'pro';

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

      const initResponse = await fetch('/api/upload_and_detect', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${tokenAPI}` },
        body: formData,
      });
      const initData = await initResponse.json();

      if (!initResponse.ok) throw new Error(initData.detail || "Initialisation failed");

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
      if (!analyzeResponse.ok) throw new Error(analyzeData.detail || "Analysis error");

      setResult(analyzeData);

    } catch (error) {
      alert(`Error ❌ : ${error.message}`);
    } finally {
      setLoadingStep(0);
    }
  };

  const scoreObtenu = result?.total_raw_score || result?.note_globale_brute || 0;
  const scoreMax = result?.raw_max_score || 24;
  const scorePercentage = (scoreObtenu / scoreMax) * 100;

  return (
    // CONTENEUR GLOBAL : THEME CYBER-LABORATOIRE
    <div className="min-h-screen bg-gray-950 text-indigo-50 font-sans relative overflow-x-hidden flex flex-col">
      
      {/* ARRIÈRE-PLAN : GRILLE & HALO LUMINEUX */}
      <div className="fixed inset-0 z-0 opacity-20 pointer-events-none" style={{ backgroundImage: `linear-gradient(rgba(99, 102, 241, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(99, 102, 241, 0.15) 1px, transparent 1px)`, backgroundSize: '40px 40px', backgroundPosition: 'center center' }} />
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-indigo-600/10 blur-[120px] rounded-full pointer-events-none z-0" />

      {/* ECRAN DE CONNEXION */}
      {!tokenAPI ? (
        <div className="relative z-10 flex flex-col items-center justify-center min-h-screen gap-6 p-4">
          <div className="bg-gray-950/60 border border-indigo-500/20 backdrop-blur-xl p-10 sm:p-16 rounded-3xl shadow-[0_0_50px_rgba(99,102,241,0.1)] text-center max-w-md w-full">
            <div className="w-16 h-16 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-indigo-500/30">
              <svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            </div>
            <h1 className="text-3xl font-black uppercase tracking-widest mb-3 text-white">Kinematics</h1>
            <p className="text-indigo-200/60 font-mono text-sm mb-8 leading-relaxed">
              System locked. Authenticate to initialize biomechanical tracking.
            </p>
            <div className="flex justify-center">
              <GoogleLogin onSuccess={handleGoogleSuccess} onError={() => alert('Login failed')} theme="filled_black" shape="pill" />
            </div>
          </div>
        </div>
      ) : (
        /* APPLICATION PRINCIPALE */
        <div className="relative z-10 flex-1 w-full max-w-5xl mx-auto p-4 sm:p-6 pb-24">
          <Header user={user} onOpenProfile={() => setShowProfile(true)} />

          {showProfile && (
            <ProfileModal user={user} tokenAPI={tokenAPI} onClose={() => setShowProfile(false)} onUpdateUser={handleUpdateUser} />
          )}

          {/* --- ZONE D'UPLOAD --- */}
          {loadingStep === 0 && !result && (
            <div className="animate-in fade-in duration-500 flex flex-col items-center w-full mt-10">
              <div className="w-full">
                <UploadZone file={file} setFile={setFile} handleUpload={handleUpload} />
              </div>

              {/* Message de confidentialité style HUD */}
              <div className="mt-8 bg-indigo-950/30 border border-indigo-500/20 text-indigo-300 py-3 px-6 rounded-xl flex items-center justify-center gap-4 text-xs font-mono shadow-[0_0_15px_rgba(99,102,241,0.05)] w-full max-w-lg transition-colors hover:border-indigo-500/40">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <p className="tracking-wide">
                  <strong className="text-indigo-100 font-bold uppercase tracking-widest mr-2">Privacy Active:</strong> 
                  Zero retention. Data is purged post-analysis.
                </p>
              </div>
            </div>
          )}

          {/* --- ZONE DE CHARGEMENT --- */}
          {loadingStep > 0 && (
            <div className="animate-in fade-in duration-500 max-w-3xl mx-auto mt-12 flex flex-col items-center gap-8">
              <GeometricSBDLoader />

              {/* Pro Tip - Style Terminal */}
              {loadingStep === 2 && detectedMovement && (
                <div className="w-full border-l-4 border-indigo-500 bg-gray-950/60 backdrop-blur-md p-6 rounded-r-2xl shadow-[0_0_20px_rgba(99,102,241,0.05)] text-left animate-in slide-in-from-bottom-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-[10px] font-mono uppercase tracking-[0.2em] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 border border-indigo-500/30 rounded">
                      {detectedMovement} DETECTED
                    </span>
                    <span className="text-[10px] font-mono text-indigo-500/60 uppercase tracking-widest">
                      SYS.ADVICE
                    </span>
                  </div>
                  <p className="text-sm font-mono text-indigo-100/90 leading-relaxed">
                    > {loadingTips[detectedMovement] || "Calibrating vectors..."}
                  </p>
                </div>
              )}

              {isFreeUser && (
                <div className="w-full mt-4 animate-in fade-in">
                  <AdBannerPlaceholder format="rectangle" />
                </div>
              )}
            </div>
          )}

          {/* --- ZONE DE RÉSULTATS --- */}
          {result && loadingStep === 0 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700 mt-8">
              
              {/* Note Technique (Dashboard Style) */}
              <div className="flex flex-col items-center justify-center p-8 bg-gray-950/80 border border-indigo-500/30 backdrop-blur-xl rounded-3xl shadow-[0_0_30px_rgba(99,102,241,0.08)] relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-indigo-400/50 to-transparent opacity-50" />
                
                <span className="text-indigo-400/70 font-mono text-[10px] sm:text-xs mb-3 uppercase tracking-[0.3em]">
                  Overall Kinematic Score • {result.movement_detected || detectedMovement}
                </span>
                
                <div className="flex items-baseline gap-2">
                  <span className={`text-7xl font-light tracking-tight ${scorePercentage >= 80 ? 'text-emerald-400 drop-shadow-[0_0_15px_rgba(52,211,153,0.4)]' : scorePercentage >= 50 ? 'text-amber-400 drop-shadow-[0_0_15px_rgba(251,191,36,0.4)]' : 'text-red-400 drop-shadow-[0_0_15px_rgba(248,113,113,0.4)]'}`}>
                    {scoreObtenu}
                  </span>
                  <span className="text-3xl text-indigo-500/40 font-mono tracking-widest">/ {scoreMax}</span>
                </div>
              </div>

              {/* Carte Persona (Cyberpunk ID Card) */}
              {result.lifter_persona && (() => {
                const { emoji, filename } = getPersonaAssets(result.lifter_persona);
                return (
                  <div className="bg-indigo-950/20 border border-indigo-400/30 rounded-3xl p-6 sm:p-8 backdrop-blur-md shadow-xl flex flex-col sm:flex-row items-center gap-6 sm:gap-8 text-center sm:text-left transition-all hover:border-indigo-400/60">
                    
                    {/* Avatar Container */}
                    <div className="w-32 h-32 flex-shrink-0 bg-gray-950 rounded-full border border-indigo-500/50 overflow-hidden flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.2)] relative group">
                      <div className="absolute inset-0 border-[3px] border-transparent border-t-indigo-400 rounded-full animate-spin" style={{ animationDuration: '4s' }} />
                      <img
                        src={`/images/personas/${filename}`}
                        alt={result.lifter_persona}
                        className="w-full h-full object-cover z-10 opacity-80 mix-blend-luminosity grayscale group-hover:grayscale-0 transition-all duration-500"
                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                      />
                      <div className="absolute inset-0 hidden items-center justify-center text-5xl z-0">
                        {emoji}
                      </div>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center justify-center sm:justify-start gap-2 mb-2">
                        <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-pulse" />
                        <span className="text-indigo-400/80 font-mono uppercase tracking-[0.2em] text-[10px]">
                          Profile Match Established
                        </span>
                      </div>
                      <h3 className="text-2xl sm:text-3xl font-black text-white mb-3 uppercase tracking-wide">
                        {result.lifter_persona}
                      </h3>
                      <p className="text-indigo-200/80 text-sm font-mono bg-gray-950/50 p-4 rounded-xl leading-relaxed border border-indigo-500/10">
                        > {result.persona_justification}
                      </p>
                    </div>
                  </div>
                );
              })()}

              {/* Grille des critères */}
              <div className="grid grid-cols-1 gap-4">
                {Object.entries(result).map(([key, data]) => {
                  const ignoredKeys = ['note_globale_brute', 'score_max_brut', 'mouvement_detecte', 'quota_restant', 'raw_overall_score', 'raw_max_score', 'movement_detected', 'quota_left', 'lifter_persona', 'persona_justification', 'total_raw_score'];
                  if (ignoredKeys.includes(key)) return null;

                  return (
                    <ResultCard
                      key={key}
                      criterionKey={key}
                      data={data}
                      isExpanded={expandedCard === key}
                      onToggle={() => setExpandedCard(expandedCard === key ? null : key)}
                      demo={criteriaGuides[key]}
                    />
                  );
                })}
              </div>

              {/* Bouton d'action "RUN NEW ANALYSIS" (Ghost Neon) */}
              <button
                onClick={() => { setResult(null); setFile(null); setExpandedCard(null); setDetectedMovement(null); }}
                className="w-full mt-6 py-4 font-mono text-xs sm:text-sm tracking-[0.2em] text-indigo-300 border border-indigo-500/40 rounded-2xl bg-indigo-950/30 hover:bg-indigo-500/20 hover:text-indigo-100 hover:shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-300 uppercase"
              >
                Run New Analysis
              </button>
            </div>
          )}

          {/* Ad Banner Free tier */}
          {isFreeUser && loadingStep === 0 && !result && (
            <div className="mt-12 w-full animate-in fade-in">
              <AdBannerPlaceholder format="banner" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
