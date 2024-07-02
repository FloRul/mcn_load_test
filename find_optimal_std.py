import json
import numpy as np
from typing import List, Dict, Any
from webs_load_tester import WebSocketLoadTester
import asyncio
import os
import pickle


def load_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    return {}


def save_cache(cache, cache_file):
    with open(cache_file, "wb") as f:
        pickle.dump(cache, f)


def analyze_responses_percentile(responses: List[Dict[str, Any]]) -> float:
    percentile_values = range(80, 100)  # Test percentiles from 80 to 99
    results = {}

    for percentile in percentile_values:
        correct_count = 0
        doc_counts = []
        for prompt, response_str, _ in responses:
            try:
                response = json.loads(response_str)
                documents = response.get("references", [])
                if not documents:
                    continue

                scores = np.array(
                    [doc["metadata"].get("score", 0) for doc in documents]
                )
                threshold = np.percentile(scores, percentile)

                selected_docs = [
                    doc
                    for doc in documents
                    if doc["metadata"].get("score", 0) >= threshold
                ]
                doc_counts.append(len(selected_docs))
                if len(selected_docs) == 1:
                    correct_count += 1

            except json.JSONDecodeError:
                continue

        results[percentile] = {
            "correct_count": correct_count,
            "avg_docs": np.mean(doc_counts),
            "max_docs": max(doc_counts),
            "min_docs": min(doc_counts),
        }

    optimal_percentile = max(results, key=lambda x: results[x]["correct_count"])

    print("\nDetailed results:")
    for percentile, data in results.items():
        print(f"Percentile: {percentile}")
        print(f"  Correct (1 doc): {data['correct_count']}/{len(responses)}")
        print(f"  Avg docs: {data['avg_docs']:.2f}")
        print(f"  Range: {data['min_docs']} - {data['max_docs']} docs")
        print()

    print(f"Best percentile: {optimal_percentile}")
    print(
        f"Correctly filtered prompts: {results[optimal_percentile]['correct_count']}/{len(responses)}"
    )
    return optimal_percentile


def analyze_responses_std(responses: List[Dict[str, Any]]) -> float:
    n_std_values = np.arange(0.1, 2.1, 0.1)
    results = {}

    for n_std in n_std_values:
        correct_count = 0
        doc_counts = []
        for prompt, response_str, _ in responses:
            try:
                response = json.loads(response_str)
                documents = response.get("references", [])
                if not documents:
                    continue

                scores = np.array(
                    [doc["metadata"].get("score", 0) for doc in documents]
                )
                mean_score = np.mean(scores)
                std_score = np.std(scores)
                threshold = mean_score + (n_std * std_score)

                selected_docs = [
                    doc
                    for doc in documents
                    if doc["metadata"].get("score", 0) >= threshold
                ]
                doc_counts.append(len(selected_docs))
                if len(selected_docs) == 1:
                    correct_count += 1

            except json.JSONDecodeError:
                continue

        results[n_std] = {
            "correct_count": correct_count,
            "avg_docs": np.mean(doc_counts),
            "max_docs": max(doc_counts),
            "min_docs": min(doc_counts),
        }

    optimal_n_std = max(results, key=lambda x: results[x]["correct_count"])

    print("\nDetailed results:")
    for n_std, data in results.items():
        print(f"n_std: {n_std:.1f}")
        print(f"  Correct (1 doc): {data['correct_count']}/{len(responses)}")
        print(f"  Avg docs: {data['avg_docs']:.2f}")
        print(f"  Range: {data['min_docs']} - {data['max_docs']} docs")
        print()

    print(f"Best n_std: {optimal_n_std}")
    print(
        f"Correctly filtered prompts: {results[optimal_n_std]['correct_count']}/{len(responses)}"
    )
    return optimal_n_std


async def fetch_uncached_responses(tester, uncached_prompts, connections):
    return await tester.run_load_test(uncached_prompts, connections)


# Usage example
async def main():
    websocket_url = "wss://dkmwo6pd6rra6.cloudfront.net/socket"
    origin = "https://dkmwo6pd6rra6.cloudfront.net"
    cache_file = "response_cache.pkl"

    with open("std_prompts.txt", "r", encoding="utf8") as f:
        prompts = [line.strip() for line in f if line.strip()]

    connections = 20

    # Load cache
    cache = load_cache(cache_file)

    # Identify uncached prompts
    uncached_prompts = [prompt for prompt in prompts if prompt not in cache]

    if uncached_prompts:
        tester = WebSocketLoadTester(websocket_url, origin)
        new_results = await fetch_uncached_responses(
            tester, uncached_prompts, connections
        )

        # Update cache with new results
        for prompt, response, latency in new_results:
            cache[prompt] = (response, latency)

        # Save updated cache
        save_cache(cache, cache_file)

    # Combine cached and new results
    results = [(prompt, cache[prompt][0], cache[prompt][1]) for prompt in prompts]

    optimal_n_std = analyze_responses_percentile(results)

    print(f"Optimal n_std value: {optimal_n_std}")


# Run the main function
asyncio.run(main())
