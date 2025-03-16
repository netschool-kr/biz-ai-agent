import os
import json
import openai
import schedule
import time
from newsapi import NewsApiClient
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List  
from dotenv import load_dotenv  
load_dotenv() 

# ✅ 1. 공유 정보 (State) 정의
class NewsState(TypedDict):  
    user_input: str  
    topic: str  
    model: str  
    max_articles: int  
    articles: List[dict]  
    summaries: List[dict]  
    save_path: str  

def create_initial_state(user_input: str) -> NewsState:  
    return {  
        "user_input": user_input,  
        "topic": "AI Agent",  
        "model": "gpt-3.5-turbo",  
        "max_articles": 5,  
        "articles": [],  
        "summaries": [],  
        "save_path": "news_summary.json"  
    }  
    
# ✅ 2. OpenAI API 설정
openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL_NAME="gpt-4"#"gpt-3.5-turbo"  
client = openai.Client(api_key=openai.api_key)

def parse_user_input(state: NewsState) -> NewsState:  
    print(f"🧠 사용자의 요청을 분석 중: '{state['user_input']}'")  
    prompt = f"""  
    사용자가 다음과 같이 요청했어: "{state['user_input']}"  
    1. 이 문장에서 사용자가 검색하려고 하는는 핵심 키워드를 추출해줘.  
    2. 예를 들어 "AI Agent, robot, 자율주행에 대한 최신 뉴스 검색해서 파일로 저장해줘"라고 하면 "AI Agent, robot, 자율주행"를 추출해야 해.  
    3. 키워드만 한 단어 또는 간결한 문장으로 출력해줘.  
    """  
    completion = client.chat.completions.create(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])  
    if completion.choices and completion.choices[0].message and completion.choices[0].message.content:  
        response = completion.choices[0].message.content  
        extracted_topic = response.strip()  
        if extracted_topic:  
            state["topic"] = extracted_topic  
        else:  
            state["topic"] = "AI Agent"  # 기본값 설정  
    else:  
        state["topic"] = "AI Agent"  # 기본값 설정  
    print(f"🔍 추출된 뉴스 검색 주제: {state['topic']}")  
    return state  

# ✅ 3. 뉴스 검색 (Fetch News)
import os
import requests
import re

def clean_topic(topic):
    return re.sub('[^a-zA-Z0-9 ]', '', topic).strip()

def fetch_news(state):
    cleaned_topic = clean_topic(state['topic'])
    print(f"📡 '{cleaned_topic}' 관련 최신 뉴스 검색 중...")
    try:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": cleaned_topic,
            "lang": "en",
            "sortby": "publishedAt",
            "max": state['max_articles'],
            "token": os.environ.get("GNEWS_API_KEY")
        }
        response = requests.get(url, params=params)
        data = response.json()
        state["articles"] = data.get("articles", [])
    except Exception as e:
        print(f"❌ 뉴스 검색 실패: {e}")
        state["articles"] = []
    return state

# newsapi = NewsApiClient(api_key=os.environ.get("NEWSAPI_KEY"))
# import re  
# def clean_topic(topic):  
#     return re.sub('[^a-zA-Z0-9 ]', '', topic).strip()  

# def fetch_news(state: NewsState) -> NewsState:  
#     cleaned_topic = clean_topic(state['topic'])  
#     print(f"📡 '{cleaned_topic}' 관련 최신 뉴스 검색 중...")  
#     try:  
#         response = newsapi.get_everything(q=cleaned_topic, language="en", sort_by="publishedAt", page_size=state['max_articles'])  
#         state["articles"] = response.get('articles', [])  
#     except Exception as e:  
#         print(f"❌ 뉴스 검색 실패: {e}")  
#         state["articles"] = []  
#     return state  


# ✅ 4. 뉴스 요약 (Summarize News)
def summarize_news(state: NewsState):
    """OpenAI LLM을 사용하여 뉴스 요약"""
    print("📝 뉴스 요약 진행 중...")
    summaries = []
    
    for article in state['articles']:
        title = article.get('title', '제목 없음')
        description = article.get('description', '')
        content = article.get('content', '')
        text_to_summarize = content if content else (description if description else title)
        
        try:  
            completion = client.chat.completions.create(  
                model=state['model'],  
                messages=[  
                    {"role": "system", "content": "You are a Korean translation assistant. Please Translate the news article to Korean ."},  
                    {"role": "user", "content": f"News article to translate: {text_to_summarize}"}  
                    # {"role": "system", "content": "You are a news summary assistant. Please summarize the news article."},  
                    # {"role": "user", "content": f"News article to summarize: {text_to_summarize}"}  
                ],  
                max_tokens=150,  
                temperature=0.5  
            )  
            summary = completion.choices[0].message.content.strip()  
        except Exception as e:  
            print(f"❌ Summary failed: {e}")  
            summary = "Summary failed"  
        
        summaries.append({"title": title, "url": article.get('url'), "summary": summary})

    state['summaries'] = summaries
    return state

# ✅ 5. HITL을 활용한 파일명 입력
def get_save_filename(state: NewsState):
    """사용자로부터 저장할 파일명을 입력받음"""
    print("\n💾 저장할 파일 이름을 입력하세요 (기본값: 'news_summary.json'):")
    filename = input("👉 ")
    state['save_path'] = filename.strip() if filename.strip() else "news_summary.json"
    return state

# ✅ 6. 뉴스 요약 결과 저장
def save_summaries(state: NewsState):
    """요약된 기사들을 JSON 파일로 저장"""
    print(f"📁 '{state['save_path']}' 파일로 저장 중...")
    with open(state['save_path'], "w", encoding="utf-8") as f:
        json.dump(state['summaries'], f, ensure_ascii=False, indent=2)

    print(f"✅ {len(state['summaries'])}개의 뉴스 요약이 저장되었습니다.")
    return state

# ✅ 7. Edge 연결 및 LangGraph Workflow 구성
workflow = StateGraph(NewsState)

workflow.add_node("parse_user_input", parse_user_input)
workflow.add_node("fetch_news", fetch_news)
workflow.add_node("summarize_news", summarize_news)
workflow.add_node("get_save_filename", get_save_filename)
workflow.add_node("save_summaries", save_summaries)

workflow.add_edge(START, "parse_user_input")
workflow.add_edge("parse_user_input", "fetch_news")
workflow.add_edge("fetch_news", "summarize_news")
workflow.add_edge("summarize_news", "get_save_filename")
workflow.add_edge("get_save_filename", "save_summaries")
workflow.add_edge("save_summaries", END)

graph = workflow.compile()

# ✅ 8. 실행 함수
def run_news_summary_job():
    """LangGraph 기반 뉴스 요약 워크플로우 실행"""
    user_input = input("\n💬 뉴스 검색 요청을 입력하세요 (예: 'AI Agent, robot, 자율주행 관련 최신 뉴스 요약 후 파일로 저장해줘'):\n👉 ")
    initial_state = create_initial_state(user_input)  
    final_state = graph.invoke(initial_state)

run_news_summary_job()

#  ✅ 9. 자동 실행 스케줄링
# schedule.every().day.at("09:00").do(run_news_summary_job)
# print("\n⏳ 뉴스 요약 에이전트 실행 준비 완료! 매일 09:00에 실행됩니다.")

# # ✅ 10. 무한 루프 실행 (스케줄 유지)
# while True:
#     schedule.run_pending()
#     time.sleep(60)
