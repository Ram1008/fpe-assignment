import os
import json
from fastapi import APIRouter, HTTPException
from app.services.persistence_service import PersistenceService
from app.services.cache_service import CacheService
from app.services.external.validator_client import ValidatorClient
from app.domain.tree_engine import TreeEngine

router = APIRouter(prefix="/api/conversations", tags=["Validation & Submission"])

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@router.post("/{conversation_id}/validate")
async def validate_conversation_tree(conversation_id: str):
    persistence = PersistenceService()
    cache = CacheService(persistence)
    validator_client = ValidatorClient()

    snapshot = await persistence.get_latest_tree_snapshot(conversation_id)
    if not snapshot or not snapshot.get("tree"):
        raise HTTPException(status_code=404, detail="Tree snapshot not found for conversation")

    engine = TreeEngine.from_dict(snapshot["tree"])
    validator_payload = engine.serialize_for_validator()
    cache_ts = await cache.get_segments_cache_timestamp()

    report = await validator_client.validate_tree(validator_payload, cache_ts)
    is_valid = report.get("ok", False)

    # Save updated snapshot validation state
    await persistence.save_tree_snapshot(conversation_id, engine.to_dict(), is_valid=is_valid, validation_report=report)

    return {
        "is_valid": is_valid,
        "validator_payload": validator_payload,
        "validation_report": report
    }

@router.post("/{conversation_id}/submit")
async def submit_final_tree(conversation_id: str):
    persistence = PersistenceService()
    cache = CacheService(persistence)
    validator_client = ValidatorClient()

    snapshot = await persistence.get_latest_tree_snapshot(conversation_id)
    if not snapshot or not snapshot.get("tree"):
        raise HTTPException(status_code=404, detail="Tree snapshot not found for conversation")

    engine = TreeEngine.from_dict(snapshot["tree"])
    validator_payload = engine.serialize_for_validator()
    cache_ts = await cache.get_segments_cache_timestamp()

    report = await validator_client.validate_tree(validator_payload, cache_ts)
    if not report.get("ok", False):
        raise HTTPException(
            status_code=400,
            detail={"message": "Tree failed validation and cannot be finalized.", "report": report}
        )

    # Export final_tree.json and validation_report.json to project root
    final_tree_path = os.path.join(ROOT_DIR, "final_tree.json")
    validation_report_path = os.path.join(ROOT_DIR, "validation_report.json")

    with open(final_tree_path, "w", encoding="utf-8") as f:
        json.dump(validator_payload, f, indent=2)

    with open(validation_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return {
        "success": True,
        "message": "Tree successfully validated and submitted.",
        "final_tree_path": final_tree_path,
        "validation_report_path": validation_report_path,
        "validation_report": report
    }
