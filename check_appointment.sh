#!/bin/bash
BASH_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $BASH_DIR
source ./env/bin/activate
source ./.visa_credentials

USER_NAME=$VISA_USER_EMAIL PASSWORD=$VISA_USER_PASSWORD VISA_CENTRE=$VISA_CENTRE python ./checker.py >> ./log/visa_checker.log
