from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator

# 1. 상태(State) 정의 및 그래프 초기화
class State(TypedDict):
    input: str
    all_actions: Annotated[List[str], operator.add]

graph = StateGraph(State)

# 2. 노드(Node) 함수 정의
def model_node(state: State):
    # 모델 노드: 다음 행동 결정 또는 응답 완료
    print("모델 노드 실행 - 결정 중...")
    # 상태에 액션 기록 추가
    return {"all_actions": ["model_decision"]}

def tool_node(state: State):
    # 툴 노드: 어떤 도구를 실행
    print("툴 노드 실행 - 도구 사용 중...")
    return {"all_actions": ["tool_action"]}

# 3. 노드를 그래프로 추가
graph.add_node("model", model_node)
graph.add_node("tools", tool_node)

# 4. 엣지(Edge) 정의
# 그래프 시작 지점 설정: 시작하면 model 노드부터 실행
graph.set_entry_point("model")
# 일반 엣지: tools 노드 실행 후 항상 model 노드로 돌아옴
graph.add_edge("tools", "model")
# 조건부 엣지: model 노드 실행 후 상태에 따라 tools 또는 END로 분기
def should_continue(state: State) -> str:
    # 항상 'continue' 반환하도록 함
    return "continue"

graph.add_conditional_edges("model", should_continue, {
    "continue": "tools",
    "end": END
})

# 5. 그래프 컴파일 및 실행
app = graph.compile()
result_state = app.invoke({"input": "Hello"})
print("그래프 실행 완료, 최종 상태:", result_state)
