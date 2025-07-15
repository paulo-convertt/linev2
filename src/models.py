from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ChatState(BaseModel):
    whatsapp_number: str = ""
    message: Optional[str] = None
    history: Optional[str] = None

    nome: Optional[str] = None
    cpf: Optional[str] = None
    estado_civil: Optional[str] = None
    naturalidade: Optional[str] = None
    endereco: Optional[str] = None
    email: Optional[str] = None
    nome_mae: Optional[str] = None
    renda: Optional[str] = None
    profissao: Optional[str] = None

    current_question_id: str = ""
    current_question_text: str = ""
    next_question_id: str = ""
    next_question_text: str = ""
    conversation_stage: str = "inicio"
    is_complete: bool = False
    requires_human_handoff: bool = False

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class LeadScoringConsorcio(BaseModel):
    score: int
    categoria: str
    razoes: list[str]
    recomendacoes: list[str]
