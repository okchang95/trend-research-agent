"""
- 유저와의 대화를 통해 요구사항을 명확히 파악합니다.
- 멀티턴 챗봇 형식의 에이전트입니다.
- 요구사항이 명확해 졌을 때, Research Agent에게 요구사항을 전달합니다.
"""

import logging
import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.core.config import Config
from app.agents.state import AgentState
from app.agents.llm import SCOPING_LLM
from app.agents.prompts import SCOPING_SYSTEM_PROMPT, SCOPING_USER_PROMPT

logger = logging.getLogger(__name__)
config = Config()


class OutputFormat(BaseModel):
    is_clarified: bool = Field(
        description="요구사항이 명확히 파악되었는지 여부. **중요**: 트렌드 분석 요청이 아닌 경우에는 반드시 False로 설정해야 합니다. 트렌드 분석 요청인 경우에만 True로 설정할 수 있습니다.",
        default=False,
    )
    reason: Optional[str] = Field(
        description="is_clarified를 True/False로 판단한 이유", default=None
    )
    subject: Optional[str] = Field(description="분석할 분야/도메인/주제", default=None)
    answer: str = Field(
        description="유저의 질문에 대한 자연스러운 대화형 응답. 반드시 마크다운 형식으로 작성해야 하며, JSON 형식이나 구조화된 데이터를 반환하지 마세요. 친절하고 부드러운 톤을 유지하되, 고정된 템플릿이나 예시를 그대로 사용하지 말고 상황에 맞게 자연스럽게 대화하세요. 불릿 포인트가 필요한 경우에만 마크다운 리스트 형식(- 또는 *)을 사용하세요. is_clarified가 True일 때는 연구를 시작한다는 안내와 함께 간단한 요약을 제공. is_clarified가 False일 때: (1) 트렌드 분석이 아닌 요청인 경우, 자연스럽게 서비스를 소개하고 할 수 있는 작업을 간단히 언급한 후 트렌드 분석으로 자연스럽게 유도 (2) 트렌드 분석 요청이지만 정보가 부족한 경우, 대화하듯이 자연스럽게 추가 정보를 물어보되, 이미 충분히 구체적인 정보가 제공되었다면 불필요한 질문을 반복하지 말고 is_clarified를 True로 설정. 첫 대화라면 자연스럽게 인사하고 서비스를 소개하되, 고정된 문구를 사용하지 말고 상황에 맞게 변형하여 사용하세요",
        default="",
    )
    brief_requirement: Optional[str] = Field(
        description="유저가 원하는 주제와 요구사항 등을 간략하게 정리한 내용. 추후 자료 조사 시에 사용될 예정. is_clarified가 True일 때는 반드시 설정해야 합니다.",
        default=None,
    )
    scope: Optional[str] = Field(
        description="트렌드 분석 범위. 사용자가 명시하지 않으면 '최신 트렌드'로 설정. 사용자가 특정 기간을 요청한 경우에만 해당 기간을 기록 (e.g. 최근 2년, 최근 5년 등)",
        default="최신 트렌드",
    )


system_prompt = SCOPING_SYSTEM_PROMPT
user_prompt = SCOPING_USER_PROMPT


async def clarify_requirement(state: AgentState):

    prompt = ChatPromptTemplate(
        messages=[
            ("system", system_prompt),
            ("user", user_prompt),
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

    state["subject"] = result.subject
    # scope가 None이거나 비어있으면 "최신 트렌드"로 설정
    state["scope"] = result.scope if result.scope else "최신 트렌드"

    # brief_requirement가 없으면 subject를 기반으로 생성
    if not result.brief_requirement or result.brief_requirement.strip() == "":
        if result.is_clarified and result.subject:
            # is_clarified가 True이고 subject가 있으면 brief_requirement를 자동 생성
            state["brief_requirement"] = f"{result.subject}에 대한 최신 트렌드 분석"
            logger.info(
                f"brief_requirement was empty, auto-generated: {state['brief_requirement']}"
            )
        else:
            state["brief_requirement"] = result.brief_requirement
    else:
        state["brief_requirement"] = result.brief_requirement

    # answer가 비어있거나 JSON 형식인 경우 기본 메시지 설정
    answer = result.answer
    if not answer or answer.strip() == "":
        if result.is_clarified:
            answer = f"{result.subject or '요청하신 주제'}에 대한 트렌드 분석을 시작하겠습니다."
        else:
            answer = (
                "안녕하세요! 어떤 주제에 대해 연구/기술 트렌드를 파악하고 싶으신가요?"
            )
    else:
        # JSON 형식이 포함되어 있는지 확인 (더 강력한 체크)
        answer_stripped = answer.strip()
        # JSON 객체 형식 체크
        if (answer_stripped.startswith("{") and answer_stripped.endswith("}")) or (
            answer_stripped.startswith("[") and answer_stripped.endswith("]")
        ):
            # JSON 형식이면 기본 메시지로 대체
            logger.warning(
                f"Answer contains JSON format, replacing with default message. Original: {answer[:100]}"
            )
            if result.is_clarified:
                answer = f"{result.subject or '요청하신 주제'}에 대한 트렌드 분석을 시작하겠습니다."
            else:
                answer = "안녕하세요! 어떤 주제에 대해 연구/기술 트렌드를 파악하고 싶으신가요?"
        # JSON 키워드가 포함되어 있는지 확인
        elif any(
            keyword in answer_stripped
            for keyword in [
                '"is_clarified"',
                '"subject"',
                '"reason"',
                '"scope"',
                '"brief_requirement"',
            ]
        ):
            logger.warning(
                f"Answer contains JSON keywords, replacing with default message. Original: {answer[:100]}"
            )
            if result.is_clarified:
                answer = f"{result.subject or '요청하신 주제'}에 대한 트렌드 분석을 시작하겠습니다."
            else:
                answer = "안녕하세요! 어떤 주제에 대해 연구/기술 트렌드를 파악하고 싶으신가요?"

    # is_clarified가 True일 때는 answer를 생성하지 않음 (researcher로 바로 진행)
    if result.is_clarified:
        # answer를 빈 문자열로 설정하여 스트리밍하지 않음
        state["answer"] = ""
    else:
        # is_clarified가 False일 때만 answer 설정
        state["answer"] = answer

    state["is_clarified"] = result.is_clarified
    state["reason"] = result.reason

    # Command를 사용하여 다음 노드 지정
    if result.is_clarified:
        # 요구사항이 명확해졌으므로 researcher 노드로 진행
        return Command(update=state, goto="researcher")
    else:
        # 요구사항이 명확하지 않으므로 종료
        return Command(update=state, goto="__end__")
