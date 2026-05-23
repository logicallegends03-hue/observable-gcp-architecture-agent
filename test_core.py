import unittest
import constraint_detector
import scorer
import knowledge_graph
import cost_estimator

class TestGCPOptimizerCore(unittest.TestCase):

    def test_constraint_detection(self):
        text = "Need low-cost, scalable, event-driven banking API with PostgreSQL, analytics, RAG and external APIs."
        detected = constraint_detector.detect_constraints(text)
        
        # Verify specific expected constraints are detected
        self.assertIn("cost_efficient", detected)
        self.assertIn("scalable", detected)
        self.assertIn("event_driven", detected)
        self.assertIn("relational_database", detected)
        self.assertIn("analytics", detected)
        self.assertIn("rag_required", detected)
        self.assertIn("external_api_required", detected)
        self.assertIn("banking_compliance", detected)
        
        # Test negative case
        self.assertNotIn("nosql_database", detected)

    def test_scorer_and_boosts(self):
        constraints = ["cost_efficient", "scalable", "event_driven"]
        results = scorer.score_services(constraints, budget_preference="low")
        
        # Results should return top 8 services
        self.assertEqual(len(results), 8)
        
        # Cloud Run should rank high because it gets cost_efficient, scalable, event_driven boosts and has high base scores
        service_names = [s["name"] for s in results]
        self.assertIn("Cloud Run", service_names)
        
        # Cloud Functions gets boosts and should also rank high
        self.assertIn("Cloud Functions", service_names)

    def test_tradeoffs_warnings(self):
        # Spanner and Cloud SQL recommended together should trigger Spanner tradeoff warning
        tradeoffs = scorer.generate_tradeoffs(["Cloud Spanner", "Cloud SQL PostgreSQL", "GKE Autopilot", "Cloud Run"])
        self.assertIn("Spanner improves scalability but increases cost compared to Cloud SQL.", tradeoffs)
        self.assertIn("GKE Autopilot is powerful but more complex than Cloud Run for a POC.", tradeoffs)
        
        # Logging should trigger observability warning
        tradeoffs_obs = scorer.generate_tradeoffs(["Cloud Logging", "Cloud Run"])
        self.assertIn("Observability improves governance but adds monitoring cost and implementation effort.", tradeoffs_obs)

    def test_knowledge_graph(self):
        selected = ["Cloud Run", "Pub/Sub", "Dataflow"]
        relationships = knowledge_graph.get_relationships(selected)
        
        # Verify relationships like Cloud Run -> integrates_with -> Pub/Sub are caught
        edges = {(r[0], r[1], r[2]) for r in relationships}
        self.assertTrue(any(src == "Cloud Run" and tgt == "Pub/Sub" for src, rel, tgt in edges))
        self.assertTrue(any(src == "Pub/Sub" and tgt == "Dataflow" for src, rel, tgt in edges))

    def test_cost_estimator(self):
        # Mostly serverless
        overall_tier, bom = cost_estimator.estimate_cost(["Cloud Run", "Cloud Functions", "Cloud Storage", "Vertex AI"])
        self.assertEqual(overall_tier, "LOW")
        
        # Includes Cloud SQL
        overall_tier_med, bom_med = cost_estimator.estimate_cost(["Cloud Run", "Cloud SQL PostgreSQL", "Pub/Sub"])
        self.assertEqual(overall_tier_med, "MEDIUM")
        
        # Includes multiple HIGH tiers (or Spanner + GKE)
        overall_tier_high, bom_high = cost_estimator.estimate_cost(["Cloud Spanner", "GKE Autopilot", "Bigtable"])
        self.assertEqual(overall_tier_high, "HIGH")

if __name__ == "__main__":
    unittest.main()
