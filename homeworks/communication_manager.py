"""The API interface for interacting with Kafka service.
Its purpose is to isolate communication service from the main application logic
"""

import kafka
import json
from . import config
from . import logging_console

log = logging_console.getLogger("homeworks")


class Communication_manager:
    """Implement the methods for creating basic Kafka resources for the application"""

    def __init__(self) -> None:
        """Default constructor

        Properties:
            kafka_access_cert (str): Path to service.cert file
            kafka_access_key (str): Path to service.key file
            kafka_ca_cert (str): Path to ca.pem file
            kafka_consumer (kafka.KafkaConsumer): Consumer permanent connection to Kafka
            kafka_producer (kafka.KafkaProducer): Producer permanent connection to Kafka
            kafka_security_protocol (str): Forces that Kafka communication is SSL
            kafka_topic_name (str): Name of kafka topic used for produce/consume messages
        """
        self.kafka_access_cert = config.kafka_access_cert
        self.kafka_access_key = config.kafka_access_key
        self.kafka_ca_cert = config.kafka_ca_cert
        self.kafka_consumer = None
        self.kafka_producer = None
        self.kafka_security_protocol = "SSL"
        self.kafka_topic_name = config.kafka_topic_name

    def __del__(self) -> None:
        """Try to close all known connections with Kafka"""
        self.close_consumer()
        self.close_producer()

    def close_consumer(self, autocommit=True) -> None:
        """Close the consumer connection, waiting indefinitely for any needed cleanup.

        Args:
            autocommit (bool, optional): If auto-commit is configured for this consumer,
            this optional flag causes the consumer to attempt to commit any pending
            consumed offsets prior to close. Defaults to True.
        """
        if self.kafka_consumer:
            self.kafka_consumer.close(autocommit)
            self.kafka_consumer = None
            log.debug("Consumer connection was closed")

    def close_producer(self) -> None:
        """Close the producer connection"""
        if self.kafka_producer:
            self.kafka_producer.close()
            self.kafka_producer = None
            log.debug("Producer connection was closed")

    def connect_admin(self) -> kafka.KafkaAdminClient:
        """Establish an administrative connection to Kafka

        Returns:
            kafka.KafkaAdminClient: A connection object for administering the Kafka cluster
        """
        result = None
        log.debug("Gooing to connect KafkaAdminClient")
        try:
            result = kafka.KafkaAdminClient(
                bootstrap_servers=config.kafka_uri,
                security_protocol=self.kafka_security_protocol,
                ssl_cafile=self.kafka_ca_cert,
                ssl_certfile=self.kafka_access_cert,
                ssl_keyfile=self.kafka_access_key,
            )
        except Exception:
            log.exception(f"KafkaAdminClient connection could not be created")
        else:
            log.debug("Established connection with KafkaAdminClient")
        return result

    def connect_producer(self) -> None:
        """Establish a permanent connection to Kafka, for producing
        (pushing/publishing) messages
        """
        if self.kafka_producer and self.kafka_producer.bootstrap_connected():
            log.debug("Producer is already connected")
        else:
            log.debug("Going to connect KafkaProducer")
            try:
                self.kafka_producer = kafka.KafkaProducer(
                    bootstrap_servers=config.kafka_uri,
                    security_protocol=self.kafka_security_protocol,
                    ssl_cafile=self.kafka_ca_cert,
                    ssl_certfile=self.kafka_access_cert,
                    ssl_keyfile=self.kafka_access_key,
                )
            except Exception:
                log.exception(
                    f"Producer cannot establish connection with Kafka, on uri: '{config.kafka_uri}'"
                )
                raise
            else:
                log.debug("Established connection with KafkaProducer")

    def connect_consumer(self) -> None:
        """Establish a permanent connection with Kafka for consuming (retrieving) messages
        Note: `auto_offset_reset` is set to "latest" instead of "earliest" because we found
        that a gap in data is easier to detect than to duplicate registers, see:
          * How Postgresql COPY TO STDIN With CSV do on conflict do update? https://stackoverflow.com/a/48020691
          * UPSERTs not working correctly #100, https://github.com/timescale/timescaledb/issues/100
        """
        # TODO: Keep a permanent track of processed messages, therefore auto_offset_reset can be set to "latest" without potential duplication
        # TODO: URGENT! Enabling group_id!=None goes in unexpected scenario where messages are not consumed. Investigate further
        if self.kafka_consumer and self.kafka_consumer.bootstrap_connected():
            log.debug("Consumer is already connected")
        else:
            try:
                log.debug("Going to connect KafkaConsumer")
                # Reference about enable_auto_commit=False, see https://www.thebookofjoel.com/python-kafka-consumers
                self.kafka_consumer = kafka.KafkaConsumer(
                    self.kafka_topic_name,
                    auto_offset_reset="latest",
                    enable_auto_commit=True,
                    auto_commit_interval_ms=5000,
                    bootstrap_servers=config.kafka_uri,
                    security_protocol=self.kafka_security_protocol,
                    ssl_cafile=self.kafka_ca_cert,
                    ssl_certfile=self.kafka_access_cert,
                    ssl_keyfile=self.kafka_access_key,
                )
            except Exception:
                log.exception(
                    f"Consumer cannot establish connection with Kafka, from topic '{self.kafka_topic_name}'"
                )
                raise
            else:
                log.debug("Established connection with KafkaConsumer")

    def initialize_metrics_communication(self) -> None:
        """Create required topic `self.kafka_topic_name` for posting/retrieving
        monitoring metrics. If topic already exists, it reports as a warning
        and continues
        """
        kafka_admin_client = None

        log.info(f"Creating topic '{self.kafka_topic_name}'")
        my_topic = kafka.admin.NewTopic(
            name=self.kafka_topic_name, num_partitions=1, replication_factor=1
        )
        log.debug(f"Object kafka.admin.NewTopic was created: {my_topic}")
        kafka_admin_client = self.connect_admin()

        try:
            responses = kafka_admin_client.create_topics(
                new_topics=[my_topic], validate_only=False
            )
        except kafka.errors.TopicAlreadyExistsError:
            log.warning(f"Topic '{[my_topic]}' already exists, skipping next step")
        except Exception:
            log.exception(f"Topic '{[my_topic]}' could not be created")
            raise
        else:
            log.info(f"Topic created")
            log.debug(f"kafka_admin_client.create_topics() responses: {responses}")
        finally:
            if kafka_admin_client:
                kafka_admin_client.close()
                log.debug("Connection with KafkaAdminClient was closed")

    def validate_metrics_communication(self) -> bool:
        """Validate that the Kafka topic is defined

        Returns:
            bool: Return True when the topic is defined
        """
        result = False
        if self.kafka_consumer and self.kafka_consumer.bootstrap_connected():
            # This method will NOT close consumer connection if it was previously opened
            did_we_connect_consumer = False
        else:
            did_we_connect_consumer = True
            self.connect_consumer()

        try:
            topics = self.kafka_consumer.topics()
        except Exception:
            log.exception("List of defined Kafka topics could not be retrieved")
        else:
            log.debug(
                f"Looking for '{self.kafka_topic_name}' in defined Kafka topics: {topics}"
            )
            if self.kafka_topic_name in topics:
                result = True
        finally:
            if did_we_connect_consumer:
                self.close_consumer()
            return result

    @staticmethod
    def serialize_and_encode(message_dict: dict) -> str:
        """Before sending messages to Kafka, the object needs to be serialized to a string,
        in our case is serialize to a JSON string; and encoded to utf-8 (Default Python
        Unicode is not supported by Kafka library)

        Args:
            message_dict (dict): Object to send to kafka, which it is going to be
            processed here

        Returns:
            str: Result after serializing and encoding `message_dict`
        """
        result = None
        log.debug(f"Serializing '{message_dict}'")
        try:
            result = json.dumps(message_dict).encode("utf-8", errors="strict")
        except TypeError:
            log.exception(f"JSON could not serialize message '{message_dict}'")
            raise
        except UnicodeDecodeError:
            log.exception(f"Message '{message_dict}' could not be encoded to utf-8")
            raise
        else:
            log.debug(
                f"Serialized message object (message_dict) to a JSON formatted string and encoded to utf-8"
            )
            return result

    @staticmethod
    def deserialize_and_decode(raw_messages_dict: dict) -> list[str]:
        """Decodes the messages consumed from Kafka and split them in a list

        Args:
            messages (dict): Topic to list of records since the last fetch
            for the subscribed list of topics and partitions.

        Returns:
            list[str]: List of recoded records
        """
        messages_list = []
        for raw_messages in raw_messages_dict.values():
            for raw_message in raw_messages:
                try:
                    # Not necessary to decode, json.loads() accepts input encoding utf-8 since v3.6
                    message = json.loads(raw_message.value)
                    log.debug(
                        f"Deserialized bytes message containing a JSON document, result: {message}"
                    )
                except json.JSONDecodeError:
                    log.exception(
                        f"JSON could not deserialize message '{raw_message.value}'"
                    )
                    raise
                else:
                    messages_list.append(message)
        return messages_list

    def produce_message(self, message_dict: dict) -> None:
        """Send a message with metrics from web monitoring to Kafka
        * Raise exception if message could no be created (No guarantee is made about
        the completion of message sent)
        * Message is synchronous (`producer.flush()`) for simplifying the code,
        since threads sample metrics less often than 5-6 times per minute
        * Kafka Key is unset, since message doesn't
        require to be sorted

        Args:
            message_dict (dict): Metrics from web monitoring
        """
        self.connect_producer()  # Connect if it's not connected
        encoded_message = self.serialize_and_encode(message_dict)
        log.debug(f"Sending message to topic '{self.kafka_topic_name}'")
        try:
            response = self.kafka_producer.send(self.kafka_topic_name, encoded_message)
            log.debug(f"Message sent, response was: {response}")
            self.kafka_producer.flush(timeout=10.0)
            log.debug("Message flushed")
        except kafka.errors.KafkaTimeoutError:
            log.exception(
                "Kafka infraestructure setup looks incomplete, e.g. Is our topic defined?"
            )
            raise
        except Exception:
            log.exception(
                f"Producer could not send message to Kafka, on topic '{self.kafka_topic_name}'"
            )
            raise
        else:
            log.info(f"Message sent to Kafka")

    def consume_messages(self) -> list[dict]:
        """Retrieve messages from Kafka
        * Raise exception in case of communication problems
        * This call will wait _in eternum_ until at least one messsage can be retrieved

        Returns:
            list[str]: All retrieved metrics, already decoded to text (utf-8)
        """
        self.connect_consumer()  # Connect if it's not connected
        messages_list = []
        number_retries_without_incoming = 0

        # TODO: Validate that these values are optimal (Load test required for better tuning)
        while number_retries_without_incoming < 2 and len(messages_list) < 100:
            # For a limit time, try to retrieve kafka messages (with a max. of 100 messages)
            log.debug("Checking for new messages")
            try:
                responses = self.kafka_consumer.poll(timeout_ms=1000)
            except Exception:
                log.exception(
                    f"Consumer cannot retrieve message with Kafka, from topic '{self.kafka_topic_name}'"
                )
                raise
            else:
                log.debug(f"kafka_consumer.poll() response: {responses}")
                if responses:
                    log.debug("Putting together all consumed messages")
                    messages_list.extend(self.deserialize_and_decode(responses))
                    # Reset counter after getting messages
                    number_retries_without_incoming = 0
                else:
                    number_retries_without_incoming += 1

        log.debug(f"Returning list of all received messages: {messages_list}")
        return messages_list
