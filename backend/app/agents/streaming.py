import json
import logging
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_tool_call_query(tool_calls: Iterable[dict]) -> Dict[str, Dict[str, str]]:
    pending_tool_calls: Dict[str, Dict[str, str]] = {}
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue
        tool_call_id = tool_call.get("id", "")
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        query = tool_args.get("query", "") if isinstance(tool_args, dict) else ""

        if query and tool_call_id:
            pending_tool_calls[tool_call_id] = {
                "name": tool_name,
                "query": query,
            }
            logger.debug(
                "Stored tool call: %s -> %s: %s", tool_call_id, tool_name, query
            )

    return pending_tool_calls


def parse_tool_output(tool_output: object) -> List[Dict[str, str]]:
    if not tool_output:
        return []

    try:
        if isinstance(tool_output, str):
            try:
                parsed_output = json.loads(tool_output)
                search_results = (
                    parsed_output if isinstance(parsed_output, list) else [parsed_output]
                )
            except json.JSONDecodeError:
                search_results = []
        elif isinstance(tool_output, list):
            search_results = tool_output
        elif isinstance(tool_output, dict):
            search_results = [tool_output]
        else:
            search_results = []

        formatted_results = []
        for result in search_results[:3]:
            if isinstance(result, dict):
                formatted_results.append(
                    {
                        "title": result.get("title", result.get("Title", "")),
                        "url": result.get(
                            "url", result.get("URL", result.get("link", ""))
                        ),
                        "snippet": (
                            (
                                result.get("content")
                                or result.get("Content")
                                or result.get("summary", "")
                            )[:200]
                            if result.get("content")
                            or result.get("Content")
                            or result.get("summary")
                            else ""
                        ),
                    }
                )
        return formatted_results
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error parsing tool output: %s", exc)
        return []


def build_research_status_start(
    tool_name: str,
    tool_call_count: int,
    query: str,
) -> str:
    if "tavily" in tool_name.lower() or "search" in tool_name.lower():
        return (
            f'[{tool_call_count}] 웹 검색 실행: "{query}"'
            if query
            else f"[{tool_call_count}] 웹 검색 실행 중..."
        )
    if "arxiv" in tool_name.lower():
        return (
            f'[{tool_call_count}] 논문 검색 실행: "{query}"'
            if query
            else f"[{tool_call_count}] 논문 검색 실행 중..."
        )
    return (
        f'[{tool_call_count}] 정보 수집: "{query}"'
        if query
        else f"[{tool_call_count}] 정보 수집 중..."
    )


def build_research_status_end(tool_name: str) -> str:
    if "tavily" in tool_name.lower() or "search" in tool_name.lower():
        return "검색 결과 수신 및 분석 중..."
    if "arxiv" in tool_name.lower():
        return "논문 내용 분석 중..."
    return "수집된 정보 분석 중..."


def extract_event_node_name(event: dict) -> str:
    return (
        event.get("name", "")
        or event.get("metadata", {}).get("name", "")
        or event.get("data", {}).get("name", "")
    )


def select_graph_node(name: str) -> Optional[str]:
    for node_name in ["clarify_requirement", "researcher", "writer"]:
        if node_name in name:
            return node_name
    return None


def extract_tool_calls_from_output(output: object) -> List[dict]:
    tool_calls = None
    if hasattr(output, "tool_calls") and output.tool_calls:
        tool_calls = output.tool_calls
    elif isinstance(output, dict) and "tool_calls" in output:
        tool_calls = output.get("tool_calls", [])

    if tool_calls is None:
        return []
    return list(tool_calls)


def extract_streaming_content(chunk: object) -> Optional[str]:
    if hasattr(chunk, "content") and chunk.content:
        return chunk.content
    if isinstance(chunk, dict) and "content" in chunk:
        return chunk.get("content", "")
    return None


def should_filter_json(streaming_buffer: str) -> Tuple[bool, bool]:
    json_keywords = [
        '"is_clarified"',
        '"subject"',
        '"reason"',
        '"scope"',
        '"brief_requirement"',
        '"answer"',
        '"is_clarified":',
        '"subject":',
        '"reason":',
        '"scope":',
        '"brief_requirement":',
        '"answer":',
    ]
    is_json = any(keyword in streaming_buffer for keyword in json_keywords)

    buffer_stripped = streaming_buffer.strip()
    starts_with_json = buffer_stripped.startswith("{") or buffer_stripped.startswith("[")

    return is_json or starts_with_json, starts_with_json
