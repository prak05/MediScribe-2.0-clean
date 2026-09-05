"""Performance Testing & Benchmarking Suite for MediScribe.
Commandment 10: Choice of Traditional Performance Testing Framework / Tools
(Load Test, Latency P50/P95/P99, Throughput QPS, Saturation).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import argparse
import concurrent.futures
import statistics
import time

from core.config import settings
from core.retrieval.retriever import SemanticRetriever
from core.retrieval.reranker import ReRanker
from core.llm.generator import ClinicalGenerator

@dataclass
class BenchmarkResult:
    """Quantitative performance metrics under simulated workload."""
    total_queries: int
    successful_queries: int
    failed_queries: int
    duration_seconds: float
    qps: float
    latency_mean_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    error_rate: float
    breakdown_by_query: List[Dict[str, float]] = field(default_factory=list)

    def print_summary(self) -> None:
        print("\n" + "=" * 60)
        print("📊 MEDISCRIBE RAG PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)
        print(f"Total Requests Processed : {self.total_queries}")
        print(f"Throughput (QPS)         : {self.qps:.2f} queries/sec")
        print(f"Average Latency          : {self.latency_mean_ms:.1f} ms")
        print(f"P50 Latency (Median)     : {self.latency_p50_ms:.1f} ms")
        print(f"P95 Latency              : {self.latency_p95_ms:.1f} ms")
        print(f"P99 Latency              : {self.latency_p99_ms:.1f} ms")
        print(f"Error Rate               : {self.error_rate * 100:.1f}%")
        print("=" * 60)

class PerformanceBenchmark:
    """Simulates concurrent medical queries to measure latency and saturation."""

    DEFAULT_QUERIES = [
        "What are the diagnostic criteria for diabetic ketoacidosis?",
        "Explain the first-line pharmacotherapy for acute myocardial infarction.",
        "What are the contraindications for beta-blockers in heart failure?",
        "Describe the pathophysiology of acute respiratory distress syndrome (ARDS).",
        "What is the recommended antibiotic regimen for community-acquired pneumonia?",
        "Outline the management of severe sepsis in intensive care units.",
        "What are the signs of acute appendicitis and its surgical indications?",
        "Explain the differential diagnosis of acute pulmonary embolism."
    ]

    def __init__(self, concurrency: int = 2):
        self.concurrency = concurrency
        self.retriever = SemanticRetriever()
        self.reranker = ReRanker()
        self.generator = ClinicalGenerator()

    def _execute_single_query(self, query: str) -> Dict[str, float]:
        """Measure end-to-end execution latency for a single RAG request."""
        t0 = time.perf_counter()
        try:
            # 1. Retrieval
            chunks = self.retriever.retrieve(query, top_k=5)
            # 2. Re-ranking
            ranked = self.reranker.rerank(query, chunks, top_k=3)
            # 3. Generation
            res = self.generator.generate(query, ranked)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return {"query": query, "latency_ms": elapsed_ms, "success": 1.0}
        except Exception:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return {"query": query, "latency_ms": elapsed_ms, "success": 0.0}

    def run_benchmark(self, num_queries: int = 8, concurrency: Optional[int] = None) -> BenchmarkResult:
        """Run concurrent workload simulation."""
        workers = concurrency or self.concurrency
        test_queries = (self.DEFAULT_QUERIES * ((num_queries // len(self.DEFAULT_QUERIES)) + 1))[:num_queries]

        start_wall = time.perf_counter()
        results: List[Dict[str, float]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_query = {executor.submit(self._execute_single_query, q): q for q in test_queries}
            for future in concurrent.futures.as_completed(future_to_query):
                res = future.result()
                results.append(res)

        total_duration = time.perf_counter() - start_wall
        latencies = [r["latency_ms"] for r in results]
        latencies.sort()

        successful = sum(1 for r in results if r["success"] > 0)
        failed = len(results) - successful

        mean_lat = statistics.mean(latencies) if latencies else 0.0
        p50 = statistics.median(latencies) if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0

        qps = len(results) / total_duration if total_duration > 0 else 0.0
        error_rate = failed / len(results) if results else 0.0

        return BenchmarkResult(
            total_queries=len(results),
            successful_queries=successful,
            failed_queries=failed,
            duration_seconds=round(total_duration, 2),
            qps=round(qps, 2),
            latency_mean_ms=round(mean_lat, 2),
            latency_p50_ms=round(p50, 2),
            latency_p95_ms=round(p95, 2),
            latency_p99_ms=round(p99, 2),
            error_rate=round(error_rate, 3),
            breakdown_by_query=results
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediScribe RAG Performance Benchmark")
    parser.add_argument("--queries", type=int, default=4, help="Number of test queries to issue")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent worker threads")
    args = parser.parse_args()

    bench = PerformanceBenchmark(concurrency=args.concurrency)
    res = bench.run_benchmark(num_queries=args.queries)
    res.print_summary()
