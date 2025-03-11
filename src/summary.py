import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())  # .env 파일 로드
openai_api_key = os.getenv('OPENAI_API_KEY')
import openai

text = """OpenAI GPT-3.5 was introduced in 2022 and is known for its strong 
conversational abilities. The model can handle a wide range of tasks, from 
answering questions to generating creative content. Many developers use GPT-3.5 
via the OpenAI API to build chatbots, virtual assistants, and other AI applications. 
However, GPT-3.5 has limitations such as knowledge only up to 2021 and occasional inaccuracies."""
prompt = (
    "다음 텍스트에서 핵심적인 3개의 문장을 추출하세요:\n" + text
)
messages = [{"role": "user", "content":prompt}]
client = openai.Client(api_key=openai_api_key)
completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)        
summary = completion.choices[0].message.content
print(summary)
