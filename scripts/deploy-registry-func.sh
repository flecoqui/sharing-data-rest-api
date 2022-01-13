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
deployAzureInfrastructure "arm-registry-func-template.json" $AZURE_SUBSCRIPTION_ID $AZURE_REGION $APP_NAME "EP1"

# Retrieve deployment outputs
# get ACR login server dns name
ACR_LOGIN_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrLoginServer.value')
# get WebApp Url
WEB_APP_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')
# get WebApp Name
WEB_APP_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppName.value')
# get Storage Account Name
STORAGE_ACCOUNT_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.storageAccountName.value')
# get Service Plan Name
APP_SERVICE_PLAN=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.appServicePlanName.value')

# get ACR Name
ACR_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.acrName.value')
# get WebApp Tenant ID
WEB_APP_TENANT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppTenantId.value')
# get WebApp Object ID
WEB_APP_OBJECT_ID=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppObjectId.value')

printMessage "Azure Container Registry DNS name: ${ACR_LOGIN_SERVER}"
printMessage "Azure Web App Url: ${WEB_APP_SERVER}"


printMessage "Deployment successfully done"