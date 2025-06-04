from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

prompt = PromptTemplate.from_template(
    "Extract features or testable flows from this PRD:\n\n{doc_chunk}"
)

llm = ChatOpenAI(model="gpt-4.1", temperature=0)

def extract_features(chunks):
    features = []
    for chunk in chunks:
        response = llm.invoke(prompt.format(doc_chunk=chunk))
        features.append(response.content.strip())
    return features
