import { useEffect, useMemo, useRef } from 'react';
import { bboxLissee, transformDeZoom } from '../utils/poseCrop.js';

// Enveloppe la vidéo (+ son overlay squelette) et lui applique le zoom pose-tracké
// quand `enabled` : une bbox unique, calculée une fois pour tout le clip (voir
// `poseCrop.bboxLissee`), qu'on recentre à chaque redimensionnement. La bbox ne bouge
// pas d'une image à l'autre — c'est un plan fixe zoomé, pas un crop qui suit le lifter
// frame par frame, qui tremble dès qu'une pose est ratée.
//
// Le parent doit porter `overflow-hidden` : le contenu zoomé déborde de son cadre.
export default function PoseZoomFrame({ videoRef, squelette, enabled, children }) {
  const wrapRef = useRef(null);
  const bbox = useMemo(() => (enabled ? bboxLissee(squelette) : null), [ squelette, enabled ]);

  useEffect(() => {
    const video = videoRef.current;
    const wrap = wrapRef.current;
    if (!video || !wrap) return undefined;

    const applique = () => {
      const transform = transformDeZoom(video, bbox);
      wrap.style.transform = transform || '';
    };

    const ro = new ResizeObserver(applique);
    ro.observe(video);
    video.addEventListener('loadedmetadata', applique);
    applique();

    return () => {
      ro.disconnect();
      video.removeEventListener('loadedmetadata', applique);
    };
  }, [ videoRef, bbox ]);

  return (
    <div
      ref={ wrapRef }
      className="absolute inset-0 flex items-center justify-center transition-transform duration-300 ease-out"
      style={ { transformOrigin: '0 0' } }
    >
      { children }
    </div>
  );
}
