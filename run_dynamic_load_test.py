import asyncio
import argparse
import json
import logging
import os
import random
from typing import List, Dict, Any
from matplotlib import pyplot as plt
from websockets.exceptions import WebSocketException

from core import WebSocketLoadTester, Metric
import datetime


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dynamic WebSocket Load Tester")
    parser.add_argument("--ws", help="WebSocket URL", required=True)
    parser.add_argument(
        "--origin", help="Origin for WebSocket connection", required=True
    )
    parser.add_argument(
        "--max-connections", type=int, default=100, help="Maximum number of connections"
    )
    parser.add_argument(
        "--step-size", type=int, default=10, help="Number of new connections per step"
    )
    parser.add_argument(
        "--think-time",
        type=float,
        default=5.0,
        help="Think time between steps (seconds)",
    )
    parser.add_argument(
        "--output-folder",
        default="./output",
        help="Output file for results",
    )
    parser.add_argument(
        "--prompts-folder",
        default="./datasets",
        help="Folder containing prompt JSONL files",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=-1,
        help="Maximum number of prompts to sample",
    )
    parser.add_argument(
        "--queue-size",
        type=int,
        default=10,
        help="Maximum number of messages in the queue per connection",
    )
    return parser.parse_args()


def read_prompts(folder_path: str, max_samples: int = -1) -> List[Dict]:
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


def get_metrics() -> List[Metric]:
    # Define your metrics here (reuse from original code if needed)
    return []


def plot_results(results: Dict[str, Any], output_file: str):
    connections = list(results.keys())
    avg_latencies = [results[conn]["avg_latency"] for conn in connections]
    error_rates = [results[conn]["error_rate"] for conn in connections]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot average latency
    color = "tab:blue"
    ax1.set_xlabel("Number of Connections")
    ax1.set_ylabel("Average Latency (s)", color=color)
    ax1.plot(connections, avg_latencies, color=color, marker="o")
    ax1.tick_params(axis="y", labelcolor=color)

    # Create a second y-axis for error rate
    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("Error Rate", color=color)
    ax2.plot(connections, error_rates, color=color, marker="s")
    ax2.tick_params(axis="y", labelcolor=color)

    # Set y-axis for error rate to percentage
    ax2.set_ylim(0, 1)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: "{:.0%}".format(y)))

    plt.title("Average Latency and Error Rate vs Number of Connections")
    fig.tight_layout()
    plt.savefig(output_file)
    plt.close()

    print(f"Results plot saved to {output_file}")


async def run_dynamic_load_test(
    args: argparse.Namespace, cached_prompts: List[Dict]
) -> Dict[str, Any]:
    load_tester = WebSocketLoadTester(args.ws, args.origin, get_metrics())
    results = {}
    current_connections = 1

    while current_connections <= args.max_connections:
        print(
            f"Testing with {current_connections} concurrent connection(s) with a queue size of {args.queue_size} and a think time of {args.think_time} seconds"
        )

        # Create a queue of prompts for each connection
        prompts_queues = [
            random.sample(cached_prompts, args.queue_size)
            for _ in range(current_connections)
        ]

        all_results = []

        for _ in range(args.queue_size):
            prompts = [queue.pop(0) for queue in prompts_queues if queue]

            # Run the load test for this batch
            step_results = await load_tester.run_load_test(prompts, current_connections, args.queue_size)
            all_results.extend(step_results)

            # Wait for think time between questions
            await asyncio.sleep(args.think_time)

        # Process and store results
        latencies = [latency for _, _, latency in all_results if latency > 0]
        errors = [
            resp
            for _, resp, _ in all_results
            if isinstance(resp, str) and "veuillez réessayer plus tard" in resp
        ]

        results[current_connections] = {
            "connections_count": current_connections,
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0,
            "min_latency": min(latencies) if latencies else 0,
            "error_count": len(errors),
            "error_rate": len(errors) / (current_connections * args.queue_size),
        }

        print(f"Results for {current_connections} connections:")
        print(
            f"  Average Latency: {results[current_connections]['avg_latency']:.2f} seconds"
        )
        print(f"  Error Rate: {results[current_connections]['error_rate']:.2%}")

        current_connections = min(
            current_connections + args.step_size, args.max_connections + 1
        )

    return results


async def main():
    args = parse_arguments()

    try:
        # Read and cache prompts
        print("Reading and caching prompts...")
        cached_prompts = read_prompts(args.prompts_folder, args.max_samples)
        print(f"Cached {len(cached_prompts)} prompts")

        if not cached_prompts:
            raise ValueError(
                "No valid prompts found. Please check your prompts folder and files."
            )

        results = await run_dynamic_load_test(args, cached_prompts)

        # Generate result file name with date
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        result_file = f"dynamic_load_test_results_{date_str}.json"

        # Save results to file
        with open(result_file, "w") as f:
            results["endpoint"] = args.ws
            json.dump(results, f, indent=2)

        # Plot and save results
        plot_output = os.path.join(
            args.output_folder, "dynamic_load_test_plot_{date_str}.png"
        )
        plot_results(results, plot_output)

        print(f"Results saved to {result_file}")

    except WebSocketException as e:
        logging.error(f"WebSocket error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
