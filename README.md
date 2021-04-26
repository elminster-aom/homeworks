# Homework - Web monitoring

## Homework description 
This applications tries to resolve a hypothetical request, developing a monitor that:
1. Monitors website availability over the network and collect:
* HTTP response time
* error code returned
* pattern that is expected to be found on the page
2. Produces metrics about this and passes these events through an [Kafka](https://kafka.apache.org/) instance into a [PostgreSQL](https://www.postgresql.org/) database

#### Scenario:
* These components may run in different systems
* One or more database tables and could handle a reasonable amount of checks performed over a longer period of time

## How it works
Two main programs are created:
 * [web_monitor_agent.py](https://github.com/elminster-aom/homeworks/blob/main/docs/web_monitor_agent.md)
 * [sink_connector.py](https://github.com/elminster-aom/homeworks/blob/main/docs/sink_connector.md)

In addition, a 3rd program is responsible of initialization the environment:
 * [setup.py](https://github.com/elminster-aom/homeworks/blob/main/docs/setup.md)

### web_monitor_agent.py
This component is designed so that several copies of it (processes) can run on the same or several independent systems, every process creates a bunch of threads which will monitor the listed URLs (1 threads monitors 1 URL). All threads publish to same Kafka topic

Note: Its main restriction is max. open sockets
 
### sink_connector.py
This component is designed thinking in performance. Since its code is not Threadsafe, see [kafka-python -- Project description](https://pypi.org/project/kafka-python/):
> **Thread safety**

> The KafkaProducer can be used across threads without issue, unlike the KafkaConsumer which cannot.
> 
> While it is possible to use the KafkaConsumer in a thread-local manner, multiprocessing is recommended.

Base on previous restriction, it is implemented as a mono-thread wich it intensives memory usage for a better performance.

Therefore, it consumes Kafka messages in windows of either time or number of messages and store them (all of them at ones) in a Postgres database, where transactional commit is disabled (We relax this setting because all our SQL operation are [ACID](https://en.wikipedia.org/wiki/ACID)). 

Additionally, performance could be improved further if both Kafka and Postgres components work independently in a continuous stream of data, for example using shared memory ([mmap system call](https://man7.org/linux/man-pages/man2/mmap.2.html)).

On the other hand, for ensuring that our storage is optimized for metrics (time-series data) and it can store them for long periods time, we took profit of [TimescaleDB](https://docs.timescale.com/latest/introduction) plug-in, e.g:
> **Scalable**
> * _Transparent time/space partitioning_ for both scaling up (single node) and scaling out (forthcoming).
> * _High data write rates_ (including batched commits, in-memory indexes, transactional support, support for data backfill).
> * _Right-sized chunks_ (two-dimensional data partitions) on single nodes to ensure fast ingest even at large data sizes.
> * _Parallelized operations_ across chunks and servers.

### setup.py
It initializes the environment, creating the required resources on Kafka and Postgres services.

### How to install
1. Clone or download as a ZIP this project
2. Ensure you have the right version of Python, see below
3. Enable Python Virtual Environment, e.g.:
```shell
$ source bin/activate
```

## How to set up and run
1. Create (if doesn't exist already) a Kafka and PostgresSQL service ([aiven.io] is an interesting option)
2. All available settings are based on an environment variables file, on the home of our application. For its creation, you can use this template: [env_example](https://github.com/elminster-aom/homeworks/blob/main/docs/env_example), e.g.:
```shell
$ wget https://github.com/elminster-aom/homeworks/blob/main/docs/env_example 
$ nano env_example
# For information of its parameters, see below
$ mv env_example .env
$ chmod 0600 .env
```
3. Run `setup.py` for initializing the infrastructure _\*_
```shell
$ ./setup.py
```
4. Start collecting metrics, using `web_monitor_agent.py` _\*\*_
```shell
$ ./web_monitor_agent.py
```
5. Store them using `sink_connector.py` _\*\*_
```shell
$ ./sink_connector.py
```
_\*_ It needs to be run only once per environment, for initialization reasons.

_\*\*_ They can run in same server or different ones

### .env
* **_WORKSPACE_PATH**: Full path to the project (e.g.: `/home/user1/homeworks`)
* **KAFKA_ACCESS_CERTIFICATE**: Full path to Kafka's access certificate (e.g.: `${_WORKSPACE_PATH}/tests/service.cert`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Access Certificate_
IMPORTANT! (Although it's encrypted) Do not forget to set *service.cert* to read-only for file owner and exclue it from git repository.
* **KAFKA_ACCESS_KEY**: Full path to Kafka's access certificate (e.g.: `${_WORKSPACE_PATH}/tests/service.key`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Access Key_
IMPORTANT! Do not forget to set *service.key* to read-only for file owner and exclue it from git repository.
* **KAFKA_CA_CERTIFICATE**: Full path to Kafka's access certificate (e.g.: `${_WORKSPACE_PATH}/tests/ca.pem`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> CA Certificate_
* **KAFKA_HOST**: Kafka's hostname (e.g.: `kafka.aivencloud.com`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Host_
* **KAFKA_PORT**: Kafka's TCP listener port (e.g.: `2181`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your Kafka\> -> Overview -> Port_
* **KAFKA_TOPIC_NAME**: A unique string, which identifies the Kafka's Topic for this application (e.g. `web_monitoring`)
* **MONITORING_RETRY_SECS**: How often, *web_monitor_agent.py* will check the target URLs (in seconds) (e.g.: `60`)
* **MONITORING_TARGETS_PATH**:  Full path to text file with the target URLs, webs to monitor (e.g.: `${_WORKSPACE_PATH}/tests/list_web_domains.txt`)
* **MONITORING_TARGETS_REGEX**: String with a Regex expression, *web_monitor_agent.py* will look for a match on HTTP GET request's Body
* **POSTGRES_AUTOCOMMIT**: As documented before, this parameter must be set `True` for performance reasons
* **POSTGRES_HOST**: PostgresSQL's hostname (e.g.: `postgres.aivencloud.com`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> Host_
* **POSTGRES_USER**: PostgresSQL's user (e.g.: `avnadmin`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> User_
* **POSTGRES_PASSWORD**: PostgresSQL's password (e.g.: `p4ssW0rd1`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> Password_
* **POSTGRES_PORT**: PostgresSQL's TCP listener port (e.g.: `5432`), it's available on your [Aiven console](https://console.aiven.io/): _Services -> \<Your PostgresSQL\> -> Overview -> Port_
* **POSTGRES_SSL**: PostgresSQL's SSL Mode Description (default: `require`). For a full list values, check PostgresSQL [documentation](https://www.postgresql.org/docs/current/libpq-ssl.html#LIBPQ-SSL-SSLMODE-STATEMENTS)
* **POSTGRES_TABLE**: Name of Database Hypertable for storing our web metrics (e.g.: `web_health_metrics`)

## Additional considerations
1. Only Unix-like systems are supported
2. The code has been tested with only these versions (Different versions may work too but we cannot ensure it):
* Kafka 2.7.0
* PostgresSQL 13.2
* Python 3.9.4
* TimesacleDB 2.1
3. For a detailed list of Python modules, check our [requirements.txt](https://github.com/elminster-aom/homeworks/blob/main/requirements.txt). It can be used like:
```shell
pip3 install --requirement requirements.txt
```

## Areas of improvement
Review the list of [TODOs](https://github.com/elminster-aom/homeworks/blob/main/docs/TODOS.md)

## References
I would like to reference some useful information, that it has been crucial to the implementation of this solution. Thank you to their creators for their disinterested collaboration
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
