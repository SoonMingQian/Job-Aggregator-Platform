from json import dumps
import json
import time
from kafka import KafkaConsumer, KafkaProducer
from transformers import pipeline, AutoTokenizer
import logging
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkillsExtractor:
    
    def __init__(self, bootstrap_servers=None, consumer_group='analysis-group'):
        if bootstrap_servers is None:
            bootstrap_servers = ['kafka1:9092', 'kafka2:9093', 'kafka3:9094']
            
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self.consumer = None
        self.producer = None
        
        # Initialize model components lazily (when first needed)
        self._token_skill_classifier = None
        self._token_knowledge_classifier = None
        self._tokenizer = None

    def create_kafka_consumer(self, retries=5, retry_interval=10):
        for attempt in range(retries):
            try:
                consumer = KafkaConsumer(
                    'analysis',
                    bootstrap_servers=['kafka1:9092', 'kafka2:9093', 'kafka3:9094'],
                    auto_offset_reset='earliest',
                    enable_auto_commit=False,
                    group_id='analysis-group',
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    session_timeout_ms=45000,           
                    request_timeout_ms=90000,           
                    heartbeat_interval_ms=15000,        
                    reconnect_backoff_ms=5000,
                    reconnect_backoff_max_ms=60000,
                    max_poll_interval_ms=600000,  # Increase from 300000 (5 minutes) to 600000 (10 minutes)
                    security_protocol='PLAINTEXT'
                )
                return consumer
            except KafkaError as e:
                logger.error(f"Kafka Error: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(retry_interval)
                else:
                    raise

    def create_kafka_producer(self, retries=5):
        for attempt in range(retries):
            try:
                return KafkaProducer(
                    bootstrap_servers=['kafka1:9092', 'kafka2:9093', 'kafka3:9094'],
                    value_serializer=lambda x: dumps(x).encode('utf-8'),
                    acks='all',
                    retries=3,
                    max_in_flight_requests_per_connection=1
                )
            except Exception as e:
                if attempt < retries - 1:
                    print(f"Failed to create producer. Retrying... (Attempt {attempt + 1}/{retries})")
                    time.sleep(5)
                else:
                    raise

    def _load_models(self):
        if self._token_skill_classifier is None:
            logger.info("Loading skill extraction models...")
            self._token_skill_classifier = pipeline(
                model="jjzha/jobbert_skill_extraction", 
                aggregation_strategy="first"
            )
            self._token_knowledge_classifier = pipeline(
                model="jjzha/jobbert_knowledge_extraction", 
                aggregation_strategy="first"
            )
            self._tokenizer = AutoTokenizer.from_pretrained("jjzha/jobbert_skill_extraction")
            logger.info("Models loaded successfully")                

    def extract_skills(self, text, max_length=512):
        
        self._load_models()
        # Split text into smaller chunks (simple sentence splitting)
        chunks = text.split('.')
        skills_set = set()
        
        # Process each chunk
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk:  # Check if chunk is not empty
                try:
                    # Tokenize and truncate the chunk
                    encoded = self._tokenizer(chunk, truncation=True, max_length=max_length, return_tensors="pt")
                    chunk_text = self._tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)
                    
                    # Process skills
                    skill_results = self._token_skill_classifier(chunk_text)
                    for result in skill_results:
                        if result.get("entity_group"):
                            skills_set.add(result["word"].strip())
                    
                    # Process knowledge
                    knowledge_results = self._token_knowledge_classifier(chunk_text)
                    for result in knowledge_results:
                        if result.get("entity_group"):
                            skills_set.add(result["word"].strip())
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
                    continue
        
        return skills_set

    def process_cv_message(self, data):
        userId = data['userId']
        cvContent = data['cvContent']
        
        logger.info(f"Processing CV for user {userId}")
        extracted_skills = self.extract_skills(cvContent)
        
        skills_message = {
            'source': 'cv',
            'userId': userId,
            'skills': list(extracted_skills)
        }
        
        return skills_message 
    
    def process_job_message(self, data):
        jobId = data['jobId']
        userId = data['userId']
        
        logger.info(f"Processing job {jobId} for user {userId}")
        extracted_skills = self.extract_skills(data['jobDescription'])
        
        skills_message = {
            'source': 'job',
            'jobId': jobId,
            'skills': list(extracted_skills)
        }
        
        matching_message = {
            'jobId': jobId,
            'userId': userId
        }
        
        return skills_message, matching_message
    
    def connect(self):
        logger.info("Connecting to Kafka...")
        self.consumer = self.create_kafka_consumer()
        self.producer = self.create_kafka_producer()
        logger.info("Connected to Kafka successfully")
    
    def disconnect(self):
        logger.info("Disconnecting from Kafka...")
        if self.consumer:
            try:
                self.consumer.close(autocommit=False)
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")
        
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
        
        logger.info("Disconnected from Kafka")

    def start_analysis(self):
        try:
            self.connect()
            logger.info("Starting analysis loop...")
            messages_since_commit = 0
            
            while True:
                try:
                    message_batch = self.consumer.poll(timeout_ms=1000)
                    
                    if not message_batch:
                        continue  # No messages, continue polling
                        
                    for tp, messages in message_batch.items():
                        for message in messages:
                            try:
                                data = message.value
                                source = data.get('source', 'job')
                                
                                # Process the message based on its source
                                if source == 'cv':
                                    skills_message = self.process_cv_message(data)
                                    self.producer.send('skill', value=skills_message)
                                    self.producer.flush()
                                    logger.info(f"Processed CV for user {data['userId']}")
                                
                                else:
                                    skills_message, matching_message = self.process_job_message(data)
                                    self.producer.send('skill', value=skills_message)
                                    self.producer.send('matching', value=matching_message)
                                    self.producer.flush()
                                    logger.info(f"Processed job {data['jobId']} for user {data['userId']}")
                                    
                                # Track successfully processed messages
                                messages_since_commit += 1
                                
                                # Commit every 5 messages or after a certain time
                                if messages_since_commit >= 5:
                                    try:
                                        # Use simple commit without offset mapping
                                        self.consumer.commit()
                                        logger.info(f"Committed offsets after {messages_since_commit} messages")
                                        messages_since_commit = 0
                                    except KafkaError as commit_error:
                                        if "CommitFailedError" in str(commit_error) or "IllegalStateError" in str(commit_error):
                                            logger.warning(f"Transient commit error: {str(commit_error)}")
                                        else:
                                            logger.error(f"Failed to commit: {str(commit_error)}")
                                    except Exception as e:
                                        logger.error(f"Unexpected error during commit: {str(e)}")
                                    
                            except Exception as process_error:
                                logger.error(f"Error processing message: {process_error}")
                                # Skip commit for failed messages
                                continue
                                
                except KafkaError as kafka_error:
                    # Handle Kafka errors
                    logger.error(f"Kafka error: {kafka_error}")
                    
                    # Check if it's a rebalance error and try to recover
                    if "CommitFailedError" in str(kafka_error) or "IllegalStateError" in str(kafka_error):
                        logger.warning("Rebalance detected, recreating consumer...")
                        try:
                            # Close old consumer cleanly
                            self.consumer.close(autocommit=False)
                        except:
                            pass  # Ignore errors during close
                            
                        # Reset counter and create new consumer
                        messages_since_commit = 0
                        time.sleep(10)  # Wait before reconnecting
                        self.consumer = self.create_kafka_consumer()
                    
                    time.sleep(5)  # Wait before retry
                    continue
                    
                except Exception as e:
                    # Handle other unexpected errors
                    logger.error(f"Unexpected error in main loop: {e}")
                    time.sleep(5)
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, closing connections...")
        finally:
            self.disconnect()
    
def main():
    extractor = SkillsExtractor()
    try:
        extractor.start_analysis()
    except KeyboardInterrupt:
        logger.info("Shutting down from main...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    return 0

# Add this compatibility function
def start_analysis():
    logger.info("Starting analysis via compatibility function")
    extractor = SkillsExtractor()
    extractor.start_analysis()

if __name__ == "__main__":
    exit(main())