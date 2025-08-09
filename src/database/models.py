from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

Base = declarative_base()

class LeadConsorcio(Base):
    __tablename__ = "leads_consorcio"

    id = Column(Integer, primary_key=True, index=True)
    whatsapp_number = Column(String(20), unique=True, index=True)

    nome = Column(String(255))
    cpf = Column(String(14))
    estado_civil = Column(String(50))
    naturalidade = Column(String(100))
    endereco = Column(Text)
    email = Column(String(255))
    nome_mae = Column(String(255))
    renda = Column(String(50))
    profissao = Column(String(100))

    conversation_stage = Column(String(50), default="inicio")
    is_complete = Column(Boolean, default=False)
    lead_score = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    whatsapp_number = Column(String(20), index=True)
    message_type = Column(String(20))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ChatState(BaseModel):
    whatsapp_number: str = ""
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
    lead_score: Optional[int] = 0

    conversation_stage: Optional[str] = "inicio"
    is_complete: bool = False
    requires_human_handoff: bool = False

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class LeadScoringConsorcio(BaseModel):
    score: int
    categoria: str
    razoes: list[str]
    recomendacoes: list[str]
