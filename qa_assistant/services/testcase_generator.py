from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4.1")

def generate_test_cases(test_plan: str):
    prompt = f"""
    Given this test plan, write detailed test cases with title, steps, expected result:

    {test_plan}
    """
    return llm.invoke(prompt).content
