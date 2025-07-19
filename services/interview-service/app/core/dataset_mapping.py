"""Dataset mapping configuration for TalentSync Interview Service."""

# Dataset to Domain Mapping
DATASET_DOMAIN_MAPPING = {
    # Core DSA dataset
    "DSA_dataset.json": "dsa",
    
    # DevOps and Infrastructure datasets
    "DevOps_dataset.json": "devops",
    "Kubernetes_dataset.json": "devops",  # Kubernetes comes under DevOps
    
    # AI and ML datasets
    "AI_Engineering_dataset.json": "ai-engineering",
    "ML_dataset.json": "machine-learning",
    "LLM_NLP_dataset.json": "machine-learning",  # LLM/NLP comes under ML and Data Science
    
    # Data Science datasets
    "Data_Science_dataset.json": "data-science",  # If exists
    "LLM_NLP_dataset.json": "data-science",  # Also applicable to Data Science
    
    # Software Engineering dataset
    "SWE_dataset.json": "software-engineering",
    
    # Resume-related datasets
    "Resume_dataset.json": "resume-based",  # Resume interview questions
    "Resumes_dataset.json": "resume-based",  # Resume data for personalization
}

# Domain descriptions for better understanding
DOMAIN_DESCRIPTIONS = {
    "dsa": {
        "name": "Data Structures & Algorithms",
        "description": "Core computer science concepts including data structures, algorithms, and problem-solving techniques",
        "key_topics": ["Arrays", "Linked Lists", "Trees", "Graphs", "Dynamic Programming", "Sorting", "Searching"],
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "devops": {
        "name": "DevOps & Infrastructure",
        "description": "Development operations, infrastructure management, and deployment practices",
        "key_topics": ["CI/CD", "Docker", "Kubernetes", "Cloud Platforms", "Monitoring", "Automation"],
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "ai-engineering": {
        "name": "AI Engineering",
        "description": "Engineering practices for AI systems, model deployment, and production AI infrastructure",
        "key_topics": ["MLOps", "Model Deployment", "AI Infrastructure", "Production Systems", "Monitoring"],
        "difficulty_levels": ["medium", "hard"]
    },
    "machine-learning": {
        "name": "Machine Learning",
        "description": "Machine learning algorithms, model development, and practical applications",
        "key_topics": ["Supervised Learning", "Unsupervised Learning", "Deep Learning", "Model Evaluation", "Feature Engineering"],
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "data-science": {
        "name": "Data Science",
        "description": "Data analysis, statistical modeling, and business intelligence",
        "key_topics": ["Data Analysis", "Statistics", "Visualization", "Predictive Modeling", "Business Intelligence"],
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "software-engineering": {
        "name": "Software Engineering",
        "description": "Software development practices, system design, and architecture",
        "key_topics": ["System Design", "Architecture", "Best Practices", "Scalability", "Testing"],
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "resume-based": {
        "name": "Resume-Based Interview",
        "description": "Personalized interviews based on candidate's resume and experience",
        "key_topics": ["Experience Analysis", "Skill Assessment", "Project Discussion", "Career Goals"],
        "difficulty_levels": ["medium"]
    }
}

# Question type mapping for each domain
DOMAIN_QUESTION_TYPES = {
    "dsa": ["conceptual", "technical", "coding", "follow-up"],
    "devops": ["conceptual", "technical", "behavioral", "follow-up"],
    "ai-engineering": ["conceptual", "technical", "behavioral", "follow-up"],
    "machine-learning": ["conceptual", "technical", "coding", "follow-up"],
    "data-science": ["conceptual", "technical", "behavioral", "follow-up"],
    "software-engineering": ["conceptual", "technical", "coding", "behavioral", "follow-up"],
    "resume-based": ["behavioral", "technical", "follow-up"]
}

def get_domain_for_dataset(dataset_name: str) -> str:
    """Get the domain for a given dataset name."""
    return DATASET_DOMAIN_MAPPING.get(dataset_name, "general")

def get_datasets_for_domain(domain: str) -> list:
    """Get all datasets that belong to a specific domain."""
    datasets = []
    for dataset, mapped_domain in DATASET_DOMAIN_MAPPING.items():
        if mapped_domain == domain:
            datasets.append(dataset)
    return datasets

def get_domain_description(domain: str) -> dict:
    """Get description and details for a specific domain."""
    return DOMAIN_DESCRIPTIONS.get(domain, {})

def get_question_types_for_domain(domain: str) -> list:
    """Get available question types for a specific domain."""
    return DOMAIN_QUESTION_TYPES.get(domain, ["conceptual", "technical", "follow-up"])

def get_all_domains() -> list:
    """Get all supported domains."""
    return list(DOMAIN_DESCRIPTIONS.keys())

def is_valid_domain(domain: str) -> bool:
    """Check if a domain is valid."""
    return domain in DOMAIN_DESCRIPTIONS 