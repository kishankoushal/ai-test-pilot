from fastapi import APIRouter, Request
from services.log_parser import summarize_log
from services.confidence import get_confidence_score
from services.slack_notifier import notify_slack
from models.schema import GHAFailurePayload
import logging

router = APIRouter()

@router.post("/")
async def receive_log(payload: GHAFailurePayload):
    try:
        # Get the summary from the log
        summary = summarize_log(payload.log)
        
        # Ensure summary is not empty
        if not summary or summary.strip() == "":
            logging.warning("Empty summary generated from log, using fallback")
            summary = f"Test failure in {payload.job_name}"
        
        # Get confidence score for the summary
        score = get_confidence_score(summary)
        
        # Send notification to Slack with complete information
        await notify_slack(summary, score, payload)
        
        return {"message": "Processed", "success": True}
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return {"message": f"Error: {str(e)}", "success": False}
