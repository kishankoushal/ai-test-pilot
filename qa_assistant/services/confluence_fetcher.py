import requests
import os

CONFLUENCE_API_BASE = "https://harness.atlassian.net/wiki/rest/api"
AUTH = (os.getenv("CONFLEUENCE_EMAIL"), os.getenv("CONFLEUENCE_API_TOKEN"))

def fetch_prd_content(page_id: str) -> str:
    url = f"{CONFLUENCE_API_BASE}/content/{page_id}?expand=body.storage"
    response = requests.get(url, auth=AUTH)
    response.raise_for_status()
    content = response.json()["body"]["storage"]["value"]
    return content  # HTML
