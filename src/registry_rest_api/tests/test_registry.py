from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from src.models import ConsumeResponse, Dataset, Error, ShareNode, StatusDetails

from .conftest import MinimalResponse


def test_version(client: TestClient):
    registry_response = client.get(
        url="/version",
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    assert registry_response.status_code == 200


def test_time(client: TestClient):
    registry_response = client.get(
        url="/time",
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    assert registry_response.status_code == 200


def test_register_node(client: TestClient):
    node = ShareNode(
        node_id="testa",
        url="http://127.0.0.1/",
        name="testa",
        tenant_id="00000000-0000-0000-000000000000",
        identity="00000000-0000-0000-000000000000",
    )
    registry_response = client.post(
        url="/register",
        json=node.dict(),
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    assert registry_response.status_code == 200


def test_get_nodes(client: TestClient):
    registry_response = client.get(
        url="/nodes",
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    assert registry_response.status_code == 200


def test_get_node(client: TestClient):
    node_id = "testa"
    registry_response = client.get(
        url=f"/nodes/{node_id}",
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    assert registry_response.status_code == 200


def test_shareconsume(client: TestClient):
    with patch("requests.get") as mock_requests_get:
        node_id = "testa"
        invitation_id = "00000000-0000-0000-000000000000"

        dataset = Dataset(
            resource_group_name="testrg",
            storage_account_name="testsa",
            container_name="testc",
            folder_path="testfolder",
            file_name="testfile",
        )
        status = StatusDetails(
            status="Pending", start=datetime.utcnow(), end=datetime.utcnow(), duration=0
        )
        error = Error(
            code=0,
            message="No error",
            source="regsitry_rest_api",
            date=datetime.utcnow(),
        )

        cr = ConsumeResponse(
            invitation_id=invitation_id,
            provider_node_id=node_id,
            consumer_node_id=node_id,
            dataset=dataset,
            status=status,
            error=error,
        )
        mock_requests_get.return_value = MinimalResponse(
            status_code=200, text=cr.json()
        )

        params = dict()
        params["provider_node_id"] = node_id
        params["consumer_node_id"] = node_id
        params["invitation_id"] = invitation_id

        registry_response = client.get(
            url="/shareconsume",
            params=params,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        assert registry_response.status_code == 200
