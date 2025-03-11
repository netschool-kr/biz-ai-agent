# 상태 스키마 정의: 기업 티커, 분석 유형, 보고서 생성 여부 등 포함
from langgraph.graph import StateGraph, START, END
from utils import show_graph
from typing import TypedDict
from dataclasses import dataclass

@dataclass
class AnalysisState:
    user_input: str = None       # 사용자 입력 질의
    company: str = None          # 기업 이름
    ticker: str = None           # 기업 티커(symbol)
    financial_data: dict = None  # 재무 데이터 (yfinance에서 수집한 데이터)
    analysis_type: str = "general"  # 분석 유형 ("credit_risk" 또는 "general")
    analysis_summary: str = None # 분석 결과 요약
    report_saved: bool = False   # 보고서 저장 여부

def query_interpret(state: AnalysisState) -> AnalysisState:
    query = state.user_input.lower()  # 소문자로 변환하여 처리
    # 분석 유형 결정
    if "credit" in query or "신용" in query:
        state.analysis_type = "credit_risk"
    else:
        state.analysis_type = "general"
    # 기업명/티커 추출 (예시로 간단히 첫 단어를 기업명으로 처리)
    # 실제로는 NLP를 이용하거나 사용자 질의 포맷을 정해 파싱하는 것이 바람직
    words = state.user_input.split()
    # 예: "애플 신용 위험 분석해줘" -> 첫 단어 "애플"을 기업명으로 간주
    if words:
        state.company = words[0]
    # 기업명으로부터 티커 결정 (여기서는 간단히 몇 가지 사례를 하드코딩)
    # 실제로는 기업명-티커 매핑 DB나 API를 이용
    company_to_ticker = {
        "애플": "AAPL",
        "삼성전자": "005930.KS",
        "google": "GOOGL",
        "apple": "AAPL"
        # 필요 시 추가 매핑
    }
    if state.company in company_to_ticker:
        state.ticker = company_to_ticker[state.company]
    else:
        state.ticker = state.company  # 입력이 이미 티커라고 가정
    return state

import yfinance as yf

def data_collector(state):
    # 수집할 핵심 재무 정보 키 목록 (불필요한 필드는 제외)
    needed_keys = [
        'currentPrice', 'marketCap', 'enterpriseValue',
        'trailingPE', 'forwardPE', 'pegRatio', 'dividendYield',
        'revenueGrowth', 'earningsGrowth',
        'profitMargins', 'grossMargins', 'operatingMargins', 'ebitdaMargins',
        'returnOnAssets', 'returnOnEquity',
        'currentRatio', 'quickRatio', 'debtToEquity',
        'totalRevenue', 'revenuePerShare',
        'ebitda', 'grossProfits',
        'operatingCashflow', 'freeCashflow',
        'totalCash', 'totalDebt',
        'financialCurrency'
    ]

    try:
        # yfinance를 사용하여 해당 기업의 재무 정보 가져오기
        ticker_data = yf.Ticker(state.ticker)
        # info와 basic_info 딕셔너리 가져오기 (None 방지 위해 기본값 {} 사용)
        info_data = ticker_data.info or {}
        basic_info_data = ticker_data.basic_info or {}
        
        # 두 딕셔너리를 병합 (basic_info_data의 내용이 info_data를 업데이트)
        merged_data = info_data.copy()  # info_data를 복사하여 새로운 딕셔너리 생성
        merged_data.update(basic_info_data)  # basic_info_data의 키/값을 병합
        
        # needed_keys에 해당하는 데이터만 추출
        financial_data = {key: merged_data[key] for key in needed_keys if key in merged_data}
    except Exception as e:
        # ticker.info를 가져올 수 없는 경우 빈 딕셔너리로 설정
        info = {}

    state.financial_data = financial_data

    return state

def risk_analyzer(state: AnalysisState) -> AnalysisState:
    # financial_data가 없으면 분석 실패 메시지 설정 후 반환
    data = state.financial_data
    if not data:
        state.analysis_summary = "분석할 금융 데이터가 없습니다."
        return state

    # 재무 지표 추출 (값이 없으면 None)
    debt_ratio = data.get('debtToEquity')      # 부채비율 (Debt/Equity)
    current_ratio = data.get('currentRatio')     # 유동비율 (유동자산/유동부채)
    profit_margin = data.get('profitMargins')    # 순이익률 (순이익/매출)
    total_debt = data.get('totalDebt')           # 총부채 (절대 금액)
    roa = data.get('returnOnAssets')             # 총자산이익률 (ROA)
    roe = data.get('returnOnEquity')             # 자기자본이익률 (ROE)
    ebitda_margin = data.get('ebitdaMargins')    # EBITDA 마진

    # [1] 레버리지 분석
    if debt_ratio is not None:
        dr_percent = debt_ratio * 100
        if debt_ratio > 0.6:
            leverage_msg = f"부채비율이 {dr_percent:.1f}%로 매우 높아 레버리지 위험이 큽니다."
        elif debt_ratio > 0.4:
            leverage_msg = f"부채비율이 {dr_percent:.1f}%로 다소 높은 편입니다."
        else:
            leverage_msg = f"부채비율이 {dr_percent:.1f}%로 낮아 재무 레버리지가 안정적입니다."
    else:
        leverage_msg = "부채비율 데이터를 확인할 수 없습니다."

    if total_debt is not None:
        try:
            total_debt_str = f"{total_debt:,}"
        except Exception:
            total_debt_str = str(total_debt)
        if debt_ratio is not None and debt_ratio > 0.6:
            leverage_msg += f" 또한, 총부채 규모가 {total_debt_str}로 상당히 높습니다."
        else:
            leverage_msg += f" 총부채는 {total_debt_str}입니다."

    # [2] 유동성 분석
    if current_ratio is not None:
        if current_ratio < 1:
            liquidity_msg = f"유동비율이 {current_ratio:.2f}배로 1 미만입니다. 단기 채무 상환에 어려움이 예상됩니다."
        elif current_ratio < 1.5:
            liquidity_msg = f"유동비율이 {current_ratio:.2f}배로 다소 낮아 개선의 여지가 있습니다."
        else:
            liquidity_msg = f"유동비율이 {current_ratio:.2f}배로 양호하여 단기 채무 상환 능력이 충분합니다."
    else:
        liquidity_msg = "유동비율 데이터를 확인할 수 없습니다."

    # [3] 수익성 분석
    profitability_comments = []
    if profit_margin is not None:
        pm_percent = profit_margin * 100
        if profit_margin < 0:
            profitability_comments.append(f"순이익률이 {pm_percent:.1f}%로 마이너스입니다.")
        elif profit_margin < 0.05:
            profitability_comments.append(f"순이익률이 {pm_percent:.1f}%로 낮습니다.")
        elif profit_margin < 0.15:
            profitability_comments.append(f"순이익률이 {pm_percent:.1f}%로 보통입니다.")
        else:
            profitability_comments.append(f"순이익률이 {pm_percent:.1f}%로 매우 우수합니다.")
    if ebitda_margin is not None:
        em_percent = ebitda_margin * 100
        profitability_comments.append(f"EBITDA 마진은 {em_percent:.1f}%입니다.")
    if roa is not None:
        roa_percent = roa * 100
        profitability_comments.append(f"총자산이익률(ROA)은 {roa_percent:.1f}%입니다.")
    if roe is not None:
        roe_percent = roe * 100
        profitability_comments.append(f"자기자본이익률(ROE)은 {roe_percent:.1f}%입니다.")
    profitability_msg = " ".join(profitability_comments)
    if profit_margin is not None and ebitda_margin is not None:
        if ebitda_margin - profit_margin > 0.1:
            profitability_msg += " EBITDA 마진과 순이익률의 차이가 커 영업 외 비용 부담이 있을 수 있습니다."

    # [4] 종합 신용 리스크 평가
    risk_reasons = []
    if debt_ratio is not None and debt_ratio > 0.6:
        risk_reasons.append("높은 부채비율")
    if current_ratio is not None and current_ratio < 1:
        risk_reasons.append("낮은 유동비율")
    if profit_margin is not None and profit_margin < 0.05:
        risk_reasons.append("취약한 수익성")
    
    # 위험 수준 판단 (낮음, 보통, 높음)
    if (debt_ratio is not None and debt_ratio > 0.8) or \
       (current_ratio is not None and current_ratio < 0.8) or \
       (profit_margin is not None and profit_margin < 0):
        risk_level = "높음"
    elif len(risk_reasons) >= 2:
        risk_level = "높음"
    elif len(risk_reasons) == 0:
        risk_level = "낮음"
    else:
        risk_level = "보통"
    
    final_summary = f"종합 신용 리스크 평가: 현재 신용 위험 수준은 {risk_level}입니다."
    if risk_reasons:
        final_summary += f" (주요 위험 요인: {', '.join(risk_reasons)})"
    else:
        final_summary += " 전반적으로 재무 상태가 건전합니다."
    
    # 최종 분석 결과를 state.analysis_summary에 저장
    state.analysis_summary = (
        f"레버리지 분석: {leverage_msg}\n"
        f"유동성 분석: {liquidity_msg}\n"
        f"수익성 분석: {profitability_msg}\n"
        f"{final_summary}"
    )
    
    return state


from fpdf import FPDF

def report_generator(state: AnalysisState) -> AnalysisState:
    if not state.analysis_summary:
        state.report_saved = False
        return state
    # PDF 객체 생성
    pdf = FPDF()
    pdf.add_page()
    # 폰트 설정 (추가한 폰트 사용, 크기 14)
    pdf.add_font('NanumGothic', '', 'C:/Windows/Fonts/NanumGothic.ttf', uni=True)
    pdf.set_font('NanumGothic', '', 14)
    # 제목 추가
    pdf.cell(0, 10, f"{state.company} 신용 리스크 분석 보고서", ln=1, align='C')
    # 본문 내용 추가
    pdf.multi_cell(0, 10, state.analysis_summary)
    # PDF 저장
    report_filename = f"{state.company}_credit_report.pdf"
    pdf.output(report_filename)
    state.report_saved = True
    return state

from langgraph.graph import StateGraph, START, END

# StateGraph 객체 생성 (분석 상태 클래스를 지정)
graph = StateGraph(AnalysisState)

# 노드 추가: 이름과 처리 함수를 매핑
graph.add_node("query_interpret", query_interpret)
graph.add_node("data_collector", data_collector)
graph.add_node("risk_analyzer", risk_analyzer)
graph.add_node("report_generator", report_generator)

# 노드 연결: START → query_interpret → data_collector → risk_analyzer → report_generator → END
graph.add_edge(START, "query_interpret")
graph.add_edge("query_interpret", "data_collector")
graph.add_edge("data_collector", "risk_analyzer")
graph.add_edge("risk_analyzer", "report_generator")
graph.add_edge("report_generator", END)
graph = graph.compile()
show_graph(graph)

# 그래프 실행: 초기 상태를 넣어 실행하고, 최종 상태 반환
initial_state = AnalysisState(user_input="애플 신용 위험 분석해줘")
final_state = graph.invoke(initial_state)

# 결과 출력 예시
print("분석 대상 기업:", final_state['company'])             # 애플 (Apple Inc.)
print("분석 유형:", final_state['analysis_type'])             # credit_risk
print("신용 리스크 분석 요약:\n", final_state['analysis_summary'])  
print("PDF 보고서 저장 여부:", final_state['report_saved'])   # True (저장 완료)
