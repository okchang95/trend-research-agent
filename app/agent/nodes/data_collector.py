import logging
from typing import List

from langchain_community.document_loaders import ArxivLoader
from langchain_tavily import TavilySearchResults
from langchain_core.documents import Document

from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)


def data_collector(state: AgentState) -> AgentState:
    """
    사용자의 의도에 따라 arxiv와 tavily를 사용하여 컨텍스트를 수집합니다.
    """
    user_message = state["user_message"]
    intent = state.get("intent", "")
    
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
                collected_data.append({
                    "source": "arxiv",
                    "title": doc.metadata.get("Title", ""),
                    "authors": doc.metadata.get("Authors", []),
                    "published": doc.metadata.get("Published", ""),
                    "summary": doc.page_content[:1000],  # 처음 1000자만
                    "url": doc.metadata.get("Entry ID", ""),
                })
            logger.info(f"Collected {len(arxiv_docs)} papers from Arxiv")
        except Exception as e:
            logger.warning(f"Arxiv search failed: {e}")
        
        # Tavily에서 웹 검색
        try:
            logger.info(f"Searching Tavily for: {user_message}")
            tavily_search = TavilySearchResults(
                api_key=settings.TAVILY_API_KEY,
                max_results=5,
            )
            tavily_docs = tavily_search.invoke(user_message)
            
            for doc in tavily_docs:
                collected_data.append({
                    "source": "tavily",
                    "title": doc.metadata.get("title", ""),
                    "url": doc.metadata.get("url", ""),
                    "content": doc.page_content[:1000],  # 처음 1000자만
                })
            logger.info(f"Collected {len(tavily_docs)} results from Tavily")
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
        
        # 수집된 데이터를 문자열로 변환
        data_summary = format_collected_data(collected_data)
        state["data_collection_result"] = data_summary
        
    except Exception as e:
        logger.error(f"Data collection error: {e}")
        state["data_collection_result"] = f"데이터 수집 중 오류가 발생했습니다: {str(e)}"
    
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

