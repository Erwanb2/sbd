import { useState, useEffect, useRef } from 'react';
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

// Délai avant d'inviter le visiteur à se connecter, une fois l'analyse lancée.
const AUTH_PROMPT_DELAY_MS = 5000;

export default function App() {
  // Bascule de modele d'analyse, pour comparer 3.5 et 3.7 sur une meme video.
  // Volontairement discrete : c'est un outil de debug, pas une fonctionnalite.
  const [ modelKey, setModelKey ] = useState(() => localStorage.getItem('sbd_model') || '3.5');
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
  // L'analyse tourne en coulisse pendant que le visiteur se connecte : la
  // modale s'ouvre au bout de AUTH_PROMPT_DELAY_MS, bien avant la fin du calcul.
  const [ analysisReady, setAnalysisReady ] = useState(false);

  // Refs pour lire l'état courant depuis les callbacks asynchrones (le
  // déverrouillage peut arriver avant ou après la connexion, dans les deux sens).
  const authTokenRef = useRef(null);
  const analysisReadyRef = useRef(false);
  const authPromptTimerRef = useRef(null);

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

  useEffect(() => () => clearTimeout(authPromptTimerRef.current), []);

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
        body: JSON.stringify({ claim_token: token, model: modelKey }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not unlock the analysis");

      if (data.quota_restant !== undefined) {
        setUser(prev => ( { ...prev, quota_left: data.quota_restant } ));
      }
      setResult(data);
      setClaimToken(null);
      setFile(null);
      setAnalysisReady(false);
      analysisReadyRef.current = false;
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
    setAnalysisReady(false);
    analysisReadyRef.current = false;

    // On demande la connexion pendant que le serveur travaille : le temps
    // d'attente sert à quelque chose au lieu d'être du temps mort.
    clearTimeout(authPromptTimerRef.current);
    if (!authTokenRef.current) {
      authPromptTimerRef.current = setTimeout(() => {
        if (!authTokenRef.current) setShowAuthModal(true);
      }, AUTH_PROMPT_DELAY_MS);
    }

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
        body: JSON.stringify({ claim_token: token, model: modelKey }),
      });
      const analyzeData = await analyzeResponse.json();

      if (!analyzeResponse.ok) throw new Error(analyzeData.detail || "Analysis error");

    } catch (error) {
      clearTimeout(authPromptTimerRef.current);
      alert(`Error ❌ : ${ error.message }`);
      setClaimToken(null);
      setShowAuthModal(false);
      setLoadingStep(0);
      return;
    }

    clearTimeout(authPromptTimerRef.current);
    setAnalysisReady(true);
    analysisReadyRef.current = true;

    // Le visiteur a pu se connecter pendant le calcul : on lit le jeton via la
    // ref, la valeur d'état capturée ici serait périmée.
    if (authTokenRef.current) {
      await claimResult(token, authTokenRef.current);
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
        authTokenRef.current = data.access_token;
        setTokenAPI(data.access_token);
        setUser(data.user);
        setShowAuthModal(false);

        // Une analyse déjà terminée attendait d'être déverrouillée : on
        // enchaîne. Si elle tourne encore, runAnalysis fera le claim lui-même
        // à la fin en relisant authTokenRef.
        if (claimToken && analysisReadyRef.current) {
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
            analysisReady={ analysisReady }
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

      <button
        onClick={ () => {
          const suivant = modelKey === '3.5' ? '3.7' : '3.5';
          setModelKey(suivant);
          localStorage.setItem('sbd_model', suivant);
        } }
        title="Modele d'analyse (debug)"
        className="fixed bottom-2 right-2 z-40 text-[10px] font-mono text-gray-700 hover:text-gray-400 px-1.5 py-0.5 rounded transition-colors"
      >
        { modelKey }
      </button>

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
