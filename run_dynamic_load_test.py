import asyncio
import argparse
import json
import logging
import os
import random
from time import sleep
from typing import List, Dict, Any
from matplotlib import pyplot as plt
from websockets.exceptions import WebSocketException

from core import WebSocketTester, Metric
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
    if parser.parse_args().step_size > parser.parse_args().max_connections:
        parser.error(
            f"argument --step-size: {parser.parse_args().step_size} "
            f"must be less than or equal to --max-connections: {parser.parse_args().max_connections}"
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


def plot_results(res_dict: Dict[str, Any], output_file: str):
    results = res_dict["results"]
    connections = list(results.keys())
    avg_latencies = [results[conn]["avg_latency"] for conn in connections]
    max_latencies = [results[conn]["max_latency"] for conn in connections]
    general_error_rates = [results[conn]["general_error_rate"] for conn in connections]
    client_error_rates = [results[conn]["client_error_rate"] for conn in connections]
    unexpected_error_rates = [
        results[conn]["unexpected_error_rate"] for conn in connections
    ]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot average latency
    color = "tab:blue"
    ax1.set_xlabel("Number of connections")
    ax1.set_ylabel("Average latency (s)", color=color, rotation=270, labelpad=10)
    ax1.plot(connections, avg_latencies, color=color, marker="o")
    ax1.tick_params(axis="y", labelcolor=color)

    # Plot max latency
    color = "tab:green"
    ax1.set_ylabel("Max latency (s)", color=color, rotation=270, labelpad=10)
    ax1.plot(connections, max_latencies, color=color, marker="o")
    ax1.tick_params(axis="y", labelcolor=color)

    # Create a second y-axis for error rate
    ax2 = ax1.twinx()
    color = "tab:orange"
    ax2.set_ylabel("General error rate", color=color, rotation=270, labelpad=10)
    ax2.plot(connections, general_error_rates, color=color, marker="s")
    ax2.tick_params(axis="y", labelcolor=color)

    # Create a third y-axis for error rate
    ax3 = ax1.twinx()
    color = "tab:red"
    ax3.set_ylabel("Client error rate", color=color, rotation=270, labelpad=10)
    ax3.plot(connections, client_error_rates, color=color, marker="s")
    ax3.tick_params(axis="y", labelcolor=color)

    # Create a fourth y-axis for error rate
    ax4 = ax1.twinx()
    color = "tab:purple"
    ax4.set_ylabel("Unexpected error rate", color=color, rotation=270, labelpad=10)
    ax4.plot(connections, unexpected_error_rates, color=color, marker="s")
    ax4.tick_params(axis="y", labelcolor=color)

    # Set y-axis for error rates to percentage
    ax2.set_ylim(0, 1)
    ax3.set_ylim(0, 1)
    ax4.set_ylim(0, 1)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: "{:.0%}".format(y)))
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: "{:.0%}".format(y)))
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: "{:.0%}".format(y)))

    plt.title("Average latency and error rates vs Number of connections")
    fig.tight_layout()
    plt.savefig(output_file)
    plt.close()

    print(f"Results plot saved to {output_file}")


async def run_dynamic_load_test(
    args: argparse.Namespace, cached_prompts: List[Dict]
) -> Dict[str, Any]:
    load_tester = WebSocketTester(args.ws, args.origin, get_metrics())
    results = {}
    connection_count = args.step_size

    while connection_count <= args.max_connections:

        all_results = await load_tester.run(
            prompts=cached_prompts,
            connections=connection_count,
            queue_size=args.queue_size,
            think_time=args.think_time,
        )

        # Process and store results
        latencies = [latency for _, _, latency in all_results if latency > 0]
        general_errors = [
            resp
            for _, resp, _ in all_results
            if isinstance(resp, dict)
            and "erreur est survenue" in resp.get("message", "")
        ]
        client_errors = [
            resp
            for _, resp, _ in all_results
            if isinstance(resp, dict)
            and "Nous rencontrons un trafic intense" in resp.get("message", "")
        ]
        unexpected_errors = [
            resp for _, resp, _ in all_results if not isinstance(resp, dict)
        ]

        results[connection_count] = {
            "connections_count": connection_count,
            "avg_latency": (
                round(sum(latencies) / len(latencies), 2) if latencies else 0
            ),
            "max_latency": round(max(latencies), 2) if latencies else 0,
            "min_latency": round(min(latencies), 2) if latencies else 0,
            "general_error_count": len(general_errors),
            "general_error_rate": round(
                len(general_errors) / (connection_count * args.queue_size), 2
            ),
            "client_error_count": len(client_errors),
            "client_error_rate": round(
                len(client_errors) / (connection_count * args.queue_size), 2
            ),
            "unexpected_error_count": len(unexpected_errors),
            "unexpected_error_rate": round(
                len(unexpected_errors) / (connection_count * args.queue_size), 2
            ),
            "total_error_count": len(general_errors)
            + len(client_errors)
            + len(unexpected_errors),
            "total_error_rate": round(
                (len(general_errors) + len(client_errors) + len(unexpected_errors))
                / (connection_count * args.queue_size),
                2,
            ),
        }

        print(f"Results for {connection_count} connections:")
        print(
            f"  Average Latency: {results[connection_count]['avg_latency']:.2f} seconds"
        )
        print(f"  Error Rate: {results[connection_count]['total_error_rate']:.2%}")

        connection_count = min(
            connection_count + args.step_size, args.max_connections + 1
        )
        # wait a minute between each iteration to make sure the bedrock quotas are reset
        sleep(60)

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

        res_dict = {}
        res_dict["endpoint"] = args.ws
        res_dict["origin"] = args.origin
        res_dict["max_connections"] = args.max_connections
        res_dict["step_size"] = args.step_size
        res_dict["queue_size"] = args.queue_size
        res_dict["think_time"] = args.think_time

        results = await run_dynamic_load_test(args, cached_prompts)
        res_dict["results"] = results
        # Generate result file name with date
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        result_file = os.path.join(
            args.output_folder,
            f"dynamic_load_test_results_{date_str}.json",
        )

        # Save results to file
        with open(result_file, "w") as f:
            json.dump(res_dict, f, indent=2)

        # Plot and save results
        plot_output = os.path.join(
            args.output_folder, f"dynamic_load_test_plot_{date_str}.png"
        )
        plot_results(res_dict, plot_output)

        print(f"Results saved to {result_file}")

    except WebSocketException as e:
        logging.error(f"WebSocket error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
