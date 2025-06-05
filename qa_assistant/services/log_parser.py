from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from utils.config import OPENAI_API_KEY
from langsmith_setup import get_project_name

def summarize_log(log: str) -> str:
    # Using LangChain components for automatic LangSmith tracing
    llm = ChatOpenAI(
        model="gpt-4.1", 
        max_tokens=25,
        openai_api_key=OPENAI_API_KEY,
        tags=["qa_assistant"]
    )
    
    prompt = ChatPromptTemplate.from_template("Summarize this failure log:\n{log}")
    
    # Define the chain
    chain = (
        {"log": RunnablePassthrough()} 
        | prompt 
        | llm
    ).with_config(
        run_name="summarize_log",
        tags=["qa_assistant"]
    )
    
    # Execute with tracing enabled automatically
    response = chain.invoke(log)
    return response.content