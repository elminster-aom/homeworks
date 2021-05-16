#!/usr/bin/env bash

RESULT=1
#MY_HOME=$(readlink -e $(dirname ${0})/..)
MY_HOME=$(dirname ${0})/..
EXCPECTED_VALUE_1='-r--------'
EXCPECTED_VALUE_2='-rw-------'
FILE_CHECKED="${MY_HOME}/.env"

if [[ -f ${FILE_CHECKED} ]]; then
    ACCESS_RIGTHS=$(stat ${FILE_CHECKED} | awk '{print $3}')
fi
if [[ ! -a ${FILE_CHECKED} ]] \
|| [[ ${ACCESS_RIGTHS} == ${EXCPECTED_VALUE_1} ]] \
|| [[ ${ACCESS_RIGTHS} == ${EXCPECTED_VALUE_2} ]]; then
    echo "File ${FILE_CHECKED} not crated or its access rights are OK"

    # .env must be inventariated in .gitignore
    if grep -q '\.env' ${MY_HOME}/.gitignore; then
        echo ".env is ignored by Git, it's OK"
        RESULT=0
    else
        echo "Git is tracking .env, it cannot be found in .gitignore; it's NOOK"
    fi
else
    echo "File access rights for ${FILE_CHECKED} are NOOK, expected values are: '${EXCPECTED_VALUE_1}' or '${EXCPECTED_VALUE_2}'"
fi

exit ${RESULT}
