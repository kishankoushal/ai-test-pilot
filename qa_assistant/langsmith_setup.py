import os
from langsmith import Client
client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))
