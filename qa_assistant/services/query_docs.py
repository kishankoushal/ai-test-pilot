import os
import logging
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"OpenAI API Key loaded: {'present' if api_key else 'missing'}")

class DocumentQuerier:
    def __init__(self, persist_directory: str = "chroma_db"):
        self.persist_directory = persist_directory
        logger.info(f"Initializing DocumentQuerier with directory: {persist_directory}")

        # Initialize embedding model
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        logger.info("Embedding model initialized")

        # Load the vector store
        if not os.path.exists(persist_directory):
            raise ValueError(f"No vector store found at {persist_directory}")

        self.vectordb = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_model
        )
        count = self.vectordb._collection.count()
        logger.info(f"Loaded vector store with {count} documents")

    def search(self, query: str, k: int = 5) -> list:
        """Search for documents similar to the query."""
        logger.info(f"Searching for: {query}")
        results = self.vectordb.similarity_search_with_score(query, k=k)

        # Format results
        formatted_results = []
        for doc, score in results:
            relevance = 1 - score  # Convert score to relevance (0-1)
            formatted_results.append({
                'relevance': relevance,
                'content': doc.page_content,
                'source': doc.metadata.get('source', 'Unknown'),
                'score': score
            })

        return formatted_results

def print_results(results: list):
    """Print search results in a formatted way."""
    for i, result in enumerate(results, 1):
        print(f"\nResult {i} (Relevance: {result['relevance']:.2%})")
        print("-" * 40)
        print(f"Content: {result['content'][:300]}...")
        print(f"Source: {result['source']}")
        print("-" * 80)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Query the document database')
    parser.add_argument('--query', required=True, help='The query to search for')
    parser.add_argument('--db-path', default='chroma_db', help='Path to the Chroma DB directory')
    parser.add_argument('--top-k', type=int, default=1, help='Number of results to return')

    args = parser.parse_args()

    try:
        querier = DocumentQuerier(persist_directory=args.db_path)
        results = querier.search(query=args.query, k=args.top_k)

        print("\n" + "="*80)
        print(f"Search Query: {args.query}")
        print("="*80 + "\n")

        print_results(results)

    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        raise
