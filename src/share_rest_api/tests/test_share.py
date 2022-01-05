from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from src.models import (
    ConsumeResponse,
    Dataset,
    Error,
    Node,
    ShareNode,
    ShareRequest,
    ShareResponse,
    StatusDetails,
)

from .conftest import MinimalResponse


def test_version(client: TestClient):
    share_response = client.get(
        url="/version",
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    assert share_response.status_code == 200


def test_time(client: TestClient):
    share_response = client.get(
        url="/time",
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    assert share_response.status_code == 200


@pytest.mark.parametrize(
    "initialize_return,initialize_azure_clients_return, status_code",
    [(True, True, 200), (True, False, 500)],
)
def test_create_share(
    client: TestClient, initialize_return, initialize_azure_clients_return, status_code
):
    with patch("requests.get") as mock_requests_get, patch(
        "src.datashare_service.DatashareService.initialize_azure_clients"
    ) as mock_initialize_azure_clients, patch(
        "src.datashare_service.DatashareService.initialize"
    ) as mock_initialize, patch(
        "src.datashare_service.DatashareService.share"
    ) as mock_share:
        node = Node(node_id="testa", tenant_id="00000000-0000-0000-000000000000", identity="00000000-0000-0000-000000000000")
        mock_requests_get.return_value = MinimalResponse(
            status_code=200, text=node.json()
        )
        mock_initialize.return_value = initialize_return
        mock_initialize_azure_clients.return_value = initialize_azure_clients_return
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
            code=0, message="No error", source="share_rest_api", date=datetime.utcnow()
        )
        node_id = "testa"

        mock_share.return_value = dict(
            ShareResponse(
                invitation_id="00000000-0000-0000-000000000000",
                invitation_name="invitationName",
                provider_node_id=node_id,
                consumer_node_id=node_id,
                dataset=dataset,
                status=status,
                error=error,
            )
        )
        share = ShareRequest(
            provider_node_id=node_id, consumer_node_id=node_id, dataset=dataset
        )
        share_response = client.post(
            url="/share",
            json=share.dict(),
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        assert share_response.status_code == status_code


@pytest.mark.parametrize(
    "initialize_return,initialize_azure_clients_return, status_code",
    [(True, True, 200), (True, False, 500)],
)
def test_get_share(
    client: TestClient, initialize_return, initialize_azure_clients_return, status_code
):
    with patch("requests.get") as mock_requests_get, patch(
        "src.datashare_service.DatashareService.initialize_azure_clients"
    ) as mock_initialize_azure_clients, patch(
        "src.datashare_service.DatashareService.initialize"
    ) as mock_initialize, patch(
        "src.datashare_service.DatashareService.share_status"
    ) as mock_share_status:
        node = Node(node_id="testa", tenant_id="00000000-0000-0000-000000000000", identity="00000000-0000-0000-000000000000")
        mock_requests_get.return_value = MinimalResponse(
            status_code=200, text=node.json()
        )
        mock_initialize.return_value = initialize_return
        mock_initialize_azure_clients.return_value = initialize_azure_clients_return
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
            code=0, message="No error", source="share_rest_api", date=datetime.utcnow()
        )
        node_id = "testa"

        mock_share_status.return_value = dict(
            ShareResponse(
                invitation_id="00000000-0000-0000-000000000000",
                invitation_name="invitationName",
                provider_node_id=node_id,
                consumer_node_id=node_id,
                dataset=dataset,
                status=status,
                error=error,
            )
        )
        params = dict()
        params["provider_node_id"] = node_id
        params["consumer_node_id"] = node_id
        params["datashare_storage_resource_group_name"] = "testrg"
        params["datashare_storage_account_name"] = "testsa"
        params["datashare_storage_container_name"] = "testc"
        params["datashare_storage_folder_path"] = "testfolder"
        params["datashare_storage_file_name"] = "testfile"

        share_response = client.get(
            url="/share",
            params=params,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        assert share_response.status_code == status_code


@pytest.mark.parametrize(
    "initialize_return,initialize_azure_clients_return, status_code",
    [(True, True, 200), (True, False, 500)],
)
def test_get_consume(
    client: TestClient, initialize_return, initialize_azure_clients_return, status_code
):
    with patch("requests.get") as mock_requests_get, patch(
        "src.datashare_service.DatashareService.initialize_azure_clients"
    ) as mock_initialize_azure_clients, patch(
        "src.datashare_service.DatashareService.initialize"
    ) as mock_initialize, patch(
        "src.datashare_service.DatashareService.consume"
    ) as mock_consume:
        node = Node(node_id="testa", tenant_id="00000000-0000-0000-000000000000", identity="00000000-0000-0000-000000000000")
        mock_requests_get.return_value = MinimalResponse(
            status_code=200, text=node.json()
        )
        mock_initialize.return_value = initialize_return
        mock_initialize_azure_clients.return_value = initialize_azure_clients_return
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
            code=0, message="No error", source="share_rest_api", date=datetime.utcnow()
        )
        node_id = "testa"
        invitation_id = ("00000000-0000-0000-000000000000",)

        mock_consume.return_value = ConsumeResponse(
            invitation_id="00000000-0000-0000-000000000000",
            provider_node_id=node_id,
            consumer_node_id=node_id,
            dataset=dataset,
            status=status,
            error=error,
        )

        params = dict()
        params["provider_node_id"] = node_id
        params["consumer_node_id"] = node_id
        params["invitation_id"] = invitation_id

        share_response = client.get(
            url="/consume",
            params=params,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        assert share_response.status_code == status_code


@pytest.mark.parametrize(
    "initialize_return,initialize_azure_clients_return, status_code",
    [(True, True, 200), (True, False, 500)],
)
def test_shareconsume(
    client: TestClient, initialize_return, initialize_azure_clients_return, status_code
):
    with patch("requests.get") as mock_requests_get, patch(
        "src.datashare_service.DatashareService.initialize_azure_clients"
    ) as mock_initialize_azure_clients, patch(
        "src.datashare_service.DatashareService.initialize"
    ) as mock_initialize, patch(
        "src.datashare_service.DatashareService.share"
    ) as mock_share:
        node = Node(node_id="testa", tenant_id="00000000-0000-0000-000000000000", identity="00000000-0000-0000-000000000000")
        mock_requests_get.return_value = MinimalResponse(
            status_code=200, text=node.json()
        )
        mock_initialize.return_value = initialize_return
        mock_initialize_azure_clients.return_value = initialize_azure_clients_return
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
            code=0, message="No error", source="share_rest_api", date=datetime.utcnow()
        )
        node_id = "testa"

        mock_share.return_value = dict(
            ShareResponse(
                invitation_id="00000000-0000-0000-000000000000",
                invitation_name="invitationName",
                provider_node_id=node_id,
                consumer_node_id=node_id,
                dataset=dataset,
                status=status,
                error=error,
            )
        )
        share = ShareRequest(
            provider_node_id=node_id, consumer_node_id=node_id, dataset=dataset
        )
        share_response = client.post(
            url="/shareconsume",
            json=share.dict(),
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        assert share_response.status_code == status_code


@pytest.mark.parametrize(
    "create_error, status_code",
    [(False, 200), (True, 500)],
)
def test_get_shareconsume(client: TestClient, create_error, status_code):
    with patch("requests.get") as mock_requests_get:
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
            code=0, message="No error", source="share_rest_api", date=datetime.utcnow()
        )
        node_id = "testa"
        invitation_id = ("00000000-0000-0000-000000000000",)

        cr = ConsumeResponse(
            invitation_id="00000000-0000-0000-000000000000",
            provider_node_id=node_id,
            consumer_node_id=node_id,
            dataset=dataset,
            status=status,
            error=error,
        )
        if create_error is True:
            mock_requests_get.return_value = MinimalResponse(
                status_code=500, text="Exception occurred"
            )
        else:
            mock_requests_get.return_value = MinimalResponse(
                status_code=200, text=cr.json()
            )

        params = dict()
        params["provider_node_id"] = node_id
        params["consumer_node_id"] = node_id
        params["invitation_id"] = invitation_id

        share_response = client.get(
            url="/shareconsume",
            params=params,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        assert share_response.status_code == status_code


@pytest.mark.parametrize(
    "initialize_return,initialize_azure_clients_return, status_code",
    [(True, True, 200), (True, False, 500)],
)
def test_consumeshare(
    client: TestClient, initialize_return, initialize_azure_clients_return, status_code
):
    with patch("requests.get") as mock_requests_get, patch(
        "src.datashare_service.DatashareService.initialize_azure_clients"
    ) as mock_initialize_azure_clients, patch(
        "src.datashare_service.DatashareService.initialize"
    ) as mock_initialize, patch(
        "src.datashare_service.DatashareService.consume"
    ) as mock_consume:
        node = Node(node_id="testa", tenant_id="00000000-0000-0000-000000000000", identity="00000000-0000-0000-000000000000")
        mock_requests_get.return_value = MinimalResponse(
            status_code=200, text=node.json()
        )
        mock_initialize.return_value = initialize_return
        mock_initialize_azure_clients.return_value = initialize_azure_clients_return
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
            code=0, message="No error", source="share_rest_api", date=datetime.utcnow()
        )
        node_id = "testa"
        invitation_id = ("00000000-0000-0000-000000000000",)

        mock_consume.return_value = dict(
            ConsumeResponse(
                invitation_id="00000000-0000-0000-000000000000",
                provider_node_id=node_id,
                consumer_node_id=node_id,
                dataset=dataset,
                status=status,
                error=error,
            )
        )
        params = dict()
        params["provider_node_id"] = node_id
        params["consumer_node_id"] = node_id
        params["invitation_id"] = invitation_id

        share_response = client.get(
            url="/consumeshare",
            params=params,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        assert share_response.status_code == status_code


def test_register_node(share_service):
    with patch("requests.post") as mock_requests_post, patch(
        "src.datashare_service.DatashareService.initialize_azure_clients"
    ) as mock_initialize_azure_clients, patch(
        "src.datashare_service.DatashareService.initialize"
    ) as mock_initialize:
        node = ShareNode(
            node_id="testa",
            tenant_id="00000000-0000-0000-000000000000",
            identity="00000000-0000-0000-000000000000",
            url="http://127.0.0.1/",
            name="testa",
        )
        mock_requests_post.return_value = MinimalResponse(
            status_code=200, text=node.json()
        )
        mock_initialize.return_value = True
        mock_initialize_azure_clients.return_value = True
        result = share_service.register_share_node()
        assert result is True
