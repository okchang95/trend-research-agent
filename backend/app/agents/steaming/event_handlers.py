"""
스트리밍 이벤트 핸들러 모듈

LangGraph의 astream_events에서 발생하는 이벤트를 처리하여 클라이언트에 스트리밍합니다.
- 도구 실행 시작/종료 이벤트 처리
- LLM 응답 스트리밍 처리
- 노드 전환 및 상태 변경 이벤트 처리
- answer 필드 스트리밍 처리
"""

import logging
from typing import AsyncIterator, Dict, Set, Optional
from dataclasses import dataclass, field

from langgraph.types import Command

from app.agents.steaming.streaming_utils import (
    build_research_status_end,
    build_research_status_start,
    extract_event_node_name,
    extract_streaming_content,
    extract_tool_call_query,
    extract_tool_calls_from_output,
    parse_tool_output,
    select_graph_node,
    should_filter_json,
)

logger = logging.getLogger(__name__)


@dataclass
class StreamState:
    """스트리밍 상태 관리"""

    processed_nodes: Set[str] = field(default_factory=set)
    current_streaming_text: str = ""
    current_node_name: Optional[str] = None
    streaming_buffer: str = ""
    researcher_llm_detected: bool = False
    tool_call_count: int = 0
    pending_tool_calls: Dict[str, Dict[str, str]] = field(default_factory=dict)
    final_state: Optional[Dict] = None
    last_answer: str = ""


class StreamEventHandler:
    """스트리밍 이벤트 핸들러 클래스"""

    def __init__(self):
        self.state = StreamState()

    def reset(self):
        """상태 초기화"""
        self.state = StreamState()

    async def handle_tool_start(self, event: Dict) -> AsyncIterator[Dict]:
        """도구 실행 시작 이벤트 처리"""
        if self.state.current_node_name != "researcher":
            return

        tool_name = event.get("name", "")
        parent_ids = event.get("parent_ids", [])

        # pending_tool_calls에서 쿼리 찾기
        query = ""
        for parent_id in parent_ids:
            if parent_id in self.state.pending_tool_calls:
                tool_info = self.state.pending_tool_calls[parent_id]
                if tool_info["name"] == tool_name:
                    query = tool_info["query"]
                    break

        # 조사 상태 메시지 전송
        self.state.tool_call_count += 1
        status_message = build_research_status_start(
            tool_name=tool_name,
            tool_call_count=self.state.tool_call_count,
            query=query,
        )

        yield {
            "type": "research_status",
            "message": status_message,
        }

    async def handle_tool_end(self, event: Dict) -> AsyncIterator[Dict]:
        """도구 실행 완료 이벤트 처리"""
        if self.state.current_node_name != "researcher":
            return

        tool_name = event.get("name", "")
        event_data = event.get("data", {})
        tool_output = event_data.get("output", "")

        # 도구 결과에서 링크와 스니펫 추출
        formatted_results = parse_tool_output(tool_output)

        # 조사 완료 후 결과 분석 단계 표시
        status_message = build_research_status_end(tool_name)

        # 검색 결과와 함께 상태 메시지 전송
        yield {
            "type": "research_status",
            "message": status_message,
            "results": formatted_results if formatted_results else None,
        }

        # 결과 분석 후 다음 검색 결정 단계
        yield {
            "type": "research_status",
            "message": "추가 검색 필요성 판단 중...",
        }

        self.state.researcher_llm_detected = False

    async def handle_chat_model_end(self, event: Dict) -> None:
        """LLM 응답 완료 이벤트 처리"""
        if self.state.current_node_name != "researcher":
            return

        output = event.get("data", {}).get("output", None)
        if output:
            tool_calls = extract_tool_calls_from_output(output)
            if tool_calls:
                self.state.pending_tool_calls.update(
                    extract_tool_call_query(tool_calls)
                )

    async def handle_chat_model_stream(self, event: Dict) -> AsyncIterator[Dict]:
        """LLM 스트리밍 출력 이벤트 처리"""
        # clarify_requirement 노드는 스트리밍하지 않음
        if self.state.current_node_name == "clarify_requirement":
            return

        # researcher 노드의 중간 텍스트 출력은 제거
        if self.state.current_node_name == "researcher":
            return

        # 스트리밍 중인 텍스트 청크 추출
        chunk = event.get("data", {}).get("chunk", None)
        if not chunk:
            return

        content = extract_streaming_content(chunk)
        if not content:
            return

        # JSON 필터링: 버퍼에 추가
        self.state.streaming_buffer += content

        # JSON 형식이면 필터링
        is_json, _ = should_filter_json(self.state.streaming_buffer)
        if is_json:
            logger.debug(
                "Filtered JSON content from streaming: %s",
                self.state.streaming_buffer[:100],
            )
            self.state.streaming_buffer = ""
            return

        # 버퍼가 일정 길이 이상이면 스트리밍
        if len(self.state.streaming_buffer) >= 5:
            self.state.current_streaming_text += self.state.streaming_buffer
            for char in self.state.streaming_buffer:
                yield {
                    "type": "text_chunk",
                    "char": char,
                }
            self.state.streaming_buffer = ""

    async def handle_chain_start(self, event: Dict) -> AsyncIterator[Dict]:
        """체인 시작 이벤트 처리 (노드 전환)"""
        name = extract_event_node_name(event)
        node_name = select_graph_node(name)

        if not node_name:
            # researcher 노드 내부의 세부 단계 감지
            if self.state.current_node_name == "researcher":
                async for e in self._handle_researcher_internal_chain(name):
                    yield e
            return

        if node_name in self.state.processed_nodes:
            return

        self.state.processed_nodes.add(node_name)
        logger.info(f"Node started: {node_name}")

        # 현재 노드 이름 업데이트
        self.state.current_node_name = node_name

        # researcher 노드 시작 시 세분화된 상태 표시
        if node_name == "researcher":
            self.state.researcher_llm_detected = False
            self.state.tool_call_count = 0
            yield {
                "type": "research_status",
                "message": "연구 요구사항 분석 중...",
            }
        # clarify_requirement와 writer는 진행 상태를 표시하지 않음
        elif node_name not in ["clarify_requirement", "writer"]:
            yield {
                "type": "node_start",
                "node": node_name,
                "status": "진행 중",
            }

        # 새로운 노드 시작 시 스트리밍 텍스트 및 버퍼 초기화
        # 단, clarify_requirement에서 researcher로 넘어갈 때는 스트리밍 텍스트 유지
        if node_name != "researcher":
            self.state.current_streaming_text = ""
        self.state.streaming_buffer = ""

    async def _handle_researcher_internal_chain(self, name: str) -> AsyncIterator[Dict]:
        """researcher 노드 내부의 세부 단계 감지"""
        # LLM 호출 감지 (검색 쿼리 생성 및 전략 수립)
        if not (
            "ChatOpenAI" in name
            or "ChatModel" in name
            or ("chat" in name.lower() and "model" in name.lower())
        ):
            return

        # 도구 호출이 아닌 순수 LLM 호출인 경우
        if (
            "tool" not in name.lower()
            and "bind" not in name.lower()
            and "tavily" not in name.lower()
            and "arxiv" not in name.lower()
            and not self.state.researcher_llm_detected
        ):
            self.state.researcher_llm_detected = True
            yield {
                "type": "research_status",
                "message": "검색 전략 수립 중...",
            }

    async def handle_chain_end(self, event: Dict) -> AsyncIterator[Dict]:
        """체인 완료 이벤트 처리 (노드 완료)"""
        name = extract_event_node_name(event)
        node_name = select_graph_node(name)

        if not node_name:
            return

        # 현재 노드 이름 업데이트
        self.state.current_node_name = node_name

        # 출력 데이터 추출
        output = event.get("data", {}).get("output", {})

        # Command를 사용하는 경우 output이 Command 객체일 수 있음
        # dict인지 먼저 확인 (dict.update는 메서드이므로 hasattr로는 구분 불가)
        if isinstance(output, dict):
            # dict에 "update" 키가 있는 경우
            if "update" in output:
                output = output["update"]
            elif not output:
                output = {}
        # Command 객체인 경우 (dict가 아닌 경우)
        elif isinstance(output, Command):
            output = output.update
        elif hasattr(output, "update") and not isinstance(output, dict):
            # Command 객체이지만 isinstance 체크가 실패한 경우 (fallback)
            output = output.update
        elif not output:
            output = {}

        logger.info(
            f"Node completed: {node_name}, output keys: {list(output.keys()) if isinstance(output, dict) else 'N/A'}"
        )

        # researcher 노드 완료 시 findings 전송
        if node_name == "researcher" and isinstance(output, dict):
            findings = output.get("findings", [])
            if findings:
                yield {
                    "type": "research_findings",
                    "findings": findings,
                }

        yield {
            "type": "node_complete",
            "node": node_name,
            "status": "완료",
            "state": {
                "current_node": (
                    output.get("current_node", "") if isinstance(output, dict) else ""
                ),
                "is_clarified": (
                    output.get("is_clarified", False)
                    if isinstance(output, dict)
                    else False
                ),
                "subject": (
                    output.get("subject", "") if isinstance(output, dict) else ""
                ),
                "scope": (output.get("scope", "") if isinstance(output, dict) else ""),
                "findings_count": (
                    len(output.get("findings", [])) if isinstance(output, dict) else 0
                ),
            },
        }

        # answer가 변경되었는지 확인 및 스트리밍
        async for event in self._handle_answer_streaming(node_name, output):
            yield event

    async def _handle_answer_streaming(
        self, node_name: str, output: Dict
    ) -> AsyncIterator[Dict]:
        """answer 스트리밍 처리"""
        if not isinstance(output, dict):
            return

        current_answer = output.get("answer", "")
        is_clarified = output.get("is_clarified", False)

        if not current_answer:
            return

        # is_clarified가 True이면 answer를 스트리밍하지 않음
        if node_name == "clarify_requirement" and is_clarified:
            return

        # clarify_requirement 노드의 answer도 스트리밍 (is_clarified가 False일 때만)
        if node_name == "clarify_requirement":
            if current_answer != self.state.current_streaming_text:
                remaining_text = current_answer[
                    len(self.state.current_streaming_text) :
                ]
                if remaining_text:
                    for char in remaining_text:
                        yield {
                            "type": "text_chunk",
                            "char": char,
                        }
                    self.state.current_streaming_text = current_answer

            # clarify_requirement 노드의 answer 스트리밍이 완료되었는지 확인
            if (
                current_answer == self.state.current_streaming_text
                and len(current_answer) > 0
            ):
                yield {
                    "type": "scoping_complete",
                }
                logger.info("clarify_requirement answer streaming completed")
        else:
            # 다른 노드는 기존 로직 유지
            if current_answer != self.state.current_streaming_text:
                remaining_text = current_answer[
                    len(self.state.current_streaming_text) :
                ]
                if remaining_text:
                    for char in remaining_text:
                        yield {
                            "type": "text_chunk",
                            "char": char,
                        }
                    self.state.current_streaming_text = current_answer

        # 최종 상태 업데이트
        self.state.last_answer = current_answer
        self.state.final_state = output

    async def handle_final_state(self) -> AsyncIterator[Dict]:
        """최종 상태 전송"""
        if not self.state.final_state:
            return

        final_answer = self.state.final_state.get("answer", "")

        # 마지막 남은 텍스트가 있으면 전송
        if final_answer and final_answer != self.state.last_answer:
            remaining_text = final_answer[len(self.state.last_answer) :]
            for char in remaining_text:
                yield {
                    "type": "text_chunk",
                    "char": char,
                }

        yield {
            "type": "final",
            "state": {
                "answer": final_answer,
                "is_clarified": self.state.final_state.get("is_clarified", False),
                "subject": self.state.final_state.get("subject", ""),
                "scope": self.state.final_state.get("scope", ""),
            },
        }
