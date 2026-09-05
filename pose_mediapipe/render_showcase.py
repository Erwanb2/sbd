"""Rendu 'vitrine' de MediaPipe Pose : squelette neon, glow, trajectoire de
barre, scan d'ouverture, recadre sur le lifter. Sort un mp4 H.264 navigateur
+ un JSON de mesures par frame pour le HUD HTML.
Passe 1 = detection (on garde les landmarks), passe 2 = dessin + crop."""
import sys, os, json
import cv2, numpy as np, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
import imageio_ffmpeg

src, model, dst = sys.argv[1], sys.argv[2], sys.argv[3]

I = dict(l_sh=11, r_sh=12, l_el=13, r_el=14, l_wr=15, r_wr=16,
         l_hip=23, r_hip=24, l_kn=25, r_kn=26, l_an=27, r_an=28,
         l_heel=29, r_heel=30, l_toe=31, r_toe=32)
CONN = [("l_sh","r_sh"),("l_hip","r_hip"),("l_sh","l_hip"),("r_sh","r_hip"),
        ("l_sh","l_el"),("l_el","l_wr"),("r_sh","r_el"),("r_el","r_wr"),
        ("l_hip","l_kn"),("l_kn","l_an"),("r_hip","r_kn"),("r_kn","r_an"),
        ("l_an","l_heel"),("l_heel","l_toe"),("l_an","l_toe"),
        ("r_an","r_heel"),("r_heel","r_toe"),("r_an","r_toe")]
KEYS = list(I)
EMERALD = (52, 235, 145)      # RGB, on encode en RGB
CYAN    = (110, 240, 255)
GOLD    = (251, 191, 36)
WHITE   = (255, 255, 255)

# ---------- passe 1 : detection
lmk = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model),
    running_mode=vision.RunningMode.VIDEO, num_poses=1,
    min_pose_detection_confidence=0.4, min_pose_presence_confidence=0.4,
    min_tracking_confidence=0.4))
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
poses, i, miss = [], 0, 0
while True:
    ok, fr = cap.read()
    if not ok: break
    res = lmk.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                        data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)),
                               int(i * 1000 / fps))
    if res.pose_landmarks:
        lm = res.pose_landmarks[0]
        poses.append({k: (lm[I[k]].x * W, lm[I[k]].y * H) for k in KEYS})
    else:
        poses.append(None); miss += 1
    i += 1
cap.release()
n = i
print(f"passe 1 : {n} frames, {miss} sans detection")

# ---------- cadrage : union des poses + marge, ramene au ratio d'origine
pts = np.array([p[k] for p in poses if p for k in KEYS])
x0, y0 = pts[:, 0].min(), pts[:, 1].min()
x1, y1 = pts[:, 0].max(), pts[:, 1].max()
mx, my = (x1 - x0) * 0.30, (y1 - y0) * 0.14
x0, x1, y0, y1 = x0 - mx, x1 + mx, y0 - my, y1 + my
ar = W / H
cw, ch = x1 - x0, y1 - y0
if cw / ch > ar: ch = cw / ar
else: cw = ch * ar
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
x0 = int(max(0, min(W - cw, cx - cw / 2))); y0 = int(max(0, min(H - ch, cy - ch / 2)))
cw, ch = int(min(cw, W - x0)) // 2 * 2, int(min(ch, H - y0)) // 2 * 2
print(f"crop {cw}x{ch} @ {x0},{y0}  (source {W}x{H})")

UP = 2                                   # le crop est petit : on suréchantillonne pour l'écran
ow, oh = (cw * UP // 2) * 2, (ch * UP // 2) * 2
scale = ow / 720.0
SCAN = int(fps * 0.9)
TRAIL = int(fps * 1.5)
writer = imageio_ffmpeg.write_frames(dst, (ow, oh), fps=fps, codec="libx264",
                                     quality=7, macro_block_size=1,
                                     output_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
writer.send(None)

# ---------- passe 2 : dessin
cap = cv2.VideoCapture(src)
trail, meas = [], []
for i in range(n):
    ok, fr = cap.read()
    if not ok: break
    fr = cv2.cvtColor(fr[y0:y0 + ch, x0:x0 + cw], cv2.COLOR_BGR2RGB)
    fr = cv2.resize(fr, (ow, oh), interpolation=cv2.INTER_CUBIC)
    base = (fr * 0.70).astype(np.uint8)
    ov = np.zeros_like(fr)
    p = poses[i]

    if p:
        pt = lambda k: (int((p[k][0] - x0) * ow / cw), int((p[k][1] - y0) * oh / ch))
        quad = np.array([pt("l_sh"), pt("r_sh"), pt("r_hip"), pt("l_hip")], np.int32)
        fill = base.copy(); cv2.fillPoly(fill, [quad], (40, 120, 80))
        base = cv2.addWeighted(base, 0.80, fill, 0.20, 0)

        for a, b in CONN:
            cv2.line(ov, pt(a), pt(b), EMERALD, max(2, int(4 * scale)), cv2.LINE_AA)
        for k in KEYS:
            cv2.circle(ov, pt(k), max(2, int(4 * scale)), CYAN, -1, cv2.LINE_AA)

        wr = ((pt("l_wr")[0] + pt("r_wr")[0]) // 2, (pt("l_wr")[1] + pt("r_wr")[1]) // 2)
        trail.append(wr)
        del trail[:-TRAIL]        # traine glissante : sur plusieurs reps, tout garder fait un gribouillis
        for j in range(1, len(trail)):
            a = j / len(trail)
            cv2.line(ov, trail[j - 1], trail[j], tuple(int(c * (0.3 + 0.7 * a)) for c in GOLD),
                     max(2, int(3 * scale)), cv2.LINE_AA)

        q = lambda k: np.array([p[k][0] / H, p[k][1] / H])   # normalise, ratio conserve
        sh_c, hip_c = (q("l_sh") + q("r_sh")) / 2, (q("l_hip") + q("r_hip")) / 2
        d = sh_c - hip_c
        meas.append(dict(t=round(i / fps, 3),
                         torso=round(float(np.degrees(np.arctan2(abs(d[0]), abs(d[1])))), 1),
                         bar=round(float(1 - (wr[1] / oh)), 3),
                         bx=round(float(wr[0] / ow), 4)))

    ov = np.clip(cv2.GaussianBlur(ov, (0, 0), 6 * scale).astype(np.float32) * 1.45 + ov, 0, 255)
    out = np.clip(base.astype(np.float32) + ov, 0, 255).astype(np.uint8)
    if p:
        for k in KEYS:
            cv2.circle(out, pt(k), max(1, int(1.6 * scale)), WHITE, -1, cv2.LINE_AA)

    if i < SCAN:                       # scan d'ouverture : overlay revele de haut en bas
        y = int(oh * (i + 1) / SCAN)
        out[y:] = (fr[y:] * 0.70).astype(np.uint8)
        cv2.line(out, (0, y), (ow, y), CYAN, max(1, int(2 * scale)), cv2.LINE_AA)

    writer.send(np.ascontiguousarray(out))
cap.release(); writer.close()

json.dump(dict(fps=fps, w=ow, h=oh, frames=meas),
          open(os.path.splitext(dst)[0] + ".json", "w"), separators=(",", ":"))
print(f"passe 2 : -> {dst} ({ow}x{oh})")
