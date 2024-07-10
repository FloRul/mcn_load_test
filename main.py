import asyncio
import hashlib
import json
import time
import argparse
from urllib.parse import urlparse
import statistics
import os
import datetime
from typing import List, Tuple, Dict, Any

from core import Metric, WebSocketLoadTester


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WebSocket Load Tester for AWS API Gateway"
    )
    parser.add_argument("websocket_url", help="WebSocket URL of the AWS API Gateway")
    parser.add_argument(
        "prompts_folder", help="Folder containing JSON files with prompts"
    )
    parser.add_argument(
        "--origin", help="Origin for the WebSocket connection", default=None
    )
    parser.add_argument(
        "--connections", type=int, default=10, help="Number of concurrent connections"
    )
    args = parser.parse_args()

    if args.origin is None:
        parsed_url = urlparse(args.websocket_url)
        args.origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

    return args


def read_prompts(folder_path: str) -> list[dict]:
    prompts = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".jsonl"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf8") as file:
                for line in file:
                    try:
                        prompt = json.loads(line)
                        prompts.append(prompt)
                    except (json.JSONDecodeError, KeyError):
                        print(f"Warning: Skipping invalid line in {filename}")
    return prompts


def calculate_statistics(results: List[Tuple[str, dict, float]]) -> Dict[str, Any]:
    latencies = [latency for _, _, latency in results if latency > 0]
    return {
        "total_requests": len(results),
        "successful_requests": sum(
            1
            for _, response, _ in results
            if not response["message"].startswith("Une erreur")
        ),
        "latency": {
            "average": statistics.mean(latencies) if latencies else 0,
            "median": statistics.median(latencies) if latencies else 0,
            "min": min(latencies) if latencies else 0,
            "max": max(latencies) if latencies else 0,
            "p95": (
                statistics.quantiles(latencies, n=20)[18]
                if len(latencies) >= 20
                else max(latencies) if latencies else 0
            ),
            "p99": (
                statistics.quantiles(latencies, n=100)[98]
                if len(latencies) >= 100
                else max(latencies) if latencies else 0
            ),
        },
    }


def generate_output_filenames(script_name: str) -> Tuple[str, str]:
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    return (
        os.path.join(output_dir, f"{script_name}-{current_time}-output.json"),
        os.path.join(output_dir, f"{script_name}-{current_time}-summary.json"),
    )


def write_results(
    filename: str,
    results: List[Tuple[str, str, float]],
):
    output = {}

    for prompt, response, latency in results:
        # Create a hash of the request
        request_hash = hashlib.md5(json.dumps(prompt["Question"]).encode()).hexdigest()

        # Parse the response JSON
        message = response.get("message", "").lstrip("\n")

        # Create the dictionary for this request
        result_dict = {"input": prompt, "output": message, "latency": latency}

        # Use the hash as the key in the output dictionary
        output[request_hash] = result_dict

    # Write the results to a JSON file
    with open(filename, "w", encoding="utf8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def write_summary(
    filename: str, stats: Dict[str, Any], total_time: float, metrics: List[Metric]
):
    summary = {
        "total_requests": stats["total_requests"],
        "successful_requests": stats["successful_requests"],
        "total_time": total_time,
        "requests_per_second": stats["total_requests"] / total_time,
        "latency": stats["latency"],
        "metrics": {},
    }

    for metric in metrics:
        metric_name, metric_average, metric_scores, failed_responses = (
            metric.get_results()
        )
        summary["metrics"][metric_name] = {
            "average": metric_average,
            "failed_responses": [
                {
                    "prompt": failed["prompt"],
                    "response": failed["response"],
                    "reason": failed.get("reason", failed.get("error", "Unknown")),
                }
                for failed in failed_responses
            ],
        }

    with open(filename, "w", encoding="utf8") as f:
        json.dump(summary, f, indent=2)


import traceback
import logging

# Set up logging
logging.basicConfig(
    filename="load_test.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_metrics() -> List[Metric]:
    def classification_accuracy(input: dict, output: dict) -> float:
        try:
            return 1.0 if input["Intent"] == output["intent"] else 0.0
        except KeyError:
            return 0.0

    def ref_recall_count(input: dict, output: dict) -> float:
        try:
            out_ref_count = len(output["references"])
            in_ref_count = int(input["RefCount"])

            if in_ref_count == 0 and out_ref_count == 0:
                return 1.0
            elif in_ref_count == 1 and out_ref_count == 1:
                return 1.0
            elif in_ref_count > 1 and out_ref_count >= 1:
                return 1.0
            else:
                return 0.0
        except KeyError:
            return 0.0

    return [
        Metric(
            "classification_accuracy",
            classification_accuracy,
            failure_condition=lambda _, __, score: score == 0.0,
        ),
        Metric(
            "ref_recall_count",
            ref_recall_count,
            failure_condition=lambda _, __, score: score == 0.0,
        ),
    ]


async def main():
    try:
        args = parse_arguments()
        prompts = read_prompts(args.prompts_folder)

        load_tester = WebSocketLoadTester(
            args.websocket_url, args.origin, get_metrics()
        )

        print(
            f"Starting load test with {len(prompts)} prompts and up to {args.connections} concurrent connections"
        )
        start_time = time.time()
        results = await load_tester.run_load_test(prompts, args.connections)
        end_time = time.time()

        total_time = end_time - start_time
        stats = calculate_statistics(results)

        script_name = os.path.splitext(os.path.basename(__file__))[0]
        output_filename, output_summary = generate_output_filenames(script_name)

        write_results(output_filename, results)
        write_summary(output_summary, stats, total_time, load_tester.metrics)

        print(f"\nResults written to {output_filename}")
        print(f"Summary results saved to {output_summary}\n")
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        logging.error(error_msg)
        raise  # Re-raise the exception after logging


if __name__ == "__main__":
    asyncio.run(main())
