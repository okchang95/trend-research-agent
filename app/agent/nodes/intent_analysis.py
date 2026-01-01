from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from app.agent.state import AgentState
from app.agent.llm import LLMSetup


class Output(BaseModel):
    intent: str = Field(description="The intent of the user's message")
    reason: str = Field(description="The reason for the intent")
    answer: str = Field(description="The answer to the user's message")


def intent_analysis(state: AgentState) -> AgentState:
    user_message = state["user_message"]

    # set chain
    llm = LLMSetup.intent_analysis_llm
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant that analyzes the user's message and returns the intent of the user."
                "Return the intent and the reason in the JSON format. (in Korean)",
            ),
            (
                "user",
                "User message: {user_message}",
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(Output)

    result = chain.invoke({"user_message": user_message})
    state["intent"] = result.intent
    state["intent_analysis_reason"] = result.reason
    state["answer"] = result.answer
    return state


if __name__ == "__main__":
    import json

    # user_message = "I want to buy a new laptop"
    user_message = input("Enter your message: ")
    state = {"user_message": user_message}
    result = intent_analysis(state)
    print(json.dumps(result, ensure_ascii=False, indent=4))
