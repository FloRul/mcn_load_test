import asyncio
import websockets
import json
import time


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
        print("\n")  # New line after progress indicator
        return results
