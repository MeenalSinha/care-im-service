import logging
import json
import redis
from typing import Dict, Any, Optional
from app.clients.care_api import CareAPIClient, CareAPIError
from app.core.intents import INTENT_REGISTRY
from app.config import settings

logger = logging.getLogger(__name__)

# Constants
STATE_IDLE = "IDLE"
STATE_AWAITING_PHONE = "AWAITING_PHONE"
STATE_AWAITING_OTP = "AWAITING_OTP"

# Local State Management (Redis)
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

class IntentDispatcher:
    """
    Main Orchestrator for Messaging and Contextual States.
    Acts as the entry point for commands and manages stateful conversations.
    """
    def __init__(self, whatsapp_id: str, message_body: str, api_client: CareAPIClient):
        self.whatsapp_id = whatsapp_id
        self.message = message_body.strip()
        self.api_client = api_client
        self.cache_key = f"wa_bot_state:{self.whatsapp_id}"
        self.user_session_key = f"wa_user_session:{self.whatsapp_id}"

        # Initialize context from Redis
        self.state = self._load_json(self.cache_key, {"state": STATE_IDLE})
        self.session = self._load_json(self.user_session_key, {})

    def _load_json(self, key: str, default: Any) -> Any:
        try:
            data = r.get(key)
            return json.loads(data) if data else default
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load context for {key}: {str(e)}")
            return default

    def dispatch(self) -> str:
        """Central dispatch logic using state machine and intent registry."""
        current_state = self.state.get("state")
        logger.info(f"Dispatching intent for {self.whatsapp_id} (State: {current_state})")

        # 1. State-based handling (Priority over commands)
        if current_state == STATE_AWAITING_PHONE:
            return self.handle_phone_input()
        if current_state == STATE_AWAITING_OTP:
            return self.handle_otp_input()

        # 2. Command-based handling (Intent Registry)
        cmd = self.message.lower().split()[0] if self.message else ""
        handler = INTENT_REGISTRY.get(cmd)
        
        if handler:
            return handler(self)

        return "I'm sorry, I don't understand that command. Type /help to see what I can do."

    # --- State Management Helpers ---

    def set_state(self, state_name: str, **kwargs):
        """Persists contextual state to Redis with 10min expiry."""
        new_state = {"state": state_name, **kwargs}
        r.set(self.cache_key, json.dumps(new_state), ex=600)

    def clear_state(self):
        """Clears the current conversation state."""
        r.delete(self.cache_key)

    def set_session(self, token: str, user_data: Dict[str, Any]):
        """Persists the authenticated user session."""
        session = {"access_token": token, "user": user_data}
        r.set(self.user_session_key, json.dumps(session), ex=settings.SESSION_EXPIRY)

    def clear_session(self):
        """Clears the authenticated user session."""
        r.delete(self.user_session_key)

    # --- Workflow Handlers ---

    def handle_phone_input(self) -> str:
        phone_number = self.message
        if not phone_number.startswith("+") or len(phone_number) < 10:
            return "❌ Invalid format. Use full international format (e.g., +91...)."

        try:
            self.api_client.request_otp(phone_number)
            self.set_state(STATE_AWAITING_OTP, phone_number=phone_number)
            return f"✅ OTP request sent via CARE. Please enter the verification code sent to {phone_number}."
        except CareAPIError as e:
            logger.error(f"OTP request failed: {str(e)}")
            return "❌ Failed to request OTP. Ensure your number is registered with CARE."

    def handle_otp_input(self) -> str:
        otp = self.message
        phone_number = self.state.get("phone_number")
        if not phone_number:
            self.clear_state()
            return "⚠️ Session expired. Type /login to restart the process."

        try:
            token = self.api_client.login_with_otp(phone_number, otp)
            if not token:
                return "❌ Invalid or expired OTP. Try again."

            user_data = self.api_client.get_user_me(token)
            self.set_session(token, user_data)
            self.clear_state()
            return f"🎉 Linked to *{user_data.get('username')}*! You can now use /meds or /records."
        except CareAPIError as e:
            return f"❌ Verification failed: {str(e.status_code) if e.status_code else ''}"
