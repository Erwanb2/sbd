import { useState } from 'react';

export default function ProfileModal({ user, tokenAPI, onClose, onUpdateUser }) {
  const [isProcessing, setIsProcessing] = useState(false);

  const maxQuota = user.plan === 'premium' ? 50 : 3;
  const usedQuota = maxQuota - user.quota_left;
  const usagePercent = Math.min((usedQuota / maxQuota) * 100, 100);

  const handlePlanChange = async (newPlan) => {
    if (user.plan === newPlan) return;
    
    setIsProcessing(true);
    try {
      const res = await fetch('/api/users/me/plan', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${ tokenAPI }`
        },
        body: JSON.stringify({ plan: newPlan })
      });

      const data = await res.json();
      if (res.ok) {
        onUpdateUser({ plan: data.plan, quota_left: data.quota_left });
      } else {
        alert("Error changing plan: " + data.detail);
      }
    } catch (error) {
      alert("Network error.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-gray-950 border border-gray-800 rounded-3xl w-full max-w-4xl shadow-2xl overflow-y-auto max-h-[95vh] relative flex flex-col md:flex-row">
        
        <button 
          onClick={ onClose }
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center bg-gray-900 hover:bg-gray-800 text-gray-400 hover:text-white rounded-full transition-colors z-10"
        >
          ✕
        </button>

        {/* LEFT: User Info */}
        <div className="md:w-1/3 bg-gray-900 p-8 border-r border-gray-800 flex flex-col">
          <div className="w-20 h-20 bg-gradient-to-tr from-emerald-500 to-teal-400 rounded-full flex items-center justify-center text-3xl font-black mb-4 shadow-lg text-white">
            { user.email.charAt(0).toUpperCase() }
          </div>
          <h2 className="text-xl font-bold truncate" title={ user.email }>{ user.email }</h2>
          <span className="inline-block bg-gray-800 text-gray-300 text-xs px-3 py-1 rounded-full uppercase tracking-widest font-semibold mt-2 w-max">
            Plan { user.plan }
          </span>

          <div className="mt-auto pt-8">
            <h3 className="text-sm text-gray-400 font-semibold uppercase tracking-wider mb-2">Today's Usage</h3>
            <div className="flex justify-between text-xs mb-1 font-medium">
              <span>{ usedQuota } analyses</span>
              <span>{ maxQuota } analyses</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-2 mb-2 overflow-hidden">
              <div 
                className={ `h-2 rounded-full transition-all duration-1000 ${ usagePercent > 80 ? 'bg-red-500' : 'bg-emerald-500' }` } 
                style={ { width: `${ usagePercent }%` } }
              ></div>
            </div>
            <p className="text-xs text-gray-500">Resets at midnight (UTC).</p>
          </div>
        </div>

        {/* RIGHT: Pricing */}
        <div className="md:w-2/3 p-8">
          <h2 className="text-2xl font-black uppercase tracking-wide mb-6">Manage Subscription</h2>
          
          <div className="grid md:grid-cols-2 gap-4">
            
            {/* FREE CARD */}
            <div className={ `border rounded-2xl p-6 transition-all ${ user.plan === 'free' ? 'border-gray-500 bg-gray-800/30' : 'border-gray-800 bg-gray-900' }` }>
              <h3 className="text-lg font-bold text-gray-300 mb-1">Free</h3>
              <div className="text-3xl font-black mb-4">€0 <span className="text-sm text-gray-500 font-normal">/month</span></div>
              <ul className="space-y-3 text-sm text-gray-400 mb-8">
                <li className="flex items-center gap-2">✓ 3 analyses / day</li>
                <li className="flex items-center gap-2">✓ Standard AI Model</li>
                <li className="flex items-center gap-2 text-gray-600">✕ Ads displayed</li>
              </ul>
              <button 
                disabled={ user.plan === 'free' || isProcessing }
                onClick={ () => handlePlanChange('free') }
                className={ `w-full py-3 rounded-xl font-bold transition-all text-sm uppercase tracking-wide ${ user.plan === 'free' ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-gray-800 hover:bg-gray-700 text-white' }` }
              >
                { user.plan === 'free' ? 'Current Plan' : 'Switch to Free' }
              </button>
            </div>

            {/* PREMIUM CARD */}
            <div className={ `border rounded-2xl p-6 relative transition-all shadow-xl ${ user.plan === 'premium' ? 'border-emerald-500 bg-emerald-900/10 shadow-[0_0_20px_rgba(16,185,129,0.15)]' : 'border-gray-700 bg-gray-800 hover:border-gray-600' }` }>
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] uppercase font-black tracking-widest px-3 py-1 rounded-full shadow-lg">
                Recommended
              </div>

              <h3 className="text-lg font-bold text-emerald-400 mb-1">Premium</h3>
              <div className="text-3xl font-black mb-4 text-white">€5 <span className="text-sm text-gray-500 font-normal">/month</span></div>
              <ul className="space-y-3 text-sm text-gray-300 mb-8">
                <li className="flex items-center gap-2">🔥 <strong className="text-white">50 analyses</strong> / day</li>
                <li className="flex items-center gap-2">🚀 Precision AI Model</li>
                <li className="flex items-center gap-2">🚫 <strong>Zero ads</strong></li>
              </ul>
              <button 
                disabled={ user.plan === 'premium' || isProcessing }
                onClick={ () => handlePlanChange('premium') }
                className={ `w-full py-3 rounded-xl font-bold transition-all text-sm uppercase tracking-wide ${ user.plan === 'premium' ? 'bg-emerald-500/20 text-emerald-500 cursor-not-allowed' : 'bg-emerald-500 hover:bg-emerald-400 text-white shadow-[0_0_15px_rgba(16,185,129,0.4)]' }` }
              >
                { isProcessing ? 'Loading...' : user.plan === 'premium' ? 'Current Plan' : 'Upgrade to Premium' }
              </button>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}