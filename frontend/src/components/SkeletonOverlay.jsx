import { useEffect, useRef } from 'react';

// Paires de points a relier. L'ordre des points eux-memes vient du backend
// (`squelette.points`, ecrit une fois par resultat) ; ces paires sont dupliquees ici
// parce que chaque frame ne porte que des coordonnees, pas de noms — les repeter
// aurait multiplie le poids du bloc par le nombre de frames pour rien.
const SEGMENTS = [
  [ 'l_sh', 'r_sh' ], [ 'l_hip', 'r_hip' ],
  [ 'l_sh', 'l_hip' ], [ 'r_sh', 'r_hip' ],
  [ 'l_sh', 'l_el' ], [ 'l_el', 'l_wr' ],
  [ 'r_sh', 'r_el' ], [ 'r_el', 'r_wr' ],
  [ 'l_hip', 'l_kn' ], [ 'l_kn', 'l_an' ],
  [ 'r_hip', 'r_kn' ], [ 'r_kn', 'r_an' ],
  [ 'l_an', 'l_heel' ], [ 'l_heel', 'l_toe' ], [ 'l_an', 'l_toe' ],
  [ 'r_an', 'r_heel' ], [ 'r_heel', 'r_toe' ], [ 'r_an', 'r_toe' ],
];

// Meme seuil que `vis_legs > 0.4` cote pose (pose_analysis._cascade) : le front ne
// doit jamais montrer avec assurance un repere que le backend a lui-meme juge pas
// fiable.
const VISIBILITE_MIN = 0.4;

// Position interpolee lineairement entre les deux images de pose qui encadrent `t` :
// a 6 im/s (la cadence de la passe dense), sans interpolation le squelette saute
// visiblement toutes les 167ms.
function positionA(frames, t) {
  let lo = 0, hi = frames.length - 1;
  if (t <= frames[0].t) return frames[0].pts;
  if (t >= frames[hi].t) return frames[hi].pts;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (frames[mid].t <= t) lo = mid; else hi = mid;
  }
  const a = frames[lo], b = frames[hi];
  const k = (t - a.t) / ((b.t - a.t) || 1);
  return a.pts.map((p, i) => {
    const q = b.pts[i];
    return [ p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k, Math.min(p[2], q[2]) ];
  });
}

// Rectangle reellement occupe par l'image dans l'element <video> : celui-ci est en
// object-contain, donc des bandes noires (letterbox) encadrent l'image quand son
// ratio ne correspond pas au cadre. Les coordonnees normalisees ne doivent pas les
// traverser.
function rectangleVideo(video) {
  const vw = video.videoWidth, vh = video.videoHeight;
  const cw = video.clientWidth, ch = video.clientHeight;
  if (!vw || !vh || !cw || !ch) return null;
  const echelle = Math.min(cw / vw, ch / vh);
  const w = vw * echelle, h = vh * echelle;
  return { x: (cw - w) / 2, y: (ch - h) / 2, w, h };
}

// Squelette de la pose calque sur la video : c'est le meme suivi MediaPipe qui a deja
// servi a detecter la variante et les repetitions, jamais recalcule ici. `videoRef`
// est l'element <video> affiche a cote ; `squelette` vient de `result.squelette`.
export default function SkeletonOverlay({ videoRef, squelette, visible }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const frames = squelette?.frames;
    if (!video || !canvas || !visible || !frames?.length) return undefined;

    const ctx = canvas.getContext('2d');
    const indexDe = new Map(squelette.points.map((nom, i) => [ nom, i ]));

    const redimensionne = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = video.clientWidth * dpr;
      canvas.height = video.clientHeight * dpr;
      canvas.style.width = `${ video.clientWidth }px`;
      canvas.style.height = `${ video.clientHeight }px`;
    };

    const dessine = () => {
      const dpr = window.devicePixelRatio || 1;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const rect = rectangleVideo(video);
      if (!rect) return;
      const pts = positionA(frames, video.currentTime);
      ctx.strokeStyle = 'rgba(52, 211, 153, 0.9)';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      for (const [ a, b ] of SEGMENTS) {
        const pa = pts[indexDe.get(a)], pb = pts[indexDe.get(b)];
        if (!pa || !pb || pa[2] < VISIBILITE_MIN || pb[2] < VISIBILITE_MIN) continue;
        ctx.beginPath();
        ctx.moveTo(rect.x + pa[0] * rect.w, rect.y + pa[1] * rect.h);
        ctx.lineTo(rect.x + pb[0] * rect.w, rect.y + pb[1] * rect.h);
        ctx.stroke();
      }
    };

    let raf = null;
    const boucle = () => {
      dessine();
      if (!video.paused && !video.ended) raf = requestAnimationFrame(boucle);
    };
    const surLecture = () => { if (!raf) raf = requestAnimationFrame(boucle); };
    const surArretOuSeek = () => dessine();

    const ro = new ResizeObserver(() => { redimensionne(); dessine(); });
    ro.observe(video);
    redimensionne();
    dessine();

    video.addEventListener('play', surLecture);
    video.addEventListener('pause', surArretOuSeek);
    video.addEventListener('seeked', surArretOuSeek);
    video.addEventListener('loadedmetadata', surArretOuSeek);
    if (!video.paused) surLecture();

    return () => {
      if (raf) cancelAnimationFrame(raf);
      ro.disconnect();
      video.removeEventListener('play', surLecture);
      video.removeEventListener('pause', surArretOuSeek);
      video.removeEventListener('seeked', surArretOuSeek);
      video.removeEventListener('loadedmetadata', surArretOuSeek);
    };
  }, [ videoRef, squelette, visible ]);

  if (!squelette?.frames?.length) return null;

  return (
    <canvas
      ref={ canvasRef }
      className={ `pointer-events-none absolute inset-0 ${ visible ? '' : 'hidden' }` }
    />
  );
}
