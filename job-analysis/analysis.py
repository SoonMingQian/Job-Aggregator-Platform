from transformers import pipeline

def extract_skills(text):
    # Initialize the classifiers
    token_skill_classifier = pipeline(model="jjzha/jobbert_skill_extraction", aggregation_strategy="first")
    token_knowledge_classifier = pipeline(model="jjzha/jobbert_knowledge_extraction", aggregation_strategy="first")
    
    # Get both skills and knowledge
    skill_results = token_skill_classifier(text)
    knowledge_results = token_knowledge_classifier(text)
    
    # Combine both results into a set
    skills_set = set()
    
    # Add skills
    for result in skill_results:
        if result.get("entity_group"):
            skills_set.add(result["word"].strip())
            
    # Add knowledge (since technical knowledge can also be considered skills)
    for result in knowledge_results:
        if result.get("entity_group"):
            skills_set.add(result["word"].strip())
            
    return skills_set

# Example usage
text = "We are seeking a Lead Web Developer with experience in React and Node.js."
skills = extract_skills(text)
print("Skills:", skills)

# For your job description text
job_description = """
Job Requirements Work on and develop features in close co-operation with our partner, Microsoft. Help the team by removing blockers and raise major issues proactively. Work on complex problems across our components in a cross functional team. Help the team grow by offering support to other team members. Education BSc degree in Computer Science or related technical field, or equivalent practical experience 4+ years’ experience in software development Strong aptitude for learning new technologies """

extracted_skills = extract_skills(job_description)
print("\nExtracted Skills from Job Description:", extracted_skills)