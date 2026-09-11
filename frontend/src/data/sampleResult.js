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
              "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3,
              "visible": true
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
              "fait": "Both gain height at the same pace: the angle of the back is the same on the two frames.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "The bar stays against or within a few centimetres of the legs the whole way up.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The lifter finishes upright and neutral.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
              "note": 3,
              "visible": true
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
              "fait": "The lower back keeps its natural inward curve at the setup.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The upper back is rounded before the bar moves.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The lower back keeps the same shape from the floor to lockout.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "llm",
              "fait": "The upper back keeps the same shape from the floor to lockout.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null,
              "visible": false
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3,
              "visible": true
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
        "lockout_s": 0.2,
        "decollage_s": null
      },
      "resume": "Textbook first pull, everything stacked.",
      "observations": {
        "lumbar_at_setup": "The lower back keeps its inward curve at the setup.",
        "thoracic_at_setup": "The upper back is rounded and already set before the bar moves.",
        "hip_vs_shoulder_rise": "Hips and shoulders leave the floor at the same rate.",
        "lumbar_under_load": "The lower back holds its shape to lockout."
      }
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
              "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3,
              "visible": true
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
              "fait": "Both gain height at the same pace: the angle of the back is the same on the two frames.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "The bar stays against or within a few centimetres of the legs the whole way up.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The lifter finishes upright and neutral.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
              "note": 3,
              "visible": true
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
              "fait": "The lower back keeps its natural inward curve at the setup.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The upper back is rounded before the bar moves.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The lower back keeps the same shape from the floor to lockout.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "llm",
              "fait": "The upper back keeps the same shape from the floor to lockout.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null,
              "visible": false
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3,
              "visible": true
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
        "lockout_s": 0.3,
        "decollage_s": null
      },
      "resume": "Still tight, the bar drifts a touch more.",
      "observations": {
        "lumbar_at_setup": "The lower back keeps its inward curve at the setup.",
        "thoracic_at_setup": "The upper back is rounded and already set before the bar moves.",
        "hip_vs_shoulder_rise": "Hips and shoulders leave the floor at the same rate.",
        "lumbar_under_load": "The lower back holds its shape to lockout."
      }
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
              "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
              "note": 3,
              "visible": true
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
              "note": 2,
              "visible": true
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3,
              "visible": true
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
              "fait": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees.",
              "note": 1,
              "visible": true
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
              "note": 2,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "The bar travels visibly away from the legs.",
              "note": 1,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The lifter finishes upright and neutral.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
              "note": 3,
              "visible": true
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
              "fait": "The lower back keeps its natural inward curve at the setup.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The upper back is rounded before the bar moves.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The lower back rounds further during the pull than it was at the start.",
              "note": 2,
              "visible": true
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "llm",
              "fait": "The upper back keeps the same shape from the floor to lockout.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null,
              "visible": false
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3,
              "visible": true
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
        "lockout_s": 0.6,
        "decollage_s": null
      },
      "resume": "The hips beat the shoulders out of the floor.",
      "observations": {
        "lumbar_at_setup": "The lower back keeps its inward curve at the setup.",
        "thoracic_at_setup": "The upper back is rounded and already set before the bar moves.",
        "hip_vs_shoulder_rise": "The hips rise first; the torso stays inclined past the knees.",
        "lumbar_under_load": "The lower back rounds further as the bar passes the knees."
      }
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
              "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The shoulders are stacked over or just ahead of the bar.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
              "note": 3,
              "visible": true
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
              "note": 2,
              "visible": true
            },
            {
              "indicateur": "L03",
              "phase": "decollage",
              "source": "a_tester",
              "fait": "The bar accelerates smoothly out of the floor.",
              "note": 3,
              "visible": true
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
              "fait": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees.",
              "note": 1,
              "visible": true
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
              "note": 2,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "The bar travels visibly away from the legs.",
              "note": 1,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The lifter finishes upright and neutral.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The lift finishes with hip extension alone.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
              "note": 3,
              "visible": true
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
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "This is the last rep of the set.",
              "note": null,
              "visible": true
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
              "fait": "The lower back keeps its natural inward curve at the setup.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The upper back is rounded before the bar moves.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The lower back rounds hard and keeps rounding as the bar rises.",
              "note": 1,
              "visible": true
            },
            {
              "indicateur": "P10",
              "phase": "tiree",
              "source": "llm",
              "fait": "The upper back rounds further during the pull than it was at the start.",
              "note": 2,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
              "note": null,
              "visible": false
            },
            {
              "indicateur": "P09",
              "phase": "tiree",
              "source": "a_tester",
              "fait": "Both sides rise together.",
              "note": 3,
              "visible": true
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
        "lockout_s": 0.9,
        "decollage_s": null
      },
      "resume": "Last rep: the back rounds and the bar swings out.",
      "observations": {
        "lumbar_at_setup": "The lower back keeps its inward curve at the setup.",
        "thoracic_at_setup": "The upper back is rounded and already set before the bar moves.",
        "hip_vs_shoulder_rise": "The hips rise first; the torso stays inclined past the knees.",
        "lumbar_under_load": "The lower back rounds further as the bar passes the knees."
      }
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
          "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
          "note": 3,
          "visible": true,
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
          "visible": true,
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
          "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
          "note": 3,
          "visible": true,
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
          "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
          "note": 3,
          "visible": true,
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
          "visible": true,
          "reps": [
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
          "visible": true,
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
          "visible": true,
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
          "fait": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees.",
          "note": 1,
          "visible": true,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "L01",
          "phase": "decollage",
          "source": "llm",
          "fait": "Both gain height at the same pace: the angle of the back is the same on the two frames.",
          "note": 3,
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
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
          "visible": true,
          "reps": [
            4
          ]
        },
        {
          "indicateur": "P04",
          "phase": "tiree",
          "source": "llm",
          "fait": "The lower back rounds further during the pull than it was at the start.",
          "note": 2,
          "visible": true,
          "reps": [
            3
          ]
        },
        {
          "indicateur": "P10",
          "phase": "tiree",
          "source": "llm",
          "fait": "The upper back rounds further during the pull than it was at the start.",
          "note": 2,
          "visible": true,
          "reps": [
            4
          ]
        },
        {
          "indicateur": "S05",
          "phase": "setup",
          "source": "llm",
          "fait": "The lower back keeps its natural inward curve at the setup.",
          "note": 3,
          "visible": true,
          "reps": [
            1,
            2,
            3,
            4
          ]
        },
        {
          "indicateur": "S10",
          "phase": "setup",
          "source": "llm",
          "fait": "The upper back is rounded before the bar moves.",
          "note": 3,
          "visible": true,
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
          "visible": true,
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
          "fait": "The lower back keeps the same shape from the floor to lockout.",
          "note": null,
          "visible": true,
          "reps": [
            1,
            2
          ]
        },
        {
          "indicateur": "P10",
          "phase": "tiree",
          "source": "llm",
          "fait": "The upper back keeps the same shape from the floor to lockout.",
          "note": null,
          "visible": true,
          "reps": [
            1,
            2,
            3
          ]
        },
        {
          "indicateur": "P05",
          "phase": "tiree",
          "source": "llm",
          "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
          "note": null,
          "visible": false,
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
        "nom": "lumbar_under_load",
        "critere": "structure",
        "constat": "The lower back rounds hard and keeps rounding as the bar rises.",
        "a_essayer": "Stop the set. Rebuild this at a load where the lower back holds its shape.",
        "etat": "collapses",
        "note": 1,
        "reps": [
          3,
          4
        ]
      },
      {
        "indicateur": "P10",
        "nom": "thoracic_under_load",
        "critere": "structure",
        "constat": "The upper back rounds further during the pull than it was at the start.",
        "a_essayer": "Set the upper back before the pull and hold that shape; stop the set when it starts to give.",
        "etat": "flexion_appears",
        "note": 2,
        "reps": [
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
        "constat": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees.",
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
          "constat": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees.",
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
  "squelette": null,
  "debug": {
    "observations_brutes": {
      "equipment": "barbell",
      "grip": "mixed",
      "foot_orientation": "forward",
      "reps": [
        {
          "rep_index": 1,
          "bar_over_midfoot": "over_midfoot",
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "progressive",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "hip_vs_shoulder_rise": "together",
          "past_the_knees": "clean",
          "bar_leg_contact": "in_contact",
          "lumbar_under_load": "unchanged",
          "thoracic_under_load": "unchanged",
          "knee_valgus": "not_visible",
          "asymmetry": "even",
          "hitch": "no",
          "shrug": "no",
          "lean_back": "upright",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "reset",
          "summary": "Textbook first pull, everything stacked.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is rounded and already set before the bar moves.",
          "lumbar_under_load_observed": "The lower back holds its shape to lockout.",
          "hip_vs_shoulder_rise_observed": "Hips and shoulders leave the floor at the same rate."
        },
        {
          "rep_index": 2,
          "bar_over_midfoot": "over_midfoot",
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "progressive",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "hip_vs_shoulder_rise": "together",
          "past_the_knees": "clean",
          "bar_leg_contact": "in_contact",
          "lumbar_under_load": "unchanged",
          "thoracic_under_load": "unchanged",
          "knee_valgus": "not_visible",
          "asymmetry": "even",
          "hitch": "no",
          "shrug": "no",
          "lean_back": "upright",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "reset",
          "summary": "Still tight, the bar drifts a touch more.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is rounded and already set before the bar moves.",
          "lumbar_under_load_observed": "The lower back holds its shape to lockout.",
          "hip_vs_shoulder_rise_observed": "Hips and shoulders leave the floor at the same rate."
        },
        {
          "rep_index": 3,
          "bar_over_midfoot": "over_midfoot",
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "partial",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "hip_vs_shoulder_rise": "hips_shoot_up",
          "past_the_knees": "loops",
          "bar_leg_contact": "away_from_legs",
          "lumbar_under_load": "flexion_appears",
          "thoracic_under_load": "unchanged",
          "knee_valgus": "not_visible",
          "asymmetry": "even",
          "hitch": "no",
          "shrug": "no",
          "lean_back": "upright",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "reset",
          "summary": "The hips beat the shoulders out of the floor.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is rounded and already set before the bar moves.",
          "lumbar_under_load_observed": "The lower back rounds further as the bar passes the knees.",
          "hip_vs_shoulder_rise_observed": "The hips rise first; the torso stays inclined past the knees."
        },
        {
          "rep_index": 4,
          "bar_over_midfoot": "over_midfoot",
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "partial",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "hip_vs_shoulder_rise": "hips_shoot_up",
          "past_the_knees": "loops",
          "bar_leg_contact": "away_from_legs",
          "lumbar_under_load": "collapses",
          "thoracic_under_load": "flexion_appears",
          "knee_valgus": "not_visible",
          "asymmetry": "even",
          "hitch": "no",
          "shrug": "no",
          "lean_back": "upright",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "last_rep",
          "summary": "Last rep: the back rounds and the bar swings out.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is rounded and already set before the bar moves.",
          "lumbar_under_load_observed": "The lower back rounds further as the bar passes the knees.",
          "hip_vs_shoulder_rise_observed": "The hips rise first; the torso stays inclined past the knees."
        }
      ]
    },
    "catalogue": {
      "hip_height": {
        "id": "S01",
        "critere": "start_position",
        "phase": "setup",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Freeze the frame where the plates leave the floor. On that frame, compare two vertical distances: hips-to-shoulders and hips-to-knees.",
        "etats": [
          {
            "cle": "too_high",
            "note": 2,
            "description": "The hips are at, or nearly at, shoulder height: the hips-to-shoulders distance is far smaller than the hips-to-knees distance. The back is close to horizontal and the knees are nearly straight."
          },
          {
            "cle": "midway",
            "note": 3,
            "description": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent."
          },
          {
            "cle": "too_low",
            "note": 2,
            "description": "The hips are close to knee height: the hips-to-knees distance is far smaller than the hips-to-shoulders distance, the shins push forward and the knees sit over the bar."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "shoulders_over_bar": {
        "id": "S02",
        "critere": "start_position",
        "phase": "setup",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Where are the shoulders relative to the bar at the start?",
        "etats": [
          {
            "cle": "behind_bar",
            "note": 2,
            "description": "The shoulders start behind the bar, which sends the bar forward as soon as it leaves the floor."
          },
          {
            "cle": "over_bar",
            "note": 3,
            "description": "The shoulders are stacked over or just ahead of the bar."
          },
          {
            "cle": "far_ahead",
            "note": 2,
            "description": "The shoulders are far ahead of the bar, lengthening the lever on the lower back."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "bar_over_midfoot": {
        "id": "S04",
        "critere": "start_position",
        "phase": "setup",
        "source": "a_tester",
        "vue": "side",
        "portee": "rep",
        "question": "On the last frame before the plates leave the floor, drop a vertical line from the bar down to the floor. Where does it hit the foot? This is only answerable when the foot is seen from the side: from the front or three-quarter view, answer 'not_visible'.",
        "etats": [
          {
            "cle": "over_midfoot",
            "note": 3,
            "description": "The line hits the foot between the ankle and the base of the toes, roughly over the laces."
          },
          {
            "cle": "ahead_of_midfoot",
            "note": 2,
            "description": "The line hits the toes or the floor in front of the foot: there is daylight between the bar and the shins."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "lumbar_at_setup": {
        "id": "S05",
        "critere": "structure",
        "phase": "setup",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Look ONLY at the lower back, between the pelvis and the bottom of the ribs, before the bar moves. Ignore the upper back entirely: it is asked separately.",
        "etats": [
          {
            "cle": "neutral",
            "note": 3,
            "description": "The lower back keeps its natural inward curve at the setup."
          },
          {
            "cle": "flexed",
            "note": 2,
            "description": "The lower back is rounded outward at the setup."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "thoracic_at_setup": {
        "id": "S10",
        "critere": "structure",
        "phase": "setup",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Look ONLY at the upper back, between the bottom of the ribs and the neck, before the bar moves. Ignore the lower back entirely: it is asked separately.",
        "etats": [
          {
            "cle": "neutral",
            "note": 3,
            "description": "The upper back is flat before the bar moves."
          },
          {
            "cle": "rounded",
            "note": 3,
            "description": "The upper back is rounded before the bar moves."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "arms_long": {
        "id": "S06",
        "critere": "start_position",
        "phase": "setup",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "From the floor to lockout, look at the line shoulder -> elbow -> hand on the arm closest to the camera. Is it one straight line on every frame, or is there an angle at the elbow at some moment?",
        "etats": [
          {
            "cle": "straight",
            "note": 3,
            "description": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle."
          },
          {
            "cle": "slightly_bent",
            "note": 2,
            "description": "A small but visible angle at the elbow on some frames: the arm is not one straight line, but the forearm does not fold up."
          },
          {
            "cle": "bent",
            "note": 1,
            "description": "A clear angle at the elbow: the forearm folds and the biceps pulls the bar."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "slack_pull": {
        "id": "S07",
        "critere": "slack_and_brace",
        "phase": "setup",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Does the lifter take the slack out before the bar leaves the floor?",
        "etats": [
          {
            "cle": "progressive",
            "note": 3,
            "description": "The arms pull taut and the bar or plates visibly load before anything moves."
          },
          {
            "cle": "partial",
            "note": 2,
            "description": "Some tension is taken but it is lost as the bar breaks the floor."
          },
          {
            "cle": "yanked",
            "note": 1,
            "description": "No pre-tension at all: the lifter yanks the bar off the floor from a loose position."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "hip_vs_shoulder_rise": {
        "id": "L01",
        "critere": "leg_drive",
        "phase": "decollage",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "From the frame where the plates leave the floor to the frame where the bar reaches the knees, track the height of the hips and the height of the shoulders separately. Which of the two gains height?",
        "etats": [
          {
            "cle": "together",
            "note": 3,
            "description": "Both gain height at the same pace: the angle of the back is the same on the two frames."
          },
          {
            "cle": "hips_slightly_ahead",
            "note": 2,
            "description": "The hips gain height a little faster than the shoulders: the back tilts somewhat more toward the floor, then holds."
          },
          {
            "cle": "hips_shoot_up",
            "note": 1,
            "description": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees."
          },
          {
            "cle": "shoulders_only",
            "note": 1,
            "description": "The shoulders gain height while the hips stay where they started: the back swings up around the hips like a hinge and the knee angle hardly changes, because the legs were already nearly straight at the floor."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "jerky_start": {
        "id": "L03",
        "critere": "slack_and_brace",
        "phase": "decollage",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "Is the start smooth, or is the bar jerked off the floor?",
        "etats": [
          {
            "cle": "smooth",
            "note": 3,
            "description": "The bar accelerates smoothly out of the floor."
          },
          {
            "cle": "jerked",
            "note": 1,
            "description": "The bar is jerked and the lifter is pulled out of position."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "bar_left_floor": {
        "id": "L04",
        "critere": null,
        "phase": "decollage",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Did the bar actually leave the floor in this segment?",
        "etats": [
          {
            "cle": "yes",
            "note": null,
            "description": "The bar left the floor and was lifted: this is a real repetition."
          },
          {
            "cle": "no",
            "note": null,
            "description": "The bar stayed on the floor, or was already down and the athlete simply stood back up: this is NOT a repetition."
          },
          {
            "cle": "incomplete",
            "note": null,
            "description": "The bar left the floor but came back down before lockout: a real attempt that was not completed."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "past_the_knees": {
        "id": "P02",
        "critere": "bar_path",
        "phase": "tiree",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "How does the bar get past the knees?",
        "etats": [
          {
            "cle": "clean",
            "note": 3,
            "description": "The bar passes the knees close to the legs, in one line."
          },
          {
            "cle": "loops",
            "note": 2,
            "description": "The bar loops forward around the knees before coming back in."
          },
          {
            "cle": "catches",
            "note": 1,
            "description": "The bar catches on the knees and the lifter has to work around them."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "bar_leg_contact": {
        "id": "P03",
        "critere": "bar_path",
        "phase": "tiree",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Does the bar stay in contact with, or very close to, the legs?",
        "etats": [
          {
            "cle": "in_contact",
            "note": 3,
            "description": "The bar stays against or within a few centimetres of the legs the whole way up."
          },
          {
            "cle": "brief_loss",
            "note": 2,
            "description": "Contact is briefly lost, then the bar comes back to the legs."
          },
          {
            "cle": "away_from_legs",
            "note": 1,
            "description": "The bar travels visibly away from the legs."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "lumbar_under_load": {
        "id": "P04",
        "critere": "structure",
        "phase": "tiree",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Look ONLY at the lower back. Compare its shape at the floor, at knee height and at lockout. Does flexion get ADDED there during the pull?",
        "etats": [
          {
            "cle": "unchanged",
            "note": null,
            "description": "The lower back keeps the same shape from the floor to lockout."
          },
          {
            "cle": "flexion_appears",
            "note": 2,
            "description": "The lower back rounds further during the pull than it was at the start."
          },
          {
            "cle": "collapses",
            "note": 1,
            "description": "The lower back rounds hard and keeps rounding as the bar rises."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "thoracic_under_load": {
        "id": "P10",
        "critere": "structure",
        "phase": "tiree",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Look ONLY at the upper back. Compare its shape at the floor, at knee height and at lockout. Does flexion get ADDED there during the pull?",
        "etats": [
          {
            "cle": "unchanged",
            "note": null,
            "description": "The upper back keeps the same shape from the floor to lockout."
          },
          {
            "cle": "flexion_appears",
            "note": 2,
            "description": "The upper back rounds further during the pull than it was at the start."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "knee_valgus": {
        "id": "P05",
        "critere": "structure",
        "phase": "tiree",
        "source": "llm",
        "vue": "front",
        "portee": "rep",
        "question": "Do the knees stay out over the feet, or do they collapse inward? This is only answerable from the front or three-quarter view: from the side a knee coming in is indistinguishable from a knee coming forward, so answer 'not_visible'.",
        "etats": [
          {
            "cle": "tracks_out",
            "note": 3,
            "description": "The knees track outward over the feet throughout."
          },
          {
            "cle": "slight",
            "note": 2,
            "description": "The knees waver inward at the hardest point but never collapse."
          },
          {
            "cle": "collapses_in",
            "note": 1,
            "description": "The knees collapse inward off the floor."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "hitch": {
        "id": "P08",
        "critere": "finish_position",
        "phase": "tiree",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "Does the lifter ratchet the bar up the thighs?",
        "etats": [
          {
            "cle": "no",
            "note": 3,
            "description": "The bar rises in one continuous motion."
          },
          {
            "cle": "yes",
            "note": 1,
            "description": "The lifter re-flexes the knees and rests the bar on the thighs to ratchet it up."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "asymmetry": {
        "id": "P09",
        "critere": "structure",
        "phase": "tiree",
        "source": "a_tester",
        "vue": "front",
        "portee": "rep",
        "question": "Does one side of the bar rise ahead of the other?",
        "etats": [
          {
            "cle": "even",
            "note": 3,
            "description": "Both sides rise together."
          },
          {
            "cle": "uneven",
            "note": 2,
            "description": "One side finishes ahead of the other and the bar rotates."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "lean_back": {
        "id": "K03",
        "critere": "finish_position",
        "phase": "lockout",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Does the lifter lean back at the top?",
        "etats": [
          {
            "cle": "upright",
            "note": 3,
            "description": "The lifter finishes upright and neutral."
          },
          {
            "cle": "slight",
            "note": 2,
            "description": "A slight lean back at the top."
          },
          {
            "cle": "hyperextension",
            "note": 1,
            "description": "Marked lumbar hyperextension at the top instead of finishing with the glutes."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "shrug": {
        "id": "K04",
        "critere": "finish_position",
        "phase": "lockout",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "Does the lifter shrug the shoulders to finish?",
        "etats": [
          {
            "cle": "no",
            "note": 3,
            "description": "The lift finishes with hip extension alone."
          },
          {
            "cle": "yes",
            "note": 2,
            "description": "The lifter shrugs the shoulders at the top: the shrug adds no height to the bar and abandons the lat position."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "lockout_completion": {
        "id": "K07",
        "critere": "finish_position",
        "phase": "lockout",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Is the lift actually finished at the top: hips and knees both locked, the lifter standing tall?",
        "etats": [
          {
            "cle": "locked",
            "note": 3,
            "description": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished."
          },
          {
            "cle": "soft_knees",
            "note": 1,
            "description": "The knees stay visibly soft at the top."
          },
          {
            "cle": "hips_short",
            "note": 1,
            "description": "The hips stay visibly bent at the top: the lifter never comes all the way through."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "descent_control": {
        "id": "E02",
        "critere": "reset",
        "phase": "descente",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "How does the bar get back to the floor? If each rep is reset on the floor, only a dropped or uncontrolled bar is a fault: a deliberately fast but accompanied lowering is not.",
        "etats": [
          {
            "cle": "controlled",
            "note": 3,
            "description": "The bar is lowered under control, the lifter staying with it."
          },
          {
            "cle": "fast_but_controlled",
            "note": 2,
            "description": "The descent is quick but the hands stay with the bar all the way down."
          },
          {
            "cle": "dropped",
            "note": 1,
            "description": "The bar is dropped or crashes to the floor."
          },
          {
            "cle": "cut_off",
            "note": null,
            "description": "The lowering is cut off by the end of the video."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "rep_transition": {
        "id": "E03",
        "critere": "reset",
        "phase": "descente",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "How does this rep connect to the next one?",
        "etats": [
          {
            "cle": "reset",
            "note": 3,
            "description": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep."
          },
          {
            "cle": "touch_and_go",
            "note": 3,
            "description": "The bar touches and is immediately pulled again, but the position is still under control."
          },
          {
            "cle": "bounce",
            "note": 2,
            "description": "The plates bounce off the floor and the bounce is used to start the next rep."
          },
          {
            "cle": "last_rep",
            "note": null,
            "description": "This is the last rep of the set."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "equipment": {
        "id": "C04",
        "critere": null,
        "phase": "contexte",
        "source": "llm",
        "vue": "toute",
        "portee": "set",
        "question": "What is being lifted, and with what equipment?",
        "etats": [
          {
            "cle": "barbell",
            "note": null,
            "description": "A standard barbell with plates on the floor."
          },
          {
            "cle": "trap_bar",
            "note": null,
            "description": "A trap bar / hex bar: the lifter stands inside the frame."
          },
          {
            "cle": "other",
            "note": null,
            "description": "Something else: dumbbells, Smith machine, blocks, deficit, or a variant that is not a standard floor deadlift."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "grip": {
        "id": "C05",
        "critere": null,
        "phase": "contexte",
        "source": "llm",
        "vue": "toute",
        "portee": "set",
        "question": "How does the lifter grip the bar?",
        "etats": [
          {
            "cle": "double_overhand",
            "note": null,
            "description": "Both palms facing the lifter (double overhand)."
          },
          {
            "cle": "mixed",
            "note": null,
            "description": "One palm forward, one back (mixed grip)."
          },
          {
            "cle": "hook",
            "note": null,
            "description": "Hook grip: the thumb is trapped under the fingers."
          },
          {
            "cle": "straps",
            "note": null,
            "description": "Lifting straps are used."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      },
      "foot_orientation": {
        "id": "S08",
        "critere": null,
        "phase": "setup",
        "source": "llm",
        "vue": "toute",
        "portee": "set",
        "question": "How are the feet oriented?",
        "etats": [
          {
            "cle": "flared",
            "note": null,
            "description": "The toes are flared outwards."
          },
          {
            "cle": "forward",
            "note": null,
            "description": "The toes point roughly forward."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked."
          }
        ]
      }
    },
    "reps": [
      {
        "index": 1,
        "candidat": 1,
        "debut_s": 1.2,
        "fin_s": 5.4,
        "statut": "complete",
        "etats": {
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "bar_over_midfoot": "over_midfoot",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "progressive",
          "hip_vs_shoulder_rise": "together",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "past_the_knees": "clean",
          "bar_leg_contact": "in_contact",
          "lumbar_under_load": "unchanged",
          "thoracic_under_load": "unchanged",
          "knee_valgus": "not_visible",
          "hitch": "no",
          "asymmetry": "even",
          "lean_back": "upright",
          "shrug": "no",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "reset"
        },
        "notes": {
          "start_position": 3,
          "slack_and_brace": 3,
          "leg_drive": 3,
          "bar_path": 3,
          "finish_position": 3,
          "reset": 3,
          "structure": 3
        },
        "indicateurs": [
          {
            "nom": "hip_height",
            "etat": "midway",
            "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
            "note": 3,
            "observation": null,
            "reponse_brute": "midway"
          },
          {
            "nom": "shoulders_over_bar",
            "etat": "over_bar",
            "fait": "The shoulders are stacked over or just ahead of the bar.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_bar"
          },
          {
            "nom": "bar_over_midfoot",
            "etat": "over_midfoot",
            "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_midfoot"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "neutral",
            "fait": "The lower back keeps its natural inward curve at the setup.",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "neutral"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "rounded",
            "fait": "The upper back is rounded before the bar moves.",
            "note": 3,
            "observation": "The upper back is rounded and already set before the bar moves.",
            "reponse_brute": "rounded"
          },
          {
            "nom": "arms_long",
            "etat": "straight",
            "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
            "note": 3,
            "observation": null,
            "reponse_brute": "straight"
          },
          {
            "nom": "slack_pull",
            "etat": "progressive",
            "fait": "The arms pull taut and the bar or plates visibly load before anything moves.",
            "note": 3,
            "observation": null,
            "reponse_brute": "progressive"
          },
          {
            "nom": "hip_vs_shoulder_rise",
            "etat": "together",
            "fait": "Both gain height at the same pace: the angle of the back is the same on the two frames.",
            "note": 3,
            "observation": "Hips and shoulders leave the floor at the same rate.",
            "reponse_brute": "together"
          },
          {
            "nom": "jerky_start",
            "etat": "smooth",
            "fait": "The bar accelerates smoothly out of the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "smooth"
          },
          {
            "nom": "bar_left_floor",
            "etat": "yes",
            "fait": "The bar left the floor and was lifted: this is a real repetition.",
            "note": null,
            "observation": null,
            "reponse_brute": "yes"
          },
          {
            "nom": "past_the_knees",
            "etat": "clean",
            "fait": "The bar passes the knees close to the legs, in one line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "clean"
          },
          {
            "nom": "bar_leg_contact",
            "etat": "in_contact",
            "fait": "The bar stays against or within a few centimetres of the legs the whole way up.",
            "note": 3,
            "observation": null,
            "reponse_brute": "in_contact"
          },
          {
            "nom": "lumbar_under_load",
            "etat": "unchanged",
            "fait": "The lower back keeps the same shape from the floor to lockout.",
            "note": null,
            "observation": "The lower back holds its shape to lockout.",
            "reponse_brute": "unchanged"
          },
          {
            "nom": "thoracic_under_load",
            "etat": "unchanged",
            "fait": "The upper back keeps the same shape from the floor to lockout.",
            "note": null,
            "observation": null,
            "reponse_brute": "unchanged"
          },
          {
            "nom": "knee_valgus",
            "etat": "not_visible",
            "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "hitch",
            "etat": "no",
            "fait": "The bar rises in one continuous motion.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "asymmetry",
            "etat": "even",
            "fait": "Both sides rise together.",
            "note": 3,
            "observation": null,
            "reponse_brute": "even"
          },
          {
            "nom": "lean_back",
            "etat": "upright",
            "fait": "The lifter finishes upright and neutral.",
            "note": 3,
            "observation": null,
            "reponse_brute": "upright"
          },
          {
            "nom": "shrug",
            "etat": "no",
            "fait": "The lift finishes with hip extension alone.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "lockout_completion",
            "etat": "locked",
            "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
            "note": 3,
            "observation": null,
            "reponse_brute": "locked"
          },
          {
            "nom": "descent_control",
            "etat": "controlled",
            "fait": "The bar is lowered under control, the lifter staying with it.",
            "note": 3,
            "observation": null,
            "reponse_brute": "controlled"
          },
          {
            "nom": "rep_transition",
            "etat": "reset",
            "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
            "note": 3,
            "observation": null,
            "reponse_brute": "reset"
          }
        ],
        "summary": "Textbook first pull, everything stacked.",
        "hors_catalogue": {}
      },
      {
        "index": 2,
        "candidat": 2,
        "debut_s": 6.2,
        "fin_s": 10.4,
        "statut": "complete",
        "etats": {
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "bar_over_midfoot": "over_midfoot",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "progressive",
          "hip_vs_shoulder_rise": "together",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "past_the_knees": "clean",
          "bar_leg_contact": "in_contact",
          "lumbar_under_load": "unchanged",
          "thoracic_under_load": "unchanged",
          "knee_valgus": "not_visible",
          "hitch": "no",
          "asymmetry": "even",
          "lean_back": "upright",
          "shrug": "no",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "reset"
        },
        "notes": {
          "start_position": 3,
          "slack_and_brace": 3,
          "leg_drive": 3,
          "bar_path": 3,
          "finish_position": 3,
          "reset": 3,
          "structure": 3
        },
        "indicateurs": [
          {
            "nom": "hip_height",
            "etat": "midway",
            "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
            "note": 3,
            "observation": null,
            "reponse_brute": "midway"
          },
          {
            "nom": "shoulders_over_bar",
            "etat": "over_bar",
            "fait": "The shoulders are stacked over or just ahead of the bar.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_bar"
          },
          {
            "nom": "bar_over_midfoot",
            "etat": "over_midfoot",
            "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_midfoot"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "neutral",
            "fait": "The lower back keeps its natural inward curve at the setup.",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "neutral"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "rounded",
            "fait": "The upper back is rounded before the bar moves.",
            "note": 3,
            "observation": "The upper back is rounded and already set before the bar moves.",
            "reponse_brute": "rounded"
          },
          {
            "nom": "arms_long",
            "etat": "straight",
            "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
            "note": 3,
            "observation": null,
            "reponse_brute": "straight"
          },
          {
            "nom": "slack_pull",
            "etat": "progressive",
            "fait": "The arms pull taut and the bar or plates visibly load before anything moves.",
            "note": 3,
            "observation": null,
            "reponse_brute": "progressive"
          },
          {
            "nom": "hip_vs_shoulder_rise",
            "etat": "together",
            "fait": "Both gain height at the same pace: the angle of the back is the same on the two frames.",
            "note": 3,
            "observation": "Hips and shoulders leave the floor at the same rate.",
            "reponse_brute": "together"
          },
          {
            "nom": "jerky_start",
            "etat": "smooth",
            "fait": "The bar accelerates smoothly out of the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "smooth"
          },
          {
            "nom": "bar_left_floor",
            "etat": "yes",
            "fait": "The bar left the floor and was lifted: this is a real repetition.",
            "note": null,
            "observation": null,
            "reponse_brute": "yes"
          },
          {
            "nom": "past_the_knees",
            "etat": "clean",
            "fait": "The bar passes the knees close to the legs, in one line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "clean"
          },
          {
            "nom": "bar_leg_contact",
            "etat": "in_contact",
            "fait": "The bar stays against or within a few centimetres of the legs the whole way up.",
            "note": 3,
            "observation": null,
            "reponse_brute": "in_contact"
          },
          {
            "nom": "lumbar_under_load",
            "etat": "unchanged",
            "fait": "The lower back keeps the same shape from the floor to lockout.",
            "note": null,
            "observation": "The lower back holds its shape to lockout.",
            "reponse_brute": "unchanged"
          },
          {
            "nom": "thoracic_under_load",
            "etat": "unchanged",
            "fait": "The upper back keeps the same shape from the floor to lockout.",
            "note": null,
            "observation": null,
            "reponse_brute": "unchanged"
          },
          {
            "nom": "knee_valgus",
            "etat": "not_visible",
            "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "hitch",
            "etat": "no",
            "fait": "The bar rises in one continuous motion.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "asymmetry",
            "etat": "even",
            "fait": "Both sides rise together.",
            "note": 3,
            "observation": null,
            "reponse_brute": "even"
          },
          {
            "nom": "lean_back",
            "etat": "upright",
            "fait": "The lifter finishes upright and neutral.",
            "note": 3,
            "observation": null,
            "reponse_brute": "upright"
          },
          {
            "nom": "shrug",
            "etat": "no",
            "fait": "The lift finishes with hip extension alone.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "lockout_completion",
            "etat": "locked",
            "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
            "note": 3,
            "observation": null,
            "reponse_brute": "locked"
          },
          {
            "nom": "descent_control",
            "etat": "controlled",
            "fait": "The bar is lowered under control, the lifter staying with it.",
            "note": 3,
            "observation": null,
            "reponse_brute": "controlled"
          },
          {
            "nom": "rep_transition",
            "etat": "reset",
            "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
            "note": 3,
            "observation": null,
            "reponse_brute": "reset"
          }
        ],
        "summary": "Still tight, the bar drifts a touch more.",
        "hors_catalogue": {}
      },
      {
        "index": 3,
        "candidat": 3,
        "debut_s": 11.2,
        "fin_s": 15.4,
        "statut": "complete",
        "etats": {
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "bar_over_midfoot": "over_midfoot",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "partial",
          "hip_vs_shoulder_rise": "hips_shoot_up",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "past_the_knees": "loops",
          "bar_leg_contact": "away_from_legs",
          "lumbar_under_load": "flexion_appears",
          "thoracic_under_load": "unchanged",
          "knee_valgus": "not_visible",
          "hitch": "no",
          "asymmetry": "even",
          "lean_back": "upright",
          "shrug": "no",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "reset"
        },
        "notes": {
          "start_position": 3,
          "slack_and_brace": 2,
          "leg_drive": 1,
          "bar_path": 1,
          "finish_position": 3,
          "reset": 3,
          "structure": 2
        },
        "indicateurs": [
          {
            "nom": "hip_height",
            "etat": "midway",
            "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
            "note": 3,
            "observation": null,
            "reponse_brute": "midway"
          },
          {
            "nom": "shoulders_over_bar",
            "etat": "over_bar",
            "fait": "The shoulders are stacked over or just ahead of the bar.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_bar"
          },
          {
            "nom": "bar_over_midfoot",
            "etat": "over_midfoot",
            "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_midfoot"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "neutral",
            "fait": "The lower back keeps its natural inward curve at the setup.",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "neutral"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "rounded",
            "fait": "The upper back is rounded before the bar moves.",
            "note": 3,
            "observation": "The upper back is rounded and already set before the bar moves.",
            "reponse_brute": "rounded"
          },
          {
            "nom": "arms_long",
            "etat": "straight",
            "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
            "note": 3,
            "observation": null,
            "reponse_brute": "straight"
          },
          {
            "nom": "slack_pull",
            "etat": "partial",
            "fait": "Some tension is taken but it is lost as the bar breaks the floor.",
            "note": 2,
            "observation": null,
            "reponse_brute": "partial"
          },
          {
            "nom": "hip_vs_shoulder_rise",
            "etat": "hips_shoot_up",
            "fait": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees.",
            "note": 1,
            "observation": "The hips rise first; the torso stays inclined past the knees.",
            "reponse_brute": "hips_shoot_up"
          },
          {
            "nom": "jerky_start",
            "etat": "smooth",
            "fait": "The bar accelerates smoothly out of the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "smooth"
          },
          {
            "nom": "bar_left_floor",
            "etat": "yes",
            "fait": "The bar left the floor and was lifted: this is a real repetition.",
            "note": null,
            "observation": null,
            "reponse_brute": "yes"
          },
          {
            "nom": "past_the_knees",
            "etat": "loops",
            "fait": "The bar loops forward around the knees before coming back in.",
            "note": 2,
            "observation": null,
            "reponse_brute": "loops"
          },
          {
            "nom": "bar_leg_contact",
            "etat": "away_from_legs",
            "fait": "The bar travels visibly away from the legs.",
            "note": 1,
            "observation": null,
            "reponse_brute": "away_from_legs"
          },
          {
            "nom": "lumbar_under_load",
            "etat": "flexion_appears",
            "fait": "The lower back rounds further during the pull than it was at the start.",
            "note": 2,
            "observation": "The lower back rounds further as the bar passes the knees.",
            "reponse_brute": "flexion_appears"
          },
          {
            "nom": "thoracic_under_load",
            "etat": "unchanged",
            "fait": "The upper back keeps the same shape from the floor to lockout.",
            "note": null,
            "observation": null,
            "reponse_brute": "unchanged"
          },
          {
            "nom": "knee_valgus",
            "etat": "not_visible",
            "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "hitch",
            "etat": "no",
            "fait": "The bar rises in one continuous motion.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "asymmetry",
            "etat": "even",
            "fait": "Both sides rise together.",
            "note": 3,
            "observation": null,
            "reponse_brute": "even"
          },
          {
            "nom": "lean_back",
            "etat": "upright",
            "fait": "The lifter finishes upright and neutral.",
            "note": 3,
            "observation": null,
            "reponse_brute": "upright"
          },
          {
            "nom": "shrug",
            "etat": "no",
            "fait": "The lift finishes with hip extension alone.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "lockout_completion",
            "etat": "locked",
            "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
            "note": 3,
            "observation": null,
            "reponse_brute": "locked"
          },
          {
            "nom": "descent_control",
            "etat": "controlled",
            "fait": "The bar is lowered under control, the lifter staying with it.",
            "note": 3,
            "observation": null,
            "reponse_brute": "controlled"
          },
          {
            "nom": "rep_transition",
            "etat": "reset",
            "fait": "The bar comes to a full stop on the floor and the lifter rebuilds the setup before the next rep.",
            "note": 3,
            "observation": null,
            "reponse_brute": "reset"
          }
        ],
        "summary": "The hips beat the shoulders out of the floor.",
        "hors_catalogue": {}
      },
      {
        "index": 4,
        "candidat": 4,
        "debut_s": 16.2,
        "fin_s": 20.4,
        "statut": "complete",
        "etats": {
          "hip_height": "midway",
          "shoulders_over_bar": "over_bar",
          "bar_over_midfoot": "over_midfoot",
          "lumbar_at_setup": "neutral",
          "thoracic_at_setup": "rounded",
          "arms_long": "straight",
          "slack_pull": "partial",
          "hip_vs_shoulder_rise": "hips_shoot_up",
          "jerky_start": "smooth",
          "bar_left_floor": "yes",
          "past_the_knees": "loops",
          "bar_leg_contact": "away_from_legs",
          "lumbar_under_load": "collapses",
          "thoracic_under_load": "flexion_appears",
          "knee_valgus": "not_visible",
          "hitch": "no",
          "asymmetry": "even",
          "lean_back": "upright",
          "shrug": "no",
          "lockout_completion": "locked",
          "descent_control": "controlled",
          "rep_transition": "last_rep"
        },
        "notes": {
          "start_position": 3,
          "slack_and_brace": 2,
          "leg_drive": 1,
          "bar_path": 1,
          "finish_position": 3,
          "reset": 3,
          "structure": 1
        },
        "indicateurs": [
          {
            "nom": "hip_height",
            "etat": "midway",
            "fait": "The hips sit well below the shoulders AND well above the knees: the two distances are of the same order, the back is clearly inclined upward and the knees are clearly bent.",
            "note": 3,
            "observation": null,
            "reponse_brute": "midway"
          },
          {
            "nom": "shoulders_over_bar",
            "etat": "over_bar",
            "fait": "The shoulders are stacked over or just ahead of the bar.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_bar"
          },
          {
            "nom": "bar_over_midfoot",
            "etat": "over_midfoot",
            "fait": "The line hits the foot between the ankle and the base of the toes, roughly over the laces.",
            "note": 3,
            "observation": null,
            "reponse_brute": "over_midfoot"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "neutral",
            "fait": "The lower back keeps its natural inward curve at the setup.",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "neutral"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "rounded",
            "fait": "The upper back is rounded before the bar moves.",
            "note": 3,
            "observation": "The upper back is rounded and already set before the bar moves.",
            "reponse_brute": "rounded"
          },
          {
            "nom": "arms_long",
            "etat": "straight",
            "fait": "One straight line from the shoulder to the hand on every frame: the elbow never makes an angle.",
            "note": 3,
            "observation": null,
            "reponse_brute": "straight"
          },
          {
            "nom": "slack_pull",
            "etat": "partial",
            "fait": "Some tension is taken but it is lost as the bar breaks the floor.",
            "note": 2,
            "observation": null,
            "reponse_brute": "partial"
          },
          {
            "nom": "hip_vs_shoulder_rise",
            "etat": "hips_shoot_up",
            "fait": "The hips rise sharply while the shoulders stay low: the back ends up nearly horizontal and the legs are straight before the bar reaches the knees.",
            "note": 1,
            "observation": "The hips rise first; the torso stays inclined past the knees.",
            "reponse_brute": "hips_shoot_up"
          },
          {
            "nom": "jerky_start",
            "etat": "smooth",
            "fait": "The bar accelerates smoothly out of the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "smooth"
          },
          {
            "nom": "bar_left_floor",
            "etat": "yes",
            "fait": "The bar left the floor and was lifted: this is a real repetition.",
            "note": null,
            "observation": null,
            "reponse_brute": "yes"
          },
          {
            "nom": "past_the_knees",
            "etat": "loops",
            "fait": "The bar loops forward around the knees before coming back in.",
            "note": 2,
            "observation": null,
            "reponse_brute": "loops"
          },
          {
            "nom": "bar_leg_contact",
            "etat": "away_from_legs",
            "fait": "The bar travels visibly away from the legs.",
            "note": 1,
            "observation": null,
            "reponse_brute": "away_from_legs"
          },
          {
            "nom": "lumbar_under_load",
            "etat": "collapses",
            "fait": "The lower back rounds hard and keeps rounding as the bar rises.",
            "note": 1,
            "observation": "The lower back rounds further as the bar passes the knees.",
            "reponse_brute": "collapses"
          },
          {
            "nom": "thoracic_under_load",
            "etat": "flexion_appears",
            "fait": "The upper back rounds further during the pull than it was at the start.",
            "note": 2,
            "observation": null,
            "reponse_brute": "flexion_appears"
          },
          {
            "nom": "knee_valgus",
            "etat": "not_visible",
            "fait": "Not assessable on this rep: the camera angle, framing, lighting or video quality makes it impossible to see. Never use this for something you saw and disliked.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "hitch",
            "etat": "no",
            "fait": "The bar rises in one continuous motion.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "asymmetry",
            "etat": "even",
            "fait": "Both sides rise together.",
            "note": 3,
            "observation": null,
            "reponse_brute": "even"
          },
          {
            "nom": "lean_back",
            "etat": "upright",
            "fait": "The lifter finishes upright and neutral.",
            "note": 3,
            "observation": null,
            "reponse_brute": "upright"
          },
          {
            "nom": "shrug",
            "etat": "no",
            "fait": "The lift finishes with hip extension alone.",
            "note": 3,
            "observation": null,
            "reponse_brute": "no"
          },
          {
            "nom": "lockout_completion",
            "etat": "locked",
            "fait": "Hips and knees both reach full extension: the lifter stands tall and the rep is finished.",
            "note": 3,
            "observation": null,
            "reponse_brute": "locked"
          },
          {
            "nom": "descent_control",
            "etat": "controlled",
            "fait": "The bar is lowered under control, the lifter staying with it.",
            "note": 3,
            "observation": null,
            "reponse_brute": "controlled"
          },
          {
            "nom": "rep_transition",
            "etat": "last_rep",
            "fait": "This is the last rep of the set.",
            "note": null,
            "observation": null,
            "reponse_brute": "last_rep"
          }
        ],
        "summary": "Last rep: the back rounds and the bar swings out.",
        "hors_catalogue": {}
      }
    ],
    "ecartes": [],
    "contexte": [
      {
        "nom": "equipment",
        "etat": "barbell",
        "fait": "A standard barbell with plates on the floor.",
        "note": null,
        "observation": null,
        "reponse_brute": "barbell"
      },
      {
        "nom": "grip",
        "etat": "mixed",
        "fait": "One palm forward, one back (mixed grip).",
        "note": null,
        "observation": null,
        "reponse_brute": "mixed"
      },
      {
        "nom": "foot_orientation",
        "etat": "forward",
        "fait": "The toes point roughly forward.",
        "note": null,
        "observation": null,
        "reponse_brute": "forward"
      }
    ]
  },
  "modele": "gemini-3.5-flash"
};
