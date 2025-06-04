from fastapi import FastAPI
from routes import webhook, slack, jira, prd_parser

app = FastAPI()
app.include_router(webhook.router, prefix="/webhook")
app.include_router(slack.router, prefix="/slack")
app.include_router(jira.router, prefix="/jira")
app.include_router(prd_parser.router, prefix="/prd")