import { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import UploadZone from './components/UploadZone.jsx';
import ProfileModal from './components/ProfileModal.jsx';
import AdBannerPlaceholder from './components/AdBannerPlaceholder.jsx';
import LandingScreen from './components/LandingScreen.jsx';
import AuthModal from './components/AuthModal.jsx';
import SampleModal from './components/SampleModal.jsx';
import ResultView from './components/ResultView.jsx';
import AnalysisLoader from './components/AnalysisLoader.jsx';
import AnalysisOverlay from './components/AnalysisOverlay.jsx';

import { validateVideoFile, DEFAULT_LIMITS } from './utils/videoValidation.js';

export default function App() {
  const [ file, setFile ] = useState(null);
  const [ result, setResult ] = useState(null);
  const [ loadingStep, setLoadingStep ] = useState(0);
  const [ detectedMovement, setDetectedMovement ] = useState(null);
  // Jeton d'une analyse déjà calculée côté serveur mais pas encore déverrouillée.
  const [ claimToken, setClaimToken ] = useState(null);

  const [ tokenAPI, setTokenAPI ] = useState(null);
  const [ user, setUser ] = useState(null);
  const [ showProfile, setShowProfile ] = useState(false);
  const [ showAuthModal, setShowAuthModal ] = useState(false);
  const [ showSample, setShowSample ] = useState(false);
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

  // Déverrouille un résultat déjà calculé : c'est CE appel qui consomme un
  // crédit, et le seul qui renvoie réellement la note au client.
  const claimResult = async (token, authToken) => {
    try {
      const res = await fetch('/api/analysis/claim', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${ authToken }`
        },
        body: JSON.stringify({ claim_token: token }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not unlock the analysis");

      if (data.quota_restant !== undefined) {
        setUser(prev => ( { ...prev, quota_left: data.quota_restant } ));
      }
      setResult(data);
      setClaimToken(null);
      setFile(null);
    } catch (error) {
      alert(`Error ❌ : ${ error.message }`);
    } finally {
      setLoadingStep(0);
    }
  };

  // Parcours unique, connecté ou non : on lance l'analyse tout de suite, et on
  // ne demande le compte qu'au moment de dévoiler le résultat.
  const runAnalysis = async () => {
    if (!file) return;

    setLoadingStep(1);
    setResult(null);
    setDetectedMovement(null);
    setClaimToken(null);
    setShowAuthModal(false);

    let token = null;

    try {
      const formData = new FormData();
      formData.append('video', file);

      const initResponse = await fetch('/api/anonymous/upload_and_detect', {
        method: 'POST',
        body: formData,
      });
      const initData = await initResponse.json();

      if (!initResponse.ok) throw new Error(initData.detail || "Initialisation failed");

      token = initData.claim_token;
      setClaimToken(token);
      setDetectedMovement(initData.mouvement_detecte);
      setLoadingStep(2);

      const analyzeResponse = await fetch('/api/anonymous/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim_token: token }),
      });
      const analyzeData = await analyzeResponse.json();

      if (!analyzeResponse.ok) throw new Error(analyzeData.detail || "Analysis error");

    } catch (error) {
      alert(`Error ❌ : ${ error.message }`);
      setClaimToken(null);
      setLoadingStep(0);
      return;
    }

    if (tokenAPI) {
      await claimResult(token, tokenAPI);
    } else {
      setLoadingStep(0);
      setShowAuthModal(true);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    // Pré-validation locale : taille + durée, avant de lancer quoi que ce soit.
    const check = await validateVideoFile(file, limits);
    if (!check.ok) {
      alert(`Error ❌ : ${ check.error }`);
      return;
    }

    runAnalysis();
  };

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
        setShowAuthModal(false);

        // Une analyse attendait d'être déverrouillée : on enchaîne directement.
        if (claimToken) {
          setLoadingStep(2);
          claimResult(claimToken, data.access_token);
        }
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

  // --- VISITEUR NON CONNECTÉ : page d'accueil ---
  if (!tokenAPI && !result) {
    return (
      <>
        <LandingScreen
          file={ file }
          setFile={ setFile }
          onSubmit={ handleUpload }
          limits={ limits }
          onOpenSample={ () => setShowSample(true) }
          pendingClaim={ !!claimToken }
          onResumeClaim={ () => setShowAuthModal(true) }
        />

        { loadingStep > 0 && (
          <AnalysisOverlay step={ loadingStep } movement={ detectedMovement } />
        ) }

        { showSample && (
          <SampleModal
            onClose={ () => setShowSample(false) }
            onUploadOwn={ () => setShowSample(false) }
          />
        ) }

        { showAuthModal && (
          <AuthModal
            fileName={ file?.name }
            movement={ detectedMovement }
            onSuccess={ handleGoogleSuccess }
            onError={ () => alert('Login failed') }
            onClose={ () => setShowAuthModal(false) }
          />
        ) }
      </>
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
        <div className="animate-fade-in flex flex-col items-center w-full">
          <div className="w-full max-w-2xl">
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
        <div className="mt-10 animate-fade-in">
          <AnalysisLoader step={ loadingStep } movement={ detectedMovement } />

          { isFreeUser && (
            <div className="mt-8 max-w-2xl mx-auto animate-fade-in">
              <AdBannerPlaceholder format="rectangle" />
            </div>
          ) }
        </div>
      ) }

      { /* --- ZONE DE RÉSULTATS --- */ }
      { result && loadingStep === 0 && (
        <div className="animate-fade-in-up">
          <ResultView
            result={ result }
            movement={ detectedMovement }
            onReset={ () => { setResult(null); setFile(null); setDetectedMovement(null); } }
          />
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
