export const getScoreColor = (score) => {
  // Critère non évaluable (hors cadre) : neutre, surtout pas rouge "danger".
  if (score === null || score === undefined) return 'bg-gray-500/10 text-gray-400 border-gray-500/30';
  if (score === 3) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  if (score === 2) return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  return 'bg-red-500/10 text-red-400 border-red-500/30';
};

export const formatKey = (key) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

// "0:07" — pour situer une rep dans la vidéo (`debut_s`/`fin_s`), jamais pour une
// durée de série : au-delà d'une minute la page n'a pas besoin des heures.
export const formatTemps = (secondes) => {
  if (secondes == null) return null;
  const s = Math.max(0, Math.round(secondes));
  return `${ Math.floor(s / 60) }:${ String(s % 60).padStart(2, '0') }`;
};