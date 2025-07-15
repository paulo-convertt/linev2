import requests
from typing import Dict, Optional
import os

class WhatsAppClient:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID") 
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        
    def send_message(self, to: str, message: str) -> Dict:
        """Envia mensagem texto via WhatsApp"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    
    def send_interactive_message(self, to: str, message: str, buttons: list) -> Dict:
        """Envia mensagem com botões interativos"""
        url = f"{self.base_url}/messages"
        
        interactive_buttons = []
        for i, button in enumerate(buttons[:3]):  # WhatsApp limita a 3 botões
            interactive_buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": button[:20]  # Limite de 20 caracteres
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message},
                "action": {"buttons": interactive_buttons}
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()