import logging

from langchain_core.prompts import ChatPromptTemplate

from app.agent.state import AgentState
from app.agent.llm import LLMSetup

logger = logging.getLogger(__name__)


def generate_response(state: AgentState) -> AgentState:
    """
    수집된 데이터를 바탕으로 마크다운 형식의 최종 응답을 생성합니다.
    """
    user_message = state["user_message"]
    intent = state.get("intent", "")
    intent_reason = state.get("intent_analysis_reason", "")
    collected_data = state.get("data_collection_result", "")

    logger.info(f"[Generate Response] Starting response generation")
    logger.info(f"[Generate Response] User message: {user_message[:100]}...")
    logger.info(f"[Generate Response] Intent: {intent}")
    logger.info(
        f"[Generate Response] Collected data length: {len(collected_data)} characters"
    )

    llm = LLMSetup.generate_response_llm

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 연구/기술 트렌드 리서치 전문가입니다. 
사용자의 질문에 대해 수집된 데이터를 바탕으로 체계적이고 전문적인 마크다운 형식의 리포트를 작성해주세요.

다음 형식을 따라 작성해주세요:
1. 제목과 간단한 요약
2. 주요 발견사항 (불릿 포인트)
3. 상세 분석 (수집된 데이터를 인용하며 설명)
4. 결론 및 향후 전망

마크다운 형식으로 작성하고, 코드 블록, 표, 링크 등을 적절히 활용해주세요.
모든 내용은 한국어로 작성해주세요.""",
            ),
            (
                "user",
                """사용자 질문: {user_message}
의도: {intent}
의도 분석 이유: {intent_reason}

수집된 데이터:
{collected_data}

위 정보를 바탕으로 전문적인 리서치 리포트를 마크다운 형식으로 작성해주세요.""",
            ),
        ]
    )

    chain = prompt | llm

    try:
        response = chain.invoke(
            {
                "user_message": user_message,
                "intent": intent,
                "intent_reason": intent_reason,
                "collected_data": collected_data,
            }
        )

        # LLM 응답에서 내용 추출
        if hasattr(response, "content"):
            markdown_response = response.content
        else:
            markdown_response = str(response)

        state["response"] = markdown_response

        logger.info(f"[Generate Response] Response generated successfully")
        logger.info(
            f"[Generate Response] Response length: {len(markdown_response)} characters"
        )
        logger.info(
            f"[Generate Response] Response preview: {markdown_response[:300]}..."
        )

    except Exception as e:
        logger.error(f"[Generate Response] Error generating response: {e}")
        state["response"] = f"응답 생성 중 오류가 발생했습니다: {str(e)}"

    return state


if __name__ == "__main__":
    import json

    state = {
        "user_message": "quantum computing trends",
        "intent": "research",
        "intent_analysis_reason": "사용자가 양자 컴퓨팅 트렌드에 대해 조사하고 싶어함",
        "data_collection_result": "Test data collection result",
    }
    result = generate_response(state)
    print(json.dumps(result, ensure_ascii=False, indent=4))
