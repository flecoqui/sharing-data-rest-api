import json
import os
from datetime import datetime
from typing import Any

import requests
from fastapi import HTTPException

from shared_code.configuration_service import ConfigurationService
from shared_code.datashare_service import DatashareService
from shared_code.log_service import LogService
from shared_code.models import (
    ConsumeResponse,
    Error,
    Node,
    ShareNode,
    ShareRequest,
    ShareResponse,
)


def get_log_service() -> LogService:
    """Getting a single instance of the LogService"""
    return LogService()


def get_configuration_service() -> ConfigurationService:
    """Getting a single instance of the ConfigurationService"""
    return ConfigurationService()


def get_datashare_service() -> DatashareService:
    """Getting a single instance of the DatashareService"""
    return DatashareService(
        subscription_id=get_configuration_service().get_subscription_id(),
        tenant_id=get_configuration_service().get_tenant_id(),
        datashare_resource_group_name=get_configuration_service().get_datashare_resource_group_name(),
        datashare_account_name=get_configuration_service().get_datashare_account_name(),
    )


class ShareService:
    """Class used to implement the datashare service"""

    def set_env_value(self, variable: str, value: str) -> str:
        """set environment variable value (string type)"""
        if not os.environ.get(variable):
            os.environ.setdefault(variable, value)
        else:
            os.environ[variable] = value
        return value

    def get_env_value(self, variable: str, default_value: str) -> str:
        """get environment variable value (string type)"""
        if not os.environ.get(variable):
            os.environ.setdefault(variable, default_value)
            return default_value
        else:
            return os.environ[variable]

    def serialize(self, o):
        """serialize object"""
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
        """store list in environment variable (string)"""
        o = self.serialize(list)
        self.set_env_value("SHARE_NODE_LIST", json.dumps(o))

    def raise_http_exception(self, code: int, message: str, detail: str):
        """raise HTTP exception"""
        if not detail:
            get_log_service().log_error(
                f"HTTP EXCEPTION code: {code} message: {message}"
            )
        else:
            get_log_service().log_error(
                f"HTTP EXCEPTION code: {code} message: {message} detail: {detail}"
            )
        error = Error(
            code=code, message=message, source="shareservice", date=datetime.utcnow()
        )
        raise HTTPException(
            status_code=code, detail=json.dumps(self.serialize(error.dict()))
        )

    def register_share_node(self) -> bool:
        """
        Call registry service to register the current node
        with the following parameters:
            node_id
            node name
            node url
            node tenant_id
            node identity
        """
        try:
            list = get_configuration_service().get_registry_list()
            for url in list:
                register_url = f"{url}/register"
                headers = {
                    "Content-Type": "application/json",
                }

                # Register current node if node_id is present
                if get_configuration_service().get_node_id() != "":
                    node = ShareNode(
                        node_id=get_configuration_service().get_node_id(),
                        url=get_configuration_service().get_node_url(),
                        name=get_configuration_service().get_node_name(),
                        tenant_id=get_configuration_service().get_tenant_id(),
                        identity=get_configuration_service().get_node_identity(),
                    )
                    register_response = requests.post(
                        url=register_url,
                        json=node.dict(),
                        headers=headers,
                    )
                    register_response.raise_for_status()
                    node: ShareNode = json.loads(register_response.text)

            return True
        except Exception as ex:
            get_log_service().log_error(f"EXCEPTION in register_share_node: {ex}")
            return False

    def share(self, share: ShareRequest) -> ShareResponse:
        """
        Implement the share method
        input ShareRequest
        return ShareResponse
        """
        try:
            list = get_configuration_service().get_registry_list()
            for url in list:
                node_url = f"{url}/nodes/{share.consumer_node_id}"
                headers = {
                    "Content-Type": "application/json",
                }
                node_response = requests.get(
                    url=node_url,
                    headers=headers,
                )
                node_response.raise_for_status()
                node: Node = json.loads(node_response.text)
                tenant_id = node["tenant_id"]
                identity = node["identity"]
                # Trigger the sharing process
                share_response = get_datashare_service().share(
                    provider_node_id=share.provider_node_id,
                    consumer_node_id=share.consumer_node_id,
                    tenant_id=tenant_id,
                    identity=identity,
                    datashare_storage_resource_group_name=share.dataset.resource_group_name,
                    datashare_storage_account_name=share.dataset.storage_account_name,
                    datashare_storage_container_name=share.dataset.container_name,
                    datashare_storage_folder_path=share.dataset.folder_path,
                    datashare_storage_file_name=share.dataset.file_name,
                )
                return share_response
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500,
                "Internal server error",
                f"Exception in 'share' method: {ex}",
            )

    def share_status(
        self,
        provider_node_id: str,
        consumer_node_id: str,
        datashare_storage_resource_group_name: str,
        datashare_storage_account_name: str,
        datashare_storage_container_name: str,
        datashare_storage_folder_path: str,
        datashare_storage_file_name: str,
    ) -> ShareResponse:
        """
        Implement the share_status method
        input:
        provider_node_id: the node_id of the node which is launching the share
        consumer_node_id: the node_id of the node which will consume the
            dataset
        datashare_storage_resource_group_name: the resource group of the
            storage account where the source dataset is stored,
        datashare_storage_account_name: the storage account where the source
            dataset is stored,
        datashare_storage_container_name: the storage container where the
            source dataset is stored,
        datashare_storage_folder_path: the folder path where the source
            dataset is stored,
        datashare_storage_file_name: the file name where the source dataset
            is stored,

        return ShareResponse
        """
        try:
            list = get_configuration_service().get_registry_list()
            for url in list:
                node_url = f"{url}/nodes/{consumer_node_id}"
                headers = {
                    "Content-Type": "application/json",
                }
                node_response = requests.get(
                    url=node_url,
                    headers=headers,
                )
                node_response.raise_for_status()
                node: Node = json.loads(node_response.text)
                tenant_id = node["tenant_id"]
                identity = node["identity"]
                # Get sharing process status
                share_response = get_datashare_service().share_status(
                    provider_node_id=provider_node_id,
                    consumer_node_id=consumer_node_id,
                    tenant_id=tenant_id,
                    identity=identity,
                    datashare_storage_resource_group_name=datashare_storage_resource_group_name,
                    datashare_storage_account_name=datashare_storage_account_name,
                    datashare_storage_container_name=datashare_storage_container_name,
                    datashare_storage_folder_path=datashare_storage_folder_path,
                    datashare_storage_file_name=datashare_storage_file_name,
                )
                return share_response
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500,
                "Internal server error",
                f"Exception in 'share' method: {ex}",
            )

    def consume(
        self, provider_node_id: str, consumer_node_id: str, invitation_id: str
    ) -> ConsumeResponse:
        """
        Implement the share_status method
        input:
        provider_node_id: the node_id of the node which is launching the share
        consumer_node_id: the node_id of the node which will consume the
            dataset
        invitation_id: invitation_id used to consume the dataset

        return ConsumeResponse
        """
        try:
            resource_group_name = (
                get_configuration_service().get_datashare_storage_resource_group_name()
            )
            storage_account_name = (
                get_configuration_service().get_datashare_storage_account_name()
            )
            container_name = (
                get_configuration_service().get_datashare_storage_consume_container_name()
            )
            folder_path = (
                get_configuration_service()
                .get_datashare_storage_consume_folder_format()
                .replace("{date}", datetime.utcnow().strftime("%Y-%m-%d"))
                .replace("{time}", datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S"))
                .replace("{node_id}", provider_node_id)
                .replace("{invitation_id}", invitation_id)
            )
            file_name = (
                get_configuration_service()
                .get_datashare_storage_consume_file_name_format()
                .replace("{date}", datetime.utcnow().strftime("%Y-%m-%d"))
                .replace("{time}", datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S"))
                .replace("{node_id}", provider_node_id)
                .replace("{invitation_id}", invitation_id)
            )
            consume_response = get_datashare_service().consume(
                provider_node_id=provider_node_id,
                consumer_node_id=consumer_node_id,
                invitation_id=invitation_id,
                datashare_storage_resource_group_name=resource_group_name,
                datashare_storage_account_name=storage_account_name,
                datashare_storage_container_name=container_name,
                datashare_storage_folder_path=folder_path,
                datashare_storage_file_name=file_name,
            )
            return consume_response
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500,
                "Internal server error",
                f"Exception in 'consume' method: {ex}",
            )

    def get_shareconsume(
        self, provider_node_id: str, consumer_node_id: str, invitation_id: str
    ):
        """
        Implement the get_shareconsume method
        input:
        provider_node_id: the node_id of the node which is launching the share
        consumer_node_id: the node_id of the node which will consume the
            dataset
        invitation_id: invitation_id used to consume the dataset

        return ConsumeResponse
        """
        try:
            list = get_configuration_service().get_registry_list()
            for url in list:
                node_url = f"{url}/shareconsume"
                headers = {
                    "Content-Type": "application/json",
                }
                params = dict()
                params["provider_node_id"] = provider_node_id
                params["consumer_node_id"] = consumer_node_id
                params["invitation_id"] = invitation_id
                consumer_node_response = requests.get(
                    url=node_url, headers=headers, params=params
                )
                consumer_node_response.raise_for_status()
                consumeresponse: ConsumeResponse = json.loads(
                    consumer_node_response.text
                )
                return consumeresponse
        except HTTPException as e:
            self.raise_http_exception(e.status_code, e.detail, "")
        except Exception as ex:
            self.raise_http_exception(
                500,
                "Internal server error",
                f"Exception in 'get_shareconsume' method: {ex}",
            )
