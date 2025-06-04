from langgraph.graph import StateGraph
from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnableLambda
from langsmith import traceable
from langsmith_setup import get_project_name

@traceable(name="summarize_step")
def summarize_step(state):
    log = state['log']
    return {"summary": f"Summarized: {log[:100]}"}

graph = StateGraph()
graph.add_node("summarize", RunnableLambda(summarize_step))
graph.set_entry_point("summarize")

# Add tracing to the compiled graph
project_name = get_project_name()
langgraph_chain = graph.compile(name="summarize_workflow", tags=["qa_assistant"])

def summarize_log(log):
    return langgraph_chain.invoke({"log": log})["summary"]