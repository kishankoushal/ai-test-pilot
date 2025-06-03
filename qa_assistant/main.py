from fastapi import FastAPI
from routes import webhook, slack, jira

app = FastAPI()
app.include_router(webhook.router, prefix="/webhook")
app.include_router(slack.router, prefix="/slack")
app.include_router(jira.router, prefix="/jira")
