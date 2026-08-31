// Association persona (texte renvoyé par l'IA) -> image + emoji de secours.
export const getPersonaAssets = (persona) => {
  if (!persona) return { emoji: '🏋️', filename: 'default.png' };
  const p = persona.toLowerCase();

  if (p.includes('grip')) return { emoji: '🚀', filename: 'grip-and-rip.png' };
  if (p.includes('crane')) return { emoji: '🏗️', filename: 'crane.png' };
  if (p.includes('squatter')) return { emoji: '📉', filename: 'squatter.png' };
  if (p.includes('extender')) return { emoji: '⚠️', filename: 'over-extender.png' };
  if (p.includes('fishing')) return { emoji: '🎣', filename: 'fishing-rod.png' };
  if (p.includes('pendulum')) return { emoji: '🔄', filename: 'pendulum.png' };
  if (p.includes('kneecapper')) return { emoji: '🦵', filename: 'kneecapper.png' };
  if (p.includes('rex')) return { emoji: '🦖', filename: 't-rex.png' };
  if (p.includes('soft')) return { emoji: '🫠', filename: 'soft-lock.png' };
  if (p.includes('x-wing')) return { emoji: '🚀', filename: 'x-wing.png' };
  if (p.includes('helicopter')) return { emoji: '🚁', filename: 'helicopter.png' };

  return { emoji: '💪', filename: 'default.png' };
};

export const loadingTips = {
  squat:
    'Focus on bracing your core before descending to maintain a neutral spine under heavy load.',
  'bench press':
    'Keep your shoulder blades retracted and depressed into the bench to protect your shoulders.',
  'conventional deadlift':
    'Ensure the bar is exactly over your mid-foot before you pull the slack out.',
  'sumo deadlift':
    "Think about 'spreading the floor' apart with your feet to engage your adductors and glutes.",
};
