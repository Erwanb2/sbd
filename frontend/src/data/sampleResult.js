// Analyse "sample" figée, affichée dans la démo de la page d'accueil.
// Valeurs fictives pour l'instant (aucun appel Gemini) — même forme que la
// réponse de /api/analyze : des critères { score, feedback } + les totaux,
// la persona et le mouvement détecté. `score` est déjà compressé sur 1-3.
export const sampleResult = {
  movement_detected: 'conventional deadlift',
  total_raw_score: 18,
  raw_max_score: 24,
  not_assessable_count: 0,

  lifter_persona: 'The Crane',
  persona_justification:
    "Your hips shoot up the moment the bar leaves the floor, so the knees straighten before the hips do and the rest of the pull turns into a stiff-legged hinge. Strong back, wasted leg drive — the lift is there, your quads just never get invited.",

  starting_position: {
    score: 2,
    feedback:
      'Hips start a touch too high and the bar sits an inch in front of your mid-foot, so the first pull drags it back into your shins. Reset with the bar over your shoelaces and your shoulders just in front of it.',
  },
  slack_pull_and_lat_engagement: {
    score: 1,
    feedback:
      'No slack pull at all — you go from standing to full effort in one jerk. Take the tension out of the bar first: pull your chest up until you hear the plates click, then drive.',
  },
  leg_drive_activation: {
    score: 2,
    feedback:
      'Your hips shoot up ahead of the bar and the lift turns into a stiff-legged pull halfway through. Think about pushing the floor away and keeping your torso angle constant off the floor.',
  },
  hip_hinge_mechanics: {
    score: 3,
    feedback:
      'Solid posterior-chain tension once the bar breaks the floor — hamstrings and glutes are clearly doing their job. Slightly earlier knee-hip synchronisation would make it perfect.',
  },
  core_bracing_and_spine_neutrality: {
    score: 3,
    feedback:
      'Strong 360-degree brace and a neutral spine held from setup to lockout. Only the faintest upper-back rounding under load, which is safe and acceptable.',
  },
  bar_path_and_proximity: {
    score: 2,
    feedback:
      'The bar loops forward around your knees before coming back in. Keep it dragging up your shins and thighs the whole way — engage your lats to pull it into you.',
  },
  lockout_execution: {
    score: 3,
    feedback:
      'Crisp lockout with a real glute squeeze and no hitching. You finish tall without leaning back — exactly what a judge wants to see.',
  },
  eccentric_control_and_descent: {
    score: 2,
    feedback:
      'You bend your knees too early on the way down, so the bar has to travel forward over them. Push your hips back first and let the bar drop straight until it clears your knees.',
  },
};
