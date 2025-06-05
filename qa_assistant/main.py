from fastapi import FastAPI
from routes import webhook, slack, prd_parser
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI()
app.include_router(webhook.router, prefix="/webhook")
app.include_router(slack.router, prefix="/slack")
app.include_router(prd_parser.router, prefix="/prd")