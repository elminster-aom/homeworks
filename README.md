# Homework - Web monitoring

## Homework description 
This application tries to resolve a hypothetical request, developing a monitor that:
1. Monitors website availability over network and collects:
* HTTP response time
* error code returned
* pattern that is expected to be found on the page
2. Produces corresponding metrics and passes these events through a [Kafka](https://kafka.apache.org/) instance into a [PostgreSQL](https://www.postgresql.org/) database

#### Scenario
* These components may run in different systems
* One or more database tables could handle a reasonable amount of checks performed over a longer period of time

## How it works
There are 2 main programs:
 * [web_monitor_agent.py](https://github.com/elminster-aom/homeworks/blob/main/docs/web_monitor_agent.md)
 * [sink_connector.py](https://github.com/elminster-aom/homeworks/blob/main/docs/sink_connector.md)

In addition, a 3rd program is responsible for initializing the environment:
 * [initialize_infra.py](https://github.com/elminster-aom/homeworks/blob/main/docs/initialize_infra.md)

### web_monitor_agent.py
This component is designed in a way that allows several copies of it run as processes on the same or several independent systems. Each process creates a bunch of threads which monitor the listed URLs (1 threads monitors 5 URLs). All threads publish to the same Kafka topic.

:information_source: The numbers of URLs monitored by thread (5) are tuned based on the _HTTP GET_ request timeout (15 seconds). If 4 of URLs assigned to a thread suffer timeouts, the 5th doesn't get its next monitoring check delayed (e.g.: 5 URLs * 15 max. time check = 60 seconds == `MONITORING_RETRY_SECS=60`). 

Note: Its main restriction is max. number of open sockets.
 
### sink_connector.py
This component is designed thinking of performance. Since its code is not Threadsafe, see [kafka-python -- Project description](https://pypi.org/project/kafka-python/):
> **Thread safety**

> The KafkaProducer can be used across threads without issue, unlike the KafkaConsumer which cannot.
> 
> While it is possible to use the KafkaConsumer in a thread-local manner, multiprocessing is recommended.

it has been implemented as a mono-thread which intensifies memory usage for a better performance.

Therefore, it consumes Kafka messages in windows of either time or number of messages and stores them in group (as a batch) in a Postgres database, where transactional commit is disabled (we relax this setting since all our SQL operations are [ACID](https://en.wikipedia.org/wiki/ACID)). 

Additionally, performance can be further improved if both Kafka and Postgres components work independently in a continuous stream of data, for example using `Store_manager.insert_metrics_copy()` and/or implementing shared memory ([mmap system call](https://man7.org/linux/man-pages/man2/mmap.2.html)).

On the other hand, for ensuring that our storage is optimized for metrics (time-series data) and can store them for long periods of time, we took profit of [TimescaleDB](https://docs.timescale.com/latest/introduction) plug-in, e.g:
> **Scalable**
> * _Transparent time/space partitioning_ for both scaling up (single node) and scaling out (forthcoming).
> * _High data write rates_ (including batched commits, in-memory indexes, transactional support, support for data backfill).
> * _Right-sized chunks_ (two-dimensional data partitions) on single nodes to ensure fast ingest even at large data sizes.
> * _Parallelized operations_ across chunks and servers.

### initialize_infra.py
It initializes the environment, creating the required resources on Kafka and Postgres services.

### How to install
1. Clone or download a ZIP of this project, e.g.:
```shell
$ git clone git@github.com:elminster-aom/homeworks.git
```
2. Ensure that you have the right version of Python (v3.9, see below)
3. Create a Python Virtual Environment and install required packages, e.g.:
```shell
$ python3 -m venv homeworks \
&& source homeworks/bin/activate \
&& python3 -m pip install --requirement homeworks/requirements.txt
```

Further details on [Installing packages using pip and virtual environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments)

## How to set up and run
1. Create (if doesn't exist already) a Kafka and PostgresSQL service ([aiven.io] is an interesting option)
2. All available settings are based on an environment variables file in the home of our application. For its creation you can use this template: [env_example](https://github.com/elminster-aom/homeworks/blob/main/docs/env_example), e.g.:
```shell
$ wget https://github.com/elminster-aom/homeworks/blob/main/docs/env_example 
$ nano env_example
# For information of its parameters, see below
$ mv env_example .env
$ chmod 0600 .env
```
3. Run `initialize_infra.py` for initializing the infrastructure _\*_
```shell
$ ./initialize_infra.py
```
4. Start collecting metrics using `web_monitor_agent.py` _\*\*_
```shell
$ ./web_monitor_agent.py
```
5. Store them using `sink_connector.py` _\*\*_
```shell
$ ./sink_connector.py
```
_\*_ It needs to be run only once per environment, for initialization reasons

_\*\*_ They can run on the same server or different ones

## Local validation tests
They can be run like:
```shell
$ cd homeworks
$ source bin/activate

# Validate that infrastructure is properly created
$ python3 -m pytest tests.py

# Validate that all parts work together: URL monitoring, Kafka communication and DB storing
$ ./tests/integration_test.sh
```

### .env
* **_WORKSPACE_PATH**: Full path to the project (e.g.: `/home/user1/homeworks`)
* **KAFKA_ACCESS_CERTIFICATE**: Full path to the Kafka access certificate (e.g.: `${_WORKSPACE_PATH}/tests/service.cert`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Access Certificate_
IMPORTANT! (Although it's encrypted) Do not forget to set *service.cert* to read-only for file owner and exclude it from git repository.
* **KAFKA_ACCESS_KEY**: Full path to the Kafka access key (e.g.: `${_WORKSPACE_PATH}/tests/service.key`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Access Key_
IMPORTANT! Do not forget to set *service.key* to read-only for file owner and exclude it from git repository.
* **KAFKA_CA_CERTIFICATE**: Full path to the Kafka access certificate (e.g.: `${_WORKSPACE_PATH}/tests/ca.pem`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> CA Certificate_
* **KAFKA_HOST**: Kafka hostname (e.g.: `kafka.aivencloud.com`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Host_
* **KAFKA_PORT**: Kafka TCP listener port (e.g.: `2181`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Port_
* **KAFKA_TOPIC_NAME**: A unique string which identifies the Kafka topic for this application (e.g. `web_monitoring`)
* **MONITORING_LOG_LEVEL=INFO**: Log level in console, valid values: DEBUG, INFO, WARNING, ERROR and FATAL
* **MONITORING_RETRY_SECS**: How often *web_monitor_agent.py* will check the target URLs (in seconds) (e.g.: `60`)
* **MONITORING_TARGETS_PATH**:  Full path to text file with the target URLs, webs to monitor (e.g.: `${_WORKSPACE_PATH}/tests/list_web_domains.txt`)
* **MONITORING_TARGETS_REGEX**: String with a Regex expression *web_monitor_agent.py* will look for a match on HTTP GET request's body
* **POSTGRES_AUTOCOMMIT**: As documented before, this parameter must be set to `True` for performance reasons
* **POSTGRES_HOST**: PostgresSQL hostname (e.g.: `postgres.aivencloud.com`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> Host_
* **POSTGRES_USER**: PostgresSQL user (e.g.: `avnadmin`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> User_
* **POSTGRES_PASSWORD**: PostgresSQL password (e.g.: `p4ssW0rd1`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> Password_
* **POSTGRES_PORT**: PostgresSQL TCP listener port (e.g.: `5432`), available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> Port_
* **POSTGRES_SSL**: PostgresSQL SSL Mode Description (default: `require`). For a full list of values, check PostgresSQL [documentation](https://www.postgresql.org/docs/current/libpq-ssl.html#LIBPQ-SSL-SSLMODE-STATEMENTS)
* **POSTGRES_TABLE**: Name of a database hypertable for storing our web metrics (e.g.: `web_health_metrics`)

## Additional considerations
1. Only Unix-like systems are supported
2. The code has been tested with only these versions (different versions may work too but we cannot ensure it):
* Kafka 2.7.0
* PostgresSQL 13.2
* Python 3.9.4
* TimesacleDB 2.1
3. For a detailed list of Python modules check out the [requirements.txt](https://github.com/elminster-aom/homeworks/blob/main/requirements.txt). It can be used like:
```shell
pip3 install --requirement requirements.txt
```

## Areas of improvement
Review the list of [TODOs](https://github.com/elminster-aom/homeworks/blob/main/docs/TODOS.md)

## References
I would like to reference some useful information sources which have been crucial for the implementation of this solution and give thanks to their creators for their collaboration:
* [How Postgresql COPY TO STDIN With CSV do on conflic do update?](https://stackoverflow.com/a/48020691)
* [UPSERTs not working correctly #100,](https://github.com/timescale/timescaledb/issues/100)
* [Reference about enable_auto_commit=False](https://www.thebookofjoel.com/python-kafka-consumers)
* [except is not needed, if any it can be raised](https://www.reddit.com/r/learnpython/comments/45erlq/is_it_okay_to_use_tryfinally_without_except/czxk5bk?utm_source=share&utm_medium=web2x&context=3)
* [Reference about enable_auto_commit=False](https://www.thebookofjoel.com/python-kafka-consumers)
* [How to create tzinfo when I have UTC offset?](https://stackoverflow.com/a/28270767)
* [Fastest Way to Load Data Into PostgreSQL Using Python](https://hakibenita.com/fast-load-data-python-postgresql#copy-data-from-a-string-iterator-with-buffer-size)
* [Getting started with TimescaleDB in Aiven for PostgreSQL](https://help.aiven.io/en/articles/1752157-getting-started-with-timescaledb-in-aiven-for-postgresql)
* [3 Libraries You Should Know to Master Apache Kafka in Python](https://towardsdatascience.com/3-libraries-you-should-know-to-master-apache-kafka-in-python-c95fdf8700f2)
* [How to create topics if it does not exists in Kafka dynamically using kafka-python](https://stackoverflow.com/a/55494337)
* [Python Kafka Consumers: at-least-once, at-most-once, exactly-once](https://www.thebookofjoel.com/python-kafka-consumers)
