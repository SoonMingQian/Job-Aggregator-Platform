import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

def wait_for_kafka(retries=5, delay=5):
    bootstrap_servers = ['kafka1:9092', 'kafka2:9093', 'kafka3:9094']
    
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                acks='all',
                retries=3
            )
            producer.close()
            print("All Kafka brokers are ready!")
            return True
        except NoBrokersAvailable:
            print(f"Kafka brokers not available. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
            time.sleep(delay)
    print("Kafka brokers not available after multiple attempts.")
    return False

if __name__ == "__main__":
    if wait_for_kafka():
        from app import app
        app.run(host='0.0.0.0', port=3001)
    else:
        print("Exiting due to Kafka not being available.")