import os
from datetime import datetime


class Configuration:
    # Static variable storing current date
    DATE = datetime.utcnow()

    def __init__(self) -> None:
        self.REGISTRY_APP_SERVER = os.environ["REGISTRY_APP_SERVER"]

        # REGISTRY configuration
        self.REGISTRY_APP_SERVER = os.environ["REGISTRY_APP_SERVER"]
        self.AZURE_SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
        self.AZURE_TENANT_ID = os.environ["AZURE_TENANT_ID"]

        # NODE A configuration
        self.AZURE_SUBSCRIPTION_ID_A = os.environ["AZURE_SUBSCRIPTION_ID_A"]
        self.AZURE_TENANT_ID_A = os.environ["AZURE_TENANT_ID_A"]
        self.SHARE_APP_SERVER_A = os.environ["SHARE_APP_SERVER_A"]
        self.RESOURCE_GROUP_A = os.environ["RESOURCE_GROUP_A"]
        self.STORAGE_ACCOUNT_NAME_A = os.environ["STORAGE_ACCOUNT_NAME_A"]
        self.CONSUME_CONTAINER_A = os.environ["CONSUME_CONTAINER_A"]
        self.SHARE_CONTAINER_A = os.environ["SHARE_CONTAINER_A"]
        self.SHARE_FOLDER_FORMAT_A = os.environ["SHARE_FOLDER_FORMAT_A"]
        self.NODE_NAME_A = os.environ["NODE_NAME_A"]

        # NODE B configuration
        self.AZURE_SUBSCRIPTION_ID_B = os.environ["AZURE_SUBSCRIPTION_ID_B"]
        self.AZURE_TENANT_ID_B = os.environ["AZURE_TENANT_ID_B"]
        self.SHARE_APP_SERVER_B = os.environ["SHARE_APP_SERVER_B"]
        self.RESOURCE_GROUP_B = os.environ["RESOURCE_GROUP_B"]
        self.STORAGE_ACCOUNT_NAME_B = os.environ["STORAGE_ACCOUNT_NAME_B"]
        self.CONSUME_CONTAINER_B = os.environ["CONSUME_CONTAINER_B"]
        self.SHARE_CONTAINER_B = os.environ["SHARE_CONTAINER_B"]
        self.CONSUME_FOLDER_FORMAT_B = os.environ["CONSUME_FOLDER_FORMAT_B"]
        self.NODE_NAME_B = os.environ["NODE_NAME_B"]

        # Parameters used for the tests
        self.SOURCE_LOCAL_RELATIVE_PATH = "data/sampledata.csv"
        self.SOURCE_LOCAL_PATH = f"{os.path.dirname(os.path.abspath(__file__))}\
/{self.SOURCE_LOCAL_RELATIVE_PATH}"
        self.SOURCE_BLOB_FILE = "sampledata.csv"
        self.SOURCE_BLOB_FOLDER = (
            self.SHARE_FOLDER_FORMAT_A.replace("{date}", self.DATE.strftime("%Y-%m-%d"))
            .replace("{time}", self.DATE.strftime("%Y-%m-%d-%H-%M-%S"))
            .replace("{node_id}", self.NODE_NAME_B)
        )
        self.SINK_BLOB_FILE = "sampledata.csv"
        self.SINK_BLOB_FOLDER = (
            self.CONSUME_FOLDER_FORMAT_B.replace(
                "{date}", self.DATE.strftime("%Y-%m-%d")
            )
            .replace("{time}", self.DATE.strftime("%Y-%m-%d-%H-%M-%S"))
            .replace("{node_id}", self.NODE_NAME_B)
        )

        self.INVITATION_ID = ""
