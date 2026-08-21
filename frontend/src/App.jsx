import { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import Header from './components/Header.jsx';
import Tabs from './components/Tabs.jsx';
import UploadZone from './components/UploadZone.jsx';
import ResultCard from './components/ResultCard.jsx';
import LoadingProgress from './components/LoadingProgress.jsx';
import ProfileModal from './components/ProfileModal.jsx';

import badLegDrive from './images/bad-leg-drive.png';
import goodLegDrive from './images/good-leg-drive.png';

// --- AD BANNER PLACEHOLDER ---
function AdBannerPlaceholder({ className = '', format = 'banner' }) {
  return (
    <div
      className={ `w-full bg-gray-900/60 border border-dashed border-gray-700/70 rounded-2xl p-4 flex flex-col items-center justify-center text-center overflow-hidden ${ format === 'rectangle' ? 'min-h-[250px]' : 'min-h-[90px]' } ${ className }` }
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

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [activeTab, setActiveTab] = useState('squat');
  const [expandedCard, setExpandedCard] = useState(null);

  const [tokenAPI, setTokenAPI] = useState(null); 
  const [user, setUser] = useState(null); 
  const [showProfile, setShowProfile] = useState(false);

  const isFreeUser = user?.plan?.toLowerCase() !== 'premium' && user?.plan?.toLowerCase() !== 'pro';

  // --- UPDATED DICTIONARY (Matching the new English backend keys) ---
  const demoAnimations = {
    hip_height_and_stability: "https://media.giphy.com/media/3o7TKnPOnEbGOXwQOQ/giphy.gif",
    
    leg_drive_activation: {
      bad: {
        title: "Common Mistake (Poor Leg Drive)",
        image: badLegDrive, 
        description: "In this image, the lifter straightens their legs too early. As a result, the hips shoot up before the bar even leaves the floor.",
        problem: "Since the legs are already straight, they can no longer assist in lifting the weight. All the load violently shifts to the lower back and hamstrings (bright red area). This is the easiest way to injure your lumbar spine, as you're 'pulling' the bar with your back instead of pushing with your legs."
      },
      good: {
        title: "Ideal Posture (Proper Leg Drive)",
        image: goodLegDrive, 
        description: "Here, the posture is corrected. The hips are lower, knees are bent, and the chest is proud. The quads and glutes (in blue) are engaged and ready to do the heavy lifting. The lower back is protected.",
        tip: "Look at the green arrows! To lift the bar properly, don't think about 'pulling' it up. Imagine pressing the floor away forcefully with your feet (like on a leg press machine) while driving your chest up. That is a proper leg drive!"
      }
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      // MODIFIÉ ICI : Utilisation de /api au lieu de http://localhost:8000
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
    setExpandedCard(null);

    try {
      const formData = new FormData();
      formData.append('video', file);

      // MODIFIÉ ICI : Utilisation de /api au lieu de http://localhost:8000
      const detectResponse = await fetch('/api/detect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${ tokenAPI }`
        },
        body: formData,
      });
      const detectData = await detectResponse.json();

      if (!detectResponse.ok) throw new Error(detectData.detail || "Detection error");

      if (detectData.quota_restant !== undefined) {
        setUser(prev => ({ ...prev, quota_left: detectData.quota_restant }));
      }

      // Handle both French and English keys from your backend just in case
      const detectedMovement = detectData.movement_detected || detectData.mouvement_detecte;
      setActiveTab(detectedMovement);
      setLoadingStep(2);

      // MODIFIÉ ICI : Utilisation de /api au lieu de http://localhost:8000
      const analyzeResponse = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${ tokenAPI }`
        },
        body: JSON.stringify({
          file_name: detectData.file_name,
          movement: detectedMovement
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

  // Adjust these keys if your backend now sends english keys like "raw_overall_score"
  const rawScore = result?.note_globale_brute || result?.raw_overall_score;
  const maxScore = result?.score_max_brut || result?.raw_max_score;
  const noteSur20 = result && maxScore ? Math.round((rawScore / maxScore) * 20) : 0;

  if (!tokenAPI) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white gap-6">
        <h1 className="text-4xl font-black uppercase tracking-wider mb-2">SBD Reviews</h1>
        <p className="text-gray-400 mb-6 text-center max-w-md">
          Sign in with Google to have your form analyzed by our AI.
        </p>
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
      
      <Tabs activeTab={ activeTab } setActiveTab={ setActiveTab } disabled={ !!result || loadingStep > 0 } />

      { loadingStep === 0 && !result && (
        <UploadZone file={ file } setFile={ setFile } handleUpload={ handleUpload } />
      ) }

      { loadingStep > 0 && (
        <div className="space-y-6">
          <LoadingProgress step={ loadingStep } />
          
          { isFreeUser && (
            <div className="mt-8 animate-in fade-in duration-500">
              <AdBannerPlaceholder format="rectangle" />
            </div>
          ) }
        </div>
      ) }

      { result && loadingStep === 0 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex flex-col items-center justify-center p-10 bg-gray-900 border border-gray-800 rounded-3xl shadow-lg">
            <span className="text-gray-400 font-semibold mb-2 uppercase tracking-widest text-sm">
              Technical Score: { result.mouvement_detecte || result.movement_detected }
            </span>
            <div className="flex items-baseline gap-2">
              <span className={ `text-7xl font-black ${ noteSur20 >= 16 ? 'text-emerald-400' : noteSur20 >= 10 ? 'text-amber-400' : 'text-red-400' }` }>
                { noteSur20 }
              </span>
              <span className="text-4xl text-gray-600 font-bold">/ 20</span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            { Object.entries(result).map(([key, data]) => {
              // Ignore technical root keys
              if (['note_globale_brute', 'score_max_brut', 'mouvement_detecte', 'quota_restant', 'raw_overall_score', 'raw_max_score', 'movement_detected', 'quota_left'].includes(key)) return null;
              
              return (
                <ResultCard
                  key={ key }
                  criterionKey={ key }
                  data={ data }
                  isExpanded={ expandedCard === key }
                  onToggle={ () => setExpandedCard(expandedCard === key ? null : key) }
                  demo={ demoAnimations[key] } 
                />
              );
            }) }
          </div>

          <button
            onClick={ () => { setResult(null); setFile(null); setExpandedCard(null); } }
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