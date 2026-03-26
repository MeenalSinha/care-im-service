import logging
from fastapi import FastAPI, Request, HTTPException
from app.messaging.providers.whatsapp import WhatsAppProvider
from app.messaging.dispatcher import IntentDispatcher
from app.clients.care_api import CareAPIClient
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CARE IM Service")

# Initialize clients
whatsapp_provider = WhatsAppProvider()
care_client = CareAPIClient(settings.CARE_API_BASE_URL, settings.CARE_API_KEY)

@app.get("/")
async def root():
    return {"status": "ok", "service": "care-im-service"}

# --- WhatsApp Webhook ---

@app.get("/webhooks/whatsapp/")
async def verify_whatsapp_webhook(request: Request):
    """
    Verification endpoint for Meta/WhatsApp.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully.")
        return int(challenge)
    
    logger.warning(f"WhatsApp webhook verification failed. Token mismatch: {token}")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhooks/whatsapp/")
async def handle_whatsapp_webhook(request: Request):
    """
    Main endpoint for receiving WhatsApp messages.
    """
    data = await request.json()
    logger.debug(f"Received WhatsApp webhook data: {data}")

    # Process messages (extracted as list of (whatsapp_id, body))
    messages = whatsapp_provider.handle_webhook(data)
    
    for whatsapp_id, message_body in messages:
        # 1. Initialize Dispatcher for this user
        dispatcher = IntentDispatcher(whatsapp_id, message_body, care_client)
        
        # 2. Process Intent & Get Response
        response_text = dispatcher.dispatch()
        
        # 3. Send Response via Provider
        whatsapp_provider.send_message(whatsapp_id, response_text)

    return {"status": "success"}

# --- Tasks & Notifications ---

@app.post("/notify/")
async def trigger_notification(recipient_id: str, message: str, provider: str = "whatsapp"):
    """
    Generic notification endpoint for CARE backend to trigger messages.
    """
    if provider == "whatsapp":
        ok = whatsapp_provider.send_message(recipient_id, message)
        if ok:
            return {"status": "sent"}
    
    raise HTTPException(status_code=400, detail="Unsupported provider or message failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
