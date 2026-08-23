// Tu peux importer tes images ici !
import badLegDrive from '../images/bad-leg-drive.png';
import goodLegDrive from '../images/good-leg-drive.png';
// Importe tes autres images pour le squat, bench, etc.

export const criteriaGuides = {
  leg_drive_activation: {
    bad: {
      title: "Common Mistake (Poor Leg Drive)",
      image: badLegDrive,
      description: "In this image, the lifter straightens their legs too early. As a result, the hips shoot up before the bar even leaves the floor.",
      problem: "Since the legs are already straight, they can no longer assist in lifting the weight. All the load violently shifts to the lower back and hamstrings."
    },
    good: {
      title: "Ideal Posture (Proper Leg Drive)",
      image: goodLegDrive,
      description: "Here, the posture is corrected. The hips are lower, knees are bent, and the chest is proud.",
      tip: "Imagine pressing the floor away forcefully with your feet while driving your chest up."
    }
  },
  hip_hinge_mechanics: {
    // bad: { ... }, good: { ... }
  },
  // Tu pourras ajouter la suite ici sans jamais polluer ton App.jsx
};