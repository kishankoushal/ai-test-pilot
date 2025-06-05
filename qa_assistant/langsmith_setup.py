import os
from dotenv import load_dotenv
from langsmith import Client

# Load environment variables
load_dotenv()

def get_langsmith_client():
    """Get or create a LangSmith client instance."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    
    if not api_key:
        raise ValueError(
            "LANGSMITH_API_KEY environment variable not set. "
            "Get your API key from https://smith.langchain.com."
        )
    
    return Client(api_key=api_key)

# Initialize client
client = get_langsmith_client()

def get_project_name():
    """Get the project name from environment or use default."""
    return os.getenv("LANGCHAIN_PROJECT", "test-pilot-ai")

def is_tracing_enabled():
    """Check if LangSmith tracing is enabled."""
    return os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"