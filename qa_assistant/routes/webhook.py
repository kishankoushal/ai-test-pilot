from fastapi import APIRouter, Request
from services.log_parser import summarize_log
from services.confidence import get_confidence_score
from services.slack_notifier import notify_slack
from models.schema import GHAFailurePayload

router = APIRouter()

@router.post("/")
async def receive_log(payload: GHAFailurePayload):
    summary = summarize_log(payload.log)
    score = get_confidence_score(summary)
    await notify_slack(summary, score, payload)
    return {"message": "Processed"}
