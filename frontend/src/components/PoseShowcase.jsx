import { useEffect, useRef, useState } from 'react';

// Vitrine MediaPipe de la démo sample : la vidéo passe du brut au rendu
// squelette dès que l'analyse démarre, avec un HUD qui rejoue les mesures
// réellement calculées sur ce clip (frontend/public/sample-deadlift-pose.json).
// `active` = l'analyse est lancée (step >= 1).
const RAW_SRC = '/sample-deadlift-crop.mp4';
const POSE_SRC = '/sample-deadlift-pose.mp4';
const POSE_DATA = '/sample-deadlift-pose.json';

export default function PoseShowcase({ active }) {
  const videoRef = useRef(null);
  const torsoRef = useRef(null);
  const barRef = useRef(null);
  const cursorRef = useRef(null);
  const [ data, setData ] = useState(null);

  // Les mesures ne servent qu'une fois l'analyse lancée : on ne les charge pas
  // tant que le visiteur regarde la vidéo brute.
  useEffect(() => {
    if (!active || data) return;
    fetch(POSE_DATA).then((r) => r.json()).then(setData).catch(() => {});
  }, [ active, data ]);

  // Le HUD suit la lecture à 60 fps : on écrit directement dans le DOM plutôt
  // que par un state React, qui re-rendrait tout le modal à chaque frame.
  useEffect(() => {
    if (!active || !data) return;
    let raf;
    const tick = () => {
      const v = videoRef.current;
      if (v && data.frames.length) {
        const i = Math.min(data.frames.length - 1, Math.round(v.currentTime * data.fps));
        const f = data.frames[i];
        if (f) {
          if (torsoRef.current) torsoRef.current.textContent = `${ f.torso.toFixed(0) }°`;
          if (barRef.current) barRef.current.textContent = `${ (f.bar * 100).toFixed(0) }%`;
        }
        if (cursorRef.current && v.duration) {
          cursorRef.current.style.left = `${ (v.currentTime / v.duration) * 100 }%`;
        }
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [ active, data ]);

  // Courbe de hauteur de barre sur tout le clip, tracée une fois pour toutes.
  const path = data?.frames.length
    ? data.frames
        .map((f, i) => `${ i === 0 ? 'M' : 'L' }${ (i / (data.frames.length - 1)) * 100 },${ 30 - f.bar * 28 }`)
        .join(' ')
    : null;

  return (
    <div className="mx-auto mb-6 grid max-w-2xl gap-4 sm:grid-cols-[minmax(0,240px)_minmax(0,1fr)] sm:items-start">

      <div
        className={ `relative overflow-hidden rounded-2xl border bg-black transition-all duration-500 ${
          active
            ? 'border-emerald-500/40 shadow-[0_0_60px_-18px_rgba(16,185,129,0.75)]'
            : 'border-gray-800'
        }` }
      >
        <video
          ref={ videoRef }
          key={ active ? 'pose' : 'raw' }
          src={ active ? POSE_SRC : RAW_SRC }
          className="block h-auto max-h-[45vh] w-full object-contain"
          autoPlay
          loop
          muted
          playsInline
        />

        { active && (
          <>
            <div className="animate-fade-in pointer-events-none absolute left-2 top-2 flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-black/70 px-2.5 py-1 backdrop-blur-sm">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              <span className="font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-emerald-300">
                Pose tracking
              </span>
            </div>
            <div className="animate-fade-in pointer-events-none absolute bottom-2 right-2 rounded-full border border-white/15 bg-black/70 px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.16em] text-white/70 backdrop-blur-sm">
              33 landmarks
            </div>
          </>
        ) }
      </div>

      { active ? (
        <div className="animate-fade-in-up space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <p className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-400">
            Measured · not guessed
          </p>

          <div className="grid grid-cols-2 gap-3">
            <Metric label="Torso angle" valueRef={ torsoRef } accent="text-emerald-300" />
            <Metric label="Bar height" valueRef={ barRef } accent="text-amber-300" />
          </div>

          <div>
            <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-gray-500">
              Bar path
            </p>
            <div className="relative">
              <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="block h-14 w-full">
                { path && (
                  <path d={ path } fill="none" stroke="#fbbf24" strokeWidth="1.2"
                        vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
                ) }
              </svg>
              <span ref={ cursorRef } className="pointer-events-none absolute inset-y-0 w-px bg-emerald-400/80" />
            </div>
          </div>

          <p className="text-[11px] leading-relaxed text-gray-500">
            Every number above is read off your video by MediaPipe Pose — 33 body
            landmarks, frame by frame — before the coaching model says a word.
          </p>
        </div>
      ) : (
        <div className="hidden rounded-2xl border border-dashed border-gray-800 p-4 sm:block">
          <p className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-gray-600">
            Pose engine · idle
          </p>
          <p className="mt-2 text-[11px] leading-relaxed text-gray-600">
            Hit analyze and watch the skeleton lock onto the lift.
          </p>
        </div>
      ) }
    </div>
  );
}

function Metric({ label, valueRef, accent }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/40 px-3 py-2">
      <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-gray-500">{ label }</p>
      <p ref={ valueRef } className={ `font-mono text-2xl font-bold tabular-nums ${ accent }` }>—</p>
    </div>
  );
}
