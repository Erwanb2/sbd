// Analyse "sample" figée, affichée dans la démo de la page d'accueil.
// Valeurs fictives pour l'instant (aucun appel Gemini) — même forme que la
// réponse de /api/analyze : une liste `reps` notée rep par rep, des critères
// de synthèse { score, feedback } dont la note est la moyenne arrondie à
// l'inférieur des reps, puis les totaux, le persona et le mouvement détecté.
// Les `score` sont déjà compressés sur 1-3.
//
// Les notes ci-dessous sont cohérentes entre elles, et elles doivent le rester :
// chaque critère de synthèse vaut la moyenne de ses trois notes par rep arrondie
// au plus proche, la note d'une rep la moyenne de ses huit critères, et
// `total_raw_score` la somme des neuf critères (les huit + set_consistency).
export const sampleResult = {
  movement_detected: 'conventional deadlift',
  total_raw_score: 20,
  raw_max_score: 27,
  not_assessable_count: 0,
  rep_count: 3,

  lifter_persona: 'The Crane',
  persona_justification:
    "Your hips shoot up the moment the bar leaves the floor, so the knees straighten before the hips do and the rest of the pull turns into a stiff-legged hinge. Strong back, wasted leg drive — the lift is there, your quads just never get invited.",

  reps: [
    {
      rep_index: 1,
      score: 3,
      total: 22,
      max: 24,
      not_assessable_count: 0,
      starting_position: { score: 3, note: 'Bar over the shoelaces, shins touching, shoulders just in front of the bar.' },
      slack_pull_and_lat_engagement: { score: 1, note: 'Even on your best rep the bar jumps off the floor with no tension taken out first.' },
      leg_drive_activation: { score: 3, note: 'Torso angle holds through the first third, hips and shoulders rise together.' },
      hip_hinge_mechanics: { score: 3, note: 'One continuous motion, no separate knee phase around the shins.' },
      core_bracing_and_spine_neutrality: { score: 3, note: 'Same back shape at setup, at the knee and at lockout.' },
      bar_path_and_proximity: { score: 3, note: 'The bar drags the legs the whole way, no loop around the knees.' },
      lockout_execution: { score: 3, note: 'Hips and knees finish together, tall and quiet, no lean back.' },
      eccentric_control_and_descent: { score: 3, note: 'Hips travel back first, the knees only bend once the bar is past them.' },
    },
    {
      rep_index: 2,
      score: 2,
      total: 18,
      max: 24,
      not_assessable_count: 0,
      starting_position: { score: 2, note: 'You reset an inch further from the bar than on rep 1 — the shins are no longer touching.' },
      slack_pull_and_lat_engagement: { score: 1, note: 'No slack pull this time: you go from standing to full effort in one jerk.' },
      leg_drive_activation: { score: 2, note: 'Hips rise ahead of the shoulders off the floor, the torso pitches forward early.' },
      hip_hinge_mechanics: { score: 3, note: 'Hamstrings and glutes still carry the middle of the pull.' },
      core_bracing_and_spine_neutrality: { score: 3, note: 'The brace holds — the lower back stays flat under load.' },
      bar_path_and_proximity: { score: 2, note: 'The bar loops forward around the knees before coming back into the thighs.' },
      lockout_execution: { score: 3, note: 'Clean finish with a real glute squeeze, no hitching.' },
      eccentric_control_and_descent: { score: 2, note: 'Knees bend early on the way down, so the bar travels forward over them.' },
    },
    {
      rep_index: 3,
      score: 2,
      total: 17,
      max: 24,
      not_assessable_count: 0,
      starting_position: { score: 2, note: 'Same drift as rep 2, and the hips start a touch higher.' },
      slack_pull_and_lat_engagement: { score: 1, note: 'Grip and rip again — the shoulders round forward as the bar breaks the floor.' },
      leg_drive_activation: { score: 2, note: 'The hips shoot up first and the last third is pulled with the back.' },
      hip_hinge_mechanics: { score: 3, note: 'The hinge itself is still there, hips and knees extend together past the shins.' },
      core_bracing_and_spine_neutrality: { score: 3, note: 'Still braced: a little upper-back rounding, stable and unchanging.' },
      bar_path_and_proximity: { score: 2, note: 'The bar swings out the furthest of the three reps around knee height.' },
      lockout_execution: { score: 3, note: 'Full extension reached, standing tall with the bar on the thighs.' },
      eccentric_control_and_descent: { score: 1, note: 'You let the bar go on the last rep — it crashes down instead of being lowered.' },
    },
  ],

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
  set_consistency: {
    score: 2,
    feedback:
      'Your first rep is the one to copy — everything is in place. It starts to slip on rep 2: the slack pull disappears, the bar drifts further out, and by rep 3 you drop it instead of lowering it. Reset properly between reps instead of chasing the next one.',
  },
};
