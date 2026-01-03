"""
보고서 작성 노드
- 연구 결과(findings)를 기반으로 마크다운 형식의 종합 보고서 작성
- 테이블, 시각화 방법, 출처 포함
- 일반 LLM 체인 사용 (ReAct 아님)
"""

import logging
import json
from typing import List, Dict
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command

from app.core.config import Config
from app.agents.state import AgentState
from app.agents.llm import WRITER_LLM
from app.agents.prompts import (
    REPORT_WRITING_SYSTEM_PROMPT,
    REPORT_WRITING_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)
config = Config()


report_writing_system_prompt = REPORT_WRITING_SYSTEM_PROMPT


def format_findings_for_prompt(findings: List[Dict]) -> str:
    """
    findings 데이터를 프롬프트에 사용할 수 있는 형식으로 변환

    Args:
        findings: 연구 결과 리스트

    Returns:
        포맷팅된 문자열
    """
    formatted_text = "## 수집된 연구 데이터\n\n"

    for i, finding in enumerate(findings, 1):
        if finding.get("type") == "final_summary":
            formatted_text += f"### [요약 {i}]\n"
            formatted_text += f"{finding.get('summary', '')}\n\n"
        else:
            query = finding.get("query", "")
            results = finding.get("results", [])
            iteration = finding.get("iteration", "")
            timestamp = finding.get("timestamp", "")

            formatted_text += f"### [연구 {i}] - 반복 {iteration}\n"
            formatted_text += f"**검색 쿼리**: {query}\n"
            formatted_text += f"**수집 시간**: {timestamp}\n\n"

            if results:
                formatted_text += "**검색 결과**:\n\n"

                # results가 리스트인지 확인
                if isinstance(results, list):
                    for j, result in enumerate(results, 1):
                        # result가 딕셔너리인지 확인
                        if isinstance(result, dict):
                            title = result.get("title", "제목 없음")
                            content = result.get("content", "")
                            url = result.get("url", "")

                            formatted_text += f"#### 결과 {j}\n"
                            formatted_text += f"- **제목**: {title}\n"
                            if url:
                                formatted_text += f"- **URL**: {url}\n"
                            if content:
                                # 내용이 너무 길면 앞부분만 표시
                                content_preview = (
                                    content[:500] + "..."
                                    if len(content) > 500
                                    else content
                                )
                                formatted_text += (
                                    f"- **내용 요약**: {content_preview}\n"
                                )
                            formatted_text += "\n"
                        else:
                            # result가 문자열이거나 다른 타입인 경우
                            formatted_text += f"#### 결과 {j}\n"
                            formatted_text += f"- **내용**: {str(result)[:500]}\n\n"
                else:
                    # results가 리스트가 아닌 경우 (문자열 등)
                    formatted_text += f"**결과**: {str(results)[:1000]}\n\n"

    return formatted_text


async def writer(state: AgentState) -> AgentState:
    """
    보고서 작성 노드
    - findings를 기반으로 마크다운 형식의 종합 보고서 작성
    - 일반 LLM 체인 사용 (도구 없음)
    """
    state["current_node"] = "writer"
    logger.info("Starting report writing")

    findings = state.get("findings", [])
    subject = state.get("subject", "")
    scope = state.get("scope", "")
    brief_requirement = state.get("brief_requirement", "")

    if not findings:
        logger.warning("No findings available, generating basic report")
        state["answer"] = (
            f"# {subject} 트렌드 분석 보고서\n\n연구 데이터가 수집되지 않았습니다."
        )
        return state

    # findings 데이터 포맷팅
    findings_text = format_findings_for_prompt(findings)

    # 현재 날짜 가져오기
    current_date = datetime.now().strftime("%Y년 %m월 %d일")

    # 사용자 프롬프트 템플릿 구성 (변수 사용)
    user_prompt_template = REPORT_WRITING_USER_PROMPT_TEMPLATE

    # 프롬프트 체인 구성
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", report_writing_system_prompt.format(current_date=current_date)),
            ("user", user_prompt_template),
        ]
    )

    chain = prompt | WRITER_LLM

    try:
        logger.info("Generating report...")
        response = await chain.ainvoke(
            {
                "current_date": current_date,
                "subject": subject,
                "brief_requirement": brief_requirement,
                "findings_text": findings_text,
            }
        )

        # 응답이 AIMessage인 경우 content 추출
        if hasattr(response, "content"):
            report = response.content
        else:
            report = str(response)

        state["answer"] = report
        logger.info(f"Report generated successfully (length: {len(report)} characters)")

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        state["answer"] = (
            f"# 보고서 생성 오류\n\n보고서 생성 중 오류가 발생했습니다: {str(e)}"
        )

    # Command를 사용하여 종료
    return Command(update=state, goto="__end__")
