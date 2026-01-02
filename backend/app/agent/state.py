from typing import TypedDict


class AgentState(TypedDict):
    # input
    user_message: str

    # 1. intent analysis
    intent: str
    intent_analysis_reason: str
    answer: str

    # 2. data collection
    data_collection_result: str

    # 3. generate response
    response: str
