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