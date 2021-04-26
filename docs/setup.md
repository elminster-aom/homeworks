# setup.py
-- [source](https://github.com/elminster-aom/homeworks/blob/main/setup.py) --

Independent module for initializing the environment, it has be run only once (per environment) before anything else
1. It assumes that PostgresSQL platform is up and running and we have administrative authorization
2. It assumes that Kafka platform is up and running and we have administrative authorization
3. It enables TimescaleDB extension in PostgresSQL
4. It creates a table for storing our metrics monitoring
5. It turns previous table in a hypertable partitioned, for storing monitoring metrics
6. It creates a Kakfa _topic_ of _Produce_/_Consume_ our metrics

## setup.init_logging()
Initialization of basic logging to console, _stdout_ and _stderr_, where log level _INFO_ goes to _stdout_ and anything else to _stderr_ (See stackoverflow, [How can INFO and DEBUG logging message be sent to stdout and higher level message to stderr](https://stackoverflow.com/a/31459386))

## setup.main() → int
Main program

**Returns**
`int` – Return 0 if all setup ran without problems
