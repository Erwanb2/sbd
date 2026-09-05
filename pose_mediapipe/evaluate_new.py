"""Score new clips against every candidate sumo/conventional rule at once.

    uv run --with mediapipe==0.10.21,opencv-python-headless,numpy python evaluate_new.py \
        ../data/nouveau1.mp4 ../data/nouveau2.mp4

Prints, per clip, the raw measurements and what each candidate model says. Give the true
label with --truth sumo|conv (applies to all clips passed) to get a tally at the end.

The rules and thresholds come from regles.json, fitted on the 27 clips of 2026-09-04.
Every one of them scores 100% on those 27, which is exactly why they need new clips.
"""
import argparse, json, os, sys, urllib.request
import cv2, numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from features import frame_features, clip_features
from zfeats import clip_z

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task")

def get_model(path):
    if not os.path.exists(path):
        print(f"telechargement du modele -> {path}")
        urllib.request.urlretrieve(MODEL_URL, path)
    return path

def landmarks(video, model, n=30):
    """Sample n frames and keep every landmark, exactly like the study did."""
    lmk = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model), running_mode=vision.RunningMode.VIDEO,
        num_poses=1, min_pose_detection_confidence=0.3, min_pose_presence_confidence=0.3,
        min_tracking_confidence=0.3))
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rot = rotation_of(video)
    want = set(np.linspace(tot * 0.05, tot * 0.95, n).astype(int)); frames = []; i = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i in want:
            if rot: fr = cv2.rotate(fr, rot); h, w = fr.shape[:2]
            r = lmk.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                              data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)), int(i * 1000 / fps))
            if r.pose_landmarks:
                lm = r.pose_landmarks[0]; wl = r.pose_world_landmarks[0]
                frames.append(dict(t=i / fps,
                    im=[[p.x, p.y, p.z, p.visibility] for p in lm],
                    wd=[[p.x, p.y, p.z] for p in wl]))
        i += 1
    cap.release()
    return dict(w=w, h=h, fps=fps, n_frames=tot, frames=frames)

def rotation_of(path):
    """OpenCV ignores the mp4 rotation flag; read it from the tkhd matrix ourselves."""
    import struct, math
    def walk(f, end):
        while f.tell() < end:
            st = f.tell(); hdr = f.read(8)
            if len(hdr) < 8: return
            size, typ = struct.unpack(">I4s", hdr); typ = typ.decode("latin1")
            if size == 1: size = struct.unpack(">Q", f.read(8))[0]
            if size < 8: return
            if typ in ("moov", "trak", "mdia"):
                yield from walk(f, st + size)
            elif typ == "tkhd":
                data = f.read(size - (f.tell() - st))
                m = struct.unpack(">9i", data[-44:-8])
                yield round(math.degrees(math.atan2(m[1] / 65536.0, m[0] / 65536.0))) % 360
            f.seek(st + size)
    try:
        with open(path, "rb") as f:
            f.seek(0, 2); end = f.tell(); f.seek(0)
            for r in walk(f, end):
                if r == 90: return cv2.ROTATE_90_CLOCKWISE
                if r == 270: return cv2.ROTATE_90_COUNTERCLOCKWISE
                if r == 180: return cv2.ROTATE_180
    except Exception:
        pass
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--truth", choices=["sumo", "conv"], help="vraie etiquette des clips passes")
    ap.add_argument("--model", default=os.path.join(HERE, "pose_landmarker_heavy.task"))
    a = ap.parse_args()
    model = get_model(a.model)
    R = json.load(open(os.path.join(HERE, "regles.json")))
    MODELS = ["largeur seule", "largeur + abstention", "CASCADE largeur -> profondeur"]
    tally = [0] * len(MODELS); seen = 0

    for v in a.videos:
        lm = landmarks(v, model)
        c = clip_features(lm); cz = clip_z(lm)
        print(f"\n=== {os.path.basename(v)} ===")
        if c is None:
            print("  aucune pose exploitable"); continue
        seen += 1
        largeur = c[R["mesure"]]; conf = c[R["confiance"]]
        prof = cz[R["profondeur"]] if cz else None
        print(f"  view {c['all_view']:.2f}   vis_jambes {c['all_vis_legs']:.2f}   "
              f"largeur {largeur:.2f}   confiance {conf:.4f}   "
              f"profondeur main/genou {prof:+.3f}" if prof is not None else
              f"  largeur {largeur:.2f}   confiance {conf:.4f}   profondeur indisponible")

        simple = "sumo" if largeur >= R["seuil_mesure"] else "conventionnel"
        fiable = conf >= R["seuil_confiance"]
        doubt = simple if fiable else "DOUTE"
        if fiable:
            cascade = simple
        elif prof is None:
            cascade = "DOUTE"
        else:
            # main derriere le genou (cote camera) = bras entre les jambes = sumo
            cascade = "sumo" if prof >= R["seuil_profondeur"] else "conventionnel"

        for k, (nm, verd) in enumerate(zip(MODELS, [simple, doubt, cascade])):
            mark = ""
            if a.truth:
                if verd == "DOUTE":
                    mark = "  (abstention)"
                else:
                    good = (verd == "sumo") == (a.truth == "sumo")
                    tally[k] += good; mark = "  ok" if good else "  RATE"
            print(f"    {nm:34} {verd:14}{mark}")

    if a.truth and seen:
        print(f"\n=== score sur {seen} clips (verite = {a.truth}) ===")
        for nm, t in zip(MODELS, tally):
            print(f"  {nm:34} {t}/{seen}")


if __name__ == "__main__":
    main()
