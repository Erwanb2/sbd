"""Render a clip with the MediaPipe Pose overlay + live stance readouts."""
import sys, os, cv2, numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pose_feats2 import CONN, I, feats

src, model, dst = sys.argv[1], sys.argv[2], sys.argv[3]
lmk = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model),
    running_mode=vision.RunningMode.VIDEO, num_poses=1,
    min_pose_detection_confidence=0.4, min_pose_presence_confidence=0.4,
    min_tracking_confidence=0.4))
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
vw = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
i, miss = 0, 0
while True:
    ok, fr = cap.read()
    if not ok: break
    res = lmk.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                        data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)),
                               int(i * 1000 / fps))
    if res.pose_landmarks:
        lm = res.pose_landmarks[0]
        pt = lambda k: (int(lm[k].x * w), int(lm[k].y * h))
        for a, b in CONN: cv2.line(fr, pt(a), pt(b), (0,255,120), max(2, w//400), cv2.LINE_AA)
        for k in set(sum(([a,b] for a,b in CONN), [])):
            cv2.circle(fr, pt(k), max(3, w//250), (0,90,255), -1, cv2.LINE_AA)
        for k in (I["l_an"], I["r_an"]):
            cv2.line(fr, (pt(k)[0], 0), (pt(k)[0], h), (255,220,0), max(1, w//600), cv2.LINE_AA)
        cv2.line(fr, pt(I["l_sh"]), pt(I["r_sh"]), (255,0,200), max(2, w//500), cv2.LINE_AA)
        f = feats(res, w, h)
        if f:
            txt = [f"view {f['view']:.2f}  (1=face, 0=profil)",
                   f"chevilles/epaules 2D {f['stance2d']:.2f}   3D {f['stance3d']:.2f}",
                   f"poignets entre chevilles: {'OUI' if f['inside3d'] else 'non'}",
                   f"torse {f['torso_lean']:.0f}deg de la verticale"]
            s = w / 900
            cv2.rectangle(fr, (0,0), (w, int(30+34*s*len(txt))), (0,0,0), -1)
            for j, t in enumerate(txt):
                cv2.putText(fr, t, (int(12*s), int((30+34*j)*s)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.75*s, (255,255,255), max(1, int(2*s)), cv2.LINE_AA)
    else:
        miss += 1
    vw.write(fr); i += 1
cap.release(); vw.release()
print(f"{i} frames, {miss} sans detection -> {dst}")
