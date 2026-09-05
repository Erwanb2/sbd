"""A wide battery of stance features, computed from the cached landmarks."""
import json, numpy as np

I = dict(nose=0, l_sh=11, r_sh=12, l_el=13, r_el=14, l_wr=15, r_wr=16,
         l_pinky=17, r_pinky=18, l_index=19, r_index=20, l_thumb=21, r_thumb=22,
         l_hip=23, r_hip=24, l_kn=25, r_kn=26, l_an=27, r_an=28,
         l_heel=29, r_heel=30, l_toe=31, r_toe=32)

def ang(u, v):
    c = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))

def frame_features(fr, w, h):
    """~50 features for one frame. 2D names end in _2d, world-3D ones in _3d."""
    im = np.array(fr["im"]); wd = np.array(fr["wd"])
    ar = w / h
    p = lambda k: np.array([im[I[k], 0] * ar, im[I[k], 1]])       # aspect-corrected 2D
    P = lambda k: wd[I[k], :3]
    V = lambda k: float(im[I[k], 3])
    mid = lambda f, a, b: (f(a) + f(b)) / 2
    f = {}

    sh_c2, hip_c2, an_c2 = mid(p,"l_sh","r_sh"), mid(p,"l_hip","r_hip"), mid(p,"l_an","r_an")
    kn_c2 = mid(p,"l_kn","r_kn")
    torso2 = np.linalg.norm(sh_c2 - hip_c2)
    body2 = abs(an_c2[1] - sh_c2[1])
    if torso2 < 1e-6 or body2 < 1e-6: return None
    dx = lambda a, b: abs(p(a)[0] - p(b)[0])
    sh_sp2, hip_sp2 = dx("l_sh","r_sh"), dx("l_hip","r_hip")
    f["view"] = sh_sp2 / torso2
    f["view_hip"] = hip_sp2 / torso2

    # --- A. stance width, 2D, several normalisations
    for nm, num in (("ank", dx("l_an","r_an")), ("kne", dx("l_kn","r_kn")),
                    ("hee", dx("l_heel","r_heel")), ("toe", dx("l_toe","r_toe")),
                    ("wri", dx("l_wr","r_wr")), ("elb", dx("l_el","r_el"))):
        f[f"{nm}_over_sh_2d"] = num / max(sh_sp2, 1e-6)
        f[f"{nm}_over_torso_2d"] = num / torso2
        f[f"{nm}_over_body_2d"] = num / body2
    f["ank_over_hip_2d"] = dx("l_an","r_an") / max(hip_sp2, 1e-6)
    f["kne_over_ank_2d"] = dx("l_kn","r_kn") / max(dx("l_an","r_an"), 1e-6)
    f["wri_over_ank_2d"] = dx("l_wr","r_wr") / max(dx("l_an","r_an"), 1e-6)
    f["wri_over_kne_2d"] = dx("l_wr","r_wr") / max(dx("l_kn","r_kn"), 1e-6)

    # --- B. posture, 2D
    d = sh_c2 - hip_c2
    f["torso_lean"] = np.degrees(np.arctan2(abs(d[0]), abs(d[1])))
    f["hip_drop"] = (an_c2[1] - hip_c2[1]) / body2
    f["knee_height"] = (an_c2[1] - kn_c2[1]) / body2
    f["hip_over_knee"] = (an_c2[1] - hip_c2[1]) / max(an_c2[1] - kn_c2[1], 1e-6)
    f["shin_lean"] = np.mean([np.degrees(np.arctan2(abs((p(f"{s}_kn")-p(f"{s}_an"))[0]),
                                                    abs((p(f"{s}_kn")-p(f"{s}_an"))[1]))) for s in "lr"])
    f["knee_angle_2d"] = np.mean([ang(p(f"{s}_hip")-p(f"{s}_kn"), p(f"{s}_an")-p(f"{s}_kn")) for s in "lr"])
    f["hip_angle_2d"] = np.mean([ang(p(f"{s}_sh")-p(f"{s}_hip"), p(f"{s}_kn")-p(f"{s}_hip")) for s in "lr"])
    f["arm_lean"] = np.mean([np.degrees(np.arctan2(abs((p(f"{s}_wr")-p(f"{s}_sh"))[0]),
                                                   abs((p(f"{s}_wr")-p(f"{s}_sh"))[1]))) for s in "lr"])

    # --- C. 3D world, on the shoulder axis and on the ankle axis
    def axis_feats(u, tag):
        pr = lambda k: float(np.dot(P(k), u))
        g = {}
        sp = lambda a, b: abs(pr(a) - pr(b))
        sh = sp("l_sh","r_sh")
        for nm, ab in (("ank",("l_an","r_an")), ("kne",("l_kn","r_kn")), ("hee",("l_heel","r_heel")),
                       ("toe",("l_toe","r_toe")), ("wri",("l_wr","r_wr")), ("elb",("l_el","r_el")),
                       ("hip",("l_hip","r_hip"))):
            g[f"{nm}_{tag}"] = sp(*ab) / max(sh, 1e-6)
        alo, ahi = sorted([pr("l_an"), pr("r_an")]); klo, khi = sorted([pr("l_kn"), pr("r_kn")])
        g[f"wr_in_ank_{tag}"] = float(alo < pr("l_wr") < ahi and alo < pr("r_wr") < ahi)
        g[f"wr_in_kne_{tag}"] = float(klo < pr("l_wr") < khi and klo < pr("r_wr") < khi)
        g[f"el_in_kne_{tag}"] = float(klo < pr("l_el") < khi and klo < pr("r_el") < khi)
        g[f"kne_out_ank_{tag}"] = (khi - klo) / max(ahi - alo, 1e-6)
        return g
    sh3 = P("l_sh") - P("r_sh"); sh3[1] = 0
    if np.linalg.norm(sh3) > 1e-6: f.update(axis_feats(sh3/np.linalg.norm(sh3), "sh3d"))
    an3 = P("l_an") - P("r_an"); an3[1] = 0
    if np.linalg.norm(an3) > 1e-6: f.update(axis_feats(an3/np.linalg.norm(an3), "an3d"))

    # --- D. absolute 3D sizes, normalised by leg length (metric, view independent)
    leg = np.mean([np.linalg.norm(P(f"{s}_hip") - P(f"{s}_an")) for s in "lr"])
    for nm, ab in (("ank",("l_an","r_an")), ("kne",("l_kn","r_kn")), ("wri",("l_wr","r_wr")),
                   ("elb",("l_el","r_el")), ("toe",("l_toe","r_toe"))):
        f[f"{nm}_dist_over_leg"] = float(np.linalg.norm(P(ab[0]) - P(ab[1])) / max(leg, 1e-6))
    f["leg_m"] = float(leg)

    # --- E. thigh abduction: how far the thighs open away from the sagittal plane
    hipax = P("l_hip") - P("r_hip"); n = np.linalg.norm(hipax)
    if n > 1e-6:
        u = hipax / n
        f["thigh_abduction"] = float(np.mean([abs(90 - ang(P(f"{s}_kn") - P(f"{s}_hip"), u)) for s in "lr"]))
        f["shank_abduction"] = float(np.mean([abs(90 - ang(P(f"{s}_an") - P(f"{s}_kn"), u)) for s in "lr"]))
        f["arm_abduction"] = float(np.mean([abs(90 - ang(P(f"{s}_wr") - P(f"{s}_sh"), u)) for s in "lr"]))

    # --- F. feet: toes flared out is the sumo tell
    for s in "lr":
        v3 = P(f"{s}_toe") - P(f"{s}_heel"); v3[1] = 0
        if np.linalg.norm(v3) > 1e-6 and n > 1e-6:
            f.setdefault("foot_flare", []).append(abs(90 - ang(v3, u)))
        v2 = p(f"{s}_toe") - p(f"{s}_heel")
        shank = np.linalg.norm(p(f"{s}_kn") - p(f"{s}_an"))
        f.setdefault("foot_short_2d", []).append(float(np.linalg.norm(v2) / max(shank, 1e-6)))
    for k in ("foot_flare", "foot_short_2d"):
        if k in f: f[k] = float(np.mean(f[k]))

    # --- G. visibility, to weigh how much of this is guessed
    f["vis_legs"] = float(np.mean([V(k) for k in ("l_an","r_an","l_kn","r_kn")]))
    f["vis_arms"] = float(np.mean([V(k) for k in ("l_wr","r_wr","l_el","r_el")]))
    f["vis_far"] = float(min(np.mean([V(k) for k in ("l_an","l_kn","l_wr","l_el")]),
                             np.mean([V(k) for k in ("r_an","r_kn","r_wr","r_el")])))
    f["hip_y"] = float(hip_c2[1])
    f["t"] = fr["t"]
    return {k: float(v) for k, v in f.items()}

def clip_features(entry):
    """Aggregate per-frame features: at setup, over the bottom frames, and over the whole clip."""
    rows = [x for x in (frame_features(fr, entry["w"], entry["h"]) for fr in entry["frames"]) if x]
    strict = [r for r in rows if r["vis_legs"] > 0.4]
    rows = strict if len(strict) >= 4 else rows   # keep weak clips rather than dropping them
    if len(rows) < 3: return None
    rows.sort(key=lambda r: -r["hip_y"])
    bot = rows[:max(3, len(rows)//4)]
    keys = [k for k in rows[0] if k not in ("hip_y", "t")]
    out = {}
    for k in keys:
        out[f"setup_{k}"] = bot[0][k]
        out[f"bot_{k}"] = float(np.median([b[k] for b in bot]))
        out[f"all_{k}"] = float(np.median([r[k] for r in rows]))
        out[f"max_{k}"] = float(np.max([r[k] for r in rows]))
        out[f"min_{k}"] = float(np.min([r[k] for r in rows]))
    out["n_rows"] = len(rows)
    return out
