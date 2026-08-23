import { useState } from 'react';
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
      className={`w-full bg-gray-900/60 border border-dashed border-gray-700/70 rounded-2xl p-4 flex flex-col items-center justify-center text-center overflow-hidden ${format === 'rectangle' ? 'min-h-[250px]' : 'min-h-[90px]'} ${className}`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] uppercase font-bold tracking-widest text-gray-400 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
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

const GeometricSBDLoader = () => (
  <div className="flex flex-col items-center justify-center p-8 space-y-8">
    <div className="relative w-40 h-40 flex items-center justify-center">
      <div className="absolute inset-0 rounded-full border border-indigo-500/20 animate-[ping_3s_ease-in-out_infinite]"></div>
      <div className="absolute inset-4 rounded-full border border-indigo-400/30 animate-[spin_4s_linear_infinite] border-t-transparent"></div>
      
      <svg className="w-24 h-24 z-10 overflow-visible" viewBox="0 0 100 100">
        <g className="animate-[bounce_2s_ease-in-out_infinite]">
          <line x1="10" y1="30" x2="90" y2="30" stroke="#818cf8" strokeWidth="4" strokeLinecap="round" />
          <circle cx="15" cy="30" r="8" fill="#4f46e5" />
          <circle cx="85" cy="30" r="8" fill="#4f46e5" />
        </g>
        <polyline points="50,30 50,65 30,95" stroke="#c7d2fe" strokeWidth="3" fill="none" strokeLinecap="round" strokeDasharray="4 4" className="opacity-80" />
        <polyline points="50,65 70,95" stroke="#c7d2fe" strokeWidth="3" fill="none" strokeLinecap="round" strokeDasharray="4 4" className="opacity-80" />
        <circle cx="50" cy="65" r="4" fill="#a5b4fc" className="animate-pulse" />
      </svg>
    </div>
    
    <div className="text-center space-y-2">
      <div className="text-indigo-400 font-mono text-sm uppercase tracking-[0.3em] animate-pulse">
        Computing Biomechanics
      </div>
      <div className="flex justify-center gap-1.5">
        <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
        <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
        <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
      </div>
    </div>
  </div>
);

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

      // On utilise le bon endpoint !
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

  if (!tokenAPI) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white gap-6">
        <h1 className="text-4xl font-black uppercase tracking-wider mb-2">SBD Reviews</h1>
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
        <div className="animate-in fade-in duration-500 flex flex-col items-center w-full">
          <div className="w-full">
            <UploadZone file={file} setFile={setFile} handleUpload={handleUpload} />
          </div>
          
          {/* Nouveau placement du message Privacy First (sous la box d'upload) */}
          <div className="mt-6 bg-emerald-900/20 border border-emerald-500/30 text-emerald-400 py-3 px-6 rounded-xl flex flex-col sm:flex-row items-center justify-center gap-3 text-sm text-center shadow-lg max-w-lg w-full transition-all hover:bg-emerald-900/30">
            <span className="text-xl">🔒</span>
            <p className="leading-tight">
              <strong>Privacy First:</strong> The video uploaded won't be saved. Our servers delete it instantly after analysis.
            </p>
          </div>
        </div>
      )}

      {/* --- ZONE DE CHARGEMENT --- */}
      {loadingStep > 0 && (
        <div className="space-y-6 animate-in fade-in duration-500 max-w-2xl mx-auto mt-10">
          
          <GeometricSBDLoader />
          
          {/* Conseils dynamiques + Mouvement détecté */}
          {loadingStep === 2 && detectedMovement && (
            <div className="bg-indigo-900/30 border border-indigo-500/30 text-indigo-300 p-6 rounded-2xl text-center shadow-inner mt-8 animate-in slide-in-from-bottom-4 duration-700">
              
              {/* Le badge du mouvement + Pro tip */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 text-xs font-black uppercase tracking-widest mb-4">
                <span className="bg-indigo-500/30 text-indigo-100 py-1.5 px-4 rounded-full border border-indigo-500/40 shadow-sm flex items-center gap-2">
                  <span>🎯</span> {detectedMovement} DETECTED
                </span>
                <span className="opacity-70 hidden sm:inline">•</span>
                <span className="opacity-70 mt-2 sm:mt-0">PRO TIP WHILE YOU WAIT</span>
              </div>
              
              <p className="italic text-lg font-medium leading-relaxed max-w-lg mx-auto">
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
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          
          <div className="flex flex-col items-center justify-center p-10 bg-gray-900 border border-gray-800 rounded-3xl shadow-lg">
            <span className="text-gray-400 font-semibold mb-2 uppercase tracking-widest text-sm">
              Technical Score: {result.movement_detected || detectedMovement}
            </span>
            <div className="flex items-baseline gap-2">
              <span className={`text-7xl font-black ${scorePercentage >= 80 ? 'text-emerald-400' : scorePercentage >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                {scoreObtenu}
              </span>
              <span className="text-4xl text-gray-600 font-bold">/ {scoreMax}</span>
            </div>
          </div>

          {result.lifter_persona && (() => {
            const { emoji, filename } = getPersonaAssets(result.lifter_persona);
            return (
              <div className="bg-gradient-to-br from-indigo-900 to-purple-900 border border-indigo-500/30 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row items-center gap-6 sm:gap-8 text-center sm:text-left transform transition-transform hover:scale-[1.02]">
                
                <div className="w-32 h-32 sm:w-40 sm:h-40 flex-shrink-0 bg-indigo-950/50 rounded-full border-4 border-indigo-400/50 overflow-hidden flex items-center justify-center shadow-inner relative">
                  <img
                    src={`/images/personas/${filename}`}
                    alt={result.lifter_persona}
                    className="w-full h-full object-cover z-10"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                  <div className="absolute inset-0 hidden items-center justify-center text-6xl sm:text-7xl z-0">
                    {emoji}
                  </div>
                </div>

                <div className="flex-1">
                  <span className="text-indigo-300 font-black uppercase tracking-widest text-xs mb-2 block">
                    AI Assessment • Your Deadlift Persona
                  </span>
                  <h3 className="text-3xl sm:text-4xl font-black text-white mb-4 drop-shadow-md">
                    {result.lifter_persona}
                  </h3>
                  <p className="text-indigo-100 text-base sm:text-lg italic bg-black/20 p-4 rounded-xl leading-relaxed border border-indigo-500/20">
                    "{result.persona_justification}"
                  </p>
                </div>
              </div>
            );
          })()}

          <div className="grid grid-cols-1 gap-4">
            {Object.entries(result).map(([key, data]) => {
              const ignoredKeys = [
                'note_globale_brute', 'score_max_brut', 'mouvement_detecte', 'quota_restant', 
                'raw_overall_score', 'raw_max_score', 'movement_detected', 'quota_left',
                'lifter_persona', 'persona_justification', 'total_raw_score'
              ];
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

          <button
            onClick={() => { setResult(null); setFile(null); setExpandedCard(null); setDetectedMovement(null); }}
            className="w-full mt-8 bg-gray-800 hover:bg-gray-700 text-white font-bold py-4 px-8 rounded-xl transition-all uppercase tracking-wider text-sm"
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