import logging

from app.agent.graph import graph_builder
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(self):
        self.graph_app = graph_builder().compile()

    async def run(self):
        state = AgentState(
            # user_message=user_message,
            # context=context,
            # summarized_context=summarized_context,
            # data_bundle=[],
            # blocks_guide="",
        )
        try:
            result_state = await self.graph_app.ainvoke(state)
            return {"result_state": result_state}
        except Exception as e:
            logger.error(f"Error: {e}")
            raise RuntimeError("Agent request failed.")
