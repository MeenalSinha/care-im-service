import logging
from typing import List, Dict, Any
from app.clients.care_api import CareAPIClient

logger = logging.getLogger(__name__)

class PatientService:
    """
    Business Logic Layer for Patient Resources.
    Mediates between the Application (Dispatcher) and Infrastructure (API Client).
    """
    def __init__(self, api_client: CareAPIClient):
        self.api_client = api_client

    def get_medication_summary(self, token: str) -> str:
        """Fetch and format a human-readable medication summary."""
        try:
            meds = self.api_client.list_medications(token)
            if not meds:
                return "💊 You have no active Medications."
            
            summary = "💊 *Active Medications:*\n"
            for med in meds:
                name = med.get("medication", {}).get("display", "Unnamed")
                summary += f"• {name}\n"
            return summary
        except Exception as e:
            logger.error(f"Service Error - Get Meds: {str(e)}")
            return "❌ Unable to retrieve medication records."

    def get_encounter_summary(self, token: str) -> str:
        """Fetch and format clinical encounter history."""
        try:
            encounters = self.api_client.list_encounters(token)
            if not encounters:
                return "📊 No patient records found."
            
            summary = "📊 *Recent Encounters:*\n"
            for enc in encounters[:5]:
                date = enc.get("created_date", "Unknown Date")
                status = enc.get("status", "Unknown")
                summary += f"• {date}: {status.capitalize()}\n"
            return summary
        except Exception as e:
            logger.error(f"Service Error - Get Encounters: {str(e)}")
            return "❌ Error retrieving encounter history."
