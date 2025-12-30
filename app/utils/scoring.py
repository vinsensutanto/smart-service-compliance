# app/utils/scoring.py
def calculate_session_score(record):
    """
    Menghitung skor berdasarkan objek ServiceRecord
    """
    if record.is_normal_flow == 1:
        return 100

    weights = {
        "System Error / AI not responding": 90,
        "Customer cancelled or left early": 80,
        "Staff forgot to finish session": 40
    }
    # Ambil skor berdasarkan record.reason
    return weights.get(record.reason, 60)