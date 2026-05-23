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
    initial_sidebar_state="expanded"
)

# 2. Premium Design Theme Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* Set main fonts */
html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Outfit', sans-serif;
}

code, pre, .mono-text {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Headers styling */
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

/* Card layout wrapper */
.custom-card {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #30363d;
}

/* Highlight tags */
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
</style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if "last_requirement" not in st.session_state:
    st.session_state.last_requirement = ""
if "selected_constraints" not in st.session_state:
    st.session_state.selected_constraints = []
if "run_executed" not in st.session_state:
    st.session_state.run_executed = False

# Default starter prompt
DEFAULT_PROMPT = "Need low-cost, scalable, event-driven banking API with PostgreSQL, analytics, RAG and external APIs."

# 4. Sidebar Controls Configuration
st.sidebar.image("https://www.gstatic.com/images/branding/product/2x/cloud_logo_64dp.png", width=50)
st.sidebar.markdown("### Agent Configuration")

budget_pref = st.sidebar.selectbox(
    "Budget Preference",
    options=["low", "medium", "high"],
    index=0,  # Default to low as in user prompt
    help="Determines the starting scoring weights for cost vs performance/scalability."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Environment Info")
gcp_project = st.sidebar.text_input("GCP Project ID", placeholder="your-gcp-project",
                                     help="Set GOOGLE_CLOUD_PROJECT env var or enter here for display.")
st.sidebar.code(
    f"GOOGLE_GENAI_USE_VERTEXAI=true\n"
    f"GOOGLE_CLOUD_PROJECT={gcp_project or 'your-gcp-project'}\n"
    "GOOGLE_CLOUD_LOCATION=us-central1\n"
    "Model: gemini-2.5-flash",
    language="ini"
)

st.sidebar.info(
    "💡 This agent operates with active fallback logic. If Vertex AI credentials or project config are not provided, "
    "it will run the recommendation engine and generate a deterministic fallback architecture report."
)

# 5. Main UI Layout
st.markdown('<div class="title-header">Observable Agentic AI GCP Architecture Optimizer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-header">Hackathon Goal: Create an Observable Agentic AI Platform for GCP Architecture Optimization</div>', unsafe_allow_html=True)

# Requirement input text area
requirement_input = st.text_area(
    "Describe your cloud system requirements",
    value=DEFAULT_PROMPT,
    height=100,
    help="Type in your functional and non-functional requirements (e.g. databases, throughput, cost boundaries)."
)

# Dynamic constraint detection trigger
if requirement_input != st.session_state.last_requirement:
    st.session_state.last_requirement = requirement_input
    st.session_state.selected_constraints = constraint_detector.detect_constraints(requirement_input)

# Allow manual additions/removals of constraints
selected_constraints = st.multiselect(
    "Detected Constraints (Modify or manually append)",
    options=constraint_detector.ALL_CONSTRAINTS,
    default=st.session_state.selected_constraints,
    key="constraints_multiselect"
)

# Run generation trigger button
generate_button = st.button("🚀 Generate Recommendation & Architecture", type="primary", use_container_width=True)

# Process recommendations — run on first load (default prompt) or whenever button is clicked
if generate_button or not st.session_state.run_executed:
    st.session_state.run_executed = True
    
    # Start timer for observability
    overall_start = observability.start_timer()
    
    # 1. Scorer recommendation list
    recommended_services = scorer.score_services(selected_constraints, budget_preference=budget_pref)
    recommended_names = [s["name"] for s in recommended_services]
    
    # 2. Get tradeoffs / warnings
    tradeoffs = scorer.generate_tradeoffs(recommended_names)
    
    # 3. Get in-memory knowledge graph relationships
    relationships = knowledge_graph.get_relationships(recommended_names)
    
    # 4. Simulated Bill of Materials (BOM) & Overall cost tier
    cost_tier, bom = cost_estimator.estimate_cost(recommended_names)
    
    # 5. Generate explanation from Gemini (or fallback template)
    explanation_text, fallback_used, gemini_latency = gemini_agent.generate_architecture(
        requirement=requirement_input,
        constraints=selected_constraints,
        services=recommended_services,
        bill_of_materials=bom,
        tradeoffs=tradeoffs
    )
    
    # Stop overall timer
    total_time_ms = observability.end_timer(overall_start)
    
    # Build and log metrics
    metrics = observability.build_observability_metrics(
        total_time_ms=total_time_ms,
        constraints_count=len(selected_constraints),
        services_count=len(recommended_services),
        tradeoffs_count=len(tradeoffs),
        cost_tier=cost_tier,
        fallback_used=fallback_used,
        gemini_latency_ms=gemini_latency,
        edges_count=len(relationships)
    )
    
    # 6. Top Metrics Bar Display
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    
    with m_col1:
        st.metric(label="Overall Cost Tier", value=cost_tier)
    with m_col2:
        st.metric(label="Execution Time", value=f"{total_time_ms:.1f} ms")
    with m_col3:
        st.metric(label="Constraints Detected", value=len(selected_constraints))
    with m_col4:
        st.metric(label="Recommended Services", value=len(recommended_services))
    with m_col5:
        mode_val = "Rule-based Fallback" if fallback_used else "Gemini (Vertex AI)"
        st.metric(label="Generation Mode", value=mode_val)
        
    st.markdown("---")
    
    # 7. Tabbed Dashboard Layout
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 AI Architecture Recommendation",
        "📊 Score Table & Tradeoffs",
        "🕸️ Service Knowledge Graph",
        "🔬 Observability & Telemetry"
    ])
    
    # TAB 1: AI Recommendation
    with tab1:
        # If fallback was used, show a nice warning alert
        if fallback_used:
            st.warning(
                "⚠️ **Observability Note**: Vertex AI credentials were not detected. "
                "Serving a structured deterministic architectural proposal compiled from local knowledge rules."
            )
        else:
            st.success("✨ **Success**: Architecture recommendation successfully synthesized via Gemini 2.5 Flash on Vertex AI.")
            
        # Display Gemini / Fallback text
        st.markdown(explanation_text)
        
    # TAB 2: Service Comparison & Scores
    with tab2:
        st.subheader("Weighted Scoring Engine Analysis")
        st.markdown(
            "This table shows how GCP services were scored based on active constraints and budget preferences. "
            "Higher scores denote better alignment with your requirements."
        )
        
        # Convert scored recommendations to DataFrame for rendering
        df_scores = pd.DataFrame([
            {
                "GCP Service": s["name"],
                "Category": s["category"],
                "Compatibility Score": s["score"],
                "Cost Tier": s["cost_tier"],
                "BOM Unit": s["bom_unit"],
                "Description": s["description"]
            } for s in recommended_services
        ])
        
        st.dataframe(df_scores, use_container_width=True, hide_index=True)
        
        # Tradeoffs / Impact Warnings Section
        st.subheader("Architectural Tradeoffs & Warnings")
        if tradeoffs:
            for t in tradeoffs:
                st.warning(t)
        else:
            st.info("No critical architectural tradeoffs triggered for this service set.")
            
        # Simulated Bill of Materials
        st.subheader("Simulated Bill of Materials")
        df_bom = pd.DataFrame(bom)
        df_bom.columns = ["Service Name", "Sizing / Usage Description", "Individual Cost Tier", "Estimated Cost"]
        st.table(df_bom)
        
    # TAB 3: Knowledge Graph
    with tab3:
        st.subheader("Service Relationship Knowledge Graph")
        st.markdown(
            "Visualizing connections and integration mechanisms between the recommended services in your architecture."
        )
        
        if relationships:
            dot_str = knowledge_graph.generate_dot_format(relationships)
            st.graphviz_chart(dot_str)
            
            # Print relationships in clean list format
            st.markdown("### Integration Details")
            for src, rel, tgt in relationships:
                st.markdown(f"- **{src}** *{rel.replace('_', ' ')}* ➡️ **{tgt}**")
        else:
            st.info("No standard integrated relationships found in the graph for the current recommended service set.")
            
    # TAB 4: Observability & Telemetry
    with tab4:
        st.subheader("Agent Telemetry & Observability Metrics")
        st.markdown(
            "Full execution details and performance metrics captured for this architecture optimization request. "
            "These metrics are logged in real-time as structured JSON logs."
        )
        
        col_tel1, col_tel2 = st.columns([2, 3])
        
        with col_tel1:
            st.markdown("#### Key Latencies")
            st.metric("Total App Time", f"{total_time_ms:.2f} ms")
            st.metric("Gemini API Time", f"{gemini_latency:.2f} ms")
            st.metric("Knowledge Graph Edges", len(relationships))
            
        with col_tel2:
            st.markdown("#### Structured JSON Log Payload")
            st.json(metrics)
            
        st.subheader("Structured Log Stream Simulator")
        st.code(f"""
INFO:gcp-architecture-agent-observability: {{"event": "agent_execution_metrics", "metrics": {metrics}}}
INFO:gcp-architecture-agent-observability: Constraint detection completed in {total_time_ms * 0.15:.1f} ms. Detected: {selected_constraints}
INFO:gcp-architecture-agent-observability: Scored {len(recommended_services)} services. Top recommendation: {recommended_names[0] if recommended_names else 'None'}
INFO:gcp-architecture-agent-observability: Knowledge graph generated with {len(relationships)} edges.
INFO:gcp-architecture-agent-observability: {"Fallback template invoked." if fallback_used else "Gemini content successfully fetched."}
""", language="json")
