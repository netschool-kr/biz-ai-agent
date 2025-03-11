from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from utils import show_graph
# 상태 모델 정의
class QAState(BaseModel):
    query: str
    info: str = ""
    answer: str = ""

# 노드 함수 정의
def research_agent(state: QAState):
    """질문에 대한 정보를 검색하는 에이전트"""
    # (여기서는 간단히 하드코딩으로 응답)
    state_query = state.query
    # 예시로, 질의에 따라 미리 준비된 정보를 리턴한다 가정
    if "LangGraph" in state_query and "LangChain" in state_query:
        found = "LangGraph는 LangChain의 에이전트 워크플로 확장 프레임워크입니다."
    else:
        found = "관련 정보를 찾지 못했습니다."
    return {"info": found}

def answer_agent(state: QAState):
    """수집된 정보를 기반으로 최종 답변을 생성하는 에이전트"""
    info_text = state.info
    if "찾지 못했습니다" in info_text:
        answer_text = f"질문: '{state.query}'에 대한 답변을 찾지 못했습니다."
    else:
        answer_text = f"질문에 대한 답변: {info_text}"
    return {"answer": answer_text}

# 그래프 구성
builder = StateGraph(QAState)
builder.add_node("research_agent", research_agent)
builder.add_node("answer_agent", answer_agent)
builder.add_edge(START, "research_agent")
builder.add_edge("research_agent", "answer_agent")
builder.add_edge("answer_agent", END)
graph = builder.compile()
show_graph(graph)

# 그래프 실행
initial_state = {"query": "LangGraph와 LangChain의 차이점은?"}
final_state = graph.invoke(initial_state)
print(final_state["answer"])
