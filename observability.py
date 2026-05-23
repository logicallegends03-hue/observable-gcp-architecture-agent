import time
import logging
import json
from typing import Dict, Any

# Configure python logging to stream to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("gcp-architecture-agent-observability")

def start_timer() -> float:
    """
    Starts a timer returning the high-precision timestamp.
    """
    return time.perf_counter()

def end_timer(start: float) -> float:
    """
    Calculates the elapsed time in milliseconds from the start time.
    """
    return (time.perf_counter() - start) * 1000.0

def build_observability_metrics(
    total_time_ms: float,
    constraints_count: int,
    services_count: int,
    tradeoffs_count: int,
    cost_tier: str,
    fallback_used: bool,
    gemini_latency_ms: float,
    edges_count: int
) -> Dict[str, Any]:
    """
    Builds the structured metric dictionary and records it via structured logs.
    """
    metrics = {
        "total_generation_time_ms": round(total_time_ms, 2),
        "constraints_detected_count": constraints_count,
        "services_recommended_count": services_count,
        "tradeoffs_count": tradeoffs_count,
        "cost_tier": cost_tier,
        "fallback_used": fallback_used,
        "gemini_latency_ms": round(gemini_latency_ms, 2),
        "scoring_engine_used": True,
        "knowledge_graph_edges_count": edges_count
    }
    
    # Write structured JSON log entry
    logger.info(json.dumps({
        "event": "agent_execution_metrics",
        "metrics": metrics
    }))
    
    return metrics
