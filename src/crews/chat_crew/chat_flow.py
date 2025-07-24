from crewai.flow import Flow, listen, start, persist, router, or_
from crewai import Flow
from models import ChatState
from typing import Dict, Any
from question_manager import QuestionManager
from datetime import datetime

@persist()
class ChatFlow(Flow[ChatState]):
    def __init__(self, persistence=None):
        super().__init__(persistence=persistence)
        self.question_manager = QuestionManager()
        self._conversation_cache = []
        self._data_loaded = False

    @start()
    def initialize_chat(self):
        """
        Inicialização otimizada - não carrega do banco aqui
        """
        if not self._data_loaded:
            self._data_loaded = True

    def add_to_conversation_cache(self, role: str, content: str):
        """
        Adiciona mensagem ao cache local (não salva no banco ainda)
        """
        self._conversation_cache.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })

        if len(self._conversation_cache) > 20:
            self._conversation_cache = self._conversation_cache[-20:]

    def get_conversation_context(self) -> str:
        """
        Retorna contexto da conversa do cache local
        """
        if self._conversation_cache:
            return "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self._conversation_cache[-10:]  # Últimas 10 mensagens
            ])
        return self.state.history or ""
