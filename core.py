from typing import Callable, List, Tuple
import statistics
import asyncio
import websockets
import json
import time

class Metric:
    def __init__(self, name: str, function: Callable[[dict, dict], float]):
        self.name: str = name
        self.function: Callable[[dict, dict], float] = function
        self.scores: List[float] = []

    def compute(self, prompt: dict, response: dict) -> float:
        try:
            score: float = self.function(prompt, response)
            self.scores.append(score)
            return score
        except KeyError:
            print(
                f"Error: {self.name} could not compute score due to missing key in input or output."
            )
            return 0.0

    def get_average(self) -> float:
        return statistics.mean(self.scores) if self.scores else 0.0

    def get_results(self) -> Tuple[str, float, List[float]]:
        return self.name, self.get_average(), self.scores


class WebSocketLoadTester:

    def __init__(self, websocket_url, origin, metrics: List[Metric] = []):
        self.websocket_url = websocket_url
        self.origin = origin
        self.completed_requests = 0
        self.total_requests = 0
        self.metrics = metrics

    async def send_message(self, prompt: dict):
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
                result = await self.send_message(prompt)
                # Compute metrics for this result
                for metric in self.metrics:
                    metric.compute(
                        prompt, json.loads(result[1])
                    )  # result[1] is the response
                return result

        tasks = [bounded_send(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        print("\n")  # New line after progress indicator
        return results
