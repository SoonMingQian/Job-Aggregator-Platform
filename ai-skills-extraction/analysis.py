from json import dumps
import json
import time
from kafka import KafkaConsumer, KafkaProducer
from transformers import pipeline, AutoTokenizer

def create_kafka_consumer(retries=5):
    for attempt in range(retries):
        try:
            return KafkaConsumer(
                'analysis',
                bootstrap_servers=['kafka1:9092', 'kafka2:9093', 'kafka3:9094'],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='analysis-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
        except Exception as e:
            if attempt < retries - 1:
                print(f"Failed to connect to Kafka. Retrying... (Attempt {attempt + 1}/{retries})")
                time.sleep(5)
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

# Initialize with retry mechanism
consumer = create_kafka_consumer()
producerSkills = create_kafka_producer()

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
    print("Waiting for messages...")
    for message in consumer:
        job_data = message.value
        jobId = job_data['jobId']
        jobDescription = job_data['jobDescription']
        source = job_data.get('source', 'job') # Default to 'job' if source not specified
        
        # Extract skills from the job description
        extracted_skills = extract_skills(jobDescription)

        skills_message = {
            'source': source,
            'jobId': jobId,
            'skills': list(extracted_skills)
        }

        json_message = json.dumps(skills_message)

        # Log the message being sent
        print(f"Sending extracted skills for job {jobId} to Kafka: {skills_message}")
        producerSkills.send('skill', value=json_message)
        producerSkills.flush()
        print(f"Sent extracted skills for job {jobId} to Kafka")

if __name__ == "__main__":
    start_analysis()