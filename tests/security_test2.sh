#!/usr/bin/env bash

#MY_HOME=$(readlink -e $(dirname ${0})/..)
MY_HOME=$(dirname ${0})/..
RESULT=1
EXCPECTED_VALUE_1='-r--------'
EXCPECTED_VALUE_2='-rw-------'

access_rights_validation() {
    local _RESULT=1
    local FILE_CHECKED=${1}
	local FILE_NAME=$(basename ${1})

    if [[ -f ${FILE_CHECKED} ]]; then
        ACCESS_RIGTHS=$(stat ${FILE_CHECKED} | awk '{print $3}')
    fi
    if [[ ! -a ${FILE_CHECKED} ]] \
    || [[ ${ACCESS_RIGTHS} == ${EXCPECTED_VALUE_1} ]] \
    || [[ ${ACCESS_RIGTHS} == ${EXCPECTED_VALUE_2} ]]; then
        echo "File ${FILE_CHECKED} not crated or its access rights are OK"
        # ${FILE_NAME} must be inventariated in .gitignore
        if grep -q "${FILE_NAME}" ${MY_HOME}/.gitignore; then
            echo "${FILE_NAME} is ignored by Git, it's OK"
            _RESULT=0
        else
            echo "Git is tracking ${FILE_NAME}, it cannot be found in .gitignore; it's NOOK"
        fi
    else
        echo "File access rights for ${FILE_CHECKED} are NOOK, expected values are: '${EXCPECTED_VALUE_1}' or '${EXCPECTED_VALUE_2}'"
    fi

    return ${_RESULT}
}

if [[ -f ${MY_HOME}/.env ]]; then
    source ${MY_HOME}/.env
else
    # If .env not present, we load default values
    KAFKA_ACCESS_KEY=service.key
    KAFKA_ACCESS_CERTIFICATE=service.cert
fi

if access_rights_validation ${KAFKA_ACCESS_KEY} ; then
    if access_rights_validation ${KAFKA_ACCESS_CERTIFICATE}; then
        RESULT=0
    fi
fi

exit ${RESULT}
