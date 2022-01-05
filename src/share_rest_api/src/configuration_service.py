import json
import os
from typing import Any


class ConfigurationService:
    """Class used to read and write application service configuration"""

    """ Below the existing configuration """
    """{ "name":"APP_VERSION", "value":"${APP_VERSION}"}, """
    """{ "name":"PORT_HTTP", "value":"${APP_PORT}"},"""
    """{ "name":"WEBSITES_PORT", "value":"${APP_PORT}"}, """
    """{ "name":"REFRESH_PERIOD", "value":"60"},"""
    """{ "name":"REGISTRY_URL_LIST", "value":"[\"${REGISTRY_URL}\"]"},"""
    """{ "name":"NODE_ID", "value":"${APP_PREFIX}"},"""
    """{ "name":"NODE_NAME", "value":"${APP_PREFIX}"},"""
    """{ "name":"NODE_URL", "value":"https://${WEB_APP_SERVER}"},"""
    """{ "name":"NODE_IDENTITY", "value":"${WEB_APP_OBJECT_ID}"},"""
    """{ "name":"DATASHARE_ACCOUNT_NAME", "value":"${DATASHARE_ACCOUNT_NAME}"},"""
    """{ "name":"DATASHARE_RESOURCE_GROUP_NAME", "value":"${RESOURCE_GROUP}"},"""
    """{ "name":"DATASHARE_STORAGE_RESOURCE_GROUP_NAME", "value":"${RESOURCE_GROUP}"},"""
    """{ "name":"DATASHARE_STORAGE_ACCOUNT_NAME", "value":"${STORAGE_ACCOUNT_NAME}"},"""
    """{ "name":"DATASHARE_STORAGE_CONSUME_CONTAINER_NAME", "value":"${CONSUME_CONTAINER}"},"""
    """{ "name":"DATASHARE_STORAGE_CONSUME_FILE_NAME_FORMAT", "value":"output-00001.csv"},"""
    """{ "name":"DATASHARE_STORAGE_CONSUME_FOLDER_FORMAT", "value":"consume/{node_id}/dataset-{date}"},"""
    """{ "name":"DATASHARE_STORAGE_SHARE_CONTAINER_NAME", "value":"${SHARE_CONTAINER}"},"""
    """{ "name":"DATASHARE_STORAGE_SHARE_FILE_NAME_FORMAT", "value":"input-00001.csv"},"""
    """{ "name":"DATASHARE_STORAGE_SHARE_FOLDER_FORMAT", "value":"share/{node_id}/dataset-{date}"},"""

    def set_env_value(self, variable: str, value: str) -> str:
        if not os.environ.get(variable):
            os.environ.setdefault(variable, value)
        else:
            os.environ[variable] = value
        return value

    def get_env_value(self, variable: str, default_value: str) -> str:
        if not os.environ.get(variable):
            os.environ.setdefault(variable, default_value)
            return default_value
        else:
            return os.environ[variable]

    def get_app_version(self) -> str:
        return self.get_env_value("APP_VERSION", "1.0.0.0")

    def get_http_port(self) -> int:
        return int(self.get_env_value("PORT_HTTP", "5000"))

    def get_websites_port(self) -> int:
        return int(self.get_env_value("WEBSITES_HTTP", "5000"))

    def get_refresh_period(self) -> int:
        return int(self.get_env_value("REFRESH_PERIOD", "120"))

    def get_registry_list(self) -> Any:
        # return json.loads(self.get_env_value("REGISTRY_URL_LIST", "[]"))
        return json.loads('["https://webappreghub0000.azurewebsites.net"]')

    def get_node_id(self) -> str:
        return self.get_env_value("NODE_ID", "node_a")

    def get_node_name(self) -> str:
        return self.get_env_value("NODE_NAME", "node_name_a")

    def get_node_url(self) -> str:
        return self.get_env_value("NODE_URL", "http://node_name_a")

    def get_node_identity(self) -> str:
        return self.get_env_value("NODE_IDENTITY", "")

    def get_datashare_account_name(self) -> str:
        return self.get_env_value("DATASHARE_ACCOUNT_NAME", "")

    def get_datashare_resource_group_name(self) -> str:
        return self.get_env_value("DATASHARE_RESOURCE_GROUP_NAME", "")

    def get_datashare_storage_resource_group_name(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_RESOURCE_GROUP_NAME", "")

    def get_datashare_storage_account_name(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_ACCOUNT_NAME", "")

    def get_datashare_storage_consume_container_name(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_CONSUME_CONTAINER_NAME", "")

    def get_datashare_storage_consume_file_name_format(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_CONSUME_FILE_NAME_FORMAT", "")

    def get_datashare_storage_consume_folder_format(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_CONSUME_FOLDER_FORMAT", "")

    def get_datashare_storage_share_container_name(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_SHARE_CONTAINER_NAME", "")

    def get_datashare_storage_share_file_name_format(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_SHARE_FILE_NAME_FORMAT", "")

    def get_datashare_storage_share_folder_format(self) -> str:
        return self.get_env_value("DATASHARE_STORAGE_SHARE_FOLDER_FORMAT", "")

    def get_subscription_id(self) -> str:
        return self.get_env_value("AZURE_SUBSCRIPTION_ID", "")

    def get_tenant_id(self) -> str:
        return self.get_env_value("AZURE_TENANT_ID", "")
