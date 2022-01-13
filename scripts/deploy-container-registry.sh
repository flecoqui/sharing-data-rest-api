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
ACR_LOGIN_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrLoginServer.value')
WEB_APP_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')
ACR_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrName.value')
WEB_APP_TENANT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppTenantId.value')
WEB_APP_OBJECT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppObjectId.value')

printMessage "Azure Container Registry DNS name: ${ACR_LOGIN_SERVER}"
printMessage "Azure Web App Url: ${WEB_APP_SERVER}"

# Deploy registry_rest_api
printMessage "Deploy containers from Azure Container Registry ${ACR_LOGIN_SERVER}"
tmp_dir=$(mktemp -d -t env-XXXXXXXXXX)
cat << EOF > ${tmp_dir}/registry-settings.conf
[
{ "name": "APP_VERSION", "value":"${APP_VERSION}"}, 
{ "name": "PORT_HTTP", "value":"${APP_PORT}"},
{ "name": "WEBSITES_PORT", "value":"${APP_PORT}"}, 
{ "name": "REFRESH_PERIOD", "value":"120"},
{ "name": "SHARE_NODE_LIST", "value":"[]"}
]
EOF
deployWebAppContainerConfigFromFile "${AZURE_SUBSCRIPTION_ID}" "${APP_NAME}" "${ACR_LOGIN_SERVER}" "${ACR_NAME}"  "registry_rest_api" "latest" "${tmp_dir}/registry-settings.conf" "webapp"
checkError

# Test registry_rest_api
registry_rest_api_url="https://${WEB_APP_SERVER}/version"
datetime=$(date +"%y/%m/%d-%H:%M:%S")
printMessage "Testing registry_rest_api url: $registry_rest_api_url at $datetime expected version: ${APP_VERSION}"
result=$(checkUrl "${registry_rest_api_url}" "${APP_VERSION}" 420)
if [[ $result != "true" ]]; then
    printError "Error while testing registry_rest_api"
else
    printMessage "Testing registry_rest_api successful"
fi

printMessage "Deployment successfully done"