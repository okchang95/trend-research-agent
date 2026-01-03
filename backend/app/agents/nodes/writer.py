"""
보고서 작성 노드
- 연구 결과(findings)를 기반으로 마크다운 형식의 종합 보고서 작성
- 테이블, 시각화 방법, 출처 포함
- 일반 LLM 체인 사용 (ReAct 아님)
"""

import logging
import json
from typing import List, Dict
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command

from app.core.config import Config
from app.agents.state import AgentState
from app.agents.llm import WRITER_LLM

logger = logging.getLogger(__name__)
config = Config()


# 보고서 작성 시스템 프롬프트
report_writing_system_prompt = """
당신은 전문 기술 보고서 작성을 담당하는 고급 연구 분석가입니다. 
수집된 연구 데이터를 바탕으로 체계적이고 전문적인 마크다운 형식의 종합 보고서를 작성해야 합니다.

**현재 날짜**: {current_date}

**최신 트렌드 분석 원칙**:
- 수집된 자료의 날짜를 확인하고, 최신성 있는 정보인지 판단하세요
- 오래된 자료(예: 2023년 이전)가 포함되어 있다면, 이를 명시하고 최신 트렌드와 구분하여 제시하세요
- 현재 날짜({current_date})를 기준으로 최신 트렌드를 강조하세요
- 자료의 최신성이 부족하다면, 보고서에 이를 명시하고 주의를 환기하세요

## 보고서 작성 원칙

### 1. 구조적 사고
- 보고서를 작성하기 전에 전체 구조를 먼저 계획하세요
- 논리적 흐름을 고려하여 섹션을 구성하세요
- 각 섹션이 명확한 목적을 가져야 합니다

### 2. 내용의 깊이
- 단순한 요약이 아닌, 심층적인 분석을 제공하세요
- 데이터 간의 연관성을 찾아 인사이트를 도출하세요
- 트렌드, 패턴, 변화를 명확히 식별하고 설명하세요

### 3. 시각적 표현
- 복잡한 정보는 테이블로 정리하세요
- 비교가 필요한 데이터는 표 형식으로 제시하세요
- 시간 흐름, 변화 추이 등을 명확히 보여주세요
- **Mermaid 다이어그램 사용 원칙**:
  * **중요**: 시각화가 실제로 의미가 있고 데이터를 명확히 전달할 수 있을 때만 사용하세요
  * 의미 없는 다이어그램이나 플레이스홀더를 생성하지 마세요
  * 데이터가 충분하고 시각화가 분석에 도움이 되는 경우에만 포함하세요
  * 사용 가능한 유형:
    - 트렌드 변화 추이: 라인 차트 (graph LR 또는 graph TD) - **시간에 따른 명확한 변화 데이터가 있을 때만**
    - 비교 분석: 바 차트 (xychart-beta) - **구체적인 수치 데이터가 있을 때만**
    - 프로세스 흐름: 플로우차트 (flowchart TD) - **명확한 단계별 프로세스가 있을 때만**
    - 관계도: 그래프 (graph) - **요소 간 관계가 명확히 정의될 수 있을 때만**
  * Mermaid 다이어그램은 ```mermaid 코드 블록으로 작성하세요
  * **시각화가 불필요하거나 데이터가 부족한 경우, Mermaid 다이어그램을 생성하지 말고 텍스트와 테이블로 설명하세요**
- 가능한 경우 ASCII 아트나 텍스트 기반 차트도 보조적으로 활용하세요

### 4. 출처 관리
- 모든 주장과 데이터에 출처를 명시하세요
- 출처는 마크다운 링크 형식으로 작성하세요: [출처 제목](URL)
- 여러 출처가 있는 경우 번호를 매겨 참조하세요
- 출처 섹션을 보고서 끝에 별도로 포함하세요

### 5. 마크다운 형식
- 제목 계층 구조를 명확히 사용하세요 (#, ##, ###)
- 리스트, 번호 목록을 적절히 활용하세요
- 강조(**굵게**, *기울임*)를 사용하여 중요 정보를 강조하세요
- 코드 블록이나 인용문이 필요하면 사용하세요

## 보고서 구조

보고서는 다음 구조를 따라야 합니다:

1. **표지 및 요약**
   - 보고서 제목
   - 작성일
   - 실행 요약 (Executive Summary)

2. **서론**
   - 연구 배경
   - 연구 목적
   - 연구 범위

3. **본문**
   - 주요 발견사항 (각 섹션별로 상세히)
   - 데이터 분석 및 해석
   - 트렌드 분석
   - 비교 분석 (테이블 활용)
   - 시각화 (Mermaid 다이어그램, ASCII 아트, 텍스트 기반 차트)

4. **결론**
   - 핵심 인사이트 요약
   - 향후 전망
   - 권장사항

5. **참고문헌 및 출처**
   - 모든 출처를 체계적으로 정리
   - URL과 함께 제목 포함

## 작성 시 주의사항

1. **정확성**: 모든 정보는 수집된 데이터에 기반해야 하며, 추측이나 가정을 피하세요
2. **객관성**: 편향되지 않은 중립적인 관점을 유지하세요
3. **완전성**: 중요한 정보를 누락하지 않도록 주의하세요
4. **가독성**: 전문가와 일반인 모두가 이해할 수 있도록 명확하게 작성하세요
5. **체계성**: 논리적 흐름과 일관된 구조를 유지하세요

## 데이터 처리 방법

수집된 findings 데이터를 분석할 때:
- 각 검색 쿼리와 그 결과를 면밀히 검토하세요
- 중복된 정보는 통합하여 제시하세요
- 상충하는 정보가 있다면 양쪽 관점을 모두 제시하세요
- 데이터의 신뢰성을 평가하여 우선순위를 정하세요
- 시간적 순서나 중요도에 따라 정보를 정렬하세요

천천히, 신중하게, 체계적으로 보고서를 작성하세요.
"""


def format_findings_for_prompt(findings: List[Dict]) -> str:
    """
    findings 데이터를 프롬프트에 사용할 수 있는 형식으로 변환

    Args:
        findings: 연구 결과 리스트

    Returns:
        포맷팅된 문자열
    """
    formatted_text = "## 수집된 연구 데이터\n\n"

    for i, finding in enumerate(findings, 1):
        if finding.get("type") == "final_summary":
            formatted_text += f"### [요약 {i}]\n"
            formatted_text += f"{finding.get('summary', '')}\n\n"
        else:
            query = finding.get("query", "")
            results = finding.get("results", [])
            iteration = finding.get("iteration", "")
            timestamp = finding.get("timestamp", "")

            formatted_text += f"### [연구 {i}] - 반복 {iteration}\n"
            formatted_text += f"**검색 쿼리**: {query}\n"
            formatted_text += f"**수집 시간**: {timestamp}\n\n"

            if results:
                formatted_text += "**검색 결과**:\n\n"

                # results가 리스트인지 확인
                if isinstance(results, list):
                    for j, result in enumerate(results, 1):
                        # result가 딕셔너리인지 확인
                        if isinstance(result, dict):
                            title = result.get("title", "제목 없음")
                            content = result.get("content", "")
                            url = result.get("url", "")

                            formatted_text += f"#### 결과 {j}\n"
                            formatted_text += f"- **제목**: {title}\n"
                            if url:
                                formatted_text += f"- **URL**: {url}\n"
                            if content:
                                # 내용이 너무 길면 앞부분만 표시
                                content_preview = (
                                    content[:500] + "..."
                                    if len(content) > 500
                                    else content
                                )
                                formatted_text += (
                                    f"- **내용 요약**: {content_preview}\n"
                                )
                            formatted_text += "\n"
                        else:
                            # result가 문자열이거나 다른 타입인 경우
                            formatted_text += f"#### 결과 {j}\n"
                            formatted_text += f"- **내용**: {str(result)[:500]}\n\n"
                else:
                    # results가 리스트가 아닌 경우 (문자열 등)
                    formatted_text += f"**결과**: {str(results)[:1000]}\n\n"

    return formatted_text


async def writer(state: AgentState) -> AgentState:
    """
    보고서 작성 노드
    - findings를 기반으로 마크다운 형식의 종합 보고서 작성
    - 일반 LLM 체인 사용 (도구 없음)
    """
    state["current_node"] = "writer"
    logger.info("Starting report writing")

    findings = state.get("findings", [])
    subject = state.get("subject", "")
    scope = state.get("scope", "")
    brief_requirement = state.get("brief_requirement", "")

    if not findings:
        logger.warning("No findings available, generating basic report")
        state["answer"] = (
            f"# {subject} 트렌드 분석 보고서\n\n연구 데이터가 수집되지 않았습니다."
        )
        return state

    # findings 데이터 포맷팅
    findings_text = format_findings_for_prompt(findings)

    # 현재 날짜 가져오기
    current_date = datetime.now().strftime("%Y년 %m월 %d일")

    # 사용자 프롬프트 템플릿 구성 (변수 사용)
    user_prompt_template = """
다음 정보를 바탕으로 전문적인 마크다운 형식의 종합 보고서를 작성하세요.

**현재 날짜**: {current_date}

## 연구 요구사항
- **주제**: {subject}
- **요구사항**: {brief_requirement}

{findings_text}

## 작성 지침

1. 위의 시스템 프롬프트에 명시된 모든 원칙과 구조를 따르세요.

2. 보고서는 마크다운 형식으로 작성하되, 다음 요소를 반드시 포함하세요:
   - 명확한 제목 계층 구조 (#, ##, ###)
   - 최소 2개 이상의 테이블 (비교, 트렌드, 통계 등)
   - 출처가 명시된 모든 주장
   - **시각적 표현 (선택적)**: 
     * **중요**: Mermaid 다이어그램은 시각화가 실제로 의미가 있고 데이터를 명확히 전달할 수 있을 때만 사용하세요
     * 구체적인 수치 데이터나 명확한 관계가 있는 경우에만 포함하세요
     * 의미 없는 다이어그램, 플레이스홀더, 또는 불완전한 다이어그램을 생성하지 마세요
     * 시각화가 불필요하거나 데이터가 부족한 경우, 텍스트와 테이블로 설명하는 것이 더 나을 수 있습니다

3. 테이블 예시 형식:
```markdown
| 항목 | 설명 | 출처 |
|------|------|------|
| 데이터1 | 설명1 | [출처1](URL1) |
| 데이터2 | 설명2 | [출처2](URL2) |
```

4. Mermaid 다이어그램 사용 가이드:
   - **사용 전 확인사항**:
     * 구체적인 수치 데이터가 있는가?
     * 시각화가 텍스트보다 정보를 더 명확히 전달하는가?
     * 다이어그램이 보고서의 핵심 내용을 보완하는가?
   - **사용하지 말아야 할 경우**:
     * 데이터가 부족하거나 추측에 기반한 경우
     * 단순한 나열이나 설명만 필요한 경우
     * 플레이스홀더나 불완전한 다이어그램을 만들 수밖에 없는 경우
   - **올바른 사용 예시** (구체적인 데이터가 있을 때만):
```markdown
```mermaid
xychart-beta
    title "2025년 플랫폼별 사용자 참여도 비교"
    x-axis [TikTok, Instagram, Twitter]
    y-axis "참여도(%)" 0 --> 100
    bar [85, 65, 45]
```
```
   - 위와 같이 구체적인 수치 데이터가 있을 때만 사용하고, 그렇지 않으면 테이블이나 텍스트로 설명하세요

5. 각 섹션에서:
   - 데이터를 분석하고 해석하세요
   - **최신 트렌드와 패턴을 식별**하세요 (현재 날짜: {current_date} 기준)
   - 수집된 자료의 날짜를 확인하고, 최신성 있는 정보인지 판단하세요
   - 오래된 자료가 포함되어 있다면, 이를 명시하고 최신 정보와 구분하여 제시하세요
   - 인사이트를 도출하세요
   - 객관적이고 중립적인 관점을 유지하세요

6. 출처는 보고서 본문에서 [^1], [^2] 형식으로 참조하고, 
   보고서 끝에 "## 참고문헌" 섹션에서 상세히 나열하세요.

7. 천천히, 신중하게, 체계적으로 작성하세요. 
   각 섹션을 완성한 후 다음 섹션으로 넘어가세요.

보고서를 작성하세요:
"""

    # 프롬프트 체인 구성
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", report_writing_system_prompt.format(current_date=current_date)),
            ("user", user_prompt_template),
        ]
    )

    chain = prompt | WRITER_LLM

    try:
        logger.info("Generating report...")
        response = await chain.ainvoke(
            {
                "current_date": current_date,
                "subject": subject,
                "brief_requirement": brief_requirement,
                "findings_text": findings_text,
            }
        )

        # 응답이 AIMessage인 경우 content 추출
        if hasattr(response, "content"):
            report = response.content
        else:
            report = str(response)

        state["answer"] = report
        logger.info(f"Report generated successfully (length: {len(report)} characters)")

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        state["answer"] = (
            f"# 보고서 생성 오류\n\n보고서 생성 중 오류가 발생했습니다: {str(e)}"
        )

    # Command를 사용하여 종료
    return Command(update=state, goto="__end__")
