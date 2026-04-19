import logging
import os
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, status

from models import NotificationType, RequestCreate, RequestItem, RequestResponse, RequestStatus, RequestStatusResponse
from services import process_request_async

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar logging
debug_logging = os.getenv('DEBUG_LOGGING', 'false').lower() == 'true'
log_level = logging.DEBUG if debug_logging else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service (Technical Test)")

requests_store: dict[str, RequestItem] = {}

# 1 - Crear una solicitud de notificación
@app.post("/v1/requests", status_code=status.HTTP_201_CREATED, response_model=RequestResponse)
def create_request(request: RequestCreate):
    request_id = str(uuid4())
    request_item = RequestItem(
        id=request_id,
        status=RequestStatus.queued,
        to=request.to,
        message=request.message,
        type=request.type,
    )
    requests_store[request_id] = request_item
    logger.info(f"Created request {request_id} for {request.to} via {request.type}")
    return {"id": request_id}

# 2 - Procesar una solicitud de notificación
@app.post("/v1/requests/{request_id}/process", status_code=status.HTTP_202_ACCEPTED)
def process_request(request_id: str, background_tasks: BackgroundTasks):
    logger.info(f"Processing request {request_id}")
    request_item = requests_store.get(request_id)
    if not request_item:
        logger.warning(f"Request {request_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if request_item.status == RequestStatus.processing:
        logger.warning(f"Request {request_id} already processing")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request already processing")

    if request_item.status != RequestStatus.queued:
        logger.warning(f"Request {request_id} not in queued state (current: {request_item.status})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request not in queued state")

    request_item.status = RequestStatus.processing
    logger.info(f"Request {request_id} status changed to processing")
    background_tasks.add_task(process_request_async, request_item, request_id)
    return {"message": "Request processing started"}

# 3 - Consultar el estado de una solicitud
@app.get("/v1/requests/{request_id}", response_model=RequestStatusResponse)
def get_request(request_id: str):
    if request_id not in requests_store:
        logger.warning(f"Status query for non-existent request {request_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    request_item = requests_store[request_id]
    logger.info(f"Status queried for request {request_id}: {request_item.status.value}")
    return {"id": request_id, "status": request_item.status}