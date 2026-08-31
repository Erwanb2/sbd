import { useState, useEffect } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import Header from './components/Header.jsx';
import UploadZone from './components/UploadZone.jsx';
import ResultCard from './components/ResultCard.jsx';
import ProfileModal from './components/ProfileModal.jsx';
import GeometricSBDLoader from './components/GeometricSBDLoader.jsx';
import AdBannerPlaceholder from './components/AdBannerPlaceholder.jsx';

import { criteriaGuides } from './data/criteriaGuides.js';
import { getPersonaAssets, loadingTips } from './data/personaAssets.js';
import { validateVideoFile, DEFAULT_LIMITS } from './utils/videoValidation.js';

export default function App() {
  const [ file, setFile ] = useState(null);
  const [ result, setResult ] = useState(null);
  const [ loadingStep, setLoadingStep ] = useState(0);
  const [ detectedMovement, setDetectedMovement ] = useState(null);
  const [ expandedCard, setExpandedCard ] = useState(null);

  const [ tokenAPI, setTokenAPI ] = useState(null);
  const [ user, setUser ] = useState(null);
  const [ showProfile, setShowProfile ] = useState(false);
  const [ limits, setLimits ] = useState(DEFAULT_LIMITS);

  const isFreeUser = user?.plan?.toLowerCase() !== 'premium' && user?.plan?.toLowerCase() !== 'pro';

  // Limites d'upload récupérées depuis l'API (taille + durée max).
  useEffect(() => {
    fetch('/api/config')
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg) => {
        if (cfg) {
          setLimits({
            maxUploadMb: cfg.max_upload_mb ?? DEFAULT_LIMITS.maxUploadMb,
            maxVideoSeconds: cfg.max_video_seconds ?? DEFAULT_LIMITS.maxVideoSeconds,
          });
        }
      })
      .catch(() => { /* on garde les valeurs par défaut */ });
  }, []);

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
    setUser(prev => ( { ...prev, ...updatedData } ));
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    if (!tokenAPI) {
      alert("You must be logged in to analyze a video.");
      return;
    }

    // Pré-validation locale : taille + durée, avant de consommer un crédit.
    const check = await validateVideoFile(file, limits);
    if (!check.ok) {
      alert(`Error ❌ : ${ check.error }`);
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
        headers: { 'Authorization': `Bearer ${ tokenAPI }` },
        body: formData,
      });
      const initData = await initResponse.json();

      if (!initResponse.ok) throw new Error(initData.detail || "Initialisation failed");

      if (initData.quota_restant !== undefined) {
        setUser(prev => ( { ...prev, quota_left: initData.quota_restant } ));
      }
      setDetectedMovement(initData.mouvement_detecte);
      setLoadingStep(2);

      const analyzeResponse = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${ tokenAPI }`
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
      alert(`Error ❌ : ${ error.message }`);
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
        <GoogleLogin
          onSuccess={ handleGoogleSuccess }
          onError={ () => alert('Login failed') }
          theme="filled_black"
          shape="pill"
        />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 pt-12 pb-24 text-white relative">
      <Header user={ user } onOpenProfile={ () => setShowProfile(true) } />

      { showProfile && (
        <ProfileModal
          user={ user }
          tokenAPI={ tokenAPI }
          onClose={ () => setShowProfile(false) }
          onUpdateUser={ handleUpdateUser }
        />
      ) }

      { /* --- ZONE D'UPLOAD + MESSAGE DE CONFIDENTIALITÉ --- */ }
      { loadingStep === 0 && !result && (
        <div className="animate-in fade-in duration-500 flex flex-col items-center w-full">
          <div className="w-full">
            <UploadZone file={ file } setFile={ setFile } handleUpload={ handleUpload } limits={ limits } />
          </div>

          <div className="mt-6 bg-emerald-900/20 border border-emerald-500/30 text-emerald-400 py-3 px-6 rounded-xl flex flex-col sm:flex-row items-center justify-center gap-3 text-sm text-center shadow-lg max-w-lg w-full transition-all hover:bg-emerald-900/30">
            <span className="text-xl">🔒</span>
            <p className="leading-tight">
              <strong>Privacy First:</strong> The video uploaded won't be saved.
            </p>
          </div>
        </div>
      ) }

      { /* --- ZONE DE CHARGEMENT --- */ }
      { loadingStep > 0 && (
        <div className="space-y-6 animate-in fade-in duration-500 max-w-2xl mx-auto mt-10">

          <GeometricSBDLoader />

          { loadingStep === 2 && detectedMovement && (
            <div className="bg-indigo-900/30 border border-indigo-500/30 text-indigo-300 p-6 rounded-2xl text-center shadow-inner mt-8 animate-in slide-in-from-bottom-4 duration-700">

              <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 text-xs font-black uppercase tracking-widest mb-4">
                <span className="bg-indigo-500/30 text-indigo-100 py-1.5 px-4 rounded-full border border-indigo-500/40 shadow-sm flex items-center gap-2">
                  <span>🎯</span> { detectedMovement } DETECTED
                </span>
              </div>

              <p className="italic text-lg font-medium leading-relaxed max-w-lg mx-auto">
                "{ loadingTips[detectedMovement] || "Hold tight, analyzing your biomechanics..." }"
              </p>
            </div>
          ) }

          { isFreeUser && (
            <div className="mt-8 animate-in fade-in duration-500">
              <AdBannerPlaceholder format="rectangle" />
            </div>
          ) }
        </div>
      ) }

      { /* --- ZONE DE RÉSULTATS --- */ }
      { result && loadingStep === 0 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">

          <div className="flex flex-col items-center justify-center p-10 bg-gray-900 border border-gray-800 rounded-3xl shadow-lg">
            <span className="text-gray-400 font-semibold mb-2 uppercase tracking-widest text-sm">
              { result.movement_detected || detectedMovement }
            </span>
            <div className="flex items-baseline gap-2">
              <span className={ `text-7xl font-black ${ scorePercentage >= 80 ? 'text-emerald-400' : scorePercentage >= 50 ? 'text-amber-400' : 'text-red-400' }` }>
                { scoreObtenu }
              </span>
              <span className="text-4xl text-gray-600 font-bold">/ { scoreMax }</span>
            </div>
          </div>

          { result.lifter_persona && (() => {
            const { emoji, filename } = getPersonaAssets(result.lifter_persona);
            return (
              <div className="bg-gradient-to-br from-indigo-900 to-purple-900 border border-indigo-500/30 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row items-center gap-6 sm:gap-8 text-center sm:text-left transform transition-transform hover:scale-[1.02]">

                <div className="w-32 h-32 sm:w-40 sm:h-40 flex-shrink-0 bg-indigo-950/50 rounded-full border-4 border-indigo-400/50 overflow-hidden flex items-center justify-center shadow-inner relative">
                  <img
                    src={ `/images/personas/${ filename }` }
                    alt={ result.lifter_persona }
                    className="w-full h-full object-cover z-10"
                    onError={ (e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    } }
                  />
                  <div className="absolute inset-0 hidden items-center justify-center text-6xl sm:text-7xl z-0">
                    { emoji }
                  </div>
                </div>

                <div className="flex-1">
                  <span className="text-indigo-300 font-black uppercase tracking-widest text-xs mb-2 block">
                    Your Deadlift Persona
                  </span>
                  <h3 className="text-3xl sm:text-4xl font-black text-white mb-4 drop-shadow-md">
                    { result.lifter_persona }
                  </h3>
                  <p className="text-indigo-100 text-base sm:text-lg italic bg-black/20 p-4 rounded-xl leading-relaxed border border-indigo-500/20">
                    "{ result.persona_justification }"
                  </p>
                </div>
              </div>
            );
          })() }

          <div className="grid grid-cols-1 gap-4">
            { Object.entries(result).map(([ key, data ]) => {
              // Un critère est le seul objet de la réponse à porter une clé "score"
              // (éventuellement null quand il n'est pas visible à l'image). Tout le
              // reste — totaux, quota, persona — est ignoré sans liste à maintenir.
              if (!data || typeof data !== 'object' || !( 'score' in data )) return null;

              return (
                <ResultCard
                  key={ key }
                  criterionKey={ key }
                  data={ data }
                  isExpanded={ expandedCard === key }
                  onToggle={ () => setExpandedCard(expandedCard === key ? null : key) }
                  demo={ criteriaGuides[key] }
                />
              );
            }) }
          </div>

          <button
            onClick={ () => { setResult(null); setFile(null); setExpandedCard(null); setDetectedMovement(null); } }
            className="w-full mt-8 bg-gray-800 hover:bg-gray-700 text-white font-bold py-4 px-8 rounded-xl transition-all uppercase tracking-wider text-sm"
          >
            Analyze another video
          </button>
        </div>
      ) }

      { isFreeUser && loadingStep === 0 && !result && (
        <div className="mt-12">
          <AdBannerPlaceholder format="banner" />
        </div>
      ) }
    </div>
  );
}
