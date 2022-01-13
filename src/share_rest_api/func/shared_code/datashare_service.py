from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Union

from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.datashare import DataShareManagementClient
from azure.mgmt.datashare.models import (
    BlobDataSet,
    BlobDataSetMapping,
    ConsumerSourceDataSet,
    DataSetMapping,
    Invitation,
    Share,
    ShareSubscription,
    ShareSubscriptionSynchronization,
    Synchronize,
)
from fastapi import HTTPException

from shared_code.models import (
    ConsumeResponse,
    Dataset,
    Error,
    ShareResponse,
    Status,
    StatusDetails,
)


class DatashareServiceError(int, Enum):
    NO_ERROR = 0
    SHARING_DATASET_ERROR = 1
    SHARING_DATASET_EXCEPTION = 2
    CONSUMING_DATASET_ERROR = 3
    CONSUMING_DATASET_EXCEPTION = 4
    SYNCHRONIZATION_ERROR = 5


class DatashareService:
    """
    Class used to implement the Datashare service using Azure
    Data Share API
    """

    def __init__(
        self,
        subscription_id: str,
        tenant_id: str,
        datashare_resource_group_name: str,
        datashare_account_name: str,
    ) -> None:
        """
        Initialize the service with subscription_id, tenant_id,
        datashare resource group and datashare account
        """
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.resource_group_name = datashare_resource_group_name
        self.account_name = datashare_account_name
        self.datashare_client = None
        self.datashare_account = None
        self.datashare_location = None
        if not self.initialize_azure_clients():
            raise HTTPException(
                status_code=500,
                detail="Internal server error. Initialize Azure Client failed",
            )

    def initialize_azure_clients(self) -> bool:
        """Initialize the connection with Datashare client"""
        try:
            self.credentials = DefaultAzureCredential()
            self.datashare_client = DataShareManagementClient(
                self.credentials, self.subscription_id
            )
            self.datashare_account = self.datashare_client.accounts.get(
                self.resource_group_name, self.account_name
            )
            self.datashare_location = self.datashare_account.location
        except Exception as ex:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error. Initialize Azure Client\
 failed. Exception: {ex}",
            )
        return True

    def initialize(self):
        """Initialize the Datashare client"""
        if self.datashare_client is None:
            self.credentials = DefaultAzureCredential()
            self.datashare_client = DataShareManagementClient(
                self.credentials, self.subscription_id
            )
        if self.datashare_account is None:
            self.datashare_account = self.datashare_client.accounts.get(
                self.resource_group_name, self.account_name
            )
            self.datashare_location = self.datashare_account.location

    def share(
        self,
        provider_node_id: str,
        consumer_node_id: str,
        tenant_id: str,
        identity: str,
        datashare_storage_resource_group_name: str,
        datashare_storage_account_name: str,
        datashare_storage_container_name: str,
        datashare_storage_folder_path: str,
        datashare_storage_file_name: str,
    ) -> ShareResponse:
        """
        Launch the datashare process, using the following parameters:
        provider_node_id: the node_id of the node which is launching the share
        consumer_node_id: the node_id of the node which will consume the
            dataset
        tenant_id: it is the tenant_id associated with the consumer node
        identity: it is the object_id of system assigned identity associated
            with the App Service running share_rest_api in consumer node
        datashare_storage_resource_group_name: the resource group of the
            storage account where the source dataset is stored,
        datashare_storage_account_name: the storage account where the source
            dataset is stored,
        datashare_storage_container_name: the storage container where the
            source dataset is stored,
        datashare_storage_folder_path: the folder path where the source
            dataset is stored,
        datashare_storage_file_name: the file name where the source dataset
            is stored,
        This API returns the object ShareResponse which contains the
        invitation_id which will be shared with the recipient share_rest_api
        to consume this datashare.
        """
        hash = self.get_hash(
            datashare_storage_resource_group_name,
            datashare_storage_account_name,
            datashare_storage_container_name,
            datashare_storage_folder_path,
            datashare_storage_file_name,
        )
        share_id = f"{provider_node_id}-{consumer_node_id}-{hash}"
        text = f"share-{share_id}-{tenant_id}-{identity}"
        share_name = text[0:90]
        text = f"datashare-{share_id}-{tenant_id}-{identity}"
        share_datashare_name = text[0:90]
        text = f"invitation-{share_id}-{tenant_id}-{identity}"
        invitation_name = text[0:90]
        folder_path = f"{datashare_storage_folder_path}"

        try:
            sent_share = self.get_share(share_name, "Provider share")
            if sent_share is None:
                return None
            if folder_path[-1] != "/":
                path = f"{folder_path}/{datashare_storage_file_name}"
            else:
                path = f"{folder_path}{datashare_storage_file_name}"
            self.create_blob_datashare(
                share_name,
                share_datashare_name,
                datashare_storage_resource_group_name,
                datashare_storage_account_name,
                datashare_storage_container_name,
                path,
            )

            invitation = self.create_invitation(
                share_name,
                invitation_name,
                tenant_id,
                identity,
            )
            share_response = self.create_share_response(
                provider_node_id=provider_node_id,
                consumer_node_id=consumer_node_id,
                invitation_id=invitation.invitation_id,
                invitation_name=invitation.name,
                datashare_storage_resource_group_name=datashare_storage_resource_group_name,
                datashare_storage_account_name=datashare_storage_account_name,
                datashare_storage_container_name=datashare_storage_container_name,
                datashare_storage_folder_path=datashare_storage_folder_path,
                datashare_storage_file_name=datashare_storage_file_name,
                invitation_status=invitation.invitation_status,
                invitation_date=invitation.sent_at,
                error_code=DatashareServiceError.NO_ERROR,
                error_message="",
            )
        except Exception as ex:
            raise HTTPException(
                status_code=500,
                detail=f"Exception in method 'share' of datashare service: {ex}",
            )
        return share_response

    def share_status(
        self,
        provider_node_id: str,
        consumer_node_id: str,
        tenant_id: str,
        identity: str,
        datashare_storage_resource_group_name: str,
        datashare_storage_account_name: str,
        datashare_storage_container_name: str,
        datashare_storage_folder_path: str,
        datashare_storage_file_name: str,
    ) -> ShareResponse:
        """
        Returns the share status till the invitation is accepted by
        the recipient share_rest_api.
        This method can be used to check whether the invitation
        has been accepted. This method use the following parameters:
        provider_node_id: the node_id of the node which is launching the share
        consumer_node_id: the node_id of the node which will consume the
            dataset
        tenant_id: it is the tenant id associated with the consumer node
        identity: it is the object_id of system assigned identity associated
            with the App Service running share_rest_api in consumer node
        datashare_storage_resource_group_name: the resource group of the
            storage account where the source dataset is stored,
        datashare_storage_account_name: the storage account where the source
            dataset is stored,
        datashare_storage_container_name: the storage container where the
            source dataset is stored,
        datashare_storage_folder_path: the folder path where the source
            dataset is stored,
        datashare_storage_file_name: the file name where the source dataset
            is stored,
        This API returns the object ShareResponse which contains the
        invitation_id and the status of the invitation. If the value of
        status.status is Status.PENDING, the invitation has been correctly
        sent to the recipient, if the invitation failed, further information
        about the error will be available in error.message.
        """
        hash = self.get_hash(
            datashare_storage_resource_group_name,
            datashare_storage_account_name,
            datashare_storage_container_name,
            datashare_storage_folder_path,
            datashare_storage_file_name,
        )
        share_id = f"{provider_node_id}-{consumer_node_id}-{hash}"
        text = f"share-{share_id}-{tenant_id}-{identity}"
        share_name = text[0:90]
        text = f"invitation-{share_id}-{tenant_id}-{identity}"
        invitation_name = text[0:90]

        try:
            invitation = self.get_invitation(share_name, invitation_name)
            if invitation is not None:
                share_response = self.create_share_response(
                    provider_node_id=provider_node_id,
                    consumer_node_id=consumer_node_id,
                    invitation_id=invitation.invitation_id,
                    invitation_name=invitation.name,
                    datashare_storage_resource_group_name=datashare_storage_resource_group_name,
                    datashare_storage_account_name=datashare_storage_account_name,
                    datashare_storage_container_name=datashare_storage_container_name,
                    datashare_storage_folder_path=datashare_storage_folder_path,
                    datashare_storage_file_name=datashare_storage_file_name,
                    invitation_status=invitation.invitation_status,
                    invitation_date=invitation.sent_at,
                    error_code=DatashareServiceError.NO_ERROR,
                    error_message="",
                )
            else:
                raise HTTPException(
                    status_code=404, detail=f"Invitation {invitation_name} not found"
                )
        except HTTPException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=f"HTTP Exception in method 'share_status' while receiving datashare {e.detail}",
            )
        except Exception as ex:
            raise HTTPException(
                status_code=500,
                detail=f"Exception in method 'share_status' of datashare service: {ex}",
            )
        return share_response

    def consume(
        self,
        provider_node_id: str,
        consumer_node_id: str,
        invitation_id: str,
        datashare_storage_resource_group_name: str,
        datashare_storage_account_name: str,
        datashare_storage_container_name: str,
        datashare_storage_folder_path: str,
        datashare_storage_file_name: str,
    ) -> ConsumeResponse:
        """
        Launch the reception of the shared dataset associated
        with the invitation_id using the following parameters:
        provider_node_id: the node_id of the node which is launching the share
        consumer_node_id: the node_id of the node which will consume the
            dataset
        invitation_id: it is the invitation_id associated with
            the shared dataset. This parameter is used by the
            datashare client API
        datashare_storage_resource_group_name: the resource group of the
            storage account where the received dataset will be stored,
        datashare_storage_account_name: the storage account where the
            received dataset will be,
        datashare_storage_container_name: the storage container where the
            received dataset will be stored,
        datashare_storage_folder_path: the folder path where the
            received dataset will be stored,
        datashare_storage_file_name: the file name where the
            received dataset will be stored,
        This API returns the object ConsumeResponse which contains the
        the status of the sharing process. If the value of
        status.status is Status.SUCCEEDED, the dataset has been
        received. If the value of status.status is Status.FAILED, an error
        occured, further information
        about the error will be available in error.message.
        """
        hash = self.get_hash(
            datashare_storage_resource_group_name,
            datashare_storage_account_name,
            datashare_storage_container_name,
            datashare_storage_folder_path,
            datashare_storage_file_name,
        )
        share_id = f"{provider_node_id}-{consumer_node_id}-{hash}"
        text = f"consume-{share_id}-{invitation_id}"
        share_name = text[0:90]
        text = f"datashare-{share_id}-{invitation_id}"
        share_datashare_name = text[0:90]

        try:
            share_subscription_synchronization = self.get_synchronize(share_name)
            if share_subscription_synchronization is None:
                # if there is no synchronization for share_name
                # create a share subscription with invitation id
                if self.is_invitations_list_empty() is True:
                    raise HTTPException(
                        status_code=500,
                        detail="The invitation list is empty or\
 the current identity can't read invitation check with your Azure AD\
 administrator",
                    )
                if self.is_invitation_received(invitation_id) is not True:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invitation {invitation_id} not received",
                    )
                share_subscription = self.create_share_subscription(
                    share_name, invitation_id
                )
                if share_subscription is not None:
                    consumer_source_datashare = self.get_consumer_source_datashare(
                        share_name
                    )
                    if consumer_source_datashare is not None:
                        folder_path = f"{datashare_storage_folder_path}"

                        if folder_path[-1] != "/":
                            path = f"{folder_path}/{datashare_storage_file_name}"
                        else:
                            path = f"{folder_path}{datashare_storage_file_name}"
                        self.create_datashare_mapping(
                            share_name=share_name,
                            name=share_datashare_name,
                            datashare_id=consumer_source_datashare.data_set_id,
                            resource_group_name=datashare_storage_resource_group_name,
                            storage_account_name=datashare_storage_account_name,
                            container_name=datashare_storage_container_name,
                            prefix=path,
                        )

                        share_subscription_synchronization = self.launch_synchronize(
                            share_name
                        )
                        consume_response = self.create_consume_response(
                            provider_node_id=provider_node_id,
                            consumer_node_id=consumer_node_id,
                            invitation_id=invitation_id,
                            datashare_storage_resource_group_name=datashare_storage_resource_group_name,
                            datashare_storage_account_name=datashare_storage_account_name,
                            datashare_storage_container_name=datashare_storage_container_name,
                            datashare_storage_folder_path=datashare_storage_folder_path,
                            datashare_storage_file_name=datashare_storage_file_name,
                            status=share_subscription_synchronization.status,
                            status_start_date=datetime.min
                            if share_subscription_synchronization.start_time is None
                            else share_subscription_synchronization.start_time,
                            status_end_date=datetime.min
                            if share_subscription_synchronization.end_time is None
                            else share_subscription_synchronization.end_time,
                            status_duration_in_ms=0
                            if share_subscription_synchronization.duration_ms is None
                            else share_subscription_synchronization.duration_ms,
                            error_code=DatashareServiceError.NO_ERROR,
                            error_message="",
                        )
            else:
                # if a synchronization already exists for share_name
                # the invitation_id has already been consumed
                # monitoring the progress of the synchronization
                consume_response = self.create_consume_response(
                    provider_node_id=provider_node_id,
                    consumer_node_id=consumer_node_id,
                    invitation_id=invitation_id,
                    datashare_storage_resource_group_name=datashare_storage_resource_group_name,
                    datashare_storage_account_name=datashare_storage_account_name,
                    datashare_storage_container_name=datashare_storage_container_name,
                    datashare_storage_folder_path=datashare_storage_folder_path,
                    datashare_storage_file_name=datashare_storage_file_name,
                    status=share_subscription_synchronization.status,
                    status_start_date=datetime.min
                    if share_subscription_synchronization.start_time is None
                    else share_subscription_synchronization.start_time,
                    status_end_date=datetime.min
                    if share_subscription_synchronization.end_time is None
                    else share_subscription_synchronization.end_time,
                    status_duration_in_ms=0
                    if share_subscription_synchronization.duration_ms is None
                    else share_subscription_synchronization.duration_ms,
                    error_code=DatashareServiceError.NO_ERROR
                    if share_subscription_synchronization.message is None
                    else DatashareServiceError.SYNCHRONIZATION_ERROR,
                    error_message=""
                    if share_subscription_synchronization.message is None
                    else share_subscription_synchronization.message,
                )

        except HTTPException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=f"Exception while receiving datashare {e.detail}",
            )
        except Exception as ex:
            raise HTTPException(
                status_code=500,
                detail=f"Exception while receiving datashare {ex}",
            )
        return consume_response

    def get_hash(
        self,
        datashare_storage_resource_group_name: str,
        datashare_storage_account_name: str,
        datashare_storage_container_name: str,
        datashare_storage_folder_path: str,
        datashare_storage_file_name: str,
    ) -> str:
        """
        Return the hash associated with the blob storage where the dataset
        is stored
        """
        text = f"{datashare_storage_resource_group_name}-\
{datashare_storage_account_name}-{datashare_storage_container_name}-\
{datashare_storage_folder_path}-{datashare_storage_file_name}"
        hash_object = hashlib.md5(text.encode())
        return hash_object.hexdigest()

    def get_share(self, name: str, description: str) -> Union[Share, None]:
        """
        Returns the object Share using the share name
        """
        self.initialize()
        try:
            share = self.datashare_client.shares.get(
                self.resource_group_name, self.account_name, name
            )
        except HttpResponseError as ex:
            if ex.status_code == 404:
                sharePayload = Share(
                    name=name,
                    terms="Terms",
                    description=description,
                    share_kind="CopyBased",
                )
                share = self.datashare_client.shares.create(
                    self.resource_group_name, self.account_name, name, sharePayload
                )
            else:
                return None
        return share

    def create_blob_datashare(
        self,
        share_name: str,
        name: str,
        resource_group_name: str,
        storage_account_name: str,
        container_name: str,
        file_path: str,
    ) -> BlobDataSet:
        """
        Create a BlobDataSet to receive the shared dataset
        """
        self.initialize()

        try:
            blob_datashare = self.datashare_client.data_sets.get(
                self.resource_group_name, self.account_name, share_name, name
            )
        except Exception as ex:
            blob_datashare = None
            if ex.status_code == 404:
                blob_datashare_playload = BlobDataSet(
                    kind="Blob",
                    container_name=container_name,
                    file_path=file_path,
                    resource_group=resource_group_name,
                    storage_account_name=storage_account_name,
                    subscription_id=self.subscription_id,
                )
                blob_datashare = self.datashare_client.data_sets.create(
                    self.resource_group_name,
                    self.account_name,
                    share_name,
                    name,
                    blob_datashare_playload,
                )
        return blob_datashare

    def create_invitation(
        self,
        share_name: str,
        invitation_name: str,
        tenant_id: str,
        object_id: str,
    ) -> Invitation:
        """
        Create an invitation
        """
        self.initialize()

        try:
            invitation = self.datashare_client.invitations.get(
                self.resource_group_name, self.account_name, share_name, invitation_name
            )
        except Exception as ex:
            invitation = None
            if ex.status_code == 404:
                try:
                    invitation_playload = Invitation(
                        target_active_directory_id=tenant_id, target_object_id=object_id
                    )
                    invitation = self.datashare_client.invitations.create(
                        self.resource_group_name,
                        self.account_name,
                        share_name,
                        invitation_name,
                        invitation_playload,
                    )
                except Exception:
                    invitation = None
        return invitation

    def get_invitation(self, share_name: str, invitation_name: str) -> Invitation:
        """
        Get an invitation using the share name and the invitation name
        """
        self.initialize()

        try:
            invitation = self.datashare_client.invitations.get(
                self.resource_group_name, self.account_name, share_name, invitation_name
            )
        except Exception:
            invitation = None
        return invitation

    def is_invitation_received(self, invitation_id: str) -> bool:
        """
        Check if an invitation has been received using the invitation_id
        """
        try:
            for (
                consumer_invitation
            ) in self.datashare_client.consumer_invitations.list_invitations():
                if consumer_invitation.invitation_id == invitation_id:
                    return True
        except Exception:
            return False
        return False

    def is_invitations_list_empty(self) -> bool:
        """
        Check if invitation are available
        """
        try:
            self.datashare_client.consumer_invitations.list_invitations().next()
        except StopIteration:
            return True
        else:
            return False

    def create_share_subscription(
        self, share_name: str, invitation_id: str
    ) -> ShareSubscription:
        """
        Create a ShareSubscription to receive the dataset
        """
        self.initialize()
        bcreate = False
        try:
            share_subscription = self.datashare_client.share_subscriptions.get(
                self.resource_group_name, self.account_name, share_name
            )
            if share_subscription.invitation_id != invitation_id:
                self.datashare_client.share_subscriptions.begin_delete(
                    self.resource_group_name, self.account_name, share_name
                )
                bcreate = True
        except Exception as ex:
            share_subscription = None
            if ex.status_code == 404:
                bcreate = True

        if bcreate is True:
            try:
                consumer_invitation = self.datashare_client.consumer_invitations.get(
                    self.datashare_location, invitation_id
                )
                if consumer_invitation is not None:
                    share_subscription_payload = ShareSubscription(
                        invitation_id=invitation_id,
                        source_share_location=self.datashare_location,
                    )

                    share_subscription = (
                        self.datashare_client.share_subscriptions.create(
                            self.resource_group_name,
                            self.account_name,
                            share_name,
                            share_subscription_payload,
                        )
                    )
                else:
                    share_subscription = None
            except Exception:
                share_subscription = None

        return share_subscription

    def get_consumer_source_datashare(self, share_name: str) -> ConsumerSourceDataSet:
        """
        Get the ConsumerSourceDataset from the Share name
        """
        self.initialize()
        try:
            consumer_source_datashare = None
            consumer_source_datashare_list = self.datashare_client.consumer_source_data_sets.list_by_share_subscription(
                self.resource_group_name, self.account_name, share_name
            )
            consumer_source_datashare = next(consumer_source_datashare_list)
            for item in consumer_source_datashare_list:
                consumer_source_datashare = item
                return consumer_source_datashare
        except Exception:
            consumer_source_datashare = None
        return consumer_source_datashare

    def create_datashare_mapping(
        self,
        share_name: str,
        name: str,
        datashare_id: str,
        resource_group_name: str,
        storage_account_name: str,
        container_name: str,
        prefix: str,
    ) -> DataSetMapping:
        """
        Create a datashare mapping
        """
        self.initialize()

        try:

            datashare_mapping = self.datashare_client.data_set_mappings.get(
                self.resource_group_name, self.account_name, share_name, name
            )
        except Exception as ex:
            datashare_mapping = None
            if ex.status_code == 404:

                datashare_mapping_payload = BlobDataSetMapping(
                    data_set_id=datashare_id,
                    container_name=container_name,
                    file_path=prefix,
                    resource_group=resource_group_name,
                    storage_account_name=storage_account_name,
                    subscription_id=self.subscription_id,
                )
                datashare_mapping = self.datashare_client.data_set_mappings.create(
                    self.resource_group_name,
                    self.account_name,
                    share_name,
                    name,
                    datashare_mapping_payload,
                )
        return datashare_mapping

    def launch_synchronize(self, share_name: str) -> ShareSubscriptionSynchronization:
        """
        Launch the synchronization to received the shared dataset
        using the share name
        """
        self.initialize()

        try:
            self.datashare_client.share_subscriptions.begin_synchronize(
                self.resource_group_name,
                self.account_name,
                share_name,
                Synchronize(synchronization_mode="FullSync"),
            )
            share_subscription_synchronization = self.get_synchronize(share_name)
        except Exception as ex:
            if ex.status_code == 409:
                share_subscription_synchronization = self.get_synchronize(share_name)
            else:
                share_subscription_synchronization = None
        return share_subscription_synchronization

    def get_synchronize(self, share_name: str) -> ShareSubscriptionSynchronization:
        """
        Get the current synchronization for the share name
        """
        self.initialize()

        try:
            list_synchronization = (
                self.datashare_client.share_subscriptions.list_synchronizations(
                    self.resource_group_name, self.account_name, share_name
                )
            )
            synchronization = next(list_synchronization)

        except Exception:
            synchronization = None
        return synchronization

    def create_share_response(
        self,
        provider_node_id: str,
        consumer_node_id: str,
        invitation_id: str,
        invitation_name: str,
        datashare_storage_resource_group_name: str,
        datashare_storage_account_name: str,
        datashare_storage_container_name: str,
        datashare_storage_folder_path: str,
        datashare_storage_file_name: str,
        invitation_status: Status,
        invitation_date: datetime,
        error_code: int,
        error_message: str,
    ) -> ShareResponse:
        """
        Create a ShareResponse using the input parameters
        """

        error = Error(
            code=error_code,
            message=error_message,
            source="share_rest_api",
            date=datetime.utcnow(),
        )

        if invitation_status == Status.FAILED or invitation_status == Status.SUCCEEDED:
            status = StatusDetails(
                status=invitation_status,
                start=invitation_date,
                end=datetime.utcnow(),
                duration=0,
            )
        else:
            status = StatusDetails(
                status=invitation_status,
                start=invitation_date,
                end=invitation_date,
                duration=0,
            )

        dataset = Dataset(
            resource_group_name=datashare_storage_resource_group_name,
            storage_account_name=datashare_storage_account_name,
            container_name=datashare_storage_container_name,
            folder_path=datashare_storage_folder_path,
            file_name=datashare_storage_file_name,
        )

        share_response = ShareResponse(
            invitation_id=invitation_id,
            invitation_name=invitation_name,
            provider_node_id=provider_node_id,
            consumer_node_id=consumer_node_id,
            dataset=dataset.dict(),
            status=status.dict(),
            error=error.dict(),
        )
        return share_response

    def create_consume_response(
        self,
        provider_node_id: str,
        consumer_node_id: str,
        invitation_id: str,
        datashare_storage_resource_group_name: str,
        datashare_storage_account_name: str,
        datashare_storage_container_name: str,
        datashare_storage_folder_path: str,
        datashare_storage_file_name: str,
        status: Status,
        status_start_date: datetime,
        status_end_date: datetime,
        status_duration_in_ms: int,
        error_code: int,
        error_message: str,
    ) -> ConsumeResponse:
        """
        Create a ConsumeResponse using the input parameters
        """

        error = Error(
            code=error_code,
            message=error_message,
            source="share_rest_api",
            date=datetime.utcnow(),
        )

        status = StatusDetails(
            status=status,
            start=status_start_date,
            end=status_end_date,
            duration=status_duration_in_ms,
        )

        dataset = Dataset(
            resource_group_name=datashare_storage_resource_group_name,
            storage_account_name=datashare_storage_account_name,
            container_name=datashare_storage_container_name,
            folder_path=datashare_storage_folder_path,
            file_name=datashare_storage_file_name,
        )

        consume_response = ConsumeResponse(
            invitation_id=invitation_id,
            provider_node_id=provider_node_id,
            consumer_node_id=consumer_node_id,
            dataset=dataset.dict(),
            status=status.dict(),
            error=error.dict(),
        )
        return consume_response
