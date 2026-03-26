from abc import ABC, abstractmethod

class BaseMessagingProvider(ABC):
    @abstractmethod
    def send_message(self, recipient_id: str, text: str) -> bool:
        """
        Send a text message to a specific recipient.
        """
        pass

    @abstractmethod
    def handle_webhook(self, request_data: dict) -> str:
        """
        Process incoming webhook data and return a response if needed.
        """
        pass
