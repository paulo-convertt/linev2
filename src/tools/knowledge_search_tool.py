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
    source_file: Optional[str] = Field(None, description="Nome do arquivo para priorizar na busca. Se especificado, busca primeiro neste arquivo com alta prioridade, e se não encontrar bons resultados, expande para todos os arquivos (ex: 'lance embutido.txt')")

class KnowledgeSearchTool(BaseTool):
    """CrewAI tool for searching FAQ knowledge base using vector similarity"""

    name: str = "knowledge_search"
    description: str = "Search FAQ knowledge base for consortium information."
    args_schema: type[BaseModel] = KnowledgeSearchInput

    def __init__(self):
        super().__init__(
            name="knowledge_search",
            description="Search FAQ knowledge base for consortium information. Uses semantic search to find relevant entries for consortium, financing, and related questions.",
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

    def _run(self, query: str, source_file: Optional[str] = None) -> str:
        """
        Search the knowledge base for relevant FAQ entries

        Args:
            query: The user's question or message
            source_file: Optional filename to prioritize in search

        Returns:
            Formatted string with relevant FAQ entries
        """
        try:
            # ✅ ROBUSTA: Normalize query input (handle both string and dict inputs)
            normalized_query = self._normalize_query_input(query)

            logger.info(f"Searching knowledge base for query: {normalized_query}")
            if source_file:
                logger.info(f"Using priority search strategy for file: {source_file}")
            else:
                logger.info("Using standard search across all files")

            # Use the knowledge base search method with priority strategy
            results = self._search_knowledge_base(normalized_query, source_file)

            if not results:
                if source_file:
                    return f"No relevant information found in priority file '{source_file}' or other files."
                else:
                    return "No relevant information found in the knowledge base."

            # Format the results
            formatted_results = []
            for i, result in enumerate(results):
                priority_indicator = ""
                if source_file and result['source_file'] == source_file:
                    priority_indicator = " (PRIORITY FILE)"

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

    def _search_knowledge_base(self, query: str, source_file: Optional[str] = None) -> List[Dict]:
        """
        Internal method to search knowledge base and return structured results

        Strategy:
        1. If source_file is provided, search first with high priority in that file
        2. If no good results (score < threshold), expand search to all files
        3. If source_file not provided, search all files normally

        Args:
            query: The search query
            source_file: Optional filename to prioritize in search (e.g., "lance embutido.txt")
        """
        try:
            # Generate embedding for the user query
            search_embedding = self.get_embedding(query)

            # Define search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }

            # Strategy: Priority search if source_file is specified
            if source_file:
                # Step 1: Search with high priority in the specified file
                priority_results = self._perform_search(
                    search_embedding,
                    search_params,
                    source_file,
                    limit=1  # Get more results from priority file
                )

                # Check if we have good quality results from priority file
                # Consider score > 0.7 as good quality (adjust threshold as needed)
                good_priority_results = [r for r in priority_results if r['relevance_score'] > 0.7]

                if good_priority_results:
                    logger.info(f"Found {len(good_priority_results)} good results in priority file: {source_file}")
                    return good_priority_results[:1]  # Return best result from priority file

                # Step 2: If no good results in priority file, search all files
                logger.info(f"No good results in priority file {source_file}, expanding search to all files")
                all_results = self._perform_search(search_embedding, search_params, None, limit=1)

                # Combine and sort results: priority file results first, then others
                combined_results = priority_results + [r for r in all_results if r['source_file'] != source_file]

                # Sort by relevance score (descending) and return top result
                combined_results.sort(key=lambda x: x['relevance_score'], reverse=True)
                return combined_results[:1] if combined_results else []

            else:
                # No source_file specified, normal search across all files
                return self._perform_search(search_embedding, search_params, None, limit=1)

        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []

    def _perform_search(self, search_embedding: List[float], search_params: Dict,
                       source_file: Optional[str] = None, limit: int = 1) -> List[Dict]:
        """
        Perform actual search operation with optional file filtering

        Args:
            search_embedding: The query embedding vector
            search_params: Milvus search parameters
            source_file: Optional file to filter by
            limit: Number of results to return

        Returns:
            List of formatted search results
        """
        try:
            # Build expression filter for source_file if provided
            expr = None
            if source_file:
                # Escape single quotes in filename if any
                escaped_filename = source_file.replace("'", "\\'")
                expr = f"source_file == '{escaped_filename}'"

            # Perform the search
            search_results = self._collection.search(  # type: ignore
                data=[search_embedding],
                anns_field="embedding",
                param=search_params,
                limit=1,
                expr=expr,  # Add the filter expression
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
            print(f"Error performing search: {e}")
            return []


# Function to get the tool for CrewAI
def get_knowledge_search_tool() -> KnowledgeSearchTool:
    """Get an instance of the knowledge search tool for use in CrewAI"""
    return KnowledgeSearchTool()

# Instance for use in CrewAI
knowledge_search_tool = KnowledgeSearchTool()
