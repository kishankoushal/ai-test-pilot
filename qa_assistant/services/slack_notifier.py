import os
import json
import re
import time
from datetime import datetime
from slack_sdk.web.async_client import AsyncWebClient
from utils.config import SLACK_BOT_TOKEN, SLACK_CHANNEL
import logging

logger = logging.getLogger(__name__)

client = AsyncWebClient(token=SLACK_BOT_TOKEN)

# Slack message size limits
MAX_TEXT_LENGTH = 2700  # Reduced further to accommodate dividers and timestamps
MAX_BUTTON_VALUE_LENGTH = 1900  # Slack limit is 2000, leaving some buffer

def clean_markdown_for_slack(text):
    """
    Clean markdown formatting to be compatible with Slack's mrkdwn format.
    Slack has its own markdown-like syntax but with differences.
    """
    # Replace ** bold with * for Slack's single asterisk bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    
    # Ensure lists have a space after the bullet
    text = re.sub(r'^-([^\s])', r'- \1', text, flags=re.MULTILINE)
    
    # Ensure headings have a space after the #
    text = re.sub(r'^(#+)([^\s])', r'\1 \2', text, flags=re.MULTILINE)
    
    return text

async def notify_slack(summary: str, score: float, payload):
    """
    Send a notification to Slack with failure summary and action button.
    Handles truncation of content to meet Slack API limits.
    """
    # Generate a timestamp for the message
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a visual divider for message separation
    divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Set color based on confidence score
    color = "#36a64f" if score >= 0.8 else "#ffcc00" if score >= 0.6 else "#ff0000"
    
    # Truncate summary for main message if needed
    truncated_summary = summary
    if len(summary) > MAX_TEXT_LENGTH:
        truncated_summary = summary[:MAX_TEXT_LENGTH] + "... (truncated)"
        logger.info(f"Summary truncated from {len(summary)} to {len(truncated_summary)} characters")
    
    # Clean the summary for Slack's markdown format
    slack_formatted_summary = clean_markdown_for_slack(truncated_summary)
    
    # Create a header with timestamp and job information
    header = f"*🚨 Test Failure Report* | {current_time}\n"
    header += f"*Job:* {payload.job_name}\n"
    header += f"*Commit:* `{payload.commit_sha[:8] if payload.commit_sha else 'unknown'}`\n"
    header += divider
    
    # Full message with header and dividers
    text = f"{header}\n*Failure Summary:*\n{slack_formatted_summary}\n\n*Confidence Score:* {score:.2f}\n{divider}"
    
    # Create a minimal payload with just essential information for the button value
    # We'll store just enough context to identify what we're filing a bug for
    action_value = json.dumps({
        "summary": summary[:75],  # Very short summary for button
        "job_name": payload.job_name,
        "commit_sha": payload.commit_sha[:8] if payload.commit_sha else "unknown"
    })
    
    # Ensure button value is within limits
    if len(action_value) > MAX_BUTTON_VALUE_LENGTH:
        logger.warning(f"Button value exceeds limit ({len(action_value)} chars), truncating further")
        # Create an even more minimal payload if needed
        action_value = json.dumps({
            "job": payload.job_name[:50],
            "sha": payload.commit_sha[:8] if payload.commit_sha else "unknown" 
        })
    
    try:
        # Send the message to Slack
        response = await client.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=[
                {
                    "type": "section", 
                    "text": {"type": "mrkdwn", "text": text}
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "File a bug"},
                            "value": action_value,
                            "action_id": "create_jira"
                        }
                    ]
                }
            ]
        )
        logger.info(f"Slack notification sent successfully to channel {SLACK_CHANNEL}")
        return response
    except Exception as e:
        logger.error(f"Error sending Slack notification: {str(e)}")
        # Try a fallback simple message without blocks if the rich message fails
        try:
            return await client.chat_postMessage(
                channel=SLACK_CHANNEL,
                text=f"Test failure in {payload.job_name}: {summary[:500]}... (Click the link to see full logs)"
            )
        except Exception as fallback_error:
            logger.error(f"Even fallback Slack message failed: {str(fallback_error)}")
            raise
