# Importa configurações globais (inclui desabilitação do OpenTelemetry)
from cache.redis_chat_session_manager import RedisChatSessionManager
from crews.chat_crew.chat_crew import ChatCrew
from human_handoff.human_handoff import HumanHandoffManager
from scoring.consorcio_scoring import ConsorcioLeadScoring
from whatsapp.client import WhatsAppClient
from typing import Dict
from datetime import datetime
from database.config import SessionLocal
from database.models import ConversationHistory
from crews.chat_crew.chat_flow import ChatFlow
from fastapi import FastAPI, Request, HTTPException
from database.database_client import DatabaseClient
from models import ChatState
import asyncio
import os
import json

app = FastAPI()

class WhatsAppWebhookHandler:
    def __init__(self):
        self.whatsapp_client = WhatsAppClient()
        self.session_manager = RedisChatSessionManager()
        self.database_client = DatabaseClient()
        self._db_write_queue = asyncio.Queue()
        # ✅ Uma única instância do ChatCrew para todos os usuários
        self.chat_crew = ChatCrew()
        self.human_handoff = HumanHandoffManager()
        self.consorcio_lead_scoring = ConsorcioLeadScoring()
        # ✅ Inicializa crews pré-criados para máxima performance
        self.chat_crew._initialize_precreated_crews()
        self._initialized = False
        self._db_worker_started = False

    async def _process_message(self, message: str, from_number: str):
        """
        Processa mensagem de forma otimizada usando Redis
        """
        # Inicializa Redis se necessário
        if not self._initialized:
            await self.session_manager.initialize()
            self._initialized = True

        # Inicia DB worker se necessário
        if not self._db_worker_started:
            asyncio.create_task(self._db_write_worker())
            self._db_worker_started = True

        chat_flow = await self.session_manager.get_or_create_session(from_number)

        await self.session_manager.add_message_to_history(from_number, "user", message)

        # Processa com o crew
        response = await self._process_with_crew(chat_flow, from_number, message)

        # Adiciona resposta do bot ao histórico do Redis
        await self.session_manager.add_message_to_history(from_number, "assistant", response)

        # Atualiza sessão no Redis
        await self.session_manager.update_session(chat_flow)

        # Envia mensagem (descomente quando pronto)
        self.whatsapp_client.send_message(from_number, response)

        # Agenda salvamento no PostgreSQL (assíncrono)
        await self._queue_db_save(from_number, "user", message)
        await self._queue_db_save(from_number, "assistant", response)

        return response

    async def _queue_db_save(self, whatsapp_number: str, message_type: str, content: str):
        """
        Agenda salvamento no banco para processamento assíncrono
        """
        await self._db_write_queue.put({
            "whatsapp_number": whatsapp_number,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.now()
        })

    async def _db_write_worker(self):
        """
        Worker assíncrono para escrever no banco sem bloquear o processamento
        """
        batch_size = 10
        batch_timeout = 5  # segundos

        while True:
            try:
                batch = []

                # Coleta batch de mensagens
                try:
                    # Primeiro item (bloqueia até ter pelo menos um)
                    item = await self._db_write_queue.get()
                    batch.append(item)

                    # Itens adicionais (não bloqueia)
                    for _ in range(batch_size - 1):
                        try:
                            item = await asyncio.wait_for(
                                self._db_write_queue.get(),
                                timeout=batch_timeout
                            )
                            batch.append(item)
                        except asyncio.TimeoutError:
                            break

                except Exception as e:
                    print(f"❌ Erro ao coletar batch: {e}")
                    continue

                # Salva batch no banco
                if batch:
                    await self._save_batch_to_db(batch)

            except Exception as e:
                print(f"❌ Erro no DB worker: {e}")
                await asyncio.sleep(1)

    async def _save_batch_to_db(self, batch: list):
        """
        Salva batch de mensagens no banco
        """
        db = SessionLocal()
        try:
            for item in batch:
                conversation = ConversationHistory(
                    whatsapp_number=item["whatsapp_number"],
                    message_type=item["message_type"],
                    content=item["content"],
                    timestamp=item["timestamp"]
                )
                db.add(conversation)

            db.commit()
            print(f"💾 Batch salvo: {len(batch)} mensagens")

        except Exception as e:
            print(f"❌ Erro ao salvar batch: {e}")
            db.rollback()
        finally:
            db.close()

    async def _process_with_crew(self, chat_flow, whatsapp_number: str, message: str) -> str:
        """Processa mensagem com o ChatCrew usando histórico do Redis"""

        # ✅ Usa a instância única do ChatCrew
        crew = self.chat_crew

        # Obtém histórico atualizado do Redis
        conversation_history = await self.session_manager.get_conversation_history(whatsapp_number)

        # ✅ Cria crew condicional baseado no estado atual
        qualification_crew = crew.get_crew()

        # Executa crew
        result = qualification_crew.kickoff(inputs={
            "state": chat_flow.state.model_dump(),
            "message": message,
            "history": conversation_history
        })

        print(f"🚀 Crew result: {result.raw}")
        # Se executou apenas qualify_lead task, processa como antes
        new_state = json.loads(result.raw.strip().strip('```'))

        for key, value in new_state.items():
            if hasattr(chat_flow.state, key):
                setattr(chat_flow.state, key, value)

        scoring = self.consorcio_lead_scoring.calculate_score(new_state)
        chat_flow.state.lead_score = scoring.get("score", 0)

        self.database_client.upsert_lead(chat_flow.state.model_dump())

        # if chat_flow.state.requires_human_handoff or chat_flow.state.is_complete:
        #     handoff_message = "Perfeito! Já vou te passar para um especialista que vai te ajudar com todos os detalhes. Obrigado por falar comigo 😊"
        #     await self.session_manager.add_message_to_history(whatsapp_number, "assistant", handoff_message)
        #     self.human_handoff.send_lead_to_zenvia(new_state, scoring, handoff_message)
        #     return handoff_message

        return new_state.get("mensagem")

    async def handle_webhook(self, request: Request):
        """Processa webhooks do WhatsApp"""
        body = await request.json()

        # Verifica se é uma mensagem
        message = body.get("message", {}).get("contents", [{}])[0].get("text", "")
        phone = body.get("message", {}).get("from", "")
        asyncio.create_task(self._process_message(message, phone))

        return {"message": "Webhook processed successfully"}

# ✅ Cria uma única instância global do handler (com crews pré-criados)
webhook_handler = WhatsAppWebhookHandler()

@app.post("/webhook")
async def webhook(request: Request):
    # ✅ Usa a instância global ao invés de criar nova a cada requisição
    return await webhook_handler.handle_webhook(request)

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Verificação do webhook (Meta requirement)"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = str(request.query_params.get("hub.challenge"))

    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

    if mode == "subscribe" and token == verify_token:
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")
