export default function Tabs({ activeTab, setActiveTab, disabled }) {
  const tabs = [
    { id: 'squat', label: 'Squat', bg: 'bg-red-500' },
    { id: 'bench', label: 'Bench Press', bg: 'bg-blue-500' },
    { id: 'deadlift', label: 'Deadlift', bg: 'bg-emerald-500' },
  ];

  return (
    <div className="flex justify-center gap-4 mb-8">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => !disabled && setActiveTab(tab.id)}
          disabled={disabled}
          className={`px-8 py-3 rounded-full font-bold text-sm uppercase tracking-wider transition-all duration-300 ${
            activeTab === tab.id 
              ? `${tab.bg} text-white shadow-[0_0_20px_rgba(0,0,0,0.3)] shadow-${tab.bg.split('-')[1]}-500/50`
              : 'bg-gray-900 text-gray-400 cursor-default opacity-50'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}