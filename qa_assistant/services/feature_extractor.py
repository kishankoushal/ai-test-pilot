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
        max_tokens=30,
        openai_api_key=OPENAI_API_KEY,
        tags=["qa_assistant", "feature_extraction"]
    )
    
    prompt = PromptTemplate.from_template(
        "Extract key features or testable flows from this PRD. Format each feature as a brief title without any markdown formatting (no asterisks or special characters). Focus on the main functionality:\n\n{doc_chunk}"
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
        # Process the response to get clean feature titles
        content = response.content.strip()
        # Split by lines and clean up each feature
        feature_lines = [line.strip() for line in content.split('\n') if line.strip()]
        features.extend(feature_lines)
    
    return features