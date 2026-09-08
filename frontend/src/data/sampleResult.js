// Analyse "sample" figée, affichée dans la démo de la page d'accueil.
//
// GÉNÉRÉE par le backend, pas écrite à la main : `rules.evalue` a tourné sur des
// mesures de pose plausibles et des observations fabriquées, et sa sortie est
// recopiée telle quelle. C'est la seule façon que la démo reste cohérente avec le
// barème — les notes, la note sur 20, la tenue du set, les conseils et le persona
// sont tous des calculs, et les recopier à la main les ferait diverger au premier
// changement de seuil.
//
// Pour la régénérer, depuis backend/ :
//   uv run python eval/sample_page.py
// puis recoller la sortie sous l'export. Aucun appel à Gemini n'est nécessaire.
export const sampleResult =
{
  "variante": "conventional",
  "contexte": {
    "variante": {
      "etat": "conventional",
      "texte": "Hands outside the legs, hip-width stance."
    },
    "vue_camera": {
      "etat": "profil",
      "texte": "Filmed from the side: bar path and joint angles are readable."
    },
    "qualite_pose": {
      "etat": "bonne",
      "texte": "Landmarks are stable and visible throughout."
    },
    "materiel": {
      "etat": "barre_libre",
      "texte": "A standard barbell with plates on the floor."
    },
    "prise": {
      "etat": "mixte",
      "texte": "One palm forward, one back (mixed grip)."
    },
    "orientation_pieds": {
      "etat": "droits",
      "texte": "The toes point roughly forward."
    },
    "mesures": {
      "vue": 0.08,
      "visibilite": 0.83
    }
  },
  "reps": [
    {
      "index": 1,
      "debut_s": 1.2,
      "fin_s": 5.4,
      "statut": "complete",
      "criteres": {
        "setup": {
          "libelle": "Setup and tension",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "pose",
              "fait": "The hips sit between the knees and the shoulders.",
              "note": 3
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "pose",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The bar sits over the middle of the foot, close to the shins.",
              "note": 3
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arms hang straight, elbows locked out.",
              "note": 3
            },
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "The arms pull taut and the bar or plates visibly load before anything moves.",
              "note": 3
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The arms stay long throughout the pull.",
              "note": 3
            }
          ]
        },
        "leg_drive": {
          "libelle": "Leg drive off the floor",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "L01",
              "phase": "decollage",
              "source": "pose",
              "fait": "Hips and shoulders rise together: the legs are driving the floor away and the torso angle holds.",
              "note": 3
            },
            {
              "indicateur": "L02",
              "phase": "decollage",
              "source": "pose",
              "fait": "The torso angle holds as the bar leaves the floor.",
              "note": 3
            }
          ]
        },
        "spine": {
          "libelle": "Spine under load",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S05",
              "phase": "setup",
              "source": "llm",
              "fait": "The back is flat and set before the bar moves.",
              "note": 3
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The back holds the same shape at the floor, at knee height and at lockout: no flexion added under load.",
              "note": 3
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar path and proximity",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P01",
              "phase": "tiree",
              "source": "pose",
              "fait": "The hands stay over the same point through the pull.",
              "note": 3
            },
            {
              "indicateur": "P02",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar passes the knees close to the legs, in one line.",
              "note": 3
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "The bar stays against or within a few centimetres of the legs the whole way up.",
              "note": 3
            }
          ]
        },
        "lockout": {
          "libelle": "Lockout",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P08",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar rises in one continuous motion.",
              "note": 3
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3
            },
            {
              "indicateur": "K01",
              "phase": "lockout",
              "source": "pose",
              "fait": "The hips reach full extension, the lifter standing tall.",
              "note": 3
            },
            {
              "indicateur": "K02",
              "phase": "lockout",
              "source": "pose",
              "fait": "The knees lock out fully.",
              "note": 3
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "pose",
              "fait": "The lifter finishes upright and neutral.",
              "note": 3
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3
            },
            {
              "indicateur": "K05",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lifter finishes balanced over the feet.",
              "note": 3
            }
          ]
        },
        "descent": {
          "libelle": "Descent",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E01",
              "phase": "descente",
              "source": "pose",
              "fait": "The hips travel back first, the knees bending once the bar has passed them.",
              "note": 3
            },
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            }
          ]
        }
      },
      "note": 3,
      "note_precise": 3.0,
      "sur": 3,
      "non_evaluables": 0,
      "temps": {
        "tiree_s": 1.35,
        "lockout_s": 0.2
      },
      "resume": "Textbook first pull, everything stacked."
    },
    {
      "index": 2,
      "debut_s": 6.2,
      "fin_s": 10.4,
      "statut": "complete",
      "criteres": {
        "setup": {
          "libelle": "Setup and tension",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "pose",
              "fait": "The hips sit between the knees and the shoulders.",
              "note": 3
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "pose",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The bar sits over the middle of the foot, close to the shins.",
              "note": 3
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arms hang straight, elbows locked out.",
              "note": 3
            },
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "The arms pull taut and the bar or plates visibly load before anything moves.",
              "note": 3
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The arms stay long throughout the pull.",
              "note": 3
            }
          ]
        },
        "leg_drive": {
          "libelle": "Leg drive off the floor",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "L01",
              "phase": "decollage",
              "source": "pose",
              "fait": "Hips and shoulders rise together: the legs are driving the floor away and the torso angle holds.",
              "note": 3
            },
            {
              "indicateur": "L02",
              "phase": "decollage",
              "source": "pose",
              "fait": "The torso angle holds as the bar leaves the floor.",
              "note": 3
            }
          ]
        },
        "spine": {
          "libelle": "Spine under load",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S05",
              "phase": "setup",
              "source": "llm",
              "fait": "The back is flat and set before the bar moves.",
              "note": 3
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The back holds the same shape at the floor, at knee height and at lockout: no flexion added under load.",
              "note": 3
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar path and proximity",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P01",
              "phase": "tiree",
              "source": "pose",
              "fait": "The hands stay over the same point through the pull.",
              "note": 3
            },
            {
              "indicateur": "P02",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar passes the knees close to the legs, in one line.",
              "note": 3
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "The bar stays against or within a few centimetres of the legs the whole way up.",
              "note": 3
            }
          ]
        },
        "lockout": {
          "libelle": "Lockout",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P08",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar rises in one continuous motion.",
              "note": 3
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3
            },
            {
              "indicateur": "K01",
              "phase": "lockout",
              "source": "pose",
              "fait": "The hips reach full extension, the lifter standing tall.",
              "note": 3
            },
            {
              "indicateur": "K02",
              "phase": "lockout",
              "source": "pose",
              "fait": "The knees lock out fully.",
              "note": 3
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "pose",
              "fait": "The lifter finishes upright and neutral.",
              "note": 3
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3
            },
            {
              "indicateur": "K05",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lifter finishes balanced over the feet.",
              "note": 3
            }
          ]
        },
        "descent": {
          "libelle": "Descent",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E01",
              "phase": "descente",
              "source": "pose",
              "fait": "The hips travel back first, the knees bending once the bar has passed them.",
              "note": 3
            },
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            }
          ]
        }
      },
      "note": 3,
      "note_precise": 3.0,
      "sur": 3,
      "non_evaluables": 0,
      "temps": {
        "tiree_s": 1.55,
        "lockout_s": 0.3
      },
      "resume": "Still tight, the bar drifts a touch more."
    },
    {
      "index": 3,
      "debut_s": 11.2,
      "fin_s": 15.4,
      "statut": "complete",
      "criteres": {
        "setup": {
          "libelle": "Setup and tension",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "pose",
              "fait": "The hips sit between the knees and the shoulders.",
              "note": 3
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "pose",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The bar sits over the middle of the foot, close to the shins.",
              "note": 3
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arms hang straight, elbows locked out.",
              "note": 3
            },
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "Some tension is taken but it is lost as the bar breaks the floor.",
              "note": 2
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The arms stay long throughout the pull.",
              "note": 3
            }
          ]
        },
        "leg_drive": {
          "libelle": "Leg drive off the floor",
          "note": 1,
          "statut": "note",
          "faits": [
            {
              "indicateur": "L01",
              "phase": "decollage",
              "source": "pose",
              "fait": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
              "note": 1
            },
            {
              "indicateur": "L02",
              "phase": "decollage",
              "source": "pose",
              "fait": "The torso pitches further forward at liftoff: the hips win the race and the back takes the load.",
              "note": 2
            }
          ]
        },
        "spine": {
          "libelle": "Spine under load",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S05",
              "phase": "setup",
              "source": "llm",
              "fait": "The back is flat and set before the bar moves.",
              "note": 3
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "Flexion appears during the pull that was not there at the start.",
              "note": 2
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar path and proximity",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P01",
              "phase": "tiree",
              "source": "pose",
              "fait": "The hands drift forward and come back.",
              "note": 2
            },
            {
              "indicateur": "P02",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar loops forward around the knees before coming back in.",
              "note": 2
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "Contact is briefly lost, then the bar comes back to the legs.",
              "note": 3
            }
          ]
        },
        "lockout": {
          "libelle": "Lockout",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P08",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar rises in one continuous motion.",
              "note": 3
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3
            },
            {
              "indicateur": "K01",
              "phase": "lockout",
              "source": "pose",
              "fait": "The hips reach full extension, the lifter standing tall.",
              "note": 3
            },
            {
              "indicateur": "K02",
              "phase": "lockout",
              "source": "pose",
              "fait": "The knees lock out fully.",
              "note": 3
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "pose",
              "fait": "The lifter finishes upright and neutral.",
              "note": 3
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3
            },
            {
              "indicateur": "K05",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lifter finishes balanced over the feet.",
              "note": 3
            }
          ]
        },
        "descent": {
          "libelle": "Descent",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E01",
              "phase": "descente",
              "source": "pose",
              "fait": "The knees bend before the bar has passed them, pushing the bar forward or into the kneecaps.",
              "note": 2
            },
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            }
          ]
        }
      },
      "note": 2,
      "note_precise": 2.0,
      "sur": 3,
      "non_evaluables": 0,
      "temps": {
        "tiree_s": 2.1,
        "lockout_s": 0.6
      },
      "resume": "The hips beat the shoulders out of the floor."
    },
    {
      "index": 4,
      "debut_s": 16.2,
      "fin_s": 20.4,
      "statut": "complete",
      "criteres": {
        "setup": {
          "libelle": "Setup and tension",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "pose",
              "fait": "The hips start very high: the pull begins as a stiff-legged lift with the shoulders far in front.",
              "note": 2
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "pose",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The bar sits over the middle of the foot, close to the shins.",
              "note": 3
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arms hang straight, elbows locked out.",
              "note": 3
            },
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "Some tension is taken but it is lost as the bar breaks the floor.",
              "note": 2
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The arms stay long throughout the pull.",
              "note": 3
            }
          ]
        },
        "leg_drive": {
          "libelle": "Leg drive off the floor",
          "note": 1,
          "statut": "note",
          "faits": [
            {
              "indicateur": "L01",
              "phase": "decollage",
              "source": "pose",
              "fait": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
              "note": 1
            },
            {
              "indicateur": "L02",
              "phase": "decollage",
              "source": "pose",
              "fait": "The torso pitches further forward at liftoff: the hips win the race and the back takes the load.",
              "note": 2
            }
          ]
        },
        "spine": {
          "libelle": "Spine under load",
          "note": 1,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S05",
              "phase": "setup",
              "source": "llm",
              "fait": "The back is flat and set before the bar moves.",
              "note": 3
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The lower back rounds hard and keeps rounding as the bar rises.",
              "note": 1
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar path and proximity",
          "note": 1,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P01",
              "phase": "tiree",
              "source": "pose",
              "fait": "The hands drift well away from the body, lengthening the lever on the lower back.",
              "note": 1
            },
            {
              "indicateur": "P02",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar loops forward around the knees before coming back in.",
              "note": 2
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "Contact is briefly lost, then the bar comes back to the legs.",
              "note": 3
            }
          ]
        },
        "lockout": {
          "libelle": "Lockout",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "P08",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "The bar rises in one continuous motion.",
              "note": 3
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3
            },
            {
              "indicateur": "K01",
              "phase": "lockout",
              "source": "pose",
              "fait": "The hips reach full extension, the lifter standing tall.",
              "note": 3
            },
            {
              "indicateur": "K02",
              "phase": "lockout",
              "source": "pose",
              "fait": "The knees lock out fully.",
              "note": 3
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "pose",
              "fait": "A slight lean back at the top.",
              "note": 3
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3
            },
            {
              "indicateur": "K05",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lifter finishes balanced over the feet.",
              "note": 3
            }
          ]
        },
        "descent": {
          "libelle": "Descent",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E01",
              "phase": "descente",
              "source": "pose",
              "fait": "The knees bend before the bar has passed them, pushing the bar forward or into the kneecaps.",
              "note": 2
            },
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            }
          ]
        }
      },
      "note": 2,
      "note_precise": 1.67,
      "sur": 3,
      "non_evaluables": 0,
      "temps": {
        "tiree_s": 2.6,
        "lockout_s": 0.9
      },
      "resume": "Last rep: the back rounds and the bar swings out."
    }
  ],
  "criteres": {
    "setup": {
      "libelle": "Setup and tension",
      "note": 2,
      "poids": 1.0,
      "notes_par_rep": [
        3,
        3,
        2,
        2
      ],
      "faits": [
        {
          "indicateur": "S07",
          "phase": "setup",
          "source": "llm",
          "fait": "Some tension is taken but it is lost as the bar breaks the floor.",
          "note": 2,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "S01",
          "phase": "setup",
          "source": "pose",
          "fait": "The hips start very high: the pull begins as a stiff-legged lift with the shoulders far in front.",
          "note": 2,
          "reps": [
            4
          ]
        },
        {
          "indicateur": "S01",
          "phase": "setup",
          "source": "pose",
          "fait": "The hips sit between the knees and the shoulders.",
          "note": 3,
          "reps": [
            1,
            2,
            3
          ]
        },
        {
          "indicateur": "S02",
          "phase": "setup",
          "source": "pose",
          "fait": "The shoulders are stacked over or just ahead of the bar.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "S04",
          "phase": "setup",
          "source": "a_tester",
          "fait": "The bar sits over the middle of the foot, close to the shins.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "S06",
          "phase": "setup",
          "source": "a_tester",
          "fait": "The arms hang straight, elbows locked out.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "S07",
          "phase": "setup",
          "source": "llm",
          "fait": "The arms pull taut and the bar or plates visibly load before anything moves.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        },
        {
          "indicateur": "L03",
          "phase": "decollage",
          "source": "a_tester",
          "fait": "The bar accelerates smoothly out of the floor.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "P10",
          "phase": "tiree",
          "source": "a_tester",
          "fait": "The arms stay long throughout the pull.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        }
      ]
    },
    "leg_drive": {
      "libelle": "Leg drive off the floor",
      "note": 2,
      "poids": 1.0,
      "notes_par_rep": [
        3,
        3,
        1,
        1
      ],
      "faits": [
        {
          "indicateur": "L01",
          "phase": "decollage",
          "source": "pose",
          "fait": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
          "note": 1,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "L02",
          "phase": "decollage",
          "source": "pose",
          "fait": "The torso pitches further forward at liftoff: the hips win the race and the back takes the load.",
          "note": 2,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "L01",
          "phase": "decollage",
          "source": "pose",
          "fait": "Hips and shoulders rise together: the legs are driving the floor away and the torso angle holds.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        },
        {
          "indicateur": "L02",
          "phase": "decollage",
          "source": "pose",
          "fait": "The torso angle holds as the bar leaves the floor.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        }
      ]
    },
    "spine": {
      "libelle": "Spine under load",
      "note": 2,
      "poids": 2.0,
      "notes_par_rep": [
        3,
        3,
        2,
        1
      ],
      "faits": [
        {
          "indicateur": "P04",
          "phase": "tiree",
          "source": "llm",
          "fait": "The lower back rounds hard and keeps rounding as the bar rises.",
          "note": 1,
          "reps": [
            4
          ]
        },
        {
          "indicateur": "P04",
          "phase": "tiree",
          "source": "llm",
          "fait": "Flexion appears during the pull that was not there at the start.",
          "note": 2,
          "reps": [
            3
          ]
        },
        {
          "indicateur": "S05",
          "phase": "setup",
          "source": "llm",
          "fait": "The back is flat and set before the bar moves.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "P04",
          "phase": "tiree",
          "source": "llm",
          "fait": "The back holds the same shape at the floor, at knee height and at lockout: no flexion added under load.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        }
      ]
    },
    "bar_path": {
      "libelle": "Bar path and proximity",
      "note": 2,
      "poids": 1.0,
      "notes_par_rep": [
        3,
        3,
        2,
        1
      ],
      "faits": [
        {
          "indicateur": "P01",
          "phase": "tiree",
          "source": "pose",
          "fait": "The hands drift well away from the body, lengthening the lever on the lower back.",
          "note": 1,
          "reps": [
            4
          ]
        },
        {
          "indicateur": "P01",
          "phase": "tiree",
          "source": "pose",
          "fait": "The hands drift forward and come back.",
          "note": 2,
          "reps": [
            3
          ]
        },
        {
          "indicateur": "P02",
          "phase": "tiree",
          "source": "a_tester",
          "fait": "The bar loops forward around the knees before coming back in.",
          "note": 2,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "P01",
          "phase": "tiree",
          "source": "pose",
          "fait": "The hands stay over the same point through the pull.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        },
        {
          "indicateur": "P02",
          "phase": "tiree",
          "source": "a_tester",
          "fait": "The bar passes the knees close to the legs, in one line.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        },
        {
          "indicateur": "P03",
          "phase": "tiree",
          "source": "llm",
          "fait": "The bar stays against or within a few centimetres of the legs the whole way up.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        },
        {
          "indicateur": "P03",
          "phase": "tiree",
          "source": "llm",
          "fait": "Contact is briefly lost, then the bar comes back to the legs.",
          "note": 3,
          "reps": [
            3,
            4
          ]
        }
      ]
    },
    "lockout": {
      "libelle": "Lockout",
      "note": 3,
      "poids": 1.5,
      "notes_par_rep": [
        3,
        3,
        3,
        3
      ],
      "faits": [
        {
          "indicateur": "P08",
          "phase": "tiree",
          "source": "a_tester",
          "fait": "The bar rises in one continuous motion.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "P09",
          "phase": "tiree",
          "source": "a_tester",
          "fait": "Both sides rise together.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "K01",
          "phase": "lockout",
          "source": "pose",
          "fait": "The hips reach full extension, the lifter standing tall.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "K02",
          "phase": "lockout",
          "source": "pose",
          "fait": "The knees lock out fully.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "K03",
          "phase": "lockout",
          "source": "pose",
          "fait": "The lifter finishes upright and neutral.",
          "note": 3,
          "reps": [
            1,
            2,
            3
          ]
        },
        {
          "indicateur": "K04",
          "phase": "lockout",
          "source": "a_tester",
          "fait": "The lift finishes with hip extension alone.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "K05",
          "phase": "lockout",
          "source": "a_tester",
          "fait": "The lifter finishes balanced over the feet.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "K03",
          "phase": "lockout",
          "source": "pose",
          "fait": "A slight lean back at the top.",
          "note": 3,
          "reps": [
            4
          ]
        }
      ]
    },
    "descent": {
      "libelle": "Descent",
      "note": 2,
      "poids": 1.0,
      "notes_par_rep": [
        3,
        3,
        2,
        2
      ],
      "faits": [
        {
          "indicateur": "E01",
          "phase": "descente",
          "source": "pose",
          "fait": "The knees bend before the bar has passed them, pushing the bar forward or into the kneecaps.",
          "note": 2,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "E01",
          "phase": "descente",
          "source": "pose",
          "fait": "The hips travel back first, the knees bending once the bar has passed them.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        },
        {
          "indicateur": "E02",
          "phase": "descente",
          "source": "llm",
          "fait": "The bar is lowered under control, the lifter staying with it.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        }
      ]
    }
  },
  "note_sur_20": 16,
  "nb_reps": 4,
  "segments_ecartes": [],
  "tenue_du_set": {
    "etat": "derive",
    "texte": "The technique drifts over the set. It starts changing at rep 3.",
    "ecart_note": -1,
    "ralentissement": 1.93,
    "decroche_a": 3
  },
  "conseils": [
    {
      "indicateur": "P04",
      "critere": "spine",
      "constat": "The lower back rounds hard and keeps rounding as the bar rises.",
      "a_essayer": "Stop the set. Rebuild this at a load where the back holds its shape.",
      "note": 1,
      "reps": [
        3,
        4
      ]
    },
    {
      "indicateur": "L01",
      "critere": "leg_drive",
      "constat": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
      "a_essayer": "Push the floor away and hold your chest angle through the first third of the pull.",
      "note": 1,
      "reps": [
        3,
        4
      ]
    }
  ],
  "persona": {
    "nom": "The Fishing Rod",
    "fait": "The lower back rounds hard and keeps rounding as the bar rises.",
    "rep": 4,
    "indicateur": "P04"
  },
  "modele": "gemini-3.5-flash"
}
;
