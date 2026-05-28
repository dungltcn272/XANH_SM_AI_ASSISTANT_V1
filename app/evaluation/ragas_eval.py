import sys
import time
from typing import List, Dict, Any

from app.rag.chain import XanhSMRAGPipeline

class XanhSMEvaluation:
    """
    RAG Quality Evaluation module.
    Runs automated checks for Faithfulness, Retrieval Accuracy, and Citation Coverage.
    """
    
    def __init__(self):
        self.pipeline = XanhSMRAGPipeline()
        
        from app.evaluation.golden_dataset import GOLDEN_DATASET
        self.test_cases = GOLDEN_DATASET

    def evaluate_item(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a single query against strict operational RAG quality metrics.
        """
        query = case["query"]
        role = case["role"]
        expected = case["expected_keywords"]
        
        start_time = time.time()
        result = self.pipeline.run(query=query, role=role)
        latency = time.time() - start_time
        
        answer = result["answer"]
        citations = result["citations"]
        
        # 1. Measure Citation Coverage
        has_citations = len(citations) > 0
        citation_score = 1.0 if has_citations else 0.0
        
        # 2. Groundedness/Keyword Retrieval Score (Simulated Faithfulness/Recall)
        found_keywords = [kw for kw in expected if kw.lower() in answer.lower() or any(kw.lower() in c["source"].lower() for c in citations)]
        retrieval_recall = len(found_keywords) / len(expected)
        
        return {
            "query": query,
            "role": role,
            "latency_seconds": round(latency, 3),
            "citation_coverage": citation_score,
            "retrieval_recall": retrieval_recall,
            "matched_keywords": found_keywords,
            "expected_keywords": expected,
            "answer": answer,
            "answer_preview": answer[:150] + "..."
        }

    def run_suite(self) -> Dict[str, Any]:
        print("\n[*] Starting Automated Quality Evaluation Suite...")
        results = []
        total_recall = 0.0
        total_citations = 0.0
        total_latency = 0.0
        
        for idx, case in enumerate(self.test_cases):
            # Safe print query to avoid any windows console encoding crash
            try:
                safe_query = case['query'].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            except Exception:
                safe_query = case['query']
            print(f"[#] Test Case {idx + 1}/{len(self.test_cases)}: '{safe_query}'")
            res = self.evaluate_item(case)
            results.append(res)
            
            total_recall += res["retrieval_recall"]
            total_citations += res["citation_coverage"]
            total_latency += res["latency_seconds"]
            
        count = len(self.test_cases)
        metrics = {
            "average_latency_sec": round(total_latency / count, 3),
            "average_citation_accuracy": round(total_citations / count, 2),
            "average_retrieval_recall": round(total_recall / count, 2),
            "total_cases": count
        }
        
        return {
            "metrics": metrics,
            "details": results
        }

if __name__ == "__main__":
    evaluator = XanhSMEvaluation()
    report = evaluator.run_suite()
    print("\n================ EVALUATION REPORT ================")
    print(f"Metrics: {report['metrics']}")
    print("===================================================")
