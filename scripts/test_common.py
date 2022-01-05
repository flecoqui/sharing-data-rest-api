# Integration Test:
# Test Data Share
# Update the file conftest.py to define the parameters associated
# with this test.
#
import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.mgmt.resource.subscriptions import SubscriptionClient

def compare_files(first_file_path: str, second_file_path: str) -> bool:
    try:
        with open(first_file_path) as first:
            with open(second_file_path) as second:
                first_lines = first.readlines()
                second_lines = second.readlines()
                if not first_lines == second_lines:
                    return False

    except Exception as e:
        print(f"Error while comparing files: Exception: {repr(e)}")
        return False
    return True


def get_substring_after_sep(line: str, sep: str) -> str:
    result = ""
    if not line:
        return line
    pos = line.index(sep)
    if pos > 0:
        result = line[pos:]
    return result


def compare_files_without_key(ref_file_path: str, file_path: str) -> bool:
    result = True
    try:
        with open(ref_file_path) as ref:
            with open(file_path) as comp:
                count = 0
                while True:
                    count += 1
                    # Get next line from file
                    first_line = get_substring_after_sep(ref.readline(), ";")
                    second_line = get_substring_after_sep(comp.readline(), ";")
                    if not first_line:
                        break
                    if first_line != second_line:
                        result = False
                        break

    except Exception as e:
        print(f"Error while comparing files: Exception: {repr(e)}")
        return False
    return result


def get_blob_service_client(account_name: str) -> BlobServiceClient:
    try:
        credentials = DefaultAzureCredential()
        # For other authentication approaches, please see: https://pypi.org/project/azure-identity/
        #subscription_client = SubscriptionClient(
        #    credential=DefaultAzureCredential()
        #)

        # List subscriptions
        #page_result = subscription_client.subscriptions.list()
        #result = [item for item in page_result]
        #for item in result:
        #    print(f"id: {item.subscription_id} tenant_id: {item.tenant_id} state: {item.state}" )

        blob_service_client = BlobServiceClient(
            account_url="https://{account}.blob.core.windows.net/".format(
                account=account_name
            ),
            credential=credentials,
        )
    except Exception as e:
        print(f"Error getting BlobServiceClient: Exception: {repr(e)}")
        return None
    return blob_service_client


def upload_file_to_azure_blob(
    local_file_path: str,
    account_name: str,
    container_name: str,
    blob_path: str,
) -> bool:
    try:
        blob_service_client = get_blob_service_client(account_name)
        container_client = blob_service_client.get_container_client(container_name)
        with open(local_file_path, "rb") as data:
            container_client.upload_blob(
                blob_path, data, blob_type="BlockBlob", overwrite=True
            )
    except Exception as e:
        print(f"Error while uploading files: Exception: {repr(e)}")
        return False
    return True


def download_file_from_azure_blob(
    local_file_path: str,
    account_name: str,
    container_name: str,
    blob_path: str,
) -> bool:
    try:
        blob_service_client = get_blob_service_client(account_name)
        blob_client = blob_service_client.get_blob_client(container_name, blob_path)
        # Download the file.
        with open(local_file_path, "wb") as blob:
            download_stream = blob_client.download_blob()
            blob.write(download_stream.readall())
    except Exception as e:
        print(f"Error while downloading files: Exception: {repr(e)}")
        return False
    return True


def azure_blob_exists(
    account_name: str,
    container_name: str,
    blob_path: str,
) -> bool:
    try:
        blob_service_client = get_blob_service_client(account_name)
        blob_client = blob_service_client.get_blob_client(container_name, blob_path)
        return blob_client.exists()
    except Exception as e:
        print(f"Error while checking if blob exists: Exception: {repr(e)}")
        return False

def set_current_subscription(subscription_id: str) -> int:
    result = os.system(f"az account set --subscription {subscription_id}")
    return result
