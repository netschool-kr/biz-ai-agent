from dotenv import load_dotenv
load_dotenv()
import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver  # SQLite 기반 체크포인트
from utils import show_graph

# (Postgres 사용 시: from langgraph.checkpoint.postgres import PostgresSaver)

# 1. 상태 정의: 예시로 'result'와 'approved' 키를 상태로 사용
# class State(dict):  # TypedDict를 사용해도 무방
#     result: str
#     approved: bool
from pydantic import BaseModel
from typing import Optional

class State(BaseModel):
    user_input: str                 # e.g. prompt or necessary input (no default means required)
    result: Optional[str] = None    # default None (no result yet)
    approved: bool = False          # default False (not approved yet)

# 2. 단계별 처리 로직 정의
def ai_decision(state: State) -> State:
    state.result = "분류 결과: 정상"
    state.approved = False
    print("AI 결정 완료:", state.result)
    return state


def human_review(state: State) -> State:
    """Human-in-the-loop 단계: 사용자에게 AI 결정 내용 확인 및 승인받음"""
    print(f"AI 결정 내용: {state.result}")  # state["result"] -> state.result
    user_input = input("이 결정을 승인할까요? (yes/no): ").strip().lower()
    if user_input == "yes":
        state.approved = True  # state["approved"] -> state.approved
        print(">> 사용자 승인 완료")
    else:
        state.approved = False  # state["approved"] -> state.approved
        correction = input("수정할 결과를 입력해주세요: ")
        state.result = correction  # state["result"] -> state.result
        state.approved = True  # state["approved"] -> state.approved
        print(">> 사용자 수정 완료, 결과 승인됨")
    return state


def final_step(state: State) -> State:
    if state.approved:  # state.get("approved") -> state.approved
        print("최종 결과:", state.result)  # state["result"] -> state.result
    else:
        print("최종 결과가 승인되지 않아 프로세스를 중단합니다.")
    return state

# 3. 그래프 구성: 노드 추가 및 연결
builder = StateGraph(State)
builder.add_node("ai_decision", ai_decision)
builder.add_node("human_review", human_review)
builder.add_node("final_step", final_step)
builder.add_edge(START, "ai_decision")       # 시작 -> AI 결정
builder.add_edge("ai_decision", "human_review")  # AI 결정 -> 인간 검토
builder.add_edge("human_review", "final_step")   # 인간 검토 -> 최종 단계
builder.add_edge("final_step", END)          # 종료

# 4. 체크포인터 설정: SQLite 사용 (':memory:'는 메모리DB, 파일경로 지정 가능)
conn = sqlite3.connect(":memory:", check_same_thread=False)  # 메모리 DB에 연결
checkpointer = SqliteSaver(conn)  # Connection 객체로 SqliteSaver 생성
#checkpointer = SqliteSaver.from_conn_string(":memory:")
graph = builder.compile(checkpointer=checkpointer)
show_graph(graph)

# **체크포인트 초기화**: SQLite의 경우 처음 한 번 .setup() 필요할 수 있음
try:
    checkpointer.setup()  # PostgreSQL 사용 시 데이터베이스 테이블 생성
except Exception as e:
    pass  # 이미 초기화된 경우 발생하는 오류 무시

# 5. 그래프 실행 with Human-in-the-loop (HITL)
thread_config = {"configurable": {"thread_id": "demo1"}}
print("=== 그래프 실행 시작 ===")
initial_state = {"user_input": "사용자 입력 예시", "result": None, "approved": False}

# 첫 번째 노드부터 human_review 직전까지 실행 (human_review에서 Interrupt 예상)
for event in graph.stream(initial_state, thread_config, stream_mode="values"):
    print(event)
    # 체크포인트는 각 노드 실행 후 자동 저장됨
    pass  # event 출력 생략 (ai_decision 단계 완료)

# human_review 단계: 사용자 입력 대기 중 (그래프 일시 정지 상태)
# 사용자가 input을 통해 승인 여부를 결정하면, human_review 노드가 완료되고 상태 저장

# 그래프 재개: human_review 이후 remaining 노드(final_step) 실행
for event in graph.stream(None, thread_config, stream_mode="values"):
    pass  # final_step 단계 실행하여 결과 출력
print("=== 그래프 실행 종료 ===")
