from regex import D
from database.models import LeadConsorcio
from typing import Any, Dict
from database.config import SessionLocal
import json

class DatabaseClient():
    def upsert_lead(self, data: Dict) -> str:
        db = SessionLocal()
        try:
            whatsapp_number = data.get("whatsapp_number")
            if not whatsapp_number:
                return "whatsapp_number é obrigatório"

            lead = db.query(LeadConsorcio).filter(
                LeadConsorcio.whatsapp_number == whatsapp_number
            ).first()

            if not lead:
                lead = LeadConsorcio(whatsapp_number=whatsapp_number)
                db.add(lead)

            lead_fields = [
                "nome", "cpf", "estado_civil", "naturalidade", "endereco",
                "email", "nome_mae", "renda", "profissao",
                "current_question_id", "current_question_text",
                "next_question_id", "next_question_text",
                "conversation_stage", "is_complete", "lead_score"
            ]

            for field in lead_fields:
                value = data.get(field)
                if hasattr(lead, field) and value is not None:
                    current_value = getattr(lead, field)
                    if current_value != value:
                        setattr(lead, field, value)

            db.commit()
            return f"Dados salvos com sucesso para {whatsapp_number}"

        except Exception as e:
            db.rollback()
            return f"Erro ao salvar dados: {str(e)}"
        finally:
            db.close()

    def get_lead(self, data: dict) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            whatsapp_number = data.get("whatsapp_number")
            if not whatsapp_number:
                return {"error": "whatsapp_number é obrigatório"}

            lead = db.query(LeadConsorcio).filter(
                LeadConsorcio.whatsapp_number == whatsapp_number
            ).first()

            if lead:
                lead_dict = {
                    "whatsapp_number": lead.whatsapp_number,
                    "nome": lead.nome,
                    "cpf": lead.cpf,
                    "estado_civil": lead.estado_civil,
                    "naturalidade": lead.naturalidade,
                    "endereco": lead.endereco,
                    "email": lead.email,
                    "nome_mae": lead.nome_mae,
                    "renda": lead.renda,
                    "profissao": lead.profissao,
                    "conversation_stage": lead.conversation_stage,
                    "is_complete": lead.is_complete,
                    "created_at": lead.created_at.isoformat() if bool(lead.created_at) else None,
                    "updated_at": lead.updated_at.isoformat() if bool(lead.updated_at) else None
                }
                return lead_dict
            else:
                return {}

        except Exception as e:
            return {"error": f"Erro ao buscar dados: {str(e)}"}
        finally:
            db.close()
