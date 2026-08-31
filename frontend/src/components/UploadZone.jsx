import { UploadCloud } from 'lucide-react';

export default function UploadZone({ file, setFile, handleUpload, limits }) {
  const maxMb = limits?.maxUploadMb ?? 50;
  const maxSeconds = limits?.maxVideoSeconds ?? 60;
  return (
    <form onSubmit={handleUpload} className="animate-in fade-in zoom-in-95 duration-500">
      <div className="bg-gray-900 border border-gray-800 rounded-3xl p-8 shadow-2xl transition-all hover:border-gray-700">
        <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-700 hover:border-gray-500 rounded-2xl p-16 bg-gray-950/50 transition-colors cursor-pointer relative group">
          <UploadCloud className="w-16 h-16 text-gray-600 mb-4 group-hover:text-white transition-colors" />
          <p className="text-gray-300 font-medium mb-1 text-center">
            Drag and drop your Squat, Bench or Deadlift video<br/>
          </p>
          <p className="text-gray-500 text-sm mt-4">
            MP4, MOV — max { maxMb } MB, { maxSeconds }s (one set only)
          </p>


          <input
            type="file"
            accept="video/mp4,video/quicktime,video/mov"
            onChange={(e) => setFile(e.target.files[0])}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          {file && (
            <div className="absolute bottom-4 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30 font-medium">
              Prêt à analyser : {file.name}
            </div>
          )}
        </div>
        <button 
          type="submit" 
          disabled={!file}
          className="w-full mt-6 bg-white text-black hover:bg-gray-200 font-bold py-4 px-8 rounded-xl disabled:opacity-50 transition-all uppercase tracking-wide"
        >
          Start AI analysis
        </button>
      </div>
    </form>
  );
}