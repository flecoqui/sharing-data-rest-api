import json
import os
import tempfile
import time

import pytest
import requests
from fastapi import HTTPException

from .configuration import Configuration
from .models import (
    ConsumeResponse,
    Dataset,
    ShareRequest,
    ShareResponse,
    Status,
)
from .test_common import (
    compare_files,
    download_file_from_azure_blob,
    upload_file_to_azure_blob,
    set_current_subscription
)


@pytest.fixture(scope="module")
def configuration():
    return Configuration()


def test_copy_input_file(
    configuration: Configuration,
):
    print(
        f"TEST DATASHARE SCENARIO 1: share from node {configuration.NODE_NAME_A} and consume API from node {configuration.NODE_NAME_B} "
    )
    # set the default subscription to get the access to the storage account
    result = set_current_subscription(configuration.AZURE_SUBSCRIPTION_ID_A)
    assert result == 0
    configuration.SOURCE_BLOB_PATH = f"{configuration.SOURCE_BLOB_FOLDER}/{configuration.SOURCE_BLOB_FILE}"  # noqa: E501
    res = upload_file_to_azure_blob(
        local_file_path=configuration.SOURCE_LOCAL_PATH,
        account_name=configuration.STORAGE_ACCOUNT_NAME_A,
        container_name=configuration.SHARE_CONTAINER_A,
        blob_path=configuration.SOURCE_BLOB_PATH,
    )
    assert res is True
    return


def test_trigger_share(configuration: Configuration, depends=["test_copy_input_file"]):
    try:
        share_url = f"https://{configuration.SHARE_APP_SERVER_A}/share"
        headers = {
            "Content-Type": "application/json",
        }
        dataset = Dataset(
            resource_group_name=configuration.RESOURCE_GROUP_A,
            storage_account_name=configuration.STORAGE_ACCOUNT_NAME_A,
            container_name=configuration.SHARE_CONTAINER_A,
            folder_path=configuration.SOURCE_BLOB_FOLDER,
            file_name=configuration.SOURCE_BLOB_FILE,
        )
        share = ShareRequest(
            provider_node_id=configuration.NODE_NAME_A,
            consumer_node_id=configuration.NODE_NAME_B,
            dataset=dataset.dict(),
        )
        share_response = requests.post(
            url=share_url,
            json=share.dict(),
            headers=headers,
        )
        share_response.raise_for_status()
        response: ShareResponse = json.loads(share_response.text)
        assert response["provider_node_id"] == share.provider_node_id
        assert response["consumer_node_id"] == share.consumer_node_id
        invitation_name = response["invitation_name"]
        invitation_id = response["invitation_id"]
        status = response["status"]["status"]
        print(
            f"Invitation received, id: {invitation_id} name: {invitation_name} status: {status}"
        )
        configuration.INVITATION_ID = invitation_id
        result = True
    except HTTPException as e:
        print(f"HTTPException while calling {share_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {share_url}: {repr(ex)}")
        result = False

    assert result is True


def test_get_share_status(configuration: Configuration, depends=["test_trigger_share"]):
    try:
        share_url = f"https://{configuration.SHARE_APP_SERVER_A}/share"
        headers = {
            "Content-Type": "application/json",
        }
        dataset = Dataset(
            resource_group_name=configuration.RESOURCE_GROUP_A,
            storage_account_name=configuration.STORAGE_ACCOUNT_NAME_A,
            container_name=configuration.SHARE_CONTAINER_A,
            folder_path=configuration.SOURCE_BLOB_FOLDER,
            file_name=configuration.SOURCE_BLOB_FILE,
        )
        share = ShareRequest(
            provider_node_id=configuration.NODE_NAME_A,
            consumer_node_id=configuration.NODE_NAME_B,
            dataset=dataset.dict(),
        )
        params = dict()
        params["provider_node_id"] = configuration.NODE_NAME_A
        params["consumer_node_id"] = configuration.NODE_NAME_B
        params["datashare_storage_resource_group_name"] = (
            configuration.RESOURCE_GROUP_A,
        )
        params["datashare_storage_account_name"] = (
            configuration.STORAGE_ACCOUNT_NAME_A,
        )
        params["datashare_storage_container_name"] = (configuration.SHARE_CONTAINER_A,)
        params["datashare_storage_folder_path"] = (configuration.SOURCE_BLOB_FOLDER,)
        params["datashare_storage_file_name"] = (configuration.SOURCE_BLOB_FILE,)
        share_response = requests.get(
            url=share_url,
            params=params,
            headers=headers,
        )
        share_response.raise_for_status()
        response: ShareResponse = json.loads(share_response.text)
        assert response["provider_node_id"] == share.provider_node_id
        assert response["consumer_node_id"] == share.consumer_node_id
        invitation_name = response["invitation_name"]
        invitation_id = response["invitation_id"]
        status = response["status"]["status"]
        print(
            f"Status received, status: {status} invitation_id: {invitation_id} name: {invitation_name} "
        )
        configuration.INVITATION_ID = invitation_id
        result = True
    except HTTPException as e:
        print(f"HTTPException while calling {share_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {share_url}: {repr(ex)}")
        result = False

    assert result is True


def test_trigger_consume(
    configuration: Configuration, depends=["test_get_share_status"]
):
    try:
        consume_url = f"https://{configuration.SHARE_APP_SERVER_B}/consume"
        headers = {
            "Content-Type": "application/json",
        }
        params = dict()
        params["provider_node_id"] = configuration.NODE_NAME_A
        params["consumer_node_id"] = configuration.NODE_NAME_B
        params["invitation_id"] = configuration.INVITATION_ID
        consume_response = requests.get(
            url=consume_url,
            params=params,
            headers=headers,
        )
        consume_response.raise_for_status()
        response: ConsumeResponse = json.loads(consume_response.text)
        assert response["provider_node_id"] == configuration.NODE_NAME_A
        assert response["consumer_node_id"] == configuration.NODE_NAME_B
        invitation_id = response["invitation_id"]
        status = response["status"]["status"]
        print(f"Invitation received, id: {invitation_id} status: {status}")
        result = True
    except HTTPException as e:
        print(f"HTTPException while calling {consume_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {consume_url}: {repr(ex)}")
        result = False
    assert result is True


def test_wait_for_consume_completion(
    configuration: Configuration, depends=["test_trigger_consume"]
):
    try:
        result = False
        status = Status.IN_PROGRESS
        while status != Status.FAILED and status != Status.SUCCEEDED:
            consume_url = f"https://{configuration.SHARE_APP_SERVER_B}/consume"
            headers = {
                "Content-Type": "application/json",
            }
            params = dict()
            params["provider_node_id"] = configuration.NODE_NAME_A
            params["consumer_node_id"] = configuration.NODE_NAME_B
            params["invitation_id"] = configuration.INVITATION_ID
            consume_response = requests.get(
                url=consume_url,
                params=params,
                headers=headers,
            )
            consume_response.raise_for_status()
            response: ConsumeResponse = json.loads(consume_response.text)
            assert response["provider_node_id"] == configuration.NODE_NAME_A
            assert response["consumer_node_id"] == configuration.NODE_NAME_B
            invitation_id = response["invitation_id"]
            status = response["status"]["status"]
            if status == Status.FAILED:
                message = response["error"]["message"]
                print(
                    f"Sharing Status from '{configuration.NODE_NAME_A}' to '{configuration.NODE_NAME_B}' Invitation '{invitation_id}' failed. message: '{message}'"
                )
            else:
                if status == Status.SUCCEEDED:
                    configuration.SINK_BLOB_FOLDER = response["dataset"]["folder_path"]
                    configuration.SINK_BLOB_FILE = response["dataset"]["file_name"]
                    print(
                        f"Sharing Status from '{configuration.NODE_NAME_A}' to '{configuration.NODE_NAME_B}' Invitation '{invitation_id}' successful. Dataset in file: {configuration.SINK_BLOB_FOLDER}/{configuration.SINK_BLOB_FILE} "
                    )
                    result = True
                else:
                    print(
                        f"Sharing Status from '{configuration.NODE_NAME_A}' to '{configuration.NODE_NAME_B}' Invitation '{invitation_id}' status: '{status}'"
                    )
            time.sleep(20)

    except HTTPException as e:
        print(f"HTTPException while calling {consume_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {consume_url}: {repr(ex)}")
        result = False
    assert result is True


def test_get_share_invitation_list_empty(
    configuration: Configuration, depends=["test_wait_for_consume_completion"]
):
    try:
        share_url = f"https://{configuration.SHARE_APP_SERVER_A}/share"
        headers = {
            "Content-Type": "application/json",
        }
        params = dict()
        params["provider_node_id"] = configuration.NODE_NAME_A
        params["consumer_node_id"] = configuration.NODE_NAME_B
        params["datashare_storage_resource_group_name"] = (
            configuration.RESOURCE_GROUP_A,
        )
        params["datashare_storage_account_name"] = (
            configuration.STORAGE_ACCOUNT_NAME_A,
        )
        params["datashare_storage_container_name"] = (configuration.SHARE_CONTAINER_A,)
        params["datashare_storage_folder_path"] = (configuration.SOURCE_BLOB_FOLDER,)
        params["datashare_storage_file_name"] = (configuration.SOURCE_BLOB_FILE,)
        share_response = requests.get(
            url=share_url,
            params=params,
            headers=headers,
        )
        # invitation shared not found as it has been consumed
        assert share_response.status_code == 404
        result = True
    except HTTPException as e:
        print(f"HTTPException while calling {share_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {share_url}: {repr(ex)}")
        result = False

    assert result is True


def test_check_received_file(
    configuration: Configuration, depends=["test_get_share_invitation_list_empty"]
):
    # set the default subscription to get the access to the storage account
    result = set_current_subscription(configuration.AZURE_SUBSCRIPTION_ID_B)

    # create temporary directory
    temp_dir = tempfile.TemporaryDirectory()
    result_local_path = f"{temp_dir.name}/{configuration.SOURCE_BLOB_FILE}"

    #
    # Download the result file
    #
    result = download_file_from_azure_blob(
        local_file_path=result_local_path,
        account_name=configuration.STORAGE_ACCOUNT_NAME_B,
        container_name=configuration.CONSUME_CONTAINER_B,
        blob_path=f"{configuration.SINK_BLOB_FOLDER}/{configuration.SINK_BLOB_FILE}",
    )
    assert result is True
    #
    # Check if the result file is correct
    #
    result = compare_files(
        first_file_path=configuration.SOURCE_LOCAL_PATH,
        second_file_path=result_local_path,
    )
    assert result is True

    if os.path.exists(result_local_path):
        os.remove(result_local_path)
    # use temp_dir, and when done:
    temp_dir.cleanup()

    print(
        f"TEST DATASHARE SCENARIO 1 SUCCESSFUL: share from node {configuration.NODE_NAME_A} and consume API from node {configuration.NODE_NAME_B} "
    )


def test_shareconsume_copy_input_file(
    configuration: Configuration, depends=["test_check_received_file"]
):
    print(
        f"TEST DATASHARE SCENARIO 2: share and consume from node {configuration.NODE_NAME_A} and consume API to node {configuration.NODE_NAME_B} through registry server "
    )
    # set the default subscription to get the access to the storage account
    result = set_current_subscription(configuration.AZURE_SUBSCRIPTION_ID_A)

    configuration.SOURCE_BLOB_PATH = f"{configuration.SOURCE_BLOB_FOLDER}-shareconsume/{configuration.SOURCE_BLOB_FILE}"  # noqa: E501
    res = upload_file_to_azure_blob(
        local_file_path=configuration.SOURCE_LOCAL_PATH,
        account_name=configuration.STORAGE_ACCOUNT_NAME_A,
        container_name=configuration.SHARE_CONTAINER_A,
        blob_path=configuration.SOURCE_BLOB_PATH,
    )
    assert res is True
    return


def test_shareconsume_trigger_shareconsume(
    configuration: Configuration, depends=["test_shareconsume_copy_input_file"]
):
    try:
        share_url = f"https://{configuration.SHARE_APP_SERVER_A}/shareconsume"
        headers = {
            "Content-Type": "application/json",
        }
        dataset = Dataset(
            resource_group_name=configuration.RESOURCE_GROUP_A,
            storage_account_name=configuration.STORAGE_ACCOUNT_NAME_A,
            container_name=configuration.SHARE_CONTAINER_A,
            folder_path=configuration.SOURCE_BLOB_FOLDER,
            file_name=configuration.SOURCE_BLOB_FILE,
        )
        share = ShareRequest(
            provider_node_id=configuration.NODE_NAME_A,
            consumer_node_id=configuration.NODE_NAME_B,
            dataset=dataset.dict(),
        )
        share_response = requests.post(
            url=share_url,
            json=share.dict(),
            headers=headers,
        )
        share_response.raise_for_status()
        response: ShareResponse = json.loads(share_response.text)
        assert response["provider_node_id"] == share.provider_node_id
        assert response["consumer_node_id"] == share.consumer_node_id
        invitation_name = response["invitation_name"]
        invitation_id = response["invitation_id"]
        status = response["status"]["status"]
        print(
            f"Invitation received, id: {invitation_id} name: {invitation_name} status: {status}"
        )
        configuration.INVITATION_ID = invitation_id
        result = True
    except HTTPException as e:
        print(f"HTTPException while calling {share_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {share_url}: {repr(ex)}")
        result = False

    assert result is True


def test_shareconsume_get_shareconsume(
    configuration: Configuration, depends=["test_shareconsume_trigger_shareconsume"]
):
    try:
        consume_url = f"https://{configuration.SHARE_APP_SERVER_A}/shareconsume"
        headers = {
            "Content-Type": "application/json",
        }
        params = dict()
        params["provider_node_id"] = configuration.NODE_NAME_A
        params["consumer_node_id"] = configuration.NODE_NAME_B
        params["invitation_id"] = configuration.INVITATION_ID
        consume_response = requests.get(
            url=consume_url,
            params=params,
            headers=headers,
        )
        consume_response.raise_for_status()
        response: ConsumeResponse = json.loads(consume_response.text)
        assert response["provider_node_id"] == configuration.NODE_NAME_A
        assert response["consumer_node_id"] == configuration.NODE_NAME_B
        invitation_id = response["invitation_id"]
        status = response["status"]["status"]
        print(f"Invitation received, id: {invitation_id} status: {status}")
        result = True
    except HTTPException as e:
        print(f"HTTPException while calling {consume_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {consume_url}: {repr(ex)}")
        result = False
    assert result is True


def test_shareconsume_wait_for_consume_completion(
    configuration: Configuration, depends=["test_shareconsume_get_shareconsume"]
):
    try:
        result = False
        status = Status.IN_PROGRESS
        while status != Status.FAILED and status != Status.SUCCEEDED:
            consume_url = f"https://{configuration.SHARE_APP_SERVER_A}/shareconsume"
            headers = {
                "Content-Type": "application/json",
            }
            params = dict()
            params["provider_node_id"] = configuration.NODE_NAME_A
            params["consumer_node_id"] = configuration.NODE_NAME_B
            params["invitation_id"] = configuration.INVITATION_ID
            consume_response = requests.get(
                url=consume_url,
                params=params,
                headers=headers,
            )
            consume_response.raise_for_status()
            response: ConsumeResponse = json.loads(consume_response.text)
            assert response["provider_node_id"] == configuration.NODE_NAME_A
            assert response["consumer_node_id"] == configuration.NODE_NAME_B
            invitation_id = response["invitation_id"]
            status = response["status"]["status"]
            if status == Status.FAILED:
                message = response["error"]["message"]
                print(
                    f"Sharing Status from '{configuration.NODE_NAME_A}' to '{configuration.NODE_NAME_B}' Invitation '{invitation_id}' failed. message: '{message}'"
                )
            else:
                if status == Status.SUCCEEDED:
                    configuration.SINK_BLOB_FOLDER = response["dataset"]["folder_path"]
                    configuration.SINK_BLOB_FILE = response["dataset"]["file_name"]
                    print(
                        f"Sharing Status from '{configuration.NODE_NAME_A}' to '{configuration.NODE_NAME_B}' Invitation '{invitation_id}' successful. Dataset in file: {configuration.SINK_BLOB_FOLDER}/{configuration.SINK_BLOB_FILE} "
                    )
                    result = True
                else:
                    print(
                        f"Sharing Status from '{configuration.NODE_NAME_A}' to '{configuration.NODE_NAME_B}' Invitation '{invitation_id}' status: '{status}'"
                    )
            time.sleep(20)

    except HTTPException as e:
        print(f"HTTPException while calling {consume_url}: {repr(e)}")
        result = False
    except Exception as ex:
        print(f"Exception while calling {consume_url}: {repr(ex)}")
        result = False
    assert result is True


def test_shareconsume_check_received_file(
    configuration: Configuration,
    depends=["test_shareconsume_wait_for_consume_completion"],
):
    # set the default subscription to get the access to the storage account
    result = set_current_subscription(configuration.AZURE_SUBSCRIPTION_ID_B)

    # create temporary directory
    temp_dir = tempfile.TemporaryDirectory()
    result_local_path = f"{temp_dir.name}/{configuration.SOURCE_BLOB_FILE}"

    #
    # Download the result file
    #
    result = download_file_from_azure_blob(
        local_file_path=result_local_path,
        account_name=configuration.STORAGE_ACCOUNT_NAME_B,
        container_name=configuration.CONSUME_CONTAINER_B,
        blob_path=f"{configuration.SINK_BLOB_FOLDER}/{configuration.SINK_BLOB_FILE}",
    )
    assert result is True
    #
    # Check if the result file is correct
    #
    result = compare_files(
        first_file_path=configuration.SOURCE_LOCAL_PATH,
        second_file_path=result_local_path,
    )
    assert result is True

    if os.path.exists(result_local_path):
        os.remove(result_local_path)
    # use temp_dir, and when done:
    temp_dir.cleanup()
    print(
        f"TEST DATASHARE SCENARIO 2 SUCCESSFUL: share and consume from node {configuration.NODE_NAME_A} and consume API to node {configuration.NODE_NAME_B} through registry server "
    )
