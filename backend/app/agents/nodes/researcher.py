"""
연구 에이전트 노드 (ReAct 패턴)
- LLM이 도구를 선택하고 사용하는 ReAct 구조
- 웹 검색 도구를 LLM에 바인딩하여 LLM이 직접 연구 수행
- 여러 라운드의 연구를 통해 깊이 있는 정보 수집
"""

import logging
from datetime import datetime
from typing import Optional
import httpx

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_community.tools import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper
from langgraph.types import Command

from app.core.config import Config
from app.agents.state import AgentState
from app.agents.llm import RESEARCHER_LLM

logger = logging.getLogger(__name__)
config = Config()


# 연구 시스템 프롬프트
research_system_prompt = """
당신은 전문 연구원입니다. 주어진 요구사항에 대해 깊이 있는 연구를 수행해야 합니다.

**현재 날짜**: {current_date}
**연구 주제**: {subject}
**요구사항**: {brief_requirement}

**중요**: 반드시 제공된 도구를 사용하여 정보를 수집해야 합니다. 도구를 사용하지 않고는 연구를 완료할 수 없습니다.

**최신 트렌드 조사 원칙**:
- 현재 날짜({current_date})를 기준으로 **최신 트렌드와 최근 정보**를 우선적으로 수집하세요
- 오래된 정보(예: 2023년 이전)보다는 **최근 1-2년간의 정보**를 중점적으로 조사하세요
- 수집한 자료의 날짜를 확인하고, 최신성이 있는지 판단하세요
- 오래된 자료만 수집되었다면, 더 최신 정보를 찾기 위해 추가 검색을 수행하세요

당신의 임무:
1. 주어진 요구사항을 분석하여 연구해야 할 핵심 질문들을 파악하세요
2. **반드시 도구를 사용하여** 정보를 수집하세요:
   - **웹 검색 도구**: 일반적인 웹 정보, 뉴스, 블로그, **최신 트렌드** 검색에 사용
   - **학술 논문 검색 도구 (arxiv)**: 학술 논문, 연구 논문, 과학적 연구 결과 검색에 사용
3. 수집한 정보의 **최신성을 확인**하고, 최신 트렌드인지 판단하세요
4. 필요하다면 추가 검색을 수행하여 더 깊이 있고 **최신의** 정보를 얻으세요

**도구 사용 필수**:
- 최신 뉴스, 트렌드, 일반 웹 정보가 필요하면 → 웹 검색 도구를 반드시 사용하세요
- 학술적 연구, 논문, 과학적 근거가 필요하면 → Arxiv 도구를 반드시 사용하세요
- 둘 다 필요하면 둘 다 사용하세요

**검색 쿼리 작성 팁**:
- "최신", "2025", "2026", "recent", "latest" 등의 키워드를 포함하여 최신 정보를 찾으세요
- 예: "{subject} 최신 트렌드 2025", "{subject} 최근 동향"

**연구 시작**: 지금 바로 도구를 사용하여 정보를 수집하기 시작하세요. 
최소 2-3개의 검색 쿼리를 실행하여 다양한 관점의 **최신** 정보를 수집하세요.

연구는 최대 {max_iterations}번의 반복을 수행할 수 있습니다.
각 반복마다 적절한 도구를 사용하여 정보를 수집하고, 결과를 분석하세요.

연구가 완료되면, 수집한 모든 정보를 종합하여 findings에 저장하세요.
"""


# Tavily API를 직접 호출하는 커스텀 도구
@tool
async def tavily_search(query: str, max_results: int = 5) -> str:
    """
    Tavily 검색 API를 사용하여 웹 검색을 수행합니다.

    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수 (기본값: 5)

    Returns:
        검색 결과를 JSON 문자열로 반환
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": config.TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            # 결과를 포맷팅
            results = []
            for result in data.get("results", []):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                    }
                )

            # JSON 문자열로 반환 (LangChain 도구 형식에 맞춤)
            import json

            return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return f"검색 중 오류가 발생했습니다: {str(e)}"


# 도구 결과를 사람이 읽기 쉬운 형식으로 변환
def format_tool_result(tool_result, tool_type: str) -> str:
    """
    도구 실행 결과를 사람이 읽기 쉬운 형식으로 변환

    Args:
        tool_result: 도구 실행 결과 (리스트, 딕셔너리, 또는 문자열)
        tool_type: 도구 타입 ("web_search" 또는 "arxiv")

    Returns:
        포맷팅된 문자열
    """
    import json

    # 문자열인 경우 JSON 파싱 시도
    if isinstance(tool_result, str):
        try:
            tool_result = json.loads(tool_result)
        except json.JSONDecodeError:
            # JSON이 아니면 그대로 반환
            return tool_result

    # 웹 검색 결과 포맷팅
    if tool_type == "web_search":
        if isinstance(tool_result, list):
            formatted_lines = []
            for i, item in enumerate(tool_result, 1):
                if isinstance(item, dict):
                    title = item.get("title", "제목 없음")
                    url = item.get("url", "")
                    content = item.get("content", "")
                    # 내용이 너무 길면 앞부분만 표시
                    content_preview = (
                        content[:300] + "..." if len(content) > 300 else content
                    )
                    formatted_lines.append(
                        f"[{i}] {title}\n" f"URL: {url}\n" f"내용: {content_preview}\n"
                    )
            return (
                "\n".join(formatted_lines)
                if formatted_lines
                else "검색 결과가 없습니다."
            )
        elif isinstance(tool_result, dict):
            title = tool_result.get("title", "제목 없음")
            url = tool_result.get("url", "")
            content = tool_result.get("content", "")
            content_preview = content[:300] + "..." if len(content) > 300 else content
            return f"제목: {title}\nURL: {url}\n내용: {content_preview}"

    # Arxiv 결과 포맷팅
    elif tool_type == "arxiv":
        if isinstance(tool_result, str):
            return tool_result
        elif isinstance(tool_result, dict):
            # Arxiv 결과는 보통 문자열로 반환되므로 그대로 사용
            return str(tool_result)

    # 기타 경우 문자열로 변환 (JSON 형식이 아닌 자연어 형식)
    if isinstance(tool_result, list):
        # 리스트를 자연어로 변환
        formatted_items = []
        for i, item in enumerate(tool_result, 1):
            if isinstance(item, dict):
                # 딕셔너리를 키-값 쌍으로 변환
                item_str = ", ".join([f"{k}: {v}" for k, v in item.items() if v])
                formatted_items.append(f"[{i}] {item_str}")
            else:
                formatted_items.append(f"[{i}] {str(item)}")
        return "\n".join(formatted_items) if formatted_items else "결과가 없습니다."
    elif isinstance(tool_result, dict):
        # 딕셔너리를 키-값 쌍으로 변환
        formatted_items = []
        for k, v in tool_result.items():
            if v:
                formatted_items.append(f"{k}: {v}")
        return "\n".join(formatted_items) if formatted_items else "결과가 없습니다."

    return str(tool_result)


# 웹 검색 도구 초기화
def get_search_tool():
    """Tavily 웹 검색 도구 반환"""
    return tavily_search


# Arxiv 학술 논문 검색 도구 초기화
def get_arxiv_tool():
    """Arxiv 학술 논문 검색 도구 반환"""
    arxiv_wrapper = ArxivAPIWrapper(
        top_k_results=3,  # 상위 3개 논문만
        doc_content_chars_max=2000,  # 각 논문의 최대 문자 수
    )
    return ArxivQueryRun(api_wrapper=arxiv_wrapper)


async def researcher(state: AgentState) -> AgentState:
    """
    연구 에이전트 메인 함수 (ReAct 패턴)
    - LLM이 도구를 선택하고 사용
    - 여러 라운드의 연구 수행
    """
    state["current_node"] = "researcher"
    logger.info(f"Starting research for subject: {state.get('subject', '')}")

    subject = state.get("subject", "")
    scope = state.get("scope", "")
    brief_requirement = state.get("brief_requirement", "")

    if not brief_requirement:
        logger.warning("No brief_requirement provided, skipping research")
        state["findings"] = []
        return state

    # 검색 도구들 초기화
    search_tool = get_search_tool()
    arxiv_tool = get_arxiv_tool()

    # 도구들을 LLM에 바인딩
    llm_with_tools = RESEARCHER_LLM.bind_tools([search_tool, arxiv_tool])

    # 현재 날짜 가져오기
    current_date = datetime.now().strftime("%Y년 %m월 %d일")

    # 시스템 프롬프트 구성
    system_message = SystemMessage(
        content=research_system_prompt.format(
            current_date=current_date,
            subject=subject,
            brief_requirement=brief_requirement,
            max_iterations=3,  # 최대 3번 반복
        )
    )

    # 초기 사용자 메시지
    user_message = HumanMessage(
        content=f"다음 요구사항에 대해 연구를 시작하세요:\n\n주제: {subject}\n요구사항: {brief_requirement}\n\n**중요**: 현재 날짜({current_date})를 기준으로 최신 트렌드와 최근 정보를 우선적으로 수집하세요."
    )

    # 메시지 히스토리 초기화
    messages = [system_message, user_message]

    # ReAct 루프: 최대 3번 반복
    max_iterations = 3
    findings = []

    for iteration in range(max_iterations):
        logger.info(f"Research iteration {iteration + 1}/{max_iterations}")

        # LLM이 도구를 선택하고 응답 생성
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        # 도구 호출이 없으면 연구 완료
        if not response.tool_calls:
            logger.info("No more tool calls, research complete")
            break

        # 도구 실행
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

            try:
                # 도구별 실행
                query = tool_args.get("query", "")

                if (
                    "tavily" in tool_name.lower()
                    or "search" in tool_name.lower()
                    or tool_name == "tavily_search"
                ):
                    # Tavily 웹 검색 도구 실행
                    tool_result_str = await search_tool.ainvoke(query)
                    # JSON 문자열을 파싱
                    import json

                    try:
                        tool_result = json.loads(tool_result_str)
                    except json.JSONDecodeError:
                        tool_result = tool_result_str
                    tool_type = "web_search"
                elif tool_name == "arxiv":
                    # Arxiv 학술 논문 검색 도구 실행
                    tool_result = await arxiv_tool.ainvoke(query)
                    tool_type = "arxiv"
                else:
                    logger.warning(f"Unknown tool: {tool_name}, trying as web search")
                    # 알 수 없는 도구는 웹 검색으로 시도
                    tool_result_str = await search_tool.ainvoke(query)
                    import json

                    try:
                        tool_result = json.loads(tool_result_str)
                    except json.JSONDecodeError:
                        tool_result = tool_result_str
                    tool_type = "web_search"

                # 결과를 findings에 추가
                findings.append(
                    {
                        "query": query,
                        "results": tool_result,
                        "tool_type": tool_type,
                        "iteration": iteration + 1,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # 도구 결과를 사람이 읽기 쉬운 형식으로 변환
                formatted_result = format_tool_result(tool_result, tool_type)

                # 도구 결과를 메시지에 추가
                tool_message = ToolMessage(
                    content=formatted_result,
                    tool_call_id=tool_id,
                )
                messages.append(tool_message)

            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                error_message = ToolMessage(
                    content=f"Error: {str(e)}",
                    tool_call_id=tool_id,
                )
                messages.append(error_message)

    # 최종 분석 및 요약
    if findings:
        logger.info(f"Research completed with {len(findings)} findings")

        # LLM에게 최종 요약 요청
        summary_prompt = HumanMessage(
            content="수집한 모든 정보를 종합하여 요약하고, 주요 발견사항을 정리하세요."
        )
        messages.append(summary_prompt)

        final_response = await RESEARCHER_LLM.ainvoke(messages)

        # findings에 최종 요약 추가
        findings.append(
            {
                "summary": final_response.content,
                "type": "final_summary",
            }
        )

    state["findings"] = findings
    logger.info(f"Research completed. Total findings: {len(findings)}")

    # Command를 사용하여 writer 노드로 진행
    return Command(update=state, goto="writer")
