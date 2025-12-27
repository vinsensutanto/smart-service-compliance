# app/services/service_detector.py

from typing import Tuple, List
import re

# --------------------------------
# Service keyword rules (ASR aware)
# --------------------------------
SERVICE_RULES = {
    "OPEN_ACCOUNT": {
        "label": "Pembukaan Rekening",
        "keywords": [
            "buka rekening",
            "buat rekening",
            "rekening baru",
            "tabungan",
            "nasabah baru",
        ]
    },
    "ATM_REPLACEMENT": {
        "label": "Penggantian Kartu ATM",
        "keywords": [
            "kartu atm",
            "kartu hilang",
            "kartu rusak",
            "ganti kartu",
            "kartu tertelan",
        ]
    },
    "MBCA_REGISTRATION": {
        "label": "Pendaftaran m-BCA",
        "keywords": [
            # clean
            "m-bca",
            "mbca",
            "bca mobile",
            "mobile banking",
            "daftar mbca",

            # ASR-noise tolerant
            "m bca",
            "m bj ai",
            "bj ai",
            "pendapatan m",
            "pendaftaran m",
        ]
    }
}


# --------------------------------
# Text normalization (CRITICAL)
# --------------------------------
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text


# --------------------------------
# Detect service from transcript
# --------------------------------
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

    for service_key, rule in SERVICE_RULES.items():
        hits = []

        for kw in rule["keywords"]:
            if kw in norm_text:
                hits.append(kw)

        if hits:
            confidence = min(1.0, 0.4 + 0.15 * len(hits))
            print(
                f"[NLP] DETECTED service={service_key} "
                f"label={rule['label']} hits={hits} conf={confidence}"
            )
            return (
                service_key,
                rule["label"],
                confidence,
                hits
            )

    return None, None, 0.0, []


# --------------------------------
# Optional lock helper
# --------------------------------
def should_lock_service(confidence: float) -> bool:
    return confidence >= 0.75
