import json
import logging
from fastapi import APIRouter, Request, HTTPException
from services.jira_client import create_jira_bug
from utils.config import SLACK_BOT_TOKEN
import asyncio
from slack_sdk.web.async_client import AsyncWebClient

router = APIRouter()
slack_client = AsyncWebClient(token=SLACK_BOT_TOKEN)

@router.post("/interact")
async def slack_interact(request: Request):
    form_data = await request.form()
    payload = json.loads(form_data.get("payload", "{}"))
    # logging.info(f"Received payload: {payload}")
    
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
                                    "initial_value": bug_data.get('summary', f"Issue in {bug_data.get('job_name', '')}")
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
                                    "initial_value": bug_data.get('description', '')
                                }
                            },
                            {
                                "type": "input",
                                "block_id": "assignee_block",
                                "label": {"type": "plain_text", "text": "Assignee"},
                                "element": {
                                    "type": "static_select",
                                    "action_id": "assignee",
                                    "placeholder": {"type": "plain_text", "text": "Select an assignee"},
                                    "options": [
                                        {
                                            "text": {"type": "plain_text", "text": "Jatin Yadav"},
                                            "value": "jatin.yadav@harness.io"
                                        },
                                        {
                                            "text": {"type": "plain_text", "text": "Shreyansh Gupta"},
                                            "value": "shreyansh.gupta@harness.io"
                                        },
                                        {
                                            "text": {"type": "plain_text", "text": "Kishan Koushal"},
                                            "value": "kishan.rongali@harness.io"
                                        },
                                        {
                                            "text": {"type": "plain_text", "text": "Lajith Puthuchery"},
                                            "value": "lajith.puthuchery@harness.io"
                                        }
                                    ]
                                }
                            },
                            {
                                "type": "input",
                                "block_id": "team_category_block",
                                "label": {"type": "plain_text", "text": "Team Category"},
                                "element": {
                                    "type": "static_select",
                                    "action_id": "team_category",
                                    "placeholder": {"type": "plain_text", "text": "Select a team category"},
                                    "options": [
                                        {"text": {"type": "plain_text", "text": "Catalog"}, "value": "Catalog"},
                                        {"text": {"type": "plain_text", "text": "Platform"}, "value": "Platform"},
                                        {"text": {"type": "plain_text", "text": "UI"}, "value": "UI"},
                                        {"text": {"type": "plain_text", "text": "Protection"}, "value": "Protection"},
                                        {"text": {"type": "plain_text", "text": "Others"}, "value": "Others"}
                                    ]
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
        # logging.info(f"View submission: {view}")
        # Get submitted values
        values = view.get("state", {}).get("values", {})
        metadata = json.loads(view.get("private_metadata", "{}"))
        
        title = values.get("title_block", {}).get("title", {}).get("value", "Untitled Bug")
        description = values.get("description_block", {}).get("description", {}).get("value", "")
        assignee = values.get("assignee_block", {}).get("assignee", {}).get("selected_option", {}).get("value", "")
        team_category = values.get("team_category_block", {}).get("team_category", {}).get("selected_option", {}).get("value", "")
        
        # Add commit info to description
        full_description = f"{description}\n\nCommit: {metadata.get('commit_sha', 'N/A')}"
        
        # Get the user ID for notifications
        user_id = payload.get("user", {}).get("id")
        
        # Create the Jira ticket asynchronously to avoid Slack timeout
        asyncio.create_task(create_and_notify(
            title=title, 
            description=full_description,
            assignee=assignee,
            team_category=team_category,
            user_id=user_id
        ))
        
        # Return immediately to prevent Slack timeout
        return {"response_action": "clear"}



# Add this new async function near the other async functions
async def create_and_notify(title, description, assignee, team_category, user_id):
    """Create Jira ticket and notify user in background"""
    try:
        ticket_url = create_jira_bug(
            summary=title,
            description=description,
            assignee=assignee,
            team_category=team_category
        )
        
        # Notify user of success
        await slack_client.chat_postMessage(
            channel=user_id,
            text=f"✅ Bug created successfully: {ticket_url}"
        )
    except Exception as e:
        # Log the error
        logging.error(f"Error creating Jira ticket: {str(e)}")
        # Notify user of error
        await slack_client.chat_postMessage(
            channel=user_id,
            text=f"❌ Error creating bug: {str(e)}"
        )