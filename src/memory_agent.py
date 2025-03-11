# 1. OpenAI API 키 설정 및 필요 라이브러리 임포트
import os, getpass
from dotenv import load_dotenv
load_dotenv()
print(os.getenv("OPENAI_API_KEY"))
from typing import Annotated
from typing_extensions import TypedDict

# LangGraph 및 LangChain 관련 클래스 임포트
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.schema import HumanMessage, AIMessage
from langchain.chat_models import ChatOpenAI
from utils import show_graph
# 2. 상태(State) 구조와 챗봇 응답 노드 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]  # 대화 메시지 목록을 상태로 유지 (add_messages로 메시지 리스트 관리)

# OpenAI ChatGPT 모델 초기화 (gpt-3.5-turbo 등 기본 모델 사용, temperature=0으로 결정론적 응답)
llm = ChatOpenAI(temperature=0)

def chatbot_node(state: State):
    # state["messages"]에는 HumanMessage/AIMessage 객체들이 순서대로 들어있습니다.
    # 최신 사용자 메시지에 모델 응답을 생성하여 반환합니다.
    response_msg = llm(state["messages"])  # 대화 히스토리를 모두 전달하여 GPT 응답 생성
    return {"messages": [response_msg]}     # 새로운 AI 메시지를 상태에 추가 반환 (add_messages 리듀서가 리스트에 붙여줌)

# 3. StateGraph 구성 및 체크포인터 설정
graph_builder = StateGraph(State)
graph_builder.add_node("Chatbot", chatbot_node)
graph_builder.add_edge(START, "Chatbot")
graph_builder.add_edge("Chatbot", END)

# 메모리 체크포인터 지정 – MemorySaver 사용 (단기 메모리 유지)&#8203;:contentReference[oaicite:31]{index=31}
from langgraph.checkpoint.memory import MemorySaver
memory_saver = MemorySaver()
graph = graph_builder.compile(checkpointer=memory_saver)  # MemorySaver로 그래프 컴파일 (상태 체크포인트 활성화)
show_graph(graph)
# ※ 영속적 저장이 필요할 경우 SQLite 체크포인터로 교체 가능 (별도 설치 필요)
# from langgraph_checkpoint_sqlite import SqliteSaver
# sqlite_saver = SqliteSaver.from_conn_string("sqlite:///chat_history.db")
# graph = graph_builder.compile(checkpointer=sqlite_saver)  # 상태가 로컬 SQLite DB에 영구 저장됨

# 4. 동일한 thread_id로 연속 대화 시나리오 실행
thread_id = "example_session_1"  # 예시 스레드 ID (실제 서비스에서는 UUID 생성 혹은 사용자별 ID 사용)
config = {"configurable": {"thread_id": thread_id}}

# 첫 번째 사용자 입력 및 응답
user_input1 = {"messages": [HumanMessage(content="Hello, I am Alice.")]}
result1 = graph.invoke(user_input1, config=config)  # 첫 대화 실행
print("AI답변 1:", result1["messages"][-1].content)  # AI의 첫 응답 출력

# 두 번째 사용자 입력 (이름을 물어봄) 및 응답
user_input2 = {"messages": [HumanMessage(content="What is my name?")]}
result2 = graph.invoke(user_input2, config=config)  # 같은 thread_id로 두 번째 대화 실행
print("AI답변 2:", result2["messages"][-1].content)  # AI의 응답 출력 (이전 대화 기억 활용 기대)
