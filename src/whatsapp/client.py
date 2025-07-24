import requests
from typing import Dict, Optional
import os

class WhatsAppClient:
    def __init__(self):
        self.x_api_token = os.getenv("ZCC_API_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.base_url = "https://api.zenvia.com/v2/channels/whatsapp"

    def send_message(self, to: str, message: str) -> Dict:
        """Envia mensagem texto via WhatsApp"""
        url = f"{self.base_url}/messages"

        payload = {
            "from": "551151430995",
            "to": f"{to}",
            "contents": [
                {
                    "type": "text",
                    "text": f"{message}"
                }
            ]
        }

        headers = {
            "X-API-TOKEN": f"{self.x_api_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()
