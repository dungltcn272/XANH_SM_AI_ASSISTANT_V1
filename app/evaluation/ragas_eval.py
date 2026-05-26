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
        
        # Comprehensive Gold Standard Test Dataset
        self.test_cases = [
            {
                "query": "So dien thoai tong dai ho tro hanh khach la so may?",
                "role": "customer",
                "expected_keywords": ["1900 2088", "terms.md", "booking.md"]
            },
            {
                "query": "Muc chiet khau hay phi dich vu he thong cua tai xe Xanh Car la bao nhieu?",
                "role": "driver",
                "expected_keywords": ["25%", "commission.md"]
            },
            {
                "query": "Ty le nhan chuyen AR va huy chuyen CR tai xe phai duy tri la bao nhieu?",
                "role": "driver",
                "expected_keywords": ["85%", "5%", "driver_policy.md"]
            },
            {
                "query": "Doi tac cua hang Xanh Food phai chiet khau hoa hong bao nhieu?",
                "role": "merchant",
                "expected_keywords": ["20%", "merchant_policy.md"]
            },
            {
                "query": "Phi huy chuyen xe doi voi hanh khach khi huy sau 2 phut la bao nhieu?",
                "role": "customer",
                "expected_keywords": ["15.000", "refund.md"]
            }
        ]

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
            # Use ASCII queries for print statements to avoid any CP1252 warning crashes
            print(f"[#] Test Case {idx + 1}/{len(self.test_cases)}: '{case['query']}'")
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
