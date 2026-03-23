"""
MentorOS – Application Constants
Centralized mapping for subjects, AI templates, and domain logic.
"""

# Subject Mastery Mapping
# Keywords determine which categories tasks fall into for analytics.
SUBJECT_MAP = {
    "System Design": ["system design", "architecture", "distributed", "scalability", "microservices"],
    "Data Structures": ["data structure", "algorithm", "tree", "graph", "sorting", "complexity"],
    "ML Fundamentals": ["ml", "machine learning", "neural", "tensor", "model training", "deep learning", "inference"]
}

# AI Planner Topics
PLANNER_TOPICS = [
    "Advanced Data Structures",
    "Microservices Architecture",
    "Concurrency & Async Programming",
    "System Optimization & Benchmarking",
    "Machine Learning Fundamentals",
    "Distributed Consensus (Raft/Paxos)",
    "API Design & Security Patterns"
]

# AI Teacher Default Explain Templates
EXPLAIN_TEMPLATE = "{topic} is a conceptual framework tailored for {level} learners to optimize systems efficiently."
ANALOGY_TEMPLATE = "Think of {topic} like specialized tools organized in a master craftsman's workshop—ready when exactly needed."
EXAMPLE_TEMPLATE = "def implement_{token}():\n    return 'System Optimized'"

# Analytics Default Colors
SUBJECT_COLORS = {
    "System Design": "var(--a1)",
    "Data Structures": "var(--a2)",
    "ML Fundamentals": "var(--gold)"
}
