import json
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.app import app as application
from src.configuration_service import ConfigurationService
from src.datashare_service import DatashareService
from src.share_service import ShareService

os.environ["AZURE_TENANT_ID"] = "02020202-0000-0000-0000-020202020202"
os.environ["AZURE_SUBSCRIPTION_ID"] = "03030303-0000-0000-0000-030303030303"


os.environ["APP_VERSION"] = "1.0.0.0"
os.environ["PORT_HTTP"] = "5000"
os.environ["WEBSITES_HTTP"] = "5000"
os.environ["REFRESH_PERIOD"] = "60"
os.environ["REGISTRY_URL_LIST"] = "http://127.0.0.1/"
os.environ["NODE_ID"] = "testa"
os.environ["NODE_NAME"] = "testa"
os.environ["NODE_URL"] = "http://127.0.0.1/"
os.environ["NODE_IDENTITY"] = "00000000-0000-0000-000000000000"
os.environ["DATASHARE_ACCOUNT_NAME"] = "testds"
os.environ["DATASHARE_RESOURCE_GROUP_NAME"] = "testrg"
os.environ["DATASHARE_STORAGE_RESOURCE_GROUP_NAME"] = "testrg"
os.environ["DATASHARE_STORAGE_ACCOUNT_NAME"] = "testsa"
os.environ["DATASHARE_STORAGE_CONSUME_CONTAINER_NAME"] = "testconsumecontainer"
os.environ["DATASHARE_STORAGE_CONSUME_FILE_NAME_FORMAT"] = "testfile.csv"
os.environ[
    "DATASHARE_STORAGE_CONSUME_FOLDER_FORMAT"
] = "consume/{node_id}/dataset-{date}"
os.environ["DATASHARE_STORAGE_SHARE_CONTAINER_NAME"] = "testsharecontainer"
os.environ["DATASHARE_STORAGE_SHARE_FILE_NAME_FORMAT"] = "testfile.csv"
os.environ["DATASHARE_STORAGE_SHARE_FOLDER_FORMAT"] = "share/{node_id}/dataset-{date}"


@pytest.fixture
def app() -> FastAPI:
    application.dependency_overrides = {}
    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


def get_configuration_service() -> ConfigurationService:
    """Getting a single instance of the LogService"""
    return ConfigurationService()


@pytest.fixture(scope="function")
def share_service():
    return ShareService()


@pytest.fixture(scope="function")
def datashare_service():
    return DatashareService(
        subscription_id=get_configuration_service().get_subscription_id(),
        tenant_id=get_configuration_service().get_tenant_id(),
        datashare_resource_group_name=get_configuration_service().get_datashare_resource_group_name(),
        datashare_account_name=get_configuration_service().get_datashare_account_name(),
    )


class MinimalResponse(object):  # Not for production use
    def __init__(self, requests_resp=None, status_code=None, text=None):
        self.status_code = status_code or requests_resp.status_code
        self.text = text or requests_resp.text
        self._raw_resp = requests_resp

    def raise_for_status(self):
        if self._raw_resp is not None:  # Turns out `if requests.response` won't work
            # cause it would be True when 200<=status<400
            self._raw_resp.raise_for_status()

    def json(self):
        return json.loads(self.text)
