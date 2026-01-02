import logging

from langgraph.graph import END, START, StateGraph

from app.agent.state import AgentState
from app.agent.nodes.intent_analysis import intent_analysis
from app.agent.nodes.data_collector import data_collector
from app.agent.nodes.generate_response import generate_response

logger = logging.getLogger(__name__)


def graph_builder():
    builder = StateGraph(AgentState)

    # 3개 노드 추가
    builder.add_node("intent_analysis", intent_analysis)
    builder.add_node("data_collector", data_collector)
    builder.add_node("generate_response", generate_response)

    # 엣지 연결: START -> intent_analysis -> data_collector -> generate_response -> END
    builder.add_edge(START, "intent_analysis")
    builder.add_edge("intent_analysis", "data_collector")
    builder.add_edge("data_collector", "generate_response")
    builder.add_edge("generate_response", END)

    return builder


if __name__ == "__main__":
    # 그래프 시각화
    from datetime import datetime

    from app.agent.utils import visualize_graph

    graph = graph_builder().compile()
    visualize_graph(
        graph, f"images/graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
