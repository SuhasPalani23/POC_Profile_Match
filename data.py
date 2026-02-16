import random
from faker import Faker
from pymongo import MongoClient

# Initialize Faker and MongoDB
fake = Faker()
client = MongoClient("mongodb://localhost:27017/")
db = client["TalentMatchDB"]
users_collection = db["users"]  # Unified collection name

# Data Mapping (Role-specific skills)
roles_data = {
    "Business Analyst": [
        "Requirements Gathering", "Stakeholder Management", "Business Process Modeling (BPMN)",
        "Gap Analysis", "Data Analysis", "SQL", "Excel / Google Sheets", 
        "Documentation (BRD, FRD, SRS)", "User Stories & Acceptance Criteria", 
        "Agile / Scrum", "Communication Skills", "Presentation Skills", 
        "JIRA / Confluence", "UAT Coordination", "Risk Analysis"
    ],
    "Cloud Engineer": [
        "AWS / Azure / GCP", "Cloud Architecture Design", "Infrastructure as Code (Terraform, CloudFormation)",
        "Docker", "Kubernetes", "CI/CD Pipelines", "Linux Administration", 
        "Networking (VPC, DNS, Load Balancing)", "Monitoring (CloudWatch, Prometheus)", 
        "Scripting (Python, Bash)", "Security Best Practices", "IAM & Access Control", 
        "Serverless Architecture", "Cost Optimization", "Disaster Recovery"
    ],
    "Cyber Security Engineer": [
        "Network Security", "Ethical Hacking", "Penetration Testing", "Vulnerability Assessment", 
        "SIEM Tools (Splunk, QRadar)", "Firewall & IDS/IPS", "Incident Response", 
        "Cryptography", "Security Auditing", "Risk Management", "OWASP Top 10", 
        "Endpoint Security", "Identity & Access Management", "Compliance (ISO 27001, NIST)", "Threat Modeling"
    ],
    "Data Engineer": [
        "Python / Java / Scala", "SQL", "ETL / ELT Development", "Apache Spark", 
        "Hadoop Ecosystem", "Airflow", "Data Warehousing", "Snowflake / Redshift / BigQuery", 
        "Kafka", "Data Modeling", "NoSQL Databases", "Cloud Data Platforms", 
        "Data Pipeline Optimization", "Data Governance", "CI/CD for Data Pipelines"
    ],
    "SDE": [
        "Data Structures & Algorithms", "Object-Oriented Programming", "System Design", 
        "Low-Level Design", "Java / Python / C++ / JavaScript", "Spring Boot", "Django", 
        "Flask", "Node.js", "Express.js", "React", "Angular", "REST APIs", "GraphQL", 
        "Microservices Architecture", "Git", "Unit Testing (JUnit, PyTest, Jest)", 
        "Design Patterns", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", 
        "Database Design", "ORM (Hibernate, Sequelize)", "Multithreading & Concurrency", 
        "Docker", "CI/CD", "Code Review", "Debugging", "Agile Development"
    ],
    "Data Scientist": [
        "Python / R", "Statistics", "Machine Learning", "Deep Learning", "Data Visualization", 
        "Pandas / NumPy", "Scikit-learn", "TensorFlow / PyTorch", "SQL", "Feature Engineering", 
        "Model Evaluation", "A/B Testing", "Big Data Tools", "Data Cleaning", "Business Understanding"
    ]
}

def populate_users_table():
    all_users = []
    
    for role_name, skills_list in roles_data.items():
        print(f"Generating 6 users for {role_name}...")
        
        for _ in range(6):
            exp = random.randint(1, 15)
            
            # Skill count logic: More experience = more skills
            if exp < 3:
                num_skills = random.randint(3, 5)
            elif exp < 8:
                num_skills = random.randint(6, 9)
            else:
                num_skills = random.randint(9, 12)

            num_skills = min(num_skills, len(skills_list))

            user = {
                "full_name": fake.name(),
                "email": fake.unique.email(),
                "password": "Test@123", # Standardized password
                "location": f"{fake.city()}, {fake.country()}",
                "user_role": "user",
                "professional_title": role_name,
                "skills": random.sample(skills_list, k=num_skills),
                "bio": fake.paragraph(nb_sentences=3),
                "experience_years": exp,
                "resume": "", 
                "founding_mindset_score": random.randint(1, 10),
                "created_at": fake.date_time_this_year()
            }
            all_users.append(user)
    
    # Batch insert all 36 users into the single 'users' collection
    if all_users:
        users_collection.insert_many(all_users)
        print(f"\nSuccessfully populated 'users' table with {len(all_users)} documents.")

if __name__ == "__main__":
    # Optional: Clear existing data to avoid duplicates during testing
    # users_collection.delete_many({}) 
    populate_users_table()