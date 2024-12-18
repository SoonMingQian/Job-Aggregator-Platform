import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

def wait_for_kafka(bootstrap_servers, retries=5, delay=5):
    for attempt in range(retries):
        try:
            producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
            producer.close()
            print("Kafka is ready!")
            return True
        except NoBrokersAvailable:
            print(f"Kafka not available. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
            time.sleep(delay)
    print("Kafka is not available after multiple attempts.")
    return False

if __name__ == "__main__":
    if wait_for_kafka('kafka:9092'):
        from analysis import start_analysis
        start_analysis()
    else:
        print("Exiting due to Kafka not being available.")