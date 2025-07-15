import redis.asyncio as redis
import json
import os
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

class RedisClient:
    _instance = None
    _pool: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        """Inicializa a conexão com Redis"""
        if self._pool is None:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self._pool = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            print("✅ Redis client inicializado")

    async def close(self):
        """Fecha a conexão com Redis"""
        if self._pool:
            await self._pool.close()
            print("🔒 Redis client fechado")

    async def _ensure_connection(self):
        """Garante que a conexão está ativa"""
        if self._pool is None:
            await self.initialize()

    async def set_session_data(self, whatsapp_number: str, data: Dict[str, Any], ttl: int = 86400):
        """
        Armazena dados da sessão no Redis
        Args:
            whatsapp_number: Número do WhatsApp
            data: Dados da sessão
            ttl: Time to live em segundos (default: 24h)
        """
        try:
            await self._ensure_connection()
            key = f"session:{whatsapp_number}"
            serialized_data = json.dumps(data, default=str)
            await self._pool.setex(key, ttl, serialized_data)  # type: ignore
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar sessão no Redis: {e}")
            return False

    async def get_session_data(self, whatsapp_number: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados da sessão do Redis
        Args:
            whatsapp_number: Número do WhatsApp
        Returns:
            Dados da sessão ou None se não encontrado
        """
        try:
            await self._ensure_connection()
            key = f"session:{whatsapp_number}"
            data = await self._pool.get(key)  # type: ignore
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"❌ Erro ao recuperar sessão do Redis: {e}")
            return None

    async def delete_session(self, whatsapp_number: str) -> bool:
        """
        Remove sessão do Redis
        Args:
            whatsapp_number: Número do WhatsApp
        Returns:
            True se removido com sucesso
        """
        try:
            await self._ensure_connection()
            key = f"session:{whatsapp_number}"
            result = await self._pool.delete(key)  # type: ignore
            return result > 0
        except Exception as e:
            print(f"❌ Erro ao deletar sessão do Redis: {e}")
            return False

    async def extend_session_ttl(self, whatsapp_number: str, ttl: int = 86400) -> bool:
        """
        Estende o TTL de uma sessão
        Args:
            whatsapp_number: Número do WhatsApp
            ttl: Novo TTL em segundos
        Returns:
            True se estendido com sucesso
        """
        try:
            await self._ensure_connection()
            key = f"session:{whatsapp_number}"
            result = await self._pool.expire(key, ttl)  # type: ignore
            return result
        except Exception as e:
            print(f"❌ Erro ao estender TTL da sessão: {e}")
            return False

    async def session_exists(self, whatsapp_number: str) -> bool:
        """
        Verifica se a sessão existe no Redis
        Args:
            whatsapp_number: Número do WhatsApp
        Returns:
            True se a sessão existe
        """
        try:
            await self._ensure_connection()
            key = f"session:{whatsapp_number}"
            result = await self._pool.exists(key)  # type: ignore
            return result > 0
        except Exception as e:
            print(f"❌ Erro ao verificar existência da sessão: {e}")
            return False

    async def add_message_to_history(self, whatsapp_number: str, message_type: str, content: str):
        """
        Adiciona mensagem ao histórico no Redis
        Args:
            whatsapp_number: Número do WhatsApp
            message_type: Tipo da mensagem (user/assistant)
            content: Conteúdo da mensagem
        """
        try:
            await self._ensure_connection()
            key = f"history:{whatsapp_number}"
            timestamp = datetime.now().isoformat()
            message_data = {
                "type": message_type,
                "content": content,
                "timestamp": timestamp
            }

            # Adiciona à lista e mantém apenas as últimas 100 mensagens
            await self._pool.lpush(key, json.dumps(message_data))  # type: ignore
            await self._pool.ltrim(key, 0, 99)  # type: ignore
            await self._pool.expire(key, 86400)  # type: ignore  # TTL de 24h

        except Exception as e:
            print(f"❌ Erro ao adicionar mensagem ao histórico: {e}")

    async def get_conversation_history(self, whatsapp_number: str, limit: int = 50) -> list:
        """
        Recupera histórico de conversas do Redis
        Args:
            whatsapp_number: Número do WhatsApp
            limit: Limite de mensagens a retornar
        Returns:
            Lista de mensagens ordenadas cronologicamente
        """
        try:
            await self._ensure_connection()
            key = f"history:{whatsapp_number}"
            messages = await self._pool.lrange(key, 0, limit - 1)  # type: ignore

            # Converte de JSON e inverte a ordem (mais antigas primeira)
            history = []
            for msg in reversed(messages):
                try:
                    history.append(json.loads(msg))
                except json.JSONDecodeError:
                    continue

            return history
        except Exception as e:
            print(f"❌ Erro ao recuperar histórico: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do Redis
        Returns:
            Dicionário com estatísticas
        """
        try:
            await self._ensure_connection()
            info = await self._pool.info()  # type: ignore

            # Conta sessões ativas
            session_keys = await self._pool.keys("session:*")  # type: ignore
            history_keys = await self._pool.keys("history:*")  # type: ignore

            return {
                "active_sessions": len(session_keys),
                "active_histories": len(history_keys),
                "redis_memory_used": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "redis_version": info.get('redis_version', 'N/A')
            }
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}

# Instância global
redis_client = RedisClient()
