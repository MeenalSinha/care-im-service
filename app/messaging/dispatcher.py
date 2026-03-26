import logging
import json
import redis
from app.services.care_api_client import CareAPIClient
from app.config import settings

logger = logging.getLogger(__name__)

# States
STATE_IDLE = "IDLE"
STATE_AWAITING_PHONE = "AWAITING_PHONE"
STATE_AWAITING_OTP = "AWAITING_OTP"

# Redis instance for state management
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

class IntentDispatcher:
    def __init__(self, whatsapp_id, message_body, api_client: CareAPIClient):
        self.whatsapp_id = whatsapp_id
        self.message = message_body.strip()
        self.api_client = api_client
        self.cache_key = f"wa_bot_state:{self.whatsapp_id}"
        self.user_session_key = f"wa_user_session:{self.whatsapp_id}"

        # Load session/state from Redis
        state_data = r.get(self.cache_key)
        self.state = json.loads(state_data) if state_data else {"state": STATE_IDLE}

        session_data = r.get(self.user_session_key)
        self.session = json.loads(session_data) if session_data else {}

    def dispatch(self) -> str:
        current_state = self.state.get("state")
        logger.info(f"Dispatching message from {self.whatsapp_id} (State: {current_state})")

        if current_state == STATE_AWAITING_PHONE:
            return self.handle_phone_input()
        if current_state == STATE_AWAITING_OTP:
            return self.handle_otp_input()

        # Command Dispatch
        cmd = self.message.lower().split()[0] if self.message else ""
        if cmd in ["/start", "/hi", "hi", "hello"]:
            return self.handle_start()
        elif cmd == "/login":
            return self.prompt_phone()
        elif cmd == "/logout":
            return self.handle_logout()
        elif cmd == "/help":
            return self.handle_help()
        elif cmd == "/meds":
            return self.handle_meds()
        elif cmd == "/records":
            return self.handle_records()
        elif cmd == "/assets":
            return self.handle_assets()

        return "I'm sorry, I don't understand that command. Type /help to see what I can do."

    def set_state(self, state_name, **kwargs):
        new_state = {"state": state_name, **kwargs}
        r.set(self.cache_key, json.dumps(new_state), ex=600)  # 10 min expiry

    def clear_state(self):
        r.delete(self.cache_key)

    def set_session(self, token, user_data):
        session = {"access_token": token, "user": user_data}
        r.set(self.user_session_key, json.dumps(session), ex=settings.SESSION_EXPIRY or 3600*24*7) # 7 days default

    def clear_session(self):
        r.delete(self.user_session_key)

    def handle_start(self):
        if self.session:
            user = self.session.get("user")
            name = user.get("first_name") or user.get("username")
            return f"Welcome back, *{name}*! 👋\nHow can I help you today? Type /help for options."
        return "Welcome to CARE! 👋\nI am your digital health assistant. Type /login to start."

    def prompt_phone(self):
        self.set_state(STATE_AWAITING_PHONE)
        return "Please enter your registered phone number (e.g., +919000000000):"

    def handle_phone_input(self):
        phone_number = self.message
        if not phone_number.startswith("+") or len(phone_number) < 10:
            return "Invalid format. Please enter a full phone number starting with +."

        ok, response = self.api_client.request_otp(phone_number)
        if not ok:
            return response.get("detail") or "Failed to request OTP. Contact support."

        self.set_state(STATE_AWAITING_OTP, phone_number=phone_number)
        return f"OTP request sent via CARE backend. Please enter the OTP sent to {phone_number}."

    def handle_otp_input(self):
        otp = self.message
        phone_number = self.state.get("phone_number")
        if not phone_number:
            self.clear_state()
            return "❌ Session expired. Type /login to start again."

        token = self.api_client.login_with_otp(phone_number, otp)
        if not token:
            return "❌ Invalid or expired OTP."

        user_data = self.api_client.get_user_profile(token)
        if not user_data:
            return "❌ Account found but failed to fetch profile."

        self.set_session(token, user_data)
        self.clear_state()
        return f"✅ Linked to *{user_data.get('username')}*! Try /meds or /records."

    def handle_logout(self):
        if not self.session:
            return "You are not logged in."
        self.clear_session()
        self.clear_state()
        return "✅ Logged out successfully."

    def handle_meds(self):
        token = self.session.get("access_token")
        if not token:
            return "🔒 Please /login to see your medications."

        meds = self.api_client.get_medications(token)
        if not meds:
            return "You have no active Medications."

        response = "💊 *Active Medications:*\n"
        for med in meds:
            name = med.get("medication", {}).get("display", "Unnamed")
            response += f"• {name}\n"
        return response

    def handle_records(self):
        token = self.session.get("access_token")
        if not token:
            return "🔒 Please /login to see your records."

        encounters = self.api_client.get_encounters(token)
        if not encounters or not encounters.get("results"):
            return "No patient records found."

        response = "📊 *Recent Encounters:*\n"
        for enc in encounters.get("results", [])[:5]:
            date = enc.get("created_date", "Unknown Date")
            status = enc.get("status", "Unknown")
            response += f"• {date}: {status.capitalize()}\n"
        return response

    def handle_assets(self):
        token = self.session.get("access_token")
        if not token:
            return "🔒 Please /login to see assets."

        user = self.session.get("user")
        facility_id = user.get("home_facility")
        if not facility_id:
            return "You are not associated with any facility."

        assets = self.api_client.get_assets(token, facility_id)
        if not assets or not assets.get("results"):
            return "No assets found in your facility."

        response = f"🏢 *Facility Assets:*\n"
        for asset in assets.get("results", [])[:10]:
            name = asset.get("name") or "Unknown Device"
            response += f"• {name} ({asset.get('status', 'Unknown')})\n"
        return response

    def handle_help(self):
        help_text = "🛠️ *Available Commands:*\n\n"
        if not self.session:
            help_text += "• /login - Link your account\n"
        else:
            help_text += "• /hi - Greeting\n"
            help_text += "• /meds - View Medications\n"
            help_text += "• /records - View Recent Encounters\n"
            help_text += "• /assets - View Assets (Staff Only)\n"
            help_text += "• /logout - Unlink account\n"
        return help_text
