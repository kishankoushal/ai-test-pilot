from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4.1")

def generate_test_plan(features):
    plans = []
    for f in features:
        plan_prompt = f"Generate a QA test plan for this feature:\n{f}"
        plan = llm.invoke(plan_prompt).content
        plans.append(plan)
    return plans
