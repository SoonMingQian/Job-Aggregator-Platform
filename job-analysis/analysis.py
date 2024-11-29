from transformers import pipeline, AutoTokenizer
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'analysis', # Topic name
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest', # Start reading from the beginning if no offset is found
    enable_auto_commit=True, # Automatically commit offsets
    group_id='analysis-group', # Consumer group ID
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # Deserialize message value
)

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

# # Example usage
# job_description = """A Day in The Life Of:

# Develop, co-ordinate and maintain .NET applications to support our industrial equipment software solutions.
# Develop, co-ordinate and HMI systems for various industrial equipment to enhance user experience and improve operational efficiency.
# Conduct automated testing using tools such as Selenium and Playwright to ensure the reliability and performance of our software products.
# Communicate/Collaborate with cross-functional teams to gather requirements and ensure timely delivery of high-quality software solutions.
# Develop your expertise, stay up to date with industry trends, new technologies, and best practices related to .NET, HMI, and automated testing.
# This is a temporary position.


# Key Skills & Experience

# Bachelor's Level 8 degree in Computer Science, Engineering, or a related field, 0 years of experience required.
# Experience with automated testing frameworks, such as Selenium or Playwright.
# Experience designing and implementing HMI systems for industrial equipment is a plus.
# Strong problem-solving and critical thinking skills.
# Excellent communication and collaboration abilities.
# Experience with version control systems (e.g., Git) and Agile methodologies."""
# extracted_skills = extract_skills(job_description)
# print("\nExtracted Skills from Job Description:", extracted_skills)

print("Waiting for messages...")
for message in consumer:
    job_data = message.value
    job_id = job_data['job_id']
    job_description = job_data['job_description']
    
    # Extract skills from the job description
    extracted_skills = extract_skills(job_description)
    
    # Process the job data as needed
    print(f"Received job ID: {job_id}")
    print(f"Job Description: {job_description}")
    print(f"Extracted Skills: {extracted_skills}")
    