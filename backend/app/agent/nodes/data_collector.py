import logging
from typing import List
import requests

from langchain_community.document_loaders import ArxivLoader

from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)


def data_collector(state: AgentState) -> AgentState:
    """
    사용자의 의도에 따라 arxiv와 tavily를 사용하여 컨텍스트를 수집합니다.
    """
    user_message = state["user_message"]
    intent = state.get("intent", "")

    logger.info(
        f"[Data Collector] Starting data collection for user message: {user_message[:100]}..."
    )
    logger.info(f"[Data Collector] Detected intent: {intent}")

    collected_data = []

    try:
        # Arxiv에서 논문 검색
        try:
            logger.info(f"Searching Arxiv for: {user_message}")
            arxiv_loader = ArxivLoader(
                query=user_message,
                load_max_docs=3,
                load_all_available_meta=True,
            )
            arxiv_docs = arxiv_loader.load()

            for doc in arxiv_docs:
                collected_data.append(
                    {
                        "source": "arxiv",
                        "title": doc.metadata.get("Title", ""),
                        "authors": doc.metadata.get("Authors", []),
                        "published": doc.metadata.get("Published", ""),
                        "summary": doc.page_content[:1000],  # 처음 1000자만
                        "url": doc.metadata.get("Entry ID", ""),
                    }
                )
            logger.info(f"Collected {len(arxiv_docs)} papers from Arxiv")
        except Exception as e:
            logger.warning(f"Arxiv search failed: {e}")

        # Tavily에서 웹 검색 (직접 API 호출)
        if settings.TAVILY_API_KEY:
            try:
                logger.info(f"Searching Tavily for: {user_message}")
                # Tavily API 직접 호출
                tavily_url = "https://api.tavily.com/search"
                payload = {
                    "api_key": settings.TAVILY_API_KEY,
                    "query": user_message,
                    "max_results": 5,
                    "search_depth": "basic",
                }

                response = requests.post(tavily_url, json=payload, timeout=30)
                response.raise_for_status()
                results = response.json()

                # 결과 처리
                if "results" in results:
                    for item in results["results"]:
                        collected_data.append(
                            {
                                "source": "tavily",
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "content": (
                                    item.get("content", "")[:1000]
                                    if item.get("content")
                                    else ""
                                ),
                            }
                        )
                    logger.info(
                        f"Collected {len(results.get('results', []))} results from Tavily"
                    )
                else:
                    logger.warning("No results in Tavily response")
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}")
        else:
            logger.warning("TAVILY_API_KEY not set, skipping Tavily search")

        # 수집된 데이터를 문자열로 변환
        data_summary = format_collected_data(collected_data)
        state["data_collection_result"] = data_summary

        # 최종 결과 로깅
        logger.info(f"[Data Collector] Data collection completed successfully")
        logger.info(f"[Data Collector] Total items collected: {len(collected_data)}")
        arxiv_count = sum(1 for item in collected_data if item.get("source") == "arxiv")
        tavily_count = sum(
            1 for item in collected_data if item.get("source") == "tavily"
        )
        logger.info(
            f"[Data Collector] Breakdown - Arxiv: {arxiv_count}, Tavily: {tavily_count}"
        )
        logger.info(
            f"[Data Collector] Data summary length: {len(data_summary)} characters"
        )

    except Exception as e:
        logger.error(f"[Data Collector] Data collection error: {e}")
        state["data_collection_result"] = (
            f"데이터 수집 중 오류가 발생했습니다: {str(e)}"
        )

    return state


def format_collected_data(data: List[dict]) -> str:
    """수집된 데이터를 포맷팅된 문자열로 변환"""
    if not data:
        return "수집된 데이터가 없습니다."

    formatted = []
    for idx, item in enumerate(data, 1):
        if item["source"] == "arxiv":
            formatted.append(f"### 논문 {idx}: {item['title']}")
            formatted.append(f"- 저자: {', '.join(item.get('authors', []))}")
            formatted.append(f"- 발행일: {item.get('published', 'N/A')}")
            formatted.append(f"- URL: {item.get('url', 'N/A')}")
            formatted.append(f"- 요약: {item.get('summary', '')[:500]}...")
        elif item["source"] == "tavily":
            formatted.append(f"### 웹 검색 결과 {idx}: {item['title']}")
            formatted.append(f"- URL: {item.get('url', 'N/A')}")
            formatted.append(f"- 내용: {item.get('content', '')[:500]}...")
        formatted.append("")

    return "\n".join(formatted)


if __name__ == "__main__":
    import json

    state = {
        "user_message": "quantum computing trends",
        "intent": "research",
    }
    result = data_collector(state)
    print(json.dumps(result, ensure_ascii=False, indent=4))
