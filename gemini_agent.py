import os
import time
from typing import Dict, List, Any, Tuple
from google import genai
from google.genai import types

# ── Module-level client singleton ─────────────────────────────────────────────
# Avoid re-initialising on every call; the client is stateless and thread-safe.
_CLIENT: genai.Client | None = None

def get_client() -> genai.Client:
    """
    Returns a cached Gemini/Vertex AI client, creating it only on first call.
    """
    global _CLIENT
    if _CLIENT is None:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
        _CLIENT = genai.Client(vertexai=use_vertex, project=project, location=location)
    return _CLIENT

def generate_architecture(
    requirement: str,
    constraints: List[str],
    services: List[Dict[str, Any]],
    bill_of_materials: List[Dict[str, Any]],
    tradeoffs: List[str]
) -> Tuple[str, bool, float]:
    """
    Generates architecture explanation using Gemini 2.5 Flash on Vertex AI.
    If it fails (due to missing project/auth/credentials), returns a robust fallback explanation.
    Returns (explanation_markdown, fallback_used, gemini_latency_ms).
    """
    start_time = time.perf_counter()

    # Format inputs for prompt
    service_names = [s["name"] for s in services]
    score_summaries = "\n".join(
        f"  • {s['name']}: score={s['score']}, cost_tier={s['cost_tier']}, category={s['category']}"
        for s in services
    )
    bom_summaries = "\n".join(
        f"  • {item['service']}: {item['description']} → {item['price']}"
        for item in bill_of_materials
    )
    constraint_str = ", ".join(constraints) if constraints else "none"
    tradeoff_str = "\n".join(f"  ⚠ {t}" for t in tradeoffs) if tradeoffs else "  • No critical tradeoffs detected."

    prompt = f"""You are a senior GCP cloud architect embedded in an agentic AI optimisation platform.
A scoring engine has already ranked services against the user's constraints — your job is to turn those results into a compelling, concrete architectural proposal.

## User Requirement
"{requirement}"

## Active Constraints
{constraint_str}

## Scoring Engine — Top Recommendations
{score_summaries}

## Bill of Materials
{bom_summaries}

## Tradeoff / Risk Assessment
{tradeoff_str}

---
Write a professional, markdown-formatted architectural proposal with these EXACT sections (use ## headers):

## 1. Recommended Architecture
(Describe the overall topology in 3-5 sentences. Include a short ASCII diagram showing the main data-flow.)

## 2. Why These Services Fit
(One bullet per service explaining WHY the score reflects the requirement.)

## 3. Constraint-to-Service Mapping
(Table: Constraint | Serving Service | Rationale)

## 4. Impact Assessment
(Address each tradeoff warning and how to mitigate it.)

## 5. Cost Efficiency View
(Concrete monthly estimate using BOM prices. Identify the top cost driver and how to reduce it.)

## 6. Scalability View
(Explain how the architecture scales at 10×, 100× load. Name specific GCP autoscaling mechanisms.)

## 7. Performance View
(Expected p99 latency per tier. Identify and fix the slowest hop.)

## 8. Observability Plan
(Logging → Monitoring → Tracing → Alerting pipeline. Which Cloud Ops services and what dashboards/alerts to create.)

## 9. RAG / External API Extension
(If rag_required or external_api_required constraints are active, give a concrete integration pattern; otherwise briefly note how it could be added.)

## 10. Cloud Run Deployment
(Provide a ready-to-run `gcloud` snippet to build and deploy the main service.)

## 11. Future Roadmap
(3 numbered next steps with estimated effort: Easy / Medium / Hard.)

Rules: be specific — cite service names, config values, and real GCP pricing where possible. No vague filler.
"""

    try:
        # Fail fast if project is unset — avoids SDK timeout hanging the UI
        if not os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true":
            raise ValueError("GOOGLE_CLOUD_PROJECT not set — using local fallback.")

        client = get_client()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096   # was 2500 — enough for all 11 sections
            )
        )
        
        latency = (time.perf_counter() - start_time) * 1000.0
        
        if response.text:
            return response.text, False, latency
        else:
            raise ValueError("Received empty response from Gemini API.")
            
    except Exception as e:
        # Catch authentication, configuration, or API errors and use fallback
        latency = (time.perf_counter() - start_time) * 1000.0
        fallback_markdown = generate_fallback_architecture(requirement, constraints, services, bill_of_materials, tradeoffs)
        return fallback_markdown, True, latency

def generate_fallback_architecture(
    requirement: str,
    constraints: List[str],
    services: List[Dict[str, Any]],
    bill_of_materials: List[Dict[str, Any]],
    tradeoffs: List[str]
) -> str:
    """
    Generates a deterministic, comprehensive, and well-structured fallback proposal.
    """
    service_names = [s["name"] for s in services]
    bom_str = "\n".join([f"- **{item['service']}**: {item['description']} ({item['price']})" for item in bill_of_materials])
    tradeoff_str = "\n".join([f"- {t}" for t in tradeoffs]) if tradeoffs else "- No high-risk tradeoffs detected for this combination."
    
    # Map constraints to services supporting them
    mapping_lines = []
    for c in constraints:
        matching_svcs = [s["name"] for s in services if c in s.get("supports_constraints", [])]
        if matching_svcs:
            mapping_lines.append(f"- **{c}** mapped to: {', '.join(matching_svcs)}")
        else:
            mapping_lines.append(f"- **{c}** general system parameter")
    mapping_str = "\n".join(mapping_lines) if mapping_lines else "- No specific constraints active."
    
    fallback_markdown = f"""# GCP Architecture Recommendation (Deterministic Fallback)

> [!NOTE]
> **Observability Alert**: Vertex AI/Gemini was unreachable or the `GOOGLE_CLOUD_PROJECT` environment variable was not set. The platform has automatically compiled this recommendation using the built-in architectural template.

## 1. Recommended Architecture
Based on your requirement: *"{requirement}"*, we have designed a secure, production-grade cloud topology utilizing the following core recommended services: **{", ".join(service_names[:5])}**.

Here is the high-level architecture diagram:
```text
                     +---------------------------------------+
                     |         Cloud Load Balancing          |
                     +-------------------+-------------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     |             Cloud Run                 | <---+ Private Google Access
                     +----+-------------+----------------+---+
                          |             |                |
            +-------------+             |                +---------------+
            | (Ingress)                 | (Store)                        | (AI Reasoning)
            v                           v                                v
   +--------+--------+      +-----------+-----------+           +--------+--------+
   |    Pub/Sub      |      | Cloud SQL PostgreSQL  |           |    Vertex AI    |
   +--------+--------+      +-----------------------+           +-----------------+
            |
            v
   +--------+--------+      +-----------------------+
   |    Dataflow     | ---> |       BigQuery        | <--- VPC Service Controls
   +-----------------+      +-----------------------+
```

## 2. Why the services fit
- **Cloud Run**: Runs your API containers serverlessly, automatically scaling instances based on traffic and scaling to zero to minimize costs during quiet periods.
- **Cloud SQL PostgreSQL**: Fully managed database instance providing relational SQL compatibility, ACID compliance, and secure automated snapshots.
- **Pub/Sub**: Facilitates decoupled event ingestion, acting as a reliable messaging buffer under spikes.
- **BigQuery**: Enables serverless analytics over massive datasets with partition configurations to manage cost.
- **Vertex AI**: Provides pre-trained foundation models (Gemini) for building RAG semantic systems.

## 3. Constraint-to-service mapping
{mapping_str}

## 4. Impact Assessment
{tradeoff_str}

## 5. Cost Efficiency View
- **Serverless Scaling**: By keeping compute components on Cloud Run, you only pay for active processing.
- **Object Storage**: Heavy files reside in Cloud Storage, minimizing expensive database disk usage.

## 6. Scalability View
- **Asynchronous Ingest**: Pub/Sub decouples API traffic spikes from processing lines, avoiding backend timeouts.
- **Autoscaled Processing**: Dataflow dynamically allocates processing workers to match queue backlogs.

## 7. Performance View
- **Cache Acceleration**: Memorystore Redis serves as a transient database read cache, speeding up query execution.
- **Global Delivery**: Cloud CDN caches assets closer to users, improving load latencies.

## 8. Observability Plan
- **Cloud Logging**: Collects application traces and structured audit logs.
- **Cloud Monitoring**: Configures automated SLIs, alerts, and dashboards.
- **Cloud Trace & Error Reporting**: Diagnoses latency bottlenecks and tracks exception patterns.

## 9. RAG / External API Extension
- **Vector Search**: Vertex AI stores document embeddings, which are queried by the API to feed context to LLMs.
- **Egress Security**: External API integration runs through Cloud NAT and Private Google Access for secure routing.

## 10. Cloud Run Deployment Suggestion
To deploy the main application container to Cloud Run:
```bash
# Build the Docker container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/architecture-optimizer-api:v1 .

# Deploy to Cloud Run
gcloud run deploy architecture-optimizer-api \\
  --image gcr.io/YOUR_PROJECT_ID/architecture-optimizer-api:v1 \\
  --platform managed \\
  --region us-central1 \\
  --allow-unauthenticated \\
  --vpc-egress=private-ranges-only
```

## 11. Future Roadmap
1. **Database Upgrade**: Switch database from Cloud SQL to Cloud Spanner if global horizontal scale is required.
2. **Multi-Region Redundancy**: Set up active-active deployments using external Cloud Load Balancing.
3. **LLM Orchestration**: Introduce custom orchestrators to govern complex prompt workflows.
"""
    return fallback_markdown
