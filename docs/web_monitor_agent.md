# web_monitor_agent module
-- [source](https://github.com/elminster-aom/homeworks/blob/main/web_monitor_agent.py) --

Monitors the health of several Web pages, collecting the information listed below, and publishes (Producer) it to a Kafka topic:
* HTTP response time
* Error code returned
* Pattern that is expected to be found on the page 

## web_monitor_agent.main() → int
Main program

**Returns**

`int` – Return 0 if all ran without issues (Note: _Ctrl+break_ is considered a normal way to stop it and it should exit with 0)

## web_monitor_agent.waitting_threads_ending_loop(threads: list)
Wait for threads to end, however these threads stop only when they’re killed; therefore process becomes a daemon and it runs for always

**Parameters**

***urls***(`list[Get_request_thread]`) – list of threads waiting to end
