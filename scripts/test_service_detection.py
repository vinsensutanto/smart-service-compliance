from app import create_app
from app.services.service_detection_checkpoint import (
    run_service_detection_checkpoint
)

app = create_app()

SERVICE_RECORD_ID = "SR0001"  # replace with real ID

with app.app_context():
    result = run_service_detection_checkpoint(SERVICE_RECORD_ID)

    print("\n===== SERVICE DETECTION CHECKPOINT =====")
    print(f"Status     : {result['status']}")

    if result.get("service_name"):
        print(f"Service    : {result['service_name']}")
        print(f"Confidence : {result['confidence']}")

    if result.get("sop"):
        print("\n--- SOP STEPS ---")
        for step in result["sop"]["steps"]:
            print(f"{step['step_order']}. {step['description']}")
