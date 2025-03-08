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
            
            if not message_batch:
                continue  # No messages, continue polling
                
            for tp, messages in message_batch.items():
                for message in messages:
                    try:
                        data = message.value
                        source = data.get('source', 'job')
                        
                        # Process the message based on its source
                        if source == 'cv':
                            userId = data['userId']
                            cvContent = data['cvContent']
                            extracted_skills = extract_skills(cvContent)

                            skills_message = {
                                'source': 'cv',
                                'userId': userId,
                                'skills': list(extracted_skills)
                            }

                            producerSkills.send('skill', value=skills_message)
                            producerSkills.flush()
                        
                        else:
                            jobId = data['jobId']
                            userId = data['userId']
                            extracted_skills = extract_skills(data['jobDescription'])

                            skills_message = {
                                'source': 'job',
                                'jobId': jobId,
                                'skills': list(extracted_skills)
                            }

                            producerSkills.send('skill', value=skills_message)
                            producerSkills.flush()

                            producerSkills.send('matching', value={
                                'jobId': jobId,
                                'userId': userId,
                            })
                            
                        # Commit after each message is processed successfully
                        try:
                            consumer.commit({tp: message.offset + 1})
                            logger.info(f"Committed offset {message.offset + 1} for {tp}")
                        except Exception as commit_error:
                            logger.error(f"Failed to commit: {commit_error}")
                            # Don't re-raise, we'll continue processing
                            
                    except Exception as process_error:
                        logger.error(f"Error processing message: {process_error}")
                        # Try to commit anyway to avoid getting stuck
                        try:
                            consumer.commit({tp: message.offset + 1})
                            logger.info(f"Committed offset after error {message.offset + 1} for {tp}")
                        except Exception as commit_error:
                            logger.error(f"Failed to commit after error: {commit_error}")
                        # Continue to next message
                        continue
                        
        except KafkaError as kafka_error:
            # Handle Kafka errors
            logger.error(f"Kafka error: {kafka_error}")
            time.sleep(5)  # Wait before retry
            
            # Check if it's a rebalance error and try to recover
            if "CommitFailedError" in str(kafka_error) or "IllegalStateError" in str(kafka_error):
                logger.warning("Rebalance detected, recreating consumer...")
                try:
                    # Close old consumer cleanly
                    consumer.close(autocommit=False)
                except:
                    pass  # Ignore errors during close
                    
                # Create new consumer
                time.sleep(10)  # Wait a bit longer before reconnecting
                consumer = create_kafka_consumer()
                
            continue
        except Exception as e:
            # Handle other unexpected errors
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(5)
            continue
    
if __name__ == "__main__":
    start_analysis()