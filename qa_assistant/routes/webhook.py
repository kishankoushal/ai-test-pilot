from fastapi import APIRouter, Request
from services.log_parser import summarize_log
from services.confidence import get_confidence_score
from services.slack_notifier import notify_slack
from services.jira_client import create_jira_bug
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
        
        # If confidence is high (>=0.8), automatically file a Jira bug
        if score >= 0.8:
            # Create a concise title for the bug
            title = f"[Auto] Test failure in {payload.job_name}"
            
            # Create detailed description
            description = f"""
                Automated bug filed by QA Assistant due to high confidence failure detection.

                **Summary:**
                {summary}

                **Job:** {payload.job_name}
                **Commit:** {payload.commit_sha[:8] if payload.commit_sha else "unknown"}
                **Confidence Score:** {score:.2f}
            """
            
            # File the bug and get the URL
            jira_url = create_jira_bug(
                summary=title,
                description=description,
                assignee="jatin.yadav@harness.io",
                team_category="Others",  # Default value as requested
            )
            
            logging.info(f"Automatically filed Jira bug: {jira_url}")
            return {"message": "Processed with auto bug filing", "success": True, "jira_url": jira_url}
        
        return {"message": "Processed", "success": True}
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return {"message": f"Error: {str(e)}", "success": False}
