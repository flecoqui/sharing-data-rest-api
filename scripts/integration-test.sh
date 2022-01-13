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

printMessage "Integration tests with this envrionment file ${env_path}"

printMessage "Deploy Registry infrastructure"
"$SCRIPTS_DIRECTORY"/deploy-registry.sh  "$SCRIPTS_DIRECTORY"/../configuration/.registry.env
printMessage "Deploy Share node 1 infrastructure"
"$SCRIPTS_DIRECTORY"/deploy-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env
printMessage "Deploy Share node 2 infrastructure"
"$SCRIPTS_DIRECTORY"/deploy-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env

printMessage "Build and Deploy Registry REST API"
"$SCRIPTS_DIRECTORY"/build-container-registry.sh  "$SCRIPTS_DIRECTORY"/../configuration/.registry.env
"$SCRIPTS_DIRECTORY"/deploy-container-registry.sh  "$SCRIPTS_DIRECTORY"/../configuration/.registry.env

# Retrieve Registry URL from deployment
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.registry.env | grep  APP_NAME | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.registry.env | grep  AZURE_SUBSCRIPTION_ID | sed "s/\"//g")
RESOURCE_GROUP="rg${APP_NAME}"
DEPLOYMENT_NAME=$(getDeploymentName $AZURE_SUBSCRIPTION_ID $RESOURCE_GROUP 'webAppName')
checkVariable "Variable DEPLOYMENT_NAME not define" $DEPLOYMENT_NAME 

REGISTRY_APP_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')

printMessage "Build and Deploy share REST API"
"$SCRIPTS_DIRECTORY"/build-container-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env
"$SCRIPTS_DIRECTORY"/deploy-container-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env "https://${REGISTRY_APP_SERVER}"

printMessage "Build and Deploy share REST API"
"$SCRIPTS_DIRECTORY"/build-container-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env
"$SCRIPTS_DIRECTORY"/deploy-container-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env  "https://${REGISTRY_APP_SERVER}"

printMessage "Getting the input parameters to test the REST APIs"
# Retrieve parameters for the tests 
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env | grep  APP_NAME | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env | grep  APP_PREFIX | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env | grep  AZURE_SUBSCRIPTION_ID | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env | grep  AZURE_TENANT_ID | sed "s/\"//g")
RESOURCE_GROUP="rg${APP_NAME}"
DEPLOYMENT_NAME=$(getDeploymentName $AZURE_SUBSCRIPTION_ID $RESOURCE_GROUP 'webAppName')
checkVariable "Variable DEPLOYMENT_NAME not define" $DEPLOYMENT_NAME 

SHARE_APP_SERVER_A=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')
STORAGE_ACCOUNT_NAME_A=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.storageAccountName.value')
CONSUME_CONTAINER_A=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.consumeContainerName.value')
SHARE_CONTAINER_A=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.shareContainerName.value')
RESOURCE_GROUP_A="${RESOURCE_GROUP}"
NODE_NAME_A="${APP_PREFIX}"
AZURE_SUBSCRIPTION_ID_A="${AZURE_SUBSCRIPTION_ID}"
AZURE_TENANT_ID_A="${AZURE_TENANT_ID}"


export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env | grep  APP_NAME | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env | grep  APP_PREFIX | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env | grep  AZURE_SUBSCRIPTION_ID | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env | grep  AZURE_TENANT_ID | sed "s/\"//g")
RESOURCE_GROUP="rg${APP_NAME}"
DEPLOYMENT_NAME=$(getDeploymentName $AZURE_SUBSCRIPTION_ID $RESOURCE_GROUP 'webAppName')
checkVariable "Variable DEPLOYMENT_NAME not define" $DEPLOYMENT_NAME 

SHARE_APP_SERVER_B=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')
STORAGE_ACCOUNT_NAME_B=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.storageAccountName.value')
CONSUME_CONTAINER_B=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.consumeContainerName.value')
SHARE_CONTAINER_B=$(az deployment group show --resource-group $RESOURCE_GROUP  --subscription $AZURE_SUBSCRIPTION_ID  -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.shareContainerName.value')
RESOURCE_GROUP_B="${RESOURCE_GROUP}"
NODE_NAME_B="${APP_PREFIX}"
AZURE_SUBSCRIPTION_ID_B="${AZURE_SUBSCRIPTION_ID}"
AZURE_TENANT_ID_B="${AZURE_TENANT_ID}"

export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.registry.env | grep  APP_NAME | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.registry.env | grep  AZURE_SUBSCRIPTION_ID | sed "s/\"//g")
export $(cat "$SCRIPTS_DIRECTORY"/../configuration/.registry.env | grep  AZURE_TENANT_ID | sed "s/\"//g")
RESOURCE_GROUP="rg${APP_NAME}"
DEPLOYMENT_NAME=$(getDeploymentName $AZURE_SUBSCRIPTION_ID $RESOURCE_GROUP 'webAppName')
checkVariable "Variable DEPLOYMENT_NAME not define" $DEPLOYMENT_NAME 

REGISTRY_APP_SERVER=$(az deployment group show --resource-group $RESOURCE_GROUP --subscription $AZURE_SUBSCRIPTION_ID -n $DEPLOYMENT_NAME | jq -r '.properties.outputs.webAppServer.value')

tmp_dir=$(mktemp -d -t env-XXXXXXXXXX)
cat << EOF > ${tmp_dir}/.test.env
# REGISTRY configuration
REGISTRY_APP_SERVER=${REGISTRY_APP_SERVER}
AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}
AZURE_TENANT_ID=${AZURE_TENANT_ID}

# NODE A configuration
AZURE_SUBSCRIPTION_ID_A=${AZURE_SUBSCRIPTION_ID_A}
AZURE_TENANT_ID_A=${AZURE_TENANT_ID_A}
SHARE_APP_SERVER_A=${SHARE_APP_SERVER_A}
RESOURCE_GROUP_A=${RESOURCE_GROUP_A}
STORAGE_ACCOUNT_NAME_A=${STORAGE_ACCOUNT_NAME_A}
CONSUME_CONTAINER_A=${CONSUME_CONTAINER_A}
SHARE_CONTAINER_A=${SHARE_CONTAINER_A}
SHARE_FOLDER_FORMAT_A="share/{node_id}/dataset-{date}"
NODE_NAME_A=${NODE_NAME_A}

# NODE B configuration
AZURE_SUBSCRIPTION_ID_B=${AZURE_SUBSCRIPTION_ID_B}
AZURE_TENANT_ID_B=${AZURE_TENANT_ID_B}
SHARE_APP_SERVER_B=${SHARE_APP_SERVER_B}
RESOURCE_GROUP_B=${RESOURCE_GROUP_B}
STORAGE_ACCOUNT_NAME_B=${STORAGE_ACCOUNT_NAME_B}
CONSUME_CONTAINER_B=${CONSUME_CONTAINER_B}
SHARE_CONTAINER_B=${SHARE_CONTAINER_B}
CONSUME_FOLDER_FORMAT_B="share/{node_id}/{invitation_id}/dataset-{date}"
NODE_NAME_B=${NODE_NAME_B}
EOF
printMessage "Input parameters in file: '${tmp_dir}/.test.env'"

printProgress  "Checking role for current user on container ${SHARE_CONTAINER_A} in storage ${STORAGE_ACCOUNT_NAME_A}..."
currentObjectId=$(az ad signed-in-user show --query "objectId" --output tsv)
roleAssignmentCount=$(az role assignment list --assignee ${currentObjectId} --scope "/subscriptions/${AZURE_SUBSCRIPTION_ID_A}/resourceGroups/${RESOURCE_GROUP_A}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME_A}/blobServices/default/containers/${SHARE_CONTAINER_A}" | jq -r 'select(.[].roleDefinitionName=="Storage Blob Data Contributor") | length')
if [ "${roleAssignmentCount}" != "1" ];
then
    printProgress  "Assigning 'Storage Blob Data Contributor' role assignment on container ${SHARE_CONTAINER_A} in storage ${STORAGE_ACCOUNT_NAME_A}..."
    printWarning  "It can sometimes take up to 30 minutes to take into account the new role assignment"
    cmd="az role assignment create --assignee-object-id \"${currentObjectId}\" --assignee-principal-type User --scope \"/subscriptions/${AZURE_SUBSCRIPTION_ID_A}/resourceGroups/${RESOURCE_GROUP_A}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME_A}/blobServices/default/containers/${SHARE_CONTAINER_A}\" --role \"Storage Blob Data Contributor\" --output none"
    printProgress "$cmd"
    eval "$cmd"

fi
printProgress  "Checking role for current user on container ${CONSUME_CONTAINER_B} in storage ${STORAGE_ACCOUNT_NAME_B}..."
currentObjectId=$(az ad signed-in-user show --query "objectId" --output tsv)
roleAssignmentCount=$(az role assignment list --assignee ${currentObjectId} --scope "/subscriptions/${AZURE_SUBSCRIPTION_ID_B}/resourceGroups/${RESOURCE_GROUP_B}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME_B}/blobServices/default/containers/${CONSUME_CONTAINER_B}" | jq -r 'select(.[].roleDefinitionName=="Storage Blob Data Reader") | length')
if [ "${roleAssignmentCount}" != "1" ];
then
    printProgress  "Assigning 'Storage Blob Data Reader' role assignment on container ${SHARE_CONTAINER_B} in storage ${STORAGE_ACCOUNT_NAME_B}..."
    printWarning  "It can sometimes take up to 30 minutes to take into account the new role assignment"
    cmd="az role assignment create --assignee-object-id \"${currentObjectId}\" --assignee-principal-type User --scope \"/subscriptions/${AZURE_SUBSCRIPTION_ID_B}/resourceGroups/${RESOURCE_GROUP_B}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME_B}/blobServices/default/containers/${CONSUME_CONTAINER_B}\" --role \"Storage Blob Data Reader\" --output none"
    printProgress "$cmd"
    eval "$cmd"
fi


printMessage "Launch the tests of the REST APIs"
"$SCRIPTS_DIRECTORY"/launch-test-datashare.sh  "${tmp_dir}/.test.env"  "https://${REGISTRY_APP_SERVER}"

printMessage "Undeploy Registry infrastructure"
"$SCRIPTS_DIRECTORY"/undeploy-registry.sh  "$SCRIPTS_DIRECTORY"/../configuration/.registry.env
printMessage "Undeploy Share node 1 infrastructure"
"$SCRIPTS_DIRECTORY"/undeploy-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.sharea.env
printMessage "Undeploy Share node 2 infrastructure"
"$SCRIPTS_DIRECTORY"/undeploy-share.sh  "$SCRIPTS_DIRECTORY"/../configuration/.shareb.env

printMessage "Integration tests successfully done"