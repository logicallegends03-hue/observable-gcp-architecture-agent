import streamlit as st
import pandas as pd
import constraint_detector
import scorer
import knowledge_graph
import cost_estimator
import observability
import gemini_agent

# 1. Page Configuration
st.set_page_config(
    page_title="Observable Agentic AI GCP Architecture Optimizer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Premium Design Theme Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Outfit', sans-serif;
}

code, pre, .mono-text {
    font-family: 'JetBrains Mono', monospace !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    font-weight: 700 !important;
}

.title-header {
    background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}

.subtitle-header {
    color: #8b949e;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

.custom-card {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

/* Hide sidebar and toggle button entirely */
[data-testid="stSidebar"]      { display: none; }
[data-testid="collapsedControl"] { display: none; }

.constraint-tag {
    background-color: #1f6feb22;
    color: #58a6ff;
    border: 1px solid #1f6feb44;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
    margin: 4px;
}

/* Solution plan radio pills */
div[data-testid="stRadio"] label {
    font-size: 1rem !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# 3. Session State
if "run_executed" not in st.session_state:
    st.session_state.run_executed = False

# Default starter prompt
DEFAULT_PROMPT = "Need low-cost, scalable, event-driven banking API with PostgreSQL, analytics, RAG and external APIs."

# 4. Main UI Layout
st.markdown('<div class="title-header">Observable Agentic AI GCP Architecture Optimizer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-header">Hackathon Goal: Create an Observable Agentic AI Platform for GCP Architecture Optimization</div>', unsafe_allow_html=True)

# Requirement input
requirement_input = st.text_area(
    "Describe your cloud system requirements",
    value=DEFAULT_PROMPT,
    height=100,
    help="Type in your functional and non-functional requirements (e.g. databases, throughput, cost boundaries)."
)

# Run button
generate_button = st.button("🚀 Generate Recommendation & Architecture", type="primary", use_container_width=True)

# ── Main processing block ─────────────────────────────────────────────────────
if generate_button or not st.session_state.run_executed:
    st.session_state.run_executed = True

    overall_start = observability.start_timer()

    # Auto-detect constraints silently from the requirement text
    auto_constraints = constraint_detector.detect_constraints(requirement_input)

    # Score services for all 3 solution profiles
    cost_services = scorer.score_services(auto_constraints, budget_preference="low")
    perf_services = scorer.score_services(auto_constraints, budget_preference="high")
    poc_services  = scorer.score_services(auto_constraints, budget_preference="medium")

    # Use cost_services as reference for BOM, graph, and metrics
    recommended_services = cost_services
    recommended_names    = [s["name"] for s in recommended_services]

    # Tradeoffs, graph, BOM
    tradeoffs     = scorer.generate_tradeoffs(recommended_names)
    relationships = knowledge_graph.get_relationships(recommended_names)
    cost_tier, bom = cost_estimator.estimate_cost(recommended_names)

    # Generate 3 architecture solutions
    solutions, fallback_used, gemini_latency, gemini_error = gemini_agent.generate_architecture(
        requirement=requirement_input,
        constraints=auto_constraints,
        cost_services=cost_services,
        perf_services=perf_services,
        poc_services=poc_services,
        bill_of_materials=bom,
        tradeoffs=tradeoffs
    )

    total_time_ms = observability.end_timer(overall_start)

    metrics = observability.build_observability_metrics(
        total_time_ms=total_time_ms,
        constraints_count=len(auto_constraints),
        services_count=len(recommended_services),
        tradeoffs_count=len(tradeoffs),
        cost_tier=cost_tier,
        fallback_used=fallback_used,
        gemini_latency_ms=gemini_latency,
        edges_count=len(relationships)
    )

    # ── Metrics bar ───────────────────────────────────────────────────────────
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        st.metric(label="Overall Cost Tier",      value=cost_tier)
    with m_col2:
        st.metric(label="Execution Time",          value=f"{total_time_ms:.1f} ms")
    with m_col3:
        st.metric(label="Constraints Detected",    value=len(auto_constraints))
    with m_col4:
        st.metric(label="Recommended Services",    value=len(recommended_services))
    with m_col5:
        mode_val = "Rule-based Fallback" if fallback_used else "Gemini (Vertex AI)"
        st.metric(label="Generation Mode",         value=mode_val)

    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 AI Architecture Recommendation",
        "📊 Score Table & Tradeoffs",
        "🕸️ Service Knowledge Graph",
        "🔬 Observability & Telemetry"
    ])

    # ── TAB 1: 3 Architecture Plans ───────────────────────────────────────────
    with tab1:
        if fallback_used:
            st.warning(
                "⚠️ **Observability Note**: Vertex AI credentials were not detected. "
                "Serving a structured deterministic architectural proposal compiled from local knowledge rules."
            )
            if gemini_error:
                st.error(f"🔍 **Debug — actual error:** `{gemini_error}`")
        else:
            st.success("✨ **Success**: Architecture recommendations synthesized via Gemini 2.5 Flash on Vertex AI.")

        st.markdown("### Choose an Architecture Plan")

        plan = st.radio(
            "plan",
            options=["💰 Cost Efficient", "⚡ High Performance", "🧪 POC / Low Resource"],
            horizontal=True,
            label_visibility="collapsed"
        )

        st.markdown("---")

        if plan == "💰 Cost Efficient":
            st.markdown(solutions["cost"])
        elif plan == "⚡ High Performance":
            st.markdown(solutions["performance"])
        else:
            st.markdown(solutions["poc"])

    # ── TAB 2: Score Table & Tradeoffs ────────────────────────────────────────
    with tab2:
        st.subheader("Weighted Scoring Engine Analysis")
        st.markdown(
            "This table shows how GCP services were scored based on active constraints and budget preferences. "
            "Higher scores denote better alignment with your requirements."
        )

        df_scores = pd.DataFrame([
            {
                "GCP Service":         s["name"],
                "Category":            s["category"],
                "Compatibility Score": s["score"],
                "Cost Tier":           s["cost_tier"],
                "BOM Unit":            s["bom_unit"],
                "Description":         s["description"]
            } for s in recommended_services
        ])
        st.dataframe(df_scores, use_container_width=True, hide_index=True)

        st.subheader("Architectural Tradeoffs & Warnings")
        if tradeoffs:
            for t in tradeoffs:
                st.warning(t)
        else:
            st.info("No critical architectural tradeoffs triggered for this service set.")

        st.subheader("Simulated Bill of Materials")
        df_bom = pd.DataFrame(bom)
        df_bom.columns = ["Service Name", "Sizing / Usage Description", "Individual Cost Tier", "Estimated Cost"]
        st.table(df_bom)

    # ── TAB 3: Knowledge Graph ────────────────────────────────────────────────
    with tab3:
        st.subheader("Service Relationship Knowledge Graph")
        st.markdown(
            "Visualizing connections and integration mechanisms between the recommended services in your architecture."
        )

        if relationships:
            dot_str = knowledge_graph.generate_dot_format(relationships)
            st.graphviz_chart(dot_str)

            st.markdown("### Integration Details")
            for src, rel, tgt in relationships:
                st.markdown(f"- **{src}** *{rel.replace('_', ' ')}* ➡️ **{tgt}**")
        else:
            st.info("No standard integrated relationships found in the graph for the current recommended service set.")

    # ── TAB 4: Observability & Telemetry ──────────────────────────────────────
    with tab4:
        st.subheader("Agent Telemetry & Observability Metrics")
        st.markdown(
            "Full execution details and performance metrics captured for this architecture optimization request. "
            "These metrics are logged in real-time as structured JSON logs."
        )

        col_tel1, col_tel2 = st.columns([2, 3])
        with col_tel1:
            st.markdown("#### Key Latencies")
            st.metric("Total App Time",        f"{total_time_ms:.2f} ms")
            st.metric("Gemini API Time",        f"{gemini_latency:.2f} ms")
            st.metric("Knowledge Graph Edges",  len(relationships))

        with col_tel2:
            st.markdown("#### Structured JSON Log Payload")
            st.json(metrics)

        st.subheader("Structured Log Stream Simulator")
        st.code(f"""
INFO:gcp-architecture-agent-observability: {{"event": "agent_execution_metrics", "metrics": {metrics}}}
INFO:gcp-architecture-agent-observability: Constraint detection completed in {total_time_ms * 0.15:.1f} ms. Detected: {auto_constraints}
INFO:gcp-architecture-agent-observability: Scored {len(recommended_services)} services. Top recommendation: {recommended_names[0] if recommended_names else 'None'}
INFO:gcp-architecture-agent-observability: Knowledge graph generated with {len(relationships)} edges.
INFO:gcp-architecture-agent-observability: {"Fallback template invoked." if fallback_used else "Gemini content successfully fetched."}
""", language="json")
