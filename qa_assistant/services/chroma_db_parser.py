import os
import requests
import logging
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Set
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"OpenAI API Key loaded: {'present' if api_key else 'missing'}")

class DocumentParser:
    def __init__(self, persist_directory: str = "chroma_db", base_url: str = None):
        self.persist_directory = persist_directory
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.rate_limit = 1  # Seconds between requests
        self.max_pages = 100  # Maximum pages to scrape

        logger.info(f"Initializing DocumentParser with directory: {persist_directory}")

        # Initialize embedding model with specific model
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        logger.info("Embedding model initialized")

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        logger.info("Text splitter initialized")

        # Initialize or load vector store
        try:
            if self.s3_bucket:
                # Try to load from S3
                self.vectordb = Chroma(
                    persist_directory=f"s3://{s3_bucket}/{s3_prefix}",
                    embedding_function=self.embedding_model
                )
                logger.info("Loaded existing vector store from S3")
            elif os.path.exists(persist_directory):
                # Load from local storage
                self.vectordb = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embedding_model
                )
                logger.info("Loaded existing vector store from local storage")
            else:
                self.vectordb = None
                logger.info("Will create new vector store when needed")
        except Exception as e:
            logger.warning(f"Could not load existing store: {e}")
            self.vectordb = None

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        logger.info("Text splitter initialized")

        # Initialize or load the vector store
        if os.path.exists(persist_directory):
            self.vectordb = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding_model
            )
        else:
            self.vectordb = None

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to the base domain."""
        if not self.base_url:
            return True

        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain

    def get_links(self, soup: BeautifulSoup, current_url: str) -> Set[str]:
        """Extract all valid links from the page."""
        links = set()
        for a in soup.find_all('a', href=True):
            url = urljoin(current_url, a['href'])
            if self.is_valid_url(url) and '#' not in url:
                links.add(url)
        return links

    def scrape_text(self, url: str) -> str:
        """Scrape text content from a URL."""
        logger.info(f"Scraping text from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.info(f"Response status code: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"Raw HTML size: {len(response.text)} bytes")

            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()

            # Get text with better formatting
            paragraphs = []
            for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                text = p.get_text(strip=True)
                if text:  # Only add non-empty paragraphs
                    if p.name.startswith('h'):  # If it's a header
                        paragraphs.append(f"\n{text}\n")
                    elif p.name == 'li':  # If it's a list item
                        paragraphs.append(f"- {text}")
                    else:
                        paragraphs.append(text)

            # Join with proper spacing
            text = '\n'.join(paragraphs)

            # Clean up extra whitespace
            text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())

            logger.info(f"Extracted text size: {len(text)} bytes")
            return text
        except Exception as e:
            logger.error(f"Error scraping URL: {str(e)}")
            raise

    def process_document(self, content: str, source: str) -> List[dict]:
        """Process document content into chunks with metadata."""
        logger.info(f"Processing document from source: {source}")
        logger.info(f"Input content size: {len(content)} bytes")

        # Split text into chunks
        chunks = self.text_splitter.split_text(content)
        logger.info(f"Created {len(chunks)} chunks")

        if chunks:
            avg_chunk_size = sum(len(chunk) for chunk in chunks) / len(chunks)
            logger.info(f"Average chunk size: {avg_chunk_size:.2f} bytes")

        # Create documents with metadata
        documents = [
            {"text": chunk, "metadata": {"source": source}}
            for chunk in chunks
        ]
        logger.info(f"Created {len(documents)} documents with metadata")
        return documents

    def add_to_vectordb(self, documents: List[dict]) -> None:
        """Add documents to the vector database."""
        logger.info(f"Adding {len(documents)} documents to vector database")

        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        try:
            # Initialize vector store if it doesn't exist
            if self.vectordb is None:
                logger.info("Creating new Chroma vector store")
                self.vectordb = Chroma.from_texts(
                    texts=texts,
                    metadatas=metadatas,
                    embedding=self.embedding_model,
                    persist_directory=self.persist_directory
                )
            else:
                logger.info("Adding to existing vector store")
                self.vectordb.add_texts(texts=texts, metadatas=metadatas)

            logger.info("Successfully added to vector database")

        except Exception as e:
            logger.error(f"Error adding to vector database: {str(e)}")
            raise

    def search_similar_chunks(self, query: str, k: int = 5) -> List[dict]:
        """Search for similar chunks in the vector database."""
        if self.vectordb is None:
            raise ValueError("Vector database is not initialized")

        results = self.vectordb.similarity_search_with_score(query, k=k)
        return [{
            "text": doc.page_content,
            "metadata": doc.metadata,
            "score": score
        } for doc, score in results]

    def process_url(self, url: str, recursive: bool = False) -> None:
        """Process a URL and optionally its linked pages recursively."""
        if not recursive:
            self._process_single_url(url)
            return

        self.visited_urls.clear()  # Reset visited URLs
        urls_to_process = {url}
        processed_count = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            while urls_to_process and processed_count < self.max_pages:
                current_url = urls_to_process.pop()
                if current_url in self.visited_urls:
                    continue

                self.visited_urls.add(current_url)
                processed_count += 1

                try:
                    # Process the current URL
                    logger.info(f"Processing URL {processed_count}/{self.max_pages}: {current_url}")
                    self._process_single_url(current_url)

                    # Get soup object for link extraction
                    response = requests.get(current_url)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Add new URLs to process
                    new_urls = self.get_links(soup, current_url)
                    urls_to_process.update(new_urls - self.visited_urls)

                    # Rate limiting
                    time.sleep(self.rate_limit)

                except Exception as e:
                    logger.error(f"Error processing {current_url}: {str(e)}")
                    continue

    def _process_single_url(self, url: str) -> None:
        """Process a single URL: scrape, chunk, and store in vector database."""
        try:
            # Scrape content
            content = self.scrape_text(url)

            # Process into chunks with metadata
            documents = self.process_document(content, source=url)

            # Add to vector database
            self.add_to_vectordb(documents)

        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Document Parser for Traceable.ai Docs')
    parser.add_argument('--recursive', action='store_true',
                        help='Recursively process all linked pages')
    parser.add_argument('--url', default='https://docs.traceable.ai',
                        help='URL to process (default: %(default)s)')
    parser.add_argument('--db-path', default='chroma_db',
                        help='Path to store the vector database (default: %(default)s)')
    args = parser.parse_args()

    try:
        # Initialize parser
        doc_parser = DocumentParser(
            persist_directory=args.db_path,
            base_url=args.url
        )

        # Process the URL
        logger.info(f"Processing URL: {args.url}")
        doc_parser.process_url(args.url, recursive=args.recursive)

        # Verify vector store status
        if doc_parser.vectordb:
            count = doc_parser.vectordb._collection.count()
            logger.info(f"Vector store contains {count} documents")
            logger.info(f"Data is stored in: {args.db_path}")
            logger.info("You can now use query_docs.py to search the documentation.")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise
