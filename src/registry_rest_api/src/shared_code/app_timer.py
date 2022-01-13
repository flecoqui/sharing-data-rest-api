from fastapi_utils.tasks import repeat_every

from shared_code.app import app
from shared_code.configuration_service import ConfigurationService
from shared_code.log_service import LogService
from shared_code.registry_service import RegistryService


def get_log_service() -> LogService:
    """Getting a single instance of the LogService"""
    return LogService()


def get_registry_service() -> RegistryService:
    """Getting a single instance of the RegistryService"""
    return RegistryService()


def get_configuration_service() -> ConfigurationService:
    """Getting a single instance of the LogService"""
    return ConfigurationService()


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
