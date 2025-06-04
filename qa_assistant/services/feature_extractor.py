from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from utils.config import OPENAI_API_KEY
from langsmith_setup import get_project_name

def extract_features(chunks):
    features = []
    
    # Using LangChain components for automatic LangSmith tracing
    llm = ChatOpenAI(
        model="gpt-4.1", 
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        tags=["qa_assistant", "feature_extraction"]
    )
    
    prompt = PromptTemplate.from_template(
        "Extract features or testable flows from this PRD:\n\n{doc_chunk}"
    )
    
    # Define the chain with proper config for LangSmith
    chain = (
        {"doc_chunk": RunnablePassthrough()} 
        | prompt 
        | llm
    ).with_config(
        run_name="extract_features",
        tags=["qa_assistant", "prd_analysis"]
    )
    
    for chunk in chunks:
        response = chain.invoke(chunk)
        features.append(response.content.strip())
    
    return features