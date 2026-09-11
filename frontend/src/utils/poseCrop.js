// Bbox UNIQUE, lissée sur tout le clip, calculée à partir du squelette pose déjà exposé
// par le backend (`result.squelette`) — jamais recalculée, même suivi MediaPipe que le
// reste de la page. Sert au zoom pose-tracké de ResultView (PoseZoomFrame.jsx).
//
// Méthode validée par exploration (planche de contact sur 14 clips) : recalculer un
// crop frame par frame décroche dès qu'une pose est ratée ou accroche la mauvaise
// personne. Une bbox par frame, union ROBUSTE (rejet des frames dont le centre s'écarte
// trop de la médiane), puis marge — donne un plan fixe stable au lieu d'un crop qui
// tremble.
//
// Limite connue : si une deuxième personne reste proche du lifter tout le clip (visible
// sur jeff_nippard_sumo.mp4), le rejet par distance au centre ne suffit pas toujours à
// l'exclure et la bbox s'étire pour englober les deux — le zoom devient alors inutile.
// Pas de parade en place ; une piste serait de filtrer aussi par cohérence de TAILLE de
// la pose plutôt que par distance seule.

const VIS_MIN = 0.3;
const MARGE = 0.18;
const OUTLIER_MULT = 1.0;
const MAX_ZOOM = 2.5;

function bboxFrame(pts) {
  const xs = [];
  const ys = [];
  for (const [ x, y, v ] of pts) {
    if (v >= VIS_MIN) { xs.push(x); ys.push(y); }
  }
  if (xs.length < 4) return null;
  return [ Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys) ];
}

function mediane(valeurs) {
  const s = [ ...valeurs ].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function ajouteMarge([ x0, y0, x1, y1 ], marge) {
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  let bw = (x1 - x0) * (1 + 2 * marge);
  let bh = (y1 - y0) * (1 + 2 * marge);
  let nx0 = cx - bw / 2, nx1 = cx + bw / 2;
  let ny0 = cy - bh / 2, ny1 = cy + bh / 2;
  // recale dans [0,1] plutôt que de rogner : le cadre garde sa taille
  if (nx0 < 0) { nx1 -= nx0; nx0 = 0; }
  if (nx1 > 1) { nx0 -= (nx1 - 1); nx1 = 1; }
  if (ny0 < 0) { ny1 -= ny0; ny0 = 0; }
  if (ny1 > 1) { ny0 -= (ny1 - 1); ny1 = 1; }
  return [ Math.max(0, nx0), Math.max(0, ny0), Math.min(1, nx1), Math.min(1, ny1) ];
}

// Renvoie [x0, y0, x1, y1] normalisés [0,1] dans le repère de `squelette` (même repère
// que `videoWidth`/`videoHeight`), ou null si le clip n'a pas assez de pose exploitable.
export function bboxLissee(squelette) {
  const frames = squelette?.frames;
  if (!frames?.length) return null;

  const boxes = frames.map((f) => bboxFrame(f.pts)).filter(Boolean);
  if (boxes.length < 3) return null;

  const cx = boxes.map(([ x0, , x1 ]) => (x0 + x1) / 2);
  const cy = boxes.map(([ , y0, , y1 ]) => (y0 + y1) / 2);
  const mcx = mediane(cx), mcy = mediane(cy);
  const mw = mediane(boxes.map(([ x0, , x1 ]) => x1 - x0));
  const mh = mediane(boxes.map(([ , y0, , y1 ]) => y1 - y0));

  let gardees = boxes.filter((_, i) =>
    Math.abs(cx[i] - mcx) < OUTLIER_MULT * Math.max(mw, 1e-3) &&
    Math.abs(cy[i] - mcy) < OUTLIER_MULT * Math.max(mh, 1e-3));
  if (gardees.length < Math.max(3, boxes.length / 4)) gardees = boxes;

  const x0 = Math.min(...gardees.map((b) => b[0]));
  const y0 = Math.min(...gardees.map((b) => b[1]));
  const x1 = Math.max(...gardees.map((b) => b[2]));
  const y1 = Math.max(...gardees.map((b) => b[3]));
  return ajouteMarge([ x0, y0, x1, y1 ], MARGE);
}

// Transform CSS (translate + scale, coin haut-gauche comme origine) qui zoome sur la
// bbox au centre de l'élément vidéo. `video` porte `videoWidth/videoHeight` (résolution
// intrinsèque) et `clientWidth/clientHeight` (boîte affichée, object-contain).
export function transformDeZoom(video, bbox) {
  const vw = video.videoWidth, vh = video.videoHeight;
  const cw = video.clientWidth, ch = video.clientHeight;
  if (!bbox || !vw || !vh || !cw || !ch) return null;

  const echelle = Math.min(cw / vw, ch / vh);
  const contenuW = vw * echelle, contenuH = vh * echelle;
  const rectX = (cw - contenuW) / 2, rectY = (ch - contenuH) / 2;

  const [ x0, y0, x1, y1 ] = bbox;
  const bboxW = (x1 - x0) * contenuW, bboxH = (y1 - y0) * contenuH;
  if (bboxW < 1 || bboxH < 1) return null;

  const s = Math.min(MAX_ZOOM, Math.max(1, Math.min(cw / bboxW, ch / bboxH)));
  const px = rectX + ((x0 + x1) / 2) * contenuW;
  const py = rectY + ((y0 + y1) / 2) * contenuH;
  const tx = cw / 2 - s * px;
  const ty = ch / 2 - s * py;
  return `translate(${ tx }px, ${ ty }px) scale(${ s })`;
}
