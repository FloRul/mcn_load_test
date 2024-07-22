import matplotlib.pyplot as plt
from collections import Counter
import os
import json

class Analytics:
    def __init__(self, results_folder: str, output_folder: str, suffix: str):
        self.results_folder = results_folder
        self.output_folder = output_folder
        self.suffix = suffix

    def _get_latest_summary(self):
        latest_file = max(
            (f for f in os.listdir(self.results_folder) if f.endswith("-summary.json")),
            key=lambda f: os.path.getmtime(os.path.join(self.results_folder, f))
        )
        with open(os.path.join(self.results_folder, latest_file), 'r') as f:
            return json.load(f)

    def _plot_bar_chart(self, data: dict, title: str, filename: str):
        plt.figure(figsize=(10, 6))
        plt.bar(data.keys(), data.values())
        plt.title(title)
        plt.xlabel("Intent")
        plt.ylabel("Count")

        for i, (intent, count) in enumerate(data.items()):
            plt.text(i, count, str(count), ha="center", va="bottom")

        plt.savefig(os.path.join(self.output_folder, f"{filename}-{self.suffix}.png"), dpi=300)
        plt.close()

    def plot_failed_responses_summary(self, data: dict = None):
        if data is None:
            data = self._get_latest_summary()

        failed_responses = data.get("metrics", {}).get("classification_accuracy", {}).get("failed_responses", [])
        intent_counts = Counter(response["prompt"]["Intent"] for response in failed_responses)

        total_responses = sum(intent_counts.values())
        intent_distribution = {intent: count / total_responses for intent, count in intent_counts.items()}

        self._plot_bar_chart(intent_counts, "Misclassification Trend", "failed_responses_summary")

        summary_text = f"Total failed responses: {len(failed_responses)}\nIntent Distribution:\n"
        summary_text += "\n".join(f"{intent}: {dist:.2%} ({intent_counts[intent]}/{total_responses})" 
                                  for intent, dist in intent_distribution.items())

        plt.text(0.5, 0.5, summary_text, transform=plt.gca().transAxes, fontsize=10, 
                 va="center", ha="center", bbox=dict(facecolor="white", alpha=0.5))
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, f"failed_responses_summary-{self.suffix}.png"), dpi=300)
        plt.close()

    def plot_intent_distribution(self, data: dict = None):
        if data is None:
            data = self._get_latest_summary()

        self._plot_bar_chart(data["per_intent"], "Intent Distribution", "intent_distribution")