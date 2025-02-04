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

def create_kafka_consumer(retries=5, retry_interval=10):
    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                'analysis',
                bootstrap_servers=['kafka1:9092', 'kafka2:9093', 'kafka3:9094'],
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                group_id='analysis-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                session_timeout_ms=45000,           # Reduced from 90000
                request_timeout_ms=90000,           # Kept at 90000
                heartbeat_interval_ms=15000,        # Reduced from 30000
                reconnect_backoff_ms=5000,
                reconnect_backoff_max_ms=60000,
                max_poll_interval_ms=300000,
                security_protocol='PLAINTEXT'
            )
            return consumer
        except KafkaError as e:
            logger.error(f"Kafka Error: {str(e)}")
            if attempt < retries - 1:
                time.sleep(retry_interval)
            else:
                raise

def create_kafka_producer(retries=5):
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



def extract_skills(text, max_length=512):
    # Initialize the classifiers and tokenizer
    token_skill_classifier = pipeline(model="jjzha/jobbert_skill_extraction", aggregation_strategy="first")
    token_knowledge_classifier = pipeline(model="jjzha/jobbert_knowledge_extraction", aggregation_strategy="first")
    tokenizer = AutoTokenizer.from_pretrained("jjzha/jobbert_skill_extraction")
    
    # Split text into smaller chunks (simple sentence splitting)
    chunks = text.split('.')
    skills_set = set()
    
    # Process each chunk
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk:  # Check if chunk is not empty
            # Tokenize and truncate the chunk
            encoded = tokenizer(chunk, truncation=True, max_length=max_length, return_tensors="pt")
            chunk_text = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)
            
            # Process skills
            skill_results = token_skill_classifier(chunk_text)
            for result in skill_results:
                if result.get("entity_group"):
                    skills_set.add(result["word"].strip())
            
            # Process knowledge
            knowledge_results = token_knowledge_classifier(chunk_text)
            for result in knowledge_results:
                if result.get("entity_group"):
                    skills_set.add(result["word"].strip())
    
    
    return skills_set

def start_analysis():
    consumer = create_kafka_consumer()
    producerSkills = create_kafka_producer()
    while True:
        try:
            message_batch = consumer.poll(timeout_ms=1000)
            
            for tp, messages in message_batch.items():
                for message in messages:
                    try:
                        # Process message
                        job_data = message.value
                        jobId = job_data['jobId']
                        userId = job_data['userId']
                        extracted_skills = extract_skills(job_data['jobDescription'])
                        
                        # Send to Kafka
                        skills_message = {
                            'source': job_data.get('source', 'job'),
                            'jobId': jobId,
                            'skills': list(extracted_skills)
                        }
                        
                        producerSkills.send('skill', value=skills_message)
                        producerSkills.flush()
                        
                        producerSkills.send('matching', value={
                            'jobId': jobId,
                            'userId': userId,
                        })
                        
                        producerSkills.flush()
                        # Manual commit after successful processing
                        consumer.commit()
                        logger.info(f"Processed and committed message for job {jobId}")
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        continue
                        
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
            time.sleep(5)  # Wait before retry
            continue
    
if __name__ == "__main__":
    start_analysis()