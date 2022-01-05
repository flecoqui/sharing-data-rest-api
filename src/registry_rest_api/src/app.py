import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, FastAPI
from fastapi.params import Depends
from fastapi_utils.tasks import repeat_every
from src.configuration_service import ConfigurationService
from src.log_service import LogService
from src.models import ConsumeResponse, Node, ShareNode
from src.registry_service import RegistryService
from starlette.requests import Request

router = APIRouter(prefix="")

app_version = os.getenv("APP_VERSION", "1.0.0.1")

app = FastAPI(
    title="registry REST API",
    description="Sample Registry REST API.",
    version=app_version,
)


def get_log_service() -> LogService:
    """Getting a single instance of the LogService"""
    return LogService()


def get_registry_service() -> RegistryService:
    """Getting a single instance of the RegistryService"""
    return RegistryService()


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
    """Get Version using GET /version"""
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
    """Get UTC Time using GET /time"""
    now = datetime.utcnow()
    return now.strftime("%Y/%m/%d-%H:%M:%S")


@router.post(
    "/register",
    responses={
        200: {"description": "ShareNode registered"},
    },
    summary="Register sharing node",
    response_model=ShareNode,
)
def register(
    request: Request,
    body: ShareNode = Body(...),
    registry_service: RegistryService = Depends(get_registry_service),
) -> ShareNode:
    """Register Node using POST /register BODY: ShareNode"""
    get_log_service().log_information(f"HTTP REQUEST POST /register BODY: {body}")
    response = registry_service.register(body)
    get_log_service().log_information(
        f"HTTP REQUEST POST /register BODY: {body} RESPONSE: {response}"
    )
    return response


@router.get(
    "/nodes",
    responses={
        200: {"description": "return List of nodes"},
    },
    summary="Get list of nodes",
    response_model=List[Node],
)
def nodes(
    request: Request,
    registry_service: RegistryService = Depends(get_registry_service),
):
    """Get list of nodes using GET /nodes RESPONSE BODY: List of Node"""
    get_log_service().log_information("HTTP REQUEST GET /nodes")
    list = registry_service.nodes()
    get_log_service().log_information(f"HTTP REQUEST GET /nodes RESPONSE: {list}")
    return list


@router.get(
    "/nodes/{node_id}",
    responses={
        200: {"description": "return node"},
        404: {"description": "The node with id {node_id} does not exist."},
    },
    summary="Get node",
    response_model=Node,
)
def node(
    request: Request,
    node_id: str,
    registry_service: RegistryService = Depends(get_registry_service),
) -> Node:
    """Get node using GET /nodes/{node_id} RESPONSE BODY: Node"""
    get_log_service().log_information(f"HTTP REQUEST GET /nodes/{node_id}")
    node = registry_service.node(node_id)
    get_log_service().log_information(
        f"HTTP REQUEST GET /nodes/{node_id} RESPONSE: {node}"
    )
    return node


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
def shareconsume(
    request: Request,
    provider_node_id: str,
    consumer_node_id: str,
    invitation_id: str,
    registry_service: RegistryService = Depends(get_registry_service),
) -> ConsumeResponse:
    """Get shareconsume using GET /shareconsume RESPONSE BODY: ConsumeResponse"""
    get_log_service().log_information(
        f"HTTP REQUEST GET /shareconsume PARAMS: {provider_node_id}\
 {consumer_node_id} {invitation_id}"
    )
    consumeresponse = registry_service.shareconsume(
        provider_node_id, consumer_node_id, invitation_id
    )
    get_log_service().log_information(
        f"HTTP REQUEST GET /shareconsume PARAMS: {provider_node_id}\
 {consumer_node_id} {invitation_id} RESPONSE: {consumeresponse}"
    )
    return consumeresponse


# Periodic task used to managed place order workflow
@app.on_event("startup")
@repeat_every(seconds=get_configuration_service().get_refresh_period())
def periodic_task() -> None:
    registry_service = get_registry_service()
    # Check logging on startup
    # get_log_service().log_debug("debug")
    # get_log_service().log_warning("warning")
    # get_log_service().log_information("info")
    # get_log_service().log_error("error")
    get_log_service().log_information("Calling registry_service.update_node_status()")
    """Update the node status for each active node"""
    registry_service.update_node_status()


app.include_router(router, prefix="")
