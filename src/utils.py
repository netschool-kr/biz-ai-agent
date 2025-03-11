from PIL import Image
import matplotlib.pyplot as plt
import os
import time
import requests
def show_graph(graph):
    # graph 이미지를 바이트 객체로 생성하고 파일로 저장
    png_data = None
 
    max_retries = 3
    for attempt in range(max_retries):
        try:
            png_data = graph.get_graph(xray=True).draw_mermaid_png()
            break
        except requests.exceptions.ReadTimeout:
            if attempt < max_retries - 1:
                print(f"Timeout 발생, 5초 후 재시도...")
                time.sleep(5)
            else:
                raise
    with open("graph.png", "wb") as f:
        f.write(png_data)  # 이미지를 파일로 저장

    print("Graph image saved as 'graph.png'. Displaying the image...")

    # 저장된 이미지를 읽어서 matplotlib으로 표시
    image = Image.open("graph.png")
    plt.imshow(image)
    plt.axis("off")  # 축 숨기기
    plt.show()


import xml.etree.ElementTree as ET


def load_xml_files(directory, encoding="utf-8"):
    """
    주어진 디렉토리에서 .xml 파일을 로드하고, XML 내용을 파싱하여 반환합니다.

    Args:
        directory (str): XML 파일이 포함된 디렉토리 경로.
        encoding (str): XML 파일을 디코딩할 때 사용할 인코딩. 기본값은 'utf-8'.

    Returns:
        list: 파싱된 XML 내용의 리스트. 각 항목은 딕셔너리 형태로 파일 이름과 내용을 포함합니다.
    """
    h1_docs = []
    for file in os.listdir(directory):
        if file.endswith(".xml"):  # XML 파일만 처리
            file_path = os.path.join(directory, file)
            try:
                with open(file_path, "rb") as f:  # 바이너리 모드로 파일 읽기
                    content = f.read()
                    root = ET.fromstring(content)  # XML 파싱
                    text = ET.tostring(root, encoding="unicode")  # 유니코드로 변환
                    h1_docs.append({"file": file, "content": text})
            except Exception as e:
                print(f"Error parsing file {file_path}: {e}")
    return h1_docs
