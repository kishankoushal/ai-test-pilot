from pydantic import BaseModel

class GHAFailurePayload(BaseModel):
    log: str
    job_name: str
    commit_sha: str
