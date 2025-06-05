from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from utils.config import OPENAI_API_KEY
from langsmith_setup import get_project_name

def generate_test_cases(test_plan: str):
    # Using LangChain components for automatic LangSmith tracing
    llm = ChatOpenAI(
        model="gpt-4.1", 
        max_tokens=40,
        openai_api_key=OPENAI_API_KEY,
        tags=["qa_assistant", "test_case_generation"]
    )
    
    prompt = ChatPromptTemplate.from_template("""
    Write 1-2 simple test cases based on this plan. Use plain text format without any markdown, asterisks, headers or formatting. For each test case include:
    - Title
    - Steps (numbered list)
    - Expected result
    
    {test_plan}
    """)
        # Given this test plan, write detailed test cases with title, steps, expected result:
    # Define the chain with proper config for LangSmith
    chain = (
        {"test_plan": RunnablePassthrough()} 
        | prompt 
        | llm
    ).with_config(
        run_name="generate_test_cases",
        tags=["qa_assistant", "test_generation"]
    )
    
    return chain.invoke(test_plan).content