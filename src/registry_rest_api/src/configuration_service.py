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
    """{ "name":"SHARE_NODE_LIST", "value":"[]"},"""

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

    def get_share_node_list(self) -> Any:
        return json.loads(self.get_env_value("SHARE_NODE_LIST", "[]"))

    def get_subscription_id(self) -> str:
        return self.get_env_value("AZURE_SUBSCRIPTION_ID", "")

    def get_tenant_id(self) -> str:
        return self.get_env_value("AZURE_TENANT_ID", "")
