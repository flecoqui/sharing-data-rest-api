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

RESOURCE_GROUP="rg${APP_NAME}"
DEPLOYMENT_NAME=$(getDeploymentName $AZURE_SUBSCRIPTION_ID $RESOURCE_GROUP 'webAppName')
checkVariable "Variable DEPLOYMENT_NAME not define" $DEPLOYMENT_NAME 


# Retrieve deployment outputs
REGISTRY_URL=$2
ACR_LOGIN_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrLoginServer.value')
WEB_APP_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')
ACR_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrName.value')
WEB_APP_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppName.value')
WEB_APP_TENANT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppTenantId.value')
WEB_APP_OBJECT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppObjectId.value')
STORAGE_ACCOUNT_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.storageAccountName.value')
CONSUME_CONTAINER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.consumeContainerName.value')
SHARE_CONTAINER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.shareContainerName.value')
DATASHARE_ACCOUNT_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.dataShareAccountName.value')
CONNECTION_STRING=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.storageAccountConnectionString.value')
INSTRUMENTATION_KEY=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.appInsightsInstrumentationKey.value')
APP_SERVICE_PLAN=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.appServicePlanName.value')

printMessage "Registry url: ${REGISTRY_URL}"
printMessage "Azure Resource Group: ${RESOURCE_GROUP}"
printMessage "Azure Container Registry DNS name: ${ACR_LOGIN_SERVER}"
printMessage "Azure Web App Url: ${WEB_APP_SERVER}"
printMessage "Azure Datashare: ${DATASHARE_ACCOUNT_NAME}"
printMessage "Azure Storage: ${STORAGE_ACCOUNT_NAME}"
printMessage "Azure Share Container: ${SHARE_CONTAINER}"
printMessage "Azure Consume Container: ${CONSUME_CONTAINER}"
printMessage "Azure Tenant Id: ${WEB_APP_TENANT_ID}"
printMessage "Azure App Service Identity: ${WEB_APP_OBJECT_ID}"

# Deploy share_rest_api
printMessage "Deploy containers from Azure Container Registry ${ACR_LOGIN_SERVER}"
tmp_dir=$(mktemp -d -t env-XXXXXXXXXX)
cat << EOF > ${tmp_dir}/share-settings.conf
[
{ "name":"AZURE_SUBSCRIPTION_ID", "value":"${AZURE_SUBSCRIPTION_ID}"}, 
{ "name":"AZURE_TENANT_ID", "value":"${AZURE_TENANT_ID}"}, 
{ "name":"APP_VERSION", "value":"${APP_VERSION}"}, 
{ "name":"PORT_HTTP", "value":"80"},
{ "name":"WEBSITES_PORT", "value":"80"}, 
{ "name":"REFRESH_PERIOD", "value":"60"},
{ "name":"REGISTRY_URL_LIST", "value":"[\"${REGISTRY_URL}\"]"},
{ "name":"NODE_ID", "value":"${APP_PREFIX}"},
{ "name":"NODE_NAME", "value":"${APP_PREFIX}"},
{ "name":"NODE_URL", "value":"https://${WEB_APP_SERVER}"},
{ "name":"NODE_IDENTITY", "value":"${WEB_APP_OBJECT_ID}"},
{ "name":"DATASHARE_ACCOUNT_NAME", "value":"${DATASHARE_ACCOUNT_NAME}"},
{ "name":"DATASHARE_RESOURCE_GROUP_NAME", "value":"${RESOURCE_GROUP}"},
{ "name":"DATASHARE_STORAGE_RESOURCE_GROUP_NAME", "value":"${RESOURCE_GROUP}"},
{ "name":"DATASHARE_STORAGE_ACCOUNT_NAME", "value":"${STORAGE_ACCOUNT_NAME}"},
{ "name":"DATASHARE_STORAGE_CONSUME_CONTAINER_NAME", "value":"${CONSUME_CONTAINER}"},
{ "name":"DATASHARE_STORAGE_CONSUME_FILE_NAME_FORMAT", "value":"output-00001.csv"},
{ "name":"DATASHARE_STORAGE_CONSUME_FOLDER_FORMAT", "value":"consume/{node_id}/{invitation_id}/dataset-{date}"},
{ "name":"DATASHARE_STORAGE_SHARE_CONTAINER_NAME", "value":"${SHARE_CONTAINER}"},
{ "name":"DATASHARE_STORAGE_SHARE_FILE_NAME_FORMAT", "value":"input-00001.csv"},
{ "name":"DATASHARE_STORAGE_SHARE_FOLDER_FORMAT", "value":"share/{node_id}/dataset-{date}"}
]
EOF
deployWebAppContainerConfigFromFile "${AZURE_SUBSCRIPTION_ID}" "${APP_NAME}" "${ACR_LOGIN_SERVER}" "${ACR_NAME}"  "share_rest_api_func" "latest" "${tmp_dir}/share-settings.conf" "functionapp"
checkError

# updating the configuration
cmd="az functionapp create --name ${WEB_APP_NAME} --storage-account ${STORAGE_ACCOUNT_NAME} --resource-group ${RESOURCE_GROUP} --plan ${APP_SERVICE_PLAN} --deployment-container-image-name ${ACR_LOGIN_SERVER}/share_rest_api_func:latest --functions-version 3"
printProgress "$cmd"
eval "$cmd"

# updating the configuration
printProgress "Add Application Config"
cmd="az functionapp config appsettings set -g "${RESOURCE_GROUP}" -n "${WEB_APP_NAME}" \
--settings @"${tmp_dir}/share-settings.conf" --output none"
printProgress "$cmd"
eval "$cmd"


# Test share_rest_api
share_rest_api_url="https://${WEB_APP_SERVER}/version"
datetime=$(date +"%y/%m/%d-%H:%M:%S")
printMessage "Testing share_rest_api url: $share_rest_api_url at $datetime expected version: ${APP_VERSION}"
result=$(checkUrl "${share_rest_api_url}" "${APP_VERSION}" 420)
if [[ "${result}" != "true" ]]; then
    printError "Error while testing share_rest_api"
else
    printMessage "Testing share_rest_api successful"
fi

printMessage "Deployment successfully done"