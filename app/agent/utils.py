import logging
from IPython.display import Image, display

logger = logging.getLogger(__name__)


# 그래프 시각화
def visualize_graph(graph, output_file_path):
    """
    주어진 그래프를 시각화하여 이미지로 저장하고 표시합니다.
    """
    try:
        display(
            Image(
                graph.get_graph(xray=True).draw_mermaid_png(
                    output_file_path=output_file_path
                ),
            )
        )
    except Exception as e:
        logger.error(f"Error visualizing graph: {e}")
