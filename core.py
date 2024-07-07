import datetime
from typing import Callable, List, Tuple, Dict, Any
import statistics
import asyncio
import websockets
import json
import time
from langfuse import Langfuse
from dotenv import load_dotenv
import os


class Metric:
    """
    Represents a metric used to compute scores for prompts and responses.

    Attributes:
        name (str): The name of the metric.
        function (Callable[[dict, dict], float]): The function used to compute the score.
        failure_condition (Callable[[dict, dict], bool], optional): The condition that determines if a response is considered a failure. Defaults to None.
        scores (List[float]): The list of computed scores.
        failed_responses (List[Dict[str, Any]]): The list of failed responses.
    """

    def __init__(
        self,
        name: str,
        function: Callable[[dict, dict], float],
        failure_condition: Callable[[dict, dict], bool] = None,
    ):
        self.name: str = name
        self.function: Callable[[dict, dict], float] = function
        self.failure_condition: Callable[[dict, dict, float], bool] = (
            failure_condition or (lambda p, r: True)
        )
        self.scores: List[float] = []
        self.failed_responses: List[Dict[str, Any]] = []

    def compute(self, prompt: dict, response: dict) -> float:
        """
        Computes the score for a given prompt and response.

        Args:
            prompt (dict): The prompt data.
            response (dict): The response data.

        Returns:
            float: The computed score.
        """

        try:
            score: float = self.function(prompt, response)
            self.scores.append(score)
            if self.failure_condition(prompt, response, score):
                self.failed_responses.append(
                    {
                        "prompt": prompt,
                        "response": response,
                        "reason": f"Failed condition check - {self.name}",
                    }
                )
            return score
        except Exception as e:
            print(f"Error: {self.name} could not compute score due to an error.")
            self.failed_responses.append(
                {"prompt": prompt, "response": response, "error": str(e)}
            )
            return 0.0

    def get_average(self) -> float:
        """
        Computes the average score.

        Returns:
            float: The average score.
        """
        return statistics.mean(self.scores) if self.scores else 0.0

    def get_results(self) -> Tuple[str, float, List[float], List[Dict[str, Any]]]:
        """
        Returns the metric results.

        Returns:
            Tuple[str, float, List[float], List[Dict[str, Any]]]: A tuple containing the metric name, average score, list of scores, and list of failed responses.
        """
        return self.name, self.get_average(), self.scores, self.failed_responses


class WebSocketLoadTester:

    def __init__(self, websocket_url, origin, metrics: List[Metric] = []):
        self.websocket_url = websocket_url
        self.origin = origin
        self.completed_requests = 0
        self.total_requests = 0
        self.metrics = metrics

    async def asend_message(self, prompt: dict):
        try:
            async with websockets.connect(
                self.websocket_url, origin=self.origin
            ) as websocket:
                payload = json.dumps({"message": prompt["Question"]})
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

    async def run_load_test(self, prompts: List[dict], connections):
        self.total_requests = len(prompts)
        self.completed_requests = 0
        semaphore = asyncio.Semaphore(connections)

        async def bounded_send(prompt: dict):
            async with semaphore:
                result = await self.asend_message(prompt)
                try:
                    # Attempt to parse the response as JSON
                    response_json = json.loads(result[1])
                except json.JSONDecodeError as e:
                    print(f"Failed to parse response as JSON: {e}")
                    print(f"Raw response: {result[1]}")
                    # Create a dummy response object for metrics computation
                    response_json = {
                        "error": "Invalid JSON response",
                        "raw_response": result[1],
                    }

                # Compute metrics for this result
                for metric in self.metrics:
                    metric.compute(prompt, response_json)

                return (
                    prompt,
                    response_json,
                    result[2],
                )  # Return parsed JSON or error dict

        tasks = [bounded_send(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        print("\n")  # New line after progress indicator
        return results
