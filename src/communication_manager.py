"""The API interface for interacting with Kafka service.
Its purpose is to isolate communication service from the main application logic
"""

import kafka
import json
import logging
from . import config

log = logging.getLogger("homeworks")


class Communication_manager:
    """Implement the methods for creating basic Kafka resources for the application"""

    def __init__(self):
        self.kafka_access_cert = config.kafka_access_cert
        self.kafka_access_key = config.kafka_access_key
        self.kafka_ca_cert = config.kafka_ca_cert
        self.kafka_consumer = None
        self.group_id = "communication_manager_1"
        self.kafka_security_protocol = "SSL"
        self.kafka_topic_name = config.kafka_topic_name

    def __del__(self) -> None:
        self.close()

    def close(self, autocommit=True) -> None:
        """Close the consumer connection, waiting indefinitely for any needed cleanup.

        Args:
            autocommit (bool, optional): If auto-commit is configured for this consumer,
            this optional flag causes the consumer to attempt to commit any pending
            consumed offsets prior to close. Defaults to True.
        """
        if self.kafka_consumer:
            self.kafka_consumer.close(autocommit)
            kafka_consumer = None
            log.debug("Consumer connection was closed")

    def initialize_metrics_communication(self):
        """Create required topic `self.kafka_topic_name` for posting/retrieving
        monitoring metrics
        * Raise exception if topic could not be created
        * If topic already exists, it reports as a warning and continues
        """
        kafka_admin_client = None
        try:
            log.info(f"Creating topic '{self.kafka_topic_name}'")
            kafka_topics = [
                kafka.admin.NewTopic(
                    name=self.kafka_topic_name, num_partitions=1, replication_factor=1
                )
            ]
            log.debug("Object kafka.admin.NewTopic was created")
            kafka_admin_client = kafka.KafkaAdminClient(
                bootstrap_servers=config.kafka_uri,
                security_protocol=self.kafka_security_protocol,
                ssl_cafile=self.kafka_ca_cert,
                ssl_certfile=self.kafka_access_cert,
                ssl_keyfile=self.kafka_access_key,
            )
            log.debug("Established connection with KafkaAdminClient")
            responses = kafka_admin_client.create_topics(
                new_topics=kafka_topics, validate_only=False
            )

        except kafka.errors.TopicAlreadyExistsError:
            log.warning(
                f"Topic '{self.kafka_topic_name}' already exists, skipping next step"
            )
        except Exception:
            log.exception(f"Topic '{self.kafka_topic_name}' could not be created")
            raise
        else:
            log.info(f"Topic '{self.kafka_topic_name}' created")
            log.debug(f"kafka_admin_client.create_topics' response: {responses}")
        finally:
            if kafka_admin_client:
                kafka_admin_client.close()
                log.debug("Connection with KafkaAdminClient was closed")

    def validate_metrics_communication(self) -> bool:
        """Vaidate that the Kafka topic is defined

        Returns:
            bool: Return True when the topic is defined
        """
        result = False
        try:
            self.connect_consumer()
            topics = self.kafka_consumer.topics()

        except Exception:
            log.exception("List of defined Kafka topics could not be retrieved")
        else:
            log.debug(f"List of defined Kafka topics: {topics}")
            if self.kafka_topic_name in topics:
                result = True
        finally:
            self.close()
        return result

    def produce_message(self, message_dict: dict):
        """Send a message with metrics from web monitoring to Kafka 
        * Raise exception if message could no be created (No guarantee is made about
        the completion of message sent)
        * Message is synchronous (`producer.flush()`) for simplifying the code,
        since threads sample metrics less often than 5-6 times per minute
        * Message is encoded as JSON
        * Kafka Key is unset, since message doesn't
        require to be sorted

        Args:
            message_dict (dict): Metrics from web monitoring
        """
        try:
            log.debug(
                f"Sending message '{message_dict}', on topic '{self.kafka_topic_name}'"
            )
            message_json = json.dumps(message_dict)
        except json.JSONDecodeError:
            log.exception(f"JSON could not encode message '{message_dict}'")
            raise
        else:
            log.debug(
                f"Serialized message object (message_dict) to a JSON formatted string"
            )

        kafka_producer = None
        try:
            kafka_producer = kafka.KafkaProducer(
                bootstrap_servers=config.kafka_uri,
                security_protocol=self.kafka_security_protocol,
                ssl_cafile=self.kafka_ca_cert,
                ssl_certfile=self.kafka_access_cert,
                ssl_keyfile=self.kafka_access_key,
            )
            log.debug("Established connection with KafkaProducer. Sending message")
            response = kafka_producer.send(
                self.kafka_topic_name, message_json.encode("utf-8")
            )
            log.debug("Message sent, waiting for kafka_producer.flush()")
            kafka_producer.flush(timeout=10.0)

        except Exception:
            log.exception(
                f"Producer could not send message to Kafka, on topic '{self.kafka_topic_name}'"
            )
            raise
        else:
            log.info(f"Message sent")
            log.debug(
                f"Message flushed, kafka_producer.send() response was '{response}'"
            )
        finally:
            if kafka_producer:
                kafka_producer.close()
                log.debug("Connection with KafkaProducer was closed")

    def connect_consumer(self) -> bool:
        """Establish a permanent connection with Kafka for consuming (retrieving) messages
        * Raise exception in case of communication problems
        * `auto_offset_reset` is set to "latest" instead of "earliest" because we found that a
        gap in data is easier to detect than to duplicate registers, see:
          ** How Postgresql COPY TO STDIN With CSV do on conflic do update? https://stackoverflow.com/a/48020691
          ** UPSERTs not working correctly #100, https://github.com/timescale/timescaledb/issues/100

        * This call is optional, `consume_messages()` establishes already this connection
        automatically

        Returns:
            bool: Return `True` when the bootstrap is succesfully connected
        """
        # TODO: Keep a permanent track of processed messages, therefore auto_offset_reset can be set to "latest" without potentional duplication

        result = False
        if (
            self.kafka_consumer == None
            or self.kafka_consumer.bootstrap_connected() != True
        ):
            try:
                log.debug("Consumer was not connected")
                # Reference about enable_auto_commit=False, see https://www.thebookofjoel.com/python-kafka-consumers
                self.kafka_consumer = kafka.KafkaConsumer(
                    self.kafka_topic_name,
                    group_id=self.group_id,
                    auto_offset_reset="earliest",
                    enable_auto_commit=False,
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
                result = True
        else:
            log.debug("Consumer is already connected")
            result = True
        return result

    def consume_messages(self) -> list[dict]:
        """Retrieve messages from Kafka
        * Raise exception in case of communication problems
        * This call will wait _in eternum_ until at least one messsage can be retrieved

        Returns:
            list[str]: All retrieved metrics, already decoded to text (utf-8)
        """
        self.connect_consumer()

        number_retries_without_incoming = 0
        messages_list = []
        try:
            # TODO: Validate that these values are optiomal (Load test required for better tuning)
            while number_retries_without_incoming < 1 and len(messages_list) < 100:
                log.debug("Receiving messages")
                responses = self.kafka_consumer.poll(timeout_ms=1000)
                self.kafka_consumer.commit()  # Commit the offset of last processed message
                log.debug(f"kafka_consumer.poll() response: {responses}")
                if responses:
                    # Reset counter after getting messages
                    number_retries_without_incoming = 0
                    for messages in responses.values():
                        for message_encoded in messages:
                            message_dict = json.loads(message_encoded.value)
                            log.debug(
                                f"Deserialized bytes message containing a JSON document, result: {message_dict}"
                            )
                            messages_list.append(message_dict)
                else:
                    number_retries_without_incoming += 1

        except Exception:
            log.exception(
                f"Consumer cannot retrieve message with Kafka, from topic '{self.kafka_topic_name}'"
            )
            raise
        log.debug("Returning the list of all received messages")
        return messages_list
