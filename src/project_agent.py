from dotenv import load_dotenv
load_dotenv()
from typing import Literal
from utils import show_graph
from typing import Dict, Annotated, List
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
import sqlite3

from langgraph.types import Command
from langgraph.checkpoint.sqlite import SqliteSaver  # SQLite 기반 체크포인트

class IdeaState(BaseModel):
    topic: str                # 사용자로부터 받은 아이디어 주제
    ideas: List[str] = []     # 브레인스토밍으로 나온 아이디어 목록
    research: Dict[str, str] = {}  # 자료 조사 결과 (키워드 -> 요약된 정보)
    summary: str = ""         # 최종 요약 결과

def brainstorm_agent(state: IdeaState):
    """topic을 받아 연관된 아이디어 3가지를 만들어내는 에이전트"""
    topic = state.topic
    # (예시 구현) topic 단어들을 변형하거나 조합해 3가지 아이디어 생성
    ideas = [f"{topic} 관련 아이디어 A", f"{topic} 관련 아이디어 B", f"{topic} 관련 아이디어 C"]
    return {"ideas": ideas}

# async def web_search_async(query: str):
#     results = [] 
#     # 가상의 비동기 웹 검색
#     await asyncio.sleep(2)  # 네트워크 지연 시뮬레이션
#     return results

async def web_search_async(query: str):
    # 4. User-Agent 및 Accept-Language 헤더 설정 (차단 방지)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.93 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US,en;q=0.8"
    }
    # Duduko 검색 URL 구성
    search_url = f"https://duckduckgo.com/html/?q={query}"

    # 1. aiohttp를 이용한 비동기 HTTP GET 요청
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers=headers) as response:
            html_content = await response.text()

    # 2. BeautifulSoup을 이용한 HTML 파싱
    soup = BeautifulSoup(html_content, 'html.parser')

    results = []
    # 3. 검색 결과가 포함된 HTML 요소 선택 (상위 3개 결과)
    result_items = soup.find_all('div', class_='result', limit=3)
    for item in result_items:
        title_elem = item.find('a', class_='result__a')
        snippet_elem = item.find(class_='result__snippet')
        link_elem = item.find('a', class_='result__url')
        
        # 요소가 존재하면 텍스트와 링크 추출
        title = title_elem.get_text() if title_elem else ''
        url = link_elem['href'] if link_elem else ''
        snippet = snippet_elem.get_text() if snippet_elem else ''
        
        results.append({
            "title": title,
            "url": url,
            "snippet": snippet
        })
    # 5. 결과 리스트 반환
    return results

async def research_agent(state: IdeaState):
    """ideas 리스트의 각 아이템에 대해 비동기적으로 정보를 검색하는 에이전트"""
    ideas = state.ideas
    # 아이디어 목록이 비어 있으면 즉시 빈 결과 반환
    if not ideas:
        return {"research": {}}
    
    results = {}
    # 각 아이디어에 대한 웹 검색을 병렬 수행
    coros = [web_search_async(idea) for idea in ideas]
    fetched_list = await asyncio.gather(*coros)
    
    # 결과를 딕셔너리에 정리 (idea -> info)
    for idea, info in zip(ideas, fetched_list):
        # info는 리스트 형태의 검색 결과(각 항목은 dict)
        # 이를 문자열로 변환: 각 결과의 제목과 요약을 "제목 - 요약" 형식으로 결합합니다.
        if info:
            info_str = "\n".join(
                [f"{item.get('title', '').strip()} - {item.get('snippet', '').strip()}" for item in info]
            )
        else:
            info_str = ""
        results[idea] = info_str

    return {"research": results}

def summarize_agent(state: IdeaState):
    """research 결과를 종합하여 요약을 작성하는 에이전트"""
    research_data = state.research  # Dict[str, str]
    if not research_data:
        summary_text = "조사된 정보가 없어 요약을 제공할 수 없습니다."
    else:
        # 모든 research 정보를 하나의 문자열로 합침
        combined = " ".join(research_data.values())
        # (예시로 combined 문자열을 그대로 summary로 사용)
        summary_text = combined  
    return {"summary": summary_text}


from langgraph.types import Command
from typing import Literal

def supervisor(state: IdeaState) -> Command[Literal["brainstorm_agent", "research_agent", "summarize_agent", "__end__"]]:
    # 만약 아직 아이디어를 안 냈으면 brainstorm부터
    print("supervisor:", state.ideas)
    if not state.ideas:
        return Command(goto="brainstorm_agent")
    # 아이디어는 냈으나 자료조사가 안됐으면 research로
    elif state.ideas and not state.research:
        # 만약 아이디어 개수가 0이면 바로 종료도 가능
        if len(state.ideas) == 0:
            return Command(goto=END)  # 종료
        return Command(goto="research_agent")
    # 자료조사까지 끝났으면 요약으로
    elif state.research and not state.summary:
        return Command(goto="summarize_agent")
    else:
        # 모든 단계 완료 혹은 종료 조건
        return Command(goto=END)

builder = StateGraph(IdeaState)
# 노드 등록 (Supervisor 및 각 에이전트)
builder.add_node("supervisor", supervisor)
builder.add_node("brainstorm_agent", brainstorm_agent)
builder.add_node("research_agent", research_agent)
builder.add_node("summarize_agent", summarize_agent)
# 엣지 연결: Supervisor가 모든 흐름의 중심
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "brainstorm_agent")
builder.add_edge("supervisor", "research_agent")
builder.add_edge("supervisor", "summarize_agent")
builder.add_edge("brainstorm_agent", "supervisor")
builder.add_edge("research_agent", "supervisor")
builder.add_edge("summarize_agent", "supervisor")


import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def init_checkpointer():
    conn = await aiosqlite.connect(":memory:")
    return AsyncSqliteSaver(conn)

async def main():
    checkpointer = await init_checkpointer()  # 비동기 체크포인터 생성
    graph = builder.compile(checkpointer=checkpointer)  # LangGraph 컴파일
    try:
        #show_graph(graph)
        # 실행 (thread_id 필수)
        thread_id = "idea1"
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
        state0 = {"topic": "인공지능"}  # 초기 주제 설정
        result = await graph.ainvoke(state0, config)
        print(result)
    except AttributeError as e:
        print(f"AttributeError occurred: {e}")    

asyncio.run(main())
