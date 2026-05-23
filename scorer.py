import json
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent

# ── Module-level cache: read services.json once per process ──────────────────
_SERVICES_CACHE: Optional[Dict[str, Any]] = None

BOOSTS = {
    "cost_efficient": ["Cloud Run", "Cloud Functions", "BigQuery", "Cloud SQL PostgreSQL", "Cloud Storage", "App Engine Standard"],
    "scalable": ["GKE Autopilot", "Cloud Spanner", "Firestore", "Pub/Sub", "Cloud Load Balancing", "Dataflow"],
    "high_performance": ["Memorystore", "Bigtable", "Cloud Spanner", "Cloud CDN", "Compute Engine"],
    "low_resource_poc": ["App Engine Standard", "Cloud Functions", "Cloud Run", "Cloud SQL PostgreSQL", "Cloud Storage"],
    "analytics": ["BigQuery", "Dataflow", "Cloud Storage"],
    "event_driven": ["Pub/Sub", "Cloud Run", "Cloud Functions", "Dataflow"],
    "relational_database": ["Cloud SQL PostgreSQL", "Cloud Spanner"],
    "nosql_database": ["Firestore", "Bigtable"],
    "caching": ["Memorystore"],
    "rag_required": ["Vertex AI", "BigQuery", "Cloud Storage"],
    "external_api_required": ["Cloud Run", "Cloud Functions"],
    "banking_compliance": ["VPC Service Controls", "Private Google Access", "Cloud Logging", "Cloud Monitoring"],
    "observability_required": ["Cloud Logging", "Cloud Monitoring", "Cloud Trace", "Error Reporting"]
}

def load_services() -> Dict[str, Any]:
    global _SERVICES_CACHE
    if _SERVICES_CACHE is None:
        json_path = BASE_DIR / "services.json"
        with open(json_path, "r") as f:
            _SERVICES_CACHE = json.load(f)
    return _SERVICES_CACHE

def score_services(constraints: List[str], budget_preference: str = "medium") -> List[Dict[str, Any]]:
    """
    Weighted scoring engine for GCP services based on active constraints and budget.
    """
    services = load_services()
    scored_list = []
    
    budget_preference = budget_preference.lower()
    
    for name, meta in services.items():
        # Retrieve scores (scale 1 to 10)
        cost_val = meta.get("cost_score", 5)
        scalability_val = meta.get("scalability_score", 5)
        performance_val = meta.get("performance_score", 5)
        complexity_val = meta.get("complexity_score", 5)
        poc_val = meta.get("poc_score", 5)
        
        # Calculate dynamic base score based on budget preference
        if budget_preference == "low":
            # Emphasize low cost and high simplicity / low complexity
            base_score = (cost_val * 3.0) + (poc_val * 2.0) + scalability_val + performance_val - (complexity_val * 1.5)
        elif budget_preference == "high":
            # Emphasize scalability and performance, cost is secondary
            base_score = (scalability_val * 3.0) + (performance_val * 3.0) + (cost_val * 0.5) - (complexity_val * 0.5) + poc_val
        else:  # medium
            base_score = (cost_val * 1.5) + (scalability_val * 1.5) + (performance_val * 1.5) + poc_val - complexity_val
            
        # Add boosts for matching constraints
        boost_count = 0
        for constraint in constraints:
            if constraint in BOOSTS and name in BOOSTS[constraint]:
                base_score += 10.0  # Apply strong boost for constraint matches
                boost_count += 1
                
        # Also check explicit service level constraints support
        for c in meta.get("supports_constraints", []):
            if c in constraints:
                base_score += 5.0
                
        scored_list.append({
            "name": name,
            "category": meta.get("category"),
            "description": meta.get("description"),
            "score": round(max(0.0, base_score), 1),
            "cost_tier": meta.get("cost_tier", "MEDIUM"),
            "bom_unit": meta.get("bom_unit", "units"),
            "tradeoffs": meta.get("tradeoffs", []),
            "supports_constraints": meta.get("supports_constraints", []),
            "boost_count": boost_count
        })
        
    # Sort descending by score
    scored_list.sort(key=lambda x: x["score"], reverse=True)
    return scored_list[:8]

def generate_tradeoffs(recommended_service_names: List[str]) -> List[str]:
    """
    Generates exact impact warnings based on the presence of services in the recommended list.
    """
    selected_set = set(recommended_service_names)
    tradeoffs = []
    
    # - Spanner improves scalability but increases cost compared to Cloud SQL.
    if "Cloud Spanner" in selected_set and "Cloud SQL PostgreSQL" in selected_set:
        tradeoffs.append("Spanner improves scalability but increases cost compared to Cloud SQL.")
        
    # - GKE Autopilot is powerful but more complex than Cloud Run for a POC.
    if "GKE Autopilot" in selected_set and "Cloud Run" in selected_set:
        tradeoffs.append("GKE Autopilot is powerful but more complex than Cloud Run for a POC.")
        
    # - Bigtable is high-performance but overkill for small workloads.
    if "Bigtable" in selected_set:
        tradeoffs.append("Bigtable is high-performance but overkill for small workloads.")
        
    # - Compute Engine gives control but increases operational effort.
    if "Compute Engine" in selected_set:
        tradeoffs.append("Compute Engine gives control but increases operational effort.")
        
    # - Cloud Run is cost-effective but may not suit ultra-low latency workloads.
    if "Cloud Run" in selected_set and ("Memorystore" in selected_set or "Cloud CDN" in selected_set):
        tradeoffs.append("Cloud Run is cost-effective but may not suit ultra-low latency workloads.")
        
    # - Observability improves governance but adds monitoring cost and implementation effort.
    if any(s in selected_set for s in ["Cloud Logging", "Cloud Monitoring", "Cloud Trace", "Error Reporting"]):
        tradeoffs.append("Observability improves governance but adds monitoring cost and implementation effort.")
        
    return tradeoffs
