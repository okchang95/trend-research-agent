from pydantic import BaseModel


class AgentRequest(BaseModel):
    user_message: str


class AgentResponse(BaseModel):
    agent_response: str
