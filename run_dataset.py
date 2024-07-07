import datetime
import json
import asyncio
from langfuse import Langfuse
from dotenv import load_dotenv
import os
from typing import Generator
from langfuse.client import DatasetItemClient
from tqdm import tqdm
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


async def process_item(ws_tester, item: DatasetItemClient):

    _, output, latency = await ws_tester.asend_message({"Question": item.input})
    trace_id = item.metadata.get("traceId", None)
    item.link(
        trace_id=trace_id,
        run_name="load_test_run" + datetime.datetime.now().isoformat(),
    )

    # Check if output is a dictionary and has the 'intent' key
    if isinstance(output, dict) and "intent" in output:
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


async def main():
    ws_tester = WebSocketLoadTester(
        websocket_url=os.environ.get("WEBSOCKET_URL"), origin=os.environ.get("ORIGIN")
    )

    if is_langfuse_enabled():
        dataset = langfuse.get_dataset(
            os.environ.get("LANGFUSE_DATASET_NAME", "load_test_dataset")
        )
        ws_tester.total_requests = len(dataset.items)

        tasks = [process_item(ws_tester, item) for item in dataset.items]
        results = await tqdm_asyncio.gather(*tasks, desc="Running load test")

        print("\nLoad test completed.")
        print(f"Total items processed: {len(results)}")

    # Flush the langfuse client to ensure all data is sent to the server at the end of the experiment run
    langfuse.flush()


if __name__ == "__main__":
    asyncio.run(main())
