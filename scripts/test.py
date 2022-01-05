import os
import tempfile
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.mgmt.resource.subscriptions import SubscriptionClient

def get_blob_service_client(account_name: str) -> BlobServiceClient:
    try:
        #subscription_id="d3814ade-afe8-4260-9b5f-43019cd32cb7"
        subscription_id="e5c9fc83-fbd0-4368-9cb6-1b5823479b6dd"
        result = os.system(f"az account set --subscription {subscription_id}")
        print(f"`az account set --subscription {subscription_id}` ran with exit code {result}" )
        credentials = DefaultAzureCredential(exclude_interactive_browser_credential=False)
        # For other authentication approaches, please see: https://pypi.org/project/azure-identity/
        subscription_client = SubscriptionClient(
            credential=DefaultAzureCredential()
        )

        # List subscriptions
        page_result = subscription_client.subscriptions.list()
        result = [item for item in page_result]
        for item in result:
            print(f"id: {item.subscription_id} tenant_id: {item.tenant_id} state: {item.state}" )

        page_result = subscription_client.tenants.list()
        result = [item for item in page_result]
        for item in result:
            print(f"id: {item.display_name} tenant_id: {item.tenant_id} " )
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


def main():
    # Create client
    # For other authentication approaches, please see: https://pypi.org/project/azure-identity/
    subscription_client = SubscriptionClient(
        credential=DefaultAzureCredential()
    )

    # List subscriptions
    page_result = subscription_client.subscriptions.list()
    result = [item for item in page_result]
    for item in result:
        print(f"id: {item.subscription_id} tenant_id: {item.tenant_id} state: {item.state}" )

    # create temporary directory
    temp_dir = tempfile.TemporaryDirectory()
    result_local_path = f"{temp_dir.name}/test.csv"

    #
    # Download the result file
    #
    result = download_file_from_azure_blob(
        local_file_path=result_local_path,
        account_name="sacorpb0000",
        container_name="consumecorpb0000",
        blob_path=f"consume/corpa/cfcfa055-47c4-4b92-b246-1370f0ea4178/dataset-2022-01-03/output-00001.csv",
    )
    assert result is True

if __name__ == "__main__":
    main()
    