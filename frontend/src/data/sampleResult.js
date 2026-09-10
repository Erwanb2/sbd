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
    "equipment": {
      "etat": "barbell",
      "texte": "A standard barbell with plates on the floor."
    },
    "grip": {
      "etat": "mixed",
      "texte": "One palm forward, one back (mixed grip)."
    },
    "foot_orientation": {
      "etat": "forward",
      "texte": "The toes point roughly forward."
    },
    "mesures": {
      "view": 0.08,
      "visibility": 0.83
    }
  },
  "reps": [
    {
      "index": 1,
      "debut_s": 1.2,
      "fin_s": 5.4,
      "statut": "complete",
      "criteres": {
        "start_position": {
          "libelle": "Start position",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The hips sit between the knees and the shoulders.",
              "note": 3
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
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
              "fait": "The arms hang straight and stay long, elbows locked out, from the setup to the top.",
              "note": 3
            }
          ]
        },
        "slack_and_brace": {
          "libelle": "Slack and brace",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "The arms pull taut and the bar or plates visibly load before anything moves.",
              "note": 3
            },
            {
              "indicateur": "S09",
              "phase": "setup",
              "source": "llm",
              "fait": "A breath is taken at the bottom and held: the midsection stays expanded and rigid through the pull.",
              "note": 3
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
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
              "source": "llm",
              "fait": "Hips and shoulders rise together: the legs are driving the floor away and the torso angle holds.",
              "note": 3
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar against the body",
          "note": 3,
          "statut": "note",
          "faits": [
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
        "finish_position": {
          "libelle": "Finish position",
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
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
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
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3
            }
          ]
        },
        "reset": {
          "libelle": "Reset between reps",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
              "note": 3
            }
          ]
        },
        "structure": {
          "libelle": "Structure under load",
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
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
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
        "start_position": {
          "libelle": "Start position",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The hips sit between the knees and the shoulders.",
              "note": 3
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
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
              "fait": "The arms hang straight and stay long, elbows locked out, from the setup to the top.",
              "note": 3
            }
          ]
        },
        "slack_and_brace": {
          "libelle": "Slack and brace",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "The arms pull taut and the bar or plates visibly load before anything moves.",
              "note": 3
            },
            {
              "indicateur": "S09",
              "phase": "setup",
              "source": "llm",
              "fait": "A breath is taken at the bottom and held: the midsection stays expanded and rigid through the pull.",
              "note": 3
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
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
              "source": "llm",
              "fait": "Hips and shoulders rise together: the legs are driving the floor away and the torso angle holds.",
              "note": 3
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar against the body",
          "note": 3,
          "statut": "note",
          "faits": [
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
        "finish_position": {
          "libelle": "Finish position",
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
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
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
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3
            }
          ]
        },
        "reset": {
          "libelle": "Reset between reps",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
              "note": 3
            }
          ]
        },
        "structure": {
          "libelle": "Structure under load",
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
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
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
        "start_position": {
          "libelle": "Start position",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The hips sit between the knees and the shoulders.",
              "note": 3
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
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
              "fait": "The arms hang straight and stay long, elbows locked out, from the setup to the top.",
              "note": 3
            }
          ]
        },
        "slack_and_brace": {
          "libelle": "Slack and brace",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "Some tension is taken but it is lost as the bar breaks the floor.",
              "note": 2
            },
            {
              "indicateur": "S09",
              "phase": "setup",
              "source": "llm",
              "fait": "A breath is taken at the bottom and held: the midsection stays expanded and rigid through the pull.",
              "note": 3
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
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
              "source": "llm",
              "fait": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
              "note": 1
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar against the body",
          "note": 1,
          "statut": "note",
          "faits": [
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
              "fait": "The bar travels visibly away from the legs.",
              "note": 1
            }
          ]
        },
        "finish_position": {
          "libelle": "Finish position",
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
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
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
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3
            }
          ]
        },
        "reset": {
          "libelle": "Reset between reps",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
              "note": 3
            }
          ]
        },
        "structure": {
          "libelle": "Structure under load",
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
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3
            }
          ]
        }
      },
      "note": 2,
      "note_precise": 2.14,
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
        "start_position": {
          "libelle": "Start position",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The hips sit between the knees and the shoulders.",
              "note": 3
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
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
              "fait": "The arms hang straight and stay long, elbows locked out, from the setup to the top.",
              "note": 3
            }
          ]
        },
        "slack_and_brace": {
          "libelle": "Slack and brace",
          "note": 2,
          "statut": "note",
          "faits": [
            {
              "indicateur": "S07",
              "phase": "setup",
              "source": "llm",
              "fait": "Some tension is taken but it is lost as the bar breaks the floor.",
              "note": 2
            },
            {
              "indicateur": "S09",
              "phase": "setup",
              "source": "llm",
              "fait": "Some air is taken but the midsection gives during the pull, or the breath is let go before lockout.",
              "note": 2
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
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
              "source": "llm",
              "fait": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
              "note": 1
            }
          ]
        },
        "bar_path": {
          "libelle": "Bar against the body",
          "note": 1,
          "statut": "note",
          "faits": [
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
              "fait": "The bar travels visibly away from the legs.",
              "note": 1
            }
          ]
        },
        "finish_position": {
          "libelle": "Finish position",
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
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
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
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3
            }
          ]
        },
        "reset": {
          "libelle": "Reset between reps",
          "note": 3,
          "statut": "note",
          "faits": [
            {
              "indicateur": "E02",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar is lowered under control, the lifter staying with it.",
              "note": 3
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "This is the last rep of the set.",
              "note": null
            }
          ]
        },
        "structure": {
          "libelle": "Structure under load",
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
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
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
        "tiree_s": 2.6,
        "lockout_s": 0.9
      },
      "resume": "Last rep: the back rounds and the bar swings out."
    }
  ],
  "criteres": {
    "start_position": {
      "libelle": "Start position",
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
          "indicateur": "S01",
          "phase": "setup",
          "source": "llm",
          "fait": "The hips sit between the knees and the shoulders.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "S02",
          "phase": "setup",
          "source": "llm",
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
          "fait": "The arms hang straight and stay long, elbows locked out, from the setup to the top.",
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
    "slack_and_brace": {
      "libelle": "Slack and brace",
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
          "indicateur": "S09",
          "phase": "setup",
          "source": "llm",
          "fait": "Some air is taken but the midsection gives during the pull, or the breath is let go before lockout.",
          "note": 2,
          "reps": [
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
          "indicateur": "S09",
          "phase": "setup",
          "source": "llm",
          "fait": "A breath is taken at the bottom and held: the midsection stays expanded and rigid through the pull.",
          "note": 3,
          "reps": [
            1,
            2,
            3
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
        }
      ]
    },
    "leg_drive": {
      "libelle": "Leg drive off the floor",
      "note": 2,
      "poids": 1.5,
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
          "source": "llm",
          "fait": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
          "note": 1,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "L01",
          "phase": "decollage",
          "source": "llm",
          "fait": "Hips and shoulders rise together: the legs are driving the floor away and the torso angle holds.",
          "note": 3,
          "reps": [
            1,
            2
          ]
        }
      ]
    },
    "bar_path": {
      "libelle": "Bar against the body",
      "note": 2,
      "poids": 1.5,
      "notes_par_rep": [
        3,
        3,
        1,
        1
      ],
      "faits": [
        {
          "indicateur": "P03",
          "phase": "tiree",
          "source": "llm",
          "fait": "The bar travels visibly away from the legs.",
          "note": 1,
          "reps": [
            3,
            4
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
        }
      ]
    },
    "finish_position": {
      "libelle": "Finish position",
      "note": 3,
      "poids": 1.0,
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
          "indicateur": "K03",
          "phase": "lockout",
          "source": "llm",
          "fait": "The lifter finishes upright and neutral.",
          "note": 3,
          "reps": [
            1,
            2,
            3,
            4
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
          "indicateur": "K07",
          "phase": "lockout",
          "source": "llm",
          "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
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
    "reset": {
      "libelle": "Reset between reps",
      "note": 3,
      "poids": 0.5,
      "notes_par_rep": [
        3,
        3,
        3,
        3
      ],
      "faits": [
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
        },
        {
          "indicateur": "E03",
          "phase": "descente",
          "source": "llm",
          "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
          "note": 3,
          "reps": [
            1,
            2,
            3
          ]
        },
        {
          "indicateur": "E03",
          "phase": "descente",
          "source": "llm",
          "fait": "This is the last rep of the set.",
          "note": null,
          "reps": [
            4
          ]
        }
      ]
    },
    "structure": {
      "libelle": "Structure under load",
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
          "indicateur": "P05",
          "phase": "tiree",
          "source": "llm",
          "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
          "note": null,
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
  "mecaniques": [
    "start_position",
    "slack_and_brace",
    "leg_drive",
    "bar_path",
    "finish_position",
    "reset"
  ],
  "structure": {
    "etat": "stop",
    "note": 1,
    "texte": "Stop the set: something is giving way under the load.",
    "defauts": [
      {
        "indicateur": "P04",
        "nom": "back_under_load",
        "critere": "structure",
        "constat": "The lower back rounds hard and keeps rounding as the bar rises.",
        "a_essayer": "Stop the set. Rebuild this at a load where the back holds its shape.",
        "etat": "collapses",
        "note": 1,
        "reps": [
          3,
          4
        ]
      }
    ]
  },
  "epingle": {
    "indicateur": "S07",
    "nom": "slack_pull",
    "critere": "slack_and_brace",
    "constat": "Some tension is taken but it is lost as the bar breaks the floor.",
    "a_essayer": "Pull the slack out until you feel the bar load, then push the floor away.",
    "etat": "partial",
    "note": 2,
    "reps": [
      3,
      4
    ],
    "consequences": [
      {
        "indicateur": "L01",
        "nom": "hip_vs_shoulder_rise",
        "critere": "leg_drive",
        "constat": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
        "a_essayer": "Push the floor away with your legs and hold your chest angle through the first third of the pull.",
        "etat": "hips_shoot_up",
        "note": 1,
        "reps": [
          3,
          4
        ]
      },
      {
        "indicateur": "P03",
        "nom": "bar_leg_contact",
        "critere": "bar_path",
        "constat": "The bar travels visibly away from the legs.",
        "a_essayer": "Keep the bar in contact with the legs the whole way up.",
        "etat": "away_from_legs",
        "note": 1,
        "reps": [
          3,
          4
        ]
      },
      {
        "indicateur": "P02",
        "nom": "past_the_knees",
        "critere": "bar_path",
        "constat": "The bar loops forward around the knees before coming back in.",
        "a_essayer": "Let the hips come through as the bar reaches the knees so it passes close.",
        "etat": "loops",
        "note": 2,
        "reps": [
          3,
          4
        ]
      }
    ],
    "autres": []
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
      "indicateur": "S07",
      "nom": "slack_pull",
      "critere": "slack_and_brace",
      "constat": "Some tension is taken but it is lost as the bar breaks the floor.",
      "a_essayer": "Pull the slack out until you feel the bar load, then push the floor away.",
      "etat": "partial",
      "note": 2,
      "reps": [
        3,
        4
      ],
      "consequences": [
        {
          "indicateur": "L01",
          "nom": "hip_vs_shoulder_rise",
          "critere": "leg_drive",
          "constat": "The hips shoot up while the shoulders barely move: the lift turns into a stiff-legged pull finished by the back.",
          "a_essayer": "Push the floor away with your legs and hold your chest angle through the first third of the pull.",
          "etat": "hips_shoot_up",
          "note": 1,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "P03",
          "nom": "bar_leg_contact",
          "critere": "bar_path",
          "constat": "The bar travels visibly away from the legs.",
          "a_essayer": "Keep the bar in contact with the legs the whole way up.",
          "etat": "away_from_legs",
          "note": 1,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "P02",
          "nom": "past_the_knees",
          "critere": "bar_path",
          "constat": "The bar loops forward around the knees before coming back in.",
          "a_essayer": "Let the hips come through as the bar reaches the knees so it passes close.",
          "etat": "loops",
          "note": 2,
          "reps": [
            3,
            4
          ]
        }
      ],
      "autres": []
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
