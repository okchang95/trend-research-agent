# import arxiv

# # 기본 API 클라이언트 생성
# client = arxiv.Client()

# # "quantum" 키워드가 포함된 가장 최근 논문 10개 검색
# search = arxiv.Search(
#     query="quantum",
#     max_results=10,
#     sort_by=arxiv.SortCriterion.SubmittedDate,  # 제출 날짜 기준 정렬
# )

# # 검색 결과 가져오기 (제너레이터 객체 반환)
# results = client.results(search)

# # 결과 출력
# for r in results:
#     print(f"제목: {r.title}")
#     print(f"저자: {[author.name for author in r.authors]}")
#     print(f"제출일: {r.published.date()}")
#     print("-" * 20)

# # 특정 논문 ID로 검색
# search_by_id = arxiv.Search(id_list=["1605.08386v1"])
# first_result = next(client.results(search_by_id))
# print(f"\n특정 ID 논문 제목: {first_result.title}")


from langchain_community.document_loaders import ArxivLoader

# Query 에 검색하고자 하는 논문의 주제를 입력합니다.
loader = ArxivLoader(
    query="Chain of thought",
    load_max_docs=2,  # 최대 문서 수
    load_all_available_meta=True,  # 메타데이터 전체 로드 여부
)

# 문서 로드 결과출력
docs = loader.load()
print(type(docs))

for doc in docs:
    print(type(doc))
    print("########## page content: ##########")
    print(doc.page_content)
    print("########## metadata: ##########")
    print(doc.metadata)
    print("####################################")

    with open("arxiv_paper.md", "w") as f:
        f.write(doc.page_content)
    break
