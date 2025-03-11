from pydantic import BaseModel
from utils import show_graph
# 전체 에이전트 시스템의 공유 상태 모델 정의
class QAState(BaseModel):
    query: str        # 사용자 질문
    info: str = ""    # 중간 정보 (예: 검색 결과 요약)
    answer: str = ""  # 최종 답변

# 1. 정보 검색 에이전트 노드
def research_agent(state: QAState):
    """사용자의 질문을 받아 관련 정보를 찾는 에이전트"""
    query = state.query
    # (여기서는 외부 검색을 가정하고 결과를 하드코딩합니다)
    result = f"{query}에 대한 관련 데이터"
    # 검색 결과를 상태의 info 필드에 저장하여 반환
    return {"info": result}

# 2. 답변 생성 에이전트 노드
def answer_agent(state: QAState):
    """수집된 정보를 바탕으로 최종 답변을 생성하는 에이전트"""
    info_text = state.info
    if info_text:
        answer_text = f"질문 '{state.query}'에 대한 답변: {info_text}"
    else:
        answer_text = "죄송합니다, 관련 정보를 찾지 못했습니다."
    # 생성한 답변을 상태의 answer 필드에 저장하여 반환
    return {"answer": answer_text}

from langgraph.graph import StateGraph, START, END

# 상태가 QAState인 그래프 빌더 생성
builder = StateGraph(QAState)
# 노드 추가 (함수와 이름 등록)
builder.add_node("research_agent", research_agent)
builder.add_node("answer_agent", answer_agent)
# 엣지 추가: 시작 -> 검색 에이전트 -> 답변 에이전트 -> 끝
builder.add_edge(START, "research_agent")
builder.add_edge("research_agent", "answer_agent")
builder.add_edge("answer_agent", END)

# 그래프 컴파일
graph = builder.compile()
show_graph(graph)
# 그래프 실행 예시
initial_state = {"query": "LangGraph의 장점"}  # 초기 상태 딕셔너리
final_state = graph.invoke(initial_state)       # 그래프 실행
print(final_state["answer"])                    # 최종 상태에서 answer 출력
