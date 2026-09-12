"""Le pipeline de prod, a UNE variable pres : des images annotees a la place des Parts video.

    cd backend
    uv run python eval/images_annotees.py [--clip pr_160.mp4] [--sans-appel] [--modele 3.5]
    uv run python eval/images_annotees.py --cles          # 6 images cles au lieu de la cadence

`--cles` ne garde que six images par repetition, choisies sur les phases de la pose :
la derniere du setup, trois reparties sur la tiree, la premiere du verrouillage, et la
derniere du segment. Le prompt le dit au modele.

Tout le reste est celui de `ai_service.analyze_movement` : meme pose, memes candidats,
meme cadence (`_cadence`, 24 im/s max, 720 images de budget), meme prompt a un mot pres
("frames" au lieu de "video segments"), meme modele, memes reglages HIGH/HIGH/0, meme
`rules.evalue`. Ce qui change : chaque image est lue ici, MediaPipe repasse dessus pour
le squelette, elle est recadree sur l'athlete et porte un bandeau `rep k - t s - PHASE`.

Sortie : eval/runs/<clip>_images_annotees.json (etats bruts sous
`debug.observations_brutes`, reglages sous `debug.appel`), et les
images dans extracted_frames/annotees/<clip>/ pour verifier a l'oeil ce que le modele
a recu. `--sans-appel` s'arrete la, sans depenser un appel.
"""

import argparse
import json
import os
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(ICI)
sys.path.insert(0, BACKEND)

import pose_analysis as pa                          # noqa: E402
import rules                                        # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
RUNS = os.path.join(ICI, "runs")
SORTIE = os.path.join(BACKEND, "extracted_frames", "annotees")

# Les segments du squelette, sur les memes reperes que l'overlay du front.
OS = [("l_sh", "r_sh"), ("l_sh", "l_hip"), ("r_sh", "r_hip"), ("l_hip", "r_hip"),
      ("l_sh", "l_el"), ("l_el", "l_wr"), ("r_sh", "r_el"), ("r_el", "r_wr"),
      ("l_hip", "l_kn"), ("l_kn", "l_an"), ("r_hip", "r_kn"), ("r_kn", "r_an"),
      ("l_an", "l_heel"), ("l_heel", "l_toe"), ("l_an", "l_toe"),
      ("r_an", "r_heel"), ("r_heel", "r_toe"), ("r_an", "r_toe")]
MARGE_CADRE = 0.25          # fraction de la boite des reperes ajoutee de chaque cote
COULEUR = {"SETUP": (90, 200, 255), "PULL": (80, 230, 120), "LOCKOUT": (255, 210, 60),
           "DESCENT": (255, 120, 120)}


def _phase_par_image(poses, cote):
    """Une etiquette par image du segment, lue sur l'extension hanche+genou."""
    ph = pa._phases(poses, cote)
    n = len(poses)
    if not ph:
        return ["?"] * n
    ext, lo, lk = ph["ext"], ph["liftoff"], ph["lockout"]
    # fin du verrouillage : premier instant apres le sommet ou l'extension retombe
    # nettement ; s'il n'y en a pas, il reste debout jusqu'a la fin du segment.
    fin_lk = n
    for j in range(lk + 1, n):
        if ext[j] < ext[lk] - 8.0:
            fin_lk = j
            break
    out = []
    for i in range(n):
        if i < lo:
            out.append("SETUP")
        elif i < lk:
            out.append("PULL")
        elif i < fin_lk:
            out.append("LOCKOUT")
        else:
            out.append("DESCENT")
    return out


def _cadre(poses, w, h):
    """Un seul recadrage pour toute la repetition : l'union des boites des reperes.

    Recadrer image par image ferait sauter le cadre a chaque image, et le modele ne
    pourrait plus juger un deplacement (barre, hanches) d'une image a l'autre.
    """
    pts = np.concatenate([f["im"][:, :2][f["im"][:, 3] > 0.3] for f in poses])
    if len(pts) == 0:
        return 0, 0, w, h
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    mx, my = (x1 - x0) * MARGE_CADRE, (y1 - y0) * MARGE_CADRE
    return (int(max(0, (x0 - mx) * w)), int(max(0, (y0 - my) * h)),
            int(min(w, (x1 + mx) * w)), int(min(h, (y1 + my) * h)))


def _police(taille):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, taille)
    return ImageFont.load_default()


def _annote(f, frame_bgr, cadre, rep_k, phase):
    img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    w, h = img.size
    p = lambda k: (f["im"][pa.L[k], 0] * w, f["im"][pa.L[k], 1] * h)
    vis = lambda k: f["im"][pa.L[k], 3] > 0.3
    ep = max(2, int(h / 250))
    for a, b in OS:
        if vis(a) and vis(b):
            d.line([p(a), p(b)], fill=(0, 255, 120), width=ep)
    for k in pa.KEYS_SQUELETTE:
        if vis(k):
            x, y = p(k)
            d.ellipse([x - ep * 1.5, y - ep * 1.5, x + ep * 1.5, y + ep * 1.5],
                      fill=(255, 60, 60))
    img = img.crop(cadre)
    # bandeau en haut du recadrage
    d = ImageDraw.Draw(img)
    taille = max(14, img.height // 28)
    police = _police(taille)
    texte = f"rep {rep_k}  |  {f['t']:.2f} s  |  {phase}"
    d.rectangle([0, 0, img.width, int(taille * 1.6)], fill=(0, 0, 0))
    d.text((taille * 0.4, taille * 0.25), texte, fill=COULEUR.get(phase, (255, 255, 255)),
           font=police)
    return img


def images_du_segment(path, c, fps_env, rep_k, cote, dossier):
    """Les images annotees d'un candidat, aux memes instants que le Part video."""
    n, fps_src = pa._probe(path)
    ts = np.arange(c["debut_s"], c["fin_s"], 1.0 / fps_env)
    idx = sorted(set(int(round(t * fps_src)) for t in ts if t * fps_src < n))
    frames, fps_src = pa._read_frames(path, idx)
    poses = pa._detect(frames, fps_src)
    par_i = {f["i"]: f for f in poses}
    if not poses:
        return []
    cadre = _cadre(poses, poses[0]["w"], poses[0]["h"])
    phases = _phase_par_image(poses, cote)
    phase_par_i = {f["i"]: ph for f, ph in zip(poses, phases)}
    out = []
    for i, t, fr in frames:
        f = par_i.get(i)
        if f is None:
            # pas de pose sur cette image : on l'envoie quand meme, sans squelette,
            # pour garder la cadence — sinon le modele verrait un saut temporel.
            f = dict(i=i, t=t, w=fr.shape[1], h=fr.shape[0], im=np.zeros((33, 4)))
            ph = "?"
        else:
            ph = phase_par_i[i]
        img = _annote(f, fr, cadre, rep_k, ph)
        nom = os.path.join(dossier, f"rep{rep_k}_{t:06.2f}s.jpg")
        img.save(nom, quality=88)
        out.append((t, ph, nom))
    return out


def _images_cles(imgs):
    """Six images par repetition : fin du setup, trois sur la tiree, verrouillage, fin."""
    phases = [ph for _, ph, _ in imgs]
    setup = [i for i, p in enumerate(phases) if p == "SETUP"]
    pull = [i for i, p in enumerate(phases) if p == "PULL"]
    lock = [i for i, p in enumerate(phases) if p == "LOCKOUT"]
    choix = []
    if setup:
        choix.append(setup[-1])
    if pull:
        choix += [pull[int(round(k * (len(pull) - 1)))] for k in (0.25, 0.5, 0.75)]
    if lock:
        choix.append(lock[0])
    choix.append(len(imgs) - 1)
    return [imgs[i] for i in sorted(set(choix))]


def _prompt_images(variante, n, cles=False):
    """Le prompt de prod, ou seule la description du support change."""
    import ai_service
    p = ai_service._prompt(variante, n)
    support = (
        "frames are a handful of key instants chosen by the detector (end of setup, three\n"
        "points of the pull, lockout, end); each carries the detector's skeleton overlay\n"
        "and a banner with the repetition number, the timestamp and the detector's phase guess."
        if cles else
        "frames are sampled at a constant rate; each carries the detector's skeleton overlay\n"
        "and a banner with the repetition number, the timestamp and the detector's phase guess.")
    return p.replace(
        f"You are given {n} video segments, in chronological order. Each segment is ONE candidate\n"
        "repetition, cut by a pose detector that sees the body but NOT the bar.",
        f"You are given {n} sequences of frames, in chronological order. Each sequence is ONE\n"
        "candidate repetition, cut by a pose detector that sees the body but NOT the bar. The\n"
        + support,
    ).replace("one per segment", "one per sequence").replace("this segment", "this sequence")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", default="pr_160.mp4")
    ap.add_argument("--modele", default="3.5")
    ap.add_argument("--sans-appel", action="store_true")
    ap.add_argument("--suffixe", default=None)
    ap.add_argument("--cles", action="store_true", help="6 images cles par rep")
    args = ap.parse_args()
    suffixe = args.suffixe or ("images_cles" if args.cles else "images_annotees")

    path = os.path.join(DATA, args.clip)
    nom = os.path.splitext(args.clip)[0]
    dossier = os.path.join(SORTIE, nom)
    os.makedirs(dossier, exist_ok=True)
    for f in os.listdir(dossier):
        os.remove(os.path.join(dossier, f))

    t0 = time.time()
    pose = pa.analyse(path)
    if not pose.get("ok"):
        sys.exit(f"pose : {pose.get('raison')}")
    candidats = pose["reps"]
    print(f"pose : {pose['variante']}, {len(candidats)} candidat(s), "
          f"{time.time() - t0:.1f}s", file=sys.stderr)

    import ai_service
    fps_env = ai_service._cadence(candidats)
    # `_phases` choisit le cote camera sur les poses du segment : les etiquettes de
    # phase n'ont pas besoin de la precision du cote decide sur tout le clip.
    cote = None
    groupes = []
    for k, c in enumerate(candidats, 1):
        imgs = images_du_segment(path, c, fps_env, k, cote, dossier)
        if args.cles:
            imgs = _images_cles(imgs)
            print("rep %d : images cles " % k + ", ".join(f"{t:.2f}s {ph}" for t, ph, _ in imgs),
                  file=sys.stderr)
        groupes.append(imgs)
        phases = [ph for _, ph, _ in imgs]
        print(f"rep {k} : {c['debut_s']}-{c['fin_s']} s, {len(imgs)} images a {fps_env} im/s, "
              f"phases " + ", ".join(f"{p}={phases.count(p)}" for p in
                                     ("SETUP", "PULL", "LOCKOUT", "DESCENT", "?")),
              file=sys.stderr)
    total = sum(len(g) for g in groupes)
    print(f"{total} images dans {dossier}", file=sys.stderr)
    if args.sans_appel:
        return

    from google.genai import types
    from schemas import SCHEMAS
    variante = pose["variante"]
    modele = ai_service.MODELES_ANALYSE.get(args.modele, ai_service.MODELES_ANALYSE["3.5"])
    prompt = _prompt_images(variante, len(candidats), args.cles)
    contenus = []
    for k, imgs in enumerate(groupes, 1):
        contenus.append(f"Candidate repetition {k} ({len(imgs)} frames):")
        for _, _, chemin in imgs:
            with open(chemin, "rb") as fh:
                contenus.append(types.Part.from_bytes(data=fh.read(), mime_type="image/jpeg"))
    contenus.append(prompt)

    t1 = time.time()
    reponse, usage = ai_service._appelle(modele, contenus, SCHEMAS[variante],
                                         f"analyse {variante} (images annotees)")
    observations = reponse.parsed.model_dump(mode="json")
    resultat = rules.evalue(pose, observations)
    resultat["modele"] = modele
    resultat["debug"]["appel"] = {
        "modele": modele, "repli": False, **ai_service.REGLAGES_ANALYSE,
        "support": ("6 images cles annotees" if args.cles else "images annotees a la cadence")
                   + " (squelette + recadrage + bandeau rep/temps/phase)",
        "fps": None if args.cles else fps_env, "nb_images": total,
        "segments": [{"debut_s": c["debut_s"], "fin_s": c["fin_s"]} for c in candidats],
        "prompt": prompt, "usage": ai_service._usage_public(usage),
        "duree_appel_s": round(time.time() - t1, 1),
    }
    sortie = os.path.join(RUNS, f"{nom}_{suffixe}.json")
    with open(sortie, "w") as fh:
        json.dump(resultat, fh, ensure_ascii=False, indent=2)
    print(f"{sortie} : {resultat['note_sur_20']}/20, usage {resultat['debug']['appel']['usage']}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
