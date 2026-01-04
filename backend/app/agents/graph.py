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
