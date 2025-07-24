# ============================================================================
# faq_system.py - Sistema Principal Corrigido
# ============================================================================

import re
import os
import json
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# ============================================================================
# CONFIGURAÇÃO CHROMADB PARA FAQs ESTRUTURADOS
# ============================================================================

def setup_chromadb_client():
    """Initialize ChromaDB with optimized configuration for Portuguese FAQ systems."""

    # Use project-relative path instead of root filesystem
    project_root = Path(__file__).parent.parent.parent
    chroma_db_path = project_root / ".chroma_db"

    chroma_db_path.mkdir(parents=True, exist_ok=True)

    # Ensure proper permissions (readable and writable)
    try:
        chroma_db_path.chmod(0o755)
    except PermissionError:
        print(f"⚠️ Warning: Could not set permissions for {chroma_db_path}")

    client = chromadb.PersistentClient(path=str(chroma_db_path))
    print(f"✅ ChromaDB initialized at: {chroma_db_path}")
    return client

def create_faq_collection(client):
    """Create optimized collection for Portuguese FAQ indexing."""

    # Embedding function optimized for Portuguese content
    embedding_function = embedding_functions.DefaultEmbeddingFunction()

    try:
        # Try to get existing collection
        collection = client.get_collection(
            name="faq_consorcio_pt",
            embedding_function=embedding_function
        )
        print("✅ Usando coleção FAQ existente")
    except:
        # Create new collection
        collection = client.create_collection(
            name="faq_consorcio_pt",
            embedding_function=embedding_function,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:batch_size": 200,
                "hnsw:sync_threshold": 2000,
                "hnsw:M": 16,
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100,
                "description": "FAQ collection for Portuguese consórcio content"
            }
        )
        print("✅ Nova coleção FAQ criada")

    return collection

# ============================================================================
# PARSER PARA FORMATO ESTRUTURADO DE FAQ
# ============================================================================

def parse_structured_faq_format(content: str) -> List[Dict]:
    """
    Parse structured FAQ format:
    q: (main question)
    sq: (sub-questions)
    a: (answer)
    t: (reference text with source)
    tags: (comma-separated tags)
    ---
    """

    faqs = []

    # Split by separator (---)
    sections = re.split(r'\n\s*---+\s*\n', content.strip())

    for section in sections:
        if not section.strip():
            continue

        faq_data = {
            "question": "",
            "sub_questions": "",
            "answer": "",
            "reference": "",
            "tags": [],
            "category": "general",
            "difficulty": "basic"
        }

        # Parse each field
        lines = section.strip().split('\n')
        current_field = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for field markers
            if line.startswith('q:'):
                # Save previous field content
                if current_field and current_content:
                    _save_field_content(faq_data, current_field, current_content)

                current_field = 'question'
                current_content = [line[2:].strip()]

            elif line.startswith('sq:'):
                if current_field and current_content:
                    _save_field_content(faq_data, current_field, current_content)

                current_field = 'sub_questions'
                current_content = [line[3:].strip()]

            elif line.startswith('a:'):
                if current_field and current_content:
                    _save_field_content(faq_data, current_field, current_content)

                current_field = 'answer'
                current_content = [line[2:].strip()]

            elif line.startswith('t:'):
                if current_field and current_content:
                    _save_field_content(faq_data, current_field, current_content)

                current_field = 'reference'
                current_content = [line[2:].strip()]

            elif line.startswith('tags:'):
                if current_field and current_content:
                    _save_field_content(faq_data, current_field, current_content)

                # Process tags
                tags_text = line[5:].strip()
                faq_data['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                current_field = None
                current_content = []

            else:
                # Continuation of current field
                if current_field:
                    current_content.append(line)

        # Save the last field
        if current_field and current_content:
            _save_field_content(faq_data, current_field, current_content)

        # Validate and add FAQ if it has required fields
        if faq_data['question'] and faq_data['answer']:

            # Extract category from tags
            faq_data['category'] = _extract_category_from_tags(faq_data['tags'])

            # Create final FAQ entry
            final_faq = {
                "question": faq_data['question'],
                "answer": faq_data['answer'],
                "category": faq_data['category'],
                "difficulty": faq_data['difficulty'],
                "tags": faq_data['tags'],
                "sub_questions": faq_data['sub_questions'],
                "reference": faq_data['reference']
            }

            faqs.append(final_faq)

    return faqs

def _save_field_content(faq_data: Dict, field: str, content: List[str]) -> None:
    """Save field content to FAQ data structure."""

    combined_content = ' '.join(content).strip()

    if field == 'question':
        faq_data['question'] = combined_content
    elif field == 'sub_questions':
        faq_data['sub_questions'] = combined_content
    elif field == 'answer':
        faq_data['answer'] = combined_content
    elif field == 'reference':
        faq_data['reference'] = combined_content

def _extract_category_from_tags(tags: List[str]) -> str:
    """Extract category from tags based on consórcio-specific patterns."""

    category_mapping = {
        # Consórcio específico
        'contemplação': 'contemplação',
        'lance': 'lances',
        'apressado': 'urgência',
        'urgência': 'urgência',
        'antecipação': 'antecipação',
        'estratégia': 'estratégias',
        'lance embutido': 'lances',
        'lance livre': 'lances',
        'lance fixo': 'lances',
        'sorteio': 'contemplação',
        'grupo': 'grupos',
        'assembleia': 'assembleia',
        'administradora': 'administração',
        'taxa': 'financeiro',
        'fundo': 'financeiro',
        'reserva': 'financeiro',
        'prestação': 'pagamentos',
        'parcela': 'pagamentos',
        'atraso': 'pagamentos',
        'inadimplência': 'pagamentos',
        'objetivo': 'geral',
        'funcionamento': 'funcionamento',
        'dinâmica': 'funcionamento'
    }

    for tag in tags:
        tag_lower = tag.lower().strip()
        if tag_lower in category_mapping:
            return category_mapping[tag_lower]

    return 'geral'

def load_faq_content(file_path: str) -> List[Dict]:
    """Load FAQ content from TXT files with structured format."""

    if not Path(file_path).exists():
        raise FileNotFoundError(f"Arquivo FAQ não encontrado: {file_path}")

    if not file_path.endswith('.txt'):
        raise ValueError("Apenas arquivos .txt são suportados no formato estruturado")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse the structured format
    faqs = parse_structured_faq_format(content)

    if faqs:
        print(f"✅ {len(faqs)} FAQs parseados com sucesso do formato estruturado")
        return faqs

    print("❌ Nenhum FAQ encontrado no formato estruturado")
    return []

# ============================================================================
# INDEXAÇÃO NO CHROMADB - CORRIGIDA
# ============================================================================

def index_structured_faqs_to_chromadb(faq_file_path: str, collection):
    """Index structured FAQ format to ChromaDB optimized for Portuguese content."""

    # Parse FAQ file
    faqs = load_faq_content(faq_file_path)

    if not faqs:
        raise ValueError("Nenhum FAQ encontrado no arquivo fornecido")

    documents = []
    metadatas = []
    ids = []

    for i, faq in enumerate(faqs):
        # Create enhanced document content for better search
        doc_content = f"Pergunta: {faq['question']}\nResposta: {faq['answer']}"

        # Add sub-questions for better retrieval
        if faq.get('sub_questions'):
            doc_content += f"\nPerguntas similares: {faq['sub_questions']}"

        documents.append(doc_content)

        # Enhanced metadata - CONVERTENDO TAGS PARA STRING
        metadata = {
            "question": faq['question'],
            "answer": faq['answer'],
            "category": faq['category'],
            "difficulty": faq['difficulty'],
            "tags": ','.join(faq['tags']),  # ← CORREÇÃO: Converter lista para string
            "answer_length": len(faq['answer']),
            "has_sub_questions": bool(faq.get('sub_questions')),
            "has_reference": bool(faq.get('reference')),
            "language": "pt-br",
            "num_tags": len(faq['tags'])  # Para filtros
        }

        # Add sub-questions and reference if available
        if faq.get('sub_questions'):
            metadata['sub_questions'] = faq['sub_questions']
        if faq.get('reference'):
            metadata['reference'] = faq['reference']

        metadatas.append(metadata)
        ids.append(f"faq_consorcio_{Path(faq_file_path).stem}_{i+1}")

    # Batch insert to ChromaDB
    try:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"✅ {len(documents)} FAQs indexados com sucesso no ChromaDB")
        return {
            "success": True,
            "indexed_count": len(documents),
            "collection_name": collection.name,
            "file_processed": Path(faq_file_path).name
        }

    except Exception as e:
        print(f"❌ Erro ao indexar FAQs no ChromaDB: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_processed": Path(faq_file_path).name
        }

# ============================================================================
# FERRAMENTA CREWAI PARA FAQS ESTRUTURADOS - CORRIGIDA
# ============================================================================

# ============================================================================
# CREWAI TOOL WITH PROPER ARGS SCHEMA
# ============================================================================

class FAQSearchInput(BaseModel):
    """Input schema for FAQ search tool."""
    query: str = Field(description="Pergunta ou busca sobre consórcio")
    category: Optional[str] = Field(default=None, description="Categoria opcional (contemplação, lances, urgência, etc.)")
    max_results: int = Field(default=3, description="Número máximo de resultados (1-5)")

class ConsorcioFAQTool(BaseTool):
    name: str = "faq_tool"
    description: str = "Busca em base de conhecimento de FAQs sobre consórcio com conteúdo em português"
    args_schema: type[BaseModel] = FAQSearchInput
    collection: Any = None  # Define collection as a field

    def __init__(self, collection, **kwargs):
        super().__init__(**kwargs)
        self.collection = collection

    def _run(self, query: str, category: Optional[str] = None, max_results: int = 3) -> str:
        """
        Search FAQ database optimized for consórcio questions in Portuguese.

        Args:
            query: Pergunta ou busca sobre consórcio
            category: Categoria opcional (contemplação, lances, urgência, etc.)
            max_results: Número máximo de resultados (1-5)
        """
        try:
            # Build metadata filters
            where_filter = {"language": "pt-br"}
            if category:
                where_filter["category"] = category

            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=min(max_results, 5),
                where=where_filter if len(where_filter) > 1 else None,
                include=["documents", "metadatas", "distances"]
            )

            # Check if results found
            if not results["documents"][0]:
                return f"❌ Nenhum FAQ encontrado para: '{query}'"

            return self._format_faq_response(results, query)

        except Exception as e:
            return f"❌ Erro ao buscar FAQs: {str(e)}"

    def _format_faq_response(self, results, query: str) -> str:
        """Format FAQ search results for Portuguese consórcio content."""

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        response = f"🔍 Encontrei {len(documents)} FAQ(s) sobre: '{query}'\n\n"

        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances), 1):
            relevance = 1 - distance

            response += f"**✅ Resposta:** {metadata.get('answer', '')}\n\n"

            if metadata.get('reference'):
                response += f"**📚 Referência:** {metadata.get('reference', '')}\n\n"

            response += "---\n\n"

        return response

# ============================================================================
# FUNÇÕES DE UTILIDADE
# ============================================================================

def get_collection_stats(collection):
    """Get statistics about the FAQ collection."""
    try:
        count = collection.count()
        print(f"📊 Estatísticas da Coleção:")
        print(f"   Total de FAQs: {count}")

        # Get sample to analyze categories
        if count > 0:
            sample = collection.get(limit=min(100, count), include=["metadatas"])
            categories = {}
            for metadata in sample["metadatas"]:
                cat = metadata.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            print(f"   Categorias encontradas:")
            for cat, cnt in categories.items():
                print(f"     - {cat}: {cnt}")

        return count
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        return 0

def clear_collection(collection):
    """Clear all FAQs from collection."""
    try:
        # Get all IDs
        all_data = collection.get()
        if all_data["ids"]:
            collection.delete(ids=all_data["ids"])
            print(f"✅ Removidos {len(all_data['ids'])} FAQs da coleção")
        else:
            print("ℹ️ Coleção já estava vazia")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar coleção: {e}")
        return False

def search_faqs_by_tag(collection, tag: str, max_results: int = 5):
    """Search FAQs by specific tag."""
    try:
        results = collection.query(
            query_texts=[tag],
            n_results=max_results,
            where={"language": "pt-br"},
            include=["documents", "metadatas", "distances"]
        )

        # Filter results that actually contain the tag
        filtered_results = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

        for doc, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            if tag.lower() in metadata.get("tags", "").lower():
                filtered_results["documents"][0].append(doc)
                filtered_results["metadatas"][0].append(metadata)
                filtered_results["distances"][0].append(distance)

        return filtered_results

    except Exception as e:
        print(f"❌ Erro ao buscar por tag '{tag}': {e}")
        return None
