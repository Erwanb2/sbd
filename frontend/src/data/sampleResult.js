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
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
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
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
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
              "fait": "The torso angle remains strictly identical between T0 and T1. The hips and shoulders rise at the exact same rate to lift the bar.",
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
              "fait": "The barbell maintains its trajectory without creating any forward visual gap. It clears the knees smoothly without horizontal forward deviation.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "There is absolutely zero visual daylight between the barbell and the lifter's legs at any point. They maintain physical contact.",
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
              "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
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
              "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop).",
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
              "fait": "The lower back is extremely flat",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The exact shape of the lumbar segment at T0 remains strictly identical at T1.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Pure side angle makes this tracking impossible.",
              "note": null,
              "visible": false
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
        "thoracic_at_setup": "The upper back is flat and set before the bar moves.",
        "initiation_sequence": "The torso angle is the same when the plates leave the floor.",
        "lumbar_geometry_delta": "The lower back holds its shape from the floor to the knees."
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
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
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
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
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
              "fait": "The torso angle remains strictly identical between T0 and T1. The hips and shoulders rise at the exact same rate to lift the bar.",
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
              "fait": "The barbell maintains its trajectory without creating any forward visual gap. It clears the knees smoothly without horizontal forward deviation.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "There is absolutely zero visual daylight between the barbell and the lifter's legs at any point. They maintain physical contact.",
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
              "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
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
              "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop).",
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
              "fait": "The lower back is extremely flat",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The exact shape of the lumbar segment at T0 remains strictly identical at T1.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Pure side angle makes this tracking impossible.",
              "note": null,
              "visible": false
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
        "thoracic_at_setup": "The upper back is flat and set before the bar moves.",
        "initiation_sequence": "The torso angle is the same when the plates leave the floor.",
        "lumbar_geometry_delta": "The lower back holds its shape from the floor to the knees."
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
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
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
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
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
              "fait": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
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
              "fait": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps.",
              "note": 1,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor).",
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
              "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
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
              "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop).",
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
              "fait": "The lower back is extremely flat",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The exact shape of the lumbar segment at T0 remains strictly identical at T1.",
              "note": null,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Pure side angle makes this tracking impossible.",
              "note": null,
              "visible": false
            }
          ]
        }
      },
      "note": 2,
      "note_precise": 2.43,
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
        "thoracic_at_setup": "The upper back is flat and set before the bar moves.",
        "initiation_sequence": "The hips rise before the plates leave the floor; the torso tilts toward horizontal.",
        "lumbar_geometry_delta": "The lower back holds its shape from the floor to the knees."
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
              "indicateur": "S04",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S02",
              "phase": "setup",
              "source": "llm",
              "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S01",
              "phase": "setup",
              "source": "llm",
              "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
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
              "indicateur": "S06",
              "phase": "setup",
              "source": "a_tester",
              "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
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
              "fait": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
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
              "fait": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps.",
              "note": 1,
              "visible": true
            },
            {
              "indicateur": "P03",
              "phase": "tiree",
              "source": "llm",
              "fait": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor).",
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
              "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K07",
              "phase": "lockout",
              "source": "llm",
              "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K03",
              "phase": "lockout",
              "source": "llm",
              "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "K04",
              "phase": "lockout",
              "source": "a_tester",
              "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
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
              "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "E03",
              "phase": "descente",
              "source": "llm",
              "fait": "The video ends, this is the final repetition, or the floor contact is cut off.",
              "note": null,
              "visible": false
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
              "fait": "The lower back is extremely flat",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "S10",
              "phase": "setup",
              "source": "llm",
              "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
              "note": 3,
              "visible": true
            },
            {
              "indicateur": "P04",
              "phase": "tiree",
              "source": "llm",
              "fait": "The lumbar segment adds flexion between T0 and T1, creating a new or more pronounced outward curve (rounding under load).",
              "note": 1,
              "visible": true
            },
            {
              "indicateur": "P05",
              "phase": "tiree",
              "source": "llm",
              "fait": "Pure side angle makes this tracking impossible.",
              "note": null,
              "visible": false
            }
          ]
        }
      },
      "note": 2,
      "note_precise": 2.14,
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
        "thoracic_at_setup": "The upper back is flat and set before the bar moves.",
        "initiation_sequence": "The hips rise before the plates leave the floor; the torso tilts toward horizontal.",
        "lumbar_geometry_delta": "The lower back rounds further as the bar passes the knees."
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
          "indicateur": "S04",
          "phase": "setup",
          "source": "a_tester",
          "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
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
          "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
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
          "indicateur": "S01",
          "phase": "setup",
          "source": "llm",
          "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
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
          "indicateur": "S06",
          "phase": "setup",
          "source": "a_tester",
          "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
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
          "fait": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
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
          "fait": "The torso angle remains strictly identical between T0 and T1. The hips and shoulders rise at the exact same rate to lift the bar.",
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
          "indicateur": "P02",
          "phase": "tiree",
          "source": "a_tester",
          "fait": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps.",
          "note": 1,
          "visible": true,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "P03",
          "phase": "tiree",
          "source": "llm",
          "fait": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor).",
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
          "fait": "The barbell maintains its trajectory without creating any forward visual gap. It clears the knees smoothly without horizontal forward deviation.",
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
          "fait": "There is absolutely zero visual daylight between the barbell and the lifter's legs at any point. They maintain physical contact.",
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
          "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
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
          "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
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
          "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
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
          "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
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
          "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
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
          "fait": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop).",
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
          "fait": "The video ends, this is the final repetition, or the floor contact is cut off.",
          "note": null,
          "visible": false,
          "reps": [
            4
          ]
        }
      ]
    },
    "structure": {
      "libelle": "Structure under load",
      "note": 2,
      "poids": 0.5,
      "notes_par_rep": [
        3,
        3,
        3,
        1
      ],
      "faits": [
        {
          "indicateur": "P04",
          "phase": "tiree",
          "source": "llm",
          "fait": "The lumbar segment adds flexion between T0 and T1, creating a new or more pronounced outward curve (rounding under load).",
          "note": 1,
          "visible": true,
          "reps": [
            4
          ]
        },
        {
          "indicateur": "S05",
          "phase": "setup",
          "source": "llm",
          "fait": "The lower back is extremely flat",
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
          "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
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
          "fait": "The exact shape of the lumbar segment at T0 remains strictly identical at T1.",
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
          "fait": "Pure side angle makes this tracking impossible.",
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
        "nom": "lumbar_geometry_delta",
        "critere": "structure",
        "constat": "The lumbar segment adds flexion between T0 and T1, creating a new or more pronounced outward curve (rounding under load).",
        "a_essayer": "Stop the set. Rebuild this at a load where the lower back holds its shape.",
        "etat": "lumbar_becomes_convex",
        "note": 1,
        "reps": [
          4
        ]
      }
    ]
  },
  "epingle": {
    "indicateur": "L01",
    "nom": "initiation_sequence",
    "critere": "leg_drive",
    "constat": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
    "a_essayer": "Push the floor away with your legs and hold your chest angle until the plates leave the floor.",
    "etat": "torso_angle_decreases",
    "note": 1,
    "reps": [
      3,
      4
    ],
    "consequences": [
      {
        "indicateur": "P03",
        "nom": "bar_leg_daylight",
        "critere": "bar_path",
        "constat": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor).",
        "a_essayer": "Keep the bar in contact with the legs the whole way up.",
        "etat": "daylight_beyond_shoe",
        "note": 1,
        "reps": [
          3,
          4
        ]
      },
      {
        "indicateur": "P02",
        "nom": "bar_path_at_knees_topology",
        "critere": "bar_path",
        "constat": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps.",
        "a_essayer": "Let the hips come through as the bar reaches the knees so it passes close.",
        "etat": "bar_deviates_forward",
        "note": 1,
        "reps": [
          3,
          4
        ]
      }
    ],
    "autres": []
  },
  "note_sur_20": 17,
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
      "indicateur": "L01",
      "nom": "initiation_sequence",
      "critere": "leg_drive",
      "constat": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
      "a_essayer": "Push the floor away with your legs and hold your chest angle until the plates leave the floor.",
      "etat": "torso_angle_decreases",
      "note": 1,
      "reps": [
        3,
        4
      ],
      "consequences": [
        {
          "indicateur": "P03",
          "nom": "bar_leg_daylight",
          "critere": "bar_path",
          "constat": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor).",
          "a_essayer": "Keep the bar in contact with the legs the whole way up.",
          "etat": "daylight_beyond_shoe",
          "note": 1,
          "reps": [
            3,
            4
          ]
        },
        {
          "indicateur": "P02",
          "nom": "bar_path_at_knees_topology",
          "critere": "bar_path",
          "constat": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps.",
          "a_essayer": "Let the hips come through as the bar reaches the knees so it passes close.",
          "etat": "bar_deviates_forward",
          "note": 1,
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
    "nom": "The Crane",
    "fait": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
    "rep": 3,
    "indicateur": "L01"
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
          "bar_over_midfoot_topology": "bar_over_laces",
          "hip_height_via_femur": "femur_angled_upward",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "bar_left_floor": "yes",
          "initiation_sequence": "torso_angle_constant",
          "bar_path_at_knees_topology": "bar_slides_past_knees",
          "bar_leg_daylight": "zero_daylight",
          "lumbar_geometry_delta": "lumbar_geometry_constant",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "shoulder_elevation_delta": "distance_remains_constant",
          "sagittal_torso_angle": "torso_perpendicular",
          "lockout_extension": "full_180_extension",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "zero_velocity_maintained",
          "summary": "Textbook first pull, everything stacked.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is flat and set before the bar moves.",
          "lumbar_geometry_delta_observed": "The lower back holds its shape from the floor to the knees.",
          "initiation_sequence_observed": "The torso angle is the same when the plates leave the floor."
        },
        {
          "rep_index": 2,
          "bar_over_midfoot_topology": "bar_over_laces",
          "hip_height_via_femur": "femur_angled_upward",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "bar_left_floor": "yes",
          "initiation_sequence": "torso_angle_constant",
          "bar_path_at_knees_topology": "bar_slides_past_knees",
          "bar_leg_daylight": "zero_daylight",
          "lumbar_geometry_delta": "lumbar_geometry_constant",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "shoulder_elevation_delta": "distance_remains_constant",
          "sagittal_torso_angle": "torso_perpendicular",
          "lockout_extension": "full_180_extension",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "zero_velocity_maintained",
          "summary": "Still tight, the bar drifts a touch more.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is flat and set before the bar moves.",
          "lumbar_geometry_delta_observed": "The lower back holds its shape from the floor to the knees.",
          "initiation_sequence_observed": "The torso angle is the same when the plates leave the floor."
        },
        {
          "rep_index": 3,
          "bar_over_midfoot_topology": "bar_over_laces",
          "hip_height_via_femur": "femur_angled_upward",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "bar_left_floor": "yes",
          "initiation_sequence": "torso_angle_decreases",
          "bar_path_at_knees_topology": "bar_deviates_forward",
          "bar_leg_daylight": "daylight_beyond_shoe",
          "lumbar_geometry_delta": "lumbar_geometry_constant",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "shoulder_elevation_delta": "distance_remains_constant",
          "sagittal_torso_angle": "torso_perpendicular",
          "lockout_extension": "full_180_extension",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "zero_velocity_maintained",
          "summary": "The hips beat the shoulders out of the floor.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is flat and set before the bar moves.",
          "lumbar_geometry_delta_observed": "The lower back holds its shape from the floor to the knees.",
          "initiation_sequence_observed": "The hips rise before the plates leave the floor; the torso tilts toward horizontal."
        },
        {
          "rep_index": 4,
          "bar_over_midfoot_topology": "bar_over_laces",
          "hip_height_via_femur": "femur_angled_upward",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "bar_left_floor": "yes",
          "initiation_sequence": "torso_angle_decreases",
          "bar_path_at_knees_topology": "bar_deviates_forward",
          "bar_leg_daylight": "daylight_beyond_shoe",
          "lumbar_geometry_delta": "lumbar_becomes_convex",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "shoulder_elevation_delta": "distance_remains_constant",
          "sagittal_torso_angle": "torso_perpendicular",
          "lockout_extension": "full_180_extension",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "not_visible",
          "summary": "Last rep: the back rounds and the bar swings out.",
          "lumbar_at_setup_observed": "The lower back keeps its inward curve at the setup.",
          "thoracic_at_setup_observed": "The upper back is flat and set before the bar moves.",
          "lumbar_geometry_delta_observed": "The lower back rounds further as the bar passes the knees.",
          "initiation_sequence_observed": "The hips rise before the plates leave the floor; the torso tilts toward horizontal."
        }
      ]
    },
    "catalogue": {
      "bar_over_midfoot_topology": {
        "id": "S04",
        "critere": "start_position",
        "phase": "setup",
        "source": "a_tester",
        "vue": "side",
        "portee": "rep",
        "question": "Pause the video at the exact frame immediately preceding the first upward movement of the lifter's body. Look vertically down from the barbell to the lifter's shoe. Which specific part of the shoe is physically located directly underneath the barbell sleeve/shaft?",
        "etats": [
          {
            "cle": "bar_over_ankle_or_shin",
            "note": 1,
            "description": "The barbell is positioned over the ankle joint or is pressed hard against the shin, fully exposing the laces and toes in front of it."
          },
          {
            "cle": "bar_over_laces",
            "note": 3,
            "description": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot)."
          },
          {
            "cle": "bar_over_toes_or_floor",
            "note": 2,
            "description": "The barbell is positioned over the toe box of the shoe, or completely in front of the shoe over the empty floor."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The plates completely block the view of the shoe."
          }
        ]
      },
      "shoulders_over_bar_gravity": {
        "id": "S02",
        "critere": "start_position",
        "phase": "setup",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Pause the video at the exact frame immediately preceding the first upward movement of the lifter's body. Drop a perfectly vertical imaginary plumb line from the lifter's shoulder joint straight down to the floor. Now, look at where this vertical line lands horizontally relative to the barbell.",
        "etats": [
          {
            "cle": "shoulder_behind_bar",
            "note": 2,
            "description": "The vertical plumb line from the shoulder falls horizontally behind the barbell (closer to the lifter's heels). The arm creates a diagonal line reaching forward to grab the bar."
          },
          {
            "cle": "shoulder_stacked_over_bar",
            "note": 3,
            "description": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor)."
          },
          {
            "cle": "shoulder_ahead_of_bar",
            "note": 3,
            "description": "The vertical plumb line from the shoulder falls horizontally in front of the barbell (closer to the lifter's toes). The arm creates a diagonal line reaching backward towards the lifter's shins to grab the bar."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The arm is obscured."
          }
        ]
      },
      "hip_height_via_femur": {
        "id": "S01",
        "critere": "start_position",
        "phase": "setup",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Pause the video at the exact frame immediately preceding the first upward movement of the lifter's body. Focus strictly on the lifter's femur (the thigh bone connecting the knee to the hip). Analyze the physical inclination of the femur relative to the floor.",
        "etats": [
          {
            "cle": "femur_angled_upward",
            "note": 3,
            "description": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line."
          },
          {
            "cle": "femur_parallel_or_downward",
            "note": 1,
            "description": "The femur is exactly parallel to the floor, or the hip joint sits strictly lower than the knee joint (downward angle)."
          },
          {
            "cle": "torso_parallel_to_floor",
            "note": 2,
            "description": "The hip joint is positioned so high that the torso is parallel to the floor, and the femurs are nearly vertical (knees locked or almost locked)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The thighs are obscured."
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
        "question": "Pause the video at the exact frame immediately preceding the first upward movement. Analyze the physical contour of the lower back",
        "etats": [
          {
            "cle": "lumbar_neutral_or_concave",
            "note": 3,
            "description": "The lower back is extremely flat"
          },
          {
            "cle": "upper_lumbar_convexity",
            "note": 2,
            "description": "The lower back forms a curve on in its upper half"
          },
          {
            "cle": "full_lumbar_convexity",
            "note": 1,
            "description": "The entire lower back forms a \"C\" shape ."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The lower back contour is obscured by clothing or camera angle."
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
        "question": "Pause the video at the exact frame immediately preceding the first upward movement of the lifter's body. Draw a perfectly straight imaginary line (the string) connecting the bottom of the lifter's ribcage to the base of their neck. Now, look at the physical contour of the lifter's upper back (the bow) relative to this straight line.",
        "etats": [
          {
            "cle": "thoracic_neutral_or_concave",
            "note": 3,
            "description": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed."
          },
          {
            "cle": "upper_thoracic_convexity",
            "note": 2,
            "description": "The physical contour crosses behind the straight line (away from the chest) to form an outward arc, BUT this curve only begins in the upper half of the segment (near the shoulder blades/base of the neck). The mid-back section directly above the ribcage remains flat."
          },
          {
            "cle": "full_thoracic_convexity",
            "note": 1,
            "description": "The physical contour crosses behind the straight line to form an outward arc, AND this curve begins immediately from the bottom of the ribcage. The entire mid-to-upper back forms a continuous \"C\" shape, indicating a complete loss of structural extension."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The camera angle or loose clothing prevents a clear view of the upper back's contour."
          }
        ]
      },
      "arms_tension_at_setup": {
        "id": "S06",
        "critere": "slack_and_brace",
        "phase": "setup",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "Analyze the sequence leading up to the exact frame the plates leave the floor. Look strictly at the angle formed by the shoulder, elbow, and wrist joints. Does this geometric angle change exactly as the weight leaves the floor?",
        "etats": [
          {
            "cle": "elbow_locked_prior",
            "note": 3,
            "description": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff."
          },
          {
            "cle": "elbow_angle_changes",
            "note": 1,
            "description": "The elbow angle is less than 180 degrees (bent) "
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The arms are obscured."
          }
        ]
      },
      "initiation_sequence": {
        "id": "L01",
        "critere": "leg_drive",
        "phase": "decollage",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Analyze the sequence from the exact frame the lifter initiates physical effort (T0) to the exact frame the plates break physical contact with the floor (T1). Focus ONLY on the angle of the torso relative to the floor. Compare this angle at T0 and at T1.",
        "etats": [
          {
            "cle": "torso_angle_decreases",
            "note": 1,
            "description": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor."
          },
          {
            "cle": "torso_angle_constant",
            "note": 3,
            "description": "The torso angle remains strictly identical between T0 and T1. The hips and shoulders rise at the exact same rate to lift the bar."
          },
          {
            "cle": "torso_angle_increases",
            "note": 2,
            "description": "The torso angle becomes visibly larger (more vertical to the floor) between T0 and T1. The shoulders rise at a faster rate than the hips before the bar leaves the floor."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Lighting or framerate prevents a clear comparison."
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
      "bar_path_at_knees_topology": {
        "id": "P02",
        "critere": "bar_path",
        "phase": "tiree",
        "source": "a_tester",
        "vue": "side",
        "portee": "rep",
        "question": "Play the video from liftoff until the barbell passes the lifter's knees. Look strictly at the physical distance between the barbell shaft and the kneecaps. Does the barbell physically loop forward to navigate around the knees?",
        "etats": [
          {
            "cle": "bar_slides_past_knees",
            "note": 3,
            "description": "The barbell maintains its trajectory without creating any forward visual gap. It clears the knees smoothly without horizontal forward deviation."
          },
          {
            "cle": "bar_deviates_forward",
            "note": 1,
            "description": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The knees or the bar are obscured."
          }
        ]
      },
      "bar_leg_daylight": {
        "id": "P03",
        "critere": "bar_path",
        "phase": "tiree",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Analyze the video from the moment the plates leave the floor until the barbell reaches the hips. Look strictly at the physical space (daylight) between the barbell and the lifter's legs, and project a vertical line from the barbell to the floor.",
        "etats": [
          {
            "cle": "zero_daylight",
            "note": 3,
            "description": "There is absolutely zero visual daylight between the barbell and the lifter's legs at any point. They maintain physical contact."
          },
          {
            "cle": "daylight_over_shoe",
            "note": 2,
            "description": "Daylight appears between the bar and the legs, BUT a vertical line dropped from the barbell still lands inside the footprint of the lifter's shoe."
          },
          {
            "cle": "daylight_beyond_shoe",
            "note": 1,
            "description": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Plates or angle obscure the gap."
          }
        ]
      },
      "lumbar_geometry_delta": {
        "id": "P04",
        "critere": "structure",
        "phase": "tiree",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Compare the exact frame just before liftoff (T0) to the exact frame where the barbell reaches the kneecaps (T1). Look strictly at the lumbar spine segment (pelvis to bottom ribs). Does the geometric shape of this segment change between T0 and T1?",
        "etats": [
          {
            "cle": "lumbar_geometry_constant",
            "note": null,
            "description": "The exact shape of the lumbar segment at T0 remains strictly identical at T1."
          },
          {
            "cle": "lumbar_becomes_convex",
            "note": 1,
            "description": "The lumbar segment adds flexion between T0 and T1, creating a new or more pronounced outward curve (rounding under load)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The lower back is obscured."
          }
        ]
      },
      "knee_valgus_tracking": {
        "id": "P05",
        "critere": "structure",
        "phase": "tiree",
        "source": "llm",
        "vue": "front",
        "portee": "rep",
        "question": "Watch the pull from a front or 3/4 angle. Draw a strict vertical line upward from the inner edge of the lifter's shoe (the side closest to the other foot). Track the center of the kneecaps (patellas) during the ascent relative to this line.",
        "etats": [
          {
            "cle": "knees_outside_line",
            "note": 3,
            "description": "The center of both kneecaps remains strictly outside (wider than) the vertical line from the inner edge of the shoe."
          },
          {
            "cle": "knees_touch_line",
            "note": 2,
            "description": "The center of one or both kneecaps moves inward and touches the vertical line, but does not cross it."
          },
          {
            "cle": "knees_cross_inside_line",
            "note": 1,
            "description": "The center of one or both kneecaps physically crosses inside (narrower than) the vertical line from the inner edge of the shoe."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Pure side angle makes this tracking impossible."
          }
        ]
      },
      "vertical_velocity_hitch": {
        "id": "P08",
        "critere": "finish_position",
        "phase": "tiree",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "Track the upward movement of the barbell on the Y-axis from the floor to the hips. Does the vertical upward velocity ever drop to zero or become negative before the lockout?",
        "etats": [
          {
            "cle": "continuous_positive_velocity",
            "note": 3,
            "description": "The barbell's Y-axis height strictly increases on every single frame until lockout."
          },
          {
            "cle": "velocity_hits_zero_or_negative",
            "note": 1,
            "description": "The barbell's Y-axis height stops increasing (pauses) or decreases (drops slightly) while resting on the lifter's thighs (hitching)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "Framerate prevents tracking the bar's continuous height."
          }
        ]
      },
      "lockout_extension": {
        "id": "K07",
        "critere": "finish_position",
        "phase": "lockout",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Pause the video at the exact frame of maximum upward completion (the lockout). Look strictly at the angle of the knee joint and the hip joint.",
        "etats": [
          {
            "cle": "full_180_extension",
            "note": 3,
            "description": "Both the knee joint and the hip joint form a strict 180-degree straight line."
          },
          {
            "cle": "hip_angle_under_180",
            "note": 2,
            "description": "The knee joint is at 180 degrees, but the hip joint angle remains visibly less than 180 degrees (torso leaning forward)."
          },
          {
            "cle": "knee_angle_under_180",
            "note": 1,
            "description": "The knee joint angle remains visibly less than 180 degrees (knees bent)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The joints are obscured."
          }
        ]
      },
      "sagittal_torso_angle": {
        "id": "K03",
        "critere": "finish_position",
        "phase": "lockout",
        "source": "llm",
        "vue": "side",
        "portee": "rep",
        "question": "Pause the video at the exact frame of maximum upward completion (the lockout). Analyze the angle of the lifter's torso relative to the floor in 3D space.",
        "etats": [
          {
            "cle": "torso_perpendicular",
            "note": 3,
            "description": "The torso is perfectly perpendicular to the floor (90 degrees)."
          },
          {
            "cle": "torso_obtuse_angle",
            "note": 1,
            "description": "The torso forms an obtuse angle relative to the floor in front of the lifter. The lifter is leaning backward away from the barbell (lumbar hyperextension)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The torso is obscured."
          }
        ]
      },
      "shoulder_elevation_delta": {
        "id": "K04",
        "critere": "finish_position",
        "phase": "lockout",
        "source": "a_tester",
        "vue": "toute",
        "portee": "rep",
        "question": "Compare the vertical physical distance between the lifter's shoulder joint and their ear lobe at two moments: when the barbell is at the knees (T1), and at the final lockout (T2).",
        "etats": [
          {
            "cle": "distance_remains_constant",
            "note": 3,
            "description": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2."
          },
          {
            "cle": "distance_decreases",
            "note": 1,
            "description": "The vertical distance between the shoulder and the ear visibly decreases at T2 (the shoulders move closer to the ears/shrugging)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The neck/shoulder area is obscured."
          }
        ]
      },
      "descent_hand_contact": {
        "id": "E02",
        "critere": "reset",
        "phase": "descente",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Analyze the sequence from the final lockout until the plates physically touch the floor again. Look strictly at the lifter's hands.",
        "etats": [
          {
            "cle": "hands_maintain_contact",
            "note": 3,
            "description": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor."
          },
          {
            "cle": "hands_break_contact",
            "note": 1,
            "description": "Visual space appears between the lifter's hands and the barbell BEFORE the plates touch the floor (the bar is dropped)."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The hands leave the video frame during the descent."
          }
        ]
      },
      "rep_transition_velocity": {
        "id": "E03",
        "critere": "reset",
        "phase": "descente",
        "source": "llm",
        "vue": "toute",
        "portee": "rep",
        "question": "Observe the exact moment the barbell touches the floor between two repetitions. Track the barbell's movement on the Y-axis. How long does the Y-axis velocity remain exactly at zero?",
        "etats": [
          {
            "cle": "zero_velocity_maintained",
            "note": 3,
            "description": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop)."
          },
          {
            "cle": "immediate_positive_velocity",
            "note": 3,
            "description": "The barbell touches the floor and its Y-axis velocity becomes positive again instantly (under 0.5 seconds), but the plates do not physically bounce off the floor (touch and go)."
          },
          {
            "cle": "impact_rebound",
            "note": 1,
            "description": "The plates strike the floor and visibly rebound, causing the bar to bounce upward using momentum."
          },
          {
            "cle": "not_visible",
            "note": null,
            "description": "The video ends, this is the final repetition, or the floor contact is cut off."
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
          "bar_over_midfoot_topology": "bar_over_laces",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "hip_height_via_femur": "femur_angled_upward",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "initiation_sequence": "torso_angle_constant",
          "bar_left_floor": "yes",
          "bar_path_at_knees_topology": "bar_slides_past_knees",
          "bar_leg_daylight": "zero_daylight",
          "lumbar_geometry_delta": "lumbar_geometry_constant",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "lockout_extension": "full_180_extension",
          "sagittal_torso_angle": "torso_perpendicular",
          "shoulder_elevation_delta": "distance_remains_constant",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "zero_velocity_maintained"
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
            "nom": "bar_over_midfoot_topology",
            "etat": "bar_over_laces",
            "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
            "note": 3,
            "observation": null,
            "reponse_brute": "bar_over_laces"
          },
          {
            "nom": "shoulders_over_bar_gravity",
            "etat": "shoulder_stacked_over_bar",
            "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
            "note": 3,
            "observation": null,
            "reponse_brute": "shoulder_stacked_over_bar"
          },
          {
            "nom": "hip_height_via_femur",
            "etat": "femur_angled_upward",
            "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "femur_angled_upward"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "lumbar_neutral_or_concave",
            "fait": "The lower back is extremely flat",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "lumbar_neutral_or_concave"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "thoracic_neutral_or_concave",
            "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
            "note": 3,
            "observation": "The upper back is flat and set before the bar moves.",
            "reponse_brute": "thoracic_neutral_or_concave"
          },
          {
            "nom": "arms_tension_at_setup",
            "etat": "elbow_locked_prior",
            "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
            "note": 3,
            "observation": null,
            "reponse_brute": "elbow_locked_prior"
          },
          {
            "nom": "initiation_sequence",
            "etat": "torso_angle_constant",
            "fait": "The torso angle remains strictly identical between T0 and T1. The hips and shoulders rise at the exact same rate to lift the bar.",
            "note": 3,
            "observation": "The torso angle is the same when the plates leave the floor.",
            "reponse_brute": "torso_angle_constant"
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
            "nom": "bar_path_at_knees_topology",
            "etat": "bar_slides_past_knees",
            "fait": "The barbell maintains its trajectory without creating any forward visual gap. It clears the knees smoothly without horizontal forward deviation.",
            "note": 3,
            "observation": null,
            "reponse_brute": "bar_slides_past_knees"
          },
          {
            "nom": "bar_leg_daylight",
            "etat": "zero_daylight",
            "fait": "There is absolutely zero visual daylight between the barbell and the lifter's legs at any point. They maintain physical contact.",
            "note": 3,
            "observation": null,
            "reponse_brute": "zero_daylight"
          },
          {
            "nom": "lumbar_geometry_delta",
            "etat": "lumbar_geometry_constant",
            "fait": "The exact shape of the lumbar segment at T0 remains strictly identical at T1.",
            "note": null,
            "observation": "The lower back holds its shape from the floor to the knees.",
            "reponse_brute": "lumbar_geometry_constant"
          },
          {
            "nom": "knee_valgus_tracking",
            "etat": "not_visible",
            "fait": "Pure side angle makes this tracking impossible.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "vertical_velocity_hitch",
            "etat": "continuous_positive_velocity",
            "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
            "note": 3,
            "observation": null,
            "reponse_brute": "continuous_positive_velocity"
          },
          {
            "nom": "lockout_extension",
            "etat": "full_180_extension",
            "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "full_180_extension"
          },
          {
            "nom": "sagittal_torso_angle",
            "etat": "torso_perpendicular",
            "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
            "note": 3,
            "observation": null,
            "reponse_brute": "torso_perpendicular"
          },
          {
            "nom": "shoulder_elevation_delta",
            "etat": "distance_remains_constant",
            "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
            "note": 3,
            "observation": null,
            "reponse_brute": "distance_remains_constant"
          },
          {
            "nom": "descent_hand_contact",
            "etat": "hands_maintain_contact",
            "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "hands_maintain_contact"
          },
          {
            "nom": "rep_transition_velocity",
            "etat": "zero_velocity_maintained",
            "fait": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop).",
            "note": 3,
            "observation": null,
            "reponse_brute": "zero_velocity_maintained"
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
          "bar_over_midfoot_topology": "bar_over_laces",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "hip_height_via_femur": "femur_angled_upward",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "initiation_sequence": "torso_angle_constant",
          "bar_left_floor": "yes",
          "bar_path_at_knees_topology": "bar_slides_past_knees",
          "bar_leg_daylight": "zero_daylight",
          "lumbar_geometry_delta": "lumbar_geometry_constant",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "lockout_extension": "full_180_extension",
          "sagittal_torso_angle": "torso_perpendicular",
          "shoulder_elevation_delta": "distance_remains_constant",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "zero_velocity_maintained"
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
            "nom": "bar_over_midfoot_topology",
            "etat": "bar_over_laces",
            "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
            "note": 3,
            "observation": null,
            "reponse_brute": "bar_over_laces"
          },
          {
            "nom": "shoulders_over_bar_gravity",
            "etat": "shoulder_stacked_over_bar",
            "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
            "note": 3,
            "observation": null,
            "reponse_brute": "shoulder_stacked_over_bar"
          },
          {
            "nom": "hip_height_via_femur",
            "etat": "femur_angled_upward",
            "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "femur_angled_upward"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "lumbar_neutral_or_concave",
            "fait": "The lower back is extremely flat",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "lumbar_neutral_or_concave"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "thoracic_neutral_or_concave",
            "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
            "note": 3,
            "observation": "The upper back is flat and set before the bar moves.",
            "reponse_brute": "thoracic_neutral_or_concave"
          },
          {
            "nom": "arms_tension_at_setup",
            "etat": "elbow_locked_prior",
            "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
            "note": 3,
            "observation": null,
            "reponse_brute": "elbow_locked_prior"
          },
          {
            "nom": "initiation_sequence",
            "etat": "torso_angle_constant",
            "fait": "The torso angle remains strictly identical between T0 and T1. The hips and shoulders rise at the exact same rate to lift the bar.",
            "note": 3,
            "observation": "The torso angle is the same when the plates leave the floor.",
            "reponse_brute": "torso_angle_constant"
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
            "nom": "bar_path_at_knees_topology",
            "etat": "bar_slides_past_knees",
            "fait": "The barbell maintains its trajectory without creating any forward visual gap. It clears the knees smoothly without horizontal forward deviation.",
            "note": 3,
            "observation": null,
            "reponse_brute": "bar_slides_past_knees"
          },
          {
            "nom": "bar_leg_daylight",
            "etat": "zero_daylight",
            "fait": "There is absolutely zero visual daylight between the barbell and the lifter's legs at any point. They maintain physical contact.",
            "note": 3,
            "observation": null,
            "reponse_brute": "zero_daylight"
          },
          {
            "nom": "lumbar_geometry_delta",
            "etat": "lumbar_geometry_constant",
            "fait": "The exact shape of the lumbar segment at T0 remains strictly identical at T1.",
            "note": null,
            "observation": "The lower back holds its shape from the floor to the knees.",
            "reponse_brute": "lumbar_geometry_constant"
          },
          {
            "nom": "knee_valgus_tracking",
            "etat": "not_visible",
            "fait": "Pure side angle makes this tracking impossible.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "vertical_velocity_hitch",
            "etat": "continuous_positive_velocity",
            "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
            "note": 3,
            "observation": null,
            "reponse_brute": "continuous_positive_velocity"
          },
          {
            "nom": "lockout_extension",
            "etat": "full_180_extension",
            "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "full_180_extension"
          },
          {
            "nom": "sagittal_torso_angle",
            "etat": "torso_perpendicular",
            "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
            "note": 3,
            "observation": null,
            "reponse_brute": "torso_perpendicular"
          },
          {
            "nom": "shoulder_elevation_delta",
            "etat": "distance_remains_constant",
            "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
            "note": 3,
            "observation": null,
            "reponse_brute": "distance_remains_constant"
          },
          {
            "nom": "descent_hand_contact",
            "etat": "hands_maintain_contact",
            "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "hands_maintain_contact"
          },
          {
            "nom": "rep_transition_velocity",
            "etat": "zero_velocity_maintained",
            "fait": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop).",
            "note": 3,
            "observation": null,
            "reponse_brute": "zero_velocity_maintained"
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
          "bar_over_midfoot_topology": "bar_over_laces",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "hip_height_via_femur": "femur_angled_upward",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "initiation_sequence": "torso_angle_decreases",
          "bar_left_floor": "yes",
          "bar_path_at_knees_topology": "bar_deviates_forward",
          "bar_leg_daylight": "daylight_beyond_shoe",
          "lumbar_geometry_delta": "lumbar_geometry_constant",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "lockout_extension": "full_180_extension",
          "sagittal_torso_angle": "torso_perpendicular",
          "shoulder_elevation_delta": "distance_remains_constant",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "zero_velocity_maintained"
        },
        "notes": {
          "start_position": 3,
          "slack_and_brace": 3,
          "leg_drive": 1,
          "bar_path": 1,
          "finish_position": 3,
          "reset": 3,
          "structure": 3
        },
        "indicateurs": [
          {
            "nom": "bar_over_midfoot_topology",
            "etat": "bar_over_laces",
            "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
            "note": 3,
            "observation": null,
            "reponse_brute": "bar_over_laces"
          },
          {
            "nom": "shoulders_over_bar_gravity",
            "etat": "shoulder_stacked_over_bar",
            "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
            "note": 3,
            "observation": null,
            "reponse_brute": "shoulder_stacked_over_bar"
          },
          {
            "nom": "hip_height_via_femur",
            "etat": "femur_angled_upward",
            "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "femur_angled_upward"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "lumbar_neutral_or_concave",
            "fait": "The lower back is extremely flat",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "lumbar_neutral_or_concave"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "thoracic_neutral_or_concave",
            "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
            "note": 3,
            "observation": "The upper back is flat and set before the bar moves.",
            "reponse_brute": "thoracic_neutral_or_concave"
          },
          {
            "nom": "arms_tension_at_setup",
            "etat": "elbow_locked_prior",
            "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
            "note": 3,
            "observation": null,
            "reponse_brute": "elbow_locked_prior"
          },
          {
            "nom": "initiation_sequence",
            "etat": "torso_angle_decreases",
            "fait": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
            "note": 1,
            "observation": "The hips rise before the plates leave the floor; the torso tilts toward horizontal.",
            "reponse_brute": "torso_angle_decreases"
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
            "nom": "bar_path_at_knees_topology",
            "etat": "bar_deviates_forward",
            "fait": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps.",
            "note": 1,
            "observation": null,
            "reponse_brute": "bar_deviates_forward"
          },
          {
            "nom": "bar_leg_daylight",
            "etat": "daylight_beyond_shoe",
            "fait": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor).",
            "note": 1,
            "observation": null,
            "reponse_brute": "daylight_beyond_shoe"
          },
          {
            "nom": "lumbar_geometry_delta",
            "etat": "lumbar_geometry_constant",
            "fait": "The exact shape of the lumbar segment at T0 remains strictly identical at T1.",
            "note": null,
            "observation": "The lower back holds its shape from the floor to the knees.",
            "reponse_brute": "lumbar_geometry_constant"
          },
          {
            "nom": "knee_valgus_tracking",
            "etat": "not_visible",
            "fait": "Pure side angle makes this tracking impossible.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "vertical_velocity_hitch",
            "etat": "continuous_positive_velocity",
            "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
            "note": 3,
            "observation": null,
            "reponse_brute": "continuous_positive_velocity"
          },
          {
            "nom": "lockout_extension",
            "etat": "full_180_extension",
            "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "full_180_extension"
          },
          {
            "nom": "sagittal_torso_angle",
            "etat": "torso_perpendicular",
            "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
            "note": 3,
            "observation": null,
            "reponse_brute": "torso_perpendicular"
          },
          {
            "nom": "shoulder_elevation_delta",
            "etat": "distance_remains_constant",
            "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
            "note": 3,
            "observation": null,
            "reponse_brute": "distance_remains_constant"
          },
          {
            "nom": "descent_hand_contact",
            "etat": "hands_maintain_contact",
            "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "hands_maintain_contact"
          },
          {
            "nom": "rep_transition_velocity",
            "etat": "zero_velocity_maintained",
            "fait": "The barbell's Y-axis velocity reaches zero and remains exactly at zero for at least 0.5 seconds before the next pull begins (dead stop).",
            "note": 3,
            "observation": null,
            "reponse_brute": "zero_velocity_maintained"
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
          "bar_over_midfoot_topology": "bar_over_laces",
          "shoulders_over_bar_gravity": "shoulder_stacked_over_bar",
          "hip_height_via_femur": "femur_angled_upward",
          "lumbar_at_setup": "lumbar_neutral_or_concave",
          "thoracic_at_setup": "thoracic_neutral_or_concave",
          "arms_tension_at_setup": "elbow_locked_prior",
          "initiation_sequence": "torso_angle_decreases",
          "bar_left_floor": "yes",
          "bar_path_at_knees_topology": "bar_deviates_forward",
          "bar_leg_daylight": "daylight_beyond_shoe",
          "lumbar_geometry_delta": "lumbar_becomes_convex",
          "knee_valgus_tracking": "not_visible",
          "vertical_velocity_hitch": "continuous_positive_velocity",
          "lockout_extension": "full_180_extension",
          "sagittal_torso_angle": "torso_perpendicular",
          "shoulder_elevation_delta": "distance_remains_constant",
          "descent_hand_contact": "hands_maintain_contact",
          "rep_transition_velocity": "not_visible"
        },
        "notes": {
          "start_position": 3,
          "slack_and_brace": 3,
          "leg_drive": 1,
          "bar_path": 1,
          "finish_position": 3,
          "reset": 3,
          "structure": 1
        },
        "indicateurs": [
          {
            "nom": "bar_over_midfoot_topology",
            "etat": "bar_over_laces",
            "fait": "The barbell is positioned directly over the tongue/laces of the shoe (the midfoot).",
            "note": 3,
            "observation": null,
            "reponse_brute": "bar_over_laces"
          },
          {
            "nom": "shoulders_over_bar_gravity",
            "etat": "shoulder_stacked_over_bar",
            "fait": "The vertical plumb line from the shoulder strictly intersects the lifter's hand and the barbell. The arm is perfectly vertical (90 degrees to the floor).",
            "note": 3,
            "observation": null,
            "reponse_brute": "shoulder_stacked_over_bar"
          },
          {
            "nom": "hip_height_via_femur",
            "etat": "femur_angled_upward",
            "fait": "The femur creates a clear upward diagonal line from the knee to the hip, AND the torso also creates a diagonal line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "femur_angled_upward"
          },
          {
            "nom": "lumbar_at_setup",
            "etat": "lumbar_neutral_or_concave",
            "fait": "The lower back is extremely flat",
            "note": 3,
            "observation": "The lower back keeps its inward curve at the setup.",
            "reponse_brute": "lumbar_neutral_or_concave"
          },
          {
            "nom": "thoracic_at_setup",
            "etat": "thoracic_neutral_or_concave",
            "fait": "The physical contour of the upper back lies exactly flat against this imaginary straight line, or dips inward (creating a valley between the shoulder blades). The straight line is not crossed.",
            "note": 3,
            "observation": "The upper back is flat and set before the bar moves.",
            "reponse_brute": "thoracic_neutral_or_concave"
          },
          {
            "nom": "arms_tension_at_setup",
            "etat": "elbow_locked_prior",
            "fait": "The arm forms a strict 180-degree straight line BEFORE the plates leave the floor, and this exact 180-degree angle remains static during liftoff.",
            "note": 3,
            "observation": null,
            "reponse_brute": "elbow_locked_prior"
          },
          {
            "nom": "initiation_sequence",
            "etat": "torso_angle_decreases",
            "fait": "The torso angle becomes visibly smaller (more horizontal to the floor) between T0 and T1. The hips rise at a faster rate than the shoulders before the bar leaves the floor.",
            "note": 1,
            "observation": "The hips rise before the plates leave the floor; the torso tilts toward horizontal.",
            "reponse_brute": "torso_angle_decreases"
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
            "nom": "bar_path_at_knees_topology",
            "etat": "bar_deviates_forward",
            "fait": "A visual horizontal gap opens up between the trajectory of the bar and the shins/knees because the bar moves forward (away from the lifter) to avoid hitting the kneecaps.",
            "note": 1,
            "observation": null,
            "reponse_brute": "bar_deviates_forward"
          },
          {
            "nom": "bar_leg_daylight",
            "etat": "daylight_beyond_shoe",
            "fait": "Daylight appears between the bar and the legs, AND a vertical line dropped from the barbell lands strictly in front of the lifter's shoe (on the empty floor).",
            "note": 1,
            "observation": null,
            "reponse_brute": "daylight_beyond_shoe"
          },
          {
            "nom": "lumbar_geometry_delta",
            "etat": "lumbar_becomes_convex",
            "fait": "The lumbar segment adds flexion between T0 and T1, creating a new or more pronounced outward curve (rounding under load).",
            "note": 1,
            "observation": "The lower back rounds further as the bar passes the knees.",
            "reponse_brute": "lumbar_becomes_convex"
          },
          {
            "nom": "knee_valgus_tracking",
            "etat": "not_visible",
            "fait": "Pure side angle makes this tracking impossible.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
          },
          {
            "nom": "vertical_velocity_hitch",
            "etat": "continuous_positive_velocity",
            "fait": "The barbell's Y-axis height strictly increases on every single frame until lockout.",
            "note": 3,
            "observation": null,
            "reponse_brute": "continuous_positive_velocity"
          },
          {
            "nom": "lockout_extension",
            "etat": "full_180_extension",
            "fait": "Both the knee joint and the hip joint form a strict 180-degree straight line.",
            "note": 3,
            "observation": null,
            "reponse_brute": "full_180_extension"
          },
          {
            "nom": "sagittal_torso_angle",
            "etat": "torso_perpendicular",
            "fait": "The torso is perfectly perpendicular to the floor (90 degrees).",
            "note": 3,
            "observation": null,
            "reponse_brute": "torso_perpendicular"
          },
          {
            "nom": "shoulder_elevation_delta",
            "etat": "distance_remains_constant",
            "fait": "The vertical distance between the shoulder and the ear is strictly identical at T1 and T2.",
            "note": 3,
            "observation": null,
            "reponse_brute": "distance_remains_constant"
          },
          {
            "nom": "descent_hand_contact",
            "etat": "hands_maintain_contact",
            "fait": "The lifter's fingers remain wrapped around or in physical contact with the barbell until the exact frame the plates hit the floor.",
            "note": 3,
            "observation": null,
            "reponse_brute": "hands_maintain_contact"
          },
          {
            "nom": "rep_transition_velocity",
            "etat": "not_visible",
            "fait": "The video ends, this is the final repetition, or the floor contact is cut off.",
            "note": null,
            "observation": null,
            "reponse_brute": "not_visible"
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
      }
    ]
  },
  "modele": "gemini-3.5-flash"
}
;
