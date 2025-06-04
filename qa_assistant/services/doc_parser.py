from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

def chunk_markdown(md: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_text(md)
