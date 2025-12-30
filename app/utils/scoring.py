# app/utils/scoring.py
def calculate_session_score(is_normal, reason):
    if is_normal == 1:
        return 100
    
    # Mapping bobot tetap sama untuk semua layar
    weights = {
        "System Error / AI not responding": 90,
        "Customer cancelled or left early": 80,
        "Staff forgot to finish session": 40,
        "other": 60
    }
    return weights.get(reason, 60)