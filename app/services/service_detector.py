import re
from collections import defaultdict
from typing import Tuple, List, Optional


# =========================================
# Service display names (for DB / UI)
# =========================================
SERVICE_ALIAS = {
    "pembukaan_rekening": "Pembukaan Rekening Tahapan",
    "penggantian_kartu_atm": "Penggantian Kartu ATM",
    "pendaftaran_m_bca": "Pendaftaran m-BCA"
}


# =========================================
# Rule-based keyword dictionary
# =========================================
RULES = {
    "pembukaan_rekening": [
        "buka rekening",
        "buka tabungan",
        "buat rekening",
        "bikin rekening",
        "buat tabungan",
        "bikin tabungan",
        "open account",
        "registrasi rekening",
        "tahapan bca",
        "tahapan xpresi",
        "tahapan gold",
        "tahapan platinum",
        "tahapan berjangka",
        "rekening dolar",
        "nasabah baru",
        "calon nasabah",
        "syarat buka rekening",
        "setoran awal"
    ],
    "penggantian_kartu_atm": [
        "kartu hilang",
        "kartu rusak",
        "kartu tertelan",
        "kartu patah",
        "chip rusak",
        "lupa pin atm",
        "kartu expired",
        "kartu kadaluarsa",
        "ganti kartu",
        "tukar kartu",
        "cetak ulang kartu",
        "kartu atm",
        "kartu debit",
        "paspor bca"
    ],
    "pendaftaran_m_bca": [
        "m-bca",
        "mbca",
        "mobile banking",
        "m-banking",
        "bca mobile",
        "daftar m-bca",
        "registrasi m-bca",
        "aktivasi m-bca",
        "aktivasi mobile banking",
        "kode akses",
        "pin m-bca",
        "aktivasi finansial",
        "transaksi di hp",
        "layanan digital"
    ]
}


# =========================================
# Detection parameters
# =========================================
MIN_KEYWORD_HIT = 1       # Minimum matched keywords
CONFIDENCE_LOCK = 0.7     # Confidence to lock service


# =========================================
# Utilities
# =========================================
def normalize_text(text: str) -> str:
    text = text.lower()

    # common ASR phonetic fixes
    replacements = {
        "pendapatan": "pendaftaran",
        "pendaptaran": "pendaftaran",
        "bj ai": "mbca",
        "b j a i": "mbca",
        "m b c a": "mbca",
        "m bca": "mbca",
        "m-bca": "mbca",
        "m b a": "mbca",
        "em be ce a": "mbca",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    # remove punctuation
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================================
# Core Detection Logic
# =========================================
def detect_service(
    full_text: str
) -> Tuple[
    Optional[str],
    Optional[str],
    float,
    List[str]
]:
    """
    Detect service from accumulated transcript text

    Args:
        full_text (str): Full transcript text (accumulated per session)

    Returns:
        service_key (str | None)
        service_alias (str | None)
        confidence (float 0–1)
        matched_keywords (list[str])
    """

    if not full_text or not full_text.strip():
        return None, None, 0.0, []

    text = normalize_text(full_text)

    scores = {}
    matched_keywords_map = defaultdict(list)

    # --- Keyword matching ---
    for service_key, keywords in RULES.items():
        for kw in keywords:
            if kw in text:
                matched_keywords_map[service_key].append(kw)
                
        hit_count = len(matched_keywords_map[service_key])
        if len(matched_keywords_map[service_key]) >= MIN_KEYWORD_HIT:
            # Soft confidence for streaming context
            scores[service_key] = min(
                1.0,
                0.5 + 0.25 * (hit_count - 1)
            )

    if not scores:
        return None, None, 0.0, []

    # Pick service with highest confidence
    best_service = max(scores, key=scores.get)

    return (
        best_service,
        SERVICE_ALIAS.get(best_service),
        round(scores[best_service], 2),
        matched_keywords_map[best_service]
    )


# =========================================
# Helper for lock decision
# =========================================
def should_lock_service(confidence: float) -> bool:
    """
    Decide whether service detection is confident enough to lock

    Args:
        confidence (float)

    Returns:
        bool
    """
    return confidence >= CONFIDENCE_LOCK
