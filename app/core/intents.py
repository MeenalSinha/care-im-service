import logging
from typing import Dict, Any, Callable, Optional, TYPE_CHECKING
from app.clients.care_api import CareAPIClient, CareAPIError

if TYPE_CHECKING:
    from app.messaging.dispatcher import IntentDispatcher

logger = logging.getLogger(__name__)

# --- Handler Functions ---

def handle_start(dispatcher: 'IntentDispatcher') -> str:
    """Greets the user based on session status."""
    if dispatcher.session:
        user = dispatcher.session.get("user", {})
        name = user.get("first_name") or user.get("username", "user")
        return f"Welcome back, *{name}*! 👋\nHow can I help you? Type /help for options."
    return "Welcome to CARE! 👋\nYour digital health assistant. Type /login to start."

def handle_login(dispatcher: 'IntentDispatcher') -> str:
    """Sets state to AWAITING_PHONE to start OTP flow."""
    dispatcher.set_state("AWAITING_PHONE")
    return "Please enter your registered phone number (e.g., +919000000000):"

def handle_logout(dispatcher: 'IntentDispatcher') -> str:
    """Clears all session and state data."""
    if not dispatcher.session:
        return "You are not logged in."
    dispatcher.clear_session()
    dispatcher.clear_state()
    return "✅ Logged out successfully."

def handle_meds(dispatcher: 'IntentDispatcher') -> str:
    """Lists active medications using the CARE client."""
    token = dispatcher.session.get("access_token")
    if not token:
        return "🔒 Please /login to see your medications."

    try:
        meds = dispatcher.api_client.list_medications(token)
        if not meds:
            return "You have no active Medications."

        response = "💊 *Active Medications:*\n"
        for med in meds:
            name = med.get("medication", {}).get("display", "Unnamed")
            response += f"• {name}\n"
        return response
    except CareAPIError as e:
        logger.error(f"Failed to fetch meds: {str(e)}")
        return "❌ Error fetching your records. Try again later."

def handle_records(dispatcher: 'IntentDispatcher') -> str:
    """Lists recent encounters using the CARE client."""
    token = dispatcher.session.get("access_token")
    if not token:
        return "🔒 Please /login to see your records."

    try:
        encounters = dispatcher.api_client.list_encounters(token)
        if not encounters:
            return "No patient records found."

        response = "📊 *Recent Encounters:*\n"
        for enc in encounters[:5]:
            date = enc.get("created_date", "Unknown Date")
            status = enc.get("status", "Unknown")
            response += f"• {date}: {status.capitalize()}\n"
        return response
    except CareAPIError as e:
        return f"❌ Error retrieving records: {str(e.status_code) if e.status_code else ''}"

def handle_assets(dispatcher: 'IntentDispatcher') -> str:
    """Lists facility assets for staff users."""
    token = dispatcher.session.get("access_token")
    if not token:
        return "🔒 Please /login to access assets."

    user = dispatcher.session.get("user", {})
    facility_id = user.get("home_facility")
    if not facility_id:
        return "⚠️ You are not associated with any facility."

    try:
        assets = dispatcher.api_client.list_facility_assets(token, facility_id)
        if not assets:
            return "No assets found in your facility."

        response = f"🏢 *Facility Assets:*\n"
        for asset in assets[:10]:
            name = asset.get("name") or "Unknown Device"
            response += f"• {name} ({asset.get('status', 'Unknown')})\n"
        return response
    except CareAPIError:
        return "❌ Failed to load assets. Ensure you have the correct permissions."

def handle_help(dispatcher: 'IntentDispatcher') -> str:
    """Returns the available command list."""
    help_text = "🛠️ *Available Commands:*\n\n"
    if not dispatcher.session:
        help_text += "• /login - Link account\n"
    else:
        help_text += "• /hi - Greeting\n"
        help_text += "• /meds - Medications\n"
        help_text += "• /records - Recent Encounters\n"
        help_text += "• /assets - Facility Assets (Staff)\n"
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
    "/assets": handle_assets,
    "/help": handle_help
}
