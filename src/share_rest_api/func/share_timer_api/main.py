# coding: utf-8
import datetime
import logging

import azure.functions as func

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


def main(sharetimer: func.TimerRequest) -> None:
    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    if sharetimer.past_due:
        logging.info("The timer is past due!")

    logging.info("Python timer trigger function ran at %s", utc_timestamp)
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
