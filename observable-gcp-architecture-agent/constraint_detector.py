import re
from typing import List

ALL_CONSTRAINTS = [
    "cost_efficient",
    "scalable",
    "high_performance",
    "low_resource_poc",
    "event_driven",
    "analytics",
    "relational_database",
    "nosql_database",
    "caching",
    "rag_required",
    "external_api_required",
    "banking_compliance",
    "observability_required"
]

KEYWORDS = {
    "cost_efficient": [r"\bcost\b", r"\bcheap\b", r"\bbudget\b", r"\binexpensive\b", r"\beconomical\b", r"\blow-cost\b", r"\bpricing\b"],
    "scalable": [r"\bscale\b", r"\bscalable\b", r"\bautoscal\w*\b", r"\bthroughput\b", r"\bmillion\b", r"\bvolume\b", r"\belastic\b"],
    "high_performance": [r"\bperformance\b", r"\blow latency\b", r"\bms\b", r"\bmilliseconds\b", r"\bfast\b", r"\bspeed\b", r"\bsub-second\b"],
    "low_resource_poc": [r"\bpoc\b", r"\bmvp\b", r"\bprototype\b", r"\bquick\b", r"\bproof of concept\b", r"\bsimple\b"],
    "event_driven": [r"\bevent\b", r"\bevent-driven\b", r"\basync\b", r"\bpubsub\b", r"\bqueue\b", r"\bmessage\b", r"\btrigger\b", r"\bdecoupling\b"],
    "analytics": [r"\banalytic\w*\b", r"\bwarehouse\b", r"\breport\w*\b", r"\bbi\b", r"\bdashboard\b", r"\bbig data\b", r"\binsight\w*\b"],
    "relational_database": [r"\bpostgres\w*\b", r"\bsql\b", r"\brelational\b", r"\bspanner\b", r"\brdbms\b", r"\btransaction\w*\b", r"\bacid\b"],
    "nosql_database": [r"\bnosql\b", r"\bdocument\b", r"\bfirestore\b", r"\bmongodb\b", r"\bkey-value\b", r"\bbigtable\b"],
    "caching": [r"\bcache\b", r"\bcaching\b", r"\bredis\b", r"\bmemorystore\b", r"\bin-memory\b"],
    "rag_required": [r"\brag\b", r"\bretrieval-augmented\b", r"\bembedding\w*\b", r"\bvector\b", r"\bllm\b", r"\bsearch\b", r"\bsemantic\b"],
    "external_api_required": [r"\bexternal api\b", r"\bthird party\b", r"\bexternal apis\b", r"\bintegration\b", r"\bwebhook\w*\b", r"\bhttp request\b", r"\bexternal integration\b"],
    "banking_compliance": [r"\bbank\w*\b", r"\bcomplian\w*\b", r"\baudit\b", r"\bpci\b", r"\bfinance\b", r"\bfinancial\b", r"\bsecurity controls\b", r"\bgovernance\b"],
    "observability_required": [r"\bobservability\b", r"\bmonitor\w*\b", r"\blogging\b", r"\btrac\w*\b", r"\balert\w*\b", r"\berror\b", r"\bmetrics\b"]
}

def detect_constraints(text: str) -> List[str]:
    """
    Parses the requirement string and returns matching constraints from ALL_CONSTRAINTS.
    """
    detected = []
    text_lower = text.lower()
    for constraint, patterns in KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                detected.append(constraint)
                break
    return detected
