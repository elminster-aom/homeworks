#!/usr/bin/env bash

#MY_HOME=$(readlink -e $(dirname ${0})/..)
MY_HOME=$(dirname ${0})/..
RESULT=1
LOG=${MY_HOME}/var/integration_test.log

if [[ -f ${MY_HOME}/.env ]]; then
    source ${MY_HOME}/.env
	> ${LOG}

    echo "Start sinking data"
    ${MY_HOME}/sink_connector.py > ${LOG} 2>&1 &
    sink_connector_PID=${!}
    echo "PID: ${sink_connector_PID}"

    sleep 10

    echo "Start monitoring web pages"
    ${MY_HOME}/web_monitor_agent.py > ${LOG} 2>&1 &
    web_monitor_agent_PID=${!}
    echo "PID: ${web_monitor_agent_PID}"

    echo "Wait 1 minute, to ensure data is being generated and collected in DB"
    sleep 60

    echo "Kill background processes"
    pkill -f web_monitor_agent.py
    pkill -f sink_connector.py

    sleep 10

    echo "Validate metrics were stored in DB"
    psql_OUT=$(psql ${POSTGRES_URI} \
        --csv \
        --quiet \
        --tuples-only \
        --command "SELECT * FROM web_health_metrics WHERE time > NOW() - INTERVAL '75 seconds' ORDER BY time DESC;")

    if [[ $(echo "${psql_OUT}" | wc -l) -gt 1 ]]; then
        echo "data colected:"
        echo "${psql_OUT}"
        echo "Test passed succesfully!"
        RESULT=0
    else
        echo "Failed test! Recent data not available"
    fi
else
    echo "Fire ${MY_HOME}/.env not found or not readable"
fi

echo "Application logs can be found on ${LOG}"
exit ${RESULT}
