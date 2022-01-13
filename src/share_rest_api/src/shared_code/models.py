from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UNKNOWN = "unknown"


class ShareNode(BaseModel):
    node_id: str
    url: str
    name: str
    tenant_id: str
    identity: str


class ShareNodeInformation(BaseModel):
    node_id: str
    url: str
    name: str
    tenant_id: str
    identity: str
    status: NodeStatus
    latest_registration: datetime


class Node(BaseModel):
    node_id: str
    tenant_id: str
    identity: str


class Dataset(BaseModel):
    resource_group_name: str
    storage_account_name: str
    container_name: str
    folder_path: str
    file_name: str


class ShareRequest(BaseModel):
    provider_node_id: str
    consumer_node_id: str
    dataset: Dataset


class ConsumeRequest(BaseModel):
    provider_node_id: str
    consumer_node_id: str
    invitation_id: str


class Error(BaseModel):
    code: int
    message: str
    source: str
    date: datetime


class Status(str, Enum):
    IN_PROGRESS = "InProgress"
    PENDING = "Pending"
    QUEUED = "Queued"
    FAILED = "Failed"
    SUCCEEDED = "Succeeded"


class StatusDetails(BaseModel):
    status: Status
    start: datetime
    end: datetime
    duration: int


class ShareResponse(BaseModel):
    invitation_id: str
    invitation_name: str
    provider_node_id: str
    consumer_node_id: str
    dataset: Dataset
    status: StatusDetails
    error: Error


class ConsumeResponse(BaseModel):
    invitation_id: str
    provider_node_id: str
    consumer_node_id: str
    dataset: Dataset
    status: StatusDetails
    error: Error
