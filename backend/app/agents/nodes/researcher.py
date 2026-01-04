"""
연구 에이전트 노드 (ReAct 패턴)
- LangGraph 표준 방식으로 ReAct 패턴 구현
- 서브그래프를 사용하여 agent 노드와 tools 노드로 분리
- 조건부 엣지로 ReAct 루프 제어
"""

import logging
from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

from app.agents.state import AgentState
from app.agents.prompts import RESEARCH_SYSTEM_PROMPT, RESEARCH_USER_PROMPT
from app.agents.nodes.research_tools import (
    get_search_tool,
    get_arxiv_tool,
    get_tools_map,
    execute_tool,
    format_tool_result,
    create_finding_entry,
)
from app.core.llm import RESEARCHER_LLM

logger = logging.getLogger(__name__)


# ReAct 서브그래프를 위한 상태 정의
class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    findings: list
    iteration: int
    max_iterations: int


def _build_research_graph(subject: str, brief_requirement: str, current_date: str):
    """ReAct 패턴을 위한 서브그래프 빌드"""
    # 도구 초기화
    search_tool = get_search_tool()
    arxiv_tool = get_arxiv_tool()
    tools = [search_tool, arxiv_tool]

    # LLM에 도구 바인딩
    llm_with_tools = RESEARCHER_LLM.bind_tools(tools)

    MAX_ITERATIONS = 3

    # 프롬프트 구성
    system_message = SystemMessage(
        content=RESEARCH_SYSTEM_PROMPT.format(
            current_date=current_date,
            subject=subject,
            brief_requirement=brief_requirement,
            max_iterations=MAX_ITERATIONS,
        )
    )
    user_message = HumanMessage(
        content=RESEARCH_USER_PROMPT.format(
            current_date=current_date,
            subject=subject,
            brief_requirement=brief_requirement,
        )
    )

    # Agent 노드: LLM 호출 및 도구 선택
    async def agent_node(research_state: ResearchState) -> ResearchState:
        """LLM이 도구를 선택하는 노드"""
        messages = research_state["messages"]
        iteration = research_state["iteration"]
        max_iterations = research_state["max_iterations"]

        # 최대 반복 횟수 확인
        if iteration >= max_iterations:
            logger.info(f"Reached max iterations ({max_iterations})")
            return research_state

        logger.info(f"Research iteration {iteration + 1}/{max_iterations}")
        response = await llm_with_tools.ainvoke(messages)
        return {
            "messages": [response],
            "findings": research_state["findings"],
            "iteration": iteration,
            "max_iterations": max_iterations,
        }

    # Tools 노드: 도구 실행
    async def tools_node(research_state: ResearchState) -> ResearchState:
        """도구를 실행하는 노드"""
        messages = research_state["messages"]
        findings = research_state["findings"]
        iteration = research_state["iteration"]

        # 마지막 메시지에서 도구 호출 추출
        last_message = messages[-1]
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return research_state

        # 도구 맵핑 가져오기
        tools_map = get_tools_map()
        tool_messages = []

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

            # 도구 실행 (research_tools 모듈로 위임)
            tool_result, tool_type, error_message = await execute_tool(
                tool_name, tool_args, tools_map
            )

            if error_message:
                # 에러 발생 시
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: {error_message}",
                        tool_call_id=tool_id,
                    )
                )
            else:
                # 성공 시 findings에 추가
                query = tool_args.get("query", "")
                finding = create_finding_entry(query, tool_result, tool_type, iteration)
                findings.append(finding)

                # 도구 결과 포맷팅 및 메시지 추가
                formatted_result = format_tool_result(tool_result, tool_type)
                tool_messages.append(
                    ToolMessage(
                        content=formatted_result,
                        tool_call_id=tool_id,
                    )
                )

        return {
            "messages": tool_messages,
            "findings": findings,
            "iteration": iteration + 1,
            "max_iterations": research_state["max_iterations"],
        }

    # conditional edge: 종료 조건 확인
    def should_continue(research_state: ResearchState) -> Literal["continue", "end"]:
        """도구 호출이 있는지 확인하여 계속할지 종료할지 결정"""
        messages = research_state["messages"]
        iteration = research_state["iteration"]
        max_iterations = research_state["max_iterations"]

        # 마지막 메시지 확인
        if not messages:
            return "end"

        last_message = messages[-1]

        # 도구 호출이 있는지 확인
        has_tool_calls = hasattr(last_message, "tool_calls") and last_message.tool_calls

        # 최대 반복 횟수 초과 체크
        if iteration + 1 >= max_iterations:
            # tool_calls가 있으면 tools 노드를 실행하고 종료
            if has_tool_calls:
                logger.info(
                    f"Reached max iterations ({max_iterations}), but tool_calls exist. Executing tools before ending."
                )
                return "continue"
            else:
                logger.info(f"Reached max iterations ({max_iterations})")
                return "end"

        # 도구 호출이 있으면 계속, 없으면 종료
        if has_tool_calls:
            return "continue"
        else:
            logger.info("No more tool calls, research complete")
            return "end"

    # conditional edge: tools 노드에서 최대 반복 횟수 체크
    def should_continue_after_tools(
        research_state: ResearchState,
    ) -> Literal["continue", "end"]:
        """tools 노드 실행 후 계속할지 종료할지 결정"""
        iteration = research_state["iteration"]
        max_iterations = research_state["max_iterations"]

        if iteration >= max_iterations:
            logger.info(
                f"Reached max iterations ({max_iterations}) after tools execution"
            )
            return "end"
        return "continue"

    # 리서치 서브 그래프 빌드
    workflow = StateGraph(ResearchState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )
    workflow.add_conditional_edges(
        "tools",
        should_continue_after_tools,
        {
            "continue": "agent",
            "end": END,
        },
    )

    return workflow.compile(), {
        "messages": [system_message, user_message],
        "findings": [],
        "iteration": 0,
        "max_iterations": MAX_ITERATIONS,
    }


async def researcher(state: AgentState) -> Command:
    """
    연구 에이전트 메인 노드 함수 (LangGraph 표준 ReAct 패턴)
    - 서브그래프를 사용하여 agent 노드와 tools 노드로 분리
    - 조건부 엣지로 ReAct 루프 제어
    """
    state["current_node"] = "researcher"
    logger.info(f"Starting research for subject: {state.get('subject', '')}")

    subject = state.get("subject", "")
    brief_requirement = state.get("brief_requirement", "")

    # 요구사항이 없으면 연구 완료
    if not brief_requirement:
        logger.warning("No brief_requirement provided, skipping research")
        state["findings"] = []
        return Command(update=state, goto="writer")

    # 현재 날짜
    current_date = datetime.now().strftime("%Y년 %m월 %d일")

    # ReAct 서브그래프 빌드 및 초기 상태 설정
    research_graph, initial_state = _build_research_graph(
        subject, brief_requirement, current_date
    )

    # 서브그래프 실행
    final_state = await research_graph.ainvoke(initial_state)
    findings = final_state["findings"]

    # 최종 분석 및 요약
    if findings:
        logger.info(f"Research completed with {len(findings)} findings")

        # LLM에게 최종 요약 요청
        messages = final_state["messages"]

        # tool_calls가 있는 assistant 메시지가 있는지 확인하고 필터링
        # (tool message가 없는 tool_calls는 제거)
        cleaned_messages = []
        pending_tool_calls = set()

        for msg in messages:
            # assistant 메시지의 tool_calls 추적
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    pending_tool_calls.add(tool_call["id"])
                cleaned_messages.append(msg)
            # tool message는 pending_tool_calls에서 제거
            elif hasattr(msg, "tool_call_id"):
                if msg.tool_call_id in pending_tool_calls:
                    pending_tool_calls.remove(msg.tool_call_id)
                cleaned_messages.append(msg)
            # 다른 메시지는 그대로 추가
            else:
                cleaned_messages.append(msg)

        # pending_tool_calls가 남아있으면 (tool message가 없는 tool_calls) 해당 assistant 메시지 제거
        if pending_tool_calls:
            logger.warning(
                f"Found {len(pending_tool_calls)} tool_calls without tool messages. Filtering them out."
            )
            final_cleaned = []
            for msg in cleaned_messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # 이 assistant 메시지의 tool_calls 중 pending이 있는지 확인
                    has_pending = any(
                        tc["id"] in pending_tool_calls for tc in msg.tool_calls
                    )
                    if has_pending:
                        # 이 메시지는 건너뛰기
                        continue
                final_cleaned.append(msg)
            cleaned_messages = final_cleaned

        summary_prompt = HumanMessage(
            content="수집한 모든 정보를 종합하여 요약하고, 주요 발견사항을 정리하세요."
        )
        cleaned_messages.append(summary_prompt)

        final_response = await RESEARCHER_LLM.ainvoke(cleaned_messages)

        # findings에 최종 요약 추가
        findings.append(
            {
                "summary": final_response.content,
                "type": "final_summary",
            }
        )

    state["findings"] = findings
    logger.info(f"Research completed. Total findings: {len(findings)}")

    return Command(update=state, goto="writer")
