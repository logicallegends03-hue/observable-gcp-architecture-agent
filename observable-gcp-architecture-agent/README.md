# Observable Agentic AI GCP Architecture Optimizer

An interactive, agent-driven platform designed to ingest cloud system requirements, detect architectural constraints, score suitability of Google Cloud Platform (GCP) services, analyze tradeoffs, and synthesize production-grade cloud topologies using Gemini on Vertex AI.

Features real-time execution telemetry and graph visualization of service relationships for complete observability.

---

## Architecture Flow

```text
  +------------------+      (Auto-Detect)      +-------------------------+
  | User Requirement | ----------------------> |   Constraint Detector   |
  +------------------+                         +------------+------------+
                                                            |
                                                            v
  +------------------+       (Scoring Engine)  +------------+------------+
  |  Budget Preference| ----------------------> |    Service Scorer       |
  +------------------+                         +------------+------------+
                                                            |
                                                            v
  +------------------+                         +------------+------------+
  |  Knowledge Graph  | <---------------------- |   Top 8 Recommendations |
  +--------+---------+                         +------------+------------+
           |                                                |
           v (Active Links)                                 v (Simulated BOM)
  +--------+---------+                         +------------+------------+
  | Graphviz Render  |                         |     Cost Estimator      |
  +------------------+                         +------------+------------+
           \                                                /
            \                                              /
             v                                            v
     +------------------------------------------------------------+
     |                    Gemini Agent Client                     |
     |                  (gemini-2.5-flash)                        |
     +------------------------------+-----------------------------+
                                    | (Vertex AI / Fallback)
                                    v
     +------------------------------------------------------------+
     |                 Interactive Web Dashboard                  |
     |            (Architecture, BOM, Observability)              |
     +------------------------------------------------------------+
```

---

## Local Setup & Run

### Prerequisites
- Python 3.11+
- Virtual Environment tool (`venv`)
- Google Cloud CLI (if connecting to Vertex AI)

### Step-by-Step Execution
1. **Clone and enter the directory**:
   ```bash
   cd observable-gcp-architecture-agent
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables (Optional - for Vertex AI integration)**:
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=true
   export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
   export GOOGLE_CLOUD_LOCATION="us-central1"
   
   # Log in to Google Cloud using Application Default Credentials (ADC)
   gcloud auth application-default login
   ```

5. **Run Streamlit app**:
   ```bash
   streamlit run app.py
   ```
   The application will run locally and open in your default browser (usually at `http://localhost:8501`).

---

## Docker Containerization

### Build Image
```bash
docker build -t gcp-architecture-agent .
```

### Run Image Locally
```bash
docker run -p 8080:8080 gcp-architecture-agent
```
Go to `http://localhost:8080` in your web browser.

---

## Cloud Run Deployment

To deploy the optimizer to Google Cloud Run, execute the following command (substituting `YOUR_PROJECT_ID`):

```bash
gcloud run deploy observable-gcp-architecture-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

---

## Sample Requirement Prompts

1. **Transactional Banking & Analytics (Default)**:
   > "Need low-cost, scalable, event-driven banking API with PostgreSQL, analytics, RAG and external APIs."

2. **High Throughput Real-Time IoT Ingestion**:
   > "High-performance IoT data ingestion pipeline handling 100k messages per second. Needs sub-second latency caching, NoSQL time-series data storage, and compliance controls."

3. **Minimalist Simple Web MVP**:
   > "I want to build a simple, cheap proof-of-concept web application to test a business idea. Low cost, fast deployment, and relational database storage."

---

## Hackathon Demo Script

Follow this script to demonstrate the platform to judges in 2 minutes:

1. **Initialization**:
   - Open the web application UI. Highlight the clean, premium styling and dark theme.
   - Point out the **Environment Info** block showing Vertex AI status and active fallback safety logic.

2. **Parsing Requirements**:
   - Paste the transactional banking prompt into the text area.
   - Show how the **Constraint Detector** instantly highlights active constraints (e.g. `cost_efficient`, `scalable`, `event_driven`, `relational_database`, etc.).
   - Manually toggle a constraint (e.g. add `high_performance`) and show how the system immediately re-scores.

3. **Architecture Summary**:
   - Click **Generate Recommendation & Architecture**.
   - Show the summary metrics bar at the top displaying **Overall Cost Tier: MEDIUM**, **Execution Time** (< 5ms if offline fallback, ~1-2s if Vertex AI is active), and **Generation Mode**.

4. **Review Tabbed Output**:
   - **Tab 1 (AI Recommendation)**: Walk through the recommendations, architectural diagram, and deployment suggestions.
   - **Tab 2 (Score Table)**: Walk through the weighted suitability scores and the generated Bill of Materials matching the budget preference.
   - **Tab 3 (Knowledge Graph)**: Show the Graphviz DAG illustrating how services integrate (e.g. `Pub/Sub -> triggers -> Cloud Run`).
   - **Tab 4 (Observability)**: Show the structured JSON metrics stream that standardizes log collection, illustrating the agent's internal traces and latencies.
