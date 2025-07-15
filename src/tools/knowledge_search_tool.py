# tools/knowledge_search_tool.py
from typing import Any
from crewai.tools import BaseTool
from knowledge.knowledge_base import ConsorcioKnowledgeBase

class KnowledgeSearchTool(BaseTool):
    name: str = "knowledge_search_tool"
    description: str = """
    Ferramenta para buscar informações na base de conhecimento sobre consórcios.
    Use quando precisar de informações sobre:
    - Tipos de consórcios disponíveis
    - Condições e regras
    - Processos legais
    - Produtos específicos
    - Perguntas frequentes

    Input: pergunta ou termo de busca
    Output: informações relevantes da base de conhecimento
    """
    knowledge_base: Any = None

    def __init__(self):
        self.knowledge_base = ConsorcioKnowledgeBase()

    def _run(self, query: str) -> str:
        results = self.knowledge_base.search_knowledge(query, n_results=3)

        if not results:
            return "Não encontrei informações específicas sobre isso. Posso ajudar com outras dúvidas sobre consórcios?"

        formatted_results = []
        for result in results:
            formatted_results.append(f"📋 {result['content']}")

        return "\n\n".join(formatted_results)
