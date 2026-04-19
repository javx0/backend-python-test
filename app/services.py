import logging
import os

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from models import RequestItem, RequestStatus

logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "http://localhost:3001")
API_KEY = os.getenv("API_KEY", "test-dev-2026")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def call_notify(request_item: RequestItem, request_id: str) -> None:
    logger.info(f"Sending notification for request {request_id} to {request_item.to} via {request_item.type}")
    provider_url = f"{PROVIDER_BASE_URL}/v1/notify"
    headers = {"X-API-Key": API_KEY}
    params = {"priority": "normal", "trace_id": request_id}
    payload = {
        "to": request_item.to,
        "message": request_item.message,
        "type": str(request_item.type),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            provider_url,
            json=payload,
            headers=headers,
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        logger.info(f"Notification sent successfully for request {request_id}")


async def process_request_async(request_item: RequestItem, request_id: str):
    """Background task para procesar la solicitud de notificación"""
    logger.info(f"Starting background processing for request {request_id}")

    try:
        await call_notify(request_item, request_id)
        request_item.status = RequestStatus.sent
        logger.info(f"Request {request_id} processed successfully")
    except Exception as e:
        request_item.status = RequestStatus.failed
        logger.error(f"Background processing failed for request {request_id}: {str(e)}")