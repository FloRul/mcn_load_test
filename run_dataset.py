import json
import asyncio
import random
import string
from langfuse import Langfuse
from dotenv import load_dotenv
import os
from langfuse.client import DatasetItemClient
from tqdm.asyncio import tqdm_asyncio

from core import WebSocketLoadTester

load_dotenv()
langfuse = Langfuse(
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY", ""),
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    host=os.environ.get("LANGFUSE_HOST"),
)


def is_langfuse_enabled():
    try:
        return langfuse.auth_check()
    except Exception as e:
        print(f"Langfuse is not enabled or not properly authenticated: {str(e)}")
        return False


def classification_accuracy(input: dict, output: dict) -> float:
    try:
        return 1.0 if input["Intent"] == output["intent"] else 0.0
    except KeyError:
        return 0.0


async def process_item(
    ws_tester, item: DatasetItemClient, run_name: str = "load_test_run"
):
    _, output, latency = await ws_tester.asend_message({"Question": item.input})
    output = json.loads(output)
    trace_id = output.get("traceId", None)
    if len(trace_id) > 0:
        try:
            item.link(trace_or_observation=None, run_name=run_name, trace_id=trace_id)
        except Exception as e:
            print(f"Error: {str(e)}")

    # Check if output is a dictionary and has the 'intent' key
    if isinstance(output, dict) and "intent" in output.keys():
        accuracy = 1.0 if item.metadata["intent"] == output["intent"] else 0.0
    else:
        accuracy = 0.0
        print(f"Warning: Unexpected output format: {output}")

    langfuse.score(
        trace_id=trace_id,
        name="classification accuracy",
        value=accuracy,
        comment=f"Latency: {latency:.2f}s",
    )
    return output


def generate_small_hash(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


async def main(max_parallel_tasks: int = 5):
    ws_tester = WebSocketLoadTester(
        websocket_url=os.environ.get("WEBSOCKET_URL"), origin=os.environ.get("ORIGIN")
    )

    run_name = "load_test_run" + generate_small_hash()

    if is_langfuse_enabled():
        dataset = langfuse.get_dataset(
            os.environ.get("LANGFUSE_DATASET_NAME", "load_test_dataset")
        )
        ws_tester.total_requests = len(dataset.items)

        semaphore = asyncio.Semaphore(max_parallel_tasks)

        async def process_item_with_semaphore(item):
            async with semaphore:
                return await process_item(ws_tester, item, run_name=run_name)

        tasks = [process_item_with_semaphore(item) for item in dataset.items]
        results = await tqdm_asyncio.gather(*tasks, desc="Running load test")

        print("\nLoad test completed.")
        print(f"Total items processed: {len(results)}")

    # Flush the langfuse client to ensure all data is sent to the server at the end of the experiment run
    langfuse.flush()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run load test with parallel execution limit"
    )
    parser.add_argument(
        "--max_parallel",
        type=int,
        default=5,
        help="Maximum number of parallel task executions",
    )
    args = parser.parse_args()

    asyncio.run(main(max_parallel_tasks=args.max_parallel))
