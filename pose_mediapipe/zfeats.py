"""Everything the depth axis can say about sumo vs conventional.

MediaPipe gives two depths: world z (metres, relative to the hip centre) and image z
(relative to the hips, roughly the same scale as x). Smaller = closer to the camera.
The human cue - "is the forearm in front of the knee or behind it" - is a depth ORDER,
so most features here are signed differences, plus the spreads and stabilities that say
whether the model believes there is any depth at all.
"""
import json, numpy as np

I = dict(nose=0, l_sh=11, r_sh=12, l_el=13, r_el=14, l_wr=15, r_wr=16,
         l_idx=19, r_idx=20, l_hip=23, r_hip=24, l_kn=25, r_kn=26,
         l_an=27, r_an=28, l_heel=29, r_heel=30, l_toe=31, r_toe=32)

def frame_z(fr):
    im = np.array(fr["im"]); wd = np.array(fr["wd"])
    W = lambda k: wd[I[k]]           # x, y, z monde
    Z = lambda k: float(wd[I[k], 2])
    z = lambda k: float(im[I[k], 2])  # z image
    V = lambda k: float(im[I[k], 3])
    f = {}
    # echelles de normalisation
    leg = float(np.mean([np.linalg.norm(W(f"{s}_hip") - W(f"{s}_an")) for s in "lr"])) + 1e-6
    torso = float(np.linalg.norm((W("l_sh")+W("r_sh"))/2 - (W("l_hip")+W("r_hip"))/2)) + 1e-6
    zext = float(np.ptp(wd[:, 2])) + 1e-6                    # etendue de profondeur du corps
    zext_im = float(np.ptp(im[:, 2])) + 1e-6

    # --- cote camera = cote le plus visible ; cote oppose = l'autre
    vl = np.mean([V(k) for k in ("l_wr","l_el","l_kn","l_an")])
    vr = np.mean([V(k) for k in ("r_wr","r_el","r_kn","r_an")])
    near, far = ("l","r") if vl >= vr else ("r","l")
    f["vis_near"] = float(max(vl, vr)); f["vis_far"] = float(min(vl, vr))

    # --- A. ordres de profondeur : membre superieur contre membre inferieur
    for a, b in (("wr","kn"), ("el","kn"), ("wr","an"), ("el","hip"), ("wr","hip"), ("idx","kn")):
        for tag, side in (("near", near), ("far", far)):
            d3 = Z(f"{side}_{a}") - Z(f"{side}_{b}")
            f[f"{a}_{b}_{tag}_leg"] = d3 / leg
            f[f"{a}_{b}_{tag}_zext"] = d3 / zext
            f[f"{a}_{b}_{tag}_im"] = (z(f"{side}_{a}") - z(f"{side}_{b}")) / zext_im
        # moyenne des deux cotes, et ecart entre les deux cotes
        f[f"{a}_{b}_both_leg"] = float(np.mean([Z(f"{s}_{a}") - Z(f"{s}_{b}") for s in "lr"])) / leg
        f[f"{a}_{b}_asym"] = float(abs((Z(f"l_{a}")-Z(f"l_{b}")) - (Z(f"r_{a}")-Z(f"r_{b}")))) / leg

    # --- B. etalements en profondeur pure (l'axe camera, pas un axe du corps)
    for nm, ab in (("ank",("l_an","r_an")), ("kne",("l_kn","r_kn")), ("wri",("l_wr","r_wr")),
                   ("elb",("l_el","r_el")), ("toe",("l_toe","r_toe")), ("hip",("l_hip","r_hip")),
                   ("sho",("l_sh","r_sh"))):
        f[f"z_{nm}_leg"] = abs(Z(ab[0]) - Z(ab[1])) / leg
        f[f"z_{nm}_zext"] = abs(Z(ab[0]) - Z(ab[1])) / zext
        f[f"zim_{nm}"] = abs(z(ab[0]) - z(ab[1])) / zext_im
    f["z_ank_over_sho"] = f["z_ank_leg"] / (f["z_sho_leg"] + 1e-6)
    f["z_ank_over_hip"] = f["z_ank_leg"] / (f["z_hip_leg"] + 1e-6)
    f["z_wri_over_ank"] = f["z_wri_leg"] / (f["z_ank_leg"] + 1e-6)
    f["z_kne_over_ank"] = f["z_kne_leg"] / (f["z_ank_leg"] + 1e-6)

    # --- C. inclusion en profondeur : les poignets sont-ils entre les chevilles selon z ?
    alo, ahi = sorted([Z("l_an"), Z("r_an")]); klo, khi = sorted([Z("l_kn"), Z("r_kn")])
    f["z_wr_in_ank"] = float(alo < Z("l_wr") < ahi and alo < Z("r_wr") < ahi)
    f["z_el_in_kne"] = float(klo < Z("l_el") < khi and klo < Z("r_el") < khi)
    f["z_wr_in_kne"] = float(klo < Z("l_wr") < khi and klo < Z("r_wr") < khi)

    # --- D. le z est-il credible ? etendue du corps en profondeur rapportee a sa taille
    f["z_body_over_leg"] = zext / leg
    f["z_body_over_torso"] = zext / torso
    f["hip_y"] = float((im[I["l_hip"],1] + im[I["r_hip"],1]) / 2)
    return f

def clip_z(entry):
    rows = [frame_z(fr) for fr in entry["frames"]]
    rows = [r for r in rows if r["vis_near"] > 0.4] or rows
    if len(rows) < 3: return None
    keys = [k for k in rows[0] if k != "hip_y"]
    rows.sort(key=lambda r: -r["hip_y"]); bot = rows[:max(3, len(rows)//3)]
    out = {}
    for k in keys:
        a = np.array([r[k] for r in rows]); b = np.array([r[k] for r in bot])
        out[f"all_{k}"] = float(np.median(a)); out[f"bot_{k}"] = float(np.median(b))
        out[f"max_{k}"] = float(a.max()); out[f"min_{k}"] = float(a.min())
        out[f"sd_{k}"] = float(a.std())                       # stabilite = confiance
        out[f"pos_{k}"] = float((a > 0).mean())               # vote de signe sur les frames
    out["n_rows"] = len(rows)
    return out
