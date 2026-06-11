import sys
import os
import time
import json
import math
from datetime import datetime
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

    def count_sources_in_docs(self, docs, expected_sources):
        if not expected_sources:
            return 1.0
        haystack = " ".join(
            [
                f"{doc.get('source', '')} {doc.get('section', '')} {doc.get('content', '')[:500]}"
                for doc in docs
            ]
        ).lower()
        found = sum(1 for source in expected_sources if source.lower() in haystack)
        return found / len(expected_sources)

    def evaluate_item(self, case: Dict[str, Any]) -> Dict[str, Any]:
        query = case["query"]
        expected = case.get("expected_keywords", [])
        
        start_time = time.time()
        result = self.pipeline.run(query=query, bypass_cache=True)
        latency = time.time() - start_time
        
        answer = result["answer"]
        top_docs = result.get("top_docs", [])
        
        # Retrieval Metrics
        recall_5 = self.count_keywords_in_docs(top_docs[:5], expected)
        recall_10 = self.count_keywords_in_docs(top_docs[:10], expected)
        source_recall_5 = self.count_sources_in_docs(top_docs[:5], case.get("expected_sources", []))
        
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
                    model=settings.AI_JUDGE_MODEL,
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
        nlu_latency_ms = result.get("nlu_latency_ms")
        nlu_fast_path = bool(result.get("nlu_fast_path"))
        nlu_fast_path_reason = result.get("nlu_fast_path_reason")
        
        print(f"   -> AI Answer: {answer[:100]}...")
        print(f"   -> R@5: {recall_5:.2f} | MRR: {mrr:.2f} | Faithfulness: {faithfulness:.2f} | Correctness: {correctness:.2f}")
        
        return {
            "id": case.get("id", query[:60]),
            "level": case.get("level", "unspecified"),
            "category": case.get("category", "general"),
            "query": query,
            "latency_seconds": round(latency, 3),
            "nlu_latency_ms": nlu_latency_ms,
            "nlu_fast_path": nlu_fast_path,
            "nlu_fast_path_reason": nlu_fast_path_reason,
            "num_chunks_before_expansion": num_chunks_before_expansion,
            "compressed_context_len": compressed_context_len,
            "retrieval": {
                "recall_5": recall_5,
                "recall_10": recall_10,
                "source_recall_5": source_recall_5,
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
        
        avg = {"recall_5": 0, "recall_10": 0, "source_recall_5": 0, "mrr": 0, "ndcg_5": 0, "faithfulness": 0, "correctness": 0, "relevancy": 0, "latency": 0, "num_chunks": 0, "context_len": 0}
        
        for idx, case in enumerate(self.test_cases):
            try:
                safe_query = case['query'].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            except:
                safe_query = case['query']
            print(f"[#] Test Case {idx + 1}/{len(self.test_cases)}: '{safe_query}'")
            
            try:
                res = self.evaluate_item(case)
                results.append(res)
                
                for k in ["recall_5", "recall_10", "source_recall_5", "mrr", "ndcg_5"]:
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
            "retrieval": {k: round(v / count, 3) for k, v in avg.items() if k in ["recall_5", "recall_10", "source_recall_5", "mrr", "ndcg_5"]},
            "generation": {k: round(v / count, 3) for k, v in avg.items() if k in ["faithfulness", "correctness", "relevancy"]},
            "total_cases": len(results),
            "by_level": self.summarize_bucket(results, "level"),
            "by_category": self.summarize_bucket(results, "category"),
        }
        
        report = {
            "metrics": metrics,
            "details": results
        }
        
        with open("evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.save_run_snapshot(report)
            
        print("[INFO] Evaluation results successfully saved to evaluation_report.json.")
        return report

    def save_run_snapshot(self, report: Dict[str, Any]) -> None:
        try:
            from app.db.database import Base, engine, SessionLocal
            from app.db.models import EvaluationRun

            Base.metadata.create_all(bind=engine)
            metrics = report.get("metrics", {})
            retrieval = metrics.get("retrieval", {})
            generation = metrics.get("generation", {})
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            dataset_name = f"golden_{metrics.get('total_cases', len(report.get('details', [])))}"
            description = os.environ.get("EVAL_DESCRIPTION")

            db = SessionLocal()
            try:
                row = EvaluationRun(
                    run_name=run_name,
                    description=description,
                    dataset_name=dataset_name,
                    model_name=settings.LLM_MODEL,
                    total_cases=metrics.get("total_cases", 0),
                    status="completed",
                    average_latency_sec=metrics.get("average_latency_sec", 0),
                    recall_5=retrieval.get("recall_5", 0),
                    recall_10=retrieval.get("recall_10", 0),
                    mrr=retrieval.get("mrr", 0),
                    ndcg_5=retrieval.get("ndcg_5", 0),
                    faithfulness=generation.get("faithfulness", 0),
                    correctness=generation.get("correctness", 0),
                    relevancy=generation.get("relevancy", 0),
                    metrics_json=json.dumps(metrics, ensure_ascii=False),
                    details_json=json.dumps(report.get("details", []), ensure_ascii=False),
                )
                db.add(row)
                db.commit()
                print(f"[INFO] Evaluation run snapshot saved to evaluation_runs: {run_name}")
            finally:
                db.close()
        except Exception as e:
            log_warn("EVAL", f"Failed to save evaluation run snapshot: {e}")

    def summarize_bucket(self, results: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for item in results:
            buckets.setdefault(item.get(key, "unspecified"), []).append(item)

        summary = {}
        for name, items in sorted(buckets.items()):
            n = len(items)
            summary[name] = {
                "cases": n,
                "avg_latency_sec": round(sum(i["latency_seconds"] for i in items) / n, 3),
                "avg_recall_5": round(sum(i["retrieval"]["recall_5"] for i in items) / n, 3),
                "avg_source_recall_5": round(sum(i["retrieval"]["source_recall_5"] for i in items) / n, 3),
                "avg_correctness": round(sum(i["generation"]["correctness"] for i in items) / n, 3),
                "avg_faithfulness": round(sum(i["generation"]["faithfulness"] for i in items) / n, 3),
            }
        return summary

if __name__ == "__main__":
    evaluator = XanhSMEvaluation()
    report = evaluator.run_suite()
    print("\n================ EVALUATION REPORT ================")
    print(json.dumps(report['metrics'], indent=2))
    print("===================================================")
