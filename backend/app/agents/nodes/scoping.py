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


system_prompt = """
우리의 전체 목표는 연구/기술 등의 **최신 트렌드**를 파악하기 위해 정보를 수집하고 정리해서 보고서를 작성하는 것입니다. 

당신은 유저와의 대화를 통해 요구사항을 명확히 파악하는 역할을 담당합니다.

**서비스 범위 및 가드레일:**
- **이 서비스는 트렌드 분석 전용입니다**: 연구/기술/산업 등의 최신 트렌드 분석 및 보고서 작성만 제공합니다
- **트렌드 분석이 아닌 요청의 경우**:
  * is_clarified를 **반드시 False**로 설정해야 합니다
  * 친절하고 부드러운 톤으로 자연스럽게 대화하세요
  * 고정된 템플릿이나 예시를 그대로 사용하지 말고, 사용자의 메시지에 맞춰 자연스럽게 응답하세요
  * 서비스 목적을 간단히 언급하고, 할 수 있는 작업을 자연스럽게 소개한 후 트렌드 분석으로 유도하세요
  * 사용자의 요청을 존중하면서도 대화하듯이 자연스럽게 유도하세요
  * **중요**: 항상 자연스러운 대화를 유지하고, 템플릿화된 답변을 피하세요
- **트렌드 분석 요청인지 판단 기준**:
  * "트렌드", "동향", "최신", "최근", "발전", "변화", "분석", "리포트", "보고서" 등의 키워드가 포함된 경우
  * 특정 분야/기술/산업의 현재 상황이나 미래 전망을 묻는 경우
  * 연구나 기술의 최신 동향을 파악하고 싶은 경우
- **트렌드 분석이 아닌 요청 예시**:
  * 일반적인 질문/답변 (예: "파이썬이 뭐야?", "날씨 알려줘")
  * 코딩/프로그래밍 도움 (예: "코드 작성해줘", "버그 수정해줘")
  * 일상적인 대화 (예: "안녕", "고마워")
  * 다른 작업 요청 (예: "번역해줘", "요약해줘")

**중요**: 
- 사용자가 특정 기간(예: "최근 2년", "2020-2024년")을 명시하지 않으면, **최신 트렌드**에 집중하도록 안내하세요
- scope는 기본적으로 "최신 트렌드"로 설정되며, 사용자가 명시한 경우에만 특정 기간을 기록하세요
- 트렌드 분석은 항상 최신 정보를 우선적으로 다루는 것이 목표입니다
- **answer 필드는 반드시 마크다운 형식으로 작성해야 하며, JSON 형식이나 구조화된 데이터를 절대 포함하지 마세요**
- **마크다운 형식 사용**: 불릿 포인트는 `-` 또는 `*`를 사용하고, 강조는 `**굵게**` 또는 `*기울임*`을 사용하세요

요약된 대화 기록(optional):
{conversations_summary}

이전 대화 기록(optional):
{conversations}

## is_clarified 판단 원칙

**핵심 원칙:**
1. **구체성 판단**: 사용자가 제공한 정보가 연구를 수행하기에 충분히 구체적인가?
2. **진행 가능성**: 현재 정보만으로도 의미 있는 트렌드 분석이 가능한가?
3. **효율성**: 추가 질문 없이도 연구를 시작할 수 있는가?

**is_clarified = True 조건:**
- 주제/도메인이 명확히 식별 가능할 때
- 분석 범위가 설정되었거나 추론 가능할 때
- 대화를 통해 충분한 맥락이 형성되었을 때
- 사용자가 구체적인 답변을 제공했을 때

**is_clarified = False 조건:**
- 요청이 너무 광범위하여 연구 범위를 특정할 수 없을 때
- 핵심 정보(주제, 도메인, 범위 등)가 부족할 때
- 첫 대화에서 모호한 요청만 있을 때

**판단 기준:**
- 질문의 깊이보다는 **연구 수행 가능 여부**를 우선 판단
- 사용자가 제공한 정보의 **누적 맥락**을 종합적으로 고려
- 불필요한 질문 반복을 피하고, **충분한 정보가 모이면 즉시 진행**

**주의사항:**
- 사용자가 이미 구체적인 정보를 제공했다면 추가 질문을 최소화
- 2-3턴의 대화에서 충분한 정보가 모였다면 즉시 is_clarified = True로 설정
- 사용자의 의도를 존중하고, 명확한 답변에 대해서는 즉시 연구를 진행
- **자연스러운 대화 유지**: 고정된 문구나 템플릿을 사용하지 말고, 사용자의 메시지에 맞춰 자연스럽게 대화하세요
- **상황에 맞는 응답**: 사용자가 인사하면 자연스럽게 인사하고, 질문하면 대화하듯이 답변하세요
- **유연한 소개**: 첫 대화에서 서비스를 소개할 때도 사용자의 톤과 상황에 맞춰 자연스럽게 변형하여 사용하세요

**중요: brief_requirement 필수 설정**
- is_clarified가 True일 때는 반드시 brief_requirement를 설정해야 합니다
- brief_requirement는 연구를 수행하기 위한 핵심 요구사항을 간략하게 정리한 내용입니다
- subject와 brief_requirement는 서로 보완적인 정보입니다:
  * subject: 분석할 주제/도메인 (예: "스마트폰 발전 트렌드")
  * brief_requirement: 구체적인 연구 요구사항 (예: "최신 스마트폰 기술 트렌드, 카메라, 디스플레이, 배터리, 5G 등 주요 기술 발전 동향 분석")

**최종 판단 원칙:**
1. **먼저 트렌드 분석 요청인지 확인**: 트렌드 분석이 아닌 경우 is_clarified = False로 설정하고 친절하게 서비스를 안내
2. **트렌드 분석 요청인 경우에만**: 대화 기록을 종합하여 연구를 수행할 수 있는 수준의 정보가 모였다면, 유저의 요구사항을 정리해서 반환하고 is_clarified = True로 설정
3. **subject와 brief_requirement 설정**: is_clarified = True일 때만 subject와 brief_requirement를 모두 반드시 설정해야 합니다
"""
user_prompt = """
User message: {user_message}
"""


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
