import { useState } from 'react';
import { UploadCloud, FileVideo, X } from 'lucide-react';

// Dropzone. Tant qu'aucun fichier n'est choisi il n'y a QUE le panneau pointillé
// (pas de gros bouton désactivé qui écrase la mise en page) : le CTA plein
// n'apparaît qu'une fois la vidéo sélectionnée.
export default function UploadZone({ file, setFile, handleUpload, limits, compact = false }) {
  const maxMb = limits?.maxUploadMb ?? 50;
  const maxSeconds = limits?.maxVideoSeconds ?? 60;
  const [ isDragging, setIsDragging ] = useState(false);

  const zoneState = isDragging
    ? 'border-emerald-400 bg-emerald-500/10'
    : file
      ? 'border-emerald-500/40 bg-emerald-500/[0.06]'
      : 'border-white/25 bg-gradient-to-b from-white/[0.07] to-white/[0.02] hover:border-white/40 hover:from-white/[0.1]';

  return (
    <form onSubmit={ handleUpload } className="w-full">
      <div
        onDragEnter={ (e) => { e.preventDefault(); setIsDragging(true); } }
        onDragOver={ (e) => e.preventDefault() }
        onDragLeave={ (e) => { e.preventDefault(); setIsDragging(false); } }
        onDrop={ () => setIsDragging(false) }
        className={ `relative rounded-2xl border border-dashed transition-all duration-200 ${ zoneState } ${ compact ? 'px-6 py-8' : 'px-6 py-12' }` }
      >
        <input
          type="file"
          accept="video/mp4,video/quicktime,video/mov"
          onChange={ (e) => setFile(e.target.files[0] || null) }
          className="absolute inset-0 z-10 h-full w-full cursor-pointer opacity-0"
          aria-label="Choose a video"
        />

        { file ? (
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
              <FileVideo className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1 text-left">
              <p className="truncate text-sm font-semibold text-white">{ file.name }</p>
              <p className="text-xs text-emerald-400/80">Ready to analyze</p>
            </div>
            <button
              type="button"
              onClick={ () => setFile(null) }
              className="relative z-20 rounded-lg p-2 text-gray-500 transition-colors hover:bg-white/10 hover:text-white"
              aria-label="Remove video"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center text-center">
            <div className={ `mb-4 flex items-center justify-center rounded-2xl border border-white/10 bg-white/5 ${ compact ? 'h-14 w-14' : 'h-16 w-16' }` }>
              <UploadCloud className={ `text-gray-300 ${ compact ? 'h-6 w-6' : 'h-7 w-7' }` } />
            </div>
            <p className="text-base font-bold text-white">
              Drag &amp; drop your set, or{ ' ' }
              <span className="text-emerald-400 underline decoration-emerald-400/40 underline-offset-4">
                browse
              </span>
            </p>
            <p className="mt-2 text-xs text-gray-500">
              Squat, bench or deadlift · MP4 or MOV · max { maxMb } MB, { maxSeconds }s
            </p>
          </div>
        ) }
      </div>

      { file && (
        <button
          type="submit"
          className="animate-fade-in-up mt-3 w-full rounded-2xl bg-white px-8 py-4 text-sm font-bold uppercase tracking-wide text-black transition-all hover:bg-gray-200 active:scale-[0.99]"
        >
          Start AI analysis
        </button>
      ) }
    </form>
  );
}
