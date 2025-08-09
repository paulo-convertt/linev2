import os
from typing import List, Dict, Optional
from pymilvus import connections, Collection
from openai import OpenAI
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import logging
from pathlib import Path

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    # Procurar o arquivo .env na raiz do projeto
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    # Se python-dotenv não estiver instalado, continuar sem carregar
    pass

logger = logging.getLogger(__name__)

class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge search tool"""
    query: str = Field(..., description="Mensagem de entrada do usuário")

class KnowledgeSearchTool(BaseTool):
    """CrewAI tool for searching FAQ knowledge base using vector similarity"""

    name: str = "knowledge_search"
    description: str = "Ferramenta utilizada para buscar informações na base de conhecimento de FAQs."
    args_schema: type[BaseModel] = KnowledgeSearchInput

    def __init__(self):
        super().__init__(
            name="knowledge_search",
            description=(
                "Search the FAQ knowledge base for relevant information based on user queries. "
                "This tool uses semantic search to find the most relevant FAQ entries that can "
                "help answer user questions about consórcios, financing, and related topics."
            ),
            args_schema=KnowledgeSearchInput
        )
        self._setup_connections()

    def _setup_connections(self):
        """Setup connections to OpenAI and Milvus"""
        # Load environment variables
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Store as private attributes (not Pydantic fields)
        object.__setattr__(self, '_api_key', api_key)
        object.__setattr__(self, '_client', OpenAI(api_key=api_key))

        # Connect to Milvus
        milvus_uri = os.getenv('MILVUS_URI')
        milvus_token = os.getenv('MILVUS_TOKEN')

        if not milvus_uri:
            raise ValueError("MILVUS_URI environment variable is required")
        if not milvus_token:
            raise ValueError("MILVUS_TOKEN environment variable is required")

        try:
            # Establish connection using connections module
            connections.connect(
                uri=milvus_uri,
                token=milvus_token
            )

            # Get the collection
            collection = Collection(name="faq_collection")
            collection.load()  # Load collection into memory for search
            object.__setattr__(self, '_collection', collection)

        except Exception as e:
            print(f"Error connecting to Milvus: {e}")
            raise

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text using OpenAI API"""
        response = self._client.embeddings.create(  # type: ignore
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _run(self, query: str) -> str:
        """
        Search the knowledge base for relevant FAQ entries

        Args:
            query: The user's question or message
            limit: Number of results to return

        Returns:
            Formatted string with relevant FAQ entries
        """
        try:
            # ✅ ROBUSTA: Normalize query input (handle both string and dict inputs)
            normalized_query = self._normalize_query_input(query)

            logger.info(f"Searching knowledge base for query: {normalized_query}")
            # Use the knowledge base search method
            results = self._search_knowledge_base(normalized_query)

            if not results:
                return "No relevant information found in the knowledge base."

            # Format the results
            formatted_results = []
            for i, result in enumerate(results):
                result_text = f"""
                    Resposta: {result['answer']}
                    ---"""
                formatted_results.append(result_text)

            return "\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return f"Error searching knowledge base: {str(e)}"

    def _normalize_query_input(self, query) -> str:
        """
        Normalize query input to handle various formats from CrewAI.

        CrewAI sometimes sends:
        - Simple string: "what is consorcio"
        - Dict format: {"description": "what is consorcio", "type": "str"}
        - Other variations

        Args:
            query: Input from CrewAI (can be string, dict, or other)

        Returns:
            str: Normalized query string
        """
        try:
            # Case 1: Already a string
            if isinstance(query, str):
                return query.strip()

            # Case 2: Dictionary with description
            if isinstance(query, dict):
                if "description" in query:
                    return str(query["description"]).strip()
                elif "query" in query:
                    return str(query["query"]).strip()
                # If dict but no known keys, convert to string
                return str(query).strip()

            # Case 3: Any other type, convert to string
            return str(query).strip()

        except Exception as e:
            logger.error(f"Error normalizing query input: {e}, input: {query}")
            # Fallback: return the string representation
            return str(query) if query is not None else ""

    def _search_knowledge_base(self, query: str) -> List[Dict]:
        """
        Internal method to search knowledge base and return structured results
        """
        try:
            # Generate embedding for the user query
            search_embedding = self.get_embedding(query)

            # Define search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }

            # Perform the search
            search_results = self._collection.search(  # type: ignore
                data=[search_embedding],
                anns_field="embedding",
                param=search_params,
                limit=1,
                output_fields=["q", "sq", "a", "t", "tags", "source_file"]
            )

            # Format results as list of dictionaries
            formatted_results = []

            # Process results - search_results is iterable and contains batches
            for batch in search_results:  # type: ignore
                for hit in batch:
                    entity = hit.entity
                    result = {
                        "question": entity.get('q', ''),
                        "sub_questions": entity.get('sq', ''),
                        "answer": entity.get('a', ''),
                        "text_reference": entity.get('t', ''),
                        "tags": entity.get('tags', ''),
                        "source_file": entity.get('source_file', ''),
                        "relevance_score": hit.score
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []


# Function to get the tool for CrewAI
def get_knowledge_search_tool() -> KnowledgeSearchTool:
    """Get an instance of the knowledge search tool for use in CrewAI"""
    return KnowledgeSearchTool()

# Instance for use in CrewAI
knowledge_search_tool = KnowledgeSearchTool()
