import json
from datetime import datetime
from typing import Any, List

import requests
from fastapi import HTTPException

from shared_code.configuration_service import ConfigurationService
from shared_code.log_service import LogService
from shared_code.models import (
    ConsumeResponse,
    Error,
    Node,
    NodeStatus,
    ShareNode,
    ShareNodeInformation,
)


def get_log_service() -> LogService:
    """Getting a single instance of the LogService"""
    return LogService()


def get_configuration_service() -> ConfigurationService:
    """Getting a single instance of the LogService"""
    return ConfigurationService()


class RegistryService:
    """Class used to implement the datashare service"""

    def serialize(self, o):
        if isinstance(o, dict):
            return {k: self.serialize(v) for k, v in o.items()}
        if isinstance(o, list):
            return [self.serialize(e) for e in o]
        if isinstance(o, bytes):
            return o.decode("utf-8")
        if isinstance(o, datetime):
            return o.isoformat()
        return o

    def set_memory_persistent_node_list(self, list: Any):
        o = self.serialize(list)
        get_configuration_service().set_env_value("SHARE_NODE_LIST", json.dumps(o))

    def raise_http_exception(self, code: int, message: str, detail: str):
        if not detail:
            get_log_service().log_error(
                f"HTTP EXCEPTION code: {code} message: {message}"
            )
        else:
            get_log_service().log_error(
                f"HTTP EXCEPTION code: {code}\
 message: {message} detail: {detail}"
            )
        error = Error(
            code=code, message=message, source="registryservice", date=datetime.utcnow()
        )
        raise HTTPException(
            status_code=code, detail=json.dumps(self.serialize(error.dict()))
        )

    def update_node_status(self) -> bool:
        try:
            list = get_configuration_service().get_share_node_list()
            updated = False
            for i in range(len(list)):
                latest = datetime.fromisoformat(list[i]["latest_registration"])
                if (
                    datetime.utcnow() - latest
                ).total_seconds() > get_configuration_service().get_refresh_period():
                    if list[i]["status"] != NodeStatus.OFFLINE:
                        list[i]["status"] = NodeStatus.OFFLINE
                        updated = True
                else:
                    if list[i]["status"] != NodeStatus.ONLINE:
                        list[i]["status"] = NodeStatus.ONLINE
                        updated = True
            if updated is True:
                self.set_memory_persistent_node_list(list)
            return True
        except Exception as ex:
            get_log_service().log_error(f"EXCEPTION in updatenode_status: {ex}")
            return False

    def register(self, node: ShareNode) -> ShareNode:
        try:
            list = get_configuration_service().get_share_node_list()
            found = False

            nodeinfo = ShareNodeInformation(
                node_id=node.node_id,
                name=node.name,
                url=node.url,
                tenant_id=node.tenant_id,
                identity=node.identity,
                latest_registration=datetime.utcnow(),
                status=NodeStatus.ONLINE,
            )
            for i in range(len(list)):
                if list[i]["node_id"] == node.node_id and list[i]["url"] == node.url:
                    list[i] = nodeinfo.dict()
                    found = True
                    break
            if found is False:
                list.append(nodeinfo.dict())
            self.set_memory_persistent_node_list(list)
            return node
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500, "Internal server error", f"Exception in 'register' method: {ex}"
            )

    def nodes(self) -> List[Node]:
        try:
            list = get_configuration_service().get_share_node_list()
            returned_list = []
            for i in range(len(list)):
                if list[i]["status"] == NodeStatus.ONLINE:
                    node = Node(
                        node_id=list[i]["node_id"],
                        tenant_id=list[i]["tenant_id"],
                        identity=list[i]["identity"],
                    )
                    returned_list.append(node)
            return returned_list
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500, "Internal server error", f"Exception in 'nodes' method: {ex}"
            )

    def node(self, node_id: str):
        try:
            list = get_configuration_service().get_share_node_list()
            for i in range(len(list)):
                if list[i]["node_id"] == node_id:
                    if list[i]["status"] == NodeStatus.ONLINE:
                        node = Node(
                            node_id=list[i]["node_id"],
                            tenant_id=list[i]["tenant_id"],
                            identity=list[i]["identity"],
                        )
                        return node
            raise HTTPException(
                status_code=404, detail=f"Node '{node_id}' does not exists."
            )
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500, "Internal server error", f"Exception in 'node' method: {ex}"
            )

    def shareconsume(
        self, provider_node_id: str, consumer_node_id: str, invitation_id: str
    ):
        try:
            list = get_configuration_service().get_share_node_list()
            for i in range(len(list)):
                if list[i]["node_id"] == consumer_node_id:
                    if list[i]["status"] == NodeStatus.ONLINE:
                        url = list[i]["url"]
                        consumer_node_url = f"{url}/consumeshare"
                        headers = {
                            "Content-Type": "application/json",
                        }
                        params = dict()
                        params["provider_node_id"] = provider_node_id
                        params["consumer_node_id"] = consumer_node_id
                        params["invitation_id"] = invitation_id
                        consumer_node_response = requests.get(
                            url=consumer_node_url,
                            params=params,
                            headers=headers,
                        )
                        consumer_node_response.raise_for_status()
                        consumeresponse: ConsumeResponse = json.loads(
                            consumer_node_response.text
                        )
                        return consumeresponse
            raise HTTPException(
                status_code=404,
                detail=f"Consumer Node '{consumer_node_id}' does not exists.",
            )
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500,
                "Internal server error",
                f"Exception in 'shareconsume' method: {ex}",
            )
