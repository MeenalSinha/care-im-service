from celery import Celery
from app.config import settings
from app.interfaces.providers.whatsapp import WhatsAppProvider
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery('care_im_tasks', broker=settings.CELERY_BROKER_URL)
app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Initialize Provider inside tasks or as a singleton
whatsapp_provider = WhatsAppProvider()

@app.task(name="send_whatsapp_message")
def send_whatsapp_message(recipient_id: str, message: str):
    """
    Async task for sending WhatsApp messages via Meta API.
    Used for mass notifications or high-volume messaging.
    """
    logger.info(f"Triggering async WhatsApp message for {recipient_id}")
    try:
        ok = whatsapp_provider.send_message(recipient_id, message)
        if not ok:
            logger.error(f"Failed to send async message to {recipient_id}")
            return False
        return True
    except Exception as e:
        logger.error(f"Celery task failed for {recipient_id}: {str(e)}")
        return False

@app.task(name="poll_care_notifications")
def poll_care_notifications():
    """
    Task to poll CARE backend for pending notifications.
    This can be scheduled to run every X minutes/seconds.
    """
    # 1. Fetch from CARE: care_client.get_pending_notifications()
    # 2. Loop & Send: whatsapp_provider.send_message()
    logger.info("Polling CARE backend for pending notifications...")
    pass
