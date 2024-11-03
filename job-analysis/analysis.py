from transformers import pipeline, AutoTokenizer

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

# Example usage
job_description = """Your job description text here"""
extracted_skills = extract_skills(job_description)
print("\nExtracted Skills from Job Description:", extracted_skills)