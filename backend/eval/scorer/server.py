"""Serveur local de notation humaine des clips de data/.

Sert une page unique qui deroule les clips un par un : la video, le nom du
fichier, les 8 criteres du schema du mouvement avec trois boutons 1/3 2/3 3/3,
une zone de commentaire, le nombre de repetitions, et — replies par defaut — l'avis de
Claude et la note du LLM sur les memes criteres.

    cd backend
    uv run python eval/scorer/server.py          # http://localhost:8800

Les notes humaines sont ecrites au fil des clics dans eval/scorer/human_labels.json,
le nombre de repetitions dans eval/reps/verite_terrain.json (cle `n`, `source: humain`).
Rien d'autre n'est modifie. Aucune dependance hors stdlib + pydantic (pour lire
les rubriques directement dans schemas.py, seule source de verite des criteres).
"""

import json
import mimetypes
import os
import posixpath
import re
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
GROUND_TRUTH = os.path.join(BACKEND, "eval", "ground_truth.json")
CLAUDE_REVIEW = os.path.join(ICI, "claude_review.json")
LLM_SCORES = os.path.join(ICI, "llm_scores.json")
HUMAN_LABELS = os.path.join(ICI, "human_labels.json")
REPS_VT = os.path.join(BACKEND, "eval", "reps", "verite_terrain.json")
REPS_SIGNAUX = os.path.join(BACKEND, "eval", "reps", "signaux.json")
UI = os.path.join(ICI, "ui.html")

import indicators  # noqa: E402  (apres l'ajout de BACKEND au path)
import persona as persona_mod  # noqa: E402

_ecriture = threading.Lock()


def liste_persona(valeur):
    """Le persona humain est une liste depuis le 2026-09-06 ; avant, une chaine.

    Plusieurs archetypes decrivent parfois le meme defaut : l'humain coche l'ensemble
    des reponses qu'il accepte, et le modele est juge sur l'appartenance a cet ensemble.
    """
    if valeur is None:
        return []
    if isinstance(valeur, str):
        return [valeur]
    return [v for v in valeur if isinstance(v, str)]


def charge(path, defaut):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaut


def ecrit_atomique(path, obj):
    """Ecrit via un fichier temporaire : une coupure ne laisse pas un JSON tronque."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def niveaux(description):
    """Extrait du bareme du schema les trois niveaux que l'humain peut donner.

    Le schema et la page notent desormais sur la meme echelle 1/2/3 : il n'y a plus
    de repartition a faire, seulement un decoupage du texte du bareme. Le motif
    tolere encore "1-2=" pour lire sans casse un bareme anterieur a la bascule.
    """
    morceaux = re.split(r"(?:^|\s)(1-2|[1-3])=", description)
    intro = morceaux[0].strip()
    brut = {}
    for i in range(1, len(morceaux) - 1, 2):
        brut[morceaux[i]] = morceaux[i + 1].strip().rstrip(".").strip()
    if not brut:
        return intro, None
    joint = lambda *k: " / ".join(brut[x] for x in k if x in brut)
    return intro, {"1": joint("1-2", "1"), "2": joint("2"), "3": joint("3")}


# Attribue par ai_service quand le total depasse 90 % du maximum : ce n'est pas une
# valeur de l'enum, mais elle sort bel et bien du pipeline, donc l'humain doit pouvoir
# la choisir aussi.
TECHNICIAN = {
    "name": "The Technician",
    "description": "Aucun defaut dominant. Attribue automatiquement par le pipeline quand le "
                   "total depasse 90 % du maximum ; absent de l'enum du schema.",
    "defined": True,
    "hors_enum": True,
}


def _variante(mouvement):
    """"sumo deadlift" / "conventional deadlift" -> la cle du catalogue."""
    return "sumo" if "sumo" in (mouvement or "").lower() else "conventional"


def personas_du_schema(mouvement):
    """[{name, description, defined}] pour un mouvement, lus dans le catalogue.

    Un persona n'est plus une valeur d'enum que le modele choisit : c'est un etat
    observable precis, et sa description est celle de l'etat qui le declenche
    (indicators.Etat.persona). Il n'y a donc plus de persona "non defini".
    """
    variante = _variante(mouvement)
    out = [TECHNICIAN]
    vus = set()
    for ind in indicators.pour(variante):
        for etat in ind.etats:
            if etat.persona and etat.persona not in vus:
                vus.add(etat.persona)
                out.append({"name": etat.persona, "description": etat.description,
                            "defined": True, "indicateur": ind.id})
    return out


def criteres_du_schema(mouvement):
    """[{name, label, intro, levels}] pour un mouvement, lus dans le catalogue.

    Les "niveaux" ne viennent plus d'une rubrique redigee en prose : ils sont composes
    des etats observables des indicateurs du critere, avec la note que chacun vaut.
    C'est la meme source que celle qui notera le clip — l'annotateur humain et le
    systeme lisent desormais exactement le meme texte.
    """
    variante = _variante(mouvement)
    if not mouvement:
        return []
    out = []
    for cle, (libelle, poids) in indicators.CRITERES.items():
        inds = [i for i in indicators.pour(variante) if i.critere == cle]
        if not inds:
            continue
        niveaux_ = []
        for note in (3, 2, 1):
            faits = [e.description for i in inds for e in i.etats if e.note == note]
            if faits:
                niveaux_.append({"score": str(note), "text": " · ".join(faits)})
        out.append({
            "name": cle,
            "label": libelle,
            "intro": f"{len(inds)} indicateur(s) · poids {poids}",
            "levels": niveaux_,
            "rubric": " | ".join(f"[{i.id}] {i.question}" for i in inds),
        })
    return out


def _human_normalise(entree):
    """Les anciennes entrees stockaient un persona unique : on les sert deja en liste."""
    if not entree:
        return entree
    return {**entree, "persona": liste_persona(entree.get("persona"))}


def verite_reps():
    "Le contenu de verite_terrain.json, structure {_about, clips:{fichier: {...}}}."
    d = charge(REPS_VT, {})
    return d if isinstance(d.get("clips"), dict) else {"clips": {}}


_POSE_REPS = None


def comptes_pose():
    """Le compte de MediaPipe par clip, ou {} si la passe de pose n'a pas ete faite.

    Charge une seule fois : signaux.json fait 1,3 Mo. Affiche replie dans la page, comme
    l'avis de Claude et la note du LLM — voir un chiffre avant de compter oriente.
    """
    global _POSE_REPS
    if _POSE_REPS is None:
        _POSE_REPS = {}
        try:
            sys.path.insert(0, os.path.join(BACKEND, "eval", "reps"))
            from compte_reps import compte             # noqa: PLC0415
            signaux = charge(REPS_SIGNAUX, {})
            for f, s in signaux.items():
                _POSE_REPS[f] = {x: compte(s["points"], x)
                                 for x in ("med", "wri", "ext", "hip", "post")}
        except Exception as exc:                       # outil de dev : ne jamais bloquer
            print(f"comptes de pose indisponibles ({exc})")
    return _POSE_REPS


def catalogue():
    """La liste des clips a noter, avec tout ce que la page doit afficher."""
    gt = {v["file"]: v for v in charge(GROUND_TRUTH, {"videos": []})["videos"]}
    claude = charge(CLAUDE_REVIEW, {})
    llm = charge(LLM_SCORES, {})
    humain = charge(HUMAN_LABELS, {})
    reps = verite_reps()["clips"]
    pose = comptes_pose()

    fichiers = sorted(f for f in os.listdir(DATA) if f.lower().endswith((".mp4", ".mov", ".webm")))
    videos = []
    for f in fichiers:
        mouvement = (gt.get(f) or {}).get("movement")
        videos.append({
            "file": f,
            "movement": mouvement,
            "movement_source": "ground_truth" if mouvement else None,
            "criteria": criteres_du_schema(mouvement or ""),
            "personas": personas_du_schema(mouvement or ""),
            "claude": claude.get(f),
            "llm": llm.get(f),
            "human": _human_normalise(humain.get(f)),
            "reps": reps.get(f),
            "reps_pose": pose.get(f),
            "gt_notes": (gt.get(f) or {}).get("notes"),
            "use_as": (gt.get(f) or {}).get("use_as"),
        })
    return {"videos": videos, "scale": {"1": "1/3", "2": "2/3", "3": "3/3"}}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):        # une ligne par octet de video sinon
        if "media" not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def handle_one_request(self):
        # Le navigateur coupe la connexion des qu'il change de video : c'est normal,
        # ce n'est pas la peine d'en imprimer une trace de dix lignes.
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError):
            self.close_connection = True

    # ------------------------------------------------------------------ helpers
    def _envoie(self, code, corps, ctype="application/json; charset=utf-8", extra=None):
        if isinstance(corps, str):
            corps = corps.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(corps)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corps)

    def _media(self, nom):
        """Sert une video avec support des requetes Range (indispensable pour seek)."""
        chemin = os.path.join(DATA, nom)
        if not os.path.abspath(chemin).startswith(DATA) or not os.path.isfile(chemin):
            return self._envoie(404, b"introuvable", "text/plain")
        taille = os.path.getsize(chemin)
        ctype = mimetypes.guess_type(chemin)[0] or "video/mp4"
        debut, fin = 0, taille - 1
        rng = self.headers.get("Range")
        partiel = False
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            if m:
                partiel = True
                if m.group(1):
                    debut = int(m.group(1))
                if m.group(2):
                    fin = min(int(m.group(2)), taille - 1)
        longueur = max(0, fin - debut + 1)
        self.send_response(206 if partiel else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(longueur))
        if partiel:
            self.send_header("Content-Range", f"bytes {debut}-{fin}/{taille}")
        self.end_headers()
        with open(chemin, "rb") as f:
            f.seek(debut)
            reste = longueur
            while reste > 0:
                bloc = f.read(min(262144, reste))
                if not bloc:
                    break
                try:
                    self.wfile.write(bloc)
                except (BrokenPipeError, ConnectionResetError):
                    return                     # le navigateur a change de video
                reste -= len(bloc)

    # ------------------------------------------------------------------ routes
    def do_GET(self):
        chemin = urllib.parse.urlparse(self.path).path
        if chemin in ("/", "/index.html"):
            with open(UI, "rb") as f:
                return self._envoie(200, f.read(), "text/html; charset=utf-8",
                                    {"Cache-Control": "no-store"})
        if chemin == "/api/catalogue":
            return self._envoie(200, json.dumps(catalogue(), ensure_ascii=False),
                                extra={"Cache-Control": "no-store"})
        if chemin.startswith("/media/"):
            nom = urllib.parse.unquote(posixpath.basename(chemin))
            return self._media(nom)
        self._envoie(404, b"introuvable", "text/plain")

    def _post_reps(self, recu):
        """Ecrit le comptage humain des reps dans eval/reps/verite_terrain.json.

        Deux champs, et ils ne disent pas la meme chose :
          `n`        combien de repetitions — la reference historique ;
          `verrous`  A QUEL INSTANT chacune se verrouille, en secondes.

        Le second existe parce qu'un compte ne dit pas OU. Deux mesures ont deja
        conclu de travers faute de savoir si un candidat de pose tombait sur une vraie
        repetition ou sur autre chose : sur conventionnal_deadlift_14, trois candidats
        pour trois reps donnaient une couverture "parfaite" alors qu'un seul candidat
        etait reel, les deux autres etant le lifter qui marche vers la camera.

        Avec les instants, la couverture se mesure vraiment (la fenetre du candidat
        contient-elle le verrouillage ?), et `pose_analysis._phases` devient verifiable
        ailleurs que sur l'unique clip ou les instants avaient ete notes a la main.

        Mon propre compte n'est pas ecrase : il passe sous `claude_n`, pour qu'on puisse
        mesurer apres coup de combien je me suis trompe, comme on le fait pour le LLM.
        """
        fichier, n = recu.get("file"), recu.get("n")
        if not fichier or not isinstance(n, int) or not 0 <= n <= 99:
            return self._envoie(400, json.dumps({"erreur": "file ou n invalide"}))
        verrous = recu.get("verrous")
        if verrous is not None:
            if (not isinstance(verrous, list) or len(verrous) > 99
                    or not all(isinstance(t, (int, float)) and 0 <= t <= 3600 for t in verrous)):
                return self._envoie(400, json.dumps({"erreur": "verrous invalides"}))
            verrous = sorted(round(float(t), 2) for t in verrous)
        with _ecriture:
            vt = verite_reps()
            entree = dict(vt["clips"].get(fichier) or {})
            if entree.get("source") != "humain" and "n" in entree:
                entree.setdefault("claude_n", entree["n"])
            entree.update(n=n, source="humain", conf="haute",
                          updated_at=recu.get("updated_at"))
            if verrous is not None:
                # Liste vide = l'annotateur a tout retire : on efface la cle plutot que
                # de laisser un [] qui se lirait comme "zero repetition verifiee".
                if verrous:
                    entree["verrous"] = verrous
                else:
                    entree.pop("verrous", None)
            vt["clips"][fichier] = entree
            vt.setdefault("_about", "")
            ecrit_atomique(REPS_VT, vt)
            faits = sum(1 for v in vt["clips"].values() if v.get("source") == "humain")
            marques = sum(1 for v in vt["clips"].values() if v.get("verrous"))
        return self._envoie(200, json.dumps({"ok": True, "clips_reps": faits,
                                             "clips_verrous": marques}))

    def do_POST(self):
        chemin = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        if chemin == "/api/reps":
            try:
                return self._post_reps(json.loads(self.rfile.read(n) or b"{}"))
            except json.JSONDecodeError:
                return self._envoie(400, json.dumps({"erreur": "json invalide"}))
        if chemin != "/api/label":
            return self._envoie(404, b"introuvable", "text/plain")
        try:
            recu = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._envoie(400, json.dumps({"erreur": "json invalide"}))
        fichier = recu.get("file")
        if not fichier:
            return self._envoie(400, json.dumps({"erreur": "file manquant"}))
        with _ecriture:
            labels = charge(HUMAN_LABELS, {})
            entree = labels.get(fichier) or {}
            entree["scores"] = recu.get("scores") or {}
            entree["persona"] = liste_persona(recu.get("persona"))
            entree["comment"] = recu.get("comment") or ""
            entree["updated_at"] = recu.get("updated_at")
            labels[fichier] = entree
            ecrit_atomique(HUMAN_LABELS, labels)
            notes = sum(1 for v in labels.values() if v.get("scores"))
        self._envoie(200, json.dumps({"ok": True, "clips_notes": notes}))


def main():
    port = int(os.environ.get("PORT", "8800"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Notation : http://localhost:{port}   (videos : {DATA})")
    print(f"Ecriture : {HUMAN_LABELS}")
    print(f"           {REPS_VT}  (nombre de repetitions)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\narret")


if __name__ == "__main__":
    main()
