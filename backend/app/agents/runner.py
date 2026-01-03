import logging
from typing import AsyncIterator, List, Dict

from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import graph_builder
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(self):
        # 메모리 체크포인터 추가 (astream_events 사용을 위해)
        memory = MemorySaver()
        self.graph_app = graph_builder().compile(checkpointer=memory)

    async def run(
        self, user_message: str, conversations: List[Dict], conversations_summary: str
    ):
        # AgentState의 모든 필수 필드 초기화
        state = AgentState(
            current_node="",
            user_message=user_message,
            conversations=conversations,
            conversations_summary=conversations_summary,
            thinking_message="",
            is_clarified=False,
            reason="",
            subject="",
            scope="",
            brief_requirement="",
            findings=[],
            answer="",
        )
        try:
            result_state = await self.graph_app.ainvoke(state)
            logger.info(f"Result state: {result_state}")
            return {
                "answer": result_state.get("answer", ""),
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            raise RuntimeError("Agent request failed.")

    async def stream(
        self, user_message: str, conversations: List[Dict], conversations_summary: str
    ) -> AsyncIterator[Dict]:
        """
        SSE를 위한 스트리밍 실행
        astream_events를 사용하여 노드 시작/완료 이벤트를 정확히 감지
        """
        import uuid

        # AgentState의 모든 필수 필드 초기화
        initial_state = AgentState(
            current_node="",
            user_message=user_message,
            conversations=conversations,
            conversations_summary=conversations_summary,
            thinking_message="",
            is_clarified=False,
            reason="",
            subject="",
            scope="",
            brief_requirement="",
            findings=[],
            answer="",
        )

        try:
            # 체크포인트용 thread_id 생성
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            final_state = None
            last_answer = ""
            processed_nodes = set()  # 처리된 노드 추적
            current_streaming_text = ""  # 현재 스트리밍 중인 텍스트
            current_node_name = None  # 현재 실행 중인 노드 이름
            streaming_buffer = ""  # JSON 필터링을 위한 버퍼
            researcher_llm_detected = False  # researcher 노드의 LLM 호출 감지 플래그
            tool_call_count = 0  # 도구 호출 횟수 추적

            # astream_events를 사용하여 노드 시작/완료 이벤트 감지
            # LLM 스트리밍을 포함한 모든 이벤트 감지
            async for event in self.graph_app.astream_events(
                initial_state,
                version="v2",
                config=config,
                include_events=[
                    "on_chain_start",
                    "on_chain_end",
                    "on_chat_model_stream",
                    "on_tool_start",
                    "on_tool_end",
                ],
            ):
                event_type = event.get("event", "")

                # 도구 실행 시작 이벤트 감지 (조사 상태 업데이트)
                if event_type == "on_tool_start":
                    # researcher 노드에서만 처리
                    if current_node_name == "researcher":
                        tool_name = event.get("name", "")
                        tool_input = event.get("data", {}).get("input", {})

                        # 쿼리 추출
                        query = ""
                        if isinstance(tool_input, dict):
                            query = tool_input.get("query", "")
                        elif isinstance(tool_input, str):
                            # 문자열인 경우 JSON 파싱 시도
                            try:
                                import json

                                tool_input_dict = json.loads(tool_input)
                                query = tool_input_dict.get("query", "")
                            except:
                                query = tool_input

                        # 조사 상태 메시지 전송 (더 구체적으로)
                        tool_call_count += 1
                        if (
                            "tavily" in tool_name.lower()
                            or "search" in tool_name.lower()
                        ):
                            if query:
                                status_message = (
                                    f'[{tool_call_count}] 웹 검색 실행: "{query}"'
                                )
                            else:
                                status_message = (
                                    f"[{tool_call_count}] 웹 검색 실행 중..."
                                )
                        elif "arxiv" in tool_name.lower():
                            if query:
                                status_message = (
                                    f'[{tool_call_count}] 논문 검색 실행: "{query}"'
                                )
                            else:
                                status_message = (
                                    f"[{tool_call_count}] 논문 검색 실행 중..."
                                )
                        else:
                            if query:
                                status_message = (
                                    f'[{tool_call_count}] 정보 수집: "{query}"'
                                )
                            else:
                                status_message = f"[{tool_call_count}] 정보 수집 중..."

                        yield {
                            "type": "research_status",
                            "message": status_message,
                        }

                # 도구 실행 완료 이벤트 감지 (조사 상태 업데이트)
                if event_type == "on_tool_end":
                    # researcher 노드에서만 처리
                    if current_node_name == "researcher":
                        tool_name = event.get("name", "")
                        tool_input = event.get("data", {}).get("input", {})
                        # tool_output 추출 - 여러 경로 시도
                        event_data = event.get("data", {})
                        tool_output = (
                            event_data.get("output")
                            or event_data.get("chunk")
                            or event.get("output")
                            or ""
                        )
                        # 디버깅을 위한 로그
                        if tool_output:
                            logger.info(
                                f"Tool output type: {type(tool_output)}, length: {len(str(tool_output)) if tool_output else 0}"
                            )
                        else:
                            logger.warning(
                                f"Tool output is empty for tool: {tool_name}, event keys: {list(event.keys())}, data keys: {list(event_data.keys()) if event_data else []}"
                            )

                        # 쿼리 추출
                        query = ""
                        if isinstance(tool_input, dict):
                            query = tool_input.get("query", "")
                        elif isinstance(tool_input, str):
                            # 문자열인 경우 JSON 파싱 시도
                            try:
                                import json

                                tool_input_dict = json.loads(tool_input)
                                query = tool_input_dict.get("query", "")
                            except:
                                query = tool_input

                        # 도구 결과에서 링크와 스니펫 추출
                        search_results = []
                        if tool_output:
                            try:
                                import json

                                # tool_output이 문자열인 경우 JSON 파싱
                                if isinstance(tool_output, str):
                                    try:
                                        parsed_output = json.loads(tool_output)
                                        if isinstance(parsed_output, list):
                                            search_results = parsed_output
                                        elif isinstance(parsed_output, dict):
                                            search_results = [parsed_output]
                                    except json.JSONDecodeError:
                                        # JSON이 아닌 경우 문자열 그대로 사용
                                        pass
                                elif isinstance(tool_output, list):
                                    search_results = tool_output
                                elif isinstance(tool_output, dict):
                                    search_results = [tool_output]

                                # 결과를 정리 (최대 3개만 표시)
                                formatted_results = []
                                for result in search_results[:3]:
                                    if isinstance(result, dict):
                                        formatted_results.append(
                                            {
                                                "title": result.get(
                                                    "title", result.get("Title", "")
                                                ),
                                                "url": result.get(
                                                    "url",
                                                    result.get(
                                                        "URL", result.get("link", "")
                                                    ),
                                                ),
                                                "snippet": (
                                                    result.get(
                                                        "content",
                                                        result.get(
                                                            "Content",
                                                            result.get("summary", ""),
                                                        ),
                                                    )[:200]
                                                    if result.get("content")
                                                    or result.get("Content")
                                                    or result.get("summary")
                                                    else ""
                                                ),
                                            }
                                        )
                            except Exception as e:
                                logger.error(f"Error parsing tool output: {e}")

                        # 조사 완료 후 결과 분석 단계 표시
                        if (
                            "tavily" in tool_name.lower()
                            or "search" in tool_name.lower()
                        ):
                            status_message = "검색 결과 수신 및 분석 중..."
                        elif "arxiv" in tool_name.lower():
                            status_message = "논문 내용 분석 중..."
                        else:
                            status_message = "수집된 정보 분석 중..."

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

                        # 판단 후 다시 전략 수립 단계로
                        researcher_llm_detected = (
                            False  # 다음 LLM 호출을 위해 플래그 리셋
                        )

                # LLM 스트리밍 출력 감지 (실시간 텍스트 스트리밍)
                if event_type == "on_chat_model_stream":
                    # clarify_requirement 노드는 스트리밍하지 않음 (구조화된 출력 사용)
                    if current_node_name == "clarify_requirement":
                        continue

                    # researcher 노드의 중간 텍스트 출력은 제거 (메타 정보만 유지)
                    if current_node_name == "researcher":
                        continue

                    # 스트리밍 중인 텍스트 청크 추출
                    chunk = event.get("data", {}).get("chunk", None)
                    if chunk:
                        content = None
                        # chunk가 AIMessageChunk인 경우
                        if hasattr(chunk, "content") and chunk.content:
                            content = chunk.content
                        # chunk가 딕셔너리인 경우
                        elif isinstance(chunk, dict) and "content" in chunk:
                            content = chunk.get("content", "")

                        if content:
                            # JSON 필터링: 버퍼에 추가
                            streaming_buffer += content

                            # JSON 키워드가 포함되어 있는지 확인 (OutputFormat 필드들)
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
                            is_json = any(
                                keyword in streaming_buffer for keyword in json_keywords
                            )

                            # JSON 형식으로 시작하는지 확인
                            buffer_stripped = streaming_buffer.strip()
                            starts_with_json = buffer_stripped.startswith(
                                "{"
                            ) or buffer_stripped.startswith("[")

                            # JSON 형식이면 필터링
                            if is_json or starts_with_json:
                                logger.debug(
                                    f"Filtered JSON content from streaming: {streaming_buffer[:100]}"
                                )
                                streaming_buffer = ""
                                continue

                            # 버퍼가 일정 길이 이상이거나 JSON이 아닌 것이 확실하면 스트리밍
                            # 버퍼가 작아도 JSON이 아니면 스트리밍 (최소 5자 이상)
                            if len(streaming_buffer) >= 5:
                                # JSON 형식이 아닌 것이 확실하면 스트리밍
                                current_streaming_text += streaming_buffer
                                for char in streaming_buffer:
                                    yield {
                                        "type": "text_chunk",
                                        "char": char,
                                    }
                                streaming_buffer = ""

                # Command 이벤트 감지 (노드 전환 시)
                elif event_type == "on_chain_start":
                    # 노드 이름 추출
                    name = (
                        event.get("name", "")
                        or event.get("metadata", {}).get("name", "")
                        or event.get("data", {}).get("name", "")
                    )

                    # 노드 이름이 우리의 노드 중 하나인지 확인
                    # 이름이 경로 형식일 수 있으므로 포함 여부로 확인
                    if any(
                        node_name in name
                        for node_name in ["clarify_requirement", "researcher", "writer"]
                    ):
                        # 정확한 노드 이름 추출
                        node_name = None
                        for n in ["clarify_requirement", "researcher", "writer"]:
                            if n in name:
                                node_name = n
                                break

                        if node_name and node_name not in processed_nodes:
                            processed_nodes.add(node_name)
                            logger.info(f"Node started: {node_name}")

                            # 현재 노드 이름 업데이트
                            current_node_name = node_name

                            # researcher 노드 시작 시 세분화된 상태 표시
                            if node_name == "researcher":
                                researcher_llm_detected = False  # 플래그 초기화
                                tool_call_count = 0  # 도구 호출 횟수 초기화
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
                                current_streaming_text = ""
                            streaming_buffer = ""

                    # researcher 노드 내부의 세부 단계 감지
                    # researcher 노드가 실행 중일 때, 내부의 모든 체인을 감지
                    if current_node_name == "researcher":
                        # 이미 처리된 노드가 아니고, researcher 노드 자체가 아닌 경우
                        # 즉, researcher 노드 내부의 체인인 경우
                        if node_name != "researcher" and node_name is None:
                            # LLM 호출 감지 (검색 쿼리 생성 및 전략 수립)
                            if (
                                "ChatOpenAI" in name
                                or "ChatModel" in name
                                or ("chat" in name.lower() and "model" in name.lower())
                            ):
                                # 도구 호출이 아닌 순수 LLM 호출인 경우
                                if (
                                    "tool" not in name.lower()
                                    and "bind" not in name.lower()
                                    and "tavily" not in name.lower()
                                    and "arxiv" not in name.lower()
                                    and not researcher_llm_detected
                                ):
                                    researcher_llm_detected = True
                                    yield {
                                        "type": "research_status",
                                        "message": "검색 전략 수립 중...",
                                    }

                # 노드 완료 이벤트 감지
                elif event_type == "on_chain_end":
                    # 노드 이름 추출
                    name = (
                        event.get("name", "")
                        or event.get("metadata", {}).get("name", "")
                        or event.get("data", {}).get("name", "")
                    )

                    # 노드 이름이 우리의 노드 중 하나인지 확인 (경로 형식 고려)
                    node_name = None
                    for n in ["clarify_requirement", "researcher", "writer"]:
                        if n in name:
                            node_name = n
                            break

                    if node_name:
                        # 현재 노드 이름 업데이트
                        current_node_name = node_name

                        # 출력 데이터 추출 (Command의 update 또는 일반 state)
                        output = event.get("data", {}).get("output", {})

                        # Command를 사용하는 경우 output이 Command 객체일 수 있음
                        # Command의 update 필드에서 실제 상태 추출
                        if hasattr(output, "update"):
                            output = output.update
                        elif isinstance(output, dict) and "update" in output:
                            output = output["update"]
                        elif not output:
                            output = {}

                        logger.info(
                            f"Node completed: {node_name}, output keys: {list(output.keys()) if isinstance(output, dict) else 'N/A'}"
                        )

                        # researcher 노드 완료 시 findings 전송
                        if node_name == "researcher" and isinstance(output, dict):
                            # 최종 요약 단계 표시 (writer 노드 시작 전에만 표시)
                            yield {
                                "type": "research_status",
                                "message": "수집된 정보 종합 및 요약 중...",
                            }

                            findings = output.get("findings", [])
                            if findings:
                                # findings를 전송 (토글 형태로 표시하기 위해)
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
                                    output.get("current_node", "")
                                    if isinstance(output, dict)
                                    else ""
                                ),
                                "is_clarified": (
                                    output.get("is_clarified", False)
                                    if isinstance(output, dict)
                                    else False
                                ),
                                "subject": (
                                    output.get("subject", "")
                                    if isinstance(output, dict)
                                    else ""
                                ),
                                "scope": (
                                    output.get("scope", "")
                                    if isinstance(output, dict)
                                    else ""
                                ),
                                "findings_count": (
                                    len(output.get("findings", []))
                                    if isinstance(output, dict)
                                    else 0
                                ),
                            },
                        }

                        # answer가 변경되었는지 확인
                        # 스트리밍으로 이미 전송된 텍스트는 제외
                        if isinstance(output, dict):
                            current_answer = output.get("answer", "")
                            # is_clarified가 True이면 answer를 스트리밍하지 않음
                            is_clarified = output.get("is_clarified", False)

                            if current_answer and not (
                                node_name == "clarify_requirement" and is_clarified
                            ):
                                # clarify_requirement 노드의 answer도 스트리밍 (is_clarified가 False일 때만)
                                if node_name == "clarify_requirement":
                                    # clarify_requirement 노드는 처음부터 스트리밍
                                    if current_answer != current_streaming_text:
                                        # 아직 스트리밍되지 않은 전체 텍스트를 스트리밍
                                        remaining_text = current_answer[
                                            len(current_streaming_text) :
                                        ]
                                        if remaining_text:
                                            for char in remaining_text:
                                                yield {
                                                    "type": "text_chunk",
                                                    "char": char,
                                                }
                                            current_streaming_text = current_answer

                                    # clarify_requirement 노드의 answer 스트리밍이 완료되었는지 확인
                                    # 스트리밍이 완료되면 scoping_complete 이벤트 전송
                                    if (
                                        current_answer == current_streaming_text
                                        and len(current_answer) > 0
                                    ):
                                        yield {
                                            "type": "scoping_complete",
                                        }
                                        logger.info(
                                            "clarify_requirement answer streaming completed"
                                        )
                                else:
                                    # 다른 노드는 기존 로직 유지
                                    if current_answer != current_streaming_text:
                                        # 스트리밍으로 전송되지 않은 부분만 확인
                                        remaining_text = current_answer[
                                            len(current_streaming_text) :
                                        ]
                                        if remaining_text:
                                            for char in remaining_text:
                                                yield {
                                                    "type": "text_chunk",
                                                    "char": char,
                                                }
                                            current_streaming_text = current_answer

                                # 최종 상태 업데이트
                                last_answer = current_answer
                                final_state = output

            # 최종 상태 전송
            if final_state:
                final_answer = final_state.get("answer", "")
                # 마지막 남은 텍스트가 있으면 전송
                if final_answer and final_answer != last_answer:
                    remaining_text = final_answer[len(last_answer) :]
                    for char in remaining_text:
                        yield {
                            "type": "text_chunk",
                            "char": char,
                        }

                yield {
                    "type": "final",
                    "state": {
                        "answer": final_answer,
                        "is_clarified": final_state.get("is_clarified", False),
                        "subject": final_state.get("subject", ""),
                        "scope": final_state.get("scope", ""),
                    },
                }

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            import traceback

            traceback.print_exc()
            yield {
                "type": "error",
                "error": str(e),
            }


#     async def stream(self, user_message: str) -> AsyncIterator[dict]:
#         """SSE를 위한 스트리밍 실행"""
#         initial_state = AgentState(
#             user_message=user_message,
#             context=[],
#             conversations_summary="",
#             answer="",
#         )
#         final_state = None

#         try:
#             async for event in self.graph_app.astream(initial_state):
#                 # 각 노드의 실행 결과를 스트리밍
#                 # event는 {node_name: state} 형태의 딕셔너리
#                 for node_name, node_state in event.items():
#                     final_state = node_state  # 마지막 상태 저장
#                     yield {
#                         "type": "node_complete",
#                         "node": node_name,
#                         "state": dict(node_state),  # TypedDict를 dict로 변환
#                     }

#             # 최종 상태 전송
#             if final_state:
#                 yield {
#                     "type": "final",
#                     "state": dict(final_state),
#                 }

#         except Exception as e:
#             logger.error(f"Streaming error: {e}")
#             yield {
#                 "type": "error",
#                 "error": str(e),
#             }


# if __name__ == "__main__":
#     import asyncio

#     user_message = ""
#     runner = AgentRunner()
#     asyncio.run(runner.run("Hello, how are you?"))
