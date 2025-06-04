from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from utils.config import OPENAI_API_KEY
from langsmith_setup import get_project_name

def generate_test_plan(features):
    plans = []
    
    # Using LangChain components for automatic LangSmith tracing
    llm = ChatOpenAI(
        model="gpt-4.1", 
        openai_api_key=OPENAI_API_KEY,
        tags=["qa_assistant", "test_plan_generation"]
    )
    
    prompt = ChatPromptTemplate.from_template(
        "Generate a QA test plan for this feature:\n{feature}"
    )
    
    # Define the chain with proper config for LangSmith
    chain = (
        {"feature": RunnablePassthrough()} 
        | prompt 
        | llm
    ).with_config(
        run_name="generate_test_plan",
        tags=["qa_assistant", "planning"]
    )
    
    for feature in features:
        plan = chain.invoke(feature).content
        plans.append(plan)
    
    return plans