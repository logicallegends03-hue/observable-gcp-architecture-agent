from typing import List, Tuple, Set

ALL_RELATIONSHIPS = [
    ("Cloud Run", "integrates_with", "Pub/Sub"),
    ("Pub/Sub", "triggers", "Cloud Run"),
    ("Pub/Sub", "feeds", "Dataflow"),
    ("Dataflow", "writes_to", "BigQuery"),
    ("BigQuery", "stores_analytics", "Cloud Storage"),
    ("Vertex AI", "powers", "Gemini reasoning"),
    ("Cloud Logging", "observes", "Cloud Run"),
    ("Cloud Monitoring", "monitors", "Cloud Run"),
    ("Cloud Trace", "traces", "Cloud Run"),
    ("Error Reporting", "captures_errors_from", "Cloud Run"),
    ("VPC Service Controls", "secures", "BigQuery"),
    ("Private Google Access", "enables_private_access_to", "Google APIs"),
    ("Memorystore", "caches_for", "Cloud Run"),
    ("Cloud CDN", "accelerates", "Cloud Storage")
]

def get_relationships(selected_services: List[str]) -> List[Tuple[str, str, str]]:
    """
    Returns relationships where at least one of the nodes is in the selected services list.
    """
    selected_set = {s.lower() for s in selected_services}
    matched_relationships = []
    
    for source, rel, target in ALL_RELATIONSHIPS:
        # Check if source or target matches any of our selected service names
        # Note: target or source might be external tags like "Gemini reasoning" or "Google APIs"
        # We also check if they match substrings (e.g. "Cloud SQL PostgreSQL" matches "Cloud SQL")
        source_match = False
        target_match = False
        
        for s in selected_set:
            if s in source.lower() or source.lower() in s:
                source_match = True
            if s in target.lower() or target.lower() in s:
                target_match = True
                
        if source_match or target_match:
            matched_relationships.append((source, rel, target))
            
    return matched_relationships

def generate_dot_format(relationships: List[Tuple[str, str, str]]) -> str:
    """
    Generates a DOT Graphviz string to render the relationships in Streamlit.
    """
    dot = "digraph G {\n"
    dot += '  graph [rankdir=LR, bgcolor="transparent", color="#30363d"];\n'
    dot += '  node [shape=box, style="filled,rounded", fillcolor="#161b22", color="#58a6ff", fontcolor="#c9d1d9", fontname="sans-serif", fontsize=11];\n'
    dot += '  edge [color="#8b949e", fontcolor="#8b949e", fontname="sans-serif", fontsize=9];\n'
    
    for src, rel, tgt in relationships:
        dot += f'  "{src}" -> "{tgt}" [label="{rel}"];\n'
        
    dot += "}"
    return dot
