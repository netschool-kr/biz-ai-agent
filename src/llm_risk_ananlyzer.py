import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # .env 파일 로드
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

import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def risk_analyzer(state: AnalysisState) -> AnalysisState:
    data = state.financial_data
    if not data:
        state.analysis_summary = "분석할 금융 데이터가 없습니다."
        return state

    # 재무 지표 추출 (값이 없으면 None)
    dte = data.get("debtToEquity")      # 부채비율 (예: 1.5 -> 150%)
    icr = data.get("interest_cover")      # 이자보상배율
    curr = data.get("currentRatio")       # 유동비율

    # LLM을 활용해 재무 지표 기반 신용 리스크 평가 요약 생성
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    
    # PromptTemplate 정의 (수치가 None인 경우 "N/A" 처리)
    prompt_template = PromptTemplate(
        input_variables=["dte", "icr", "curr"],
        template="""다음은 기업의 주요 재무 지표입니다.
부채비율 (Debt-to-Equity): {dte}
이자보상배율 (Interest Coverage Ratio): {icr}
유동비율 (Current Ratio): {curr}

위 수치를 바탕으로 해당 기업의 신용 리스크를 평가하세요.
분석 결과를 한 문단의 한국어 텍스트로 작성해 주세요.
예시:
'부채비율이 높아 재무 건전성에 부담이 있으며, 이자보상배율이 낮아 이자 지급에 어려움이 예상됩니다. 또한 유동비율이 1 미만으로 단기 채무 상환에 위험이 있으므로, 해당 기업의 신용 리스크는 높은 편입니다.'
반드시 구체적인 수치와 함께 평가 내용을 포함해 주세요.
"""
    )
    
    # LLMChain 생성
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    # 입력값 준비: None이면 "N/A"로 대체
    input_values = {
        "dte": f"{dte:.2f}" if isinstance(dte, (int, float)) else "N/A",
        "icr": f"{icr:.2f}" if isinstance(icr, (int, float)) else "N/A",
        "curr": f"{curr:.2f}" if isinstance(curr, (int, float)) else "N/A"
    }
    
    # 체인 실행하여 요약 생성 (LLM이 반환하는 결과 문자열)
    try:
        summary = chain.run(input_values).strip()
    except Exception as e:
        summary = f"LLM 기반 신용 리스크 분석 생성 중 오류 발생: {e}"
    
    state.analysis_summary = summary
    return state

# 사용 예시:
if __name__ == "__main__":
    # 예시 재무 데이터 (실제 값은 yfinance로 수집한 데이터 사용)
    example_financial_data = {
        "debtToEquity": 1.5,         # 150%
        "interest_cover": 0.8,        # 낮은 이자보상배율
        "currentRatio": 0.9           # 1 미만의 유동비율
    }
    
    # 초기 상태 예시 (기타 필드는 이전 단계에서 채워졌다고 가정)
    state = AnalysisState(
        user_input="애플 신용 위험 분석해줘",
        company="애플",
        ticker="AAPL",
        analysis_type="credit_risk",
        financial_data=example_financial_data
    )
    
    updated_state = risk_analyzer(state)
    print("신용 리스크 분석 요약:")
    print(updated_state.analysis_summary)
