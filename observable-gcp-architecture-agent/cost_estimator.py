from typing import List, Dict, Any, Tuple

# Detailed simulated Bill of Materials (BOM) specs
BOM_DETAILS = {
    "Cloud Run": {"description": "2 serverless containers, autoscaling, moderate API traffic", "cost_tier": "LOW", "price": "$15/month"},
    "Cloud Functions": {"description": "100k invocations/month, lightweight background workers", "cost_tier": "LOW", "price": "$5/month"},
    "BigQuery": {"description": "Serverless analytics warehouse, pay-per-query (1 TB scanned)", "cost_tier": "LOW", "price": "$10/month"},
    "Cloud SQL PostgreSQL": {"description": "1 managed database instance (db-f1-micro, 10GB SSD)", "cost_tier": "MEDIUM", "price": "$45/month"},
    "GKE Autopilot": {"description": "Autopilot Kubernetes cluster, 2 small workloads", "cost_tier": "MEDIUM", "price": "$60/month"},
    "Cloud Storage": {"description": "100 GB regional standard object storage", "cost_tier": "LOW", "price": "$5/month"},
    "Compute Engine": {"description": "1 e2-medium instance (2 vCPUs, 4 GB memory) with 50GB disk", "cost_tier": "MEDIUM", "price": "$25/month"},
    "Cloud Spanner": {"description": "1 regional database instance, 100 processing units (PUs)", "cost_tier": "HIGH", "price": "$65/month"},
    "Firestore": {"description": "Serverless document storage, 1M read/write operations", "cost_tier": "LOW", "price": "$15/month"},
    "Pub/Sub": {"description": "Managed messaging event ingestion, 10M messages", "cost_tier": "LOW", "price": "$8/month"},
    "Cloud Load Balancing": {"description": "1 global HTTPS load balancer, SSL routing rules", "cost_tier": "MEDIUM", "price": "$25/month"},
    "Dataflow": {"description": "Managed streaming pipeline worker resources", "cost_tier": "MEDIUM", "price": "$70/month"},
    "Memorystore": {"description": "1 Redis cache node, 1GB memory capacity", "cost_tier": "MEDIUM", "price": "$30/month"},
    "Bigtable": {"description": "1 development node, SSD storage, analytical column database", "cost_tier": "HIGH", "price": "$90/month"},
    "Cloud CDN": {"description": "CDN cache egress edge transfers, 500GB traffic", "cost_tier": "LOW", "price": "$12/month"},
    "App Engine Standard": {"description": "1 standard F1 instance hosting runtime", "cost_tier": "LOW", "price": "$20/month"},
    "Vertex AI": {"description": "Gemini API token volume, foundation model calls", "cost_tier": "LOW", "price": "$15/month"},
    "Cloud Logging": {"description": "Basic application logs, 50 GB ingestion volume", "cost_tier": "LOW", "price": "$25/month"},
    "Cloud Monitoring": {"description": "Custom dashboards, automated metric checks", "cost_tier": "LOW", "price": "$10/month"},
    "Cloud Trace": {"description": "Distributed API call tracer span collection", "cost_tier": "LOW", "price": "$5/month"},
    "Error Reporting": {"description": "Exception trace aggregator and crash notifier", "cost_tier": "LOW", "price": "$0/month"},
    "VPC Service Controls": {"description": "Compliance data boundary protection controls", "cost_tier": "LOW", "price": "$0/month"},
    "Private Google Access": {"description": "Secure private routing interfaces to Google APIs", "cost_tier": "LOW", "price": "$0/month"}
}

def estimate_cost(selected_services: List[str]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns the overall cost tier and a detailed simulated bill of materials.
    """
    bom = []
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for svc in selected_services:
        details = BOM_DETAILS.get(svc, {
            "description": "Standard service usage tier",
            "cost_tier": "LOW",
            "price": "$10/month"
        })
        bom.append({
            "service": svc,
            "description": details["description"],
            "cost_tier": details["cost_tier"],
            "price": details["price"]
        })
        
        tier = details["cost_tier"]
        if tier == "HIGH":
            high_count += 1
        elif tier == "MEDIUM":
            medium_count += 1
        else:
            low_count += 1
            
    # Overall cost tier rules:
    # - Includes Spanner/Bigtable/GKE together (or multiple HIGH nodes) = HIGH
    # - Includes Cloud SQL/Dataflow/GKE = MEDIUM
    # - Mostly serverless = LOW
    selected_set = set(selected_services)
    
    if (("Cloud Spanner" in selected_set or "Bigtable" in selected_set) and 
        ("GKE Autopilot" in selected_set or "Dataflow" in selected_set or "Cloud SQL PostgreSQL" in selected_set)):
        overall_tier = "HIGH"
    elif high_count >= 2:
        overall_tier = "HIGH"
    elif "Cloud SQL PostgreSQL" in selected_set or "Dataflow" in selected_set or "GKE Autopilot" in selected_set or medium_count >= 2:
        overall_tier = "MEDIUM"
    else:
        overall_tier = "LOW"
        
    return overall_tier, bom
