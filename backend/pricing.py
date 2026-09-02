"""Comptabilité détaillée des tokens et du coût (USD/EUR) des appels Gemini.

Tarifs relevés le 2026-09-01 sur https://ai.google.dev/gemini-api/docs/pricing
(tier payant, prix en USD par million de tokens). À re-vérifier régulièrement :
Google fait bouger cette grille, et certains prix sont promotionnels.
"""

import datetime as dt
import logging
import os
import threading

logger = logging.getLogger(__name__)

PRICING_SOURCE = "https://ai.google.dev/gemini-api/docs/pricing"
PRICING_CHECKED_ON = dt.date(2026, 9, 1)

# "text" couvre texte / image / vidéo (Google les facture au même tarif),
# "audio" la piste audio, "output" la sortie (tokens de raisonnement inclus).
# Plusieurs paliers par modèle : on retient le dernier dont la date est passée.
PRICING_USD_PER_MTOK = {
    "gemini-3.7-flash": [
        # Tarif promotionnel jusqu'au 31/12/2026, puis x2.
        (dt.date.min, {"text": 0.75, "audio": 0.75, "output": 3.75}),
        (dt.date(2027, 1, 1), {"text": 1.50, "audio": 1.50, "output": 7.50}),
    ],
    "gemini-3.6-flash": [
        (dt.date.min, {"text": 0.75, "audio": 0.75, "output": 3.75}),
        (dt.date(2027, 1, 1), {"text": 1.50, "audio": 1.50, "output": 7.50}),
    ],
    "gemini-3.5-flash": [
        (dt.date.min, {"text": 1.50, "audio": 1.50, "output": 9.00}),
    ],
    "gemini-3.5-flash-lite": [
        (dt.date.min, {"text": 0.30, "audio": 0.30, "output": 2.50}),
    ],
    "gemini-3.1-flash-lite": [
        (dt.date.min, {"text": 0.25, "audio": 0.50, "output": 1.50}),
    ],
    "gemini-2.5-flash": [
        (dt.date.min, {"text": 0.30, "audio": 1.00, "output": 2.50}),
    ],
    "gemini-2.5-flash-lite": [
        (dt.date.min, {"text": 0.10, "audio": 0.30, "output": 0.40}),
    ],
    # ⚠️ gemini-2.0-flash ne figure PLUS sur la grille officielle (modèle retiré
    # du tableau public). Les valeurs ci-dessous sont ses derniers tarifs connus
    # et ne sont PAS vérifiables : le coût calculé est signalé comme approximatif.
    "gemini-2.0-flash": [
        (dt.date.min, {"text": 0.10, "audio": 0.70, "output": 0.40}),
    ],
    "gemini-2.0-flash-lite": [
        (dt.date.min, {"text": 0.075, "audio": 0.075, "output": 0.30}),
    ],
}

UNVERIFIED_MODELS = {"gemini-2.0-flash", "gemini-2.0-flash-lite"}

# Taux de change USD -> EUR (frankfurter.dev / BCE, 2026-09-01).
# Surchargeable via la variable d'environnement USD_EUR_RATE.
DEFAULT_USD_EUR_RATE = 0.86281

_MILLION = 1_000_000
_warned_models = set()
_lock = threading.Lock()
_totals = {"calls": 0, "input": 0, "output": 0, "total": 0, "usd": 0.0}


def usd_eur_rate() -> float:
    """Taux de change courant, lu à chaque appel pour rester surchargeable."""
    try:
        return float(os.getenv("USD_EUR_RATE", DEFAULT_USD_EUR_RATE))
    except ValueError:
        logger.warning("USD_EUR_RATE illisible, repli sur %.5f", DEFAULT_USD_EUR_RATE)
        return DEFAULT_USD_EUR_RATE


def cost_logging_enabled() -> bool:
    return os.getenv("GEMINI_COST_LOG", "1").lower() not in ("0", "false", "no")


def normalize_model(model: str) -> str:
    """'models/gemini-3.7-flash-preview-01' -> 'gemini-3.7-flash'."""
    name = (model or "").strip().lower()
    if name.startswith("models/"):
        name = name[len("models/") :]
    # Plus long préfixe connu : tolère les suffixes de version/preview.
    matches = [key for key in PRICING_USD_PER_MTOK if name.startswith(key)]
    return max(matches, key=len) if matches else name


def rates_for(model: str, on: dt.date = None) -> dict:
    """Tarifs USD/Mtok applicables au modèle à la date donnée, ou None."""
    tiers = PRICING_USD_PER_MTOK.get(normalize_model(model))
    if not tiers:
        return None
    on = on or dt.date.today()
    applicable = [rates for start, rates in tiers if start <= on]
    return applicable[-1] if applicable else None


def _modality_split(details) -> dict:
    """Répartit les tokens d'un bloc par modalité (audio facturé à part)."""
    split = {}
    for item in details or []:
        modality = getattr(item, "modality", None)
        key = str(getattr(modality, "name", modality) or "UNKNOWN").upper()
        split[key] = split.get(key, 0) + (getattr(item, "token_count", 0) or 0)
    return split


def compute_cost(model: str, usage, on: dt.date = None) -> dict:
    """Détaille tokens et coût d'un appel à partir de response.usage_metadata."""
    get = lambda attr: getattr(usage, attr, None) or 0

    prompt_tokens = get("prompt_token_count")
    cached_tokens = get("cached_content_token_count")
    thoughts_tokens = get("thoughts_token_count")
    candidates_tokens = get("candidates_token_count")
    tool_tokens = get("tool_use_prompt_token_count")

    prompt_split = _modality_split(getattr(usage, "prompt_tokens_details", None))
    audio_tokens = prompt_split.get("AUDIO", 0)
    # Si la ventilation par modalité manque, tout passe au tarif texte/vidéo.
    visual_tokens = max(prompt_tokens + tool_tokens - audio_tokens, 0)

    # Les tokens de raisonnement sont facturés au tarif de sortie.
    billed_output = candidates_tokens + thoughts_tokens
    total_tokens = get("total_token_count") or (prompt_tokens + billed_output)

    detail = {
        "model": normalize_model(model),
        "model_raw": model,
        "prompt_tokens": prompt_tokens,
        "tool_tokens": tool_tokens,
        "cached_tokens": cached_tokens,
        "audio_tokens": audio_tokens,
        "visual_tokens": visual_tokens,
        "prompt_split": prompt_split,
        "thoughts_tokens": thoughts_tokens,
        "candidates_tokens": candidates_tokens,
        "billed_output_tokens": billed_output,
        "total_tokens": total_tokens,
        "priced": False,
        "unverified": normalize_model(model) in UNVERIFIED_MODELS,
    }

    rates = rates_for(model, on)
    if not rates:
        return detail

    input_usd = (visual_tokens * rates["text"] + audio_tokens * rates["audio"]) / _MILLION
    output_usd = billed_output * rates["output"] / _MILLION
    rate = usd_eur_rate()

    detail.update(
        priced=True,
        rates=rates,
        input_usd=input_usd,
        output_usd=output_usd,
        total_usd=input_usd + output_usd,
        input_eur=input_usd * rate,
        output_eur=output_usd * rate,
        total_eur=(input_usd + output_usd) * rate,
        usd_eur_rate=rate,
    )
    return detail


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def log_usage(model: str, response, label: str = "appel", extra: str = "") -> dict:
    """Loggue le détail tokens + coût d'une réponse Gemini. Ne lève jamais."""
    try:
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            logger.warning("[coût] %s (%s) : usage_metadata absent", label, model)
            return None

        d = compute_cost(model, usage)

        with _lock:
            _totals["calls"] += 1
            _totals["input"] += d["prompt_tokens"] + d["tool_tokens"]
            _totals["output"] += d["billed_output_tokens"]
            _totals["total"] += d["total_tokens"]
            if d["priced"]:
                _totals["usd"] += d["total_usd"]
            snapshot = dict(_totals)

        if not cost_logging_enabled():
            return d

        if not d["priced"]:
            if d["model"] not in _warned_models:
                _warned_models.add(d["model"])
                logger.warning(
                    "[coût] Modèle '%s' absent de la grille tarifaire (%s) : "
                    "tokens loggués, coût non calculé. Ajoute-le dans pricing.py.",
                    d["model"], PRICING_SOURCE,
                )
            logger.info(
                "[coût] %s | %s%s | entrée %s tok | sortie %s tok | total %s tok | coût inconnu",
                label, d["model_raw"], f" | {extra}" if extra else "",
                _fmt(d["prompt_tokens"]), _fmt(d["billed_output_tokens"]), _fmt(d["total_tokens"]),
            )
            return d

        approx = "~" if d["unverified"] else ""
        if d["unverified"] and d["model"] not in _warned_models:
            _warned_models.add(d["model"])
            logger.warning(
                "[coût] Tarif de '%s' non vérifiable (modèle absent de %s) : "
                "les montants sont indicatifs.", d["model"], PRICING_SOURCE,
            )

        modalites = ", ".join(
            f"{k.lower()} {_fmt(v)}" for k, v in sorted(d["prompt_split"].items())
        ) or "non ventilé"
        rates = d["rates"]

        logger.info(
            "\n"
            "┌─ [coût] %s | modèle %s%s\n"
            "│  entrée   : %10s tok  (%s)\n"
            "│             visuel/texte %s @ $%.3f/Mtok · audio %s @ $%.3f/Mtok · cache %s\n"
            "│             %s$%.6f  =  %s%.6f EUR\n"
            "│  sortie   : %10s tok  (réponse %s + raisonnement %s) @ $%.3f/Mtok\n"
            "│             %s$%.6f  =  %s%.6f EUR\n"
            "│  TOTAL    : %10s tok  →  %s$%.6f  =  %s%.6f EUR  (1 USD = %.5f EUR)\n"
            "└─ cumul session : %s appels · %s tok · %s$%.4f = %s%.4f EUR",
            label, d["model_raw"], f" | {extra}" if extra else "",
            _fmt(d["prompt_tokens"] + d["tool_tokens"]), modalites,
            _fmt(d["visual_tokens"]), rates["text"],
            _fmt(d["audio_tokens"]), rates["audio"],
            _fmt(d["cached_tokens"]),
            approx, d["input_usd"], approx, d["input_eur"],
            _fmt(d["billed_output_tokens"]),
            _fmt(d["candidates_tokens"]), _fmt(d["thoughts_tokens"]), rates["output"],
            approx, d["output_usd"], approx, d["output_eur"],
            _fmt(d["total_tokens"]),
            approx, d["total_usd"], approx, d["total_eur"],
            d["usd_eur_rate"],
            _fmt(snapshot["calls"]), _fmt(snapshot["total"]),
            approx, snapshot["usd"], approx, snapshot["usd"] * d["usd_eur_rate"],
        )
        return d

    except Exception as e:  # le logging de coût ne doit jamais casser une analyse
        logger.warning("[coût] Impossible de calculer le coût de l'appel %s : %s", label, e)
        return None


def session_totals() -> dict:
    """Cumul depuis le démarrage du process (tokens + USD + EUR)."""
    with _lock:
        snapshot = dict(_totals)
    snapshot["eur"] = snapshot["usd"] * usd_eur_rate()
    return snapshot
