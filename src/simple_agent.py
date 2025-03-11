import sys
import os

sys.path.insert(0, os.path.abspath("."))
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
print(os.getenv("OPENAI_API_KEY"))
# Define the State structure with annotations
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Create a StateGraph and language model instance
graph_builder = StateGraph(State)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


# Define the chatbot function
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# Build the graph structure
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

# Main interaction loop
while True:
    user_input = input("사용자: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break
    for event in graph.stream({"messages": ("user", user_input)}):
        for value in event.values():
            print("에이전트:", value["messages"][-1].content)
