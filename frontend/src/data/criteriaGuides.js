// Le contenu PÉDAGOGIQUE des six mécaniques, indexé par la clé de critère du
// backend (`indicators.CRITERES`).
//
// C'est la moitié du travail qu'un critère doit faire. Un critère a deux métiers :
// nommer une mécanique — pour que la chose existe dans la tête du lifter, avec un nom,
// un repère et un exercice — et désigner quoi corriger. Le second est porté par
// l'épingle, côté backend. Le premier est porté par ce fichier.
//
// Ce contenu ne change JAMAIS d'une vidéo à l'autre : c'est la carte, et c'est ce qui
// la rend apprenable. Au troisième upload, le lifter connaît les six noms. Le rapport,
// lui, plante une épingle sur cette carte.
//
// Trois champs, et chacun répond à une question différente :
//   what  — à quoi ça ressemble quand c'est juste (ce que le lifter doit voir en se
//           rematant : s'il ne peut pas le voir, il ne le corrigera pas)
//   cue   — le repère à se dire pendant la série
//   drill — l'exercice pour le travailler à charge légère
//
// `bad`/`good` (images) restent optionnels et s'affichent en plus quand ils existent.
import badLegDrive from '../images/leg-drive/bad-leg-drive.png';
import goodLegDrive from '../images/leg-drive/good-leg-drive.png';

export const criteriaGuides = {
  start_position: {
    what: "Hips between your knees and your shoulders, shoulders just ahead of the bar, "
        + "bar over your mid-foot and against your shins, arms hanging long.",
    cue: "Shoulders just in front of the bar, not on top of it and not behind it.",
    drill: "Set up, hold the position for three seconds without pulling, then stand up "
         + "and do it again. The start is a position you learn by holding it.",
  },
  slack_and_brace: {
    what: "A breath taken and held at the bottom, then the arms pulling taut until the bar "
        + "loads — the plates click — and only then the lift.",
    cue: "Take the air, take the slack, then push the floor away.",
    drill: "At a light load, pull the slack out and hold it for two seconds before every "
         + "single rep, until the click happens on its own.",
  },
  leg_drive: {
    what: "Hips and shoulders rising together over the first third of the pull, your chest "
        + "angle unchanged as the bar breaks the floor.",
    // Le repère porte sur ce qu'on PEUT faire. « Ne laisse pas tes hanches monter » est
    // inapplicable : la montée des hanches est ce qui rend la barre soulevable depuis
    // une mauvaise position. Si tes hanches décollent, la correction est au départ.
    cue: "Push the floor away with your legs rather than pulling with your back.",
    drill: "Paused deadlifts, two seconds just below the knee. You cannot hold that pause "
         + "if your hips have already shot up.",
    bad: {
      title: "Common Mistake (Poor Leg Drive)",
      image: badLegDrive,
      description: "The lifter straightens their legs too early. The hips shoot up before "
                 + "the bar even leaves the floor.",
      problem: "The legs are already straight, so they can no longer help. The whole load "
             + "shifts to the lower back and hamstrings.",
    },
    good: {
      title: "Ideal Posture (Proper Leg Drive)",
      image: goodLegDrive,
      description: "Hips lower, knees bent, chest proud. Hips and shoulders will rise "
                 + "together.",
      tip: "Imagine pressing the floor away forcefully with your feet while driving your "
         + "chest up.",
    },
  },
  bar_path: {
    what: "The bar dragging up your shins and thighs, staying against you — or within a "
        + "few centimetres — the whole way up.",
    cue: "Pull your shoulder blades down and drag the bar up your legs.",
    drill: "Deadlift in long socks at a load you can control. If the bar leaves you, "
         + "you will feel it before you see it.",
  },
  finish_position: {
    what: "Standing tall in one continuous motion: hips through, knees locked, glutes "
        + "squeezed, no lean back and no ratcheting the bar up the thighs.",
    cue: "Finish by squeezing your glutes, not by leaning back.",
    drill: "Hip thrusts or glute bridges: the top of the deadlift is a hip extension, and "
         + "it is easier to learn without the bar in your hands.",
  },
  reset: {
    what: "Every rep rebuilt from the same start position, and the bar accompanied back "
        + "to the floor rather than dropped.",
    cue: "Put it down, breathe, rebuild. Every rep starts from scratch.",
    drill: "Singles with a full reset between each, until the setup is identical on rep 5 "
         + "and on rep 1.",
  },
  // L'axe structure n'est pas une mécanique — on ne l'exécute pas, il lâche — mais il
  // a une carte dans le dépliant du bandeau, avec le même contenu.
  structure: {
    what: "A back that keeps the SAME shape from the floor to lockout, knees tracking out "
        + "over your toes, both sides of the bar rising together.",
    // Ce n'est pas un repère de geste, et c'est délibéré : la lombaire qui prend est le
    // prix payé pour des hanches hautes sans leg drive, jamais une chose à corriger
    // directement. Le danger fixe l'urgence, la cause fixe l'action.
    cue: "Whatever shape your back starts in, it has to end in. If it changes, the set is over.",
    drill: "Drop the load until the shape holds for every rep, and build back from there.",
  },
};
