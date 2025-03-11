import aiohttp
from bs4 import BeautifulSoup
import asyncio

async def search_duduko(query: str):
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

#사용 예시 (asyncio를 활용하여 함수 실행)
results = asyncio.run(search_duduko("python web scraping"))
print(results)  # [{"title": ..., "url": ..., "snippet": ...}, ...]
