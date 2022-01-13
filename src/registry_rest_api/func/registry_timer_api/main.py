# coding: utf-8
import datetime
import logging

import azure.functions as func

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


def main(registrytimer: func.TimerRequest) -> None:
    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    if registrytimer.past_due:
        logging.info("The timer is past due!")

    logging.info("Python timer trigger function ran at %s", utc_timestamp)
    registry_service = get_registry_service()
    # Check logging on startup
    # get_log_service().log_debug("debug")
    # get_log_service().log_warning("warning")
    # get_log_service().log_information("info")
    # get_log_service().log_error("error")
    get_log_service().log_information("Calling registry_service.update_node_status()")
    """Update the node status for each active node"""
    registry_service.update_node_status()
