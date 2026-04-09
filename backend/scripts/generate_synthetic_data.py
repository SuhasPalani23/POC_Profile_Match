import json
import random
import os
from datetime import datetime

# We will generate a base set of synthetic data that represents raw inputs vs normalized outputs.

def generate_synthetic_user(user_id):
    # Dummy profiles
    roles = [
        ("Full Stack Developer", ["React", "Node.js", "Python", "MongoDB", "AWS"]),
        ("Data Scientist", ["Python", "TensorFlow", "SQL", "Pandas", "Scikit-Learn"]),
        ("Product Manager", ["Agile", "Scrum", "Jira", "Stakeholder Management", "Roadmapping"]),
        ("UX Designer", ["Figma", "Sketch", "Prototyping", "User Research", "Wireframing"])
    ]
    
    role, core_skills = random.choice(roles)
    
    # Simulate LinkedIn Data (Noisy, marketing focused)
    linkedin_data = {
        "headline": f"Experienced {role} | Helping startups scale",
        "about_summary": f"Passionate {role} with a proven track record. I love building things and working with great teams. Skills include " + ", ".join(core_skills[:3]) + " and more.",
        "experience": f"Worked at various tech companies as a {role} for {random.randint(3, 8)} years.",
        "linkedin_skills": core_skills + ["Leadership", "Communication", "Teamwork", "Problem Solving", "Microsoft Word"]
    }
    
    # Simulate Resume Data (Structured, technical)
    resume_data = {
        "objective": f"Seeking a challenging role as a {role} to utilize my technical skills.",
        "work_history": [
            {"company": "Tech Innovators Inc.", "title": role, "duration": "3 years", "description": f"Developed scalable applications using {core_skills[0]} and {core_skills[1]}."},
            {"company": "Startup Hub", "title": f"Junior {role}", "duration": "2 years", "description": "Collaborated with cross-functional teams."}
        ],
        "technical_skills": core_skills,
        "education": "B.S. in Computer Science"
    }
    
    # Simulate AI Assistant Q&A Data (The questionnaire from Edit Profile)
    ai_questionnaire_data = {
        "preferred_work_style": random.choice(["Remote", "Hybrid", "On-site"]),
        "startup_mindset_indicator": random.choice(["Highly Adaptable", "Process Oriented", "Visionary", "Execution Focused"]),
        "biggest_achievement": f"Led a project that increased revenue by 20% using {core_skills[0]}."
    }
    
    # The Expected Normalized Output (What the LLM should learn to produce)
    # This represents the clean, deduplicated, highly searchable profile that gets embedded in Pinecone
    # and matched against the Startup Idea for the 90%+ matching score.
    total_yoe = 5
    normalized_output = {
        "canonical_skills": core_skills + ["Agile Methodologies"], # Cleaned and deduplicated
        "total_experience_years": total_yoe,
        "primary_role": role,
        "core_domains": [role.split()[0], "Software Development", "Tech Startups"],
        "unified_profile_summary": f"A highly capable {role} with {total_yoe} years of experience. Specializes in {core_skills[0]} and {core_skills[1]} with a {ai_questionnaire_data['startup_mindset_indicator']} approach to problem-solving. Proven ability to deliver projects such as their noted revenue-increasing achievement.",
        "startup_compatibility_flags": [ai_questionnaire_data['startup_mindset_indicator'], ai_questionnaire_data['preferred_work_style']]
    }
    
    # OpenAI Fine-Tuning Format (User Prompt -> Assistant Output)
    return {
        "messages": [
            {"role": "system", "content": "You are an expert AI recruiter and data normalizer. Your job is to take raw, messy data from LinkedIn, Resumes, and User Questionnaires, and synthesize it into a clean, canonical JSON profile. This normalized profile will be embedded into Pinecone to match against startup ideas."},
            {"role": "user", "content": json.dumps({"linkedin": linkedin_data, "resume": resume_data, "questionnaire": ai_questionnaire_data})},
            {"role": "assistant", "content": json.dumps(normalized_output)}
        ]
    }

def main():
    print("Generating Synthetic Data...")
    dataset = []
    for i in range(50): # Generate 50 synthetic examples
        dataset.append(generate_synthetic_user(i))
    
    output_path = os.path.join(os.path.dirname(__file__), '../data/llm_finetuning_dataset.jsonl')
    
    # Save as JSONL (standard format for OpenAI fine-tuning)
    with open(output_path, 'w') as f:
        for entry in dataset:
            f.write(json.dumps(entry) + '\n')
            
    print(f"✅ Successfully generated {len(dataset)} synthetic profile pairs.")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    main()
