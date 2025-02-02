﻿import asyncio
from collections import Counter
import hashlib
import json
import random
import time
import argparse
from urllib.parse import urlparse
import statistics
import os
import datetime
from typing import List, Tuple, Dict, Any
import zipfile
from analytics import Analytics
from core import Metric, WebSocketTester
import traceback
import logging
import glob
import shutil


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WebSocket Load Tester for AWS API Gateway"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=-1,
        help="Maximum number of samples to use",
        dest="max_samples",
    )
    parser.add_argument(
        "--ws", help="WebSocket URL of the AWS API Gateway", dest="websocket_url"
    )
    parser.add_argument(
        "--o", help="Origin for the WebSocket connection", dest="origin", default=None
    )
    parser.add_argument(
        "--out",
        help="Folder to save all output files",
        default="output",
        dest="output_folder",
    )
    parser.add_argument(
        "--c",
        type=int,
        default=5,
        help="Number of concurrent connections",
        dest="connections",
    )
    args = parser.parse_args()

    if args.origin is None:
        parsed_url = urlparse(args.websocket_url)
        args.origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

    return args


def read_prompts(folder_path: str, max_samples: int = -1) -> list[dict]:
    prompts = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".jsonl"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf8") as file:
                lines = file.readlines()
                if max_samples == -1:
                    sampled_lines = lines
                else:
                    num_samples = min(max_samples, len(lines))
                    sampled_lines = random.sample(lines, num_samples)
                for line in sampled_lines:
                    try:
                        prompt = json.loads(line)
                        prompts.append(prompt)
                    except (json.JSONDecodeError, KeyError):
                        print(f"Warning: Skipping invalid line in {filename}")
    return prompts


def calculate_statistics(results: List[Tuple[str, dict, float]]) -> Dict[str, Any]:
    intent_latencies = {}
    intent_count = Counter(
        [
            response.get("intent", "")
            for _, response, _ in results
            if isinstance(response, dict)
        ]
    )

    for intent in intent_count.keys():
        intent_results = [
            (prompt, response, latency)
            for prompt, response, latency in results
            if isinstance(response, dict) and response.get("intent") == intent
        ]
        latencies = [latency for _, _, latency in intent_results if latency > 0]
        intent_latencies[intent] = {
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
        }

    return {
        "total_requests": len(results),
        "per_intent": {intent: count for intent, count in intent_count.items()},
        "successful_requests": sum(
            1
            for _, response, _ in results
            if isinstance(response, dict)
            and not response.get("message", "").startswith("Une erreur")
        ),
        "latency": intent_latencies,
    }


def generate_output_filenames(
    output_dir: str, script_name: str, suffix: str
) -> Tuple[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    return (
        os.path.join(output_dir, f"{script_name}-{suffix}-output.json"),
        os.path.join(output_dir, f"{script_name}-{suffix}-summary.json"),
    )


def write_results(filename: str, results: List[Tuple[str, str, float]]):
    output = {}

    for prompt, response, latency in results:
        request_hash = hashlib.md5(json.dumps(prompt["Question"]).encode()).hexdigest()
        message = response.get("message", "").lstrip("\n")
        infered_intent = response.get("intent", "")
        result_dict = {
            "input": prompt,
            "output": {
                "response": message,
                "intent": infered_intent,
                "length": len(message),
            },
            "latency": round(latency, 2),
        }
        output[request_hash] = result_dict

    with open(filename, "w", encoding="utf8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def write_summary(
    filename: str, stats: Dict[str, Any], total_time: float, metrics: List[Metric]
):
    summary = {
        "total_requests": stats["total_requests"],
        "successful_requests": stats["successful_requests"],
        "total_time": round(total_time, 2),
        "requests_per_second": round(stats["total_requests"] / total_time, 2),
        "per_intent": stats["per_intent"],
        "latency": {},
        "metrics": {},
    }

    # Add latency statistics for each intent
    for intent, latency_stats in stats["latency"].items():
        summary["latency"][intent] = {
            "average": round(latency_stats["average"], 2),
            "median": round(latency_stats["median"], 2),
            "min": round(latency_stats["min"], 2),
            "max": round(latency_stats["max"], 2),
            "p95": round(latency_stats["p95"], 2),
            "p99": round(latency_stats["p99"], 2),
        }

    # Add metrics
    for metric in metrics:
        metric_name, metric_average, metric_scores, failed_responses = (
            metric.get_results()
        )
        summary["metrics"][metric_name] = {
            "average": round(metric_average, 2),
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
    return summary


def get_metrics() -> List[Metric]:
    def classification_accuracy(input: dict, output: dict) -> float:
        try:
            return 1.0 if input["Intent"] == output["intent"] else 0.0
        except KeyError:
            return 0.0

    def length_check(input: dict, output: dict) -> float:
        try:
            return 0.0 if len(output.get("message", "")) > 1000 else 1.0
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

    def sentence_count(input: dict, output: dict) -> float:
        try:
            return 1.0 if len(output.get("message", "").split(".")) > 1 else 0.0
        except KeyError:
            return 0.0

    return [
        Metric(
            "classification_accuracy",
            classification_accuracy,
            failure_condition=lambda _, __, score: score == 0.0,
        ),
        # Metric(
        #     "ref_recall_count",
        #     ref_recall_count,
        #     failure_condition=lambda _, __, score: score == 0.0,
        # ),
        Metric(
            "length_check",
            length_check,
            failure_condition=lambda _, __, score: score == 0.0,
        ),
    ]


async def main():
    try:
        args = parse_arguments()
        prompts = read_prompts("./datasets", max_samples=args.max_samples)

        tester = WebSocketTester(args.websocket_url, args.origin, get_metrics())

        print(
            f"Starting quality test with {len(prompts)} prompts and up to {args.connections} concurrent connections"
        )
        start_time = time.time()
        results = await tester.run(
            prompts=prompts,
            connections=args.connections,
            queue_size=-1,
            think_time=0.5,
        )
        end_time = time.time()

        total_time = end_time - start_time
        stats = calculate_statistics(results)

        script_name = "quality_test"
        suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename, output_summary = generate_output_filenames(
            args.output_folder, script_name, suffix
        )

        write_results(output_filename, results)
        summary = write_summary(output_summary, stats, total_time, tester.metrics)
        analytics = Analytics(args.output_folder, args.output_folder, suffix=suffix)
        analytics.plot_failed_responses_summary(summary)
        analytics.plot_intent_distribution(stats)

        files = glob.glob(f"{args.output_folder}/*{suffix}*")

        zip_filename = f"results_{suffix}.zip"
        with zipfile.ZipFile(zip_filename, "w") as zip_file:
            for file in files:
                zip_file.write(file, os.path.basename(file))

        shutil.move(zip_filename, os.path.join(args.output_folder, zip_filename))

        print(f"Zip file created: {os.path.join(args.output_folder, zip_filename)}")
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        logging.error(error_msg)
        raise


if __name__ == "__main__":
    logging.basicConfig(
        filename="quality_test.log",
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
