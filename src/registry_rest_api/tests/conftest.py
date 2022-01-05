import json
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.app import app as application  # pragma: no cover # NOQA: E402
from src.configuration_service import ConfigurationService
from src.registry_service import RegistryService

os.environ["AZURE_TENANT_ID"] = "02020202-0000-0000-0000-020202020202"
os.environ["AZURE_SUBSCRIPTION_ID"] = "03030303-0000-0000-0000-030303030303"


os.environ["APP_VERSION"] = "1.0.0.0"
os.environ["PORT_HTTP"] = "5000"
os.environ["WEBSITES_HTTP"] = "5000"
os.environ["REFRESH_PERIOD"] = "60"
os.environ["SHARE_NODE_LIST"] = "[]"


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
def registry_service():
    return RegistryService()


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
