import logging
from typing import Dict, Any, Callable, Optional, TYPE_CHECKING
from app.services.patient_service import PatientService

if TYPE_CHECKING:
    from app.application.dispatcher import IntentDispatcher

logger = logging.getLogger(__name__)

# --- Handler Functions ---

def handle_start(dispatcher: 'IntentDispatcher') -> str:
    if dispatcher.session:
        user = dispatcher.session.get("user", {})
        name = user.get("first_name") or user.get("username", "user")
        return f"Welcome back, *{name}*! 👋\nHow can I help you? Type /help for options."
    return "Welcome to CARE! 👋\nYour digital health assistant. Type /login to start."

def handle_login(dispatcher: 'IntentDispatcher') -> str:
    dispatcher.set_state("AWAITING_PHONE")
    return "Please enter your registered phone number (e.g., +919000000000):"

def handle_logout(dispatcher: 'IntentDispatcher') -> str:
    dispatcher.clear_session()
    dispatcher.clear_state()
    return "✅ Logged out successfully."

def handle_meds(dispatcher: 'IntentDispatcher') -> str:
    token = dispatcher.session.get("access_token")
    if not token:
        return "🔒 Please /login to see your medications."
    
    # Use PatientService instead of calling API directly
    service = PatientService(dispatcher.api_client)
    return service.get_medication_summary(token)

def handle_records(dispatcher: 'IntentDispatcher') -> str:
    token = dispatcher.session.get("access_token")
    if not token:
        return "🔒 Please /login to see your records."
    
    # Use PatientService instead of calling API directly
    service = PatientService(dispatcher.api_client)
    return service.get_encounter_summary(token)

def handle_help(dispatcher: 'IntentDispatcher') -> str:
    help_text = "🛠️ *Available Commands:*\n\n"
    if not dispatcher.session:
        help_text += "• /login - Link account\n"
    else:
        help_text += "• /hi - Greeting\n"
        help_text += "• /meds - Medications\n"
        help_text += "• /records - Clinical Encounters\n"
        help_text += "• /logout - Unlink session\n"
    return help_text

# --- Intent Registry ---

INTENT_REGISTRY: Dict[str, Callable[['IntentDispatcher'], str]] = {
    "/start": handle_start,
    "/hi": handle_start,
    "hi": handle_start,
    "hello": handle_start,
    "/login": handle_login,
    "/logout": handle_logout,
    "/meds": handle_meds,
    "/records": handle_records,
    "/help": handle_help
}
