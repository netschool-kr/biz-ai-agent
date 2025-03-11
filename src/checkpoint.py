from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    foo: int
    bar: Annotated[list[str], add]

def node_a(state: State):
    return {"foo": "a", "bar": ["a"]}

def node_b(state: State):
    return {"foo": "b", "bar": ["b"]}


workflow = StateGraph(State)
workflow.add_node(node_a)
workflow.add_node(node_b)
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", "node_b")
workflow.add_edge("node_b", END)

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}
graph.invoke({"foo": ""}, config)

# get the latest state snapshot
config = {"configurable": {"thread_id": "1"}}
print(graph.get_state(config))

# get a state snapshot for a specific checkpoint_id
config = {"configurable": {"thread_id": "1", "checkpoint_id": "1ef663ba-28fe-6528-8002-5a559208592c"}}
print("get_state:", graph.get_state(config))

# get the full history of the graph execution for a given thread
config = {"configurable": {"thread_id": "1"}}
print("\n\nget_state_history:", list(graph.get_state_history(config)))

from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    foo: int
    bar: Annotated[list[str], add]
    
print("\n\n update_state:", graph.update_state(config, {"foo": 2, "bar": ["b"]}))

from langgraph.store.memory import InMemoryStore
in_memory_store = InMemoryStore()

user_id = "1"
namespace_for_memory = (user_id, "memories")

import uuid
#use the store.put method to save memories to our namespace in the store
memory_id = str(uuid.uuid4())
memory = {"food_preference" : "I like pizza"}
in_memory_store.put(namespace_for_memory, memory_id, memory)

memories = in_memory_store.search(namespace_for_memory)
print("\n\n memories[-1]:", memories[-1].dict())

