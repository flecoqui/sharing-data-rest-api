#!/bin/bash
#
# executable
#

set -e
# Read variables in configuration file
parent_path=$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../"
    pwd -P
)
SCRIPTS_DIRECTORY=`dirname $0`
source "$SCRIPTS_DIRECTORY"/common.sh

env_path=$1
if [[ -z $env_path ]]; then
    env_path="$(dirname "${BASH_SOURCE[0]}")/../configuration/.default.env"
fi

if [[ $env_path ]]; then
    if [ ! -f "$env_path" ]; then
        printError "$env_path does not exist."
        exit 1
    fi
    set -o allexport
    source "$env_path"
    set +o allexport
else
    printWarning "No env. file specified. Using environment variables."
fi

# Check Variables
checkVariables
checkError

# Check Azure connection
printMessage "Check Azure connection for subscription: '$AZURE_SUBSCRIPTION_ID'"
azLogin
checkError

# Deploy infrastructure image
printMessage "Deploy infrastructure subscription: '$AZURE_SUBSCRIPTION_ID' region: '$AZURE_REGION' prefix: '$APP_NAME' sku: 'EP1'"
deployAzureInfrastructure "arm-share-func-template.json" $AZURE_SUBSCRIPTION_ID $AZURE_REGION $APP_NAME "EP1"

# Retrieve deployment outputs
ACR_LOGIN_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrLoginServer.value')
WEB_APP_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')
WEB_APP_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppName.value')
ACR_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrName.value')
WEB_APP_TENANT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppTenantId.value')
WEB_APP_OBJECT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppObjectId.value')
STORAGE_ACCOUNT_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.storageAccountName.value')
CONSUME_CONTAINER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.consumeContainerName.value')
SHARE_CONTAINER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.shareContainerName.value')
DATASHARE_ACCOUNT_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.dataShareAccountName.value')
APP_SERVICE_PLAN=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.appServicePlanName.value')

printMessage "Azure Resource Group: ${RESOURCE_GROUP}"
printMessage "Azure Container Registry DNS name: ${ACR_LOGIN_SERVER}"
printMessage "Azure Web App Url: ${WEB_APP_SERVER}"
printMessage "Azure Datashare: ${DATASHARE_ACCOUNT_NAME}"
printMessage "Azure Storage: ${STORAGE_ACCOUNT_NAME}"
printMessage "Azure Share Container: ${SHARE_CONTAINER}"
printMessage "Azure Consume Container: ${CONSUME_CONTAINER}"
printMessage "Azure Tenant Id: ${WEB_APP_TENANT_ID}"
printMessage "Azure App Service Identity: ${WEB_APP_OBJECT_ID}"

printProgress  "Checking role 'Contributor' for App Service ${WEB_APP_SERVER} on datashare ${DATASHARE_ACCOUNT_NAME}..."
appServicePrincipalId=$(az webapp identity show --name "${WEB_APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query "principalId" --output tsv)
roleAssignmentCount=$(az role assignment list --assignee ${appServicePrincipalId} --scope "/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.DataShare/accounts/${DATASHARE_ACCOUNT_NAME}" | jq -r 'select(.[].roleDefinitionName=="Contributor") | length')
if [ "${roleAssignmentCount}" != "1" ];
then
    printProgress  "Assigning 'Storage Blob Data Reader' role for App Service ${WEB_APP_SERVER} on datashare ${DATASHARE_ACCOUNT_NAME}..."
    printWarning  "It can sometimes take up to 30 minutes to take into account the new role assignment"
    cmd="az role assignment create --assignee-object-id \"${appServicePrincipalId}\" --assignee-principal-type ServicePrincipal --scope \"/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.DataShare/accounts/${DATASHARE_ACCOUNT_NAME}\" --role \"Contributor\" --output none"
    printProgress "$cmd"
    eval "$cmd"
fi

printProgress  "Checking role 'Storage Account Contributor' for App Service ${WEB_APP_SERVER} on storage ${STORAGE_ACCOUNT_NAME}..."
appServicePrincipalId=$(az webapp identity show --name "${WEB_APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query "principalId" --output tsv)
roleAssignmentCount=$(az role assignment list --assignee ${appServicePrincipalId} --scope "/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME}" | jq -r 'select(.[].roleDefinitionName=="Storage Account Contributor") | length')
if [ "${roleAssignmentCount}" != "1" ];
then
    printProgress  "Assigning 'Storage Account Contributor' role for App Service ${WEB_APP_SERVER} on storage ${STORAGE_ACCOUNT_NAME}..."
    printWarning  "It can sometimes take up to 30 minutes to take into account the new role assignment"
    cmd="az role assignment create --assignee-object-id \"${appServicePrincipalId}\" --assignee-principal-type ServicePrincipal --scope \"/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME}\" --role \"Storage Account Contributor\" --output none"
    printProgress "$cmd"
    eval "$cmd"
fi

printProgress  "Checking role 'Storage Blob Data Contributor' for Datashare Account ${DATASHARE_ACCOUNT_NAME} on storage ${STORAGE_ACCOUNT_NAME}..."
datasharePrincipalId=$(az datashare account show --resource-group "${RESOURCE_GROUP}" --name "${DATASHARE_ACCOUNT_NAME}" --subscription "${AZURE_SUBSCRIPTION_ID}" --query "identity.principalId" --output tsv)
roleAssignmentCount=$(az role assignment list --assignee ${datasharePrincipalId} --scope "/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME}" | jq -r 'select(.[].roleDefinitionName=="Storage Blob Data Contributor") | length')
if [ "${roleAssignmentCount}" != "1" ];
then
    printProgress  "Assigning 'Storage Blob Data Contributor' role for Datashare Account ${DATASHARE_ACCOUNT_NAME} on storage ${STORAGE_ACCOUNT_NAME}..."
    printWarning  "It can sometimes take up to 30 minutes to take into account the new role assignment"
    cmd="az role assignment create --assignee-object-id \"${datasharePrincipalId}\" --assignee-principal-type ServicePrincipal --scope \"/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME}\" --role \"Storage Blob Data Contributor\" --output none"
    printProgress "$cmd"
    eval "$cmd"
fi


printMessage "Deployment successfully done"