"""
연구 도구 모듈
- 웹 검색 도구 (Tavily)
- 학술 논문 검색 도구 (Arxiv)
- 도구 결과 포맷팅 함수
- 도구 실행 로직
"""

import json
import logging
from datetime import datetime
from typing import Tuple, Optional

import httpx
from langchain_core.tools import tool
from langchain_community.tools import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper

from app.core.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


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
            return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return f"검색 중 오류가 발생했습니다: {str(e)}"


def format_tool_result(tool_result, tool_type: str) -> str:
    """
    도구 실행 결과를 사람이 읽기 쉬운 형식으로 변환

    Args:
        tool_result: 도구 실행 결과 (리스트, 딕셔너리, 또는 문자열)
        tool_type: 도구 타입 ("web_search" 또는 "arxiv")

    Returns:
        포맷팅된 문자열
    """
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


def get_search_tool():
    """Tavily 웹 검색 도구 반환"""
    return tavily_search


def get_arxiv_tool():
    """Arxiv 학술 논문 검색 도구 반환"""
    arxiv_wrapper = ArxivAPIWrapper(
        top_k_results=3,  # 상위 3개 논문만
        doc_content_chars_max=2000,  # 각 논문의 최대 문자 수
    )
    return ArxivQueryRun(api_wrapper=arxiv_wrapper)


def get_tools_map():
    """
    도구 이름 -> 도구 함수 맵핑 반환

    Returns:
        dict: 도구 이름을 키로, 도구 함수를 값으로 하는 딕셔너리
    """
    return {
        "tavily_search": get_search_tool(),
        "arxiv": get_arxiv_tool(),
    }


async def execute_tool(
    tool_name: str, tool_args: dict, tools_map: dict
) -> Tuple[Optional[object], str, Optional[str]]:
    """
    도구를 실행하고 결과를 반환

    Args:
        tool_name: 도구 이름
        tool_args: 도구 실행 인자
        tools_map: 도구 이름 -> 도구 함수 맵핑

    Returns:
        tuple: (tool_result, tool_type, error_message)
        - tool_result: 도구 실행 결과 (성공 시)
        - tool_type: 도구 타입 ("web_search" 또는 "arxiv")
        - error_message: 에러 메시지 (실패 시)
    """
    query = tool_args.get("query", "")

    # 도구 이름 정규화 및 매칭
    tool_name_lower = tool_name.lower()

    # Tavily 웹 검색 도구 매칭
    if (
        "tavily" in tool_name_lower
        or "search" in tool_name_lower
        or tool_name == "tavily_search"
    ):
        tool = tools_map.get("tavily_search")
        if not tool:
            tool = get_search_tool()

        try:
            tool_result_str = await tool.ainvoke(query)
            # JSON 문자열 파싱 시도
            try:
                tool_result = json.loads(tool_result_str)
            except json.JSONDecodeError:
                tool_result = tool_result_str
            return tool_result, "web_search", None
        except Exception as e:
            logger.error(f"Error executing tavily_search: {e}")
            return None, "web_search", str(e)

    # Arxiv 학술 논문 검색 도구 매칭
    elif tool_name == "arxiv":
        tool = tools_map.get("arxiv")
        if not tool:
            tool = get_arxiv_tool()

        try:
            tool_result = await tool.ainvoke(query)
            return tool_result, "arxiv", None
        except Exception as e:
            logger.error(f"Error executing arxiv: {e}")
            return None, "arxiv", str(e)

    # 알 수 없는 도구는 웹 검색으로 시도
    else:
        logger.warning(f"Unknown tool: {tool_name}, trying as web search")
        tool = tools_map.get("tavily_search") or get_search_tool()
        try:
            tool_result_str = await tool.ainvoke(query)
            try:
                tool_result = json.loads(tool_result_str)
            except json.JSONDecodeError:
                tool_result = tool_result_str
            return tool_result, "web_search", None
        except Exception as e:
            logger.error(f"Error executing fallback web search: {e}")
            return None, "web_search", str(e)


def create_finding_entry(
    query: str, tool_result: object, tool_type: str, iteration: int
) -> dict:
    """
    findings에 추가할 엔트리 생성

    Args:
        query: 검색 쿼리
        tool_result: 도구 실행 결과
        tool_type: 도구 타입
        iteration: 반복 횟수

    Returns:
        dict: finding 엔트리
    """
    return {
        "query": query,
        "results": tool_result,
        "tool_type": tool_type,
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
    }
