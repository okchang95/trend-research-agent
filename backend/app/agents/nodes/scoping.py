"""
- 유저와의 대화를 통해 요구사항을 명확히 파악합니다.
- 멀티턴 챗봇 형식의 에이전트입니다.
- 요구사항이 명확해 졌을 때, Research Agent에게 요구사항을 전달합니다.
"""

import logging
import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.agents.prompts import SCOPING_SYSTEM_PROMPT, SCOPING_USER_PROMPT
from app.core.config import get_config
from app.core.llm import SCOPING_LLM

logger = logging.getLogger(__name__)
config = get_config()


class OutputFormat(BaseModel):
    is_clarified: bool = Field(
        description="요구사항이 명확히 파악되었는지 여부."
        "**중요**: 트렌드 분석 요청이 아닌 경우에는 반드시 False로 설정해야 합니다."
        "트렌드 분석 요청인 경우에만 True로 설정할 수 있습니다.",
        default=False,
    )
    reason: Optional[str] = Field(
        description="is_clarified를 True/False로 판단한 이유", default=None
    )
    subject: Optional[str] = Field(description="분석할 분야/도메인/주제", default=None)
    answer: str = Field(
        description="유저의 질문에 대한 자연스러운 대화형 응답. 반드시 마크다운 형식으로 작성해야 하며, 친절하고 부드러운 톤을 유지하되,"
        "고정된 템플릿이나 예시를 그대로 사용하지 말고 상황에 맞게 자연스럽게 대화하세요."
        "불릿 포인트가 필요한 경우에만 마크다운 리스트 형식(- 또는 *)을 사용하세요."
        "is_clarified가 False일 때: "
        "(1) 트렌드 분석이 아닌 요청인 경우, 자연스럽게 서비스를 소개하고 할 수 있는 작업을 간단히 언급한 후 트렌드 분석으로 자연스럽게 유도"
        "(2) 트렌드 분석 요청이지만 정보가 부족한 경우, 대화하듯이 자연스럽게 추가 정보를 물어보되, 이미 충분히 구체적인 정보가 제공되었다면 불필요한 질문을 반복하지 말고 is_clarified를 True로 설정."
        "첫 대화라면 자연스럽게 인사하고 서비스를 소개하되, 고정된 문구를 사용하지 말고 상황에 맞게 변형하여 사용하세요",
        default="",
    )
    brief_requirement: Optional[str] = Field(
        description="유저가 원하는 주제와 요구사항 등을 간략하게 정리한 내용. 추후 자료 조사 시에 사용될 예정. is_clarified가 True일 때는 반드시 작성해야 합니다.",
        default=None,
    )
    scope: Optional[str] = Field(
        description="트렌드 분석 범위. 사용자가 명시하지 않으면 '최신 트렌드'로 설정. 사용자가 특정 기간을 요청한 경우에만 해당 기간을 기록 (e.g. 최근 2년, 최근 5년 등)",
        default="최신 트렌드",
    )


async def clarify_requirement(state: AgentState):
    # 체인 설정
    prompt = ChatPromptTemplate(
        messages=[
            ("system", SCOPING_SYSTEM_PROMPT),
            ("user", SCOPING_USER_PROMPT),
        ]
    )
    chain = prompt | SCOPING_LLM.with_structured_output(OutputFormat)
    result = await chain.ainvoke(
        {
            "conversations_summary": state["conversations_summary"],
            "conversations": state["conversations"],
            "user_message": state["user_message"],
        }
    )
    logger.info(
        f"Scoping result: {json.dumps(result.model_dump(), ensure_ascii=False, indent=4)}"
    )

    # brief_requirement 설정: is_clarified가 True이고 비어있으면 자동 생성
    if result.is_clarified and result.subject:
        if result.brief_requirement and result.brief_requirement.strip():
            state["brief_requirement"] = result.brief_requirement.strip()
        else:
            state["brief_requirement"] = f"{result.subject}에 대한 최신 트렌드 분석"
            logger.info(
                f"brief_requirement was empty, auto-generated: {state['brief_requirement']}"
            )
    else:
        state["brief_requirement"] = result.brief_requirement or ""

    # answer 설정: is_clarified가 False일 때만 사용
    if result.is_clarified:
        state["answer"] = ""
    else:
        answer = result.answer
        if not answer or not answer.strip():
            answer = (
                "안녕하세요! 어떤 주제에 대해 연구/기술 트렌드를 파악하고 싶으신가요?"
            )
        state["answer"] = answer

    # state 업데이트
    state["is_clarified"] = result.is_clarified
    state["reason"] = result.reason
    state["subject"] = result.subject
    state["scope"] = result.scope or "최신 트렌드"

    if result.is_clarified:
        return Command(update=state, goto="researcher")
    else:
        return Command(update=state, goto=END)
