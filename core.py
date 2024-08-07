import random
from typing import Callable, List, Tuple, Dict, Any
import statistics
import asyncio
from tqdm import tqdm
import websockets
import json
import time


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

    def compute(
        self,
        prompt: dict,
        response: dict,
    ) -> float:
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
                        "response": str(response),
                        "reason": f"Failed condition check - {self.name}",
                    }
                )
            return score
        except Exception as e:
            print(
                f"Error: {self.name} could not compute score due to an error : {str(e)}"
            )
            self.failed_responses.append(
                {"prompt": prompt, "response": str(response), "error": str(e)}
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


class WebSocketTester:

    def __init__(
        self,
        websocket_url: str,
        origin: str,
        metrics: List = [],
    ):
        self.websocket_url = websocket_url
        self.origin = origin
        self.metrics = metrics

    async def asend_batch(self, prompts: List[Dict], think_time: float = 0, pbar=None):
        results = []
        for prompt in prompts:
            await asyncio.sleep(think_time)
            response = await self.asend_message(prompt)
            results.append(response)
            if pbar:
                pbar.update(1)  # Update progress bar for each message processed
        return results

    async def asend_message(self, prompt: Dict, timeout: float = 120):
        try:
            async with websockets.connect(
                self.websocket_url, origin=self.origin, close_timeout=timeout
            ) as websocket:
                payload = json.dumps({"message": prompt["Question"]})
                start_time = time.time()
                await asyncio.wait_for(websocket.send(payload), timeout=timeout)
                response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                end_time = time.time()
                latency = end_time - start_time
                response = json.loads(response)
                for metric in self.metrics:
                    metric.compute(prompt, response)
                return prompt, response, latency
        except asyncio.TimeoutError:
            print(f"Timeout occurred for prompt: {prompt}")
            return prompt, {"error": "Error: Timeout"}, 0
        except Exception as e:
            print(f"Error occurred for prompt: {prompt}. Error: {str(e)}")
            return prompt, {"error": f"Error: {str(e)}"}, 0

    async def run(
        self,
        prompts: List[Dict],
        connections: int = 1,
        queue_size: int = 1,
        think_time: float = 0,
    ):
        if queue_size == -1:
            # Spread prompts across connections
            prompts_per_connection = len(prompts) // connections
            remainder = len(prompts) % connections
            total_messages = len(prompts)
        else:
            total_messages = connections * queue_size

        print(
            f"Starting tests with {len(prompts)} prompts across {connections} connections "
            f"with a {'spread' if queue_size == -1 else f'queue size of {queue_size}'} "
            f"and a think time of {think_time} seconds"
        )

        tasks = []

        with tqdm(total=total_messages) as pbar:
            for i in range(connections):
                if queue_size == -1:
                    # Distribute prompts evenly, accounting for remainder
                    start = i * prompts_per_connection + min(i, remainder)
                    end = start + prompts_per_connection + (1 if i < remainder else 0)
                    connection_prompts = prompts[start:end]
                else:
                    connection_prompts = [
                        random.choice(prompts) for _ in range(queue_size)
                    ]

                tasks.append(self.asend_batch(connection_prompts, think_time, pbar))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        print(
            f"Completed test with {len(prompts)} prompts across {connections} connections "
            f"with a {'spread' if queue_size == -1 else f'queue size of {queue_size}'} "
            f"and a think time of {think_time} seconds"
        )

        flattened_results = [
            item for sublist in results if isinstance(sublist, list) for item in sublist
        ]
        return flattened_results
