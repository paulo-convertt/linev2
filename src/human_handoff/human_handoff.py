import os
import requests
import json
import uuid
from typing import Dict, Any, Optional, Union
from datetime import datetime
from database.models import ChatState


class HumanHandoffManager:
    """
    Manages the handoff process from chatbot to human agents by converting
    chat state data to lead format and sending it to Zenvia Sales API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the HumanHandoffManager.

        Args:
            api_key: Zenvia API key. If not provided, will use ZCC_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('ZCC_API_KEY')
        self.base_url = "https://sales.zenvia.com/api/v1/lead/retail"

    def format_history(self, history: str, handoff_message: str) -> str:
        """
        Format the conversation history with proper structure and bullet points.

        Args:
            history: Raw conversation history string

        Returns:
            Formatted history string with header and bullet points
        """
        if not history:
            return ""

        # Split the history into individual messages
        messages = []
        current_message = ""

        for line in history.split():
            if line.startswith("user:") or line.startswith("assistant:"):
                if current_message:
                    messages.append(current_message.strip())
                current_message = line
            else:
                current_message += " " + line

        # Add the last message if there's any
        if current_message:
            messages.append(current_message.strip())

        # Take only the last 10 messages
        recent_messages = messages[-10:] if len(messages) > 10 else messages

        # Format with bullet points
        formatted_messages = []
        for message in recent_messages:
            formatted_messages.append(f"• {message}")

        formatted_messages.append(f"• assistant: {handoff_message}")

        # Create the final formatted string
        formatted_history = "HISTÓRICO DAS ÚLTIMAS 10 MENSAGENS:\n" + " ".join(formatted_messages)

        return formatted_history

    def format_scoring(self, scoring: Dict[str, Any]) -> str:
        """
        Format the scoring dictionary into a structured string.

        Args:
            scoring: Dictionary containing scoring information

        Returns:
            Formatted scoring string
        """
        if not scoring:
            return ""

        score = scoring.get('score', 'N/A')
        categoria = scoring.get('categoria', 'N/A')
        prioridade = scoring.get('prioridade', 'N/A')
        recomendacoes = scoring.get('recomendacoes', 'N/A')

        formatted_scoring = (
            f"• Score: {score} "
            f"• Categoria: {categoria} "
            f"• Prioridade: {prioridade} "
            f"• Recomendacoes: {recomendacoes} "
        )

        return formatted_scoring

    def convert_lead_data_to_lead_data(self, lead_data: Dict[str, Any], scoring: Dict[str, Any], handoff_message: str, conversation_history: str) -> Dict[str, Any]:
        """
        Convert ChatState to Zenvia lead data format

        Args:
            lead_data: ChatState object containing lead information

        Returns:
            Dictionary formatted for Zenvia API
        """
        # Split nome into firstName and lastName if available
        first_name = ""
        last_name = ""
        if lead_data.get("nome"):
            name_parts = lead_data["nome"].strip().split()
            if len(name_parts) > 0:
                first_name = name_parts[0]
                if len(name_parts) > 1:
                    last_name = " ".join(name_parts[1:])

        # Prepare phones list
        phones = []
        if lead_data.get("whatsapp_number"):
            # Remove any non-numeric characters and ensure it starts with country code
            clean_phone = ''.join(filter(str.isdigit, lead_data["whatsapp_number"]))
            if not clean_phone.startswith('55'):
                clean_phone = '55' + clean_phone
            phones.append(clean_phone)

        # Prepare emails list
        emails = []
        if lead_data.get("email"):
            emails.append(lead_data["email"])

        # Create history entry with conversation summary
        history = []

        formatted_history = self.format_history(conversation_history, handoff_message)
        history.append({
            "type": "note",
            "content": formatted_history
        })

        # Add professional and income info if available
        formatted_scoring = self.format_scoring(scoring)

            # Collect all available lead information
        lead_info = []
        if lead_data.get("nome"):
            lead_info.append(f"• Nome: {lead_data['nome']}")
        if lead_data.get("cpf"):
            lead_info.append(f"• CPF: {lead_data['cpf']}")
        if lead_data.get("estado_civil"):
            lead_info.append(f"• Estado Civil: {lead_data['estado_civil']}")
        if lead_data.get("naturalidade"):
            lead_info.append(f"• Naturalidade: {lead_data['naturalidade']}")
        if lead_data.get("endereco"):
            lead_info.append(f"• Endereço: {lead_data['endereco']}")
        if lead_data.get("email"):
            lead_info.append(f"• Email: {lead_data['email']}")
        if lead_data.get("nome_mae"):
            lead_info.append(f"• Nome da Mãe: {lead_data['nome_mae']}")
        if lead_data.get("renda"):
            lead_info.append(f"• Renda: {lead_data['renda']}")
        if lead_data.get("profissao"):
            lead_info.append(f"• Profissão: {lead_data['profissao']}")

        lead_info_content = " ".join(lead_info)

        history.append({
            "type": "note",
            "content": f"INFORMAÇÕES COMPLETAS DO LEAD: {lead_info_content} {formatted_scoring}"
        })

        # Add sentiment analysis if available
        if lead_data.get("sentiment_analysis"):
            history.append({
                "type": "note",
                "content": f"ANÁLISE DE SENTIMENTO: {lead_data['sentiment_analysis']}"
            })

        # Build the payload
        lead_data = {
            "priority": 0,
            "provider": "naRede Consórcio",
            "utmSource": "whatsapp_chatbot",
            "utmMedium": "chatbot",
            "utmCampaign": "Lead Qualification Bot",
            "firstName": first_name,
            "lastName": last_name,
            "phones": phones,
            "emails": emails,
            "address": lead_data.get("endereco") or "",
            "country": "Brasil",
            "source": "whatsapp_chatbot",
            "medium": "chatbot",
            "history": history
        }

        return lead_data

    def send_lead_to_zenvia(self, lead_data: Dict[str, Any], scoring: Dict[str, Any], handoff_message: str, conversation_history: str) -> Optional[Dict[str, Any]]:
        """
        Send lead data to Zenvia Sales API

        Args:
            lead_data: ChatState object or Dictionary containing the lead information

        Returns:
            Response data from the API or None if failed

        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If the response is not valid JSON
        """
        payload = self.convert_lead_data_to_lead_data(lead_data, scoring, handoff_message, conversation_history)

        url = f"{self.base_url}?api-key={self.api_key}"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            print("📤 Enviando lead para Zenvia Sales API...")
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )

            # Raise an exception for bad status codes
            response.raise_for_status()

            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                # If response is not JSON, return status info
                return {
                    "status_code": response.status_code,
                    "message": "Request successful but response is not JSON",
                    "text": response.text
                }

        except requests.exceptions.Timeout:
            raise requests.exceptions.RequestException("Request timed out")
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.RequestException("Connection error occurred")
        except requests.exceptions.HTTPError as e:
            raise requests.exceptions.RequestException(f"HTTP error occurred: {e}")
        except Exception as e:
            raise requests.exceptions.RequestException(f"Unexpected error: {e}")

