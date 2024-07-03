from typing import Callable, List, Tuple, Any
import statistics


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
