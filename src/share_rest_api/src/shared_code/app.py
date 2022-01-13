import os
from datetime import datetime

from fastapi import APIRouter, Body, FastAPI
from fastapi.params import Depends
from starlette.requests import Request

from shared_code.configuration_service import ConfigurationService
from shared_code.log_service import LogService
from shared_code.models import ConsumeResponse, ShareRequest, ShareResponse
from shared_code.share_service import ShareService

router = APIRouter(prefix="")

app_version = os.getenv("APP_VERSION", "1.0.0.1")

app = FastAPI(
    title="share REST API",
    description="Sample share REST API.",
    version=app_version,
)


def get_log_service() -> LogService:
    """Getting a single instance of the LogService"""
    return LogService()


def get_share_service() -> ShareService:
    """Getting a single instance of the ShareService"""
    return ShareService()


def get_configuration_service() -> ConfigurationService:
    """Getting a single instance of the LogService"""
    return ConfigurationService()


@router.get(
    "/version",
    responses={
        200: {"description": "Get version."},
    },
    summary="Returns the current version.",
)
def get_version(
    request: Request,
) -> str:
    """Get version using GET /version"""
    app_version = os.getenv("APP_VERSION", "1.0.0.1")
    return app_version


@router.get(
    "/time",
    responses={
        200: {"description": "Get current time."},
    },
    summary="Returns the current time.",
)
def get_time(
    request: Request,
) -> str:
    """Get utc time using GET /time"""
    now = datetime.utcnow()
    return now.strftime("%Y/%m/%d-%H:%M:%S")


@router.post(
    "/share",
    responses={
        200: {
            "description": "return shareresponse  (ShareResponse)\
 status with params: {ShareRequest}"
        },
        404: {
            "description": "The node with id {consumer_node_id}\
 does not exist."
        },
    },
    summary="Trigger ShareConsume process with Body: {ShareRequest}",
    response_model=ShareResponse,
)
def share(
    request: Request,
    body: ShareRequest = Body(...),
    share_service: ShareService = Depends(get_share_service),
) -> ShareResponse:
    """Trigger sharing process using POST /share BODY: ShareRequest \
RESPONSE: ShareResponse"""
    get_log_service().log_information(f"HTTP REQUEST POST /share BODY: {body}")
    shareresponse = share_service.share(body)
    get_log_service().log_information(
        f"HTTP REQUEST POST /share BODY: {body} RESPONSE: {shareresponse}"
    )
    return shareresponse


@router.get(
    "/share",
    responses={
        200: {
            "description": "return shareresponse  (ShareResponse)\
 status with params"
        },
        404: {
            "description": "The share \
 does not exist."
        },
    },
    summary="Get Share status using params",
    response_model=ShareResponse,
)
def share_status(
    request: Request,
    provider_node_id: str,
    consumer_node_id: str,
    datashare_storage_resource_group_name: str,
    datashare_storage_account_name: str,
    datashare_storage_container_name: str,
    datashare_storage_folder_path: str,
    datashare_storage_file_name: str,
    share_service: ShareService = Depends(get_share_service),
) -> ShareResponse:
    """Get share status using GET /share RESPONSE ShareResponse"""
    get_log_service().log_information(
        f"HTTP REQUEST GET /share PARAMS: {provider_node_id}\
 {consumer_node_id} ..."
    )
    shareresponse = share_service.share_status(
        provider_node_id=provider_node_id,
        consumer_node_id=consumer_node_id,
        datashare_storage_resource_group_name=datashare_storage_resource_group_name,
        datashare_storage_account_name=datashare_storage_account_name,
        datashare_storage_container_name=datashare_storage_container_name,
        datashare_storage_folder_path=datashare_storage_folder_path,
        datashare_storage_file_name=datashare_storage_file_name,
    )
    get_log_service().log_information(
        f"HTTP REQUEST GET /share PARAMS: {provider_node_id}\
 {consumer_node_id} ... RESPONSE: {shareresponse}"
    )
    return shareresponse


@router.get(
    "/consume",
    responses={
        200: {
            "description": "return consume (ConsumeResponse)\
 status with params: {provider_node_id} {consumer_node_id} {invitation_id}"
        },
        404: {
            "description": "The node with id {consumer_node_id}\
 does not exist."
        },
    },
    summary="Get Consume status in ConsumeResponse with params:\
 {provider_node_id} {consumer_node_id} {invitation_id}",
    response_model=ConsumeResponse,
)
def consume(
    request: Request,
    provider_node_id: str,
    consumer_node_id: str,
    invitation_id: str,
    share_service: ShareService = Depends(get_share_service),
) -> ConsumeResponse:
    """Trigger data consumption using GET /consume RESPONSE ConsumeResponse"""
    get_log_service().log_information(
        f"HTTP REQUEST GET /consume PARAMS:\
 {provider_node_id} {consumer_node_id} {invitation_id}"
    )
    consumeresponse = share_service.consume(
        provider_node_id, consumer_node_id, invitation_id
    )
    get_log_service().log_information(
        f"HTTP REQUEST GET /consume PARAMS:\
 {provider_node_id} {consumer_node_id} {invitation_id}\
 RESPONSE: {consumeresponse}"
    )
    return consumeresponse


@router.post(
    "/shareconsume",
    responses={
        200: {
            "description": "return shareresponse  (ShareResponse)\
 status with Body: {ShareRequest}"
        },
        404: {
            "description": "The node with id\
 {consumer_node_id} does not exist."
        },
    },
    summary="Trigger ShareConsume process with Body: {ShareRequest}",
    response_model=ShareResponse,
)
def shareconsume(
    request: Request,
    body: ShareRequest = Body(...),
    share_service: ShareService = Depends(get_share_service),
) -> ShareResponse:
    """Trigger data sharing using POST /shareconsume RESPONSE ShareResponse"""
    get_log_service().log_information(
        f"HTTP REQUEST POST\
 /shareconsume BODY: {body}"
    )
    shareresponse = share_service.share(body)
    get_log_service().log_information(
        f"HTTP REQUEST GET /shareconsume BODY: {body}\
 RESPONSE: {shareresponse}"
    )
    return shareresponse


@router.get(
    "/shareconsume",
    responses={
        200: {
            "description": "return shareconsume (ConsumeResponse)\
 status with params: {provider_node_id} {consumer_node_id} {invitation_id}"
        },
        404: {
            "description": "The node with id {consumer_node_id}\
 does not exist."
        },
    },
    summary="Get ShareConsumer status in ConsumeResponse with params:\
 {provider_node_id} {consumer_node_id} {invitation_id}",
    response_model=ConsumeResponse,
)
def get_shareconsume(
    request: Request,
    provider_node_id: str,
    consumer_node_id: str,
    invitation_id: str,
    share_service: ShareService = Depends(get_share_service),
) -> ConsumeResponse:
    """Get data share status using GET /shareconsume \
RESPONSE ConsumeResponse"""
    get_log_service().log_information(
        f"HTTP REQUEST GET /shareconsume PARAMS: {provider_node_id}\
 {consumer_node_id} {invitation_id}"
    )
    consumeresponse = share_service.get_shareconsume(
        provider_node_id, consumer_node_id, invitation_id
    )
    get_log_service().log_information(
        f"HTTP REQUEST GET /shareconsume PARAMS: {provider_node_id}\
 {consumer_node_id} {invitation_id} RESPONSE: {consumeresponse}"
    )
    return consumeresponse


@router.get(
    "/consumeshare",
    responses={
        200: {
            "description": "return consumeshare (ConsumeResponse)\
 status with params: {provider_node_id} {consumer_node_id} {invitation_id}"
        },
        404: {
            "description": "The node with id {consumer_node_id}\
 does not exist."
        },
    },
    summary="Get ConsumeShare status in ConsumeResponse with\
 params: {provider_node_id} {consumer_node_id} {invitation_id}",
    response_model=ConsumeResponse,
)
def consumeshare(
    request: Request,
    provider_node_id: str,
    consumer_node_id: str,
    invitation_id: str,
    share_service: ShareService = Depends(get_share_service),
) -> ConsumeResponse:
    """Get data share status using GET /consumeshare RESPONSE\
 ConsumeResponse"""
    get_log_service().log_information(
        f"HTTP REQUEST GET /consumeshare PARAMS: {provider_node_id}\
 {consumer_node_id} {invitation_id}"
    )
    consumeresponse = share_service.consume(
        provider_node_id, consumer_node_id, invitation_id
    )
    get_log_service().log_information(
        f"HTTP REQUEST GET /consumeshare PARAMS: {provider_node_id}\
 {consumer_node_id} {invitation_id} RESPONSE: {consumeresponse}"
    )
    return consumeresponse


app.include_router(router, prefix="")
