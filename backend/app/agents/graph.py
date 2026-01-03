import logging

from langgraph.graph import END, START, StateGraph

from app.agents.state import AgentState
from app.agents.nodes.scoping import clarify_requirement
from app.agents.nodes.researcher import researcher
from app.agents.nodes.writer import writer

logger = logging.getLogger(__name__)


def graph_builder():
    builder = StateGraph(AgentState)

    # nodes
    builder.add_node("clarify_requirement", clarify_requirement)
    builder.add_node("researcher", researcher)
    builder.add_node("writer", writer)

    # edges
    # START에서 clarify_requirement로 시작
    builder.add_edge(START, "clarify_requirement")

    # Command를 사용하므로 조건부 엣지는 제거
    # clarify_requirement 노드가 Command로 다음 노드를 지정함
    # 하지만 fallback을 위해 조건부 엣지 유지 (Command가 없을 경우 대비)
    builder.add_conditional_edges(
        "clarify_requirement",
        lambda x: x.get("is_clarified", False),
        {
            True: "researcher",
            False: END,
        },
    )

    # researcher와 writer는 Command로 다음 노드를 지정하므로
    # 엣지는 fallback으로만 유지
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", END)

    return builder


if __name__ == "__main__":
    # 그래프 시각화
    from datetime import datetime
    from pathlib import Path

    from app.agents.utils import visualize_graph

    graph = graph_builder().compile()
    save_path = (
        Path(__file__).parent.parent.parent.parent
        / "images"
        / f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    visualize_graph(graph, save_path)
