import json
from fastapi import APIRouter, Request, HTTPException
from services.jira_client import create_jira_bug
from utils.config import SLACK_BOT_TOKEN

from slack_sdk.web.async_client import AsyncWebClient

router = APIRouter()
slack_client = AsyncWebClient(token=SLACK_BOT_TOKEN)

@router.post("/interact")
async def slack_interact(request: Request):
    form_data = await request.form()
    payload = json.loads(form_data.get("payload", "{}"))
    
    if payload.get("type") == "block_actions":
        # Handle button click to open modal
        trigger_id = payload.get("trigger_id")
        action = payload.get("actions", [{}])[0]
        
        if action.get("action_id") == "create_jira":
            try:
                # Parse the value from the button
                bug_data = json.loads(action.get("value", "{}"))
                
                # Open a modal for the user to confirm and add details
                await slack_client.views_open(
                    trigger_id=trigger_id,
                    view={
                        "type": "modal",
                        "callback_id": "submit_jira_bug",
                        "title": {"type": "plain_text", "text": "File a Jira Bug"},
                        "submit": {"type": "plain_text", "text": "Submit"},
                        "close": {"type": "plain_text", "text": "Cancel"},
                        "private_metadata": json.dumps(bug_data),
                        "blocks": [
                            {
                                "type": "input",
                                "block_id": "title_block",
                                "label": {"type": "plain_text", "text": "Bug Title"},
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "title",
                                    "initial_value": f"Automation Failure - {bug_data.get('job_name')}"
                                }
                            },
                            {
                                "type": "input",
                                "block_id": "description_block",
                                "label": {"type": "plain_text", "text": "Description"},
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "description",
                                    "multiline": True,
                                    "initial_value": bug_data.get("description", "")
                                }
                            },
                            {
                                "type": "input",
                                "block_id": "assignee_block",
                                "optional": True,
                                "label": {"type": "plain_text", "text": "Assignee"},
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "assignee"
                                }
                            },
                            {
                                "type": "input",
                                "block_id": "labels_block",
                                "optional": True,
                                "label": {"type": "plain_text", "text": "Labels (comma separated)"},
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "labels",
                                    "initial_value": "automation,bug"
                                }
                            }
                        ]
                    }
                )
                return {"text": "Opening bug creation form..."}
            except Exception as e:
                return {"text": f"Error creating modal: {str(e)}"}
    
    elif payload.get("type") == "view_submission":
        # Handle form submission
        view = payload.get("view", {})
        
        # Get submitted values
        values = view.get("state", {}).get("values", {})
        metadata = json.loads(view.get("private_metadata", "{}"))
        
        title = values.get("title_block", {}).get("title", {}).get("value", "Untitled Bug")
        description = values.get("description_block", {}).get("description", {}).get("value", "")
        assignee = values.get("assignee_block", {}).get("assignee", {}).get("value", "")
        labels = values.get("labels_block", {}).get("labels", {}).get("value", "")
        
        # Add commit info to description
        full_description = f"{description}\n\nCommit: {metadata.get('commit_sha', 'N/A')}"
        
        # Create the bug
        ticket_url = create_jira_bug(
            summary=title,
            description=full_description,
            assignee=assignee,
            labels=labels.split(',') if labels else []
        )
        
        # Post a message in the channel about the new bug
        await slack_client.chat_postMessage(
            channel=payload.get("user", {}).get("id"),
            text=f"✅ Bug created successfully: {ticket_url}"
        )
        
        return {}  # Must return empty dict for view_submission
        
    return {"text": "Unknown interaction"}
