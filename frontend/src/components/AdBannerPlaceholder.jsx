export default function AdBannerPlaceholder({ className = '', format = 'banner' }) {
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
