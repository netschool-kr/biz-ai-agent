import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())  # .env 파일 로드
openai_api_key = os.getenv('OPENAI_API_KEY')
serpapi_api_key = os.getenv('SERPAPI_API_KEY')

# OpenAI 라이브러리에 API 키 설정
#from utils import show_graph
import openai
openai.api_key = openai_api_key

from typing import TypedDict, List, Annotated
import operator

class State(TypedDict):
    user_input: str                        # 사용자의 질문
    search_results: Annotated[List[str], operator.add]  # 검색 결과 목록 (누적 가능)
    final_answer: str                      # 최종 답변

import openai
from langchain_community.utilities import SerpAPIWrapper

# OpenAI GPT-3.5 Turbo 모델 설정 (또는 원하는 모델로 변경 가능)
MODEL_NAME = "gpt-3.5-turbo"

# LangChain의 SerpAPI 검색 래퍼 초기화 (환경 변수 SERPAPI_API_KEY를 자동사용)
search_tool = SerpAPIWrapper()  

def search_agent(state: State) -> dict:
    query = state["user_input"]
    # SerpAPI를 사용하여 웹 검색 수행
    try:
        result_str = search_tool.run(query)  # 검색 결과를 문자열로 반환
    except Exception as e:
        result_str = f"(검색 중 오류 발생: {e})"
    # 검색 결과 문자열을 리스트에 담아 반환
    return {"search_results": [result_str]}


def answer_agent(state: State) -> dict:
    query = state["user_input"]
    results = state.get("search_results", [])
    # 프롬프트 생성: 검색 결과가 있으면 이를 포함하여 질문과 함께 전달
    if results:
        # 최신 검색 결과 (리스트의 마지막 항목)만 사용하거나 합쳐서 사용
        info = "\n".join(results)
        user_content = f"사용자 질문: {query}\n\n다음은 웹 검색 정보입니다:\n{info}\n\n이 정보를 참고하여 질문에 답변해 주세요."
    else:
        user_content = f"사용자 질문: {query}"
    # 시스템 메시지 (선택사항): 답변 형식 가이드
    system_content = "당신은 다중 단계를 거쳐 질문에 답하는 지능형 비서입니다. 가능한 정확하고 간결하게 답변하세요."
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
    # OpenAI ChatCompletion 호출
    try:
        client = openai.Client(api_key=openai_api_key)
        completion = client.chat.completions.create(model=MODEL_NAME, messages=messages)        
        answer_text = completion.choices[0].message.content
    except Exception as e:
        answer_text = f"답변 생성 중 오류가 발생했습니다: {e}"
    # 최종 답변을 state에 반환
    return {"final_answer": answer_text}

def decide_next_step(state: State) -> str:
    """사용자 질문을 분석해 'search' 또는 'answer' 중 다음 스텝 결정"""
    query = state["user_input"].lower()
    # 간단한 조건: 특정 키워드가 질문에 포함되면 검색 필요
    NEED_SEARCH_KEYWORDS = ["날씨", "오늘", "내일", "어제", "현재", "검색"]
    if any(keyword in query for keyword in NEED_SEARCH_KEYWORDS):
        return {"route": "search"}   # 검색 노드로 분기
    else:
        return {"route": "answer"}   # 바로 답변 생성 노드로 분기

#그래프 초기화 및 노드 추가:
from langgraph.graph import StateGraph, START, END

# StateGraph 초기화
graph = StateGraph(State)

# 노드 추가: graph.add_node("노드이름", 함수)
graph.add_node("router", decide_next_step)    # 컨트롤러 노드
graph.add_node("search_node", search_agent)   # 검색 노드
graph.add_node("answer_node", answer_agent)   # 응답 생성 노드

# 엔트리 포인트(Entry Point):
graph.add_edge(START, "router")
#조건부 엣지(Conditional Edge)graph.add_edge("search_node", "answer_node")
graph.add_conditional_edges(
    "router",          # 조건 판단을 수행한 이전 노드
    lambda state: state["route"],   # 이미 router 함수가 반환한 state에서 "route" 값 추출
    {"search": "search_node", "answer": "answer_node"}
)

#일반 엣지(Normal Edge)
graph.add_edge("search_node", "answer_node")

#종료 엣지(End Edge)
graph.add_edge("answer_node", END)
graph = graph.compile()
#show_graph(graph)

# 그래프 실행
user_question = "서울의 내일 날씨는?"
initial_state = {"user_input": user_question}
result_state = graph.invoke(initial_state)  # 그래프 실행하여 최종 state 반환

print("질문:", user_question)
print("검색 결과 요약:", result_state.get("search_results"))
print("답변:", result_state.get("final_answer"))
