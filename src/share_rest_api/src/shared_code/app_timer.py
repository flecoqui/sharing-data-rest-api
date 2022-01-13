from fastapi_utils.tasks import repeat_every

from shared_code.app import app
from shared_code.configuration_service import ConfigurationService
from shared_code.log_service import LogService
from shared_code.share_service import ShareService


def get_log_service() -> LogService:
    """Getting a single instance of the LogService"""
    return LogService()


def get_share_service() -> ShareService:
    """Getting a single instance of the ShareService"""
    return ShareService()


def get_configuration_service() -> ConfigurationService:
    """Getting a single instance of the LogService"""
    return ConfigurationService()


# Periodic task used to managed place order workflow
@app.on_event("startup")
@repeat_every(seconds=get_configuration_service().get_refresh_period())
def periodic_task() -> None:
    share_service = get_share_service()
    get_log_service().log_information("Calling share_service.register_share_node()")
    result = share_service.register_share_node()
    if result is True:
        get_log_service().log_information(
            "Calling share_service.register_share_node() share_rest_api\
 registration successful"
        )
    else:
        get_log_service().log_information(
            "Calling share_service.register_share_node() share_rest_api\
 registration failed"
        )
