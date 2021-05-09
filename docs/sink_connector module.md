# sink_connector module
-- [source](https://github.com/elminster-aom/homeworks/blob/main/sink_connector.py) --

Retrieves (Consumer) metrics from a Kafka topic and stores it in a PostgresSQL hypertable

## sink_connector.main() -> int:
Main pogram

**Returns**

`int` – Return 0 if all ran without issues (Note: Ctrl+break is considered a normal way to stop it and it should exit with 0)

## sink_connector.sink_data()
While connection to communication bus is still established, batches of messages are retrieved and stored in the DB

### Additional considerations
* Loop can be interrupted with a _Ctrl+Break_
