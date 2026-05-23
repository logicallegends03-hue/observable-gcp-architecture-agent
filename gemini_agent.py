import os
import re
import time
import logging
from typing import Dict, List, Any, Tuple, Optional
from google import genai
from google.genai import types

logger = logging.getLogger("gcp-architecture-agent-observability")

# ── Module-level client singleton ────────────────────────────────────────────
_CLIENT: Optional[genai.Client] = None

def get_client() -> genai.Client:
    """
    Returns a cached Gemini client, creating it only on first call.
    Supports two auth modes:
      - Vertex AI (Cloud Run / ADC):  GOOGLE_GENAI_USE_VERTEXAI=true
      - AI Studio API key (local dev): GOOGLE_GENAI_USE_VERTEXAI=false + GOOGLE_API_KEY
    """
    global _CLIENT
    if _CLIENT is None:
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
        if use_vertex:
            project  = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            _CLIENT  = genai.Client(vertexai=True, project=project, location=location)
        else:
            # AI Studio mode — SDK picks up GOOGLE_API_KEY automatically
            _CLIENT = genai.Client()
    return _CLIENT


# ── Solution parser ───────────────────────────────────────────────────────────

def parse_solutions(text: str) -> Dict[str, str]:
    """
    Splits Gemini's single response into the 3 solution sections using
    the emoji anchors that the prompt guarantees.
    """
    cost = re.search(r'(##\s*💰.*?)(?=##\s*⚡|##\s*🧪|\Z)', text, re.DOTALL)
    perf = re.search(r'(##\s*⚡.*?)(?=##\s*💰|##\s*🧪|\Z)', text, re.DOTALL)
    poc  = re.search(r'(##\s*🧪.*?)(?=##\s*💰|##\s*⚡|\Z)', text, re.DOTALL)
    return {
        "cost":        cost.group(1).strip() if cost else text,
        "performance": perf.group(1).strip() if perf else "",
        "poc":         poc.group(1).strip()  if poc  else "",
    }


# ── Main generation function ──────────────────────────────────────────────────

def generate_architecture(
    requirement: str,
    constraints: List[str],
    cost_services: List[Dict[str, Any]],
    perf_services: List[Dict[str, Any]],
    poc_services:  List[Dict[str, Any]],
    bill_of_materials: List[Dict[str, Any]],
    tradeoffs: List[str]
) -> Tuple[Dict[str, str], bool, float, str]:
    """
    Generates 3 architecture solutions via Gemini 2.5 Flash:
      💰 Cost Efficient | ⚡ High Performance | 🧪 POC / Low Resource
    Returns (solutions_dict, fallback_used, latency_ms, error_str).
    """
    start_time = time.perf_counter()

    constraint_str = ", ".join(constraints) if constraints else "none"

    def fmt(svcs: List[Dict[str, Any]]) -> str:
        return "\n".join(
            f"  • {s['name']} (score={s['score']}, cost={s['cost_tier']}, category={s['category']})"
            for s in svcs
        )

    bom_str = "\n".join(
        f"  • {item['service']}: {item['description']} → {item['price']}"
        for item in bill_of_materials
    )
    tradeoff_str = (
        "\n".join(f"  ⚠ {t}" for t in tradeoffs)
        if tradeoffs else "  • No critical tradeoffs detected."
    )

    prompt = f"""You are a senior GCP cloud architect. Generate exactly 3 distinct architectural solutions for the requirement below.

## User Requirement
"{requirement}"

## Detected Constraints
{constraint_str}

## Scored Service Sets

**Cost Efficient Services** (optimised for low spend):
{fmt(cost_services)}

**High Performance Services** (optimised for speed & scale):
{fmt(perf_services)}

**POC / Low Resource Services** (optimised for simplicity & quick launch):
{fmt(poc_services)}

## Bill of Materials (reference for cost estimates)
{bom_str}

## Risk Flags
{tradeoff_str}

---
Write exactly 3 solutions. Start each section with EXACTLY these headers (keep the emojis):

## 💰 Cost Efficient Solution
## ⚡ High Performance Solution
## 🧪 POC / Low Resource Solution

Each solution MUST contain these sub-sections:
### Services Used
### Architecture Overview
(Include a short ASCII data-flow diagram)
### Why It Fits
(One bullet per service)
### Cost / Performance / Simplicity View
### Deployment Snippet
(A ready-to-run `gcloud` command)
### Key Tradeoffs & Mitigations

Rules:
- Use only the services from the respective scored set for each solution.
- Be specific — cite service names, config values, and real GCP pricing.
- Do NOT add any introductory text before ## 💰.
"""

    try:
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
        if use_vertex and not os.getenv("GOOGLE_CLOUD_PROJECT"):
            raise ValueError("GOOGLE_CLOUD_PROJECT not set.")
        if not use_vertex and not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not set.")

        client   = get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=8192
            )
        )

        latency = (time.perf_counter() - start_time) * 1000.0

        if response.text:
            return parse_solutions(response.text), False, latency, ""
        else:
            raise ValueError("Empty response from Gemini API.")

    except Exception as e:
        latency   = (time.perf_counter() - start_time) * 1000.0
        error_msg = f"{type(e).__name__}: {e}"
        logger.error("Gemini call failed — using fallback. Reason: %s", error_msg)
        fallback = _fallback_three_solutions(
            requirement, constraints,
            cost_services, perf_services, poc_services,
            bill_of_materials, tradeoffs
        )
        return fallback, True, latency, error_msg


# ── Deterministic fallback ─────────────────────────────────────────────────────

def _fallback_three_solutions(
    requirement: str,
    constraints: List[str],
    cost_services: List[Dict[str, Any]],
    perf_services: List[Dict[str, Any]],
    poc_services:  List[Dict[str, Any]],
    bill_of_materials: List[Dict[str, Any]],
    tradeoffs: List[str]
) -> Dict[str, str]:
    """Deterministic fallback returning all 3 solutions as a dict."""

    bom_str = "\n".join(
        f"- **{item['service']}**: {item['description']} ({item['price']})"
        for item in bill_of_materials
    )
    tradeoff_str = (
        "\n".join(f"- {t}" for t in tradeoffs)
        if tradeoffs else "- No high-risk tradeoffs detected."
    )

    def mapping(svcs: List[Dict[str, Any]]) -> str:
        lines = []
        for c in constraints:
            matched = [s["name"] for s in svcs if c in s.get("supports_constraints", [])]
            lines.append(f"- **{c}**: {', '.join(matched) if matched else 'general parameter'}")
        return "\n".join(lines) if lines else "- No specific constraints active."

    cost_names = [s["name"] for s in cost_services]
    perf_names = [s["name"] for s in perf_services]
    poc_names  = [s["name"] for s in poc_services]

    cost_md = f"""## 💰 Cost Efficient Solution

> Serverless-first architecture optimised for minimum monthly spend.

### Services Used
{", ".join(cost_names[:6])}

### Architecture Overview
```
[Cloud Load Balancing]
        ↓
  [Cloud Run API]  ←→  [Memorystore Redis]
     ↓        ↓
[Cloud SQL]  [Pub/Sub]
                ↓
          [Dataflow] → [BigQuery]
                            ↑
                    [VPC Service Controls]
```

### Why It Fits
- **Cloud Run**: scales to zero, pay-per-request — ideal for variable traffic.
- **Cloud SQL PostgreSQL**: managed RDBMS, ACID compliant, no ops overhead.
- **Pub/Sub**: decouples ingestion spikes from processing; near-zero idle cost.
- **BigQuery**: serverless analytics, pay-per-query, no cluster to provision.
- **Vertex AI**: on-demand LLM/RAG calls, no model hosting required.

### Cost / Performance / Simplicity View
Estimated monthly spend (pay-as-you-go):
{bom_str}

### Deployment Snippet
```bash
gcloud run deploy api-service \\
  --source . --region us-central1 \\
  --allow-unauthenticated \\
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID
```

### Key Tradeoffs & Mitigations
{tradeoff_str}
- **Cold starts**: mitigate with `--min-instances 1` on Cloud Run.
- **SQL bottleneck**: add read replicas or Memorystore cache for hot queries.
"""

    perf_md = f"""## ⚡ High Performance Solution

> High-throughput architecture built for sub-50ms latency and horizontal scale.

### Services Used
{", ".join(perf_names[:6])}

### Architecture Overview
```
[Global LB + Cloud CDN]
        ↓
  [GKE Autopilot]  ←→  [Memorystore Redis]
     ↓        ↓
[Spanner]  [Pub/Sub]
                ↓
          [Dataflow] → [Bigtable / BigQuery]
                              ↑
                  [VPC Service Controls]
```

### Why It Fits
- **GKE Autopilot**: fine-grained container scheduling for latency-sensitive pods.
- **Cloud Spanner**: globally consistent SQL at any scale, 99.999% SLA.
- **Memorystore Redis**: sub-millisecond cache layer in front of the DB tier.
- **Cloud CDN**: edge-caches static/repeated responses, reduces origin hits.
- **Bigtable**: columnar, low-latency reads for time-series & analytical queries.

### Cost / Performance / Simplicity View
- Higher cost tier — justified by SLA and global distribution needs.
- Expected p99 API latency: **< 50 ms** (cached) / **< 200 ms** (cold).
- Spanner minimum cost: ~$65/month even at low traffic.

### Deployment Snippet
```bash
gcloud container clusters create-auto perf-cluster \\
  --region us-central1 --project $PROJECT_ID

kubectl apply -f k8s/deployment.yaml
```

### Key Tradeoffs & Mitigations
- **Complexity**: GKE requires Kubernetes expertise vs Cloud Run's simplicity.
- **Spanner cost floor**: switch to Cloud SQL if global scale is not yet needed.
- **Bigtable overkill**: use BigQuery for analytics unless sub-10ms reads required.
"""

    poc_md = f"""## 🧪 POC / Low Resource Solution

> Minimal viable architecture to validate the concept in under a day, under $30/month.

### Services Used
{", ".join(poc_names[:5])}

### Architecture Overview
```
[Cloud Run (single service)]
      ↓            ↓
[Cloud SQL    [Cloud Storage]
  micro]           ↓
              [Vertex AI API]
              (on-demand calls)
```

### Why It Fits
- **Cloud Run**: zero infra setup, deployable in minutes from source.
- **Cloud SQL (db-f1-micro)**: smallest managed DB, sufficient for POC load.
- **Cloud Storage**: cheap blob/asset store — no server, no maintenance.
- **Vertex AI**: call Gemini on-demand; no model hosting or GPU required.
- **Cloud Functions**: lightweight event triggers without a full service.

### Cost / Performance / Simplicity View
- Estimated: **< $30/month** for typical POC traffic levels.
- Deploy-to-demo in under 30 minutes.
- Scales to a production pilot by upgrading Cloud SQL tier only.

### Deployment Snippet
```bash
gcloud run deploy poc-app \\
  --source . --region us-central1 \\
  --allow-unauthenticated \\
  --memory 512Mi --max-instances 3
```

### Key Tradeoffs & Mitigations
- **Not production-ready**: no HA, limited autoscaling, no CDN.
- **SQL micro bottleneck**: upgrade to `db-g1-small` before load testing.
- **No async pipeline**: add Pub/Sub + Cloud Functions when event volume grows.
"""

    return {"cost": cost_md, "performance": perf_md, "poc": poc_md}
