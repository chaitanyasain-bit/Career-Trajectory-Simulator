"""
Seed data for the Career Trajectory Simulator.

This module defines all reference data:
  - Skill categories
  - Skills (global catalog)
  - Roles (global career role catalog)
  - Role-Skill requirements (what skills each role needs, with importance)
  - Role transitions (the career graph edges with weights)

Design rules:
  1. No hardcoded UUIDs in Python code — UUIDs are generated at insert time.
  2. All references use string keys (normalized names) that are resolved
     to actual IDs during seeding.
  3. Data is idempotent: running seed multiple times is safe (upsert pattern).
  4. This data directly feeds the trajectory engine:
       current skills → gap analysis → target role → roadmap
"""

from __future__ import annotations

# ── Skill Categories ──────────────────────────────────────────────────────────

SKILL_CATEGORIES: list[dict] = [
    {"name": "Programming Languages",   "description": "Core coding languages",                       "display_order": 1},
    {"name": "Data & Analytics",        "description": "Data processing and analysis tools",          "display_order": 2},
    {"name": "Machine Learning",        "description": "ML frameworks, algorithms, and concepts",     "display_order": 3},
    {"name": "Cloud & Infrastructure",  "description": "Cloud platforms and DevOps tooling",          "display_order": 4},
    {"name": "Databases",               "description": "SQL, NoSQL, and graph databases",             "display_order": 5},
    {"name": "Web Development",         "description": "Frontend and backend web technologies",       "display_order": 6},
    {"name": "Data Engineering",        "description": "Pipelines, ETL, streaming, orchestration",    "display_order": 7},
    {"name": "Soft Skills",             "description": "Communication, leadership, product thinking", "display_order": 8},
    {"name": "AI & LLM",               "description": "Generative AI, LLMs, prompt engineering",    "display_order": 9},
    {"name": "Mathematics & Statistics","description": "Foundational quantitative skills",            "display_order": 10},
]

# ── Skills ────────────────────────────────────────────────────────────────────
# Format: {"name": <display>, "normalized_name": <slug>, "category": <cat name>, "description": ...}

SKILLS: list[dict] = [
    # Programming Languages
    {"name": "Python",           "normalized_name": "python",          "category": "Programming Languages", "description": "General-purpose programming language dominant in data/ML"},
    {"name": "SQL",              "normalized_name": "sql",             "category": "Programming Languages", "description": "Structured Query Language for relational databases"},
    {"name": "R",                "normalized_name": "r",               "category": "Programming Languages", "description": "Statistical computing language"},
    {"name": "Scala",            "normalized_name": "scala",           "category": "Programming Languages", "description": "JVM language used with Apache Spark"},
    {"name": "Java",             "normalized_name": "java",            "category": "Programming Languages", "description": "Enterprise and Android development"},
    {"name": "JavaScript",       "normalized_name": "javascript",      "category": "Programming Languages", "description": "Web scripting language"},
    {"name": "TypeScript",       "normalized_name": "typescript",      "category": "Programming Languages", "description": "Typed superset of JavaScript"},
    {"name": "Go",               "normalized_name": "go",              "category": "Programming Languages", "description": "Systems language by Google — common in backend/infra"},
    {"name": "Rust",             "normalized_name": "rust",            "category": "Programming Languages", "description": "Memory-safe systems programming"},
    {"name": "C++",              "normalized_name": "cpp",             "category": "Programming Languages", "description": "High-performance systems programming"},
    {"name": "Shell/Bash",       "normalized_name": "bash",            "category": "Programming Languages", "description": "Unix shell scripting"},

    # Data & Analytics
    {"name": "Pandas",           "normalized_name": "pandas",          "category": "Data & Analytics", "description": "Python DataFrame library for data manipulation"},
    {"name": "NumPy",            "normalized_name": "numpy",           "category": "Data & Analytics", "description": "Numerical computing in Python"},
    {"name": "Excel",            "normalized_name": "excel",           "category": "Data & Analytics", "description": "Spreadsheet tool — widely used for analysis"},
    {"name": "Tableau",          "normalized_name": "tableau",         "category": "Data & Analytics", "description": "Business intelligence and data visualization"},
    {"name": "Power BI",         "normalized_name": "power_bi",        "category": "Data & Analytics", "description": "Microsoft BI and visualization platform"},
    {"name": "Data Visualization","normalized_name": "data_visualization","category": "Data & Analytics","description": "General skill for communicating insights visually"},
    {"name": "Statistics",       "normalized_name": "statistics",      "category": "Data & Analytics", "description": "Descriptive and inferential statistics"},
    {"name": "A/B Testing",      "normalized_name": "ab_testing",      "category": "Data & Analytics", "description": "Controlled experiments for product decisions"},

    # Machine Learning
    {"name": "scikit-learn",     "normalized_name": "scikit_learn",    "category": "Machine Learning", "description": "Classic ML algorithms library for Python"},
    {"name": "TensorFlow",       "normalized_name": "tensorflow",      "category": "Machine Learning", "description": "Google's deep learning framework"},
    {"name": "PyTorch",          "normalized_name": "pytorch",         "category": "Machine Learning", "description": "Meta's deep learning framework — research favourite"},
    {"name": "Keras",            "normalized_name": "keras",           "category": "Machine Learning", "description": "High-level neural network API"},
    {"name": "XGBoost",          "normalized_name": "xgboost",         "category": "Machine Learning", "description": "Gradient boosting — dominates tabular data competitions"},
    {"name": "Feature Engineering","normalized_name": "feature_engineering","category": "Machine Learning","description": "Creating informative features from raw data"},
    {"name": "Model Evaluation",  "normalized_name": "model_evaluation","category": "Machine Learning","description": "Metrics, cross-validation, and model selection"},
    {"name": "NLP",              "normalized_name": "nlp",             "category": "Machine Learning", "description": "Natural Language Processing"},
    {"name": "Computer Vision",  "normalized_name": "computer_vision", "category": "Machine Learning", "description": "Image and video analysis with ML"},
    {"name": "MLflow",           "normalized_name": "mlflow",          "category": "Machine Learning", "description": "ML lifecycle and experiment tracking"},
    {"name": "Hugging Face",     "normalized_name": "hugging_face",    "category": "Machine Learning", "description": "Transformers library and model hub"},
    {"name": "Reinforcement Learning","normalized_name": "reinforcement_learning","category": "Machine Learning","description": "Agent-based learning through rewards"},

    # Cloud & Infrastructure
    {"name": "AWS",              "normalized_name": "aws",             "category": "Cloud & Infrastructure", "description": "Amazon Web Services cloud platform"},
    {"name": "GCP",              "normalized_name": "gcp",             "category": "Cloud & Infrastructure", "description": "Google Cloud Platform"},
    {"name": "Azure",            "normalized_name": "azure",           "category": "Cloud & Infrastructure", "description": "Microsoft Azure cloud platform"},
    {"name": "Docker",           "normalized_name": "docker",          "category": "Cloud & Infrastructure", "description": "Container platform"},
    {"name": "Kubernetes",       "normalized_name": "kubernetes",      "category": "Cloud & Infrastructure", "description": "Container orchestration system"},
    {"name": "Terraform",        "normalized_name": "terraform",       "category": "Cloud & Infrastructure", "description": "Infrastructure as Code tool"},
    {"name": "CI/CD",            "normalized_name": "cicd",            "category": "Cloud & Infrastructure", "description": "Continuous integration and delivery pipelines"},
    {"name": "Linux",            "normalized_name": "linux",           "category": "Cloud & Infrastructure", "description": "Linux server administration"},

    # Databases
    {"name": "PostgreSQL",       "normalized_name": "postgresql",      "category": "Databases", "description": "Advanced open-source relational database"},
    {"name": "MySQL",            "normalized_name": "mysql",           "category": "Databases", "description": "Popular relational database"},
    {"name": "MongoDB",          "normalized_name": "mongodb",         "category": "Databases", "description": "Document-oriented NoSQL database"},
    {"name": "Redis",            "normalized_name": "redis",           "category": "Databases", "description": "In-memory key-value store / cache"},
    {"name": "Elasticsearch",    "normalized_name": "elasticsearch",   "category": "Databases", "description": "Distributed search and analytics engine"},

    # Web Development
    {"name": "React",            "normalized_name": "react",           "category": "Web Development", "description": "Facebook's UI component library"},
    {"name": "FastAPI",          "normalized_name": "fastapi",         "category": "Web Development", "description": "Modern Python async web framework"},
    {"name": "Django",           "normalized_name": "django",          "category": "Web Development", "description": "Full-featured Python web framework"},
    {"name": "Flask",            "normalized_name": "flask",           "category": "Web Development", "description": "Lightweight Python web framework"},
    {"name": "Node.js",          "normalized_name": "nodejs",          "category": "Web Development", "description": "JavaScript runtime for server-side development"},
    {"name": "REST APIs",        "normalized_name": "rest_apis",       "category": "Web Development", "description": "RESTful API design and implementation"},
    {"name": "GraphQL",          "normalized_name": "graphql",         "category": "Web Development", "description": "Query language for APIs"},
    {"name": "HTML/CSS",         "normalized_name": "html_css",        "category": "Web Development", "description": "Web markup and styling"},

    # Data Engineering
    {"name": "Apache Spark",     "normalized_name": "apache_spark",    "category": "Data Engineering", "description": "Large-scale distributed data processing"},
    {"name": "Apache Kafka",     "normalized_name": "apache_kafka",    "category": "Data Engineering", "description": "Distributed event streaming platform"},
    {"name": "Airflow",          "normalized_name": "airflow",         "category": "Data Engineering", "description": "Workflow orchestration for data pipelines"},
    {"name": "dbt",              "normalized_name": "dbt",             "category": "Data Engineering", "description": "Data transformation tool for analytics"},
    {"name": "ETL/ELT",          "normalized_name": "etl_elt",         "category": "Data Engineering", "description": "Extract, Transform, Load pipeline design"},
    {"name": "Data Warehousing", "normalized_name": "data_warehousing","category": "Data Engineering", "description": "Designing and maintaining data warehouses (BigQuery, Redshift, Snowflake)"},
    {"name": "Data Modeling",    "normalized_name": "data_modeling",   "category": "Data Engineering", "description": "Schema design: star/snowflake schemas, normalization"},
    {"name": "Snowflake",        "normalized_name": "snowflake",       "category": "Data Engineering", "description": "Cloud data warehousing platform"},

    # Soft Skills
    {"name": "Communication",    "normalized_name": "communication",   "category": "Soft Skills", "description": "Clear verbal and written communication"},
    {"name": "Problem Solving",  "normalized_name": "problem_solving", "category": "Soft Skills", "description": "Analytical and structured problem-solving"},
    {"name": "Project Management","normalized_name": "project_management","category": "Soft Skills","description": "Planning, execution, and delivery of projects"},
    {"name": "Leadership",       "normalized_name": "leadership",      "category": "Soft Skills", "description": "Team leadership and mentoring"},
    {"name": "Product Thinking", "normalized_name": "product_thinking","category": "Soft Skills", "description": "User-centric feature prioritization and roadmapping"},
    {"name": "Stakeholder Management","normalized_name": "stakeholder_management","category": "Soft Skills","description": "Managing relationships with cross-functional teams"},

    # AI & LLM
    {"name": "LLM Integration",  "normalized_name": "llm_integration", "category": "AI & LLM", "description": "Integrating large language models via APIs (OpenAI, Anthropic)"},
    {"name": "Prompt Engineering","normalized_name": "prompt_engineering","category": "AI & LLM","description": "Designing effective prompts for LLMs"},
    {"name": "RAG",              "normalized_name": "rag",             "category": "AI & LLM", "description": "Retrieval Augmented Generation patterns"},
    {"name": "Fine-tuning",      "normalized_name": "fine_tuning",     "category": "AI & LLM", "description": "Adapting pre-trained models on domain data"},
    {"name": "LangChain",        "normalized_name": "langchain",       "category": "AI & LLM", "description": "Framework for LLM-powered applications"},

    # Mathematics & Statistics
    {"name": "Linear Algebra",   "normalized_name": "linear_algebra",  "category": "Mathematics & Statistics", "description": "Vectors, matrices, eigenvalues — foundation of ML"},
    {"name": "Probability",      "normalized_name": "probability",     "category": "Mathematics & Statistics", "description": "Probability theory and distributions"},
    {"name": "Calculus",         "normalized_name": "calculus",        "category": "Mathematics & Statistics", "description": "Differential calculus — used in optimization/backprop"},
    {"name": "Hypothesis Testing","normalized_name": "hypothesis_testing","category": "Mathematics & Statistics","description": "Statistical significance testing"},
]

# ── Roles ─────────────────────────────────────────────────────────────────────
# seniority_level: 1=Junior, 2=Mid, 3=Senior, 4=Lead, 5=Executive

ROLES: list[dict] = [
    {
        "title": "Data Analyst",
        "normalized_title": "data_analyst",
        "description": "Extracts insights from data using SQL, Excel, and visualization tools. Communicates findings to stakeholders.",
        "domain": "Data",
        "seniority_level": 2,
        "avg_salary_inr": 700000,
        "avg_years_to_reach": 1.0,
    },
    {
        "title": "Senior Data Analyst",
        "normalized_title": "senior_data_analyst",
        "description": "Leads analytics projects, mentors junior analysts, and drives data-driven decision making.",
        "domain": "Data",
        "seniority_level": 3,
        "avg_salary_inr": 1200000,
        "avg_years_to_reach": 3.5,
    },
    {
        "title": "Data Scientist",
        "normalized_title": "data_scientist",
        "description": "Builds predictive models and applies ML to solve business problems. Bridges data and business strategy.",
        "domain": "Data",
        "seniority_level": 2,
        "avg_salary_inr": 1400000,
        "avg_years_to_reach": 3.0,
    },
    {
        "title": "Senior Data Scientist",
        "normalized_title": "senior_data_scientist",
        "description": "Leads complex modelling efforts, mentors teams, and defines ML strategy.",
        "domain": "Data",
        "seniority_level": 3,
        "avg_salary_inr": 2500000,
        "avg_years_to_reach": 6.0,
    },
    {
        "title": "ML Engineer",
        "normalized_title": "ml_engineer",
        "description": "Builds, trains, and deploys ML models at scale in production systems.",
        "domain": "ML",
        "seniority_level": 2,
        "avg_salary_inr": 1800000,
        "avg_years_to_reach": 3.5,
    },
    {
        "title": "Senior ML Engineer",
        "normalized_title": "senior_ml_engineer",
        "description": "Architects ML systems, leads model deployment strategy, mentors ML engineers.",
        "domain": "ML",
        "seniority_level": 3,
        "avg_salary_inr": 3000000,
        "avg_years_to_reach": 6.5,
    },
    {
        "title": "AI Engineer",
        "normalized_title": "ai_engineer",
        "description": "Integrates AI/LLM capabilities into products. Builds RAG systems, fine-tuned models, and AI pipelines.",
        "domain": "AI",
        "seniority_level": 2,
        "avg_salary_inr": 2000000,
        "avg_years_to_reach": 3.0,
    },
    {
        "title": "Data Engineer",
        "normalized_title": "data_engineer",
        "description": "Designs and maintains data pipelines, warehouses, and infrastructure that feeds analytics and ML.",
        "domain": "Data",
        "seniority_level": 2,
        "avg_salary_inr": 1500000,
        "avg_years_to_reach": 3.0,
    },
    {
        "title": "Senior Data Engineer",
        "normalized_title": "senior_data_engineer",
        "description": "Architects large-scale data platforms, leads platform teams, sets engineering standards.",
        "domain": "Data",
        "seniority_level": 3,
        "avg_salary_inr": 2800000,
        "avg_years_to_reach": 6.0,
    },
    {
        "title": "Backend Developer",
        "normalized_title": "backend_developer",
        "description": "Builds server-side APIs and services. Works with databases, business logic, and system design.",
        "domain": "Engineering",
        "seniority_level": 2,
        "avg_salary_inr": 1200000,
        "avg_years_to_reach": 2.0,
    },
    {
        "title": "Senior Backend Developer",
        "normalized_title": "senior_backend_developer",
        "description": "Leads backend architecture decisions, system design, and mentors junior engineers.",
        "domain": "Engineering",
        "seniority_level": 3,
        "avg_salary_inr": 2200000,
        "avg_years_to_reach": 5.0,
    },
    {
        "title": "Frontend Developer",
        "normalized_title": "frontend_developer",
        "description": "Builds user interfaces with modern web technologies. Focus on UX, performance, and accessibility.",
        "domain": "Engineering",
        "seniority_level": 2,
        "avg_salary_inr": 1100000,
        "avg_years_to_reach": 2.0,
    },
    {
        "title": "Full Stack Developer",
        "normalized_title": "full_stack_developer",
        "description": "Works across frontend and backend. Can own entire features end-to-end.",
        "domain": "Engineering",
        "seniority_level": 2,
        "avg_salary_inr": 1400000,
        "avg_years_to_reach": 3.0,
    },
    {
        "title": "Software Engineer",
        "normalized_title": "software_engineer",
        "description": "Designs, builds, and maintains software systems. Broad role covering algorithms, data structures, and system design.",
        "domain": "Engineering",
        "seniority_level": 2,
        "avg_salary_inr": 1300000,
        "avg_years_to_reach": 2.0,
    },
    {
        "title": "Product Manager",
        "normalized_title": "product_manager",
        "description": "Defines product vision and roadmap. Bridges engineering, design, and business stakeholders.",
        "domain": "Product",
        "seniority_level": 2,
        "avg_salary_inr": 1600000,
        "avg_years_to_reach": 4.0,
    },
    {
        "title": "Research Scientist",
        "normalized_title": "research_scientist",
        "description": "Conducts original AI/ML research and publishes findings. Deep expertise in theory and experimentation.",
        "domain": "Research",
        "seniority_level": 3,
        "avg_salary_inr": 2500000,
        "avg_years_to_reach": 6.0,
    },
]

# ── Role Skill Requirements ───────────────────────────────────────────────────
# Format: {"role": <normalized_title>, "skill": <normalized_name>, "importance": 1-5, "mandatory": bool}

ROLE_SKILL_REQUIREMENTS: list[dict] = [
    # ── Data Analyst ─────────────────────────────────────────────────────────
    {"role": "data_analyst", "skill": "sql",               "importance": 5, "mandatory": True},
    {"role": "data_analyst", "skill": "excel",             "importance": 5, "mandatory": True},
    {"role": "data_analyst", "skill": "python",            "importance": 4, "mandatory": True},
    {"role": "data_analyst", "skill": "pandas",            "importance": 4, "mandatory": True},
    {"role": "data_analyst", "skill": "data_visualization","importance": 4, "mandatory": True},
    {"role": "data_analyst", "skill": "statistics",        "importance": 4, "mandatory": True},
    {"role": "data_analyst", "skill": "tableau",           "importance": 3, "mandatory": False},
    {"role": "data_analyst", "skill": "power_bi",          "importance": 3, "mandatory": False},
    {"role": "data_analyst", "skill": "communication",     "importance": 4, "mandatory": True},
    {"role": "data_analyst", "skill": "problem_solving",   "importance": 4, "mandatory": True},

    # ── Senior Data Analyst ───────────────────────────────────────────────────
    {"role": "senior_data_analyst", "skill": "sql",               "importance": 5, "mandatory": True},
    {"role": "senior_data_analyst", "skill": "python",            "importance": 5, "mandatory": True},
    {"role": "senior_data_analyst", "skill": "pandas",            "importance": 5, "mandatory": True},
    {"role": "senior_data_analyst", "skill": "data_visualization","importance": 5, "mandatory": True},
    {"role": "senior_data_analyst", "skill": "statistics",        "importance": 5, "mandatory": True},
    {"role": "senior_data_analyst", "skill": "ab_testing",        "importance": 4, "mandatory": True},
    {"role": "senior_data_analyst", "skill": "leadership",        "importance": 3, "mandatory": False},
    {"role": "senior_data_analyst", "skill": "stakeholder_management","importance": 4,"mandatory": True},

    # ── Data Scientist ────────────────────────────────────────────────────────
    {"role": "data_scientist", "skill": "python",            "importance": 5, "mandatory": True},
    {"role": "data_scientist", "skill": "sql",               "importance": 5, "mandatory": True},
    {"role": "data_scientist", "skill": "pandas",            "importance": 5, "mandatory": True},
    {"role": "data_scientist", "skill": "numpy",             "importance": 4, "mandatory": True},
    {"role": "data_scientist", "skill": "scikit_learn",      "importance": 5, "mandatory": True},
    {"role": "data_scientist", "skill": "statistics",        "importance": 5, "mandatory": True},
    {"role": "data_scientist", "skill": "feature_engineering","importance": 4,"mandatory": True},
    {"role": "data_scientist", "skill": "model_evaluation",  "importance": 4, "mandatory": True},
    {"role": "data_scientist", "skill": "data_visualization","importance": 4, "mandatory": True},
    {"role": "data_scientist", "skill": "linear_algebra",    "importance": 3, "mandatory": False},
    {"role": "data_scientist", "skill": "probability",       "importance": 3, "mandatory": False},
    {"role": "data_scientist", "skill": "xgboost",           "importance": 3, "mandatory": False},
    {"role": "data_scientist", "skill": "communication",     "importance": 4, "mandatory": True},
    {"role": "data_scientist", "skill": "problem_solving",   "importance": 5, "mandatory": True},

    # ── Senior Data Scientist ─────────────────────────────────────────────────
    {"role": "senior_data_scientist", "skill": "python",             "importance": 5, "mandatory": True},
    {"role": "senior_data_scientist", "skill": "scikit_learn",       "importance": 5, "mandatory": True},
    {"role": "senior_data_scientist", "skill": "pytorch",            "importance": 4, "mandatory": False},
    {"role": "senior_data_scientist", "skill": "tensorflow",         "importance": 3, "mandatory": False},
    {"role": "senior_data_scientist", "skill": "mlflow",             "importance": 4, "mandatory": True},
    {"role": "senior_data_scientist", "skill": "statistics",         "importance": 5, "mandatory": True},
    {"role": "senior_data_scientist", "skill": "linear_algebra",     "importance": 4, "mandatory": True},
    {"role": "senior_data_scientist", "skill": "leadership",         "importance": 3, "mandatory": False},
    {"role": "senior_data_scientist", "skill": "communication",      "importance": 5, "mandatory": True},

    # ── ML Engineer ───────────────────────────────────────────────────────────
    {"role": "ml_engineer", "skill": "python",            "importance": 5, "mandatory": True},
    {"role": "ml_engineer", "skill": "scikit_learn",      "importance": 4, "mandatory": True},
    {"role": "ml_engineer", "skill": "pytorch",           "importance": 4, "mandatory": True},
    {"role": "ml_engineer", "skill": "tensorflow",        "importance": 3, "mandatory": False},
    {"role": "ml_engineer", "skill": "docker",            "importance": 5, "mandatory": True},
    {"role": "ml_engineer", "skill": "kubernetes",        "importance": 3, "mandatory": False},
    {"role": "ml_engineer", "skill": "mlflow",            "importance": 4, "mandatory": True},
    {"role": "ml_engineer", "skill": "rest_apis",         "importance": 4, "mandatory": True},
    {"role": "ml_engineer", "skill": "aws",               "importance": 3, "mandatory": False},
    {"role": "ml_engineer", "skill": "cicd",              "importance": 3, "mandatory": False},
    {"role": "ml_engineer", "skill": "sql",               "importance": 3, "mandatory": False},
    {"role": "ml_engineer", "skill": "linux",             "importance": 4, "mandatory": True},
    {"role": "ml_engineer", "skill": "feature_engineering","importance": 4,"mandatory": True},
    {"role": "ml_engineer", "skill": "model_evaluation",  "importance": 4, "mandatory": True},

    # ── Senior ML Engineer ────────────────────────────────────────────────────
    {"role": "senior_ml_engineer", "skill": "python",         "importance": 5, "mandatory": True},
    {"role": "senior_ml_engineer", "skill": "pytorch",        "importance": 5, "mandatory": True},
    {"role": "senior_ml_engineer", "skill": "kubernetes",     "importance": 4, "mandatory": True},
    {"role": "senior_ml_engineer", "skill": "docker",         "importance": 5, "mandatory": True},
    {"role": "senior_ml_engineer", "skill": "aws",            "importance": 4, "mandatory": True},
    {"role": "senior_ml_engineer", "skill": "mlflow",         "importance": 5, "mandatory": True},
    {"role": "senior_ml_engineer", "skill": "cicd",           "importance": 4, "mandatory": True},
    {"role": "senior_ml_engineer", "skill": "leadership",     "importance": 3, "mandatory": False},
    {"role": "senior_ml_engineer", "skill": "system_design",  "importance": 4, "mandatory": True} if False else None,  # system_design not in catalog yet
    {"role": "senior_ml_engineer", "skill": "linear_algebra", "importance": 4, "mandatory": True},

    # ── AI Engineer ───────────────────────────────────────────────────────────
    {"role": "ai_engineer", "skill": "python",            "importance": 5, "mandatory": True},
    {"role": "ai_engineer", "skill": "llm_integration",   "importance": 5, "mandatory": True},
    {"role": "ai_engineer", "skill": "prompt_engineering","importance": 5, "mandatory": True},
    {"role": "ai_engineer", "skill": "rag",               "importance": 4, "mandatory": True},
    {"role": "ai_engineer", "skill": "langchain",         "importance": 4, "mandatory": False},
    {"role": "ai_engineer", "skill": "rest_apis",         "importance": 4, "mandatory": True},
    {"role": "ai_engineer", "skill": "docker",            "importance": 3, "mandatory": False},
    {"role": "ai_engineer", "skill": "hugging_face",      "importance": 4, "mandatory": True},
    {"role": "ai_engineer", "skill": "fine_tuning",       "importance": 3, "mandatory": False},
    {"role": "ai_engineer", "skill": "nlp",               "importance": 4, "mandatory": True},
    {"role": "ai_engineer", "skill": "pytorch",           "importance": 3, "mandatory": False},

    # ── Data Engineer ─────────────────────────────────────────────────────────
    {"role": "data_engineer", "skill": "python",          "importance": 5, "mandatory": True},
    {"role": "data_engineer", "skill": "sql",             "importance": 5, "mandatory": True},
    {"role": "data_engineer", "skill": "apache_spark",    "importance": 4, "mandatory": True},
    {"role": "data_engineer", "skill": "apache_kafka",    "importance": 3, "mandatory": False},
    {"role": "data_engineer", "skill": "airflow",         "importance": 4, "mandatory": True},
    {"role": "data_engineer", "skill": "etl_elt",         "importance": 5, "mandatory": True},
    {"role": "data_engineer", "skill": "data_warehousing","importance": 4, "mandatory": True},
    {"role": "data_engineer", "skill": "data_modeling",   "importance": 4, "mandatory": True},
    {"role": "data_engineer", "skill": "postgresql",      "importance": 4, "mandatory": True},
    {"role": "data_engineer", "skill": "docker",          "importance": 3, "mandatory": False},
    {"role": "data_engineer", "skill": "aws",             "importance": 3, "mandatory": False},
    {"role": "data_engineer", "skill": "linux",           "importance": 4, "mandatory": True},
    {"role": "data_engineer", "skill": "dbt",             "importance": 3, "mandatory": False},

    # ── Backend Developer ─────────────────────────────────────────────────────
    {"role": "backend_developer", "skill": "python",      "importance": 4, "mandatory": False},
    {"role": "backend_developer", "skill": "java",        "importance": 3, "mandatory": False},
    {"role": "backend_developer", "skill": "go",          "importance": 3, "mandatory": False},
    {"role": "backend_developer", "skill": "rest_apis",   "importance": 5, "mandatory": True},
    {"role": "backend_developer", "skill": "sql",         "importance": 5, "mandatory": True},
    {"role": "backend_developer", "skill": "postgresql",  "importance": 4, "mandatory": True},
    {"role": "backend_developer", "skill": "docker",      "importance": 4, "mandatory": True},
    {"role": "backend_developer", "skill": "linux",       "importance": 3, "mandatory": False},
    {"role": "backend_developer", "skill": "fastapi",     "importance": 3, "mandatory": False},
    {"role": "backend_developer", "skill": "redis",       "importance": 3, "mandatory": False},
    {"role": "backend_developer", "skill": "problem_solving","importance": 5,"mandatory": True},

    # ── Frontend Developer ────────────────────────────────────────────────────
    {"role": "frontend_developer", "skill": "javascript",   "importance": 5, "mandatory": True},
    {"role": "frontend_developer", "skill": "typescript",   "importance": 4, "mandatory": True},
    {"role": "frontend_developer", "skill": "react",        "importance": 5, "mandatory": True},
    {"role": "frontend_developer", "skill": "html_css",     "importance": 5, "mandatory": True},
    {"role": "frontend_developer", "skill": "rest_apis",    "importance": 4, "mandatory": True},
    {"role": "frontend_developer", "skill": "problem_solving","importance":4,"mandatory": True},

    # ── Software Engineer ─────────────────────────────────────────────────────
    {"role": "software_engineer", "skill": "python",        "importance": 4, "mandatory": False},
    {"role": "software_engineer", "skill": "java",          "importance": 4, "mandatory": False},
    {"role": "software_engineer", "skill": "sql",           "importance": 4, "mandatory": True},
    {"role": "software_engineer", "skill": "rest_apis",     "importance": 4, "mandatory": True},
    {"role": "software_engineer", "skill": "docker",        "importance": 3, "mandatory": False},
    {"role": "software_engineer", "skill": "problem_solving","importance": 5,"mandatory": True},
    {"role": "software_engineer", "skill": "linux",         "importance": 3, "mandatory": False},

    # ── Product Manager ───────────────────────────────────────────────────────
    {"role": "product_manager", "skill": "product_thinking",     "importance": 5, "mandatory": True},
    {"role": "product_manager", "skill": "communication",        "importance": 5, "mandatory": True},
    {"role": "product_manager", "skill": "stakeholder_management","importance": 5,"mandatory": True},
    {"role": "product_manager", "skill": "project_management",   "importance": 5, "mandatory": True},
    {"role": "product_manager", "skill": "data_visualization",   "importance": 3, "mandatory": False},
    {"role": "product_manager", "skill": "ab_testing",           "importance": 3, "mandatory": False},
    {"role": "product_manager", "skill": "sql",                  "importance": 3, "mandatory": False},
    {"role": "product_manager", "skill": "problem_solving",      "importance": 5, "mandatory": True},

    # ── Research Scientist ────────────────────────────────────────────────────
    {"role": "research_scientist", "skill": "python",             "importance": 5, "mandatory": True},
    {"role": "research_scientist", "skill": "pytorch",            "importance": 5, "mandatory": True},
    {"role": "research_scientist", "skill": "tensorflow",         "importance": 3, "mandatory": False},
    {"role": "research_scientist", "skill": "linear_algebra",     "importance": 5, "mandatory": True},
    {"role": "research_scientist", "skill": "probability",        "importance": 5, "mandatory": True},
    {"role": "research_scientist", "skill": "calculus",           "importance": 5, "mandatory": True},
    {"role": "research_scientist", "skill": "statistics",         "importance": 5, "mandatory": True},
    {"role": "research_scientist", "skill": "nlp",                "importance": 4, "mandatory": False},
    {"role": "research_scientist", "skill": "reinforcement_learning","importance":3,"mandatory": False},
    {"role": "research_scientist", "skill": "hugging_face",       "importance": 4, "mandatory": False},
    {"role": "research_scientist", "skill": "communication",      "importance": 4, "mandatory": True},
]

# Filter out None entries (from the guard above)
ROLE_SKILL_REQUIREMENTS = [r for r in ROLE_SKILL_REQUIREMENTS if r is not None]

# ── Role Transitions (Career Graph Edges) ─────────────────────────────────────
# transition_weight: 0.0–1.0 (higher = more common/observed transition)
# avg_transition_months: typical duration to make this move

ROLE_TRANSITIONS: list[dict] = [
    # Data Analyst → many paths
    {"from": "data_analyst",    "to": "senior_data_analyst","weight": 0.90, "months": 24},
    {"from": "data_analyst",    "to": "data_scientist",     "weight": 0.75, "months": 18},
    {"from": "data_analyst",    "to": "data_engineer",      "weight": 0.60, "months": 24},
    {"from": "data_analyst",    "to": "ml_engineer",        "weight": 0.40, "months": 30},
    {"from": "data_analyst",    "to": "product_manager",    "weight": 0.30, "months": 36},
    {"from": "data_analyst",    "to": "ai_engineer",        "weight": 0.35, "months": 24},

    # Senior Data Analyst → leadership paths
    {"from": "senior_data_analyst", "to": "data_scientist",    "weight": 0.65, "months": 12},
    {"from": "senior_data_analyst", "to": "product_manager",   "weight": 0.40, "months": 18},
    {"from": "senior_data_analyst", "to": "senior_data_scientist","weight": 0.50,"months": 24},

    # Data Scientist → senior/specializations
    {"from": "data_scientist",  "to": "senior_data_scientist","weight": 0.85, "months": 30},
    {"from": "data_scientist",  "to": "ml_engineer",          "weight": 0.70, "months": 18},
    {"from": "data_scientist",  "to": "ai_engineer",          "weight": 0.65, "months": 18},
    {"from": "data_scientist",  "to": "research_scientist",   "weight": 0.35, "months": 36},
    {"from": "data_scientist",  "to": "product_manager",      "weight": 0.25, "months": 30},

    # Senior Data Scientist
    {"from": "senior_data_scientist", "to": "senior_ml_engineer","weight": 0.45,"months": 18},
    {"from": "senior_data_scientist", "to": "research_scientist", "weight": 0.40,"months": 24},

    # ML Engineer → senior/adjacent
    {"from": "ml_engineer",     "to": "senior_ml_engineer",   "weight": 0.85, "months": 30},
    {"from": "ml_engineer",     "to": "ai_engineer",           "weight": 0.70, "months": 18},
    {"from": "ml_engineer",     "to": "data_engineer",         "weight": 0.45, "months": 18},

    # AI Engineer
    {"from": "ai_engineer",     "to": "senior_ml_engineer",   "weight": 0.55, "months": 24},
    {"from": "ai_engineer",     "to": "research_scientist",   "weight": 0.35, "months": 30},

    # Data Engineer → senior/adjacent
    {"from": "data_engineer",   "to": "senior_data_engineer", "weight": 0.85, "months": 30},
    {"from": "data_engineer",   "to": "ml_engineer",          "weight": 0.50, "months": 24},
    {"from": "data_engineer",   "to": "software_engineer",    "weight": 0.35, "months": 12},

    # Backend Developer
    {"from": "backend_developer","to": "senior_backend_developer","weight": 0.85,"months": 30},
    {"from": "backend_developer","to": "full_stack_developer",    "weight": 0.60,"months": 12},
    {"from": "backend_developer","to": "data_engineer",           "weight": 0.40,"months": 24},
    {"from": "backend_developer","to": "software_engineer",       "weight": 0.70,"months": 6},

    # Frontend Developer
    {"from": "frontend_developer","to": "full_stack_developer","weight": 0.75, "months": 18},
    {"from": "frontend_developer","to": "software_engineer",   "weight": 0.60, "months": 12},

    # Software Engineer → any
    {"from": "software_engineer","to": "backend_developer",    "weight": 0.70, "months": 6},
    {"from": "software_engineer","to": "data_engineer",        "weight": 0.50, "months": 18},
    {"from": "software_engineer","to": "ml_engineer",          "weight": 0.45, "months": 24},
    {"from": "software_engineer","to": "full_stack_developer", "weight": 0.65, "months": 12},
]
