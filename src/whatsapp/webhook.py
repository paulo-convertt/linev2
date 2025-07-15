from cache.redis_chat_session_manager import RedisChatSessionManager
from whatsapp.client import WhatsAppClient
from typing import Dict
from datetime import datetime
from database.config import SessionLocal
from database.models import ConversationHistory
from crews.chat_crew.chat_crew import ChatCrew
from crews.chat_crew.chat_flow import ChatFlow
from fastapi import FastAPI, Request, HTTPException
from database.database_client import DatabaseClient
from models import ChatState
import asyncio
import os

app = FastAPI()

class WhatsAppWebhookHandler:
    def __init__(self):
        self.whatsapp_client = WhatsAppClient()
        self.session_manager = RedisChatSessionManager()
        self.database_client = DatabaseClient()
        self._db_write_queue = asyncio.Queue()
        self.chat_crews = {}
        self._initialized = False

        asyncio.create_task(self._db_write_worker())

    async def _process_message(self, message_data: Dict):
        """
        Processa mensagem de forma otimizada usando Redis
        """
        # Inicializa Redis se necessário
        if not self._initialized:
            await self.session_manager.initialize()
            self._initialized = True

        messages = message_data.get("messages", [])

        for message in messages:
            from_number = message["from"]
            message_text = message.get("text", {}).get("body", "")

            chat_flow = await self.session_manager.get_or_create_session(from_number)

            await self.session_manager.add_message_to_history(from_number, "user", message_text)

            # Processa com o crew
            response = await self._process_with_crew(chat_flow, from_number, message_text)

            # Adiciona resposta do bot ao histórico do Redis
            await self.session_manager.add_message_to_history(from_number, "assistant", response)

            # Atualiza sessão no Redis
            await self.session_manager.update_session(chat_flow)

            # Envia mensagem (descomente quando pronto)
            #self.whatsapp_client.send_message(from_number, response)

            # Agenda salvamento no PostgreSQL (assíncrono)
            await self._queue_db_save(from_number, "user", message_text)
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

        # Cria ou recupera crew para este número
        if whatsapp_number not in self.chat_crews:
            self.chat_crews[whatsapp_number] = ChatCrew()

        crew = self.chat_crews[whatsapp_number]

        # Obtém histórico atualizado do Redis
        conversation_history = await self.session_manager.get_conversation_history(whatsapp_number)

        # Executa crew
        result = crew.crew().kickoff(inputs={
            "state": chat_flow.state.model_dump(),
            "current_question_text": chat_flow.state.current_question_text,
            "message": message,
            "history": conversation_history
        })

        if isinstance(result.pydantic, ChatState):
            new_state = result.pydantic.model_dump()
            chat_flow.state.message = new_state["message"]
            field_id = chat_flow.question_manager.get_field_id(
                chat_flow.state.current_question_id
            )

            for key, value in new_state.items():
                if hasattr(chat_flow.state, key):
                    setattr(chat_flow.state, key, value)

            self.database_client.upsert_lead(chat_flow.state.model_dump())

            if new_state.get(field_id):
                chat_flow._determine_next_question()

        return chat_flow.state.current_question_text

    async def handle_webhook(self, request: Request):
        """Processa webhooks do WhatsApp"""
        body = await request.json()

        # Verifica se é uma mensagem
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        response = await self._process_message(change["value"])

        return {"response": response}

@app.post("/webhook")
async def webhook(request: Request):
    handler = WhatsAppWebhookHandler()
    return await handler.handle_webhook(request)

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
