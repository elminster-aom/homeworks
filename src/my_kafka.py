"""Our API interface for interacting with Kafka service.
Its purpose is isolating communication service from main application logic
"""

import kafka
import json
import logging
from . import config

log = logging.getLogger("homeworks")


class MyKafka:
    """Implement the methods for creating basic Kafka resources for our application"""

    def __init__(self):
        self.kafka_access_cert = config.kafka_access_cert
        self.kafka_access_key = config.kafka_access_key
        self.kafka_ca_cert = config.kafka_ca_cert
        self.kafka_security_protocol = "SSL"
        self.kafka_topic_name = config.kafka_topic_name
        self.kafka_uri = config.kafka_uri

    def create_topic(self):
        """Create required topic, `self.kafka_topic_name`, for our application
        * Raise exception if topic could not be created
        * If topic already exists, it reports as a warning and it countinues
        """
        kafka_admin_client = None
        try:
            log.info(f"Creating topic '{self.kafka_topic_name}'")
            kafka_topics = [
                kafka.admin.NewTopic(
                    name=self.kafka_topic_name, num_partitions=1, replication_factor=1
                )
            ]
            kafka_admin_client = kafka.KafkaAdminClient(
                bootstrap_servers=self.kafka_uri,
                security_protocol=self.kafka_security_protocol,
                ssl_cafile=self.kafka_ca_cert,
                ssl_certfile=self.kafka_access_cert,
                ssl_keyfile=self.kafka_access_key,
            )
            responses = kafka_admin_client.create_topics(
                new_topics=kafka_topics, validate_only=False
            )

        except kafka.errors.TopicAlreadyExistsError:
            log.warning(
                f"Topic '{self.kafka_topic_name}' already exist, skipping next step"
            )
        except Exception:
            log.exception(f"Topic '{self.kafka_topic_name}' could not be created")
            raise
        else:
            log.debug(f"kafka_admin_client.create_topics' response: {responses}")
            log.info(f"Topic '{self.kafka_topic_name}' created")
        finally:
            if kafka_admin_client:
                kafka_admin_client.close()

    def produce_message(self, message_dict: dict):
        """Send a message to Kafka, with metrics, from web monitoring
        * Raise exception if message could no be crated (No guarantee is made about
        the completation of message sent)
        * Missage is syncronous (`producer.flush()`) for simplifying the code,
        since threads sample metrics less often than 5-6 times per minute
        * Message is encoded as JSON and Kafka Key is unset, since message doesn't
        require been sorted

        Args:
            message_dict (dict): Metrics from web monitoring
        """
        try:
            log.debug(f"Sending message '{message_dict}'")
            message_json = json.dumps(message_dict)
        except json.JSONDecodeError:
            log.exception(f"JSON could not encode message '{message_dict}'")
            raise

        kafka_producer = None
        try:
            kafka_producer = kafka.KafkaProducer(
                bootstrap_servers=self.kafka_uri,
                security_protocol=self.kafka_security_protocol,
                ssl_cafile=self.kafka_ca_cert,
                ssl_certfile=self.kafka_access_cert,
                ssl_keyfile=self.kafka_access_key,
            )
            response = kafka_producer.send(
                self.kafka_topic_name, message_json.encode("utf-8")
            )
            kafka_producer.flush(timeout=10.0)

        except Exception:
            log.exception(
                f"Producer could not send message to Kafka, on topic '{self.kafka_topic_name}'"
            )
            raise
        else:
            log.debug(f"kafka_producer.send response: {response}")
            log.info(f"Message sent")
        finally:
            if kafka_producer:
                kafka_producer.close()

    def consume_messages(self) -> list[dict]:
        """Retrieve messages from Kafka
        * Raise exception if communication problems
        * This call will wait _in eternum_ until at least one messsage can be retrived
        * `auto_offset_reset` is set to "earliest" instead "latest" because we found a
        gap in data is easier to detect that duplicate registers

        Returns:
            list[str]: All retrived metrics, already decoded to text (utf-8)
        """

        # TODO: Keep a permanent track of processed messages, therefore auto_offset_reset can be set to "latest" without potentional duplication
        try:
            kafka_consumer = kafka.KafkaConsumer(
                self.kafka_topic_name,
                auto_offset_reset="earliest",
                bootstrap_servers=self.kafka_uri,
                security_protocol=self.kafka_security_protocol,
                ssl_cafile=self.kafka_ca_cert,
                ssl_certfile=self.kafka_access_cert,
                ssl_keyfile=self.kafka_access_key,
            )
        except Exception:
            log.exception(
                f"Consumer cannot stablish connection with Kafka, from topic '{self.kafka_topic_name}'"
            )
            raise

        responses = None
        messages_list = []
        try:
            while len(messages_list) == 0:
                log.debug(f"Receiving messages")
                responses = kafka_consumer.poll(timeout_ms=10000)
                log.debug(f"kafka_consumer.poll responses: {responses}")
                if responses:
                    for _, messages in responses.items():
                        for message_encoded in messages:
                            message_dict = json.loads(
                                message_encoded.value.decode("utf-8")
                            )
                            print(message_dict)
                            messages_list.append(message_dict)
        except Exception:
            log.exception(
                f"Consumer cannot retrieve message with Kafka, from topic '{self.kafka_topic_name}'"
            )
            raise
        finally:
            kafka_consumer.close()

        return messages_list
