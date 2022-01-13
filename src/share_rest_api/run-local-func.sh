#!/bin/bash
set -e
# Read variables in configuration file
parent_path=$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../../"
    pwd -P
)

export PORT_HTTP=7000
export APP_VERSION=$(date +"%y%M%d.%H%M%S")
echo "PORT_HTTP $PORT_HTTP"
echo "APP_VERSION $APP_VERSION"
pushd "$(dirname "${BASH_SOURCE[0]}")/func" > /dev/null
cp ../src/shared_code/app.py ./shared_code/app.py
cp ../src/shared_code/configuration_service.py ./shared_code/configuration_service.py
cp ../src/shared_code/log_service.py ./shared_code/log_service.py
cp ../src/shared_code/models.py ./shared_code/models.py
cp ../src/shared_code/share_service.py ./shared_code/share_service.py
cp ../src/shared_code/datashare_service.py ./shared_code/datashare_service.py
func start
popd > /dev/null
