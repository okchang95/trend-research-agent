from typing import List, TypedDict


class AgentState(TypedDict):
    # metadata
    current_node: str
    user_message: str
    conversations: List[dict]
    conversations_summary: str

    # scoping
    is_clarified: bool
    reason: str
    subject: str
    scope: str
    brief_requirement: str

    # research
    findings: List[dict]

    # writer (or scoping)
    answer: str
