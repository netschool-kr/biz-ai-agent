import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # .env 파일 로드
openai_api_key = os.getenv('OPENAI_API_KEY')
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dataclasses import dataclass

@dataclass
class AnalysisState:
    user_input: str = None       # 사용자 입력 질의
    company: str = None          # 기업 이름
    ticker: str = None           # 기업 티커(symbol)
    analysis_type: str = "general"  # 분석 유형 ("credit_risk" 또는 "general")
    analysis_summary: str = None # 분석 결과 요약
    report_saved: bool = False   # 보고서 저장 여부
    financial_data: dict = None  # 재무 데이터 (yfinance에서 수집한 데이터)

def query_interpret(state: AnalysisState) -> AnalysisState:
    """
    사용자의 질의를 LLMChain을 이용하여 해석하고, 기업 이름, 티커, 분석 유형을 추출합니다.
    모델은 입력 문장을 분석해 JSON 형태의 결과(예: {"company": "애플", "ticker": "AAPL", "analysis_type": "credit_risk"})를 반환합니다.
    """
    # ChatOpenAI 모델 초기화 (필요 시 temperature, model_name 등 조정)
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    
    # PromptTemplate 정의 - JSON 리터럴 부분에서 중괄호를 이스케이프 처리함
    prompt = PromptTemplate(
        input_variables=["user_input"],
        template="""다음 사용자 질의를 분석하여 기업 이름, 티커 및 분석 유형을 JSON 형식으로 반환하세요.
        
사용자 질의: {user_input}

규칙:
- 입력 문장에 'credit' 또는 '신용'이 포함되어 있으면 "analysis_type"은 "credit_risk"로 설정합니다.
- 그렇지 않으면 "analysis_type"은 "general"로 설정합니다.
- 기업 이름은 입력 질의의 첫 단어로 간주합니다.
- 아래 매핑을 사용하여 기업 이름으로부터 티커를 결정합니다:
    • "애플" 또는 "apple" -> "AAPL"
    • "삼성전자" -> "005930.KS"
    • "google" -> "GOOGL"
    
반환 형식은 반드시 다음과 같이 JSON 형태여야 합니다:
{{"company": "<기업명>", "ticker": "<티커>", "analysis_type": "<분석유형>"}}
"""
    )
    
    # LLMChain 생성
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # 체인을 실행하여 JSON 결과 생성
    result_json = chain.run({"user_input": state.user_input})
    
    # JSON 파싱 후 상태 업데이트
    try:
        result = json.loads(result_json)
        state.company = result.get("company", state.company)
        state.ticker = result.get("ticker", state.ticker)
        state.analysis_type = result.get("analysis_type", state.analysis_type)
    except Exception as e:
        # JSON 파싱 실패 시 기존 룰 기반 처리
        query = state.user_input.lower()
        if "credit" in query or "신용" in query:
            state.analysis_type = "credit_risk"
        else:
            state.analysis_type = "general"
        words = state.user_input.split()
        if words:
            state.company = words[0]
        company_to_ticker = {
            "애플": "AAPL",
            "삼성전자": "005930.KS",
            "google": "GOOGL",
            "apple": "AAPL"
        }
        if state.company in company_to_ticker:
            state.ticker = company_to_ticker[state.company]
        else:
            state.ticker = state.company
    return state

# 사용 예시
if __name__ == "__main__":
    # 초기 상태 생성: 사용자 입력만 설정 (나머지는 LLM에 의해 채워짐)
    initial_state = AnalysisState(user_input="애플 신용 위험 분석해줘")
    updated_state = query_interpret(initial_state)
    print("업데이트된 상태:")
    print(updated_state)
