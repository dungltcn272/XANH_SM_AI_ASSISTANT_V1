import sys
import os
import time
import json
import math
from typing import List, Dict, Any, Optional

# Set TIKTOKEN_CACHE_DIR for offline mode
if "TIKTOKEN_CACHE_DIR" not in os.environ:
    os.environ["TIKTOKEN_CACHE_DIR"] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "tiktoken_cache"
    )

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from app.rag.chain import XanhSMRAGPipeline
from app.core.config import settings
from app.core.logger import log_warn, log_error
from openai import OpenAI

class XanhSMEvaluation:
    def __init__(self, dataset: Optional[List[Dict[str, Any]]] = None):
        self.pipeline = XanhSMRAGPipeline()
        if dataset and len(dataset) > 0:
            self.test_cases = dataset
        else:
            from evaluation.golden_dataset import GOLDEN_DATASET
            self.test_cases = GOLDEN_DATASET
            
        self.llm_client = None
        if settings.OPENAI_API_KEY and "YOUR_" not in settings.OPENAI_API_KEY:
            self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=15.0)

    def count_keywords_in_docs(self, docs, expected_kws):
        if not expected_kws: return 1.0
        found = 0
        for kw in expected_kws:
            for doc in docs:
                if kw.lower() in doc["content"].lower():
                    found += 1
                    break
        return found / len(expected_kws)

    def evaluate_item(self, case: Dict[str, Any]) -> Dict[str, Any]:
        query = case["query"]
        expected = case.get("expected_keywords", [])
        
        start_time = time.time()
        result = self.pipeline.run(query=query)
        latency = time.time() - start_time
        
        answer = result["answer"]
        top_docs = result.get("top_docs", [])
        
        # Retrieval Metrics
        recall_5 = self.count_keywords_in_docs(top_docs[:5], expected)
        recall_10 = self.count_keywords_in_docs(top_docs[:10], expected)
        
        first_rel_rank = -1
        for i, doc in enumerate(top_docs):
            if any(kw.lower() in doc["content"].lower() for kw in expected):
                first_rel_rank = i + 1
                break
        
        mrr = 1.0 / first_rel_rank if first_rel_rank > 0 else 0.0
        
        dcg = 0.0
        idcg = 0.0
        max_rel = min(len(expected), 5) if expected else 1
        for i in range(1, max_rel + 1):
            idcg += 1.0 / math.log2(i + 1)
            
        for i, doc in enumerate(top_docs[:5]):
            if expected and any(kw.lower() in doc["content"].lower() for kw in expected):
                dcg += 1.0 / math.log2((i+1) + 1)
        
        ndcg_5 = dcg / idcg if idcg > 0 else 0.0
        if not expected:
            ndcg_5 = 1.0
            
        # Generation Metrics (LLM as Judge)
        faithfulness = 0.0
        correctness = 0.0
        relevancy = 0.0
        
        if self.llm_client:
            try:
                context_str = str([d["content"] for d in top_docs[:5]])
                prompt = f"""Evaluate the RAG system response based on the query and context. Provide scores from 0.0 to 1.0 for four metrics:
1. faithfulness: Is the answer supported by the Context? (1.0 = fully supported). If Context is empty and answer says "I don't know", score 1.0.
2. correctness: Does the answer correctly address the Query and match Expected Keywords ({expected})?
3. relevancy: Is the answer direct and relevant without tangents?
4. context_recall: Does the Context contain enough information to address the Expected Keywords ({expected}) or the Query? (1.0 = contains all necessary info, 0.5 = partial, 0.0 = none).

Query: {query}
Context: {context_str}
Answer: {answer}

Return ONLY a JSON object with keys: "faithfulness", "correctness", "relevancy", "context_recall" (floats)."""
                res = self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" },
                    temperature=0.0
                )
                scores = json.loads(res.choices[0].message.content)
                faithfulness = float(scores.get("faithfulness", 0.0))
                correctness = float(scores.get("correctness", 0.0))
                relevancy = float(scores.get("relevancy", 0.0))
                recall_5 = float(scores.get("context_recall", recall_5))
                recall_10 = recall_5 # approximate recall_10 with recall_5 for LLM judge
            except Exception as e:
                log_warn("EVAL", f"LLM Judge error: {e}")
        num_chunks_before_expansion = result.get("num_chunks_before_expansion", 0)
        compressed_context_len = result.get("compressed_context_len", 0)
        
        print(f"   -> AI Answer: {answer[:100]}...")
        print(f"   -> R@5: {recall_5:.2f} | MRR: {mrr:.2f} | Faithfulness: {faithfulness:.2f} | Correctness: {correctness:.2f}")
        
        return {
            "query": query,
            "latency_seconds": round(latency, 3),
            "num_chunks_before_expansion": num_chunks_before_expansion,
            "compressed_context_len": compressed_context_len,
            "retrieval": {
                "recall_5": recall_5,
                "recall_10": recall_10,
                "mrr": mrr,
                "ndcg_5": ndcg_5
            },
            "generation": {
                "faithfulness": faithfulness,
                "correctness": correctness,
                "relevancy": relevancy
            },
            "matched_keywords": [kw for kw in expected if kw.lower() in answer.lower()],
            "expected_keywords": expected,
            "answer": answer
        }

    def run_suite(self) -> Dict[str, Any]:
        print("\n[*] Starting Automated Quality Evaluation Suite (RAGAS)...")
        results = []
        
        avg = {"recall_5": 0, "recall_10": 0, "mrr": 0, "ndcg_5": 0, "faithfulness": 0, "correctness": 0, "relevancy": 0, "latency": 0, "num_chunks": 0, "context_len": 0}
        
        for idx, case in enumerate(self.test_cases):
            try:
                safe_query = case['query'].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            except:
                safe_query = case['query']
            print(f"[#] Test Case {idx + 1}/{len(self.test_cases)}: '{safe_query}'")
            
            try:
                res = self.evaluate_item(case)
                results.append(res)
                
                for k in ["recall_5", "recall_10", "mrr", "ndcg_5"]:
                    avg[k] += res["retrieval"][k]
                for k in ["faithfulness", "correctness", "relevancy"]:
                    avg[k] += res["generation"][k]
                avg["latency"] += res["latency_seconds"]
                avg["num_chunks"] += res["num_chunks_before_expansion"]
                avg["context_len"] += res["compressed_context_len"]
                
            except Exception as e:
                log_error("EVAL", f"Failed to evaluate: {e}")
            
        count = len(results) if len(results) > 0 else 1
        metrics = {
            "average_latency_sec": round(avg["latency"] / count, 3),
            "average_num_chunks_before_expansion": round(avg["num_chunks"] / count, 2),
            "average_context_len": round(avg["context_len"] / count, 1),
            "retrieval": {k: round(v / count, 3) for k, v in avg.items() if k in ["recall_5", "recall_10", "mrr", "ndcg_5"]},
            "generation": {k: round(v / count, 3) for k, v in avg.items() if k in ["faithfulness", "correctness", "relevancy"]},
            "total_cases": len(results)
        }
        
        report = {
            "metrics": metrics,
            "details": results
        }
        
        with open("evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print("[INFO] Evaluation results successfully saved to evaluation_report.json.")
        return report

if __name__ == "__main__":
    evaluator = XanhSMEvaluation()
    report = evaluator.run_suite()
    print("\n================ EVALUATION REPORT ================")
    print(json.dumps(report['metrics'], indent=2))
    print("===================================================")
