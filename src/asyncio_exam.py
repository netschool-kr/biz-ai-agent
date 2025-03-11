import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())  # .env 파일 로드
openai_api_key = os.getenv('OPENAI_API_KEY')

import aiohttp, asyncio

API_URL = "https://api.openai.com/v1/chat/completions"
headers = {"Authorization": f"Bearer {openai_api_key}"}

async def fetch_completion(session, prompt):
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with session.post(API_URL, json=data, headers=headers) as resp:
        result = await resp.json()
        return result["choices"][0]["message"]["content"]

async def get_responses(prompts):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_completion(session, p) for p in prompts]
        return await asyncio.gather(*tasks)

# 여러 질문 프롬프트를 병렬로 처리
prompts = ["질문1 ...", "질문2 ...", "질문3 ..."]
responses = asyncio.run(get_responses(prompts))
for resp in responses:
    print(resp)
