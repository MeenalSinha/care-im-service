import requests
import logging
from app.messaging.providers.base import BaseMessagingProvider
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppProvider(BaseMessagingProvider):
    def __init__(self):
        self.api_url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    def send_message(self, recipient_id: str, text: str) -> bool:
        if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            logger.info(f"[WhatsApp DEV] To {recipient_id}: {text}")
            return True

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text},
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"WhatsApp message sent to {recipient_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return False

    def handle_webhook(self, request_data: dict) -> list:
        """
        Extract messages from WhatsApp webhook data.
        Returns a list of tuples (whatsapp_id, message_body).
        """
        extracted = []
        try:
            for entry in request_data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for msg in value["messages"]:
                            whatsapp_id = msg.get("from")
                            if msg.get("type") == "text":
                                body = msg.get("text", {}).get("body")
                                extracted.append((whatsapp_id, body))
        except Exception as e:
            logger.error(f"Error parsing WhatsApp webhook: {str(e)}")
        
        return extracted
