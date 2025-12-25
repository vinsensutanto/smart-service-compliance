# from app.extensions import db
# from app.models.service_record import ServiceRecord
# from app.services.service_detector import detect_service
# from app.services.sop_engine import load_sop_by_service_name

# def run_service_detection_checkpoint(service_record_id: str):
#     record = (
#         db.session.query(ServiceRecord)
#         .filter_by(service_record_id=service_record_id)
#         .first()
#     )

#     if not record or not record.full_transcript:
#         return {"status": "error", "message": "Transcript not ready"}

#     # Already locked
#     if record.service_id:
#         return {
#             "status": "already_detected",
#             "service_id": record.service_id,
#             "confidence": record.confidence
#         }

#     service_id, confidence, keywords = detect_service(record.full_transcript)

#     if not service_id:
#         return {"status": "not_detected"}

#     record.service_id = service_id
#     record.confidence = confidence
#     db.session.commit()

#     return {
#         "status": "detected",
#         "service_id": service_id,
#         "confidence": confidence,
#         "matched_keywords": keywords
#     }