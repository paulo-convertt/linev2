import asyncio
from typing import Dict, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from dataclasses import dataclass
from database.config import SessionLocal
from database.models import ConversationHistory, LeadConsorcio
from cache.redis_session_manager import redis_client
from crews.chat_crew.chat_flow import ChatFlow

@dataclass
class SessionStats:
    redis_sessions: int
    redis_histories: int
    redis_memory: str
    total_messages_processed: int
    avg_response_time_ms: float

class RedisChatSessionManager:
    """
    Session Manager usando Redis para cache
    - Performance superior (~1-2ms vs 50-200ms do PostgreSQL)
    - Escalabilidade horizontal
    - Persistência entre restarts
    - TTL automático para limpeza
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.session_ttl = 86400  # 24 horas
            self.history_limit = 100  # Últimas 100 mensagens
            self.initialized = True
            self._stats = {
                'total_messages': 0,
                'total_response_time': 0.0,
                'request_count': 0
            }

    async def initialize(self):
        """Inicializa conexão com Redis"""
        await redis_client.initialize()
        print("🚀 RedisChatSessionManager inicializado")

    async def get_or_create_session(self, whatsapp_number: str):
        """
        Obtém sessão existente do Redis ou cria nova carregando do PostgreSQL
        """
        start_time = datetime.now()

        try:
            # Verifica se sessão existe no Redis
            session_data = await redis_client.get_session_data(whatsapp_number)

            if session_data:
                # Sessão encontrada no cache
                chat_flow = await self._restore_session_from_redis(session_data)
                await redis_client.extend_session_ttl(whatsapp_number, self.session_ttl)

                print(f"✅ Sessão restaurada do Redis: {whatsapp_number}")

            else:
                # Criar nova sessão carregando do PostgreSQL
                chat_flow = await self._create_session_from_database(whatsapp_number)
                print(f"🆕 Nova sessão criada para: {whatsapp_number}")

            # Atualiza estatísticas
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_stats(response_time)

            return chat_flow

        except Exception as e:
            print(f"❌ Erro ao obter/criar sessão: {e}")
            # Fallback: cria sessão básica
            return await self._create_fallback_session(whatsapp_number)

    async def _restore_session_from_redis(self, session_data: Dict):
        """
        Restaura ChatFlow a partir dos dados do Redis
        """
        from crews.chat_crew.chat_flow import ChatFlow

        chat_flow = ChatFlow()

        # Restaura estado básico
        for key, value in session_data.items():
            if hasattr(chat_flow.state, key):
                setattr(chat_flow.state, key, value)

        # Carrega histórico do Redis
        history = await redis_client.get_conversation_history(
            session_data['whatsapp_number'],
            self.history_limit
        )

        if history:
            history_text = []
            for msg in history:
                history_text.append(f"{msg['type']}: {msg['content']}")
            chat_flow.state.history = "\n".join(history_text)

        return chat_flow

    async def _create_session_from_database(self, whatsapp_number: str) -> "ChatFlow":
        """
        Cria nova sessão carregando dados do PostgreSQL e salvando no Redis
        """
        chat_flow = ChatFlow()
        db = SessionLocal()

        try:
            # Carrega lead do PostgreSQL
            lead = db.query(LeadConsorcio).filter(
                LeadConsorcio.whatsapp_number == whatsapp_number
            ).first()

            if lead:
                # Lead existente
                chat_flow.state.whatsapp_number = whatsapp_number
                chat_flow.state.nome = lead.nome
                chat_flow.state.cpf = lead.cpf
                chat_flow.state.estado_civil = lead.estado_civil
                chat_flow.state.naturalidade = lead.naturalidade
                chat_flow.state.endereco = lead.endereco
                chat_flow.state.email = lead.email
                chat_flow.state.nome_mae = lead.nome_mae
                chat_flow.state.renda = lead.renda
                chat_flow.state.profissao = lead.profissao
                chat_flow.state.conversation_stage = lead.conversation_stage
                chat_flow.state.is_complete = lead.is_complete
                chat_flow.state.requires_human_handoff = lead.requires_human_handoff

                print(f"📋 Lead existente carregado: {whatsapp_number}")
            else:
                # Novo lead
                chat_flow.state.whatsapp_number = whatsapp_number
                chat_flow.state.conversation_stage = "inicio"
                print(f"🆕 Novo lead detectado: {whatsapp_number}")

            # Carrega histórico do PostgreSQL
            conversation_history = db.query(ConversationHistory)\
                .filter(ConversationHistory.whatsapp_number == whatsapp_number)\
                .order_by(ConversationHistory.timestamp.desc())\
                .limit(self.history_limit).all()

            if conversation_history:
                conversation_history.reverse()

                # Salva no Redis para acesso rápido
                for msg in conversation_history:
                    await redis_client.add_message_to_history(
                        whatsapp_number,
                        msg.message_type,
                        msg.content
                    )

                # Atualiza histórico no ChatFlow
                history_text = []
                for msg in conversation_history:
                    history_text.append(f"{msg.message_type}: {msg.content}")
                chat_flow.state.history = "\n".join(history_text)

                print(f"💬 Histórico carregado: {len(conversation_history)} mensagens")

            # Salva sessão no Redis
            await self._save_session_to_redis(chat_flow)

            return chat_flow

        except Exception as e:
            print(f"❌ Erro ao carregar do banco: {e}")
            return await self._create_fallback_session(whatsapp_number)
        finally:
            db.close()

    async def _create_fallback_session(self, whatsapp_number: str) -> "ChatFlow":
        """
        Cria sessão básica em caso de erro
        """
        chat_flow = ChatFlow()
        chat_flow.state.whatsapp_number = whatsapp_number
        chat_flow.state.conversation_stage = "inicio"

        await self._save_session_to_redis(chat_flow)
        print(f"⚠️ Sessão fallback criada: {whatsapp_number}")

        return chat_flow

    async def _save_session_to_redis(self, chat_flow: "ChatFlow"):
        """
        Salva estado da sessão no Redis
        """
        session_data = {
            'whatsapp_number': chat_flow.state.whatsapp_number,
            'nome': chat_flow.state.nome,
            'cpf': chat_flow.state.cpf,
            'estado_civil': chat_flow.state.estado_civil,
            'naturalidade': chat_flow.state.naturalidade,
            'endereco': chat_flow.state.endereco,
            'email': chat_flow.state.email,
            'nome_mae': chat_flow.state.nome_mae,
            'renda': chat_flow.state.renda,
            'profissao': chat_flow.state.profissao,
            'current_question_id': chat_flow.state.current_question_id,
            'current_question_text': chat_flow.state.current_question_text,
            'next_question_id': chat_flow.state.next_question_id,
            'next_question_text': chat_flow.state.next_question_text,
            'conversation_stage': chat_flow.state.conversation_stage,
            'is_complete': chat_flow.state.is_complete,
            'updated_at': datetime.now().isoformat()
        }

        await redis_client.set_session_data(
            chat_flow.state.whatsapp_number,
            session_data,
            self.session_ttl
        )

    async def update_session(self, chat_flow: "ChatFlow"):
        """
        Atualiza sessão no Redis após mudanças
        """
        await self._save_session_to_redis(chat_flow)

    async def add_message_to_history(self, whatsapp_number: str, message_type: str, content: str):
        """
        Adiciona mensagem ao histórico no Redis
        """
        await redis_client.add_message_to_history(whatsapp_number, message_type, content)

    async def get_conversation_history(self, whatsapp_number: str, limit: int = 50) -> str:
        """
        Recupera histórico de conversas do Redis em formato de string
        """
        history = await redis_client.get_conversation_history(whatsapp_number, limit)

        if history:
            history_text = []
            for msg in history:
                history_text.append(f"{msg['type']}: {msg['content']}")
            return "\n".join(history_text)

        return ""

    async def remove_session(self, whatsapp_number: str):
        """
        Remove sessão do Redis
        """
        result = await redis_client.delete_session(whatsapp_number)
        if result:
            print(f"🗑️ Sessão removida do Redis: {whatsapp_number}")

    async def get_session_stats(self) -> SessionStats:
        """
        Retorna estatísticas detalhadas
        """
        redis_stats = await redis_client.get_stats()

        avg_response_time = 0.0
        if self._stats['request_count'] > 0:
            avg_response_time = self._stats['total_response_time'] / self._stats['request_count']

        return SessionStats(
            redis_sessions=redis_stats.get('active_sessions', 0),
            redis_histories=redis_stats.get('active_histories', 0),
            redis_memory=redis_stats.get('redis_memory_used', 'N/A'),
            total_messages_processed=self._stats['total_messages'],
            avg_response_time_ms=round(avg_response_time, 2)
        )

    def _update_stats(self, response_time_ms: float):
        """
        Atualiza estatísticas internas
        """
        self._stats['request_count'] += 1
        self._stats['total_response_time'] += response_time_ms

        if response_time_ms > 1000:  # Log se demorar mais que 1s
            print(f"⚠️ Resposta lenta: {response_time_ms:.2f}ms")

    async def cleanup(self):
        """
        Limpeza de recursos
        """
        await redis_client.close()
        print("🧹 RedisChatSessionManager limpo")

# Instância global
redis_session_manager = RedisChatSessionManager()
