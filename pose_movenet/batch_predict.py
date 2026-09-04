"""Rejoue app.py du repo weggry/deadlift-classifier sur des fichiers mp4.

app.py est une boucle webcam interactive : elle lit cv2.VideoCapture(0), attend qu'un
detecteur d'angle de hanche declenche l'enregistrement d'UNE repetition, puis attend
la touche 'P'. Ici on remplace la webcam par un fichier, on segmente TOUTES les reps
du clip, et on predit sur chacune. Le pretraitement par frame est identique a app.py.
"""
import argparse, json, math, os, struct, sys
import numpy as np
import cv2

REPO = os.environ.get("DLC_REPO", "/home/erwan/deadlift-classifier")
sys.path.insert(0, REPO)

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf
from utils import (movenet, run_inference, init_crop_region, determine_crop_region,
                   return_angle, DeadliftRepDetector, interpolate_kps)

INPUT_SIZE = 256  # thunder
MIN_CONF = 0.1
BASE_CLASSES = {0: "Romanian", 1: "Sumo", 2: "Conventional"}
CONV_CLASSES = {0: "Correct", 1: "Early hip elevation", 2: "Overextension", 3: "Rounded back"}
SUMO_CLASSES = CONV_CLASSES
RDL_CLASSES = {0: "Correct", 1: "Overextension", 2: "Rounded back"}


def rotation_of(path):
    """cv2 ignore le flag de rotation mp4 ; on lit la matrice tkhd nous-memes.
    Repris de pose_mediapipe/evaluate_new.py."""
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


# Les clips d'entrainement vont du bas de la rep jusqu'apres la redescente. La fenetre
# brute du detecteur s'arrete des le retour sous le seuil et tronque cette fin : sur les
# 550 tableaux du repo, la fenetre brute tombe a 34% (tout devient "Romanian") alors que
# la meme fenetre etendue de 30% rend 98.9%. D'ou EXTEND.
EXTEND = 0.30


class AllRepsDetector:
    """Meme logique d'angle que DeadliftRepDetector mais ne s'arrete pas a la 1re rep.

    Le detecteur d'origine passe done_recording=True et se fige. Ici on le reinstancie
    apres chaque rep pour balayer tout le clip. On memorise les bornes, pas les frames,
    pour pouvoir etendre la fenetre ensuite.
    """
    def __init__(self, start=85, top=160, end=85, add_frames=2):
        self.args = (start, top, end, add_frames)
        self.det = DeadliftRepDetector(*self.args)
        self.spans, self.cur = [], []

    def update(self, a1, a2, i):
        if self.det.update(a1, a2):
            self.cur.append(i)
        if self.det.done_recording:
            if len(self.cur) >= 10:
                self.spans.append((self.cur[0], self.cur[-1] + 1))
            self.cur = []
            self.det = DeadliftRepDetector(*self.args)

    def windows(self, kps):
        out = []
        for s, e in self.spans:
            e2 = min(len(kps), int(e + EXTEND * (e - s)))
            out.append(kps[s:e2])
        return out


def extract_keypoints(path, rotate=True, max_frames=None):
    """Boucle par frame identique a app.py : resize_with_pad 256 + crop region suivie."""
    rot = rotation_of(path) if rotate else None
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    ok, first = cap.read()
    if not ok:
        raise RuntimeError(f"empty video {path}")
    if rot is not None:
        first = cv2.rotate(first, rot)
    fh, fw = first.shape[:2]
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # NB: app.py passe (fh, fw) ici, mais l'image croppee est le carre pade INPUT_SIZE.
    # Les tableaux de keypoints du repo se reproduisent avec les dimensions du carre
    # (coord MAE 0.0002 contre 0.005 avec fh/fw) : app.py publie est incoherent sur ce point.
    crop_region = init_crop_region(INPUT_SIZE, INPUT_SIZE)
    detector = AllRepsDetector()
    all_kps, angles = [], []
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if rot is not None:
            frame = cv2.rotate(frame, rot)
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = tf.image.resize_with_pad(img, INPUT_SIZE, INPUT_SIZE)
        kws = run_inference(movenet, img, crop_region,
                            crop_size=[INPUT_SIZE, INPUT_SIZE], interpreter=INTERP)
        crop_region = determine_crop_region(kws, image_height=INPUT_SIZE, image_width=INPUT_SIZE)
        a1, a2 = return_angle(kws, MIN_CONF)
        kp = kws[0, 0].copy()
        all_kps.append(kp)
        angles.append((a1, a2))
        detector.update(a1, a2, n)
        n += 1
        if max_frames and n >= max_frames:
            break
    cap.release()
    kps = np.array(all_kps)
    return kps, detector.windows(kps), angles, (fw, fh)


def predict(kps_seq, models):
    arr = np.expand_dims(interpolate_kps(np.asarray(kps_seq)), axis=0)
    base = models["base"].predict(arr, verbose=0)[0]
    idx = int(np.argmax(base))
    label = BASE_CLASSES[idx]
    if label == "Conventional":
        sub, table = models["conv"].predict(arr, verbose=0)[0], CONV_CLASSES
    elif label == "Sumo":
        sub, table = models["sumo"].predict(arr, verbose=0)[0], SUMO_CLASSES
    else:
        sub, table = models["rdl"].predict(arr, verbose=0)[0], RDL_CLASSES
    return {
        "style": label,
        "style_probs": {BASE_CLASSES[i]: round(float(p), 4) for i, p in enumerate(base)},
        "form": table[int(np.argmax(sub))],
        "form_conf": round(float(np.max(sub)), 4),
    }


def load_models():
    import keras
    p = lambda *a: os.path.join(REPO, *a)
    return {
        "base": keras.models.load_model(p("Base Classifications", "LSTM Base Classification", "CNN-LSTM base.keras")),
        "conv": keras.models.load_model(p("Subclass Conv Classifications", "LSTM Conv Subclass Classification", "LSTM Conv Classifier.keras")),
        "sumo": keras.models.load_model(p("Subclass Sumo Classifications", "LSTM S Subclass Classification", "LSTM Sumo Classifier.keras")),
        "rdl": keras.models.load_model(p("Subclass Romanian Classifications", "LSTM R Subclass Classification", "LSTM R Classifier.keras")),
    }


INTERP = None

def main():
    global INTERP
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-rotate", action="store_true")
    ap.add_argument("--dump-kps", default=None, help="repertoire ou ecrire les kps bruts .npy")
    args = ap.parse_args()

    INTERP = tf.lite.Interpreter(os.path.join(REPO, "MoveNet Models", "singlepose_thunder_tflite_f16.tflite"))
    INTERP.allocate_tensors()
    models = load_models()

    results = []
    for path in args.videos:
        name = os.path.basename(path)
        try:
            kps, reps, angles, dims = extract_keypoints(path, rotate=not args.no_rotate)
        except Exception as e:
            print(f"{name}: ERREUR {e}", flush=True)
            results.append({"file": name, "error": str(e)})
            continue
        if args.dump_kps:
            os.makedirs(args.dump_kps, exist_ok=True)
            np.save(os.path.join(args.dump_kps, name.replace(".mp4", ".npy")), kps)

        rec = {"file": name, "dims": dims, "n_frames": len(kps), "n_reps": len(reps)}
        rec["per_rep"] = [predict(r, models) for r in reps]
        # Repli quand le detecteur d'angle ne boucle aucune rep : tout le clip.
        rec["whole_clip"] = predict(kps, models)
        if rec["per_rep"]:
            votes = {}
            for r in rec["per_rep"]:
                votes[r["style"]] = votes.get(r["style"], 0) + 1
            rec["style_vote"] = max(votes, key=votes.get)
            rec["votes"] = votes
            rec["style_first_rep"] = rec["per_rep"][0]["style"]
        else:
            rec["style_vote"] = rec["whole_clip"]["style"]
            rec["style_first_rep"] = rec["whole_clip"]["style"]
        print(f"{name}: {rec['n_frames']}f {len(reps)}rep -> vote={rec['style_vote']} "
              f"clip={rec['whole_clip']['style']} {rec['whole_clip']['style_probs']}", flush=True)
        results.append(rec)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n-> {args.out}")


if __name__ == "__main__":
    main()
