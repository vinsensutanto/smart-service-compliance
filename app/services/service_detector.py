# app/services/service_detector.py

from typing import Tuple, List
import re

# --------------------------------
# Service keyword rules (weighted, ASR-aware)
# --------------------------------
INTENT_SCORE = 0.5

SERVICE_RULES = {
    "MBCA_REGISTRATION": {
        "label": "Pendaftaran m-BCA",
        "threshold": 0.65,
        "keywords": {
            "pendaftaran m": 0.7,
            "pendaftaran mbca": 0.7,
            "registrasi": 0.7,
            "daftar mbca": 0.7,
            "m bca": 0.65,
            "mbca": 0.65,
            "bca mobile": 0.6,
            "mobile banking": 0.6,

            "m bj ai": 0.4,
            "bj ai": 0.3,
            "pendapatan m": 0.4,
        }
    },

    "OPEN_ACCOUNT": {
        "label": "Pembukaan Rekening",
        "threshold": 0.65,
        "keywords": {
            "pembukaan rekening": 0.8,
            "rekening tahapan": 0.8,

            "rekening baru": 0.65,
            "buka rekening": 0.65,
            "buat rekening": 0.65,
            "nasabah baru": 0.65,
            "nasa bah baru": 0.65,
            "tabungan": 0.4,
        }
    },

    "ATM_REPLACEMENT": {
        "label": "Penggantian Kartu ATM",
        "threshold": 0.6,
        "keywords": {
            "kartu atm": 0.7,
            "kartu hilang": 0.7,
            "kartu rusak": 0.6,
            "ganti kartu": 0.6,
            "penggantian kartu": 0.7,
            "penggantian atm": 0.7,
            "kartu tidak bisa": 0.4,
            "atm tidak bisa": 0.4,
            "kartu tertelan": 0.7,
            "gantian kartu":0.7,
        },
        "intents": [
            "mau ganti kartu",
            "proses penggantian",
            "atm saya rusak",
            "kartu atm hilang",
        ]
    }
}

# def normalize_text(text: str) -> str:
#     text = text.lower()
#     text = re.sub(r"[^a-z0-9\s]", " ", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     return text

def normalize_text(text: str) -> str:
    text = text.lower()

    # basic typo normalization (ASR-aware)
    text = text.replace("menggantian", "penggantian")
    text = text.replace("mengganti", "ganti")
    text = text.replace("pengganti", "ganti")

    # remove punctuation
    # text = re.sub(r"[^a-z0-9\s]", " ", text)
    # text = re.sub(r"\s+", " ", text).strip()
    return text

def keyword_match(keyword: str, text: str) -> bool:
    kw_tokens = keyword.split()
    text_tokens = text.split()
    return all(t in text_tokens for t in kw_tokens)

def phrase_match(phrase: str, text: str) -> bool:
    return keyword_match(phrase, text)

def detect_service(text: str) -> Tuple[str, str, float, List[str]]:
    """
    Returns:
    - service_key
    - service_label
    - confidence
    - matched_keywords
    """

    if not text:
        return None, None, 0.0, []

    norm_text = normalize_text(text)
    print(f"[NLP] normalized_text='{norm_text}'")

    best_service = None
    best_score = 0.0
    best_hits = []

    for service_key, rule in SERVICE_RULES.items():
        score = 0.0
        hits = []

        for kw, weight in rule["keywords"].items():
            # if kw in norm_text:
            #     score += weight
            #     hits.append(kw)
            if keyword_match(kw, norm_text):
                score += weight
                hits.append(kw)

        for phrase in rule.get("intents", []):
            if phrase_match(phrase, norm_text):
                score += INTENT_SCORE
                hits.append(phrase)

        if hits:
            print(
                f"[NLP] candidate={service_key} "
                f"hits={hits} score={score:.2f}"
            )

        if score > best_score:
            best_service = service_key
            best_score = score
            best_hits = hits

    if best_service:
        confidence = min(1.0, best_score)
        rule = SERVICE_RULES[best_service]

        print(
            f"[NLP] DETECTED service={best_service} "
            f"label={rule['label']} conf={confidence}"
        )

        return (
            best_service,
            rule["label"],
            confidence,
            best_hits
        )

    return None, None, 0.0, []

def should_lock_service(service_key: str, confidence: float) -> bool:
    rule = SERVICE_RULES.get(service_key)
    if not rule:
        return False
    return confidence >= rule["threshold"]