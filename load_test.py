import asyncio
import websockets
import json
import time
import argparse
from urllib.parse import urlparse
import statistics


class WebSocketLoadTester:
    def __init__(self, websocket_url, origin):
        self.websocket_url = websocket_url
        self.origin = origin
        self.completed_requests = 0
        self.total_requests = 0

    async def send_message(self, prompt):
        try:
            async with websockets.connect(
                self.websocket_url, origin=self.origin
            ) as websocket:
                payload = json.dumps({"message": prompt})
                start_time = time.time()
                await websocket.send(payload)
                response = await websocket.recv()
                end_time = time.time()
                latency = end_time - start_time
                self.completed_requests += 1
                print(
                    f"\rCompleted {self.completed_requests}/{self.total_requests} requests",
                    end="",
                    flush=True,
                )
                return prompt, response, latency
        except Exception as e:
            self.completed_requests += 1
            print(
                f"\rCompleted {self.completed_requests}/{self.total_requests} requests",
                end="",
                flush=True,
            )
            return prompt, f"Error: {str(e)}", 0

    async def run_load_test(self, prompts, connections):
        self.total_requests = len(prompts)
        self.completed_requests = 0
        semaphore = asyncio.Semaphore(connections)

        async def bounded_send(prompt):
            async with semaphore:
                return await self.send_message(prompt)

        tasks = [bounded_send(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        print()  # New line after progress indicator
        return results


async def main():
    parser = argparse.ArgumentParser(
        description="WebSocket Load Tester for AWS API Gateway"
    )
    parser.add_argument("websocket_url", help="WebSocket URL of the AWS API Gateway")
    parser.add_argument("prompts_file", help="File containing prompts, one per line")
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

    with open(args.prompts_file, "r") as f:
        prompts = [line.strip() for line in f if line.strip()]

    load_tester = WebSocketLoadTester(args.websocket_url, args.origin)

    print(
        f"Starting load test with {len(prompts)} prompts and up to {args.connections} concurrent connections"
    )
    start_time = time.time()
    results = await load_tester.run_load_test(prompts, args.connections)
    end_time = time.time()

    total_requests = len(results)
    total_time = end_time - start_time
    successful_requests = sum(
        1 for _, response, _ in results if not response.startswith("Error")
    )
    latencies = [latency for _, _, latency in results if latency > 0]
    avg_latency = statistics.mean(latencies) if latencies else 0
    median_latency = statistics.median(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    p95_latency = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else max_latency
    )
    p99_latency = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else max_latency
    )

    print(f"\nLoad Test Results:")
    print(f"Total Requests: {total_requests}")
    print(f"Successful Requests: {successful_requests}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Requests per second: {total_requests / total_time:.2f}")
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Median Latency: {median_latency:.4f} seconds")
    print(f"Min Latency: {min_latency:.4f} seconds")
    print(f"Max Latency: {max_latency:.4f} seconds")
    print(f"95th Percentile Latency: {p95_latency:.4f} seconds")
    print(f"99th Percentile Latency: {p99_latency:.4f} seconds")

    print("\nSample Results:")
    for i, (prompt, response, latency) in enumerate(results[:5]):
        print(f"Request {i+1}:")
        print(f"  Prompt: {prompt}")
        print(f"  Response: {response}")
        print(f"  Latency: {latency:.4f} seconds")
        print()

    # Save summary results as JSON
    summary = {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "total_time": total_time,
        "requests_per_second": total_requests / total_time,
        "latency": {
            "average": avg_latency,
            "median": median_latency,
            "min": min_latency,
            "max": max_latency,
            "p95": p95_latency,
            "p99": p99_latency,
        },
    }

    with open("load_test_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Summary results saved to load_test_summary.json")


if __name__ == "__main__":
    asyncio.run(main())
