from langgraph.graph import StateGraph
from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnableLambda

def summarize_step(state):
    log = state['log']
    return {"summary": f"Summarized: {log[:100]}"}

graph = StateGraph()
graph.add_node("summarize", RunnableLambda(summarize_step))
graph.set_entry_point("summarize")
langgraph_chain = graph.compile()

def summarize_log(log):
    return langgraph_chain.invoke({"log": log})["summary"]
