from fpdf import FPDF
pdf = FPDF()
pdf.add_page()
# 한글 폰트 추가 (예: 나눔고딕 폰트 파일)
pdf.add_font('NanumGothic', '', 'C:/Windows/Fonts/NanumGothic.ttf', uni=True)
# 폰트 설정 (추가한 폰트 사용, 크기 14)
pdf.set_font('NanumGothic', '', 14)
# 한글 텍스트 출력
pdf.cell(0, 10, txt="한글 테스트입니다.", ln=1)
pdf.output("output.pdf")
